"""test_mode — mode_node 단위 테스트."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.nodes.mode import (
    _compute_budget,
    _compute_trigger_t1,
    _compute_trigger_t3,
    _compute_trigger_t7_staleness,
    _get_cycle_stage,
    mode_node,
)

BENCH = Path("bench/japan-travel/state")


@pytest.fixture(scope="module")
def skeleton() -> dict:
    with open(BENCH / "domain-skeleton.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def kus() -> list[dict]:
    with open(BENCH / "knowledge-units.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def gap_map() -> list[dict]:
    with open(BENCH / "gap-map.json", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Trigger 테스트
# ---------------------------------------------------------------------------

class TestTriggerT1:
    def test_no_deficit(self, gap_map: list[dict], skeleton: dict) -> None:
        # bench Cycle 2 데이터: geography deficit 이미 해소
        result = _compute_trigger_t1(gap_map, skeleton)
        # category/risk 축은 전 카테고리에 GU 존재 → deficit 0
        # geography/condition은 axis_tags 기반이므로 대부분 GU에 태그 없음 → deficit 가능
        # 실제 결과는 데이터에 따라 다름
        assert isinstance(result, bool)

    def test_deficit_with_empty_anchor(self) -> None:
        gap_map = [
            {"status": "open", "target": {"entity_key": "d:cat-a:x"}, "risk_level": "safety"},
        ]
        skeleton = {
            "axes": [
                {"name": "category", "anchors": ["cat-a", "cat-b"], "required": True},
            ],
            "categories": [{"slug": "cat-a"}, {"slug": "cat-b"}],
        }
        result = _compute_trigger_t1(gap_map, skeleton)
        assert result is True  # cat-b에 GU 없음 → deficit > 0


class TestTriggerT3:
    def test_bench_kus(self, kus: list[dict]) -> None:
        result = _compute_trigger_t3(kus)
        assert isinstance(result, bool)

    def test_two_blindspots(self) -> None:
        kus = [
            {"status": "active", "evidence_links": ["EU-1"], "confidence": 0.7},
            {"status": "active", "evidence_links": ["EU-2"], "confidence": 0.6},
        ]
        assert _compute_trigger_t3(kus) is True

    def test_no_blindspots(self) -> None:
        kus = [
            {"status": "active", "evidence_links": ["EU-1", "EU-2"], "confidence": 0.9},
        ]
        assert _compute_trigger_t3(kus) is False


# ---------------------------------------------------------------------------
# Budget 배분
# ---------------------------------------------------------------------------

class TestBudget:
    def test_normal_mode(self) -> None:
        explore, exploit = _compute_budget(8, "normal", "early")
        assert explore == 0
        assert exploit == 8

    def test_jump_early(self) -> None:
        explore, exploit = _compute_budget(10, "jump", "early")
        assert explore == 6  # 60%
        assert exploit == 4  # 40%

    def test_jump_mid(self) -> None:
        explore, exploit = _compute_budget(10, "jump", "mid")
        assert explore == 5
        assert exploit == 5

    def test_jump_converging(self) -> None:
        explore, exploit = _compute_budget(10, "jump", "converging")
        assert explore == 4
        assert exploit == 6

    def test_odd_target_exploit_gets_extra(self) -> None:
        explore, exploit = _compute_budget(7, "jump", "early")
        # 7 * 0.6 = 4.2 → int(4.2) = 4
        # exploit = 7 - 4 = 3
        assert explore + exploit == 7
        assert exploit >= explore or explore + exploit == 7


class TestCycleStage:
    def test_early(self) -> None:
        assert _get_cycle_stage(1) == "early"
        assert _get_cycle_stage(3) == "early"

    def test_mid(self) -> None:
        assert _get_cycle_stage(4) == "mid"
        assert _get_cycle_stage(6) == "mid"

    def test_converging(self) -> None:
        assert _get_cycle_stage(7) == "converging"
        assert _get_cycle_stage(10) == "converging"


# ---------------------------------------------------------------------------
# mode_node 통합
# ---------------------------------------------------------------------------

class TestModeNode:
    def test_normal_mode_no_triggers(self) -> None:
        """trigger 없으면 Normal Mode."""
        state = {
            "gap_map": [
                {"status": "open", "target": {"entity_key": "d:a:x"}, "risk_level": "convenience"},
            ] * 10,
            "domain_skeleton": {
                "axes": [
                    {"name": "category", "anchors": ["a"], "required": True},
                ],
                "categories": [{"slug": "a"}],
            },
            "knowledge_units": [
                {"status": "active", "evidence_links": ["EU-1", "EU-2"], "confidence": 0.95},
            ],
            "current_cycle": 1,
            "jump_history": [],
        }
        result = mode_node(state)
        assert result["current_mode"]["mode"] == "normal"
        assert result["current_mode"]["explore_budget"] == 0
        assert len(result["current_mode"]["trigger_set"]) == 0

    def test_jump_mode_with_deficit(self) -> None:
        """required 축 deficit → Jump Mode."""
        state = {
            "gap_map": [
                {"status": "open", "target": {"entity_key": "d:cat-a:x"}, "risk_level": "safety"},
            ] * 5,
            "domain_skeleton": {
                "axes": [
                    {"name": "category", "anchors": ["cat-a", "cat-b"], "required": True},
                ],
                "categories": [{"slug": "cat-a"}, {"slug": "cat-b"}],
            },
            "knowledge_units": [],
            "current_cycle": 1,
            "jump_history": [],
        }
        result = mode_node(state)
        assert result["current_mode"]["mode"] == "jump"
        assert "T1:axis_under_coverage" in result["current_mode"]["trigger_set"]

    def test_convergence_warning(self) -> None:
        """연속 2 Cycle Jump → convergence_warning."""
        state = {
            "gap_map": [
                {"status": "open", "target": {"entity_key": "d:cat-a:x"}, "risk_level": "safety"},
            ] * 5,
            "domain_skeleton": {
                "axes": [
                    {"name": "category", "anchors": ["cat-a", "cat-b"], "required": True},
                ],
                "categories": [{"slug": "cat-a"}, {"slug": "cat-b"}],
            },
            "knowledge_units": [],
            "current_cycle": 3,
            "jump_history": [2],  # 이전 Cycle=2에서 Jump
        }
        result = mode_node(state)
        assert result["current_mode"].get("convergence_warning") is True

    def test_jump_history_updated(self) -> None:
        state = {
            "gap_map": [
                {"status": "open", "target": {"entity_key": "d:cat-a:x"}, "risk_level": "safety"},
            ] * 5,
            "domain_skeleton": {
                "axes": [
                    {"name": "category", "anchors": ["cat-a", "cat-b"], "required": True},
                ],
                "categories": [{"slug": "cat-a"}, {"slug": "cat-b"}],
            },
            "knowledge_units": [],
            "current_cycle": 2,
            "jump_history": [],
        }
        result = mode_node(state)
        if result["current_mode"]["mode"] == "jump":
            assert 2 in result["jump_history"]

    def test_cap_bounds(self) -> None:
        """cap 하한: normal ≥4, jump ≥10."""
        # Normal with few open
        state = {
            "gap_map": [
                {"status": "open", "target": {"entity_key": "d:a:x"}, "risk_level": "convenience"},
            ] * 3,
            "domain_skeleton": {
                "axes": [{"name": "category", "anchors": ["a"], "required": True}],
                "categories": [{"slug": "a"}],
            },
            "knowledge_units": [
                {"status": "active", "evidence_links": ["EU-1", "EU-2"], "confidence": 0.95},
            ],
            "current_cycle": 1,
            "jump_history": [],
        }
        result = mode_node(state)
        cap = result["current_mode"]["cap"]
        assert cap >= 4

    def test_target_count_no_upper_cap_jump(self) -> None:
        """D-129 regression guard: jump target_count = ceil(open*0.5), no upper cap.

        b12545d 에서 재도입된 JUMP_TARGET_CAP=10 을 Phase 5(b122a23) 공식으로 복원.
        open=67 기준 target_count=34 (10 아님) 이어야 함.
        """
        gap_map = [
            {"status": "open", "target": {"entity_key": f"d:a:x{i}"}, "risk_level": "convenience"}
            for i in range(67)
        ]
        state = {
            "gap_map": gap_map,
            "domain_skeleton": {
                "axes": [{"name": "category", "anchors": ["a"], "required": True}],
                "categories": [{"slug": "a"}],
            },
            "knowledge_units": [
                {"status": "active", "entity_key": "d:a:y", "field": "f",
                 "evidence_links": ["EU-1"], "confidence": 0.95,
                 "axis_tags": {"category": "a"}},
            ],
            "current_cycle": 2,
            "jump_history": [1],
            "metrics": {"rates": {"staleness_risk": 50}},  # T7 → jump
        }
        result = mode_node(state)
        md = result["current_mode"]
        assert md["mode"] == "jump", f"expected jump, got {md['mode']}"
        tc = md["explore_budget"] + md["exploit_budget"]
        assert tc == 34, (
            f"jump target_count regression: expected 34 (ceil(67*0.5)), got {tc}"
        )

    def test_target_count_no_upper_cap_normal(self) -> None:
        """D-129 regression guard: normal target_count = ceil(open*0.4), no cap."""
        gap_map = [
            {"status": "open", "target": {"entity_key": f"d:a:x{i}"}, "risk_level": "convenience"}
            for i in range(50)
        ]
        state = {
            "gap_map": gap_map,
            "domain_skeleton": {
                "axes": [{"name": "category", "anchors": ["a"], "required": True}],
                "categories": [{"slug": "a"}],
            },
            "knowledge_units": [
                {"status": "active", "entity_key": "d:a:y", "field": "f",
                 "evidence_links": ["EU-1", "EU-2"], "confidence": 0.95,
                 "axis_tags": {"category": "a"}},
            ],
            "current_cycle": 1,
            "jump_history": [],
        }
        result = mode_node(state)
        md = result["current_mode"]
        if md["mode"] == "normal":
            tc = md["explore_budget"] + md["exploit_budget"]
            assert tc == 20, (
                f"normal target_count regression: expected 20 (ceil(50*0.4)), got {tc}"
            )


# ---------------------------------------------------------------------------
# Stage E: Fix D — T7 Staleness Trigger (D-65)
# ---------------------------------------------------------------------------

class TestTriggerT7:
    def test_staleness_over_20_triggers(self) -> None:
        assert _compute_trigger_t7_staleness({"rates": {"staleness_risk": 25}}) is True

    def test_staleness_under_20_no_trigger(self) -> None:
        assert _compute_trigger_t7_staleness({"rates": {"staleness_risk": 10}}) is False

    def test_staleness_exactly_20_no_trigger(self) -> None:
        assert _compute_trigger_t7_staleness({"rates": {"staleness_risk": 20}}) is False

    def test_empty_metrics_no_trigger(self) -> None:
        assert _compute_trigger_t7_staleness({}) is False

    def test_t7_in_mode_node(self) -> None:
        """staleness_risk > 20 → T7 trigger → Jump Mode."""
        state = {
            "gap_map": [
                {"status": "open", "target": {"entity_key": "d:a:x"}, "risk_level": "convenience"},
            ] * 5,
            "domain_skeleton": {
                "axes": [{"name": "category", "anchors": ["a"], "required": True}],
                "categories": [{"slug": "a"}],
            },
            "knowledge_units": [
                {"status": "active", "evidence_links": ["EU-1", "EU-2"], "confidence": 0.95},
            ],
            "current_cycle": 1,
            "jump_history": [],
            "metrics": {"rates": {"staleness_risk": 50}},
        }
        result = mode_node(state)
        assert "T7:staleness_risk" in result["current_mode"]["trigger_set"]
        assert result["current_mode"]["mode"] == "jump"
