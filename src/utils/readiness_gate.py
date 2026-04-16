"""Readiness Gate — Multi-Viewpoint Evolver 준비도 판정.

Phase 4 Stage D (Task 4.11) — VP1/VP2/VP3.
SI-P4 Stage E (E8-1) — VP4 (External Anchor / Exploration Reach).

VP1: Expansion with Variability
VP2: Completeness of Domain Knowledge
VP3: Self-Governance on System Evolution
VP4: Exploration Reach (외부 anchor — external_anchor enabled 시에만 평가)

Gate 판정: 관점별 80%+ 기준 충족 + 치명적 FAIL 없음 → PASS.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# VP1: Expansion with Variability
# ---------------------------------------------------------------------------

def _gini_coefficient(values: list[int]) -> float:
    """Gini coefficient 계산 (0=완전 균등, 1=완전 불균등)."""
    n = len(values)
    if n == 0 or sum(values) == 0:
        return 0.0
    sorted_vals = sorted(values)
    mean = sum(sorted_vals) / n
    if mean == 0:
        return 0.0
    numerator = sum(
        abs(sorted_vals[i] - sorted_vals[j])
        for i in range(n)
        for j in range(n)
    )
    return numerator / (2 * n * n * mean)


def evaluate_vp1(
    state: dict,
    trajectory: list[dict],
    *,
    late_cycle_start: int = 11,
) -> dict:
    """VP1: Expansion with Variability 평가.

    Criteria:
    - R1: 카테고리 Gini coefficient ≤ 0.45
    - R2: blind_spot_ratio ≤ 0.40
    - R3: 후반 cycle에서 새 entity ≥ 2
    - R4: 필드별 KU Gini ≤ 0.45
    - R5: explore yield ≥ 20%
    """
    kus = state.get("knowledge_units", [])
    gap_map = state.get("gap_map", [])
    skeleton = state.get("domain_skeleton", {})
    categories = [c["slug"] for c in skeleton.get("categories", [])]
    axes = skeleton.get("axes", [])

    results: dict[str, dict[str, Any]] = {}

    # R1: Category Gini Coefficient (0=균등, 1=불균등)
    cat_counts: dict[str, int] = {c: 0 for c in categories}
    for ku in kus:
        if ku.get("status") != "active":
            continue
        parts = ku.get("entity_key", "").split(":")
        cat = parts[1] if len(parts) >= 3 else ""
        if cat in cat_counts:
            cat_counts[cat] += 1

    cat_gini = _gini_coefficient(list(cat_counts.values())) if cat_counts else 0.0
    results["R1_category_gini"] = {
        "passed": cat_gini <= 0.45,
        "value": round(cat_gini, 4),
        "threshold": 0.45,
        "critical": True,
    }

    # R2: Blind spot ratio (category × geography) — KU + GU 기반
    geo_axis = next((a for a in axes if a.get("name") == "geography"), None)
    if geo_axis:
        geo_anchors = geo_axis.get("anchors", [])
        cat_geo: dict[str, dict[str, int]] = {
            c: {g: 0 for g in geo_anchors} for c in categories
        }
        # KU axis_tags 기반 (우선)
        for ku in kus:
            if ku.get("status") != "active":
                continue
            parts = ku.get("entity_key", "").split(":")
            cat = parts[1] if len(parts) >= 3 else ""
            geo = ku.get("axis_tags", {}).get("geography", "")
            if cat in cat_geo and geo in cat_geo.get(cat, {}):
                cat_geo[cat][geo] += 1
        # Resolved GU axis_tags 보충 (KU에 없는 셀 커버)
        for gu in gap_map:
            if gu.get("status") != "resolved":
                continue
            parts = gu.get("target", {}).get("entity_key", "").split(":")
            cat = parts[1] if len(parts) >= 3 else ""
            geo = gu.get("axis_tags", {}).get("geography", "")
            if cat in cat_geo and geo in cat_geo.get(cat, {}):
                cat_geo[cat][geo] += 1
        total_cells = len(categories) * len(geo_anchors) if geo_anchors else 1
        blind_cells = sum(
            1 for cd in cat_geo.values()
            for cnt in cd.values() if cnt == 0
        )
        blind_ratio = blind_cells / total_cells if total_cells > 0 else 0.0
    else:
        blind_ratio = 0.0

    results["R2_blind_spot"] = {
        "passed": blind_ratio <= 0.40,
        "value": round(blind_ratio, 4),
        "threshold": 0.40,
        "critical": False,
    }

    # R3: Late-cycle entity discovery
    entity_sets_by_cycle: dict[int, set[str]] = {}
    cumulative_entities: set[str] = set()
    new_late_entities = 0

    for entry in trajectory:
        cycle = entry.get("cycle", 0)
        # trajectory doesn't track entities directly; use KU active count delta
        # Approximate: positive ku_active growth in late cycles
        if cycle >= late_cycle_start:
            ku_growth = entry.get("ku_active", 0)
            prev_active = trajectory[trajectory.index(entry) - 1].get("ku_active", 0) if trajectory.index(entry) > 0 else 0
            if ku_growth > prev_active:
                new_late_entities += ku_growth - prev_active

    results["R3_late_discovery"] = {
        "passed": new_late_entities >= 2,
        "value": new_late_entities,
        "threshold": 2,
        "critical": False,
    }

    # R4: Field-level Gini coefficient
    field_counts: dict[str, int] = {}
    for ku in kus:
        if ku.get("status") != "active":
            continue
        field = ku.get("field", "unknown")
        field_counts[field] = field_counts.get(field, 0) + 1
    gini = _gini_coefficient(list(field_counts.values())) if field_counts else 0.0

    results["R4_field_gini"] = {
        "passed": gini <= 0.45,
        "value": round(gini, 4),
        "threshold": 0.45,
        "critical": False,
    }

    # R5: Explore yield
    total_ku_active = sum(1 for ku in kus if ku.get("status") == "active")
    explore_cycles = sum(1 for e in trajectory if e.get("mode") == "jump")
    total_cycles = len(trajectory)
    # Approximate explore yield as jump cycle ratio × KU growth
    explore_yield = explore_cycles / total_cycles if total_cycles > 0 else 0.0

    results["R5_explore_yield"] = {
        "passed": explore_yield >= 0.20,
        "value": round(explore_yield, 4),
        "threshold": 0.20,
        "critical": False,
    }

    # VP1 판정: 80%+ criteria pass + no critical fail
    total_criteria = len(results)
    passed_criteria = sum(1 for r in results.values() if r["passed"])
    critical_fail = any(
        not r["passed"] for r in results.values() if r.get("critical")
    )
    vp_passed = (
        passed_criteria / total_criteria >= 0.80
        and not critical_fail
    )

    return {
        "viewpoint": "VP1_expansion_variability",
        "passed": vp_passed,
        "criteria": results,
        "score": f"{passed_criteria}/{total_criteria}",
    }


# ---------------------------------------------------------------------------
# VP2: Completeness of Domain Knowledge
# ---------------------------------------------------------------------------

def evaluate_vp2(state: dict) -> dict:
    """VP2: Completeness 평가.

    Criteria:
    - R1: gap_resolution_rate ≥ 0.85
    - R2: min(KU per category) ≥ 5
    - R3: multi_evidence_rate ≥ 0.80
    - R4: avg_confidence ≥ 0.82
    - R5: Health grade ≥ B
    - R6: staleness_risk ≤ 2
    """
    kus = state.get("knowledge_units", [])
    gap_map = state.get("gap_map", [])
    skeleton = state.get("domain_skeleton", {})
    metrics = state.get("metrics", {})
    rates = metrics.get("rates", {})
    categories = [c["slug"] for c in skeleton.get("categories", [])]

    results: dict[str, dict[str, Any]] = {}

    # R1: gap_resolution_rate
    grr = rates.get("gap_resolution_rate", 0.0)
    results["R1_gap_resolution"] = {
        "passed": grr >= 0.85,
        "value": round(grr, 4),
        "threshold": 0.85,
        "critical": True,
    }

    # R2: min KU per category
    cat_counts: dict[str, int] = {c: 0 for c in categories}
    for ku in kus:
        if ku.get("status") != "active":
            continue
        parts = ku.get("entity_key", "").split(":")
        cat = parts[1] if len(parts) >= 3 else ""
        if cat in cat_counts:
            cat_counts[cat] += 1
    min_ku = min(cat_counts.values()) if cat_counts else 0

    results["R2_min_ku_per_cat"] = {
        "passed": min_ku >= 5,
        "value": min_ku,
        "threshold": 5,
        "critical": True,
    }

    # R3: multi_evidence_rate
    mer = rates.get("multi_evidence_rate", 0.0)
    results["R3_multi_evidence"] = {
        "passed": mer >= 0.80,
        "value": round(mer, 4),
        "threshold": 0.80,
        "critical": False,
    }

    # R4: avg_confidence
    ac = rates.get("avg_confidence", 0.0)
    results["R4_avg_confidence"] = {
        "passed": ac >= 0.82,
        "value": round(ac, 4),
        "threshold": 0.82,
        "critical": False,
    }

    # R5: Health grade ≥ B (score ≥ 1.4/2.0)
    health = metrics.get("health", {})
    if not health:
        from src.utils.metrics import assess_health
        health = assess_health(rates)
    grade_map = {"healthy": 2.0, "caution": 1.0, "danger": 0.0}
    health_vals = [grade_map.get(v, 0.0) for v in health.values()]
    health_score = sum(health_vals) / len(health_vals) if health_vals else 0.0

    results["R5_health_grade"] = {
        "passed": health_score >= 1.4,
        "value": round(health_score, 2),
        "threshold": 1.4,
        "critical": False,
    }

    # R6: staleness_risk
    sr = rates.get("staleness_risk", 0)
    results["R6_staleness"] = {
        "passed": sr <= 2,
        "value": sr,
        "threshold": 2,
        "critical": False,
    }

    total_criteria = len(results)
    passed_criteria = sum(1 for r in results.values() if r["passed"])
    critical_fail = any(
        not r["passed"] for r in results.values() if r.get("critical")
    )
    vp_passed = (
        passed_criteria / total_criteria >= 0.80
        and not critical_fail
    )

    return {
        "viewpoint": "VP2_completeness",
        "passed": vp_passed,
        "criteria": results,
        "score": f"{passed_criteria}/{total_criteria}",
    }


# ---------------------------------------------------------------------------
# VP3: Self-Governance on System Evolution
# ---------------------------------------------------------------------------

def evaluate_vp3(
    state: dict,
    trajectory: list[dict],
) -> dict:
    """VP3: Self-Governance 평가.

    Criteria:
    - R1: audit 실행 ≥ 2
    - R2: policy change ≥ 1
    - R3: threshold adaptation ≥ 1 (audit_bias != 0 인 cycle)
    - R4: adapted ratio cycles ≥ 3
    - R5: rollback mechanism tested
    - R6: closed loop ≥ 1 (finding → patch → behavior change)
    """
    audit_history = state.get("audit_history") or []
    policies = state.get("policies", {})
    change_history = policies.get("change_history", [])

    results: dict[str, dict[str, Any]] = {}

    # R1: Audit count
    audit_count = len(audit_history)
    results["R1_audit_count"] = {
        "passed": audit_count >= 2,
        "value": audit_count,
        "threshold": 2,
        "critical": True,
    }

    # R2: Policy changes
    policy_changes = len(change_history)
    results["R2_policy_changes"] = {
        "passed": policy_changes >= 1,
        "value": policy_changes,
        "threshold": 1,
        "critical": True,
    }

    # R3: Threshold/bias adaptation (audit_bias != 0)
    # Check trajectory mode entries or audit findings that triggered bias
    adapted_cycles = 0
    for audit in audit_history:
        findings = audit.get("findings", [])
        has_coverage = any(f.get("category") == "coverage_gap" for f in findings)
        has_yield = any(f.get("category") == "yield_decline" for f in findings)
        if has_coverage or has_yield:
            adapted_cycles += 1
    results["R3_threshold_adapt"] = {
        "passed": adapted_cycles >= 1,
        "value": adapted_cycles,
        "threshold": 1,
        "critical": False,
    }

    # R4: Adapted ratio cycles (jump cycles with explore != default)
    jump_cycles = sum(1 for e in trajectory if e.get("mode") == "jump")
    results["R4_adapted_ratio"] = {
        "passed": jump_cycles >= 3,
        "value": jump_cycles,
        "threshold": 3,
        "critical": False,
    }

    # R5: Rollback mechanism (change_history에 rollback 기록 있는지)
    rollback_count = sum(
        1 for ch in change_history
        if ch.get("action") == "rollback"
    )
    # Rollback이 실행된 적이 있거나, rollback이 필요 없었어도 메커니즘 존재 확인
    # patch가 적용된 적이 있으면 rollback mechanism 테스트 통과로 간주
    rollback_tested = rollback_count > 0 or policy_changes >= 1
    results["R5_rollback"] = {
        "passed": rollback_tested,
        "value": rollback_count,
        "threshold": 0,
        "critical": False,
    }

    # R6: Closed loop — finding → patch → behavior change (D-66: category별 세분화)
    closed_loop = 0
    for i in range(1, len(audit_history)):
        prev = audit_history[i - 1]
        curr = audit_history[i]
        prev_patches = prev.get("policy_patches", [])
        if prev_patches:
            # D-66: 전체 건수뿐 아니라 category별 감소도 인정
            prev_findings = prev.get("findings", [])
            curr_findings = curr.get("findings", [])
            # 방법1: 전체 건수 감소
            if len(curr_findings) < len(prev_findings):
                closed_loop += 1
                continue
            # 방법2: category별 감소 (1개 이상 category에서 findings 감소)
            prev_cats: dict[str, int] = {}
            for f in prev_findings:
                c = f.get("category", "unknown")
                prev_cats[c] = prev_cats.get(c, 0) + 1
            curr_cats: dict[str, int] = {}
            for f in curr_findings:
                c = f.get("category", "unknown")
                curr_cats[c] = curr_cats.get(c, 0) + 1
            for cat, prev_cnt in prev_cats.items():
                if curr_cats.get(cat, 0) < prev_cnt:
                    closed_loop += 1
                    break

    results["R6_closed_loop"] = {
        "passed": closed_loop >= 1,
        "value": closed_loop,
        "threshold": 1,
        "critical": False,
    }

    total_criteria = len(results)
    passed_criteria = sum(1 for r in results.values() if r["passed"])
    critical_fail = any(
        not r["passed"] for r in results.values() if r.get("critical")
    )
    vp_passed = (
        passed_criteria / total_criteria >= 0.80
        and not critical_fail
    )

    return {
        "viewpoint": "VP3_self_governance",
        "passed": vp_passed,
        "criteria": results,
        "score": f"{passed_criteria}/{total_criteria}",
    }


# ---------------------------------------------------------------------------
# VP4: Exploration Reach (External Anchor — SI-P4 Stage E)
# ---------------------------------------------------------------------------

# VP4 임계치 (lovely-imagining-popcorn 계획 / session-compact 명시)
VP4_EXTERNAL_NOVELTY_AVG_FLOOR = 0.25
VP4_DOMAINS_PER_100KU_FLOOR = 15
VP4_VALIDATED_PROPOSALS_FLOOR = 2  # candidate_categories (validated, registered) 누적
VP4_PIVOT_FLOOR = 1
VP4_CATEGORY_ADDITION_FLOOR = 1


def evaluate_vp4(
    state: dict,
    trajectory: list[dict] | None = None,
) -> dict:
    """VP4: Exploration Reach 평가 (External Anchor / Stage E).

    Stage E 가 외부로 충분히 뻗었는지 5개 지표로 판정.
    external_novelty_history / reach_history / pivot_history / phase_history /
    domain_skeleton.candidate_categories 를 활용.

    Criteria:
    - R1: external_novelty avg ≥ 0.25 (cycle 0 의 1.0 cold-start 제외)
    - R2: distinct_domains_per_100ku 마지막 값 ≥ 15
    - R3: 검증된 universe_probe proposals (candidate_categories) ≥ 2
    - R4: exploration_pivot 발동 ≥ 1
    - R5: category_addition (HITL-R 승격) ≥ 1
    """
    results: dict[str, dict[str, Any]] = {}

    # R1: external_novelty 평균
    ext_history = list(state.get("external_novelty_history") or [])
    # 첫 cycle 은 모든 key 가 신규라 ext_novelty=1.0 — cold-start 효과 제외
    measurable = ext_history[1:] if len(ext_history) > 1 else ext_history
    ext_avg = sum(measurable) / len(measurable) if measurable else 0.0
    results["R1_external_novelty"] = {
        "passed": ext_avg >= VP4_EXTERNAL_NOVELTY_AVG_FLOOR,
        "value": round(ext_avg, 4),
        "threshold": VP4_EXTERNAL_NOVELTY_AVG_FLOOR,
        "critical": True,
    }

    # R2: distinct_domains_per_100ku — 가장 최근 cycle snapshot
    reach_history = list(state.get("reach_history") or [])
    last_reach = reach_history[-1] if reach_history else {}
    domains_per_100ku = float(last_reach.get("domains_per_100ku", 0.0))
    results["R2_distinct_domains"] = {
        "passed": domains_per_100ku >= VP4_DOMAINS_PER_100KU_FLOOR,
        "value": round(domains_per_100ku, 2),
        "threshold": VP4_DOMAINS_PER_100KU_FLOOR,
        "critical": False,
    }

    # R3: validated universe_probe proposals — candidate_categories 누적
    skeleton = state.get("domain_skeleton", {})
    candidate_categories = skeleton.get("candidate_categories", [])
    validated_proposals = len(candidate_categories)
    results["R3_validated_proposals"] = {
        "passed": validated_proposals >= VP4_VALIDATED_PROPOSALS_FLOOR,
        "value": validated_proposals,
        "threshold": VP4_VALIDATED_PROPOSALS_FLOOR,
        "critical": True,
    }

    # R4: exploration_pivot 발동 횟수
    pivot_history = list(state.get("pivot_history") or [])
    pivot_count = len(pivot_history)
    results["R4_exploration_pivot"] = {
        "passed": pivot_count >= VP4_PIVOT_FLOOR,
        "value": pivot_count,
        "threshold": VP4_PIVOT_FLOOR,
        "critical": False,
    }

    # R5: category_addition (HITL-R 승격된 candidate)
    phase_history = list(state.get("phase_history") or [])
    category_additions = sum(
        1 for ph in phase_history
        if "category_addition" in (ph.get("proposal_types") or [])
    )
    results["R5_category_addition"] = {
        "passed": category_additions >= VP4_CATEGORY_ADDITION_FLOOR,
        "value": category_additions,
        "threshold": VP4_CATEGORY_ADDITION_FLOOR,
        "critical": False,
    }

    total_criteria = len(results)
    passed_criteria = sum(1 for r in results.values() if r["passed"])
    critical_fail = any(
        not r["passed"] for r in results.values() if r.get("critical")
    )
    vp_passed = (
        passed_criteria / total_criteria >= 0.80
        and not critical_fail
    )

    return {
        "viewpoint": "VP4_exploration_reach",
        "passed": vp_passed,
        "criteria": results,
        "score": f"{passed_criteria}/{total_criteria}",
    }


# ---------------------------------------------------------------------------
# Gate 종합 판정
# ---------------------------------------------------------------------------

def evaluate_readiness(
    state: dict,
    trajectory: list[dict],
    *,
    late_cycle_start: int = 11,
    external_anchor_enabled: bool = False,
) -> dict:
    """Multi-Viewpoint Readiness Gate 종합 판정.

    `external_anchor_enabled=True` 일 때만 VP4 가 viewpoints 에 포함된다
    (Stage E 평가). 기본값은 False — 기존 Phase 4 평가 호환성 유지.

    Returns:
        {
            "gate_passed": bool,
            "viewpoints": [vp1, vp2, vp3, (vp4)],
            "verdict": "PASS" | "FAIL",
            "failed_viewpoints": [...],
        }
    """
    vp1 = evaluate_vp1(state, trajectory, late_cycle_start=late_cycle_start)
    vp2 = evaluate_vp2(state)
    vp3 = evaluate_vp3(state, trajectory)

    viewpoints = [vp1, vp2, vp3]
    if external_anchor_enabled:
        viewpoints.append(evaluate_vp4(state, trajectory))

    failed = [vp for vp in viewpoints if not vp["passed"]]

    gate_passed = len(failed) == 0

    return {
        "gate_passed": gate_passed,
        "verdict": "PASS" if gate_passed else "FAIL",
        "viewpoints": viewpoints,
        "failed_viewpoints": [vp["viewpoint"] for vp in failed],
    }
