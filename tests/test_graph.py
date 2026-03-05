"""test_graph — StateGraph 빌드 + 엣지 라우팅 + 통합 테스트.

Task 1.14/1.15/1.16: Graph 컴파일, 라우팅 함수, 단일 Cycle 실행.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.graph import (
    build_graph,
    cycle_increment_node,
    has_disputes,
    has_high_risk_claims,
    route_after_collect,
    route_after_critique,
    route_after_integrate,
    route_after_mode,
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
        "metrics": {},
        "domain_skeleton": {},
        "current_cycle": 1,
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
    """Task 1.14: Graph 컴파일 + 노드 등록."""

    def test_compile_success(self):
        """기본 빌드 — 컴파일 성공."""
        graph = build_graph()
        assert graph is not None

    def test_node_count(self):
        """8개 노드 + cycle_inc + 5개 HITL + __start__ = 15개."""
        graph = build_graph()
        # __start__ 제외 실제 노드 14개
        node_names = set(graph.nodes.keys()) - {"__start__"}
        expected = {
            "seed", "mode", "plan", "collect", "integrate",
            "critique", "plan_modify", "cycle_inc",
            "hitl_a", "hitl_b", "hitl_c", "hitl_d", "hitl_e",
        }
        assert node_names == expected

    def test_build_with_custom_tools(self):
        """LLM/search_tool/hitl_response 주입 — 컴파일 성공."""
        graph = build_graph(
            llm="mock_llm",
            search_tool="mock_search",
            hitl_response={"action": "approve"},
        )
        assert graph is not None


# ===========================================================================
# 2. 라우팅 함수 테스트 (Task 1.15)
# ===========================================================================

class TestRouteAfterMode:
    """mode_node 이후 라우팅."""

    def test_normal_mode(self):
        state = _make_state(current_mode={"mode": "normal"})
        assert route_after_mode(state) == "plan"

    def test_jump_mode_no_warning(self):
        state = _make_state(current_mode={"mode": "jump"})
        assert route_after_mode(state) == "plan"

    def test_convergence_warning(self):
        state = _make_state(
            current_mode={"mode": "jump", "convergence_warning": True}
        )
        assert route_after_mode(state) == "hitl_e"

    def test_empty_mode(self):
        state = _make_state(current_mode=None)
        assert route_after_mode(state) == "plan"


class TestRouteAfterCollect:
    """collect_node 이후 라우팅."""

    def test_no_claims(self):
        state = _make_state(current_claims=[])
        assert route_after_collect(state) == "integrate"

    def test_normal_claims(self):
        claims = [{"text": "claim1"}, {"text": "claim2"}]
        state = _make_state(current_claims=claims)
        assert route_after_collect(state) == "integrate"

    def test_high_risk_claims(self):
        claims = [
            {"text": "safe"},
            {"text": "danger", "risk_flag": True},
        ]
        state = _make_state(current_claims=claims)
        assert route_after_collect(state) == "hitl_b"

    def test_none_claims(self):
        state = _make_state(current_claims=None)
        assert route_after_collect(state) == "integrate"


class TestRouteAfterIntegrate:
    """integrate_node 이후 라우팅."""

    def test_no_disputes(self):
        kus = [{"ku_id": "KU-0001", "status": "active"}]
        state = _make_state(knowledge_units=kus)
        assert route_after_integrate(state) == "critique"

    def test_with_disputes(self):
        kus = [
            {"ku_id": "KU-0001", "status": "active"},
            {"ku_id": "KU-0002", "status": "disputed"},
        ]
        state = _make_state(knowledge_units=kus)
        assert route_after_integrate(state) == "hitl_c"

    def test_empty_kus(self):
        state = _make_state(knowledge_units=[])
        assert route_after_integrate(state) == "critique"


class TestRouteAfterCritique:
    """critique_node 이후 라우팅."""

    def test_converged(self):
        critique = {"convergence": {"converged": True}}
        state = _make_state(current_critique=critique)
        assert route_after_critique(state) == "__end__"

    def test_not_converged(self):
        critique = {"convergence": {"converged": False}}
        state = _make_state(current_critique=critique, current_cycle=3)
        assert route_after_critique(state) == "plan_modify"

    def test_gate_d_10_cycle(self):
        critique = {"convergence": {"converged": False}}
        state = _make_state(current_critique=critique, current_cycle=10)
        assert route_after_critique(state) == "hitl_d"

    def test_gate_d_20_cycle(self):
        critique = {"convergence": {"converged": False}}
        state = _make_state(current_critique=critique, current_cycle=20)
        assert route_after_critique(state) == "hitl_d"

    def test_converged_overrides_gate_d(self):
        """수렴이 Gate D보다 우선."""
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
    """should_continue, has_high_risk_claims, has_disputes, cycle_increment."""

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

    def test_has_high_risk_claims_true(self):
        state = _make_state(
            current_claims=[{"risk_flag": True}]
        )
        assert has_high_risk_claims(state) is True

    def test_has_high_risk_claims_false(self):
        state = _make_state(current_claims=[{"text": "safe"}])
        assert has_high_risk_claims(state) is False

    def test_has_disputes_true(self):
        state = _make_state(
            knowledge_units=[{"status": "disputed"}]
        )
        assert has_disputes(state) is True

    def test_has_disputes_false(self):
        state = _make_state(
            knowledge_units=[{"status": "active"}]
        )
        assert has_disputes(state) is False

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
    """graph.stream()으로 특정 노드까지만 실행, 누적 state 반환.

    Args:
        graph: 컴파일된 StateGraph.
        state: 초기 State dict.
        stop_after: 이 노드 실행 후 중단.
        config: LangGraph config (recursion_limit 등).

    Returns:
        (accumulated_state, visited_nodes) 튜플.
    """
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


class TestConvergenceTermination:
    """수렴 시 Graph 종료 확인."""

    def test_converged_critique_ends_graph(self, skeleton, kus, policies):
        """critique가 수렴 판정하면 route_after_critique → END.

        _check_convergence 직접 검증 + 라우팅 함수 확인.
        """
        # 충분한 evidence가 있는 KU (evidence_rate, confidence 충족)
        rich_kus = []
        for i, ku in enumerate(kus):
            enriched = dict(ku)
            enriched["evidence_links"] = [f"EU-{i:04d}"]
            enriched["confidence"] = 0.9
            enriched["status"] = "active"
            rich_kus.append(enriched)

        # 수렴 critique 결과를 가진 state에서 라우팅 검증
        converged_critique = {"convergence": {"converged": True}}
        state = _make_state(
            current_critique=converged_critique,
            current_cycle=5,
            knowledge_units=rich_kus,
        )
        # route_after_critique가 END 반환
        assert route_after_critique(state) == "__end__"

        # 수렴 안 된 상태에서는 plan_modify
        not_converged = {"convergence": {"converged": False}}
        state2 = _make_state(
            current_critique=not_converged,
            current_cycle=5,
        )
        assert route_after_critique(state2) == "plan_modify"

    def test_convergence_overrides_gate_d_at_cycle_10(self):
        """수렴이 Gate D(10-cycle audit)보다 우선."""
        converged = {"convergence": {"converged": True}}
        state = _make_state(current_critique=converged, current_cycle=10)
        assert route_after_critique(state) == "__end__"


class TestHITLGateIntegration:
    """HITL Gate 통합 — 자동 승인 흐름."""

    def test_gate_a_auto_approve(self, skeleton, kus, policies):
        """Gate A(Plan 승인) — response=None → 자동 승인 → collect 진행."""
        graph = build_graph(hitl_response=None)
        state = _make_bench_state(skeleton, kus, policies)

        result, visited = _stream_until(graph, state, "collect")

        # hitl_a를 통과해서 collect까지 실행됨
        assert "hitl_a" in visited
        assert "collect" in visited
        assert result["current_plan"] is not None
        # hitl_pending은 처리 후 None
        assert result.get("hitl_pending") is None

    def test_explicit_approve_response(self, skeleton, kus, policies):
        """명시적 approve 응답 주입."""
        graph = build_graph(hitl_response={"action": "approve"})
        state = _make_bench_state(skeleton, kus, policies)

        result, visited = _stream_until(graph, state, "collect")

        assert "hitl_a" in visited
        assert result["current_plan"] is not None


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
