"""Tavily SearchProvider.

P3-A2: 기존 TavilySearchAdapter.search 를 SearchProvider 기반으로 이식.
fetch 는 FetchPipeline 으로 이관 — 여기서는 search 만 담당.
"""

from __future__ import annotations

import logging
from typing import Any

from src.adapters.providers.base import SearchProvider, SearchResult
from src.adapters.search_adapter import _retry_with_backoff
from src.config import SearchConfig

logger = logging.getLogger(__name__)


class TavilyProvider:
    """Tavily Search API 기반 SearchProvider."""

    provider_id: str = "tavily"

    def __init__(self, config: SearchConfig | None = None) -> None:
        if config is None:
            config = SearchConfig.from_env()

        from tavily import TavilyClient

        self._client = TavilyClient(api_key=config.api_key)
        self._default_max_results = config.max_results
        self._timeout = config.request_timeout
        self.search_calls: int = 0

    def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        """Tavily 검색 → SearchResult 리스트."""
        self.search_calls += 1
        k = max_results or self._default_max_results
        response = _retry_with_backoff(
            self._client.search,
            query=query,
            max_results=k,
            timeout=self._timeout,
        )
        results: list[SearchResult] = []
        for item in response.get("results", []):
            results.append(SearchResult(
                url=item.get("url", ""),
                title=item.get("title", ""),
                snippet=item.get("content", ""),
                score=float(item.get("score", 0.0)),
                provider_id=self.provider_id,
                trust_tier="primary",
            ))
        logger.debug(
            "tavily search #%d: %r → %d results",
            self.search_calls, query, len(results),
        )
        return results
