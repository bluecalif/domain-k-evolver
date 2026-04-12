"""Domain-K-Evolver StateGraph 빌드 + 엣지 라우팅 (Silver).

P0-C1/C2/C3 (P0 Foundation Hardening, Stage C): HITL 축소 반영.
Bronze HITL-A/B/C/D 인라인 게이트 제거, Silver HITL-S/R/E 재배치.
masterplan v2 §14 기반.

Silver Flow (Inner Loop — 단일 사이클):
  START → seed → (phase 첫 cycle → hitl_s → mode, else → mode)
    → mode → (auto_pause violations → hitl_e → plan, else → plan)
    → plan → collect → integrate → critique
    → (converged → END, else → plan_modify → cycle_inc → END)

Remodel Flow (Outer Loop — Orchestrator 관리, P2):
  Orchestrator._maybe_run_remodel:
    audit (has_critical) + cycle % remodel_interval == 0
    → remodel_node → HITL-R → (approve) phase_transition + phase_bump
                              → (reject) skip (state 무변경)

HITL gates:
  - S: phase 첫 cycle seed 승인 (blocking)
  - R: Remodel 승인 (P2 구현, Orchestrator 관리)
  - E: Exception auto-pause (should_auto_pause 5개 임계치 위반 시)
  - D: dispute_queue 비블로킹 append (graph edge 아님, integrate_node 내부 처리)
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
from src.nodes.remodel import remodel_node
from src.nodes.plan_modify import plan_modify_node
from src.nodes.seed import seed_node
from src.state import EvolverState
from src.utils.metrics_guard import should_auto_pause


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
# Routing functions (Silver: P0-C1~C3)
# ---------------------------------------------------------------------------

def route_after_seed(state: EvolverState) -> str:
    """seed_node 이후: phase 첫 cycle → hitl_s, else → mode.

    seed_node는 current_cycle==0에서 시작해 1로 설정한다.
    current_cycle > 1 이면 subsequent cycle → 이미 승인받은 seed → mode 직행.
    """
    if state.get("current_cycle", 0) <= 1:
        return "hitl_s"
    return "mode"


def route_after_mode(state: EvolverState) -> str:
    """mode_node 이후: should_auto_pause 위반 → hitl_e, else → plan.

    Silver HITL-E: 5개 임계치 (conflict_rate, evidence_rate,
    collect_failure_rate, staleness_ratio, avg_confidence) 중 1개라도
    위반 시 interrupt.
    """
    pause_result = should_auto_pause(state)
    if pause_result.should_pause:
        return "hitl_e"
    return "plan"


def route_after_critique(state: EvolverState) -> str:
    """critique_node 이후: converged → END, else → plan_modify.

    Silver: HITL-D 는 dispute batch queue (integrate_node 에서 append) →
    graph edge 아니므로 10-cycle audit 분기 제거.
    """
    critique = state.get("current_critique") or {}
    convergence = critique.get("convergence", {})
    if convergence.get("converged"):
        return END
    return "plan_modify"


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
    providers: list | None = None,
    fetch_pipeline: Any | None = None,
    search_config: Any | None = None,
) -> StateGraph:
    """Evolver StateGraph 빌드 (Silver).

    Args:
        llm: LLM 인스턴스. None이면 결정론적 fallback.
        search_tool: 레거시 검색 도구. providers 가 있으면 무시.
        hitl_response: HITL 응답. None이면 자동 승인.
        providers: P3 SearchProvider 리스트.
        fetch_pipeline: P3 FetchPipeline 인스턴스.
        search_config: P3 SearchConfig (fetch_top_n, k_per_provider 등).

    Returns:
        컴파일된 StateGraph.
    """
    graph = StateGraph(EvolverState)

    # -- Core pipeline nodes --
    graph.add_node("seed", seed_node)
    graph.add_node("mode", mode_node)
    graph.add_node("plan", partial(plan_node, llm=llm))
    graph.add_node(
        "collect",
        partial(
            collect_node,
            search_tool=search_tool,
            llm=llm,
            providers=providers,
            fetch_pipeline=fetch_pipeline,
            search_config=search_config,
        ),
    )
    graph.add_node("integrate", partial(integrate_node, llm=llm))
    graph.add_node("critique", partial(critique_node, llm=llm))
    graph.add_node("plan_modify", partial(plan_modify_node, llm=llm))
    graph.add_node("cycle_inc", cycle_increment_node)

    # -- Silver HITL nodes (S / R / E) --
    graph.add_node("hitl_s", _make_hitl_node("S", response=hitl_response))
    graph.add_node("hitl_r", _make_hitl_node("R", response=hitl_response))
    graph.add_node("hitl_e", _make_hitl_node("E", response=hitl_response))

    # -- Remodel node (P2) — Orchestrator 관리, inner-loop edge 없음 --
    graph.add_node("remodel", remodel_node)

    # -- Edges --

    # START → seed → (첫 cycle → hitl_s → mode, else → mode)
    graph.add_edge(START, "seed")
    graph.add_conditional_edges(
        "seed",
        route_after_seed,
        {"hitl_s": "hitl_s", "mode": "mode"},
    )
    graph.add_edge("hitl_s", "mode")

    # mode → (auto_pause → hitl_e → plan, else → plan)
    graph.add_conditional_edges(
        "mode",
        route_after_mode,
        {"plan": "plan", "hitl_e": "hitl_e"},
    )
    graph.add_edge("hitl_e", "plan")

    # plan → collect → integrate → critique (인라인 HITL 제거)
    graph.add_edge("plan", "collect")
    graph.add_edge("collect", "integrate")
    graph.add_edge("integrate", "critique")

    # critique → (converged → END, else → plan_modify)
    graph.add_conditional_edges(
        "critique",
        route_after_critique,
        {END: END, "plan_modify": "plan_modify"},
    )

    # plan_modify → cycle_inc → END (단일 사이클, 루프는 Orchestrator가 외부 관리)
    graph.add_edge("plan_modify", "cycle_inc")
    graph.add_edge("cycle_inc", END)

    return graph.compile()
