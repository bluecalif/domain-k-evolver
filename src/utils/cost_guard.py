"""SI-P4 Stage E: External Anchor 비용 가드.

universe_probe + exploration_pivot 가 LLM/Tavily 예산을 넘기지 않도록
per-cycle / per-run 사용량을 추적하고 kill-switch 를 발동.

사용 패턴:
    guard = CostGuard(config.external_anchor)
    if guard.allow("universe_probe", llm=2, tavily=5):
        guard.record("universe_probe", llm=2, tavily=5)
        # ... 실행
    else:
        # budget 초과 — Stage E skip, core loop 지속
        pass
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import ExternalAnchorConfig

logger = logging.getLogger(__name__)


@dataclass
class CostUsage:
    """누적 비용 추적."""

    llm_calls: int = 0
    tavily_queries: int = 0
    by_op: dict[str, dict[str, int]] = field(default_factory=dict)

    def add(self, op: str, llm: int, tavily: int) -> None:
        self.llm_calls += llm
        self.tavily_queries += tavily
        bucket = self.by_op.setdefault(op, {"llm": 0, "tavily": 0})
        bucket["llm"] += llm
        bucket["tavily"] += tavily


class CostGuard:
    """Stage E 예산 가드 + kill-switch.

    한 run (= 15c bench) 동안 누적 사용량을 추적.
    `allow()` 는 예산 내에서만 True 반환. `record()` 는 실제 사용 후 호출.
    """

    def __init__(self, config: ExternalAnchorConfig):
        self._config = config
        self._usage = CostUsage()
        self._killed = False

    @property
    def usage(self) -> CostUsage:
        return self._usage

    @property
    def killed(self) -> bool:
        return self._killed

    def allow(self, op: str, *, llm: int = 0, tavily: int = 0) -> bool:
        """예산 내에서만 True. 초과 시 kill-switch 발동."""
        if not self._config.enabled:
            return False
        if self._killed:
            return False

        next_llm = self._usage.llm_calls + llm
        next_tavily = self._usage.tavily_queries + tavily

        if next_llm > self._config.llm_budget_per_run:
            self._trip(f"LLM budget {self._config.llm_budget_per_run} 초과 ({op}, +{llm})")
            return False
        if next_tavily > self._config.tavily_budget_per_run:
            self._trip(
                f"Tavily budget {self._config.tavily_budget_per_run} 초과 ({op}, +{tavily})"
            )
            return False
        return True

    def record(self, op: str, *, llm: int = 0, tavily: int = 0) -> None:
        """실제 호출 후 사용량 기록."""
        self._usage.add(op, llm, tavily)
        logger.info(
            "[cost_guard] %s: llm=%d tavily=%d (total llm=%d/%d tavily=%d/%d)",
            op,
            llm,
            tavily,
            self._usage.llm_calls,
            self._config.llm_budget_per_run,
            self._usage.tavily_queries,
            self._config.tavily_budget_per_run,
        )

    def _trip(self, reason: str) -> None:
        if not self._killed:
            logger.warning("[cost_guard] kill-switch 발동: %s", reason)
            self._killed = True

    def to_dict(self) -> dict:
        """trial_dir 에 dump 가능한 dict."""
        return {
            "enabled": self._config.enabled,
            "killed": self._killed,
            "llm_budget": self._config.llm_budget_per_run,
            "tavily_budget": self._config.tavily_budget_per_run,
            "llm_used": self._usage.llm_calls,
            "tavily_used": self._usage.tavily_queries,
            "by_op": dict(self._usage.by_op),
        }
