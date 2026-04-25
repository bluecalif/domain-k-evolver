"""plan_node — Collection Plan 생성.

Gap Map + Mode → LLM 호출 → Collection Plan.
design-v2 §7 기반.

P4 확장: reason_code 체계 + Gini/coverage 기반 우선순위.
"""

from __future__ import annotations

from typing import Any

from src.state import EvolverState

# --- P4: Reason Code 상수 ---
DEFICIT_THRESHOLD = 0.5     # deficit_score 초과 시 deficit reason
GINI_THRESHOLD = 0.45       # Gini 임계치

# --- SI-P4 Stage E: External Anchor reason_code 임계치 ---
EXTERNAL_NOVELTY_STAGNATION_THRESHOLD = 0.1   # 5c 연속 < 0.1 → stagnation
EXTERNAL_NOVELTY_STAGNATION_WINDOW = 5


def _assign_reason_code(
    gu: dict,
    coverage_map: dict | None,
    novelty_history: list[float] | None,
    has_remodel_pending: bool,
    cycle: int,
    *,
    external_novelty_history: list[float] | None = None,
) -> str:
    """GU 에 reason_code 부여 (P4-B1 + SI-P4 Stage E).

    우선순위: external_novelty > universe_probe > reach_diversity >
              deficit > gini > plateau > remodel > audit > seed.
    """
    entity_key = gu.get("target", {}).get("entity_key", "")
    parts = entity_key.split(":")
    category = parts[1] if len(parts) >= 3 else ""
    field = gu.get("target", {}).get("field", "")

    # SI-P4 Stage E — External Anchor 계열 (최상위 우선순위)

    # 0a. external_novelty:stagnation — 누적 history 신호 (cycle-level, 모든 target 에 적용)
    if external_novelty_history and len(external_novelty_history) >= EXTERNAL_NOVELTY_STAGNATION_WINDOW:
        recent = external_novelty_history[-EXTERNAL_NOVELTY_STAGNATION_WINDOW:]
        if all(n < EXTERNAL_NOVELTY_STAGNATION_THRESHOLD for n in recent):
            avg = sum(recent) / len(recent)
            return f"external_novelty:stagnation(avg={avg:.2f})"

    # 0b. universe_probe:candidate — universe_probe 가 제안한 candidate target
    trigger_src = gu.get("trigger_source", "") or ""
    if "universe_probe" in trigger_src:
        return "universe_probe:candidate"

    # 0c. reach_diversity:degraded — reach_ledger 기반 domain 다양성 확장 target
    if "reach_ledger" in trigger_src or "reach_diversity" in trigger_src:
        return "reach_diversity:degraded"

    # 1. deficit:category 또는 deficit:field
    if coverage_map and category:
        cat_info = coverage_map.get(category)
        if cat_info and isinstance(cat_info, dict) and "deficit_score" in cat_info:
            if cat_info["deficit_score"] > DEFICIT_THRESHOLD:
                return f"deficit:category={category}"
            # field-level deficit (해당 카테고리에서 field 미존재)
            fc = cat_info.get("field_coverage", {})
            if field and field not in fc:
                return f"deficit:field={field}"

    # 2. gini:category_imbalance 또는 gini:field_imbalance
    if coverage_map:
        summary = coverage_map.get("summary", {})
        cat_gini = summary.get("category_gini", 0)
        field_gini = summary.get("field_gini", 0)
        if cat_gini > GINI_THRESHOLD and category:
            cat_info = coverage_map.get(category)
            if cat_info and isinstance(cat_info, dict):
                if cat_info.get("ku_count", 0) < 5:
                    return "gini:category_imbalance"
        if field_gini > GINI_THRESHOLD:
            return "gini:field_imbalance"

    # 3. plateau:novelty
    if novelty_history and len(novelty_history) >= 5:
        recent = novelty_history[-5:]
        if all(n < 0.1 for n in recent):
            avg = sum(recent) / len(recent)
            return f"plateau:novelty<0.1(avg={avg:.2f})"

    # 4. remodel:pending
    if has_remodel_pending:
        return "remodel:pending"

    # 5. audit trigger
    trigger = gu.get("trigger", "")
    if trigger and "audit" in trigger.lower():
        return "audit:merge_pending"

    # 6. fallback
    if cycle == 0:
        return "seed:initial"

    return "seed:initial"


def _boost_deficit_categories(
    open_gus: list[dict],
    coverage_map: dict | None,
) -> list[dict]:
    """Gini 불균형 시 소수 카테고리 GU 우선 (P4-B4)."""
    if not coverage_map:
        return open_gus

    summary = coverage_map.get("summary", {})
    if summary.get("category_gini", 0) <= GINI_THRESHOLD:
        return open_gus

    # deficit 높은 카테고리 GU를 앞으로
    def deficit_key(gu: dict) -> float:
        ek = gu.get("target", {}).get("entity_key", "")
        parts = ek.split(":")
        cat = parts[1] if len(parts) >= 3 else ""
        cat_info = coverage_map.get(cat)
        if cat_info and isinstance(cat_info, dict):
            return -cat_info.get("deficit_score", 0)  # 높은 deficit = 낮은 정렬값
        return 0

    return sorted(open_gus, key=deficit_key)


def _select_targets(
    gap_map: list[dict],
    mode_decision: dict,
    axis_coverage: list[dict] | None = None,
) -> tuple[list[dict], list[dict]]:
    """Target 선정 — open_gus 전체에서 cycle_cap 만큼 반환 (S1-T2).

    explore/exploit 분리 제거. 정렬 없이 gap_map 순서 그대로.
    Returns:
        ([], exploit_targets)  — explore 슬롯 항상 비움
    """
    cycle_cap = (
        mode_decision.get("cycle_cap")
        or mode_decision.get("explore_budget", 0) + mode_decision.get("exploit_budget", 0)
    )

    open_gus = [gu for gu in gap_map if gu.get("status") == "open"]
    return [], open_gus[:cycle_cap]


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
    coverage_map = state.get("coverage_map")
    novelty_history = state.get("novelty_history")
    external_novelty_history = state.get("external_novelty_history")
    cycle = state.get("current_cycle", 0)

    # P4-B3: remodel pending 확인
    remodel_report = state.get("remodel_report")
    has_remodel_pending = bool(
        remodel_report
        and remodel_report.get("approval", {}).get("status") == "pending"
    )

    # P4-B4: Gini 불균형 시 소수 카테고리 우선
    # _select_targets 내부에서 정렬 전 적용
    open_gus_for_boost = [gu for gu in gap_map if gu.get("status") == "open"]
    boosted = _boost_deficit_categories(open_gus_for_boost, coverage_map)
    # boost 결과를 gap_map 순서에 반영 (open GU 순서만 변경)
    boosted_ids = [gu.get("gu_id") for gu in boosted]
    non_open = [gu for gu in gap_map if gu.get("status") != "open"]
    gap_map_ordered = boosted + non_open

    # Target 선정
    explore_targets, exploit_targets = _select_targets(
        gap_map_ordered, mode_decision, axis_coverage,
    )

    # 불변원칙 검증: Plan.target_gaps ⊆ G.open
    open_gu_ids = {gu.get("gu_id") for gu in gap_map if gu.get("status") == "open"}
    all_targets = explore_targets + exploit_targets
    for gu in all_targets:
        assert gu.get("gu_id") in open_gu_ids, (
            f"Gap-driven 위반: {gu.get('gu_id')} is not in open GU set"
        )

    import logging
    _logger = logging.getLogger(__name__)

    if llm is not None:
        # LLM 호출
        prompt = _build_plan_prompt(
            explore_targets, exploit_targets,
            mode_decision, skeleton, policies, critique,
        )
        response = llm.invoke(prompt)
        # LLM 응답 파싱 (JSON)
        from src.utils.llm_parse import extract_json
        try:
            plan = extract_json(response.content)
        except (ValueError, AttributeError):
            # fallback
            plan = _build_plan_from_targets(
                explore_targets, exploit_targets, mode_decision,
            )
            _logger.warning("plan: LLM parse failed → fallback (targets=%d)", len(all_targets))
    else:
        plan = _build_plan_from_targets(
            explore_targets, exploit_targets, mode_decision,
        )

    # P4-B1: reason_code 부여 (모든 target 에 필수)
    all_target_gus = explore_targets + exploit_targets
    gu_by_id = {gu.get("gu_id"): gu for gu in all_target_gus}
    reason_codes: dict[str, str] = {}
    for gu_id in plan.get("target_gaps", []):
        gu = gu_by_id.get(gu_id)
        if gu:
            reason_codes[gu_id] = _assign_reason_code(
                gu, coverage_map, novelty_history, has_remodel_pending, cycle,
                external_novelty_history=external_novelty_history,
            )
        else:
            reason_codes[gu_id] = "seed:initial"
    plan["reason_codes"] = reason_codes

    # P4-B3: remodel pending → target count 감소
    if has_remodel_pending:
        plan["remodel_pending_note"] = "remodel 대기 중 — target 보수화 권장"

    tg = plan.get("target_gaps", [])
    q = plan.get("queries", {})
    no_query = [gid for gid in tg if not q.get(gid)]
    rc = plan.get("reason_codes", {})
    _logger.info("plan: targets=%d, queries=%d, no_query=%d, reason_codes=%d",
                 len(tg), len(q), len(no_query), len(rc))

    return {"current_plan": plan}
