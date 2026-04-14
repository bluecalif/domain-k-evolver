"""Evolver 환경 설정.

API 키, 모델 파라미터, 실행 옵션을 환경변수에서 로드.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMConfig:
    """LLM 설정."""

    provider: str = "openai"
    model: str = "gpt-4.1-mini"
    temperature: float = 0.2
    max_tokens: int = 4096
    request_timeout: int = 60
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
    """검색 도구 설정 (SI-P3R: Tavily snippet-only)."""

    provider: str = "tavily"
    api_key: str = ""
    max_results: int = 5
    request_timeout: int = 30
    entropy_floor: float = 2.5
    cycle_llm_token_budget: int = 100_000

    @classmethod
    def from_env(cls) -> SearchConfig:
        return cls(
            provider=os.environ.get("EVOLVER_SEARCH_PROVIDER", "tavily"),
            api_key=os.environ.get("TAVILY_API_KEY", ""),
            max_results=int(os.environ.get("EVOLVER_SEARCH_MAX_RESULTS", "5")),
            entropy_floor=float(os.environ.get("EVOLVER_ENTROPY_FLOOR", "2.5")),
            cycle_llm_token_budget=int(os.environ.get("EVOLVER_CYCLE_LLM_BUDGET", "100000")),
        )


@dataclass(frozen=True)
class OrchestratorConfig:
    """Orchestrator 실행 설정."""

    max_cycles: int = 10
    snapshot_every: int = 1
    invariant_check: bool = True
    stop_on_convergence: bool = True
    plateau_window: int = 3
    audit_interval: int = 5  # N cycle마다 Executive Audit 실행 (0=비활성)
    bench_domain: str = "japan-travel"
    bench_path: str = "bench"
    bench_root: str = ""  # Silver: 직접 trial 경로 (설정 시 bench_path/bench_domain 무시)

    @classmethod
    def from_env(cls) -> OrchestratorConfig:
        return cls(
            max_cycles=int(os.environ.get("EVOLVER_MAX_CYCLES", "10")),
            snapshot_every=int(os.environ.get("EVOLVER_SNAPSHOT_EVERY", "1")),
            invariant_check=os.environ.get("EVOLVER_INVARIANT_CHECK", "true").lower() == "true",
            stop_on_convergence=os.environ.get("EVOLVER_STOP_ON_CONVERGENCE", "true").lower() == "true",
            plateau_window=int(os.environ.get("EVOLVER_PLATEAU_WINDOW", "3")),
            audit_interval=int(os.environ.get("EVOLVER_AUDIT_INTERVAL", "5")),
            bench_domain=os.environ.get("EVOLVER_BENCH_DOMAIN", "japan-travel"),
            bench_path=os.environ.get("EVOLVER_BENCH_PATH", "bench"),
            bench_root=os.environ.get("EVOLVER_BENCH_ROOT", ""),
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


# --- P0-A6: config snapshot ---------------------------------------------

def _get_git_head(repo_dir: Path | None = None) -> str:
    """현재 git HEAD commit hash. 실패 시 'unknown'."""
    try:
        cmd = ["git"]
        if repo_dir is not None:
            cmd += ["-C", str(repo_dir)]
        cmd += ["rev-parse", "HEAD"]
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=5)
        return out.decode("utf-8").strip()
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
        logger.warning("git HEAD 조회 실패: %s", e)
        return "unknown"


def _redact(value: object) -> object:
    """API 키는 snapshot 에 저장하지 않는다."""
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k == "api_key":
                out[k] = "<redacted>" if v else ""
            else:
                out[k] = _redact(v)
        return out
    return value


def write_config_snapshot(
    config: EvolverConfig,
    trial_dir: Path | str,
    *,
    provider_list: list[str] | None = None,
    skeleton_path: Path | str | None = None,
    repo_dir: Path | str | None = None,
) -> Path:
    """Silver trial 시작 시 `config.snapshot.json` 을 trial_dir 에 기록.

    Args:
        config: 실행에 사용되는 EvolverConfig.
        trial_dir: Silver trial 디렉토리 (`bench/silver/{domain}/{trial_id}/`).
        provider_list: 활성 provider 목록. 미지정 시 `[config.search.provider]`.
        skeleton_path: domain-skeleton.json 경로. 미지정 시 `trial_dir/state/domain-skeleton.json`
            → 존재하지 않으면 `"missing"` 해시로 기록.
        repo_dir: git HEAD 조회 기준 디렉토리. 미지정 시 현재 작업 디렉토리.

    Returns:
        작성된 snapshot 파일의 Path.
    """
    trial_dir = Path(trial_dir)
    trial_dir.mkdir(parents=True, exist_ok=True)

    if provider_list is None:
        provider_list = [config.search.provider]

    # skeleton sha256
    if skeleton_path is None:
        candidate = trial_dir / "state" / "domain-skeleton.json"
        skeleton_path = candidate if candidate.exists() else None
    else:
        skeleton_path = Path(skeleton_path)

    if skeleton_path is not None and skeleton_path.exists():
        skeleton_sha256 = hashlib.sha256(skeleton_path.read_bytes()).hexdigest()
        skeleton_ref = str(skeleton_path)
    else:
        skeleton_sha256 = "missing"
        skeleton_ref = str(skeleton_path) if skeleton_path is not None else ""

    snapshot = {
        "schema_version": 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_head": _get_git_head(Path(repo_dir) if repo_dir else None),
        "llm": _redact(dataclasses.asdict(config.llm)),
        "search": _redact(dataclasses.asdict(config.search)),
        "orchestrator": dataclasses.asdict(config.orchestrator),
        "providers": list(provider_list),
        "skeleton_path": skeleton_ref,
        "skeleton_sha256": skeleton_sha256,
    }

    target = trial_dir / "config.snapshot.json"
    target.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("config snapshot 기록: %s", target)
    return target
