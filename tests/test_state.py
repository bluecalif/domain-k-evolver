"""EvolverState 타입 테스트 — 생성, 필드 접근, bench 데이터 호환성."""

import json
from pathlib import Path

from src.state import EvolverState, KnowledgeUnit, GapUnit

BENCH_STATE = Path("bench/japan-travel/state")


def test_create_empty_state():
    state: EvolverState = {
        "knowledge_units": [],
        "gap_map": [],
        "policies": {},
        "metrics": {},
        "domain_skeleton": {},
        "current_cycle": 0,
        "current_plan": None,
        "current_claims": None,
        "current_critique": None,
        "current_mode": None,
        "axis_coverage": None,
        "jump_history": [],
        "hitl_pending": None,
    }
    assert state["current_cycle"] == 0
    assert state["knowledge_units"] == []


def test_create_ku():
    ku: KnowledgeUnit = {
        "ku_id": "KU-0001",
        "entity_key": "japan-travel:pass-ticket:jr-pass",
        "field": "eligibility",
        "value": "test",
        "observed_at": "2026-03-04",
        "validity": {"ttl_days": 90},
        "evidence_links": ["EU-0001"],
        "confidence": 0.95,
        "status": "active",
    }
    assert ku["ku_id"] == "KU-0001"
    assert ku["confidence"] == 0.95


def test_create_gu():
    gu: GapUnit = {
        "gu_id": "GU-0001",
        "gap_type": "missing",
        "target": {"entity_key": "japan-travel:transport:taxi", "field": "price"},
        "expected_utility": "medium",
        "risk_level": "financial",
        "resolution_criteria": "기본요금 확인",
        "status": "open",
    }
    assert gu["status"] == "open"


def test_bench_knowledge_units_load():
    """bench/japan-travel/state/knowledge-units.json → list[KnowledgeUnit] 호환."""
    path = BENCH_STATE / "knowledge-units.json"
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        kus = json.load(f)
    assert isinstance(kus, list)
    assert len(kus) > 0
    ku: KnowledgeUnit = kus[0]
    assert "ku_id" in ku
    assert "entity_key" in ku
    assert "status" in ku


def test_bench_gap_map_load():
    """bench/japan-travel/state/gap-map.json → list[GapUnit] 호환."""
    path = BENCH_STATE / "gap-map.json"
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        gus = json.load(f)
    assert isinstance(gus, list)
    assert len(gus) > 0
    gu: GapUnit = gus[0]
    assert "gu_id" in gu
    assert "gap_type" in gu
    assert "status" in gu


def test_bench_domain_skeleton_load():
    """bench/japan-travel/state/domain-skeleton.json 호환."""
    path = BENCH_STATE / "domain-skeleton.json"
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        skel = json.load(f)
    assert "domain" in skel
    assert "categories" in skel
    assert "axes" in skel
    assert len(skel["axes"]) == 4  # category, geography, condition, risk


def test_bench_metrics_load():
    """bench/japan-travel/state/metrics.json 호환."""
    path = BENCH_STATE / "metrics.json"
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        m = json.load(f)
    assert "cycle" in m
    assert "rates" in m
    assert m["rates"]["evidence_rate"] == 1.0


def test_bench_policies_load():
    """bench/japan-travel/state/policies.json 호환."""
    path = BENCH_STATE / "policies.json"
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        p = json.load(f)
    assert "credibility_priors" in p
    assert "ttl_defaults" in p
    assert "conflict_resolution" in p


def test_full_state_from_bench():
    """5개 JSON → EvolverState 조립."""
    files = {
        "knowledge_units": "knowledge-units.json",
        "gap_map": "gap-map.json",
        "domain_skeleton": "domain-skeleton.json",
        "metrics": "metrics.json",
        "policies": "policies.json",
    }
    data = {}
    for key, fname in files.items():
        path = BENCH_STATE / fname
        if not path.exists():
            return
        with open(path, encoding="utf-8") as f:
            data[key] = json.load(f)

    state: EvolverState = {
        **data,
        "current_cycle": data["metrics"].get("cycle", 0),
        "current_plan": None,
        "current_claims": None,
        "current_critique": None,
        "current_mode": None,
        "axis_coverage": None,
        "jump_history": [],
        "hitl_pending": None,
    }
    assert state["current_cycle"] == 14
    assert len(state["knowledge_units"]) == 90
    assert len(state["gap_map"]) == 96
