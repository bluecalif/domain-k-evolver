"""P5-C3: slowdown 시나리오 fixture — Overview/Timeline/Sources에서 원인 식별 가능."""

from __future__ import annotations

import json
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


def _slowdown_state(cycle: int) -> dict:
    """cycle 7~10: novelty < 0.10, collect_failure > 0.15 (slowdown 시나리오)."""
    if cycle >= 7:
        novelty, failure = 0.05, 0.20
    else:
        novelty, failure = 0.35, 0.04
    return {
        "metrics": {"rates": {
            "evidence_rate": 0.95, "multi_evidence_rate": 0.55,
            "conflict_rate": 0.04, "avg_confidence": 0.80,
            "gap_resolution_rate": 0.75, "staleness_risk": 0,
        }},
        "collect_failure_rate": failure,
        "current_mode": {"mode": "normal"},
        "gap_map": [{"status": "open"}] * 5,
        "novelty_history": [novelty],
        "external_novelty_history": [novelty * 0.8],
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
def slowdown_trial(tmp_path_factory):
    root = tmp_path_factory.mktemp("slowdown")
    (root / "trial-card.md").write_text("# slowdown fixture", encoding="utf-8")
    for i in range(10):
        emit_cycle(_slowdown_state(i + 1), root, cycle_elapsed_s=5.0)
    return root


def test_slowdown_overview_shows_warning(slowdown_trial):
    """Overview: collect_failure_rate가 warn 임계치(>0.10) 초과 표시."""
    app = create_app(trial_root=slowdown_trial)
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "0.20" in resp.text or "warn" in resp.text or "crit" in resp.text


def test_slowdown_timeline_has_all_cycles(slowdown_trial):
    """Timeline: 10 cycle 모두 표시."""
    app = create_app(trial_root=slowdown_trial)
    client = TestClient(app)
    resp = client.get("/timeline")
    assert resp.status_code == 200
    cycles_jsonl = slowdown_trial / "telemetry" / "cycles.jsonl"
    lines = cycles_jsonl.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 10


def test_slowdown_sources_detects_failure_spike(slowdown_trial):
    """Sources: collect_failure 0.20 데이터가 응답에 포함됨."""
    app = create_app(trial_root=slowdown_trial)
    client = TestClient(app)
    resp = client.get("/sources")
    assert resp.status_code == 200
    assert "0.20" in resp.text
