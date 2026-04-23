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
    *,
    cycle_ctx: dict | None = None,
) -> None:
    """cycle 끝에서 호출. telemetry/cycles.jsonl에 snapshot 1행 append.

    실패 시 warning log만 남기고 계속 진행 (cycle을 블로킹하면 안 됨).
    """
    try:
        _emit(state, trial_root, cycle_elapsed_s, cycle_ctx=cycle_ctx)
    except Exception as exc:
        logger.warning("Telemetry emit 실패 (무시): %s", exc)


def _emit(
    state: "EvolverState",
    trial_root: Path,
    cycle_elapsed_s: float,
    *,
    cycle_ctx: dict | None = None,
) -> None:
    telemetry_dir = trial_root / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)

    trial_card = trial_root / "trial-card.md"
    if not trial_card.exists():
        logger.warning("trial-card.md 없음: %s (telemetry emit 계속)", trial_root)

    snapshot = _build_snapshot(state, trial_root.name, cycle_elapsed_s, cycle_ctx=cycle_ctx)

    out_path = telemetry_dir / "cycles.jsonl"
    tmp_path = telemetry_dir / "cycles.jsonl.tmp"

    existing = out_path.read_bytes() if out_path.exists() else b""
    line = (json.dumps(snapshot, ensure_ascii=False) + "\n").encode("utf-8")

    tmp_path.write_bytes(existing + line)
    os.replace(tmp_path, out_path)

    if cycle_ctx:
        emit_gu_trace(cycle_ctx, telemetry_dir)


def _build_snapshot(
    state: "EvolverState",
    trial_id: str,
    cycle_elapsed_s: float,
    *,
    cycle_ctx: dict | None = None,
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
        "deferred_targets": len(state.get("deferred_targets") or []),
        "defer_reason": state.get("defer_reason") or {},
        "cycle_trace": _build_cycle_trace(cycle_ctx) if cycle_ctx else None,
        "si_p7": _build_si_p7_subdict(state),
    }


def _build_si_p7_subdict(state: "EvolverState") -> dict:
    """SI-P7 V2 계측 — cycle snapshot 용 si_p7 sub-dict.

    관찰 전용. state 를 변형하지 않음.
    Cycle 기준은 current_cycle (integrate 가 event stamp 에 사용하는 필드와 동일).
    """
    cycle_num = int(state.get("current_cycle", state.get("cycle_count", 0)))
    return {
        "aggressive_mode_remaining": int(state.get("aggressive_mode_remaining", 0)),
        "integration_result_cycle": _extract_integration_cycle(state, cycle_num),
        "condition_split_count_cycle": _count_events_in_cycle(
            state.get("condition_split_events"), cycle_num
        ),
        "suppress_count_cycle": _count_events_in_cycle(
            state.get("suppress_event_log"), cycle_num
        ),
        "query_rewrite_count_cycle": _count_events_in_cycle(
            state.get("query_rewrite_rx_log"), cycle_num
        ),
        "recent_conflict_fields_count": len(state.get("recent_conflict_fields") or []),
        "adjacency_yield_top3": _top_n_rules(state.get("adjacency_yield"), n=3),
        "coverage_deficit_top3": _top_n_deficit(state.get("coverage_map"), n=3),
    }


def _extract_integration_cycle(state: "EvolverState", cycle_num: int) -> dict:
    """integration_result_dist.cycle_history 중 해당 cycle 엔트리 반환 (없으면 {})."""
    dist = state.get("integration_result_dist") or {}
    history = dist.get("cycle_history") or []
    for entry in history:
        if entry.get("cycle") == cycle_num:
            return dict(entry)
    return {}


def _count_events_in_cycle(events: list | None, cycle_num: int) -> int:
    """cycle-stamped event list 에서 해당 cycle 항목 수 카운트."""
    if not events:
        return 0
    return sum(1 for e in events if isinstance(e, dict) and e.get("cycle") == cycle_num)


def _top_n_rules(adjacency_yield: dict | None, n: int = 3) -> list[dict]:
    """adjacency_yield 에서 최근 누적 resolved 가 큰 rule_id 상위 N개.

    구조: {rule_id: [{"cycle": int, "attempted": int, "resolved": int}, ...]}
    """
    if not adjacency_yield:
        return []
    summaries: list[dict] = []
    for rule_id, records in adjacency_yield.items():
        if not isinstance(records, list):
            continue
        total_attempted = sum(int(r.get("attempted", 0)) for r in records)
        total_resolved = sum(int(r.get("resolved", 0)) for r in records)
        summaries.append({
            "rule_id": rule_id,
            "attempted": total_attempted,
            "resolved": total_resolved,
            "yield": round(total_resolved / total_attempted, 3) if total_attempted else 0.0,
        })
    summaries.sort(key=lambda s: (s["resolved"], s["attempted"]), reverse=True)
    return summaries[:n]


def _top_n_deficit(coverage_map: dict | None, n: int = 3) -> list[dict]:
    """coverage_map 에서 deficit_score 가 큰 category 상위 N개.

    구조: {cat: {"deficit_score": float, ...}} 또는 {cat: float}
    """
    if not coverage_map:
        return []
    entries: list[dict] = []
    for cat, value in coverage_map.items():
        if isinstance(value, dict):
            score = float(value.get("deficit_score", 0.0))
        elif isinstance(value, (int, float)):
            score = float(value)
        else:
            continue
        entries.append({"category": cat, "deficit_score": round(score, 3)})
    entries.sort(key=lambda e: e["deficit_score"], reverse=True)
    return entries[:n]


def _build_cycle_trace(cycle_ctx: dict) -> dict:
    """cycle_ctx → cycle_trace 요약 dict."""
    targets = cycle_ctx.get("targets_selected", [])
    search_yield = cycle_ctx.get("search_yield_by_gu", {})
    resolved = cycle_ctx.get("resolved_gus", [])

    wildcard_targets = [t for t in targets if t.get("is_wildcard")]
    concrete_targets = [t for t in targets if not t.get("is_wildcard")]

    wildcard_yield = sum(search_yield.get(t["gu_id"], 0) for t in wildcard_targets)
    concrete_yield = sum(search_yield.get(t["gu_id"], 0) for t in concrete_targets)

    return {
        "target_count": len(targets),
        "wildcard_count": len(wildcard_targets),
        "concrete_count": len(concrete_targets),
        "wildcard_search_yield": wildcard_yield,
        "concrete_search_yield": concrete_yield,
        "resolved_count": len(resolved),
        "resolved_gus": resolved,
        "adjacent_gap_generated": cycle_ctx.get("adjacent_gap_generated", 0),
    }


def emit_gu_trace(cycle_ctx: dict, telemetry_dir: Path) -> None:
    """GU별 진단 행을 telemetry/gu_trace.jsonl에 append."""
    try:
        targets = cycle_ctx.get("targets_selected", [])
        if not targets:
            return

        search_yield = cycle_ctx.get("search_yield_by_gu", {})
        queries = cycle_ctx.get("queries_by_gu", {})
        resolved_set = set(cycle_ctx.get("resolved_gus", []))
        cycle_num = cycle_ctx.get("cycle", 0)

        lines: list[bytes] = []
        for t in targets:
            gu_id = t["gu_id"]
            row = {
                "cycle": cycle_num,
                "gu_id": gu_id,
                "entity_key": t.get("entity_key", ""),
                "field": t.get("field", ""),
                "is_wildcard": t.get("is_wildcard", False),
                "query_count": len(queries.get(gu_id, [])),
                "search_yield": search_yield.get(gu_id, 0),
                "resolved": gu_id in resolved_set,
            }
            lines.append((json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8"))

        out_path = telemetry_dir / "gu_trace.jsonl"
        existing = out_path.read_bytes() if out_path.exists() else b""
        tmp_path = telemetry_dir / "gu_trace.jsonl.tmp"
        tmp_path.write_bytes(existing + b"".join(lines))
        os.replace(tmp_path, out_path)
    except Exception as exc:
        logger.warning("GU trace emit 실패 (무시): %s", exc)


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
