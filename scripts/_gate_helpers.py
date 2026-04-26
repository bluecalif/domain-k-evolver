"""S3 GU Mechanistic Gate 보조 함수 (private, 순수 함수).

Plan: C:\\Users\\User\\.claude\\plans\\b-plann-very-carefully-breezy-flame.md §4
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Callable


def load_json(path: Path | str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def count_adj_gus(gap_map: list[dict], predicate: Callable[[dict], bool] | None = None) -> int:
    """trigger == 'A:adjacent_gap' 인 GU 카운트. 옵션 predicate 로 추가 필터링."""
    n = 0
    for gu in gap_map:
        if gu.get("trigger") != "A:adjacent_gap":
            continue
        if predicate is not None and not predicate(gu):
            continue
        n += 1
    return n


def slot_state_count(
    matrix: dict,
    state: str,
    cat: str | None = None,
    entity: str | None = None,
) -> int:
    """matrix['categories'][cat]['matrix'][entity][field]['state'] 가 state 인 슬롯 수.

    cat=None: 모든 카테고리 합산. entity=None: 카테고리 내 모든 entity.
    """
    cats = matrix.get("categories", {})
    target_cats = [cat] if cat is not None else list(cats.keys())
    total = 0
    for c in target_cats:
        ent_map = cats.get(c, {}).get("matrix", {})
        target_ents = [entity] if entity is not None else list(ent_map.keys())
        for e in target_ents:
            for cell in ent_map.get(e, {}).values():
                if cell.get("state") == state:
                    total += 1
    return total


def snapshot_diff_adj(snapshots_dir: Path | str) -> list[int]:
    """state-snapshots/cycle-N-snapshot/gap-map.json 들에서 adj GU 카운트 차분.

    반환: 길이 (N_cycles - 1) 의 정수 리스트. [Δc2, Δc3, ..., ΔcN].
    cycle 디렉터리가 1개면 빈 리스트.
    """
    snapshots_dir = Path(snapshots_dir)
    cycle_dirs = sorted(
        [
            d
            for d in snapshots_dir.iterdir()
            if d.is_dir() and d.name.startswith("cycle-") and d.name.endswith("-snapshot")
        ],
        key=lambda d: int(d.name.split("-")[1]),
    )
    counts: list[int] = []
    for d in cycle_dirs:
        gm_path = d / "gap-map.json"
        counts.append(count_adj_gus(load_json(gm_path)) if gm_path.exists() else 0)
    return [counts[i] - counts[i - 1] for i in range(1, len(counts))]


def kl_divergence(p: dict[str, float], q: dict[str, float]) -> float:
    """KL(p || q) — 이산 분포. 정규화는 caller 책임.

    - p[k] == 0: 항 0 (0·log0 = 0 컨벤션).
    - p[k] > 0 ∧ q[k] == 0: ∞ (KL 정의 불가 → O2 검사용 시그널).
    """
    keys = set(p) | set(q)
    total = 0.0
    for k in keys:
        pk = p.get(k, 0.0)
        qk = q.get(k, 0.0)
        if pk == 0:
            continue
        if qk == 0:
            return float("inf")
        total += pk * math.log(pk / qk)
    return total
