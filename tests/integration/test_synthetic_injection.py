"""E7-1 Synthetic Injection: universe_probe ground-truth 검증.

목적: skeleton 에서 "알려진 진짜" 카테고리를 의도적으로 숨긴 상태에서,
universe_probe 4-step pipeline (survey→evidence→validate→register) 이
그 카테고리를 표면화 (candidate_categories 에 등록) 하는지 검증.

mock LLM/Tavily 로 합성 환경에서 실행하므로 API 비용 0.
실 벤치 (E7-2) 와 분리 — 메커니즘 검증용.

Ground truth (japan-travel 도메인 가정):
  - accessibility (장애인 여행 정보)
  - seasonality  (성수기/비수기)
  - budget-extremes (백패커/럭셔리)
"""
from __future__ import annotations

import json
from dataclasses import replace
from unittest.mock import MagicMock

from src.config import EvolverConfig, ExternalAnchorConfig
from src.nodes.universe_probe import (
    gather_evidence,
    register_validated,
    run_universe_probe,
    validate_proposals,
)
from src.utils.cost_guard import CostGuard
from src.utils.skeleton_tiers import get_active_category_slugs


# Ground truth — 도메인 전문가 기준 "마땅히 있어야 할" 카테고리들
GROUND_TRUTH_CATEGORIES = {
    "accessibility": {
        "name": "Accessibility",
        "rationale": "wheelchair, sign-language, sensory-friendly travel info",
        "expected_source": "gov.jp / accessible-japan.com",
    },
    "seasonality": {
        "name": "Seasonality",
        "rationale": "peak/off-season pricing, weather, crowd patterns",
        "expected_source": "JNTO seasonal guides",
    },
    "budget-extremes": {
        "name": "Budget Extremes",
        "rationale": "backpacker hostels and ultra-luxury ryokan",
        "expected_source": "hostel/ryokan booking aggregators",
    },
}


def _config_enabled() -> EvolverConfig:
    cfg = EvolverConfig()
    return replace(cfg, external_anchor=ExternalAnchorConfig(
        enabled=True, llm_budget_per_run=20, tavily_budget_per_run=20,
    ))


def _hidden_skeleton() -> dict:
    """Ground truth 카테고리들을 숨긴 skeleton — 의도적으로 transport/dining만."""
    return {
        "domain": "japan-travel",
        "categories": [
            {"slug": "transport"},
            {"slug": "dining"},
        ],
        "fields": [{"name": "price"}, {"name": "hours"}],
    }


def _state_with_hints() -> dict:
    """KU 에 ground-truth 관련 entity 힌트를 일부 노출 — LLM 판단 근거."""
    return {
        "cycle": 5,
        "current_cycle": 5,
        "domain_skeleton": _hidden_skeleton(),
        "knowledge_units": [
            {"entity_key": "japan-travel:transport:jr-pass"},
            {"entity_key": "japan-travel:dining:sushi-etiquette"},
            # 힌트: 다른 카테고리 entity 가 잘못된 위치에 등장
            {"entity_key": "japan-travel:transport:wheelchair-rental"},
            {"entity_key": "japan-travel:dining:cherry-blossom-menu"},
        ],
    }


def _make_survey_llm(propose_slugs: list[str], noise_slugs: list[str] | None = None):
    """survey LLM mock — ground-truth + (선택) noise proposals 반환."""
    proposals = []
    for slug in propose_slugs:
        gt = GROUND_TRUTH_CATEGORIES.get(slug, {})
        proposals.append({
            "slug": slug,
            "name": gt.get("name", slug.title()),
            "rationale": gt.get("rationale", "synthetic"),
            "expected_source": gt.get("expected_source", "web"),
            "type": "NEW_CATEGORY",
        })
    for slug in (noise_slugs or []):
        proposals.append({
            "slug": slug,
            "name": slug.title(),
            "rationale": "noise — does not exist as distinct knowledge area",
            "expected_source": "n/a",
            "type": "NEW_CATEGORY",
        })
    llm = MagicMock()
    resp = MagicMock()
    resp.content = json.dumps({"proposals": proposals})
    llm.invoke.return_value = resp
    return llm


def _make_validator_llm(ground_truth_slugs: set[str]):
    """validator LLM mock — ground truth 는 pass, 그 외는 fail."""
    def _side_effect(prompt: str):
        # Validator prompt 에는 "Proposed category: {slug}" 라인이 들어감
        slug_match = None
        for line in prompt.splitlines():
            if line.startswith("Proposed category:"):
                slug_match = line.split(":", 2)[1].strip().split(" ")[0].strip()
                break
        resp = MagicMock()
        if slug_match in ground_truth_slugs:
            resp.content = json.dumps({
                "exists": True, "confidence": 0.88,
                "source_diversity": 3,
                "sample_entity_names": [f"{slug_match}-example-1", f"{slug_match}-example-2"],
            })
        else:
            resp.content = json.dumps({
                "exists": False, "confidence": 0.2,
                "source_diversity": 1, "sample_entity_names": [],
            })
        return resp

    llm = MagicMock()
    llm.invoke.side_effect = _side_effect
    return llm


def _make_search(snippet_count: int = 3):
    """Tavily mock — 모든 query 에 동일한 snippets."""
    search = MagicMock()
    search.search.return_value = [
        {"url": f"https://src{i}.com", "title": f"T{i}", "snippet": f"snippet {i}"}
        for i in range(snippet_count)
    ]
    return search


def _run_full_pipeline(state, cfg, guard, survey_llm, search, validator_llm):
    """4-step pipeline 실행 헬퍼."""
    survey = run_universe_probe(state, survey_llm, cfg, guard, cycle=5)
    assert survey["status"] == "ok"

    domain = state["domain_skeleton"]["domain"]
    evidenced, _ = gather_evidence(survey["proposals"], search, guard, domain)
    validated, _ = validate_proposals(evidenced, validator_llm, guard, min_confidence=0.6)
    skeleton = state["domain_skeleton"]
    registered, errors = register_validated(validated, skeleton)
    return {
        "survey": survey,
        "evidenced": evidenced,
        "validated": validated,
        "registered": registered,
        "errors": errors,
        "skeleton": skeleton,
    }


def test_single_hidden_category_surfaced():
    """ground truth 1개 (accessibility) 숨김 → 4-step pipeline 통과 후 candidate 등록."""
    cfg = _config_enabled()
    guard = CostGuard(cfg.external_anchor)
    state = _state_with_hints()

    survey_llm = _make_survey_llm(propose_slugs=["accessibility"])
    validator_llm = _make_validator_llm({"accessibility"})

    result = _run_full_pipeline(
        state, cfg, guard, survey_llm, _make_search(), validator_llm,
    )

    assert len(result["registered"]) == 1
    assert result["registered"][0]["slug"] == "accessibility"
    assert result["registered"][0]["status"] == "validated"
    assert result["registered"][0]["validation"]["confidence"] >= 0.6

    candidate_slugs = {
        c["slug"] for c in result["skeleton"].get("candidate_categories", [])
    }
    assert "accessibility" in candidate_slugs

    # active categories 는 불변 (D-139)
    active = set(get_active_category_slugs(result["skeleton"]))
    assert "accessibility" not in active
    assert active == {"transport", "dining"}


def test_multiple_hidden_categories_surfaced():
    """ground truth 3개 모두 표면화되는지 검증."""
    cfg = _config_enabled()
    guard = CostGuard(cfg.external_anchor)
    state = _state_with_hints()

    truths = ["accessibility", "seasonality", "budget-extremes"]
    survey_llm = _make_survey_llm(propose_slugs=truths)
    validator_llm = _make_validator_llm(set(truths))

    result = _run_full_pipeline(
        state, cfg, guard, survey_llm, _make_search(), validator_llm,
    )

    registered_slugs = {r["slug"] for r in result["registered"]}
    assert registered_slugs == set(truths)

    candidate_slugs = {
        c["slug"] for c in result["skeleton"].get("candidate_categories", [])
    }
    for slug in truths:
        assert slug in candidate_slugs


def test_noise_proposals_filtered_by_validator():
    """ground truth + noise 혼재 → validator 가 noise 만 거부, ground truth 만 등록."""
    cfg = _config_enabled()
    guard = CostGuard(cfg.external_anchor)
    state = _state_with_hints()

    truths = ["accessibility", "seasonality"]
    noise = ["zzz-fictional", "qqq-nonexistent"]
    survey_llm = _make_survey_llm(propose_slugs=truths, noise_slugs=noise)
    validator_llm = _make_validator_llm(set(truths))

    result = _run_full_pipeline(
        state, cfg, guard, survey_llm, _make_search(), validator_llm,
    )

    # survey 단계에서 4개 모두 통과 (slug collision 없음)
    assert len(result["survey"]["proposals"]) == 4
    # validator 가 noise 2개 거부 → ground truth 2개만 등록
    assert len(result["registered"]) == 2
    registered_slugs = {r["slug"] for r in result["registered"]}
    assert registered_slugs == set(truths)
    # noise 는 candidate 등록 안 됨
    candidate_slugs = {
        c["slug"] for c in result["skeleton"].get("candidate_categories", [])
    }
    for n in noise:
        assert n not in candidate_slugs


def test_collision_with_active_skeleton_rejected_in_survey():
    """ground truth 가 이미 active skeleton 에 있으면 survey 단계에서 reject."""
    cfg = _config_enabled()
    guard = CostGuard(cfg.external_anchor)
    state = _state_with_hints()
    # 이미 transport 가 active 인 상태에서 transport 를 다시 propose
    survey_llm = _make_survey_llm(propose_slugs=["accessibility", "transport"])
    validator_llm = _make_validator_llm({"accessibility"})

    result = _run_full_pipeline(
        state, cfg, guard, survey_llm, _make_search(), validator_llm,
    )

    # survey: accessibility 만 accepted, transport 는 rejected
    survey = result["survey"]
    accepted_slugs = {p["slug"] for p in survey["proposals"]}
    rejected = survey["rejected"]
    assert "accessibility" in accepted_slugs
    assert "transport" not in accepted_slugs
    assert any(r.get("_reject_reason") == "collision_active" for r in rejected)
    # 최종 등록은 accessibility 1개
    assert len(result["registered"]) == 1
    assert result["registered"][0]["slug"] == "accessibility"
