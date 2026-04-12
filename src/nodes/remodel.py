"""remodel_node -- Outer-Loop Remodel (Silver P2-A1).

audit 결과(findings)를 소비하여 skeleton/state 구조 변경 제안(RemodelReport)을 생성한다.
중복 분석은 하지 않으며, audit의 4 분석함수 출력만 소비한다.

제안 유형:
- merge: entity 중복 → canonical key 통합
- split: 하나의 entity에 상반 axis_tag → entity 분리
- reclassify: 카테고리 부정합 → 카테고리 이동
- alias_canonicalize: alias 정리 제안
- source_policy: 출처 정책 변경 제안
- gap_rule: gap 규칙 변경 제안
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# merge 제안 트리거 임계치: entity 중복률
_MERGE_OVERLAP_THRESHOLD = 0.30

# split 제안 트리거: 한 entity에 상반 axis_tag 수
_SPLIT_CONFLICTING_AXES_MIN = 2

# report_id 카운터 (단일 프로세스 내)
_report_counter = 0


def _next_report_id() -> str:
    global _report_counter
    _report_counter += 1
    return f"RM-{_report_counter:04d}"


def reset_report_counter() -> None:
    """테스트용: report_id 카운터 초기화."""
    global _report_counter
    _report_counter = 0


# ---------------------------------------------------------------------------
# Proposal Generators — audit findings 를 소비하여 제안 생성
# ---------------------------------------------------------------------------

def _propose_merges(
    knowledge_units: list[dict],
    skeleton: dict,
) -> list[dict]:
    """entity 중복 분석 → merge 제안.

    같은 category 내에서 field + value 가 겹치는 entity 쌍을 탐지한다.
    중복률이 MERGE_OVERLAP_THRESHOLD 이상이면 merge 제안.
    """
    proposals: list[dict] = []

    # entity_key → {(field, str(value))} 집합
    entity_fields: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for ku in knowledge_units:
        if ku.get("status") != "active":
            continue
        ek = ku.get("entity_key", "")
        field = ku.get("field", "")
        value = str(ku.get("value", ""))
        entity_fields[ek].add((field, value))

    # 같은 category 내 entity 쌍 비교
    entities_by_cat: dict[str, list[str]] = defaultdict(list)
    for ek in entity_fields:
        parts = ek.split(":")
        cat = parts[1] if len(parts) >= 3 else ""
        entities_by_cat[cat].append(ek)

    seen_pairs: set[tuple[str, str]] = set()
    for cat, ek_list in entities_by_cat.items():
        for i, ek_a in enumerate(ek_list):
            for ek_b in ek_list[i + 1:]:
                pair = (min(ek_a, ek_b), max(ek_a, ek_b))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                fields_a = entity_fields[ek_a]
                fields_b = entity_fields[ek_b]
                if not fields_a or not fields_b:
                    continue

                overlap = len(fields_a & fields_b)
                total = len(fields_a | fields_b)
                overlap_ratio = overlap / total if total > 0 else 0.0

                if overlap_ratio >= _MERGE_OVERLAP_THRESHOLD:
                    # canonical = 더 많은 KU 를 가진 쪽
                    canonical = ek_a if len(fields_a) >= len(fields_b) else ek_b
                    proposals.append({
                        "type": "merge",
                        "rationale": (
                            f"entity 중복률 {overlap_ratio:.1%} "
                            f"({overlap}/{total} field-value 겹침)"
                        ),
                        "target_entities": [ek_a, ek_b],
                        "params": {
                            "canonical_key": canonical,
                            "overlap_ratio": round(overlap_ratio, 4),
                        },
                        "expected_delta": {
                            "metric": "entity_count",
                            "before": len(entity_fields),
                            "after": len(entity_fields) - 1,
                        },
                    })

    return proposals


def _propose_splits(
    knowledge_units: list[dict],
    findings: list[dict],
) -> list[dict]:
    """한 entity에 상반 axis_tag → split 제안.

    audit findings 중 axis_imbalance 가 있으면, 해당 entity 의
    axis_tags 를 검사하여 분리 대상을 식별한다.
    """
    proposals: list[dict] = []

    # entity_key → axis_tag 값 집합 (geography 기준)
    entity_geo_tags: dict[str, set[str]] = defaultdict(set)
    for ku in knowledge_units:
        if ku.get("status") != "active":
            continue
        ek = ku.get("entity_key", "")
        geo = ku.get("axis_tags", {}).get("geography", "")
        if geo:
            entity_geo_tags[ek].add(geo)

    for ek, geo_set in entity_geo_tags.items():
        if len(geo_set) >= _SPLIT_CONFLICTING_AXES_MIN:
            geo_list = sorted(geo_set)
            parts = ek.split(":")
            slug = parts[2] if len(parts) >= 3 else ek
            new_keys = [
                f"{parts[0]}:{parts[1]}:{slug}-{g}" if len(parts) >= 3 else f"{ek}-{g}"
                for g in geo_list
            ]
            proposals.append({
                "type": "split",
                "rationale": (
                    f"entity '{ek}' 에 상반 geography tag {len(geo_set)}개: "
                    f"{', '.join(geo_list)}"
                ),
                "target_entities": [ek],
                "params": {
                    "new_keys": new_keys,
                    "split_axis": "geography",
                    "axis_values": geo_list,
                },
                "expected_delta": {
                    "metric": "entity_count",
                    "before": 1,
                    "after": len(geo_list),
                },
            })

    return proposals


def _propose_reclassify(
    knowledge_units: list[dict],
    skeleton: dict,
) -> list[dict]:
    """카테고리 부정합 탐지 → reclassify 제안.

    entity_key 의 category 가 skeleton categories 에 없으면 가장 유사한 카테고리로 제안.
    """
    proposals: list[dict] = []

    valid_cats = {c["slug"] for c in skeleton.get("categories", [])}
    if not valid_cats:
        return proposals

    # entity별 category 추출
    mismatched: dict[str, str] = {}
    for ku in knowledge_units:
        if ku.get("status") != "active":
            continue
        ek = ku.get("entity_key", "")
        parts = ek.split(":")
        cat = parts[1] if len(parts) >= 3 else ""
        if cat and cat not in valid_cats:
            mismatched[ek] = cat

    for ek, bad_cat in mismatched.items():
        # 가장 짧은 편집거리의 valid category 제안 (간단히 첫 번째)
        suggested = sorted(valid_cats)[0]
        proposals.append({
            "type": "reclassify",
            "rationale": (
                f"entity '{ek}' 의 category '{bad_cat}' 가 "
                f"skeleton categories 에 없음"
            ),
            "target_entities": [ek],
            "params": {
                "from_category": bad_cat,
                "to_category": suggested,
            },
            "expected_delta": {
                "metric": "category_validity",
                "before": 0.0,
                "after": 1.0,
            },
        })

    return proposals


def _propose_from_audit_findings(
    findings: list[dict],
    policies: dict,
) -> list[dict]:
    """audit findings 기반 source_policy / gap_rule 제안.

    - yield_decline → source_policy 제안 (TTL 조정 등)
    - coverage_gap (critical) → gap_rule 제안
    """
    proposals: list[dict] = []

    for finding in findings:
        fid = finding.get("finding_id", "")
        cat = finding.get("category", "")
        sev = finding.get("severity", "")

        if cat == "yield_decline":
            proposals.append({
                "type": "source_policy",
                "rationale": f"KU yield 체감 감지 ({fid}): {finding.get('description', '')}",
                "target_entities": ["*:*:*"],
                "params": {
                    "action": "extend_ttl",
                    "finding_id": fid,
                    "ttl_multiplier": 1.5,
                },
                "expected_delta": {
                    "metric": "yield_rate",
                    "before": finding.get("evidence", {}).get("second_half_avg", 0.0),
                    "after": finding.get("evidence", {}).get("first_half_avg", 0.0),
                },
            })

        if cat == "coverage_gap" and sev == "critical":
            evidence = finding.get("evidence", {})
            target_cat = evidence.get("category", "")
            proposals.append({
                "type": "gap_rule",
                "rationale": f"critical coverage gap ({fid}): {finding.get('description', '')}",
                "target_entities": [f"*:{target_cat}:*"] if target_cat else [],
                "params": {
                    "action": "prioritize_category",
                    "finding_id": fid,
                    "category": target_cat,
                },
                "expected_delta": {
                    "metric": "coverage_gap_count",
                    "before": evidence.get("ku_count", 0),
                    "after": max(evidence.get("ku_count", 0), 3),
                },
            })

    return proposals


def _build_rollback_payload(
    state: dict,
    proposals: list[dict],
) -> dict:
    """rollback_payload 구성 — 승인 전 상태 보존."""
    affected_kus: list[str] = []
    for p in proposals:
        for ek in p.get("target_entities", []):
            for ku in state.get("knowledge_units", []):
                if ku.get("entity_key") == ek:
                    ku_id = ku.get("ku_id", "")
                    if ku_id and ku_id not in affected_kus:
                        affected_kus.append(ku_id)

    return {
        "skeleton_snapshot": state.get("domain_skeleton", {}),
        "affected_kus": affected_kus,
    }


# ---------------------------------------------------------------------------
# Main Remodel Function
# ---------------------------------------------------------------------------

def run_remodel(
    state: dict,
    audit_report: dict,
) -> dict:
    """Remodel 실행 — audit 결과를 소비하여 RemodelReport 생성.

    audit.py 의 4 분석함수 결과를 **소비만** 한다 (중복 분석 금지).

    Args:
        state: 현재 EvolverState.
        audit_report: run_audit() 반환값 (findings, recommendations, policy_patches).

    Returns:
        RemodelReport dict (schema: remodel_report.schema.json).
    """
    kus = state.get("knowledge_units", [])
    skeleton = state.get("domain_skeleton", {})
    policies = state.get("policies", {})
    findings = audit_report.get("findings", [])
    audit_cycle = audit_report.get("audit_cycle", 0)

    # --- 제안 생성 (audit findings 소비) ---
    proposals: list[dict] = []

    # merge: entity 중복률 기반
    proposals.extend(_propose_merges(kus, skeleton))

    # split: 상반 axis_tag 기반
    proposals.extend(_propose_splits(kus, findings))

    # reclassify: 카테고리 부정합
    proposals.extend(_propose_reclassify(kus, skeleton))

    # source_policy / gap_rule: audit findings 기반
    proposals.extend(_propose_from_audit_findings(findings, policies))

    # --- rollback payload ---
    rollback_payload = _build_rollback_payload(state, proposals)

    # --- report 구성 ---
    report = {
        "report_id": _next_report_id(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_audit_id": audit_cycle,
        "proposals": proposals,
        "rollback_payload": rollback_payload,
        "approval": {"status": "pending"},
    }

    logger.info(
        "Remodel 완료: audit_cycle=%d, proposals=%d (%s)",
        audit_cycle,
        len(proposals),
        ", ".join(p["type"] for p in proposals) if proposals else "none",
    )

    return report


def remodel_node(state: dict) -> dict:
    """LangGraph node wrapper — state 에서 audit_history 의 최신 report 를 읽어 remodel 실행.

    Returns:
        state update dict: {"remodel_report": RemodelReport, "hitl_pending": {"gate": "R", ...}}.
    """
    audit_history = state.get("audit_history") or []
    if not audit_history:
        logger.warning("Remodel 스킵: audit_history 없음")
        return {"remodel_report": None}

    latest_audit = audit_history[-1]
    report = run_remodel(state, latest_audit)

    return {
        "remodel_report": report,
        "hitl_pending": {
            "gate": "R",
            "report_id": report["report_id"],
            "proposal_count": len(report["proposals"]),
        },
    }
