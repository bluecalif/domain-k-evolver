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
)

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _extract_chart_series(cycles: list[dict]) -> dict:
    return {
        "cycle_nums": [c["cycle"] for c in cycles],
        "novelty": [c["metrics"]["novelty"] for c in cycles],
        "conflict_rate": [c["metrics"]["conflict_rate"] for c in cycles],
        "evidence_rate": [c["metrics"]["evidence_rate"] for c in cycles],
        "collect_failure": [c["metrics"]["collect_failure_rate"] for c in cycles],
        "gaps_open": [c["gaps"]["open"] for c in cycles],
        "gaps_resolved": [c["gaps"]["resolved"] for c in cycles],
        "search_calls": [c["metrics"]["search_calls"] for c in cycles],
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


def create_app(trial_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="Evolver Dashboard", docs_url=None, redoc_url=None)
    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

    _root = trial_root

    def _trial_root() -> Path | None:
        return _root

    def _trial_id() -> str:
        return _root.name if _root else "—"

    @app.get("/", response_class=HTMLResponse)
    async def overview(request: Request):
        root = _trial_root()
        cycles = load_cycles(root) if root else []
        return templates.TemplateResponse(request, "overview.html", {
            "cycles": cycles, "trial_id": _trial_id(),
        })

    @app.get("/timeline", response_class=HTMLResponse)
    async def timeline(request: Request):
        root = _trial_root()
        cycles = load_cycles(root) if root else []
        series = _extract_chart_series(cycles)
        return templates.TemplateResponse(request, "timeline.html", {
            "cycles": cycles, "trial_id": _trial_id(), **series,
        })

    @app.get("/coverage", response_class=HTMLResponse)
    async def coverage(request: Request):
        root = _trial_root()
        cycles = load_cycles(root) if root else []
        series = _extract_chart_series(cycles)
        return templates.TemplateResponse(request, "coverage.html", {
            "cycles": cycles, "trial_id": _trial_id(),
            "cycle_nums": series["cycle_nums"],
            "gaps_open": series["gaps_open"],
            "gaps_resolved": series["gaps_resolved"],
        })

    @app.get("/sources", response_class=HTMLResponse)
    async def sources(request: Request):
        root = _trial_root()
        cycles = load_cycles(root) if root else []
        series = _extract_chart_series(cycles)
        return templates.TemplateResponse(request, "sources.html", {
            "cycles": cycles, "trial_id": _trial_id(),
            "cycle_nums": series["cycle_nums"],
            "collect_failure": series["collect_failure"],
            "search_calls": series["search_calls"],
        })

    @app.get("/conflicts", response_class=HTMLResponse)
    async def conflicts(request: Request):
        root = _trial_root()
        ledger = load_conflict_ledger(root) if root else []
        return templates.TemplateResponse(request, "conflicts.html", {
            "ledger": ledger, "trial_id": _trial_id(),
        })

    @app.get("/hitl", response_class=HTMLResponse)
    async def hitl(request: Request):
        root = _trial_root()
        cycles = load_cycles(root) if root else []
        last = cycles[-1] if cycles else {}
        hitl_q = last.get("hitl_queue", {"seed": 0, "remodel": 0, "exception": 0})
        dispute_size = last.get("dispute_queue_size", 0)
        exceptions = _extract_exceptions(cycles)
        return templates.TemplateResponse(request, "hitl.html", {
            "hitl": hitl_q, "dispute_size": dispute_size,
            "exceptions": exceptions, "trial_id": _trial_id(),
        })

    @app.get("/remodel", response_class=HTMLResponse)
    async def remodel(request: Request):
        root = _trial_root()
        report = load_remodel_report(root) if root else None
        return templates.TemplateResponse(request, "remodel.html", {
            "report": report, "trial_id": _trial_id(),
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
