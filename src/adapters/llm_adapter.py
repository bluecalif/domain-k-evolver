"""LLM Adapter — OpenAI GPT 래퍼.

build_graph(llm=...) 에 전달할 LLM 인스턴스 생성.
429/5xx 자동 재시도 (langchain max_retries) + 호출 카운터 래퍼.
"""

from __future__ import annotations

import logging
from typing import Any

from src.config import LLMConfig

logger = logging.getLogger(__name__)


class LLMCallCounter:
    """LLM 호출 카운터 래퍼.

    BaseChatModel을 감싸고, invoke 호출 횟수를 기록.
    """

    def __init__(self, llm: Any) -> None:
        self._llm = llm
        self.call_count: int = 0
        self.batch_call_count: int = 0
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0

    def invoke(self, prompt: str | list) -> Any:
        self.call_count += 1
        response = self._llm.invoke(prompt)
        usage = getattr(response, "usage_metadata", None)
        if usage:
            self.total_prompt_tokens += usage.get("input_tokens", 0)
            self.total_completion_tokens += usage.get("output_tokens", 0)
            logger.debug(
                "LLM call #%d: prompt=%d, completion=%d tokens",
                self.call_count,
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
            )
        return response

    def batch(self, prompts: list) -> list:
        """N개 프롬프트를 1회 batch API 호출. 실패 시 단발 invoke로 fallback."""
        if not prompts:
            return []
        try:
            responses = self._llm.batch(prompts)
            self.call_count += 1
            self.batch_call_count += 1
            for r in responses:
                usage = getattr(r, "usage_metadata", None)
                if usage:
                    self.total_prompt_tokens += usage.get("input_tokens", 0)
                    self.total_completion_tokens += usage.get("output_tokens", 0)
            logger.debug("LLM batch #%d: %d prompts → 1 call", self.batch_call_count, len(prompts))
            return responses
        except Exception as exc:
            logger.warning("LLM batch 실패 (%s) → 단발 invoke fallback", exc)
            return [self.invoke(p) for p in prompts]

    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens

    def __getattr__(self, name: str) -> Any:
        return getattr(self._llm, name)


def create_llm(config: LLMConfig | None = None, *, track_usage: bool = True) -> Any:
    """LLM 인스턴스 생성.

    Args:
        config: LLM 설정. None이면 환경변수에서 로드.
        track_usage: True이면 LLMCallCounter로 래핑하여 호출/토큰 추적.

    Returns:
        ChatOpenAI 인스턴스 (또는 LLMCallCounter 래퍼).
    """
    if config is None:
        config = LLMConfig.from_env()

    if config.provider == "openai":
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=config.api_key,
            max_retries=3,
            request_timeout=config.request_timeout,
        )
        if track_usage:
            return LLMCallCounter(llm)
        return llm

    raise ValueError(f"Unsupported LLM provider: {config.provider}")


class MockLLM:
    """테스트용 Mock LLM.

    지정된 응답을 순서대로 반환.
    """

    def __init__(self, responses: list[str] | None = None) -> None:
        self.responses = list(responses or ['{"result": "mock"}'])
        self._call_index = 0
        self.calls: list[str] = []
        self.call_count: int = 0

    def invoke(self, prompt: str | list) -> Any:
        self.calls.append(str(prompt))
        self.call_count += 1
        text = self.responses[self._call_index % len(self.responses)]
        self._call_index += 1
        return _MockResponse(text)

    def batch(self, prompts: list) -> list:
        return [self.invoke(p) for p in prompts]


class _MockResponse:
    """Mock LLM 응답 객체."""

    def __init__(self, content: str) -> None:
        self.content = content
