"""test_plan — plan_node 단위 테스트."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.nodes.plan import CYCLE_CAP, _select_targets, plan_node

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
    def test_normal_mode_returns_all_open(self, gap_map: list[dict]) -> None:
        """S1-T2: normal mode → explore 없음, 모든 open GU 반환 (budget 상한 없음)."""
        open_count = sum(1 for gu in gap_map if gu.get("status") == "open")
        mode = {"mode": "normal"}
        explore, exploit = _select_targets(gap_map, mode)
        assert len(explore) == 0
        assert len(exploit) == open_count

    def test_jump_mode_split(self, gap_map: list[dict]) -> None:
        """S1-T2: jump mode → explore + exploit = 모든 open GU (budget 상한 없음)."""
        open_count = sum(1 for gu in gap_map if gu.get("status") == "open")
        mode = {"mode": "jump"}
        explore, exploit = _select_targets(gap_map, mode)
        assert len(explore) + len(exploit) == open_count

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
        """S1-T2: plan target_gaps = 모든 open GU (exploit_budget 상한 무시)."""
        open_count = sum(1 for gu in gap_map if gu.get("status") == "open")
        state = {
            "gap_map": gap_map,
            "domain_skeleton": skeleton,
            "current_mode": {"mode": "normal"},
        }
        result = plan_node(state)
        plan = result["current_plan"]

        assert "target_gaps" in plan
        assert "queries" in plan
        assert "budget" in plan
        assert len(plan["target_gaps"]) == open_count

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


# ---------------------------------------------------------------------------
# D-129 Regression Guard (S1-T7) — plan-side
# ---------------------------------------------------------------------------

class TestD129RegressionGuardPlan:
    """D-129: _select_targets 에서 exploit_budget 으로 target 수를 cap하지 않음.

    위반 패턴:
      - _select_targets 내부에서 open_gus = open_gus[:exploit_budget] 복귀
      - mode_decision 의 exploit_budget 이 cap 역할 재도입
    """

    def test_exploit_budget_does_not_cap_targets(self) -> None:
        """exploit_budget=3 이어도 open GU 가 10개면 10개 모두 반환해야 함."""
        gap_map = [
            {"gu_id": f"GU-{i:04d}", "status": "open",
             "target": {"entity_key": f"d:a:x{i}", "field": "f"},
             "risk_level": "convenience"}
            for i in range(10)
        ]
        mode = {"mode": "normal", "explore_budget": 0, "exploit_budget": 3}
        _, exploit = _select_targets(gap_map, mode)
        assert len(exploit) == 10, (
            f"D-129 regression (plan): exploit_budget=3 이 cap 역할을 함. "
            f"expected 10, got {len(exploit)}"
        )

    def test_cap_field_controls_selection(self) -> None:
        """mode_decision 의 cap 필드만이 target 수를 제한해야 함."""
        gap_map = [
            {"gu_id": f"GU-{i:04d}", "status": "open",
             "target": {"entity_key": f"d:a:x{i}", "field": "f"},
             "risk_level": "convenience"}
            for i in range(20)
        ]
        mode_no_cap = {"mode": "normal"}
        mode_with_cap = {"mode": "normal", "cap": 7}

        _, exploit_no_cap = _select_targets(gap_map, mode_no_cap)
        _, exploit_with_cap = _select_targets(gap_map, mode_with_cap)

        assert len(exploit_no_cap) == 20, f"cap 미지정 → CYCLE_CAP({CYCLE_CAP}) 이내 전체 반환해야 함"
        assert len(exploit_with_cap) == 7, f"cap=7 → 7개만 반환해야 함"
