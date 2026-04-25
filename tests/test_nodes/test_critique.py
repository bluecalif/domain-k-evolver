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
    _detect_ku_stagnation,
    _generate_balance_gus,
    _generate_refresh_gus,
    critique_node,
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

    def test_generates_gus_for_underrepresented_category(self) -> None:
        kus = [
            {"ku_id": f"KU-{i}", "entity_key": f"test:transport:e{i}",
             "field": "price", "status": "active"}
            for i in range(8)
        ] + [
            {"ku_id": "KU-20", "entity_key": "test:dining:e20",
             "field": "price", "status": "active"},
        ]
        # transport=8 (ok), dining=1 (need 4), payment=0 (need 5)
        gus = _generate_balance_gus(kus, [], self._SKELETON, max_gu_id=0)
        assert len(gus) > 0
        triggers = {gu["trigger"] for gu in gus}
        assert triggers == {"E:category_balance"}
        # dining GUs (applicable fields: hours, price → min(4, 2)=2)
        dining_gus = [gu for gu in gus if "dining" in gu["target"]["entity_key"]]
        assert len(dining_gus) == 2
        # payment GUs (applicable fields: how_to_use, price → min(5, 2)=2)
        payment_gus = [gu for gu in gus if "payment" in gu["target"]["entity_key"]]
        assert len(payment_gus) == 2

    def test_no_gus_when_all_sufficient(self) -> None:
        kus = []
        for cat in ["transport", "dining", "payment"]:
            for i in range(6):
                kus.append({
                    "ku_id": f"KU-{cat}-{i}", "entity_key": f"test:{cat}:e{i}",
                    "field": "price", "status": "active",
                })
        gus = _generate_balance_gus(kus, [], self._SKELETON, max_gu_id=0)
        assert len(gus) == 0

    def test_category_specific_fields_prioritized(self) -> None:
        kus = [
            {"ku_id": "KU-1", "entity_key": "test:dining:e1",
             "field": "price", "status": "active"},
        ]
        gus = _generate_balance_gus(kus, [], self._SKELETON, max_gu_id=0)
        dining_gus = [gu for gu in gus if "dining" in gu["target"]["entity_key"]]
        # dining-specific 필드 (hours)가 먼저 나와야 함
        fields = [gu["target"]["field"] for gu in dining_gus]
        assert fields[0] == "hours"  # category-specific first

    def test_expansion_mode_jump(self) -> None:
        kus = []
        gus = _generate_balance_gus(kus, [], self._SKELETON, max_gu_id=0)
        for gu in gus:
            assert gu["expansion_mode"] == "jump"

    def test_critique_node_adds_balance_gus(self) -> None:
        kus = [
            {"ku_id": f"KU-{i}", "entity_key": f"test:transport:e{i}",
             "field": "price", "status": "active",
             "evidence_links": ["EU-1", "EU-2"], "confidence": 0.9,
             "observed_at": "2026-03-01", "validity": {"ttl_days": 180}}
            for i in range(8)
        ]
        state = {
            "knowledge_units": kus,
            "gap_map": [],
            "domain_skeleton": self._SKELETON,
            "current_cycle": 1,
            "metrics": {"rates": {}},
        }
        result = critique_node(state, today=date(2026, 3, 7))
        assert "gap_map" in result
        balance = [gu for gu in result["gap_map"] if gu.get("trigger") == "E:category_balance"]
        assert len(balance) > 0


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


# ============================================================
# S2-T2: _detect_ku_stagnation L1 테스트
# ============================================================

def _make_dist_entry(cycle: int, added_ratio: float, condition_split: int = 0) -> dict:
    total = 10
    added = round(added_ratio * total)
    return {
        "cycle": cycle,
        "total_claims": total,
        "added": added,
        "conflict_hold": 0,
        "condition_split": condition_split,
        "resolved": added,
        "conv_rate": added_ratio,
        "added_ratio": added_ratio,
    }


class TestKuStagnation:
    """S2-T2: _detect_ku_stagnation — 3-cycle window 정체 감지."""

    def test_no_signal_insufficient_window(self) -> None:
        """2-cycle 미만 → 신호 없음 (3-cycle 완성 전)."""
        dist = [_make_dist_entry(1, 0.1), _make_dist_entry(2, 0.1)]
        _, signals, _ = _detect_ku_stagnation(dist, [], 1)
        assert signals == []

    def test_integration_added_low_signal(self) -> None:
        """3-cycle added_ratio < 0.3 → integration_added_low 신호."""
        dist = [
            _make_dist_entry(1, 0.1, condition_split=1),  # condition_split>0 → adjacent_yield_low 미발생
            _make_dist_entry(2, 0.2, condition_split=1),
            _make_dist_entry(3, 0.15, condition_split=1),
        ]
        prescriptions, signals, rx_counter = _detect_ku_stagnation(dist, [], 1)
        assert "integration_added_low" in signals
        assert any(p.get("rx_subtype") == "integration_added_low" for p in prescriptions)
        assert rx_counter == 2

    def test_adjacent_yield_low_signal(self) -> None:
        """3-cycle condition_split=0 → adjacent_yield_low 신호."""
        dist = [
            _make_dist_entry(1, 0.5, condition_split=0),
            _make_dist_entry(2, 0.5, condition_split=0),
            _make_dist_entry(3, 0.5, condition_split=0),
        ]
        _, signals, _ = _detect_ku_stagnation(dist, [], 1)
        assert "adjacent_yield_low" in signals

    def test_no_signal_normal_added_ratio(self) -> None:
        """added_ratio >= 0.3 → integration_added_low 신호 없음."""
        dist = [
            _make_dist_entry(1, 0.4),
            _make_dist_entry(2, 0.35),
            _make_dist_entry(3, 0.5),
        ]
        _, signals, _ = _detect_ku_stagnation(dist, [], 1)
        assert "integration_added_low" not in signals

    def test_both_signals_combined(self) -> None:
        """added_ratio 낮고 condition_split=0 → 두 신호 모두."""
        dist = [
            _make_dist_entry(1, 0.1, condition_split=0),
            _make_dist_entry(2, 0.1, condition_split=0),
            _make_dist_entry(3, 0.1, condition_split=0),
        ]
        _, signals, _ = _detect_ku_stagnation(dist, [], 1)
        assert "integration_added_low" in signals
        assert "adjacent_yield_low" in signals

    def test_window_uses_last_3(self) -> None:
        """5-cycle dist에서 마지막 3개만 사용 (앞 2개는 낮아도 뒤 3개 정상이면 신호 없음)."""
        dist = [
            _make_dist_entry(1, 0.05),  # 낮음 (무시)
            _make_dist_entry(2, 0.05),  # 낮음 (무시)
            _make_dist_entry(3, 0.4),
            _make_dist_entry(4, 0.5),
            _make_dist_entry(5, 0.6),
        ]
        _, signals, _ = _detect_ku_stagnation(dist, [], 1)
        assert "integration_added_low" not in signals

    def test_ku_stagnation_signals_in_critique_output(self) -> None:
        """critique_node 반환에 ku_stagnation_signals 필드 포함."""
        from tests.conftest import make_minimal_state
        state = make_minimal_state(
            integration_result_dist=[
                _make_dist_entry(1, 0.1, 0),
                _make_dist_entry(2, 0.1, 0),
                _make_dist_entry(3, 0.1, 0),
            ],
        )
        result = critique_node(state)
        assert "ku_stagnation_signals" in result
        assert isinstance(result["ku_stagnation_signals"], list)
