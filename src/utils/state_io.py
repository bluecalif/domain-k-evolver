"""JSON 파일 I/O 유틸리티 — State ↔ 5개 JSON 파일 변환.

bench/{domain}/state/ 디렉토리의 5개 JSON 파일을 EvolverState로 로드/저장.
Silver 세대: --bench-root 격리 + legacy bench 쓰기 금지.
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from src.state import EvolverState

logger = logging.getLogger(__name__)

# Legacy bench 경로 — read-only (Bronze 보호)
_LEGACY_BENCH_DIRS = {"japan-travel"}


def _check_write_guard(domain_path: Path) -> None:
    """Legacy bench 디렉토리 쓰기 금지 가드.

    bench/japan-travel/ 에 직접 쓰기를 시도하면 에러 발생.
    bench/japan-travel-auto/, bench/silver/japan-travel/ 등은 허용.
    """
    resolved = domain_path.resolve()
    # bench/{legacy_name} 패턴만 차단 (bench/{legacy_name}-auto 등은 허용)
    if resolved.parent.name == "bench" and resolved.name in _LEGACY_BENCH_DIRS:
        raise PermissionError(
            f"Legacy bench 쓰기 금지: {domain_path} (read-only). "
            f"Silver trial 은 bench/silver/ 하위에, "
            f"auto 결과는 {resolved.name}-auto/ 에 저장하세요."
        )

# State JSON 파일 ↔ EvolverState 필드 매핑
_FILE_MAP: dict[str, str] = {
    "knowledge-units.json": "knowledge_units",
    "gap-map.json": "gap_map",
    "domain-skeleton.json": "domain_skeleton",
    "metrics.json": "metrics",
    "policies.json": "policies",
}

# Silver P1-B3: 추가 state 파일 (파일 부재 시 빈 배열, migration-safe)
_OPTIONAL_LIST_FILES: dict[str, str] = {
    "conflict-ledger.json": "conflict_ledger",
}

# SI-P4 Stage E: external anchor state (하나의 파일에 history + 누적 키 병합)
_EXTERNAL_ANCHOR_FILE = "external-anchor.json"


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

    Raises:
        StateCorruptError: JSON 파싱 실패 시 (.bak 복구 시도 후에도 실패).
    """
    state_dir = Path(domain_path) / "state"
    # snapshot 디렉토리는 state/ 하위 없이 직접 JSON 포함
    if not state_dir.exists():
        state_dir = Path(domain_path)
    data: dict = {}

    for filename, field in _FILE_MAP.items():
        path = state_dir / filename
        data[field] = _load_json_with_recovery(path, field)

    # Silver P1-B3: optional list 파일 로드 (부재 시 빈 배열)
    for filename, field in _OPTIONAL_LIST_FILES.items():
        path = state_dir / filename
        if path.exists():
            try:
                data[field] = _read_json(path)
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.warning("Optional file 파싱 실패, 빈 배열 사용: %s", path)
                data[field] = []
        else:
            data[field] = []

    # 필수 필드 검증
    _validate_required_fields(data)

    cycle = data.get("metrics", {}).get("cycle", 0)

    # SI-P4 Stage E: external-anchor.json 로드 (부재 시 빈 값)
    ext_path = state_dir / _EXTERNAL_ANCHOR_FILE
    ext_history: list[float] = []
    ext_keys: list[str] = []
    if ext_path.exists():
        try:
            ext_data = _read_json(ext_path)
            if isinstance(ext_data, dict):
                ext_history = list(ext_data.get("novelty_history") or [])
                ext_keys = list(ext_data.get("observation_keys") or [])
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("external-anchor 파싱 실패, 빈 값 사용: %s", ext_path)

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
        "conflict_ledger": data.get("conflict_ledger", []),
        "phase_number": 0,
        "phase_history": [],
        "remodel_report": None,
        "coverage_map": {},
        "novelty_history": [],
        "external_novelty_history": ext_history,
        "external_observation_keys": ext_keys,
        "deferred_targets": [],
        "defer_reason": {},
    }
    return state


class StateCorruptError(Exception):
    """State JSON 파일 복구 불가능."""


def _load_json_with_recovery(path: Path, field: str) -> dict | list:
    """JSON 로드 — 실패 시 .bak 복구 시도."""
    default = [] if field in ("knowledge_units", "gap_map") else {}

    if not path.exists():
        return default

    # 1차: 원본 파일 시도
    try:
        return _read_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.error("JSON 파싱 실패: %s — %s", path, exc)

    # 2차: .bak 복구 시도
    bak_path = path.with_suffix(path.suffix + ".bak")
    if bak_path.exists():
        try:
            data = _read_json(bak_path)
            logger.warning("Backup 에서 복구: %s → %s", bak_path, path)
            # 복구된 데이터로 원본 덮어쓰기
            _write_json(path, data)
            return data
        except (json.JSONDecodeError, UnicodeDecodeError) as exc2:
            logger.error("Backup 복구도 실패: %s — %s", bak_path, exc2)

    raise StateCorruptError(
        f"State 파일 복구 불가: {path} (원본 + .bak 모두 실패)"
    )


def _validate_required_fields(data: dict) -> None:
    """State 필수 필드 존재 검증."""
    for field in ("knowledge_units", "gap_map", "domain_skeleton"):
        if field not in data:
            raise StateCorruptError(f"필수 필드 누락: {field}")


def save_state(state: EvolverState, domain_path: str | Path) -> None:
    """EvolverState → 5개 JSON 파일 저장.

    Args:
        state: 저장할 EvolverState.
        domain_path: bench/{domain} 또는 bench/silver/{domain}/{trial_id} 경로.

    Raises:
        PermissionError: legacy bench 디렉토리에 쓰기 시도 시.
    """
    _check_write_guard(Path(domain_path))
    state_dir = Path(domain_path) / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    for filename, field in _FILE_MAP.items():
        data = state.get(field)
        if data is not None:
            target = state_dir / filename
            # .bak rotation — 기존 파일이 있으면 백업
            if target.exists():
                bak_path = target.with_suffix(target.suffix + ".bak")
                shutil.copy2(target, bak_path)
            _write_json(target, data)

    # Silver P1-B3: optional list 파일 저장
    for filename, field in _OPTIONAL_LIST_FILES.items():
        data = state.get(field)
        if data:  # 빈 배열이 아닌 경우만 저장
            target = state_dir / filename
            if target.exists():
                bak_path = target.with_suffix(target.suffix + ".bak")
                shutil.copy2(target, bak_path)
            _write_json(target, data)

    # SI-P4 Stage E: external-anchor.json 저장 (history 또는 keys 가 있을 때만)
    ext_history = state.get("external_novelty_history") or []
    ext_keys = state.get("external_observation_keys") or []
    if ext_history or ext_keys:
        target = state_dir / _EXTERNAL_ANCHOR_FILE
        if target.exists():
            shutil.copy2(target, target.with_suffix(target.suffix + ".bak"))
        _write_json(target, {
            "novelty_history": list(ext_history),
            "observation_keys": list(ext_keys),
        })


def snapshot_state(domain_path: str | Path, cycle: int) -> Path:
    """state/ → state-snapshots/cycle-{n}-snapshot/ 스냅샷 복사.

    Args:
        domain_path: bench/{domain} 또는 bench/silver/{domain}/{trial_id} 경로.
        cycle: 스냅샷 대상 Cycle 번호.

    Returns:
        생성된 스냅샷 디렉토리 경로.

    Raises:
        PermissionError: legacy bench 디렉토리에 쓰기 시도 시.
    """
    _check_write_guard(Path(domain_path))
    domain = Path(domain_path)
    state_dir = domain / "state"
    snapshot_dir = domain / "state-snapshots" / f"cycle-{cycle}-snapshot"

    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)

    snapshot_dir.mkdir(parents=True, exist_ok=True)

    for filename in list(_FILE_MAP) + list(_OPTIONAL_LIST_FILES) + [_EXTERNAL_ANCHOR_FILE]:
        src = state_dir / filename
        if src.exists():
            shutil.copy2(src, snapshot_dir / filename)

    return snapshot_dir


def snapshot_phase(domain_path: str | Path, phase_number: int) -> Path:
    """state/ → state/phase_{N}/ phase 스냅샷 복사 (P2-A4).

    phase bump 시 현재 state 전체를 phase 번호별 디렉토리로 보존한다.

    Args:
        domain_path: bench/{domain} 또는 bench/silver/{domain}/{trial_id} 경로.
        phase_number: 스냅샷 대상 phase 번호.

    Returns:
        생성된 phase 스냅샷 디렉토리 경로.

    Raises:
        PermissionError: legacy bench 디렉토리에 쓰기 시도 시.
    """
    _check_write_guard(Path(domain_path))
    domain = Path(domain_path)
    state_dir = domain / "state"
    phase_dir = domain / "state" / f"phase_{phase_number}"

    if phase_dir.exists():
        shutil.rmtree(phase_dir)

    phase_dir.mkdir(parents=True, exist_ok=True)

    for filename in list(_FILE_MAP) + list(_OPTIONAL_LIST_FILES) + [_EXTERNAL_ANCHOR_FILE]:
        src = state_dir / filename
        if src.exists():
            shutil.copy2(src, phase_dir / filename)

    logger.info("Phase snapshot 저장: phase_%d → %s", phase_number, phase_dir)
    return phase_dir
