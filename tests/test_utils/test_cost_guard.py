"""SI-P4 Stage E: cost_guard 단위 테스트."""

from __future__ import annotations

import pytest

from src.config import ExternalAnchorConfig
from src.utils.cost_guard import CostGuard


@pytest.fixture
def enabled_config() -> ExternalAnchorConfig:
    return ExternalAnchorConfig(
        enabled=True,
        probe_interval_cycles=5,
        llm_budget_per_run=3,
        tavily_budget_per_run=9,
    )


@pytest.fixture
def disabled_config() -> ExternalAnchorConfig:
    return ExternalAnchorConfig(enabled=False)


def test_disabled_config_blocks_everything(disabled_config):
    guard = CostGuard(disabled_config)
    assert guard.allow("universe_probe", llm=1) is False
    assert guard.killed is False  # disabled != killed


def test_allow_within_budget(enabled_config):
    guard = CostGuard(enabled_config)
    assert guard.allow("universe_probe", llm=2, tavily=5) is True
    guard.record("universe_probe", llm=2, tavily=5)
    assert guard.usage.llm_calls == 2
    assert guard.usage.tavily_queries == 5


def test_allow_exact_budget(enabled_config):
    guard = CostGuard(enabled_config)
    assert guard.allow("op", llm=3, tavily=9) is True
    guard.record("op", llm=3, tavily=9)
    # exactly at limit — next call denies
    assert guard.allow("op", llm=1) is False


def test_llm_budget_exceeded_trips_killswitch(enabled_config):
    guard = CostGuard(enabled_config)
    guard.record("op", llm=2, tavily=0)
    assert guard.allow("op", llm=2) is False  # 2+2=4 > 3
    assert guard.killed is True


def test_tavily_budget_exceeded_trips_killswitch(enabled_config):
    guard = CostGuard(enabled_config)
    guard.record("op", llm=0, tavily=8)
    assert guard.allow("op", tavily=2) is False  # 8+2=10 > 9
    assert guard.killed is True


def test_killed_blocks_subsequent_calls(enabled_config):
    guard = CostGuard(enabled_config)
    guard.record("op", llm=3, tavily=0)
    assert guard.allow("op", llm=1) is False  # trips
    assert guard.killed is True
    # even 0-cost call denied
    assert guard.allow("op", llm=0, tavily=0) is False


def test_per_op_breakdown(enabled_config):
    guard = CostGuard(enabled_config)
    guard.record("universe_probe", llm=2, tavily=5)
    guard.record("exploration_pivot", llm=1, tavily=2)
    snap = guard.to_dict()
    assert snap["by_op"]["universe_probe"] == {"llm": 2, "tavily": 5}
    assert snap["by_op"]["exploration_pivot"] == {"llm": 1, "tavily": 2}
    assert snap["llm_used"] == 3
    assert snap["tavily_used"] == 7


def test_to_dict_serializable(enabled_config):
    import json

    guard = CostGuard(enabled_config)
    guard.record("op", llm=1, tavily=2)
    json.dumps(guard.to_dict())  # must not raise
