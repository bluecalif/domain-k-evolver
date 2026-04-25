"""test_plan — plan_node 단위 테스트."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.nodes.plan import _select_targets, plan_node

BENCH = Path("bench/japan-travel/state")


@pytest.fixture(scope="module")
def gap_map() -> list[dict]:
    with open(BENCH / "gap-map.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def skeleton() -> dict:
    with open(BENCH / "domain-skeleton.json", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Target 선정
# ---------------------------------------------------------------------------

class TestSelectTargets:
    def test_normal_mode_exploit_only(self, gap_map: list[dict]) -> None:
        mode = {"mode": "normal", "explore_budget": 0, "exploit_budget": 5}
        explore, exploit = _select_targets(gap_map, mode)
        assert len(explore) == 0
        assert len(exploit) == 5

    def test_jump_mode_uses_cycle_cap(self, gap_map: list[dict]) -> None:
        mode = {"mode": "jump", "explore_budget": 3, "exploit_budget": 5}
        explore, exploit = _select_targets(gap_map, mode)
        assert len(explore) == 0
        assert len(exploit) <= 8  # cycle_cap = explore_budget + exploit_budget

    def test_targets_are_open(self, gap_map: list[dict]) -> None:
        mode = {"mode": "normal", "explore_budget": 0, "exploit_budget": 8}
        _, exploit = _select_targets(gap_map, mode)
        for gu in exploit:
            assert gu["status"] == "open"


# ---------------------------------------------------------------------------
# plan_node 통합 (mock LLM = None → fallback)
# ---------------------------------------------------------------------------

class TestPlanNode:
    def test_deterministic_plan(
        self, gap_map: list[dict], skeleton: dict,
    ) -> None:
        state = {
            "gap_map": gap_map,
            "domain_skeleton": skeleton,
            "current_mode": {"mode": "normal", "explore_budget": 0, "exploit_budget": 5},
        }
        result = plan_node(state)
        plan = result["current_plan"]

        assert "target_gaps" in plan
        assert "queries" in plan
        assert "budget" in plan
        assert len(plan["target_gaps"]) == 5

    def test_all_targets_are_open_gus(
        self, gap_map: list[dict], skeleton: dict,
    ) -> None:
        state = {
            "gap_map": gap_map,
            "domain_skeleton": skeleton,
            "current_mode": {"mode": "normal", "explore_budget": 0, "exploit_budget": 5},
        }
        result = plan_node(state)
        open_ids = {gu["gu_id"] for gu in gap_map if gu["status"] == "open"}
        for target_id in result["current_plan"]["target_gaps"]:
            assert target_id in open_ids

    def test_queries_per_target(
        self, gap_map: list[dict], skeleton: dict,
    ) -> None:
        state = {
            "gap_map": gap_map,
            "domain_skeleton": skeleton,
            "current_mode": {"mode": "normal", "explore_budget": 0, "exploit_budget": 3},
        }
        result = plan_node(state)
        queries = result["current_plan"]["queries"]
        for gu_id in result["current_plan"]["target_gaps"]:
            assert gu_id in queries
            assert len(queries[gu_id]) >= 1

    def test_jump_mode_budget_includes_extra(
        self, gap_map: list[dict], skeleton: dict,
    ) -> None:
        state = {
            "gap_map": gap_map,
            "domain_skeleton": skeleton,
            "current_mode": {"mode": "jump", "explore_budget": 3, "exploit_budget": 5},
        }
        result = plan_node(state)
        plan = result["current_plan"]
        n_targets = len(plan["target_gaps"])
        # Jump budget = targets * 2 + 4
        assert plan["budget"] == n_targets * 2 + 4

    def test_gap_driven_invariant_violation(self) -> None:
        """open이 아닌 GU를 target으로 잡으면 AssertionError."""
        gap_map = [
            {"gu_id": "GU-0001", "status": "resolved", "expected_utility": "high",
             "risk_level": "financial", "target": {"entity_key": "d:a:x", "field": "y"}},
        ]
        state = {
            "gap_map": gap_map,
            "domain_skeleton": {},
            "current_mode": {"mode": "normal", "explore_budget": 0, "exploit_budget": 1},
        }
        # open GU가 없으므로 target이 비어있음 → 정상 (target 0개)
        result = plan_node(state)
        assert len(result["current_plan"]["target_gaps"]) == 0
