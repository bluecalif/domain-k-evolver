"""Telemetry emitter — cycle 단위 snapshot을 cycles.jsonl에 atomic append."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.state import EvolverState

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = "v1"


def emit_cycle(
    state: "EvolverState",
    trial_root: Path,
    cycle_elapsed_s: float,
) -> None:
    """cycle 끝에서 호출. telemetry/cycles.jsonl에 snapshot 1행 append.

    실패 시 warning log만 남기고 계속 진행 (cycle을 블로킹하면 안 됨).
    """
    try:
        _emit(state, trial_root, cycle_elapsed_s)
    except Exception as exc:
        logger.warning("Telemetry emit 실패 (무시): %s", exc)


def _emit(state: "EvolverState", trial_root: Path, cycle_elapsed_s: float) -> None:
    telemetry_dir = trial_root / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)

    trial_card = trial_root / "trial-card.md"
    if not trial_card.exists():
        logger.warning("trial-card.md 없음: %s (telemetry emit 계속)", trial_root)

    snapshot = _build_snapshot(state, trial_root.name, cycle_elapsed_s)

    out_path = telemetry_dir / "cycles.jsonl"
    tmp_path = telemetry_dir / "cycles.jsonl.tmp"

    existing = out_path.read_bytes() if out_path.exists() else b""
    line = (json.dumps(snapshot, ensure_ascii=False) + "\n").encode("utf-8")

    tmp_path.write_bytes(existing + line)
    os.replace(tmp_path, out_path)


def _build_snapshot(
    state: "EvolverState",
    trial_id: str,
    cycle_elapsed_s: float,
) -> dict:
    metrics_entry = _latest_metrics_entry(state)
    audit_history = state.get("audit_history") or []
    latest_audit = audit_history[-1] if audit_history else {}
    findings = latest_audit.get("findings", [])

    gap_map = state.get("gap_map") or []
    novelty_history = state.get("novelty_history") or []
    ext_novelty_history = state.get("external_novelty_history") or []
    probe_history = state.get("probe_history") or []
    pivot_history = state.get("pivot_history") or []
    dispute_queue = state.get("dispute_queue") or []
    failures = state.get("failures") or []

    plateau = state.get("plateau_reason") is not None

    return {
        "trial_id": trial_id,
        "phase": state.get("phase", "unknown"),
        "cycle": state.get("cycle_count", 0),
        "mode": (state.get("current_mode") or {}).get("mode", "normal"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "evidence_rate":        metrics_entry.get("evidence_rate", 0.0),
            "multi_evidence_rate":  metrics_entry.get("multi_evidence_rate", 0.0),
            "conflict_rate":        metrics_entry.get("conflict_rate", 0.0),
            "avg_confidence":       metrics_entry.get("avg_confidence", 0.0),
            "gap_resolution_rate":  metrics_entry.get("gap_resolution_rate", 0.0),
            "staleness_risk":       int(metrics_entry.get("staleness_risk", 0)),
            "collect_failure_rate": metrics_entry.get("collect_failure_rate", 0.0),
            "novelty":              novelty_history[-1] if novelty_history else 0.0,
            "external_novelty":     ext_novelty_history[-1] if ext_novelty_history else 0.0,
            "wall_clock_s":         round(cycle_elapsed_s, 2),
            "llm_calls":            int(metrics_entry.get("llm_calls", 0)),
            "llm_tokens":           int(metrics_entry.get("llm_tokens", 0)),
            "search_calls":         int(metrics_entry.get("search_calls", 0)),
            "fetch_calls":          int(metrics_entry.get("fetch_calls", 0)),
        },
        "gaps": {
            "open":                sum(1 for g in gap_map if g.get("status") == "open"),
            "resolved":            sum(1 for g in gap_map if g.get("status") == "resolved"),
            "plateau":             plateau,
            "probe_history_count": len(probe_history),
            "pivot_history_count": len(pivot_history),
        },
        "failures": [str(f) for f in failures],
        "audit_summary": {
            "has_critical":     any(f.get("severity") == "critical" for f in findings),
            "findings_count":   len(findings),
            "last_audit_cycle": latest_audit.get("cycle", -1) if latest_audit else -1,
        },
        "hitl_queue": {
            "seed":      int(state.get("hitl_seed_count", 0)),
            "remodel":   int(1 if state.get("remodel_report") else 0),
            "exception": int(state.get("hitl_exception_count", 0)),
        },
        "dispute_queue_size": len(dispute_queue),
    }


def _latest_metrics_entry(state: "EvolverState") -> dict:
    """state["metrics"]["rates"]에서 최신 metric 값을 반환.

    llm_calls/search_calls/fetch_calls는 orchestrator가 metrics_logger.log()에
    직접 전달하는 값으로 state에 저장되지 않으므로 0으로 처리 (현행 구현 기준).
    """
    rates = (state.get("metrics") or {}).get("rates", {})
    return {
        "evidence_rate":        rates.get("evidence_rate", 0.0),
        "multi_evidence_rate":  rates.get("multi_evidence_rate", 0.0),
        "conflict_rate":        rates.get("conflict_rate", 0.0),
        "avg_confidence":       rates.get("avg_confidence", 0.0),
        "gap_resolution_rate":  rates.get("gap_resolution_rate", 0.0),
        "staleness_risk":       rates.get("staleness_risk", 0),
        "collect_failure_rate": state.get("collect_failure_rate", 0.0),
        "llm_calls":            0,
        "llm_tokens":           0,
        "search_calls":         0,
        "fetch_calls":          0,
    }
