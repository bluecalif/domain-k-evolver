"""KU saturation 진단 스크립트 (P6-A1)

stage-e-on / stage-e-off / p2-smart-remodel-trial 세 trial을 비교해
KU 포화 원인을 진단한다. API 미호출.

Usage:
    python scripts/analyze_saturation.py
    python scripts/analyze_saturation.py --trials stage-e-on stage-e-off
    python scripts/analyze_saturation.py --output dev/active/phase-si-p6-consolidation/debug-history.md

    # D2 진단 옵션 (A1-D1 gu_trace.jsonl 필요)
    python scripts/analyze_saturation.py --trace-frozen 3 --trials stage-e-on
    python scripts/analyze_saturation.py --query-patterns --trials stage-e-on
    python scripts/analyze_saturation.py --cycle-diff 5 10 --trials stage-e-on
    python scripts/analyze_saturation.py --compare-trials stage-e-on stage-e-off
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Optional

BENCH_ROOT = Path(__file__).parent.parent / "bench" / "silver" / "japan-travel"

DEFAULT_TRIALS = ["stage-e-on", "stage-e-off", "p2-smart-remodel-trial"]


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def load_trajectory(trial: str) -> list[dict]:
    path = BENCH_ROOT / trial / "trajectory" / "trajectory.csv"
    if not path.exists():
        print(f"  [WARN] trajectory not found: {path}", file=sys.stderr)
        return []
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_gap_map(trial: str, cycle: int) -> list[dict]:
    path = BENCH_ROOT / trial / "state-snapshots" / f"cycle-{cycle}-snapshot" / "gap-map.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_knowledge_units(trial: str, cycle: int) -> list[dict]:
    path = BENCH_ROOT / trial / "state-snapshots" / f"cycle-{cycle}-snapshot" / "knowledge-units.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_gu_trace(trial: str) -> list[dict]:
    """gu_trace.jsonl 로드 (A1-D1 진단 로깅 결과)."""
    path = BENCH_ROOT / trial / "telemetry" / "gu_trace.jsonl"
    if not path.exists():
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def load_cycles_jsonl(trial: str) -> list[dict]:
    """cycles.jsonl 로드 (telemetry emit 결과)."""
    path = BENCH_ROOT / trial / "telemetry" / "cycles.jsonl"
    if not path.exists():
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def available_snapshot_cycles(trial: str) -> list[int]:
    snap_dir = BENCH_ROOT / trial / "state-snapshots"
    if not snap_dir.exists():
        return []
    cycles = []
    for d in snap_dir.iterdir():
        if d.is_dir() and d.name.startswith("cycle-") and d.name.endswith("-snapshot"):
            try:
                n = int(d.name.split("-")[1])
                cycles.append(n)
            except ValueError:
                pass
    return sorted(cycles)


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def ku_growth_by_window(rows: list[dict]) -> dict:
    """c1-5, c6-10, c11-15 각 window KU 성장률 계산"""
    windows = {"c1-5": (1, 5), "c6-10": (6, 10), "c11-15": (11, 15)}
    result = {}
    cycle_map = {int(r["cycle"]): r for r in rows}
    for label, (start, end) in windows.items():
        if start in cycle_map and end in cycle_map:
            ku_start = int(cycle_map[start]["ku_active"])
            ku_end = int(cycle_map[end]["ku_active"])
            delta = ku_end - ku_start
            rate = delta / (end - start + 1)
            result[label] = {"start": ku_start, "end": ku_end, "delta": delta, "rate_per_cycle": round(rate, 2)}
        elif end in cycle_map:
            # window 시작 전 데이터로 시작점 추정
            prev = cycle_map.get(start - 1) or rows[0]
            ku_start = int(prev["ku_active"])
            ku_end = int(cycle_map[end]["ku_active"])
            delta = ku_end - ku_start
            rate = delta / (end - start + 1)
            result[label] = {"start": ku_start, "end": ku_end, "delta": delta, "rate_per_cycle": round(rate, 2)}
        else:
            result[label] = None
    return result


def gap_map_delta(trial: str, cycles: list[int]) -> list[dict]:
    """연속 cycle 간 gap_map open 수 변화 측정"""
    deltas = []
    prev_open = None
    for c in cycles:
        gm = load_gap_map(trial, c)
        if not gm:
            continue
        open_count = sum(1 for g in gm if g.get("status") == "open")
        resolved_count = sum(1 for g in gm if g.get("status") == "resolved")
        delta = (open_count - prev_open) if prev_open is not None else None
        deltas.append({
            "cycle": c,
            "open": open_count,
            "resolved": resolved_count,
            "total": len(gm),
            "delta_open": delta,
            "frozen": delta == 0 if delta is not None else False,
        })
        prev_open = open_count
    return deltas


def frozen_cycle_count(deltas: list[dict]) -> int:
    """delta_open == 0 인 cycle 수 (gap_map 완전 동결 사이클)"""
    return sum(1 for d in deltas if d.get("frozen"))


def parse_yield_trend(rows: list[dict]) -> list[dict]:
    """GU당 claims 생성 지표 — search_calls / llm_calls 비율로 추정"""
    result = []
    for r in rows:
        c = int(r["cycle"])
        llm = int(r.get("llm_calls", 0) or 0)
        search = int(r.get("search_calls", 0) or 0)
        fetch = int(r.get("fetch_calls", 0) or 0)
        gu_open = int(r.get("gu_open", 0) or 0)
        gu_resolved = int(r.get("gu_resolved", 0) or 0)
        gap_res = float(r.get("gap_resolution_rate", 0) or 0)
        result.append({
            "cycle": c,
            "gu_open": gu_open,
            "gu_resolved": gu_resolved,
            "gap_res_rate": round(gap_res, 3),
            "llm_calls": llm,
            "search_calls": search,
            "fetch_calls": fetch,
        })
    return result


def ku_category_gini(trial: str, cycles: list[int]) -> dict:
    """KU 카테고리별 분포 → Gini 계수 추이"""
    result = {}
    for c in cycles:
        kus = load_knowledge_units(trial, c)
        if not kus:
            continue
        cat_counts: dict[str, int] = {}
        for ku in kus:
            ek = ku.get("entity_key", "")
            parts = ek.split(":")
            cat = parts[1] if len(parts) >= 2 else "unknown"
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        total = sum(cat_counts.values())
        if total == 0:
            continue
        proportions = sorted(v / total for v in cat_counts.values())
        n = len(proportions)
        gini = 0.0
        if n > 1:
            cumulative = 0.0
            for i, p in enumerate(proportions):
                cumulative += p
                gini += (2 * (i + 1) - n - 1) * p
            gini = abs(gini) / n
        result[c] = {"gini": round(gini, 4), "categories": cat_counts, "total_ku": total}
    return result


def entity_dedup_rate(trial: str, cycles: list[int]) -> dict:
    """같은 entity_key 에 복수 KU가 있는 비율 (dedup 필요도 지표)"""
    result = {}
    for c in cycles:
        kus = load_knowledge_units(trial, c)
        if not kus:
            continue
        ek_counts: dict[str, int] = {}
        for ku in kus:
            ek = ku.get("entity_key", "")
            ek_counts[ek] = ek_counts.get(ek, 0) + 1
        multi = sum(1 for v in ek_counts.values() if v > 1)
        result[c] = {
            "unique_entities": len(ek_counts),
            "multi_ku_entities": multi,
            "dedup_ratio": round(multi / len(ek_counts), 3) if ek_counts else 0,
        }
    return result


# ---------------------------------------------------------------------------
# D2 진단 분석 함수
# ---------------------------------------------------------------------------

def report_trace_frozen(trial: str, min_cycles: int) -> str:
    """--trace-frozen N: N cycle 이상 open 상태인 GU 목록 + 쿼리/yield 요약."""
    lines = [f"## trace-frozen (min={min_cycles}c) — {trial}\n"]

    trace = load_gu_trace(trial)
    if not trace:
        lines.append("> [INFO] gu_trace.jsonl 없음 — gap_map 스냅샷으로 대체\n")
        return _trace_frozen_from_snapshots(trial, min_cycles, lines)

    # GU별 cycle 집합 수집
    gu_cycles: dict[str, list[int]] = {}
    gu_meta: dict[str, dict] = {}
    gu_search: dict[str, list[int]] = {}

    for row in trace:
        gu_id = row.get("gu_id", "")
        cycle = row.get("cycle", 0)
        resolved = row.get("resolved", False)

        if gu_id not in gu_cycles:
            gu_cycles[gu_id] = []
            gu_search[gu_id] = []
            gu_meta[gu_id] = {
                "entity_key": row.get("entity_key", ""),
                "field": row.get("field", ""),
                "is_wildcard": row.get("is_wildcard", False),
            }
        if not resolved:
            gu_cycles[gu_id].append(cycle)
        gu_search[gu_id].append(row.get("search_yield", 0))

    frozen_gus = {
        gu_id: cycles
        for gu_id, cycles in gu_cycles.items()
        if len(cycles) >= min_cycles
    }

    if not frozen_gus:
        lines.append(f"> {min_cycles}c 이상 open GU 없음\n")
        return "\n".join(lines)

    lines.append(f"**{min_cycles}c 이상 open GU: {len(frozen_gus)}개**\n")
    rows = []
    for gu_id, open_cycles in sorted(frozen_gus.items(), key=lambda x: -len(x[1])):
        meta = gu_meta[gu_id]
        yields = gu_search.get(gu_id, [])
        avg_yield = round(sum(yields) / len(yields), 1) if yields else 0
        rows.append([
            gu_id,
            meta["entity_key"],
            meta["field"],
            "Y" if meta["is_wildcard"] else "N",
            len(open_cycles),
            avg_yield,
        ])
    lines.append(fmt_table(
        ["gu_id", "entity_key", "field", "wildcard", "open_cycles", "avg_yield"],
        rows,
    ))
    lines.append("\n")
    return "\n".join(lines)


def _trace_frozen_from_snapshots(trial: str, min_cycles: int, lines: list) -> str:
    """gu_trace 없을 때 gap_map 스냅샷에서 long-open GU 추적."""
    snap_cycles = available_snapshot_cycles(trial)
    if not snap_cycles:
        lines.append("> [SKIP] 스냅샷 없음\n")
        return "\n".join(lines)

    # GU별 open cycle 집합 집계
    gu_open_cycles: dict[str, list[int]] = {}
    gu_meta: dict[str, dict] = {}

    for c in snap_cycles:
        gm = load_gap_map(trial, c)
        for gu in gm:
            gu_id = gu.get("gu_id", "")
            if gu.get("status") == "open":
                gu_open_cycles.setdefault(gu_id, []).append(c)
                if gu_id not in gu_meta:
                    target = gu.get("target", {})
                    ek = target.get("entity_key", "")
                    gu_meta[gu_id] = {
                        "entity_key": ek,
                        "field": target.get("field", ""),
                        "is_wildcard": "*" in ek,
                    }

    frozen_gus = {
        gid: cs for gid, cs in gu_open_cycles.items() if len(cs) >= min_cycles
    }

    if not frozen_gus:
        lines.append(f"> {min_cycles}c 이상 open GU 없음 (스냅샷 기준)\n")
        return "\n".join(lines)

    lines.append(f"**{min_cycles}c 이상 open GU (스냅샷 기준): {len(frozen_gus)}개**\n")
    rows = []
    for gu_id, open_cycles in sorted(frozen_gus.items(), key=lambda x: -len(x[1])):
        meta = gu_meta.get(gu_id, {})
        rows.append([
            gu_id,
            meta.get("entity_key", ""),
            meta.get("field", ""),
            "Y" if meta.get("is_wildcard") else "N",
            len(open_cycles),
        ])
    lines.append(fmt_table(
        ["gu_id", "entity_key", "field", "wildcard", "open_snap_count"],
        rows,
    ))
    lines.append("\n")
    return "\n".join(lines)


def report_query_patterns(trial: str) -> str:
    """--query-patterns: wildcard vs concrete search yield 분포."""
    lines = [f"## query-patterns — {trial}\n"]

    trace = load_gu_trace(trial)
    if not trace:
        lines.append("> [INFO] gu_trace.jsonl 없음 — bench 실행 후 재시도\n")
        return "\n".join(lines)

    wildcard_yields: list[int] = []
    concrete_yields: list[int] = []
    wildcard_zero = 0
    concrete_zero = 0

    per_cycle: dict[int, dict] = {}
    for row in trace:
        cycle = row.get("cycle", 0)
        is_wc = row.get("is_wildcard", False)
        sy = row.get("search_yield", 0)
        if is_wc:
            wildcard_yields.append(sy)
            if sy == 0:
                wildcard_zero += 1
        else:
            concrete_yields.append(sy)
            if sy == 0:
                concrete_zero += 1

        entry = per_cycle.setdefault(cycle, {
            "wc_count": 0, "wc_yield": 0, "cc_count": 0, "cc_yield": 0,
        })
        if is_wc:
            entry["wc_count"] += 1
            entry["wc_yield"] += sy
        else:
            entry["cc_count"] += 1
            entry["cc_yield"] += sy

    def avg(lst: list) -> float:
        return round(sum(lst) / len(lst), 2) if lst else 0.0

    lines.append("### 전체 요약\n")
    summary_rows = [
        ["wildcard", len(wildcard_yields), avg(wildcard_yields),
         f"{wildcard_zero}/{len(wildcard_yields)}" if wildcard_yields else "-"],
        ["concrete", len(concrete_yields), avg(concrete_yields),
         f"{concrete_zero}/{len(concrete_yields)}" if concrete_yields else "-"],
    ]
    lines.append(fmt_table(["type", "count", "avg_yield", "zero_yield"], summary_rows))
    lines.append("\n")

    lines.append("\n### cycle별 wildcard / concrete yield\n")
    cycle_rows = []
    for c in sorted(per_cycle):
        e = per_cycle[c]
        wc_avg = round(e["wc_yield"] / e["wc_count"], 1) if e["wc_count"] else 0
        cc_avg = round(e["cc_yield"] / e["cc_count"], 1) if e["cc_count"] else 0
        cycle_rows.append([c, e["wc_count"], wc_avg, e["cc_count"], cc_avg])
    lines.append(fmt_table(
        ["cycle", "wc_targets", "wc_avg_yield", "cc_targets", "cc_avg_yield"],
        cycle_rows,
    ))
    lines.append("\n")
    return "\n".join(lines)


def report_cycle_diff(trial: str, c1: int, c2: int) -> str:
    """--cycle-diff C1 C2: 두 cycle 간 gap_map 변화 상세."""
    lines = [f"## cycle-diff ({c1} → {c2}) — {trial}\n"]

    gm1 = load_gap_map(trial, c1)
    gm2 = load_gap_map(trial, c2)
    if not gm1 and not gm2:
        lines.append(f"> [SKIP] cycle {c1}, {c2} 스냅샷 없음\n")
        return "\n".join(lines)
    if not gm1:
        lines.append(f"> [WARN] cycle {c1} 스냅샷 없음 — cycle {c2}만 표시\n")
    if not gm2:
        lines.append(f"> [WARN] cycle {c2} 스냅샷 없음 — cycle {c1}만 표시\n")

    id_to_c1 = {g.get("gu_id"): g for g in gm1}
    id_to_c2 = {g.get("gu_id"): g for g in gm2}
    all_ids = sorted(set(id_to_c1) | set(id_to_c2))

    changes = []
    for gu_id in all_ids:
        g1 = id_to_c1.get(gu_id)
        g2 = id_to_c2.get(gu_id)
        s1 = g1.get("status", "-") if g1 else "new"
        s2 = g2.get("status", "-") if g2 else "gone"
        if s1 == s2:
            continue  # 변화 없는 GU 생략
        g = g1 or g2
        target = g.get("target", {})
        ek = target.get("entity_key", "")
        changes.append([gu_id, ek, target.get("field", ""), s1, s2])

    summary_c1 = {
        "open": sum(1 for g in gm1 if g.get("status") == "open"),
        "resolved": sum(1 for g in gm1 if g.get("status") == "resolved"),
        "total": len(gm1),
    }
    summary_c2 = {
        "open": sum(1 for g in gm2 if g.get("status") == "open"),
        "resolved": sum(1 for g in gm2 if g.get("status") == "resolved"),
        "total": len(gm2),
    }

    lines.append("### 요약\n")
    s_rows = [
        [f"c{c1}", summary_c1["open"], summary_c1["resolved"], summary_c1["total"]],
        [f"c{c2}", summary_c2["open"], summary_c2["resolved"], summary_c2["total"]],
        ["delta", summary_c2["open"] - summary_c1["open"],
         summary_c2["resolved"] - summary_c1["resolved"],
         summary_c2["total"] - summary_c1["total"]],
    ]
    lines.append(fmt_table(["cycle", "open", "resolved", "total"], s_rows))
    lines.append("\n")

    if changes:
        lines.append(f"\n### 상태 변화 GU ({len(changes)}개)\n")
        lines.append(fmt_table(["gu_id", "entity_key", "field", f"c{c1}", f"c{c2}"], changes))
    else:
        lines.append(f"\n> 상태 변화 없음 (c{c1} → c{c2})\n")
    lines.append("\n")
    return "\n".join(lines)


def report_compare_trials(trial_a: str, trial_b: str) -> str:
    """--compare-trials A B: 두 trial의 frozen GU 집합 + open GU entity_key 비교."""
    lines = [f"## compare-trials: {trial_a} vs {trial_b}\n"]

    def get_last_open_gus(trial: str) -> dict[str, dict]:
        snaps = available_snapshot_cycles(trial)
        if not snaps:
            return {}
        gm = load_gap_map(trial, snaps[-1])
        return {
            g.get("gu_id", ""): g for g in gm if g.get("status") == "open"
        }

    open_a = get_last_open_gus(trial_a)
    open_b = get_last_open_gus(trial_b)

    def ek_set(gus: dict) -> set:
        result = set()
        for g in gus.values():
            t = g.get("target", {})
            result.add(f"{t.get('entity_key', '')}:{t.get('field', '')}")
        return result

    eks_a = ek_set(open_a)
    eks_b = ek_set(open_b)
    only_a = sorted(eks_a - eks_b)
    only_b = sorted(eks_b - eks_a)
    common = sorted(eks_a & eks_b)

    lines.append(f"**{trial_a}**: open={len(open_a)} GU | **{trial_b}**: open={len(open_b)} GU\n")
    lines.append(f"공통 open entity:field = {len(common)}, {trial_a}만 = {len(only_a)}, {trial_b}만 = {len(only_b)}\n")

    def fmt_list(items: list, max_n: int = 20) -> str:
        shown = items[:max_n]
        rest = len(items) - max_n
        out = "\n".join(f"  - {x}" for x in shown)
        if rest > 0:
            out += f"\n  - ... 외 {rest}개"
        return out

    if only_a:
        lines.append(f"\n### {trial_a}에만 존재 ({len(only_a)}개)\n")
        lines.append(fmt_list(only_a))
        lines.append("\n")
    if only_b:
        lines.append(f"\n### {trial_b}에만 존재 ({len(only_b)}개)\n")
        lines.append(fmt_list(only_b))
        lines.append("\n")
    if common:
        lines.append(f"\n### 공통 open ({len(common)}개)\n")
        lines.append(fmt_list(common))
        lines.append("\n")

    # gu_trace 기반 wildcard 비율 비교
    for trial in (trial_a, trial_b):
        trace = load_gu_trace(trial)
        if not trace:
            continue
        wc = sum(1 for r in trace if r.get("is_wildcard") and not r.get("resolved"))
        cc = sum(1 for r in trace if not r.get("is_wildcard") and not r.get("resolved"))
        wc_yield_zero = sum(
            1 for r in trace if r.get("is_wildcard") and r.get("search_yield", 0) == 0
        )
        lines.append(f"\n**{trial} frozen GU 구성** (gu_trace 기준): "
                     f"wildcard={wc}, concrete={cc}, wildcard_zero_yield={wc_yield_zero}\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def fmt_table(headers: list[str], rows: list[list]) -> str:
    widths = [max(len(str(r[i])) for r in ([headers] + rows)) for i in range(len(headers))]
    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    header_row = "| " + " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    lines = [header_row, sep]
    for r in rows:
        lines.append("| " + " | ".join(str(v).ljust(widths[i]) for i, v in enumerate(r)) + " |")
    return "\n".join(lines)


def build_report(trials: list[str]) -> str:
    sections = []
    sections.append("# KU Saturation 진단 리포트 (P6-A1)\n")
    sections.append(f"> 분석 대상: {', '.join(trials)}\n")

    all_data: dict[str, dict] = {}

    for trial in trials:
        rows = load_trajectory(trial)
        if not rows:
            sections.append(f"\n## {trial}\n\n> [SKIP] trajectory 없음\n")
            continue

        snap_cycles = available_snapshot_cycles(trial)
        gm_deltas = gap_map_delta(trial, snap_cycles)
        frozen = frozen_cycle_count(gm_deltas)
        growth = ku_growth_by_window(rows)
        parse_yield = parse_yield_trend(rows)
        gini_data = ku_category_gini(trial, snap_cycles)
        dedup_data = entity_dedup_rate(trial, snap_cycles)

        all_data[trial] = {
            "rows": rows, "gm_deltas": gm_deltas, "frozen": frozen,
            "growth": growth, "parse_yield": parse_yield,
            "gini_data": gini_data, "dedup_data": dedup_data,
        }

        sections.append(f"\n## {trial}\n")

        # 1. KU 성장률
        sections.append("### 1. KU 성장률 (window별)\n")
        g_rows = []
        for w, v in growth.items():
            if v:
                g_rows.append([w, v["start"], v["end"], v["delta"], v["rate_per_cycle"]])
            else:
                g_rows.append([w, "-", "-", "-", "-"])
        sections.append(fmt_table(["window", "ku_start", "ku_end", "delta", "rate/cycle"], g_rows))
        sections.append("\n")

        # 2. gap_map delta
        sections.append(f"\n### 2. gap_map 동결 분석\n")
        sections.append(f"**동결 사이클 수**: {frozen} / {len(gm_deltas)}\n")
        if gm_deltas:
            gd_rows = [[d["cycle"], d["open"], d["resolved"], d["delta_open"] if d["delta_open"] is not None else "-", "🔴 FROZEN" if d["frozen"] else ""] for d in gm_deltas]
            sections.append(fmt_table(["cycle", "open", "resolved", "delta_open", "note"], gd_rows))
        sections.append("\n")

        # 3. parse_yield (gap_res + LLM)
        sections.append("\n### 3. GU 해소율 + LLM 호출 추이\n")
        py_rows = [[d["cycle"], d["gu_open"], d["gu_resolved"], d["gap_res_rate"], d["llm_calls"], d["search_calls"]] for d in parse_yield]
        sections.append(fmt_table(["cycle", "gu_open", "gu_resolved", "gap_res", "llm_calls", "search_calls"], py_rows))
        sections.append("\n")

        # 4. Gini 추이
        sections.append("\n### 4. KU Gini 추이\n")
        if gini_data:
            gi_rows = [[c, v["gini"], v["total_ku"], len(v["categories"])] for c, v in sorted(gini_data.items())]
            sections.append(fmt_table(["cycle", "gini", "total_ku", "num_categories"], gi_rows))
        else:
            sections.append("> [SKIP] snapshot 없음\n")
        sections.append("\n")

        # 5. entity dedup
        sections.append("\n### 5. Entity Dedup 비율\n")
        if dedup_data:
            dd_rows = [[c, v["unique_entities"], v["multi_ku_entities"], v["dedup_ratio"]] for c, v in sorted(dedup_data.items())]
            sections.append(fmt_table(["cycle", "unique_entities", "multi_ku", "dedup_ratio"], dd_rows))
        else:
            sections.append("> [SKIP] snapshot 없음\n")
        sections.append("\n")

    # Cross-trial summary
    if len(all_data) >= 2:
        sections.append("\n---\n\n## 비교 요약\n")
        summary_rows = []
        for trial, d in all_data.items():
            rows = d["rows"]
            last = rows[-1] if rows else {}
            growth = d["growth"]
            c11_15 = growth.get("c11-15")
            rate = c11_15["rate_per_cycle"] if c11_15 else "-"
            frozen = d["frozen"]
            last_gm = d["gm_deltas"][-1] if d["gm_deltas"] else {}
            summary_rows.append([
                trial,
                last.get("ku_active", "-"),
                rate,
                frozen,
                last_gm.get("open", "-"),
                last_gm.get("resolved", "-"),
            ])
        sections.append(fmt_table(
            ["trial", "final_ku_active", "c11-15_rate/cyc", "frozen_cycles", "final_open", "final_resolved"],
            summary_rows
        ))
        sections.append("\n")

        # Root cause hints
        sections.append("\n## 진단 결론\n")
        for trial, d in all_data.items():
            frozen = d["frozen"]
            growth = d["growth"]
            c11_15 = growth.get("c11-15")
            rate = c11_15["rate_per_cycle"] if c11_15 else None
            hints = []
            if frozen and frozen >= 2:
                hints.append(f"gap_map 완전 동결 {frozen}사이클 — core loop 마비 의심")
            if rate is not None and rate < 1.0:
                hints.append(f"c11-15 KU 성장률 {rate}/cyc — 포화 진입")
            if not hints:
                hints.append("포화 징후 없음")
            sections.append(f"- **{trial}**: {'; '.join(hints)}\n")

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="KU saturation 진단 (P6-A1)")
    parser.add_argument("--trials", nargs="+", default=DEFAULT_TRIALS, help="분석할 trial 이름")
    parser.add_argument("--output", default=None, help="결과를 기록할 파일 경로 (없으면 stdout만)")

    # D2 진단 옵션
    parser.add_argument("--trace-frozen", type=int, metavar="N",
                        help="N cycle 이상 open 상태인 GU 목록 + yield 요약 (--trials로 trial 지정)")
    parser.add_argument("--query-patterns", action="store_true",
                        help="wildcard vs concrete search yield 분포 (--trials로 trial 지정)")
    parser.add_argument("--cycle-diff", nargs=2, type=int, metavar=("C1", "C2"),
                        help="두 cycle 간 gap_map 변화 상세 (--trials로 trial 지정)")
    parser.add_argument("--compare-trials", nargs=2, metavar=("A", "B"),
                        help="두 trial의 frozen GU 집합 비교 (--trials 무시)")

    args = parser.parse_args()

    # D2 모드: 특정 옵션이 지정된 경우 해당 분석만 수행
    d2_sections: list[str] = []

    if args.compare_trials:
        trial_a, trial_b = args.compare_trials
        d2_sections.append(report_compare_trials(trial_a, trial_b))

    if args.trace_frozen is not None:
        for trial in args.trials:
            d2_sections.append(report_trace_frozen(trial, args.trace_frozen))

    if args.query_patterns:
        for trial in args.trials:
            d2_sections.append(report_query_patterns(trial))

    if args.cycle_diff:
        c1, c2 = args.cycle_diff
        for trial in args.trials:
            d2_sections.append(report_cycle_diff(trial, c1, c2))

    if d2_sections:
        report = "\n".join(d2_sections)
    else:
        report = build_report(args.trials)

    print(report)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        separator = "\n\n---\n<!-- analyze_saturation.py output -->\n\n"
        if out_path.exists():
            existing = out_path.read_text(encoding="utf-8")
            out_path.write_text(existing + separator + report, encoding="utf-8")
            print(f"\n[+] appended to {out_path}", file=sys.stderr)
        else:
            out_path.write_text(report, encoding="utf-8")
            print(f"\n[+] written to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
