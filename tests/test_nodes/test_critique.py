"""test_critique — critique_node 단위 테스트."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from src.nodes.critique import (
    _analyze_failure_modes,
    _check_convergence,
    _compute_refresh_cap,
    _generate_balance_gus,
    _identify_deficit_categories,
    _generate_refresh_gus,
    critique_node,
    INTEGRATION_CONV_RATE_THRESHOLD,
)

BENCH = Path("bench/japan-travel/state")


@pytest.fixture(scope="module")
def kus() -> list[dict]:
    with open(BENCH / "knowledge-units.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def gap_map() -> list[dict]:
    with open(BENCH / "gap-map.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def skeleton() -> dict:
    with open(BENCH / "domain-skeleton.json", encoding="utf-8") as f:
        return json.load(f)


class TestFailureModes:
    def test_epistemic_single_source(self) -> None:
        kus = [
            {"ku_id": "KU-001", "status": "active", "entity_key": "d:regulation:x",
             "evidence_links": ["EU-1"], "confidence": 0.7},
        ]
        rxs = _analyze_failure_modes(kus, [], {"categories": []})
        assert any(rx["type"] == "epistemic" for rx in rxs)

    def test_temporal_expiring(self) -> None:
        kus = [
            {"ku_id": "KU-001", "status": "active", "entity_key": "d:a:x",
             "evidence_links": ["EU-1", "EU-2"], "confidence": 0.9,
             "validity": {"expires_at": "2026-03-20"}},
        ]
        rxs = _analyze_failure_modes(kus, [], {"categories": []}, today=date(2026, 3, 4))
        assert any(rx["type"] == "temporal" for rx in rxs)

    def test_consistency_disputed(self) -> None:
        kus = [
            {"ku_id": "KU-001", "status": "disputed", "entity_key": "d:a:x",
             "evidence_links": ["EU-1"]},
        ]
        rxs = _analyze_failure_modes(kus, [], {"categories": []})
        assert any(rx["type"] == "consistency" for rx in rxs)

    def test_bench_prescriptions(
        self, kus: list[dict], gap_map: list[dict], skeleton: dict,
    ) -> None:
        rxs = _analyze_failure_modes(kus, gap_map, skeleton, today=date(2026, 3, 4))
        # Phase 3 이후 disputed=0, staleness=59 → epistemic 처방만 존재
        assert any(rx["type"] == "epistemic" for rx in rxs)


class TestConvergence:
    def test_not_converged_early_cycle(self) -> None:
        result = _check_convergence([], [], {"categories": []}, cycle=2, metrics_rates={})
        assert result["converged"] is False
        assert result["conditions"]["min_cycle"] is False

    def test_converged_all_met(self) -> None:
        kus = [{"status": "active", "confidence": 0.9}] * 10
        gap_map = [
            {"gu_id": "GU-1", "status": "resolved", "expected_utility": "critical",
             "gap_type": "missing", "target": {"entity_key": "d:a:x"}},
            {"gu_id": "GU-2", "status": "resolved", "expected_utility": "high",
             "gap_type": "missing", "target": {"entity_key": "d:b:x"}},
        ]
        skeleton = {"categories": [{"slug": "a"}, {"slug": "b"}]}
        rates = {"avg_confidence": 0.90, "conflict_rate": 0.05}
        result = _check_convergence(kus, gap_map, skeleton, cycle=5, metrics_rates=rates)
        assert result["converged"] is True
        assert result["conditions"]["C6_conflict_rate"] is True

    def test_not_converged_high_conflict_rate(self) -> None:
        """C6: conflict_rate > threshold → 수렴 불가."""
        kus = [{"status": "active", "confidence": 0.9}] * 10
        gap_map = [
            {"gu_id": "GU-1", "status": "resolved", "expected_utility": "critical",
             "gap_type": "missing", "target": {"entity_key": "d:a:x"}},
        ]
        skeleton = {"categories": [{"slug": "a"}]}
        rates = {"avg_confidence": 0.90, "conflict_rate": 0.30}
        result = _check_convergence(kus, gap_map, skeleton, cycle=5, metrics_rates=rates)
        assert result["converged"] is False
        assert result["conditions"]["C6_conflict_rate"] is False


class TestCritiqueNode:
    def test_bench_critique(
        self, kus: list[dict], gap_map: list[dict], skeleton: dict,
    ) -> None:
        state = {
            "knowledge_units": kus,
            "gap_map": gap_map,
            "domain_skeleton": skeleton,
            "current_cycle": 2,
            "metrics": {"rates": {}},
        }
        result = critique_node(state, today=date(2026, 3, 4))

        assert "current_critique" in result
        assert "axis_coverage" in result
        assert "metrics" in result

        critique = result["current_critique"]
        assert "health" in critique
        assert "prescriptions" in critique
        assert "convergence" in critique

    def test_metrics_rates_match(
        self, kus: list[dict], gap_map: list[dict], skeleton: dict,
    ) -> None:
        state = {
            "knowledge_units": kus,
            "gap_map": gap_map,
            "domain_skeleton": skeleton,
            "current_cycle": 2,
            "metrics": {"rates": {}},
        }
        result = critique_node(state, today=date(2026, 3, 4))
        rates = result["metrics"]["rates"]

        assert rates["evidence_rate"] == pytest.approx(1.0)
        # Phase 3 dispute resolution: KU-0007 (3 EU vs 1 dispute) 자동 해소 → conflict_rate 0
        assert rates["conflict_rate"] == pytest.approx(0.0, abs=0.002)

    def test_axis_coverage_entries(
        self, kus: list[dict], gap_map: list[dict], skeleton: dict,
    ) -> None:
        state = {
            "knowledge_units": kus,
            "gap_map": gap_map,
            "domain_skeleton": skeleton,
            "current_cycle": 2,
            "metrics": {"rates": {}},
        }
        result = critique_node(state, today=date(2026, 3, 4))
        entries = result["axis_coverage"]

        assert len(entries) > 0
        for entry in entries:
            assert "axis" in entry
            assert "anchor" in entry
            assert "open_count" in entry
            assert "resolved_count" in entry

    def test_not_converged_cycle_2(
        self, kus: list[dict], gap_map: list[dict], skeleton: dict,
    ) -> None:
        state = {
            "knowledge_units": kus,
            "gap_map": gap_map,
            "domain_skeleton": skeleton,
            "current_cycle": 2,
            "metrics": {"rates": {}},
        }
        result = critique_node(state, today=date(2026, 3, 4))
        assert result["current_critique"]["convergence"]["converged"] is False

    def test_dispute_resolution_in_critique(self) -> None:
        """critique_node에서 disputed KU 자동 해소 (evidence majority)."""
        kus = [
            {
                "ku_id": "KU-001", "entity_key": "d:a:x", "field": "price",
                "status": "disputed",
                "evidence_links": ["EU-1", "EU-2", "EU-3"],
                "confidence": 0.8,
                "disputes": [{"nature": "conflict", "resolution": "hold"}],
            },
        ]
        state = {
            "knowledge_units": kus,
            "gap_map": [],
            "domain_skeleton": {"categories": []},
            "current_cycle": 1,
            "metrics": {"rates": {}},
        }
        result = critique_node(state, today=date(2026, 3, 4))

        # KU가 active로 해소됨
        assert "knowledge_units" in result
        assert result["knowledge_units"][0]["status"] == "active"

        # dispute_resolved 처방이 생성됨
        rxs = result["current_critique"]["prescriptions"]
        assert any(rx["type"] == "dispute_resolved" for rx in rxs)

    def test_no_dispute_resolution_insufficient_evidence(self) -> None:
        """evidence 부족 시 disputed 유지."""
        kus = [
            {
                "ku_id": "KU-001", "entity_key": "d:a:x", "field": "price",
                "status": "disputed",
                "evidence_links": ["EU-1"],
                "confidence": 0.8,
                "disputes": [{"nature": "conflict", "resolution": "hold"}],
            },
        ]
        state = {
            "knowledge_units": kus,
            "gap_map": [],
            "domain_skeleton": {"categories": []},
            "current_cycle": 1,
            "metrics": {"rates": {}},
        }
        result = critique_node(state, today=date(2026, 3, 4))

        # KU는 여전히 disputed
        assert kus[0]["status"] == "disputed"
        # knowledge_units가 반환되지 않음 (변경 없으므로)
        assert "knowledge_units" not in result


# ---------------------------------------------------------------------------
# Task 5.5: Stale KU → Refresh GU
# ---------------------------------------------------------------------------

class TestGenerateRefreshGus:
    def test_stale_ku_generates_refresh_gu(self) -> None:
        kus = [
            {
                "ku_id": "KU-001", "entity_key": "d:transport:bus",
                "field": "price", "status": "active",
                "observed_at": "2025-01-01", "validity": {"ttl_days": 180},
                "evidence_links": ["EU-1"], "confidence": 0.8,
            },
        ]
        gus = _generate_refresh_gus(kus, [], max_gu_id=0, today=date(2026, 3, 7))
        assert len(gus) == 1
        assert gus[0]["gap_type"] == "stale"
        assert gus[0]["trigger"] == "D:stale_refresh"
        assert gus[0]["trigger_source"] == "KU-001"
        assert gus[0]["target"]["entity_key"] == "d:transport:bus"
        assert gus[0]["target"]["field"] == "price"

    def test_non_expired_ku_skipped(self) -> None:
        kus = [
            {
                "ku_id": "KU-001", "entity_key": "d:a:x",
                "field": "price", "status": "active",
                "observed_at": "2026-03-01", "validity": {"ttl_days": 180},
                "evidence_links": ["EU-1"], "confidence": 0.8,
            },
        ]
        gus = _generate_refresh_gus(kus, [], max_gu_id=0, today=date(2026, 3, 7))
        assert len(gus) == 0

    def test_duplicate_prevention(self) -> None:
        """동일 entity_key+field에 open refresh GU 있으면 스킵."""
        kus = [
            {
                "ku_id": "KU-001", "entity_key": "d:a:x",
                "field": "price", "status": "active",
                "observed_at": "2025-01-01", "validity": {"ttl_days": 180},
                "evidence_links": ["EU-1"], "confidence": 0.8,
            },
        ]
        existing_gap_map = [
            {
                "gu_id": "GU-0001", "gap_type": "stale", "status": "open",
                "target": {"entity_key": "d:a:x", "field": "price"},
            },
        ]
        gus = _generate_refresh_gus(kus, existing_gap_map, max_gu_id=1, today=date(2026, 3, 7))
        assert len(gus) == 0

    def test_cap_limit(self) -> None:
        """cycle당 상한 10개."""
        kus = [
            {
                "ku_id": f"KU-{i:04d}", "entity_key": f"d:a:x{i}",
                "field": "price", "status": "active",
                "observed_at": "2025-01-01", "validity": {"ttl_days": 180},
                "evidence_links": ["EU-1"], "confidence": 0.8,
            }
            for i in range(15)
        ]
        gus = _generate_refresh_gus(kus, [], max_gu_id=0, today=date(2026, 3, 7))
        assert len(gus) == 10

    def test_axis_tags_inherited(self) -> None:
        """KU의 axis_tags가 refresh GU에 복사."""
        kus = [
            {
                "ku_id": "KU-001", "entity_key": "d:transport:bus",
                "field": "price", "status": "active",
                "observed_at": "2025-01-01", "validity": {"ttl_days": 180},
                "evidence_links": ["EU-1"], "confidence": 0.8,
                "axis_tags": {"geography": "tokyo"},
            },
        ]
        gus = _generate_refresh_gus(kus, [], max_gu_id=0, today=date(2026, 3, 7))
        assert gus[0]["axis_tags"] == {"geography": "tokyo"}

    def test_critique_node_adds_refresh_gus(self) -> None:
        """critique_node에서 stale KU → gap_map에 refresh GU 추가."""
        kus = [
            {
                "ku_id": "KU-001", "entity_key": "d:transport:bus",
                "field": "price", "status": "active",
                "observed_at": "2025-01-01", "validity": {"ttl_days": 180},
                "evidence_links": ["EU-1", "EU-2"], "confidence": 0.9,
            },
        ]
        state = {
            "knowledge_units": kus,
            "gap_map": [
                {"gu_id": "GU-0001", "status": "resolved", "gap_type": "missing",
                 "expected_utility": "high",
                 "target": {"entity_key": "d:transport:bus", "field": "price"}},
            ],
            "domain_skeleton": {"categories": [{"slug": "transport"}]},
            "current_cycle": 1,
            "metrics": {"rates": {}},
        }
        result = critique_node(state, today=date(2026, 3, 7))
        assert "gap_map" in result
        refresh = [gu for gu in result["gap_map"] if gu.get("gap_type") == "stale"]
        assert len(refresh) == 1
        assert refresh[0]["trigger"] == "D:stale_refresh"


# ---------------------------------------------------------------------------
# Task 5.7: Category 균형 GU 생성
# ---------------------------------------------------------------------------

class TestGenerateBalanceGus:
    """S4-T1: _generate_balance_gus 는 항상 빈 리스트 반환 (virtual entity 제거)."""

    _SKELETON = {
        "domain": "test",
        "categories": [
            {"slug": "transport"},
            {"slug": "dining"},
            {"slug": "payment"},
        ],
        "fields": [
            {"name": "price", "categories": ["*"]},
            {"name": "hours", "categories": ["dining"]},
            {"name": "how_to_use", "categories": ["transport", "payment"]},
        ],
    }

    def test_always_returns_empty(self) -> None:
        """S4-T1: virtual balance-N 제거 — 항상 빈 리스트."""
        kus = []
        gus = _generate_balance_gus(kus, [], self._SKELETON, max_gu_id=0)
        assert gus == []

    def test_no_balance_entity_in_gap_map_after_critique(self) -> None:
        """critique 실행 후 gap_map에 balance-* entity GU 없음."""
        state = {
            "knowledge_units": [],
            "gap_map": [],
            "domain_skeleton": self._SKELETON,
            "current_cycle": 1,
            "metrics": {"rates": {}},
        }
        result = critique_node(state, today=date(2026, 3, 7))
        gap_map = result.get("gap_map", [])
        balance = [gu for gu in gap_map
                   if "balance-" in gu.get("target", {}).get("entity_key", "")]
        assert balance == []


class TestIdentifyDeficitCategories:
    """S4-T2: _identify_deficit_categories — coverage_map.deficit_score 기반."""

    _SKELETON = {
        "categories": [
            {"slug": "transport"},
            {"slug": "dining"},
            {"slug": "payment"},
        ],
    }

    def test_returns_deficit_categories(self) -> None:
        coverage_map = {
            "transport": {"deficit_score": 0.8, "ku_count": 2},
            "dining": {"deficit_score": 0.3, "ku_count": 7},
            "payment": {"deficit_score": 0.9, "ku_count": 1},
        }
        result = _identify_deficit_categories(coverage_map, self._SKELETON)
        cats = [r["category"] for r in result]
        assert "transport" in cats
        assert "payment" in cats
        assert "dining" not in cats  # 0.3 < 0.5 threshold

    def test_sorted_by_deficit_desc(self) -> None:
        coverage_map = {
            "transport": {"deficit_score": 0.7, "ku_count": 3},
            "dining": {"deficit_score": 0.2, "ku_count": 8},
            "payment": {"deficit_score": 0.9, "ku_count": 1},
        }
        result = _identify_deficit_categories(coverage_map, self._SKELETON)
        scores = [r["deficit_score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_none_coverage_map_returns_empty(self) -> None:
        result = _identify_deficit_categories(None, self._SKELETON)
        assert result == []

    def test_deficit_categories_in_critique_report(self) -> None:
        """critique_node 결과에 deficit_categories 포함."""
        state = {
            "knowledge_units": [],
            "gap_map": [],
            "domain_skeleton": self._SKELETON,
            "current_cycle": 1,
            "metrics": {},
            "coverage_map": {
                "transport": {"deficit_score": 0.8, "ku_count": 2},
                "dining": {"deficit_score": 0.2, "ku_count": 8},
                "payment": {"deficit_score": 0.9, "ku_count": 1},
            },
        }
        result = critique_node(state, today=date(2026, 3, 7))
        report = result["current_critique"]
        assert "deficit_categories" in report
        cats = [d["category"] for d in report["deficit_categories"]]
        assert "transport" in cats
        assert "payment" in cats


# ---------------------------------------------------------------------------
# Stage E: Fix C — Adaptive REFRESH_GU_CAP (D-64)
# ---------------------------------------------------------------------------

class TestAdaptiveRefreshCap:
    def test_default_cap_under_20(self) -> None:
        """stale <= 20 → 기본값 10."""
        assert _compute_refresh_cap(5) == 10
        assert _compute_refresh_cap(15) == 10
        assert _compute_refresh_cap(20) == 10

    def test_medium_staleness(self) -> None:
        """20 < stale <= 50 → min(20, max(10, stale//2))."""
        assert _compute_refresh_cap(30) == 15  # 30//2 = 15
        assert _compute_refresh_cap(40) == 20  # 40//2 = 20
        assert _compute_refresh_cap(50) == 20  # cap at 20

    def test_high_staleness(self) -> None:
        """stale > 50 → min(25, max(10, stale//3))."""
        assert _compute_refresh_cap(60) == 20  # 60//3 = 20
        assert _compute_refresh_cap(93) == 25  # 93//3 = 31 → capped at 25
        assert _compute_refresh_cap(150) == 25  # 150//3 = 50 → capped at 25

    def test_adaptive_cap_in_generate_refresh_gus(self) -> None:
        """실제 _generate_refresh_gus에서 adaptive cap 적용 확인."""
        # 60개 stale KU → cap = min(25, max(10, 60//3)) = 20
        kus = [
            {
                "ku_id": f"KU-{i:04d}", "entity_key": f"d:a:x{i}",
                "field": "price", "status": "active",
                "observed_at": "2025-01-01", "validity": {"ttl_days": 180},
                "evidence_links": ["EU-1"], "confidence": 0.8,
            }
            for i in range(60)
        ]
        gus = _generate_refresh_gus(kus, [], max_gu_id=0, today=date(2026, 3, 7))
        assert len(gus) == 20  # adaptive: 60//3 = 20


# ---------------------------------------------------------------------------
# S2-T1: integration_bottleneck 처방
# ---------------------------------------------------------------------------

class TestIntegrationBottleneck:
    def test_low_conv_rate_generates_prescription(self) -> None:
        """conv_rate < 0.3 → integration_bottleneck 처방 생성."""
        dist = {"conv_rate": 0.1, "total_claims": 20, "resolved": 2,
                "no_source_gu": 5, "invalid_result": 3, "other": 10}
        rxs = _analyze_failure_modes([], [], {"categories": []}, integration_result_dist=dist)
        assert any(rx["type"] == "integration_bottleneck" for rx in rxs)

    def test_high_conv_rate_no_prescription(self) -> None:
        """conv_rate >= 0.3 → integration_bottleneck 처방 없음."""
        dist = {"conv_rate": 0.5, "total_claims": 10, "resolved": 5,
                "no_source_gu": 0, "invalid_result": 0, "other": 5}
        rxs = _analyze_failure_modes([], [], {"categories": []}, integration_result_dist=dist)
        assert not any(rx["type"] == "integration_bottleneck" for rx in rxs)

    def test_zero_claims_no_prescription(self) -> None:
        """total_claims == 0 → 처방 없음."""
        dist = {"conv_rate": 0.0, "total_claims": 0, "resolved": 0,
                "no_source_gu": 0, "invalid_result": 0, "other": 0}
        rxs = _analyze_failure_modes([], [], {"categories": []}, integration_result_dist=dist)
        assert not any(rx["type"] == "integration_bottleneck" for rx in rxs)

    def test_bottleneck_machine_rule_generated(self) -> None:
        """conv_rate < 0.3 → machine_rules에 integration_bottleneck 규칙 포함."""
        state = {
            "knowledge_units": [],
            "gap_map": [],
            "domain_skeleton": {"categories": [], "fields": [], "axes": []},
            "current_cycle": 3,
            "metrics": {},
            "integration_result_dist": {
                "conv_rate": 0.1, "total_claims": 20, "resolved": 2,
                "no_source_gu": 5, "invalid_result": 3, "other": 10,
                "cycle_history": [],
            },
        }
        result = critique_node(state, today=date(2026, 4, 21))
        rules = result["current_critique"]["machine_rules"]
        bottleneck_rules = [r for r in rules if r.get("action") == "integration_bottleneck"]
        assert len(bottleneck_rules) == 1
        assert bottleneck_rules[0]["value"] == 0.1

    def test_threshold_boundary(self) -> None:
        """conv_rate = THRESHOLD → 처방 없음 (미만이어야 발동)."""
        dist = {"conv_rate": INTEGRATION_CONV_RATE_THRESHOLD, "total_claims": 10, "resolved": 3,
                "no_source_gu": 0, "invalid_result": 0, "other": 7}
        rxs = _analyze_failure_modes([], [], {"categories": []}, integration_result_dist=dist)
        assert not any(rx["type"] == "integration_bottleneck" for rx in rxs)


# ---------------------------------------------------------------------------
# S2-T2: KU stagnation trigger
# ---------------------------------------------------------------------------

def _make_added_history(ratios: list[float]) -> list[dict]:
    return [
        {"cycle": i + 1, "added": int(r * 10), "total_claims": 10, "added_ratio": r}
        for i, r in enumerate(ratios)
    ]


def _make_conflict_hold_history(holds: list[int]) -> list[dict]:
    return [{"cycle": i + 1, "conflict_hold": h} for i, h in enumerate(holds)]


def _make_condition_split_history(splits: list[int]) -> list[dict]:
    return [{"cycle": i + 1, "condition_split": s} for i, s in enumerate(splits)]


class TestKuStagnationTrigger:
    def test_added_low_trigger_fires(self) -> None:
        """최근 3c added_ratio < 0.3 → ku_stagnation:added_low 처방."""
        signals = {
            "added_history": _make_added_history([0.1, 0.2, 0.1]),
            "conflict_hold_history": _make_conflict_hold_history([0, 0, 0]),
            "condition_split_history": _make_condition_split_history([1, 1, 1]),
        }
        rxs = _analyze_failure_modes([], [], {"categories": []}, ku_stagnation_signals=signals)
        types = [rx["type"] for rx in rxs]
        assert "ku_stagnation:added_low" in types

    def test_added_low_trigger_does_not_fire_when_high(self) -> None:
        """최근 3c added_ratio >= 0.3 → ku_stagnation:added_low 없음."""
        signals = {
            "added_history": _make_added_history([0.4, 0.5, 0.3]),
            "conflict_hold_history": _make_conflict_hold_history([0, 0, 0]),
            "condition_split_history": _make_condition_split_history([0, 0, 0]),
        }
        rxs = _analyze_failure_modes([], [], {"categories": []}, ku_stagnation_signals=signals)
        assert not any(rx["type"] == "ku_stagnation:added_low" for rx in rxs)

    def test_added_low_requires_3_cycles(self) -> None:
        """history < 3c → added_low 발동 안 함."""
        signals = {
            "added_history": _make_added_history([0.1, 0.1]),  # 2c만
            "conflict_hold_history": _make_conflict_hold_history([0, 0]),
            "condition_split_history": _make_condition_split_history([0, 0]),
        }
        rxs = _analyze_failure_modes([], [], {"categories": []}, ku_stagnation_signals=signals)
        assert not any(rx["type"] == "ku_stagnation:added_low" for rx in rxs)

    def test_conflict_rising_trigger_fires(self) -> None:
        """conflict_hold 증가 추세 → ku_stagnation:conflict_rising 처방."""
        signals = {
            "added_history": _make_added_history([0.5, 0.5]),
            "conflict_hold_history": _make_conflict_hold_history([1, 5]),  # 증가
            "condition_split_history": _make_condition_split_history([1, 1]),
        }
        rxs = _analyze_failure_modes([], [], {"categories": []}, ku_stagnation_signals=signals)
        assert any(rx["type"] == "ku_stagnation:conflict_rising" for rx in rxs)

    def test_conflict_rising_no_fire_when_flat(self) -> None:
        """conflict_hold 평탄 → conflict_rising 없음."""
        signals = {
            "added_history": _make_added_history([0.5, 0.5]),
            "conflict_hold_history": _make_conflict_hold_history([3, 3]),
            "condition_split_history": _make_condition_split_history([1, 1]),
        }
        rxs = _analyze_failure_modes([], [], {"categories": []}, ku_stagnation_signals=signals)
        assert not any(rx["type"] == "ku_stagnation:conflict_rising" for rx in rxs)

    def test_no_condition_split_trigger_fires(self) -> None:
        """최근 3c condition_split=0 → ku_stagnation:no_condition_split 처방."""
        signals = {
            "added_history": _make_added_history([0.5, 0.5, 0.5]),
            "conflict_hold_history": _make_conflict_hold_history([0, 0, 0]),
            "condition_split_history": _make_condition_split_history([0, 0, 0]),
        }
        rxs = _analyze_failure_modes([], [], {"categories": []}, ku_stagnation_signals=signals)
        assert any(rx["type"] == "ku_stagnation:no_condition_split" for rx in rxs)

    def test_no_condition_split_no_fire_when_present(self) -> None:
        """최근 3c 중 하나라도 condition_split > 0 → no_condition_split 없음."""
        signals = {
            "added_history": _make_added_history([0.5, 0.5, 0.5]),
            "conflict_hold_history": _make_conflict_hold_history([0, 0, 0]),
            "condition_split_history": _make_condition_split_history([0, 1, 0]),
        }
        rxs = _analyze_failure_modes([], [], {"categories": []}, ku_stagnation_signals=signals)
        assert not any(rx["type"] == "ku_stagnation:no_condition_split" for rx in rxs)

    def test_none_signals_no_stagnation_prescriptions(self) -> None:
        """ku_stagnation_signals=None → stagnation 처방 없음."""
        rxs = _analyze_failure_modes([], [], {"categories": []}, ku_stagnation_signals=None)
        stagnation = [rx for rx in rxs if rx["type"].startswith("ku_stagnation")]
        assert stagnation == []

    def test_multiple_triggers_can_fire_simultaneously(self) -> None:
        """여러 trigger 동시 발동 가능."""
        signals = {
            "added_history": _make_added_history([0.1, 0.1, 0.1]),  # added_low
            "conflict_hold_history": _make_conflict_hold_history([1, 5]),  # conflict_rising
            "condition_split_history": _make_condition_split_history([0, 0, 0]),  # no_condition_split
        }
        rxs = _analyze_failure_modes([], [], {"categories": []}, ku_stagnation_signals=signals)
        types = {rx["type"] for rx in rxs}
        assert "ku_stagnation:added_low" in types
        assert "ku_stagnation:no_condition_split" in types
