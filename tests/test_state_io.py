"""state_io 테스트 — load/save 라운드트립, 스냅샷."""

import json
from pathlib import Path

from src.utils.state_io import load_state, save_state, snapshot_state

BENCH = Path("bench/japan-travel")


def test_load_bench_state():
    """bench/japan-travel → EvolverState 로드."""
    state = load_state(BENCH)
    assert state["current_cycle"] == 14
    assert len(state["knowledge_units"]) == 90
    assert len(state["gap_map"]) == 96
    assert state["domain_skeleton"]["domain"] == "japan-travel"
    assert state["metrics"]["rates"]["evidence_rate"] == 1.0
    assert "credibility_priors" in state["policies"]
    # 초기화 필드
    assert state["current_plan"] is None
    assert state["jump_history"] == []


def test_save_and_reload(tmp_path):
    """save → load 라운드트립."""
    state = load_state(BENCH)
    save_state(state, tmp_path)

    reloaded = load_state(tmp_path)
    assert reloaded["current_cycle"] == state["current_cycle"]
    assert len(reloaded["knowledge_units"]) == len(state["knowledge_units"])
    assert len(reloaded["gap_map"]) == len(state["gap_map"])
    assert reloaded["domain_skeleton"] == state["domain_skeleton"]
    assert reloaded["policies"] == state["policies"]


def test_save_creates_directory(tmp_path):
    """존재하지 않는 디렉토리에 save 시 자동 생성."""
    target = tmp_path / "new-domain"
    state = load_state(BENCH)
    save_state(state, target)
    assert (target / "state" / "knowledge-units.json").exists()


def test_save_utf8(tmp_path):
    """한글 데이터가 UTF-8로 올바르게 저장."""
    state = load_state(BENCH)
    save_state(state, tmp_path)

    path = tmp_path / "state" / "knowledge-units.json"
    raw = path.read_text(encoding="utf-8")
    # 한글이 escape 없이 저장되어야 함
    assert "\\u" not in raw
    data = json.loads(raw)
    assert len(data) == 90


def test_snapshot(tmp_path):
    """스냅샷 생성 확인."""
    # tmp에 state 먼저 저장
    state = load_state(BENCH)
    save_state(state, tmp_path)

    snap_dir = snapshot_state(tmp_path, cycle=2)
    assert snap_dir.exists()
    assert (snap_dir / "knowledge-units.json").exists()
    assert (snap_dir / "gap-map.json").exists()
    assert (snap_dir / "domain-skeleton.json").exists()
    assert (snap_dir / "metrics.json").exists()
    assert (snap_dir / "policies.json").exists()


def test_snapshot_overwrite(tmp_path):
    """동일 Cycle 스냅샷 재실행 시 덮어쓰기."""
    state = load_state(BENCH)
    save_state(state, tmp_path)

    snap1 = snapshot_state(tmp_path, cycle=0)
    snap2 = snapshot_state(tmp_path, cycle=0)
    assert snap1 == snap2
    assert snap2.exists()


def test_load_missing_files(tmp_path):
    """state/ 파일이 없을 때 빈 기본값."""
    (tmp_path / "state").mkdir()
    state = load_state(tmp_path)
    assert state["knowledge_units"] == []
    assert state["gap_map"] == []
    assert state["metrics"] == {}
    assert state["current_cycle"] == 0
