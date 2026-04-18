"""KU saturation 진단 스크립트 (P6-A1)

stage-e-on / stage-e-off / p2-smart-remodel-trial 세 trial을 비교해
KU 포화 원인을 진단한다. API 미호출.

Usage:
    python scripts/analyze_saturation.py
    python scripts/analyze_saturation.py --trials stage-e-on stage-e-off
    python scripts/analyze_saturation.py --output dev/active/phase-si-p6-consolidation/debug-history.md
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
    parser = argparse.ArgumentParser(description="KU saturation 진단 (P6-A1)")
    parser.add_argument("--trials", nargs="+", default=DEFAULT_TRIALS, help="분석할 trial 이름")
    parser.add_argument("--output", default=None, help="결과를 기록할 파일 경로 (없으면 stdout만)")
    args = parser.parse_args()

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
