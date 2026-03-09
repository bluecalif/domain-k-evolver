"""mode_node — Normal/Jump Mode 판정.

expansion-policy v1.0 §5 기반.
5종 trigger 판정 → Mode 결정 → cap/budget 계산.
"""

from __future__ import annotations

from math import ceil
from typing import Any

from src.state import EvolverState
from src.utils.metrics import compute_axis_coverage, compute_deficit_ratios

# --- 우선순위 상수 ---
HIGH_RISK_LEVELS = {"safety", "financial", "policy"}


def _compute_trigger_t1(
    gap_map: list[dict],
    skeleton: dict,
) -> bool:
    """T1: Axis Under-Coverage — required 축 deficit_ratio > 0."""
    axes = skeleton.get("axes", [])
    if not axes:
        return False

    coverage = compute_axis_coverage(gap_map, skeleton)
    deficits = compute_deficit_ratios(coverage, skeleton)

    for axis_def in axes:
        if axis_def.get("required", False):
            if deficits.get(axis_def["name"], 0.0) > 0:
                return True
    return False


def _compute_trigger_t2(state: EvolverState) -> bool:
    """T2: Spillover — Gap Map 외 슬롯 참조 3건 이상.

    Collect/Integrate에서 발견된 spillover 정보는
    current_critique 또는 별도 필드에 기록된다.
    현재 구현: current_critique.spillover_count로 판정.
    """
    critique = state.get("current_critique") or {}
    spillover = critique.get("spillover_count", 0)
    return spillover >= 3


def _compute_trigger_t3(knowledge_units: list[dict]) -> bool:
    """T3: High-Risk Blindspot — safety/financial/policy 중
    단일출처 + confidence < 0.85 KU가 2건 이상."""
    count = 0
    for ku in knowledge_units:
        if ku.get("status") != "active":
            continue
        # entity_key에서 category 추출하여 risk_level 판단은 복잡하므로
        # evidence_links 수 + confidence로 직접 판정
        evidence_count = len(ku.get("evidence_links", []))
        confidence = ku.get("confidence", 1.0)
        if evidence_count <= 1 and confidence < 0.85:
            count += 1
    return count >= 2


def _compute_trigger_t4(state: EvolverState) -> bool:
    """T4: Prescription — Critique RX에서 구조 보강 명시 1건 이상."""
    critique = state.get("current_critique") or {}
    prescriptions = critique.get("prescriptions", [])
    for rx in prescriptions:
        rx_type = rx.get("type", "")
        if rx_type in ("structural", "planning", "integration"):
            return True
    return False


def _compute_trigger_t5(state: EvolverState) -> bool:
    """T5: Domain Shift — skeleton 미등록 category 수준 엔티티 1건 이상."""
    critique = state.get("current_critique") or {}
    return critique.get("domain_shift_detected", False)


def _get_cycle_stage(cycle: int) -> str:
    """Cycle 단계 판정."""
    if cycle <= 3:
        return "early"
    elif cycle <= 6:
        return "mid"
    else:
        return "converging"


def _compute_audit_bias(audit_history: list[dict]) -> float:
    """최신 Audit findings 기반 explore/exploit bias 계산.

    Returns:
        bias: -0.15 ~ +0.15 범위.
              양수 = explore 증가, 음수 = exploit 증가.
    """
    if not audit_history:
        return 0.0

    latest = audit_history[-1]
    findings = latest.get("findings", [])
    if not findings:
        return 0.0

    coverage_gaps = sum(
        1 for f in findings if f.get("category") == "coverage_gap"
    )
    yield_declines = sum(
        1 for f in findings if f.get("category") == "yield_decline"
    )

    # coverage_gap → explore 증가 (+0.05 per finding, max +0.15)
    # yield_decline → exploit 증가 (-0.10 per finding, max -0.15)
    bias = min(coverage_gaps * 0.05, 0.15) - min(yield_declines * 0.10, 0.15)
    return round(bias, 2)


def _compute_trigger_t6_audit(audit_history: list[dict]) -> bool:
    """T6: Audit Axis Imbalance — 최신 Audit에 axis_imbalance finding 존재."""
    if not audit_history:
        return False
    latest = audit_history[-1]
    return any(
        f.get("category") == "axis_imbalance"
        for f in latest.get("findings", [])
    )


def _compute_trigger_t7_staleness(metrics: dict) -> bool:
    """T7: Staleness Trigger — staleness_risk > 20 → Jump Mode (D-65)."""
    rates = metrics.get("rates", {})
    return rates.get("staleness_risk", 0) > 20


def _compute_budget(
    target_count: int,
    mode: str,
    cycle_stage: str,
    audit_bias: float = 0.0,
) -> tuple[int, int]:
    """explore/exploit budget 배분.

    Args:
        audit_bias: Audit 기반 bias (-0.15 ~ +0.15). 양수=explore↑.

    Returns:
        (explore_budget, exploit_budget)
    """
    if mode == "normal":
        return 0, target_count

    # Jump Mode 배분
    ratios = {
        "early": (0.6, 0.4),
        "mid": (0.5, 0.5),
        "converging": (0.4, 0.6),
    }
    explore_ratio, _ = ratios.get(cycle_stage, (0.5, 0.5))

    # Audit bias 적용 (guardrail: explore_ratio 0.2 ~ 0.8)
    explore_ratio = max(0.2, min(0.8, explore_ratio + audit_bias))

    explore = int(target_count * explore_ratio)
    exploit = target_count - explore  # 홀수 시 exploit에 +1

    return explore, exploit


def mode_node(state: EvolverState) -> dict:
    """Normal/Jump Mode 판정 + cap/budget 계산."""
    gap_map = state.get("gap_map", [])
    skeleton = state.get("domain_skeleton", {})
    kus = state.get("knowledge_units", [])
    cycle = state.get("current_cycle", 1)
    jump_history = list(state.get("jump_history", []))
    audit_history = state.get("audit_history") or []

    open_count = sum(1 for gu in gap_map if gu.get("status") == "open")

    # 7종 trigger 판정 (T1~T6 + T7 Staleness, D-65)
    metrics = state.get("metrics", {})
    triggers: list[str] = []
    if _compute_trigger_t1(gap_map, skeleton):
        triggers.append("T1:axis_under_coverage")
    if _compute_trigger_t2(state):
        triggers.append("T2:spillover")
    if _compute_trigger_t3(kus):
        triggers.append("T3:high_risk_blindspot")
    if _compute_trigger_t4(state):
        triggers.append("T4:prescription")
    if _compute_trigger_t5(state):
        triggers.append("T5:domain_shift")
    if _compute_trigger_t6_audit(audit_history):
        triggers.append("T6:audit_axis_imbalance")
    if _compute_trigger_t7_staleness(metrics):
        triggers.append("T7:staleness_risk")

    # Mode 결정
    mode = "jump" if triggers else "normal"

    # Cap 계산
    if mode == "normal":
        cap = max(4, ceil(open_count * 0.2))
        target_count = max(4, ceil(open_count * 0.4))
    else:
        cap = max(10, ceil(open_count * 0.6))
        target_count = max(10, ceil(open_count * 0.5))

    # Convergence Guard: 연속 2 Cycle Jump 감지
    convergence_warning = False
    if mode == "jump" and len(jump_history) >= 1:
        if jump_history[-1] == cycle - 1:
            convergence_warning = True

    # net_gap_change 3 Cycle 연속 양수 → cap 감쇠
    # (metrics.delta_from_prev_cycle에서 확인, 현재 단순화)

    # Jump 기록 갱신
    if mode == "jump":
        jump_history.append(cycle)

    # Budget 배분 — Audit 기반 bias 적용 (Task 4.7)
    cycle_stage = _get_cycle_stage(cycle)
    audit_bias = _compute_audit_bias(audit_history)
    explore_budget, exploit_budget = _compute_budget(
        target_count, mode, cycle_stage, audit_bias=audit_bias,
    )

    mode_decision: dict[str, Any] = {
        "mode": mode,
        "cap": cap,
        "explore_budget": explore_budget,
        "exploit_budget": exploit_budget,
        "trigger_set": triggers,
    }

    if audit_bias != 0.0:
        mode_decision["audit_bias"] = audit_bias

    if convergence_warning:
        mode_decision["convergence_warning"] = True

    return {
        "current_mode": mode_decision,
        "jump_history": jump_history,
    }
