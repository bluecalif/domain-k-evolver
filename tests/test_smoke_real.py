"""Task 2.1 Smoke Test: Real API 1회 호출 검증.

pytest -m real 로 실행. 기본 pytest 실행 시 스킵됨.
"""

import os

import pytest

real = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY") or not os.environ.get("TAVILY_API_KEY"),
    reason="Real API keys not set (OPENAI_API_KEY, TAVILY_API_KEY)",
)


@real
def test_openai_smoke():
    """OpenAI API 1회 호출 — 응답이 비어있지 않은지 확인."""
    from src.adapters.llm_adapter import create_llm
    from src.config import LLMConfig

    config = LLMConfig.from_env()
    llm = create_llm(config)
    response = llm.invoke("Say 'hello' in one word.")
    assert response.content
    assert len(response.content) > 0


@real
def test_tavily_smoke():
    """Tavily Search API 1회 호출 — 결과가 비어있지 않은지 확인."""
    from src.adapters.search_adapter import create_search_tool
    from src.config import SearchConfig

    config = SearchConfig.from_env()
    tool = create_search_tool(config)
    results = tool.search("Japan Rail Pass 2025")
    assert isinstance(results, list)
    assert len(results) > 0
    assert "url" in results[0]


@real
def test_config_validate_api_keys():
    """API 키 검증 — 환경변수 설정 시 에러 없이 통과."""
    from src.config import EvolverConfig

    config = EvolverConfig.from_env()
    config.validate_api_keys()


def test_config_validate_missing_openai_key():
    """API 키 미설정 시 ValueError."""
    from src.config import EvolverConfig, LLMConfig, SearchConfig

    config = EvolverConfig(
        llm=LLMConfig(api_key=""),
        search=SearchConfig(api_key="tvly-test"),
    )
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        config.validate_api_keys()


def test_config_validate_missing_tavily_key():
    """Tavily 키 미설정 시 ValueError."""
    from src.config import EvolverConfig, LLMConfig, SearchConfig

    config = EvolverConfig(
        llm=LLMConfig(api_key="sk-test"),
        search=SearchConfig(api_key=""),
    )
    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        config.validate_api_keys()
