"""Real API N Cycle 벤치 실행 스크립트.

Usage:
    set -a && source .env && set +a
    python scripts/run_bench.py --cycles 3
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from src.adapters.llm_adapter import create_llm
from src.adapters.search_adapter import create_search_tool
from src.config import EvolverConfig
from src.graph import build_graph
from src.utils.invariant_checker import check_invariants
from src.utils.metrics_logger import MetricsLogger
from src.utils.state_io import load_state, save_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_bench")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evolver N-Cycle Bench Run")
    parser.add_argument("--cycles", type=int, default=3, help="Number of cycles to run")
    parser.add_argument("--domain", type=str, default=None, help="Override bench domain")
    args = parser.parse_args()

    config = EvolverConfig.from_env()
    config.validate_api_keys()

    if args.domain:
        # Override domain (frozen dataclass → recreate)
        from src.config import OrchestratorConfig
        orch = OrchestratorConfig(
            max_cycles=args.cycles,
            snapshot_every=config.orchestrator.snapshot_every,
            invariant_check=config.orchestrator.invariant_check,
            stop_on_convergence=config.orchestrator.stop_on_convergence,
            bench_domain=args.domain,
            bench_path=config.orchestrator.bench_path,
        )
        from src.config import EvolverConfig as EC
        config = EC(llm=config.llm, search=config.search, orchestrator=orch)

    logger.info("Config: model=%s, search=%s, cycles=%d",
                config.llm.model, config.search.provider, args.cycles)

    # State 로드
    domain_path = Path(config.orchestrator.bench_path) / config.orchestrator.bench_domain
    state = load_state(domain_path)
    start_cycle = state.get("current_cycle", 1)
    logger.info("State 로드: KU=%d, GU=%d, cycle=%d",
                len(state.get("knowledge_units", [])),
                len(state.get("gap_map", [])),
                start_cycle)

    # LLM + Search 생성
    llm = create_llm(config.llm)
    search_tool = create_search_tool(config.search)

    # Graph 빌드
    graph = build_graph(llm=llm, search_tool=search_tool)
    logger.info("Graph 빌드 완료.")

    # Metrics Logger
    metrics_logger = MetricsLogger()
    invariant_violations = 0
    output_path = domain_path.parent / f"{domain_path.name}-auto"

    for i in range(args.cycles):
        cycle_num = start_cycle + i
        logger.info("=== Cycle %d 시작 ===", cycle_num)

        # LLM/Search 카운터 리셋 (사이클별 추적)
        prev_llm_calls = getattr(llm, "call_count", 0)
        prev_search_calls = getattr(search_tool, "search_calls", 0)
        prev_fetch_calls = getattr(search_tool, "fetch_calls", 0)

        try:
            state = graph.invoke(state, config={"recursion_limit": 50})
        except Exception as e:
            logger.error("Cycle %d 실패: %s", cycle_num, e)
            break

        # 사이클별 API 사용량
        cycle_llm_calls = getattr(llm, "call_count", 0) - prev_llm_calls
        cycle_search_calls = getattr(search_tool, "search_calls", 0) - prev_search_calls
        cycle_fetch_calls = getattr(search_tool, "fetch_calls", 0) - prev_fetch_calls
        cycle_llm_tokens = getattr(llm, "total_tokens", 0)

        # Metrics 기록
        metrics_logger.log(
            cycle_num, state,
            llm_calls=cycle_llm_calls,
            llm_tokens=cycle_llm_tokens,
            search_calls=cycle_search_calls,
            fetch_calls=cycle_fetch_calls,
        )

        # 불변원칙 검증
        inv_result = check_invariants(state)
        if not inv_result.passed:
            invariant_violations += 1
            for v in inv_result.violations:
                logger.warning("불변원칙 위반: %s", v)
        for w in inv_result.warnings:
            logger.info("경고: %s", w)

        # 결과 요약
        kus = state.get("knowledge_units", [])
        gus = state.get("gap_map", [])
        logger.info("Cycle %d 완료: KU=%d (active=%d, disputed=%d), GU=%d (open=%d, resolved=%d)",
                     cycle_num,
                     len(kus),
                     sum(1 for k in kus if k.get("status") == "active"),
                     sum(1 for k in kus if k.get("status") == "disputed"),
                     len(gus),
                     sum(1 for g in gus if g.get("status") == "open"),
                     sum(1 for g in gus if g.get("status") == "resolved"))
        logger.info("API: LLM=%d calls, Search=%d, Fetch=%d",
                     cycle_llm_calls, cycle_search_calls, cycle_fetch_calls)

        # 매 사이클 State 저장
        save_state(state, output_path)

        # 수렴 체크
        critique = state.get("current_critique", {})
        convergence = critique.get("convergence", {})
        if convergence.get("converged"):
            logger.info("수렴 조건 달성 — 조기 종료.")
            break

    # 최종 요약
    summary = metrics_logger.summary()
    logger.info("=" * 60)
    logger.info("=== 벤치 실행 완료 ===")
    logger.info("총 사이클: %d", summary.get("total_cycles", 0))
    logger.info("KU 증가: %d", summary.get("ku_growth", 0))
    logger.info("GU resolved: %d", summary.get("gu_resolved_total", 0))
    logger.info("Jump cycles: %d", summary.get("jump_cycles", 0))
    logger.info("불변원칙 위반: %d회", invariant_violations)
    logger.info("총 LLM calls: %d (tokens: %d)",
                summary.get("total_llm_calls", 0),
                summary.get("total_llm_tokens", 0))
    logger.info("총 Search calls: %d, Fetch calls: %d",
                summary.get("total_search_calls", 0),
                summary.get("total_fetch_calls", 0))

    # Trajectory 저장
    traj_path = output_path / "trajectory"
    metrics_logger.save_json(traj_path / "trajectory.json")
    metrics_logger.save_csv(traj_path / "trajectory.csv")
    logger.info("Trajectory 저장: %s/", traj_path)
    logger.info("State 저장: %s/state/", output_path)


if __name__ == "__main__":
    main()
