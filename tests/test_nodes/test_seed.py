"""test_seed — seed_node 단위 테스트.

bench/japan-travel skeleton + Seed KU로 Bootstrap GU 생성 검증.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from src.nodes.seed import (
    _build_field_matrix,
    _determine_expected_utility,
    _determine_gap_type,
    _determine_risk_level,
    _get_entities_by_category,
    _get_per_category_cap,
    seed_node,
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
def policies() -> dict:
    with open(BENCH / "policies.json", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 1단계: Field Matrix
# ---------------------------------------------------------------------------

class TestFieldMatrix:
    def test_japan_travel_slots(self, skeleton: dict) -> None:
        slots = _build_field_matrix(skeleton)
        # japan-travel: 35개 슬롯
        assert len(slots) == 35

    def test_wildcard_field_covers_all_categories(self, skeleton: dict) -> None:
        slots = _build_field_matrix(skeleton)
        # price는 "*" → 8개 카테고리 전부
        price_slots = [(c, f) for c, f in slots if f == "price"]
        assert len(price_slots) == 8

    def test_specific_field_categories(self, skeleton: dict) -> None:
        slots = _build_field_matrix(skeleton)
        hours_cats = {c for c, f in slots if f == "hours"}
        assert hours_cats == {"attraction", "dining"}


# ---------------------------------------------------------------------------
# 우선순위 산정
# ---------------------------------------------------------------------------

class TestPriority:
    def test_safety_is_critical(self) -> None:
        assert _determine_expected_utility("safety", "policy", "regulation") == "critical"

    def test_financial_price_is_high(self) -> None:
        assert _determine_expected_utility("financial", "price", "transport") == "high"

    def test_financial_other_is_medium(self) -> None:
        assert _determine_expected_utility("financial", "tips", "payment") == "medium"

    def test_convenience_core_is_medium(self) -> None:
        assert _determine_expected_utility("convenience", "how_to_use", "transport") == "medium"

    def test_convenience_non_core_is_low(self) -> None:
        assert _determine_expected_utility("convenience", "hours", "dining") == "low"

    def test_regulation_upgrade(self) -> None:
        # regulation 카테고리: convenience → policy (1단계 상향)
        risk = _determine_risk_level("regulation", "how_to_use")
        assert risk == "policy"

    def test_payment_price_stays_financial(self) -> None:
        risk = _determine_risk_level("payment", "price")
        assert risk == "financial"


# ---------------------------------------------------------------------------
# gap_type 판정
# ---------------------------------------------------------------------------

class TestGapType:
    def test_missing_when_no_ku(self) -> None:
        result = _determine_gap_type("dining", "hours", [], date(2026, 3, 4))
        assert result == "missing"

    def test_none_when_covered(self) -> None:
        kus = [{
            "entity_key": "japan-travel:dining:izakaya",
            "field": "hours",
            "status": "active",
            "confidence": 0.9,
            "observed_at": "2026-03-01",
            "validity": {"ttl_days": 365},
        }]
        result = _determine_gap_type("dining", "hours", kus, date(2026, 3, 4))
        assert result is None

    def test_uncertain_low_confidence(self) -> None:
        kus = [{
            "entity_key": "japan-travel:dining:izakaya",
            "field": "hours",
            "status": "active",
            "confidence": 0.5,
            "observed_at": "2026-03-01",
            "validity": {"ttl_days": 365},
        }]
        result = _determine_gap_type("dining", "hours", kus, date(2026, 3, 4))
        assert result == "uncertain"

    def test_conflicting_takes_priority(self) -> None:
        kus = [
            {
                "entity_key": "japan-travel:dining:izakaya",
                "field": "hours",
                "status": "disputed",
                "confidence": 0.5,
            },
            {
                "entity_key": "japan-travel:dining:ramen",
                "field": "hours",
                "status": "active",
                "confidence": 0.5,
                "observed_at": "2020-01-01",
                "validity": {"ttl_days": 30},
            },
        ]
        result = _determine_gap_type("dining", "hours", kus, date(2026, 3, 4))
        assert result == "conflicting"


# ---------------------------------------------------------------------------
# seed_node 통합 테스트
# ---------------------------------------------------------------------------

class TestSeedNode:
    def test_bootstrap_gu_count(
        self, skeleton: dict, kus: list[dict], policies: dict,
    ) -> None:
        state = {
            "domain_skeleton": skeleton,
            "knowledge_units": kus,
            "policies": policies,
        }
        with patch("src.nodes.seed.date") as mock_date:
            mock_date.today.return_value = date(2026, 3, 4)
            mock_date.fromisoformat = date.fromisoformat
            result = seed_node(state)

        gap_map = result["gap_map"]
        # Bootstrap GU >= 20
        assert len(gap_map) >= 20
        # Bootstrap GU <= 40
        assert len(gap_map) <= 40

    def test_all_categories_covered(
        self, skeleton: dict, kus: list[dict], policies: dict,
    ) -> None:
        state = {
            "domain_skeleton": skeleton,
            "knowledge_units": kus,
            "policies": policies,
        }
        result = seed_node(state)
        gap_map = result["gap_map"]

        categories = {c["slug"] for c in skeleton["categories"]}
        covered = set()
        for gu in gap_map:
            entity_key = gu["target"]["entity_key"]
            parts = entity_key.split(":")
            if len(parts) >= 2:
                covered.add(parts[1])

        assert categories == covered

    def test_critical_high_minimum(
        self, skeleton: dict, kus: list[dict], policies: dict,
    ) -> None:
        state = {
            "domain_skeleton": skeleton,
            "knowledge_units": kus,
            "policies": policies,
        }
        result = seed_node(state)
        gap_map = result["gap_map"]

        critical_high = sum(
            1 for gu in gap_map
            if gu["expected_utility"] in ("critical", "high")
        )
        assert critical_high >= 3

    def test_gu_ids_sequential(
        self, skeleton: dict, kus: list[dict], policies: dict,
    ) -> None:
        state = {
            "domain_skeleton": skeleton,
            "knowledge_units": kus,
            "policies": policies,
        }
        result = seed_node(state)
        gap_map = result["gap_map"]

        for i, gu in enumerate(gap_map, start=1):
            assert gu["gu_id"] == f"GU-{i:04d}"

    def test_all_have_resolution_criteria(
        self, skeleton: dict, kus: list[dict], policies: dict,
    ) -> None:
        state = {
            "domain_skeleton": skeleton,
            "knowledge_units": kus,
            "policies": policies,
        }
        result = seed_node(state)
        for gu in result["gap_map"]:
            assert "resolution_criteria" in gu
            assert len(gu["resolution_criteria"]) > 0

    def test_returns_cycle_and_metrics(
        self, skeleton: dict, kus: list[dict], policies: dict,
    ) -> None:
        state = {
            "domain_skeleton": skeleton,
            "knowledge_units": kus,
            "policies": policies,
        }
        result = seed_node(state)

        assert result["current_cycle"] == 1
        assert "metrics" in result
        assert result["metrics"]["phase"] == "seed"
        assert "rates" in result["metrics"]

    def test_priority_ordering(
        self, skeleton: dict, kus: list[dict], policies: dict,
    ) -> None:
        """GU가 우선순위 내림차순 정렬인지 확인."""
        state = {
            "domain_skeleton": skeleton,
            "knowledge_units": kus,
            "policies": policies,
        }
        result = seed_node(state)
        gap_map = result["gap_map"]

        utility_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        for i in range(len(gap_map) - 1):
            curr = utility_order[gap_map[i]["expected_utility"]]
            next_ = utility_order[gap_map[i + 1]["expected_utility"]]
            assert curr <= next_, (
                f"GU {gap_map[i]['gu_id']} ({gap_map[i]['expected_utility']}) "
                f"should come before GU {gap_map[i+1]['gu_id']} ({gap_map[i+1]['expected_utility']})"
            )

    def test_no_excluded_scope(
        self, skeleton: dict, kus: list[dict], policies: dict,
    ) -> None:
        state = {
            "domain_skeleton": skeleton,
            "knowledge_units": kus,
            "policies": policies,
        }
        result = seed_node(state)
        excludes = skeleton.get("scope_boundary", {}).get("excludes", [])
        for gu in result["gap_map"]:
            entity_key = gu["target"]["entity_key"]
            for excl in excludes:
                assert excl.lower() not in entity_key.lower()
