"""Tests for exploration_pivot (SI-P4 Stage E, E4)."""
from __future__ import annotations

import json
from dataclasses import replace
from unittest.mock import MagicMock

import pytest

from src.config import EvolverConfig, ExternalAnchorConfig
from src.nodes.exploration_pivot import (
    EXTERNAL_NOVELTY_THRESHOLD,
    EXTERNAL_NOVELTY_WINDOW,
    run_exploration_pivot,
    should_pivot,
)
from src.utils.cost_guard import CostGuard


def _config(enabled: bool = True) -> EvolverConfig:
    cfg = EvolverConfig()
    return replace(cfg, external_anchor=ExternalAnchorConfig(
        enabled=enabled, llm_budget_per_run=10, tavily_budget_per_run=10,
    ))


def _stagnant_state(
    ext_novelty: float = 0.05,
    reach_per_100: float = 10.0,
    audit_consumed: bool = False,
) -> dict:
    """should_pivot 가 True 를 반환하는 state."""
    return {
        "current_cycle": 10,
        "domain_skeleton": {
            "domain": "japan-travel",
            "categories": [{"slug": "transport"}, {"slug": "dining"}],
            "fields": [{"name": "price"}],
            "candidate_categories": [
                {"slug": "accessibility", "name": "Accessibility"},
                {"slug": "nightlife", "name": "Nightlife"},
                {"slug": "seasonality", "name": "Seasonality"},
            ],
        },
        "knowledge_units": [],
        "external_novelty_history": [ext_novelty] * EXTERNAL_NOVELTY_WINDOW,
        "reach_history": [
            {"domains_per_100ku": reach_per_100},
            {"domains_per_100ku": reach_per_100},
            {"domains_per_100ku": reach_per_100},
        ],
        "current_plan": {"targets": [
            {"entity_key": "japan-travel:transport:jr-pass"},
        ]},
        "_audit_consumed_this_cycle": audit_consumed,
    }


def _mock_llm(variants=None):
    llm = MagicMock()
    resp = MagicMock()
    resp.content = json.dumps({"variants": variants or [
        {"strategy": "ABSTRACTION_RAISE", "query": "long-distance rail Japan", "rationale": "broaden"},
        {"strategy": "TIME_SHIFT", "query": "Japan travel 2026", "rationale": "temporal"},
        {"strategy": "LONG_TAIL", "query": "wheelchair accessible onsen", "rationale": "underserved"},
    ]})
    llm.invoke.return_value = resp
    return llm


# --- should_pivot tests ---

class TestShouldPivot:
    def test_all_conditions_met(self):
        cfg = _config(enabled=True)
        state = _stagnant_state()
        should, reason = should_pivot(state, cfg)
        assert should is True
        assert reason == "plateau:exploration_pivot"

    def test_disabled(self):
        cfg = _config(enabled=False)
        should, reason = should_pivot(_stagnant_state(), cfg)
        assert should is False
        assert reason == "external_anchor_disabled"

    def test_insufficient_ext_history(self):
        cfg = _config(enabled=True)
        state = _stagnant_state()
        state["external_novelty_history"] = [0.05, 0.05]  # < 5
        should, reason = should_pivot(state, cfg)
        assert should is False
        assert "insufficient_ext_history" in reason

    def test_ext_novelty_not_stagnant(self):
        cfg = _config(enabled=True)
        state = _stagnant_state()
        state["external_novelty_history"] = [0.05, 0.05, 0.3, 0.05, 0.05]
        should, reason = should_pivot(state, cfg)
        assert should is False
        assert reason == "ext_novelty_not_stagnant"

    def test_reach_not_degraded(self):
        cfg = _config(enabled=True)
        state = _stagnant_state(reach_per_100=20.0)  # above floor
        should, reason = should_pivot(state, cfg)
        assert should is False
        assert "reach_not_degraded" in reason

    def test_audit_already_consumed(self):
        cfg = _config(enabled=True)
        state = _stagnant_state(audit_consumed=True)
        should, reason = should_pivot(state, cfg)
        assert should is False
        assert reason == "audit_already_consumed"


# --- run_exploration_pivot tests ---

class TestRunExplorationPivot:
    def test_happy_path(self):
        cfg = _config(enabled=True)
        guard = CostGuard(cfg.external_anchor)
        state = _stagnant_state()
        llm = _mock_llm()

        result = run_exploration_pivot(state, llm, cfg, guard, cycle=10)

        assert result["status"] == "ok"
        assert len(result["variants"]) == 3
        assert result["variants"][0]["strategy"] == "ABSTRACTION_RAISE"
        # candidate_targets: top 2 from candidate_categories
        assert len(result["candidate_targets"]) == 2
        assert result["candidate_targets"][0]["slug"] == "accessibility"
        assert result["candidate_targets"][1]["slug"] == "nightlife"
        assert guard.usage.llm_calls == 1

    def test_skipped_no_trigger(self):
        cfg = _config(enabled=True)
        guard = CostGuard(cfg.external_anchor)
        state = _stagnant_state(ext_novelty=0.5)  # not stagnant

        result = run_exploration_pivot(state, _mock_llm(), cfg, guard)

        assert result["status"] == "skipped"
        assert guard.usage.llm_calls == 0

    def test_budget_exceeded(self):
        ea = ExternalAnchorConfig(enabled=True, llm_budget_per_run=0, tavily_budget_per_run=10)
        guard = CostGuard(ea)
        state = _stagnant_state()

        result = run_exploration_pivot(state, _mock_llm(), _config(), guard)

        assert result["status"] == "skipped"
        assert result["reason"] == "budget_exceeded"

    def test_llm_error(self):
        cfg = _config(enabled=True)
        guard = CostGuard(cfg.external_anchor)
        state = _stagnant_state()
        llm = MagicMock()
        llm.invoke.side_effect = RuntimeError("llm down")

        result = run_exploration_pivot(state, llm, cfg, guard)

        assert result["status"] == "error"
        assert "llm_error" in result["reason"]
        assert guard.usage.llm_calls == 1

    def test_no_candidate_categories(self):
        cfg = _config(enabled=True)
        guard = CostGuard(cfg.external_anchor)
        state = _stagnant_state()
        state["domain_skeleton"]["candidate_categories"] = []

        result = run_exploration_pivot(state, _mock_llm(), cfg, guard)

        assert result["status"] == "ok"
        assert len(result["variants"]) == 3
        assert len(result["candidate_targets"]) == 0

    def test_malformed_llm_response(self):
        cfg = _config(enabled=True)
        guard = CostGuard(cfg.external_anchor)
        state = _stagnant_state()
        llm = MagicMock()
        resp = MagicMock()
        resp.content = json.dumps({"variants": "not a list"})
        llm.invoke.return_value = resp

        result = run_exploration_pivot(state, llm, cfg, guard)

        assert result["status"] == "ok"
        assert result["variants"] == []  # graceful fallback
