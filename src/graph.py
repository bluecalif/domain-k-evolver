"""Domain-K-Evolver StateGraph 빌드 + 엣지 라우팅.

Task 1.14 + 1.15: Graph 구조, 조건부 엣지, HITL Gate 통합.
design-v2 §10 기반.

Flow:
  START → seed → mode → plan → hitl_a → collect → integrate → critique
    → plan_modify → cycle_inc → mode (loop)

Conditional edges:
  - mode: convergence_warning → hitl_e → plan, else → plan
  - collect → hitl_b (high-risk claims) or integrate
  - integrate → hitl_c (disputed KUs) or critique
  - critique → END (converged) / hitl_d (10-cycle audit) / plan_modify
"""

from __future__ import annotations

from functools import partial
from typing import Any

from langgraph.graph import END, START, StateGraph

from src.nodes.collect import collect_node
from src.nodes.critique import critique_node
from src.nodes.hitl_gate import hitl_gate_node
from src.nodes.integrate import integrate_node
from src.nodes.mode import mode_node
from src.nodes.plan import plan_node
from src.nodes.plan_modify import plan_modify_node
from src.nodes.seed import seed_node
from src.state import EvolverState


# ---------------------------------------------------------------------------
# Helper nodes
# ---------------------------------------------------------------------------

def _make_hitl_node(
    gate: str,
    *,
    response: dict | None = None,
):
    """HITL Gate 노드 팩토리.

    hitl_pending를 설정한 뒤 hitl_gate_node를 호출.
    같은 hitl_gate_node를 여러 gate 지점에서 재사용.
    """

    def node(state: EvolverState) -> dict:
        modified = dict(state)
        modified["hitl_pending"] = {"gate": gate}
        return hitl_gate_node(modified, response=response)

    node.__name__ = f"hitl_{gate.lower()}"
    return node


def cycle_increment_node(state: EvolverState) -> dict:
    """Cycle 증가. plan_modify → mode 전환 시 실행."""
    return {"current_cycle": state.get("current_cycle", 1) + 1}


# ---------------------------------------------------------------------------
# Routing functions (Task 1.15)
# ---------------------------------------------------------------------------

def route_after_mode(state: EvolverState) -> str:
    """mode_node 이후: convergence_warning → hitl_e, else → plan."""
    mode_decision = state.get("current_mode") or {}
    if mode_decision.get("convergence_warning"):
        return "hitl_e"
    return "plan"


def route_after_collect(state: EvolverState) -> str:
    """collect_node 이후: high-risk claims → hitl_b, else → integrate."""
    claims = state.get("current_claims") or []
    if any(c.get("risk_flag") for c in claims):
        return "hitl_b"
    return "integrate"


def route_after_integrate(state: EvolverState) -> str:
    """integrate_node 이후: disputed KUs → hitl_c, else → critique."""
    kus = state.get("knowledge_units") or []
    if any(ku.get("status") == "disputed" for ku in kus):
        return "hitl_c"
    return "critique"


def route_after_critique(state: EvolverState) -> str:
    """critique_node 이후: converged → END, 10-cycle → hitl_d, else → plan_modify."""
    critique = state.get("current_critique") or {}

    # 수렴 판정
    convergence = critique.get("convergence", {})
    if convergence.get("converged"):
        return END

    # Gate D: 10 Cycle마다 Executive Audit
    cycle = state.get("current_cycle", 0)
    if cycle > 0 and cycle % 10 == 0:
        return "hitl_d"

    return "plan_modify"


def has_high_risk_claims(state: EvolverState) -> bool:
    """Gate B 발동 여부."""
    claims = state.get("current_claims") or []
    return any(c.get("risk_flag") for c in claims)


def has_disputes(state: EvolverState) -> bool:
    """Gate C 발동 여부."""
    kus = state.get("knowledge_units") or []
    return any(ku.get("status") == "disputed" for ku in kus)


def should_continue(state: EvolverState) -> str:
    """수렴 판정 (END vs continue). route_after_critique의 단순 래퍼."""
    critique = state.get("current_critique") or {}
    if critique.get("convergence", {}).get("converged"):
        return "end"
    return "continue"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(
    *,
    llm: Any | None = None,
    search_tool: Any | None = None,
    hitl_response: dict | None = None,
) -> StateGraph:
    """Evolver StateGraph 빌드.

    Args:
        llm: LLM 인스턴스. None이면 결정론적 fallback.
        search_tool: 검색 도구. None이면 빈 결과.
        hitl_response: HITL 응답. None이면 자동 승인.

    Returns:
        컴파일된 StateGraph.
    """
    graph = StateGraph(EvolverState)

    # -- Nodes --
    graph.add_node("seed", seed_node)
    graph.add_node("mode", mode_node)
    graph.add_node("plan", partial(plan_node, llm=llm))
    graph.add_node(
        "collect",
        partial(collect_node, search_tool=search_tool, llm=llm),
    )
    graph.add_node("integrate", partial(integrate_node, llm=llm))
    graph.add_node("critique", partial(critique_node, llm=llm))
    graph.add_node("plan_modify", partial(plan_modify_node, llm=llm))
    graph.add_node("cycle_inc", cycle_increment_node)

    # HITL Gate nodes (각 gate 지점마다 별도 등록)
    graph.add_node("hitl_a", _make_hitl_node("A", response=hitl_response))
    graph.add_node("hitl_b", _make_hitl_node("B", response=hitl_response))
    graph.add_node("hitl_c", _make_hitl_node("C", response=hitl_response))
    graph.add_node("hitl_d", _make_hitl_node("D", response=hitl_response))
    graph.add_node("hitl_e", _make_hitl_node("E", response=hitl_response))

    # -- Edges --

    # START → seed → mode
    graph.add_edge(START, "seed")
    graph.add_edge("seed", "mode")

    # mode → (conditional) plan or hitl_e
    graph.add_conditional_edges(
        "mode",
        route_after_mode,
        {"plan": "plan", "hitl_e": "hitl_e"},
    )
    graph.add_edge("hitl_e", "plan")

    # plan → hitl_a (Gate A: 항상) → collect
    graph.add_edge("plan", "hitl_a")
    graph.add_edge("hitl_a", "collect")

    # collect → (conditional) hitl_b or integrate
    graph.add_conditional_edges(
        "collect",
        route_after_collect,
        {"hitl_b": "hitl_b", "integrate": "integrate"},
    )
    graph.add_edge("hitl_b", "integrate")

    # integrate → (conditional) hitl_c or critique
    graph.add_conditional_edges(
        "integrate",
        route_after_integrate,
        {"hitl_c": "hitl_c", "critique": "critique"},
    )
    graph.add_edge("hitl_c", "critique")

    # critique → (conditional) END / hitl_d / plan_modify
    graph.add_conditional_edges(
        "critique",
        route_after_critique,
        {END: END, "hitl_d": "hitl_d", "plan_modify": "plan_modify"},
    )
    graph.add_edge("hitl_d", "plan_modify")

    # plan_modify → cycle_inc → END (단일 사이클, 루프는 Orchestrator가 외부 관리)
    graph.add_edge("plan_modify", "cycle_inc")
    graph.add_edge("cycle_inc", END)

    return graph.compile()
