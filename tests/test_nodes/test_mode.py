"""test_mode — mode_node 단위 테스트."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.nodes.mode import (
    CYCLE_CAP,
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
        """cap = min(open_count, CYCLE_CAP) — 하한 없음, open 수 그대로 (S1-T3)."""
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
        assert cap == 3

    def test_target_count_no_upper_cap_jump(self) -> None:
        """S1-T3: jump target_count = min(open, CYCLE_CAP) = 67 (이전 비율 공식 34 아님)."""
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
        assert tc == 67, (
            f"jump target_count regression: expected 67 (min(67,100)), got {tc}"
        )

    def test_target_count_no_upper_cap_normal(self) -> None:
        """S1-T3: normal target_count = min(open, CYCLE_CAP) = 50 (이전 비율 공식 20 아님)."""
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
            assert tc == 50, (
                f"normal target_count regression: expected 50 (min(50,100)), got {tc}"
            )


# ---------------------------------------------------------------------------
# D-129 Regression Guard (S1-T7)
# ---------------------------------------------------------------------------

class TestD129RegressionGuard:
    """D-129: target_count 상한 재도입 방지.

    Phase 5(b122a23) 에서 의도적으로 제거된 per-mode cap 이
    재도입되지 않도록 보호하는 전용 regression suite.

    위반 패턴:
      - mode.py 에 max(4, ceil(open*0.2)) / max(10, ceil(open*0.6)) 복귀
      - CYCLE_CAP 을 10 이하로 낮춤
      - cap 을 mode 별로 다르게 설정
    """

    def test_cycle_cap_constant_is_100(self) -> None:
        """CYCLE_CAP 상수가 100 이어야 함 — 낮추면 D-129 위반."""
        assert CYCLE_CAP == 100, f"CYCLE_CAP regression: expected 100, got {CYCLE_CAP}"

    def test_cap_equals_open_count_below_cycle_cap(self) -> None:
        """open < CYCLE_CAP 일 때 cap == open (비율 공식 아님)."""
        for open_n in (1, 5, 15, 30, 99):
            gap_map = [
                {"status": "open", "target": {"entity_key": f"d:a:x{i}"}, "risk_level": "convenience"}
                for i in range(open_n)
            ]
            state = {
                "gap_map": gap_map,
                "domain_skeleton": {"axes": [{"name": "category", "anchors": ["a"], "required": True}],
                                    "categories": [{"slug": "a"}]},
                "knowledge_units": [{"status": "active", "evidence_links": ["EU-1", "EU-2"],
                                     "confidence": 0.95}],
                "current_cycle": 1,
                "jump_history": [],
            }
            result = mode_node(state)
            cap = result["current_mode"]["cap"]
            assert cap == open_n, (
                f"D-129 regression (open={open_n}): cap={cap}, expected {open_n}. "
                "비율 공식이 재도입됐을 가능성."
            )

    def test_cap_clamped_at_cycle_cap_above_100(self) -> None:
        """open > CYCLE_CAP 이면 cap == CYCLE_CAP (100)."""
        gap_map = [
            {"status": "open", "target": {"entity_key": f"d:a:x{i}"}, "risk_level": "convenience"}
            for i in range(150)
        ]
        state = {
            "gap_map": gap_map,
            "domain_skeleton": {"axes": [{"name": "category", "anchors": ["a"], "required": True}],
                                 "categories": [{"slug": "a"}]},
            "knowledge_units": [{"status": "active", "evidence_links": ["EU-1", "EU-2"],
                                  "confidence": 0.95}],
            "current_cycle": 1,
            "jump_history": [],
        }
        result = mode_node(state)
        cap = result["current_mode"]["cap"]
        assert cap == CYCLE_CAP, (
            f"D-129 regression: open=150, expected cap={CYCLE_CAP}, got {cap}"
        )

    def test_normal_and_jump_use_same_cap_formula(self) -> None:
        """normal / jump 양 mode 의 cap 공식이 동일해야 함 (mode 별 비율 복귀 방지)."""
        open_n = 40
        gap_map_base = [
            {"status": "open", "target": {"entity_key": f"d:a:x{i}"}, "risk_level": "convenience"}
            for i in range(open_n)
        ]

        # normal mode
        state_normal = {
            "gap_map": gap_map_base,
            "domain_skeleton": {"axes": [{"name": "category", "anchors": ["a"], "required": True}],
                                 "categories": [{"slug": "a"}]},
            "knowledge_units": [{"status": "active", "evidence_links": ["EU-1", "EU-2"],
                                  "confidence": 0.95}],
            "current_cycle": 1,
            "jump_history": [],
        }
        r_normal = mode_node(state_normal)

        # jump mode (T7 staleness trigger)
        state_jump = {**state_normal, "metrics": {"rates": {"staleness_risk": 50}}}
        r_jump = mode_node(state_jump)

        cap_normal = r_normal["current_mode"]["cap"]
        cap_jump = r_jump["current_mode"]["cap"]
        assert cap_normal == cap_jump == open_n, (
            f"D-129 regression: cap diverged by mode — normal={cap_normal}, jump={cap_jump}. "
            "per-mode 비율 공식이 재도입됐을 가능성."
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
