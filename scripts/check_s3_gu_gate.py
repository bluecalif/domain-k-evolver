"""S3 GU Mechanistic Gate (M-Gate) — V/O composite + M criteria 평가.

Plan: C:\\Users\\User\\.claude\\plans\\b-plann-very-carefully-breezy-flame.md

Usage:
    python scripts/check_s3_gu_gate.py \\
        --baseline bench/silver/japan-travel/p7-rebuild-s3-smoke \\
        --target   bench/silver/japan-travel/p7-rebuild-s3-gu-smoke \\
        [--json out.json] [--strict]

Exit codes:
    0  PASS         (V/O 모두 PASS ∧ M FAIL 0)
    1  FAIL         (V/O FAIL 어느 하나라도 — V/O 우선 정책)
    2  ERROR        (파일 부재, schema 파싱 오류)
    3  CONDITIONAL  (V/O PASS ∧ M 일부 FAIL — diagnosis 필요하나 release-blocker 아님)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

# 직접 실행 시 (python scripts/check_s3_gu_gate.py) repo root 를 sys.path 에 추가.
# pytest 는 pyproject.toml `pythonpath=["."]` 로 처리되어 영향 없음.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts._gate_helpers import (
    count_adj_gus,
    kl_divergence,
    load_json,
    snapshot_diff_adj,
)


# ── Constants (plan §1, §2 — 임계값 근거는 plan 본문 참조) ────────────

WILDCARD_PARALLEL_FIELDS = {"price", "duration", "how_to_use", "acceptance", "where_to_buy"}

P_ZONE_TOTAL = 97
V1_REQUIRED_DELTA = 29  # P-zone 30%

O1_VACANT_FLOOR = 5
COLLECT_BUDGET_5C = 50  # 추정 (5c × 10 GUs/c — telemetry 추가 후 동적화 가능)
O1_BACKLOG_MULT = 1.5

O2_KL_MAX = 0.5

M1_MIN_ABS = 12
M1_MIN_RATIO = 2.0
M2_MIN_RATIO = 0.70
M3_MIN_ABS = 18
M3_MIN_RATIO = 1.5
M3_TARGET_CATS = {"regulation", "pass-ticket"}
M4_MIN_DELTA = 2
M4_MIN_ABS = 6
M6_MIN_RATIO = 0.9
M8_MIN_RATIO = 0.95
M9_ORIGIN_COVERAGE_MIN = 0.90
M10_CYCLE_COVERAGE_MIN = 0.90

_GU_VALID_ORIGINS = frozenset({"claim_loop", "post_cycle_sweep", "seed_bootstrap"})

VXO_VACANT_FLOOR_PER_ENTITY = 0.5
VXO_OPEN_RATIO_MIN = 0.05
VXO_VACANT_REDUCTION_RATIO = 0.20


# ── Result dataclass ───────────────────────────────────────────


@dataclass
class Result:
    id: str
    label: str
    detail: str
    passed: bool | None  # None = NA
    is_v_or_o: bool = False
    is_telemetry_deferred: bool = False


# ── Trial loader ───────────────────────────────────────────────


@dataclass
class TrialData:
    path: Path
    matrix: dict
    gap_map: list[dict]
    knowledge_units: list[dict]
    conflict_ledger: list[dict]
    adjacency_yield: list[dict]
    trajectory: list[dict]
    snapshots_dir: Path


def load_trial(trial_dir: Path) -> TrialData:
    trial_dir = Path(trial_dir)
    matrix_path = trial_dir / "entity-field-matrix.json"
    state_dir = trial_dir / "state"
    snapshots_dir = trial_dir / "state-snapshots"
    trajectory_path = trial_dir / "trajectory" / "trajectory.json"

    for required in (matrix_path, state_dir, snapshots_dir, trajectory_path):
        if not required.exists():
            raise FileNotFoundError(f"Required artifact missing: {required}")

    return TrialData(
        path=trial_dir,
        matrix=load_json(matrix_path),
        gap_map=load_json(state_dir / "gap-map.json"),
        knowledge_units=load_json(state_dir / "knowledge-units.json"),
        conflict_ledger=load_json(state_dir / "conflict-ledger.json"),
        adjacency_yield=load_json(state_dir / "adjacency-yield.json"),
        trajectory=load_json(trajectory_path),
        snapshots_dir=snapshots_dir,
    )


# ── Measurement helpers ────────────────────────────────────────


def _vacant_total(t: TrialData) -> int:
    return t.matrix["summary"]["vacant"]


def _by_cat(t: TrialData, key: str) -> dict[str, int]:
    return {cat: stats.get(key, 0) for cat, stats in t.matrix["summary"]["by_category"].items()}


def _entity_count_per_cat(t: TrialData) -> dict[str, int]:
    return {
        cat: len(cat_data.get("matrix", {}))
        for cat, cat_data in t.matrix.get("categories", {}).items()
    }


def _untouched_entities(t: TrialData) -> int:
    """모든 field state == 'vacant' 인 entity 수 (KU·GU 어느 것도 없음)."""
    n = 0
    for cat_data in t.matrix.get("categories", {}).values():
        for ent_fields in cat_data.get("matrix", {}).values():
            if ent_fields and all(c.get("state") == "vacant" for c in ent_fields.values()):
                n += 1
    return n


def _named_entity_adj_count(t: TrialData) -> int:
    def not_wildcard(g: dict) -> bool:
        ek = g.get("target", {}).get("entity_key", "")
        parts = ek.split(":")
        return len(parts) >= 3 and parts[2] != "*"

    return count_adj_gus(t.gap_map, predicate=not_wildcard)


def _wildcard_pair_ratio(t: TrialData) -> tuple[int, int]:
    """WPF field 별로 entity-specific adj GU 와 같은 (cat,*) wildcard GU 의 짝지어진 비율.

    Returns: (paired, total_entity_specific_on_wpf)
    """
    by_cat_field: dict[tuple[str, str], set[str]] = {}
    for gu in t.gap_map:
        if gu.get("trigger") != "A:adjacent_gap":
            continue
        ek = gu.get("target", {}).get("entity_key", "")
        parts = ek.split(":")
        if len(parts) < 3:
            continue
        cat, slug = parts[1], parts[2]
        fld = gu.get("target", {}).get("field", "")
        by_cat_field.setdefault((cat, fld), set()).add(slug)

    paired = 0
    total = 0
    for (cat, fld), slugs in by_cat_field.items():
        if fld not in WILDCARD_PARALLEL_FIELDS:
            continue
        entity_slugs = {s for s in slugs if s != "*"}
        has_wildcard = "*" in slugs
        for _ in entity_slugs:
            total += 1
            if has_wildcard:
                paired += 1
    return paired, total


def _gus_in_cats(t: TrialData, cats: set[str]) -> int:
    n = 0
    for gu in t.gap_map:
        ek = gu.get("target", {}).get("entity_key", "")
        parts = ek.split(":")
        if len(parts) >= 2 and parts[1] in cats:
            n += 1
    return n


def _adj_field_diversity(t: TrialData) -> int:
    fields = set()
    for gu in t.gap_map:
        if gu.get("trigger") == "A:adjacent_gap":
            f = gu.get("target", {}).get("field")
            if f:
                fields.add(f)
    return len(fields)


def _adj_yield_avg(t: TrialData) -> float:
    rows = t.adjacency_yield
    if not rows:
        return 0.0
    return sum(r.get("yield", 0.0) for r in rows) / len(rows)


def _conflict_target_set(t: TrialData) -> set[tuple[str, str]]:
    """conflict-ledger 의 ku_id 들을 KU 파일에서 (entity_key, field) 로 역참조.

    plan §2 M7 의 '최근 2 cycle' 시간 한정은 ledger 에 cycle 정보 부재로 구현 불가.
    현재 ledger 전체 conflict 의 (entity_key, field) 집합으로 단순화 (loose check).
    """
    ku_by_id = {ku.get("ku_id"): ku for ku in t.knowledge_units}
    targets: set[tuple[str, str]] = set()
    for entry in t.conflict_ledger:
        ku_id = entry.get("ku_id")
        ku = ku_by_id.get(ku_id)
        if ku is None:
            continue
        ek = ku.get("entity_key")
        fld = ku.get("field")
        if ek and fld:
            targets.add((ek, fld))
    return targets


def _last_ku_active(t: TrialData) -> int:
    if not t.trajectory:
        return 0
    return t.trajectory[-1].get("ku_active", 0)


# ── V/O criteria ───────────────────────────────────────────────


def eval_v1(b: TrialData, t: TrialData, *, self_mode: bool) -> Result:
    bv, tv = _vacant_total(b), _vacant_total(t)
    delta = bv - tv
    if self_mode:
        passed = tv <= bv
        detail = f"self-mode: target={tv}, baseline={bv} (no-regression {'OK' if passed else 'NO'})"
    else:
        passed = delta >= V1_REQUIRED_DELTA
        detail = f"Δ={delta} (need ≥{V1_REQUIRED_DELTA}; P-zone {P_ZONE_TOTAL}×30%)"
    return Result("V1", "vacant_total_reduction", detail, passed, is_v_or_o=True)


def eval_v2(b: TrialData, t: TrialData, *, self_mode: bool) -> Result:
    bcv = _by_cat(b, "vacant")
    tcv = _by_cat(t, "vacant")
    regressions = []
    for cat, tv in tcv.items():
        bv = bcv.get(cat, 0)
        if tv > bv:
            regressions.append(f"{cat} +{tv - bv}")
    passed = len(regressions) == 0
    detail = "no regression" if passed else "; ".join(regressions)
    return Result("V2", "per_category_vacant_no_regression", detail, passed, is_v_or_o=True)


def eval_v3(b: TrialData, t: TrialData, *, self_mode: bool) -> Result:
    bu, tu = _untouched_entities(b), _untouched_entities(t)
    passed = tu <= bu
    detail = f"target={tu}, baseline={bu}"
    return Result("V3", "untouched_entity_bound", detail, passed, is_v_or_o=True)


def eval_o1(b: TrialData, t: TrialData, *, self_mode: bool) -> Result:
    tcv = _by_cat(t, "vacant")
    tco = _by_cat(t, "gu_open")
    abandoned = [cat for cat, v in tcv.items() if v >= O1_VACANT_FLOOR and tco.get(cat, 0) == 0]
    total_open = t.matrix["summary"].get("gu_open", 0)
    backlog_limit = int(COLLECT_BUDGET_5C * O1_BACKLOG_MULT)
    backlog_ok = total_open <= backlog_limit

    parts = []
    if abandoned:
        parts.append(f"abandoned: {', '.join(f'{c}(v={tcv[c]},o=0)' for c in abandoned)}")
    else:
        parts.append("no abandoned cats")
    if not backlog_ok:
        parts.append(f"backlog: open={total_open} > {backlog_limit}")
    passed = (not abandoned) and backlog_ok
    return Result("O1", "active_frontier_existence", "; ".join(parts), passed, is_v_or_o=True)


def eval_o2(b: TrialData, t: TrialData, *, self_mode: bool) -> Result:
    tcv = _by_cat(t, "vacant")
    tco = _by_cat(t, "gu_open")
    total_v = sum(tcv.values())
    total_o = sum(tco.values())

    if total_v == 0:
        return Result("O2", "open_gu_category_coverage", "vacant total=0 (nothing to cover)", True, is_v_or_o=True)
    if total_o == 0:
        any_vacant = any(v > 0 for v in tcv.values())
        if any_vacant:
            return Result(
                "O2",
                "open_gu_category_coverage",
                "open_gu total=0 with vacant>0 (KL=∞)",
                False,
                is_v_or_o=True,
            )
        return Result("O2", "open_gu_category_coverage", "all-zero (NA)", True, is_v_or_o=True)

    vacant_share = {cat: v / total_v for cat, v in tcv.items()}
    open_share = {cat: tco.get(cat, 0) / total_o for cat in tcv}
    kl = kl_divergence(vacant_share, open_share)
    passed = kl <= O2_KL_MAX
    kl_str = "∞" if kl == float("inf") else f"{kl:.3f}"
    detail = f"KL(vacant_share || open_share) = {kl_str} (max {O2_KL_MAX})"
    return Result("O2", "open_gu_category_coverage", detail, passed, is_v_or_o=True)


def eval_vxo(b: TrialData, t: TrialData, *, self_mode: bool) -> Result:
    """각 cat 가 cond_done ∨ cond_active ∨ cond_improving 하나라도 만족."""
    tcv = _by_cat(t, "vacant")
    tco = _by_cat(t, "gu_open")
    bcv = _by_cat(b, "vacant")
    ent_count = _entity_count_per_cat(t)

    failures = []
    for cat, tv in tcv.items():
        floor = ent_count.get(cat, 0) * VXO_VACANT_FLOOR_PER_ENTITY
        cond_done = tv <= floor
        to = tco.get(cat, 0)
        cond_active = to >= 1 and tv > 0 and (to / tv) >= VXO_OPEN_RATIO_MIN
        bv = bcv.get(cat, 0)
        cond_improving = bv > 0 and (bv - tv) / bv >= VXO_VACANT_REDUCTION_RATIO
        if not (cond_done or cond_active or cond_improving):
            failures.append(f"{cat}(v={tv},o={to},base={bv})")

    n_total = len(tcv)
    n_fail = len(failures)
    detail = f"{n_total - n_fail}/{n_total} cats healthy"
    if failures:
        shown = failures[:3]
        more = "..." if n_fail > 3 else ""
        detail += f"; failed: {', '.join(shown)}{more}"
    passed = n_fail == 0
    return Result("VxO", "frontier_health", detail, passed, is_v_or_o=True)


# ── M criteria ─────────────────────────────────────────────────


def eval_m1(b: TrialData, t: TrialData, *, self_mode: bool) -> Result:
    bn, tn = _named_entity_adj_count(b), _named_entity_adj_count(t)
    if self_mode:
        passed = tn >= bn
        detail = f"self-mode: target={tn}, baseline={bn}"
    else:
        ratio = tn / bn if bn > 0 else float("inf")
        passed = tn >= M1_MIN_ABS and ratio >= M1_MIN_RATIO
        detail = f"target={tn}, baseline={bn}, ratio={ratio:.2f} (need ≥{M1_MIN_ABS} ∧ ≥{M1_MIN_RATIO}×)"
    return Result("M1", "named_entity_adj_gu_count", detail, passed)


def eval_m2(t: TrialData) -> Result:
    paired, total = _wildcard_pair_ratio(t)
    if total == 0:
        return Result("M2", "wildcard_parallel_pair_ratio", "no entity-specific WPF GUs", None)
    ratio = paired / total
    passed = ratio >= M2_MIN_RATIO
    return Result(
        "M2",
        "wildcard_parallel_pair_ratio",
        f"{paired}/{total}={ratio:.2f} (need ≥{M2_MIN_RATIO})",
        passed,
    )


def eval_m3(b: TrialData, t: TrialData, *, self_mode: bool) -> Result:
    bn = _gus_in_cats(b, M3_TARGET_CATS)
    tn = _gus_in_cats(t, M3_TARGET_CATS)
    if self_mode:
        passed = tn >= bn
        detail = f"self-mode: target={tn}, baseline={bn}"
    else:
        ratio = tn / bn if bn > 0 else float("inf")
        passed = tn >= M3_MIN_ABS and ratio >= M3_MIN_RATIO
        detail = f"target={tn}, baseline={bn}, ratio={ratio:.2f} (need ≥{M3_MIN_ABS} ∧ ≥{M3_MIN_RATIO}×)"
    return Result("M3", "reg_pass_ticket_gu_count", detail, passed)


def eval_m4(b: TrialData, t: TrialData, *, self_mode: bool) -> Result:
    bd, td = _adj_field_diversity(b), _adj_field_diversity(t)
    if self_mode:
        passed = td >= bd
        detail = f"self-mode: target={td}, baseline={bd}"
    else:
        passed = td >= bd + M4_MIN_DELTA and td >= M4_MIN_ABS
        detail = f"target={td}, baseline={bd} (need ≥+{M4_MIN_DELTA} ∧ ≥{M4_MIN_ABS})"
    return Result("M4", "adj_gu_field_diversity", detail, passed)


def eval_m5(t: TrialData, *, strict: bool) -> Result:
    diffs = snapshot_diff_adj(t.snapshots_dir)
    if len(diffs) < 4:
        return Result("M5", "late_cycle_adj_gen", f"only {len(diffs) + 1} cycles available", None)
    d_c4, d_c5 = diffs[2], diffs[3]
    if strict:
        passed = d_c4 > 0 and d_c5 > 0
        rule = "Δc4>0 ∧ Δc5>0 (strict)"
    else:
        passed = d_c4 > 0 or d_c5 > 0
        rule = "Δc4>0 ∨ Δc5>0 (weak)"
    return Result("M5", "late_cycle_adj_gen", f"Δc4={d_c4}, Δc5={d_c5}; {rule}", passed)


def eval_m6(b: TrialData, t: TrialData, *, self_mode: bool) -> Result:
    by, ty = _adj_yield_avg(b), _adj_yield_avg(t)
    if self_mode:
        passed = ty >= by - 1e-9
        detail = f"self-mode: target={ty:.3f}, baseline={by:.3f}"
    else:
        ratio = ty / by if by > 0 else float("inf")
        passed = ratio >= M6_MIN_RATIO
        detail = f"target={ty:.3f}, baseline={by:.3f}, ratio={ratio:.2f} (need ≥{M6_MIN_RATIO})"
    return Result("M6", "adj_yield_floor", detail, passed)


def eval_m7(b: TrialData, t: TrialData, *, self_mode: bool) -> Result:
    """Conflict 발생 (entity_key, field) 에 adj GU 가 동일 target 으로 재생성되었는지 (loose check).

    Plan §2 M7 의 '최근 2 cycle' 시간 한정은 ledger cycle 정보 부재로 구현 불가 →
    ledger 전체 conflict 의 (entity_key, field) 와 adj GU target 의 교집합 카운트로 단순화.
    M10 telemetry (created_cycle) 추가 시 strict version 으로 강화.
    """
    conflict_targets = _conflict_target_set(t)
    if not conflict_targets:
        return Result("M7", "conflict_regen_zero", "no conflicts in ledger", True)
    violations = 0
    for gu in t.gap_map:
        if gu.get("trigger") != "A:adjacent_gap":
            continue
        ek = gu.get("target", {}).get("entity_key", "")
        fld = gu.get("target", {}).get("field", "")
        if (ek, fld) in conflict_targets:
            violations += 1
    passed = violations == 0
    return Result(
        "M7",
        "conflict_regen_zero",
        f"violations={violations} (loose check; M10 telemetry needed for strict)",
        passed,
    )


def eval_m8(b: TrialData, t: TrialData, *, self_mode: bool) -> Result:
    bk, tk = _last_ku_active(b), _last_ku_active(t)
    if self_mode:
        passed = tk >= bk
        detail = f"self-mode: target={tk}, baseline={bk}"
    else:
        ratio = tk / bk if bk > 0 else float("inf")
        passed = ratio >= M8_MIN_RATIO
        detail = f"target={tk}, baseline={bk}, ratio={ratio:.2f} (need ≥{M8_MIN_RATIO})"
    return Result("M8", "ku_active_sanity", detail, passed)


def eval_m5b(t: TrialData) -> Result:
    """M5b: cap_hit_count telemetry 존재 여부 — trajectory 100% coverage."""
    if not t.trajectory:
        return Result("M5b", "dynamic_cap_hit", "no trajectory", False)
    total = len(t.trajectory)
    present = sum(1 for e in t.trajectory if "cap_hit_count" in e)
    passed = present == total
    return Result(
        "M5b", "dynamic_cap_hit",
        f"coverage={present}/{total} (need 100%)",
        passed,
    )


def eval_m9(t: TrialData) -> Result:
    """M9: adj GU origin attribution ≥ 90% coverage."""
    adj = [g for g in t.gap_map if g.get("trigger") == "A:adjacent_gap"]
    if not adj:
        return Result("M9", "sweep_attribution", "no adj GUs", None)
    total = len(adj)
    with_origin = sum(1 for g in adj if g.get("origin") in _GU_VALID_ORIGINS)
    coverage = with_origin / total
    passed = coverage >= M9_ORIGIN_COVERAGE_MIN
    return Result(
        "M9", "sweep_attribution",
        f"coverage={with_origin}/{total}={coverage:.2f} (need ≥{M9_ORIGIN_COVERAGE_MIN})",
        passed,
    )


def eval_m10(t: TrialData) -> Result:
    """M10: created_cycle int 필드 ≥ 90% coverage in adj GUs."""
    adj = [g for g in t.gap_map if g.get("trigger") == "A:adjacent_gap"]
    if not adj:
        return Result("M10", "created_cycle", "no adj GUs", None)
    total = len(adj)
    with_cycle = sum(1 for g in adj if isinstance(g.get("created_cycle"), int))
    coverage = with_cycle / total
    passed = coverage >= M10_CYCLE_COVERAGE_MIN
    return Result(
        "M10", "created_cycle",
        f"coverage={with_cycle}/{total}={coverage:.2f} (need ≥{M10_CYCLE_COVERAGE_MIN})",
        passed,
    )


def eval_m11(t: TrialData) -> Result:
    """M11: adj_gen_count + wildcard_gen_count telemetry 존재 — trajectory 100% coverage."""
    if not t.trajectory:
        return Result("M11", "per_cycle_counts", "no trajectory", False)
    total = len(t.trajectory)
    with_adj = sum(1 for e in t.trajectory if "adj_gen_count" in e)
    with_wc = sum(1 for e in t.trajectory if "wildcard_gen_count" in e)
    present = min(with_adj, with_wc)
    passed = present == total
    return Result(
        "M11", "per_cycle_counts",
        f"adj={with_adj}/{total} wc={with_wc}/{total} (need 100%)",
        passed,
    )


def _na_result(rid: str, label: str, why: str) -> Result:
    return Result(rid, label, why, None, is_telemetry_deferred=True)


# ── Verdict + render ───────────────────────────────────────────


def compute_verdict(results: list[Result]) -> tuple[int, str]:
    vo = [r for r in results if r.is_v_or_o]
    m = [r for r in results if not r.is_v_or_o and not r.is_telemetry_deferred]
    vo_fails = [r for r in vo if r.passed is False]
    m_fails = [r for r in m if r.passed is False]
    if vo_fails:
        return 1, f"FAIL  (V/O FAIL: {', '.join(r.id for r in vo_fails)})"
    if m_fails:
        return 3, f"CONDITIONAL  (V/O PASS, M FAIL: {', '.join(r.id for r in m_fails)})"
    return 0, "PASS"


def _status_str(r: Result) -> str:
    if r.passed is None:
        return "N/A"
    return "PASS" if r.passed else "FAIL"


def render_report(results: list[Result], code: int, label: str, baseline: Path, target: Path, self_mode: bool) -> str:
    lines = []
    lines.append(f"baseline: {baseline}")
    lines.append(f"target  : {target}")
    if self_mode:
        lines.append("MODE    : self-sanity (baseline == target)")
    lines.append("")
    lines.append("=== Primary (V/O composite) ===")
    for r in results:
        if r.is_v_or_o:
            lines.append(f"{r.id:<3} {r.label:<34} : {r.detail:<58} {_status_str(r)}")
    lines.append("")
    lines.append("=== Mechanistic (M) ===")
    for r in results:
        if not r.is_v_or_o and not r.is_telemetry_deferred:
            lines.append(f"{r.id:<3} {r.label:<34} : {r.detail:<58} {_status_str(r)}")
    lines.append("")
    lines.append("=== Telemetry-deferred ===")
    for r in results:
        if r.is_telemetry_deferred:
            lines.append(f"{r.id:<3} {r.label:<34} : {r.detail}")

    vo = [r for r in results if r.is_v_or_o]
    m = [r for r in results if not r.is_v_or_o and not r.is_telemetry_deferred]
    tel = [r for r in results if r.is_telemetry_deferred]
    vo_p = sum(1 for r in vo if r.passed is True)
    vo_f = sum(1 for r in vo if r.passed is False)
    m_p = sum(1 for r in m if r.passed is True)
    m_f = sum(1 for r in m if r.passed is False)
    m_na = sum(1 for r in m if r.passed is None)

    lines.append("")
    lines.append("─" * 70)
    lines.append(f"Primary V/O : {vo_p} PASS, {vo_f} FAIL")
    lines.append(f"Mechanistic : {m_p} PASS, {m_f} FAIL, {m_na} N/A")
    lines.append(f"Telemetry NA: {len(tel)}")
    lines.append(f"VERDICT     : {label}  (exit={code})")
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    # Windows console UTF-8 강제 (CLAUDE.md 인코딩 규칙).
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="S3 GU Mechanistic Gate (M-Gate)")
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--target", type=Path, required=True)
    p.add_argument("--json", type=Path, help="JSON 리포트 출력 경로")
    p.add_argument("--strict", action="store_true", help="M5 strong form (Δc4>0 ∧ Δc5>0)")
    args = p.parse_args(argv)

    try:
        b = load_trial(args.baseline)
        t = load_trial(args.target)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    self_mode = args.baseline.resolve() == args.target.resolve()

    results: list[Result] = [
        eval_v1(b, t, self_mode=self_mode),
        eval_v2(b, t, self_mode=self_mode),
        eval_v3(b, t, self_mode=self_mode),
        eval_o1(b, t, self_mode=self_mode),
        eval_o2(b, t, self_mode=self_mode),
        eval_vxo(b, t, self_mode=self_mode),
        eval_m1(b, t, self_mode=self_mode),
        eval_m2(t),
        eval_m3(b, t, self_mode=self_mode),
        eval_m4(b, t, self_mode=self_mode),
        eval_m5(t, strict=args.strict),
        eval_m6(b, t, self_mode=self_mode),
        eval_m7(b, t, self_mode=self_mode),
        eval_m8(b, t, self_mode=self_mode),
        eval_m5b(t),
        eval_m9(t),
        eval_m10(t),
        eval_m11(t),
    ]

    code, label = compute_verdict(results)
    print(render_report(results, code, label, args.baseline, args.target, self_mode))

    if args.json:
        out = {
            "baseline": str(args.baseline),
            "target": str(args.target),
            "self_mode": self_mode,
            "strict": args.strict,
            "verdict": {"code": code, "label": label},
            "results": [
                {
                    "id": r.id,
                    "label": r.label,
                    "detail": r.detail,
                    "passed": r.passed,
                    "is_v_or_o": r.is_v_or_o,
                    "is_telemetry_deferred": r.is_telemetry_deferred,
                }
                for r in results
            ],
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

    return code


if __name__ == "__main__":
    sys.exit(main())
