"""Coverage Map — 카테고리 × 필드 coverage + Gini tracking.

P4-A2: deficit score 계산 + category/field Gini 통합.
P4-A5: Gini → deficit 가중 반영.
"""

from __future__ import annotations

from typing import Any


def _gini_coefficient(values: list[int]) -> float:
    """Gini coefficient 계산 (0=완전 균등, 1=완전 불균등).

    readiness_gate.py 와 동일 알고리즘. 공유 유틸화.
    """
    n = len(values)
    if n == 0 or sum(values) == 0:
        return 0.0
    sorted_vals = sorted(values)
    mean = sum(sorted_vals) / n
    if mean == 0:
        return 0.0
    numerator = sum(
        abs(sorted_vals[i] - sorted_vals[j])
        for i in range(n)
        for j in range(n)
    )
    return numerator / (2 * n * n * mean)


# Gini → deficit 가중 상수
GINI_WEIGHT = 0.3          # Gini 가 deficit 에 기여하는 가중치
GINI_THRESHOLD = 0.45      # readiness_gate 기준 동일


def build_coverage_map(
    state: dict,
    skeleton: dict | None = None,
    *,
    target_per_category: int = 10,
    gini_weight: float = GINI_WEIGHT,
    gini_threshold: float = GINI_THRESHOLD,
) -> dict:
    """Coverage Map 생성 — 카테고리별 KU/필드 분포 + Gini + deficit.

    Args:
        state: EvolverState.
        skeleton: domain_skeleton (None 이면 state 에서 추출).
        target_per_category: 카테고리당 목표 KU 수 (deficit 분모).
        gini_weight: Gini → deficit 가중 계수.
        gini_threshold: Gini 임계치 (초과 시 deficit 상향).

    Returns:
        dict:
          {category_slug: {ku_count, deficit_score, field_coverage: {field: count}}}
          + "summary": {category_gini, field_gini, gini_deficit_adjustment}
    """
    if skeleton is None:
        skeleton = state.get("domain_skeleton", {})

    kus = state.get("knowledge_units", [])
    categories = [c["slug"] for c in skeleton.get("categories", [])]

    # 카테고리별 KU 카운트 + 필드별 분포
    cat_ku_counts: dict[str, int] = {c: 0 for c in categories}
    cat_field_counts: dict[str, dict[str, int]] = {c: {} for c in categories}
    all_field_counts: dict[str, int] = {}

    for ku in kus:
        if ku.get("status") not in ("active", "disputed"):
            continue
        ek = ku.get("entity_key", "")
        parts = ek.split(":")
        cat = parts[1] if len(parts) >= 3 else ""
        field = ku.get("field", "")

        if cat in cat_ku_counts:
            cat_ku_counts[cat] += 1
            cat_field_counts[cat][field] = cat_field_counts[cat].get(field, 0) + 1

        all_field_counts[field] = all_field_counts.get(field, 0) + 1

    # Gini 계산
    cat_values = list(cat_ku_counts.values())
    category_gini = _gini_coefficient(cat_values) if cat_values else 0.0

    field_values = list(all_field_counts.values())
    field_gini = _gini_coefficient(field_values) if field_values else 0.0

    # Gini deficit adjustment (P4-A5)
    gini_adj = 0.0
    if category_gini > gini_threshold:
        gini_adj = gini_weight * (category_gini - gini_threshold)

    # 카테고리별 coverage 구축
    result: dict[str, Any] = {}
    for cat in categories:
        count = cat_ku_counts[cat]
        base_deficit = 1.0 - min(1.0, count / target_per_category) if target_per_category > 0 else 0.0

        # Gini 가중 deficit: 소수 카테고리(count 낮은)에 추가 deficit
        adjusted_deficit = base_deficit
        if gini_adj > 0 and count < target_per_category:
            # deficit 비례로 Gini 보정 적용 (deficit 높을수록 더 많이 보정)
            adjusted_deficit = min(1.0, base_deficit + gini_adj * base_deficit)

        result[cat] = {
            "ku_count": count,
            "deficit_score": round(adjusted_deficit, 4),
            "base_deficit": round(base_deficit, 4),
            "field_coverage": dict(cat_field_counts[cat]),
        }

    result["summary"] = {
        "category_gini": round(category_gini, 4),
        "field_gini": round(field_gini, 4),
        "gini_deficit_adjustment": round(gini_adj, 4),
        "total_kus": sum(cat_ku_counts.values()),
        "categories_count": len(categories),
    }

    return result
