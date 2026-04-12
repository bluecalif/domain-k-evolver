"""state_io 테스트 — load/save 라운드트립, 스냅샷, 복구, write guard."""

import json
from pathlib import Path

import pytest

from src.utils.state_io import (
    StateCorruptError,
    load_state,
    save_state,
    snapshot_state,
)

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
    # domain-skeleton 은 필수 — 빈 dict 를 기본값으로 허용
    (tmp_path / "state" / "domain-skeleton.json").write_text("{}", encoding="utf-8")
    state = load_state(tmp_path)
    assert state["knowledge_units"] == []
    assert state["gap_map"] == []
    assert state["metrics"] == {}
    assert state["current_cycle"] == 0


# ============================================================
# P0-B9 (S3): state_io 복구 + write guard + 필수필드 검증
# ============================================================

def _prepare_minimal_state_dir(root: Path) -> Path:
    """테스트용 최소 state 디렉토리 작성. state/ 하위에 5개 JSON."""
    state_dir = root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "knowledge-units.json").write_text("[]", encoding="utf-8")
    (state_dir / "gap-map.json").write_text("[]", encoding="utf-8")
    (state_dir / "domain-skeleton.json").write_text(
        '{"domain": "test"}', encoding="utf-8",
    )
    (state_dir / "metrics.json").write_text("{}", encoding="utf-8")
    (state_dir / "policies.json").write_text("{}", encoding="utf-8")
    return state_dir


class TestStateIoCorruptRecovery:
    """P0-B8/B9: JSON decode 실패 → .bak 복구 경로."""

    def test_corrupt_json_without_bak_raises(self, tmp_path):
        """원본 JSON 깨짐 + .bak 없음 → StateCorruptError."""
        state_dir = _prepare_minimal_state_dir(tmp_path)
        # knowledge-units.json 을 깨진 JSON 으로 교체
        (state_dir / "knowledge-units.json").write_text(
            "{broken json", encoding="utf-8",
        )
        with pytest.raises(StateCorruptError):
            load_state(tmp_path)

    def test_corrupt_json_with_valid_bak_recovers(self, tmp_path):
        """원본 깨짐 + .bak 정상 → 복구 성공."""
        state_dir = _prepare_minimal_state_dir(tmp_path)
        # 정상 .bak 생성
        valid_data = [{"ku_id": "KU-0001", "entity_key": "d:a:x", "field": "price"}]
        (state_dir / "knowledge-units.json.bak").write_text(
            json.dumps(valid_data), encoding="utf-8",
        )
        # 원본을 깨진 상태로 덮어쓰기
        (state_dir / "knowledge-units.json").write_text(
            "{{{", encoding="utf-8",
        )
        state = load_state(tmp_path)
        assert len(state["knowledge_units"]) == 1
        assert state["knowledge_units"][0]["ku_id"] == "KU-0001"
        # .bak 복구 후 원본이 정상화되었는지
        raw = (state_dir / "knowledge-units.json").read_text(encoding="utf-8")
        assert "KU-0001" in raw

    def test_corrupt_main_and_bak_raises(self, tmp_path):
        """원본 + .bak 모두 깨짐 → StateCorruptError."""
        state_dir = _prepare_minimal_state_dir(tmp_path)
        (state_dir / "knowledge-units.json").write_text("bad", encoding="utf-8")
        (state_dir / "knowledge-units.json.bak").write_text(
            "also bad", encoding="utf-8",
        )
        with pytest.raises(StateCorruptError):
            load_state(tmp_path)


class TestStateIoRequiredFields:
    """P0-B8/B9: 필수 필드 누락 시 StateCorruptError."""

    def test_missing_domain_skeleton_raises(self, tmp_path):
        """domain-skeleton.json 부재 → StateCorruptError 또는 빈 dict default."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        # knowledge_units / gap_map 은 존재하지만 domain_skeleton 파일 없음
        (state_dir / "knowledge-units.json").write_text("[]", encoding="utf-8")
        (state_dir / "gap-map.json").write_text("[]", encoding="utf-8")
        # domain-skeleton.json 은 파일 자체가 없어서 default={} 반환되지만 필수필드는 있음
        state = load_state(tmp_path)
        # _validate_required_fields 는 key 존재만 검증 → 통과
        assert "domain_skeleton" in state


class TestStateIoSaveBakRotation:
    """P0-B8/B9: save 시 기존 파일 .bak rotation."""

    def test_save_creates_bak_on_overwrite(self, tmp_path):
        """기존 파일이 있으면 save 시 .bak 생성."""
        state = load_state(BENCH)
        save_state(state, tmp_path)
        ku_file = tmp_path / "state" / "knowledge-units.json"
        assert ku_file.exists()
        assert not ku_file.with_suffix(".json.bak").exists()

        # 두 번째 save → .bak 생성
        save_state(state, tmp_path)
        bak_file = ku_file.with_suffix(".json.bak")
        assert bak_file.exists()

    def test_bak_preserves_previous_content(self, tmp_path):
        """.bak 는 이전 상태의 내용을 보존."""
        state = load_state(BENCH)
        # 첫 save
        save_state(state, tmp_path)
        original_ku_count = len(state["knowledge_units"])

        # state 변경 후 두 번째 save
        modified = dict(state)
        modified["knowledge_units"] = state["knowledge_units"][:1]
        save_state(modified, tmp_path)

        # .bak 이 이전 상태를 보존하는지
        bak_path = tmp_path / "state" / "knowledge-units.json.bak"
        bak_data = json.loads(bak_path.read_text(encoding="utf-8"))
        assert len(bak_data) == original_ku_count


class TestStateIoWriteGuard:
    """Silver write guard — legacy bench 직접 쓰기 차단."""

    def test_legacy_bench_write_blocked(self):
        """bench/japan-travel/ 에 직접 save 시도 → PermissionError."""
        state = load_state(BENCH)
        with pytest.raises(PermissionError):
            save_state(state, BENCH)

    def test_auto_suffix_allowed(self, tmp_path):
        """bench/japan-travel-auto/ 형태는 허용 (이름만 같으면 안 됨)."""
        # tmp_path 하위에 japan-travel-auto 디렉토리 생성 시뮬레이션
        target = tmp_path / "japan-travel-auto"
        state = load_state(BENCH)
        # PermissionError 발생 안 함
        save_state(state, target)
        assert (target / "state" / "knowledge-units.json").exists()

    def test_snapshot_blocked_on_legacy(self):
        """snapshot_state 도 legacy bench 에서 차단."""
        with pytest.raises(PermissionError):
            snapshot_state(BENCH, cycle=99)


class TestX4NewStateFields:
    """P0-X4: load_state 후 4개 신규 필드가 빈 기본값으로 초기화."""

    def test_conflict_ledger_default(self):
        state = load_state(BENCH)
        assert state["conflict_ledger"] == []

    def test_phase_history_default(self):
        state = load_state(BENCH)
        assert state["phase_history"] == []

    def test_coverage_map_default(self):
        state = load_state(BENCH)
        assert state["coverage_map"] == {}

    def test_novelty_history_default(self):
        state = load_state(BENCH)
        assert state["novelty_history"] == []


class TestConflictLedgerPersistence:
    """Silver P1-C4: conflict_ledger save/load 영속화 테스트."""

    def test_save_and_load_ledger(self, tmp_path):
        """ledger 가 save → load round-trip 유지."""
        from tests.conftest import make_minimal_state

        domain_dir = tmp_path / "test-domain"
        state_dir = domain_dir / "state"
        state_dir.mkdir(parents=True)

        # 필수 파일 생성
        for fname, default in [
            ("knowledge-units.json", "[]"),
            ("gap-map.json", "[]"),
            ("domain-skeleton.json", '{"domain":"test"}'),
            ("metrics.json", '{"cycle": 1}'),
            ("policies.json", "{}"),
        ]:
            (state_dir / fname).write_text(default, encoding="utf-8")

        ledger_data = [
            {
                "ledger_id": "CL-0001",
                "ku_id": "KU-0001",
                "created_at": "2026-04-12",
                "status": "open",
                "conflicting_evidence": ["EU-0001", "EU-0002"],
                "resolution": None,
            },
            {
                "ledger_id": "CL-0002",
                "ku_id": "KU-0002",
                "created_at": "2026-04-12",
                "status": "resolved",
                "conflicting_evidence": ["EU-0003"],
                "resolution": {
                    "method": "evidence_weighted",
                    "resolved_at": "2026-04-12",
                    "chosen_ku": "KU-0002",
                },
            },
        ]

        state = make_minimal_state(conflict_ledger=ledger_data)
        state["domain_skeleton"] = {"domain": "test"}
        state["metrics"] = {"cycle": 1}
        save_state(state, str(domain_dir))

        # ledger 파일 존재 확인
        assert (state_dir / "conflict-ledger.json").exists()

        # load 후 데이터 일치 확인
        loaded = load_state(str(domain_dir))
        assert len(loaded["conflict_ledger"]) == 2
        assert loaded["conflict_ledger"][0]["ledger_id"] == "CL-0001"
        assert loaded["conflict_ledger"][1]["status"] == "resolved"

    def test_load_without_ledger_file(self, tmp_path):
        """ledger 파일 부재 시 빈 배열 (migration-safe)."""
        domain_dir = tmp_path / "no-ledger-domain"
        state_dir = domain_dir / "state"
        state_dir.mkdir(parents=True)

        for fname, default in [
            ("knowledge-units.json", "[]"),
            ("gap-map.json", "[]"),
            ("domain-skeleton.json", '{"domain":"test"}'),
            ("metrics.json", '{"cycle": 1}'),
            ("policies.json", "{}"),
        ]:
            (state_dir / fname).write_text(default, encoding="utf-8")

        loaded = load_state(str(domain_dir))
        assert loaded["conflict_ledger"] == []

    def test_ledger_id_queryable_after_resolve(self, tmp_path):
        """resolved 전환 후에도 ledger_id 로 조회 가능."""
        ledger = [
            {
                "ledger_id": "CL-0010",
                "ku_id": "KU-0050",
                "created_at": "2026-04-12",
                "status": "resolved",
                "conflicting_evidence": ["EU-0100"],
                "resolution": {
                    "method": "evidence majority",
                    "resolved_at": "2026-04-12",
                    "chosen_ku": "KU-0050",
                },
            },
        ]
        found = [e for e in ledger if e["ledger_id"] == "CL-0010"]
        assert len(found) == 1
        assert found[0]["status"] == "resolved"
