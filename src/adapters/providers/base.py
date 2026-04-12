"""SearchProvider Protocol + SearchResult dataclass.

P3-A1: 모든 검색 provider 의 공통 인터페이스.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class SearchResult:
    """단일 검색 결과."""

    url: str
    title: str
    snippet: str
    score: float = 0.0
    provider_id: str = ""
    trust_tier: str = "secondary"  # "primary" | "secondary" | "tertiary"


@runtime_checkable
class SearchProvider(Protocol):
    """검색 provider 프로토콜.

    모든 provider 는 이 인터페이스를 구현해야 한다.
    fetch 는 포함하지 않음 — fetch 는 FetchPipeline 이 담당.
    """

    provider_id: str

    def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        """검색 실행 → SearchResult 리스트 반환."""
        ...
