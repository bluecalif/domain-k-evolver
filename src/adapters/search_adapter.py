"""SearchTool Adapter — Tavily Search 래퍼.

SearchTool Protocol을 구현하는 Real 검색 어댑터.
429/5xx 에러 시 지수 백오프 재시도 + 호출 카운터.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from src.config import SearchConfig
from src.tools.search import SearchTool

logger = logging.getLogger(__name__)

# Retry 설정
MAX_RETRIES = 3
BACKOFF_BASE = 1.0  # 초
BACKOFF_FACTOR = 2.0
RETRYABLE_EXCEPTIONS = (Exception,)  # Tavily는 범용 Exception 사용


def _retry_with_backoff(
    func: Any,
    *args: Any,
    max_retries: int = MAX_RETRIES,
    **kwargs: Any,
) -> Any:
    """지수 백오프 재시도."""
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            exc_str = str(exc).lower()
            is_retryable = bool(re.search(r"429|5\d\d|rate", exc_str))
            if not is_retryable or attempt == max_retries:
                raise
            wait = BACKOFF_BASE * (BACKOFF_FACTOR ** attempt)
            logger.warning(
                "Retry %d/%d after %.1fs — %s",
                attempt + 1, max_retries, wait, exc,
            )
            time.sleep(wait)
    raise last_exc  # type: ignore[misc]  # unreachable


class TavilySearchAdapter:
    """Tavily Search API를 SearchTool 프로토콜에 맞춰 래핑."""

    def __init__(self, config: SearchConfig | None = None) -> None:
        if config is None:
            config = SearchConfig.from_env()

        from tavily import TavilyClient

        self._client = TavilyClient(api_key=config.api_key)
        self._max_results = config.max_results
        self._timeout = config.request_timeout
        self.search_calls: int = 0
        self.fetch_calls: int = 0

    def search(self, query: str) -> list[dict]:
        """Tavily 검색 → [{url, title, snippet}, ...] 반환."""
        self.search_calls += 1
        response = _retry_with_backoff(
            self._client.search,
            query=query,
            max_results=self._max_results,
            timeout=self._timeout,
        )
        results = []
        for item in response.get("results", []):
            results.append({
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "snippet": item.get("content", ""),
            })
        logger.debug("search #%d: %r → %d results", self.search_calls, query, len(results))
        return results

    def fetch(self, url: str) -> str:
        """URL 내용 추출 (Tavily extract API 사용)."""
        self.fetch_calls += 1
        try:
            response = _retry_with_backoff(
                self._client.extract,
                urls=[url],
                timeout=self._timeout,
            )
            extracted = response.get("results", [])
            if extracted:
                return extracted[0].get("raw_content", "") or extracted[0].get("text", "")
        except Exception:
            logger.debug("fetch #%d failed: %s", self.fetch_calls, url)
        return ""

    @property
    def total_calls(self) -> int:
        return self.search_calls + self.fetch_calls


def create_search_tool(config: SearchConfig | None = None) -> SearchTool:
    """SearchTool 인스턴스 생성.

    Args:
        config: 검색 설정. None이면 환경변수에서 로드.

    Returns:
        SearchTool 프로토콜 구현체.
    """
    if config is None:
        config = SearchConfig.from_env()

    if config.provider == "tavily":
        return TavilySearchAdapter(config)

    raise ValueError(f"Unsupported search provider: {config.provider}")
