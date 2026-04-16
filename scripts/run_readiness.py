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
import dataclasses
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


def _run_benchmark(
    cycles: int, resume: bool, bench_root: str | None = None,
    audit_interval: int | None = None,
    external_anchor: bool | None = None,
) -> tuple[dict, list[dict]]:
    """N Cycle 벤치마크 실행 → (final_state, trajectory)."""
    from src.adapters.llm_adapter import create_llm
    from src.adapters.search_adapter import create_search_tool
    from src.config import EvolverConfig, OrchestratorConfig
    from src.orchestrator import Orchestrator

    config = EvolverConfig.from_env()
    config.validate_api_keys()

    # Stage E (External Anchor) 플래그 override
    if external_anchor is not None:
        ea_cfg = dataclasses.replace(config.external_anchor, enabled=external_anchor)
        config = dataclasses.replace(config, external_anchor=ea_cfg)
        logger.info("external_anchor=%s (flag override)", external_anchor)

    ai = audit_interval if audit_interval is not None else 5
    if bench_root:
        # Silver: --bench-root 직접 경로 사용
        orch_cfg = OrchestratorConfig(
            max_cycles=cycles,
            snapshot_every=config.orchestrator.snapshot_every,
            invariant_check=config.orchestrator.invariant_check,
            stop_on_convergence=False,
            plateau_window=0,
            audit_interval=ai,
            bench_domain=config.orchestrator.bench_domain,
            bench_path=config.orchestrator.bench_path,
            bench_root=bench_root,
        )
        output_path = Path(bench_root)
    else:
        # Legacy: {bench_domain}-readiness 경로
        orch_cfg = OrchestratorConfig(
            max_cycles=cycles,
            snapshot_every=config.orchestrator.snapshot_every,
            invariant_check=config.orchestrator.invariant_check,
            stop_on_convergence=False,
            plateau_window=0,
            audit_interval=ai,
            bench_domain=f"{config.orchestrator.bench_domain}-readiness",
            bench_path=config.orchestrator.bench_path,
        )
        output_path = Path(orch_cfg.bench_path) / orch_cfg.bench_domain

    config = EvolverConfig(
        llm=config.llm, search=config.search, orchestrator=orch_cfg,
        external_anchor=config.external_anchor,
    )

    llm = create_llm(config.llm)
    search_tool = create_search_tool(config.search)

    # Seed state 로드 (providers 생성 전에 skeleton 필요)
    from src.utils.state_io import load_state

    if resume and (output_path / "state").exists():
        initial_state = load_state(output_path)
        logger.info("Resume: readiness 결과에서 State 로드")
    elif bench_root:
        # Silver: bench-root 에 기존 state 가 있으면 사용, 없으면 원본 seed 에서
        orig_domain = config.orchestrator.bench_domain
        orig_path = Path(config.orchestrator.bench_path) / orig_domain
        seed_path = orig_path / "state-snapshots" / "cycle-0-snapshot"
        if seed_path.exists():
            initial_state = load_state(seed_path)
            initial_state["current_cycle"] = 0
            logger.info("Seed state 로드: %s (KU=%d, GU=%d)",
                         seed_path, len(initial_state.get("knowledge_units", [])),
                         len(initial_state.get("gap_map", [])))
        else:
            initial_state = load_state(orig_path)
    else:
        # Legacy: 원본 bench domain 에서 seed 로드
        orig_domain = orch_cfg.bench_domain.removesuffix("-readiness")
        orig_path = Path(orch_cfg.bench_path) / orig_domain
        seed_path = orig_path / "state-snapshots" / "cycle-0-snapshot"
        if seed_path.exists():
            initial_state = load_state(seed_path)
            initial_state["current_cycle"] = 0
            logger.info("Seed state 로드: %s (KU=%d, GU=%d)",
                         seed_path, len(initial_state.get("knowledge_units", [])),
                         len(initial_state.get("gap_map", [])))
        else:
            initial_state = load_state(orig_path)

    # SI-P3R: Tavily snippet-only 단일 경로
    orchestrator = Orchestrator(
        config, llm=llm, search_tool=search_tool,
    )

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
    if domain_path.name.endswith("-readiness"):
        output_path = domain_path
    else:
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
    parser.add_argument("--bench-root", type=str, default=None,
                        help="Silver trial 직접 경로 (예: bench/silver/japan-travel/p0-20260411-baseline)")
    parser.add_argument("--audit-interval", type=int, default=None,
                        help="audit_interval 오버라이드 (0=audit+remodel 비활성)")
    parser.add_argument("--external-anchor", dest="external_anchor",
                        action="store_true", default=None,
                        help="Stage E (External Anchor) 활성화. VP4 포함 평가.")
    parser.add_argument("--no-external-anchor", dest="external_anchor",
                        action="store_false",
                        help="Stage E 비활성화 (env override).")
    args = parser.parse_args()

    if args.evaluate_only:
        logger.info("Evaluate-only 모드: 기존 결과 로드")
        state, trajectory = _load_existing_results()
    else:
        logger.info("벤치마크 실행: %d cycles (audit_interval=%s, external_anchor=%s)",
                    args.cycles, args.audit_interval, args.external_anchor)
        state, trajectory = _run_benchmark(
            args.cycles, args.resume, args.bench_root, args.audit_interval,
            external_anchor=args.external_anchor,
        )

    # Gate 평가
    from src.config import EvolverConfig
    from src.utils.readiness_gate import evaluate_readiness

    _eval_cfg = EvolverConfig.from_env()
    if args.external_anchor is not None:
        ea_enabled = args.external_anchor
    else:
        ea_enabled = _eval_cfg.external_anchor.enabled

    gate_result = evaluate_readiness(
        state, trajectory, external_anchor_enabled=ea_enabled,
    )

    _print_report(gate_result)

    # 결과 저장
    if args.bench_root:
        output_path = Path(args.bench_root)
    else:
        domain_path = Path(_eval_cfg.orchestrator.bench_path) / _eval_cfg.orchestrator.bench_domain
        if domain_path.name.endswith("-readiness"):
            output_path = domain_path
        else:
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
