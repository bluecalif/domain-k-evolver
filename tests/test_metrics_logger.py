"""Task 2.6 테스트: Metrics Logger."""

import json
from pathlib import Path

import pytest

from src.utils.metrics_logger import MetricsLogger


def _make_state(
    *,
    ku_active: int = 10,
    ku_disputed: int = 1,
    gu_open: int = 5,
    gu_resolved: int = 8,
    evidence_rate: float = 0.95,
    conflict_rate: float = 0.02,
    avg_confidence: float = 0.88,
    mode: str = "normal",
) -> dict:
    kus = [{"status": "active"}] * ku_active + [{"status": "disputed"}] * ku_disputed
    gus = [{"status": "open"}] * gu_open + [{"status": "resolved"}] * gu_resolved
    return {
        "knowledge_units": kus,
        "gap_map": gus,
        "metrics": {
            "rates": {
                "evidence_rate": evidence_rate,
                "multi_evidence_rate": 0.50,
                "conflict_rate": conflict_rate,
                "avg_confidence": avg_confidence,
                "gap_resolution_rate": 0.60,
                "staleness_risk": 0,
            },
        },
        "current_mode": {"mode": mode},
    }


class TestMetricsLogger:
    def test_log_entry(self):
        logger = MetricsLogger()
        state = _make_state()
        entry = logger.log(1, state)
        assert entry["cycle"] == 1
        assert entry["ku_active"] == 10
        assert entry["ku_disputed"] == 1
        assert entry["gu_open"] == 5
        assert entry["gu_resolved"] == 8
        assert entry["evidence_rate"] == 0.95
        assert entry["mode"] == "normal"

    def test_multiple_cycles(self):
        logger = MetricsLogger()
        logger.log(1, _make_state(ku_active=10))
        logger.log(2, _make_state(ku_active=15))
        logger.log(3, _make_state(ku_active=20))
        assert len(logger.entries) == 3
        assert logger.entries[2]["ku_active"] == 20

    def test_summary(self):
        logger = MetricsLogger()
        logger.log(1, _make_state(ku_active=10, gu_resolved=5))
        logger.log(2, _make_state(ku_active=15, gu_resolved=10, mode="jump"))
        logger.log(3, _make_state(ku_active=20, gu_resolved=15))
        summary = logger.summary()
        assert summary["total_cycles"] == 3
        assert summary["ku_growth"] == 10
        assert summary["gu_resolved_total"] == 15
        assert summary["jump_cycles"] == 1

    def test_summary_empty(self):
        logger = MetricsLogger()
        assert logger.summary() == {}

    def test_save_json(self, tmp_path):
        logger = MetricsLogger()
        logger.log(1, _make_state())
        out = tmp_path / "metrics" / "trajectory.json"
        logger.save_json(out)
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["cycle"] == 1

    def test_save_csv(self, tmp_path):
        logger = MetricsLogger()
        logger.log(1, _make_state())
        logger.log(2, _make_state(ku_active=15))
        out = tmp_path / "trajectory.csv"
        logger.save_csv(out)
        assert out.exists()
        lines = out.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3  # header + 2 rows
        assert "cycle" in lines[0]

    def test_save_csv_empty(self, tmp_path):
        logger = MetricsLogger()
        out = tmp_path / "empty.csv"
        logger.save_csv(out)
        assert not out.exists()

    def test_collect_failure_rate_in_entry(self):
        """P0-X5: collect_failure_rate 가 logger entry 에 기록."""
        logger = MetricsLogger()
        state = _make_state()
        state["collect_failure_rate"] = 0.25
        entry = logger.log(1, state)
        assert entry["collect_failure_rate"] == 0.25

    def test_collect_failure_rate_default_zero(self):
        """collect_failure_rate 없는 state → 0.0 기본값."""
        logger = MetricsLogger()
        state = _make_state()
        entry = logger.log(1, state)
        assert entry["collect_failure_rate"] == 0.0

    def test_m11_adj_gen_count_in_entry(self):
        """SI-P7 M11: adj_gen_count = state._diag_adjacent_gap_count."""
        logger = MetricsLogger()
        state = _make_state()
        state["_diag_adjacent_gap_count"] = 5
        entry = logger.log(1, state)
        assert entry["adj_gen_count"] == 5

    def test_m11_wildcard_gen_count_in_entry(self):
        """SI-P7 M11: wildcard_gen_count = state._diag_wildcard_gen_count."""
        logger = MetricsLogger()
        state = _make_state()
        state["_diag_wildcard_gen_count"] = 12
        entry = logger.log(1, state)
        assert entry["wildcard_gen_count"] == 12

    def test_m11_counts_default_zero_when_missing(self):
        """adj/wildcard count 없는 state → 0 기본값."""
        logger = MetricsLogger()
        entry = logger.log(1, _make_state())
        assert entry["adj_gen_count"] == 0
        assert entry["wildcard_gen_count"] == 0

    def test_m5b_cap_hit_count_in_entry(self):
        """SI-P7 M5b: cap_hit_count = state._diag_cap_hit_count."""
        logger = MetricsLogger()
        state = _make_state()
        state["_diag_cap_hit_count"] = 1
        entry = logger.log(1, state)
        assert entry["cap_hit_count"] == 1

    def test_m5b_cap_hit_default_zero(self):
        """_diag_cap_hit_count 없는 state → cap_hit_count 0."""
        logger = MetricsLogger()
        entry = logger.log(1, _make_state())
        assert entry["cap_hit_count"] == 0
