"""collect_node — Tavily snippet 기반 2단계 파이프라인 (SEARCH → PARSE).

SI-P3R (D-121): Provider/Fetch/Parse 3단계 폐기 → snippet-first 2단계로 복원.
외부 인터페이스 보존: return {"current_claims": [...], "collect_failure_rate": float}.
"""

from __future__ import annotations

import logging
import math
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from typing import Any
from urllib.parse import urlparse

from src.state import EvolverState

logger = logging.getLogger(__name__)

HIGH_RISK_LEVELS = {"safety", "financial", "policy"}


def _compute_search_budget(plan: dict, mode: str) -> int:
    n_targets = len(plan.get("target_gaps", []))
    budget = n_targets * 2
    if mode == "jump":
        budget += 4
    return budget


# ============================================================
# SEARCH
# ============================================================

def _search_phase(
    gu_queries: list[str],
    search_tool: Any,
) -> list[dict]:
    """Tavily search_tool.search → [{url, title, snippet}] 리스트."""
    if search_tool is None:
        return []

    results: list[dict] = []
    for query in gu_queries:
        try:
            raw = search_tool.search(query)
        except Exception as exc:
            logger.warning("search failed: %r — %s", query, exc)
            continue
        for item in raw:
            results.append({
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "snippet": item.get("snippet", "") or item.get("content", ""),
            })
    return results


# ============================================================
# PARSE
# ============================================================

def _build_provenance(source_url: str) -> dict:
    """축소 provenance (4필드): provider/domain/retrieved_at/trust_tier."""
    domain = urlparse(source_url).netloc if source_url else ""
    return {
        "provider": "tavily",
        "domain": domain,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "trust_tier": "primary",
    }


def _parse_claims_deterministic(
    gu: dict,
    search_results: list[dict],
) -> list[dict]:
    """LLM 없이 결정론적 Claim 생성 (fallback / mock)."""
    target = gu.get("target", {})
    entity_key = target.get("entity_key", "")
    field = target.get("field", "")
    gu_id = gu.get("gu_id", "")

    claims = []
    for i, sr in enumerate(search_results[:2]):
        eu_id = f"EU-{gu_id.replace('GU-', '')}-{i + 1:02d}"
        url = sr.get("url", "")
        claims.append({
            "claim_id": f"CL-{gu_id.replace('GU-', '')}-{i + 1:02d}",
            "entity_key": entity_key,
            "field": field,
            "value": f"Collected info for {field} from {sr.get('title') or 'source'}",
            "source_gu_id": gu_id,
            "evidence": {
                "eu_id": eu_id,
                "url": url,
                "title": sr.get("title", ""),
                "snippet": sr.get("snippet", ""),
                "observed_at": date.today().isoformat(),
                "credibility": 0.7,
            },
            "risk_flag": gu.get("risk_level", "") in HIGH_RISK_LEVELS,
            "provenance": _build_provenance(url),
        })
    return claims


def _parse_claims_llm(
    gu: dict,
    search_results: list[dict],
    llm: Any,
) -> list[dict]:
    """LLM snippet-only Claim 파싱 (단발 invoke — fallback 경로 전용)."""
    gu_id = gu.get("gu_id", "?")
    snippet_count = sum(1 for sr in search_results if sr.get("snippet"))

    if not any(sr.get("snippet") for sr in search_results):
        logger.info("parse[%s]: no snippets — skip LLM", gu_id)
        logger.info("parse_yield: gu=%s snippets=%d claims=0 path=no_snippets",
                    gu_id, snippet_count)
        return []

    logger.info("parse[%s]: LLM 단발 invoke — snippets=%d/%d", gu_id, snippet_count, len(search_results))

    prompt = _build_parse_prompt(gu, search_results)
    try:
        response = llm.invoke(prompt)
        return _parse_llm_response(gu, response.content, search_results)
    except (ValueError, AttributeError) as exc:
        logger.info("parse[%s]: invoke 실패 (%s) → deterministic fallback", gu_id, exc)
        fb_claims = _parse_claims_deterministic(gu, search_results)
        logger.info("parse_yield: gu=%s snippets=%d claims=%d path=fallback",
                    gu_id, snippet_count, len(fb_claims))
        return fb_claims


def _parse_llm_response(
    gu: dict,
    resp_text: str,
    search_results: list[dict],
) -> list[dict]:
    """LLM 응답 텍스트 → claims 파싱 (batch path 공유)."""
    from src.utils.llm_parse import extract_json

    gu_id = gu.get("gu_id", "?")
    snippet_count = sum(1 for sr in search_results if sr.get("snippet"))
    try:
        claims = extract_json(resp_text)
        if isinstance(claims, dict):
            claims = [claims]
        logger.info("parse[%s]: claims=%d (resp_len=%d)", gu_id, len(claims), len(resp_text))
    except (ValueError, AttributeError) as exc:
        logger.info("parse[%s]: JSON extract failed (%s) → deterministic fallback", gu_id, exc)
        fb_claims = _parse_claims_deterministic(gu, search_results)
        logger.info("parse_yield: gu=%s snippets=%d claims=%d path=fallback",
                    gu_id, snippet_count, len(fb_claims))
        return fb_claims

    for claim in claims:
        source_url = ""
        ev = claim.get("evidence", {})
        if isinstance(ev, dict):
            source_url = ev.get("url", "")
        claim["provenance"] = _build_provenance(source_url)

    logger.info("parse_yield: gu=%s snippets=%d claims=%d path=llm",
                gu_id, snippet_count, len(claims))
    return claims


# ============================================================
# Collect 메인
# ============================================================

def _calc_execution_queue(
    target_gap_ids: list[str],
    gu_by_id: dict[str, dict],
    queries: dict[str, list[str]],
    budget: int,
) -> tuple[list[tuple[dict, list[str]]], list[dict]]:
    """budget 범위 내 실행 queue 와 초과분 deferred 반환.

    utility 필터 없음 — 초과 GU 는 drop 대신 deferred 에 적재 (S1-T4).
    """
    tasks: list[tuple[dict, list[str]]] = []
    deferred: list[dict] = []
    search_calls_used = 0

    for gu_id in target_gap_ids:
        gu = gu_by_id.get(gu_id)
        if gu is None:
            continue
        gu_queries = queries.get(gu_id, [])
        needed = len(gu_queries)
        if search_calls_used + needed > budget:
            deferred.append(gu)
            continue
        tasks.append((gu, gu_queries))
        search_calls_used += needed

    return tasks, deferred


def _search_for_gu(
    gu: dict,
    gu_queries: list[str],
    search_tool: Any,
) -> tuple[dict, list[dict], int]:
    """Search 전담 — PARSE 없음. (gu, search_results, search_count) 반환."""
    gu_id = gu.get("gu_id", "?")
    search_results = _search_phase(gu_queries, search_tool)
    if not search_results:
        logger.debug("collect[%s]: SEARCH=0 results (queries=%d)", gu_id, len(gu_queries))
    return gu, search_results, len(search_results)


def collect_node(
    state: EvolverState,
    *,
    search_tool: Any | None = None,
    llm: Any | None = None,
    max_workers: int = 5,
    search_config: Any | None = None,
) -> dict:
    """Collection Plan → Claim + EU 배열 (2단계: SEARCH→PARSE).

    외부 인터페이스 보존: return {"current_claims": [...], "collect_failure_rate": float}
    """
    plan = state.get("current_plan", {})
    gap_map = state.get("gap_map", [])
    mode_decision = state.get("current_mode", {})
    mode = mode_decision.get("mode", "normal")

    target_gap_ids = plan.get("target_gaps", [])
    queries = plan.get("queries", {})
    budget = plan.get("budget", _compute_search_budget(plan, mode))

    gu_by_id = {gu.get("gu_id"): gu for gu in gap_map}

    if search_tool is None:
        return {"current_claims": []}

    tasks, deferred_gus = _calc_execution_queue(target_gap_ids, gu_by_id, queries, budget)
    if deferred_gus:
        logger.info("collect: %d GU deferred (budget=%d 초과)", len(deferred_gus), budget)

    all_claims: list[dict] = []
    total_gu_count = len(tasks)
    failed_gu_count = 0
    per_gu_claims: list[int] = []
    diag_search_by_gu: dict[str, int] = {}

    # Phase 1: Search (ThreadPool 병렬 — I/O bound)
    search_data: list[tuple[dict, list[dict]]] = []  # (gu, search_results)

    if tasks:
        workers = min(max_workers, len(tasks))
        logger.info("collect: %d GU search 병렬 (workers=%d)", len(tasks), workers)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_search_for_gu, gu, gu_queries, search_tool): gu.get("gu_id")
                for gu, gu_queries in tasks
            }
            try:
                for future in as_completed(futures, timeout=300):
                    gu_id = futures[future]
                    try:
                        gu, search_results, search_count = future.result(timeout=120)
                        diag_search_by_gu[gu_id] = search_count
                        search_data.append((gu, search_results))
                    except TimeoutError:
                        logger.warning("collect: %s search timeout (120s)", gu_id)
                        failed_gu_count += 1
                    except Exception as e:
                        logger.warning("collect: %s search 실패 — %s", gu_id, e)
                        failed_gu_count += 1
            except TimeoutError:
                unfinished = sum(1 for f in futures if not f.done())
                logger.warning(
                    "collect: as_completed 300s 초과 — %d/%d GU 미완료로 skip",
                    unfinished, len(futures),
                )
                failed_gu_count += unfinished
                for f in futures:
                    if not f.done():
                        f.cancel()

    # Phase 2: LLM Batch Parse (1회 호출)
    if search_data:
        if llm is not None:
            has_snippet = [(gu, sr) for gu, sr in search_data if any(r.get("snippet") for r in sr)]
            no_snippet = [(gu, sr) for gu, sr in search_data if not any(r.get("snippet") for r in sr)]

            for gu, _ in no_snippet:
                gu_id = gu.get("gu_id", "?")
                logger.info("parse[%s]: no snippets — skip LLM", gu_id)
                logger.info("parse_yield: gu=%s snippets=0 claims=0 path=no_snippets", gu_id)
                per_gu_claims.append(0)

            if has_snippet:
                prompts = [_build_parse_prompt(gu, sr) for gu, sr in has_snippet]
                logger.info("collect: batch LLM %d prompts (1회 호출)", len(prompts))
                try:
                    responses = llm.batch(prompts)
                except Exception as exc:
                    logger.warning("collect: batch API 실패 (%s) → 단발 invoke fallback", exc)
                    responses = None

                if responses is not None:
                    for (gu, sr), response in zip(has_snippet, responses):
                        gu_id = gu.get("gu_id", "?")
                        try:
                            resp_text = response.content
                        except AttributeError:
                            resp_text = ""
                        claims = _parse_llm_response(gu, resp_text, sr)
                        if not claims and sr:
                            logger.info("collect[%s]: 0 claims despite SEARCH=%d", gu_id, len(sr))
                        all_claims.extend(claims)
                        per_gu_claims.append(len(claims))
                        logger.info("collect: %s → %d claims", gu_id, len(claims))
                else:
                    for gu, sr in has_snippet:
                        gu_id = gu.get("gu_id", "?")
                        claims = _parse_claims_llm(gu, sr, llm)
                        if not claims and sr:
                            logger.info("collect[%s]: 0 claims despite SEARCH=%d", gu_id, len(sr))
                        all_claims.extend(claims)
                        per_gu_claims.append(len(claims))
                        logger.info("collect: %s → %d claims", gu_id, len(claims))
        else:
            for gu, sr in search_data:
                claims = _parse_claims_deterministic(gu, sr)
                all_claims.extend(claims)
                per_gu_claims.append(len(claims))

    failure_rate = failed_gu_count / total_gu_count if total_gu_count > 0 else 0.0

    if per_gu_claims:
        zero_count = sum(1 for c in per_gu_claims if c == 0)
        zero_ratio = zero_count / len(per_gu_claims)
        avg_claims = sum(per_gu_claims) / len(per_gu_claims)
        logger.info(
            "parse_yield_summary: targets=%d completed=%d avg_claims=%.2f "
            "zero_claims=%d zero_ratio=%.3f total_claims=%d",
            total_gu_count, len(per_gu_claims), avg_claims,
            zero_count, zero_ratio, sum(per_gu_claims),
        )

    domain_ent = _domain_entropy(all_claims)

    if domain_ent > 0:
        logger.info("collect diversity: domain_entropy=%.3f", domain_ent)

    return {
        "current_claims": all_claims,
        "collect_failure_rate": round(failure_rate, 3),
        "_diag_search_by_gu": diag_search_by_gu,
        "deferred_targets": deferred_gus,
    }


# ============================================================
# Diversity
# ============================================================

def _shannon_entropy(counts: dict[str, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    ent = 0.0
    for c in counts.values():
        if c > 0:
            p = c / total
            ent -= p * math.log2(p)
    return round(ent, 4)


def _domain_entropy(claims: list[dict]) -> float:
    domains: Counter[str] = Counter()
    for claim in claims:
        prov = claim.get("provenance")
        if prov and isinstance(prov, dict):
            d = prov.get("domain", "")
            if d:
                domains[d] += 1
    return _shannon_entropy(dict(domains))


# ============================================================
# Prompt
# ============================================================

def _build_parse_prompt(gu: dict, search_results: list[dict]) -> str:
    """LLM Claim 파싱 프롬프트 (snippet 전용)."""
    target = gu.get("target", {})
    gu_id = gu.get("gu_id", "")
    entity_key = target.get("entity_key", "")
    field = target.get("field", "")

    sorted_results = sorted(
        search_results,
        key=lambda r: len(r.get("snippet", "")),
        reverse=True,
    )

    source_lines = []
    for i, r in enumerate(sorted_results[:5], 1):
        source_lines.append(
            f"  [{i}] {r.get('title', 'N/A')}\n"
            f"      URL: {r.get('url', '')}\n"
            f"      Snippet: {r.get('snippet', '')}"
        )
    sources_text = "\n".join(source_lines) if source_lines else "  (no results)"

    return f"""You are a knowledge extraction agent. Extract factual claims from web search snippets.

## Target
- Entity: {entity_key}
- Field: {field}
- Gap ID: {gu_id}
- Gap Type: {gu.get('gap_type', 'unknown')}
- Resolution Criteria: {gu.get('resolution_criteria', 'N/A')}

## Sources (search snippets)
{sources_text}

## Output Format
Return a JSON array. Each element MUST have these fields:
- "claim_id": string (format: "CL-XXXX-NN")
- "entity_key": "{entity_key}"
- "field": "{field}"
- "value": string (the factual claim — be specific with numbers, dates, names)
- "source_gu_id": "{gu_id}"
- "evidence": {{
    "eu_id": string (format: "EU-XXXX-NN"),
    "url": string,
    "title": string,
    "snippet": string (relevant excerpt from the source),
    "observed_at": string (today's date YYYY-MM-DD),
    "credibility": number (0.0-1.0, official=0.9, news=0.7, forum=0.5)
  }}
- "risk_flag": boolean (true if safety/financial/policy related)

## Rules
- Extract ONLY claims supported by the snippets above.
- Each claim must cite exactly one source URL.
- If no factual information is found, return an empty array: []
- Return ONLY valid JSON, no markdown fences or explanations."""
