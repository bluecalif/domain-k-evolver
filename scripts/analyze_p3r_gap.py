"""P3R 15c trial 정적 분석 — gap_resolution 병목 조사 (D-126).

입력: bench/silver/japan-travel/p3r-gate-trial-15c/
출력:
  1. KU evidence_links 분포 (avg, histogram)
  2. GU resolved_by 매핑 검증 (resolved GU의 resolved_by 존재/형식)
  3. cycle별 target/resolve 비교 (trajectory 기반)

사용:
  python scripts/analyze_p3r_gap.py [--trial PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


DEFAULT_TRIAL = "bench/silver/japan-travel/p3r-gate-trial-15c"


def _load(path: Path) -> object:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def analyze_evidence_distribution(kus: list[dict]) -> dict:
    counts = [len(ku.get("evidence_links", [])) for ku in kus]
    active_counts = [
        len(ku.get("evidence_links", []))
        for ku in kus
        if ku.get("status") == "active"
    ]
    hist = Counter(counts)
    return {
        "ku_total": len(kus),
        "ku_active": len(active_counts),
        "avg_evidence_all": round(sum(counts) / len(counts), 3) if counts else 0,
        "avg_evidence_active": round(sum(active_counts) / len(active_counts), 3) if active_counts else 0,
        "histogram": dict(sorted(hist.items())),
        "zero_evidence_count": hist.get(0, 0),
    }


def analyze_gu_resolution(gap_map: list[dict]) -> dict:
    total = len(gap_map)
    by_status = Counter(gu.get("status", "?") for gu in gap_map)
    resolved = [gu for gu in gap_map if gu.get("status") == "resolved"]

    missing_resolved_by = 0
    invalid_resolved_by = 0
    valid_resolved_by = 0
    for gu in resolved:
        rb = gu.get("resolved_by", "")
        if not rb:
            missing_resolved_by += 1
        elif not isinstance(rb, str) or not rb.startswith("CL-"):
            invalid_resolved_by += 1
        else:
            valid_resolved_by += 1

    open_gus = [gu for gu in gap_map if gu.get("status") == "open"]
    open_by_type = Counter(gu.get("gap_type", "?") for gu in open_gus)

    return {
        "gu_total": total,
        "by_status": dict(by_status),
        "resolved_breakdown": {
            "valid_resolved_by": valid_resolved_by,
            "missing_resolved_by": missing_resolved_by,
            "invalid_resolved_by": invalid_resolved_by,
        },
        "open_by_gap_type": dict(open_by_type),
    }


def analyze_cycle_conversion(trajectory: list[dict]) -> dict:
    rows = []
    prev_resolved = 0
    for row in trajectory:
        cycle = row.get("cycle")
        gu_open = row.get("gu_open", 0)
        gu_resolved = row.get("gu_resolved", 0)
        delta_resolved = gu_resolved - prev_resolved
        rows.append({
            "cycle": cycle,
            "mode": row.get("mode", ""),
            "gu_open": gu_open,
            "gu_resolved_cum": gu_resolved,
            "resolved_this_cycle": delta_resolved,
            "gap_resolution_rate": row.get("gap_resolution_rate"),
            "llm_calls": row.get("llm_calls"),
        })
        prev_resolved = gu_resolved

    total_resolved = rows[-1]["gu_resolved_cum"] if rows else 0
    return {
        "cycles": len(rows),
        "final_gap_resolution_rate": trajectory[-1].get("gap_resolution_rate") if trajectory else None,
        "final_gu_open": trajectory[-1].get("gu_open") if trajectory else None,
        "final_gu_resolved": total_resolved,
        "per_cycle": rows,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--trial", default=DEFAULT_TRIAL)
    args = p.parse_args()

    trial = Path(args.trial)
    state = trial / "state"
    traj = trial / "trajectory" / "trajectory.json"

    if not state.is_dir() or not traj.exists():
        print(f"ERROR: invalid trial path {trial}", file=sys.stderr)
        return 1

    kus = _load(state / "knowledge-units.json")
    gap_map = _load(state / "gap-map.json")
    trajectory = _load(traj)

    report = {
        "trial": str(trial),
        "evidence": analyze_evidence_distribution(kus),
        "gu_resolution": analyze_gu_resolution(gap_map),
        "cycle_conversion": analyze_cycle_conversion(trajectory),
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
