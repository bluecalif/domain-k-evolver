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


# ---------------------------------------------------------------------------
# S1-T8: deferred_targets 우선 소진 (선-FIFO)
# ---------------------------------------------------------------------------

class TestDeferredTargetsPriority:
    """이전 cycle 에서 defer 된 GU 가 다음 cycle plan 에서 앞에 배치되는지 검증."""

    def _make_gu(self, gu_id: str, entity_key: str = None) -> dict:
        return {
            "gu_id": gu_id,
            "status": "open",
            "target": {"entity_key": entity_key or f"d:a:{gu_id}", "field": "f"},
            "risk_level": "convenience",
        }

    def test_deferred_gus_placed_first(self) -> None:
        """deferred_targets 에 있는 GU 가 plan target_gaps 앞에 위치해야 함."""
        deferred_ids = ["GU-0003", "GU-0004"]
        gap_map = [self._make_gu(f"GU-{i:04d}") for i in range(1, 6)]
        state = {
            "gap_map": gap_map,
            "domain_skeleton": {},
            "current_mode": {"mode": "normal"},
            "deferred_targets": deferred_ids,
        }
        result = plan_node(state)
        target_gaps = result["current_plan"]["target_gaps"]

        # 처음 2개가 deferred GU 여야 함 (FIFO 순서 보존)
        assert target_gaps[:2] == deferred_ids, (
            f"deferred_targets 가 앞에 배치되지 않음: {target_gaps[:4]}"
        )

    def test_deferred_fifo_order_preserved(self) -> None:
        """deferred 순서(FIFO)가 plan 에서 보존되어야 함."""
        deferred_ids = ["GU-0005", "GU-0002", "GU-0004"]
        gap_map = [self._make_gu(f"GU-{i:04d}") for i in range(1, 6)]
        state = {
            "gap_map": gap_map,
            "domain_skeleton": {},
            "current_mode": {"mode": "normal"},
            "deferred_targets": deferred_ids,
        }
        result = plan_node(state)
        target_gaps = result["current_plan"]["target_gaps"]

        # deferred 3개가 FIFO 순서로 앞에
        assert target_gaps[:3] == deferred_ids

    def test_plan_metrics_include_deferred_counts(self) -> None:
        """plan 에 executed/prev_deferred/deferred_first 카운트 포함 여부."""
        deferred_ids = ["GU-0001", "GU-0002"]
        gap_map = [self._make_gu(f"GU-{i:04d}") for i in range(1, 4)]
        state = {
            "gap_map": gap_map,
            "domain_skeleton": {},
            "current_mode": {"mode": "normal"},
            "deferred_targets": deferred_ids,
        }
        result = plan_node(state)
        plan = result["current_plan"]

        assert "executed_target_count" in plan
        assert "prev_deferred_count" in plan
        assert "deferred_first_count" in plan
        assert plan["prev_deferred_count"] == 2
        assert plan["deferred_first_count"] == 2

    def test_no_prev_deferred_normal_order(self) -> None:
        """deferred_targets 없으면 기존 순서 유지."""
        gap_map = [self._make_gu(f"GU-{i:04d}") for i in range(1, 4)]
        state = {
            "gap_map": gap_map,
            "domain_skeleton": {},
            "current_mode": {"mode": "normal"},
            "deferred_targets": [],
        }
        result = plan_node(state)
        plan = result["current_plan"]
        assert plan["deferred_first_count"] == 0
        assert plan["prev_deferred_count"] == 0
        assert len(plan["target_gaps"]) == 3
