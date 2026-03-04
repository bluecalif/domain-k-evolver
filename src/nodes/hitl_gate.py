"""hitl_gate_node — HITL Gate (Human-in-the-Loop).

LangGraph interrupt() 기반. Gate A~E.
design-v2 §9 기반.
"""

from __future__ import annotations

from typing import Any

from src.state import EvolverState

HIGH_RISK_LEVELS = {"safety", "financial", "policy"}


def _should_trigger_gate(state: EvolverState) -> str | None:
    """Gate 발동 여부 판정.

    Returns:
        Gate 유형 ("A" ~ "E") 또는 None.
    """
    hitl_pending = state.get("hitl_pending")
    if hitl_pending and hitl_pending.get("gate"):
        return hitl_pending["gate"]
    return None


def _build_gate_payload(gate: str, state: EvolverState) -> dict:
    """Gate 유형별 검토 데이터 구성."""
    if gate == "A":
        return {
            "gate": "A",
            "description": "Plan 승인",
            "plan_summary": _summarize_plan(state.get("current_plan", {})),
        }
    elif gate == "B":
        claims = state.get("current_claims", [])
        high_risk = [
            c for c in claims
            if c.get("risk_flag") or c.get("risk_level", "") in HIGH_RISK_LEVELS
        ]
        return {
            "gate": "B",
            "description": "High-risk Claims 검토",
            "high_risk_claims": high_risk,
            "total_claims": len(claims),
        }
    elif gate == "C":
        kus = state.get("knowledge_units", [])
        disputed = [ku for ku in kus if ku.get("status") == "disputed"]
        return {
            "gate": "C",
            "description": "Conflict Adjudication",
            "disputed_kus": disputed,
        }
    elif gate == "D":
        return {
            "gate": "D",
            "description": "Executive Audit (10 Cycle)",
            "metrics": state.get("metrics", {}),
            "cycle": state.get("current_cycle", 0),
        }
    elif gate == "E":
        return {
            "gate": "E",
            "description": "Convergence Guard (연속 Jump)",
            "jump_history": state.get("jump_history", []),
            "cycle": state.get("current_cycle", 0),
        }
    return {"gate": gate, "description": "Unknown gate"}


def _summarize_plan(plan: dict) -> dict:
    """Plan 요약."""
    return {
        "target_count": len(plan.get("target_gaps", [])),
        "target_gaps": plan.get("target_gaps", []),
        "budget": plan.get("budget", 0),
    }


def _handle_response(
    response: dict,
    gate: str,
    state: EvolverState,
) -> dict:
    """Gate 응답 처리.

    Args:
        response: {"action": "approve"|"reject"|"modify", ...}
    """
    action = response.get("action", "approve")

    if action == "approve":
        return {"hitl_pending": None}

    elif action == "reject":
        return {
            "hitl_pending": {
                "gate": gate,
                "result": "rejected",
                "reason": response.get("reason", ""),
            },
        }

    elif action == "modify":
        result: dict[str, Any] = {"hitl_pending": None}
        if gate == "A" and "modified_plan" in response:
            result["current_plan"] = response["modified_plan"]
        elif gate == "C" and "resolutions" in response:
            # disputed KU 해결 적용
            kus = list(state.get("knowledge_units", []))
            for resolution in response["resolutions"]:
                ku_id = resolution.get("ku_id")
                new_status = resolution.get("new_status", "active")
                for ku in kus:
                    if ku.get("ku_id") == ku_id:
                        ku["status"] = new_status
                        break
            result["knowledge_units"] = kus
        return result

    return {"hitl_pending": None}


def hitl_gate_node(
    state: EvolverState,
    *,
    response: dict | None = None,
) -> dict:
    """HITL Gate 처리.

    실제 LangGraph에서는 interrupt()를 사용하지만,
    테스트/단독 실행 시 response 파라미터로 응답을 주입.

    Args:
        response: 사용자 응답. None이면 자동 승인.
    """
    gate = _should_trigger_gate(state)

    if gate is None:
        return {"hitl_pending": None}

    payload = _build_gate_payload(gate, state)

    if response is None:
        # 자동 승인 (테스트/비대화형 모드)
        response = {"action": "approve"}

    return _handle_response(response, gate, state)


def check_gate_conditions(state: EvolverState) -> dict | None:
    """Gate 발동 조건 체크 → hitl_pending 설정.

    Graph 엣지에서 호출하여 Gate 필요 여부 판정.

    Returns:
        hitl_pending dict 또는 None.
    """
    cycle = state.get("current_cycle", 0)
    claims = state.get("current_claims", [])
    kus = state.get("knowledge_units", [])
    jump_history = state.get("jump_history", [])

    # Gate A: 항상 (Plan 후)
    # → Graph 엣지에서 직접 설정

    # Gate B: high-risk claims 존재
    high_risk = [c for c in claims if c.get("risk_flag")]
    if high_risk:
        return {"gate": "B"}

    # Gate C: disputed KU 존재
    disputed = [ku for ku in kus if ku.get("status") == "disputed"]
    if disputed:
        return {"gate": "C"}

    # Gate D: 10 Cycle마다
    if cycle > 0 and cycle % 10 == 0:
        return {"gate": "D"}

    # Gate E: 연속 2 Cycle Jump
    if len(jump_history) >= 2:
        if jump_history[-1] == cycle and jump_history[-2] == cycle - 1:
            return {"gate": "E"}
        if jump_history[-1] == cycle - 1 and jump_history[-2] == cycle - 2:
            return {"gate": "E"}

    return None
