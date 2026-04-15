"""P4-D1: novelty 단위 테스트."""

from __future__ import annotations

import pytest

from src.utils.novelty import compute_novelty


def _make_ku(entity_key: str, field: str, claim: str = "") -> dict:
    return {
        "status": "active",
        "entity_key": entity_key,
        "field": field,
        "claim": claim,
    }


class TestComputeNovelty:
    """compute_novelty 기본 동작."""

    def test_identical_kus_returns_zero(self):
        """완전 동일 KU → novelty 0."""
        kus = [
            _make_ku("d:cat:a", "price", "100 yen"),
            _make_ku("d:cat:b", "name", "item B"),
        ]
        assert compute_novelty(kus, kus) == 0.0

    def test_completely_new_kus_returns_one(self):
        """이전 KU 와 겹침 0 → novelty 1."""
        prev = [_make_ku("d:cat:a", "price", "100 yen")]
        curr = [_make_ku("d:food:x", "taste", "spicy noodle")]
        result = compute_novelty(prev, curr)
        assert result == 1.0

    def test_partial_overlap(self):
        """일부 겹침 → 0 < novelty < 1."""
        prev = [
            _make_ku("d:cat:a", "price", "100 yen"),
            _make_ku("d:cat:b", "name", "item B"),
        ]
        curr = [
            _make_ku("d:cat:a", "price", "100 yen"),  # 동일
            _make_ku("d:food:c", "taste", "spicy"),    # 새로
        ]
        result = compute_novelty(prev, curr)
        assert 0.0 < result < 1.0

    def test_empty_prev_returns_one(self):
        """이전 없으면 전부 새로 → 1."""
        curr = [_make_ku("d:cat:a", "price", "100")]
        assert compute_novelty([], curr) == 1.0

    def test_both_empty_returns_zero(self):
        """둘 다 비면 0."""
        assert compute_novelty([], []) == 0.0

    def test_empty_curr_partial(self):
        """현재 비면 novelty > 0 (이전 대비 전부 사라짐)."""
        prev = [_make_ku("d:cat:a", "price", "100")]
        # curr 가 비면 claim/entity/token 모두 빈 set
        # jaccard(non-empty, empty) = 0 → sim=0 → novelty=1
        result = compute_novelty(prev, [])
        assert result > 0.0

    def test_inactive_kus_excluded(self):
        """inactive KU 는 계산에서 제외."""
        prev = [_make_ku("d:cat:a", "price", "100")]
        curr = [
            {"status": "superseded", "entity_key": "d:cat:a", "field": "price", "claim": "100"},
            _make_ku("d:food:b", "name", "ramen"),
        ]
        # prev 의 d:cat:a:price 와 curr 의 active 만(d:food:b:name) → 겹침 0 → novelty 1
        result = compute_novelty(prev, curr)
        assert result == 1.0

    def test_custom_weights(self):
        """가중치 변경 시 결과 변화."""
        prev = [_make_ku("d:cat:a", "price", "100 yen")]
        curr = [_make_ku("d:cat:a", "name", "item A")]
        # entity 동일, claim/token 다름
        w_entity_heavy = compute_novelty(prev, curr, weights=(0.1, 0.8, 0.1))
        w_claim_heavy = compute_novelty(prev, curr, weights=(0.8, 0.1, 0.1))
        # entity 겹침 높으면 entity 가중 시 novelty 낮아야 함
        assert w_entity_heavy < w_claim_heavy
