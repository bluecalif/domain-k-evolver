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
    llm_batch_size: int = 12

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
class SIP7AxisToggles:
    """SI-P7 Step A/B 축별 기능 toggle (V3 ablation 용).

    기본값 전부 True = 기존 동작 유지. False 로 설정 시 해당 축 no-op.
    `SI_P7_AXIS_OFF=s2` env var 로 비활성화 축 지정 (콤마 구분, e.g. "s2,s3").

    SI-P7 V-T11 (Action A): S2 내부 condition_split rule 단위 토글 추가.
    `SI_P7_RULE_OFF=t6,t7,t8` 로 개별 비활성화. s2_enabled=True 하에서만 의미.
    s2_enabled=False 면 3 rule 모두 강제 off (기존 회귀 동작).
    """

    s1_enabled: bool = True  # defer/queue, target 자유화 (S1-T1~T8)
    s2_enabled: bool = True  # integration_injection + ku_stagnation + query_rewrite
                             # + aggressive_mode + condition_split 재정의 (S2-T1~T8)
    s3_enabled: bool = True  # adjacent rule engine + suppress + blocklist + yield (S3-T1~T8)
    s4_enabled: bool = True  # virtual entity 제거 + coverage_map.deficit_score (S4-T1~T2)
    # S2 내부 condition_split rule 단위 토글 (V-T11)
    t6_struct_split: bool = True       # Rule 2b: 값 구조 차이 (range vs scalar vs set)
    t7_axes_forced_split: bool = True  # Rule 2d: skeleton condition_axes 정의 → 강제
    t8_axis_tags_split: bool = True    # Rule 2c: axis_tags 차이

    @classmethod
    def from_env(cls) -> SIP7AxisToggles:
        off_raw = os.environ.get("SI_P7_AXIS_OFF", "").strip().lower()
        off_axes = {a.strip() for a in off_raw.split(",") if a.strip()}
        rule_off_raw = os.environ.get("SI_P7_RULE_OFF", "").strip().lower()
        off_rules = {r.strip() for r in rule_off_raw.split(",") if r.strip()}
        return cls(
            s1_enabled="s1" not in off_axes,
            s2_enabled="s2" not in off_axes,
            s3_enabled="s3" not in off_axes,
            s4_enabled="s4" not in off_axes,
            t6_struct_split="t6" not in off_rules,
            t7_axes_forced_split="t7" not in off_rules,
            t8_axis_tags_split="t8" not in off_rules,
        )

    def to_dict(self) -> dict[str, bool]:
        """state 에 저장할 dict 형태 — node 에서 state 로 참조."""
        return {
            "s1_enabled": self.s1_enabled,
            "s2_enabled": self.s2_enabled,
            "s3_enabled": self.s3_enabled,
            "s4_enabled": self.s4_enabled,
            "t6_struct_split": self.t6_struct_split,
            "t7_axes_forced_split": self.t7_axes_forced_split,
            "t8_axis_tags_split": self.t8_axis_tags_split,
        }


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
class ExternalAnchorConfig:
    """SI-P4 Stage E: External Anchor 예산 + kill-switch 설정.

    Stage E 는 universe_probe + exploration_pivot 로 외부 추론을 도입.
    예산 초과 시 kill-switch 가 발동하여 Stage E 만 skip, core loop 는 지속.
    """

    enabled: bool = False  # 기본 off — 명시적 활성화 필요
    probe_interval_cycles: int = 5  # universe_probe 주기 (cycle N마다)
    llm_budget_per_run: int = 12  # 15c bench 당 Stage E 전용 LLM call 상한 (D-147: 3→12)
    tavily_budget_per_run: int = 9  # 15c bench 당 Stage E 전용 Tavily query 상한
    pivot_min_plateau_cycles: int = 5  # exploration_pivot 발동 최소 plateau 길이
    candidate_promotion_min_confidence: float = 0.6  # universe_probe candidate → HITL-R 최소 신뢰도

    @classmethod
    def from_env(cls) -> ExternalAnchorConfig:
        return cls(
            enabled=os.environ.get("EVOLVER_EXTERNAL_ANCHOR_ENABLED", "false").lower() == "true",
            probe_interval_cycles=int(os.environ.get("EVOLVER_PROBE_INTERVAL_CYCLES", "5")),
            llm_budget_per_run=int(os.environ.get("EVOLVER_STAGE_E_LLM_BUDGET", "12")),
            tavily_budget_per_run=int(os.environ.get("EVOLVER_STAGE_E_TAVILY_BUDGET", "9")),
            pivot_min_plateau_cycles=int(os.environ.get("EVOLVER_PIVOT_MIN_PLATEAU", "5")),
            candidate_promotion_min_confidence=float(
                os.environ.get("EVOLVER_CANDIDATE_MIN_CONFIDENCE", "0.6")
            ),
        )


@dataclass(frozen=True)
class EvolverConfig:
    """전체 설정 통합."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    orchestrator: OrchestratorConfig = field(default_factory=OrchestratorConfig)
    external_anchor: ExternalAnchorConfig = field(default_factory=ExternalAnchorConfig)

    @classmethod
    def from_env(cls) -> EvolverConfig:
        return cls(
            llm=LLMConfig.from_env(),
            search=SearchConfig.from_env(),
            orchestrator=OrchestratorConfig.from_env(),
            external_anchor=ExternalAnchorConfig.from_env(),
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
        "external_anchor": dataclasses.asdict(config.external_anchor),
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
