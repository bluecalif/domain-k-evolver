"""실제 trial artifact를 읽는 로더. stub/mock 절대 금지 (P5-X3)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_cycles(trial_root: Path) -> list[dict]:
    """bench/silver/{trial}/telemetry/cycles.jsonl → list of snapshots."""
    path = trial_root / "telemetry" / "cycles.jsonl"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    result = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning("cycles.jsonl 파싱 실패 (line 무시): %s", e)
    return result


def load_conflict_ledger(trial_root: Path) -> list[dict]:
    """state/conflict_ledger.json → list of ledger entries."""
    path = trial_root / "state" / "conflict_ledger.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("entries", [])


def load_remodel_report(trial_root: Path) -> dict | None:
    """state/phase_*/remodel_report.json 중 가장 최신 파일 반환."""
    state_dir = trial_root / "state"
    if not state_dir.exists():
        return None
    candidates = sorted(state_dir.glob("phase_*/remodel_report.json"), reverse=True)
    if not candidates:
        return None
    try:
        return json.loads(candidates[0].read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("remodel_report 로드 실패: %s", e)
        return None


def load_trajectory(trial_root: Path) -> list[dict]:
    """trajectory/trajectory.json → list of cycle records."""
    path = trial_root / "trajectory" / "trajectory.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("cycles", [])
