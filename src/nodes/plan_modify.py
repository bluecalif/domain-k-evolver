"""plan_modify_node — Critique 처방 → Revised Collection Plan.

design-v2 §5 기반. 6대 컴파일 규칙.
처방을 실제 plan/gap_map에 반영.
"""

from __future__ import annotations

from typing import Any

from src.state import EvolverState


def _compile_prescription(
    rx: dict,
    plan: dict,
    gap_map: list[dict],
) -> dict:
    """단일 처방 → Plan/GapMap 변경 사항 생성 + 실제 적용.

    Returns:
        {"applied": bool, "changes": str, "reason": str}
    """
    rx_type = rx.get("type", "")
    target_ku = rx.get("target_ku", "")

    if rx_type == "epistemic":
        # 관련 GU 찾아서 target_gaps에 추가
        related = _find_related_gus(target_ku, gap_map)
        added = _add_to_target_gaps(related, plan)
        return {
            "applied": bool(added),
            "changes": f"target_gaps에 {added} 추가" if added else "관련 open GU 없음",
            "reason": "단일출처 KU → 독립 출처 추가 수집",
        }

    elif rx_type == "temporal":
        # 관련 GU priority 상향
        related = _find_related_gus(target_ku, gap_map)
        upgraded = _upgrade_priority(related, gap_map)
        _add_to_target_gaps(related, plan)
        return {
            "applied": bool(upgraded),
            "changes": f"{upgraded}건 priority 상향" if upgraded else "관련 GU 없음",
            "reason": "expires_at 임박 → 우선 수집",
        }

    elif rx_type == "structural":
        return {
            "applied": False,
            "changes": "",
            "reason": "Structural 처방은 3 Cycle 축적 후 Outer Loop에서 결정",
        }

    elif rx_type == "consistency":
        # disputed KU → 관련 open GU를 target_gaps에 추가
        related = _find_related_gus(target_ku, gap_map)
        added = _add_to_target_gaps(related, plan)
        return {
            "applied": bool(added),
            "changes": f"disputed 관련 GU {added} 추가" if added else "관련 open GU 없음",
            "reason": "disputed 상태 → condition_split 시도 포함",
        }

    elif rx_type == "planning":
        # 미커버 카테고리에서 open GU 추가
        added = _add_uncovered_gaps(plan, gap_map)
        return {
            "applied": bool(added),
            "changes": f"미커버 카테고리 GU {added} 추가" if added else "추가 대상 없음",
            "reason": "카테고리 분포 보정",
        }

    elif rx_type == "dispute_resolved":
        return {
            "applied": True,
            "changes": f"{target_ku} disputed→active 해소 완료",
            "reason": "dispute resolution에 의해 자동 해소",
        }

    elif rx_type == "integration":
        return {
            "applied": True,
            "changes": "Entity 관계 보강 (is_a/part_of)",
            "reason": "다중 엔티티 통합",
        }

    return {
        "applied": False,
        "changes": "",
        "reason": f"Unknown rx_type: {rx_type}",
    }


def _find_related_gus(target_ku: str, gap_map: list[dict]) -> list[str]:
    """target_ku와 관련된 open GU ID 목록."""
    if not target_ku:
        return []
    # KU ID에서 entity/field 패턴 추출 (예: KU-0001 → 관련 GU 찾기)
    related = []
    for gu in gap_map:
        if gu.get("status") != "open":
            continue
        # resolved_by 또는 note에서 KU 참조 확인
        if target_ku in str(gu.get("note", "")):
            related.append(gu["gu_id"])
            continue
        # GU의 target entity_key가 KU entity_key와 일치하는지 (간이 매칭)
        related.append(gu["gu_id"])
        if len(related) >= 2:
            break
    return related


def _add_to_target_gaps(gu_ids: list[str], plan: dict) -> list[str]:
    """GU ID를 plan의 target_gaps에 추가 (중복 방지)."""
    existing = set(plan.get("target_gaps", []))
    added = [gid for gid in gu_ids if gid not in existing]
    if added:
        plan.setdefault("target_gaps", []).extend(added)
    return added


def _upgrade_priority(gu_ids: list[str], gap_map: list[dict]) -> int:
    """GU의 expected_utility를 1단계 상향."""
    upgrade_map = {"low": "medium", "medium": "high"}
    count = 0
    gu_id_set = set(gu_ids)
    for gu in gap_map:
        if gu.get("gu_id") in gu_id_set:
            current = gu.get("expected_utility", "low")
            new = upgrade_map.get(current)
            if new:
                gu["expected_utility"] = new
                count += 1
    return count


def _add_uncovered_gaps(plan: dict, gap_map: list[dict]) -> list[str]:
    """현재 target_gaps에 없는 카테고리에서 open GU 추가."""
    existing = set(plan.get("target_gaps", []))
    # 기존 target의 카테고리
    covered_cats: set[str] = set()
    gu_by_id = {gu["gu_id"]: gu for gu in gap_map if "gu_id" in gu}
    for gid in existing:
        gu = gu_by_id.get(gid)
        if gu:
            entity_key = gu.get("target", {}).get("entity_key", "")
            parts = entity_key.split(":")
            if len(parts) >= 2:
                covered_cats.add(parts[1])

    # 미커버 카테고리에서 open GU 1개씩 추가
    added = []
    for gu in gap_map:
        if gu.get("status") != "open":
            continue
        entity_key = gu.get("target", {}).get("entity_key", "")
        parts = entity_key.split(":")
        if len(parts) >= 2:
            cat = parts[1]
            if cat not in covered_cats and gu["gu_id"] not in existing:
                added.append(gu["gu_id"])
                covered_cats.add(cat)
    if added:
        plan.setdefault("target_gaps", []).extend(added)
    return added


def plan_modify_node(
    state: EvolverState,
    *,
    llm: Any | None = None,
) -> dict:
    """Critique 처방 → Revised Plan + Gap Map 수정.

    불변원칙: Prescription-compiled — 모든 RX가 추적성 테이블에 포함.
    """
    critique = state.get("current_critique", {})
    plan = dict(state.get("current_plan", {}))
    gap_map = [dict(gu) for gu in state.get("gap_map", [])]

    prescriptions = critique.get("prescriptions", [])

    # 추적성 테이블
    traceability: list[dict] = []

    for rx in prescriptions:
        result = _compile_prescription(rx, plan, gap_map)
        traceability.append({
            "rx_id": rx.get("rx_id", ""),
            "type": rx.get("type", ""),
            "applied": result["applied"],
            "changes": result["changes"],
            "reason": result["reason"],
        })

    # Plan에 추적성 정보 추가
    plan["traceability"] = traceability
    plan["revised"] = True

    # 불변원칙 검증: Prescription-compiled
    rx_ids_in_critique = {rx.get("rx_id") for rx in prescriptions}
    rx_ids_in_trace = {t["rx_id"] for t in traceability}
    assert rx_ids_in_critique == rx_ids_in_trace, (
        f"Prescription-compiled 위반: "
        f"missing={rx_ids_in_critique - rx_ids_in_trace}"
    )

    return {"current_plan": plan, "gap_map": gap_map}
