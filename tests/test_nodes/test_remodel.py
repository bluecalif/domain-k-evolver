"""Remodel node (Silver P2) 테스트.

P2-C1: merge 시나리오 (중복률 30%+)
P2-C2: split 시나리오 (상반 axis_tag 2+)
P2-C3: reclassify 시나리오 (카테고리 부정합)
P2-C6: schema 양방향 테스트
P2-A3: phase_number 필드 테스트
P2-A4: phase snapshot 테스트
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import jsonschema
import pytest

from src.nodes.remodel import (
    _build_rollback_payload,
    _propose_from_audit_findings,
    _propose_merges,
    _propose_reclassify,
    _propose_splits,
    remodel_node,
    reset_report_counter,
    run_remodel,
)
from src.utils.state_io import snapshot_phase


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "remodel_report.schema.json"


@pytest.fixture(autouse=True)
def _reset_counter():
    reset_report_counter()
    yield
    reset_report_counter()


def _make_ku(
    ku_id: str,
    category: str,
    field: str = "price",
    value: str = "1000",
    status: str = "active",
    geo: str = "",
) -> dict:
    ku = {
        "ku_id": ku_id,
        "entity_key": f"japan-travel:{category}:item-{ku_id[-2:]}",
        "field": field,
        "value": value,
        "observed_at": "2026-04-12",
        "evidence_links": ["EU-0001"],
        "confidence": 0.85,
        "status": status,
    }
    if geo:
        ku["axis_tags"] = {"geography": geo}
    return ku


def _make_skeleton(categories: list[str]) -> dict:
    return {
        "domain": "japan-travel",
        "categories": [{"slug": c, "description": ""} for c in categories],
        "axes": [{"name": "geography", "anchors": ["tokyo", "osaka", "kyoto"]}],
        "aliases": {},
    }


def _make_audit_report(findings: list[dict] | None = None, cycle: int = 10) -> dict:
    return {
        "audit_cycle": cycle,
        "window": [1, cycle],
        "findings": findings or [],
        "recommendations": [],
        "policy_patches": [],
    }


def _make_state(
    kus: list[dict] | None = None,
    skeleton: dict | None = None,
    audit_history: list[dict] | None = None,
) -> dict:
    return {
        "knowledge_units": kus or [],
        "gap_map": [],
        "domain_skeleton": skeleton or _make_skeleton(["transport", "food", "accommodation"]),
        "policies": {},
        "metrics": {"cycle": 10},
        "current_cycle": 10,
        "audit_history": audit_history,
        "phase_number": 0,
        "phase_history": [],
        "remodel_report": None,
    }


# ---------------------------------------------------------------------------
# P2-C1: merge 시나리오 (중복률 30%+)
# ---------------------------------------------------------------------------

class TestMergeProposal:
    def test_merge_overlap_above_threshold(self):
        """entity 중복률 30%+ → merge 제안 생성."""
        kus = [
            # item-01 과 item-02 가 같은 category, 같은 field+value
            {
                "ku_id": "KU-0001", "entity_key": "japan-travel:transport:item-01",
                "field": "price", "value": "1000", "status": "active",
                "evidence_links": ["EU-0001"], "confidence": 0.85,
            },
            {
                "ku_id": "KU-0002", "entity_key": "japan-travel:transport:item-01",
                "field": "duration", "value": "2h", "status": "active",
                "evidence_links": ["EU-0002"], "confidence": 0.80,
            },
            {
                "ku_id": "KU-0003", "entity_key": "japan-travel:transport:item-02",
                "field": "price", "value": "1000", "status": "active",
                "evidence_links": ["EU-0003"], "confidence": 0.85,
            },
            {
                "ku_id": "KU-0004", "entity_key": "japan-travel:transport:item-02",
                "field": "duration", "value": "2h", "status": "active",
                "evidence_links": ["EU-0004"], "confidence": 0.80,
            },
        ]
        skeleton = _make_skeleton(["transport", "food"])
        proposals = _propose_merges(kus, skeleton)
        assert len(proposals) >= 1
        merge = proposals[0]
        assert merge["type"] == "merge"
        assert merge["params"]["overlap_ratio"] >= 0.30
        assert len(merge["target_entities"]) == 2

    def test_no_merge_below_threshold(self):
        """중복률이 30% 미만이면 merge 제안 없음."""
        kus = [
            {
                "ku_id": "KU-0001", "entity_key": "japan-travel:transport:item-01",
                "field": "price", "value": "1000", "status": "active",
                "evidence_links": ["EU-0001"], "confidence": 0.85,
            },
            {
                "ku_id": "KU-0002", "entity_key": "japan-travel:transport:item-01",
                "field": "duration", "value": "2h", "status": "active",
                "evidence_links": ["EU-0002"], "confidence": 0.80,
            },
            {
                "ku_id": "KU-0003", "entity_key": "japan-travel:transport:item-02",
                "field": "location", "value": "tokyo", "status": "active",
                "evidence_links": ["EU-0003"], "confidence": 0.85,
            },
            {
                "ku_id": "KU-0004", "entity_key": "japan-travel:transport:item-02",
                "field": "hours", "value": "9-17", "status": "active",
                "evidence_links": ["EU-0004"], "confidence": 0.80,
            },
        ]
        skeleton = _make_skeleton(["transport"])
        proposals = _propose_merges(kus, skeleton)
        assert len(proposals) == 0

    def test_merge_ignores_deprecated_kus(self):
        """deprecated KU 는 merge 대상에서 제외."""
        kus = [
            {
                "ku_id": "KU-0001", "entity_key": "japan-travel:transport:item-01",
                "field": "price", "value": "1000", "status": "deprecated",
                "evidence_links": ["EU-0001"], "confidence": 0.85,
            },
            {
                "ku_id": "KU-0002", "entity_key": "japan-travel:transport:item-02",
                "field": "price", "value": "1000", "status": "active",
                "evidence_links": ["EU-0002"], "confidence": 0.85,
            },
        ]
        skeleton = _make_skeleton(["transport"])
        proposals = _propose_merges(kus, skeleton)
        assert len(proposals) == 0


# ---------------------------------------------------------------------------
# P2-C2: split 시나리오 (상반 axis_tag 2+)
# ---------------------------------------------------------------------------

class TestSplitProposal:
    def test_split_conflicting_geo_tags(self):
        """한 entity에 geography tag 2개 이상 → split 제안."""
        kus = [
            _make_ku("KU-0001", "transport", field="price", value="1000", geo="tokyo"),
            _make_ku("KU-0002", "transport", field="price", value="2000", geo="osaka"),
        ]
        # 같은 entity_key 로 맞추기
        kus[0]["entity_key"] = "japan-travel:transport:jr-pass"
        kus[1]["entity_key"] = "japan-travel:transport:jr-pass"

        findings = [{"finding_id": "F-COV-01", "category": "axis_imbalance", "severity": "warning"}]
        proposals = _propose_splits(kus, findings)
        assert len(proposals) >= 1
        split = proposals[0]
        assert split["type"] == "split"
        assert "tokyo" in str(split["params"]["axis_values"])
        assert "osaka" in str(split["params"]["axis_values"])

    def test_no_split_single_geo(self):
        """한 entity에 geography tag 1개면 split 제안 없음."""
        kus = [
            _make_ku("KU-0001", "transport", geo="tokyo"),
        ]
        kus[0]["entity_key"] = "japan-travel:transport:jr-pass"
        proposals = _propose_splits(kus, [])
        assert len(proposals) == 0


# ---------------------------------------------------------------------------
# P2-C3: reclassify 시나리오 (카테고리 부정합)
# ---------------------------------------------------------------------------

class TestReclassifyProposal:
    def test_reclassify_invalid_category(self):
        """skeleton에 없는 category → reclassify 제안."""
        kus = [
            {
                "ku_id": "KU-0001",
                "entity_key": "japan-travel:invalid-cat:item-01",
                "field": "price", "value": "1000", "status": "active",
                "evidence_links": ["EU-0001"], "confidence": 0.85,
            },
        ]
        skeleton = _make_skeleton(["transport", "food"])
        proposals = _propose_reclassify(kus, skeleton)
        assert len(proposals) >= 1
        reclass = proposals[0]
        assert reclass["type"] == "reclassify"
        assert reclass["params"]["from_category"] == "invalid-cat"
        assert reclass["params"]["to_category"] in ("transport", "food")

    def test_no_reclassify_valid_category(self):
        """유효한 category 는 reclassify 대상 아님."""
        kus = [_make_ku("KU-0001", "transport")]
        skeleton = _make_skeleton(["transport", "food"])
        proposals = _propose_reclassify(kus, skeleton)
        assert len(proposals) == 0


# ---------------------------------------------------------------------------
# Audit findings 기반 제안 (source_policy, gap_rule)
# ---------------------------------------------------------------------------

class TestAuditFindingsProposals:
    def test_yield_decline_produces_source_policy(self):
        findings = [{
            "finding_id": "F-YIELD-01",
            "category": "yield_decline",
            "severity": "warning",
            "description": "KU yield 체감",
            "evidence": {"first_half_avg": 0.5, "second_half_avg": 0.1},
        }]
        proposals = _propose_from_audit_findings(findings, {})
        assert any(p["type"] == "source_policy" for p in proposals)

    def test_critical_coverage_gap_produces_gap_rule(self):
        findings = [{
            "finding_id": "F-COV-FOOD",
            "category": "coverage_gap",
            "severity": "critical",
            "description": "카테고리 'food' KU 부족: 0개",
            "evidence": {"category": "food", "ku_count": 0},
        }]
        proposals = _propose_from_audit_findings(findings, {})
        gap_rules = [p for p in proposals if p["type"] == "gap_rule"]
        assert len(gap_rules) >= 1
        assert gap_rules[0]["params"]["category"] == "food"

    def test_non_critical_coverage_gap_no_proposal(self):
        """warning severity coverage_gap 은 gap_rule 제안하지 않음."""
        findings = [{
            "finding_id": "F-COV-01",
            "category": "coverage_gap",
            "severity": "warning",
            "description": "KU 부족",
            "evidence": {"category": "food", "ku_count": 2},
        }]
        proposals = _propose_from_audit_findings(findings, {})
        gap_rules = [p for p in proposals if p["type"] == "gap_rule"]
        assert len(gap_rules) == 0


# ---------------------------------------------------------------------------
# run_remodel 통합
# ---------------------------------------------------------------------------

class TestRunRemodel:
    def test_returns_valid_report_structure(self):
        kus = [_make_ku("KU-0001", "transport")]
        state = _make_state(kus=kus)
        audit = _make_audit_report()
        report = run_remodel(state, audit)

        assert "report_id" in report
        assert report["report_id"].startswith("RM-")
        assert "proposals" in report
        assert "rollback_payload" in report
        assert report["approval"]["status"] == "pending"

    def test_empty_findings_may_still_detect_merges(self):
        """audit findings 가 없어도 entity 중복은 탐지 가능."""
        kus = [
            {"ku_id": "KU-0001", "entity_key": "japan-travel:transport:a",
             "field": "price", "value": "100", "status": "active",
             "evidence_links": ["EU-0001"], "confidence": 0.8},
            {"ku_id": "KU-0002", "entity_key": "japan-travel:transport:b",
             "field": "price", "value": "100", "status": "active",
             "evidence_links": ["EU-0002"], "confidence": 0.8},
        ]
        state = _make_state(kus=kus)
        audit = _make_audit_report(findings=[])
        report = run_remodel(state, audit)
        # 1 field 각각이므로 overlap = 1/1 = 100% → merge
        merges = [p for p in report["proposals"] if p["type"] == "merge"]
        assert len(merges) >= 1

    def test_rollback_payload_captures_affected_kus(self):
        kus = [
            {"ku_id": "KU-0001", "entity_key": "japan-travel:transport:a",
             "field": "price", "value": "100", "status": "active",
             "evidence_links": ["EU-0001"], "confidence": 0.8},
            {"ku_id": "KU-0002", "entity_key": "japan-travel:transport:b",
             "field": "price", "value": "100", "status": "active",
             "evidence_links": ["EU-0002"], "confidence": 0.8},
        ]
        state = _make_state(kus=kus)
        audit = _make_audit_report()
        report = run_remodel(state, audit)
        payload = report["rollback_payload"]
        assert "skeleton_snapshot" in payload
        assert "affected_kus" in payload


# ---------------------------------------------------------------------------
# remodel_node (LangGraph wrapper)
# ---------------------------------------------------------------------------

class TestRemodelNode:
    def test_node_with_audit_history(self):
        audit = _make_audit_report()
        state = _make_state(
            kus=[_make_ku("KU-0001", "transport")],
            audit_history=[audit],
        )
        result = remodel_node(state)
        assert "remodel_report" in result
        assert result["remodel_report"] is not None
        assert result["hitl_pending"]["gate"] == "R"

    def test_node_without_audit_history(self):
        state = _make_state(audit_history=[])
        result = remodel_node(state)
        assert result["remodel_report"] is None

    def test_node_without_audit_history_none(self):
        state = _make_state(audit_history=None)
        result = remodel_node(state)
        assert result["remodel_report"] is None


# ---------------------------------------------------------------------------
# P2-C6: schema 양방향 테스트
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    @pytest.fixture
    def schema(self):
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            return json.load(f)

    def test_valid_report_passes_schema(self, schema):
        """유효한 report → validate pass."""
        report = {
            "report_id": "RM-0001",
            "created_at": "2026-04-12T00:00:00+00:00",
            "source_audit_id": 10,
            "proposals": [
                {
                    "type": "merge",
                    "rationale": "entity 중복률 50%",
                    "target_entities": ["japan-travel:transport:a", "japan-travel:transport:b"],
                    "params": {"canonical_key": "japan-travel:transport:a"},
                    "expected_delta": {"metric": "entity_count", "before": 10, "after": 9},
                }
            ],
            "rollback_payload": {
                "skeleton_snapshot": {},
                "affected_kus": ["KU-0001"],
            },
            "approval": {"status": "pending"},
        }
        jsonschema.validate(report, schema)

    def test_missing_required_field_fails_schema(self, schema):
        """필수 필드 누락 → validate fail."""
        report = {
            "report_id": "RM-0001",
            # created_at 누락
            "source_audit_id": 10,
            "proposals": [],
            "rollback_payload": {},
            "approval": {"status": "pending"},
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(report, schema)

    def test_invalid_proposal_type_fails(self, schema):
        """잘못된 proposal type → validate fail."""
        report = {
            "report_id": "RM-0001",
            "created_at": "2026-04-12T00:00:00+00:00",
            "source_audit_id": 10,
            "proposals": [
                {
                    "type": "invalid_type",
                    "rationale": "test",
                    "target_entities": ["x"],
                    "params": {},
                    "expected_delta": {"metric": "x", "before": 0, "after": 1},
                }
            ],
            "rollback_payload": {},
            "approval": {"status": "pending"},
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(report, schema)

    def test_invalid_approval_status_fails(self, schema):
        """잘못된 approval status → validate fail."""
        report = {
            "report_id": "RM-0001",
            "created_at": "2026-04-12T00:00:00+00:00",
            "source_audit_id": 10,
            "proposals": [],
            "rollback_payload": {},
            "approval": {"status": "unknown"},
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(report, schema)

    def test_run_remodel_output_validates(self, schema):
        """run_remodel 출력이 schema 를 통과."""
        kus = [_make_ku("KU-0001", "transport")]
        state = _make_state(kus=kus)
        audit = _make_audit_report()
        report = run_remodel(state, audit)
        jsonschema.validate(report, schema)


# ---------------------------------------------------------------------------
# P2-A3: phase_number 필드
# ---------------------------------------------------------------------------

class TestPhaseNumber:
    def test_state_has_phase_number(self):
        """EvolverState 에 phase_number 필드 존재."""
        from src.state import EvolverState
        # TypedDict 의 __annotations__ 에 phase_number 있음
        assert "phase_number" in EvolverState.__annotations__

    def test_state_io_initializes_phase_number(self):
        """state_io.load_state 가 phase_number 를 0 으로 초기화 확인."""
        from src.utils.state_io import load_state
        # 실제 bench 데이터로 load
        bench_path = Path(__file__).resolve().parents[2] / "bench" / "japan-travel"
        if bench_path.exists():
            state = load_state(bench_path)
            assert "phase_number" in state
            assert state["phase_number"] == 0


# ---------------------------------------------------------------------------
# P2-A4: phase snapshot
# ---------------------------------------------------------------------------

class TestPhaseSnapshot:
    def test_snapshot_phase_creates_directory(self, tmp_path):
        """snapshot_phase 가 state/phase_{N}/ 디렉토리를 생성."""
        domain = tmp_path / "test-domain"
        state_dir = domain / "state"
        state_dir.mkdir(parents=True)

        # 더미 state 파일 생성
        for fname in ("knowledge-units.json", "gap-map.json", "domain-skeleton.json",
                       "metrics.json", "policies.json"):
            (state_dir / fname).write_text("{}", encoding="utf-8")

        result = snapshot_phase(domain, phase_number=1)
        assert result.exists()
        assert result.name == "phase_1"
        assert (result / "knowledge-units.json").exists()
        assert (result / "domain-skeleton.json").exists()

    def test_snapshot_phase_overwrites_existing(self, tmp_path):
        """이미 존재하는 phase snapshot 을 덮어쓰기."""
        domain = tmp_path / "test-domain"
        state_dir = domain / "state"
        state_dir.mkdir(parents=True)
        (state_dir / "knowledge-units.json").write_text("[]", encoding="utf-8")

        # 첫 번째 스냅샷
        snapshot_phase(domain, 1)
        # 두 번째 스냅샷 (덮어쓰기)
        result = snapshot_phase(domain, 1)
        assert result.exists()
