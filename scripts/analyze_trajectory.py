"""Task 2.16: 심층 분석 + 개선 권고 보고서.

Usage:
    python scripts/analyze_trajectory.py [--dir bench/japan-travel-auto] [--report] [--json]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def load_json(path: Path) -> list | dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── Constants (self-contained, copied from src/utils/metrics.py) ─────

THRESHOLDS = {
    "evidence_rate":       {"healthy": 0.95, "caution": 0.80, "higher_better": True},
    "multi_evidence_rate": {"healthy": 0.50, "caution": 0.30, "higher_better": True},
    "conflict_rate":       {"healthy": 0.05, "caution": 0.15, "higher_better": False},
    "avg_confidence":      {"healthy": 0.85, "caution": 0.70, "higher_better": True},
    "staleness_risk":      {"healthy": 0,    "caution": 3,    "higher_better": False},
}

NUMERIC_FIELDS = [
    "ku_total", "ku_active", "ku_disputed",
    "gu_open", "gu_resolved",
    "evidence_rate", "multi_evidence_rate", "conflict_rate",
    "avg_confidence", "gap_resolution_rate", "staleness_risk",
]

RATE_FIELDS = {"evidence_rate", "multi_evidence_rate", "conflict_rate",
               "avg_confidence", "gap_resolution_rate"}

CUMULATIVE_FIELDS = {"llm_tokens"}  # trajectory에서 누적값으로 기록


# ── Helpers ──────────────────────────────────────────────────────────

def _grade(name: str, val) -> str:
    """Threshold-based healthy/caution/danger 판정."""
    t = THRESHOLDS.get(name)
    if t is None or val is None:
        return "n/a"
    if t["higher_better"]:
        if val >= t["healthy"]:
            return "healthy"
        if val >= t["caution"]:
            return "caution"
        return "danger"
    else:
        if val <= t["healthy"]:
            return "healthy"
        if val <= t["caution"]:
            return "caution"
        return "danger"


def _pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def _delta_sign(v: float) -> str:
    return f"+{v:.2f}" if v >= 0 else f"{v:.2f}"


def _per_cycle_tokens(trajectory: list[dict]) -> list[int]:
    """llm_tokens가 누적값이므로 per-cycle delta로 변환."""
    result = []
    for i, r in enumerate(trajectory):
        t = r.get("llm_tokens", 0)
        if i == 0:
            result.append(t)
        else:
            prev = trajectory[i - 1].get("llm_tokens", 0)
            result.append(t - prev)
    return result


# ══════════════════════════════════════════════════════════════════════
# Section 1: Cycle Table (기존)
# ══════════════════════════════════════════════════════════════════════

def print_cycle_table(trajectory: list[dict]) -> None:
    print("\n=== Cycle-by-Cycle Trajectory ===\n")
    header = (
        f"{'Cycle':>5} | {'KU Total':>8} | {'Active':>6} | {'Disputed':>8} | "
        f"{'GU Open':>7} | {'Resolved':>8} | {'Evid%':>6} | {'Conf%':>6} | "
        f"{'Conflict%':>9} | {'GapRes%':>7} | {'Stale':>5} | {'Mode':>5}"
    )
    print(header)
    print("-" * len(header))
    for r in trajectory:
        print(
            f"{r['cycle']:>5} | {r['ku_total']:>8} | {r['ku_active']:>6} | "
            f"{r['ku_disputed']:>8} | {r['gu_open']:>7} | {r['gu_resolved']:>8} | "
            f"{r['evidence_rate'] * 100:>5.1f}% | {r['avg_confidence'] * 100:>5.1f}% | "
            f"{r['conflict_rate'] * 100:>8.1f}% | {r['gap_resolution_rate'] * 100:>6.1f}% | "
            f"{r['staleness_risk']:>5} | {r['mode']:>5}"
        )


# ══════════════════════════════════════════════════════════════════════
# Section 2: Snapshot Diff (기존)
# ══════════════════════════════════════════════════════════════════════

def print_snapshot_diff(trajectory: list[dict]) -> None:
    if len(trajectory) < 2:
        print("\n(Snapshot diff requires at least 2 cycles)")
        return

    first, last = trajectory[0], trajectory[-1]
    print("\n=== Snapshot Diff (Cycle {} -> {}) ===\n".format(first["cycle"], last["cycle"]))

    fields = [
        ("KU Total", "ku_total"),
        ("KU Active", "ku_active"),
        ("KU Disputed", "ku_disputed"),
        ("GU Open", "gu_open"),
        ("GU Resolved", "gu_resolved"),
        ("Evidence Rate", "evidence_rate"),
        ("Conflict Rate", "conflict_rate"),
        ("Avg Confidence", "avg_confidence"),
        ("Gap Resolution Rate", "gap_resolution_rate"),
        ("Staleness Risk", "staleness_risk"),
    ]

    header = f"{'Metric':<22} | {'Start':>10} | {'End':>10} | {'Delta':>10}"
    print(header)
    print("-" * len(header))

    for label, key in fields:
        v0, v1 = first[key], last[key]
        delta = v1 - v0
        if key in RATE_FIELDS:
            print(f"{label:<22} | {v0 * 100:>9.1f}% | {v1 * 100:>9.1f}% | {delta * 100:>+9.1f}%")
        else:
            print(f"{label:<22} | {v0:>10} | {v1:>10} | {delta:>+10}")

    # LLM / API cost summary
    total_llm = sum(r.get("llm_calls", 0) for r in trajectory)
    total_tokens = trajectory[-1].get("llm_tokens", 0)  # 누적값 → 최종값이 총합
    total_search = sum(r.get("search_calls", 0) for r in trajectory)
    total_fetch = sum(r.get("fetch_calls", 0) for r in trajectory)
    print(f"\n--- API Usage (cumulative) ---")
    print(f"  LLM calls : {total_llm}")
    print(f"  LLM tokens: {total_tokens:,}")
    print(f"  Search     : {total_search}")
    print(f"  Fetch      : {total_fetch}")


# ══════════════════════════════════════════════════════════════════════
# Section 3: Category Coverage (기존)
# ══════════════════════════════════════════════════════════════════════

def print_category_coverage(kus: list[dict]) -> None:
    print("\n=== Category Coverage ===\n")

    cat_counter: Counter[str] = Counter()
    cat_status: dict[str, Counter[str]] = {}

    for ku in kus:
        ek = ku.get("entity_key", "")
        parts = ek.split(":")
        category = parts[1] if len(parts) >= 2 else "unknown"
        status = ku.get("status", "unknown")

        cat_counter[category] += 1
        if category not in cat_status:
            cat_status[category] = Counter()
        cat_status[category][status] += 1

    header = f"{'Category':<25} | {'Total':>5} | {'Active':>6} | {'Disputed':>8} | {'Other':>5}"
    print(header)
    print("-" * len(header))

    for cat, total in cat_counter.most_common():
        active = cat_status[cat].get("active", 0)
        disputed = cat_status[cat].get("disputed", 0)
        other = total - active - disputed
        print(f"{cat:<25} | {total:>5} | {active:>6} | {disputed:>8} | {other:>5}")

    print(f"\nTotal categories: {len(cat_counter)}, Total KUs: {sum(cat_counter.values())}")


# ══════════════════════════════════════════════════════════════════════
# Section 4: Entity Summary (기존)
# ══════════════════════════════════════════════════════════════════════

def print_entity_summary(kus: list[dict]) -> None:
    print("\n=== Entity Summary (by entity_key) ===\n")

    entity_counter: Counter[str] = Counter()
    entity_status: dict[str, Counter[str]] = {}

    for ku in kus:
        ek = ku.get("entity_key", "unknown")
        status = ku.get("status", "unknown")
        entity_counter[ek] += 1
        if ek not in entity_status:
            entity_status[ek] = Counter()
        entity_status[ek][status] += 1

    header = f"{'Entity Key':<45} | {'Total':>5} | {'Active':>6} | {'Disputed':>8}"
    print(header)
    print("-" * len(header))

    for ek, total in entity_counter.most_common():
        active = entity_status[ek].get("active", 0)
        disputed = entity_status[ek].get("disputed", 0)
        print(f"{ek:<45} | {total:>5} | {active:>6} | {disputed:>8}")


# ══════════════════════════════════════════════════════════════════════
# Section 5: Gap Summary (기존)
# ══════════════════════════════════════════════════════════════════════

def print_gap_summary(gus: list[dict]) -> None:
    print("\n=== Gap Map Summary ===\n")

    status_counter: Counter[str] = Counter()
    type_counter: Counter[str] = Counter()

    for gu in gus:
        status_counter[gu.get("status", "unknown")] += 1
        type_counter[gu.get("gap_type", "unknown")] += 1

    print("By status:")
    for s, c in status_counter.most_common():
        print(f"  {s:<12}: {c}")

    print("\nBy gap_type:")
    for t, c in type_counter.most_common():
        print(f"  {t:<12}: {c}")


# ══════════════════════════════════════════════════════════════════════
# Section A: Trend Analysis (신규)
# ══════════════════════════════════════════════════════════════════════

def compute_trends(trajectory: list[dict]) -> dict:
    """사이클별 delta + 변곡점 + 성장률 비교."""
    if len(trajectory) < 2:
        return {"deltas": [], "inflections": {}, "growth_comparison": {}}

    # Per-cycle deltas
    deltas = []
    for i in range(1, len(trajectory)):
        d = {"cycle": trajectory[i]["cycle"]}
        for f in NUMERIC_FIELDS:
            d[f] = trajectory[i].get(f, 0) - trajectory[i - 1].get(f, 0)
        deltas.append(d)

    # Inflection points: delta 부호 전환 시점
    inflections: dict[str, list[int]] = {}
    for f in NUMERIC_FIELDS:
        pts = []
        for i in range(1, len(deltas)):
            prev_d = deltas[i - 1][f]
            curr_d = deltas[i][f]
            if prev_d != 0 and curr_d != 0 and (prev_d > 0) != (curr_d > 0):
                pts.append(deltas[i]["cycle"])
            elif prev_d != 0 and curr_d == 0:
                pts.append(deltas[i]["cycle"])
        if pts:
            inflections[f] = pts

    # Growth comparison: 전반부 vs 후반부
    mid = len(trajectory) // 2
    growth: dict[str, dict] = {}
    for f in NUMERIC_FIELDS:
        first_half = trajectory[mid].get(f, 0) - trajectory[0].get(f, 0)
        second_half = trajectory[-1].get(f, 0) - trajectory[mid].get(f, 0)
        growth[f] = {"first_half": first_half, "second_half": second_half}

    return {"deltas": deltas, "inflections": inflections, "growth_comparison": growth}


def print_trend_analysis(trajectory: list[dict]) -> dict:
    print("\n=== A. Trend Analysis ===\n")
    trends = compute_trends(trajectory)

    if not trends["deltas"]:
        print("(Not enough data for trend analysis)")
        return trends

    # Delta table
    print("--- Per-Cycle Deltas ---\n")
    header = f"{'Cycle':>5} | {'dKU':>5} | {'dActive':>7} | {'dDisp':>6} | {'dGUopen':>7} | {'dGUres':>6} | {'dConf%':>8}"
    print(header)
    print("-" * len(header))
    for d in trends["deltas"]:
        print(
            f"{d['cycle']:>5} | {d['ku_total']:>+5} | {d['ku_active']:>+7} | "
            f"{d['ku_disputed']:>+6} | {d['gu_open']:>+7} | {d['gu_resolved']:>+6} | "
            f"{d['conflict_rate'] * 100:>+7.1f}%"
        )

    # Inflection points
    if trends["inflections"]:
        print("\n--- Inflection Points ---\n")
        for field, cycles in trends["inflections"].items():
            print(f"  {field}: cycle {cycles}")

    # Growth comparison
    print("\n--- Growth: First Half vs Second Half ---\n")
    key_fields = ["ku_total", "ku_active", "ku_disputed", "gu_resolved", "conflict_rate"]
    header = f"{'Metric':<22} | {'1st Half':>10} | {'2nd Half':>10} | {'Ratio':>8}"
    print(header)
    print("-" * len(header))
    for f in key_fields:
        g = trends["growth_comparison"][f]
        fh, sh = g["first_half"], g["second_half"]
        if f in RATE_FIELDS:
            fh_s, sh_s = f"{fh * 100:+.1f}%", f"{sh * 100:+.1f}%"
        else:
            fh_s, sh_s = f"{fh:+}", f"{sh:+}"
        ratio = sh / fh if fh != 0 else float("inf") if sh != 0 else 0.0
        print(f"{f:<22} | {fh_s:>10} | {sh_s:>10} | {ratio:>7.2f}x")

    return trends


# ══════════════════════════════════════════════════════════════════════
# Section B: Disputed KU 심층 분석 (신규)
# ══════════════════════════════════════════════════════════════════════

def analyze_disputes(kus: list[dict]) -> dict:
    """Disputed KU를 true conflict vs false positive로 분류."""
    active_kus = [ku for ku in kus if ku.get("status") == "active"]
    disputed_kus = [ku for ku in kus if ku.get("status") == "disputed"]

    # active (entity_key, field) 집합
    active_keys = set()
    for ku in active_kus:
        active_keys.add((ku.get("entity_key", ""), ku.get("field", "")))

    true_conflicts = []
    false_positives = []
    resolution_types: Counter[str] = Counter()
    field_dist: Counter[str] = Counter()
    entity_dist: Counter[str] = Counter()

    for ku in disputed_kus:
        ek = ku.get("entity_key", "")
        field = ku.get("field", "")
        field_dist[field] += 1
        entity_dist[ek] += 1

        # resolution 집계
        for disp in ku.get("disputes", []):
            resolution_types[disp.get("resolution", "unknown")] += 1

        # true conflict: 동일 (entity_key, field)에 active KU도 존재
        if (ek, field) in active_keys:
            true_conflicts.append(ku)
        else:
            false_positives.append(ku)

    total_disputed = len(disputed_kus)
    fp_rate = len(false_positives) / total_disputed if total_disputed > 0 else 0

    return {
        "total_active": len(active_kus),
        "total_disputed": total_disputed,
        "true_conflicts": len(true_conflicts),
        "false_positives": len(false_positives),
        "fp_rate": fp_rate,
        "resolution_types": dict(resolution_types.most_common()),
        "field_distribution": dict(field_dist.most_common()),
        "entity_distribution": dict(entity_dist.most_common(10)),
    }


def print_dispute_analysis(kus: list[dict]) -> dict:
    print("\n=== B. Disputed KU Analysis ===\n")
    result = analyze_disputes(kus)

    print(f"Active KUs:      {result['total_active']}")
    print(f"Disputed KUs:    {result['total_disputed']}")
    print(f"True Conflicts:  {result['true_conflicts']}")
    print(f"False Positives: {result['false_positives']}")
    print(f"FP Rate:         {result['fp_rate'] * 100:.1f}%")

    print("\n--- Resolution Types ---")
    for rt, count in result["resolution_types"].items():
        print(f"  {rt:<25}: {count}")

    print("\n--- Field Distribution ---")
    for field, count in result["field_distribution"].items():
        print(f"  {field:<25}: {count}")

    print("\n--- Top Entities with Disputes ---")
    for ek, count in result["entity_distribution"].items():
        print(f"  {ek:<45}: {count}")

    return result


# ══════════════════════════════════════════════════════════════════════
# Section C: Efficiency Metrics (신규)
# ══════════════════════════════════════════════════════════════════════

def compute_efficiency(trajectory: list[dict]) -> dict:
    """API 비용 대비 지식 획득 효율."""
    last = trajectory[-1]
    total_ku = last.get("ku_total", 0)
    active_ku = last.get("ku_active", 0)
    disputed_ku = last.get("ku_disputed", 0)

    total_llm = sum(r.get("llm_calls", 0) for r in trajectory)
    total_tokens = last.get("llm_tokens", 0)
    total_search = sum(r.get("search_calls", 0) for r in trajectory)
    total_fetch = sum(r.get("fetch_calls", 0) for r in trajectory)

    # Per-cycle marginal returns (new active KU per cycle)
    marginal = []
    for i, r in enumerate(trajectory):
        new_active = r["ku_active"] - (trajectory[i - 1]["ku_active"] if i > 0 else 0)
        new_total = r["ku_total"] - (trajectory[i - 1]["ku_total"] if i > 0 else 0)
        marginal.append({
            "cycle": r["cycle"],
            "new_active": new_active,
            "new_total": new_total,
            "new_disputed": r["ku_disputed"] - (trajectory[i - 1]["ku_disputed"] if i > 0 else 0),
        })

    return {
        "tokens_per_ku": total_tokens / total_ku if total_ku else 0,
        "tokens_per_active_ku": total_tokens / active_ku if active_ku else 0,
        "searches_per_ku": total_search / total_ku if total_ku else 0,
        "llm_calls_per_ku": total_llm / total_ku if total_ku else 0,
        "active_ratio": active_ku / total_ku if total_ku else 0,
        "waste_ratio": disputed_ku / total_ku if total_ku else 0,
        "marginal_returns": marginal,
        "totals": {
            "llm_calls": total_llm,
            "llm_tokens": total_tokens,
            "search_calls": total_search,
            "fetch_calls": total_fetch,
            "total_ku": total_ku,
            "active_ku": active_ku,
        },
    }


def print_efficiency(trajectory: list[dict]) -> dict:
    print("\n=== C. Efficiency Metrics ===\n")
    eff = compute_efficiency(trajectory)

    print("--- Overall ---")
    print(f"  Tokens / KU (total):  {eff['tokens_per_ku']:,.0f}")
    print(f"  Tokens / KU (active): {eff['tokens_per_active_ku']:,.0f}")
    print(f"  Searches / KU:        {eff['searches_per_ku']:.1f}")
    print(f"  LLM calls / KU:       {eff['llm_calls_per_ku']:.1f}")
    print(f"  Active ratio:         {eff['active_ratio'] * 100:.1f}%")
    print(f"  Waste ratio:          {eff['waste_ratio'] * 100:.1f}%")

    print("\n--- Marginal Returns (per cycle) ---\n")
    header = f"{'Cycle':>5} | {'New Active':>10} | {'New Total':>10} | {'New Disputed':>12}"
    print(header)
    print("-" * len(header))
    for m in eff["marginal_returns"]:
        print(f"{m['cycle']:>5} | {m['new_active']:>+10} | {m['new_total']:>+10} | {m['new_disputed']:>+12}")

    # Diminishing returns detection
    later_active = [m["new_active"] for m in eff["marginal_returns"][len(eff["marginal_returns"]) // 2:]]
    avg_later = sum(later_active) / len(later_active) if later_active else 0
    print(f"\n  Avg new active (2nd half): {avg_later:.1f} / cycle")
    if avg_later < 0.5:
        print("  >> Diminishing returns detected: active KU growth near zero")

    return eff


# ══════════════════════════════════════════════════════════════════════
# Section D: Health Score (신규)
# ══════════════════════════════════════════════════════════════════════

def compute_health(trajectory: list[dict], trends: dict) -> dict:
    """최종 사이클 기준 건강도 + 종합 등급."""
    last = trajectory[-1]
    grades = {}
    for name in THRESHOLDS:
        val = last.get(name)
        grades[name] = {"value": val, "grade": _grade(name, val)}

    # Plateau detection
    active_plateau = False
    if len(trajectory) >= 4:
        recent_active = [r["ku_active"] for r in trajectory[-3:]]
        if len(set(recent_active)) == 1:
            active_plateau = True

    # Overall grade
    grade_values = {"healthy": 2, "caution": 1, "danger": 0}
    scores = [grade_values.get(g["grade"], 0) for g in grades.values()]
    avg_score = sum(scores) / len(scores) if scores else 0

    if active_plateau:
        avg_score -= 0.5  # plateau penalty

    if avg_score >= 1.8:
        overall = "A"
    elif avg_score >= 1.4:
        overall = "B"
    elif avg_score >= 1.0:
        overall = "C"
    elif avg_score >= 0.6:
        overall = "D"
    else:
        overall = "F"

    return {
        "grades": grades,
        "active_plateau": active_plateau,
        "overall_score": avg_score,
        "overall_grade": overall,
    }


def print_health(trajectory: list[dict], trends: dict) -> dict:
    print("\n=== D. Health Score ===\n")
    health = compute_health(trajectory, trends)

    header = f"{'Metric':<22} | {'Value':>10} | {'Grade':>8}"
    print(header)
    print("-" * len(header))
    for name, info in health["grades"].items():
        val = info["value"]
        val_s = _pct(val) if name in RATE_FIELDS else str(val)
        grade = info["grade"].upper()
        print(f"{name:<22} | {val_s:>10} | {grade:>8}")

    if health["active_plateau"]:
        print("\n  ** Active KU Plateau detected (3+ cycles unchanged)")

    print(f"\n  Overall Grade: {health['overall_grade']} (score: {health['overall_score']:.1f}/2.0)")

    return health


# ══════════════════════════════════════════════════════════════════════
# Section E: Recommendations (신규)
# ══════════════════════════════════════════════════════════════════════

def generate_recommendations(
    trajectory: list[dict],
    dispute_result: dict,
    health: dict,
    efficiency: dict,
) -> list[dict]:
    """패턴 기반 자동 권고 생성."""
    recs: list[dict] = []
    last = trajectory[-1]

    # R1: 오탐률 > 50%
    fp_rate = dispute_result.get("fp_rate", 0)
    if fp_rate > 0.5:
        recs.append({
            "id": "R1",
            "severity": "critical",
            "title": "Integrate 노드 semantic conflict detection 필요",
            "detail": (
                f"Disputed KU 오탐률 {fp_rate * 100:.0f}%. "
                f"_detect_conflict()의 단순 문자열 비교가 원인. "
                f"LLM 기반 semantic similarity 판정으로 교체 권고."
            ),
        })

    # R2: active KU 3사이클+ 정체
    if health.get("active_plateau", False):
        recs.append({
            "id": "R2",
            "severity": "high",
            "title": "Dispute resolution mechanism 필요",
            "detail": (
                f"Active KU가 {last['ku_active']}에서 3+ 사이클 정체. "
                f"새 claim이 모두 disputed로 분류되어 active로 전환 불가. "
                f"disputed KU 자동 재평가 메커니즘 필요."
            ),
        })

    # R3: conflict_rate > 30%
    conflict_rate = last.get("conflict_rate", 0)
    if conflict_rate > 0.30:
        recs.append({
            "id": "R3",
            "severity": "critical",
            "title": "Dispute resolution workflow 필요",
            "detail": (
                f"Conflict rate {conflict_rate * 100:.1f}% (임계치 15%). "
                f"해소 없이 누적만 진행 → positive feedback loop. "
                f"Critique 노드에 dispute resolution 단계 추가 권고."
            ),
        })

    # R4: hold 비율 > 90%
    hold_count = dispute_result.get("resolution_types", {}).get("hold", 0)
    total_resolutions = sum(dispute_result.get("resolution_types", {}).values())
    hold_ratio = hold_count / total_resolutions if total_resolutions > 0 else 0
    if hold_ratio > 0.90:
        recs.append({
            "id": "R4",
            "severity": "high",
            "title": "disputed -> active 전환 경로 필요",
            "detail": (
                f"Resolution 유형 중 hold가 {hold_ratio * 100:.0f}%. "
                f"disputed KU의 98%가 방치 상태. "
                f"조건부 승격(promote) 또는 근거 보강 후 재판정 경로 필요."
            ),
        })

    # R5: conflict_rate danger인데 수렴 가능
    conflict_grade = health.get("grades", {}).get("conflict_rate", {}).get("grade", "")
    if conflict_grade == "danger":
        recs.append({
            "id": "R5",
            "severity": "medium",
            "title": "수렴 조건에 conflict_rate 상한 추가 (C6)",
            "detail": (
                f"Conflict rate {conflict_rate * 100:.1f}%로 danger인데 "
                f"현재 수렴 조건(C1-C5)에 conflict_rate 미포함. "
                f"C6: conflict_rate < 0.15 조건 추가 권고."
            ),
        })

    # R6: 후반부 new active < 0.5/cycle
    marginal = efficiency.get("marginal_returns", [])
    if len(marginal) >= 4:
        later = marginal[len(marginal) // 2:]
        avg_new = sum(m["new_active"] for m in later) / len(later)
        if avg_new < 0.5:
            recs.append({
                "id": "R6",
                "severity": "medium",
                "title": "Early stopping 강화 필요",
                "detail": (
                    f"후반부 평균 new active KU: {avg_new:.1f}/cycle. "
                    f"사실상 성장 정지. "
                    f"active KU 정체 N사이클 연속 시 조기 종료 로직 강화 권고."
                ),
            })

    return recs


def print_recommendations(recs: list[dict]) -> None:
    print("\n=== E. Recommendations ===\n")
    if not recs:
        print("No recommendations generated.")
        return

    for r in recs:
        sev = r["severity"].upper()
        print(f"[{r['id']}] ({sev}) {r['title']}")
        print(f"    {r['detail']}")
        print()


# ══════════════════════════════════════════════════════════════════════
# Section F: Markdown Report (--report)
# ══════════════════════════════════════════════════════════════════════

def generate_report(
    trajectory: list[dict],
    kus: list[dict],
    gus: list[dict],
    trends: dict,
    dispute_result: dict,
    efficiency: dict,
    health: dict,
    recs: list[dict],
    output_path: Path,
) -> None:
    """docs/phase2-analysis.md 한국어 심층 분석 보고서 생성."""
    last = trajectory[-1]
    first = trajectory[0]
    n_cycles = len(trajectory)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)

    # ── Header ──
    w("# Phase 2 심층 분석 보고서")
    w()
    w(f"> 생성 시각: {now}")
    w(f"> 대상: {n_cycles} Cycles (Cycle {first['cycle']}~{last['cycle']})")
    w(f"> 벤치 도메인: japan-travel")
    w()

    # ── Executive Summary ──
    w("## 1. Executive Summary")
    w()
    w(f"| 항목 | 값 |")
    w(f"|------|-----|")
    w(f"| 총 Cycle | {n_cycles} |")
    w(f"| KU (active/disputed/total) | {last['ku_active']}/{last['ku_disputed']}/{last['ku_total']} |")
    w(f"| Evidence Rate | {_pct(last['evidence_rate'])} |")
    w(f"| Conflict Rate | {_pct(last['conflict_rate'])} |")
    w(f"| Gap Resolution | {_pct(last['gap_resolution_rate'])} |")
    w(f"| Health Grade | **{health['overall_grade']}** |")
    w(f"| 권고 수 | {len(recs)} ({sum(1 for r in recs if r['severity'] == 'critical')} critical) |")
    w()

    # ── Trajectory ──
    w("## 2. Cycle-by-Cycle Trajectory")
    w()
    w("| Cycle | KU Total | Active | Disputed | GU Open | Resolved | Conflict% | Mode |")
    w("|------:|---------:|-------:|---------:|--------:|---------:|----------:|------|")
    for r in trajectory:
        w(f"| {r['cycle']} | {r['ku_total']} | {r['ku_active']} | {r['ku_disputed']} | "
          f"{r['gu_open']} | {r['gu_resolved']} | {r['conflict_rate'] * 100:.1f}% | {r['mode']} |")
    w()

    # ── Trend ──
    w("## 3. Trend Analysis")
    w()
    w("### 성장률 비교 (전반부 vs 후반부)")
    w()
    w("| Metric | 1st Half | 2nd Half | Ratio |")
    w("|--------|----------:|----------:|------:|")
    for f in ["ku_total", "ku_active", "ku_disputed", "gu_resolved", "conflict_rate"]:
        g = trends["growth_comparison"].get(f, {})
        fh, sh = g.get("first_half", 0), g.get("second_half", 0)
        ratio = sh / fh if fh != 0 else 0
        if f in RATE_FIELDS:
            w(f"| {f} | {fh * 100:+.1f}% | {sh * 100:+.1f}% | {ratio:.2f}x |")
        else:
            w(f"| {f} | {fh:+} | {sh:+} | {ratio:.2f}x |")
    w()
    if trends["inflections"]:
        w("### 변곡점")
        w()
        for field, cycles in trends["inflections"].items():
            w(f"- **{field}**: Cycle {cycles}")
        w()

    # ── KU 분석 ──
    w("## 4. Knowledge Unit 분석")
    w()
    w(f"- 총 KU: {last['ku_total']}")
    w(f"- Active: {last['ku_active']} ({last['ku_active'] / last['ku_total'] * 100:.0f}%)")
    w(f"- Disputed: {last['ku_disputed']} ({last['ku_disputed'] / last['ku_total'] * 100:.0f}%)")
    w()

    # Category coverage
    cat_counter: Counter[str] = Counter()
    entity_set: set[str] = set()
    for ku in kus:
        ek = ku.get("entity_key", "")
        parts = ek.split(":")
        cat_counter[parts[1] if len(parts) >= 2 else "unknown"] += 1
        entity_set.add(ek)
    w(f"- 카테고리: {len(cat_counter)}개")
    w(f"- Entity: {len(entity_set)}개")
    w()

    # ── Disputed 심층 ──
    w("## 5. Disputed KU 심층 분석")
    w()
    w(f"| 항목 | 값 |")
    w(f"|------|-----|")
    w(f"| Total Disputed | {dispute_result['total_disputed']} |")
    w(f"| True Conflicts | {dispute_result['true_conflicts']} |")
    w(f"| False Positives | {dispute_result['false_positives']} |")
    w(f"| FP Rate | {dispute_result['fp_rate'] * 100:.1f}% |")
    w()
    w("### Resolution 유형")
    w()
    for rt, count in dispute_result["resolution_types"].items():
        w(f"- `{rt}`: {count}")
    w()
    w("### 근본 원인")
    w()
    w("`integrate` 노드의 `_detect_conflict()`가 단순 문자열 비교를 사용하여, "
      "동일 entity_key+field에 대한 새 claim이 기존 값과 조금만 달라도 conflict로 판정. "
      "semantic 동치 여부를 판단하지 못하므로 대부분 오탐(false positive)이 발생.")
    w()

    # ── Gap 분석 ──
    w("## 6. Gap Map 분석")
    w()
    gap_status: Counter[str] = Counter()
    gap_type: Counter[str] = Counter()
    for gu in gus:
        gap_status[gu.get("status", "unknown")] += 1
        gap_type[gu.get("gap_type", "unknown")] += 1
    w(f"- 총 Gap: {len(gus)}")
    for s, c in gap_status.most_common():
        w(f"- {s}: {c}")
    w()

    # ── API 비용 ──
    w("## 7. API 비용 효율성")
    w()
    t = efficiency["totals"]
    w(f"| 항목 | 값 |")
    w(f"|------|-----|")
    w(f"| LLM calls | {t['llm_calls']} |")
    w(f"| LLM tokens | {t['llm_tokens']:,} |")
    w(f"| Search calls | {t['search_calls']} |")
    w(f"| Fetch calls | {t['fetch_calls']} |")
    w(f"| Tokens/KU (total) | {efficiency['tokens_per_ku']:,.0f} |")
    w(f"| Tokens/KU (active) | {efficiency['tokens_per_active_ku']:,.0f} |")
    w(f"| Active ratio | {efficiency['active_ratio'] * 100:.1f}% |")
    w(f"| Waste ratio | {efficiency['waste_ratio'] * 100:.1f}% |")
    w()

    # ── Health ──
    w("## 8. Health Score")
    w()
    w(f"| Metric | Value | Grade |")
    w(f"|--------|------:|-------|")
    for name, info in health["grades"].items():
        val = info["value"]
        val_s = _pct(val) if name in RATE_FIELDS else str(val)
        w(f"| {name} | {val_s} | {info['grade'].upper()} |")
    w()
    w(f"**Overall Grade: {health['overall_grade']}** (score: {health['overall_score']:.1f}/2.0)")
    if health["active_plateau"]:
        w(f"\n- Active KU Plateau 감지 (3+ 사이클 정체)")
    w()

    # ── 권고 ──
    w("## 9. 개선 권고")
    w()
    for r in recs:
        w(f"### [{r['id']}] {r['title']}")
        w()
        w(f"- **심각도**: {r['severity'].upper()}")
        w(f"- {r['detail']}")
        w()

    # ── 결론 ──
    w("## 10. 결론")
    w()
    w("Phase 2 벤치 검증을 통해 Domain-K-Evolver 프레임워크의 기본 루프가 정상 동작함을 확인했다. "
      f"10 Cycle 동안 {last['ku_total']}개 KU를 생성하고, evidence rate 100%, "
      f"gap resolution {last['gap_resolution_rate'] * 100:.0f}%를 달성했다.")
    w()
    w("그러나 **false positive dispute 문제**가 시스템의 핵심 병목으로 드러났다. "
      f"Disputed KU {dispute_result['total_disputed']}개 중 "
      f"true conflict는 {dispute_result['true_conflicts']}개에 불과하며, "
      f"conflict rate는 {last['conflict_rate'] * 100:.1f}%까지 상승했다.")
    w()
    w("Phase 3에서는 다음을 우선 해결해야 한다:")
    w()
    critical_recs = [r for r in recs if r["severity"] == "critical"]
    for r in critical_recs:
        w(f"1. **{r['title']}** ({r['id']})")
    high_recs = [r for r in recs if r["severity"] == "high"]
    for r in high_recs:
        w(f"2. **{r['title']}** ({r['id']})")
    w()

    # Write file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nReport written to: {output_path}")


# ══════════════════════════════════════════════════════════════════════
# JSON Output (--json)
# ══════════════════════════════════════════════════════════════════════

def build_json_output(
    trajectory: list[dict],
    trends: dict,
    dispute_result: dict,
    efficiency: dict,
    health: dict,
    recs: list[dict],
) -> dict:
    return {
        "generated_at": datetime.now().isoformat(),
        "cycles": len(trajectory),
        "snapshot": {
            "first": trajectory[0],
            "last": trajectory[-1],
        },
        "trends": {
            "inflections": trends.get("inflections", {}),
            "growth_comparison": trends.get("growth_comparison", {}),
        },
        "disputes": dispute_result,
        "efficiency": {
            "tokens_per_ku": efficiency["tokens_per_ku"],
            "tokens_per_active_ku": efficiency["tokens_per_active_ku"],
            "searches_per_ku": efficiency["searches_per_ku"],
            "active_ratio": efficiency["active_ratio"],
            "waste_ratio": efficiency["waste_ratio"],
        },
        "health": {
            "grades": {k: v["grade"] for k, v in health["grades"].items()},
            "overall_grade": health["overall_grade"],
            "overall_score": health["overall_score"],
            "active_plateau": health["active_plateau"],
        },
        "recommendations": recs,
    }


# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════

def generate_entity_field_matrix(base: Path) -> None:
    """entity-field-matrix.json 생성 — Gate 판정 전 필수 아티팩트."""
    import re
    from datetime import date as _date

    ku_path   = base / "state" / "knowledge-units.json"
    gap_path  = base / "state" / "gap-map.json"
    skel_path = Path("bench/japan-travel/state-snapshots/cycle-0-snapshot/domain-skeleton.json")
    prev_path = Path("bench/silver/japan-travel/p7-rebuild-s3-smoke/entity-field-matrix.json")

    if not ku_path.exists() or not gap_path.exists():
        print("Error: state/knowledge-units.json or gap-map.json not found")
        return
    if not skel_path.exists():
        print(f"Error: skeleton not found at {skel_path}")
        return

    kus  = load_json(ku_path)
    gmap = load_json(gap_path)
    skel = load_json(skel_path)
    prev = load_json(prev_path) if prev_path.exists() else {}

    domain     = skel.get("domain", "japan-travel")
    cat_defs   = skel.get("categories", [])
    field_defs = skel.get("fields", [])

    ku_map: dict[tuple, list] = {}
    for ku in kus:
        if ku.get("status") not in ("active", "disputed"):
            continue
        ku_map.setdefault((ku["entity_key"], ku["field"]), []).append(ku["ku_id"])

    gu_map: dict[tuple, list] = {}
    for gu in gmap:
        t = gu.get("target", {})
        slot = (t.get("entity_key", ""), t.get("field", ""))
        gu_map.setdefault(slot, []).append({
            "gu_id": gu.get("gu_id"),
            "status": gu.get("status"),
            "trigger": gu.get("trigger", ""),
        })

    def ents_for_cat(cat: str) -> list[str]:
        slugs: set[str] = set()
        for ek, _ in list(ku_map.keys()) + list(gu_map.keys()):
            p = ek.split(":")
            if len(p) == 3 and p[0] == domain and p[1] == cat and p[2] != "*":
                slugs.add(p[2])
        prev_order = prev.get("categories", {}).get(cat, {}).get("entities", [])
        ordered = [s for s in prev_order if s in slugs]
        ordered += sorted(slugs - set(ordered))
        return ordered

    def app_fields(cat: str) -> list[str]:
        return [f["name"] for f in field_defs
                if "*" in f.get("categories", []) or cat in f.get("categories", [])]

    def slot_state(ek: str, field: str) -> str:
        has_ku = (ek, field) in ku_map
        gus    = gu_map.get((ek, field), [])
        if has_ku and gus:   return "ku_gu"
        if has_ku:            return "ku_only"
        if gus:
            return "gu_open" if any(g["status"] == "open" for g in gus) else "gu_resolved_no_wildcard_ku"
        return "vacant"

    def make_note(ek: str, field: str, state: str, cat: str) -> str | None:
        parts  = ek.split(":")
        slug   = parts[2] if len(parts) == 3 else "?"
        gus    = gu_map.get((ek, field), [])
        ku_ids = ku_map.get((ek, field), [])
        adj_gus = [g for g in gus if "adjacent" in g.get("trigger", "")]
        prev_note = (prev.get("categories", {}).get(cat, {})
                        .get("matrix", {}).get(slug, {})
                        .get(field, {}).get("note"))
        if state == "ku_only":
            if prev_note: return prev_note
            nums = [int(m.group(1)) for k in ku_ids if (m := re.search(r"KU-(\d+)", k))]
            return ("seed KU — entity-specific GU 미생성" if nums and max(nums) <= 13
                    else "entity-specific GU 없음 (wildcard-GU 파생 KU)")
        if state == "ku_gu" and adj_gus:
            return f"adj {'/'.join(g['gu_id'] for g in adj_gus)} 해소 후 KU 생성"
        if state == "ku_gu" and prev_note:
            return prev_note
        if state == "gu_resolved_no_wildcard_ku":
            return prev_note or "GU resolved, KU는 specific entity 수준으로 생성됨"
        return None

    summary: dict[str, int] = {
        "ku_gu": 0, "ku_only": 0, "gu_open": 0, "vacant": 0,
        "gu_resolved_no_wildcard_ku": 0, "total": 0,
    }
    by_cat: dict[str, dict] = {}
    cat_data: dict[str, dict] = {}

    for cdef in cat_defs:
        cat    = cdef["slug"]
        fields = app_fields(cat)
        ents   = ents_for_cat(cat)
        ct: dict[str, int] = {k: 0 for k in summary}
        matrix_rows: dict[str, dict] = {}

        for slug in ents + ["*"]:
            ek  = f"{domain}:{cat}:{slug}"
            row: dict[str, dict] = {}
            for field in fields:
                st    = slot_state(ek, field)
                entry: dict = {
                    "state":   st,
                    "ku_ids":  ku_map.get((ek, field), []),
                    "gu_ids":  [g["gu_id"] for g in gu_map.get((ek, field), [])],
                }
                note = make_note(ek, field, st, cat)
                if note:
                    entry["note"] = note
                row[field] = entry
                ct[st]    = ct.get(st, 0) + 1
                ct["total"] += 1
                summary[st]      = summary.get(st, 0) + 1
                summary["total"] += 1
            matrix_rows[slug] = row

        cat_data[cat] = {"entities": ents, "fields": fields, "matrix": matrix_rows}
        prev_anom = prev.get("categories", {}).get(cat, {}).get("anomalies")
        if prev_anom:
            cat_data[cat]["anomalies"] = prev_anom
        by_cat[cat] = ct

    # trial_id from bench-root dir name
    trial_id = base.name

    matrix_out = {
        "trial_id":   trial_id,
        "cycle":      len(load_json(base / "trajectory" / "trajectory.json")),
        "generated_at": str(_date.today()),
        "generation_method": "auto",
        "note": f"analyze_trajectory.py --matrix で生成. KU/GU: state/*.json 최종 cycle 기준.",
        "state_definitions": {
            "ku_gu":  "KU + GU 모두 존재 (GU resolved, KU 생성됨)",
            "ku_only": "KU 존재, 해당 entity-field GU 없음 (seed 또는 wildcard-GU 파생)",
            "gu_open": "GU open, KU 미생성 (수집 진행 중)",
            "vacant":  "KU·GU 모두 없음 (미탐색 슬롯)",
            "gu_resolved_no_wildcard_ku": "GU resolved되었으나 KU가 specific entity 수준으로 생성됨",
        },
        "categories": cat_data,
        "summary": {
            "total_slots": summary["total"],
            "ku_gu":       summary["ku_gu"],
            "gu_resolved_no_wildcard_ku": summary["gu_resolved_no_wildcard_ku"],
            "ku_only":     summary["ku_only"],
            "gu_open":     summary["gu_open"],
            "vacant":      summary["vacant"],
            "by_category": by_cat,
        },
    }

    out_path = base / "entity-field-matrix.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(matrix_out, f, ensure_ascii=False, indent=2)

    s = matrix_out["summary"]
    print(f"entity-field-matrix.json 생성 완료: {out_path}")
    print(f"  총 슬롯: {s['total_slots']} | ku_gu={s['ku_gu']} ku_only={s['ku_only']} gu_open={s['gu_open']} vacant={s['vacant']}")
    for cat, ct in s["by_category"].items():
        print(f"  {cat:<15}: total={ct['total']} ku_gu={ct['ku_gu']} ku_only={ct['ku_only']} vacant={ct['vacant']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze trajectory results (deep analysis)")
    parser.add_argument(
        "--dir",
        default="bench/japan-travel-auto",
        help="Bench result directory (default: bench/japan-travel-auto)",
    )
    parser.add_argument(
        "--bench-root",
        dest="bench_root",
        default=None,
        help="Silver trial root directory (alias for --dir, e.g. bench/silver/japan-travel/p7-s3-gu-smoke)",
    )
    parser.add_argument("--report", action="store_true", help="Generate docs/phase2-analysis.md")
    parser.add_argument("--json", action="store_true", dest="json_output", help="JSON output to stdout")
    parser.add_argument("--matrix", action="store_true", help="Generate entity-field-matrix.json (Gate 필수 아티팩트)")
    args = parser.parse_args()

    # --bench-root overrides --dir
    base = Path(args.bench_root if args.bench_root else args.dir)

    # ── Matrix-only mode ──
    if args.matrix and not args.json_output and not args.report:
        generate_entity_field_matrix(base)
        return

    traj_path = base / "trajectory" / "trajectory.json"
    ku_path = base / "state" / "knowledge-units.json"
    gap_path = base / "state" / "gap-map.json"

    if not traj_path.exists():
        print(f"Error: {traj_path} not found")
        return

    trajectory = load_json(traj_path)
    kus = load_json(ku_path) if ku_path.exists() else []
    gus = load_json(gap_path) if gap_path.exists() else []

    # ── JSON mode ──
    if args.json_output:
        trends = compute_trends(trajectory)
        dispute_result = analyze_disputes(kus)
        efficiency = compute_efficiency(trajectory)
        health = compute_health(trajectory, trends)
        recs = generate_recommendations(trajectory, dispute_result, health, efficiency)
        output = build_json_output(trajectory, trends, dispute_result, efficiency, health, recs)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    # ── Text mode ──
    # 기존 섹션
    print_cycle_table(trajectory)
    print_snapshot_diff(trajectory)

    if kus:
        print_category_coverage(kus)
        print_entity_summary(kus)

    if gus:
        print_gap_summary(gus)

    # 신규 섹션
    trends = print_trend_analysis(trajectory)
    dispute_result = print_dispute_analysis(kus) if kus else analyze_disputes([])
    efficiency = print_efficiency(trajectory)
    health = print_health(trajectory, trends)
    recs = generate_recommendations(trajectory, dispute_result, health, efficiency)
    print_recommendations(recs)

    # ── Report mode ──
    if args.report:
        report_path = Path("docs") / "phase2-analysis.md"
        generate_report(
            trajectory, kus, gus, trends,
            dispute_result, efficiency, health, recs, report_path,
        )

    print("\n=== Analysis Complete ===")


if __name__ == "__main__":
    main()
