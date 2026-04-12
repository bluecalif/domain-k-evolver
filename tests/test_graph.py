"""test_graph — StateGraph 빌드 + 엣지 라우팅 + 통합 테스트 (Silver).

P0-C1/C2/C3 반영: HITL-A/B/C/D 제거, HITL-S/R/E 재배치.
Silver Flow:
  START → seed → (첫 cycle → hitl_s → mode, else → mode)
    → mode → (auto_pause → hitl_e → plan, else → plan)
    → plan → collect → integrate → critique
    → (converged → END, else → plan_modify → cycle_inc → END)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.graph import (
    build_graph,
    cycle_increment_node,
    route_after_critique,
    route_after_mode,
    route_after_seed,
    should_continue,
)
from src.state import EvolverState

BENCH = Path("bench/japan-travel/state")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def skeleton() -> dict:
    with open(BENCH / "domain-skeleton.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def kus() -> list[dict]:
    with open(BENCH / "knowledge-units.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def policies() -> dict:
    with open(BENCH / "policies.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def gap_map() -> list[dict]:
    with open(BENCH / "gap-map.json", encoding="utf-8") as f:
        return json.load(f)


def _make_state(**overrides) -> dict:
    """테스트용 최소 State 생성."""
    base: dict = {
        "knowledge_units": [],
        "gap_map": [],
        "policies": {},
        "metrics": {"rates": {"evidence_rate": 1.0, "avg_confidence": 1.0}},
        "domain_skeleton": {},
        "current_cycle": 2,  # default: not first cycle
        "current_plan": None,
        "current_claims": None,
        "current_critique": None,
        "current_mode": None,
        "axis_coverage": None,
        "jump_history": [],
        "hitl_pending": None,
    }
    base.update(overrides)
    return base


# ===========================================================================
# 1. Graph 컴파일 테스트
# ===========================================================================

class TestGraphBuild:
    """Silver Graph 빌드 + 노드 등록."""

    def test_compile_success(self):
        """기본 빌드 — 컴파일 성공."""
        graph = build_graph()
        assert graph is not None

    def test_node_count(self):
        """8 core + cycle_inc + 3 HITL (S/R/E) = 11 노드 (+ __start__)."""
        graph = build_graph()
        node_names = set(graph.nodes.keys()) - {"__start__"}
        expected = {
            "seed", "mode", "plan", "collect", "integrate",
            "critique", "plan_modify", "cycle_inc",
            "hitl_s", "hitl_r", "hitl_e",
        }
        assert node_names == expected

    def test_bronze_hitl_removed(self):
        """Bronze HITL-A/B/C/D 노드는 Silver 그래프에 없다."""
        graph = build_graph()
        nodes = set(graph.nodes.keys())
        for removed in ("hitl_a", "hitl_b", "hitl_c", "hitl_d"):
            assert removed not in nodes

    def test_build_with_custom_tools(self):
        """LLM/search_tool/hitl_response 주입 — 컴파일 성공."""
        graph = build_graph(
            llm="mock_llm",
            search_tool="mock_search",
            hitl_response={"action": "approve"},
        )
        assert graph is not None


# ===========================================================================
# 2. 라우팅 함수 테스트 (Silver P0-C1~C3)
# ===========================================================================

class TestRouteAfterSeed:
    """seed_node 이후 라우팅 — phase 첫 cycle 조건부 HITL-S."""

    def test_first_cycle_routes_to_hitl_s(self):
        state = _make_state(current_cycle=1)
        assert route_after_seed(state) == "hitl_s"

    def test_cycle_zero_routes_to_hitl_s(self):
        """초기 상태(cycle=0)도 첫 cycle로 간주."""
        state = _make_state(current_cycle=0)
        assert route_after_seed(state) == "hitl_s"

    def test_subsequent_cycle_routes_to_mode(self):
        state = _make_state(current_cycle=2)
        assert route_after_seed(state) == "mode"

    def test_later_cycle_routes_to_mode(self):
        state = _make_state(current_cycle=10)
        assert route_after_seed(state) == "mode"


class TestRouteAfterMode:
    """mode_node 이후 라우팅 — should_auto_pause 기반."""

    def test_healthy_routes_to_plan(self):
        state = _make_state(
            metrics={"rates": {
                "evidence_rate": 0.8,
                "conflict_rate": 0.1,
                "staleness_ratio": 0.1,
                "avg_confidence": 0.8,
            }},
            collect_failure_rate=0.0,
        )
        assert route_after_mode(state) == "plan"

    def test_conflict_rate_violation_routes_to_hitl_e(self):
        state = _make_state(
            metrics={"rates": {
                "evidence_rate": 0.8,
                "conflict_rate": 0.30,  # > 0.25 → violation
                "staleness_ratio": 0.1,
                "avg_confidence": 0.8,
            }},
            collect_failure_rate=0.0,
        )
        assert route_after_mode(state) == "hitl_e"

    def test_evidence_rate_violation_routes_to_hitl_e(self):
        state = _make_state(
            metrics={"rates": {
                "evidence_rate": 0.40,  # < 0.55
                "conflict_rate": 0.1,
                "staleness_ratio": 0.1,
                "avg_confidence": 0.8,
            }},
            collect_failure_rate=0.0,
        )
        assert route_after_mode(state) == "hitl_e"

    def test_collect_failure_rate_violation_routes_to_hitl_e(self):
        state = _make_state(
            metrics={"rates": {
                "evidence_rate": 0.8,
                "conflict_rate": 0.1,
                "staleness_ratio": 0.1,
                "avg_confidence": 0.8,
            }},
            collect_failure_rate=0.60,  # > 0.50
        )
        assert route_after_mode(state) == "hitl_e"


class TestRouteAfterCritique:
    """critique_node 이후 라우팅 — Silver 단순화 (hitl_d 제거)."""

    def test_converged(self):
        critique = {"convergence": {"converged": True}}
        state = _make_state(current_critique=critique)
        assert route_after_critique(state) == "__end__"

    def test_not_converged(self):
        critique = {"convergence": {"converged": False}}
        state = _make_state(current_critique=critique, current_cycle=3)
        assert route_after_critique(state) == "plan_modify"

    def test_cycle_10_does_not_trigger_hitl_d(self):
        """Silver: 10-cycle audit 분기 제거 — plan_modify 로 직행."""
        critique = {"convergence": {"converged": False}}
        state = _make_state(current_critique=critique, current_cycle=10)
        assert route_after_critique(state) == "plan_modify"

    def test_cycle_20_does_not_trigger_hitl_d(self):
        critique = {"convergence": {"converged": False}}
        state = _make_state(current_critique=critique, current_cycle=20)
        assert route_after_critique(state) == "plan_modify"

    def test_converged_overrides_cycle(self):
        """수렴이 최우선."""
        critique = {"convergence": {"converged": True}}
        state = _make_state(current_critique=critique, current_cycle=10)
        assert route_after_critique(state) == "__end__"

    def test_no_critique(self):
        state = _make_state(current_critique=None, current_cycle=1)
        assert route_after_critique(state) == "plan_modify"


# ===========================================================================
# 3. 헬퍼 함수 테스트
# ===========================================================================

class TestHelperFunctions:
    """should_continue, cycle_increment."""

    def test_should_continue_yes(self):
        state = _make_state(
            current_critique={"convergence": {"converged": False}}
        )
        assert should_continue(state) == "continue"

    def test_should_continue_end(self):
        state = _make_state(
            current_critique={"convergence": {"converged": True}}
        )
        assert should_continue(state) == "end"

    def test_cycle_increment(self):
        state = _make_state(current_cycle=3)
        result = cycle_increment_node(state)
        assert result == {"current_cycle": 4}

    def test_cycle_increment_default(self):
        result = cycle_increment_node({})
        assert result == {"current_cycle": 2}


# ===========================================================================
# 4. 단일 Cycle 통합 테스트 (mock LLM + mock search)
# ===========================================================================

def _stream_until(graph, state, stop_after, *, config=None):
    """graph.stream()으로 특정 노드까지만 실행, 누적 state 반환."""
    if config is None:
        config = {"recursion_limit": 100}
    accumulated = dict(state)
    visited: list[str] = []
    for event in graph.stream(state, config):
        for node_name, node_output in event.items():
            visited.append(node_name)
            if isinstance(node_output, dict):
                accumulated.update(node_output)
        if stop_after in visited:
            break
    return accumulated, visited


def _make_bench_state(skeleton, kus, policies, **overrides):
    """bench 데이터 기반 초기 State 생성."""
    base: dict = {
        "knowledge_units": kus,
        "gap_map": [],
        "policies": policies,
        "metrics": {},
        "domain_skeleton": skeleton,
        "current_cycle": 0,
        "current_plan": None,
        "current_claims": None,
        "current_critique": None,
        "current_mode": None,
        "axis_coverage": None,
        "jump_history": [],
        "hitl_pending": None,
    }
    base.update(overrides)
    return base


class TestSingleCycleRun:
    """Graph 단일 Cycle 실행 — stream으로 1 Cycle만 검증."""

    def test_single_cycle_with_bench_data(self, skeleton, kus, policies):
        """bench/japan-travel 데이터로 1 Cycle — critique까지 도달 확인."""
        graph = build_graph()
        state = _make_bench_state(skeleton, kus, policies)

        result, visited = _stream_until(graph, state, "critique")

        # 핵심 노드가 모두 실행됨
        assert "seed" in visited
        assert "mode" in visited
        assert "plan" in visited
        assert "collect" in visited
        assert "integrate" in visited
        assert "critique" in visited

        # seed_node이 실행되어 gap_map이 생성됨
        assert len(result["gap_map"]) > 0
        # mode_node이 실행되어 current_mode 설정
        assert result["current_mode"] is not None
        # plan_node이 실행되어 current_plan 설정
        assert result["current_plan"] is not None
        # critique_node이 실행되어 current_critique 설정
        assert result["current_critique"] is not None
        # Cycle 0에서 시작 → critique 시점에서 수렴 불가 (cycle < 5)
        convergence = result["current_critique"].get("convergence", {})
        assert convergence.get("converged") is False

    def test_seed_produces_gaps(self, skeleton, kus, policies):
        """seed_node가 GU를 정상 생성하는지 확인."""
        graph = build_graph()
        state = _make_bench_state(skeleton, kus, policies)

        result, visited = _stream_until(graph, state, "seed")

        # Bootstrap GU >= 20개
        gap_map = result["gap_map"]
        assert len(gap_map) >= 20

        # 모든 GU는 GU-NNNN 형식 ID
        for gu in gap_map:
            assert gu["gu_id"].startswith("GU-")

    def test_first_cycle_passes_through_hitl_s(self, skeleton, kus, policies):
        """첫 cycle 실행 시 hitl_s 가 visited 에 포함된다."""
        graph = build_graph(hitl_response={"action": "approve"})
        state = _make_bench_state(skeleton, kus, policies)

        _, visited = _stream_until(graph, state, "mode")

        assert "seed" in visited
        assert "hitl_s" in visited
        assert "mode" in visited


class TestConvergenceTermination:
    """수렴 시 Graph 종료 확인."""

    def test_converged_critique_ends_graph(self, skeleton, kus, policies):
        """critique가 수렴 판정하면 route_after_critique → END."""
        converged_critique = {"convergence": {"converged": True}}
        state = _make_state(
            current_critique=converged_critique,
            current_cycle=5,
        )
        assert route_after_critique(state) == "__end__"

        not_converged = {"convergence": {"converged": False}}
        state2 = _make_state(
            current_critique=not_converged,
            current_cycle=5,
        )
        assert route_after_critique(state2) == "plan_modify"

    def test_convergence_overrides_cycle_10(self):
        """수렴이 최우선 — Silver 에서는 10-cycle audit 분기 자체가 없음."""
        converged = {"convergence": {"converged": True}}
        state = _make_state(current_critique=converged, current_cycle=10)
        assert route_after_critique(state) == "__end__"


# ===========================================================================
# 5. 5대 불변원칙 그래프 레벨 검증
# ===========================================================================

class TestInvariantsInGraph:
    """Graph 실행 후 5대 불변원칙 성립 확인 (1 Cycle stream)."""

    def test_gap_driven_plan(self, skeleton, kus, policies):
        """불변원칙 1: Plan은 Gap이 구동 — Plan target_gaps ⊆ gap_map."""
        graph = build_graph()
        state = _make_bench_state(skeleton, kus, policies)

        result, _ = _stream_until(graph, state, "plan")

        plan = result.get("current_plan", {})
        target_gaps = plan.get("target_gaps", [])
        gap_ids = {gu["gu_id"] for gu in result.get("gap_map", [])}

        # Plan의 target_gaps는 gap_map에 존재하는 GU만 참조
        for tg in target_gaps:
            gu_id = tg if isinstance(tg, str) else tg.get("gu_id", "")
            assert gu_id in gap_ids, f"Plan target {gu_id} not in gap_map"

    def test_evidence_first_kus(self, skeleton, kus, policies):
        """불변원칙 3: evidence_links 없는 KU는 active 불가."""
        graph = build_graph()
        state = _make_bench_state(skeleton, kus, policies)

        result, _ = _stream_until(graph, state, "integrate")

        for ku in result.get("knowledge_units", []):
            if ku.get("status") == "active":
                evidence = ku.get("evidence_links", [])
                assert len(evidence) >= 1, (
                    f"KU {ku.get('ku_id')} is active but has no evidence"
                )
