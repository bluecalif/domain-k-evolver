"""Tests for reach_ledger (SI-P4 Stage E, E3)."""
from __future__ import annotations

import pytest

from src.utils.reach_ledger import (
    build_ledger_snapshot,
    distinct_domains_per_100ku,
    extract_domains,
    extract_tlds,
    is_reach_degraded,
)


def _ku(entity_key: str, domain: str, status: str = "active") -> dict:
    return {
        "ku_id": f"KU-{entity_key}",
        "entity_key": entity_key,
        "field": "info",
        "value": "v",
        "status": status,
        "provenance": {"provider": "tavily", "domain": domain},
    }


class TestExtractDomains:
    def test_basic(self):
        kus = [_ku("a", "example.com"), _ku("b", "foo.jp"), _ku("c", "example.com")]
        assert extract_domains(kus) == {"example.com", "foo.jp"}

    def test_empty_provenance(self):
        kus = [{"ku_id": "KU-1", "provenance": None}]
        assert extract_domains(kus) == set()

    def test_no_provenance_key(self):
        kus = [{"ku_id": "KU-1"}]
        assert extract_domains(kus) == set()


class TestExtractTlds:
    def test_basic(self):
        domains = {"example.com", "foo.jp", "bar.co.kr"}
        tlds = extract_tlds(domains)
        assert "com" in tlds
        assert "jp" in tlds
        assert "kr" in tlds

    def test_empty(self):
        assert extract_tlds(set()) == set()


class TestDistinctDomainsper100ku:
    def test_basic(self):
        kus = [_ku(f"a:{i}", f"d{i}.com") for i in range(10)]
        # 10 unique domains / 10 KU * 100 = 100
        assert distinct_domains_per_100ku(kus) == 100.0

    def test_duplicates(self):
        kus = [_ku(f"a:{i}", "same.com") for i in range(10)]
        # 1 domain / 10 KU * 100 = 10
        assert distinct_domains_per_100ku(kus) == 10.0

    def test_excludes_inactive(self):
        kus = [
            _ku("a", "d1.com", status="active"),
            _ku("b", "d2.com", status="disputed"),
            _ku("c", "d3.com", status="active"),
        ]
        # 2 active, 2 unique domains among active → 100.0
        result = distinct_domains_per_100ku(kus)
        assert result == 100.0

    def test_empty(self):
        assert distinct_domains_per_100ku([]) == 0.0


class TestBuildLedgerSnapshot:
    def test_basic(self):
        kus = [
            _ku("a", "example.com"),
            _ku("b", "foo.jp"),
            _ku("c", "example.com"),
        ]
        snap = build_ledger_snapshot(kus, cycle=5)
        assert snap["cycle"] == 5
        assert snap["distinct_domains"] == 2
        assert snap["distinct_tlds"] == 2  # com, jp
        assert snap["active_ku_count"] == 3
        assert snap["domains_per_100ku"] == pytest.approx(66.67, abs=0.01)
        assert sorted(snap["domains"]) == ["example.com", "foo.jp"]

    def test_empty_kus(self):
        snap = build_ledger_snapshot([], cycle=0)
        assert snap["distinct_domains"] == 0
        assert snap["domains_per_100ku"] == 0.0

    def test_inactive_excluded(self):
        kus = [
            _ku("a", "d1.com", status="active"),
            _ku("b", "d2.com", status="disputed"),
        ]
        snap = build_ledger_snapshot(kus, cycle=1)
        assert snap["active_ku_count"] == 1
        assert snap["distinct_domains"] == 1


class TestIsReachDegraded:
    def test_degraded_below_floor(self):
        history = [
            {"domains_per_100ku": 10.0},
            {"domains_per_100ku": 12.0},
            {"domains_per_100ku": 8.0},
        ]
        degraded, reason = is_reach_degraded(history, floor=15, window=3)
        assert degraded is True
        assert "degraded" in reason

    def test_not_degraded_above_floor(self):
        history = [
            {"domains_per_100ku": 20.0},
            {"domains_per_100ku": 18.0},
            {"domains_per_100ku": 22.0},
        ]
        degraded, reason = is_reach_degraded(history, floor=15, window=3)
        assert degraded is False
        assert reason == "ok"

    def test_not_degraded_mixed(self):
        history = [
            {"domains_per_100ku": 10.0},
            {"domains_per_100ku": 20.0},  # above floor
            {"domains_per_100ku": 8.0},
        ]
        degraded, reason = is_reach_degraded(history, floor=15, window=3)
        assert degraded is False

    def test_insufficient_history(self):
        history = [{"domains_per_100ku": 5.0}]
        degraded, reason = is_reach_degraded(history, floor=15, window=3)
        assert degraded is False
        assert "insufficient_history" in reason

    def test_empty_history(self):
        degraded, reason = is_reach_degraded([], floor=15, window=3)
        assert degraded is False

    def test_exactly_at_floor_not_degraded(self):
        """floor 와 동일하면 degraded 아님 (< 비교)."""
        history = [
            {"domains_per_100ku": 15.0},
            {"domains_per_100ku": 15.0},
            {"domains_per_100ku": 15.0},
        ]
        degraded, _ = is_reach_degraded(history, floor=15, window=3)
        assert degraded is False

    def test_custom_window(self):
        history = [
            {"domains_per_100ku": 5.0},
            {"domains_per_100ku": 5.0},
        ]
        degraded, _ = is_reach_degraded(history, floor=15, window=2)
        assert degraded is True

    def test_longer_history_uses_last_window(self):
        """history 가 window 보다 길면 마지막 window 만 확인."""
        history = [
            {"domains_per_100ku": 5.0},  # old, below
            {"domains_per_100ku": 5.0},  # old, below
            {"domains_per_100ku": 20.0},  # recent, above
            {"domains_per_100ku": 20.0},
            {"domains_per_100ku": 20.0},
        ]
        degraded, _ = is_reach_degraded(history, floor=15, window=3)
        assert degraded is False
