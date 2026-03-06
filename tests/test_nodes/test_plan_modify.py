"""test_plan_modify — plan_modify_node 단위 테스트."""

from __future__ import annotations

import pytest

from src.nodes.plan_modify import plan_modify_node


class TestPlanModifyNode:
    def test_traceability_table(self) -> None:
        state = {
            "current_critique": {
                "prescriptions": [
                    {"rx_id": "RX-0001", "type": "epistemic", "target_ku": "KU-0001"},
                    {"rx_id": "RX-0002", "type": "consistency", "target_ku": "KU-0007"},
                ],
            },
            "current_plan": {"target_gaps": ["GU-0001"]},
            "gap_map": [],
        }
        result = plan_modify_node(state)
        plan = result["current_plan"]

        assert plan["revised"] is True
        assert len(plan["traceability"]) == 2

        # 모든 RX가 추적성 테이블에 포함
        rx_ids = {t["rx_id"] for t in plan["traceability"]}
        assert rx_ids == {"RX-0001", "RX-0002"}

    def test_epistemic_applied(self) -> None:
        state = {
            "current_critique": {
                "prescriptions": [
                    {"rx_id": "RX-0001", "type": "epistemic", "target_ku": "KU-001"},
                ],
            },
            "current_plan": {"target_gaps": []},
            "gap_map": [
                {"gu_id": "GU-0001", "status": "open",
                 "target": {"entity_key": "d:cat:slug", "field": "f"}},
            ],
        }
        result = plan_modify_node(state)
        trace = result["current_plan"]["traceability"][0]
        assert trace["applied"] is True

    def test_structural_deferred(self) -> None:
        state = {
            "current_critique": {
                "prescriptions": [
                    {"rx_id": "RX-0001", "type": "structural"},
                ],
            },
            "current_plan": {},
            "gap_map": [],
        }
        result = plan_modify_node(state)
        trace = result["current_plan"]["traceability"][0]
        assert trace["applied"] is False
        assert "3 Cycle" in trace["reason"]

    def test_no_prescriptions(self) -> None:
        state = {
            "current_critique": {"prescriptions": []},
            "current_plan": {"target_gaps": ["GU-0001"]},
            "gap_map": [],
        }
        result = plan_modify_node(state)
        assert result["current_plan"]["revised"] is True
        assert len(result["current_plan"]["traceability"]) == 0

    def test_prescription_compiled_invariant(self) -> None:
        """불변원칙: Prescription-compiled."""
        state = {
            "current_critique": {
                "prescriptions": [
                    {"rx_id": "RX-0001", "type": "temporal", "target_ku": "KU-001"},
                    {"rx_id": "RX-0002", "type": "planning"},
                    {"rx_id": "RX-0003", "type": "integration"},
                ],
            },
            "current_plan": {},
            "gap_map": [],
        }
        result = plan_modify_node(state)
        rx_ids = {t["rx_id"] for t in result["current_plan"]["traceability"]}
        assert rx_ids == {"RX-0001", "RX-0002", "RX-0003"}

    def test_dispute_resolved_applied(self) -> None:
        """dispute_resolved 처방 처리."""
        state = {
            "current_critique": {
                "prescriptions": [
                    {"rx_id": "RX-0001", "type": "dispute_resolved",
                     "target_ku": "KU-001",
                     "description": "KU-001: disputed→active 해소"},
                ],
            },
            "current_plan": {},
            "gap_map": [],
        }
        result = plan_modify_node(state)
        trace = result["current_plan"]["traceability"][0]
        assert trace["applied"] is True
        assert "해소 완료" in trace["changes"]
