"""P5-C2: 100-cycle fixture — 모든 7개 view 10s 이내 응답."""

from __future__ import annotations

import json
import time
import tempfile
from pathlib import Path

import pytest

from src.obs.telemetry import emit_cycle
from src.obs.dashboard.app import create_app

try:
    from fastapi.testclient import TestClient
    _HAVE_FASTAPI = True
except ImportError:
    _HAVE_FASTAPI = False

pytestmark = pytest.mark.skipif(not _HAVE_FASTAPI, reason="fastapi not installed")


def _minimal_state(cycle: int) -> dict:
    return {
        "metrics": {"rates": {
            "evidence_rate": 0.97, "multi_evidence_rate": 0.61,
            "conflict_rate": 0.03, "avg_confidence": 0.85,
            "gap_resolution_rate": 0.88, "staleness_risk": 0,
        }},
        "collect_failure_rate": 0.04,
        "current_mode": {"mode": "normal"},
        "gap_map": [{"status": "open"}, {"status": "resolved"}],
        "novelty_history": [0.3],
        "external_novelty_history": [0.4],
        "probe_history": [],
        "pivot_history": [],
        "dispute_queue": [],
        "failures": [],
        "audit_history": [],
        "phase": "si-p5",
        "cycle_count": cycle,
        "remodel_report": None,
    }


@pytest.fixture(scope="module")
def trial_root_with_100_cycles(tmp_path_factory):
    root = tmp_path_factory.mktemp("trial100")
    (root / "trial-card.md").write_text("# 100c fixture", encoding="utf-8")
    (root / "state").mkdir()
    (root / "state" / "conflict_ledger.json").write_text(
        json.dumps([{"ledger_id": "L-001", "entity_key": "test:a:b", "field": "f", "status": "open", "ku_ids": [], "created_at": "2026-01-01"}]),
        encoding="utf-8",
    )
    for i in range(100):
        emit_cycle(_minimal_state(i + 1), root, cycle_elapsed_s=0.5)
    return root


VIEWS = ["/", "/timeline", "/coverage", "/sources", "/conflicts", "/hitl", "/remodel"]


@pytest.mark.parametrize("path", VIEWS)
def test_view_loads_under_10s(trial_root_with_100_cycles, path):
    """각 view가 100-cycle fixture 기준 10s 이내 응답."""
    app = create_app(trial_root=trial_root_with_100_cycles)
    client = TestClient(app)
    t0 = time.monotonic()
    resp = client.get(path)
    elapsed = time.monotonic() - t0
    assert resp.status_code == 200
    assert elapsed < 10.0, f"{path} 응답 {elapsed:.2f}s > 10s"
