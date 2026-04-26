"""Metrics Logger — 사이클별 지표 기록.

사이클마다 Metrics + KU/GU 카운트를 누적 기록하고
JSON/CSV로 출력.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class MetricsLogger:
    """사이클별 Metrics 기록기."""

    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def log(
        self,
        cycle: int,
        state: dict,
        *,
        llm_calls: int = 0,
        llm_tokens: int = 0,
        search_calls: int = 0,
        fetch_calls: int = 0,
    ) -> dict[str, Any]:
        """사이클 종료 시 Metrics를 기록.

        Args:
            cycle: 현재 사이클 번호.
            state: EvolverState dict.
            llm_calls: LLM API 호출 횟수.
            llm_tokens: LLM 총 토큰 수.
            search_calls: 검색 API 호출 횟수.
            fetch_calls: URL Fetch 호출 횟수.

        Returns:
            기록된 엔트리.
        """
        metrics = state.get("metrics", {})
        rates = metrics.get("rates", {})
        kus = state.get("knowledge_units", [])
        gus = state.get("gap_map", [])

        entry = {
            "cycle": cycle,
            "ku_total": len(kus),
            "ku_active": sum(1 for k in kus if k.get("status") == "active"),
            "ku_disputed": sum(1 for k in kus if k.get("status") == "disputed"),
            "gu_total": len(gus),
            "gu_open": sum(1 for g in gus if g.get("status") == "open"),
            "gu_resolved": sum(1 for g in gus if g.get("status") == "resolved"),
            "evidence_rate": rates.get("evidence_rate", 0.0),
            "multi_evidence_rate": rates.get("multi_evidence_rate", 0.0),
            "conflict_rate": rates.get("conflict_rate", 0.0),
            "avg_confidence": rates.get("avg_confidence", 0.0),
            "gap_resolution_rate": rates.get("gap_resolution_rate", 0.0),
            "staleness_risk": rates.get("staleness_risk", 0),
            "mode": (state.get("current_mode") or {}).get("mode", "normal"),
            "collect_failure_rate": state.get("collect_failure_rate", 0.0),
            "llm_calls": llm_calls,
            "llm_tokens": llm_tokens,
            "search_calls": search_calls,
            "fetch_calls": fetch_calls,
            "adj_gen_count": state.get("_diag_adjacent_gap_count") or 0,
            "wildcard_gen_count": state.get("_diag_wildcard_gen_count") or 0,
            "cap_hit_count": state.get("_diag_cap_hit_count", 0) or 0,
        }
        self.entries.append(entry)
        return entry

    def save_json(self, path: str | Path) -> None:
        """JSON 파일로 저장."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.entries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def save_csv(self, path: str | Path) -> None:
        """CSV 파일로 저장."""
        if not self.entries:
            return
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(self.entries[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.entries)

    def summary(self) -> dict[str, Any]:
        """전체 실행 요약 통계."""
        if not self.entries:
            return {}
        first = self.entries[0]
        last = self.entries[-1]
        return {
            "total_cycles": len(self.entries),
            "ku_growth": last["ku_active"] - first["ku_active"],
            "gu_resolved_total": last["gu_resolved"],
            "final_evidence_rate": last["evidence_rate"],
            "final_conflict_rate": last["conflict_rate"],
            "final_avg_confidence": last["avg_confidence"],
            "jump_cycles": sum(1 for e in self.entries if e["mode"] == "jump"),
            "total_llm_calls": sum(e.get("llm_calls", 0) for e in self.entries),
            "total_llm_tokens": sum(e.get("llm_tokens", 0) for e in self.entries),
            "total_search_calls": sum(e.get("search_calls", 0) for e in self.entries),
            "total_fetch_calls": sum(e.get("fetch_calls", 0) for e in self.entries),
        }
