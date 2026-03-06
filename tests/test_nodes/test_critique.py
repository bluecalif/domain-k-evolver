"""test_critique — critique_node 단위 테스트."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from src.nodes.critique import _analyze_failure_modes, _check_convergence, critique_node

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
        # bench에 disputed KU 1개 (KU-0007) → consistency 처방
        assert any(rx["type"] == "consistency" for rx in rxs)


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
