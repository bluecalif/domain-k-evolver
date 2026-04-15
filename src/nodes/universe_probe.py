"""universe_probe — Skeleton 외부 카테고리 발굴 (SI-P4 Stage E, L4b).

LLM survey 로 skeleton 에 없는 MAJOR category/axis 후보를 3-5개 제안.
반응형 category_addition (L4a) 과 달리 선제적 — 기수집 데이터 없이도 작동.

본 모듈은 **proposal 생성까지만** 책임. 실제 skeleton 승격은
validator (E2-4) + HITL-R 경로를 거쳐야 함 (D-139).

Pipeline (전체):
    survey (this module)  →  broad Tavily probe (E2-3)
                          →  evidence validator (E2-4)
                          →  candidate_categories 등록 (HITL-R 대기)
                          →  promote_candidate (HITL-R 승인 시)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from src.utils.llm_parse import extract_json
from src.utils.skeleton_tiers import (
    add_candidate_category,
    get_active_category_slugs,
    get_candidate_category_slugs,
)

if TYPE_CHECKING:
    from src.config import EvolverConfig
    from src.tools.search import SearchTool
    from src.utils.cost_guard import CostGuard

logger = logging.getLogger(__name__)

VALID_PROPOSAL_TYPES = {"NEW_CATEGORY", "NEW_AXIS"}


UNIVERSE_PROBE_PROMPT = """SYSTEM:
You are a domain-knowledge auditor. Your job is to find GAPS in a knowledge
skeleton — categories or axes that exist in the real world but are missing
from the current skeleton.

USER:
Domain: {domain}
Current skeleton categories (slug: ku_count):
{skeleton_categories_with_ku_counts}

Current skeleton fields:
{skeleton_fields}

Top retrieved entities:
{top_entities}

Task:
Propose 3-5 MAJOR categories or axes that are plausibly important for this
domain but absent from the skeleton. For each:
1. slug (lowercase, hyphen-separated)
2. name (human-readable)
3. rationale (1-2 sentences, why it matters)
4. expected_source (where in the world this knowledge lives)
5. type: NEW_CATEGORY (sibling of existing) or NEW_AXIS (cross-cutting)

Rules:
- DO NOT propose refinements of existing categories (that's gap_rule's job).
- DO propose categories that would appear in a comprehensive guide but are
  missing here.
- Prioritize categories that affect non-majority user segments (accessibility,
  budget extremes, long-stay, professional travel, etc.) as these are typically
  underserved.

Return JSON only:
{{"proposals": [{{"slug": "...", "name": "...", "rationale": "...",
                 "expected_source": "...", "type": "NEW_CATEGORY"}}]}}
"""


def _ku_count_by_category(knowledge_units: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ku in knowledge_units:
        entity_key = ku.get("entity_key", "")
        parts = entity_key.split(":")
        if len(parts) >= 2:
            cat = parts[1]
            counts[cat] = counts.get(cat, 0) + 1
    return counts


def _top_entities(knowledge_units: list[dict], limit: int = 10) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for ku in knowledge_units:
        ek = ku.get("entity_key", "")
        if ek and ek not in seen:
            seen.add(ek)
            result.append(ek)
            if len(result) >= limit:
                break
    return result


def _build_prompt(skeleton: dict, knowledge_units: list[dict]) -> str:
    domain = skeleton.get("domain", "unknown")
    ku_counts = _ku_count_by_category(knowledge_units)
    active_slugs = get_active_category_slugs(skeleton)
    cat_lines = "\n".join(f"- {s}: {ku_counts.get(s, 0)}" for s in active_slugs) or "- (none)"
    field_lines = "\n".join(f"- {f.get('name')}" for f in skeleton.get("fields", [])) or "- (none)"
    entity_lines = "\n".join(f"- {e}" for e in _top_entities(knowledge_units)) or "- (none)"
    return UNIVERSE_PROBE_PROMPT.format(
        domain=domain,
        skeleton_categories_with_ku_counts=cat_lines,
        skeleton_fields=field_lines,
        top_entities=entity_lines,
    )


def gather_evidence(
    proposals: list[dict],
    search_client: "SearchTool",
    cost_guard: "CostGuard",
    domain: str,
) -> tuple[list[dict], list[dict]]:
    """각 proposal 에 대해 Tavily 검색으로 evidence snippets 수집.

    cost_guard 예산 내에서만 호출. 예산 초과 시 해당 proposal 은 skip.

    Returns:
        (evidenced, skipped) — evidenced 는 evidence.snippets 주입된 proposals,
        skipped 는 budget 부족으로 skip 된 proposals.
    """
    evidenced: list[dict] = []
    skipped: list[dict] = []

    for p in proposals:
        if not cost_guard.allow("universe_probe_evidence", tavily=1):
            p["evidence"] = {"skipped": True, "reason": "budget_exceeded"}
            skipped.append(p)
            continue

        slug = p.get("slug", "unknown")
        name = p.get("name", slug)
        query = f"{name} {domain}"

        try:
            results = search_client.search(query)
            cost_guard.record("universe_probe_evidence", tavily=1)
        except Exception as exc:
            logger.warning(
                "[gather_evidence] Tavily call failed for %s: %s", slug, exc,
            )
            cost_guard.record("universe_probe_evidence", tavily=1)
            p["evidence"] = {"snippets": [], "error": str(exc)}
            evidenced.append(p)
            continue

        snippets = [
            {"url": r.get("url", ""), "title": r.get("title", ""), "snippet": r.get("snippet", "")}
            for r in results
        ]
        p["evidence"] = {"snippets": snippets}
        evidenced.append(p)
        logger.info(
            "[gather_evidence] %s: %d snippets collected", slug, len(snippets),
        )

    return evidenced, skipped


EVIDENCE_VALIDATOR_PROMPT = """SYSTEM:
You validate whether a proposed new category has real-world evidence.

USER:
Proposed category: {slug} — {name}
Rationale: {rationale}

Tavily search results (5 snippets):
{snippets}

Questions:
1. Do these snippets confirm the category exists as a distinct knowledge area?
2. Confidence (0-1)?
3. Are there 2+ independent sources, or is it a single echo?

Return JSON: {{"exists": true/false, "confidence": 0.0-1.0, "source_diversity": int,
              "sample_entity_names": ["..."]}}
"""


def _build_validator_prompt(proposal: dict) -> str:
    snippets = proposal.get("evidence", {}).get("snippets", [])
    snippet_lines = "\n".join(
        f"{i+1}. [{s.get('title', '')}] {s.get('snippet', '')}"
        for i, s in enumerate(snippets)
    ) or "(no snippets)"
    return EVIDENCE_VALIDATOR_PROMPT.format(
        slug=proposal.get("slug", ""),
        name=proposal.get("name", ""),
        rationale=proposal.get("rationale", ""),
        snippets=snippet_lines,
    )


def validate_proposals(
    proposals: list[dict],
    llm: Any,
    cost_guard: "CostGuard",
    min_confidence: float = 0.6,
) -> tuple[list[dict], list[dict]]:
    """LLM 으로 evidence snippets 기반 proposal 검증 (Prompt 3).

    Returns:
        (validated, failed) — validated 는 exists=True + confidence >= threshold,
        failed 는 exists=False / low confidence / budget skip / error.
    """
    validated: list[dict] = []
    failed: list[dict] = []

    for p in proposals:
        evidence = p.get("evidence", {})
        # snippets 없는 proposal (skipped/error) 은 검증 불가
        if evidence.get("skipped") or evidence.get("error") or not evidence.get("snippets"):
            p["validation"] = {"status": "skipped", "reason": "no_evidence"}
            failed.append(p)
            continue

        if not cost_guard.allow("universe_probe_validator", llm=1):
            p["validation"] = {"status": "skipped", "reason": "budget_exceeded"}
            failed.append(p)
            continue

        prompt = _build_validator_prompt(p)
        try:
            response = llm.invoke(prompt)
            text = response.content if hasattr(response, "content") else str(response)
            parsed = extract_json(text)
        except Exception as exc:
            logger.warning("[validate_proposals] LLM call failed for %s: %s", p.get("slug"), exc)
            cost_guard.record("universe_probe_validator", llm=1)
            p["validation"] = {"status": "error", "reason": str(exc)}
            failed.append(p)
            continue

        cost_guard.record("universe_probe_validator", llm=1)

        exists = parsed.get("exists", False) if isinstance(parsed, dict) else False
        confidence = float(parsed.get("confidence", 0.0)) if isinstance(parsed, dict) else 0.0
        source_diversity = int(parsed.get("source_diversity", 0)) if isinstance(parsed, dict) else 0
        sample_entities = parsed.get("sample_entity_names", []) if isinstance(parsed, dict) else []

        p["validation"] = {
            "exists": exists,
            "confidence": confidence,
            "source_diversity": source_diversity,
            "sample_entity_names": sample_entities,
        }

        if exists and confidence >= min_confidence:
            p["status"] = "validated"
            p["validation"]["status"] = "passed"
            validated.append(p)
        else:
            reason = "not_exists" if not exists else f"low_confidence:{confidence}"
            p["validation"]["status"] = "failed"
            p["validation"]["reason"] = reason
            failed.append(p)

    logger.info(
        "[validate_proposals] validated=%d failed=%d", len(validated), len(failed),
    )
    return validated, failed


def register_validated(
    proposals: list[dict],
    skeleton: dict,
) -> tuple[list[dict], list[dict]]:
    """검증 통과 proposals 를 skeleton candidate_categories 에 등록 (HITL-R 대기).

    Returns:
        (registered, errors) — errors 는 slug collision 등으로 등록 실패한 entries.
    """
    registered: list[dict] = []
    errors: list[dict] = []

    for p in proposals:
        try:
            add_candidate_category(skeleton, p)
            registered.append(p)
        except ValueError as exc:
            logger.warning("[register_validated] skip %s: %s", p.get("slug"), exc)
            p["_register_error"] = str(exc)
            errors.append(p)

    logger.info(
        "[register_validated] registered=%d errors=%d", len(registered), len(errors),
    )
    return registered, errors


def _validate_and_filter_proposals(
    proposals: list[dict],
    skeleton: dict,
) -> tuple[list[dict], list[dict]]:
    """반환: (accepted, rejected). reject reason 은 rejected[i]['_reject_reason']."""
    accepted: list[dict] = []
    rejected: list[dict] = []

    active = set(get_active_category_slugs(skeleton))
    candidates = set(get_candidate_category_slugs(skeleton))
    seen_in_batch: set[str] = set()

    for p in proposals:
        if not isinstance(p, dict):
            rejected.append({"_raw": p, "_reject_reason": "not_a_dict"})
            continue
        slug = p.get("slug", "").strip().lower()
        if not slug:
            rejected.append({**p, "_reject_reason": "missing_slug"})
            continue
        ptype = p.get("type")
        if ptype not in VALID_PROPOSAL_TYPES:
            rejected.append({**p, "_reject_reason": f"invalid_type:{ptype}"})
            continue
        if slug in active:
            rejected.append({**p, "_reject_reason": "collision_active"})
            continue
        if slug in candidates:
            rejected.append({**p, "_reject_reason": "collision_candidate"})
            continue
        if slug in seen_in_batch:
            rejected.append({**p, "_reject_reason": "duplicate_in_batch"})
            continue
        seen_in_batch.add(slug)
        p["slug"] = slug
        accepted.append(p)

    return accepted, rejected


EXTERNAL_NOVELTY_STAGNATION_THRESHOLD = 0.15
EXTERNAL_NOVELTY_STAGNATION_WINDOW = 3


def should_run_universe_probe(
    state: dict,
    config: "EvolverConfig",
) -> tuple[bool, str]:
    """universe_probe 실행 여부 판정.

    조건 (OR):
    1. cycle % probe_interval_cycles == 0 (주기 도달)
    2. external_novelty < 0.15 이 연속 3 cycle (정체 감지)

    Returns:
        (should_run, reason)
    """
    ea = config.external_anchor
    if not ea.enabled:
        return False, "external_anchor_disabled"

    cycle = state.get("current_cycle", state.get("cycle", 0))

    # 조건 1: 주기
    if cycle > 0 and cycle % ea.probe_interval_cycles == 0:
        return True, f"periodic(cycle={cycle}%{ea.probe_interval_cycles}==0)"

    # 조건 2: external_novelty 정체
    ext_history = state.get("external_novelty_history") or []
    w = EXTERNAL_NOVELTY_STAGNATION_WINDOW
    if len(ext_history) >= w:
        recent = ext_history[-w:]
        if all(v < EXTERNAL_NOVELTY_STAGNATION_THRESHOLD for v in recent):
            return True, f"novelty_stagnation(last_{w}<{EXTERNAL_NOVELTY_STAGNATION_THRESHOLD})"

    return False, "no_trigger"


def run_universe_probe(
    state: dict,
    llm: Any,
    config: "EvolverConfig",
    cost_guard: "CostGuard",
    cycle: Optional[int] = None,
) -> dict:
    """LLM survey 로 skeleton 외부 category 후보 proposals 생성.

    Returns:
        {
            "status": "ok" | "skipped" | "error",
            "reason": str,
            "proposals": [{slug, name, rationale, expected_source, type,
                           proposed_at_cycle}],
            "rejected": [...],
            "cycle": int,
        }
    """
    cycle = cycle if cycle is not None else state.get("cycle", 0)
    ea = config.external_anchor

    if not ea.enabled:
        return {"status": "skipped", "reason": "external_anchor_disabled",
                "proposals": [], "rejected": [], "cycle": cycle}

    if not cost_guard.allow("universe_probe", llm=1):
        return {"status": "skipped", "reason": "budget_exceeded",
                "proposals": [], "rejected": [], "cycle": cycle}

    skeleton = state.get("domain_skeleton", {})
    knowledge_units = state.get("knowledge_units", [])
    prompt = _build_prompt(skeleton, knowledge_units)

    try:
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        parsed = extract_json(text)
    except Exception as exc:
        logger.warning("[universe_probe] LLM call failed: %s", exc)
        cost_guard.record("universe_probe", llm=1)
        return {"status": "error", "reason": f"llm_or_parse_error:{exc}",
                "proposals": [], "rejected": [], "cycle": cycle}

    cost_guard.record("universe_probe", llm=1)

    raw = parsed.get("proposals", []) if isinstance(parsed, dict) else []
    if not isinstance(raw, list):
        return {"status": "error", "reason": "proposals_not_list",
                "proposals": [], "rejected": [], "cycle": cycle}

    accepted, rejected = _validate_and_filter_proposals(raw, skeleton)

    for p in accepted:
        p["proposed_at_cycle"] = cycle
        p["status"] = "pending_validation"
        p.setdefault("evidence", None)

    logger.info(
        "[universe_probe] cycle=%d accepted=%d rejected=%d",
        cycle, len(accepted), len(rejected),
    )
    return {
        "status": "ok",
        "reason": "",
        "proposals": accepted,
        "rejected": rejected,
        "cycle": cycle,
    }
