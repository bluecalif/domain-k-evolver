"""Search Provider 플러그인 패키지.

P3-A: SearchProvider Protocol + Tavily/DDG/Curated 구현체.
"""

from src.adapters.providers.base import SearchProvider, SearchResult

__all__ = ["SearchProvider", "SearchResult"]
