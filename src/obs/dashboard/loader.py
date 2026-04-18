"""실제 trial artifact를 읽는 로더. stub/mock 절대 금지 (P5-X3)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


_METRIC_KEYS = (
    "evidence_rate", "multi_evidence_rate", "conflict_rate", "avg_confidence",
    "gap_resolution_rate", "staleness_risk", "collect_failure_rate",
    "llm_calls", "llm_tokens", "search_calls", "fetch_calls",
)


def _from_trajectory(rec: dict, trial_id: str) -> dict:
    """Bronze trajectory record → Silver cycles.jsonl snapshot (호환 어댑터).

    P5 이전 trial은 trajectory.json 만 보유. 메모리 변환만 수행 (파일 생성 없음).
    누락 필드는 안전한 기본값으로 채워 dashboard 템플릿이 깨지지 않게 한다.
    """
    metrics = {k: rec.get(k, 0) for k in _METRIC_KEYS}
    metrics["novelty"] = 0
    metrics["external_novelty"] = 0
    metrics["wall_clock_s"] = 0
    return {
        "trial_id": trial_id,
        "phase": "legacy",
        "cycle": rec.get("cycle", 0),
        "mode": rec.get("mode", "normal"),
        "timestamp": None,
        "metrics": metrics,
        "gaps": {
            "open": rec.get("gu_open", 0),
            "resolved": rec.get("gu_resolved", 0),
            "plateau": False,
            "probe_history_count": 0,
            "pivot_history_count": 0,
        },
        "failures": [],
        "audit_summary": {"has_critical": False, "findings_count": 0, "last_audit_cycle": -1},
        "hitl_queue": {"seed": 0, "remodel": 0, "exception": 0},
        "dispute_queue_size": 0,
    }


def load_cycles(trial_root: Path) -> list[dict]:
    """bench/silver/{trial}/telemetry/cycles.jsonl → list of snapshots.

    cycles.jsonl이 없으면 trajectory.json (Bronze 포맷) 을 자동 변환해 반환.
    """
    path = trial_root / "telemetry" / "cycles.jsonl"
    if path.exists():
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        result = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    result.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning("cycles.jsonl 파싱 실패 (line 무시): %s", e)
        return result
    traj = load_trajectory(trial_root)
    if traj:
        return [_from_trajectory(r, trial_root.name) for r in traj]
    return []


def load_conflict_ledger(trial_root: Path) -> list[dict]:
    """state/conflict-ledger.json → list of ledger entries.

    legacy/silver 양쪽 파일명(`conflict-ledger.json` 하이픈, `conflict_ledger.json`
    언더스코어)을 모두 시도. P1-B1 schema는 하이픈을 채택했으나 P5 dashboard 초기
    버전이 언더스코어로 잘못 찾아 12/13 trial에서 ledger가 빈 화면이었음.
    """
    state_dir = trial_root / "state"
    for name in ("conflict-ledger.json", "conflict_ledger.json"):
        path = state_dir / name
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            return data.get("entries", [])
    return []


def load_remodel_report(trial_root: Path) -> dict | None:
    """state/phase_*/remodel_report.json 중 가장 최신 파일 반환."""
    state_dir = trial_root / "state"
    if not state_dir.exists():
        return None
    candidates = sorted(state_dir.glob("phase_*/remodel_report.json"), reverse=True)
    if not candidates:
        return None
    try:
        return json.loads(candidates[0].read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("remodel_report 로드 실패: %s", e)
        return None


def derive_remodel_events(cycles: list[dict]) -> dict:
    """cycles 에서 remodel 발동 이력 + 효과 (KU/res_rate delta) 추출.

    persisted remodel_report.json 파일이 없는 trial 을 위해 telemetry/trajectory
    데이터에서 mode='jump' 또는 hitl_queue.remodel==1 이벤트를 events 로 매핑.
    """
    events: list[dict] = []
    prev = None
    for c in cycles:
        mode = c.get("mode", "normal")
        hitl_remodel = c.get("hitl_queue", {}).get("remodel", 0)
        if mode == "jump" or hitl_remodel:
            ku = c.get("metrics", {}).get("evidence_rate", 0)  # placeholder
            gaps_resolved = c.get("gaps", {}).get("resolved", 0)
            gaps_open = c.get("gaps", {}).get("open", 0)
            ku_total = gaps_resolved + gaps_open  # rough proxy when ku not in cycles
            event = {
                "cycle": c.get("cycle"),
                "mode": mode,
                "hitl_remodel": bool(hitl_remodel),
                "gap_resolution_rate": c.get("metrics", {}).get("gap_resolution_rate", 0),
                "gaps_open": gaps_open,
                "gaps_resolved": gaps_resolved,
            }
            if prev is not None:
                event["delta_gap_resolved"] = gaps_resolved - prev.get("gaps", {}).get("resolved", 0)
                event["delta_res_rate"] = (
                    c.get("metrics", {}).get("gap_resolution_rate", 0)
                    - prev.get("metrics", {}).get("gap_resolution_rate", 0)
                )
            events.append(event)
        prev = c
    return {
        "total_events": len(events),
        "first_cycle": events[0]["cycle"] if events else None,
        "last_cycle": events[-1]["cycle"] if events else None,
        "events": events,
    }


def load_trajectory(trial_root: Path) -> list[dict]:
    """trajectory/trajectory.json → list of cycle records."""
    path = trial_root / "trajectory" / "trajectory.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("cycles", [])


def _gini(values: list[int]) -> float:
    """Gini 계수 (0=완전 균등, 1=완전 편중). category 분포 다양성 지표."""
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    total = sum(s)
    if total == 0:
        return 0.0
    cum = sum((i + 1) * v for i, v in enumerate(s))
    return (2 * cum) / (n * total) - (n + 1) / n


def load_ku_progression(trial_root: Path) -> list[dict]:
    """state-snapshots/cycle-N-snapshot/knowledge-units.json → cycle별 KU/카테고리/Gini.

    P4 variability 지표(category Gini)는 cycles.jsonl/trajectory.json에 없으므로
    KU snapshot 에서 사후 계산. snapshot 없으면 빈 리스트.
    """
    snap_dir = trial_root / "state-snapshots"
    if not snap_dir.exists():
        return []
    snaps = sorted(
        snap_dir.glob("cycle-*-snapshot/knowledge-units.json"),
        key=lambda p: int(p.parent.name.split("-")[1]),
    )
    out = []
    for snap in snaps:
        try:
            cycle = int(snap.parent.name.split("-")[1])
            kus = json.loads(snap.read_text(encoding="utf-8"))
            if isinstance(kus, dict):
                kus = kus.get("knowledge_units", kus.get("kus", []))
            from collections import Counter
            cats = Counter()
            for k in kus:
                ek = k.get("entity_key", "")
                cats[ek.split(":")[1] if ":" in ek else "unknown"] += 1
            out.append({
                "cycle": cycle,
                "ku_total": len(kus),
                "category_count": len(cats),
                "category_gini": round(_gini(list(cats.values())), 4),
            })
        except Exception as e:
            logger.warning("KU snapshot 분석 실패 %s: %s", snap, e)
    return out
