"""legacy trajectory.json → cycles 호환 어댑터 회귀 테스트.

P5 dashboard는 cycles.jsonl 만 읽었으나, 실제 trial artifact 12/13개는 P5 이전
trajectory.json 포맷이라 전부 빈 화면이 떴다. loader가 fallback 변환하도록 수정.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.obs.dashboard.loader import (
    load_cycles, load_conflict_ledger, derive_remodel_events,
)


def _write_trajectory(root: Path, records: list[dict]) -> None:
    (root / "trajectory").mkdir(parents=True, exist_ok=True)
    (root / "trajectory" / "trajectory.json").write_text(
        json.dumps(records), encoding="utf-8"
    )


def test_load_cycles_uses_trajectory_when_no_jsonl(tmp_path):
    _write_trajectory(tmp_path, [
        {
            "cycle": 1, "mode": "normal",
            "evidence_rate": 0.97, "multi_evidence_rate": 0.6, "conflict_rate": 0.03,
            "avg_confidence": 0.85, "gap_resolution_rate": 0.88, "staleness_risk": 0,
            "collect_failure_rate": 0.04,
            "llm_calls": 0, "llm_tokens": 0, "search_calls": 0, "fetch_calls": 0,
            "gu_open": 19, "gu_resolved": 2,
        },
    ])
    cycles = load_cycles(tmp_path)
    assert len(cycles) == 1
    c = cycles[0]
    assert c["cycle"] == 1
    assert c["mode"] == "normal"
    assert c["phase"] == "legacy"
    assert c["metrics"]["evidence_rate"] == 0.97
    assert c["metrics"]["novelty"] == 0  # trajectory.json엔 없음 → 0 fallback
    assert c["gaps"]["open"] == 19
    assert c["gaps"]["resolved"] == 2
    assert c["hitl_queue"] == {"seed": 0, "remodel": 0, "exception": 0}
    assert c["dispute_queue_size"] == 0
    assert c["failures"] == []


def test_load_cycles_prefers_jsonl_over_trajectory(tmp_path):
    """cycles.jsonl 이 있으면 trajectory.json 무시 (Silver 포맷 우선)."""
    (tmp_path / "telemetry").mkdir()
    silver = {
        "trial_id": "x", "phase": "si-p5", "cycle": 7, "mode": "jump",
        "metrics": {"evidence_rate": 0.99},
        "gaps": {"open": 1, "resolved": 99},
    }
    (tmp_path / "telemetry" / "cycles.jsonl").write_text(
        json.dumps(silver) + "\n", encoding="utf-8"
    )
    _write_trajectory(tmp_path, [{"cycle": 1, "gu_open": 0, "gu_resolved": 0}])
    cycles = load_cycles(tmp_path)
    assert len(cycles) == 1
    assert cycles[0]["cycle"] == 7
    assert cycles[0]["phase"] == "si-p5"


def test_load_cycles_empty_when_neither_exists(tmp_path):
    assert load_cycles(tmp_path) == []


def test_load_conflict_ledger_accepts_hyphen_filename(tmp_path):
    """P1-B1 schema 는 conflict-ledger.json (하이픈) 채택. 둘 다 시도해야 함."""
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "conflict-ledger.json").write_text(
        json.dumps([{"ledger_id": "L1", "status": "open"}]), encoding="utf-8"
    )
    ledger = load_conflict_ledger(tmp_path)
    assert len(ledger) == 1
    assert ledger[0]["ledger_id"] == "L1"


def test_load_conflict_ledger_accepts_underscore_filename(tmp_path):
    """과거 P5 dashboard 가 underscore 를 가정한 trial 도 호환."""
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "conflict_ledger.json").write_text(
        json.dumps([{"ledger_id": "L2", "status": "resolved"}]), encoding="utf-8"
    )
    ledger = load_conflict_ledger(tmp_path)
    assert len(ledger) == 1
    assert ledger[0]["ledger_id"] == "L2"


def test_derive_remodel_events_extracts_jump_cycles():
    """trajectory 의 mode='jump' 가 remodel event 로 추출됨."""
    cycles = [
        {"cycle": 1, "mode": "normal", "metrics": {"gap_resolution_rate": 0.30},
         "gaps": {"open": 50, "resolved": 10}, "hitl_queue": {"remodel": 0}},
        {"cycle": 2, "mode": "jump", "metrics": {"gap_resolution_rate": 0.45},
         "gaps": {"open": 40, "resolved": 25}, "hitl_queue": {"remodel": 0}},
        {"cycle": 3, "mode": "normal", "metrics": {"gap_resolution_rate": 0.50},
         "gaps": {"open": 38, "resolved": 30}, "hitl_queue": {"remodel": 1}},
    ]
    out = derive_remodel_events(cycles)
    assert out["total_events"] == 2
    assert out["events"][0]["cycle"] == 2
    assert out["events"][0]["mode"] == "jump"
    assert out["events"][0]["delta_gap_resolved"] == 15
    assert out["events"][1]["hitl_remodel"] is True


def test_derive_remodel_events_empty_when_no_jump():
    cycles = [
        {"cycle": 1, "mode": "normal", "metrics": {"gap_resolution_rate": 0.5},
         "gaps": {"open": 10, "resolved": 5}, "hitl_queue": {"remodel": 0}},
    ]
    out = derive_remodel_events(cycles)
    assert out["total_events"] == 0
    assert out["events"] == []
