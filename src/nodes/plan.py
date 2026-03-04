"""plan_node — Collection Plan 생성.

Gap Map + Mode → LLM 호출 → Collection Plan.
design-v2 §7 기반.
"""

from __future__ import annotations

from typing import Any

from src.state import EvolverState

# --- 우선순위 정렬 키 ---
_UTILITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_RISK_ORDER = {"safety": 0, "financial": 1, "policy": 2, "convenience": 3, "informational": 4}


def _select_targets(
    gap_map: list[dict],
    mode_decision: dict,
    axis_coverage: list[dict] | None = None,
) -> tuple[list[dict], list[dict]]:
    """explore/exploit Target 선정.

    Returns:
        (explore_targets, exploit_targets)
    """
    mode = mode_decision.get("mode", "normal")
    explore_budget = mode_decision.get("explore_budget", 0)
    exploit_budget = mode_decision.get("exploit_budget", 0)

    open_gus = [gu for gu in gap_map if gu.get("status") == "open"]

    # 우선순위 정렬
    open_gus.sort(key=lambda g: (
        _UTILITY_ORDER.get(g.get("expected_utility", "low"), 99),
        _RISK_ORDER.get(g.get("risk_level", "informational"), 99),
    ))

    if mode == "normal":
        # Normal: exploit만
        exploit_targets = open_gus[:exploit_budget]
        return [], exploit_targets

    # Jump Mode: explore + exploit 분리
    # explore: deficit 축 기반 (axis_tags가 없거나 coverage가 낮은 영역)
    # 단순화: expansion_mode == "jump"인 GU를 explore로 분류
    explore_candidates = [
        gu for gu in open_gus
        if gu.get("expansion_mode") == "jump"
    ]
    exploit_candidates = [
        gu for gu in open_gus
        if gu.get("expansion_mode") != "jump"
    ]

    explore_targets = explore_candidates[:explore_budget]
    exploit_targets = exploit_candidates[:exploit_budget]

    # explore가 부족하면 exploit에서 보충, 반대도 마찬가지
    remaining_explore = explore_budget - len(explore_targets)
    if remaining_explore > 0:
        extra = [g for g in exploit_candidates[exploit_budget:] if g not in explore_targets]
        explore_targets.extend(extra[:remaining_explore])

    remaining_exploit = exploit_budget - len(exploit_targets)
    if remaining_exploit > 0:
        extra = [g for g in explore_candidates[explore_budget:] if g not in exploit_targets]
        exploit_targets.extend(extra[:remaining_exploit])

    return explore_targets, exploit_targets


def _build_plan_prompt(
    explore_targets: list[dict],
    exploit_targets: list[dict],
    mode_decision: dict,
    skeleton: dict,
    policies: dict,
    critique: dict | None,
) -> str:
    """LLM 프롬프트 생성."""
    all_targets = explore_targets + exploit_targets
    target_descs = []
    for i, gu in enumerate(all_targets, 1):
        target = gu.get("target", {})
        target_descs.append(
            f"{i}. [{gu.get('gu_id')}] {target.get('entity_key')} / {target.get('field')} "
            f"({gu.get('gap_type')}, {gu.get('expected_utility')}/{gu.get('risk_level')})"
        )

    domain = skeleton.get("domain", "unknown")
    mode = mode_decision.get("mode", "normal")

    prompt = f"""You are a knowledge collection planner for the domain "{domain}".

## Mode: {mode.upper()}
- Explore targets: {len(explore_targets)}
- Exploit targets: {len(exploit_targets)}

## Target Gaps:
{chr(10).join(target_descs)}

## Instructions:
Create a Collection Plan in JSON format with these fields:
- target_gaps: list of GU IDs to address
- queries: dict mapping each GU ID to a list of search queries (2-3 per gap)
- source_strategy: recommended sources per gap
- acceptance_tests: conditions for considering each gap resolved
- budget: search call budget
- stop_rules: when to stop collection

Return ONLY valid JSON."""

    if critique:
        prescriptions = critique.get("prescriptions", [])
        if prescriptions:
            rx_descs = [f"- {rx.get('rx_id')}: {rx.get('description', '')}" for rx in prescriptions]
            prompt += f"\n\n## Previous Critique Prescriptions:\n{chr(10).join(rx_descs)}"

    return prompt


def _build_plan_from_targets(
    explore_targets: list[dict],
    exploit_targets: list[dict],
    mode_decision: dict,
) -> dict:
    """LLM 없이 결정론적 Plan 생성 (fallback / mock용)."""
    all_targets = explore_targets + exploit_targets
    target_gap_ids = [gu.get("gu_id") for gu in all_targets]

    queries: dict[str, list[str]] = {}
    acceptance_tests: dict[str, str] = {}
    source_strategy: dict[str, str] = {}

    for gu in all_targets:
        gu_id = gu.get("gu_id", "")
        target = gu.get("target", {})
        entity_key = target.get("entity_key", "")
        field = target.get("field", "")
        criteria = gu.get("resolution_criteria", "")

        # 기본 쿼리 생성
        slug = entity_key.split(":")[-1] if ":" in entity_key else entity_key
        queries[gu_id] = [
            f"{slug} {field}",
            f"{slug} {field} 2026",
        ]
        acceptance_tests[gu_id] = criteria
        source_strategy[gu_id] = "official_first"

    mode = mode_decision.get("mode", "normal")
    budget = len(all_targets) * 2
    if mode == "jump":
        budget += 4

    return {
        "target_gaps": target_gap_ids,
        "queries": queries,
        "source_strategy": source_strategy,
        "acceptance_tests": acceptance_tests,
        "budget": budget,
        "stop_rules": {
            "max_search_calls": budget,
            "skip_low_utility_on_budget_exceed": True,
        },
        "explore_targets": [gu.get("gu_id") for gu in explore_targets],
        "exploit_targets": [gu.get("gu_id") for gu in exploit_targets],
    }


def plan_node(
    state: EvolverState,
    *,
    llm: Any | None = None,
) -> dict:
    """Gap Map + Mode → Collection Plan 생성.

    Args:
        llm: LLM 인스턴스. None이면 결정론적 fallback 사용.
    """
    gap_map = state.get("gap_map", [])
    mode_decision = state.get("current_mode", {"mode": "normal", "explore_budget": 0, "exploit_budget": 4})
    axis_coverage = state.get("axis_coverage")
    critique = state.get("current_critique")
    skeleton = state.get("domain_skeleton", {})
    policies = state.get("policies", {})

    # Target 선정
    explore_targets, exploit_targets = _select_targets(
        gap_map, mode_decision, axis_coverage,
    )

    # 불변원칙 검증: Plan.target_gaps ⊆ G.open
    open_gu_ids = {gu.get("gu_id") for gu in gap_map if gu.get("status") == "open"}
    all_targets = explore_targets + exploit_targets
    for gu in all_targets:
        assert gu.get("gu_id") in open_gu_ids, (
            f"Gap-driven 위반: {gu.get('gu_id')} is not in open GU set"
        )

    if llm is not None:
        # LLM 호출
        prompt = _build_plan_prompt(
            explore_targets, exploit_targets,
            mode_decision, skeleton, policies, critique,
        )
        response = llm.invoke(prompt)
        # LLM 응답 파싱 (JSON)
        import json
        try:
            plan = json.loads(response.content)
        except (json.JSONDecodeError, AttributeError):
            # fallback
            plan = _build_plan_from_targets(
                explore_targets, exploit_targets, mode_decision,
            )
    else:
        plan = _build_plan_from_targets(
            explore_targets, exploit_targets, mode_decision,
        )

    return {"current_plan": plan}
