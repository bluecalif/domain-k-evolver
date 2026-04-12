"""collect_node — 웹 수집 → Claim + EU 생성.

P3-C1: SEARCH → FETCH → PARSE 3단계 파이프라인.
P3-C2: search_tool.fetch 직접호출 삭제 → FetchPipeline 이관.
P3-C3: Provenance 7필드 채움.
외부 인터페이스 (current_claims, collect_failure_rate) 보존 — P0-X2 동결.
"""

from __future__ import annotations

import logging
import math
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Any
from urllib.parse import urlparse

from src.adapters.fetch_pipeline import FetchPipeline, FetchResult
from src.adapters.providers.base import SearchResult
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


# ============================================================
# Phase 1: SEARCH
# ============================================================

def _search_phase(
    gu: dict,
    gu_queries: list[str],
    search_tool: Any | None = None,
    providers: list | None = None,
    k_per_provider: int = 5,
) -> list[SearchResult]:
    """SEARCH 단계: query → SearchResult 리스트.

    providers 가 있으면 P3 provider 사용, 없으면 레거시 search_tool 사용.
    """
    all_results: list[SearchResult] = []

    for query in gu_queries:
        if providers:
            for provider in providers:
                try:
                    results = provider.search(query, max_results=k_per_provider)
                    all_results.extend(results)
                except Exception as exc:
                    logger.warning(
                        "search failed [%s]: %r — %s",
                        getattr(provider, "provider_id", "?"), query, exc,
                    )
        elif search_tool is not None:
            try:
                raw = search_tool.search(query)
                for item in raw:
                    all_results.append(SearchResult(
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        snippet=item.get("snippet", ""),
                        provider_id="legacy",
                        trust_tier="secondary",
                    ))
            except Exception as exc:
                logger.warning("collect search failed: %r — %s", query, exc)

    return all_results


# ============================================================
# Phase 2: FETCH
# ============================================================

def _fetch_phase(
    search_results: list[SearchResult],
    fetch_pipeline: FetchPipeline | None,
    fetch_top_n: int = 3,
) -> list[FetchResult]:
    """FETCH 단계: SearchResult URL → FetchResult 리스트.

    fetch_pipeline 이 None 이면 빈 리스트 반환 (테스트 모드).
    """
    if fetch_pipeline is None:
        return []

    urls = []
    seen: set[str] = set()
    for sr in search_results:
        if sr.url and sr.url not in seen:
            seen.add(sr.url)
            urls.append(sr.url)
        if len(urls) >= fetch_top_n:
            break

    if not urls:
        return []

    return fetch_pipeline.fetch_many(urls)


# ============================================================
# Phase 3: PARSE
# ============================================================

def _build_provenance(
    search_results: list[SearchResult],
    fetch_results: list[FetchResult],
    source_url: str,
) -> dict:
    """P3-C3: provenance 7필드 생성."""
    providers_used = list({sr.provider_id for sr in search_results if sr.provider_id})
    domain = urlparse(source_url).netloc if source_url else ""

    # FetchResult 에서 매칭
    fr_match = next((fr for fr in fetch_results if fr.url == source_url), None)

    return {
        "providers_used": providers_used,
        "domain": domain,
        "fetch_ok": fr_match.fetch_ok if fr_match else False,
        "fetch_depth": len(fetch_results),
        "content_type": fr_match.content_type if fr_match else "",
        "retrieved_at": fr_match.retrieved_at if fr_match else "",
        "trust_tier": fr_match.trust_tier if fr_match else "secondary",
    }


def _parse_claims_deterministic(
    gu: dict,
    search_results: list[SearchResult],
    fetch_results: list[FetchResult],
) -> list[dict]:
    """LLM 없이 결정론적 Claim 생성 (fallback / mock)."""
    target = gu.get("target", {})
    entity_key = target.get("entity_key", "")
    field = target.get("field", "")
    gu_id = gu.get("gu_id", "")

    claims = []
    for i, sr in enumerate(search_results[:2]):
        eu_id = f"EU-{gu_id.replace('GU-', '')}-{i + 1:02d}"
        provenance = _build_provenance(search_results, fetch_results, sr.url)
        claim = {
            "claim_id": f"CL-{gu_id.replace('GU-', '')}-{i + 1:02d}",
            "entity_key": entity_key,
            "field": field,
            "value": f"Collected info for {field} from {sr.title or 'source'}",
            "source_gu_id": gu_id,
            "evidence": {
                "eu_id": eu_id,
                "url": sr.url,
                "title": sr.title,
                "snippet": sr.snippet,
                "observed_at": date.today().isoformat(),
                "credibility": 0.7,
            },
            "risk_flag": gu.get("risk_level", "") in HIGH_RISK_LEVELS,
            "provenance": provenance,
        }
        claims.append(claim)

    return claims


def _parse_claims_llm(
    gu: dict,
    search_results: list[SearchResult],
    fetch_results: list[FetchResult],
    llm: Any,
) -> list[dict]:
    """LLM 기반 Claim 파싱 + provenance 주입."""
    # fetched content 결합
    fetched_content = "\n".join(
        fr.body for fr in fetch_results if fr.fetch_ok and fr.body
    )

    # 레거시 형식으로 변환 (프롬프트 호환)
    raw_results = [
        {"url": sr.url, "title": sr.title, "snippet": sr.snippet}
        for sr in search_results
    ]

    prompt = _build_parse_prompt(gu, raw_results, fetched_content)
    try:
        response = llm.invoke(prompt)
        from src.utils.llm_parse import extract_json
        claims = extract_json(response.content)
        if isinstance(claims, dict):
            claims = [claims]
    except (ValueError, AttributeError):
        claims = _parse_claims_deterministic(gu, search_results, fetch_results)
        return claims

    # provenance 주입
    for claim in claims:
        source_url = ""
        ev = claim.get("evidence", {})
        if isinstance(ev, dict):
            source_url = ev.get("url", "")
        claim["provenance"] = _build_provenance(search_results, fetch_results, source_url)

    return claims


# ============================================================
# Collect 메인 (3단계 통합)
# ============================================================

def _collect_single_gu(
    gu: dict,
    gu_queries: list[str],
    search_tool: Any,
    llm: Any | None,
    *,
    providers: list | None = None,
    fetch_pipeline: FetchPipeline | None = None,
    k_per_provider: int = 5,
    fetch_top_n: int = 3,
) -> list[dict]:
    """단일 GU에 대한 3단계 수집 (병렬 실행 단위)."""
    # Phase 1: SEARCH
    search_results = _search_phase(
        gu, gu_queries, search_tool=search_tool,
        providers=providers, k_per_provider=k_per_provider,
    )

    # Phase 2: FETCH
    fetch_results = _fetch_phase(search_results, fetch_pipeline, fetch_top_n=fetch_top_n)

    # Phase 3: PARSE
    if llm is not None:
        claims = _parse_claims_llm(gu, search_results, fetch_results, llm)
    else:
        claims = _parse_claims_deterministic(gu, search_results, fetch_results)

    return claims


def collect_node(
    state: EvolverState,
    *,
    search_tool: Any | None = None,
    llm: Any | None = None,
    max_workers: int = 5,
    providers: list | None = None,
    fetch_pipeline: FetchPipeline | None = None,
    search_config: Any | None = None,
) -> dict:
    """Collection Plan → Claim + EU 배열 생성.

    P3-C1: 3단계 파이프라인 (SEARCH→FETCH→PARSE).
    외부 인터페이스 보존: return {"current_claims": [...], "collect_failure_rate": float}

    Args:
        search_tool: 레거시 SearchTool. providers 가 있으면 무시.
        llm: LLM 인스턴스. None이면 결정론적 파싱.
        max_workers: 병렬 수집 스레드 수.
        providers: P3 SearchProvider 리스트.
        fetch_pipeline: P3 FetchPipeline. None이면 fetch 생략.
        search_config: SearchConfig (비용 가드/설정용).
    """
    plan = state.get("current_plan", {})
    gap_map = state.get("gap_map", [])
    mode_decision = state.get("current_mode", {})
    mode = mode_decision.get("mode", "normal")

    target_gap_ids = plan.get("target_gaps", [])
    queries = plan.get("queries", {})
    budget = plan.get("budget", _compute_search_budget(plan, mode))

    # config 기본값
    k_per_provider = 5
    fetch_top_n = 3
    if search_config is not None:
        k_per_provider = getattr(search_config, "k_per_provider", 5)
        fetch_top_n = getattr(search_config, "fetch_top_n", 3)

    # GU ID → GU dict 매핑
    gu_by_id = {gu.get("gu_id"): gu for gu in gap_map}

    if search_tool is None and not providers:
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

    # 병렬 수집
    all_claims: list[dict] = []
    total_gu_count = len(tasks)
    failed_gu_count = 0

    if tasks and (llm is not None or search_tool is not None or providers):
        workers = min(max_workers, len(tasks))
        logger.info("collect: %d GU 병렬 수집 (workers=%d)", len(tasks), workers)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    _collect_single_gu, gu, gu_queries, search_tool, llm,
                    providers=providers, fetch_pipeline=fetch_pipeline,
                    k_per_provider=k_per_provider, fetch_top_n=fetch_top_n,
                ): gu.get("gu_id")
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
        for gu, gu_queries in tasks:
            claims = _parse_claims_deterministic(gu, [], [])
            all_claims.extend(claims)

    # collect_failure_rate 계산
    failure_rate = failed_gu_count / total_gu_count if total_gu_count > 0 else 0.0

    # P3-C5: diversity metrics
    domain_ent = _domain_entropy(all_claims)
    provider_ent = _provider_entropy(all_claims)

    result = {
        "current_claims": all_claims,
        "collect_failure_rate": round(failure_rate, 3),
    }

    # metrics 는 state 에 직접 넣지 않고 로그로 emit (metrics_logger 연동은 후속)
    if domain_ent > 0 or provider_ent > 0:
        logger.info(
            "collect diversity: domain_entropy=%.3f provider_entropy=%.3f",
            domain_ent, provider_ent,
        )

    return result


# ============================================================
# P3-C5: Diversity Metrics
# ============================================================

def _shannon_entropy(counts: dict[str, int]) -> float:
    """Shannon entropy (log2, bits)."""
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
    """claim provenance 의 domain 분포 Shannon entropy."""
    domains: Counter[str] = Counter()
    for claim in claims:
        prov = claim.get("provenance")
        if prov and isinstance(prov, dict):
            d = prov.get("domain", "")
            if d:
                domains[d] += 1
    return _shannon_entropy(dict(domains))


def _provider_entropy(claims: list[dict]) -> float:
    """claim provenance 의 provider 분포 Shannon entropy."""
    providers: Counter[str] = Counter()
    for claim in claims:
        prov = claim.get("provenance")
        if prov and isinstance(prov, dict):
            for pid in prov.get("providers_used", []):
                providers[pid] += 1
    return _shannon_entropy(dict(providers))


# ============================================================
# LLM Parse Prompt (기존 유지)
# ============================================================

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
