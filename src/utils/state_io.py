"""JSON 파일 I/O 유틸리티 — State ↔ 5개 JSON 파일 변환.

bench/{domain}/state/ 디렉토리의 5개 JSON 파일을 EvolverState로 로드/저장.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.state import EvolverState

# State JSON 파일 ↔ EvolverState 필드 매핑
_FILE_MAP: dict[str, str] = {
    "knowledge-units.json": "knowledge_units",
    "gap-map.json": "gap_map",
    "domain-skeleton.json": "domain_skeleton",
    "metrics.json": "metrics",
    "policies.json": "policies",
}


def _read_json(path: Path) -> dict | list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_state(domain_path: str | Path) -> EvolverState:
    """5개 JSON 파일 → EvolverState 로드.

    Args:
        domain_path: bench/{domain} 디렉토리 경로 (state/ 하위에 JSON 존재).

    Returns:
        EvolverState dict.
    """
    state_dir = Path(domain_path) / "state"
    # snapshot 디렉토리는 state/ 하위 없이 직접 JSON 포함
    if not state_dir.exists():
        state_dir = Path(domain_path)
    data: dict = {}

    for filename, field in _FILE_MAP.items():
        path = state_dir / filename
        if path.exists():
            data[field] = _read_json(path)
        else:
            data[field] = [] if field in ("knowledge_units", "gap_map") else {}

    cycle = data.get("metrics", {}).get("cycle", 0)

    state: EvolverState = {
        **data,
        "current_cycle": cycle,
        "current_plan": None,
        "current_claims": None,
        "current_critique": None,
        "current_mode": None,
        "axis_coverage": None,
        "jump_history": [],
        "hitl_pending": None,
    }
    return state


def save_state(state: EvolverState, domain_path: str | Path) -> None:
    """EvolverState → 5개 JSON 파일 저장.

    Args:
        state: 저장할 EvolverState.
        domain_path: bench/{domain} 디렉토리 경로.
    """
    state_dir = Path(domain_path) / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    for filename, field in _FILE_MAP.items():
        data = state.get(field)
        if data is not None:
            _write_json(state_dir / filename, data)


def snapshot_state(domain_path: str | Path, cycle: int) -> Path:
    """state/ → state-snapshots/cycle-{n}-snapshot/ 스냅샷 복사.

    Args:
        domain_path: bench/{domain} 디렉토리 경로.
        cycle: 스냅샷 대상 Cycle 번호.

    Returns:
        생성된 스냅샷 디렉토리 경로.
    """
    domain = Path(domain_path)
    state_dir = domain / "state"
    snapshot_dir = domain / "state-snapshots" / f"cycle-{cycle}-snapshot"

    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)

    snapshot_dir.mkdir(parents=True, exist_ok=True)

    for filename in _FILE_MAP:
        src = state_dir / filename
        if src.exists():
            shutil.copy2(src, snapshot_dir / filename)

    return snapshot_dir
