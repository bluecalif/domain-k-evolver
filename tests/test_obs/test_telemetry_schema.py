"""S10 blocking: telemetry.v1.schema.json 계약 검증 테스트."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import jsonschema
import pytest

from src.obs.telemetry import emit_cycle, _build_snapshot

SCHEMA_PATH = Path(__file__).parents[2] / "schemas" / "telemetry.v1.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _minimal_state(cycle: int = 1) -> dict:
    return {
        "metrics": {"rates": {
            "evidence_rate": 0.97,
            "multi_evidence_rate": 0.61,
            "conflict_rate": 0.03,
            "avg_confidence": 0.85,
            "gap_resolution_rate": 0.88,
            "staleness_risk": 0,
        }},
        "collect_failure_rate": 0.04,
        "current_mode": {"mode": "normal"},
        "gap_map": [
            {"status": "open"},
            {"status": "open"},
            {"status": "resolved"},
        ],
        "novelty_history": [0.31],
        "external_novelty_history": [0.44],
        "probe_history": [],
        "pivot_history": [],
        "dispute_queue": [],
        "failures": [],
        "audit_history": [],
        "phase": "si-p5",
        "cycle_count": cycle,
        "remodel_report": None,
    }


def test_positive_valid_snapshot(schema):
    """S10: 1 cycle emit 결과가 telemetry.v1 schema validate pass."""
    snap = _build_snapshot(_minimal_state(), trial_id="test-trial", cycle_elapsed_s=12.5)
    jsonschema.validate(instance=snap, schema=schema)


def test_negative_missing_trial_id(schema):
    """필수 필드 trial_id 누락 시 ValidationError."""
    snap = _build_snapshot(_minimal_state(), trial_id="test-trial", cycle_elapsed_s=1.0)
    del snap["trial_id"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=snap, schema=schema)


def test_negative_missing_cycle(schema):
    """필수 필드 cycle 누락 시 ValidationError."""
    snap = _build_snapshot(_minimal_state(), trial_id="test-trial", cycle_elapsed_s=1.0)
    del snap["cycle"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=snap, schema=schema)


def test_negative_missing_metrics(schema):
    """필수 필드 metrics 누락 시 ValidationError."""
    snap = _build_snapshot(_minimal_state(), trial_id="test-trial", cycle_elapsed_s=1.0)
    del snap["metrics"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=snap, schema=schema)


def test_negative_extra_field_rejected(schema):
    """additionalProperties: false — 미정의 필드 추가 시 ValidationError."""
    snap = _build_snapshot(_minimal_state(), trial_id="test-trial", cycle_elapsed_s=1.0)
    snap["unknown_field"] = "should_fail"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=snap, schema=schema)


def test_emit_cycle_writes_jsonl(schema):
    """emit_cycle이 cycles.jsonl을 생성하고 각 행이 schema validate pass."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trial_root = Path(tmpdir)
        (trial_root / "trial-card.md").write_text("# test", encoding="utf-8")

        for i in range(3):
            state = _minimal_state(cycle=i + 1)
            emit_cycle(state, trial_root, cycle_elapsed_s=float(i + 1))

        jsonl_path = trial_root / "telemetry" / "cycles.jsonl"
        assert jsonl_path.exists()
        lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3
        for line in lines:
            snap = json.loads(line)
            jsonschema.validate(instance=snap, schema=schema)


def test_100_cycle_fixture_all_valid(schema):
    """100-cycle fixture emit → 모든 행 schema validate pass."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trial_root = Path(tmpdir)
        (trial_root / "trial-card.md").write_text("# test", encoding="utf-8")

        for i in range(100):
            emit_cycle(_minimal_state(cycle=i + 1), trial_root, cycle_elapsed_s=10.0)

        lines = (trial_root / "telemetry" / "cycles.jsonl").read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 100
        for line in lines:
            jsonschema.validate(instance=json.loads(line), schema=schema)
