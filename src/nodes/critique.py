"""critique_node — Metrics + 실패모드 분석 + 수렴 판정 + 처방.

design-v2 §4~§5 기반.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from src.nodes.dispute_resolver import resolve_disputes
from src.state import EvolverState
from src.utils.metrics import (
    assess_health,
    compute_axis_coverage,
    compute_deficit_ratios,
    compute_metrics,
)

HIGH_RISK_LEVELS = {"safety", "financial", "policy"}


def _analyze_failure_modes(
    kus: list[dict],
    gap_map: list[dict],
    skeleton: dict,
    today: date | None = None,
) -> list[dict]:
    """6대 실패모드 분석 → 처방 목록."""
    if today is None:
        today = date.today()
    prescriptions: list[dict] = []
    rx_counter = 1

    # 1. Epistemic: 단일출처 high-risk KU
    for ku in kus:
        if ku.get("status") != "active":
            continue
        if len(ku.get("evidence_links", [])) <= 1:
            # risk 판정 (entity_key 기반 간이)
            entity_key = ku.get("entity_key", "")
            parts = entity_key.split(":")
            category = parts[1] if len(parts) >= 3 else ""
            if category in ("regulation",) or ku.get("confidence", 1.0) < 0.85:
                prescriptions.append({
                    "rx_id": f"RX-{rx_counter:04d}",
                    "type": "epistemic",
                    "description": f"{ku.get('ku_id')}: 단일출처, 독립 출처 추가 필요",
                    "target_ku": ku.get("ku_id"),
                })
                rx_counter += 1

    # 2. Temporal: expires_at 30일 이내
    for ku in kus:
        if ku.get("status") != "active":
            continue
        validity = ku.get("validity", {})
        expires_at = validity.get("expires_at")
        if expires_at:
            exp_date = date.fromisoformat(expires_at)
            if exp_date - timedelta(days=30) <= today:
                prescriptions.append({
                    "rx_id": f"RX-{rx_counter:04d}",
                    "type": "temporal",
                    "description": f"{ku.get('ku_id')}: expires_at {expires_at} 임박",
                    "target_ku": ku.get("ku_id"),
                })
                rx_counter += 1

    # 3. Consistency: disputed KU
    disputed = [ku for ku in kus if ku.get("status") == "disputed"]
    for ku in disputed:
        prescriptions.append({
            "rx_id": f"RX-{rx_counter:04d}",
            "type": "consistency",
            "description": f"{ku.get('ku_id')}: disputed 상태, 추가 수집 필요",
            "target_ku": ku.get("ku_id"),
        })
        rx_counter += 1

    # 4. Planning: 미커버 카테고리 > 50%
    categories = {c["slug"] for c in skeleton.get("categories", [])}
    covered_cats = set()
    for gu in gap_map:
        if gu.get("status") == "resolved":
            entity_key = gu.get("target", {}).get("entity_key", "")
            parts = entity_key.split(":")
            if len(parts) >= 2:
                covered_cats.add(parts[1])
    if categories and len(covered_cats) / len(categories) < 0.5:
        prescriptions.append({
            "rx_id": f"RX-{rx_counter:04d}",
            "type": "planning",
            "description": f"카테고리 커버리지 부족: {len(covered_cats)}/{len(categories)}",
        })
        rx_counter += 1

    return prescriptions


REFRESH_GU_CAP_DEFAULT = 10  # D-55: cycle당 refresh GU 기본 상한
MIN_KU_PER_CAT = 5   # D-56: 카테고리당 최소 KU 수


def _compute_refresh_cap(stale_count: int) -> int:
    """D-64: Adaptive REFRESH_GU_CAP — staleness 비례 스케일링.

    - stale > 50 → min(25, stale // 3)
    - stale > 20 → min(20, stale // 2)
    - else → REFRESH_GU_CAP_DEFAULT (10)
    """
    if stale_count > 50:
        return min(25, max(REFRESH_GU_CAP_DEFAULT, stale_count // 3))
    if stale_count > 20:
        return min(20, max(REFRESH_GU_CAP_DEFAULT, stale_count // 2))
    return REFRESH_GU_CAP_DEFAULT


def _generate_refresh_gus(
    kus: list[dict],
    gap_map: list[dict],
    max_gu_id: int,
    today: date | None = None,
) -> list[dict]:
    """TTL 만료 KU → stale refresh GU 자동생성.

    - 중복 방지: 동일 entity_key+field에 open refresh GU 있으면 스킵
    - cycle당 상한: Adaptive cap (D-64, staleness 비례)
    """
    if today is None:
        today = date.today()

    # 기존 open refresh GU 슬롯
    existing_refresh_slots = {
        (gu.get("target", {}).get("entity_key"), gu.get("target", {}).get("field"))
        for gu in gap_map
        if gu.get("gap_type") == "stale" and gu.get("status") == "open"
    }

    # TTL 만료 KU 수집
    stale_candidates: list[tuple[int, dict]] = []
    for ku in kus:
        if ku.get("status") != "active":
            continue
        observed = ku.get("observed_at")
        validity = ku.get("validity", {})
        ttl = validity.get("ttl_days")
        if observed and ttl is not None:
            obs_date = date.fromisoformat(observed)
            expire_date = obs_date + timedelta(days=ttl)
            if expire_date < today:
                days_over = (today - expire_date).days
                slot = (ku.get("entity_key"), ku.get("field"))
                if slot not in existing_refresh_slots:
                    stale_candidates.append((days_over, ku))

    # D-64: Adaptive cap 계산
    refresh_cap = _compute_refresh_cap(len(stale_candidates))

    # 우선순위: TTL 초과 일수 내림차순, 상한 적용
    stale_candidates.sort(key=lambda x: x[0], reverse=True)
    stale_candidates = stale_candidates[:refresh_cap]

    new_gus: list[dict] = []
    for _, ku in stale_candidates:
        max_gu_id += 1
        new_gus.append({
            "gu_id": f"GU-{max_gu_id:04d}",
            "gap_type": "stale",
            "target": {
                "entity_key": ku.get("entity_key", ""),
                "field": ku.get("field", ""),
            },
            "expected_utility": "high",
            "risk_level": ku.get("risk_level", "convenience"),
            "resolution_criteria": f"{ku.get('ku_id')} TTL 만료, 최신 정보 갱신",
            "status": "open",
            "trigger": "D:stale_refresh",
            "trigger_source": ku.get("ku_id", ""),
            "axis_tags": dict(ku.get("axis_tags", {})) if ku.get("axis_tags") else {},
            "created_at": today.isoformat(),
        })

    return new_gus


def _generate_balance_gus(
    kus: list[dict],
    gap_map: list[dict],
    skeleton: dict,
    max_gu_id: int,
    today: date | None = None,
) -> list[dict]:
    """min_ku < MIN_KU_PER_CAT인 카테고리 → 균형 GU 생성.

    category-specific 필드 우선, expansion_mode="jump".
    """
    if today is None:
        today = date.today()

    categories = [c["slug"] for c in skeleton.get("categories", [])]
    if not categories:
        return []

    # 카테고리별 active KU 수
    cat_counts: dict[str, int] = {c: 0 for c in categories}
    for ku in kus:
        if ku.get("status") != "active":
            continue
        parts = ku.get("entity_key", "").split(":")
        cat = parts[1] if len(parts) >= 3 else ""
        if cat in cat_counts:
            cat_counts[cat] += 1

    # 기존 open GU 슬롯
    existing_open_slots = {
        (gu.get("target", {}).get("entity_key"), gu.get("target", {}).get("field"))
        for gu in gap_map
        if gu.get("status") == "open"
    }

    fields = skeleton.get("fields", [])
    new_gus: list[dict] = []

    for cat, count in cat_counts.items():
        if count >= MIN_KU_PER_CAT:
            continue
        needed = MIN_KU_PER_CAT - count
        # category-specific 필드 우선
        applicable = [
            f["name"] for f in fields
            if cat in f.get("categories", [])
        ] + [
            f["name"] for f in fields
            if "*" in f.get("categories", [])
        ]
        # 중복 제거, 순서 유지
        seen: set[str] = set()
        unique_fields: list[str] = []
        for fn in applicable:
            if fn not in seen:
                seen.add(fn)
                unique_fields.append(fn)

        generated = 0
        for fn in unique_fields:
            if generated >= needed:
                break
            entity_key = f"{skeleton.get('domain', 'unknown')}:{cat}:balance-{generated}"
            slot = (entity_key, fn)
            if slot in existing_open_slots:
                continue
            max_gu_id += 1
            new_gus.append({
                "gu_id": f"GU-{max_gu_id:04d}",
                "gap_type": "missing",
                "target": {"entity_key": entity_key, "field": fn},
                "expected_utility": "high",
                "risk_level": "informational",
                "resolution_criteria": f"{cat} 카테고리 균형 보충: {fn}",
                "status": "open",
                "trigger": "E:category_balance",
                "trigger_source": f"cat:{cat}",
                "expansion_mode": "jump",
                "created_at": today.isoformat(),
            })
            generated += 1

    return new_gus


def _generate_machine_rules(
    state: dict,
    rates: dict,
    deficits: dict,
) -> list[dict]:
    """P4-B2: metric 기반 machine-readable 처방 규칙 생성.

    각 규칙: {rule, condition, action, target, value}.
    """
    rules: list[dict] = []
    coverage_map = state.get("coverage_map") or {}
    novelty_history = state.get("novelty_history") or []
    summary = coverage_map.get("summary", {})

    # 1. coverage_deficit > 0.5 → explore
    for axis, deficit in deficits.items():
        if deficit > 0.5:
            rules.append({
                "rule": f"coverage_deficit>{0.5}",
                "condition": f"axis={axis}, deficit={deficit:.2f}",
                "action": "explore",
                "target_axis": axis,
                "value": round(deficit, 4),
            })

    # 2. category_gini > 0.45 → diversify
    cat_gini = summary.get("category_gini", 0)
    if cat_gini > 0.45:
        rules.append({
            "rule": "category_gini>0.45",
            "condition": f"gini={cat_gini:.3f}",
            "action": "diversify",
            "target": "category_balance",
            "value": round(cat_gini, 4),
        })

    # 3. field_gini > 0.45 → diversify_fields
    field_gini = summary.get("field_gini", 0)
    if field_gini > 0.45:
        rules.append({
            "rule": "field_gini>0.45",
            "condition": f"gini={field_gini:.3f}",
            "action": "diversify_fields",
            "target": "field_balance",
            "value": round(field_gini, 4),
        })

    # 4. novelty < 0.1 (최근 3c 평균) → jump
    if len(novelty_history) >= 3:
        recent_avg = sum(novelty_history[-3:]) / 3
        if recent_avg < 0.1:
            rules.append({
                "rule": "novelty_avg<0.1",
                "condition": f"avg_3c={recent_avg:.3f}",
                "action": "jump",
                "target": "exploration_strategy",
                "value": round(recent_avg, 4),
            })

    # 5. conflict_rate > 0.10 → resolve_conflicts
    cr = rates.get("conflict_rate", 0)
    if cr > 0.10:
        rules.append({
            "rule": "conflict_rate>0.10",
            "condition": f"rate={cr:.3f}",
            "action": "resolve_conflicts",
            "target": "dispute_resolution",
            "value": round(cr, 4),
        })

    # 6. evidence_rate < 0.90 → collect_evidence
    er = rates.get("evidence_rate", 1.0)
    if er < 0.90:
        rules.append({
            "rule": "evidence_rate<0.90",
            "condition": f"rate={er:.3f}",
            "action": "collect_evidence",
            "target": "evidence_gaps",
            "value": round(er, 4),
        })

    return rules


CONFLICT_RATE_THRESHOLD = 0.15  # D-43: C6 수렴 조건 임계치


def _check_convergence(
    kus: list[dict],
    gap_map: list[dict],
    skeleton: dict,
    cycle: int,
    metrics_rates: dict,
    net_gap_changes: list[int] | None = None,
    audit_history: list[dict] | None = None,
) -> dict:
    """수렴 조건 판정 (C1~C6)."""
    result = {
        "converged": False,
        "conditions": {},
    }

    if cycle < 5:
        result["conditions"]["min_cycle"] = False
        return result

    result["conditions"]["min_cycle"] = True

    # C1: critical+high open 비율 < 10%
    critical_high = [
        gu for gu in gap_map
        if gu.get("expected_utility") in ("critical", "high")
    ]
    critical_high_open = [gu for gu in critical_high if gu.get("status") == "open"]
    c1 = (len(critical_high_open) / len(critical_high) < 0.10) if critical_high else True
    result["conditions"]["C1_critical_high_resolved"] = c1

    # C2: stale open 비율 < 15%
    stale_gus = [gu for gu in gap_map if gu.get("gap_type") == "stale"]
    stale_open = [gu for gu in stale_gus if gu.get("status") == "open"]
    c2 = (len(stale_open) / len(stale_gus) < 0.15) if stale_gus else True
    result["conditions"]["C2_stale_resolved"] = c2

    # C3: net_gap_change 3 Cycle > -1
    c3 = True
    if net_gap_changes and len(net_gap_changes) >= 3:
        recent = net_gap_changes[-3:]
        c3 = all(ngc > -1 for ngc in recent)
    result["conditions"]["C3_gap_stable"] = c3

    # C4: avg_confidence >= 0.85
    c4 = metrics_rates.get("avg_confidence", 0) >= 0.85
    result["conditions"]["C4_avg_confidence"] = c4

    # C5: 카테고리 커버리지 >= 80%
    categories = {c["slug"] for c in skeleton.get("categories", [])}
    covered = set()
    for gu in gap_map:
        if gu.get("status") == "resolved":
            entity_key = gu.get("target", {}).get("entity_key", "")
            parts = entity_key.split(":")
            if len(parts) >= 2:
                covered.add(parts[1])
    c5 = (len(covered) / len(categories) >= 0.80) if categories else True
    result["conditions"]["C5_category_coverage"] = c5

    # C6: conflict_rate < CONFLICT_RATE_THRESHOLD (D-43)
    c6 = metrics_rates.get("conflict_rate", 0) < CONFLICT_RATE_THRESHOLD
    result["conditions"]["C6_conflict_rate"] = c6

    # C7: Audit 건강도 — critical findings 없어야 수렴 허용 (Task 4.9)
    c7 = True
    if audit_history:
        latest_audit = audit_history[-1]
        critical_findings = [
            f for f in latest_audit.get("findings", [])
            if f.get("severity") == "critical"
        ]
        c7 = len(critical_findings) == 0
    result["conditions"]["C7_audit_health"] = c7

    result["converged"] = c1 and c2 and c3 and c4 and c5 and c6 and c7

    return result


def critique_node(
    state: EvolverState,
    *,
    llm: Any | None = None,
    today: date | None = None,
) -> dict:
    """Metrics 계산 + 실패모드 분석 + 수렴 판정 + Critique Report 생성."""
    if today is None:
        today = date.today()

    kus = state.get("knowledge_units", [])
    gap_map = state.get("gap_map", [])
    skeleton = state.get("domain_skeleton", {})
    cycle = state.get("current_cycle", 1)
    prev_metrics = state.get("metrics", {})

    # Metrics 계산
    rates = compute_metrics(
        {"knowledge_units": kus, "gap_map": gap_map},
        today=today,
    )
    health = assess_health(rates)

    # Axis Coverage 재계산
    axis_cov = compute_axis_coverage(gap_map, skeleton)
    deficits = compute_deficit_ratios(axis_cov, skeleton)

    # Dispute Resolution (Phase 3 Stage B) + P1-B2 conflict_ledger 연동
    conflict_ledger = state.get("conflict_ledger", [])
    dispute_log = resolve_disputes(kus, llm=llm, conflict_ledger=conflict_ledger)

    # 실패모드 분석 (dispute resolution 후 — 해소된 KU는 consistency 처방 불필요)
    prescriptions = _analyze_failure_modes(kus, gap_map, skeleton, today)

    # 해소된 dispute에 대한 처방 추가
    rx_counter = len(prescriptions) + 1
    for entry in dispute_log:
        prescriptions.append({
            "rx_id": f"RX-{rx_counter:04d}",
            "type": "dispute_resolved",
            "description": (
                f"{entry['ku_id']}: disputed→active 해소 ({entry['reason']})"
            ),
            "target_ku": entry["ku_id"],
        })
        rx_counter += 1

    # Category 균형 GU 생성 (Task 5.7)
    max_gu_id = 0
    for gu in gap_map:
        gu_id_str = gu.get("gu_id", "")
        if gu_id_str.startswith("GU-"):
            try:
                num = int(gu_id_str.replace("GU-", ""))
                max_gu_id = max(max_gu_id, num)
            except ValueError:
                pass
    balance_gus = _generate_balance_gus(kus, gap_map, skeleton, max_gu_id, today)
    if balance_gus:
        gap_map = list(gap_map)
        gap_map.extend(balance_gus)
        # max_gu_id 업데이트
        for gu in balance_gus:
            gu_id_str = gu.get("gu_id", "")
            if gu_id_str.startswith("GU-"):
                try:
                    num = int(gu_id_str.replace("GU-", ""))
                    max_gu_id = max(max_gu_id, num)
                except ValueError:
                    pass

    # Stale KU → Refresh GU 자동생성 (Task 5.5)
    refresh_gus = _generate_refresh_gus(kus, gap_map, max_gu_id, today)
    if refresh_gus:
        gap_map = list(gap_map)  # 원본 변경 방지
        gap_map.extend(refresh_gus)

    # net_gap_change 계산 (open GU 변화)
    prev_counts = prev_metrics.get("counts", {})
    prev_open = prev_counts.get("total_gu_open", 0)
    curr_open = sum(1 for gu in gap_map if gu.get("status") == "open")
    net_gap_change = curr_open - prev_open

    # 누적 net_gap_changes
    net_gap_changes = list(state.get("net_gap_changes", []))
    net_gap_changes.append(net_gap_change)

    # 수렴 판정 — audit_history 전달 (Task 4.9: C7 건강도 조건)
    audit_history = state.get("audit_history") or []
    convergence = _check_convergence(
        kus, gap_map, skeleton, cycle, rates, net_gap_changes,
        audit_history=audit_history,
    )

    # Delta 계산
    prev_rates = prev_metrics.get("rates", {})
    delta = {}
    for key in rates:
        if key in prev_rates:
            if isinstance(rates[key], (int, float)) and isinstance(prev_rates[key], (int, float)):
                delta[key] = round(rates[key] - prev_rates[key], 4)

    # Counts
    counts = {
        "total_ku": len(kus),
        "active_ku": sum(1 for ku in kus if ku.get("status") == "active"),
        "disputed_ku": sum(1 for ku in kus if ku.get("status") == "disputed"),
        "deprecated_ku": sum(1 for ku in kus if ku.get("status") == "deprecated"),
        "total_gu_open": sum(1 for gu in gap_map if gu.get("status") == "open"),
        "total_gu_resolved": sum(1 for gu in gap_map if gu.get("status") == "resolved"),
        "total_gu_deferred": sum(1 for gu in gap_map if gu.get("status") == "deferred"),
    }

    # Metrics 객체 구축
    new_metrics = {
        "cycle": cycle,
        "phase": "post_critique",
        "timestamp": today.isoformat(),
        "counts": counts,
        "rates": rates,
        "delta_from_prev_cycle": delta,
    }

    # P4-B2: Machine-readable 처방 규칙 생성
    machine_rules = _generate_machine_rules(state, rates, deficits)

    # Critique Report
    critique_report = {
        "cycle": cycle,
        "health": health,
        "prescriptions": prescriptions,
        "machine_rules": machine_rules,
        "convergence": convergence,
        "deficit_ratios": deficits,
    }

    # AxisCoverageEntry 리스트 변환
    axis_coverage_entries: list[dict] = []
    for axis_name, anchors in axis_cov.items():
        axis_deficit = deficits.get(axis_name, 0.0)
        for anchor, data in anchors.items():
            total = data.get("open", 0) + data.get("resolved", 0)
            cov = data.get("resolved", 0) / total if total > 0 else 0.0
            axis_coverage_entries.append({
                "axis": axis_name,
                "anchor": anchor,
                "open_count": data.get("open", 0),
                "resolved_count": data.get("resolved", 0),
                "total_count": total,
                "coverage": round(cov, 3),
                "deficit_ratio": axis_deficit,
            })

    result = {
        "current_critique": critique_report,
        "axis_coverage": axis_coverage_entries,
        "metrics": new_metrics,
        "net_gap_changes": net_gap_changes,
    }

    # balance/refresh GU가 추가되었으면 gap_map 반환
    if refresh_gus or balance_gus:
        result["gap_map"] = gap_map

    # dispute resolution으로 KU 상태가 변경되었으면 반환
    if dispute_log:
        result["knowledge_units"] = kus

    # P1-B2: conflict_ledger 가 업데이트되었으면 반환
    if conflict_ledger:
        result["conflict_ledger"] = conflict_ledger

    return result
