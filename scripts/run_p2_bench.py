"""P2 Remodel 실 벤치 trial — remodel off/on 비교.

Before (remodel off, audit_interval=0) vs After (remodel on, audit_interval=5)
각 10 cycle 실행 → metrics 비교.

Usage:
    set -a && source .env && set +a
    python scripts/run_p2_bench.py
    python scripts/run_p2_bench.py --cycles 10
    python scripts/run_p2_bench.py --compare-only   # 기실행 결과만 비교
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRIAL_BASE = ROOT / "bench" / "silver" / "japan-travel"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_p2_bench")


def _extract_metrics(trial_dir: Path) -> dict:
    """trial 결과에서 핵심 metrics 추출."""
    state_dir = trial_dir / "state"
    metrics = {}

    # KU count + status 분포
    ku_path = state_dir / "knowledge-units.json"
    if ku_path.exists():
        kus = json.loads(ku_path.read_text(encoding="utf-8"))
        metrics["ku_total"] = len(kus)
        metrics["ku_active"] = sum(1 for k in kus if k.get("status") == "active")
        metrics["ku_disputed"] = sum(1 for k in kus if k.get("status") == "disputed")
        # entity_key 고유 수
        entity_keys = {k.get("entity_key", "") for k in kus}
        metrics["entity_count"] = len(entity_keys)
        # category 분포
        categories = {}
        for k in kus:
            cat = k.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        metrics["categories"] = categories
        metrics["category_count"] = len(categories)
        # 평균 confidence
        confs = [k.get("confidence", 0) for k in kus if k.get("confidence") is not None]
        metrics["avg_confidence"] = round(sum(confs) / len(confs), 3) if confs else 0
    else:
        metrics["ku_total"] = 0

    # GU count
    gu_path = state_dir / "gap-map.json"
    if gu_path.exists():
        gus = json.loads(gu_path.read_text(encoding="utf-8"))
        metrics["gu_total"] = len(gus)
        metrics["gu_open"] = sum(1 for g in gus if g.get("status") == "open")
    else:
        metrics["gu_total"] = 0

    # Metrics (conflict_rate, coverage 등)
    metrics_path = state_dir / "metrics.json"
    if metrics_path.exists():
        m = json.loads(metrics_path.read_text(encoding="utf-8"))
        metrics["conflict_rate"] = m.get("conflict_rate", 0)
        metrics["coverage"] = m.get("coverage", 0)
        metrics["evidence_ratio"] = m.get("evidence_ratio", 0)
        metrics["staleness"] = m.get("staleness", 0)

    # Remodel report (on case)
    remodel_path = state_dir / "remodel-report.json"
    if remodel_path.exists():
        report = json.loads(remodel_path.read_text(encoding="utf-8"))
        metrics["remodel_proposals"] = len(report.get("proposals", []))
        metrics["remodel_types"] = [p.get("type") for p in report.get("proposals", [])]
    else:
        # state 내 remodel_report 확인
        metrics["remodel_proposals"] = 0

    # Trajectory (LLM calls, cycle count)
    traj_path = trial_dir / "trajectory" / "trajectory.json"
    if traj_path.exists():
        traj = json.loads(traj_path.read_text(encoding="utf-8"))
        metrics["cycles_run"] = len(traj)
        metrics["total_llm_calls"] = sum(e.get("llm_calls", 0) for e in traj)
    else:
        metrics["cycles_run"] = 0

    return metrics


def _run_trial(label: str, trial_dir: Path, cycles: int, audit_interval: int) -> None:
    """run_readiness.py 를 subprocess 로 실행."""
    logger.info("=== %s 실행 시작 (cycles=%d, audit_interval=%d) ===", label, cycles, audit_interval)

    cmd = [
        sys.executable, str(ROOT / "scripts" / "run_readiness.py"),
        "--cycles", str(cycles),
        "--bench-root", str(trial_dir),
        "--audit-interval", str(audit_interval),
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8",
        cwd=str(ROOT), timeout=600,
    )

    # 로그 출력
    if result.stdout:
        for line in result.stdout.strip().split("\n")[-20:]:
            logger.info("[%s stdout] %s", label, line)
    if result.stderr:
        for line in result.stderr.strip().split("\n")[-20:]:
            logger.info("[%s stderr] %s", label, line)

    if result.returncode != 0:
        logger.warning("%s 종료 코드: %d (Gate FAIL 시 정상)", label, result.returncode)


def _print_comparison(off_metrics: dict, on_metrics: dict) -> str:
    """Before/After 비교표 출력 + 문자열 반환."""
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("  P2 REMODEL BENCH — BEFORE (off) vs AFTER (on)")
    lines.append("=" * 70)

    rows = [
        ("KU total", "ku_total"),
        ("KU active", "ku_active"),
        ("KU disputed", "ku_disputed"),
        ("Entity count", "entity_count"),
        ("Category count", "category_count"),
        ("Avg confidence", "avg_confidence"),
        ("GU total", "gu_total"),
        ("GU open", "gu_open"),
        ("Conflict rate", "conflict_rate"),
        ("Coverage", "coverage"),
        ("Evidence ratio", "evidence_ratio"),
        ("Staleness", "staleness"),
        ("Cycles run", "cycles_run"),
        ("LLM calls", "total_llm_calls"),
        ("Remodel proposals", "remodel_proposals"),
    ]

    lines.append(f"  {'Metric':<20} {'OFF':>12} {'ON':>12} {'Delta':>12}")
    lines.append(f"  {'-'*20} {'-'*12} {'-'*12} {'-'*12}")

    for label, key in rows:
        off_val = off_metrics.get(key, "N/A")
        on_val = on_metrics.get(key, "N/A")
        if isinstance(off_val, (int, float)) and isinstance(on_val, (int, float)):
            delta = on_val - off_val
            delta_str = f"{delta:+.3f}" if isinstance(delta, float) else f"{delta:+d}"
        else:
            delta_str = ""
        lines.append(f"  {label:<20} {str(off_val):>12} {str(on_val):>12} {delta_str:>12}")

    # Remodel types
    if on_metrics.get("remodel_types"):
        lines.append(f"\n  Remodel types: {', '.join(on_metrics['remodel_types'])}")

    # Category 분포
    for label, m in [("OFF", off_metrics), ("ON", on_metrics)]:
        cats = m.get("categories", {})
        if cats:
            cat_str = ", ".join(f"{k}:{v}" for k, v in sorted(cats.items()))
            lines.append(f"  Categories ({label}): {cat_str}")

    lines.append("=" * 70)

    output = "\n".join(lines)
    print(output)
    return output


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="P2 Remodel Bench — off/on 비교")
    parser.add_argument("--cycles", type=int, default=10)
    parser.add_argument("--compare-only", action="store_true",
                        help="기실행 결과만 비교 (API 호출 없음)")
    args = parser.parse_args()

    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    off_dir = TRIAL_BASE / f"p2-{today}-remodel-off"
    on_dir = TRIAL_BASE / f"p2-{today}-remodel-on"

    if not args.compare_only:
        # 1. Remodel OFF (audit_interval=0)
        _run_trial("REMODEL-OFF", off_dir, args.cycles, audit_interval=0)

        # 2. Remodel ON (audit_interval=5)
        _run_trial("REMODEL-ON", on_dir, args.cycles, audit_interval=5)

    # 3. 비교
    if not (off_dir / "state").exists():
        logger.error("OFF trial 결과 없음: %s", off_dir)
        sys.exit(1)
    if not (on_dir / "state").exists():
        logger.error("ON trial 결과 없음: %s", on_dir)
        sys.exit(1)

    off_metrics = _extract_metrics(off_dir)
    on_metrics = _extract_metrics(on_dir)

    comparison = _print_comparison(off_metrics, on_metrics)

    # 비교 결과 저장
    result = {
        "trial_id": f"p2-{today}-remodel",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cycles": args.cycles,
        "off": off_metrics,
        "on": on_metrics,
        "comparison_text": comparison,
    }

    # 기존 trial 디렉토리에 저장
    parent_trial = TRIAL_BASE / "p2-20260412-remodel"
    parent_trial.mkdir(parents=True, exist_ok=True)
    result_path = parent_trial / "bench-comparison.json"
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("비교 결과 저장: %s", result_path)


if __name__ == "__main__":
    main()
