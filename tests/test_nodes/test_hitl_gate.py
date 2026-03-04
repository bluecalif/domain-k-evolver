"""test_hitl_gate — hitl_gate_node 단위 테스트."""

from __future__ import annotations

import pytest

from src.nodes.hitl_gate import check_gate_conditions, hitl_gate_node


class TestHitlGateNode:
    def test_auto_approve(self) -> None:
        state = {"hitl_pending": {"gate": "A"}, "current_plan": {"target_gaps": []}}
        result = hitl_gate_node(state)
        assert result["hitl_pending"] is None

    def test_explicit_approve(self) -> None:
        state = {"hitl_pending": {"gate": "A"}, "current_plan": {}}
        result = hitl_gate_node(state, response={"action": "approve"})
        assert result["hitl_pending"] is None

    def test_reject(self) -> None:
        state = {"hitl_pending": {"gate": "A"}, "current_plan": {}}
        result = hitl_gate_node(state, response={"action": "reject", "reason": "Bad plan"})
        assert result["hitl_pending"]["result"] == "rejected"
        assert result["hitl_pending"]["reason"] == "Bad plan"

    def test_modify_plan(self) -> None:
        state = {"hitl_pending": {"gate": "A"}, "current_plan": {"target_gaps": ["GU-0001"]}}
        modified = {"target_gaps": ["GU-0002"]}
        result = hitl_gate_node(state, response={"action": "modify", "modified_plan": modified})
        assert result["hitl_pending"] is None
        assert result["current_plan"]["target_gaps"] == ["GU-0002"]

    def test_no_gate_pending(self) -> None:
        state = {"hitl_pending": None}
        result = hitl_gate_node(state)
        assert result["hitl_pending"] is None

    def test_gate_b_high_risk(self) -> None:
        state = {
            "hitl_pending": {"gate": "B"},
            "current_claims": [
                {"risk_flag": True, "claim_id": "CL-001"},
                {"risk_flag": False, "claim_id": "CL-002"},
            ],
        }
        result = hitl_gate_node(state, response={"action": "approve"})
        assert result["hitl_pending"] is None

    def test_gate_c_conflict_modify(self) -> None:
        state = {
            "hitl_pending": {"gate": "C"},
            "knowledge_units": [
                {"ku_id": "KU-001", "status": "disputed"},
                {"ku_id": "KU-002", "status": "active"},
            ],
        }
        result = hitl_gate_node(state, response={
            "action": "modify",
            "resolutions": [{"ku_id": "KU-001", "new_status": "active"}],
        })
        assert result["hitl_pending"] is None
        resolved_ku = next(ku for ku in result["knowledge_units"] if ku["ku_id"] == "KU-001")
        assert resolved_ku["status"] == "active"


class TestCheckGateConditions:
    def test_gate_b_high_risk_claims(self) -> None:
        state = {
            "current_cycle": 1,
            "current_claims": [{"risk_flag": True}],
            "knowledge_units": [],
            "jump_history": [],
        }
        result = check_gate_conditions(state)
        assert result is not None
        assert result["gate"] == "B"

    def test_gate_c_disputed(self) -> None:
        state = {
            "current_cycle": 1,
            "current_claims": [],
            "knowledge_units": [{"status": "disputed"}],
            "jump_history": [],
        }
        result = check_gate_conditions(state)
        assert result is not None
        assert result["gate"] == "C"

    def test_gate_d_every_10_cycles(self) -> None:
        state = {
            "current_cycle": 10,
            "current_claims": [],
            "knowledge_units": [],
            "jump_history": [],
        }
        result = check_gate_conditions(state)
        assert result is not None
        assert result["gate"] == "D"

    def test_gate_e_consecutive_jumps(self) -> None:
        state = {
            "current_cycle": 3,
            "current_claims": [],
            "knowledge_units": [],
            "jump_history": [2, 3],
        }
        result = check_gate_conditions(state)
        assert result is not None
        assert result["gate"] == "E"

    def test_no_gate_needed(self) -> None:
        state = {
            "current_cycle": 1,
            "current_claims": [],
            "knowledge_units": [{"status": "active"}],
            "jump_history": [],
        }
        result = check_gate_conditions(state)
        assert result is None
