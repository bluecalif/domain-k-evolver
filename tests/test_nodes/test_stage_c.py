"""test_stage_c — Phase 4 Stage C: Strategic Self-Tuning 테스트.

Task 4.7: Explore/Exploit 비율 자동 조정 (Audit bias)
Task 4.8: Jump Trigger 동적 관리 (T6:audit_axis_imbalance)
Task 4.9: Convergence 조건 고도화 (C7:audit_health)
"""

from __future__ import annotations

import pytest

from src.nodes.mode import (
    _compute_audit_bias,
    _compute_budget,
    _compute_trigger_t6_audit,
    mode_node,
)
from src.nodes.critique import _check_convergence


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_audit(findings: list[dict]) -> dict:
    return {"audit_cycle": 5, "window": [1, 5], "findings": findings}


def _coverage_gap_finding(cat: str = "transport") -> dict:
    return {
        "finding_id": f"F-COV-{cat[:4].upper()}",
        "category": "coverage_gap",
        "severity": "warning",
        "description": f"'{cat}' KU 부족",
        "evidence": {"category": cat, "ku_count": 1},
    }


def _yield_decline_finding() -> dict:
    return {
        "finding_id": "F-YIELD-01",
        "category": "yield_decline",
        "severity": "warning",
        "description": "KU yield 체감",
        "evidence": {},
    }


def _axis_imbalance_finding() -> dict:
    return {
        "finding_id": "F-COV-01",
        "category": "axis_imbalance",
        "severity": "warning",
        "description": "카테고리 균등도 부족",
        "evidence": {"uniformity": 0.5},
    }


def _critical_finding() -> dict:
    return {
        "finding_id": "F-COV-ACCOM",
        "category": "coverage_gap",
        "severity": "critical",
        "description": "카테고리 'accommodation' KU 0개",
        "evidence": {"category": "accommodation", "ku_count": 0},
    }


# ---------------------------------------------------------------------------
# Task 4.7: _compute_audit_bias
# ---------------------------------------------------------------------------

class TestComputeAuditBias:
    def test_no_audit_history(self) -> None:
        assert _compute_audit_bias([]) == 0.0

    def test_no_findings(self) -> None:
        audit = _make_audit([])
        assert _compute_audit_bias([audit]) == 0.0

    def test_coverage_gap_increases_explore(self) -> None:
        audit = _make_audit([_coverage_gap_finding()])
        bias = _compute_audit_bias([audit])
        assert bias > 0  # explore bias
        assert bias == 0.05

    def test_multiple_coverage_gaps_capped(self) -> None:
        findings = [_coverage_gap_finding(c) for c in ["a", "b", "c", "d"]]
        audit = _make_audit(findings)
        bias = _compute_audit_bias([audit])
        assert bias == 0.15  # max cap

    def test_yield_decline_increases_exploit(self) -> None:
        audit = _make_audit([_yield_decline_finding()])
        bias = _compute_audit_bias([audit])
        assert bias < 0  # exploit bias
        assert bias == -0.10

    def test_mixed_findings_net_bias(self) -> None:
        audit = _make_audit([
            _coverage_gap_finding("a"),
            _coverage_gap_finding("b"),
            _yield_decline_finding(),
        ])
        bias = _compute_audit_bias([audit])
        # +0.10 (2 gaps) - 0.10 (1 yield) = 0.0
        assert bias == 0.0

    def test_uses_latest_audit_only(self) -> None:
        old = _make_audit([_yield_decline_finding()])
        new = _make_audit([_coverage_gap_finding()])
        bias = _compute_audit_bias([old, new])
        assert bias == 0.05  # latest only


# ---------------------------------------------------------------------------
# Task 4.7: _compute_budget with audit_bias
# ---------------------------------------------------------------------------

class TestBudgetWithBias:
    def test_normal_mode_ignores_bias(self) -> None:
        explore, exploit = _compute_budget(10, "normal", "mid", audit_bias=0.15)
        assert explore == 0
        assert exploit == 10

    def test_positive_bias_increases_explore(self) -> None:
        base_explore, _ = _compute_budget(10, "jump", "mid", audit_bias=0.0)
        biased_explore, _ = _compute_budget(10, "jump", "mid", audit_bias=0.15)
        assert biased_explore > base_explore

    def test_negative_bias_decreases_explore(self) -> None:
        base_explore, _ = _compute_budget(10, "jump", "mid", audit_bias=0.0)
        biased_explore, _ = _compute_budget(10, "jump", "mid", audit_bias=-0.10)
        assert biased_explore < base_explore

    def test_budget_sum_preserved(self) -> None:
        explore, exploit = _compute_budget(10, "jump", "early", audit_bias=0.1)
        assert explore + exploit == 10

    def test_guardrail_min(self) -> None:
        # converging = 0.4, bias = -0.3 → clamped to 0.2
        explore, exploit = _compute_budget(10, "jump", "converging", audit_bias=-0.30)
        assert explore >= 2  # 0.2 * 10 = 2

    def test_guardrail_max(self) -> None:
        # early = 0.6, bias = +0.3 → clamped to 0.8
        explore, exploit = _compute_budget(10, "jump", "early", audit_bias=0.30)
        assert explore <= 8  # 0.8 * 10 = 8

    def test_default_bias_zero(self) -> None:
        a = _compute_budget(10, "jump", "mid")
        b = _compute_budget(10, "jump", "mid", audit_bias=0.0)
        assert a == b


# ---------------------------------------------------------------------------
# Task 4.8: T6 Audit Axis Imbalance Trigger
# ---------------------------------------------------------------------------

class TestTriggerT6:
    def test_no_audit(self) -> None:
        assert _compute_trigger_t6_audit([]) is False

    def test_no_axis_imbalance(self) -> None:
        audit = _make_audit([_coverage_gap_finding()])
        assert _compute_trigger_t6_audit([audit]) is False

    def test_axis_imbalance_triggers(self) -> None:
        audit = _make_audit([_axis_imbalance_finding()])
        assert _compute_trigger_t6_audit([audit]) is True

    def test_uses_latest_audit(self) -> None:
        old = _make_audit([_axis_imbalance_finding()])
        new = _make_audit([])  # latest has no imbalance
        assert _compute_trigger_t6_audit([old, new]) is False


class TestModeNodeWithAudit:
    def _base_state(self) -> dict:
        return {
            "gap_map": [
                {"status": "open", "target": {"entity_key": "d:cat-a:x"},
                 "risk_level": "safety"},
            ] * 5,
            "domain_skeleton": {
                "axes": [
                    {"name": "category", "anchors": ["cat-a", "cat-b"],
                     "required": True},
                ],
                "categories": [{"slug": "cat-a"}, {"slug": "cat-b"}],
            },
            "knowledge_units": [],
            "current_cycle": 6,
            "jump_history": [],
            "audit_history": [],
        }

    def test_t6_triggers_jump(self) -> None:
        state = self._base_state()
        # Remove T1 trigger by covering both categories
        state["gap_map"] = [
            {"status": "open", "target": {"entity_key": "d:cat-a:x"},
             "risk_level": "convenience"},
            {"status": "open", "target": {"entity_key": "d:cat-b:y"},
             "risk_level": "convenience"},
        ]
        state["knowledge_units"] = [
            {"status": "active", "evidence_links": ["EU-1", "EU-2"],
             "confidence": 0.95},
        ]
        state["audit_history"] = [_make_audit([_axis_imbalance_finding()])]

        result = mode_node(state)
        assert result["current_mode"]["mode"] == "jump"
        assert "T6:audit_axis_imbalance" in result["current_mode"]["trigger_set"]

    def test_audit_bias_in_mode_decision(self) -> None:
        state = self._base_state()
        state["audit_history"] = [
            _make_audit([_coverage_gap_finding("a"), _coverage_gap_finding("b")]),
        ]
        result = mode_node(state)
        assert result["current_mode"].get("audit_bias", 0.0) > 0

    def test_no_audit_no_bias(self) -> None:
        state = self._base_state()
        result = mode_node(state)
        assert "audit_bias" not in result["current_mode"]


# ---------------------------------------------------------------------------
# Task 4.9: C7 Audit Health Convergence Condition
# ---------------------------------------------------------------------------

class TestConvergenceC7:
    def _converging_args(self, audit_history=None):
        """All C1~C6 pass 하는 기본 인자."""
        kus = [
            {"status": "active", "ku_id": f"KU-{i}",
             "evidence_links": ["EU-1", "EU-2"], "confidence": 0.9}
            for i in range(10)
        ]
        gap_map = [
            {"status": "resolved", "gap_type": "missing",
             "expected_utility": "high",
             "target": {"entity_key": "d:cat-a:x"}},
        ]
        skeleton = {"categories": [{"slug": "cat-a"}]}
        rates = {
            "conflict_rate": 0.0,
            "avg_confidence": 0.90,
        }
        return dict(
            kus=kus,
            gap_map=gap_map,
            skeleton=skeleton,
            cycle=10,
            metrics_rates=rates,
            net_gap_changes=[0, 0, 0],
            audit_history=audit_history,
        )

    def test_no_audit_c7_pass(self) -> None:
        result = _check_convergence(**self._converging_args())
        assert result["conditions"]["C7_audit_health"] is True
        assert result["converged"] is True

    def test_empty_audit_c7_pass(self) -> None:
        result = _check_convergence(**self._converging_args(audit_history=[]))
        assert result["conditions"]["C7_audit_health"] is True

    def test_audit_no_critical_c7_pass(self) -> None:
        audit = _make_audit([_coverage_gap_finding()])  # warning, not critical
        result = _check_convergence(**self._converging_args(
            audit_history=[audit],
        ))
        assert result["conditions"]["C7_audit_health"] is True
        assert result["converged"] is True

    def test_audit_critical_c7_fail(self) -> None:
        audit = _make_audit([_critical_finding()])
        result = _check_convergence(**self._converging_args(
            audit_history=[audit],
        ))
        assert result["conditions"]["C7_audit_health"] is False
        assert result["converged"] is False

    def test_old_critical_resolved_latest_clean(self) -> None:
        old = _make_audit([_critical_finding()])
        new = _make_audit([])  # resolved
        result = _check_convergence(**self._converging_args(
            audit_history=[old, new],
        ))
        assert result["conditions"]["C7_audit_health"] is True
        assert result["converged"] is True

    def test_c7_blocks_convergence_even_if_c1_c6_pass(self) -> None:
        audit = _make_audit([_critical_finding()])
        result = _check_convergence(**self._converging_args(
            audit_history=[audit],
        ))
        # C1~C6 all pass, but C7 blocks
        for key, val in result["conditions"].items():
            if key == "C7_audit_health":
                assert val is False
            else:
                assert val is True, f"{key} should be True"
