"""Real API 1 Cycle 실행 스크립트.

Usage:
    set -a && source .env && set +a
    python scripts/run_one_cycle.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from src.adapters.llm_adapter import create_llm
from src.adapters.search_adapter import create_search_tool
from src.config import EvolverConfig
from src.graph import build_graph
from src.utils.state_io import load_state, save_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_one_cycle")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Evolver 1-Cycle Run")
    parser.add_argument("--bench-root", type=str, default=None,
                        help="Silver trial 직접 경로 (예: bench/silver/japan-travel/p0-20260411-baseline)")
    args = parser.parse_args()

    config = EvolverConfig.from_env()
    if args.bench_root:
        from src.config import OrchestratorConfig, EvolverConfig as EC
        orch = OrchestratorConfig(
            max_cycles=1,
            snapshot_every=config.orchestrator.snapshot_every,
            invariant_check=config.orchestrator.invariant_check,
            stop_on_convergence=config.orchestrator.stop_on_convergence,
            plateau_window=config.orchestrator.plateau_window,
            bench_domain=config.orchestrator.bench_domain,
            bench_path=config.orchestrator.bench_path,
            bench_root=args.bench_root,
        )
        config = EC(llm=config.llm, search=config.search, orchestrator=orch)
    config.validate_api_keys()

    logger.info("Config: model=%s, search=%s", config.llm.model, config.search.provider)

    # State 로드
    if config.orchestrator.bench_root:
        domain_path = Path(config.orchestrator.bench_root)
    else:
        domain_path = Path(config.orchestrator.bench_path) / config.orchestrator.bench_domain
    state = load_state(domain_path)
    logger.info(
        "State 로드: KU=%d, GU=%d, cycle=%d",
        len(state.get("knowledge_units", [])),
        len(state.get("gap_map", [])),
        state.get("current_cycle", 0),
    )

    # LLM + Search 생성
    llm = create_llm(config.llm)
    search_tool = create_search_tool(config.search)

    # Graph 빌드 + 실행
    graph = build_graph(llm=llm, search_tool=search_tool)
    logger.info("Graph 빌드 완료. 실행 시작...")

    final_state = graph.invoke(state, config={"recursion_limit": 50})

    # 결과 요약
    kus = final_state.get("knowledge_units", [])
    gus = final_state.get("gap_map", [])
    claims = final_state.get("current_claims", [])
    critique = final_state.get("current_critique", {})

    logger.info("=== 1 Cycle 완료 ===")
    logger.info("KU: %d (active=%d, disputed=%d)",
                len(kus),
                sum(1 for k in kus if k.get("status") == "active"),
                sum(1 for k in kus if k.get("status") == "disputed"))
    logger.info("GU: %d (open=%d, resolved=%d)",
                len(gus),
                sum(1 for g in gus if g.get("status") == "open"),
                sum(1 for g in gus if g.get("status") == "resolved"))
    logger.info("Claims: %d", len(claims))

    # API 호출 카운터
    if hasattr(llm, "call_count"):
        logger.info("LLM calls: %d (tokens: %d)", llm.call_count, getattr(llm, "total_tokens", 0))
    if hasattr(search_tool, "search_calls"):
        logger.info("Search calls: %d, Fetch calls: %d (total: %d)",
                     search_tool.search_calls, search_tool.fetch_calls, search_tool.total_calls)

    if critique:
        convergence = critique.get("convergence", {})
        logger.info("Critique convergence: %s", convergence.get("converged", False))
        prescriptions = critique.get("prescriptions", [])
        logger.info("Prescriptions: %d", len(prescriptions))

    # State 저장
    if config.orchestrator.bench_root:
        output_path = Path(config.orchestrator.bench_root)
    else:
        output_path = domain_path.parent / f"{domain_path.name}-auto"
    save_state(final_state, output_path)
    logger.info("State 저장: %s/state/", output_path)


if __name__ == "__main__":
    main()
