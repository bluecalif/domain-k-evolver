"""공통 pytest fixture — P0-X6.

bench/japan-travel/state/ JSON 로더를 한 곳에 모아 P1/P3 충돌 방지.
개별 테스트 파일에서 동일 이름 fixture 를 삭제하면 자동으로 이쪽을 사용한다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

BENCH_STATE = Path("bench/japan-travel/state")


@pytest.fixture(scope="session")
def bench_skeleton() -> dict:
    with open(BENCH_STATE / "domain-skeleton.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def bench_kus() -> list[dict]:
    with open(BENCH_STATE / "knowledge-units.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def bench_gap_map() -> list[dict]:
    with open(BENCH_STATE / "gap-map.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def bench_policies() -> dict:
    with open(BENCH_STATE / "policies.json", encoding="utf-8") as f:
        return json.load(f)


def make_minimal_state(**overrides: object) -> dict:
    """테스트용 최소 EvolverState 생성. Silver P0 X4 필드 포함."""
    base: dict = {
        "knowledge_units": [],
        "gap_map": [],
        "policies": {},
        "metrics": {"rates": {"evidence_rate": 1.0, "avg_confidence": 1.0}},
        "domain_skeleton": {},
        "current_cycle": 2,
        "current_plan": None,
        "current_claims": None,
        "current_critique": None,
        "current_mode": None,
        "axis_coverage": None,
        "jump_history": [],
        "hitl_pending": None,
        "dispute_queue": [],
        "conflict_ledger": [],
        "phase_history": [],
        "coverage_map": {},
        "novelty_history": [],
    }
    base.update(overrides)
    return base
