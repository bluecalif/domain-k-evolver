"""integrate_node — Claims → KU/GU 통합.

Entity Resolution + KB Patch + Conflict Handling + 동적 GU 발견.
design-v2 §6 기반.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from math import ceil
from typing import Any

from src.state import EvolverState
from src.utils.llm_parse import extract_json

logger = logging.getLogger(__name__)

HIGH_RISK_LEVELS = {"safety", "financial", "policy"}


def _normalize_entity_key(raw: str) -> str:
    """entity_key 정규화: 소문자, 공백→하이픈."""
    return raw.strip().lower().replace(" ", "-")


def _find_matching_ku(
    entity_key: str,
    field: str,
    knowledge_units: list[dict],
) -> dict | None:
    """entity_key + field로 기존 KU 검색."""
    for ku in knowledge_units:
        if ku.get("entity_key") == entity_key and ku.get("field") == field:
            return ku
    return None


def _build_conflict_prompt(
    entity_key: str,
    field: str,
    existing_value: str,
    new_value: str,
) -> str:
    """LLM semantic conflict detection 프롬프트 생성."""
    return f"""You are a knowledge integration expert. Determine if two values for the same knowledge slot are semantically conflicting.

Entity: {entity_key}
Field: {field}
Existing value: {existing_value}
New value: {new_value}

Classify as one of:
- "conflict": The values genuinely contradict each other (e.g., different prices, incompatible facts)
- "update": The new value is a more recent or more detailed version of the same information
- "equivalent": The values mean the same thing expressed differently

Respond in JSON: {{"verdict": "conflict"|"update"|"equivalent", "reason": "brief explanation"}}"""


def _detect_conflict(
    existing_ku: dict,
    claim: dict,
    *,
    llm: Any | None = None,
) -> str | None:
    """충돌 감지. 반환: 'hold' | 'condition_split' | None.

    Args:
        llm: LLM 인스턴스. None이면 결정론적 문자열 비교 fallback.
    """
    existing_value = existing_ku.get("value")
    claim_value = claim.get("value")

    if existing_value is None or claim_value is None:
        return None

    # Rule 1: 동일 값 → 충돌 없음
    if str(existing_value) == str(claim_value):
        return None

    # Rule 2: conditions 있으면 condition_split
    if claim.get("conditions") or existing_ku.get("conditions"):
        return "condition_split"

    # Rule 3: LLM semantic 판정
    if llm is not None:
        entity_key = existing_ku.get("entity_key", "")
        field = existing_ku.get("field", "")
        prompt = _build_conflict_prompt(
            entity_key, field, str(existing_value), str(claim_value),
        )
        try:
            response = llm.invoke(prompt)
            text = response.content if hasattr(response, "content") else str(response)
            parsed = extract_json(text)
            verdict = parsed.get("verdict", "conflict")
            logger.info(
                "Conflict check [%s/%s]: '%s' vs '%s' → %s (%s)",
                entity_key, field,
                str(existing_value)[:50], str(claim_value)[:50],
                verdict, parsed.get("reason", ""),
            )
            if verdict in ("update", "equivalent"):
                return None  # 충돌 아님 → 업데이트로 처리
            return "hold"  # 진짜 충돌
        except Exception:
            logger.warning(
                "LLM conflict detection failed for %s/%s, falling back to hold",
                existing_ku.get("entity_key", ""), existing_ku.get("field", ""),
                exc_info=True,
            )
            return "hold"

    # Fallback (no LLM): 결정론적 — 값이 다르면 hold
    return "hold"


def _generate_dynamic_gus(
    claim: dict,
    gap_map: list[dict],
    skeleton: dict,
    mode: str,
    open_count: int,
) -> list[dict]:
    """동적 GU 발견 (Trigger A: 인접 Gap).

    Claim의 entity_key/field가 기존 Gap Map에 없는 슬롯 참조 시 missing GU 생성.
    """
    entity_key = claim.get("entity_key", "")
    field = claim.get("field", "")

    # 기존 GU에 이미 있는 슬롯
    existing_slots = {
        (gu.get("target", {}).get("entity_key"), gu.get("target", {}).get("field"))
        for gu in gap_map
    }

    new_gus: list[dict] = []

    # 같은 entity의 다른 필드 중 Gap Map에 없는 것
    categories = [c["slug"] for c in skeleton.get("categories", [])]
    parts = entity_key.split(":")
    if len(parts) < 3:
        return []

    category = parts[1]
    fields = skeleton.get("fields", [])
    applicable_fields = [
        f["name"] for f in fields
        if "*" in f.get("categories", []) or category in f.get("categories", [])
    ]

    for adj_field in applicable_fields:
        if adj_field == field:
            continue
        slot = (entity_key, adj_field)
        if slot not in existing_slots:
            new_gus.append({
                "gap_type": "missing",
                "target": {"entity_key": entity_key, "field": adj_field},
                "expected_utility": "medium",
                "risk_level": "convenience",
                "resolution_criteria": f"{parts[-1]} {adj_field} 정보 수집",
                "status": "open",
                "trigger": "A:adjacent_gap",
                "trigger_source": claim.get("claim_id", ""),
                "created_at": date.today().isoformat(),
            })

    return new_gus


def _compute_dynamic_gu_cap(mode: str, open_count: int) -> int:
    """동적 GU 상한 계산."""
    if mode == "jump":
        return min(max(10, ceil(open_count * 0.6)), 30)
    return min(max(4, ceil(open_count * 0.2)), 12)


def integrate_node(
    state: EvolverState,
    *,
    llm: Any | None = None,
) -> dict:
    """Claims → KU/GU 통합.

    Args:
        llm: LLM 인스턴스. None이면 결정론적 통합.
    """
    claims = list(state.get("current_claims", []))
    kus = list(state.get("knowledge_units", []))
    gap_map = list(state.get("gap_map", []))
    skeleton = state.get("domain_skeleton", {})
    mode_decision = state.get("current_mode", {})
    mode = mode_decision.get("mode", "normal")

    open_count = sum(1 for gu in gap_map if gu.get("status") == "open")
    dynamic_cap = _compute_dynamic_gu_cap(mode, open_count)

    # KU ID 카운터
    max_ku_id = 0
    for ku in kus:
        ku_id = ku.get("ku_id", "")
        if ku_id.startswith("KU-"):
            try:
                num = int(ku_id.replace("KU-", ""))
                max_ku_id = max(max_ku_id, num)
            except ValueError:
                pass

    # GU ID 카운터
    max_gu_id = 0
    for gu in gap_map:
        gu_id = gu.get("gu_id", "")
        if gu_id.startswith("GU-"):
            try:
                num = int(gu_id.replace("GU-", ""))
                max_gu_id = max(max_gu_id, num)
            except ValueError:
                pass

    # 통합 처리
    adds: list[dict] = []
    updates: list[dict] = []
    rejected: list[dict] = []
    new_dynamic_gus: list[dict] = []

    for claim in claims:
        entity_key = _normalize_entity_key(claim.get("entity_key", ""))
        field = claim.get("field", "")
        value = claim.get("value", "")
        evidence = claim.get("evidence", {})
        source_gu_id = claim.get("source_gu_id", "")

        # Entity Resolution
        existing_ku = _find_matching_ku(entity_key, field, kus)

        if existing_ku is not None:
            # 충돌 감지 (LLM semantic 비교)
            conflict = _detect_conflict(existing_ku, claim, llm=llm)

            if conflict == "hold":
                # disputed 처리
                if existing_ku.get("status") != "disputed":
                    existing_ku["status"] = "disputed"
                    if "disputes" not in existing_ku:
                        existing_ku["disputes"] = []
                    existing_ku["disputes"].append({
                        "conflicting_claim": claim.get("claim_id", ""),
                        "nature": f"Conflicting value for {field}",
                        "resolution": "hold",
                    })

                # EU 추가
                eu_id = evidence.get("eu_id", "")
                if eu_id and eu_id not in existing_ku.get("evidence_links", []):
                    existing_ku.setdefault("evidence_links", []).append(eu_id)

                updates.append(existing_ku)
                claim["integration_result"] = "conflict_hold"

            elif conflict == "condition_split":
                # 조건 분리: 새 KU 생성
                max_ku_id += 1
                new_ku = {
                    "ku_id": f"KU-{max_ku_id:04d}",
                    "entity_key": entity_key,
                    "field": field,
                    "value": value,
                    "conditions": claim.get("conditions", {}),
                    "observed_at": evidence.get("observed_at", date.today().isoformat()),
                    "validity": {"ttl_days": 180},
                    "evidence_links": [evidence.get("eu_id", "")] if evidence.get("eu_id") else [],
                    "confidence": evidence.get("credibility", 0.7),
                    "status": "active",
                }
                kus.append(new_ku)
                adds.append(new_ku)
                claim["integration_result"] = "condition_split"

            else:
                # 충돌 없음: 기존 KU 업데이트 (EU 추가, confidence 갱신)
                eu_id = evidence.get("eu_id", "")
                if eu_id and eu_id not in existing_ku.get("evidence_links", []):
                    existing_ku.setdefault("evidence_links", []).append(eu_id)

                # confidence 갱신 (새 값과 평균)
                new_conf = evidence.get("credibility", 0.7)
                old_conf = existing_ku.get("confidence", 0.7)
                existing_ku["confidence"] = round((old_conf + new_conf) / 2, 3)

                updates.append(existing_ku)
                claim["integration_result"] = "updated"

        else:
            # 신규 KU 생성
            max_ku_id += 1
            new_ku = {
                "ku_id": f"KU-{max_ku_id:04d}",
                "entity_key": entity_key,
                "field": field,
                "value": value,
                "observed_at": evidence.get("observed_at", date.today().isoformat()),
                "validity": {"ttl_days": 180},
                "evidence_links": [evidence.get("eu_id", "")] if evidence.get("eu_id") else [],
                "confidence": evidence.get("credibility", 0.7),
                "status": "active",
            }
            kus.append(new_ku)
            adds.append(new_ku)
            claim["integration_result"] = "added"

        # GU 상태 업데이트 (resolved)
        if source_gu_id and claim.get("integration_result") in ("added", "updated", "condition_split"):
            for gu in gap_map:
                if gu.get("gu_id") == source_gu_id and gu.get("status") == "open":
                    gu["status"] = "resolved"
                    gu["resolved_by"] = claim.get("claim_id", "")
                    break

        # 동적 GU 발견 (Trigger A)
        if len(new_dynamic_gus) < dynamic_cap:
            discovered = _generate_dynamic_gus(claim, gap_map + new_dynamic_gus, skeleton, mode, open_count)
            remaining = dynamic_cap - len(new_dynamic_gus)
            for dgu in discovered[:remaining]:
                max_gu_id += 1
                dgu["gu_id"] = f"GU-{max_gu_id:04d}"
                if mode == "jump":
                    dgu["expansion_mode"] = "jump"
                new_dynamic_gus.append(dgu)

    # 동적 GU를 gap_map에 추가
    gap_map.extend(new_dynamic_gus)

    # 불변원칙 검증
    # Claim→KU 착지성
    processed = len(adds) + len(updates) + len(rejected)
    # (claim 수 == adds + updates + rejected는 이상적, 여기서는 soft check)

    # Evidence-first: 새 active KU는 EU >= 1
    for ku in adds:
        if ku.get("status") == "active":
            assert len(ku.get("evidence_links", [])) >= 1, (
                f"Evidence-first 위반: {ku.get('ku_id')} has no evidence"
            )

    # Conflict-preserving: disputed KU 삭제 금지 (이 노드에서는 삭제 자체를 하지 않음)

    return {
        "knowledge_units": kus,
        "gap_map": gap_map,
        "current_claims": claims,
    }
