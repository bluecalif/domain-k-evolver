"""Schema 검증 유틸리티 테스트 — 유효/무효 데이터 + bench 데이터."""

from src.utils.schema_validator import (
    validate_ku,
    validate_eu,
    validate_gu,
    validate_pu,
    validate_state,
)
from src.utils.state_io import load_state

BENCH = "bench/japan-travel"


# --- KU ---


def test_valid_ku():
    ku = {
        "ku_id": "KU-0001",
        "entity_key": "japan-travel:transport:jr-pass",
        "field": "price",
        "value": "50000 JPY",
        "observed_at": "2026-03-04",
        "evidence_links": ["EU-0001"],
        "confidence": 0.95,
        "status": "active",
    }
    assert validate_ku(ku) == []


def test_invalid_ku_missing_field():
    ku = {"ku_id": "KU-0001", "entity_key": "japan-travel:transport:jr-pass"}
    errors = validate_ku(ku)
    assert len(errors) > 0


def test_invalid_ku_bad_id():
    ku = {
        "ku_id": "KU-1",  # 패턴 불일치
        "entity_key": "japan-travel:transport:jr-pass",
        "field": "price",
        "value": "test",
        "observed_at": "2026-03-04",
        "evidence_links": ["EU-0001"],
        "confidence": 0.95,
        "status": "active",
    }
    errors = validate_ku(ku)
    assert any("ku_id" in str(e.path) or "pattern" in e.message for e in errors)


def test_invalid_ku_empty_evidence():
    ku = {
        "ku_id": "KU-0001",
        "entity_key": "japan-travel:transport:jr-pass",
        "field": "price",
        "value": "test",
        "observed_at": "2026-03-04",
        "evidence_links": [],  # minItems: 1
        "confidence": 0.95,
        "status": "active",
    }
    errors = validate_ku(ku)
    assert len(errors) > 0


def test_invalid_ku_confidence_range():
    ku = {
        "ku_id": "KU-0001",
        "entity_key": "japan-travel:transport:jr-pass",
        "field": "price",
        "value": "test",
        "observed_at": "2026-03-04",
        "evidence_links": ["EU-0001"],
        "confidence": 1.5,  # > 1.0
        "status": "active",
    }
    errors = validate_ku(ku)
    assert len(errors) > 0


# --- EU ---


def test_valid_eu():
    eu = {
        "eu_id": "EU-0001",
        "source_id": "https://example.com",
        "source_type": "official",
        "retrieved_at": "2026-03-04",
        "snippet": "test snippet",
    }
    assert validate_eu(eu) == []


def test_invalid_eu_bad_source_type():
    eu = {
        "eu_id": "EU-0001",
        "source_id": "https://example.com",
        "source_type": "unknown",  # enum 외
        "retrieved_at": "2026-03-04",
        "snippet": "test",
    }
    errors = validate_eu(eu)
    assert len(errors) > 0


# --- GU ---


def test_valid_gu():
    gu = {
        "gu_id": "GU-0001",
        "gap_type": "missing",
        "target": {"entity_key": "japan-travel:transport:taxi", "field": "price"},
        "expected_utility": "high",
        "status": "open",
    }
    assert validate_gu(gu) == []


def test_invalid_gu_missing_target():
    gu = {
        "gu_id": "GU-0001",
        "gap_type": "missing",
        "expected_utility": "high",
        "status": "open",
    }
    errors = validate_gu(gu)
    assert len(errors) > 0


# --- PU ---


def test_valid_pu():
    pu = {
        "pu_id": "PU-0001",
        "cycle": 1,
        "timestamp": "2026-03-04",
        "adds": ["KU-0010"],
        "updates": [],
        "deprecates": [],
    }
    assert validate_pu(pu) == []


def test_invalid_pu_missing_cycle():
    pu = {
        "pu_id": "PU-0001",
        "timestamp": "2026-03-04",
        "adds": [],
        "updates": [],
        "deprecates": [],
    }
    errors = validate_pu(pu)
    assert len(errors) > 0


# --- Bench 데이터 검증 ---


def test_bench_all_ku_valid():
    """bench KU 28개 전체 스키마 통과."""
    state = load_state(BENCH)
    for ku in state["knowledge_units"]:
        errors = validate_ku(ku)
        assert errors == [], f"{ku['ku_id']}: {[e.message for e in errors]}"


def test_bench_all_gu_valid():
    """bench GU 39개 전체 스키마 통과."""
    state = load_state(BENCH)
    for gu in state["gap_map"]:
        errors = validate_gu(gu)
        assert errors == [], f"{gu['gu_id']}: {[e.message for e in errors]}"


def test_bench_validate_state():
    """validate_state로 bench 전체 검증."""
    state = load_state(BENCH)
    errors = validate_state(state)
    assert errors == [], f"State errors: {[e.message for e in errors]}"
