"""Silver P1-C1: entity_resolver 단위 테스트.

S4: alias equivalence, S5: is_a inheritance.
최소 8 테스트.
"""

from __future__ import annotations

import pytest

from src.utils.entity_resolver import (
    canonicalize_entity_key,
    resolve_alias,
    resolve_is_a,
)

# --- Fixtures ---

SKELETON_WITH_ALIASES = {
    "aliases": {
        "japan-travel:pass-ticket:jr-pass": [
            "japan-rail-pass",
            "재팬레일패스",
            "japan-travel:pass-ticket:japan-rail-pass",
        ],
        "japan-travel:transport:shinkansen": ["bullet-train", "신칸센"],
        "japan-travel:connectivity:pocket-wifi": ["portable-wifi", "포켓와이파이"],
    },
    "is_a": {
        "japan-travel:transport:shinkansen": "japan-travel:transport:train",
        "japan-travel:transport:narita-express": "japan-travel:transport:train",
        "japan-travel:transport:train": "japan-travel:transport:rail",
    },
}

SKELETON_EMPTY: dict = {}

SKELETON_NO_ALIAS_NO_IS_A = {
    "domain": "japan-travel",
    "categories": [{"slug": "transport"}],
}


# --- S4: Alias Equivalence Tests ---


class TestResolveAlias:
    """S4 scenario — 동의어 2개 (JR-Pass / 재팬레일패스)."""

    def test_alias_forward(self) -> None:
        """alias → canonical (재팬레일패스 → jr-pass)."""
        result = resolve_alias("재팬레일패스", SKELETON_WITH_ALIASES)
        assert result == "japan-travel:pass-ticket:jr-pass"

    def test_alias_reverse(self) -> None:
        """다른 alias → same canonical."""
        result = resolve_alias("japan-rail-pass", SKELETON_WITH_ALIASES)
        assert result == "japan-travel:pass-ticket:jr-pass"

    def test_canonical_identity(self) -> None:
        """canonical key 자체는 자기 자신 반환."""
        result = resolve_alias("japan-travel:pass-ticket:jr-pass", SKELETON_WITH_ALIASES)
        assert result == "japan-travel:pass-ticket:jr-pass"

    def test_full_key_alias(self) -> None:
        """full entity_key 형식 alias → canonical."""
        result = resolve_alias(
            "japan-travel:pass-ticket:japan-rail-pass", SKELETON_WITH_ALIASES,
        )
        assert result == "japan-travel:pass-ticket:jr-pass"

    def test_no_alias_passthrough(self) -> None:
        """alias 맵에 없는 key → 원본 반환."""
        result = resolve_alias("japan-travel:transport:taxi", SKELETON_WITH_ALIASES)
        assert result == "japan-travel:transport:taxi"

    def test_empty_skeleton(self) -> None:
        """빈 skeleton → 원본 반환."""
        result = resolve_alias("japan-travel:pass-ticket:jr-pass", SKELETON_EMPTY)
        assert result == "japan-travel:pass-ticket:jr-pass"

    def test_case_insensitive(self) -> None:
        """alias 매칭은 case-insensitive."""
        result = resolve_alias("Bullet-Train", SKELETON_WITH_ALIASES)
        assert result == "japan-travel:transport:shinkansen"


# --- S5: is_a Inheritance Tests ---


class TestResolveIsA:
    """S5 scenario — shinkansen is_a train."""

    def test_single_parent(self) -> None:
        """shinkansen → [train]."""
        chain = resolve_is_a("japan-travel:transport:shinkansen", SKELETON_WITH_ALIASES)
        assert "japan-travel:transport:train" in chain

    def test_two_level_chain(self) -> None:
        """shinkansen → train → rail (2단 chain)."""
        chain = resolve_is_a("japan-travel:transport:shinkansen", SKELETON_WITH_ALIASES)
        assert len(chain) >= 2
        assert chain[0] == "japan-travel:transport:train"
        assert chain[1] == "japan-travel:transport:rail"

    def test_no_is_a_returns_empty(self) -> None:
        """is_a 관계 없는 entity → 빈 리스트."""
        chain = resolve_is_a("japan-travel:transport:taxi", SKELETON_WITH_ALIASES)
        assert chain == []

    def test_empty_skeleton_returns_empty(self) -> None:
        """빈 skeleton → 빈 리스트."""
        chain = resolve_is_a("japan-travel:transport:shinkansen", SKELETON_EMPTY)
        assert chain == []

    def test_circular_protection(self) -> None:
        """순환 is_a → 무한루프 없이 중단."""
        circular_skeleton = {
            "is_a": {
                "a": "b",
                "b": "c",
                "c": "a",  # 순환
            },
        }
        chain = resolve_is_a("a", circular_skeleton)
        assert len(chain) <= 5  # depth limit


# --- Canonicalize Tests ---


class TestCanonicalizeEntityKey:
    def test_alias_resolution(self) -> None:
        """alias + lowercase + space→hyphen."""
        result = canonicalize_entity_key("Japan Rail Pass", SKELETON_WITH_ALIASES)
        assert result == "japan-travel:pass-ticket:jr-pass"

    def test_idempotent(self) -> None:
        """이미 canonical 인 key 에 적용해도 동일."""
        key = "japan-travel:pass-ticket:jr-pass"
        assert canonicalize_entity_key(key, SKELETON_WITH_ALIASES) == key
        # 두 번 적용
        assert canonicalize_entity_key(
            canonicalize_entity_key(key, SKELETON_WITH_ALIASES),
            SKELETON_WITH_ALIASES,
        ) == key

    def test_no_skeleton_fields(self) -> None:
        """aliases/is_a 없는 skeleton → lowercase 정규화만."""
        result = canonicalize_entity_key(
            "Japan-Travel:Transport:TAXI", SKELETON_NO_ALIAS_NO_IS_A,
        )
        assert result == "japan-travel:transport:taxi"

    def test_missing_field_handling(self) -> None:
        """skeleton 에 aliases 필드 없어도 에러 없이 처리."""
        result = canonicalize_entity_key("some-key", {})
        assert result == "some-key"
