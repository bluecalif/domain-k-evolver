"""MetricsGuard 테스트."""

from __future__ import annotations

from src.utils.metrics_guard import GUARD_THRESHOLDS, check_metrics_guard


def _make_state(evidence_rate: float = 1.0, conflict_rate: float = 0.0) -> dict:
    return {
        "metrics": {
            "rates": {
                "evidence_rate": evidence_rate,
                "conflict_rate": conflict_rate,
            }
        }
    }


class TestMetricsGuard:
    def test_healthy_no_halt(self):
        result = check_metrics_guard(_make_state(0.90, 0.05))
        assert not result.triggered
        assert result.warnings == []

    def test_conflict_rate_exceeds(self):
        result = check_metrics_guard(_make_state(0.90, 0.35))
        assert result.triggered
        assert len(result.warnings) == 1
        assert "conflict_rate" in result.warnings[0]

    def test_evidence_rate_below(self):
        result = check_metrics_guard(_make_state(0.40, 0.05))
        assert result.triggered
        assert len(result.warnings) == 1
        assert "evidence_rate" in result.warnings[0]

    def test_both_violations(self):
        result = check_metrics_guard(_make_state(0.30, 0.50))
        assert result.triggered
        assert len(result.warnings) == 2

    def test_boundary_conflict_rate_not_halt(self):
        """exactly at threshold should not halt (> not >=)."""
        result = check_metrics_guard(_make_state(0.90, 0.30))
        assert not result.triggered

    def test_boundary_evidence_rate_not_halt(self):
        """exactly at threshold should not halt (< not <=)."""
        result = check_metrics_guard(_make_state(0.50, 0.05))
        assert not result.triggered

    def test_empty_state(self):
        result = check_metrics_guard({})
        assert result.triggered
        assert len(result.warnings) == 1
        assert "evidence_rate" in result.warnings[0]

    def test_missing_rates(self):
        result = check_metrics_guard({"metrics": {}})
        assert result.triggered

    def test_thresholds_values(self):
        assert GUARD_THRESHOLDS["conflict_rate_max"] == 0.30
        assert GUARD_THRESHOLDS["evidence_rate_min"] == 0.50
