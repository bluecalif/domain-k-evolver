"""Tests for skeleton_tiers — candidate vs active category separation (D-139)."""
import pytest

from src.utils.skeleton_tiers import (
    TIER_ACTIVE,
    TIER_CANDIDATE,
    add_candidate_category,
    find_category,
    get_active_categories,
    get_active_category_slugs,
    get_candidate_categories,
    get_candidate_category_slugs,
    promote_candidate,
    reject_candidate,
)


def _base_skeleton():
    return {
        "domain": "japan-travel",
        "categories": [
            {"slug": "transport", "description": "교통"},
            {"slug": "dining", "description": "식당"},
        ],
    }


def _valid_candidate(slug="accessibility", cycle=3):
    return {
        "slug": slug,
        "name": "Accessibility",
        "rationale": "Wheelchair/mobility info missing",
        "expected_source": "gov.jp/accessibility",
        "type": "NEW_CATEGORY",
        "proposed_at_cycle": cycle,
    }


def test_active_readers_ignore_candidates():
    skel = _base_skeleton()
    add_candidate_category(skel, _valid_candidate())
    # 핵심 불변: 기존 skeleton["categories"] 접근 경로가 candidate 를 보지 않음
    assert get_active_category_slugs(skel) == ["transport", "dining"]
    assert "accessibility" in get_candidate_category_slugs(skel)
    assert len(skel["categories"]) == 2
    assert len(skel["candidate_categories"]) == 1


def test_add_candidate_normalizes_defaults():
    skel = _base_skeleton()
    entry = add_candidate_category(skel, _valid_candidate())
    assert entry["status"] == "pending_validation"
    assert entry["evidence"] is None


def test_add_candidate_rejects_active_slug_collision():
    skel = _base_skeleton()
    with pytest.raises(ValueError, match="active"):
        add_candidate_category(skel, _valid_candidate(slug="transport"))


def test_add_candidate_rejects_duplicate_candidate():
    skel = _base_skeleton()
    add_candidate_category(skel, _valid_candidate())
    with pytest.raises(ValueError, match="candidate"):
        add_candidate_category(skel, _valid_candidate())


def test_add_candidate_validates_schema():
    skel = _base_skeleton()
    bad = _valid_candidate()
    del bad["rationale"]
    with pytest.raises(ValueError, match="missing"):
        add_candidate_category(skel, bad)

    bad_type = _valid_candidate(slug="budget")
    bad_type["type"] = "INVALID"
    with pytest.raises(ValueError, match="type"):
        add_candidate_category(skel, bad_type)


def test_promote_candidate_moves_to_active():
    skel = _base_skeleton()
    add_candidate_category(skel, _valid_candidate())
    promote_candidate(skel, "accessibility", description="접근성")

    assert "accessibility" in get_active_category_slugs(skel)
    assert "accessibility" not in get_candidate_category_slugs(skel)
    active = [c for c in skel["categories"] if c["slug"] == "accessibility"][0]
    assert active["description"] == "접근성"


def test_promote_unknown_slug_raises():
    skel = _base_skeleton()
    with pytest.raises(ValueError, match="not found"):
        promote_candidate(skel, "nonexistent")


def test_reject_candidate_removes_entry():
    skel = _base_skeleton()
    add_candidate_category(skel, _valid_candidate())
    removed = reject_candidate(skel, "accessibility")
    assert removed["status"] == "rejected"
    assert get_candidate_category_slugs(skel) == []


def test_find_category_tier_distinction():
    skel = _base_skeleton()
    add_candidate_category(skel, _valid_candidate())

    tier, entry = find_category(skel, "transport")
    assert tier == TIER_ACTIVE
    assert entry["slug"] == "transport"

    tier, entry = find_category(skel, "accessibility")
    assert tier == TIER_CANDIDATE
    assert entry["type"] == "NEW_CATEGORY"

    assert find_category(skel, "nonexistent") is None


def test_getters_return_copies_not_references():
    skel = _base_skeleton()
    add_candidate_category(skel, _valid_candidate())
    actives = get_active_categories(skel)
    candidates = get_candidate_categories(skel)
    actives.clear()
    candidates.clear()
    assert len(skel["categories"]) == 2
    assert len(skel["candidate_categories"]) == 1
