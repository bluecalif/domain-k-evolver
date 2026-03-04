"""Metrics 계산 유틸리티 — Task 1.5.

design-v2.md §4 기반.
6개 Metrics 공식 + assess_health + axis_coverage + deficit_ratio.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


# ---------------------------------------------------------------------------
# 개별 Metric 공식
# ---------------------------------------------------------------------------

def evidence_rate(knowledge_units: list[dict]) -> float:
    """active KU 중 EU 1개 이상인 비율."""
    active = [ku for ku in knowledge_units if ku.get("status") == "active"]
    if not active:
        return 0.0
    with_ev = sum(1 for ku in active if len(ku.get("evidence_links", [])) >= 1)
    return with_ev / len(active)


def multi_evidence_rate(knowledge_units: list[dict]) -> float:
    """active KU 중 독립 출처 2개 이상인 비율."""
    active = [ku for ku in knowledge_units if ku.get("status") == "active"]
    if not active:
        return 0.0
    with_multi = sum(1 for ku in active if len(ku.get("evidence_links", [])) >= 2)
    return with_multi / len(active)


def gap_resolution_rate(
    gap_map: list[dict],
    *,
    cycle_start_open: int | None = None,
) -> float:
    """이번 Cycle에서 해결된 Gap 비율.

    cycle_start_open이 주어지면 분모로 사용.
    주어지지 않으면 전체 GU 중 resolved + open 합산을 분모로 사용 (근사).
    """
    resolved = sum(1 for gu in gap_map if gu.get("status") == "resolved")
    if cycle_start_open is not None:
        denom = cycle_start_open
    else:
        # 근사: resolved + open (deferred 제외)
        denom = sum(
            1 for gu in gap_map
            if gu.get("status") in ("open", "resolved")
        )
    if denom == 0:
        return 0.0
    return resolved / denom


def conflict_rate(knowledge_units: list[dict]) -> float:
    """disputed KU / (active + disputed) KU."""
    active_or_disputed = [
        ku for ku in knowledge_units
        if ku.get("status") in ("active", "disputed")
    ]
    if not active_or_disputed:
        return 0.0
    disputed = sum(1 for ku in active_or_disputed if ku.get("status") == "disputed")
    return disputed / len(active_or_disputed)


def avg_confidence(knowledge_units: list[dict]) -> float:
    """active KU의 평균 confidence."""
    active = [ku for ku in knowledge_units if ku.get("status") == "active"]
    if not active:
        return 0.0
    total = sum(ku.get("confidence", 0.0) for ku in active)
    return total / len(active)


def staleness_risk(
    knowledge_units: list[dict],
    today: date | None = None,
) -> int:
    """TTL 초과 KU 수 (정수)."""
    if today is None:
        today = date.today()
    count = 0
    for ku in knowledge_units:
        if ku.get("status") != "active":
            continue
        observed = ku.get("observed_at")
        validity = ku.get("validity", {})
        ttl = validity.get("ttl_days")
        if observed and ttl is not None:
            obs_date = date.fromisoformat(observed)
            if obs_date + timedelta(days=ttl) < today:
                count += 1
    return count


# ---------------------------------------------------------------------------
# 통합 compute_metrics
# ---------------------------------------------------------------------------

def compute_metrics(
    state: dict,
    *,
    cycle_start_open: int | None = None,
    today: date | None = None,
) -> dict:
    """State에서 전체 Metrics dict 반환.

    Returns:
        MetricRates 형태의 dict.
    """
    kus = state.get("knowledge_units", [])
    gm = state.get("gap_map", [])
    return {
        "evidence_rate": evidence_rate(kus),
        "multi_evidence_rate": multi_evidence_rate(kus),
        "gap_resolution_rate": gap_resolution_rate(gm, cycle_start_open=cycle_start_open),
        "conflict_rate": conflict_rate(kus),
        "avg_confidence": avg_confidence(kus),
        "staleness_risk": staleness_risk(kus, today=today),
    }


# ---------------------------------------------------------------------------
# 건강 판정
# ---------------------------------------------------------------------------

_THRESHOLDS: dict[str, dict[str, Any]] = {
    "evidence_rate":       {"healthy": 0.95, "caution": 0.80, "higher_better": True},
    "multi_evidence_rate": {"healthy": 0.50, "caution": 0.30, "higher_better": True},
    "conflict_rate":       {"healthy": 0.05, "caution": 0.15, "higher_better": False},
    "avg_confidence":      {"healthy": 0.85, "caution": 0.70, "higher_better": True},
    "staleness_risk":      {"healthy": 0,    "caution": 3,    "higher_better": False},
}


def assess_health(metrics: dict) -> dict:
    """각 지표의 건강/주의/위험 판정.

    Returns:
        {metric_name: "healthy" | "caution" | "danger"} dict.
    """
    result: dict[str, str] = {}
    for name, thresholds in _THRESHOLDS.items():
        val = metrics.get(name)
        if val is None:
            continue
        if thresholds["higher_better"]:
            if val >= thresholds["healthy"]:
                result[name] = "healthy"
            elif val >= thresholds["caution"]:
                result[name] = "caution"
            else:
                result[name] = "danger"
        else:
            if val <= thresholds["healthy"]:
                result[name] = "healthy"
            elif val <= thresholds["caution"]:
                result[name] = "caution"
            else:
                result[name] = "danger"
    return result


# ---------------------------------------------------------------------------
# Axis Coverage Matrix
# ---------------------------------------------------------------------------

def compute_axis_coverage(
    gap_map: list[dict],
    skeleton: dict,
) -> dict[str, dict[str, dict[str, int | float]]]:
    """Axis Coverage Matrix 계산.

    Returns:
        {axis_name: {anchor: {"open": N, "resolved": N,
                               "critical_open": N, "evidence_density": float}}}
    """
    axes = skeleton.get("axes", [])
    result: dict[str, dict[str, dict[str, int | float]]] = {}

    for axis_def in axes:
        axis_name = axis_def["name"]
        anchors = axis_def.get("anchors", [])
        axis_data: dict[str, dict[str, int | float]] = {}

        for anchor in anchors:
            axis_data[anchor] = {
                "open": 0,
                "resolved": 0,
                "critical_open": 0,
                "evidence_density": 0.0,
            }
        result[axis_name] = axis_data

    # category 축 특수 처리: entity_key에서 추출
    for gu in gap_map:
        status = gu.get("status", "open")
        expected_utility = gu.get("expected_utility", "")
        axis_tags = gu.get("axis_tags", {})

        # entity_key에서 category 추출
        target = gu.get("target", {})
        entity_key = target.get("entity_key", "")
        parts = entity_key.split(":")
        category_from_key = parts[1] if len(parts) >= 3 else ""

        # risk 축: risk_level 필드에서 추출
        risk_level = gu.get("risk_level", "")

        for axis_def in axes:
            axis_name = axis_def["name"]
            anchors_set = set(axis_def.get("anchors", []))

            # anchor 값 결정
            anchor: str | None = None
            if axis_name == "category":
                anchor = category_from_key if category_from_key in anchors_set else None
            elif axis_name == "risk":
                anchor = risk_level if risk_level in anchors_set else None
            else:
                # axis_tags에서 직접 가져옴
                tag_val = axis_tags.get(axis_name)
                anchor = tag_val if tag_val in anchors_set else None

            if anchor is None:
                continue

            entry = result[axis_name][anchor]
            if status == "open":
                entry["open"] += 1
                if expected_utility in ("critical", "high"):
                    entry["critical_open"] += 1
            elif status == "resolved":
                entry["resolved"] += 1

    return result


# ---------------------------------------------------------------------------
# Deficit Ratios
# ---------------------------------------------------------------------------

def compute_deficit_ratios(
    axis_coverage: dict[str, dict[str, dict[str, int | float]]],
    skeleton: dict,
) -> dict[str, float]:
    """축별 deficit_ratio 계산.

    deficit_ratio = (GU가 전혀 없는 anchor 수) / (전체 anchor 수).
    """
    axes = skeleton.get("axes", [])
    result: dict[str, float] = {}

    for axis_def in axes:
        axis_name = axis_def["name"]
        anchors = axis_def.get("anchors", [])
        if not anchors:
            result[axis_name] = 0.0
            continue

        axis_data = axis_coverage.get(axis_name, {})
        zero_count = 0
        for anchor in anchors:
            entry = axis_data.get(anchor, {})
            total = entry.get("open", 0) + entry.get("resolved", 0)
            if total == 0:
                zero_count += 1

        result[axis_name] = zero_count / len(anchors)

    return result
