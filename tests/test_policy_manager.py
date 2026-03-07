"""PolicyManager 테스트 — Phase 4 Task 4.4."""

import copy

import pytest

from src.utils.policy_manager import (
    MAX_PATCHES_PER_APPLY,
    _get_nested,
    _set_nested,
    apply_patches,
    compute_credibility_stats,
    learn_credibility,
    rollback,
    should_rollback,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_policies():
    return {
        "credibility_priors": {
            "official": 0.95,
            "public": 0.80,
            "platform": 0.65,
            "personal": 0.40,
        },
        "ttl_defaults": {
            "price": 180,
            "policy": 90,
            "hours": 90,
        },
        "cross_validation": {
            "safety": {"min_independent_sources": 2, "min_credibility": 0.80},
            "convenience": {"min_independent_sources": 1, "min_credibility": 0.70},
        },
        "conflict_resolution": {
            "source_priority": ["official", "public", "platform", "personal"],
        },
    }


@pytest.fixture()
def sample_patches():
    return [
        {
            "patch_id": "PP-001",
            "target_field": "ttl_defaults.price",
            "current_value": 180,
            "proposed_value": 270,
            "reason": "yield 체감",
        },
        {
            "patch_id": "PP-002",
            "target_field": "cross_validation.convenience.min_sources",
            "current_value": 1,
            "proposed_value": 2,
            "reason": "multi_evidence_rate 부족",
        },
    ]


# ---------------------------------------------------------------------------
# _get_nested / _set_nested
# ---------------------------------------------------------------------------

class TestNestedHelpers:
    def test_get_nested_simple(self, sample_policies):
        assert _get_nested(sample_policies, "ttl_defaults.price") == 180

    def test_get_nested_deep(self, sample_policies):
        val = _get_nested(sample_policies, "cross_validation.safety.min_credibility")
        assert val == 0.80

    def test_get_nested_missing_raises(self, sample_policies):
        with pytest.raises(KeyError):
            _get_nested(sample_policies, "ttl_defaults.nonexistent")

    def test_set_nested_existing(self, sample_policies):
        _set_nested(sample_policies, "ttl_defaults.price", 300)
        assert sample_policies["ttl_defaults"]["price"] == 300

    def test_set_nested_creates_path(self):
        d = {"a": {}}
        _set_nested(d, "a.b.c", 42)
        assert d["a"]["b"]["c"] == 42

    def test_set_nested_top_level(self):
        d = {}
        _set_nested(d, "version", 1)
        assert d["version"] == 1


# ---------------------------------------------------------------------------
# apply_patches
# ---------------------------------------------------------------------------

class TestApplyPatches:
    def test_basic_apply(self, sample_policies, sample_patches):
        new_pol, applied = apply_patches(sample_policies, sample_patches, cycle=5)

        assert len(applied) == 2
        assert new_pol["ttl_defaults"]["price"] == 270
        assert new_pol["cross_validation"]["convenience"]["min_sources"] == 2

    def test_version_increment(self, sample_policies, sample_patches):
        new_pol, _ = apply_patches(sample_policies, sample_patches, cycle=5)
        assert new_pol["version"] == 1  # 0 → 1

    def test_version_increment_from_existing(self, sample_policies, sample_patches):
        sample_policies["version"] = 3
        new_pol, _ = apply_patches(sample_policies, sample_patches, cycle=5)
        assert new_pol["version"] == 4

    def test_change_history_added(self, sample_policies, sample_patches):
        new_pol, _ = apply_patches(sample_policies, sample_patches, cycle=5)

        history = new_pol["change_history"]
        assert len(history) == 1
        assert history[0]["cycle"] == 5
        assert history[0]["patches_applied"] == ["PP-001", "PP-002"]
        assert "timestamp" in history[0]

    def test_original_not_mutated(self, sample_policies, sample_patches):
        original = copy.deepcopy(sample_policies)
        apply_patches(sample_policies, sample_patches, cycle=5)
        assert sample_policies == original

    def test_empty_patches(self, sample_policies):
        new_pol, applied = apply_patches(sample_policies, [])
        assert applied == []
        assert new_pol is sample_policies  # 변경 없으면 원본 반환

    def test_max_patches_limit(self, sample_policies):
        patches = [
            {
                "patch_id": f"PP-{i:03d}",
                "target_field": f"ttl_defaults.field_{i}",
                "current_value": 0,
                "proposed_value": i * 10,
                "reason": "test",
            }
            for i in range(5)
        ]
        _, applied = apply_patches(sample_policies, patches, cycle=1)
        assert len(applied) == MAX_PATCHES_PER_APPLY

    def test_invalid_patch_skipped(self, sample_policies):
        patches = [
            {"patch_id": "PP-BAD", "target_field": "", "proposed_value": 1},
            {
                "patch_id": "PP-001",
                "target_field": "ttl_defaults.price",
                "current_value": 180,
                "proposed_value": 270,
                "reason": "ok",
            },
        ]
        _, applied = apply_patches(sample_policies, patches, cycle=1)
        assert len(applied) == 1
        assert applied[0]["patch_id"] == "PP-001"

    def test_patch_missing_proposed_value(self, sample_policies):
        patches = [{"patch_id": "PP-BAD", "target_field": "ttl_defaults.price"}]
        _, applied = apply_patches(sample_policies, patches, cycle=1)
        assert len(applied) == 0

    def test_history_accumulates(self, sample_policies, sample_patches):
        pol1, _ = apply_patches(sample_policies, sample_patches[:1], cycle=5)
        pol2, _ = apply_patches(pol1, sample_patches[1:], cycle=10)

        assert len(pol2["change_history"]) == 2
        assert pol2["version"] == 2


# ---------------------------------------------------------------------------
# rollback
# ---------------------------------------------------------------------------

class TestRollback:
    def test_basic_rollback(self, sample_policies, sample_patches):
        new_pol, _ = apply_patches(sample_policies, sample_patches, cycle=5)
        rolled = rollback(new_pol, sample_policies, cycle=6)

        # 값은 원래로 복원
        assert rolled["ttl_defaults"]["price"] == 180
        # version은 증가
        assert rolled["version"] == 2  # 1 → 2

    def test_rollback_history_preserved(self, sample_policies, sample_patches):
        new_pol, _ = apply_patches(sample_policies, sample_patches, cycle=5)
        rolled = rollback(new_pol, sample_policies, cycle=6, reason="test_reason")

        history = rolled["change_history"]
        assert len(history) == 2  # apply + rollback
        assert history[-1]["patches_applied"] == ["ROLLBACK"]
        assert history[-1]["reason"] == "test_reason"
        assert history[-1]["cycle"] == 6

    def test_rollback_does_not_mutate_originals(self, sample_policies, sample_patches):
        new_pol, _ = apply_patches(sample_policies, sample_patches, cycle=5)
        orig_new = copy.deepcopy(new_pol)
        orig_old = copy.deepcopy(sample_policies)

        rollback(new_pol, sample_policies, cycle=6)

        assert new_pol == orig_new
        assert sample_policies == orig_old


# ---------------------------------------------------------------------------
# should_rollback
# ---------------------------------------------------------------------------

class TestShouldRollback:
    def test_no_rollback_when_stable(self):
        prev = {"evidence_rate": 0.80, "gap_resolution_rate": 0.60}
        curr = {"evidence_rate": 0.78, "gap_resolution_rate": 0.58}
        assert should_rollback(curr, prev) is False

    def test_rollback_on_evidence_rate_drop(self):
        prev = {"evidence_rate": 0.80, "gap_resolution_rate": 0.60}
        curr = {"evidence_rate": 0.70, "gap_resolution_rate": 0.60}
        assert should_rollback(curr, prev) is True

    def test_rollback_on_gap_resolution_drop(self):
        prev = {"evidence_rate": 0.80, "gap_resolution_rate": 0.60}
        curr = {"evidence_rate": 0.80, "gap_resolution_rate": 0.50}
        assert should_rollback(curr, prev) is True

    def test_custom_threshold(self):
        prev = {"evidence_rate": 0.80, "gap_resolution_rate": 0.60}
        curr = {"evidence_rate": 0.70, "gap_resolution_rate": 0.60}
        # threshold=0.15이면 0.10 하락은 허용
        assert should_rollback(curr, prev, threshold=0.15) is False

    def test_no_rollback_when_prev_zero(self):
        prev = {"evidence_rate": 0.0, "gap_resolution_rate": 0.0}
        curr = {"evidence_rate": 0.0, "gap_resolution_rate": 0.0}
        assert should_rollback(curr, prev) is False

    def test_improvement_no_rollback(self):
        prev = {"evidence_rate": 0.60, "gap_resolution_rate": 0.40}
        curr = {"evidence_rate": 0.80, "gap_resolution_rate": 0.60}
        assert should_rollback(curr, prev) is False


# ---------------------------------------------------------------------------
# compute_credibility_stats
# ---------------------------------------------------------------------------

class TestComputeCredibilityStats:
    def test_basic_stats(self):
        kus = [
            {"ku_id": "KU-1", "source_type": "official", "status": "active", "confidence": 0.95},
            {"ku_id": "KU-2", "source_type": "official", "status": "active", "confidence": 0.90},
            {"ku_id": "KU-3", "source_type": "personal", "status": "disputed", "confidence": 0.40},
            {"ku_id": "KU-4", "source_type": "personal", "status": "active", "confidence": 0.50},
            {"ku_id": "KU-5", "source_type": "personal", "status": "deprecated", "confidence": 0.30},
        ]
        stats = compute_credibility_stats(kus)

        assert stats["official"]["total"] == 2
        assert stats["official"]["disputed"] == 0
        assert stats["personal"]["total"] == 3
        assert stats["personal"]["disputed"] == 1
        assert stats["personal"]["deprecated"] == 1

    def test_no_source_type_skipped(self):
        kus = [
            {"ku_id": "KU-1", "status": "active", "confidence": 0.9},
            {"ku_id": "KU-2", "source_type": "official", "status": "active", "confidence": 0.9},
        ]
        stats = compute_credibility_stats(kus)
        assert "official" in stats
        assert len(stats) == 1

    def test_empty_kus(self):
        assert compute_credibility_stats([]) == {}

    def test_avg_confidence(self):
        kus = [
            {"ku_id": "KU-1", "source_type": "public", "status": "active", "confidence": 0.80},
            {"ku_id": "KU-2", "source_type": "public", "status": "active", "confidence": 0.60},
        ]
        stats = compute_credibility_stats(kus)
        assert stats["public"]["avg_confidence"] == 0.70


# ---------------------------------------------------------------------------
# learn_credibility
# ---------------------------------------------------------------------------

class TestLearnCredibility:
    def test_downgrade_high_dispute_rate(self):
        stats = {
            "personal": {"total": 10, "disputed": 3, "deprecated": 1, "avg_confidence": 0.40},
        }
        priors = {"personal": 0.40}
        patches = learn_credibility(stats, priors)

        assert len(patches) == 1
        assert patches[0]["proposed_value"] == 0.35
        assert "personal" in patches[0]["target_field"]

    def test_upgrade_high_quality(self):
        stats = {
            "official": {"total": 10, "disputed": 0, "deprecated": 0, "avg_confidence": 0.95},
        }
        priors = {"official": 0.90}
        patches = learn_credibility(stats, priors)

        assert len(patches) == 1
        assert patches[0]["proposed_value"] == 0.95

    def test_no_change_middle_ground(self):
        stats = {
            "platform": {"total": 10, "disputed": 2, "deprecated": 0, "avg_confidence": 0.65},
        }
        priors = {"platform": 0.65}
        patches = learn_credibility(stats, priors)
        assert len(patches) == 0

    def test_min_samples_filter(self):
        stats = {
            "personal": {"total": 2, "disputed": 2, "deprecated": 0, "avg_confidence": 0.30},
        }
        priors = {"personal": 0.40}
        patches = learn_credibility(stats, priors, min_samples=3)
        assert len(patches) == 0

    def test_prior_floor(self):
        stats = {
            "personal": {"total": 10, "disputed": 5, "deprecated": 3, "avg_confidence": 0.20},
        }
        priors = {"personal": 0.10}
        patches = learn_credibility(stats, priors)
        assert len(patches) == 0  # 이미 최저

    def test_prior_ceiling(self):
        stats = {
            "official": {"total": 10, "disputed": 0, "deprecated": 0, "avg_confidence": 0.99},
        }
        priors = {"official": 0.99}
        patches = learn_credibility(stats, priors)
        assert len(patches) == 0  # 이미 최고

    def test_unknown_source_type_ignored(self):
        stats = {
            "unknown_type": {"total": 10, "disputed": 5, "deprecated": 0, "avg_confidence": 0.40},
        }
        priors = {"official": 0.95}
        patches = learn_credibility(stats, priors)
        assert len(patches) == 0

    def test_custom_adjustment_rate(self):
        stats = {
            "personal": {"total": 10, "disputed": 4, "deprecated": 0, "avg_confidence": 0.40},
        }
        priors = {"personal": 0.40}
        patches = learn_credibility(stats, priors, adjustment_rate=0.10)
        assert patches[0]["proposed_value"] == 0.30
