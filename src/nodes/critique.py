"""critique_node — Metrics + 실패모드 분석 + 수렴 판정 + 처방.

design-v2 §4~§5 기반.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from src.state import EvolverState
from src.utils.metrics import (
    assess_health,
    compute_axis_coverage,
    compute_deficit_ratios,
    compute_metrics,
)

HIGH_RISK_LEVELS = {"safety", "financial", "policy"}


def _analyze_failure_modes(
    kus: list[dict],
    gap_map: list[dict],
    skeleton: dict,
    today: date | None = None,
) -> list[dict]:
    """6대 실패모드 분석 → 처방 목록."""
    if today is None:
        today = date.today()
    prescriptions: list[dict] = []
    rx_counter = 1

    # 1. Epistemic: 단일출처 high-risk KU
    for ku in kus:
        if ku.get("status") != "active":
            continue
        if len(ku.get("evidence_links", [])) <= 1:
            # risk 판정 (entity_key 기반 간이)
            entity_key = ku.get("entity_key", "")
            parts = entity_key.split(":")
            category = parts[1] if len(parts) >= 3 else ""
            if category in ("regulation",) or ku.get("confidence", 1.0) < 0.85:
                prescriptions.append({
                    "rx_id": f"RX-{rx_counter:04d}",
                    "type": "epistemic",
                    "description": f"{ku.get('ku_id')}: 단일출처, 독립 출처 추가 필요",
                    "target_ku": ku.get("ku_id"),
                })
                rx_counter += 1

    # 2. Temporal: expires_at 30일 이내
    for ku in kus:
        if ku.get("status") != "active":
            continue
        validity = ku.get("validity", {})
        expires_at = validity.get("expires_at")
        if expires_at:
            exp_date = date.fromisoformat(expires_at)
            if exp_date - timedelta(days=30) <= today:
                prescriptions.append({
                    "rx_id": f"RX-{rx_counter:04d}",
                    "type": "temporal",
                    "description": f"{ku.get('ku_id')}: expires_at {expires_at} 임박",
                    "target_ku": ku.get("ku_id"),
                })
                rx_counter += 1

    # 3. Consistency: disputed KU
    disputed = [ku for ku in kus if ku.get("status") == "disputed"]
    for ku in disputed:
        prescriptions.append({
            "rx_id": f"RX-{rx_counter:04d}",
            "type": "consistency",
            "description": f"{ku.get('ku_id')}: disputed 상태, 추가 수집 필요",
            "target_ku": ku.get("ku_id"),
        })
        rx_counter += 1

    # 4. Planning: 미커버 카테고리 > 50%
    categories = {c["slug"] for c in skeleton.get("categories", [])}
    covered_cats = set()
    for gu in gap_map:
        if gu.get("status") == "resolved":
            entity_key = gu.get("target", {}).get("entity_key", "")
            parts = entity_key.split(":")
            if len(parts) >= 2:
                covered_cats.add(parts[1])
    if categories and len(covered_cats) / len(categories) < 0.5:
        prescriptions.append({
            "rx_id": f"RX-{rx_counter:04d}",
            "type": "planning",
            "description": f"카테고리 커버리지 부족: {len(covered_cats)}/{len(categories)}",
        })
        rx_counter += 1

    return prescriptions


def _check_convergence(
    kus: list[dict],
    gap_map: list[dict],
    skeleton: dict,
    cycle: int,
    metrics_rates: dict,
    net_gap_changes: list[int] | None = None,
) -> dict:
    """수렴 조건 판정 (C1~C5)."""
    result = {
        "converged": False,
        "conditions": {},
    }

    if cycle < 5:
        result["conditions"]["min_cycle"] = False
        return result

    result["conditions"]["min_cycle"] = True

    # C1: critical+high open 비율 < 10%
    critical_high = [
        gu for gu in gap_map
        if gu.get("expected_utility") in ("critical", "high")
    ]
    critical_high_open = [gu for gu in critical_high if gu.get("status") == "open"]
    c1 = (len(critical_high_open) / len(critical_high) < 0.10) if critical_high else True
    result["conditions"]["C1_critical_high_resolved"] = c1

    # C2: stale open 비율 < 15%
    stale_gus = [gu for gu in gap_map if gu.get("gap_type") == "stale"]
    stale_open = [gu for gu in stale_gus if gu.get("status") == "open"]
    c2 = (len(stale_open) / len(stale_gus) < 0.15) if stale_gus else True
    result["conditions"]["C2_stale_resolved"] = c2

    # C3: net_gap_change 3 Cycle > -1
    c3 = True
    if net_gap_changes and len(net_gap_changes) >= 3:
        recent = net_gap_changes[-3:]
        c3 = all(ngc > -1 for ngc in recent)
    result["conditions"]["C3_gap_stable"] = c3

    # C4: avg_confidence >= 0.85
    c4 = metrics_rates.get("avg_confidence", 0) >= 0.85
    result["conditions"]["C4_avg_confidence"] = c4

    # C5: 카테고리 커버리지 >= 80%
    categories = {c["slug"] for c in skeleton.get("categories", [])}
    covered = set()
    for gu in gap_map:
        if gu.get("status") == "resolved":
            entity_key = gu.get("target", {}).get("entity_key", "")
            parts = entity_key.split(":")
            if len(parts) >= 2:
                covered.add(parts[1])
    c5 = (len(covered) / len(categories) >= 0.80) if categories else True
    result["conditions"]["C5_category_coverage"] = c5

    result["converged"] = c1 and c2 and c3 and c4 and c5

    return result


def critique_node(
    state: EvolverState,
    *,
    llm: Any | None = None,
    today: date | None = None,
) -> dict:
    """Metrics 계산 + 실패모드 분석 + 수렴 판정 + Critique Report 생성."""
    if today is None:
        today = date.today()

    kus = state.get("knowledge_units", [])
    gap_map = state.get("gap_map", [])
    skeleton = state.get("domain_skeleton", {})
    cycle = state.get("current_cycle", 1)
    prev_metrics = state.get("metrics", {})

    # Metrics 계산
    rates = compute_metrics(
        {"knowledge_units": kus, "gap_map": gap_map},
        today=today,
    )
    health = assess_health(rates)

    # Axis Coverage 재계산
    axis_cov = compute_axis_coverage(gap_map, skeleton)
    deficits = compute_deficit_ratios(axis_cov, skeleton)

    # 실패모드 분석
    prescriptions = _analyze_failure_modes(kus, gap_map, skeleton, today)

    # net_gap_change 계산 (open GU 변화)
    prev_counts = prev_metrics.get("counts", {})
    prev_open = prev_counts.get("total_gu_open", 0)
    curr_open = sum(1 for gu in gap_map if gu.get("status") == "open")
    net_gap_change = curr_open - prev_open

    # 누적 net_gap_changes
    net_gap_changes = list(state.get("net_gap_changes", []))
    net_gap_changes.append(net_gap_change)

    # 수렴 판정
    convergence = _check_convergence(kus, gap_map, skeleton, cycle, rates, net_gap_changes)

    # Delta 계산
    prev_rates = prev_metrics.get("rates", {})
    delta = {}
    for key in rates:
        if key in prev_rates:
            if isinstance(rates[key], (int, float)) and isinstance(prev_rates[key], (int, float)):
                delta[key] = round(rates[key] - prev_rates[key], 4)

    # Counts
    counts = {
        "total_ku": len(kus),
        "active_ku": sum(1 for ku in kus if ku.get("status") == "active"),
        "disputed_ku": sum(1 for ku in kus if ku.get("status") == "disputed"),
        "deprecated_ku": sum(1 for ku in kus if ku.get("status") == "deprecated"),
        "total_gu_open": sum(1 for gu in gap_map if gu.get("status") == "open"),
        "total_gu_resolved": sum(1 for gu in gap_map if gu.get("status") == "resolved"),
        "total_gu_deferred": sum(1 for gu in gap_map if gu.get("status") == "deferred"),
    }

    # Metrics 객체 구축
    new_metrics = {
        "cycle": cycle,
        "phase": "post_critique",
        "timestamp": today.isoformat(),
        "counts": counts,
        "rates": rates,
        "delta_from_prev_cycle": delta,
    }

    # Critique Report
    critique_report = {
        "cycle": cycle,
        "health": health,
        "prescriptions": prescriptions,
        "convergence": convergence,
        "deficit_ratios": deficits,
    }

    # AxisCoverageEntry 리스트 변환
    axis_coverage_entries: list[dict] = []
    for axis_name, anchors in axis_cov.items():
        axis_deficit = deficits.get(axis_name, 0.0)
        for anchor, data in anchors.items():
            total = data.get("open", 0) + data.get("resolved", 0)
            cov = data.get("resolved", 0) / total if total > 0 else 0.0
            axis_coverage_entries.append({
                "axis": axis_name,
                "anchor": anchor,
                "open_count": data.get("open", 0),
                "resolved_count": data.get("resolved", 0),
                "total_count": total,
                "coverage": round(cov, 3),
                "deficit_ratio": axis_deficit,
            })

    return {
        "current_critique": critique_report,
        "axis_coverage": axis_coverage_entries,
        "metrics": new_metrics,
        "net_gap_changes": net_gap_changes,
    }
