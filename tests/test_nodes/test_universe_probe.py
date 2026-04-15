"""Tests for universe_probe LLM survey node (SI-P4 Stage E, E2-2)."""
from __future__ import annotations

import json
from dataclasses import replace
from unittest.mock import MagicMock

import pytest

from src.config import EvolverConfig, ExternalAnchorConfig
from src.nodes.universe_probe import (
    _validate_and_filter_proposals,
    gather_evidence,
    register_validated,
    run_universe_probe,
    should_run_universe_probe,
    validate_proposals,
)
from src.utils.cost_guard import CostGuard


def _config(enabled: bool = True, llm_budget: int = 3) -> EvolverConfig:
    cfg = EvolverConfig()
    return replace(cfg, external_anchor=ExternalAnchorConfig(
        enabled=enabled, llm_budget_per_run=llm_budget, tavily_budget_per_run=9
    ))


def _skeleton():
    return {
        "domain": "japan-travel",
        "categories": [
            {"slug": "transport"},
            {"slug": "dining"},
        ],
        "fields": [{"name": "price"}],
    }


def _state(skeleton=None):
    return {
        "cycle": 7,
        "domain_skeleton": skeleton or _skeleton(),
        "knowledge_units": [
            {"entity_key": "japan-travel:transport:jr-pass"},
            {"entity_key": "japan-travel:dining:sushi-etiquette"},
        ],
    }


def _mock_llm(payload: dict):
    llm = MagicMock()
    resp = MagicMock()
    resp.content = json.dumps(payload)
    llm.invoke.return_value = resp
    return llm


def test_disabled_config_skips():
    cfg = _config(enabled=False)
    guard = CostGuard(cfg.external_anchor)
    result = run_universe_probe(_state(), _mock_llm({"proposals": []}), cfg, guard)
    assert result["status"] == "skipped"
    assert result["reason"] == "external_anchor_disabled"
    assert result["proposals"] == []


def test_budget_exceeded_skips():
    cfg = _config(enabled=True, llm_budget=0)  # 0 budget → any call exceeds
    guard = CostGuard(cfg.external_anchor)
    result = run_universe_probe(_state(), _mock_llm({"proposals": []}), cfg, guard)
    assert result["status"] == "skipped"
    assert result["reason"] == "budget_exceeded"


def test_happy_path_generates_proposals():
    cfg = _config()
    guard = CostGuard(cfg.external_anchor)
    llm = _mock_llm({
        "proposals": [
            {"slug": "accessibility", "name": "Accessibility",
             "rationale": "wheelchair info missing",
             "expected_source": "gov.jp", "type": "NEW_CATEGORY"},
            {"slug": "seasonality", "name": "Seasonality",
             "rationale": "peak/off season pricing",
             "expected_source": "travel-guides", "type": "NEW_AXIS"},
        ]
    })
    result = run_universe_probe(_state(), llm, cfg, guard, cycle=7)
    assert result["status"] == "ok"
    assert len(result["proposals"]) == 2
    for p in result["proposals"]:
        assert p["proposed_at_cycle"] == 7
        assert p["status"] == "pending_validation"
        assert p["evidence"] is None
    assert guard.usage.llm_calls == 1


def test_collision_with_active_rejected():
    cfg = _config()
    guard = CostGuard(cfg.external_anchor)
    llm = _mock_llm({
        "proposals": [
            {"slug": "transport", "name": "Transport", "rationale": "x",
             "expected_source": "y", "type": "NEW_CATEGORY"},
            {"slug": "accessibility", "name": "Accessibility", "rationale": "x",
             "expected_source": "y", "type": "NEW_CATEGORY"},
        ]
    })
    result = run_universe_probe(_state(), llm, cfg, guard)
    assert len(result["proposals"]) == 1
    assert result["proposals"][0]["slug"] == "accessibility"
    assert len(result["rejected"]) == 1
    assert result["rejected"][0]["_reject_reason"] == "collision_active"


def test_collision_with_existing_candidate_rejected():
    cfg = _config()
    guard = CostGuard(cfg.external_anchor)
    skel = _skeleton()
    skel["candidate_categories"] = [{"slug": "accessibility"}]
    llm = _mock_llm({
        "proposals": [
            {"slug": "accessibility", "name": "Accessibility", "rationale": "x",
             "expected_source": "y", "type": "NEW_CATEGORY"},
        ]
    })
    result = run_universe_probe(_state(skel), llm, cfg, guard)
    assert result["proposals"] == []
    assert result["rejected"][0]["_reject_reason"] == "collision_candidate"


def test_invalid_type_and_missing_slug_rejected():
    cfg = _config()
    guard = CostGuard(cfg.external_anchor)
    llm = _mock_llm({
        "proposals": [
            {"slug": "", "name": "X", "rationale": "x", "expected_source": "y",
             "type": "NEW_CATEGORY"},
            {"slug": "budget", "name": "Budget", "rationale": "x",
             "expected_source": "y", "type": "REFINEMENT"},
            {"slug": "valid", "name": "Valid", "rationale": "x",
             "expected_source": "y", "type": "NEW_CATEGORY"},
        ]
    })
    result = run_universe_probe(_state(), llm, cfg, guard)
    assert [p["slug"] for p in result["proposals"]] == ["valid"]
    reasons = sorted(r["_reject_reason"] for r in result["rejected"])
    assert reasons == ["invalid_type:REFINEMENT", "missing_slug"]


def test_duplicate_slugs_in_batch_rejected():
    cfg = _config()
    guard = CostGuard(cfg.external_anchor)
    llm = _mock_llm({
        "proposals": [
            {"slug": "accessibility", "name": "A", "rationale": "x",
             "expected_source": "y", "type": "NEW_CATEGORY"},
            {"slug": "accessibility", "name": "B", "rationale": "x",
             "expected_source": "y", "type": "NEW_AXIS"},
        ]
    })
    result = run_universe_probe(_state(), llm, cfg, guard)
    assert len(result["proposals"]) == 1
    assert result["rejected"][0]["_reject_reason"] == "duplicate_in_batch"


def test_llm_error_returns_error_status():
    cfg = _config()
    guard = CostGuard(cfg.external_anchor)
    llm = MagicMock()
    llm.invoke.side_effect = RuntimeError("boom")
    result = run_universe_probe(_state(), llm, cfg, guard)
    assert result["status"] == "error"
    assert "boom" in result["reason"]
    # cost recorded even on error (LLM 실제 호출 시도되었으므로)
    assert guard.usage.llm_calls == 1


def test_malformed_json_returns_error():
    cfg = _config()
    guard = CostGuard(cfg.external_anchor)
    llm = MagicMock()
    resp = MagicMock()
    resp.content = "not json at all"
    llm.invoke.return_value = resp
    result = run_universe_probe(_state(), llm, cfg, guard)
    assert result["status"] == "error"


def test_proposals_not_list_returns_error():
    cfg = _config()
    guard = CostGuard(cfg.external_anchor)
    llm = _mock_llm({"proposals": "not a list"})
    result = run_universe_probe(_state(), llm, cfg, guard)
    assert result["status"] == "error"
    assert result["reason"] == "proposals_not_list"


def test_slug_lowercased():
    cfg = _config()
    guard = CostGuard(cfg.external_anchor)
    llm = _mock_llm({
        "proposals": [
            {"slug": "  Accessibility  ", "name": "A", "rationale": "x",
             "expected_source": "y", "type": "NEW_CATEGORY"},
        ]
    })
    result = run_universe_probe(_state(), llm, cfg, guard)
    assert result["proposals"][0]["slug"] == "accessibility"


def test_filter_rejects_non_dict_proposal():
    accepted, rejected = _validate_and_filter_proposals(
        ["not_a_dict", {"slug": "ok", "type": "NEW_CATEGORY"}],
        _skeleton(),
    )
    assert len(accepted) == 1
    assert rejected[0]["_reject_reason"] == "not_a_dict"


# --- gather_evidence tests (E2-3) ---

def _proposals(slugs=None):
    """테스트용 accepted proposals 생성."""
    slugs = slugs or ["accessibility", "seasonality"]
    return [
        {"slug": s, "name": s.title(), "rationale": "test",
         "expected_source": "web", "type": "NEW_CATEGORY",
         "proposed_at_cycle": 7, "status": "pending_validation", "evidence": None}
        for s in slugs
    ]


def _mock_search(results=None):
    """MockSearchTool 대용. search(query) → results."""
    mock = MagicMock()
    mock.search.return_value = results or [
        {"url": "https://ex.com/1", "title": "T1", "snippet": "S1"},
        {"url": "https://ex.com/2", "title": "T2", "snippet": "S2"},
    ]
    return mock


def test_gather_evidence_happy_path():
    """정상 경로: 모든 proposal 에 snippets 주입."""
    cfg = _config(enabled=True)
    guard = CostGuard(cfg.external_anchor)
    props = _proposals()
    search = _mock_search()

    evidenced, skipped = gather_evidence(props, search, guard, "japan-travel")

    assert len(evidenced) == 2
    assert len(skipped) == 0
    for p in evidenced:
        assert "snippets" in p["evidence"]
        assert len(p["evidence"]["snippets"]) == 2
    assert guard.usage.tavily_queries == 2
    # query 형식 확인
    calls = [c.args[0] for c in search.search.call_args_list]
    assert "Accessibility japan-travel" in calls
    assert "Seasonality japan-travel" in calls


def test_gather_evidence_budget_exceeded_skips():
    """Tavily budget 소진 시 남은 proposal skip."""
    cfg = _config(enabled=True)
    ea = ExternalAnchorConfig(enabled=True, llm_budget_per_run=3, tavily_budget_per_run=1)
    guard = CostGuard(ea)
    props = _proposals(["a", "b", "c"])
    search = _mock_search()

    evidenced, skipped = gather_evidence(props, search, guard, "japan-travel")

    assert len(evidenced) == 1
    assert len(skipped) == 2
    for s in skipped:
        assert s["evidence"]["skipped"] is True
        assert s["evidence"]["reason"] == "budget_exceeded"
    assert guard.usage.tavily_queries == 1


def test_gather_evidence_search_error_still_records():
    """Tavily 호출 실패 시 error 기록 + cost 기록."""
    cfg = _config(enabled=True)
    guard = CostGuard(cfg.external_anchor)
    props = _proposals(["accessibility"])
    search = MagicMock()
    search.search.side_effect = RuntimeError("tavily down")

    evidenced, skipped = gather_evidence(props, search, guard, "japan-travel")

    assert len(evidenced) == 1
    assert len(skipped) == 0
    assert evidenced[0]["evidence"]["snippets"] == []
    assert "tavily down" in evidenced[0]["evidence"]["error"]
    assert guard.usage.tavily_queries == 1


def test_gather_evidence_empty_proposals():
    """빈 proposals → 빈 결과."""
    cfg = _config(enabled=True)
    guard = CostGuard(cfg.external_anchor)
    search = _mock_search()

    evidenced, skipped = gather_evidence([], search, guard, "japan-travel")

    assert evidenced == []
    assert skipped == []
    assert guard.usage.tavily_queries == 0


def test_gather_evidence_partial_budget():
    """3개 중 2개만 budget 허용 — 마지막 1개 skip."""
    ea = ExternalAnchorConfig(enabled=True, llm_budget_per_run=3, tavily_budget_per_run=2)
    guard = CostGuard(ea)
    props = _proposals(["a", "b", "c"])
    search = _mock_search()

    evidenced, skipped = gather_evidence(props, search, guard, "japan-travel")

    assert len(evidenced) == 2
    assert len(skipped) == 1
    assert skipped[0]["slug"] == "c"


def test_gather_evidence_snippet_fields():
    """snippets 가 url/title/snippet 필드를 정확히 보존."""
    cfg = _config(enabled=True)
    guard = CostGuard(cfg.external_anchor)
    results = [
        {"url": "https://a.com", "title": "Title A", "snippet": "Snippet A"},
        {"url": "https://b.com", "title": "Title B", "snippet": "Snippet B"},
        {"url": "https://c.com", "title": "Title C", "snippet": "Snippet C"},
    ]
    props = _proposals(["test-cat"])
    search = _mock_search(results)

    evidenced, _ = gather_evidence(props, search, guard, "japan-travel")

    snips = evidenced[0]["evidence"]["snippets"]
    assert len(snips) == 3
    assert snips[0] == {"url": "https://a.com", "title": "Title A", "snippet": "Snippet A"}
    assert snips[2]["url"] == "https://c.com"


def test_gather_evidence_cost_guard_killed_skips_all():
    """kill-switch 이미 발동 상태 → 모든 proposal skip."""
    ea = ExternalAnchorConfig(enabled=True, llm_budget_per_run=3, tavily_budget_per_run=9)
    guard = CostGuard(ea)
    guard._killed = True  # 이미 kill-switch 발동
    props = _proposals(["a", "b"])
    search = _mock_search()

    evidenced, skipped = gather_evidence(props, search, guard, "japan-travel")

    assert len(evidenced) == 0
    assert len(skipped) == 2
    assert guard.usage.tavily_queries == 0


# --- validate_proposals + register_validated tests (E2-4) ---

def _evidenced_proposals(slugs=None, snippets=None):
    """evidence.snippets 가 주입된 proposals 생성."""
    slugs = slugs or ["accessibility", "seasonality"]
    snips = snippets or [
        {"url": "https://ex.com/1", "title": "T1", "snippet": "S1"},
        {"url": "https://ex.com/2", "title": "T2", "snippet": "S2"},
    ]
    return [
        {"slug": s, "name": s.title(), "rationale": "important for travelers",
         "expected_source": "web", "type": "NEW_CATEGORY",
         "proposed_at_cycle": 7, "status": "pending_validation",
         "evidence": {"snippets": snips}}
        for s in slugs
    ]


def _mock_validator_llm(exists=True, confidence=0.8, source_diversity=3):
    """validator LLM mock — 동일 결과 반환."""
    llm = MagicMock()
    resp = MagicMock()
    resp.content = json.dumps({
        "exists": exists,
        "confidence": confidence,
        "source_diversity": source_diversity,
        "sample_entity_names": ["entity-a", "entity-b"],
    })
    llm.invoke.return_value = resp
    return llm


def test_validate_proposals_happy_path():
    """exists=True, confidence >= 0.6 → validated."""
    ea = ExternalAnchorConfig(enabled=True, llm_budget_per_run=10, tavily_budget_per_run=9)
    guard = CostGuard(ea)
    props = _evidenced_proposals()
    llm = _mock_validator_llm(exists=True, confidence=0.8)

    validated, failed = validate_proposals(props, llm, guard, min_confidence=0.6)

    assert len(validated) == 2
    assert len(failed) == 0
    for p in validated:
        assert p["status"] == "validated"
        assert p["validation"]["status"] == "passed"
        assert p["validation"]["confidence"] == 0.8
        assert p["validation"]["source_diversity"] == 3
    assert guard.usage.llm_calls == 2


def test_validate_proposals_low_confidence_fails():
    """confidence < min_confidence → failed."""
    ea = ExternalAnchorConfig(enabled=True, llm_budget_per_run=10, tavily_budget_per_run=9)
    guard = CostGuard(ea)
    props = _evidenced_proposals(["test-cat"])
    llm = _mock_validator_llm(exists=True, confidence=0.3)

    validated, failed = validate_proposals(props, llm, guard, min_confidence=0.6)

    assert len(validated) == 0
    assert len(failed) == 1
    assert "low_confidence" in failed[0]["validation"]["reason"]


def test_validate_proposals_not_exists_fails():
    """exists=False → failed."""
    ea = ExternalAnchorConfig(enabled=True, llm_budget_per_run=10, tavily_budget_per_run=9)
    guard = CostGuard(ea)
    props = _evidenced_proposals(["test-cat"])
    llm = _mock_validator_llm(exists=False, confidence=0.9)

    validated, failed = validate_proposals(props, llm, guard, min_confidence=0.6)

    assert len(validated) == 0
    assert len(failed) == 1
    assert failed[0]["validation"]["reason"] == "not_exists"


def test_validate_proposals_no_evidence_skips():
    """evidence 없는 proposal → no_evidence skip."""
    ea = ExternalAnchorConfig(enabled=True, llm_budget_per_run=10, tavily_budget_per_run=9)
    guard = CostGuard(ea)
    props = [
        {"slug": "a", "name": "A", "rationale": "x", "type": "NEW_CATEGORY",
         "proposed_at_cycle": 7, "status": "pending_validation",
         "evidence": {"skipped": True, "reason": "budget_exceeded"}},
    ]
    llm = _mock_validator_llm()

    validated, failed = validate_proposals(props, llm, guard)

    assert len(validated) == 0
    assert len(failed) == 1
    assert failed[0]["validation"]["reason"] == "no_evidence"
    assert guard.usage.llm_calls == 0


def test_validate_proposals_budget_exceeded():
    """LLM budget 소진 시 남은 proposals skip."""
    ea = ExternalAnchorConfig(enabled=True, llm_budget_per_run=1, tavily_budget_per_run=9)
    guard = CostGuard(ea)
    props = _evidenced_proposals(["a", "b", "c"])
    llm = _mock_validator_llm()

    validated, failed = validate_proposals(props, llm, guard, min_confidence=0.6)

    assert len(validated) == 1  # 첫 번째만 budget 내
    assert len(failed) == 2
    budget_skipped = [f for f in failed if f["validation"].get("reason") == "budget_exceeded"]
    assert len(budget_skipped) == 2


def test_validate_proposals_llm_error():
    """LLM 호출 실패 → error + cost 기록."""
    ea = ExternalAnchorConfig(enabled=True, llm_budget_per_run=10, tavily_budget_per_run=9)
    guard = CostGuard(ea)
    props = _evidenced_proposals(["test-cat"])
    llm = MagicMock()
    llm.invoke.side_effect = RuntimeError("llm down")

    validated, failed = validate_proposals(props, llm, guard)

    assert len(validated) == 0
    assert len(failed) == 1
    assert failed[0]["validation"]["status"] == "error"
    assert guard.usage.llm_calls == 1


def test_register_validated_happy_path():
    """검증 통과 proposals → skeleton candidate_categories 에 등록."""
    skel = _skeleton()
    props = _evidenced_proposals(["accessibility"])
    props[0]["status"] = "validated"

    registered, errors = register_validated(props, skel)

    assert len(registered) == 1
    assert len(errors) == 0
    assert len(skel["candidate_categories"]) == 1
    assert skel["candidate_categories"][0]["slug"] == "accessibility"
    assert skel["candidate_categories"][0]["status"] == "validated"


def test_register_validated_collision_error():
    """이미 active 에 있는 slug → 등록 실패."""
    skel = _skeleton()
    props = _evidenced_proposals(["transport"])  # already in active
    props[0]["status"] = "validated"

    registered, errors = register_validated(props, skel)

    assert len(registered) == 0
    assert len(errors) == 1
    assert "already exists" in errors[0]["_register_error"]


def test_register_validated_multiple():
    """여러 proposals 등록 — 성공/실패 분리."""
    skel = _skeleton()
    props = _evidenced_proposals(["accessibility", "dining", "seasonality"])
    for p in props:
        p["status"] = "validated"

    registered, errors = register_validated(props, skel)

    assert len(registered) == 2  # accessibility, seasonality
    assert len(errors) == 1  # dining (active collision)
    slugs = [c["slug"] for c in skel["candidate_categories"]]
    assert "accessibility" in slugs
    assert "seasonality" in slugs


# --- E2-5: 통합 테스트 (3-step pipeline end-to-end) + budget kill-switch ---

def test_e2e_pipeline_survey_evidence_validate_register():
    """3-step pipeline: survey → evidence → validate → register.

    survey LLM 이 3개 proposal 반환, Tavily 가 snippets 제공,
    validator 가 2개 통과(1개 low_confidence) → skeleton 에 2개 등록.
    """
    # --- setup ---
    ea = ExternalAnchorConfig(
        enabled=True, llm_budget_per_run=10, tavily_budget_per_run=10,
    )
    guard = CostGuard(ea)
    skel = _skeleton()
    state = _state(skel)

    # Step 1: survey — 3 proposals
    survey_llm = _mock_llm({
        "proposals": [
            {"slug": "accessibility", "name": "Accessibility",
             "rationale": "wheelchair info", "expected_source": "gov.jp",
             "type": "NEW_CATEGORY"},
            {"slug": "seasonality", "name": "Seasonality",
             "rationale": "peak/off pricing", "expected_source": "guides",
             "type": "NEW_AXIS"},
            {"slug": "nightlife", "name": "Nightlife",
             "rationale": "entertainment info", "expected_source": "blogs",
             "type": "NEW_CATEGORY"},
        ]
    })
    cfg = _config(enabled=True)
    survey_result = run_universe_probe(state, survey_llm, cfg, guard, cycle=5)
    assert survey_result["status"] == "ok"
    assert len(survey_result["proposals"]) == 3

    # Step 2: gather evidence
    search = _mock_search([
        {"url": "https://a.com", "title": "A", "snippet": "snippet A"},
        {"url": "https://b.com", "title": "B", "snippet": "snippet B"},
    ])
    evidenced, ev_skipped = gather_evidence(
        survey_result["proposals"], search, guard, "japan-travel",
    )
    assert len(evidenced) == 3
    assert len(ev_skipped) == 0

    # Step 3: validate — accessibility/seasonality pass, nightlife fails
    call_count = [0]
    def _make_validator_response(*args, **kwargs):
        call_count[0] += 1
        resp = MagicMock()
        if call_count[0] <= 2:
            resp.content = json.dumps({
                "exists": True, "confidence": 0.85,
                "source_diversity": 3, "sample_entity_names": ["e1"],
            })
        else:
            resp.content = json.dumps({
                "exists": True, "confidence": 0.3,  # low
                "source_diversity": 1, "sample_entity_names": [],
            })
        return resp

    validator_llm = MagicMock()
    validator_llm.invoke.side_effect = _make_validator_response

    validated, val_failed = validate_proposals(
        evidenced, validator_llm, guard, min_confidence=0.6,
    )
    assert len(validated) == 2
    assert len(val_failed) == 1
    assert val_failed[0]["slug"] == "nightlife"

    # Step 4: register
    registered, reg_errors = register_validated(validated, skel)
    assert len(registered) == 2
    assert len(reg_errors) == 0
    candidate_slugs = [c["slug"] for c in skel.get("candidate_categories", [])]
    assert "accessibility" in candidate_slugs
    assert "seasonality" in candidate_slugs

    # active categories 는 불변 (D-139)
    active_slugs = [c["slug"] for c in skel["categories"]]
    assert "accessibility" not in active_slugs
    assert "seasonality" not in active_slugs

    # cost 확인: survey 1 LLM + evidence 3 Tavily + validator 3 LLM
    assert guard.usage.llm_calls == 4  # 1 survey + 3 validator
    assert guard.usage.tavily_queries == 3


def test_e2e_pipeline_disabled_skips_everything():
    """external_anchor disabled → survey skip, 나머지 단계 불필요."""
    cfg = _config(enabled=False)
    guard = CostGuard(cfg.external_anchor)
    result = run_universe_probe(_state(), _mock_llm({"proposals": []}), cfg, guard)
    assert result["status"] == "skipped"
    assert result["proposals"] == []
    assert guard.usage.llm_calls == 0
    assert guard.usage.tavily_queries == 0


def test_budget_killswitch_mid_pipeline():
    """예산 극소 설정 → pipeline 중간에 kill-switch 발동.

    LLM 1 + Tavily 1 budget → survey 성공, evidence 1개만, 나머지 skip.
    """
    ea = ExternalAnchorConfig(
        enabled=True, llm_budget_per_run=1, tavily_budget_per_run=1,
    )
    guard = CostGuard(ea)
    cfg = _config(enabled=True)

    # survey: budget llm=1 → 허용
    survey_llm = _mock_llm({
        "proposals": [
            {"slug": "accessibility", "name": "Accessibility",
             "rationale": "x", "expected_source": "y", "type": "NEW_CATEGORY"},
            {"slug": "nightlife", "name": "Nightlife",
             "rationale": "x", "expected_source": "y", "type": "NEW_CATEGORY"},
        ]
    })
    survey_result = run_universe_probe(_state(), survey_llm, cfg, guard, cycle=5)
    assert survey_result["status"] == "ok"
    assert guard.usage.llm_calls == 1  # survey 소진

    # evidence: budget tavily=1 → 첫 번째만 성공
    search = _mock_search()
    evidenced, ev_skipped = gather_evidence(
        survey_result["proposals"], search, guard, "japan-travel",
    )
    assert len(evidenced) == 1
    assert len(ev_skipped) == 1
    assert guard.usage.tavily_queries == 1

    # validate: budget llm 이미 소진 → 모두 skip
    validator_llm = _mock_validator_llm()
    validated, val_failed = validate_proposals(evidenced, validator_llm, guard)
    assert len(validated) == 0
    assert len(val_failed) == 1
    assert val_failed[0]["validation"]["reason"] == "budget_exceeded"


def test_budget_killswitch_trips_blocks_all():
    """kill-switch 발동 후 → 모든 allow() 거부."""
    ea = ExternalAnchorConfig(
        enabled=True, llm_budget_per_run=10, tavily_budget_per_run=10,
    )
    guard = CostGuard(ea)

    # 정상 allow
    assert guard.allow("test", llm=1) is True

    # 강제 kill
    guard._trip("manual test trip")
    assert guard.killed is True

    # 이후 모두 거부
    assert guard.allow("test", llm=1) is False
    assert guard.allow("test", tavily=1) is False

    # survey 도 skip
    cfg = _config(enabled=True)
    result = run_universe_probe(
        _state(), _mock_llm({"proposals": []}), cfg, guard, cycle=5,
    )
    assert result["status"] == "skipped"
    assert result["reason"] == "budget_exceeded"


def test_e2e_partial_evidence_failure_continues():
    """Tavily 일부 실패해도 pipeline 계속 — 실패 proposal 은 validator 에서 no_evidence."""
    ea = ExternalAnchorConfig(
        enabled=True, llm_budget_per_run=10, tavily_budget_per_run=10,
    )
    guard = CostGuard(ea)

    # 2 proposals
    props = [
        {"slug": "accessibility", "name": "Accessibility", "rationale": "x",
         "expected_source": "y", "type": "NEW_CATEGORY",
         "proposed_at_cycle": 5, "status": "pending_validation", "evidence": None},
        {"slug": "nightlife", "name": "Nightlife", "rationale": "x",
         "expected_source": "y", "type": "NEW_CATEGORY",
         "proposed_at_cycle": 5, "status": "pending_validation", "evidence": None},
    ]

    # search: 첫 번째 성공, 두 번째 실패
    call_idx = [0]
    def _search_side_effect(query):
        call_idx[0] += 1
        if call_idx[0] == 1:
            return [{"url": "https://a.com", "title": "A", "snippet": "s"}]
        raise RuntimeError("tavily timeout")

    search = MagicMock()
    search.search.side_effect = _search_side_effect

    evidenced, ev_skipped = gather_evidence(props, search, guard, "japan-travel")
    assert len(evidenced) == 2  # 둘 다 evidenced (하나는 error)
    assert evidenced[0]["evidence"]["snippets"] == [{"url": "https://a.com", "title": "A", "snippet": "s"}]
    assert "error" in evidenced[1]["evidence"]

    # validate: 첫 번째만 LLM 검증, 두 번째는 no_evidence
    validator_llm = _mock_validator_llm(exists=True, confidence=0.9)
    validated, val_failed = validate_proposals(evidenced, validator_llm, guard)
    assert len(validated) == 1
    assert validated[0]["slug"] == "accessibility"
    assert len(val_failed) == 1
    assert val_failed[0]["validation"]["reason"] == "no_evidence"


# --- E2-3: 트리거 조건 테스트 ---

def test_trigger_disabled_returns_false():
    """external_anchor disabled → trigger false."""
    cfg = _config(enabled=False)
    should, reason = should_run_universe_probe({"current_cycle": 5}, cfg)
    assert should is False
    assert reason == "external_anchor_disabled"


def test_trigger_periodic_cycle_match():
    """cycle % probe_interval == 0 → trigger true."""
    cfg = _config(enabled=True)
    # default probe_interval_cycles=5
    should, reason = should_run_universe_probe({"current_cycle": 5}, cfg)
    assert should is True
    assert "periodic" in reason


def test_trigger_periodic_cycle_no_match():
    """cycle % probe_interval != 0, no stagnation → trigger false."""
    cfg = _config(enabled=True)
    should, reason = should_run_universe_probe({"current_cycle": 3}, cfg)
    assert should is False
    assert reason == "no_trigger"


def test_trigger_novelty_stagnation():
    """external_novelty < 0.15 연속 3 cycle → trigger true."""
    cfg = _config(enabled=True)
    state = {
        "current_cycle": 3,  # not periodic
        "external_novelty_history": [0.1, 0.12, 0.08],
    }
    should, reason = should_run_universe_probe(state, cfg)
    assert should is True
    assert "novelty_stagnation" in reason


def test_trigger_novelty_not_stagnant():
    """external_novelty 중 하나라도 >= 0.15 → stagnation 미충족."""
    cfg = _config(enabled=True)
    state = {
        "current_cycle": 3,
        "external_novelty_history": [0.1, 0.2, 0.08],  # 0.2 >= 0.15
    }
    should, reason = should_run_universe_probe(state, cfg)
    assert should is False


def test_trigger_novelty_insufficient_history():
    """history < 3 cycles → stagnation 판정 불가."""
    cfg = _config(enabled=True)
    state = {
        "current_cycle": 2,
        "external_novelty_history": [0.05, 0.05],
    }
    should, reason = should_run_universe_probe(state, cfg)
    assert should is False


def test_trigger_cycle_zero_no_trigger():
    """cycle 0 → periodic 조건 미충족."""
    cfg = _config(enabled=True)
    should, reason = should_run_universe_probe({"current_cycle": 0}, cfg)
    assert should is False
