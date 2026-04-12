"""test_hitl_gate — Silver hitl_gate_node 단위 테스트.

P0-C5 반영: HITL-A/B/C/D 제거, HITL-S/R/E 유효.
Deprecated gate 호출 시 DeprecationWarning + auto-approve.
"""

from __future__ import annotations

import warnings

import pytest

from src.nodes.hitl_gate import hitl_gate_node


class TestHitlGateNodeSilver:
    """Silver HITL-S / HITL-R / HITL-E 단위 테스트."""

    def test_no_gate_pending(self) -> None:
        state = {"hitl_pending": None}
        result = hitl_gate_node(state)
        assert result["hitl_pending"] is None

    # -- Gate S (Seed 승인) --

    def test_gate_s_auto_approve(self) -> None:
        state = {
            "hitl_pending": {"gate": "S"},
            "domain_skeleton": {"domain": "japan-travel"},
            "knowledge_units": [],
            "gap_map": [{"gu_id": "GU-0001"}],
            "current_cycle": 1,
        }
        result = hitl_gate_node(state)
        assert result["hitl_pending"] is None

    def test_gate_s_explicit_approve(self) -> None:
        state = {
            "hitl_pending": {"gate": "S"},
            "domain_skeleton": {"domain": "japan-travel"},
        }
        result = hitl_gate_node(state, response={"action": "approve"})
        assert result["hitl_pending"] is None

    def test_gate_s_reject(self) -> None:
        state = {
            "hitl_pending": {"gate": "S"},
            "domain_skeleton": {"domain": "japan-travel"},
        }
        result = hitl_gate_node(
            state, response={"action": "reject", "reason": "Skeleton incomplete"},
        )
        assert result["hitl_pending"]["result"] == "rejected"
        assert result["hitl_pending"]["reason"] == "Skeleton incomplete"

    def test_gate_s_modify_skeleton(self) -> None:
        state = {
            "hitl_pending": {"gate": "S"},
            "domain_skeleton": {"domain": "japan-travel", "version": 1},
        }
        modified = {"domain": "japan-travel", "version": 2, "categories": []}
        result = hitl_gate_node(
            state, response={"action": "modify", "modified_skeleton": modified},
        )
        assert result["hitl_pending"] is None
        assert result["domain_skeleton"]["version"] == 2

    # -- Gate R (Remodel stub, P2) --

    def test_gate_r_auto_approve_stub(self) -> None:
        state = {"hitl_pending": {"gate": "R"}}
        result = hitl_gate_node(state)
        assert result["hitl_pending"] is None

    # -- Gate E (Exception auto-pause) --

    def test_gate_e_auto_approve(self) -> None:
        state = {
            "hitl_pending": {"gate": "E"},
            "metrics": {"rates": {
                "conflict_rate": 0.30,  # > 0.25
                "evidence_rate": 0.80,
                "avg_confidence": 0.8,
                "staleness_ratio": 0.1,
            }},
            "collect_failure_rate": 0.0,
        }
        result = hitl_gate_node(state)
        assert result["hitl_pending"] is None

    def test_gate_e_reject(self) -> None:
        state = {
            "hitl_pending": {"gate": "E"},
            "metrics": {"rates": {"conflict_rate": 0.30}},
            "collect_failure_rate": 0.0,
        }
        result = hitl_gate_node(
            state, response={"action": "reject", "reason": "Halt"},
        )
        assert result["hitl_pending"]["result"] == "rejected"


class TestDeprecatedGates:
    """Bronze HITL-A/B/C/D: deprecated — warning + auto-approve."""

    @pytest.mark.parametrize("gate", ["A", "B", "C", "D"])
    def test_deprecated_gate_auto_approves(self, gate: str) -> None:
        state = {"hitl_pending": {"gate": gate}}
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = hitl_gate_node(state)
        assert result["hitl_pending"] is None
        assert any(
            issubclass(w.category, DeprecationWarning) for w in caught
        ), f"Gate {gate} should emit DeprecationWarning"
