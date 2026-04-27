"""scripts/check_s3_gu_gate.py 통합 테스트.

Plan: C:\\Users\\User\\.claude\\plans\\b-plann-very-carefully-breezy-flame.md §7.2

- compute_verdict: V/O 우선 정책, exit code 0/1/3
- load_trial: 실 베이스라인 / 누락 파일 처리
- main: subprocess 통한 e2e exit code 검증 (smoke)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.check_s3_gu_gate import (
    Result,
    TrialData,
    compute_verdict,
    eval_m5b,
    eval_m9,
    eval_m10,
    eval_m11,
    eval_v2,
    load_trial,
    main,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE = REPO_ROOT / "bench/silver/japan-travel/p7-rebuild-s3-smoke"
TARGET = REPO_ROOT / "bench/silver/japan-travel/p7-rebuild-s3-gu-smoke"


# ── compute_verdict ────────────────────────────────────────────


def _r(rid: str, passed: bool | None, *, vo: bool = False, tel: bool = False) -> Result:
    return Result(id=rid, label=rid.lower(), detail="-", passed=passed, is_v_or_o=vo, is_telemetry_deferred=tel)


def test_compute_verdict_pass_when_all_pass():
    results = [
        _r("V1", True, vo=True),
        _r("V2", True, vo=True),
        _r("M1", True),
        _r("M5b", None, tel=True),
    ]
    code, label = compute_verdict(results)
    assert code == 0
    assert label == "PASS"


def test_compute_verdict_fail_when_any_vo_fails():
    results = [
        _r("V1", True, vo=True),
        _r("V2", False, vo=True),
        _r("M1", True),
    ]
    code, label = compute_verdict(results)
    assert code == 1
    assert "FAIL" in label
    assert "V2" in label


def test_compute_verdict_conditional_when_only_m_fails():
    """V/O all PASS but some M FAIL → exit 3 (CONDITIONAL)."""
    results = [
        _r("V1", True, vo=True),
        _r("V2", True, vo=True),
        _r("M1", False),
        _r("M5", True),
    ]
    code, label = compute_verdict(results)
    assert code == 3
    assert "CONDITIONAL" in label
    assert "M1" in label


def test_compute_verdict_telemetry_na_does_not_fail():
    """Telemetry-deferred N/A 는 verdict 에 영향 없음."""
    results = [
        _r("V1", True, vo=True),
        _r("M1", True),
        _r("M5b", None, tel=True),
        _r("M9", None, tel=True),
    ]
    code, _ = compute_verdict(results)
    assert code == 0


def test_compute_verdict_m_na_in_normal_flow_treated_as_pass():
    """일반 M criterion 의 None (e.g. M2 no data) 는 verdict 카운트에서 제외 → 다른 PASS 면 PASS."""
    results = [
        _r("V1", True, vo=True),
        _r("M2", None),  # no data
        _r("M3", True),
    ]
    code, _ = compute_verdict(results)
    assert code == 0


def test_compute_verdict_vo_priority_over_m():
    """V/O FAIL ∧ M FAIL → 1 (V/O 우선), not 3."""
    results = [
        _r("V1", False, vo=True),
        _r("M1", False),
    ]
    code, label = compute_verdict(results)
    assert code == 1
    assert "FAIL" in label


# ── load_trial ─────────────────────────────────────────────────


def test_load_trial_real_baseline_no_error():
    t = load_trial(BASELINE)
    assert t.matrix["summary"]["vacant"] == 97
    assert len(t.gap_map) > 0
    assert len(t.knowledge_units) == 79
    assert len(t.adjacency_yield) == 5


def test_load_trial_missing_dir_raises():
    with pytest.raises(FileNotFoundError):
        load_trial(REPO_ROOT / "bench/nonexistent-trial-xyz")


def test_load_trial_missing_artifact_raises(tmp_path):
    """Trial dir 존재하지만 entity-field-matrix.json 없음 → FileNotFoundError."""
    (tmp_path / "state").mkdir()
    (tmp_path / "state-snapshots").mkdir()
    (tmp_path / "trajectory").mkdir()
    (tmp_path / "trajectory" / "trajectory.json").write_text("[]", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        load_trial(tmp_path)


# ── main (e2e exit code) ───────────────────────────────────────


def test_main_returns_2_on_missing_baseline(tmp_path, capsys):
    """존재하지 않는 baseline → ERROR exit code 2."""
    rc = main(["--baseline", str(tmp_path / "nonexistent"), "--target", str(TARGET)])
    assert rc == 2


def test_main_real_evaluation_returns_fail(tmp_path):
    """실 baseline vs target → V/O FAIL → exit 1.

    JSON 출력도 함께 검증.
    """
    out_json = tmp_path / "report.json"
    rc = main(["--baseline", str(BASELINE), "--target", str(TARGET), "--json", str(out_json)])
    assert rc == 1
    assert out_json.exists()
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["verdict"]["code"] == 1
    assert "FAIL" in data["verdict"]["label"]
    assert data["self_mode"] is False
    # V/O 카테고리 전부 포함
    ids = {r["id"] for r in data["results"]}
    assert {"V1", "V2", "V3", "O1", "O2", "VxO"}.issubset(ids)
    assert {"M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"}.issubset(ids)
    assert {"M5b", "M9", "M10", "M11"}.issubset(ids)


def test_main_self_sanity_baseline_only_records_self_mode(tmp_path):
    """baseline == target → self_mode=True flag in JSON."""
    out_json = tmp_path / "self.json"
    rc = main(["--baseline", str(BASELINE), "--target", str(BASELINE), "--json", str(out_json)])
    # baseline 자체가 unhealthy (3 cats abandoned) 라 exit 1 예상.
    assert rc == 1
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["self_mode"] is True
    # V1/V2/V3/M1/M3/M4/M6/M8 모두 PASS (no-regression)
    by_id = {r["id"]: r for r in data["results"]}
    for rid in ["V1", "V2", "V3", "M1", "M3", "M4", "M6", "M8"]:
        assert by_id[rid]["passed"] is True, f"{rid} should PASS in self-mode"


def test_main_strict_flag_tightens_m5(tmp_path):
    """--strict → M5 strong form (Δc4>0 ∧ Δc5>0).

    target s3-gu-smoke: Δc4=0, Δc5=2 → strict FAIL, weak PASS.
    """
    out_weak = tmp_path / "weak.json"
    out_strict = tmp_path / "strict.json"
    main(["--baseline", str(BASELINE), "--target", str(TARGET), "--json", str(out_weak)])
    main(["--baseline", str(BASELINE), "--target", str(TARGET), "--json", str(out_strict), "--strict"])
    weak = {r["id"]: r for r in json.loads(out_weak.read_text(encoding="utf-8"))["results"]}
    strict = {r["id"]: r for r in json.loads(out_strict.read_text(encoding="utf-8"))["results"]}
    assert weak["M5"]["passed"] is True
    assert strict["M5"]["passed"] is False


# ── M5b/M9/M10/M11 eval functions (L2) ────────────────────────


def _make_trial(**overrides) -> TrialData:
    defaults: dict = dict(
        path=Path("."),
        matrix={"summary": {"vacant": 0, "by_category": {}}, "categories": {}},
        gap_map=[],
        knowledge_units=[],
        conflict_ledger=[],
        adjacency_yield=[],
        trajectory=[],
        snapshots_dir=Path("."),
    )
    defaults.update(overrides)
    return TrialData(**defaults)


def _adj_gu(origin: str | None = None, created_cycle: int | str | None = None) -> dict:
    g: dict = {"trigger": "A:adjacent_gap", "target": {"entity_key": "d:cat:slug", "field": "f"}}
    if origin is not None:
        g["origin"] = origin
    if created_cycle is not None:
        g["created_cycle"] = created_cycle
    return g


class TestEvalM5b:
    def test_pass_when_all_entries_have_cap_hit_count(self):
        t = _make_trial(trajectory=[{"cycle": 1, "cap_hit_count": 0}, {"cycle": 2, "cap_hit_count": 1}])
        r = eval_m5b(t)
        assert r.passed is True

    def test_fail_when_entries_missing_cap_hit_count(self):
        t = _make_trial(trajectory=[{"cycle": 1}, {"cycle": 2}])
        r = eval_m5b(t)
        assert r.passed is False


class TestEvalM9:
    def test_pass_when_adj_gus_have_valid_origin(self):
        t = _make_trial(gap_map=[
            _adj_gu("claim_loop"),
            _adj_gu("post_cycle_sweep"),
            _adj_gu("seed_bootstrap"),
        ])
        r = eval_m9(t)
        assert r.passed is True

    def test_fail_when_adj_gus_missing_origin(self):
        t = _make_trial(gap_map=[_adj_gu() for _ in range(5)])
        r = eval_m9(t)
        assert r.passed is False


class TestEvalM10:
    def test_pass_when_adj_gus_have_int_created_cycle(self):
        t = _make_trial(gap_map=[_adj_gu(created_cycle=1), _adj_gu(created_cycle=3)])
        r = eval_m10(t)
        assert r.passed is True

    def test_fail_when_adj_gus_missing_created_cycle(self):
        t = _make_trial(gap_map=[_adj_gu() for _ in range(5)])
        r = eval_m10(t)
        assert r.passed is False


def _matrix_with(cat_entities: dict[str, dict[str, dict[str, str]]]) -> dict:
    """cat_entities = {cat: {slug: {field: state}}}"""
    cats: dict = {}
    for cat, ents in cat_entities.items():
        matrix: dict = {}
        for slug, fields in ents.items():
            matrix[slug] = {f: {"state": st, "ku_ids": [], "gu_ids": []} for f, st in fields.items()}
        cats[cat] = {"entities": [s for s in ents if s != "*"], "fields": [], "matrix": matrix}
    return {"summary": {"vacant": 0, "by_category": {}}, "categories": cats}


class TestEvalV2:
    def test_pass_when_existing_entities_no_regression(self):
        b = _make_trial(matrix=_matrix_with({"transport": {"shinkansen": {"price": "ku_gu"}}}))
        t = _make_trial(matrix=_matrix_with({"transport": {"shinkansen": {"price": "ku_gu"}}}))
        r = eval_v2(b, t, self_mode=False)
        assert r.passed is True

    def test_excludes_new_entities_from_regression(self):
        """baseline 에 없던 entity 의 vacant 는 regression 미산정."""
        b = _make_trial(matrix=_matrix_with({"transport": {"shinkansen": {"price": "ku_gu"}}}))
        t = _make_trial(matrix=_matrix_with({"transport": {
            "shinkansen": {"price": "ku_gu"},
            "new-bus-line": {"price": "vacant", "duration": "vacant"},
        }}))
        r = eval_v2(b, t, self_mode=False)
        assert r.passed is True
        assert "new-entity vacant excluded" in r.detail
        assert "transport=2(1ent)" in r.detail

    def test_fail_when_existing_entity_regresses(self):
        """기존 entity 의 vacant 가 늘어나면 FAIL."""
        b = _make_trial(matrix=_matrix_with({"transport": {"shinkansen": {"price": "ku_gu", "duration": "ku_gu"}}}))
        t = _make_trial(matrix=_matrix_with({"transport": {"shinkansen": {"price": "vacant", "duration": "vacant"}}}))
        r = eval_v2(b, t, self_mode=False)
        assert r.passed is False
        assert "transport +2" in r.detail

    def test_wildcard_treated_as_entity_when_in_baseline(self):
        """`*` 가 baseline 에 있으면 existing 으로 간주."""
        b = _make_trial(matrix=_matrix_with({"transport": {"*": {"price": "vacant"}}}))
        t = _make_trial(matrix=_matrix_with({"transport": {"*": {"price": "vacant"}}}))
        r = eval_v2(b, t, self_mode=False)
        assert r.passed is True

    def test_wildcard_new_in_target_excluded(self):
        """target 에 처음 등장한 `*` 슬롯의 vacant 는 제외."""
        b = _make_trial(matrix=_matrix_with({"pass-ticket": {"jr-pass": {"price": "ku_gu"}}}))
        t = _make_trial(matrix=_matrix_with({"pass-ticket": {
            "jr-pass": {"price": "ku_gu"},
            "*": {"price": "vacant", "where_to_buy": "vacant"},
        }}))
        r = eval_v2(b, t, self_mode=False)
        assert r.passed is True


class TestEvalM11:
    def test_pass_when_all_entries_have_both_counts(self):
        t = _make_trial(trajectory=[
            {"cycle": 1, "adj_gen_count": 3, "wildcard_gen_count": 5},
            {"cycle": 2, "adj_gen_count": 0, "wildcard_gen_count": 0},
        ])
        r = eval_m11(t)
        assert r.passed is True

    def test_fail_when_entries_missing_counts(self):
        t = _make_trial(trajectory=[{"cycle": 1}, {"cycle": 2}])
        r = eval_m11(t)
        assert r.passed is False
