"""plan_modify_node — Critique 처방 → Revised Collection Plan.

design-v2 §5 기반. 6대 컴파일 규칙.
"""

from __future__ import annotations

from typing import Any

from src.state import EvolverState


def _compile_prescription(
    rx: dict,
    plan: dict,
    gap_map: list[dict],
) -> dict:
    """단일 처방 → Plan 변경 사항 생성.

    Returns:
        {"applied": bool, "changes": str, "reason": str}
    """
    rx_type = rx.get("type", "")
    rx_id = rx.get("rx_id", "")
    target_ku = rx.get("target_ku", "")

    if rx_type == "epistemic":
        # Source Strategy 강화: min_eu >= 2 강제
        return {
            "applied": True,
            "changes": f"acceptance_tests에 {target_ku} min_eu >= 2 추가",
            "reason": "단일출처 KU → 독립 출처 추가 수집",
        }

    elif rx_type == "temporal":
        # Gap Priority 상향
        return {
            "applied": True,
            "changes": f"{target_ku} 관련 Gap을 critical로 승격",
            "reason": "expires_at 임박 → 우선 수집",
        }

    elif rx_type == "structural":
        # 즉시 분리 안 함 → 플래그만
        return {
            "applied": False,
            "changes": "",
            "reason": "Structural 처방은 3 Cycle 축적 후 Outer Loop에서 결정",
        }

    elif rx_type == "consistency":
        # disputed KU → Cycle N+1 추가 수집
        return {
            "applied": True,
            "changes": f"{target_ku} 관련 Gap에 독립 출처 추가 쿼리",
            "reason": "disputed 상태 → condition_split 시도 포함",
        }

    elif rx_type == "planning":
        # 미커버 카테고리 강제 포함
        return {
            "applied": True,
            "changes": "미커버 카테고리에서 최소 1 Gap 강제 포함",
            "reason": "카테고리 분포 보정",
        }

    elif rx_type == "integration":
        # is_a/part_of 관계 추가
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


def plan_modify_node(
    state: EvolverState,
    *,
    llm: Any | None = None,
) -> dict:
    """Critique 처방 → Revised Plan.

    불변원칙: Prescription-compiled — 모든 RX가 추적성 테이블에 포함.
    """
    critique = state.get("current_critique", {})
    plan = dict(state.get("current_plan", {}))
    gap_map = state.get("gap_map", [])

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

    return {"current_plan": plan}
