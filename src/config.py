"""Evolver 환경 설정.

API 키, 모델 파라미터, 실행 옵션을 환경변수에서 로드.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LLMConfig:
    """LLM 설정."""

    provider: str = "openai"
    model: str = "gpt-4.1-mini"
    temperature: float = 0.2
    max_tokens: int = 4096
    api_key: str = ""

    @classmethod
    def from_env(cls) -> LLMConfig:
        return cls(
            provider=os.environ.get("EVOLVER_LLM_PROVIDER", "openai"),
            model=os.environ.get("EVOLVER_LLM_MODEL", "gpt-4.1-mini"),
            temperature=float(os.environ.get("EVOLVER_LLM_TEMPERATURE", "0.2")),
            max_tokens=int(os.environ.get("EVOLVER_LLM_MAX_TOKENS", "4096")),
            api_key=os.environ.get("OPENAI_API_KEY", ""),
        )


@dataclass(frozen=True)
class SearchConfig:
    """검색 도구 설정."""

    provider: str = "tavily"
    api_key: str = ""
    max_results: int = 5

    @classmethod
    def from_env(cls) -> SearchConfig:
        return cls(
            provider=os.environ.get("EVOLVER_SEARCH_PROVIDER", "tavily"),
            api_key=os.environ.get("TAVILY_API_KEY", ""),
            max_results=int(os.environ.get("EVOLVER_SEARCH_MAX_RESULTS", "5")),
        )


@dataclass(frozen=True)
class OrchestratorConfig:
    """Orchestrator 실행 설정."""

    max_cycles: int = 10
    snapshot_every: int = 1
    invariant_check: bool = True
    stop_on_convergence: bool = True
    bench_domain: str = "japan-travel"
    bench_path: str = "bench"

    @classmethod
    def from_env(cls) -> OrchestratorConfig:
        return cls(
            max_cycles=int(os.environ.get("EVOLVER_MAX_CYCLES", "10")),
            snapshot_every=int(os.environ.get("EVOLVER_SNAPSHOT_EVERY", "1")),
            invariant_check=os.environ.get("EVOLVER_INVARIANT_CHECK", "true").lower() == "true",
            stop_on_convergence=os.environ.get("EVOLVER_STOP_ON_CONVERGENCE", "true").lower() == "true",
            bench_domain=os.environ.get("EVOLVER_BENCH_DOMAIN", "japan-travel"),
            bench_path=os.environ.get("EVOLVER_BENCH_PATH", "bench"),
        )


@dataclass(frozen=True)
class EvolverConfig:
    """전체 설정 통합."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    orchestrator: OrchestratorConfig = field(default_factory=OrchestratorConfig)

    @classmethod
    def from_env(cls) -> EvolverConfig:
        return cls(
            llm=LLMConfig.from_env(),
            search=SearchConfig.from_env(),
            orchestrator=OrchestratorConfig.from_env(),
        )

    def validate_api_keys(self) -> None:
        """API 키가 설정되었는지 검증. 빈 문자열이면 ValueError."""
        if not self.llm.api_key:
            raise ValueError(
                "OPENAI_API_KEY가 설정되지 않았습니다. "
                ".env 파일 또는 환경변수를 확인하세요."
            )
        if not self.search.api_key:
            raise ValueError(
                "TAVILY_API_KEY가 설정되지 않았습니다. "
                ".env 파일 또는 환경변수를 확인하세요."
            )
