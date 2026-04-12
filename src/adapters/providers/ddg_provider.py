"""DuckDuckGo SearchProvider (optional fallback).

P3-A3: duckduckgo-search 패키지 사용. enable_ddg_fallback=True 일 때만 활성.
trust_tier="secondary".
"""

from __future__ import annotations

import logging

from src.adapters.providers.base import SearchResult

logger = logging.getLogger(__name__)


class DDGProvider:
    """DuckDuckGo 검색 fallback provider."""

    provider_id: str = "ddg"

    def __init__(self) -> None:
        self.search_calls: int = 0

    def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        """DDG 검색 → SearchResult 리스트.

        duckduckgo-search 가 설치되지 않았으면 빈 리스트 반환.
        """
        self.search_calls += 1
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.warning("duckduckgo-search 미설치 — DDG provider 비활성")
            return []

        results: list[SearchResult] = []
        try:
            with DDGS() as ddgs:
                for item in ddgs.text(query, max_results=max_results):
                    results.append(SearchResult(
                        url=item.get("href", ""),
                        title=item.get("title", ""),
                        snippet=item.get("body", ""),
                        score=0.0,
                        provider_id=self.provider_id,
                        trust_tier="secondary",
                    ))
        except Exception as exc:
            logger.warning("DDG search failed: %s", exc)
            return []

        logger.debug(
            "ddg search #%d: %r → %d results",
            self.search_calls, query, len(results),
        )
        return results
