"""P4-D3: plan reason_code 생성 테스트 + B2 machine_rules + B3 remodel_pending + B4 Gini priority."""

from __future__ import annotations

import pytest

from src.nodes.plan import (
    _assign_reason_code,
    _boost_deficit_categories,
    plan_node,
)


def _make_gu(gu_id: str, entity_key: str, field: str = "price", **extra) -> dict:
    return {
        "gu_id": gu_id,
        "gap_type": "missing",
        "target": {"entity_key": entity_key, "field": field},
        "expected_utility": "high",
        "risk_level": "convenience",
        "status": "open",
        **extra,
    }


def _make_coverage_map(categories: dict[str, dict], gini: float = 0.0, field_gini: float = 0.0) -> dict:
    result = dict(categories)
    result["summary"] = {
        "category_gini": gini,
        "field_gini": field_gini,
        "gini_deficit_adjustment": 0.0,
        "total_kus": sum(c.get("ku_count", 0) for c in categories.values()),
        "categories_count": len(categories),
    }
    return result


class TestAssignReasonCode:
    """_assign_reason_code 단위 테스트."""

    def test_deficit_category(self):
        """deficit > 0.5 → deficit:category=..."""
        gu = _make_gu("GU-1", "d:food:ramen", "price")
        cm = _make_coverage_map({
            "food": {"ku_count": 1, "deficit_score": 0.8, "field_coverage": {}},
        })
        code = _assign_reason_code(gu, cm, None, False, 5)
        assert code == "deficit:category=food"

    def test_deficit_field(self):
        """카테고리 deficit 낮지만 field 미존재 → deficit:field=..."""
        gu = _make_gu("GU-1", "d:transport:jr", "schedule")
        cm = _make_coverage_map({
            "transport": {"ku_count": 8, "deficit_score": 0.2, "field_coverage": {"price": 5}},
        })
        code = _assign_reason_code(gu, cm, None, False, 5)
        assert code == "deficit:field=schedule"

    def test_gini_category_imbalance(self):
        """Gini > 0.45 + 소수 카테고리 → gini:category_imbalance."""
        gu = _make_gu("GU-1", "d:culture:temple", "hours")
        cm = _make_coverage_map(
            {"culture": {"ku_count": 2, "deficit_score": 0.3, "field_coverage": {"hours": 2}}},
            gini=0.55,
        )
        code = _assign_reason_code(gu, cm, None, False, 5)
        assert code == "gini:category_imbalance"

    def test_gini_field_imbalance(self):
        """field Gini > 0.45 → gini:field_imbalance."""
        gu = _make_gu("GU-1", "d:cat:a", "price")
        cm = _make_coverage_map(
            {"cat": {"ku_count": 10, "deficit_score": 0.0, "field_coverage": {"price": 10}}},
            gini=0.3,
            field_gini=0.55,
        )
        code = _assign_reason_code(gu, cm, None, False, 5)
        assert code == "gini:field_imbalance"

    def test_plateau_novelty(self):
        """novelty < 0.1 × 5c → plateau:novelty<0.1."""
        gu = _make_gu("GU-1", "d:cat:a", "price")
        cm = _make_coverage_map(
            {"cat": {"ku_count": 10, "deficit_score": 0.0, "field_coverage": {"price": 10}}},
        )
        history = [0.05, 0.03, 0.08, 0.02, 0.01]
        code = _assign_reason_code(gu, cm, history, False, 5)
        assert code.startswith("plateau:novelty<0.1")

    def test_remodel_pending(self):
        """remodel pending → remodel:pending."""
        gu = _make_gu("GU-1", "d:cat:a", "price")
        cm = _make_coverage_map(
            {"cat": {"ku_count": 10, "deficit_score": 0.0, "field_coverage": {"price": 10}}},
        )
        code = _assign_reason_code(gu, cm, [0.5, 0.6, 0.7], True, 5)
        assert code == "remodel:pending"

    def test_audit_trigger(self):
        """audit trigger → audit:merge_pending."""
        gu = _make_gu("GU-1", "d:cat:a", "price", trigger="audit_coverage_gap")
        code = _assign_reason_code(gu, None, None, False, 5)
        assert code == "audit:merge_pending"

    def test_fallback_seed(self):
        """매칭 조건 없으면 seed:initial."""
        gu = _make_gu("GU-1", "d:cat:a", "price")
        code = _assign_reason_code(gu, None, None, False, 5)
        assert code == "seed:initial"


class TestBoostDeficitCategories:
    """_boost_deficit_categories Gini 우선순위 테스트."""

    def test_no_boost_when_gini_low(self):
        """Gini ≤ 0.45 → 순서 변경 없음."""
        gus = [
            _make_gu("GU-1", "d:transport:jr"),
            _make_gu("GU-2", "d:food:ramen"),
        ]
        cm = _make_coverage_map({
            "transport": {"ku_count": 5, "deficit_score": 0.3},
            "food": {"ku_count": 5, "deficit_score": 0.3},
        }, gini=0.1)
        result = _boost_deficit_categories(gus, cm)
        assert [g["gu_id"] for g in result] == ["GU-1", "GU-2"]

    def test_boost_when_gini_high(self):
        """Gini > 0.45 → deficit 높은 카테고리 GU 앞으로."""
        gus = [
            _make_gu("GU-1", "d:transport:jr"),    # deficit 0.2
            _make_gu("GU-2", "d:food:ramen"),       # deficit 0.9
        ]
        cm = _make_coverage_map({
            "transport": {"ku_count": 8, "deficit_score": 0.2},
            "food": {"ku_count": 1, "deficit_score": 0.9},
        }, gini=0.6)
        result = _boost_deficit_categories(gus, cm)
        assert result[0]["gu_id"] == "GU-2"  # food 먼저


class TestPlanNodeReasonCode:
    """plan_node 에서 reason_code 부여 통합 테스트."""

    def test_all_targets_have_reason_code(self):
        """모든 target 에 reason_code 부여."""
        state = {
            "gap_map": [
                _make_gu("GU-1", "d:cat:a", "price"),
                _make_gu("GU-2", "d:cat:b", "name"),
                _make_gu("GU-3", "d:food:c", "taste"),
            ],
            "current_mode": {"mode": "normal", "explore_budget": 0, "exploit_budget": 3},
            "domain_skeleton": {
                "domain": "d",
                "categories": [{"slug": "cat"}, {"slug": "food"}],
                "axes": [],
            },
            "knowledge_units": [],
            "coverage_map": None,
            "novelty_history": [],
            "current_cycle": 3,
            "remodel_report": None,
        }
        result = plan_node(state)
        plan = result["current_plan"]
        rc = plan.get("reason_codes", {})

        # 모든 target 에 reason_code 존재
        for gu_id in plan["target_gaps"]:
            assert gu_id in rc, f"{gu_id} has no reason_code"
            assert rc[gu_id], f"{gu_id} has empty reason_code"

    def test_remodel_pending_note(self):
        """remodel pending 시 note 추가."""
        state = {
            "gap_map": [_make_gu("GU-1", "d:cat:a", "price")],
            "current_mode": {"mode": "normal", "explore_budget": 0, "exploit_budget": 1},
            "domain_skeleton": {"domain": "d", "categories": [{"slug": "cat"}], "axes": []},
            "knowledge_units": [],
            "coverage_map": None,
            "novelty_history": [],
            "current_cycle": 3,
            "remodel_report": {"approval": {"status": "pending"}},
        }
        result = plan_node(state)
        plan = result["current_plan"]
        assert "remodel_pending_note" in plan


class TestCritiqueMachineRules:
    """P4-B2: critique machine_rules 테스트."""

    def test_machine_rules_in_critique(self):
        """critique 에 machine_rules 필드 존재."""
        from src.nodes.critique import critique_node
        state = {
            "knowledge_units": [
                {"ku_id": "KU-1", "status": "active", "entity_key": "d:cat:a",
                 "field": "price", "confidence": 0.9, "evidence_links": ["e1"],
                 "claim": "test", "validity": {}},
            ],
            "gap_map": [
                {"gu_id": "GU-1", "status": "open", "gap_type": "missing",
                 "target": {"entity_key": "d:cat:a", "field": "name"},
                 "expected_utility": "medium", "risk_level": "convenience"},
            ],
            "domain_skeleton": {
                "domain": "d",
                "categories": [{"slug": "cat"}],
                "axes": [],
                "fields": [],
            },
            "current_cycle": 3,
            "metrics": {},
            "coverage_map": {},
            "novelty_history": [],
        }
        result = critique_node(state)
        critique = result["current_critique"]
        assert "machine_rules" in critique
        assert isinstance(critique["machine_rules"], list)

    def test_gini_rule_generated(self):
        """Gini 높을 때 diversify rule 생성."""
        from src.nodes.critique import critique_node
        state = {
            "knowledge_units": [
                {"ku_id": "KU-1", "status": "active", "entity_key": "d:cat:a",
                 "field": "price", "confidence": 0.9, "evidence_links": ["e1"],
                 "claim": "test", "validity": {}},
            ],
            "gap_map": [],
            "domain_skeleton": {
                "domain": "d",
                "categories": [{"slug": "cat"}, {"slug": "food"}],
                "axes": [],
                "fields": [],
            },
            "current_cycle": 3,
            "metrics": {},
            "coverage_map": {
                "summary": {"category_gini": 0.6, "field_gini": 0.3},
            },
            "novelty_history": [],
        }
        result = critique_node(state)
        rules = result["current_critique"]["machine_rules"]
        gini_rules = [r for r in rules if "gini" in r.get("rule", "")]
        assert len(gini_rules) >= 1
