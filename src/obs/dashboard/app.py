"""FastAPI 로컬 운영자 대시보드.

실행: run_readiness.py --serve-dashboard --bench-root <trial_root> (D-152)
또는 직접: uvicorn src.obs.dashboard.app:create_app --factory
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from src.obs.dashboard.loader import (
    load_cycles,
    load_conflict_ledger,
    load_remodel_report,
    load_ku_progression,
    derive_remodel_events,
)

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _extract_chart_series(cycles: list[dict]) -> dict:
    return {
        "cycle_nums": [c["cycle"] for c in cycles],
        "novelty": [c["metrics"]["novelty"] for c in cycles],
        "external_novelty": [c["metrics"].get("external_novelty", 0) for c in cycles],
        "conflict_rate": [c["metrics"]["conflict_rate"] for c in cycles],
        "evidence_rate": [c["metrics"]["evidence_rate"] for c in cycles],
        "collect_failure": [c["metrics"]["collect_failure_rate"] for c in cycles],
        "gap_resolution": [c["metrics"]["gap_resolution_rate"] for c in cycles],
        "gaps_open": [c["gaps"]["open"] for c in cycles],
        "gaps_resolved": [c["gaps"]["resolved"] for c in cycles],
        "search_calls": [c["metrics"]["search_calls"] for c in cycles],
    }


def _ku_growth_summary(progression: list[dict]) -> dict:
    """최근 5cycle 평균 성장률 + 카테고리 다양성 요약."""
    if not progression:
        return {"current_ku": 0, "current_cats": 0, "current_gini": 0,
                "growth_5c": 0, "first_cycle": 0, "last_cycle": 0}
    last = progression[-1]
    window = progression[-min(5, len(progression)):]
    growth = (last["ku_total"] - window[0]["ku_total"]) / max(1, len(window) - 1)
    return {
        "current_ku": last["ku_total"],
        "current_cats": last["category_count"],
        "current_gini": last["category_gini"],
        "growth_5c": round(growth, 2),
        "first_cycle": progression[0]["cycle"],
        "last_cycle": last["cycle"],
    }


def _extract_exceptions(cycles: list[dict]) -> list[dict]:
    """auto-pause 기준(metrics_guard 임계치) 위반 cycle을 exception으로 표시."""
    exceptions = []
    for c in cycles:
        m = c["metrics"]
        reasons = []
        if m["conflict_rate"] > 0.25:
            reasons.append(f"conflict_rate {m['conflict_rate']:.3f} > 0.25")
        if m["evidence_rate"] < 0.55:
            reasons.append(f"evidence_rate {m['evidence_rate']:.2f} < 0.55")
        if m["collect_failure_rate"] > 0.50:
            reasons.append(f"collect_failure_rate {m['collect_failure_rate']:.2f} > 0.50")
        if m["avg_confidence"] < 0.60:
            reasons.append(f"avg_confidence {m['avg_confidence']:.2f} < 0.60")
        if reasons:
            exceptions.append({"cycle": c["cycle"], "reason": "; ".join(reasons)})
    return exceptions


def _discover_trials(bench_root: Path | None) -> list[str]:
    if not bench_root or not bench_root.exists():
        return []
    return sorted(p.name for p in bench_root.iterdir() if p.is_dir())


def create_app(trial_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="Evolver Dashboard", docs_url=None, redoc_url=None)
    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

    _default_root = trial_root
    _bench_root = trial_root.parent if trial_root else None

    def _resolve(trial: str | None) -> Path | None:
        if trial and _bench_root:
            candidate = _bench_root / trial
            return candidate if candidate.is_dir() else _default_root
        return _default_root

    def _ctx(trial: str | None) -> dict:
        root = _resolve(trial)
        return {
            "trial_id": root.name if root else "—",
            "trials": _discover_trials(_bench_root),
            "root": root,
        }

    @app.get("/", response_class=HTMLResponse)
    async def overview(request: Request, trial: str | None = None):
        c = _ctx(trial)
        cycles = load_cycles(c["root"]) if c["root"] else []
        progression = load_ku_progression(c["root"]) if c["root"] else []
        ku_summary = _ku_growth_summary(progression)
        return templates.TemplateResponse(request, "overview.html", {
            "cycles": cycles, "trial_id": c["trial_id"], "trials": c["trials"],
            "ku_summary": ku_summary,
        })

    @app.get("/timeline", response_class=HTMLResponse)
    async def timeline(request: Request, trial: str | None = None):
        c = _ctx(trial)
        cycles = load_cycles(c["root"]) if c["root"] else []
        progression = load_ku_progression(c["root"]) if c["root"] else []
        series = _extract_chart_series(cycles)
        # KU progression aligned to cycle index
        prog_map = {p["cycle"]: p for p in progression}
        series["ku_total"] = [prog_map.get(cn, {}).get("ku_total", 0) for cn in series["cycle_nums"]]
        series["category_gini"] = [prog_map.get(cn, {}).get("category_gini", 0) for cn in series["cycle_nums"]]
        series["category_count"] = [prog_map.get(cn, {}).get("category_count", 0) for cn in series["cycle_nums"]]
        return templates.TemplateResponse(request, "timeline.html", {
            "cycles": cycles, "trial_id": c["trial_id"], "trials": c["trials"], **series,
        })

    @app.get("/coverage", response_class=HTMLResponse)
    async def coverage(request: Request, trial: str | None = None):
        c = _ctx(trial)
        cycles = load_cycles(c["root"]) if c["root"] else []
        series = _extract_chart_series(cycles)
        return templates.TemplateResponse(request, "coverage.html", {
            "cycles": cycles, "trial_id": c["trial_id"], "trials": c["trials"],
            "cycle_nums": series["cycle_nums"],
            "gaps_open": series["gaps_open"],
            "gaps_resolved": series["gaps_resolved"],
        })

    @app.get("/sources", response_class=HTMLResponse)
    async def sources(request: Request, trial: str | None = None):
        c = _ctx(trial)
        cycles = load_cycles(c["root"]) if c["root"] else []
        series = _extract_chart_series(cycles)
        return templates.TemplateResponse(request, "sources.html", {
            "cycles": cycles, "trial_id": c["trial_id"], "trials": c["trials"],
            "cycle_nums": series["cycle_nums"],
            "collect_failure": series["collect_failure"],
            "search_calls": series["search_calls"],
        })

    @app.get("/conflicts", response_class=HTMLResponse)
    async def conflicts(request: Request, trial: str | None = None):
        c = _ctx(trial)
        ledger = load_conflict_ledger(c["root"]) if c["root"] else []
        return templates.TemplateResponse(request, "conflicts.html", {
            "ledger": ledger, "trial_id": c["trial_id"], "trials": c["trials"],
        })

    @app.get("/hitl", response_class=HTMLResponse)
    async def hitl(request: Request, trial: str | None = None):
        c = _ctx(trial)
        cycles = load_cycles(c["root"]) if c["root"] else []
        last = cycles[-1] if cycles else {}
        hitl_q = last.get("hitl_queue", {"seed": 0, "remodel": 0, "exception": 0})
        dispute_size = last.get("dispute_queue_size", 0)
        exceptions = _extract_exceptions(cycles)
        return templates.TemplateResponse(request, "hitl.html", {
            "hitl": hitl_q, "dispute_size": dispute_size,
            "exceptions": exceptions, "trial_id": c["trial_id"], "trials": c["trials"],
        })

    @app.get("/remodel", response_class=HTMLResponse)
    async def remodel(request: Request, trial: str | None = None):
        c = _ctx(trial)
        report = load_remodel_report(c["root"]) if c["root"] else None
        cycles = load_cycles(c["root"]) if c["root"] else []
        events = derive_remodel_events(cycles)
        return templates.TemplateResponse(request, "remodel.html", {
            "report": report, "events": events,
            "trial_id": c["trial_id"], "trials": c["trials"],
        })

    return app


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evolver Dashboard")
    p.add_argument("--trial-root", type=Path, help="bench/silver/{domain}/{trial_id} 경로")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    return p.parse_args()


if __name__ == "__main__":
    import uvicorn
    args = _parse_args()
    trial_root = args.trial_root.resolve() if args.trial_root else None
    app = create_app(trial_root=trial_root)
    uvicorn.run(app, host=args.host, port=args.port)
