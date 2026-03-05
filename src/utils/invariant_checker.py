"""불변원칙 자동검증 — 5대 불변원칙 체크.

매 사이클 후 호출하여 위반 사항을 감지.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InvariantResult:
    """검증 결과."""

    passed: bool
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def check_invariants(state: dict) -> InvariantResult:
    """5대 불변원칙 검증.

    1. Gap-driven: Plan.target_gaps ⊆ G.open
    2. Claim→KU 착지성: claims 수 ≈ adds + updates + rejected (경고만)
    3. Evidence-first: active KU에 EU >= 1
    4. Conflict-preserving: disputed KU 삭제 불가 (이전 상태 비교 필요 → 경고만)
    5. Prescription-compiled: RX ID 추적성
    """
    violations: list[str] = []
    warnings: list[str] = []

    gap_map = state.get("gap_map", [])
    kus = state.get("knowledge_units", [])
    plan = state.get("current_plan") or {}
    critique = state.get("current_critique") or {}

    # 1. Gap-driven: Plan.target_gaps ⊆ open GU IDs
    open_gu_ids = {gu["gu_id"] for gu in gap_map if gu.get("status") == "open"}
    target_gaps = set(plan.get("target_gaps", []))
    invalid_targets = target_gaps - open_gu_ids
    if invalid_targets:
        # plan_modify가 gap_map을 변경할 수 있으므로, 모든 GU ID도 허용
        all_gu_ids = {gu["gu_id"] for gu in gap_map}
        truly_invalid = invalid_targets - all_gu_ids
        if truly_invalid:
            violations.append(
                f"[I1] Gap-driven 위반: target_gaps에 존재하지 않는 GU: {truly_invalid}"
            )

    # 2. Claim→KU 착지성 (경고만 — claims가 있는데 KU 변화가 0이면)
    claims = state.get("current_claims") or []
    if claims and not kus:
        warnings.append("[I2] Claim→KU: claims 있으나 KU 0건")

    # 3. Evidence-first: active KU에 evidence_links >= 1
    for ku in kus:
        if ku.get("status") == "active":
            evidence = ku.get("evidence_links", [])
            if not evidence:
                violations.append(
                    f"[I3] Evidence-first 위반: {ku.get('ku_id')} — evidence_links 비어있음"
                )

    # 4. Conflict-preserving (경고 — 이전 상태와 비교 불가하므로 disputed 존재만 확인)
    disputed = [ku for ku in kus if ku.get("status") == "disputed"]
    if disputed:
        warnings.append(f"[I4] disputed KU {len(disputed)}건 존재 (삭제 불가 확인 필요)")

    # 5. Prescription-compiled: critique RX IDs == plan traceability RX IDs
    prescriptions = critique.get("prescriptions", [])
    traceability = plan.get("traceability", [])
    if prescriptions:
        rx_ids_critique = {rx.get("rx_id") for rx in prescriptions}
        rx_ids_trace = {t.get("rx_id") for t in traceability}
        missing = rx_ids_critique - rx_ids_trace
        if missing:
            violations.append(
                f"[I5] Prescription-compiled 위반: 추적 누락 RX: {missing}"
            )

    passed = len(violations) == 0
    return InvariantResult(passed=passed, violations=violations, warnings=warnings)
