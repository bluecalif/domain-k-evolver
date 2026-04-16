"""test_readiness_gate — Phase 4 Stage D: Readiness Gate 테스트.

Task 4.11: 3-Viewpoint Readiness 판정
Task 4.10: Gate 통합 판정
"""

from __future__ import annotations

import pytest

from src.utils.readiness_gate import (
    _gini_coefficient,
    evaluate_readiness,
    evaluate_vp1,
    evaluate_vp2,
    evaluate_vp3,
    evaluate_vp4,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_kus(categories: dict[str, int], confidence: float = 0.90) -> list[dict]:
    """카테고리별 KU 개수 지정하여 KU 리스트 생성."""
    kus = []
    ku_id = 1
    for cat, count in categories.items():
        for i in range(count):
            kus.append({
                "ku_id": f"KU-{ku_id:04d}",
                "entity_key": f"test:{cat}:entity-{i}",
                "field": f"field-{i % 3}",
                "status": "active",
                "evidence_links": ["EU-1", "EU-2"],
                "confidence": confidence,
            })
            ku_id += 1
    return kus


def _make_gap_map(resolved: int, open_count: int, categories: list[str]) -> list[dict]:
    gus = []
    gu_id = 1
    for i in range(resolved):
        cat = categories[i % len(categories)]
        gus.append({
            "gu_id": f"GU-{gu_id:04d}",
            "status": "resolved",
            "gap_type": "missing",
            "expected_utility": "high",
            "target": {"entity_key": f"test:{cat}:entity-{i}"},
        })
        gu_id += 1
    for i in range(open_count):
        cat = categories[i % len(categories)]
        gus.append({
            "gu_id": f"GU-{gu_id:04d}",
            "status": "open",
            "gap_type": "missing",
            "expected_utility": "medium",
            "target": {"entity_key": f"test:{cat}:entity-r{i}"},
        })
        gu_id += 1
    return gus


def _make_skeleton(categories: list[str]) -> dict:
    return {
        "categories": [{"slug": c} for c in categories],
        "axes": [
            {"name": "category", "anchors": categories, "required": True},
        ],
    }


def _make_trajectory(cycles: int, mode: str = "normal") -> list[dict]:
    entries = []
    for i in range(1, cycles + 1):
        entries.append({
            "cycle": i,
            "ku_active": 5 + i * 3,
            "mode": mode if i <= cycles // 2 else "normal",
        })
    return entries


def _healthy_state(categories: list[str] | None = None) -> dict:
    """모든 VP가 PASS 가능한 건강한 State."""
    cats = categories or ["transport", "accommodation", "food", "activity"]
    cat_kus = {c: 8 for c in cats}
    kus = _make_kus(cat_kus, confidence=0.92)
    gap_map = _make_gap_map(resolved=40, open_count=5, categories=cats)
    return {
        "knowledge_units": kus,
        "gap_map": gap_map,
        "domain_skeleton": _make_skeleton(cats),
        "metrics": {
            "rates": {
                "evidence_rate": 1.0,
                "multi_evidence_rate": 0.85,
                "gap_resolution_rate": 0.89,
                "conflict_rate": 0.0,
                "avg_confidence": 0.92,
                "staleness_risk": 0,
            },
        },
        "policies": {
            "version": 3,
            "change_history": [
                {"action": "apply", "cycle": 5},
                {"action": "apply", "cycle": 10},
            ],
        },
        "audit_history": [
            {
                "audit_cycle": 5,
                "findings": [
                    {"category": "coverage_gap", "severity": "warning"},
                    {"category": "yield_decline", "severity": "warning"},
                ],
                "policy_patches": [{"patch_id": "PP-001"}],
            },
            {
                "audit_cycle": 10,
                "findings": [
                    {"category": "coverage_gap", "severity": "info"},
                ],
                "policy_patches": [],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Gini Coefficient
# ---------------------------------------------------------------------------

class TestGiniCoefficient:
    def test_perfect_equality(self) -> None:
        assert _gini_coefficient([10, 10, 10]) == 0.0

    def test_inequality(self) -> None:
        gini = _gini_coefficient([0, 0, 100])
        assert gini > 0.5

    def test_empty(self) -> None:
        assert _gini_coefficient([]) == 0.0


# ---------------------------------------------------------------------------
# VP1: Expansion with Variability
# ---------------------------------------------------------------------------

class TestVP1:
    def test_healthy_passes(self) -> None:
        state = _healthy_state()
        trajectory = _make_trajectory(15, mode="jump")
        result = evaluate_vp1(state, trajectory, late_cycle_start=11)
        assert result["viewpoint"] == "VP1_expansion_variability"
        assert result["criteria"]["R1_category_gini"]["passed"] is True

    def test_skewed_gini_fails(self) -> None:
        cats = ["transport", "accommodation", "food", "activity"]
        kus = _make_kus({"transport": 50, "accommodation": 1, "food": 1, "activity": 1})
        state = {
            "knowledge_units": kus,
            "gap_map": [],
            "domain_skeleton": _make_skeleton(cats),
        }
        result = evaluate_vp1(state, _make_trajectory(15))
        assert result["criteria"]["R1_category_gini"]["passed"] is False
        # R1 is critical → VP1 fails
        assert result["passed"] is False

    def test_no_late_discovery(self) -> None:
        state = _healthy_state()
        # Flat trajectory (no growth in late cycles)
        trajectory = [{"cycle": i, "ku_active": 30, "mode": "normal"} for i in range(1, 16)]
        result = evaluate_vp1(state, trajectory, late_cycle_start=11)
        assert result["criteria"]["R3_late_discovery"]["passed"] is False

    def test_blind_spot_from_ku_axis_tags(self) -> None:
        """KU axis_tags.geography 기반 blind_spot 계산."""
        cats = ["transport", "dining"]
        geo_anchors = ["tokyo", "osaka"]
        kus = []
        ku_id = 1
        # transport: tokyo, osaka 모두 커버
        for geo in ["tokyo", "osaka"]:
            kus.append({
                "ku_id": f"KU-{ku_id:04d}", "entity_key": f"test:{cats[0]}:e-{ku_id}",
                "field": "price", "status": "active", "axis_tags": {"geography": geo},
                "evidence_links": ["EU-1"], "confidence": 0.9,
            })
            ku_id += 1
        # dining: tokyo만 커버 → osaka blind spot
        kus.append({
            "ku_id": f"KU-{ku_id:04d}", "entity_key": f"test:{cats[1]}:e-{ku_id}",
            "field": "price", "status": "active", "axis_tags": {"geography": "tokyo"},
            "evidence_links": ["EU-1"], "confidence": 0.9,
        })
        state = {
            "knowledge_units": kus,
            "gap_map": [],
            "domain_skeleton": {
                "categories": [{"slug": c} for c in cats],
                "axes": [{"name": "geography", "anchors": geo_anchors}],
            },
        }
        result = evaluate_vp1(state, _make_trajectory(15))
        # 4 cells, 1 blind (dining×osaka) → ratio=0.25
        assert result["criteria"]["R2_blind_spot"]["value"] == 0.25
        assert result["criteria"]["R2_blind_spot"]["passed"] is True


# ---------------------------------------------------------------------------
# VP2: Completeness
# ---------------------------------------------------------------------------

class TestVP2:
    def test_healthy_passes(self) -> None:
        state = _healthy_state()
        result = evaluate_vp2(state)
        assert result["viewpoint"] == "VP2_completeness"
        assert result["passed"] is True

    def test_low_gap_resolution_critical_fail(self) -> None:
        state = _healthy_state()
        state["metrics"]["rates"]["gap_resolution_rate"] = 0.50
        result = evaluate_vp2(state)
        assert result["criteria"]["R1_gap_resolution"]["passed"] is False
        assert result["passed"] is False  # critical

    def test_low_min_ku_critical_fail(self) -> None:
        cats = ["transport", "accommodation", "food", "activity"]
        kus = _make_kus({"transport": 10, "accommodation": 2, "food": 10, "activity": 10})
        state = _healthy_state()
        state["knowledge_units"] = kus
        result = evaluate_vp2(state)
        assert result["criteria"]["R2_min_ku_per_cat"]["passed"] is False
        assert result["passed"] is False

    def test_low_confidence_non_critical(self) -> None:
        state = _healthy_state()
        state["metrics"]["rates"]["avg_confidence"] = 0.75
        result = evaluate_vp2(state)
        assert result["criteria"]["R4_avg_confidence"]["passed"] is False
        # Not critical, other criteria pass → might still pass VP2

    def test_staleness_pass(self) -> None:
        state = _healthy_state()
        state["metrics"]["rates"]["staleness_risk"] = 1
        result = evaluate_vp2(state)
        assert result["criteria"]["R6_staleness"]["passed"] is True


# ---------------------------------------------------------------------------
# VP3: Self-Governance
# ---------------------------------------------------------------------------

class TestVP3:
    def test_healthy_passes(self) -> None:
        state = _healthy_state()
        trajectory = _make_trajectory(15, mode="jump")
        result = evaluate_vp3(state, trajectory)
        assert result["viewpoint"] == "VP3_self_governance"
        assert result["passed"] is True

    def test_no_audits_critical_fail(self) -> None:
        state = _healthy_state()
        state["audit_history"] = []
        result = evaluate_vp3(state, _make_trajectory(15))
        assert result["criteria"]["R1_audit_count"]["passed"] is False
        assert result["passed"] is False

    def test_no_policy_changes_critical_fail(self) -> None:
        state = _healthy_state()
        state["policies"]["change_history"] = []
        result = evaluate_vp3(state, _make_trajectory(15))
        assert result["criteria"]["R2_policy_changes"]["passed"] is False
        assert result["passed"] is False

    def test_closed_loop_detection(self) -> None:
        state = _healthy_state()
        # audit[0] has 2 findings + patches, audit[1] has 1 finding → improvement
        trajectory = _make_trajectory(15)
        result = evaluate_vp3(state, trajectory)
        assert result["criteria"]["R6_closed_loop"]["passed"] is True
        assert result["criteria"]["R6_closed_loop"]["value"] == 1

    def test_no_closed_loop(self) -> None:
        state = _healthy_state()
        # Make findings increase in all categories (no improvement anywhere)
        state["audit_history"] = [
            {"audit_cycle": 5, "findings": [{"category": "coverage_gap"}],
             "policy_patches": [{"patch_id": "PP-001"}]},
            {"audit_cycle": 10, "findings": [
                {"category": "coverage_gap"}, {"category": "yield_decline"},
            ], "policy_patches": []},
        ]
        result = evaluate_vp3(state, _make_trajectory(15))
        assert result["criteria"]["R6_closed_loop"]["passed"] is False

    def test_closed_loop_category_improvement(self) -> None:
        """D-66: 전체 건수 동일해도 특정 category 감소 시 closed loop 인정."""
        state = _healthy_state()
        state["audit_history"] = [
            {
                "audit_cycle": 5,
                "findings": [
                    {"category": "coverage_gap", "severity": "warning"},
                    {"category": "yield_decline", "severity": "warning"},
                ],
                "policy_patches": [{"patch_id": "PP-001"}],
            },
            {
                "audit_cycle": 10,
                # 전체 2건 유지, 하지만 coverage_gap 1→0 (category 감소!)
                "findings": [
                    {"category": "yield_decline", "severity": "warning"},
                    {"category": "yield_decline", "severity": "info"},
                ],
                "policy_patches": [],
            },
        ]
        result = evaluate_vp3(state, _make_trajectory(15))
        # D-66: coverage_gap이 1→0으로 감소 → closed loop 인정
        assert result["criteria"]["R6_closed_loop"]["passed"] is True
        assert result["criteria"]["R6_closed_loop"]["value"] >= 1

    def test_rollback_with_policy_change(self) -> None:
        state = _healthy_state()
        result = evaluate_vp3(state, _make_trajectory(15))
        assert result["criteria"]["R5_rollback"]["passed"] is True

    def test_threshold_adaptation_detected(self) -> None:
        state = _healthy_state()
        # audit has coverage_gap → bias adaptation
        result = evaluate_vp3(state, _make_trajectory(15))
        assert result["criteria"]["R3_threshold_adapt"]["passed"] is True


# ---------------------------------------------------------------------------
# Gate 종합
# ---------------------------------------------------------------------------

class TestEvaluateReadiness:
    def test_all_pass(self) -> None:
        state = _healthy_state()
        trajectory = _make_trajectory(15, mode="jump")
        result = evaluate_readiness(state, trajectory)
        assert result["verdict"] == "PASS"
        assert result["gate_passed"] is True
        assert len(result["failed_viewpoints"]) == 0

    def test_vp3_fail_blocks_gate(self) -> None:
        state = _healthy_state()
        state["audit_history"] = []
        state["policies"]["change_history"] = []
        trajectory = _make_trajectory(15)
        result = evaluate_readiness(state, trajectory)
        assert result["verdict"] == "FAIL"
        assert "VP3_self_governance" in result["failed_viewpoints"]

    def test_multiple_failures(self) -> None:
        state = _healthy_state()
        state["audit_history"] = []
        state["policies"]["change_history"] = []
        state["metrics"]["rates"]["gap_resolution_rate"] = 0.30
        trajectory = _make_trajectory(15)
        result = evaluate_readiness(state, trajectory)
        assert result["verdict"] == "FAIL"
        assert len(result["failed_viewpoints"]) >= 2

    def test_returns_three_viewpoints(self) -> None:
        state = _healthy_state()
        trajectory = _make_trajectory(15, mode="jump")
        result = evaluate_readiness(state, trajectory)
        assert len(result["viewpoints"]) == 3
        vp_names = {vp["viewpoint"] for vp in result["viewpoints"]}
        assert vp_names == {
            "VP1_expansion_variability",
            "VP2_completeness",
            "VP3_self_governance",
        }


# ---------------------------------------------------------------------------
# VP4: Exploration Reach (External Anchor) — SI-P4 Stage E (E8-1)
# ---------------------------------------------------------------------------

def _stage_e_state(
    *,
    ext_history: list[float] | None = None,
    domains_per_100ku: float = 18.0,
    candidate_count: int = 3,
    pivot_count: int = 1,
    category_addition_count: int = 1,
) -> dict:
    """VP4 평가용 state — 모든 criteria pass 가능한 기본값."""
    base = _healthy_state()
    if ext_history is None:
        # cold-start cycle 1 = 1.0, 이후 0.30~ → avg(slice[1:]) ≈ 0.30 ≥ 0.25
        ext_history = [1.0] + [0.30] * 14
    base["external_novelty_history"] = ext_history
    base["reach_history"] = [
        {"cycle": i, "domains_per_100ku": domains_per_100ku, "distinct_domains": 5,
         "active_ku_count": 30}
        for i in range(1, 16)
    ]
    base["pivot_history"] = [
        {"cycle": 7, "variants": 3, "candidate_targets": 2, "reason": "plateau"}
        for _ in range(pivot_count)
    ]
    base["domain_skeleton"]["candidate_categories"] = [
        {"slug": f"cand-{i}", "status": "validated"} for i in range(candidate_count)
    ]
    base["phase_history"] = [
        {"phase_number": i, "cycle": 5 * i, "report_id": f"R-{i}",
         "proposals_applied": 1, "proposal_types": ["category_addition"]}
        for i in range(1, category_addition_count + 1)
    ]
    return base


class TestVP4:
    def test_healthy_passes(self) -> None:
        state = _stage_e_state()
        result = evaluate_vp4(state)
        assert result["viewpoint"] == "VP4_exploration_reach"
        assert result["passed"] is True
        for key, crit in result["criteria"].items():
            assert crit["passed"] is True, f"{key} should pass: {crit}"

    def test_low_external_novelty_fails_critical(self) -> None:
        # 모든 measurable cycle 의 ext_novelty 가 floor 미만
        state = _stage_e_state(ext_history=[1.0] + [0.10] * 14)
        result = evaluate_vp4(state)
        assert result["criteria"]["R1_external_novelty"]["passed"] is False
        assert result["passed"] is False  # critical fail

    def test_external_novelty_skips_cold_start(self) -> None:
        """cycle 1 의 1.0 (cold-start) 는 평균 계산에서 제외."""
        state = _stage_e_state(ext_history=[1.0, 0.30])
        result = evaluate_vp4(state)
        # avg(slice[1:]) = 0.30 → pass
        assert result["criteria"]["R1_external_novelty"]["value"] == 0.30
        assert result["criteria"]["R1_external_novelty"]["passed"] is True

    def test_external_novelty_empty_history_fails(self) -> None:
        state = _stage_e_state(ext_history=[])
        result = evaluate_vp4(state)
        assert result["criteria"]["R1_external_novelty"]["value"] == 0.0
        assert result["criteria"]["R1_external_novelty"]["passed"] is False

    def test_low_distinct_domains_non_critical(self) -> None:
        state = _stage_e_state(domains_per_100ku=10.0)
        result = evaluate_vp4(state)
        assert result["criteria"]["R2_distinct_domains"]["passed"] is False
        # 4/5 → 80% 충족 + critical 모두 통과 → VP4 still passes
        assert result["passed"] is True

    def test_no_validated_proposals_fails_critical(self) -> None:
        state = _stage_e_state(candidate_count=0)
        result = evaluate_vp4(state)
        assert result["criteria"]["R3_validated_proposals"]["passed"] is False
        assert result["passed"] is False  # critical fail

    def test_no_pivot_non_critical(self) -> None:
        state = _stage_e_state(pivot_count=0)
        result = evaluate_vp4(state)
        assert result["criteria"]["R4_exploration_pivot"]["passed"] is False
        assert result["passed"] is True

    def test_no_category_addition_non_critical(self) -> None:
        state = _stage_e_state(category_addition_count=0)
        result = evaluate_vp4(state)
        assert result["criteria"]["R5_category_addition"]["passed"] is False
        assert result["passed"] is True

    def test_two_non_critical_fails_breaks_80pct(self) -> None:
        """non-critical 2개 fail → 3/5 = 60% < 80% → VP4 fail."""
        state = _stage_e_state(pivot_count=0, category_addition_count=0)
        result = evaluate_vp4(state)
        # R4, R5 fail → 3/5 = 60%
        assert result["score"] == "3/5"
        assert result["passed"] is False


class TestEvaluateReadinessWithVP4:
    """VP4 통합 — external_anchor_enabled=True 시 viewpoints 에 포함."""

    def test_vp4_excluded_by_default(self) -> None:
        state = _stage_e_state()
        result = evaluate_readiness(state, _make_trajectory(15, mode="jump"))
        vp_names = {vp["viewpoint"] for vp in result["viewpoints"]}
        assert "VP4_exploration_reach" not in vp_names
        assert len(result["viewpoints"]) == 3

    def test_vp4_included_when_enabled(self) -> None:
        state = _stage_e_state()
        result = evaluate_readiness(
            state, _make_trajectory(15, mode="jump"),
            external_anchor_enabled=True,
        )
        assert len(result["viewpoints"]) == 4
        vp_names = {vp["viewpoint"] for vp in result["viewpoints"]}
        assert "VP4_exploration_reach" in vp_names
        assert result["verdict"] == "PASS"

    def test_vp4_failure_blocks_gate_when_enabled(self) -> None:
        state = _stage_e_state(candidate_count=0)  # critical R3 fail
        result = evaluate_readiness(
            state, _make_trajectory(15, mode="jump"),
            external_anchor_enabled=True,
        )
        assert result["verdict"] == "FAIL"
        assert "VP4_exploration_reach" in result["failed_viewpoints"]
