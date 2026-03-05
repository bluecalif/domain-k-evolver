"""Task 2.3 테스트: Config 환경 설정."""

import os

import pytest

from src.config import EvolverConfig, LLMConfig, OrchestratorConfig, SearchConfig


class TestLLMConfig:
    def test_defaults(self):
        cfg = LLMConfig()
        assert cfg.provider == "openai"
        assert cfg.model == "gpt-4.1-mini"
        assert cfg.temperature == 0.2
        assert cfg.max_tokens == 4096

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
        monkeypatch.setenv("EVOLVER_LLM_MODEL", "gpt-4o")
        monkeypatch.setenv("EVOLVER_LLM_TEMPERATURE", "0.5")
        cfg = LLMConfig.from_env()
        assert cfg.api_key == "sk-test-123"
        assert cfg.model == "gpt-4o"
        assert cfg.temperature == 0.5

    def test_frozen(self):
        cfg = LLMConfig()
        with pytest.raises(AttributeError):
            cfg.model = "other"


class TestSearchConfig:
    def test_defaults(self):
        cfg = SearchConfig()
        assert cfg.provider == "tavily"
        assert cfg.max_results == 5

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-456")
        monkeypatch.setenv("EVOLVER_SEARCH_MAX_RESULTS", "10")
        cfg = SearchConfig.from_env()
        assert cfg.api_key == "tvly-test-456"
        assert cfg.max_results == 10


class TestOrchestratorConfig:
    def test_defaults(self):
        cfg = OrchestratorConfig()
        assert cfg.max_cycles == 10
        assert cfg.snapshot_every == 1
        assert cfg.invariant_check is True
        assert cfg.stop_on_convergence is True

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("EVOLVER_MAX_CYCLES", "20")
        monkeypatch.setenv("EVOLVER_STOP_ON_CONVERGENCE", "false")
        cfg = OrchestratorConfig.from_env()
        assert cfg.max_cycles == 20
        assert cfg.stop_on_convergence is False


class TestEvolverConfig:
    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
        cfg = EvolverConfig.from_env()
        assert cfg.llm.api_key == "sk-test"
        assert cfg.search.api_key == "tvly-test"
        assert cfg.orchestrator.max_cycles == 10
