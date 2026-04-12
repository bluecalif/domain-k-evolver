"""FetchPipeline — Provider 무관 공용 HTTP fetch 계층.

P3-B: robots.txt 캐시 / content-type 필터 / max_bytes 절단 / 도메인별 rate-limit.
D-100: urllib.request 기반 (httpx 미도입).
D-101: robots.txt 캐시 = per-run in-memory.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)

# 기본값
DEFAULT_MAX_BYTES = 500_000  # 500KB
DEFAULT_TIMEOUT = 15  # seconds
DEFAULT_CONTENT_TYPES = frozenset({"text/html", "application/xhtml+xml"})
DEFAULT_USER_AGENT = "DomainKEvolver/1.0"
DEFAULT_RATE_LIMIT_S = 1.0  # 도메인당 최소 간격


@dataclass
class FetchResult:
    """단일 URL fetch 결과."""

    url: str
    fetch_ok: bool
    content_type: str = ""
    retrieved_at: str = ""
    bytes_read: int = 0
    trust_tier: str = "secondary"
    failure_reason: str = ""
    body: str = ""


class _RobotsCache:
    """Per-run in-memory robots.txt 캐시 (P3-B3, S8)."""

    def __init__(self, user_agent: str = DEFAULT_USER_AGENT) -> None:
        self._cache: dict[str, RobotFileParser] = {}
        self._user_agent = user_agent
        self._lock = threading.Lock()

    def is_allowed(self, url: str) -> bool:
        """url 에 대해 robots.txt 가 허용하는지 확인."""
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        with self._lock:
            if origin not in self._cache:
                rp = RobotFileParser()
                robots_url = f"{origin}/robots.txt"
                rp.set_url(robots_url)
                try:
                    rp.read()
                except Exception:
                    # robots.txt 가져오기 실패 → 허용 (관례)
                    rp.allow_all = True
                self._cache[origin] = rp

            rp = self._cache[origin]

        return rp.can_fetch(self._user_agent, url)


class _RateLimiter:
    """도메인별 최소 간격 rate-limiter (P3-B6)."""

    def __init__(self, min_interval_s: float = DEFAULT_RATE_LIMIT_S) -> None:
        self._min_interval = min_interval_s
        self._last_request: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait(self, domain: str) -> None:
        """필요 시 sleep 하여 도메인별 rate-limit 준수."""
        with self._lock:
            now = time.monotonic()
            last = self._last_request.get(domain, 0.0)
            elapsed = now - last
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_request[domain] = time.monotonic()


class FetchPipeline:
    """URL 목록을 fetch 하여 FetchResult 리스트 반환.

    robots.txt 체크 → content-type 필터 → max_bytes 절단 → rate-limit 적용.
    """

    def __init__(
        self,
        *,
        robots_check: bool = True,
        max_bytes: int = DEFAULT_MAX_BYTES,
        content_type_allowlist: frozenset[str] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        per_domain_min_interval_s: float = DEFAULT_RATE_LIMIT_S,
    ) -> None:
        self._robots_check = robots_check
        self._max_bytes = max_bytes
        self._content_types = content_type_allowlist or DEFAULT_CONTENT_TYPES
        self._timeout = timeout
        self._user_agent = user_agent
        self._robots = _RobotsCache(user_agent) if robots_check else None
        self._limiter = _RateLimiter(per_domain_min_interval_s)

    def fetch_many(
        self,
        urls: list[str],
        *,
        trust_tier: str = "secondary",
    ) -> list[FetchResult]:
        """URL 목록 순차 fetch → FetchResult 리스트."""
        results: list[FetchResult] = []
        for url in urls:
            results.append(self._fetch_one(url, trust_tier=trust_tier))
        return results

    def _fetch_one(self, url: str, *, trust_tier: str = "secondary") -> FetchResult:
        """단일 URL fetch."""
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1) robots.txt 체크 (S8)
        if self._robots and not self._robots.is_allowed(url):
            logger.info("robots.txt 거부: %s", url)
            return FetchResult(
                url=url, fetch_ok=False, retrieved_at=now_iso,
                trust_tier=trust_tier, failure_reason="robots",
            )

        # 2) rate-limit
        domain = urlparse(url).netloc
        self._limiter.wait(domain)

        # 3) HTTP fetch
        try:
            req = Request(url, headers={"User-Agent": self._user_agent})
            with urlopen(req, timeout=self._timeout) as resp:
                # 4) content-type 필터 (P3-B4)
                ct_raw = resp.headers.get("Content-Type", "")
                ct = ct_raw.split(";")[0].strip().lower()
                if ct not in self._content_types:
                    return FetchResult(
                        url=url, fetch_ok=False, content_type=ct,
                        retrieved_at=now_iso, trust_tier=trust_tier,
                        failure_reason="content_type",
                    )

                # 5) max_bytes 절단 (P3-B5)
                raw = resp.read(self._max_bytes)
                body = raw.decode("utf-8", errors="replace")

                return FetchResult(
                    url=url, fetch_ok=True, content_type=ct,
                    retrieved_at=now_iso, bytes_read=len(raw),
                    trust_tier=trust_tier, body=body,
                )

        except Exception as exc:
            logger.warning("fetch failed: %s — %s", url, exc)
            return FetchResult(
                url=url, fetch_ok=False, retrieved_at=now_iso,
                trust_tier=trust_tier, failure_reason=f"error:{type(exc).__name__}",
            )
