"""hitl_gate_node — Silver HITL Gate (Human-in-the-Loop).

Silver 세대: HITL-S (Seed) / HITL-R (Remodel stub) / HITL-E (Exception).
Bronze HITL-A/B/C/D 는 제거 (P0-C5). deprecated gate 호출 시 warning + auto-approve.
"""

from __future__ import annotations

import logging
import warnings
from typing import Any

from src.state import EvolverState

logger = logging.getLogger(__name__)

# Silver 유효 gate 목록
_SILVER_GATES = {"S", "R", "E"}
_DEPRECATED_GATES = {"A", "B", "C", "D"}


def _build_gate_payload(gate: str, state: EvolverState) -> dict:
    """Gate 유형별 검토 데이터 구성."""
    if gate == "S":
        return {
            "gate": "S",
            "description": "Seed 승인 (phase 첫 cycle)",
            "domain_skeleton": state.get("domain_skeleton", {}),
            "knowledge_units_count": len(state.get("knowledge_units", [])),
            "gap_map_count": len(state.get("gap_map", [])),
            "cycle": state.get("current_cycle", 0),
        }
    elif gate == "R":
        return {
            "gate": "R",
            "description": "Remodel 제안 승인 (stub — P2 실구현)",
        }
    elif gate == "E":
        from src.utils.metrics_guard import should_auto_pause
        pause_result = should_auto_pause(state)
        return {
            "gate": "E",
            "description": "Exception auto-pause",
            "violations": pause_result.violations,
            "cycle": state.get("current_cycle", 0),
            "collect_failure_rate": state.get("collect_failure_rate", 0.0),
        }
    return {"gate": gate, "description": "Unknown gate"}


def _handle_response(
    response: dict,
    gate: str,
    state: EvolverState,
) -> dict:
    """Gate 응답 처리."""
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
        if gate == "S" and "modified_skeleton" in response:
            result["domain_skeleton"] = response["modified_skeleton"]
        return result

    return {"hitl_pending": None}


def hitl_gate_node(
    state: EvolverState,
    *,
    response: dict | None = None,
) -> dict:
    """Silver HITL Gate 처리.

    S/R/E 만 유효. A/B/C/D 호출 시 deprecation warning + auto-approve.

    Args:
        response: 사용자 응답. None이면 자동 승인.
    """
    hitl_pending = state.get("hitl_pending")
    gate = hitl_pending.get("gate") if hitl_pending else None

    if gate is None:
        return {"hitl_pending": None}

    # Deprecated gate 처리
    if gate in _DEPRECATED_GATES:
        warnings.warn(
            f"HITL gate '{gate}' is deprecated in Silver. Auto-approving.",
            DeprecationWarning,
            stacklevel=2,
        )
        logger.warning("Deprecated HITL gate '%s' called — auto-approve", gate)
        return {"hitl_pending": None}

    _build_gate_payload(gate, state)

    if response is None:
        response = {"action": "approve"}

    return _handle_response(response, gate, state)
