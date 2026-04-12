"""P3-D3: FetchPipeline 테스트.

robots.txt 거부 (S8), content-type 필터, timeout, max_bytes, rate-limit.
"""

from __future__ import annotations

import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from io import BytesIO
from threading import Thread
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.fetch_pipeline import (
    DEFAULT_CONTENT_TYPES,
    DEFAULT_MAX_BYTES,
    FetchPipeline,
    FetchResult,
    _RateLimiter,
    _RobotsCache,
)


# ============================================================
# FetchResult
# ============================================================

class TestFetchResult:
    def test_defaults(self) -> None:
        fr = FetchResult(url="http://a.com", fetch_ok=True)
        assert fr.content_type == ""
        assert fr.bytes_read == 0
        assert fr.failure_reason == ""
        assert fr.body == ""

    def test_failure(self) -> None:
        fr = FetchResult(url="http://a.com", fetch_ok=False, failure_reason="robots")
        assert not fr.fetch_ok
        assert fr.failure_reason == "robots"


# ============================================================
# RobotsCache (S8)
# ============================================================

class TestRobotsCache:
    def test_allows_when_no_robots(self) -> None:
        """robots.txt 가져오기 실패 → 허용 (관례)."""
        cache = _RobotsCache()
        # robots.txt fetch 가 실패하도록 mock
        with patch("src.adapters.fetch_pipeline.RobotFileParser") as MockRP:
            rp = MagicMock()
            rp.can_fetch.return_value = True
            rp.read.side_effect = Exception("network error")
            MockRP.return_value = rp
            assert cache.is_allowed("http://example.com/page") is True

    def test_disallows_when_blocked(self) -> None:
        """robots.txt 에 의해 차단."""
        cache = _RobotsCache()
        with patch("src.adapters.fetch_pipeline.RobotFileParser") as MockRP:
            rp = MagicMock()
            rp.can_fetch.return_value = False
            MockRP.return_value = rp
            assert cache.is_allowed("http://blocked.com/secret") is False

    def test_cache_reuse(self) -> None:
        """같은 origin 에 대해 robots.txt 를 한 번만 fetch."""
        cache = _RobotsCache()
        with patch("src.adapters.fetch_pipeline.RobotFileParser") as MockRP:
            rp = MagicMock()
            rp.can_fetch.return_value = True
            MockRP.return_value = rp

            cache.is_allowed("http://a.com/page1")
            cache.is_allowed("http://a.com/page2")
            # RobotFileParser 는 한 번만 생성
            assert MockRP.call_count == 1


# ============================================================
# FetchPipeline — robots 거부 (S8)
# ============================================================

class TestIsRobotsAllowed:
    def test_allowed_when_robots_check_disabled(self) -> None:
        """robots_check=False → 항상 True."""
        pipeline = FetchPipeline(robots_check=False)
        assert pipeline.is_robots_allowed("http://blocked.com/secret") is True

    def test_delegates_to_robots_cache(self) -> None:
        """robots_check=True → _RobotsCache 에 위임."""
        pipeline = FetchPipeline(robots_check=True)
        with patch.object(pipeline._robots, "is_allowed", return_value=False):
            assert pipeline.is_robots_allowed("http://blocked.com/page") is False
        with patch.object(pipeline._robots, "is_allowed", return_value=True):
            assert pipeline.is_robots_allowed("http://ok.com/page") is True


class TestFetchPipelineRobots:
    def test_robots_blocked_returns_failure(self) -> None:
        """S8: robots.txt 거부 시 fetch_ok=False, failure_reason='robots'."""
        pipeline = FetchPipeline(robots_check=True)
        with patch.object(pipeline._robots, "is_allowed", return_value=False):
            results = pipeline.fetch_many(["http://blocked.com/page"])
        assert len(results) == 1
        assert results[0].fetch_ok is False
        assert results[0].failure_reason == "robots"

    def test_robots_disabled(self) -> None:
        """robots_check=False 면 robots 체크 스킵."""
        pipeline = FetchPipeline(robots_check=False)
        assert pipeline._robots is None


# ============================================================
# FetchPipeline — content-type 필터
# ============================================================

class TestFetchPipelineContentType:
    def test_rejects_non_html(self) -> None:
        """text/html 이 아닌 content-type 거부."""
        pipeline = FetchPipeline(robots_check=False)

        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "application/pdf"}
        mock_resp.read.return_value = b"PDF content"
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("src.adapters.fetch_pipeline.urlopen", return_value=mock_resp):
            results = pipeline.fetch_many(["http://a.com/doc.pdf"])

        assert len(results) == 1
        assert results[0].fetch_ok is False
        assert results[0].failure_reason == "content_type"
        assert results[0].content_type == "application/pdf"

    def test_accepts_html(self) -> None:
        """text/html 허용."""
        pipeline = FetchPipeline(robots_check=False)

        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_resp.read.return_value = b"<html>hello</html>"
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("src.adapters.fetch_pipeline.urlopen", return_value=mock_resp):
            results = pipeline.fetch_many(["http://a.com/page"])

        assert len(results) == 1
        assert results[0].fetch_ok is True
        assert results[0].content_type == "text/html"


# ============================================================
# FetchPipeline — max_bytes 절단
# ============================================================

class TestFetchPipelineMaxBytes:
    def test_truncates_large_content(self) -> None:
        """max_bytes 초과 시 절단."""
        pipeline = FetchPipeline(robots_check=False, max_bytes=100)

        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.read.return_value = b"x" * 100  # max_bytes 만큼만 읽음
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("src.adapters.fetch_pipeline.urlopen", return_value=mock_resp):
            results = pipeline.fetch_many(["http://a.com/big"])

        assert results[0].fetch_ok is True
        assert results[0].bytes_read == 100
        # read 에 max_bytes 가 전달되는지 확인
        mock_resp.read.assert_called_once_with(100)


# ============================================================
# FetchPipeline — error handling
# ============================================================

class TestFetchPipelineErrors:
    def test_network_error(self) -> None:
        """네트워크 에러 시 graceful failure."""
        pipeline = FetchPipeline(robots_check=False)

        with patch("src.adapters.fetch_pipeline.urlopen", side_effect=ConnectionError("refused")):
            results = pipeline.fetch_many(["http://down.com/page"])

        assert len(results) == 1
        assert results[0].fetch_ok is False
        assert "ConnectionError" in results[0].failure_reason

    def test_timeout_error(self) -> None:
        """타임아웃 시 graceful failure."""
        pipeline = FetchPipeline(robots_check=False, timeout=1)

        with patch("src.adapters.fetch_pipeline.urlopen", side_effect=TimeoutError("timeout")):
            results = pipeline.fetch_many(["http://slow.com/page"])

        assert results[0].fetch_ok is False
        assert "TimeoutError" in results[0].failure_reason


# ============================================================
# RateLimiter
# ============================================================

class TestRateLimiter:
    def test_rate_limit_enforced(self) -> None:
        """도메인별 rate-limit 간격 준수."""
        limiter = _RateLimiter(min_interval_s=0.1)
        start = time.monotonic()
        limiter.wait("a.com")
        limiter.wait("a.com")
        elapsed = time.monotonic() - start
        assert elapsed >= 0.09  # 최소 0.1s 대기

    def test_different_domains_no_wait(self) -> None:
        """다른 도메인은 대기 없음."""
        limiter = _RateLimiter(min_interval_s=10.0)
        start = time.monotonic()
        limiter.wait("a.com")
        limiter.wait("b.com")
        elapsed = time.monotonic() - start
        assert elapsed < 1.0  # 다른 도메인이므로 즉시


# ============================================================
# FetchPipeline — multiple URLs
# ============================================================

class TestFetchPipelineMultiple:
    def test_fetch_many_multiple(self) -> None:
        """여러 URL fetch."""
        pipeline = FetchPipeline(robots_check=False)

        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.read.return_value = b"<html>page</html>"
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("src.adapters.fetch_pipeline.urlopen", return_value=mock_resp):
            results = pipeline.fetch_many([
                "http://a.com/1", "http://b.com/2", "http://c.com/3",
            ])

        assert len(results) == 3
        assert all(r.fetch_ok for r in results)

    def test_trust_tier_propagated(self) -> None:
        """trust_tier 파라미터 전파."""
        pipeline = FetchPipeline(robots_check=False)

        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.read.return_value = b"<html></html>"
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("src.adapters.fetch_pipeline.urlopen", return_value=mock_resp):
            results = pipeline.fetch_many(["http://a.com/1"], trust_tier="primary")

        assert results[0].trust_tier == "primary"
