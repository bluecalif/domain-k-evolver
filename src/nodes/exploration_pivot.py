"""exploration_pivot — 정체 탈출 쿼리 재작성 노드 (SI-P4 Stage E, E4).

5 cycle 연속 external_novelty < 0.1 AND reach_degraded AND audit 미소비 시
LLM query rewriter + candidate axis probe 로 이번 cycle targets 를 치환.
다음 cycle 은 normal loop 복귀.

Pipeline:
    should_pivot → (true) → run_exploration_pivot (query rewrite + candidate axis)
                → planned_targets 치환 (이번 cycle only)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from src.utils.llm_parse import extract_json
from src.utils.skeleton_tiers import get_candidate_categories

if TYPE_CHECKING:
    from src.config import EvolverConfig
    from src.utils.cost_guard import CostGuard

logger = logging.getLogger(__name__)

EXTERNAL_NOVELTY_THRESHOLD = 0.1
EXTERNAL_NOVELTY_WINDOW = 5

QUERY_REWRITER_PROMPT = """SYSTEM:
You are a search-query strategist for a knowledge-evolution system.
The system has been collecting knowledge about {domain} for {cycle_count} cycles
and has plateaued — it keeps retrieving similar content. Your job is to generate
query variants that push into UNEXPLORED territory.

USER:
Current collection state:
- Categories covered: {skeleton_categories}
- Recently retrieved domains: {top_domains}
- Current query targets: {current_targets}
- Novelty against full history (0-1, lower = more redundant): {external_novelty}

Generate EXACTLY 3 query variants, each following one strategy:
1. ABSTRACTION_RAISE: broaden the scope one level up
   (e.g., "JR Pass" → "long-distance rail options in Japan")
2. TIME_SHIFT: add a temporal qualifier that forces different sources
   (e.g., add "as of 2026" or "pre-2020 era")
3. LONG_TAIL: target a specific, underserved sub-angle
   (e.g., "accessibility for wheelchair travelers in rural onsen")

Rules:
- Each variant must be DISTINCT from any covered category.
- Avoid terms that match {top_domains}' typical content patterns.
- Return JSON: {{"variants": [{{"strategy": "...", "query": "...", "rationale": "..."}}]}}
"""


def should_pivot(
    state: dict,
    config: "EvolverConfig",
) -> tuple[bool, str]:
    """exploration_pivot 실행 여부 판정.

    조건 (AND):
    1. external_anchor enabled
    2. external_novelty < 0.1 연속 5 cycle (D-149: reach_degraded 조건 제거)
    3. audit coverage_gap 이 이번 cycle 에 소비되지 않음

    D-149: domains_per_100ku < 15 floor 는 실측 52~57 대비 구조적 unreachable.
    novelty 정체만으로 pivot 트리거.

    Returns:
        (should_run, reason)
    """
    ea = config.external_anchor
    if not ea.enabled:
        return False, "external_anchor_disabled"

    # 조건 1: external novelty 정체
    ext_history = state.get("external_novelty_history") or []
    if len(ext_history) < EXTERNAL_NOVELTY_WINDOW:
        return False, f"insufficient_ext_history({len(ext_history)}<{EXTERNAL_NOVELTY_WINDOW})"

    recent_ext = ext_history[-EXTERNAL_NOVELTY_WINDOW:]
    if not all(v < EXTERNAL_NOVELTY_THRESHOLD for v in recent_ext):
        return False, "ext_novelty_not_stagnant"

    # 조건 2: audit coverage_gap 미소비
    if state.get("_audit_consumed_this_cycle", False):
        return False, "audit_already_consumed"

    return True, "plateau:exploration_pivot"


def _build_rewriter_prompt(state: dict) -> str:
    skeleton = state.get("domain_skeleton", {})
    domain = skeleton.get("domain", "unknown")
    cycle = state.get("current_cycle", state.get("cycle", 0))
    categories = [c.get("slug", "") for c in skeleton.get("categories", [])]

    # top domains from reach_history
    reach_history = state.get("reach_history") or []
    top_domains: list[str] = []
    if reach_history:
        latest = reach_history[-1]
        top_domains = latest.get("domains", [])[:10]

    # current targets
    plan = state.get("current_plan") or {}
    targets = plan.get("targets") or []
    target_strs = []
    for t in targets[:5]:
        if isinstance(t, dict):
            target_strs.append(t.get("entity_key", str(t)))
        else:
            target_strs.append(str(t))

    ext_history = state.get("external_novelty_history") or []
    ext_novelty = ext_history[-1] if ext_history else 0.0

    return QUERY_REWRITER_PROMPT.format(
        domain=domain,
        cycle_count=cycle,
        skeleton_categories=", ".join(categories) or "(none)",
        top_domains=", ".join(top_domains) or "(none)",
        current_targets=", ".join(target_strs) or "(none)",
        external_novelty=f"{ext_novelty:.3f}",
    )


def run_exploration_pivot(
    state: dict,
    llm: Any,
    config: "EvolverConfig",
    cost_guard: "CostGuard",
    cycle: Optional[int] = None,
) -> dict:
    """LLM query rewriter + candidate axis probe → targets 치환.

    Returns:
        {
            "status": "ok" | "skipped" | "error",
            "reason": str,
            "variants": [{strategy, query, rationale}],
            "candidate_targets": [{slug, name}],
            "cycle": int,
        }
    """
    cycle = cycle if cycle is not None else state.get("current_cycle", state.get("cycle", 0))

    should, reason = should_pivot(state, config)
    if not should:
        return {"status": "skipped", "reason": reason,
                "variants": [], "candidate_targets": [], "cycle": cycle}

    if not cost_guard.allow("exploration_pivot", llm=1):
        return {"status": "skipped", "reason": "budget_exceeded",
                "variants": [], "candidate_targets": [], "cycle": cycle}

    prompt = _build_rewriter_prompt(state)

    try:
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        parsed = extract_json(text)
    except Exception as exc:
        logger.warning("[exploration_pivot] LLM call failed: %s", exc)
        cost_guard.record("exploration_pivot", llm=1)
        return {"status": "error", "reason": f"llm_error:{exc}",
                "variants": [], "candidate_targets": [], "cycle": cycle}

    cost_guard.record("exploration_pivot", llm=1)

    variants = parsed.get("variants", []) if isinstance(parsed, dict) else []
    if not isinstance(variants, list):
        variants = []

    # candidate axis probe — skeleton candidate_categories 상위 2개
    skeleton = state.get("domain_skeleton", {})
    candidates = get_candidate_categories(skeleton)
    candidate_targets = [
        {"slug": c.get("slug", ""), "name": c.get("name", "")}
        for c in candidates[:2]
        if c.get("slug")
    ]

    logger.info(
        "[exploration_pivot] cycle=%d variants=%d candidate_targets=%d",
        cycle, len(variants), len(candidate_targets),
    )

    return {
        "status": "ok",
        "reason": reason,
        "variants": variants,
        "candidate_targets": candidate_targets,
        "cycle": cycle,
    }
