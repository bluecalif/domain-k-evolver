"""Readiness Gate 벤치마크 실행 + 3-Viewpoint 판정.

Phase 4 Stage D (Task 4.10).
japan-travel 15 Cycle 실행 → Readiness Gate 평가 → 보고서 출력.

Usage:
    set -a && source .env && set +a
    python scripts/run_readiness.py --cycles 15
    python scripts/run_readiness.py --evaluate-only   # 기존 결과로 Gate만 평가
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_readiness")


def _run_benchmark(cycles: int, resume: bool) -> tuple[dict, list[dict]]:
    """N Cycle 벤치마크 실행 → (final_state, trajectory)."""
    from src.adapters.llm_adapter import create_llm
    from src.adapters.search_adapter import create_search_tool
    from src.config import EvolverConfig, OrchestratorConfig
    from src.orchestrator import Orchestrator

    config = EvolverConfig.from_env()
    config.validate_api_keys()

    # 15 cycle 설정
    orch_cfg = OrchestratorConfig(
        max_cycles=cycles,
        snapshot_every=config.orchestrator.snapshot_every,
        invariant_check=config.orchestrator.invariant_check,
        stop_on_convergence=False,  # Gate 평가 위해 강제 실행
        plateau_window=config.orchestrator.plateau_window,
        audit_interval=5,
        bench_domain=config.orchestrator.bench_domain,
        bench_path=config.orchestrator.bench_path,
    )
    config = EvolverConfig(
        llm=config.llm, search=config.search, orchestrator=orch_cfg,
    )

    llm = create_llm(config.llm)
    search_tool = create_search_tool(config.search)

    orchestrator = Orchestrator(config, llm=llm, search_tool=search_tool)

    # Resume 지원
    from src.utils.state_io import load_state
    domain_path = Path(orch_cfg.bench_path) / orch_cfg.bench_domain
    output_path = domain_path.parent / f"{domain_path.name}-readiness"

    if resume and (output_path / "state").exists():
        initial_state = load_state(output_path)
        logger.info("Resume: readiness 결과에서 State 로드")
    else:
        initial_state = load_state(domain_path)

    results = orchestrator.run(initial_state)
    final_state = results[-1].state if results else initial_state

    # State + Trajectory 저장
    from src.utils.state_io import save_state
    save_state(final_state, output_path)
    trajectory = orchestrator.logger.entries
    orchestrator.logger.save_json(output_path / "trajectory" / "trajectory.json")
    orchestrator.logger.save_csv(output_path / "trajectory" / "trajectory.csv")

    return final_state, trajectory


def _load_existing_results() -> tuple[dict, list[dict]]:
    """기존 readiness 결과 로드."""
    from src.utils.state_io import load_state
    from src.config import EvolverConfig

    config = EvolverConfig.from_env()
    domain_path = Path(config.orchestrator.bench_path) / config.orchestrator.bench_domain
    output_path = domain_path.parent / f"{domain_path.name}-readiness"

    state = load_state(output_path)
    traj_path = output_path / "trajectory" / "trajectory.json"
    if traj_path.exists():
        trajectory = json.loads(traj_path.read_text(encoding="utf-8"))
    else:
        trajectory = []

    return state, trajectory


def _print_report(gate_result: dict) -> None:
    """Gate 판정 결과 보고서 출력."""
    verdict = gate_result["verdict"]
    print("\n" + "=" * 60)
    print(f"  READINESS GATE: {verdict}")
    print("=" * 60)

    for vp in gate_result["viewpoints"]:
        status = "PASS" if vp["passed"] else "FAIL"
        print(f"\n  [{status}] {vp['viewpoint']} ({vp['score']})")
        for name, criterion in vp["criteria"].items():
            mark = "O" if criterion["passed"] else "X"
            critical = " [CRITICAL]" if criterion.get("critical") and not criterion["passed"] else ""
            print(f"    [{mark}] {name}: {criterion['value']} (>= {criterion['threshold']}){critical}")

    if gate_result["failed_viewpoints"]:
        print(f"\n  Failed: {', '.join(gate_result['failed_viewpoints'])}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Readiness Gate Benchmark")
    parser.add_argument("--cycles", type=int, default=15)
    parser.add_argument("--evaluate-only", action="store_true",
                        help="기존 결과로 Gate만 평가 (API 호출 없음)")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if args.evaluate_only:
        logger.info("Evaluate-only 모드: 기존 결과 로드")
        state, trajectory = _load_existing_results()
    else:
        logger.info("벤치마크 실행: %d cycles", args.cycles)
        state, trajectory = _run_benchmark(args.cycles, args.resume)

    # Gate 평가
    from src.utils.readiness_gate import evaluate_readiness

    gate_result = evaluate_readiness(state, trajectory)

    _print_report(gate_result)

    # 결과 저장
    from src.config import EvolverConfig
    config = EvolverConfig.from_env()
    domain_path = Path(config.orchestrator.bench_path) / config.orchestrator.bench_domain
    output_path = domain_path.parent / f"{domain_path.name}-readiness"
    output_path.mkdir(parents=True, exist_ok=True)

    report_path = output_path / "readiness-report.json"
    report_path.write_text(
        json.dumps(gate_result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("보고서 저장: %s", report_path)

    sys.exit(0 if gate_result["gate_passed"] else 1)


if __name__ == "__main__":
    main()
