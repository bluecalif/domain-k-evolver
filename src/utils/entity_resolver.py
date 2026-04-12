"""entity_resolver — Alias / is_a 해상도 + entity_key canonicalization.

Silver P1-A1: skeleton 의 aliases / is_a 맵 기반으로
동의어를 canonical key 로 치환하고 is_a 계층 체인을 반환한다.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# is_a chain 순환 방지 depth limit (D-97)
_IS_A_DEPTH_LIMIT = 5


def _build_reverse_alias_map(skeleton: dict) -> dict[str, str]:
    """aliases → {alias_lower: canonical_key} 역방향 맵 생성.

    skeleton["aliases"] 포맷: {canonical_key: [alias1, alias2, ...]}
    canonical_key 자신도 자기 자신으로 매핑한다.
    """
    reverse: dict[str, str] = {}
    aliases = skeleton.get("aliases", {})
    for canonical, alias_list in aliases.items():
        canonical_lower = canonical.strip().lower()
        reverse[canonical_lower] = canonical_lower
        for alias in alias_list:
            alias_lower = alias.strip().lower()
            reverse[alias_lower] = canonical_lower
    return reverse


def resolve_alias(entity_key: str, skeleton: dict) -> str:
    """entity_key 가 alias 이면 canonical key 로 치환.

    entity_key 포맷: {domain}:{category}:{slug}
    alias 매칭은 slug 부분에 대해 수행. 매칭 실패 시 원본 반환.

    Args:
        entity_key: 정규화된 entity_key (lowercase, hyphen).
        skeleton: domain_skeleton dict.

    Returns:
        canonical entity_key (alias 치환 완료) 또는 원본.
    """
    reverse_map = _build_reverse_alias_map(skeleton)
    if not reverse_map:
        return entity_key

    key_lower = entity_key.strip().lower()

    # 전체 key 매칭 시도
    if key_lower in reverse_map:
        return reverse_map[key_lower]

    # slug 부분만 매칭 시도
    parts = key_lower.split(":")
    if len(parts) >= 3:
        slug = parts[-1]
        if slug in reverse_map:
            canonical_slug = reverse_map[slug]
            # canonical_slug 가 full key 형식이면 그대로, slug 만이면 조립
            if ":" in canonical_slug:
                return canonical_slug
            return ":".join(parts[:-1] + [canonical_slug])

    return entity_key


def resolve_is_a(entity_key: str, skeleton: dict) -> list[str]:
    """entity_key 의 is_a parent chain 반환.

    skeleton["is_a"] 포맷: {child_key: parent_key}
    depth limit 초과 또는 순환 시 중단.

    Args:
        entity_key: 정규화된 entity_key.
        skeleton: domain_skeleton dict.

    Returns:
        parent chain list (가까운 부모부터). 빈 리스트 = is_a 관계 없음.
    """
    is_a_map = skeleton.get("is_a", {})
    if not is_a_map:
        return []

    # lowercase 정규화된 맵 생성
    normalized_map: dict[str, str] = {
        k.strip().lower(): v.strip().lower()
        for k, v in is_a_map.items()
    }

    chain: list[str] = []
    visited: set[str] = set()
    current = entity_key.strip().lower()

    for _ in range(_IS_A_DEPTH_LIMIT):
        parent = normalized_map.get(current)
        if parent is None:
            break
        if parent in visited:
            logger.warning("is_a 순환 감지: %s → %s (chain: %s)", current, parent, chain)
            break
        visited.add(parent)
        chain.append(parent)
        current = parent

    return chain


def canonicalize_entity_key(entity_key: str, skeleton: dict) -> str:
    """entity_key 를 canonical 형태로 정규화.

    1. lowercase + strip
    2. alias 치환
    3. 공백 → 하이픈

    이 함수는 idempotent — 이미 canonical 인 key 에 적용해도 동일 결과.

    Args:
        entity_key: 원본 entity_key.
        skeleton: domain_skeleton dict.

    Returns:
        canonical entity_key.
    """
    normalized = entity_key.strip().lower().replace(" ", "-")
    resolved = resolve_alias(normalized, skeleton)
    return resolved
