"""scripts/_gate_helpers.py L1 테스트.

Plan: C:\\Users\\User\\.claude\\plans\\b-plann-very-carefully-breezy-flame.md §4, §7.2
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from scripts._gate_helpers import (
    count_adj_gus,
    kl_divergence,
    slot_state_count,
    snapshot_diff_adj,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_SNAPSHOTS = REPO_ROOT / "bench/silver/japan-travel/p7-rebuild-s3-smoke/state-snapshots"


# ── count_adj_gus ──────────────────────────────────────────────


def test_count_adj_gus_total():
    gm = [
        {"trigger": "A:adjacent_gap", "target": {"entity_key": "d:c:foo", "field": "f1"}},
        {"trigger": "A:adjacent_gap", "target": {"entity_key": "d:c:bar", "field": "f2"}},
        {"trigger": "", "target": {"entity_key": "d:c:baz", "field": "f3"}},
    ]
    assert count_adj_gus(gm) == 2


def test_count_adj_gus_filters_wildcard_with_predicate():
    """M1 named-entity adj count: entity slug == '*' 제외."""
    gm = [
        {"trigger": "A:adjacent_gap", "target": {"entity_key": "d:c:*", "field": "price"}},
        {"trigger": "A:adjacent_gap", "target": {"entity_key": "d:c:foo", "field": "price"}},
        {"trigger": "A:adjacent_gap", "target": {"entity_key": "d:c:bar", "field": "duration"}},
    ]

    def not_wildcard(g: dict) -> bool:
        return g.get("target", {}).get("entity_key", "").split(":")[2] != "*"

    assert count_adj_gus(gm, predicate=not_wildcard) == 2


def test_count_adj_gus_empty_returns_zero():
    assert count_adj_gus([]) == 0


def test_count_adj_gus_no_trigger_field_treated_as_non_adj():
    gm = [{"target": {"entity_key": "d:c:foo", "field": "f"}}]
    assert count_adj_gus(gm) == 0


# ── slot_state_count ───────────────────────────────────────────


def _make_matrix(cells: dict[tuple[str, str, str], str]) -> dict:
    """cells: {(cat, entity, field): state} → matrix dict (categories.[c].matrix.[e].[f].state)."""
    cats: dict = {}
    for (cat, ent, fld), state in cells.items():
        cat_node = cats.setdefault(cat, {"matrix": {}})
        cat_node["matrix"].setdefault(ent, {})[fld] = {"state": state, "ku_ids": [], "gu_ids": []}
    return {"categories": cats}


def test_slot_state_count_total_aggregates_all_categories():
    m = _make_matrix(
        {
            ("a", "e1", "f1"): "vacant",
            ("a", "e1", "f2"): "ku_only",
            ("b", "e2", "f1"): "vacant",
        }
    )
    assert slot_state_count(m, "vacant") == 2
    assert slot_state_count(m, "ku_only") == 1


def test_slot_state_count_per_category_filter():
    m = _make_matrix(
        {
            ("a", "e1", "f1"): "vacant",
            ("b", "e2", "f1"): "vacant",
            ("b", "e3", "f1"): "ku_only",
        }
    )
    assert slot_state_count(m, "vacant", cat="a") == 1
    assert slot_state_count(m, "vacant", cat="b") == 1


def test_slot_state_count_per_entity_filter():
    m = _make_matrix(
        {
            ("a", "e1", "f1"): "vacant",
            ("a", "e1", "f2"): "vacant",
            ("a", "e2", "f1"): "ku_only",
        }
    )
    assert slot_state_count(m, "vacant", cat="a", entity="e1") == 2
    assert slot_state_count(m, "vacant", cat="a", entity="e2") == 0


def test_slot_state_count_unknown_state_returns_zero():
    m = _make_matrix({("a", "e1", "f1"): "vacant"})
    assert slot_state_count(m, "nonexistent_state") == 0


def test_slot_state_count_real_baseline_attraction_vacant():
    """실 베이스라인 attraction vacant=72 (summary.by_category 기준)."""
    matrix_path = (
        REPO_ROOT
        / "bench/silver/japan-travel/p7-rebuild-s3-smoke/entity-field-matrix.json"
    )
    with open(matrix_path, encoding="utf-8") as f:
        m = json.load(f)
    assert slot_state_count(m, "vacant", cat="attraction") == 72


# ── snapshot_diff_adj ──────────────────────────────────────────


def test_snapshot_diff_adj_baseline_real_data():
    """실 베이스라인 snapshot adj counts: c1=6, c2=8, c3=14, c4=16, c5=16 → diffs [2, 6, 2, 0]."""
    diffs = snapshot_diff_adj(BASELINE_SNAPSHOTS)
    assert diffs == [2, 6, 2, 0]


def test_snapshot_diff_adj_synthetic(tmp_path):
    for cyc, adj_n in [(1, 2), (2, 5), (3, 5)]:
        d = tmp_path / f"cycle-{cyc}-snapshot"
        d.mkdir()
        gm = [{"trigger": "A:adjacent_gap"}] * adj_n + [{"trigger": ""}]
        (d / "gap-map.json").write_text(json.dumps(gm), encoding="utf-8")
    assert snapshot_diff_adj(tmp_path) == [3, 0]


def test_snapshot_diff_adj_treats_missing_gap_map_as_zero(tmp_path):
    for cyc in [1, 2]:
        (tmp_path / f"cycle-{cyc}-snapshot").mkdir()
    # 두 cycle 모두 gap-map.json 없음 → counts=[0,0] → diffs=[0]
    assert snapshot_diff_adj(tmp_path) == [0]


def test_snapshot_diff_adj_single_cycle_returns_empty(tmp_path):
    d = tmp_path / "cycle-1-snapshot"
    d.mkdir()
    (d / "gap-map.json").write_text("[]", encoding="utf-8")
    assert snapshot_diff_adj(tmp_path) == []


def test_snapshot_diff_adj_orders_by_cycle_number_not_lex(tmp_path):
    """cycle-10 이 cycle-2 뒤에 와야 함 (lex 정렬은 10<2)."""
    for cyc, adj_n in [(2, 5), (10, 9)]:
        d = tmp_path / f"cycle-{cyc}-snapshot"
        d.mkdir()
        gm = [{"trigger": "A:adjacent_gap"}] * adj_n
        (d / "gap-map.json").write_text(json.dumps(gm), encoding="utf-8")
    assert snapshot_diff_adj(tmp_path) == [4]  # 9-5


# ── kl_divergence ──────────────────────────────────────────────


def test_kl_divergence_identical_returns_zero():
    p = {"a": 0.5, "b": 0.3, "c": 0.2}
    assert kl_divergence(p, p) == pytest.approx(0.0, abs=1e-9)


def test_kl_divergence_zero_p_skipped():
    """0·log(0/q)=0 컨벤션 — p[k]=0 항 제외."""
    p = {"a": 0.0, "b": 1.0}
    q = {"a": 0.5, "b": 0.5}
    assert kl_divergence(p, q) == pytest.approx(math.log(2.0), abs=1e-9)


def test_kl_divergence_zero_q_with_positive_p_returns_inf():
    """O2 attraction 케이스 — open_share[a]=0 ∧ vacant_share[a]>0 → KL=∞."""
    p = {"attraction": 0.9, "other": 0.1}
    q = {"attraction": 0.0, "other": 1.0}
    assert kl_divergence(p, q) == float("inf")


def test_kl_divergence_attraction_pattern_high():
    """vacant 가 attraction 에 집중되었는데 open GU 는 다른 곳 → ∞ (O2 FAIL 신호)."""
    vacant_share = {"attraction": 0.84, "transport": 0.05, "regulation": 0.11}
    open_share = {"attraction": 0.00, "transport": 0.50, "regulation": 0.50}
    assert kl_divergence(vacant_share, open_share) == float("inf")


def test_kl_divergence_finite_when_q_covers_p():
    """KL 일반 케이스: 모든 q[k]>0 보장 → 유한값."""
    p = {"a": 0.6, "b": 0.4}
    q = {"a": 0.5, "b": 0.5}
    expected = 0.6 * math.log(0.6 / 0.5) + 0.4 * math.log(0.4 / 0.5)
    assert kl_divergence(p, q) == pytest.approx(expected, abs=1e-9)


def test_kl_divergence_handles_missing_keys_in_q():
    """q 에 없는 key 는 q[k]=0 으로 취급. p 가 양수면 ∞."""
    p = {"a": 0.5, "b": 0.5}
    q = {"a": 1.0}  # b 없음
    assert kl_divergence(p, q) == float("inf")
