"""collect_node — 웹 수집 → Claim + EU 생성.

Collection Plan → WebSearch/WebFetch → LLM 파싱 → Claim 배열.
design-v2 §7 기반.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Any

from src.state import EvolverState

logger = logging.getLogger(__name__)

# high-risk 카테고리
HIGH_RISK_LEVELS = {"safety", "financial", "policy"}


def _compute_search_budget(plan: dict, mode: str) -> int:
    """Cost Guard G2: 검색 호출 예산."""
    n_targets = len(plan.get("target_gaps", []))
    budget = n_targets * 2
    if mode == "jump":
        budget += 4
    return budget


def _parse_claims_deterministic(
    gu: dict,
    search_results: list[dict],
    fetched_content: str,
) -> list[dict]:
    """LLM 없이 결정론적 Claim 생성 (fallback / mock)."""
    target = gu.get("target", {})
    entity_key = target.get("entity_key", "")
    field = target.get("field", "")
    gu_id = gu.get("gu_id", "")

    claims = []
    for i, result in enumerate(search_results[:2]):
        eu_id = f"EU-{gu_id.replace('GU-', '')}-{i + 1:02d}"
        claim = {
            "claim_id": f"CL-{gu_id.replace('GU-', '')}-{i + 1:02d}",
            "entity_key": entity_key,
            "field": field,
            "value": f"Collected info for {field} from {result.get('title', 'source')}",
            "source_gu_id": gu_id,
            "evidence": {
                "eu_id": eu_id,
                "url": result.get("url", ""),
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "observed_at": date.today().isoformat(),
                "credibility": 0.7,
            },
            "risk_flag": gu.get("risk_level", "") in HIGH_RISK_LEVELS,
            "provenance": None,
        }
        claims.append(claim)

    return claims


def _collect_single_gu(
    gu: dict,
    gu_queries: list[str],
    search_tool: Any,
    llm: Any | None,
) -> list[dict]:
    """단일 GU에 대한 수집 + 파싱 (병렬 실행 단위)."""
    all_results: list[dict] = []
    failures: list[str] = []

    for query in gu_queries:
        try:
            results = search_tool.search(query)
            all_results.extend(results)
        except (TimeoutError, ConnectionError, OSError) as exc:
            logger.warning("collect search failed: %r — %s", query, exc)
            failures.append(f"search:{query}")
        except Exception as exc:
            logger.warning("collect search unexpected error: %r — %s", query, exc)
            failures.append(f"search:{query}")

    # URL fetch (상위 2개)
    fetched_content = ""
    for result in all_results[:2]:
        url = result.get("url", "")
        if url:
            try:
                content = search_tool.fetch(url)
                fetched_content += content + "\n"
            except (TimeoutError, ConnectionError, OSError) as exc:
                logger.warning("collect fetch failed: %s — %s", url, exc)
                failures.append(f"fetch:{url}")
            except Exception as exc:
                logger.warning("collect fetch unexpected error: %s — %s", url, exc)
                failures.append(f"fetch:{url}")

    if llm is not None:
        prompt = _build_parse_prompt(gu, all_results, fetched_content)
        try:
            response = llm.invoke(prompt)
            from src.utils.llm_parse import extract_json
            claims = extract_json(response.content)
            if isinstance(claims, dict):
                claims = [claims]
        except (ValueError, AttributeError):
            claims = _parse_claims_deterministic(gu, all_results, fetched_content)
    else:
        claims = _parse_claims_deterministic(gu, all_results, fetched_content)

    return claims


def collect_node(
    state: EvolverState,
    *,
    search_tool: Any | None = None,
    llm: Any | None = None,
    max_workers: int = 5,
) -> dict:
    """Collection Plan → Claim + EU 배열 생성.

    Args:
        search_tool: SearchTool 인터페이스 구현체. None이면 수집 생략.
        llm: LLM 인스턴스. None이면 결정론적 파싱.
        max_workers: 병렬 수집 스레드 수.
    """
    plan = state.get("current_plan", {})
    gap_map = state.get("gap_map", [])
    mode_decision = state.get("current_mode", {})
    mode = mode_decision.get("mode", "normal")

    target_gap_ids = plan.get("target_gaps", [])
    queries = plan.get("queries", {})
    budget = plan.get("budget", _compute_search_budget(plan, mode))

    # GU ID → GU dict 매핑
    gu_by_id = {gu.get("gu_id"): gu for gu in gap_map}

    if search_tool is None:
        return {"current_claims": []}

    # 수집 대상 필터링 (budget 내)
    tasks: list[tuple[dict, list[str]]] = []
    search_calls_used = 0
    for gu_id in target_gap_ids:
        gu = gu_by_id.get(gu_id)
        if gu is None:
            continue

        gu_queries = queries.get(gu_id, [])
        needed = len(gu_queries)

        if search_calls_used + needed > budget:
            if gu.get("expected_utility") in ("low", "medium"):
                continue

        tasks.append((gu, gu_queries))
        search_calls_used += needed

    # 병렬 수집 (search_tool + llm이 있을 때)
    all_claims: list[dict] = []
    total_gu_count = len(tasks)
    failed_gu_count = 0

    if tasks and (llm is not None or search_tool is not None):
        workers = min(max_workers, len(tasks))
        logger.info("collect: %d GU 병렬 수집 (workers=%d)", len(tasks), workers)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_collect_single_gu, gu, gu_queries, search_tool, llm): gu.get("gu_id")
                for gu, gu_queries in tasks
            }
            for future in as_completed(futures, timeout=120):
                gu_id = futures[future]
                try:
                    claims = future.result(timeout=60)
                    all_claims.extend(claims)
                    logger.info("collect: %s → %d claims", gu_id, len(claims))
                except TimeoutError:
                    logger.warning("collect: %s timeout (60s)", gu_id)
                    failed_gu_count += 1
                except Exception as e:
                    logger.warning("collect: %s 실패 — %s", gu_id, e)
                    failed_gu_count += 1
    else:
        # search_tool 없으면 순차 (결정론적 mock)
        for gu, gu_queries in tasks:
            claims = _parse_claims_deterministic(gu, [], "")
            all_claims.extend(claims)

    # collect_failure_rate 계산
    failure_rate = failed_gu_count / total_gu_count if total_gu_count > 0 else 0.0

    return {
        "current_claims": all_claims,
        "collect_failure_rate": round(failure_rate, 3),
    }


def _build_parse_prompt(
    gu: dict,
    search_results: list[dict],
    fetched_content: str,
) -> str:
    """LLM Claim 파싱 프롬프트."""
    target = gu.get("target", {})
    gu_id = gu.get("gu_id", "")
    entity_key = target.get("entity_key", "")
    field = target.get("field", "")

    # 검색 결과를 구조화된 텍스트로 변환
    source_lines = []
    for i, r in enumerate(search_results[:5], 1):
        source_lines.append(
            f"  [{i}] {r.get('title', 'N/A')}\n"
            f"      URL: {r.get('url', '')}\n"
            f"      Snippet: {r.get('snippet', '')}"
        )
    sources_text = "\n".join(source_lines) if source_lines else "  (no results)"

    return f"""You are a knowledge extraction agent. Extract factual claims from web sources.

## Target
- Entity: {entity_key}
- Field: {field}
- Gap ID: {gu_id}
- Gap Type: {gu.get('gap_type', 'unknown')}
- Resolution Criteria: {gu.get('resolution_criteria', 'N/A')}

## Sources
{sources_text}

## Fetched Content (truncated)
{fetched_content[:3000] if fetched_content.strip() else '(no content fetched)'}

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
    "snippet": string (relevant excerpt),
    "observed_at": string (today's date YYYY-MM-DD),
    "credibility": number (0.0-1.0, official=0.9, news=0.7, forum=0.5)
  }}
- "risk_flag": boolean (true if safety/financial/policy related)

## Rules
- Extract ONLY claims supported by the sources above.
- Each claim must cite exactly one source URL.
- If no factual information is found, return an empty array: []
- Return ONLY valid JSON, no markdown fences or explanations."""
