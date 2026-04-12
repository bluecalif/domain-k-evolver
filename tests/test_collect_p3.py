"""P3-D4: Collect 통합 테스트.

mixed provider + provenance e2e + entropy + cost degrade (S9).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.adapters.fetch_pipeline import FetchPipeline, FetchResult
from src.adapters.providers.base import SearchResult
from src.adapters.providers.curated_provider import CuratedProvider
from src.config import SearchConfig
from src.nodes.collect import (
    _domain_entropy,
    _fetch_phase,
    _provider_entropy,
    _search_phase,
    _shannon_entropy,
    collect_node,
)


def _gu_state(gu_ids: list[str]) -> dict:
    """테스트용 state 생성."""
    gap_map = [
        {
            "gu_id": gid,
            "status": "open",
            "target": {"entity_key": "d:cat:slug", "field": "info"},
            "expected_utility": "high",
        }
        for gid in gu_ids
    ]
    queries = {gid: [f"query for {gid}"] for gid in gu_ids}
    return {
        "gap_map": gap_map,
        "current_plan": {
            "target_gaps": gu_ids,
            "queries": queries,
            "budget": 20,
        },
        "current_mode": {"mode": "normal"},
    }


# ============================================================
# Mixed Provider 통합
# ============================================================

class TestCollectWithProviders:
    def test_providers_used_over_search_tool(self) -> None:
        """providers 가 있으면 레거시 search_tool 보다 우선."""
        mock_provider = MagicMock()
        mock_provider.provider_id = "mock"
        mock_provider.search.return_value = [
            SearchResult(url="http://mock.com/1", title="Mock 1", snippet="s1",
                         provider_id="mock", trust_tier="primary"),
        ]

        state = _gu_state(["GU-0001"])
        result = collect_node(state, providers=[mock_provider])

        assert len(result["current_claims"]) > 0
        mock_provider.search.assert_called()

    def test_multi_provider_claims(self) -> None:
        """여러 provider 에서 결과 수집."""
        prov1 = MagicMock()
        prov1.provider_id = "tavily"
        prov1.search.return_value = [
            SearchResult(url="http://a.com", title="A", snippet="s",
                         provider_id="tavily", trust_tier="primary"),
        ]
        prov2 = MagicMock()
        prov2.provider_id = "curated"
        prov2.search.return_value = [
            SearchResult(url="http://b.com", title="B", snippet="s",
                         provider_id="curated", trust_tier="primary"),
        ]

        state = _gu_state(["GU-0001"])
        result = collect_node(state, providers=[prov1, prov2])
        assert len(result["current_claims"]) == 2


# ============================================================
# Provenance E2E
# ============================================================

class TestProvenanceE2E:
    def test_provenance_fields_populated(self) -> None:
        """provider 경유 수집 시 provenance 7필드 존재."""
        mock_provider = MagicMock()
        mock_provider.provider_id = "tavily"
        mock_provider.search.return_value = [
            SearchResult(url="http://test.com/page", title="Test", snippet="s",
                         provider_id="tavily", trust_tier="primary"),
        ]

        state = _gu_state(["GU-0001"])
        result = collect_node(state, providers=[mock_provider])

        for claim in result["current_claims"]:
            prov = claim["provenance"]
            assert isinstance(prov, dict)
            assert "providers_used" in prov
            assert "domain" in prov
            assert "fetch_ok" in prov
            assert "fetch_depth" in prov
            assert "content_type" in prov
            assert "retrieved_at" in prov
            assert "trust_tier" in prov

    def test_provenance_domain_extracted(self) -> None:
        """provenance domain 이 URL 에서 추출됨."""
        mock_provider = MagicMock()
        mock_provider.provider_id = "tavily"
        mock_provider.search.return_value = [
            SearchResult(url="http://example.org/page", title="T", snippet="s",
                         provider_id="tavily"),
        ]

        state = _gu_state(["GU-0001"])
        result = collect_node(state, providers=[mock_provider])
        prov = result["current_claims"][0]["provenance"]
        assert prov["domain"] == "example.org"


# ============================================================
# Entropy 계산
# ============================================================

class TestEntropy:
    def test_shannon_entropy_uniform(self) -> None:
        """균등 분포 entropy."""
        ent = _shannon_entropy({"a": 10, "b": 10, "c": 10, "d": 10})
        assert abs(ent - 2.0) < 0.01  # log2(4) = 2.0

    def test_shannon_entropy_single(self) -> None:
        """단일 항목 entropy = 0."""
        assert _shannon_entropy({"a": 100}) == 0.0

    def test_shannon_entropy_empty(self) -> None:
        assert _shannon_entropy({}) == 0.0

    def test_domain_entropy_from_claims(self) -> None:
        """claim provenance 기반 domain entropy."""
        claims = [
            {"provenance": {"domain": "a.com", "providers_used": ["tavily"]}},
            {"provenance": {"domain": "b.com", "providers_used": ["tavily"]}},
            {"provenance": {"domain": "a.com", "providers_used": ["curated"]}},
        ]
        ent = _domain_entropy(claims)
        assert ent > 0  # 2 domains → entropy > 0

    def test_provider_entropy_from_claims(self) -> None:
        """claim provenance 기반 provider entropy."""
        claims = [
            {"provenance": {"domain": "a.com", "providers_used": ["tavily"]}},
            {"provenance": {"domain": "b.com", "providers_used": ["curated"]}},
        ]
        ent = _provider_entropy(claims)
        assert abs(ent - 1.0) < 0.01  # 2 providers uniform → log2(2) = 1.0


# ============================================================
# Search Phase
# ============================================================

class TestSearchPhase:
    def test_legacy_search_tool(self) -> None:
        """레거시 search_tool 로 SearchResult 변환."""
        mock_tool = MagicMock()
        mock_tool.search.return_value = [
            {"url": "http://a.com", "title": "A", "snippet": "s"},
        ]

        gu = {"gu_id": "GU-0001", "target": {"entity_key": "d:c:s", "field": "f"}}
        results = _search_phase(gu, ["q1"], search_tool=mock_tool)
        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].provider_id == "legacy"


# ============================================================
# Fetch Phase
# ============================================================

class TestFetchPhase:
    def test_no_pipeline_returns_empty(self) -> None:
        """fetch_pipeline=None 이면 빈 결과."""
        sr = [SearchResult(url="http://a.com", title="A", snippet="s")]
        results = _fetch_phase(sr, None)
        assert results == []

    def test_dedup_urls(self) -> None:
        """중복 URL 제거."""
        sr = [
            SearchResult(url="http://a.com", title="A", snippet="s"),
            SearchResult(url="http://a.com", title="A2", snippet="s2"),
            SearchResult(url="http://b.com", title="B", snippet="s"),
        ]
        pipeline = MagicMock()
        pipeline.fetch_many.return_value = [
            FetchResult(url="http://a.com", fetch_ok=True),
            FetchResult(url="http://b.com", fetch_ok=True),
        ]
        results = _fetch_phase(sr, pipeline, fetch_top_n=5)
        # fetch_many 에 중복 없이 2개만 전달
        call_args = pipeline.fetch_many.call_args
        assert len(call_args[0][0]) == 2

    def test_fetch_top_n_limit(self) -> None:
        """fetch_top_n 으로 URL 수 제한."""
        sr = [
            SearchResult(url=f"http://{i}.com", title=f"T{i}", snippet="s")
            for i in range(10)
        ]
        pipeline = MagicMock()
        pipeline.fetch_many.return_value = []
        _fetch_phase(sr, pipeline, fetch_top_n=2)
        call_args = pipeline.fetch_many.call_args
        assert len(call_args[0][0]) == 2
