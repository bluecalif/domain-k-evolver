"""audit_node -- Executive Audit (Phase 4 Task 4.1).

N-cycle 주기로 trajectory를 분석하여 AuditReport를 생성한다.

분석 항목:
1. 다축 교차 커버리지 진단 (blind spot 식별)
2. KU yield/cost 효율 분석 (category별 수확 체감 감지)
3. 품질 추세 분석 (metrics 건강도 변화)
4. Policy 수정 제안 (findings 기반)
"""

from __future__ import annotations

import logging
import math
from typing import Any

from src.utils.policy_manager import compute_credibility_stats, learn_credibility

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Coverage Analysis (Task 4.2 연계)
# ---------------------------------------------------------------------------

def _analyze_cross_axis_coverage(
    knowledge_units: list[dict],
    gap_map: list[dict],
    skeleton: dict,
) -> list[dict]:
    """다축 교차 커버리지 진단 -> findings."""
    findings: list[dict] = []

    categories = [c["slug"] for c in skeleton.get("categories", [])]
    axes = skeleton.get("axes", [])

    # category별 KU 수
    cat_ku_counts: dict[str, int] = {c: 0 for c in categories}
    for ku in knowledge_units:
        if ku.get("status") != "active":
            continue
        entity_key = ku.get("entity_key", "")
        parts = entity_key.split(":")
        cat = parts[1] if len(parts) >= 3 else ""
        if cat in cat_ku_counts:
            cat_ku_counts[cat] += 1

    # Shannon entropy로 카테고리 균등도 측정
    total_ku = sum(cat_ku_counts.values())
    if total_ku > 0 and len(categories) > 1:
        h_max = math.log2(len(categories))
        entropy = 0.0
        for count in cat_ku_counts.values():
            if count > 0:
                p = count / total_ku
                entropy -= p * math.log2(p)
        uniformity = entropy / h_max if h_max > 0 else 0.0

        if uniformity < 0.75:
            findings.append({
                "finding_id": "F-COV-01",
                "category": "axis_imbalance",
                "severity": "warning",
                "description": (
                    f"카테고리 균등도 부족: H={entropy:.3f}, "
                    f"H_max={h_max:.3f}, uniformity={uniformity:.3f} (< 0.75)"
                ),
                "evidence": {
                    "entropy": round(entropy, 4),
                    "h_max": round(h_max, 4),
                    "uniformity": round(uniformity, 4),
                    "distribution": cat_ku_counts,
                },
            })

    # 최소 KU 카테고리 진단
    for cat, count in cat_ku_counts.items():
        if count < 3:
            findings.append({
                "finding_id": f"F-COV-{cat[:4].upper()}",
                "category": "coverage_gap",
                "severity": "critical" if count == 0 else "warning",
                "description": f"카테고리 '{cat}' KU 부족: {count}개",
                "evidence": {"category": cat, "ku_count": count},
            })

    # category × geography 교차 blind spot
    geo_axis = next((a for a in axes if a.get("name") == "geography"), None)
    if geo_axis:
        geo_anchors = geo_axis.get("anchors", [])
        # KU별 geography tag 추출 (axis_tags 또는 entity_key 기반)
        cat_geo_matrix: dict[str, dict[str, int]] = {
            c: {g: 0 for g in geo_anchors} for c in categories
        }

        for gu in gap_map:
            if gu.get("status") != "resolved":
                continue
            target = gu.get("target", {})
            entity_key = target.get("entity_key", "")
            parts = entity_key.split(":")
            cat = parts[1] if len(parts) >= 3 else ""
            geo = gu.get("axis_tags", {}).get("geography", "")
            if cat in cat_geo_matrix and geo in cat_geo_matrix.get(cat, {}):
                cat_geo_matrix[cat][geo] += 1

        total_cells = len(categories) * len(geo_anchors) if geo_anchors else 1
        blind_cells = sum(
            1
            for cat_data in cat_geo_matrix.values()
            for count in cat_data.values()
            if count == 0
        )
        blind_ratio = blind_cells / total_cells if total_cells > 0 else 0.0

        if blind_ratio > 0.40:
            findings.append({
                "finding_id": "F-COV-GEO",
                "category": "coverage_gap",
                "severity": "warning",
                "description": (
                    f"category x geography 교차 blind spot: "
                    f"{blind_cells}/{total_cells} ({blind_ratio:.1%})"
                ),
                "evidence": {
                    "blind_cells": blind_cells,
                    "total_cells": total_cells,
                    "blind_ratio": round(blind_ratio, 4),
                },
            })

    return findings


# ---------------------------------------------------------------------------
# Yield/Cost Analysis (Task 4.3 연계)
# ---------------------------------------------------------------------------

def _analyze_yield_cost(
    trajectory: list[dict],
) -> list[dict]:
    """KU yield/cost 효율 분석 -> findings."""
    findings: list[dict] = []

    if len(trajectory) < 3:
        return findings

    # cycle별 yield 계산
    yields: list[float] = []
    for i, entry in enumerate(trajectory):
        llm_calls = entry.get("llm_calls", 0)
        if i == 0:
            ku_growth = entry.get("ku_active", 0)
        else:
            ku_growth = entry.get("ku_active", 0) - trajectory[i - 1].get("ku_active", 0)
        yield_val = ku_growth / max(llm_calls, 1)
        yields.append(yield_val)

    # 후반부 yield 체감 감지
    mid = len(yields) // 2
    if mid > 0:
        first_half_avg = sum(yields[:mid]) / mid
        second_half_avg = sum(yields[mid:]) / len(yields[mid:])

        if first_half_avg > 0 and second_half_avg < first_half_avg * 0.3:
            findings.append({
                "finding_id": "F-YIELD-01",
                "category": "yield_decline",
                "severity": "warning",
                "description": (
                    f"KU yield 체감: 전반 {first_half_avg:.3f} → "
                    f"후반 {second_half_avg:.3f} ({second_half_avg/first_half_avg:.0%})"
                ),
                "evidence": {
                    "first_half_avg": round(first_half_avg, 4),
                    "second_half_avg": round(second_half_avg, 4),
                    "yields": [round(y, 4) for y in yields],
                },
            })

    return findings


# ---------------------------------------------------------------------------
# Quality Trend Analysis
# ---------------------------------------------------------------------------

def _analyze_quality_trends(
    trajectory: list[dict],
) -> list[dict]:
    """품질 지표 추세 분석 -> findings."""
    findings: list[dict] = []

    if len(trajectory) < 3:
        return findings

    # avg_confidence 하락 추세
    last_3_conf = [e.get("avg_confidence", 0) for e in trajectory[-3:]]
    if all(last_3_conf[i] > last_3_conf[i + 1] for i in range(len(last_3_conf) - 1)):
        findings.append({
            "finding_id": "F-QUAL-01",
            "category": "quality_issue",
            "severity": "warning",
            "description": (
                f"avg_confidence 3연속 하락: "
                f"{' -> '.join(f'{c:.3f}' for c in last_3_conf)}"
            ),
            "evidence": {"trend": last_3_conf},
        })

    # multi_evidence_rate 정체
    last_3_multi = [e.get("multi_evidence_rate", 0) for e in trajectory[-3:]]
    if all(m < 0.50 for m in last_3_multi):
        findings.append({
            "finding_id": "F-QUAL-02",
            "category": "quality_issue",
            "severity": "info",
            "description": (
                f"multi_evidence_rate 3연속 caution 미만: "
                f"{' -> '.join(f'{m:.3f}' for m in last_3_multi)}"
            ),
            "evidence": {"trend": last_3_multi},
        })

    return findings


# ---------------------------------------------------------------------------
# Policy Patch Generation
# ---------------------------------------------------------------------------

def _generate_policy_patches(
    findings: list[dict],
    policies: dict,
) -> list[PolicyPatchDict]:
    """Findings 기반 policy 수정 제안 생성.

    Safety: 한 Audit당 최대 3개 patch.
    """
    patches: list[PolicyPatchDict] = []
    patch_counter = 1

    for finding in findings:
        if len(patches) >= 3:
            break

        fid = finding.get("finding_id", "")
        cat = finding.get("category", "")

        # multi_evidence_rate 부족 → cross_validation min_sources 증가
        if fid == "F-QUAL-02" and cat == "quality_issue":
            cv = policies.get("cross_validation", {})
            for risk_key, rule in cv.items():
                if isinstance(rule, dict) and rule.get("min_sources", 0) < 3:
                    patches.append({
                        "patch_id": f"PP-{patch_counter:03d}",
                        "target_field": f"cross_validation.{risk_key}.min_sources",
                        "current_value": rule.get("min_sources", 1),
                        "proposed_value": min(rule.get("min_sources", 1) + 1, 3),
                        "reason": f"multi_evidence_rate 부족 ({fid})",
                    })
                    patch_counter += 1
                    break

        # yield 체감 → TTL 연장 검토 (수집 범위 확장 유도)
        if fid == "F-YIELD-01" and cat == "yield_decline":
            ttl = policies.get("ttl_defaults", {})
            # 가장 짧은 TTL 항목 연장
            if ttl:
                shortest_key = min(ttl, key=lambda k: ttl[k])
                current_val = ttl[shortest_key]
                patches.append({
                    "patch_id": f"PP-{patch_counter:03d}",
                    "target_field": f"ttl_defaults.{shortest_key}",
                    "current_value": current_val,
                    "proposed_value": int(current_val * 1.5),
                    "reason": f"KU yield 체감 → TTL 연장으로 탐색 범위 확대 ({fid})",
                })
                patch_counter += 1

    return patches


# Type alias (avoiding import cycle with state.py)
PolicyPatchDict = dict


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def _generate_recommendations(findings: list[dict]) -> list[str]:
    """Findings 기반 텍스트 권고 생성."""
    recs: list[str] = []

    severity_counts = {"critical": 0, "warning": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    if severity_counts["critical"] > 0:
        recs.append(
            f"Critical finding {severity_counts['critical']}건 — "
            "해당 카테고리/축에 대한 집중 탐색 권장"
        )

    coverage_gaps = [f for f in findings if f["category"] == "coverage_gap"]
    if coverage_gaps:
        recs.append(
            f"커버리지 갭 {len(coverage_gaps)}건 발견 — "
            "explore 비율 상향 또는 해당 축 GU 우선 생성 권장"
        )

    yield_issues = [f for f in findings if f["category"] == "yield_decline"]
    if yield_issues:
        recs.append(
            "KU yield 체감 감지 — 탐색 방향 전환 또는 exploit 비율 증가 권장"
        )

    if not findings:
        recs.append("시스템 건강 양호 — 현재 전략 유지")

    return recs


# ---------------------------------------------------------------------------
# Main Audit Function
# ---------------------------------------------------------------------------

def run_audit(
    state: dict,
    trajectory: list[dict],
    *,
    audit_cycle: int | None = None,
    window_start: int | None = None,
) -> dict:
    """Executive Audit 실행.

    Args:
        state: 현재 EvolverState.
        trajectory: MetricsLogger entries (cycle별 기록).
        audit_cycle: 현재 cycle 번호.
        window_start: 분석 시작 cycle (None이면 전체).

    Returns:
        AuditReport dict.
    """
    kus = state.get("knowledge_units", [])
    gap_map = state.get("gap_map", [])
    skeleton = state.get("domain_skeleton", {})
    policies = state.get("policies", {})
    cycle = audit_cycle or state.get("current_cycle", 0)

    # 분석 대상 trajectory 필터링
    if window_start is not None:
        window_trajectory = [
            e for e in trajectory if e.get("cycle", 0) >= window_start
        ]
    else:
        window_trajectory = list(trajectory)

    window = [
        window_trajectory[0]["cycle"] if window_trajectory else 1,
        window_trajectory[-1]["cycle"] if window_trajectory else cycle,
    ]

    # 진단 수행
    findings: list[dict] = []
    findings.extend(_analyze_cross_axis_coverage(kus, gap_map, skeleton))
    findings.extend(_analyze_yield_cost(window_trajectory))
    findings.extend(_analyze_quality_trends(window_trajectory))

    # 권고 생성
    recommendations = _generate_recommendations(findings)

    # Policy patch 생성
    policy_patches = _generate_policy_patches(findings, policies)

    # Credibility 학습 (Task 4.6)
    cred_stats = compute_credibility_stats(kus)
    cred_patches = learn_credibility(
        cred_stats, policies.get("credibility_priors", {}),
    )
    # 3개 한도 내에서 credibility patch 추가
    remaining_slots = 3 - len(policy_patches)
    if remaining_slots > 0 and cred_patches:
        policy_patches.extend(cred_patches[:remaining_slots])

    report = {
        "audit_cycle": cycle,
        "window": window,
        "findings": findings,
        "recommendations": recommendations,
        "policy_patches": policy_patches,
    }

    logger.info(
        "Audit 완료: cycle=%d, findings=%d, patches=%d",
        cycle,
        len(findings),
        len(policy_patches),
    )

    return report
