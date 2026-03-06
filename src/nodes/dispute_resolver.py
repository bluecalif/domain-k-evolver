"""dispute_resolver — Disputed KU 해소 모듈.

Phase 3 Stage B: disputed→active 전환 경로.
D-42: Evidence-weighted resolution 전략.
"""

from __future__ import annotations

import logging
from typing import Any

from src.utils.llm_parse import extract_json

logger = logging.getLogger(__name__)

# 자동 해소 임계치: evidence_links >= EVIDENCE_RATIO * disputes 이면 자동 해소
EVIDENCE_RATIO = 2


def _build_adjudication_prompt(ku: dict) -> str:
    """LLM dispute adjudication 프롬프트 생성."""
    disputes_desc = "; ".join(
        d.get("nature", "unknown") for d in ku.get("disputes", [])
    )
    return f"""You are a knowledge adjudicator. A knowledge unit is in "disputed" status due to conflicting claims.
Evaluate whether the dispute can be resolved.

Entity: {ku.get("entity_key", "")}
Field: {ku.get("field", "")}
Current value: {str(ku.get("value", ""))[:500]}
Evidence count: {len(ku.get("evidence_links", []))}
Dispute count: {len(ku.get("disputes", []))}
Dispute details: {disputes_desc}

Consider:
1. If the evidence strongly outweighs the disputes, the current value should be kept (resolve).
2. If the dispute nature suggests a minor update rather than a true contradiction, resolve.
3. If the dispute is genuinely unresolvable with current evidence, keep disputed.

Respond in JSON: {{"verdict": "resolve"|"keep_disputed", "reason": "brief explanation"}}"""


def evaluate_disputed_ku(
    ku: dict,
    *,
    llm: Any | None = None,
) -> dict:
    """Disputed KU를 평가하여 해소 여부 결정.

    Returns:
        {"action": "resolve"|"keep_disputed", "reason": str}
    """
    evidence_count = len(ku.get("evidence_links", []))
    dispute_count = len(ku.get("disputes", []))

    if dispute_count == 0:
        return {"action": "resolve", "reason": "no disputes remaining"}

    # 전략 1: Evidence 다수결 — evidence가 dispute의 EVIDENCE_RATIO배 이상
    if evidence_count >= EVIDENCE_RATIO * dispute_count:
        return {
            "action": "resolve",
            "reason": f"evidence majority ({evidence_count} evidence vs {dispute_count} disputes)",
        }

    # 전략 2: LLM 중재
    if llm is not None:
        prompt = _build_adjudication_prompt(ku)
        try:
            response = llm.invoke(prompt)
            text = response.content if hasattr(response, "content") else str(response)
            parsed = extract_json(text)
            verdict = parsed.get("verdict", "keep_disputed")
            reason = parsed.get("reason", "")
            logger.info(
                "Dispute adjudication [%s/%s]: %s (%s)",
                ku.get("entity_key", ""), ku.get("field", ""),
                verdict, reason,
            )
            return {"action": verdict, "reason": reason}
        except Exception:
            logger.warning(
                "LLM dispute adjudication failed for %s/%s",
                ku.get("entity_key", ""), ku.get("field", ""),
                exc_info=True,
            )

    # 전략 3: 해소 불가
    return {
        "action": "keep_disputed",
        "reason": f"insufficient evidence ({evidence_count} vs {dispute_count} disputes)",
    }


def resolve_dispute(ku: dict, decision: dict) -> bool:
    """Disputed KU를 active로 전환.

    Args:
        ku: 원본 KU dict (in-place 수정)
        decision: evaluate_disputed_ku() 반환값

    Returns:
        True if resolved, False if kept disputed.
    """
    if decision.get("action") != "resolve":
        return False

    ku["status"] = "active"
    # disputes를 resolved로 마킹 (Conflict-preserving: 삭제하지 않고 보존)
    for dispute in ku.get("disputes", []):
        dispute["resolution"] = "resolved"
        dispute["resolution_reason"] = decision.get("reason", "")

    return True


def resolve_disputes(
    kus: list[dict],
    *,
    llm: Any | None = None,
) -> list[dict]:
    """전체 KU 목록에서 disputed KU를 평가하고 해소.

    Returns:
        해소된 KU ID 목록 (resolution log).
    """
    resolved_log: list[dict] = []

    for ku in kus:
        if ku.get("status") != "disputed":
            continue

        decision = evaluate_disputed_ku(ku, llm=llm)

        if resolve_dispute(ku, decision):
            resolved_log.append({
                "ku_id": ku.get("ku_id", ""),
                "entity_key": ku.get("entity_key", ""),
                "field": ku.get("field", ""),
                "reason": decision.get("reason", ""),
            })
            logger.info(
                "Dispute resolved: %s (%s/%s) — %s",
                ku.get("ku_id", ""),
                ku.get("entity_key", ""),
                ku.get("field", ""),
                decision.get("reason", ""),
            )

    return resolved_log
