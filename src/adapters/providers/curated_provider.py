"""Curated Source Provider.

P3-A4: skeleton 의 preferred_sources 에서 axis_tags/category 매칭 URL 반환.
검색을 수행하지 않음 — 사전 정의된 신뢰 소스 목록 기반.
trust_tier="primary".
"""

from __future__ import annotations

import logging
from typing import Any

from src.adapters.providers.base import SearchResult

logger = logging.getLogger(__name__)


class CuratedProvider:
    """Skeleton preferred_sources 기반 provider."""

    provider_id: str = "curated"

    def __init__(self, preferred_sources: list[dict] | None = None) -> None:
        """
        Args:
            preferred_sources: skeleton 의 preferred_sources 리스트.
                각 항목: {"url": str, "title": str, "categories": [str], "axis_tags": {str: str}}
                None 이면 빈 목록 — 결과 0건 반환 (fallback safe).
        """
        self._sources = preferred_sources or []
        self.search_calls: int = 0

    def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        """preferred_sources 에서 query 키워드 매칭 URL 반환.

        매칭 로직: query 토큰이 source 의 title/categories/url 에 포함되면 매칭.
        """
        self.search_calls += 1

        if not self._sources:
            return []

        query_tokens = set(query.lower().split())
        scored: list[tuple[float, dict]] = []

        for src in self._sources:
            score = _match_score(query_tokens, src)
            if score > 0:
                scored.append((score, src))

        scored.sort(key=lambda x: x[0], reverse=True)

        results: list[SearchResult] = []
        for score, src in scored[:max_results]:
            results.append(SearchResult(
                url=src.get("url", ""),
                title=src.get("title", ""),
                snippet=f"Curated source: {', '.join(src.get('categories', []))}",
                score=score,
                provider_id=self.provider_id,
                trust_tier="primary",
            ))

        logger.debug(
            "curated search #%d: %r → %d results (from %d sources)",
            self.search_calls, query, len(results), len(self._sources),
        )
        return results


def _match_score(query_tokens: set[str], source: dict) -> float:
    """query 토큰 vs source 메타데이터 매칭 점수 (0.0~1.0)."""
    if not query_tokens:
        return 0.0

    searchable = " ".join([
        source.get("title", ""),
        source.get("url", ""),
        " ".join(source.get("categories", [])),
        " ".join(str(v) for v in source.get("axis_tags", {}).values()),
    ]).lower()

    matched = sum(1 for t in query_tokens if t in searchable)
    return matched / len(query_tokens)
