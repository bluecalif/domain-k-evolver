"""Plateau Detector — 연속 N사이클 KU/GU 변화 0 감지.

연속 plateau_window 사이클 동안 KU active 수와 GU resolved 수가
변하지 않으면 plateau로 판정.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PlateauSnapshot:
    """사이클 종료 시점의 KU/GU 스냅샷."""

    cycle: int
    ku_active: int
    gu_resolved: int


class PlateauDetector:
    """연속 N사이클 변화 없음을 감지."""

    def __init__(self, window: int = 3) -> None:
        if window < 2:
            raise ValueError("plateau_window must be >= 2")
        self.window = window
        self._history: list[PlateauSnapshot] = []

    def record(self, cycle: int, state: dict) -> None:
        """사이클 종료 후 스냅샷 기록."""
        kus = state.get("knowledge_units", [])
        gus = state.get("gap_map", [])
        self._history.append(PlateauSnapshot(
            cycle=cycle,
            ku_active=sum(1 for k in kus if k.get("status") == "active"),
            gu_resolved=sum(1 for g in gus if g.get("status") == "resolved"),
        ))

    def is_plateau(self) -> bool:
        """최근 window 사이클 동안 KU/GU 변화가 0이면 True."""
        if len(self._history) < self.window:
            return False
        recent = self._history[-self.window:]
        first = recent[0]
        return all(
            s.ku_active == first.ku_active and s.gu_resolved == first.gu_resolved
            for s in recent[1:]
        )

    @property
    def history(self) -> list[PlateauSnapshot]:
        return list(self._history)
