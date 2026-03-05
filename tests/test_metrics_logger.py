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
