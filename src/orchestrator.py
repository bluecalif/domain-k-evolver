"""Orchestrator — Graph 외부 Multi-Cycle 관리.

Graph를 반복 실행하면서 사이클 간 save/snapshot/invariant check 수행.
D-32: Orchestrator가 Graph 외부에서 사이클 관리.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.config import EvolverConfig, OrchestratorConfig
from src.graph import build_graph
from src.nodes.audit import run_audit
from src.state import EvolverState
from src.utils.metrics_guard import check_metrics_guard
from src.utils.metrics_logger import MetricsLogger
from src.utils.plateau_detector import PlateauDetector
from src.utils.state_io import load_state, save_state, snapshot_state

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
        self.plateau_detector = PlateauDetector(
            window=self.config.orchestrator.plateau_window
        )
        self.results: list[CycleResult] = []
        self.audit_reports: list[dict] = []

    @property
    def _domain_path(self) -> Path:
        return Path(self.config.orchestrator.bench_path) / self.config.orchestrator.bench_domain

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

        for cycle_num in range(1, orch_cfg.max_cycles + 1):
            logger.info("=== Cycle %d 시작 ===", cycle_num)

            result = self._run_single_cycle(state, cycle_num)
            self.results.append(result)

            if result.error:
                logger.error("Cycle %d 에러: %s", cycle_num, result.error)
                break

            state = result.state

            # 사이클 후 처리
            self._post_cycle(state, cycle_num, orch_cfg)

            # Metrics 기록
            self.logger.log(cycle_num, state)

            # Metrics Guard (warning-only)
            guard = check_metrics_guard(state)
            for w in guard.warnings:
                logger.warning("Metrics Guard: %s", w)

            # Executive Audit (Phase 4)
            self._maybe_run_audit(state, cycle_num, orch_cfg)

            # Plateau 감지
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
        """audit_interval 주기에 해당하면 Executive Audit 실행."""
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

        logger.info(
            "Executive Audit cycle=%d: findings=%d, patches=%d",
            cycle_num,
            len(report.get("findings", [])),
            len(report.get("policy_patches", [])),
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
