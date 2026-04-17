"""SI-P4 Stage E / E1-4: external_novelty 단위 테스트."""

from __future__ import annotations

from src.utils.external_novelty import (
    claim_value_hash,
    compute_delta_kus,
    compute_external_novelty,
    extract_observation_keys,
)


def _item(entity_key: str, field: str) -> dict:
    return {"entity_key": entity_key, "field": field}


class TestComputeExternalNovelty:
    """compute_external_novelty 기본 동작."""

    def test_all_new_against_empty_history_returns_one(self):
        """history 비어 있으면 모든 관찰이 신규 → 1.0."""
        items = [_item("d:c:a", "price"), _item("d:c:b", "name")]
        score, new_keys = compute_external_novelty(items, None)
        assert score == 1.0
        assert new_keys == {"d:c:a|price", "d:c:b|name"}

    def test_all_seen_returns_zero(self):
        """모든 키가 history 에 있으면 → 0.0, new_keys 없음."""
        items = [_item("d:c:a", "price")]
        history = ["d:c:a|price"]
        score, new_keys = compute_external_novelty(items, history)
        assert score == 0.0
        assert new_keys == set()

    def test_partial_overlap_returns_fractional(self):
        """절반만 신규 → 0.5."""
        items = [
            _item("d:c:a", "price"),
            _item("d:c:a", "name"),
            _item("d:c:b", "price"),
            _item("d:c:b", "name"),
        ]
        history = ["d:c:a|price", "d:c:a|name"]
        score, new_keys = compute_external_novelty(items, history)
        assert score == 0.5
        assert new_keys == {"d:c:b|price", "d:c:b|name"}

    def test_empty_items_returns_zero(self):
        """현재 cycle 관찰이 없으면 → 0.0 (nothing to be novel about)."""
        score, new_keys = compute_external_novelty([], ["d:c:a|price"])
        assert score == 0.0
        assert new_keys == set()

    def test_missing_entity_or_field_filtered(self):
        """entity_key 또는 field 비어있으면 관찰 키에서 제외."""
        items = [
            {"entity_key": "", "field": "price"},   # drop
            {"entity_key": "d:c:x", "field": ""},    # drop
            _item("d:c:y", "note"),                  # keep
        ]
        keys = extract_observation_keys(items)
        assert keys == {"d:c:y|note"}

        score, new_keys = compute_external_novelty(items, None)
        assert score == 1.0
        assert new_keys == {"d:c:y|note"}


class TestComputeDeltaKus:
    """compute_delta_kus — prev/curr 대비 신규 KU 추출 (D-148)."""

    def test_all_new(self):
        """prev 없으면 curr 전체가 delta."""
        curr = [_item("d:c:a", "price"), _item("d:c:b", "name")]
        delta = compute_delta_kus([], curr)
        assert len(delta) == 2

    def test_no_new(self):
        """prev 와 curr 동일하면 delta 빈 목록."""
        kus = [_item("d:c:a", "price"), _item("d:c:a", "name")]
        delta = compute_delta_kus(kus, kus)
        assert delta == []

    def test_partial_new(self):
        """일부만 신규."""
        prev = [_item("d:c:a", "price")]
        curr = [_item("d:c:a", "price"), _item("d:c:b", "note")]
        delta = compute_delta_kus(prev, curr)
        assert len(delta) == 1
        assert delta[0]["entity_key"] == "d:c:b"

    def test_external_novelty_with_delta_avoids_convergence(self):
        """delta 기반 분모 사용 시 score 가 0 으로 수렴하지 않음.

        all_kus 기반이면 cycle 경과 후 score ≈ 0 (D-148 버그).
        delta 기반이면 신규 KU 가 있는 한 score ≥ 0 유지.
        """
        # 10 cycle 분 누적 KU (100개)
        history_kus = [_item(f"d:c:e{i}", "price") for i in range(100)]
        external_hist = [f"d:c:e{i}|price" for i in range(100)]

        # 이번 cycle 에 새 KU 5개 추가
        new_kus = [_item(f"d:c:new{j}", "price") for j in range(5)]
        all_kus = history_kus + new_kus

        # D-148 이전: all_kus 기반 → score = 5/105 ≈ 0.048
        score_old, _ = compute_external_novelty(all_kus, external_hist)
        assert score_old < 0.1

        # D-148 이후: delta_kus 기반 → score = 5/5 = 1.0
        delta = compute_delta_kus(history_kus, all_kus)
        score_new, _ = compute_external_novelty(delta, external_hist)
        assert score_new == 1.0


class TestClaimValueHash:
    """claim_value_hash 안정성 (보조 disambiguation 용도)."""

    def test_stable_across_dict_order_and_types(self):
        """같은 내용의 dict 는 키 순서 무관하게 동일 해시, string 도 stable."""
        h1 = claim_value_hash({"a": 1, "b": 2})
        h2 = claim_value_hash({"b": 2, "a": 1})
        assert h1 == h2

        s1 = claim_value_hash("hello")
        s2 = claim_value_hash("hello")
        assert s1 == s2

        # 다른 값은 다른 해시
        assert claim_value_hash({"a": 1}) != claim_value_hash({"a": 2})
