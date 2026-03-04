"""seed_node — Bootstrap GU 생성.

gu-bootstrap-spec §1 (5단계) 기반.
입력: domain_skeleton, knowledge_units (Seed KU), policies
출력: gap_map (Bootstrap GU 배열), metrics (초기화), current_cycle=1
"""

from __future__ import annotations

from datetime import date, timedelta
from math import ceil
from typing import Any

from src.state import EvolverState

# --- 핵심 카테고리 (도메인별 정의, §3) ---
# japan-travel 기준. 추후 skeleton에서 읽도록 확장 가능.
CORE_CATEGORIES = {"transport", "regulation", "pass-ticket"}

# --- risk_level 1단계 상향 대상 카테고리 ---
RISK_UPGRADE_CATEGORIES = {"regulation"}

# --- 우선순위 정렬 키 ---
_UTILITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_RISK_ORDER = {"safety": 0, "financial": 1, "policy": 2, "convenience": 3, "informational": 4}
_RISK_UPGRADE = {
    "informational": "convenience",
    "convenience": "policy",
    "policy": "safety",
    "safety": "safety",
    "financial": "financial",
}

# --- 와일드카드 사용 필드 (카테고리 공통 규칙) ---
WILDCARD_FIELDS = {"tips", "etiquette"}

# --- 엔티티별 값이 다를 수 있는 필드 ---
ENTITY_SPECIFIC_FIELDS = {"price", "hours", "location", "duration", "how_to_use",
                          "acceptance", "where_to_buy", "eligibility", "policy"}


def _build_field_matrix(skeleton: dict) -> list[tuple[str, str]]:
    """1단계: Category × Field 적용 매트릭스 구성.

    Returns:
        [(category_slug, field_name), ...] 적용 가능 슬롯 목록.
    """
    categories = [c["slug"] for c in skeleton.get("categories", [])]
    fields = skeleton.get("fields", [])
    slots: list[tuple[str, str]] = []

    for field_def in fields:
        field_name = field_def["name"]
        field_cats = field_def.get("categories", [])
        if "*" in field_cats:
            for cat in categories:
                slots.append((cat, field_name))
        else:
            for cat in field_cats:
                if cat in categories:
                    slots.append((cat, field_name))

    return slots


def _determine_risk_level(category: str, field: str) -> str:
    """§3 규칙: field + category → risk_level."""
    # field 기반 기본 risk
    if field == "policy" and category == "regulation":
        base_risk = "policy"
    elif field == "price":
        base_risk = "financial"
    elif field == "eligibility":
        base_risk = "policy"
    elif field in ("hours", "location", "duration", "how_to_use"):
        base_risk = "convenience"
    elif field in ("tips", "etiquette", "acceptance", "where_to_buy"):
        base_risk = "convenience"
    elif field == "policy":
        base_risk = "policy"
    else:
        base_risk = "convenience"

    # regulation 카테고리 오버라이드: 1단계 상향
    if category in RISK_UPGRADE_CATEGORIES:
        base_risk = _RISK_UPGRADE.get(base_risk, base_risk)

    return base_risk


def _determine_expected_utility(risk_level: str, field: str, category: str) -> str:
    """§3 규칙: risk_level → expected_utility."""
    if risk_level == "safety":
        return "critical"
    elif risk_level == "financial" and field in ("price", "policy"):
        return "high"
    elif risk_level == "financial":
        return "medium"
    elif risk_level == "policy":
        return "high"
    elif risk_level == "convenience" and category in CORE_CATEGORIES:
        return "medium"
    elif risk_level == "convenience":
        return "low"
    elif risk_level == "informational":
        return "low"
    return "medium"


def _determine_gap_type(
    category: str,
    field: str,
    kus: list[dict],
    today: date,
) -> str | None:
    """2단계: 슬롯별 gap_type 판정.

    Returns:
        gap_type 문자열, 또는 Gap 아닌 경우 None.
    """
    # 해당 슬롯에 매칭되는 KU 찾기
    matching_kus = [
        ku for ku in kus
        if ku.get("entity_key", "").split(":")[1] == category
        if ku.get("field") == field
    ]

    if not matching_kus:
        return "missing"

    active_kus = [ku for ku in matching_kus if ku.get("status") == "active"]
    disputed_kus = [ku for ku in matching_kus if ku.get("status") == "disputed"]

    # 복수 조건: conflicting > stale > uncertain > missing
    gap_type: str | None = None

    if disputed_kus:
        gap_type = "conflicting"

    for ku in active_kus:
        observed = ku.get("observed_at")
        validity = ku.get("validity", {})
        ttl = validity.get("ttl_days")
        if observed and ttl is not None:
            obs_date = date.fromisoformat(observed)
            if obs_date + timedelta(days=ttl) < today:
                if gap_type not in ("conflicting",):
                    gap_type = "stale"

    for ku in active_kus:
        if ku.get("confidence", 1.0) < 0.7:
            if gap_type not in ("conflicting", "stale"):
                gap_type = "uncertain"

    if not active_kus and not disputed_kus:
        gap_type = "missing"

    return gap_type


def _get_entities_by_category(
    kus: list[dict],
    domain: str,
) -> dict[str, list[str]]:
    """Seed KU에서 카테고리별 엔티티 목록 추출."""
    result: dict[str, list[str]] = {}
    for ku in kus:
        entity_key = ku.get("entity_key", "")
        parts = entity_key.split(":")
        if len(parts) >= 3 and parts[0] == domain:
            cat = parts[1]
            slug = parts[2]
            if cat not in result:
                result[cat] = []
            if slug not in result[cat]:
                result[cat].append(slug)
    return result


def _get_per_category_cap(n_categories: int) -> int:
    """§4: 카테고리당 상한."""
    if n_categories <= 5:
        return 6
    elif n_categories <= 8:
        return 4
    else:
        return 3


def _is_excluded(entity_key: str, scope_boundary: dict) -> bool:
    """§5: Scope 경계 판정."""
    excludes = scope_boundary.get("excludes", [])
    for excl in excludes:
        excl_lower = excl.lower()
        if excl_lower in entity_key.lower():
            return True
    return False


def seed_node(state: EvolverState) -> dict:
    """Bootstrap GU 생성 + State 초기화."""
    skeleton = state.get("domain_skeleton", {})
    kus = state.get("knowledge_units", [])
    domain = skeleton.get("domain", "")
    today = date.today()
    scope_boundary = skeleton.get("scope_boundary", {})

    categories = [c["slug"] for c in skeleton.get("categories", [])]
    n_categories = len(categories)
    per_cat_cap = _get_per_category_cap(n_categories)

    # 1단계: Category × Field 매트릭스
    slots = _build_field_matrix(skeleton)

    # 카테고리별 엔티티 목록
    entities_by_cat = _get_entities_by_category(kus, domain)

    # 2~3단계: 각 슬롯에 대해 gap_type 판정 + 엔티티 확장
    raw_gus: list[dict[str, Any]] = []
    cat_counts: dict[str, int] = {cat: 0 for cat in categories}

    for cat, field in slots:
        gap_type = _determine_gap_type(cat, field, kus, today)
        if gap_type is None:
            continue

        risk_level = _determine_risk_level(cat, field)
        expected_utility = _determine_expected_utility(risk_level, field, cat)

        # 엔티티 확장
        known_entities = entities_by_cat.get(cat, [])

        if field in WILDCARD_FIELDS:
            # 와일드카드 GU (카테고리 공통)
            entity_key = f"{domain}:{cat}:*"
            if _is_excluded(entity_key, scope_boundary):
                continue
            raw_gus.append({
                "gap_type": gap_type,
                "target": {"entity_key": entity_key, "field": field},
                "expected_utility": expected_utility,
                "risk_level": risk_level,
                "resolution_criteria": f"{cat} {field} 정보 수집",
                "status": "open",
                "category": cat,
            })
        elif field in ENTITY_SPECIFIC_FIELDS and known_entities:
            # 엔티티별 GU (알려진 엔티티 중 커버 안된 것)
            for slug in known_entities:
                entity_key = f"{domain}:{cat}:{slug}"
                # 이미 해당 슬롯에 KU가 있는지 확인
                has_ku = any(
                    ku for ku in kus
                    if ku.get("entity_key") == entity_key
                    and ku.get("field") == field
                    and ku.get("status") in ("active", "disputed")
                )
                if has_ku:
                    # KU가 있으면 세부 gap_type 재판정
                    slot_gap = _determine_gap_type_for_entity(
                        entity_key, field, kus, today
                    )
                    if slot_gap is None:
                        continue
                    gap_type_local = slot_gap
                else:
                    gap_type_local = "missing"

                if _is_excluded(entity_key, scope_boundary):
                    continue

                raw_gus.append({
                    "gap_type": gap_type_local,
                    "target": {"entity_key": entity_key, "field": field},
                    "expected_utility": expected_utility,
                    "risk_level": risk_level,
                    "resolution_criteria": f"{slug} {field} 정보 수집/검증",
                    "status": "open",
                    "category": cat,
                })
        else:
            # 와일드카드 (엔티티 없거나 generic 필드)
            entity_key = f"{domain}:{cat}:*"
            if _is_excluded(entity_key, scope_boundary):
                continue
            raw_gus.append({
                "gap_type": gap_type,
                "target": {"entity_key": entity_key, "field": field},
                "expected_utility": expected_utility,
                "risk_level": risk_level,
                "resolution_criteria": f"{cat} {field} 정보 수집",
                "status": "open",
                "category": cat,
            })

    # 중복 제거 (entity_key + field 기준)
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for gu in raw_gus:
        key = (gu["target"]["entity_key"], gu["target"]["field"])
        if key not in seen:
            seen.add(key)
            deduped.append(gu)

    # 4단계: 우선순위 정렬
    deduped.sort(key=lambda g: (
        _UTILITY_ORDER.get(g["expected_utility"], 99),
        _RISK_ORDER.get(g["risk_level"], 99),
        g["category"],
    ))

    # 카테고리당 상한 적용
    capped: list[dict[str, Any]] = []
    for gu in deduped:
        cat = gu["category"]
        if cat_counts[cat] < per_cat_cap:
            capped.append(gu)
            cat_counts[cat] += 1

    # 최소 커버리지 보장: 빈 카테고리에 최소 1개
    for cat in categories:
        if cat_counts[cat] == 0:
            # 해당 카테고리의 첫 번째 필드로 GU 추가
            cat_fields = [
                f["name"] for f in skeleton.get("fields", [])
                if "*" in f.get("categories", []) or cat in f.get("categories", [])
            ]
            if cat_fields:
                field = cat_fields[0]
                risk_level = _determine_risk_level(cat, field)
                expected_utility = _determine_expected_utility(risk_level, field, cat)
                capped.append({
                    "gap_type": "missing",
                    "target": {"entity_key": f"{domain}:{cat}:*", "field": field},
                    "expected_utility": expected_utility,
                    "risk_level": risk_level,
                    "resolution_criteria": f"{cat} {field} 정보 수집",
                    "status": "open",
                    "category": cat,
                })
                cat_counts[cat] += 1

    # 최종 정렬 + GU ID 부여
    capped.sort(key=lambda g: (
        _UTILITY_ORDER.get(g["expected_utility"], 99),
        _RISK_ORDER.get(g["risk_level"], 99),
        g["category"],
    ))

    gap_map: list[dict[str, Any]] = []
    for i, gu in enumerate(capped, start=1):
        gu_entry = {
            "gu_id": f"GU-{i:04d}",
            "gap_type": gu["gap_type"],
            "target": gu["target"],
            "expected_utility": gu["expected_utility"],
            "risk_level": gu["risk_level"],
            "resolution_criteria": gu["resolution_criteria"],
            "status": "open",
            "created_at": today.isoformat(),
        }
        gap_map.append(gu_entry)

    # 초기 Metrics
    initial_metrics = {
        "cycle": 0,
        "phase": "seed",
        "timestamp": today.isoformat(),
        "counts": {
            "total_ku": len(kus),
            "active_ku": sum(1 for ku in kus if ku.get("status") == "active"),
            "disputed_ku": sum(1 for ku in kus if ku.get("status") == "disputed"),
            "deprecated_ku": sum(1 for ku in kus if ku.get("status") == "deprecated"),
            "total_gu_open": len(gap_map),
            "total_gu_resolved": 0,
            "total_gu_deferred": 0,
        },
        "rates": {
            "evidence_rate": 0.0,
            "multi_evidence_rate": 0.0,
            "gap_resolution_rate": 0.0,
            "conflict_rate": 0.0,
            "avg_confidence": 0.0,
            "staleness_risk": 0,
        },
    }

    # rates를 실제 값으로 계산
    from src.utils.metrics import compute_metrics
    actual_rates = compute_metrics(
        {"knowledge_units": kus, "gap_map": gap_map},
        today=today,
    )
    initial_metrics["rates"] = actual_rates

    return {
        "gap_map": gap_map,
        "metrics": initial_metrics,
        "current_cycle": 1,
    }


def _determine_gap_type_for_entity(
    entity_key: str,
    field: str,
    kus: list[dict],
    today: date,
) -> str | None:
    """특정 entity_key + field 조합의 gap_type 판정."""
    matching = [
        ku for ku in kus
        if ku.get("entity_key") == entity_key
        and ku.get("field") == field
    ]

    if not matching:
        return "missing"

    active = [ku for ku in matching if ku.get("status") == "active"]
    disputed = [ku for ku in matching if ku.get("status") == "disputed"]

    if disputed:
        return "conflicting"

    for ku in active:
        observed = ku.get("observed_at")
        validity = ku.get("validity", {})
        ttl = validity.get("ttl_days")
        if observed and ttl is not None:
            obs_date = date.fromisoformat(observed)
            if obs_date + timedelta(days=ttl) < today:
                return "stale"

    for ku in active:
        if ku.get("confidence", 1.0) < 0.7:
            return "uncertain"

    if active:
        return None  # Gap 아님

    return "missing"
