"""Task 2.1, 2.2, 2.6 테스트: LLM Adapter + Search Adapter + Retry/Counter."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.llm_adapter import LLMCallCounter, MockLLM, _MockResponse
from src.adapters.search_adapter import _retry_with_backoff
from src.config import LLMConfig, SearchConfig


class TestMockLLM:
    def test_single_response(self):
        llm = MockLLM(responses=['{"answer": "hello"}'])
        resp = llm.invoke("test prompt")
        assert resp.content == '{"answer": "hello"}'
        assert len(llm.calls) == 1
        assert llm.calls[0] == "test prompt"

    def test_multiple_responses_cycle(self):
        llm = MockLLM(responses=["first", "second"])
        assert llm.invoke("q1").content == "first"
        assert llm.invoke("q2").content == "second"
        assert llm.invoke("q3").content == "first"  # cycle back

    def test_default_response(self):
        llm = MockLLM()
        resp = llm.invoke("test")
        data = json.loads(resp.content)
        assert data == {"result": "mock"}

    def test_works_with_plan_node(self):
        """MockLLM이 plan_node의 llm 인터페이스와 호환되는지 확인."""
        plan = {"target_gaps": ["GU-0001"], "queries": {}, "budget": 4}
        llm = MockLLM(responses=[json.dumps(plan)])
        resp = llm.invoke("Generate plan")
        parsed = json.loads(resp.content)
        assert parsed["target_gaps"] == ["GU-0001"]

    def test_call_count(self):
        llm = MockLLM(responses=["a", "b"])
        llm.invoke("q1")
        llm.invoke("q2")
        llm.invoke("q3")
        assert llm.call_count == 3


class TestMockResponse:
    def test_content_attribute(self):
        resp = _MockResponse("test content")
        assert resp.content == "test content"


class TestLLMCallCounter:
    def test_counter_wraps_invoke(self):
        inner = MockLLM(responses=["hello", "world"])
        counter = LLMCallCounter(inner)
        r1 = counter.invoke("q1")
        r2 = counter.invoke("q2")
        assert r1.content == "hello"
        assert r2.content == "world"
        assert counter.call_count == 2

    def test_usage_tracking(self):
        """usage_metadata가 있으면 토큰 추적."""
        inner = MockLLM(responses=["ok"])
        counter = LLMCallCounter(inner)
        # MockResponse에 usage_metadata 주입
        resp = counter.invoke("test")
        # MockResponse엔 usage_metadata 없으므로 토큰은 0
        assert counter.total_tokens == 0

    def test_getattr_delegation(self):
        inner = MockLLM(responses=["x"])
        counter = LLMCallCounter(inner)
        # MockLLM의 responses 속성에 접근 가능
        assert counter.responses == ["x"]


class TestCreateLLM:
    def test_unsupported_provider(self):
        from src.adapters.llm_adapter import create_llm

        cfg = LLMConfig(provider="unsupported")
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            create_llm(cfg)


class TestCreateSearchTool:
    def test_unsupported_provider(self):
        from src.adapters.search_adapter import create_search_tool

        cfg = SearchConfig(provider="unsupported")
        with pytest.raises(ValueError, match="Unsupported search provider"):
            create_search_tool(cfg)


class TestRetryWithBackoff:
    def test_success_no_retry(self):
        func = MagicMock(return_value="ok")
        result = _retry_with_backoff(func, "arg1", max_retries=3)
        assert result == "ok"
        func.assert_called_once_with("arg1")

    @patch("src.adapters.search_adapter.time.sleep")
    def test_retry_on_429(self, mock_sleep):
        func = MagicMock(side_effect=[
            Exception("429 Too Many Requests"),
            Exception("429 rate limit"),
            "success",
        ])
        result = _retry_with_backoff(func, max_retries=3)
        assert result == "success"
        assert func.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("src.adapters.search_adapter.time.sleep")
    def test_raises_after_max_retries(self, mock_sleep):
        func = MagicMock(side_effect=Exception("429 rate limit"))
        with pytest.raises(Exception, match="429"):
            _retry_with_backoff(func, max_retries=2)
        assert func.call_count == 3  # initial + 2 retries

    def test_non_retryable_raises_immediately(self):
        func = MagicMock(side_effect=ValueError("bad input"))
        with pytest.raises(ValueError, match="bad input"):
            _retry_with_backoff(func, max_retries=3)
        func.assert_called_once()


class TestTavilySearchAdapterCounter:
    """TavilySearchAdapter 호출 카운터 테스트 (Tavily 없이 mock)."""

    def test_search_counter(self):
        from src.adapters.search_adapter import TavilySearchAdapter

        adapter = TavilySearchAdapter.__new__(TavilySearchAdapter)
        adapter.search_calls = 0
        adapter._max_results = 5
        adapter._timeout = 30

        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [{"url": "http://a.com", "title": "A", "content": "snippet"}]
        }
        adapter._client = mock_client

        results = adapter.search("test query")
        assert len(results) == 1
        assert adapter.search_calls == 1

        adapter.search("another query")
        assert adapter.search_calls == 2
        assert adapter.total_calls == 2


# ============================================================
# P0-B9: search_adapter 추가 — 504/503 retry, timeout 전달
# ============================================================

class TestRetryOn5xx:
    """P0-B9: 5xx 에러도 retry 대상 (정규표현식 5\\d\\d)."""

    @patch("src.adapters.search_adapter.time.sleep")
    def test_retry_on_504(self, mock_sleep):
        func = MagicMock(side_effect=[
            Exception("504 Gateway Timeout"),
            "ok",
        ])
        result = _retry_with_backoff(func, max_retries=3)
        assert result == "ok"
        assert func.call_count == 2

    @patch("src.adapters.search_adapter.time.sleep")
    def test_retry_on_503(self, mock_sleep):
        func = MagicMock(side_effect=[
            Exception("503 Service Unavailable"),
            Exception("503 still unavailable"),
            "recovered",
        ])
        result = _retry_with_backoff(func, max_retries=3)
        assert result == "recovered"
        assert func.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("src.adapters.search_adapter.time.sleep")
    def test_retry_on_500(self, mock_sleep):
        func = MagicMock(side_effect=[
            Exception("500 Internal Server Error"),
            "ok",
        ])
        result = _retry_with_backoff(func, max_retries=3)
        assert result == "ok"

    @patch("src.adapters.search_adapter.time.sleep")
    def test_5xx_exhausts_retries(self, mock_sleep):
        func = MagicMock(side_effect=Exception("504 Gateway Timeout"))
        with pytest.raises(Exception, match="504"):
            _retry_with_backoff(func, max_retries=2)
        assert func.call_count == 3  # initial + 2 retries


class TestTavilyTimeoutPropagation:
    """P0-B4: Tavily search/extract 호출 시 timeout 명시 전달."""

    def test_search_passes_timeout_to_client(self):
        from src.adapters.search_adapter import TavilySearchAdapter

        adapter = TavilySearchAdapter.__new__(TavilySearchAdapter)
        adapter.search_calls = 0
        adapter._max_results = 5
        adapter._timeout = 15  # 커스텀 timeout

        mock_client = MagicMock()
        mock_client.search.return_value = {"results": []}
        adapter._client = mock_client

        adapter.search("q")
        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs.get("timeout") == 15


# ============================================================
# create_search_tool
# ============================================================

class TestCreateSearchTool:
    def test_unsupported_provider_raises(self):
        from src.adapters.search_adapter import create_search_tool
        cfg = SearchConfig(provider="unsupported")
        with pytest.raises(ValueError, match="Unsupported"):
            create_search_tool(cfg)
