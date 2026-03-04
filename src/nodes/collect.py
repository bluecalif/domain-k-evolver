"""collect_node — 웹 수집 → Claim + EU 생성.

Collection Plan → WebSearch/WebFetch → LLM 파싱 → Claim 배열.
design-v2 §7 기반.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from src.state import EvolverState

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
    """LLM 없이 결정론적 Claim 생성 (fallback / mock).

    실제 파이프라인에서는 LLM이 raw text에서 Claim을 추출.
    """
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
        }
        claims.append(claim)

    return claims


def collect_node(
    state: EvolverState,
    *,
    search_tool: Any | None = None,
    llm: Any | None = None,
) -> dict:
    """Collection Plan → Claim + EU 배열 생성.

    Args:
        search_tool: SearchTool 인터페이스 구현체. None이면 수집 생략.
        llm: LLM 인스턴스. None이면 결정론적 파싱.
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

    all_claims: list[dict] = []
    search_calls_used = 0
    skipped: list[str] = []

    # 우선순위 순서 (plan에서 이미 정렬됨)
    for gu_id in target_gap_ids:
        gu = gu_by_id.get(gu_id)
        if gu is None:
            skipped.append(gu_id)
            continue

        gu_queries = queries.get(gu_id, [])

        # Budget 체크: low utility부터 중단
        if search_calls_used + len(gu_queries) > budget:
            if gu.get("expected_utility") in ("low", "medium"):
                skipped.append(gu_id)
                continue

        if search_tool is not None:
            # 실제 수집
            all_results: list[dict] = []
            fetched_content = ""

            for query in gu_queries:
                if search_calls_used >= budget:
                    break
                try:
                    results = search_tool.search(query)
                    all_results.extend(results)
                    search_calls_used += 1
                except Exception:
                    # 재시도 로직 (최대 3회)
                    for _ in range(2):
                        try:
                            results = search_tool.search(query)
                            all_results.extend(results)
                            search_calls_used += 1
                            break
                        except Exception:
                            continue
                    else:
                        skipped.append(gu_id)
                        continue

            # URL fetch (상위 2개)
            for result in all_results[:2]:
                url = result.get("url", "")
                if url:
                    try:
                        content = search_tool.fetch(url)
                        fetched_content += content + "\n"
                    except Exception:
                        pass

            if llm is not None:
                # LLM 파싱
                prompt = _build_parse_prompt(gu, all_results, fetched_content)
                try:
                    response = llm.invoke(prompt)
                    import json
                    claims = json.loads(response.content)
                except Exception:
                    claims = _parse_claims_deterministic(gu, all_results, fetched_content)
            else:
                claims = _parse_claims_deterministic(gu, all_results, fetched_content)
        else:
            # search_tool 없으면 빈 결과
            claims = []

        all_claims.extend(claims)

    return {"current_claims": all_claims}


def _build_parse_prompt(
    gu: dict,
    search_results: list[dict],
    fetched_content: str,
) -> str:
    """LLM Claim 파싱 프롬프트."""
    target = gu.get("target", {})
    return f"""Extract structured claims from the following content.

Target: {target.get('entity_key')} / {target.get('field')}
Resolution Criteria: {gu.get('resolution_criteria', '')}

Search Results:
{search_results[:5]}

Fetched Content (truncated):
{fetched_content[:3000]}

Return a JSON array of claims with fields:
- claim_id, entity_key, field, value, evidence (eu_id, url, title, observed_at, credibility)
"""
