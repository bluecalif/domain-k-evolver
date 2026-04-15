"""Reach Diversity Ledger — 출처 다양성 추적 (SI-P4 Stage E, E3).

KU provenance 에서 publisher_domain / tld 축을 추출하여 누적 추적.
VP4 지표 `distinct_domains_per_100ku` 계산 + `is_reach_degraded()` 판정.

확정 축 (E0-2 reach-axes-survey):
  - publisher_domain (primary): urlparse(url).netloc → provenance.domain
  - tld (secondary): domain rsplit('.', 1)[-1] — region/language proxy
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# is_reach_degraded 임계치
DOMAINS_PER_100KU_FLOOR = 15  # VP4 기준
DEGRADATION_WINDOW = 3  # 최근 N cycle 연속 floor 미달 시 degraded


def extract_domains(knowledge_units: list[dict]) -> set[str]:
    """KU 목록에서 publisher_domain set 추출."""
    domains: set[str] = set()
    for ku in knowledge_units:
        prov = ku.get("provenance") or {}
        domain = prov.get("domain", "")
        if domain:
            domains.add(domain)
    return domains


def extract_tlds(domains: set[str]) -> set[str]:
    """domain set → tld set (secondary axis)."""
    tlds: set[str] = set()
    for d in domains:
        parts = d.rsplit(".", 1)
        if len(parts) == 2:
            tlds.add(parts[1])
        elif parts:
            tlds.add(parts[0])
    return tlds


def distinct_domains_per_100ku(
    knowledge_units: list[dict],
) -> float:
    """distinct publisher_domain / 100 KU (VP4 핵심 지표)."""
    active_kus = [ku for ku in knowledge_units if ku.get("status") == "active"]
    n = len(active_kus)
    if n == 0:
        return 0.0
    domains = extract_domains(active_kus)
    return len(domains) / n * 100


def build_ledger_snapshot(
    knowledge_units: list[dict],
    cycle: int,
) -> dict:
    """단일 cycle 의 reach diversity snapshot.

    Returns:
        {
            "cycle": int,
            "distinct_domains": int,
            "distinct_tlds": int,
            "domains_per_100ku": float,
            "active_ku_count": int,
            "domains": [sorted list],
            "tlds": [sorted list],
        }
    """
    active_kus = [ku for ku in knowledge_units if ku.get("status") == "active"]
    domains = extract_domains(active_kus)
    tlds = extract_tlds(domains)
    n = len(active_kus)
    per_100 = len(domains) / n * 100 if n > 0 else 0.0

    return {
        "cycle": cycle,
        "distinct_domains": len(domains),
        "distinct_tlds": len(tlds),
        "domains_per_100ku": round(per_100, 2),
        "active_ku_count": n,
        "domains": sorted(domains),
        "tlds": sorted(tlds),
    }


def is_reach_degraded(
    reach_history: list[dict],
    floor: float = DOMAINS_PER_100KU_FLOOR,
    window: int = DEGRADATION_WINDOW,
) -> tuple[bool, str]:
    """reach diversity 저하 판정.

    최근 `window` cycle 연속으로 `domains_per_100ku < floor` 이면 degraded.

    Returns:
        (is_degraded, reason)
    """
    if len(reach_history) < window:
        return False, f"insufficient_history({len(reach_history)}<{window})"

    recent = reach_history[-window:]
    values = [s.get("domains_per_100ku", 0.0) for s in recent]

    if all(v < floor for v in values):
        avg = sum(values) / len(values)
        return True, f"degraded(last_{window}_avg={avg:.1f}<{floor})"

    return False, "ok"
