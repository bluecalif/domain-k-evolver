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
