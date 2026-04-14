"""search tools — WebSearch/WebFetch 래퍼.

collect_node에서 사용하는 검색 도구.
실제 실행 시 langchain 도구로 바인딩, 테스트 시 mock 교체.
"""

from __future__ import annotations

from typing import Any, Protocol


class SearchTool(Protocol):
    """검색 도구 인터페이스 (snippet-only)."""

    def search(self, query: str) -> list[dict]:
        """검색 실행 → [{url, title, snippet}, ...] 반환."""
        ...


class MockSearchTool:
    """테스트용 Mock 검색 도구."""

    def __init__(self, results: list[dict] | None = None) -> None:
        self.results = results or [
            {"url": "https://example.com/1", "title": "Result 1", "snippet": "Info about topic"},
            {"url": "https://example.com/2", "title": "Result 2", "snippet": "More info"},
        ]
        self.search_calls: list[str] = []

    def search(self, query: str) -> list[dict]:
        self.search_calls.append(query)
        return self.results
