"""Novelty 계산 — cycle-to-cycle 신규성 측정.

P4-A1: Jaccard, token, entity overlap 기반 novelty score.
novelty = 1 - overlap (0 = 완전 중복, 1 = 완전 새로).
"""

from __future__ import annotations


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Jaccard similarity: |A ∩ B| / |A ∪ B|."""
    if not set_a and not set_b:
        return 1.0  # 둘 다 비면 완전 중복 취급
    union = set_a | set_b
    if not union:
        return 1.0
    return len(set_a & set_b) / len(union)


def _extract_claim_keys(kus: list[dict]) -> set[str]:
    """KU 목록에서 claim 식별자 set 추출.

    claim_key = entity_key + ":" + field (KU 단위 고유 식별).
    """
    keys: set[str] = set()
    for ku in kus:
        if ku.get("status") not in ("active", "disputed"):
            continue
        ek = ku.get("entity_key", "")
        field = ku.get("field", "")
        keys.add(f"{ek}:{field}")
    return keys


def _extract_entity_keys(kus: list[dict]) -> set[str]:
    """KU 목록에서 entity_key set 추출."""
    return {
        ku.get("entity_key", "")
        for ku in kus
        if ku.get("status") in ("active", "disputed")
    }


def _extract_tokens(kus: list[dict]) -> set[str]:
    """KU 목록에서 claim text 토큰 set 추출 (간이 토큰화)."""
    tokens: set[str] = set()
    for ku in kus:
        if ku.get("status") not in ("active", "disputed"):
            continue
        claim = ku.get("claim", "")
        if isinstance(claim, str):
            tokens.update(claim.lower().split())
    return tokens


def compute_novelty(
    prev_kus: list[dict],
    curr_kus: list[dict],
    *,
    weights: tuple[float, float, float] = (0.5, 0.3, 0.2),
) -> float:
    """두 cycle 간 novelty score 계산.

    Args:
        prev_kus: 이전 cycle KU 목록.
        curr_kus: 현재 cycle KU 목록.
        weights: (claim, entity, token) 가중치. 합 = 1.0.

    Returns:
        float (0~1). 0 = 완전 중복, 1 = 완전 새로.
    """
    if not prev_kus and not curr_kus:
        return 0.0
    if not prev_kus:
        return 1.0

    w_claim, w_entity, w_token = weights

    # Claim-level Jaccard
    prev_claims = _extract_claim_keys(prev_kus)
    curr_claims = _extract_claim_keys(curr_kus)
    claim_sim = _jaccard_similarity(prev_claims, curr_claims)

    # Entity-level Jaccard
    prev_entities = _extract_entity_keys(prev_kus)
    curr_entities = _extract_entity_keys(curr_kus)
    entity_sim = _jaccard_similarity(prev_entities, curr_entities)

    # Token-level Jaccard
    prev_tokens = _extract_tokens(prev_kus)
    curr_tokens = _extract_tokens(curr_kus)
    token_sim = _jaccard_similarity(prev_tokens, curr_tokens)

    # Weighted novelty = 1 - weighted_similarity
    weighted_sim = w_claim * claim_sim + w_entity * entity_sim + w_token * token_sim
    return round(1.0 - weighted_sim, 4)
