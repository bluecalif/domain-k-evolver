"""test_metrics — Task 1.5 Metrics 계산 유틸리티 단위 테스트.

bench/japan-travel Cycle 2 수치와 대조 검증.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from src.utils.metrics import (
    avg_confidence,
    assess_health,
    compute_axis_coverage,
    compute_deficit_ratios,
    compute_metrics,
    conflict_rate,
    evidence_rate,
    gap_resolution_rate,
    multi_evidence_rate,
    staleness_risk,
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


@pytest.fixture(scope="module")
def bench_metrics() -> dict:
    with open(BENCH / "metrics.json", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 개별 공식 테스트 (bench 데이터 대조)
# ---------------------------------------------------------------------------

class TestEvidenceRate:
    def test_bench_value(self, kus: list[dict]) -> None:
        assert evidence_rate(kus) == pytest.approx(1.0)

    def test_empty(self) -> None:
        assert evidence_rate([]) == 0.0

    def test_no_evidence(self) -> None:
        kus = [{"status": "active", "evidence_links": []}]
        assert evidence_rate(kus) == 0.0

    def test_ignores_deprecated(self) -> None:
        kus = [
            {"status": "active", "evidence_links": ["EU-1"]},
            {"status": "deprecated", "evidence_links": []},
        ]
        assert evidence_rate(kus) == 1.0


class TestMultiEvidenceRate:
    def test_bench_value(self, kus: list[dict]) -> None:
        # bench: 0.911 (= 82/90 active KU with >= 2 evidence)
        result = multi_evidence_rate(kus)
        assert result == pytest.approx(0.911, abs=0.01)

    def test_empty(self) -> None:
        assert multi_evidence_rate([]) == 0.0


class TestGapResolutionRate:
    def test_bench_value(self, gap_map: list[dict]) -> None:
        # bench: 0.844 — 81 resolved / (81 + 15 open) = 81/96
        result = gap_resolution_rate(gap_map)
        assert result == pytest.approx(0.844, abs=0.002)

    def test_fallback_without_cycle_start(self, gap_map: list[dict]) -> None:
        # 근사치: resolved / (open + resolved)
        result = gap_resolution_rate(gap_map)
        assert 0.0 < result < 1.0

    def test_empty(self) -> None:
        assert gap_resolution_rate([]) == 0.0


class TestConflictRate:
    def test_bench_value(self, kus: list[dict]) -> None:
        # bench: 0.000 (Phase 3 dispute resolution 이후 충돌 0)
        result = conflict_rate(kus)
        assert result == pytest.approx(0.000, abs=0.002)

    def test_no_disputes(self) -> None:
        kus = [{"status": "active"}, {"status": "active"}]
        assert conflict_rate(kus) == 0.0


class TestAvgConfidence:
    def test_bench_value(self, kus: list[dict]) -> None:
        # bench: 0.801 (Phase 3~4 이후 90 active KU)
        result = avg_confidence(kus)
        assert result == pytest.approx(0.801, abs=0.01)

    def test_empty(self) -> None:
        assert avg_confidence([]) == 0.0


class TestStalenessRisk:
    def test_bench_value(self, kus: list[dict]) -> None:
        # bench: 59 (2026-03-04 기준, 2024년 KU 59개가 TTL 180일 초과)
        result = staleness_risk(kus, today=date(2026, 3, 4))
        assert result == 59

    def test_expired_ku(self) -> None:
        kus = [{
            "status": "active",
            "observed_at": "2025-01-01",
            "validity": {"ttl_days": 30},
        }]
        assert staleness_risk(kus, today=date(2025, 3, 1)) == 1

    def test_not_expired(self) -> None:
        kus = [{
            "status": "active",
            "observed_at": "2026-03-01",
            "validity": {"ttl_days": 90},
        }]
        assert staleness_risk(kus, today=date(2026, 3, 4)) == 0


# ---------------------------------------------------------------------------
# compute_metrics 통합
# ---------------------------------------------------------------------------

class TestComputeMetrics:
    def test_bench_state(
        self, kus: list[dict], gap_map: list[dict], bench_metrics: dict,
    ) -> None:
        state = {"knowledge_units": kus, "gap_map": gap_map}
        result = compute_metrics(state, today=date(2026, 3, 4))

        # bench metrics.json은 flat 구조 (rates 키 없음)
        expected = bench_metrics.get("rates", bench_metrics)
        assert result["evidence_rate"] == pytest.approx(expected["evidence_rate"])
        assert result["conflict_rate"] == pytest.approx(expected["conflict_rate"], abs=0.002)
        assert result["avg_confidence"] == pytest.approx(expected["avg_confidence"], abs=0.01)
        assert result["staleness_risk"] == expected["staleness_risk"]

    def test_returns_all_keys(
        self, kus: list[dict], gap_map: list[dict],
    ) -> None:
        state = {"knowledge_units": kus, "gap_map": gap_map}
        result = compute_metrics(state, today=date(2026, 3, 4))
        expected_keys = {
            "evidence_rate", "multi_evidence_rate", "gap_resolution_rate",
            "conflict_rate", "avg_confidence", "staleness_risk",
        }
        assert set(result.keys()) == expected_keys


# ---------------------------------------------------------------------------
# assess_health
# ---------------------------------------------------------------------------

class TestAssessHealth:
    def test_bench_health(self, bench_metrics: dict) -> None:
        # bench metrics.json은 flat 구조 (rates 키 없음)
        rates = bench_metrics.get("rates", bench_metrics)
        result = assess_health(rates)

        assert result["evidence_rate"] == "healthy"       # 1.0 >= 0.95
        assert result["multi_evidence_rate"] == "healthy"  # 0.911 >= 0.50
        assert result["conflict_rate"] == "healthy"        # 0.0 <= 0.05
        assert result["avg_confidence"] == "caution"       # 0.801 < 0.85
        assert result["staleness_risk"] == "danger"        # 59 > 5

    def test_danger_values(self) -> None:
        metrics = {
            "evidence_rate": 0.5,
            "multi_evidence_rate": 0.1,
            "conflict_rate": 0.3,
            "avg_confidence": 0.5,
            "staleness_risk": 10,
        }
        result = assess_health(metrics)
        for name in metrics:
            assert result[name] == "danger"

    def test_caution_values(self) -> None:
        metrics = {
            "evidence_rate": 0.90,
            "multi_evidence_rate": 0.40,
            "conflict_rate": 0.10,
            "avg_confidence": 0.75,
            "staleness_risk": 2,
        }
        result = assess_health(metrics)
        for name in metrics:
            assert result[name] == "caution"


# ---------------------------------------------------------------------------
# Axis Coverage
# ---------------------------------------------------------------------------

class TestAxisCoverage:
    def test_bench_structure(
        self, gap_map: list[dict], skeleton: dict,
    ) -> None:
        result = compute_axis_coverage(gap_map, skeleton)

        # 4개 축 존재
        assert set(result.keys()) == {"category", "geography", "condition", "risk"}

        # category 축에 8개 anchor
        assert len(result["category"]) == 8

        # transport 카테고리에 GU 존재 확인
        transport = result["category"]["transport"]
        assert transport["open"] + transport["resolved"] > 0

    def test_category_counts(
        self, gap_map: list[dict], skeleton: dict,
    ) -> None:
        result = compute_axis_coverage(gap_map, skeleton)
        cat = result["category"]

        # 모든 GU가 entity_key에서 category를 추출 가능 → 합산 = 전체 GU 수
        total = sum(v["open"] + v["resolved"] for v in cat.values())
        assert total == len(gap_map)

    def test_risk_axis(
        self, gap_map: list[dict], skeleton: dict,
    ) -> None:
        result = compute_axis_coverage(gap_map, skeleton)
        risk = result["risk"]

        # risk_level 필드 기반이므로 전체 GU 수와 합산 일치
        total = sum(v["open"] + v["resolved"] for v in risk.values())
        assert total == len(gap_map)

    def test_critical_open(
        self, gap_map: list[dict], skeleton: dict,
    ) -> None:
        result = compute_axis_coverage(gap_map, skeleton)

        # critical_open은 open이면서 expected_utility가 critical/high인 것
        total_critical_open = sum(
            v["critical_open"]
            for axis in result.values()
            for v in axis.values()
        )
        expected = sum(
            1 for gu in gap_map
            if gu.get("status") == "open"
            and gu.get("expected_utility") in ("critical", "high")
        )
        # category 축 기준으로 확인
        cat_critical = sum(v["critical_open"] for v in result["category"].values())
        assert cat_critical == expected


# ---------------------------------------------------------------------------
# Deficit Ratios
# ---------------------------------------------------------------------------

class TestDeficitRatios:
    def test_bench_values(
        self, gap_map: list[dict], skeleton: dict,
    ) -> None:
        coverage = compute_axis_coverage(gap_map, skeleton)
        result = compute_deficit_ratios(coverage, skeleton)

        assert set(result.keys()) == {"category", "geography", "condition", "risk"}

        # category: 모든 8개 anchor에 GU가 있으므로 deficit = 0
        assert result["category"] == 0.0

        # risk: 모든 5개 anchor에 GU가 있으므로 deficit = 0
        assert result["risk"] == 0.0

    def test_full_deficit(self) -> None:
        """GU 없으면 deficit_ratio = 1.0."""
        coverage = {"category": {"a": {"open": 0, "resolved": 0}}}
        skeleton = {"axes": [{"name": "category", "anchors": ["a"]}]}
        result = compute_deficit_ratios(coverage, skeleton)
        assert result["category"] == 1.0

    def test_partial_deficit(self) -> None:
        coverage = {
            "geo": {
                "tokyo": {"open": 1, "resolved": 2},
                "osaka": {"open": 0, "resolved": 0},
            },
        }
        skeleton = {"axes": [{"name": "geo", "anchors": ["tokyo", "osaka"]}]}
        result = compute_deficit_ratios(coverage, skeleton)
        assert result["geo"] == pytest.approx(0.5)
