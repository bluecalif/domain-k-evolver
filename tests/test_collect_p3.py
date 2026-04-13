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
    _parse_claims_llm,
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
        pipeline.is_robots_allowed.return_value = True
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
        pipeline.is_robots_allowed.return_value = True
        pipeline.fetch_many.return_value = []
        _fetch_phase(sr, pipeline, fetch_top_n=2)
        call_args = pipeline.fetch_many.call_args
        assert len(call_args[0][0]) == 2

    def test_robots_prefilter_skips_blocked(self) -> None:
        """B-3: robots 차단 URL을 건너뛰고 대체 URL 선택."""
        sr = [
            SearchResult(url="http://reddit.com/r/japan", title="Reddit", snippet="s"),
            SearchResult(url="http://ok-site.com/page", title="OK", snippet="s"),
            SearchResult(url="http://facebook.com/travel", title="FB", snippet="s"),
            SearchResult(url="http://good.com/info", title="Good", snippet="s"),
        ]
        pipeline = MagicMock()
        pipeline.is_robots_allowed.side_effect = lambda url: url not in {
            "http://reddit.com/r/japan", "http://facebook.com/travel",
        }
        pipeline.fetch_many.return_value = [
            FetchResult(url="http://ok-site.com/page", fetch_ok=True),
            FetchResult(url="http://good.com/info", fetch_ok=True),
        ]

        results = _fetch_phase(sr, pipeline, fetch_top_n=2)

        # robots 차단 2건 + fetch 성공 2건 = 4건
        assert len(results) == 4
        blocked = [r for r in results if r.failure_reason == "robots_prefilter"]
        assert len(blocked) == 2
        assert {r.url for r in blocked} == {
            "http://reddit.com/r/japan", "http://facebook.com/travel",
        }

        fetched = [r for r in results if r.fetch_ok]
        assert len(fetched) == 2
        # fetch_many 에는 허용된 URL만 전달
        call_urls = pipeline.fetch_many.call_args[0][0]
        assert "http://reddit.com/r/japan" not in call_urls
        assert "http://facebook.com/travel" not in call_urls

    def test_robots_prefilter_all_blocked(self) -> None:
        """모든 URL이 robots 차단되면 빈 fetch + blocked 결과만."""
        sr = [
            SearchResult(url="http://reddit.com/1", title="R1", snippet="s"),
            SearchResult(url="http://reddit.com/2", title="R2", snippet="s"),
        ]
        pipeline = MagicMock()
        pipeline.is_robots_allowed.return_value = False

        results = _fetch_phase(sr, pipeline, fetch_top_n=3)

        assert len(results) == 2
        assert all(r.failure_reason == "robots_prefilter" for r in results)
        pipeline.fetch_many.assert_not_called()


# ============================================================
# _parse_claims_llm Happy-Path (D-120 핵심 검증)
# ============================================================

def _make_llm_response(claims_json: str) -> MagicMock:
    """mock LLM response 생성."""
    resp = MagicMock()
    resp.content = claims_json
    return resp


class TestParseClaimsLlmHappyPath:
    """_parse_claims_llm이 valid JSON 반환 시 정상 파싱 + provenance 주입."""

    def _gu(self, gu_id: str = "GU-0001") -> dict:
        return {
            "gu_id": gu_id,
            "target": {"entity_key": "japan-travel:transport:jr-pass", "field": "price"},
            "gap_type": "unknown",
            "resolution_criteria": "price info needed",
        }

    def _search_results(self) -> list[SearchResult]:
        return [
            SearchResult(
                url="http://jrpass.com/prices",
                title="JR Pass Prices 2026",
                snippet="7-day JR Pass costs 50,000 yen",
                provider_id="tavily",
                trust_tier="primary",
            ),
            SearchResult(
                url="http://japan-guide.com/jr",
                title="Japan Guide JR",
                snippet="JR Pass is available for 7, 14, 21 days",
                provider_id="tavily",
                trust_tier="primary",
            ),
        ]

    def _fetch_results(self) -> list[FetchResult]:
        return [
            FetchResult(
                url="http://jrpass.com/prices",
                fetch_ok=True,
                body="The 7-day JR Pass costs 50,000 yen as of 2026.",
                content_type="text/html",
                trust_tier="primary",
            ),
        ]

    def test_valid_json_array_parsed(self) -> None:
        """mock LLM이 valid JSON array 반환 → claims 정상 파싱."""
        llm_json = """[
            {
                "claim_id": "CL-0001-01",
                "entity_key": "japan-travel:transport:jr-pass",
                "field": "price",
                "value": "7-day JR Pass costs 50,000 yen",
                "source_gu_id": "GU-0001",
                "evidence": {
                    "eu_id": "EU-0001-01",
                    "url": "http://jrpass.com/prices",
                    "title": "JR Pass Prices 2026",
                    "snippet": "7-day JR Pass costs 50,000 yen",
                    "observed_at": "2026-04-13",
                    "credibility": 0.8
                },
                "risk_flag": false
            }
        ]"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_llm_response(llm_json)

        claims = _parse_claims_llm(
            self._gu(), self._search_results(), self._fetch_results(), mock_llm,
        )

        assert len(claims) == 1
        assert claims[0]["claim_id"] == "CL-0001-01"
        assert claims[0]["value"] == "7-day JR Pass costs 50,000 yen"
        assert claims[0]["field"] == "price"
        mock_llm.invoke.assert_called_once()

    def test_provenance_injected(self) -> None:
        """LLM 파싱 후 provenance 7필드가 주입됨."""
        llm_json = """[{
            "claim_id": "CL-0001-01",
            "entity_key": "japan-travel:transport:jr-pass",
            "field": "price",
            "value": "50,000 yen",
            "source_gu_id": "GU-0001",
            "evidence": {
                "eu_id": "EU-0001-01",
                "url": "http://jrpass.com/prices",
                "title": "JR Pass Prices",
                "snippet": "costs 50,000 yen",
                "observed_at": "2026-04-13",
                "credibility": 0.8
            },
            "risk_flag": false
        }]"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_llm_response(llm_json)

        claims = _parse_claims_llm(
            self._gu(), self._search_results(), self._fetch_results(), mock_llm,
        )

        prov = claims[0]["provenance"]
        assert isinstance(prov, dict)
        assert "providers_used" in prov
        assert "domain" in prov
        assert prov["domain"] == "jrpass.com"
        assert "fetch_ok" in prov
        assert prov["fetch_ok"] is True
        assert "fetch_depth" in prov
        assert "content_type" in prov
        assert "retrieved_at" in prov
        assert "trust_tier" in prov

    def test_multiple_claims_parsed(self) -> None:
        """LLM이 여러 claim 반환 시 모두 파싱."""
        llm_json = """[
            {"claim_id": "CL-0001-01", "entity_key": "e", "field": "f",
             "value": "claim1", "source_gu_id": "GU-0001",
             "evidence": {"eu_id": "EU-0001-01", "url": "http://jrpass.com/prices"},
             "risk_flag": false},
            {"claim_id": "CL-0001-02", "entity_key": "e", "field": "f",
             "value": "claim2", "source_gu_id": "GU-0001",
             "evidence": {"eu_id": "EU-0001-02", "url": "http://japan-guide.com/jr"},
             "risk_flag": false}
        ]"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_llm_response(llm_json)

        claims = _parse_claims_llm(
            self._gu(), self._search_results(), self._fetch_results(), mock_llm,
        )

        assert len(claims) == 2
        assert all("provenance" in c for c in claims)

    def test_single_object_wrapped_to_list(self) -> None:
        """LLM이 단일 object(배열 아님) 반환 시 list로 래핑."""
        llm_json = """{
            "claim_id": "CL-0001-01", "entity_key": "e", "field": "f",
            "value": "single claim", "source_gu_id": "GU-0001",
            "evidence": {"eu_id": "EU-0001-01", "url": "http://jrpass.com/prices"},
            "risk_flag": false
        }"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_llm_response(llm_json)

        claims = _parse_claims_llm(
            self._gu(), self._search_results(), self._fetch_results(), mock_llm,
        )

        assert len(claims) == 1
        assert claims[0]["value"] == "single claim"

    def test_markdown_fenced_json_parsed(self) -> None:
        """LLM이 markdown fence로 감싼 JSON도 정상 파싱."""
        llm_json = """Here are the claims:
```json
[{"claim_id": "CL-0001-01", "entity_key": "e", "field": "f",
  "value": "fenced claim", "source_gu_id": "GU-0001",
  "evidence": {"eu_id": "EU-0001-01", "url": "http://jrpass.com/prices"},
  "risk_flag": false}]
```"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_llm_response(llm_json)

        claims = _parse_claims_llm(
            self._gu(), self._search_results(), self._fetch_results(), mock_llm,
        )

        assert len(claims) == 1
        assert claims[0]["value"] == "fenced claim"

    def test_json_parse_failure_falls_back_to_deterministic(self) -> None:
        """LLM이 invalid JSON 반환 → deterministic fallback."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_llm_response("This is not JSON at all")

        claims = _parse_claims_llm(
            self._gu(), self._search_results(), self._fetch_results(), mock_llm,
        )

        # deterministic fallback은 search_results[:2]에서 claim 생성
        assert len(claims) > 0
        assert all("provenance" in c for c in claims)


# ============================================================
# Snippet Fallback: fetch 실패 시 snippet만으로 LLM claims
# ============================================================

class TestParseClaimsLlmSnippetFallback:
    """fetch 실패(빈 content) + snippet만 있을 때 LLM이 claims 생성."""

    def _gu(self) -> dict:
        return {
            "gu_id": "GU-0002",
            "target": {"entity_key": "japan-travel:food:ramen", "field": "types"},
            "gap_type": "unknown",
        }

    def _search_results_with_snippets(self) -> list[SearchResult]:
        return [
            SearchResult(
                url="http://ramen.com/types",
                title="Ramen Types",
                snippet="Shoyu, miso, tonkotsu, and shio are the main types",
                provider_id="tavily",
            ),
        ]

    def _empty_fetch_results(self) -> list[FetchResult]:
        """fetch 실패 — body 없음."""
        return [
            FetchResult(
                url="http://ramen.com/types",
                fetch_ok=False,
                failure_reason="timeout",
            ),
        ]

    def test_snippet_only_llm_produces_claims(self) -> None:
        """fetch 실패해도 snippet이 있으면 LLM이 claim 생성 가능."""
        llm_json = """[{
            "claim_id": "CL-0002-01",
            "entity_key": "japan-travel:food:ramen",
            "field": "types",
            "value": "Main ramen types: shoyu, miso, tonkotsu, shio",
            "source_gu_id": "GU-0002",
            "evidence": {
                "eu_id": "EU-0002-01",
                "url": "http://ramen.com/types",
                "title": "Ramen Types",
                "snippet": "Shoyu, miso, tonkotsu, and shio are the main types",
                "observed_at": "2026-04-13",
                "credibility": 0.7
            },
            "risk_flag": false
        }]"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_llm_response(llm_json)

        claims = _parse_claims_llm(
            self._gu(),
            self._search_results_with_snippets(),
            self._empty_fetch_results(),
            mock_llm,
        )

        assert len(claims) == 1
        assert claims[0]["value"] == "Main ramen types: shoyu, miso, tonkotsu, shio"

        # prompt에 snippet이 포함되었는지 검증
        call_args = mock_llm.invoke.call_args[0][0]
        assert "Shoyu, miso, tonkotsu" in call_args
        assert "(no content fetched" in call_args

    def test_no_fetch_no_snippet_llm_empty(self) -> None:
        """fetch 실패 + snippet도 없으면 LLM이 빈 배열 반환."""
        no_snippet_results = [
            SearchResult(url="http://empty.com", title="Empty", snippet="",
                         provider_id="tavily"),
        ]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_llm_response("[]")

        claims = _parse_claims_llm(
            self._gu(), no_snippet_results, self._empty_fetch_results(), mock_llm,
        )

        assert claims == []


# ============================================================
# collect_node LLM 통합 (providers + fetch_pipeline + llm)
# ============================================================

class TestCollectNodeLlmIntegration:
    """collect_node에 llm + providers + fetch_pipeline 전부 전달 → LLM parse 경로."""

    def test_full_pipeline_llm_parse(self) -> None:
        """providers → fetch → LLM parse 전체 경로 통합 테스트."""
        # Provider mock
        mock_provider = MagicMock()
        mock_provider.provider_id = "tavily"
        mock_provider.search.return_value = [
            SearchResult(
                url="http://example.com/page",
                title="Example Page",
                snippet="Important factual info here",
                provider_id="tavily",
                trust_tier="primary",
            ),
        ]

        # FetchPipeline mock
        mock_pipeline = MagicMock(spec=FetchPipeline)
        mock_pipeline.is_robots_allowed.return_value = True
        mock_pipeline.fetch_many.return_value = [
            FetchResult(
                url="http://example.com/page",
                fetch_ok=True,
                body="Full article content with detailed facts.",
                content_type="text/html",
                trust_tier="primary",
            ),
        ]

        # LLM mock
        llm_json = """[{
            "claim_id": "CL-0001-01",
            "entity_key": "d:cat:slug",
            "field": "info",
            "value": "Detailed factual claim from LLM",
            "source_gu_id": "GU-0001",
            "evidence": {
                "eu_id": "EU-0001-01",
                "url": "http://example.com/page",
                "title": "Example Page",
                "snippet": "Important factual info here",
                "observed_at": "2026-04-13",
                "credibility": 0.8
            },
            "risk_flag": false
        }]"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_llm_response(llm_json)

        state = _gu_state(["GU-0001"])
        result = collect_node(
            state,
            llm=mock_llm,
            providers=[mock_provider],
            fetch_pipeline=mock_pipeline,
        )

        # LLM이 호출되었는지 확인
        mock_llm.invoke.assert_called_once()

        # claims 생성 확인
        claims = result["current_claims"]
        assert len(claims) >= 1
        assert claims[0]["value"] == "Detailed factual claim from LLM"

        # provenance 주입 확인
        prov = claims[0]["provenance"]
        assert prov["domain"] == "example.com"
        assert prov["fetch_ok"] is True

        # fetch pipeline도 호출되었는지
        mock_pipeline.fetch_many.assert_called_once()

    def test_llm_none_uses_deterministic(self) -> None:
        """llm=None이면 deterministic parse 경로 사용."""
        mock_provider = MagicMock()
        mock_provider.provider_id = "tavily"
        mock_provider.search.return_value = [
            SearchResult(
                url="http://example.com/p",
                title="T",
                snippet="s",
                provider_id="tavily",
            ),
        ]

        state = _gu_state(["GU-0001"])
        result = collect_node(state, llm=None, providers=[mock_provider])

        # deterministic fallback claims
        assert len(result["current_claims"]) > 0
        for c in result["current_claims"]:
            assert "provenance" in c
