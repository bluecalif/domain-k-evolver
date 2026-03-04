"""test_collect — collect_node 단위 테스트."""

from __future__ import annotations

import pytest

from src.nodes.collect import collect_node
from src.tools.search import MockSearchTool


class TestCollectNode:
    def test_with_mock_search(self) -> None:
        tool = MockSearchTool()
        state = {
            "gap_map": [
                {
                    "gu_id": "GU-0001",
                    "status": "open",
                    "target": {"entity_key": "d:a:x", "field": "price"},
                    "expected_utility": "high",
                    "risk_level": "financial",
                    "resolution_criteria": "Find price info",
                },
            ],
            "current_plan": {
                "target_gaps": ["GU-0001"],
                "queries": {"GU-0001": ["x price", "x price 2026"]},
                "budget": 4,
            },
            "current_mode": {"mode": "normal"},
        }
        result = collect_node(state, search_tool=tool)
        claims = result["current_claims"]

        assert len(claims) >= 1
        assert claims[0]["entity_key"] == "d:a:x"
        assert claims[0]["field"] == "price"
        assert claims[0]["source_gu_id"] == "GU-0001"

    def test_search_tool_called(self) -> None:
        tool = MockSearchTool()
        state = {
            "gap_map": [
                {
                    "gu_id": "GU-0001",
                    "status": "open",
                    "target": {"entity_key": "d:a:x", "field": "price"},
                    "expected_utility": "high",
                    "risk_level": "financial",
                },
            ],
            "current_plan": {
                "target_gaps": ["GU-0001"],
                "queries": {"GU-0001": ["q1", "q2"]},
                "budget": 10,
            },
            "current_mode": {"mode": "normal"},
        }
        collect_node(state, search_tool=tool)
        assert len(tool.search_calls) == 2
        assert len(tool.fetch_calls) == 2  # top 2 results fetched

    def test_no_search_tool_returns_empty(self) -> None:
        state = {
            "gap_map": [
                {"gu_id": "GU-0001", "status": "open",
                 "target": {"entity_key": "d:a:x", "field": "y"}},
            ],
            "current_plan": {
                "target_gaps": ["GU-0001"],
                "queries": {"GU-0001": ["q1"]},
                "budget": 2,
            },
            "current_mode": {"mode": "normal"},
        }
        result = collect_node(state)
        assert result["current_claims"] == []

    def test_budget_respected(self) -> None:
        tool = MockSearchTool()
        state = {
            "gap_map": [
                {"gu_id": f"GU-{i:04d}", "status": "open",
                 "target": {"entity_key": f"d:a:x{i}", "field": "price"},
                 "expected_utility": "low", "risk_level": "convenience"}
                for i in range(1, 6)
            ],
            "current_plan": {
                "target_gaps": [f"GU-{i:04d}" for i in range(1, 6)],
                "queries": {f"GU-{i:04d}": [f"q{i}a", f"q{i}b"] for i in range(1, 6)},
                "budget": 4,  # Only 2 targets worth of budget
            },
            "current_mode": {"mode": "normal"},
        }
        collect_node(state, search_tool=tool)
        assert len(tool.search_calls) <= 4

    def test_risk_flag_on_high_risk(self) -> None:
        tool = MockSearchTool()
        state = {
            "gap_map": [
                {"gu_id": "GU-0001", "status": "open",
                 "target": {"entity_key": "d:a:x", "field": "policy"},
                 "expected_utility": "critical", "risk_level": "safety"},
            ],
            "current_plan": {
                "target_gaps": ["GU-0001"],
                "queries": {"GU-0001": ["safety policy"]},
                "budget": 4,
            },
            "current_mode": {"mode": "normal"},
        }
        result = collect_node(state, search_tool=tool)
        for claim in result["current_claims"]:
            assert claim["risk_flag"] is True

    def test_evidence_has_required_fields(self) -> None:
        tool = MockSearchTool()
        state = {
            "gap_map": [
                {"gu_id": "GU-0001", "status": "open",
                 "target": {"entity_key": "d:a:x", "field": "price"},
                 "expected_utility": "high", "risk_level": "financial"},
            ],
            "current_plan": {
                "target_gaps": ["GU-0001"],
                "queries": {"GU-0001": ["q1"]},
                "budget": 4,
            },
            "current_mode": {"mode": "normal"},
        }
        result = collect_node(state, search_tool=tool)
        for claim in result["current_claims"]:
            ev = claim["evidence"]
            assert "eu_id" in ev
            assert "url" in ev
            assert "observed_at" in ev
            assert "credibility" in ev
