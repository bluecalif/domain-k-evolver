"""V-T1: p7-ab-on / p7-ab-off trial 의 Step A/B 신호 재파싱.

SI-P7 Step V 검증의 첫 단계. 기존 trial 데이터(telemetry + state-snapshots + run.log)에서
Step A/B 각 task 동작 증거를 cycle 별로 추출하여 ✓/✗/~ 재판정.

대상 신호:
- S1-T8: deferred_targets, defer_reason
- S2-T1: integration_result 분포 (metrics.json / cycle_trace)
- S2-T2: ku_stagnation_signals
- S2-T4 β: aggressive_mode_remaining
- S3-T2/T8: recent_conflict_fields (blocklist)
- S3-T7: adjacency_yield (rule 별 기여도)
- S4-T2: coverage_map.deficit_score

출력: stdout 요약표 + (옵션) JSON 덤프.

Usage:
    python scripts/analyze_p7_ab_signals.py
    python scripts/analyze_p7_ab_signals.py --trial p7-ab-on
    python scripts/analyze_p7_ab_signals.py --json-out signals.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

BENCH_ROOT = Path("bench/silver/japan-travel")
DEFAULT_TRIALS = ["p7-ab-on", "p7-ab-off"]

STATE_FIELDS = [
    "deferred_targets",
    "defer_reason",
    "ku_stagnation_signals",
    "aggressive_mode_remaining",
    "recent_conflict_fields",
    "adjacency_yield",
    "coverage_map",
]

LOG_KEYWORDS = [
    # S2-T4 β 활성화 흔적
    "aggressive",
    "aggressive_mode",
    # S2-T2 stagnation trigger — remodel 경로와 critique rx 형태 둘 다 커버
    "ku_stagnation",
    "growth_stagnation",
    "exploration_drought",
    "Remodel 트리거",
    # S2-T4 α
    "query_rewrite",
    # S5a 관련
    "entity_discovery",
    # S3-T1/T7
    "suppressed",
    "adjacency_yield",
    # S3-T2/T8
    "recent_conflict_fields",
    "conflict_blocklist",
    # S2-T5~T8
    "condition_split",
    "axis_tags",
    # integration result 분류
    "integration_result",
]


def load_telemetry(trial_dir: Path) -> list[dict]:
    path = trial_dir / "telemetry" / "cycles.jsonl"
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_cycle_metrics(trial_dir: Path, cycle: int) -> dict:
    path = trial_dir / "state-snapshots" / f"cycle-{cycle}-snapshot" / "metrics.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_cycle_gap_map(trial_dir: Path, cycle: int) -> list[dict]:
    path = trial_dir / "state-snapshots" / f"cycle-{cycle}-snapshot" / "gap-map.json"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("gus") or data.get("gaps") or []
    return []


def grep_log(trial_dir: Path, keywords: list[str]) -> dict[str, list[int]]:
    """run.log 의 각 keyword 가 등장한 줄 번호 list."""
    path = trial_dir / "run.log"
    hits: dict[str, list[int]] = {kw: [] for kw in keywords}
    if not path.exists():
        return hits
    with path.open(encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            for kw in keywords:
                if kw in line:
                    hits[kw].append(lineno)
    return hits


def extract_cycle_signals(tel: dict, metrics: dict, gu_list: list[dict]) -> dict:
    """cycle 단위 신호 추출. 부재 시 None 반환."""
    cycle_trace = tel.get("cycle_trace") or {}
    mode = tel.get("mode") or {}
    return {
        "cycle": tel.get("cycle"),
        "mode": mode.get("mode") if isinstance(mode, dict) else mode,
        "deferred_targets": tel.get("deferred_targets"),
        "defer_reason": tel.get("defer_reason"),
        "adjacent_gap_generated": cycle_trace.get("adjacent_gap_generated"),
        "target_count": cycle_trace.get("target_count"),
        "resolved_count": cycle_trace.get("resolved_count"),
        "concrete_count": cycle_trace.get("concrete_count"),
        "wildcard_count": cycle_trace.get("wildcard_count"),
        "ku_total": metrics.get("counts", {}).get("total_ku"),
        "gu_open": metrics.get("counts", {}).get("total_gu_open"),
        "gu_resolved": metrics.get("counts", {}).get("total_gu_resolved"),
        "conflict_rate": metrics.get("rates", {}).get("conflict_rate"),
        "gap_resolution_rate": metrics.get("rates", {}).get("gap_resolution_rate"),
        "gu_count_in_gap_map": len(gu_list),
        # 아래는 state-snapshot 에 없음 — V2 계측 필요
        "aggressive_mode_remaining": None,
        "ku_stagnation_signals": None,
        "recent_conflict_fields": None,
        "adjacency_yield": None,
        "coverage_map_deficit": None,
    }


def analyze_trial(trial_dir: Path) -> dict:
    trial_name = trial_dir.name
    print(f"\n=== {trial_name} ===")

    telemetry = load_telemetry(trial_dir)
    if not telemetry:
        print(f"  [!] telemetry/cycles.jsonl 없음")
        return {"trial": trial_name, "error": "no telemetry"}

    # telemetry 의 cycle 필드가 모두 0 으로 기록된 알려진 문제 — 순서 index 사용
    telemetry_cycle_buggy = all((t.get("cycle") or 0) == 0 for t in telemetry)

    cycle_signals: list[dict] = []
    for idx, tel in enumerate(telemetry, start=1):
        cycle = idx if telemetry_cycle_buggy else tel.get("cycle") or idx
        metrics = load_cycle_metrics(trial_dir, cycle)
        gu_list = load_cycle_gap_map(trial_dir, cycle)
        sig = extract_cycle_signals(tel, metrics, gu_list)
        sig["cycle"] = cycle  # overwrite with authoritative index
        cycle_signals.append(sig)

    log_hits = grep_log(trial_dir, LOG_KEYWORDS)

    print_cycle_table(cycle_signals)
    print_log_summary(log_hits)

    return {
        "trial": trial_name,
        "cycle_signals": cycle_signals,
        "log_keyword_hits": {k: len(v) for k, v in log_hits.items()},
    }


def print_cycle_table(rows: list[dict]) -> None:
    print("\n[A] Cycle × 신호 (telemetry + state-snapshots)")
    cols = [
        ("cycle", 3),
        ("mode", 8),
        ("ku", 4),
        ("gu_op", 5),
        ("gu_rs", 5),
        ("defer", 5),
        ("adj_gen", 7),
        ("tgt", 3),
        ("rslv", 4),
        ("cncr", 4),
        ("wild", 4),
        ("confl", 5),
        ("gap_res", 7),
    ]
    # header
    print("  " + " ".join(f"{name:>{w}}" for name, w in cols))
    for r in rows:
        vals = [
            r.get("cycle"),
            (r.get("mode") or "")[:8],
            r.get("ku_total"),
            r.get("gu_open"),
            r.get("gu_resolved"),
            r.get("deferred_targets"),
            r.get("adjacent_gap_generated"),
            r.get("target_count"),
            r.get("resolved_count"),
            r.get("concrete_count"),
            r.get("wildcard_count"),
            _fmt(r.get("conflict_rate")),
            _fmt(r.get("gap_resolution_rate")),
        ]
        print("  " + " ".join(f"{_s(v):>{w}}" for v, (_, w) in zip(vals, cols)))


def print_log_summary(hits: dict[str, list[int]]) -> None:
    print("\n[B] run.log keyword 발생 (라인 수)")
    for kw, lines in hits.items():
        n = len(lines)
        preview = ""
        if 0 < n <= 5:
            preview = f" — lines {lines}"
        elif n > 5:
            preview = f" — first 5 lines {lines[:5]}…"
        print(f"  {kw:30s} {n:>4}{preview}")


def print_verdict_matrix(results: list[dict]) -> None:
    print("\n[C] Step A/B 항목별 재판정 (V1 중간)")
    print("  기호: ✓ 확인 / ✗ 미발생 / ~ 계측 부재")
    print()

    # p7-ab-on 기준으로 요약
    target = next((r for r in results if r["trial"] == "p7-ab-on"), results[0])
    rows = target.get("cycle_signals", [])
    log_hits = target.get("log_keyword_hits", {})

    defer_observed = any((r.get("deferred_targets") or 0) > 0 for r in rows)
    defer_reason_observed = any(r.get("defer_reason") for r in rows)
    adj_gen_observed = any((r.get("adjacent_gap_generated") or 0) > 0 for r in rows)
    ku_stagnation_in_log = (
        log_hits.get("ku_stagnation", 0)
        + log_hits.get("growth_stagnation", 0)
        + log_hits.get("exploration_drought", 0)
    )
    aggressive_in_log = log_hits.get("aggressive", 0) + log_hits.get("aggressive_mode", 0)
    query_rewrite_in_log = log_hits.get("query_rewrite", 0)
    condition_split_in_log = log_hits.get("condition_split", 0)
    suppressed_in_log = log_hits.get("suppressed", 0)
    integration_result_in_log = log_hits.get("integration_result", 0)
    axis_tags_in_log = log_hits.get("axis_tags", 0)

    matrix = [
        ("S1-T4/T5/T8 defer mechanism",
         "✓" if defer_observed else "✗",
         f"deferred_targets>0 at least once: {defer_observed}"),
        ("S1-T8 defer_reason telemetry",
         "✓" if defer_reason_observed else "✗",
         f"defer_reason present: {defer_reason_observed}"),
        ("S2-T1 integration_result_dist (state-level)",
         "~",
         "state-snapshot 에 integration_result_dist 필드 부재 — V2 계측 필요"),
        ("S2-T2 ku_stagnation trigger (log)",
         "✓" if ku_stagnation_in_log > 0 else "~",
         f"run.log ku_stagnation 등장: {ku_stagnation_in_log}회"),
        ("S2-T4 α query_rewrite rx (log)",
         "✓" if query_rewrite_in_log > 0 else "✗",
         f"run.log query_rewrite: {query_rewrite_in_log}회"),
        ("S2-T4 β aggressive_mode_remaining",
         "✓" if aggressive_in_log > 0 else "✗",
         f"run.log aggressive: {aggressive_in_log}회 / state field 부재"),
        ("S2-T5~T8 condition_split",
         "✓" if condition_split_in_log > 0 else "~",
         f"run.log condition_split: {condition_split_in_log}회"),
        ("S3-T1 suppress threshold",
         "✓" if suppressed_in_log > 0 else "~",
         f"run.log suppressed: {suppressed_in_log}회 / state 부재"),
        ("S3-T2/T8 recent_conflict_fields",
         "~",
         "state-snapshot 에 필드 부재 — V2 계측 필요"),
        ("S3-T3~T6 adjacent rule engine (adj_gen)",
         "✓" if adj_gen_observed else "✗",
         f"adjacent_gap_generated>0: {adj_gen_observed}"),
        ("S3-T7 adjacency_yield tracker",
         "~",
         "state-snapshot 에 필드 부재 — V2 계측 필요"),
        ("S4-T2 coverage_map.deficit_score",
         "~",
         "state-snapshot 에 필드 부재 — V2 계측 필요"),
    ]
    for name, verdict, reason in matrix:
        print(f"  {verdict} {name:45s}  {reason}")


def _s(v) -> str:
    if v is None:
        return "-"
    return str(v)


def _fmt(v) -> str:
    if v is None:
        return "-"
    try:
        return f"{float(v):.2f}"
    except (TypeError, ValueError):
        return str(v)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial", action="append", help="trial name under bench/silver/japan-travel (can repeat)")
    parser.add_argument("--json-out", type=Path, help="optional: dump full result as JSON")
    args = parser.parse_args()

    trials = args.trial or DEFAULT_TRIALS
    results: list[dict] = []
    for name in trials:
        trial_dir = BENCH_ROOT / name
        if not trial_dir.exists():
            print(f"[skip] {trial_dir} 없음")
            continue
        results.append(analyze_trial(trial_dir))

    if any("cycle_signals" in r for r in results):
        print_verdict_matrix(results)

    if args.json_out:
        args.json_out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[saved] {args.json_out}")


if __name__ == "__main__":
    main()
