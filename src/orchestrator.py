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
from src.utils.metrics_guard import check_metrics_guard
from src.utils.metrics_logger import MetricsLogger
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
            ku_after = len(state.get("knowledge_units", []))
            gu_after = len(state.get("gap_map", []))
            logger.info("  Graph 완료: %.1fs (KU %d→%d, GU %d→%d)",
                        graph_elapsed, ku_before, ku_after, gu_before, gu_after)

            # Metrics 기록 (rollback 판정에 필요)
            self.logger.log(cycle_num, state)

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

            # Remodel (P2) — audit 후 조건 충족 시 실행
            t = time.monotonic()
            self._maybe_run_remodel(state, cycle_num, orch_cfg)
            remodel_elapsed = time.monotonic() - t

            # 사이클 후 처리: save, snapshot
            self._post_cycle(state, cycle_num, orch_cfg)

            cycle_elapsed = time.monotonic() - cycle_t0
            total_elapsed = time.monotonic() - orch_t0
            logger.info("  Cycle %d 완료: %.1fs (graph=%.1fs, audit=%.1fs, remodel=%.1fs) | 누적 %.1fs",
                        cycle_num, cycle_elapsed, graph_elapsed, audit_elapsed, remodel_elapsed, total_elapsed)

            # Plateau 감지 (plateau_window=0이면 비활성)
            if self.plateau_detector is not None:
                self.plateau_detector.record(cycle_num, state)
                if self.plateau_detector.is_plateau():
                    reason = self.plateau_detector.plateau_reason()
                    logger.info(
                        "Plateau 감지: 최근 %d사이클 KU/GU 변화 없음 (%s). 조기 종료.",
                        orch_cfg.plateau_window,
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

    def _maybe_run_remodel(
        self,
        state: EvolverState,
        cycle_num: int,
        cfg: OrchestratorConfig,
    ) -> None:
        """Remodel 조건 확인 + 실행 (P2).

        조건: cycle > 0 AND cycle % remodel_interval == 0 AND audit.has_critical.
        remodel_interval 은 audit_interval 과 동일 (기본 10).
        """
        remodel_interval = getattr(cfg, "remodel_interval", cfg.audit_interval)
        if remodel_interval <= 0:
            return
        if cycle_num <= 0 or cycle_num % remodel_interval != 0:
            return

        # 최신 audit 에 critical finding 이 있는지 확인
        audit_history = state.get("audit_history") or []
        if not audit_history:
            return

        latest_audit = audit_history[-1]
        findings = latest_audit.get("findings", [])
        has_critical = any(f.get("severity") == "critical" for f in findings)
        if not has_critical:
            logger.info("Remodel 스킵: cycle=%d, critical finding 없음", cycle_num)
            return

        # Remodel report 생성
        report = run_remodel(state, latest_audit)
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
