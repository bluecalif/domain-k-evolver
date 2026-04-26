"""Orchestrator — Graph 외부 Multi-Cycle 관리.

Graph를 반복 실행하면서 사이클 간 save/snapshot/invariant check 수행.
D-32: Orchestrator가 Graph 외부에서 사이클 관리.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from src.config import EvolverConfig, OrchestratorConfig
from src.graph import build_graph
from src.nodes.audit import run_audit
from src.nodes.hitl_gate import hitl_gate_node
from src.nodes.remodel import run_remodel
from src.state import EvolverState
from src.utils.cost_guard import CostGuard
from src.utils.coverage_map import build_coverage_map
from src.utils.metrics_guard import check_metrics_guard
from src.utils.metrics_logger import MetricsLogger
from src.utils.external_novelty import compute_delta_kus, compute_external_novelty
from src.utils.novelty import compute_novelty
from src.utils.reach_ledger import build_ledger_snapshot
from src.obs.telemetry import emit_cycle
from src.nodes.exploration_pivot import run_exploration_pivot
from src.nodes.universe_probe import (
    gather_evidence,
    register_validated,
    run_universe_probe,
    should_run_universe_probe,
    validate_proposals,
)
from src.utils.plateau_detector import PlateauDetector
from src.utils.policy_manager import apply_patches, rollback, should_rollback
from src.utils.state_io import load_state, save_state, snapshot_phase, snapshot_state

logger = logging.getLogger(__name__)


class CycleResult:
    """단일 사이클 실행 결과."""

    def __init__(
        self,
        cycle: int,
        state: EvolverState,
        converged: bool = False,
        error: str | None = None,
    ) -> None:
        self.cycle = cycle
        self.state = state
        self.converged = converged
        self.error = error


class Orchestrator:
    """Multi-Cycle Evolver Orchestrator.

    사용법:
        config = EvolverConfig.from_env()
        orch = Orchestrator(config)
        results = orch.run()
    """

    def __init__(
        self,
        config: EvolverConfig | None = None,
        *,
        llm: Any | None = None,
        search_tool: Any | None = None,
    ) -> None:
        self.config = config or EvolverConfig()
        self._llm = llm
        self._search_tool = search_tool
        self.logger = MetricsLogger()
        pw = self.config.orchestrator.plateau_window
        self.plateau_detector = PlateauDetector(window=max(pw, 2)) if pw > 0 else None
        self.results: list[CycleResult] = []
        self.audit_reports: list[dict] = []
        self._pre_patch_policies: dict | None = None  # 롤백용 백업
        self._patch_applied_cycle: int = 0  # patch 적용 cycle
        self._hitl_response: dict | None = None  # HITL 응답 (테스트용 주입)
        self._prev_kus: list[dict] = []  # novelty 계산용 이전 cycle KU 스냅샷
        self._cost_guard = CostGuard(self.config.external_anchor)  # Stage E 예산 가드

    @property
    def _domain_path(self) -> Path:
        orch = self.config.orchestrator
        if orch.bench_root:
            return Path(orch.bench_root)
        return Path(orch.bench_path) / orch.bench_domain

    def run(self, initial_state: EvolverState | None = None) -> list[CycleResult]:
        """Multi-Cycle 실행.

        Args:
            initial_state: 초기 State. None이면 bench 파일에서 로드.

        Returns:
            사이클별 결과 리스트.
        """
        orch_cfg = self.config.orchestrator
        state = initial_state or load_state(self._domain_path)

        logger.info(
            "Orchestrator 시작: domain=%s, max_cycles=%d",
            orch_cfg.bench_domain,
            orch_cfg.max_cycles,
        )

        orch_t0 = time.monotonic()
        for cycle_num in range(1, orch_cfg.max_cycles + 1):
            cycle_t0 = time.monotonic()
            ku_before = len(state.get("knowledge_units", []))
            gu_before = len(state.get("gap_map", []))
            logger.info("=== Cycle %d/%d 시작 (KU=%d, GU=%d) ===",
                        cycle_num, orch_cfg.max_cycles, ku_before, gu_before)

            t = time.monotonic()
            result = self._run_single_cycle(state, cycle_num)
            graph_elapsed = time.monotonic() - t
            self.results.append(result)

            if result.error:
                logger.error("Cycle %d 에러 (%.1fs): %s", cycle_num, graph_elapsed, result.error)
                break

            state = result.state

            # 진단 필드 추출 (state에서 제거하기 전에 cycle_ctx 캡처)
            cycle_ctx = self._extract_cycle_ctx(state, cycle_num)
            ku_after = len(state.get("knowledge_units", []))
            gu_after = len(state.get("gap_map", []))
            logger.info("  Graph 완료: %.1fs (KU %d→%d, GU %d→%d)",
                        graph_elapsed, ku_before, ku_after, gu_before, gu_after)

            # Metrics 기록 (rollback 판정에 필요) — _diag_* 필드 삭제 전에 호출해야
            # adj_gen_count/wildcard_gen_count/cap_hit_count telemetry 가 보존됨
            self.logger.log(cycle_num, state)

            # _diag_* 필드 제거 (telemetry 기록 후)
            for k in list(state.keys()):
                if k.startswith("_diag_"):
                    del state[k]

            # Novelty + Coverage Map 갱신 (P4)
            self._update_novelty_and_coverage(state)

            # Metrics Guard (warning-only)
            guard = check_metrics_guard(state)
            for w in guard.warnings:
                logger.warning("Metrics Guard: %s", w)

            # Policy 롤백 체크 (patch 적용 1 cycle 후, metrics 기록 후)
            self._maybe_rollback_policy(state, cycle_num)

            # Executive Audit (Phase 4) — patch 적용 포함
            t = time.monotonic()
            self._maybe_run_audit(state, cycle_num, orch_cfg)
            audit_elapsed = time.monotonic() - t

            # Universe Probe (Stage E) — audit 후, remodel 전
            self._maybe_run_universe_probe(state, cycle_num)

            # Exploration Pivot (Stage E) — novelty+reach 정체 시 targets 치환
            self._maybe_run_exploration_pivot(state, cycle_num)

            # Remodel (P2) — audit 후 조건 충족 시 실행
            t = time.monotonic()
            self._maybe_run_remodel(state, cycle_num, orch_cfg)
            remodel_elapsed = time.monotonic() - t

            # 사이클 후 처리: save, snapshot
            self._post_cycle(state, cycle_num, orch_cfg)

            # Telemetry emit (P5-A3) — trial_root 없으면 무시
            cycle_elapsed = time.monotonic() - cycle_t0
            if self.config.orchestrator.bench_root:
                emit_cycle(state, self._domain_path, cycle_elapsed, cycle_ctx=cycle_ctx)
            total_elapsed = time.monotonic() - orch_t0
            logger.info("  Cycle %d 완료: %.1fs (graph=%.1fs, audit=%.1fs, remodel=%.1fs) | 누적 %.1fs",
                        cycle_num, cycle_elapsed, graph_elapsed, audit_elapsed, remodel_elapsed, total_elapsed)

            # Plateau 감지 (plateau_window=0이면 비활성)
            # 주의: KU/GU plateau 만 조기 종료 트리거. novelty plateau 는 audit/remodel 트리거 (Stage B).
            if self.plateau_detector is not None:
                self.plateau_detector.record(cycle_num, state)
                if self.plateau_detector.is_plateau():
                    reason = self.plateau_detector.plateau_reason()
                    logger.info(
                        "Plateau 감지: %s. 조기 종료.",
                        reason,
                    )
                    break

            # 수렴 체크
            if orch_cfg.stop_on_convergence and result.converged:
                logger.info("Cycle %d에서 수렴 감지. 종료.", cycle_num)
                break

        logger.info("Orchestrator 완료: %d cycles", len(self.results))
        return self.results

    def _run_single_cycle(self, state: EvolverState, cycle_num: int) -> CycleResult:
        """단일 사이클 Graph 실행."""
        try:
            graph = build_graph(
                llm=self._llm,
                search_tool=self._search_tool,
                search_config=self.config.search,
            )

            # Graph 실행 — invoke로 최종 state 직접 획득
            final_state = graph.invoke(state, config={"recursion_limit": 50})

            # 수렴 판정
            critique = final_state.get("current_critique", {})
            converged = bool(
                critique
                and critique.get("convergence", {}).get("converged")
            )

            return CycleResult(
                cycle=cycle_num,
                state=final_state,
                converged=converged,
            )
        except Exception as e:
            return CycleResult(
                cycle=cycle_num,
                state=state,
                error=str(e),
            )

    def _update_novelty_and_coverage(self, state: EvolverState) -> None:
        """Novelty score + Coverage map 갱신 (P4-A3)."""
        curr_kus = state.get("knowledge_units", [])

        # Novelty 계산
        novelty = compute_novelty(self._prev_kus, curr_kus)
        novelty_history = list(state.get("novelty_history") or [])
        novelty_history.append(novelty)
        state["novelty_history"] = novelty_history
        # D-148: delta_kus 먼저 계산 (self._prev_kus 갱신 전)
        delta_kus = compute_delta_kus(self._prev_kus, curr_kus)
        self._prev_kus = [dict(ku) for ku in curr_kus]  # 다음 cycle 용 스냅샷

        # SI-P4 Stage E: external_novelty — delta KU 기준 신규 비율 (D-148 fix)
        # 분모를 전체 KU 가 아닌 이번 cycle 신규 KU 로 제한해 단조 수렴 방지
        prev_keys = state.get("external_observation_keys") or []
        ext_score, new_keys = compute_external_novelty(delta_kus if delta_kus else curr_kus, prev_keys)
        ext_history = list(state.get("external_novelty_history") or [])
        ext_history.append(ext_score)
        state["external_novelty_history"] = ext_history
        state["external_observation_keys"] = sorted(set(prev_keys) | new_keys)

        # Reach diversity ledger (E3)
        cycle = state.get("current_cycle", 0)
        reach_snap = build_ledger_snapshot(curr_kus, cycle)
        reach_history = list(state.get("reach_history") or [])
        reach_history.append(reach_snap)
        state["reach_history"] = reach_history

        # Coverage map 갱신
        skeleton = state.get("domain_skeleton", {})
        coverage = build_coverage_map(state, skeleton)
        state["coverage_map"] = coverage

        summary = coverage.get("summary", {})
        logger.info(
            "  Novelty=%.3f, ext_novelty=%.3f, cat_gini=%.3f, field_gini=%.3f, domains/100ku=%.1f",
            novelty,
            ext_score,
            summary.get("category_gini", 0),
            summary.get("field_gini", 0),
            reach_snap.get("domains_per_100ku", 0),
        )

    def _maybe_run_universe_probe(
        self,
        state: EvolverState,
        cycle_num: int,
    ) -> None:
        """universe_probe 트리거 조건 확인 + 3-step pipeline 실행 (Stage E).

        audit → **probe** → remodel 순서.
        """
        should_run, reason = should_run_universe_probe(state, self.config)
        if not should_run:
            return

        logger.info("Universe probe 트리거: cycle=%d, reason=%s", cycle_num, reason)

        # Step 1: LLM survey
        survey = run_universe_probe(
            state, self._llm, self.config, self._cost_guard, cycle=cycle_num,
        )
        if survey["status"] != "ok" or not survey["proposals"]:
            logger.info(
                "Universe probe 종료: status=%s, proposals=%d",
                survey["status"], len(survey.get("proposals", [])),
            )
            return

        # Step 2: Tavily evidence
        if self._search_tool is not None:
            domain = state.get("domain_skeleton", {}).get("domain", "unknown")
            evidenced, _ = gather_evidence(
                survey["proposals"], self._search_tool, self._cost_guard, domain,
            )
        else:
            evidenced = survey["proposals"]
            logger.warning("Universe probe: search_tool 없음, evidence 수집 skip")

        # Step 3: LLM validation + skeleton 등록
        if self._llm is not None:
            min_conf = self.config.external_anchor.candidate_promotion_min_confidence
            validated, _ = validate_proposals(
                evidenced, self._llm, self._cost_guard, min_confidence=min_conf,
            )
        else:
            validated = []

        registered: list = []
        if validated:
            skeleton = state.get("domain_skeleton", {})
            registered, errors = register_validated(validated, skeleton)
            state["domain_skeleton"] = skeleton
            logger.info(
                "Universe probe 완료: cycle=%d, registered=%d, errors=%d",
                cycle_num, len(registered), len(errors),
            )
        else:
            logger.info("Universe probe: cycle=%d, 검증 통과 proposal 없음", cycle_num)

        # D-150: probe_history 기록 — VP4 R5 자동 벤치 기준
        probe_history = list(state.get("probe_history") or [])
        probe_history.append({"cycle": cycle_num, "registered": len(registered)})
        state["probe_history"] = probe_history

    def _maybe_run_exploration_pivot(
        self,
        state: EvolverState,
        cycle_num: int,
    ) -> None:
        """exploration_pivot 트리거 조건 확인 + query 치환 (Stage E).

        novelty + reach 동시 정체 시 LLM query rewriter 로 이번 cycle targets 치환.
        """
        result = run_exploration_pivot(
            state, self._llm, self.config, self._cost_guard, cycle=cycle_num,
        )
        if result["status"] != "ok":
            return

        # pivot history 기록
        pivot_history = list(state.get("pivot_history") or [])
        pivot_history.append({
            "cycle": cycle_num,
            "variants": len(result["variants"]),
            "candidate_targets": len(result["candidate_targets"]),
            "reason": result["reason"],
        })
        state["pivot_history"] = pivot_history

        logger.info(
            "Exploration pivot 실행: cycle=%d, variants=%d, candidate_targets=%d",
            cycle_num, len(result["variants"]), len(result["candidate_targets"]),
        )

    def _maybe_run_audit(
        self,
        state: EvolverState,
        cycle_num: int,
        cfg: OrchestratorConfig,
    ) -> None:
        """audit_interval 주기에 해당하면 Executive Audit 실행 + Policy Patch 적용."""
        if cfg.audit_interval <= 0:
            return
        if cycle_num % cfg.audit_interval != 0:
            return

        # 이전 audit 이후 window 계산
        prev_audit_cycle = (
            self.audit_reports[-1]["audit_cycle"] if self.audit_reports else 0
        )
        window_start = prev_audit_cycle + 1

        report = run_audit(
            state,
            self.logger.entries,
            audit_cycle=cycle_num,
            window_start=window_start,
        )
        self.audit_reports.append(report)

        # State에 audit_history 누적
        audit_history = list(state.get("audit_history") or [])
        audit_history.append(report)
        state["audit_history"] = audit_history

        # Policy Patch 적용 (Task 4.5)
        patches = report.get("policy_patches", [])
        if patches:
            self._pre_patch_policies = state.get("policies", {})
            new_policies, applied = apply_patches(
                self._pre_patch_policies, patches, cycle=cycle_num,
            )
            if applied:
                state["policies"] = new_policies
                self._patch_applied_cycle = cycle_num
                logger.info(
                    "Policy patches 적용: %d개 (cycle=%d, v%d)",
                    len(applied),
                    cycle_num,
                    new_policies.get("version", 0),
                )

        logger.info(
            "Executive Audit cycle=%d: findings=%d, patches=%d",
            cycle_num,
            len(report.get("findings", [])),
            len(patches),
        )

    def _maybe_rollback_policy(self, state: EvolverState, cycle_num: int) -> None:
        """Patch 적용 후 1 cycle 뒤 성능 악화 시 Policy 롤백."""
        if self._pre_patch_policies is None:
            return
        if cycle_num != self._patch_applied_cycle + 1:
            return

        # 현재 cycle과 patch 적용 전 cycle의 metrics.rates 비교
        entries = self.logger.entries
        if len(entries) < 2:
            self._pre_patch_policies = None
            return

        current_rates = entries[-1].get("rates", {})
        previous_rates = entries[-2].get("rates", {})

        if should_rollback(current_rates, previous_rates):
            rolled = rollback(
                state.get("policies", {}),
                self._pre_patch_policies,
                cycle=cycle_num,
                reason="performance_degradation",
            )
            state["policies"] = rolled
            logger.warning(
                "Policy 롤백 실행: cycle=%d → v%d",
                cycle_num,
                rolled.get("version", 0),
            )
        else:
            logger.info("Policy patch 성능 유지 확인 (cycle=%d)", cycle_num)

        self._pre_patch_policies = None

    # Smart Remodel Criteria 임계치
    GROWTH_STAGNATION_THRESHOLD = 5    # KU 순증 하한 (per cycle, 3c 평균)
    GROWTH_STAGNATION_WINDOW = 3       # 최근 N cycle 평균
    EXPLORATION_DROUGHT_THRESHOLD = 30  # 신규 GU open 하한 (누적)
    EXPLORATION_DROUGHT_WINDOW = 5     # 최근 N cycle 누적

    def _should_remodel(self, state: EvolverState, cycle_num: int) -> tuple[bool, str]:
        """Smart Remodel 조건 판정 — 3가지 OR.

        Returns:
            (should_run, reason) 튜플.
        """
        reasons: list[str] = []

        # ③ 기존: audit critical finding
        audit_history = state.get("audit_history") or []
        if audit_history:
            findings = audit_history[-1].get("findings", [])
            if any(f.get("severity") == "critical" for f in findings):
                reasons.append("audit_critical")

        entries = self.logger.entries
        n = len(entries)

        # ① Growth Stagnation: 최근 3 cycle KU 순증 평균 < 5
        w1 = self.GROWTH_STAGNATION_WINDOW
        if n >= w1 + 1:
            recent = entries[-(w1):]
            before_entry = entries[-(w1 + 1)]
            total_growth = recent[-1]["ku_active"] - before_entry["ku_active"]
            avg_growth = total_growth / w1
            if avg_growth < self.GROWTH_STAGNATION_THRESHOLD:
                reasons.append(f"growth_stagnation(avg={avg_growth:.1f}<{self.GROWTH_STAGNATION_THRESHOLD})")

        # ② Exploration Drought: 최근 5 cycle 신규 GU open 누적 < 30
        w2 = self.EXPLORATION_DROUGHT_WINDOW
        if n >= w2 + 1:
            recent = entries[-(w2):]
            before_entry = entries[-(w2 + 1)]
            # gu_total 증가 = 신규 GU 생성 수 (open + resolved 포함)
            new_gu = recent[-1]["gu_total"] - before_entry["gu_total"]
            if new_gu < self.EXPLORATION_DROUGHT_THRESHOLD:
                reasons.append(f"exploration_drought(new_gu={new_gu}<{self.EXPLORATION_DROUGHT_THRESHOLD})")

        if reasons:
            reason_str = " | ".join(reasons)
            logger.info("Remodel 트리거: cycle=%d, reasons=[%s]", cycle_num, reason_str)
            return True, reason_str

        return False, ""

    def _maybe_run_remodel(
        self,
        state: EvolverState,
        cycle_num: int,
        cfg: OrchestratorConfig,
    ) -> None:
        """Remodel 조건 확인 + 실행 (P2).

        Smart Criteria: cycle % remodel_interval == 0 AND
        (audit_critical OR growth_stagnation OR exploration_drought).
        remodel_interval 기본값 = audit_interval.
        """
        remodel_interval = getattr(cfg, "remodel_interval", cfg.audit_interval)
        if remodel_interval <= 0:
            return
        if cycle_num <= 0 or cycle_num % remodel_interval != 0:
            return

        # audit_history 없으면 최소 audit 1회 필요
        audit_history = state.get("audit_history") or []
        if not audit_history:
            return

        # Smart Criteria 판정
        should_run, reason = self._should_remodel(state, cycle_num)
        if not should_run:
            logger.info("Remodel 스킵: cycle=%d, smart criteria 미충족", cycle_num)
            return

        latest_audit = audit_history[-1]

        # Remodel report 생성
        report = run_remodel(state, latest_audit)
        report["trigger_reason"] = reason
        state["remodel_report"] = report

        if not report.get("proposals"):
            logger.info("Remodel 스킵: cycle=%d, 제안 0건", cycle_num)
            return

        # HITL-R 게이트
        state["hitl_pending"] = {
            "gate": "R",
            "report_id": report["report_id"],
            "proposal_count": len(report["proposals"]),
        }
        hitl_result = hitl_gate_node(state, response=self._hitl_response)

        # hitl_result 를 state 에 반영
        for k, v in hitl_result.items():
            state[k] = v

        # 승인/거부 판정
        approval = state.get("remodel_report", {}).get("approval", {})
        if approval.get("status") == "approved":
            self._apply_remodel_proposals(state, cycle_num)
        elif approval.get("status") == "rejected":
            logger.info(
                "Remodel 거부: cycle=%d, report=%s, reason=%s",
                cycle_num,
                report.get("report_id"),
                approval.get("reason", ""),
            )
        else:
            # auto-approve (response=None 이면 hitl_gate_node 가 자동 승인)
            self._apply_remodel_proposals(state, cycle_num)

    def _apply_remodel_proposals(
        self,
        state: EvolverState,
        cycle_num: int,
    ) -> None:
        """승인된 remodel 제안을 skeleton/state 에 적용 + phase bump.

        proposal types:
        - merge: entity_key 통합 (KU entity_key 재연결)
        - split: entity_key 분할 (KU entity_key 분리)
        - reclassify: category 변경
        - alias_canonicalize / source_policy / gap_rule: 기록만 (skeleton 직접 변경 없음)
        """
        report = state.get("remodel_report") or {}
        proposals = report.get("proposals", [])
        skeleton = dict(state.get("domain_skeleton", {}))
        kus = list(state.get("knowledge_units", []))

        applied_count = 0
        for proposal in proposals:
            p_type = proposal.get("type")
            targets = proposal.get("target_entities", [])
            params = proposal.get("params", {})

            if p_type == "merge" and len(targets) >= 2:
                canonical = params.get("canonical_key", targets[0])
                merge_from = [t for t in targets if t != canonical]
                for ku in kus:
                    if ku.get("entity_key") in merge_from:
                        ku["entity_key"] = canonical
                applied_count += 1

            elif p_type == "split" and targets:
                source_ek = targets[0]
                new_keys = params.get("new_keys", [])
                axis_values = params.get("axis_values", [])
                if new_keys and axis_values:
                    for ku in kus:
                        if ku.get("entity_key") == source_ek:
                            geo = ku.get("axis_tags", {}).get("geography", "")
                            if geo in axis_values:
                                idx = axis_values.index(geo)
                                if idx < len(new_keys):
                                    ku["entity_key"] = new_keys[idx]
                    applied_count += 1

            elif p_type == "reclassify" and targets:
                from_cat = params.get("from_category", "")
                to_cat = params.get("to_category", "")
                if from_cat and to_cat:
                    for ku in kus:
                        if ku.get("entity_key") in targets:
                            ek = ku["entity_key"]
                            ku["entity_key"] = ek.replace(
                                f":{from_cat}:", f":{to_cat}:",
                            )
                    applied_count += 1

            elif p_type == "source_policy":
                action = params.get("action")
                if action == "extend_ttl":
                    multiplier = params.get("ttl_multiplier", 1.5)
                    policies = dict(state.get("policies", {}))
                    ttl_defaults = dict(policies.get("ttl_defaults", {}))
                    for key in ttl_defaults:
                        ttl_defaults[key] = min(
                            int(ttl_defaults[key] * multiplier), 365,
                        )
                    policies["ttl_defaults"] = ttl_defaults
                    state["policies"] = policies
                applied_count += 1

            elif p_type == "gap_rule":
                action = params.get("action")
                if action == "prioritize_category":
                    target_cat = params.get("category", "")
                    if target_cat:
                        gap_map = list(state.get("gap_map", []))
                        skel_fields = [
                            f["name"]
                            for f in skeleton.get("fields", [])
                        ]
                        max_id = max(
                            (
                                int(gu["gu_id"].split("-")[1])
                                for gu in gap_map
                                if gu.get("gu_id")
                            ),
                            default=0,
                        )
                        domain = skeleton.get("domain", "")
                        for field in skel_fields[:3]:
                            max_id += 1
                            gap_map.append({
                                "gu_id": f"GU-{max_id:04d}",
                                "gap_type": "missing",
                                "target": {
                                    "entity_key": f"{domain}:{target_cat}:*",
                                    "field": field,
                                },
                                "expected_utility": "critical",
                                "risk_level": "convenience",
                                "status": "open",
                                "trigger": "remodel_gap_rule",
                                "trigger_source": proposal.get(
                                    "rationale", "",
                                ),
                            })
                        state["gap_map"] = gap_map
                applied_count += 1

            elif p_type == "category_addition":
                # P4-C3: 새 카테고리를 skeleton categories 에 추가
                new_cat = params.get("new_category", {})
                if new_cat and new_cat.get("slug"):
                    existing_slugs = {
                        c["slug"] for c in skeleton.get("categories", [])
                    }
                    if new_cat["slug"] not in existing_slugs:
                        cats = list(skeleton.get("categories", []))
                        cats.append({
                            "slug": new_cat["slug"],
                            "name": new_cat.get("name", new_cat["slug"]),
                        })
                        skeleton["categories"] = cats
                        logger.info(
                            "Category 추가: '%s' (evidence=%d KUs)",
                            new_cat["slug"],
                            params.get("evidence_ku_count", 0),
                        )
                applied_count += 1

            elif p_type == "alias_canonicalize":
                # 의도적 defer — entity_resolver가 ingestion 시 처리
                applied_count += 1

        state["knowledge_units"] = kus
        state["domain_skeleton"] = skeleton

        # Phase bump
        phase_number = state.get("phase_number", 0) + 1
        state["phase_number"] = phase_number

        # Phase snapshot
        try:
            snapshot_phase(self._domain_path, phase_number)
        except Exception as e:
            logger.warning("Phase snapshot 실패: %s", e)

        # Phase history 기록
        phase_history = list(state.get("phase_history") or [])
        phase_history.append({
            "phase_number": phase_number,
            "cycle": cycle_num,
            "report_id": report.get("report_id", ""),
            "proposals_applied": applied_count,
            "proposal_types": [p.get("type") for p in proposals],
        })
        state["phase_history"] = phase_history

        logger.info(
            "Remodel 적용: phase=%d, cycle=%d, proposals=%d/%d applied",
            phase_number,
            cycle_num,
            applied_count,
            len(proposals),
        )

    def _extract_cycle_ctx(self, state: EvolverState, cycle_num: int) -> dict:
        """진단 필드에서 cycle_ctx dict 구성."""
        plan = state.get("current_plan") or {}
        gap_map = state.get("gap_map") or []
        gu_by_id = {gu.get("gu_id"): gu for gu in gap_map}

        target_gap_ids = plan.get("target_gaps", [])
        targets_selected = []
        for gu_id in target_gap_ids:
            gu = gu_by_id.get(gu_id)
            if gu is None:
                continue
            target = gu.get("target", {})
            entity_key = target.get("entity_key", "")
            targets_selected.append({
                "gu_id": gu_id,
                "entity_key": entity_key,
                "field": target.get("field", ""),
                "is_wildcard": "*" in entity_key,
                "status": gu.get("status", "open"),
            })

        return {
            "cycle": cycle_num,
            "targets_selected": targets_selected,
            "queries_by_gu": plan.get("queries", {}),
            "search_yield_by_gu": state.get("_diag_search_by_gu") or {},
            "resolved_gus": state.get("_diag_resolved_gus") or [],
            "adjacent_gap_generated": state.get("_diag_adjacent_gap_count") or 0,
        }

    def _post_cycle(
        self,
        state: EvolverState,
        cycle_num: int,
        cfg: OrchestratorConfig,
    ) -> None:
        """사이클 후 처리: save, snapshot."""
        # State 저장
        save_state(state, self._domain_path)

        # 스냅샷
        if cfg.snapshot_every > 0 and cycle_num % cfg.snapshot_every == 0:
            snapshot_path = snapshot_state(self._domain_path, cycle_num)
            logger.info("Snapshot 저장: %s", snapshot_path)

    def save_metrics(self, output_dir: str | Path | None = None) -> None:
        """Metrics 로그를 JSON/CSV로 저장."""
        out = Path(output_dir or self._domain_path / "metrics")
        self.logger.save_json(out / "trajectory.json")
        self.logger.save_csv(out / "trajectory.csv")
        logger.info("Metrics 저장: %s", out)
