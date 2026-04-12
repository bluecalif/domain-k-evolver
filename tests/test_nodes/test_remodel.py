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


# ---------------------------------------------------------------------------
# P2-B2: HITL-R 핸들러 테스트
# ---------------------------------------------------------------------------

class TestHitlRHandler:
    def test_hitl_r_approve_updates_report(self):
        """HITL-R approve → remodel_report.approval.status = approved."""
        from src.nodes.hitl_gate import hitl_gate_node

        report = {
            "report_id": "RM-0001",
            "proposals": [{"type": "merge", "rationale": "test"}],
            "approval": {"status": "pending"},
        }
        state = {
            "hitl_pending": {"gate": "R"},
            "remodel_report": report,
        }
        result = hitl_gate_node(state, response={"action": "approve", "actor": "tester"})
        assert result["hitl_pending"] is None
        assert result["remodel_report"]["approval"]["status"] == "approved"
        assert result["remodel_report"]["approval"]["actor"] == "tester"

    def test_hitl_r_reject_preserves_state(self):
        """HITL-R reject → remodel_report.approval.status = rejected."""
        from src.nodes.hitl_gate import hitl_gate_node

        report = {
            "report_id": "RM-0001",
            "proposals": [{"type": "merge", "rationale": "test"}],
            "approval": {"status": "pending"},
        }
        state = {
            "hitl_pending": {"gate": "R"},
            "remodel_report": report,
        }
        result = hitl_gate_node(
            state, response={"action": "reject", "reason": "불필요", "actor": "tester"},
        )
        assert result["hitl_pending"]["result"] == "rejected"
        assert result["remodel_report"]["approval"]["status"] == "rejected"
        assert result["remodel_report"]["approval"]["reason"] == "불필요"

    def test_hitl_r_auto_approve(self):
        """HITL-R response=None → 자동 승인."""
        from src.nodes.hitl_gate import hitl_gate_node

        state = {
            "hitl_pending": {"gate": "R"},
            "remodel_report": {
                "report_id": "RM-0001",
                "proposals": [],
                "approval": {"status": "pending"},
            },
        }
        result = hitl_gate_node(state, response=None)
        assert result["hitl_pending"] is None

    def test_hitl_r_payload_shows_proposals(self):
        """HITL-R payload 에 proposals_summary 포함."""
        from src.nodes.hitl_gate import _build_gate_payload

        state = {
            "remodel_report": {
                "report_id": "RM-0001",
                "proposals": [
                    {"type": "merge", "rationale": "entity 중복률 50%", "target_entities": ["a", "b"]},
                    {"type": "split", "rationale": "상반 geo tag", "target_entities": ["c"]},
                ],
                "approval": {"status": "pending"},
            },
        }
        payload = _build_gate_payload("R", state)
        assert payload["gate"] == "R"
        assert payload["proposal_count"] == 2
        assert len(payload["proposals_summary"]) == 2
        assert payload["proposals_summary"][0]["type"] == "merge"


# ---------------------------------------------------------------------------
# P2-B3: Orchestrator remodel 통합 테스트
# ---------------------------------------------------------------------------

class TestOrchestratorRemodel:
    def _make_orch_state(self, cycle: int = 10) -> dict:
        """remodel 테스트용 Orchestrator state."""
        return {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001", "entity_key": "japan-travel:transport:item-01",
                    "field": "price", "value": "1000", "status": "active",
                    "evidence_links": ["EU-0001"], "confidence": 0.85,
                    "observed_at": "2026-04-12",
                },
                {
                    "ku_id": "KU-0002", "entity_key": "japan-travel:transport:item-02",
                    "field": "price", "value": "1000", "status": "active",
                    "evidence_links": ["EU-0002"], "confidence": 0.85,
                    "observed_at": "2026-04-12",
                },
            ],
            "gap_map": [],
            "domain_skeleton": {
                "domain": "japan-travel",
                "categories": [{"slug": "transport", "description": ""}],
                "axes": [],
                "aliases": {},
            },
            "metrics": {"cycle": cycle, "rates": {}},
            "policies": {},
            "current_cycle": cycle,
            "current_plan": None,
            "current_claims": None,
            "current_critique": None,
            "current_mode": None,
            "axis_coverage": None,
            "jump_history": [],
            "hitl_pending": None,
            "conflict_ledger": [],
            "phase_number": 0,
            "phase_history": [],
            "remodel_report": None,
            "audit_history": [{
                "audit_cycle": cycle,
                "window": [1, cycle],
                "findings": [{
                    "finding_id": "F-COV-FOOD",
                    "category": "coverage_gap",
                    "severity": "critical",
                    "description": "카테고리 'food' KU 0개",
                    "evidence": {"category": "food", "ku_count": 0},
                }],
                "recommendations": [],
                "policy_patches": [],
            }],
            "dispute_queue": [],
            "coverage_map": {},
            "novelty_history": [],
            "net_gap_changes": [],
        }

    def test_remodel_triggers_on_critical_audit(self, tmp_path):
        """critical finding + cycle % interval == 0 → remodel 실행."""
        from src.config import EvolverConfig, OrchestratorConfig
        from src.orchestrator import Orchestrator

        domain_path = tmp_path / "test-domain"
        state_dir = domain_path / "state"
        state_dir.mkdir(parents=True)
        for fname in ("knowledge-units.json", "gap-map.json", "domain-skeleton.json",
                       "metrics.json", "policies.json"):
            (state_dir / fname).write_text("{}", encoding="utf-8")

        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                audit_interval=10,
                bench_root=str(domain_path),
            ),
        )
        orch = Orchestrator(cfg)
        state = self._make_orch_state(cycle=10)

        orch._maybe_run_remodel(state, 10, cfg.orchestrator)

        # remodel 실행됨 → phase_number bump
        assert state["phase_number"] == 1
        assert len(state["phase_history"]) == 1
        assert state["phase_history"][0]["cycle"] == 10

    def test_remodel_skips_without_critical(self, tmp_path):
        """critical finding 없으면 remodel 스킵."""
        from src.config import EvolverConfig, OrchestratorConfig
        from src.orchestrator import Orchestrator

        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                audit_interval=10,
                bench_root=str(tmp_path),
            ),
        )
        orch = Orchestrator(cfg)
        state = self._make_orch_state(cycle=10)
        # finding 을 warning 으로 변경
        state["audit_history"][0]["findings"][0]["severity"] = "warning"

        orch._maybe_run_remodel(state, 10, cfg.orchestrator)
        assert state["phase_number"] == 0  # 변경 없음

    def test_remodel_skips_wrong_cycle(self, tmp_path):
        """cycle % interval != 0 이면 remodel 스킵."""
        from src.config import EvolverConfig, OrchestratorConfig
        from src.orchestrator import Orchestrator

        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                audit_interval=10,
                bench_root=str(tmp_path),
            ),
        )
        orch = Orchestrator(cfg)
        state = self._make_orch_state(cycle=7)

        orch._maybe_run_remodel(state, 7, cfg.orchestrator)
        assert state["phase_number"] == 0  # 변경 없음


# ---------------------------------------------------------------------------
# P2-B3: Phase transition (merge/split/reclassify 적용)
# ---------------------------------------------------------------------------

class TestPhaseTransition:
    def test_merge_applies_entity_key_change(self, tmp_path):
        """merge 제안 승인 → KU entity_key 통합."""
        from src.config import EvolverConfig, OrchestratorConfig
        from src.orchestrator import Orchestrator

        domain_path = tmp_path / "test-domain"
        state_dir = domain_path / "state"
        state_dir.mkdir(parents=True)
        for fname in ("knowledge-units.json", "gap-map.json", "domain-skeleton.json",
                       "metrics.json", "policies.json"):
            (state_dir / fname).write_text("{}", encoding="utf-8")

        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(bench_root=str(domain_path)),
        )
        orch = Orchestrator(cfg)
        state = {
            "knowledge_units": [
                {"ku_id": "KU-0001", "entity_key": "t:cat:a", "field": "p", "value": "1",
                 "status": "active", "evidence_links": ["EU-0001"], "confidence": 0.8},
                {"ku_id": "KU-0002", "entity_key": "t:cat:b", "field": "p", "value": "1",
                 "status": "active", "evidence_links": ["EU-0002"], "confidence": 0.8},
            ],
            "domain_skeleton": {"domain": "t", "categories": [{"slug": "cat"}]},
            "remodel_report": {
                "report_id": "RM-0001",
                "proposals": [{
                    "type": "merge",
                    "rationale": "50% overlap",
                    "target_entities": ["t:cat:a", "t:cat:b"],
                    "params": {"canonical_key": "t:cat:a"},
                    "expected_delta": {"metric": "entity_count", "before": 2, "after": 1},
                }],
                "approval": {"status": "approved"},
            },
            "phase_number": 0,
            "phase_history": [],
        }

        orch._apply_remodel_proposals(state, cycle_num=10)

        # KU-0002 의 entity_key 가 canonical 로 변경됨
        assert state["knowledge_units"][0]["entity_key"] == "t:cat:a"
        assert state["knowledge_units"][1]["entity_key"] == "t:cat:a"
        assert state["phase_number"] == 1

    def test_split_applies_geo_based_keys(self, tmp_path):
        """split 제안 승인 → geography 기반 entity_key 분리."""
        from src.config import EvolverConfig, OrchestratorConfig
        from src.orchestrator import Orchestrator

        domain_path = tmp_path / "test-domain"
        state_dir = domain_path / "state"
        state_dir.mkdir(parents=True)
        for fname in ("knowledge-units.json", "gap-map.json", "domain-skeleton.json",
                       "metrics.json", "policies.json"):
            (state_dir / fname).write_text("{}", encoding="utf-8")

        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(bench_root=str(domain_path)),
        )
        orch = Orchestrator(cfg)
        state = {
            "knowledge_units": [
                {"ku_id": "KU-0001", "entity_key": "t:cat:item", "field": "p", "value": "1",
                 "status": "active", "evidence_links": ["EU-0001"], "confidence": 0.8,
                 "axis_tags": {"geography": "tokyo"}},
                {"ku_id": "KU-0002", "entity_key": "t:cat:item", "field": "p", "value": "2",
                 "status": "active", "evidence_links": ["EU-0002"], "confidence": 0.8,
                 "axis_tags": {"geography": "osaka"}},
            ],
            "domain_skeleton": {"domain": "t", "categories": [{"slug": "cat"}]},
            "remodel_report": {
                "report_id": "RM-0002",
                "proposals": [{
                    "type": "split",
                    "rationale": "상반 geo tag",
                    "target_entities": ["t:cat:item"],
                    "params": {
                        "new_keys": ["t:cat:item-tokyo", "t:cat:item-osaka"],
                        "split_axis": "geography",
                        "axis_values": ["tokyo", "osaka"],
                    },
                    "expected_delta": {"metric": "entity_count", "before": 1, "after": 2},
                }],
                "approval": {"status": "approved"},
            },
            "phase_number": 0,
            "phase_history": [],
        }

        orch._apply_remodel_proposals(state, cycle_num=10)

        assert state["knowledge_units"][0]["entity_key"] == "t:cat:item-tokyo"
        assert state["knowledge_units"][1]["entity_key"] == "t:cat:item-osaka"
        assert state["phase_number"] == 1

    def test_reclassify_changes_category(self, tmp_path):
        """reclassify 제안 승인 → entity_key 의 category 변경."""
        from src.config import EvolverConfig, OrchestratorConfig
        from src.orchestrator import Orchestrator

        domain_path = tmp_path / "test-domain"
        state_dir = domain_path / "state"
        state_dir.mkdir(parents=True)
        for fname in ("knowledge-units.json", "gap-map.json", "domain-skeleton.json",
                       "metrics.json", "policies.json"):
            (state_dir / fname).write_text("{}", encoding="utf-8")

        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(bench_root=str(domain_path)),
        )
        orch = Orchestrator(cfg)
        state = {
            "knowledge_units": [
                {"ku_id": "KU-0001", "entity_key": "t:old-cat:item", "field": "p", "value": "1",
                 "status": "active", "evidence_links": ["EU-0001"], "confidence": 0.8},
            ],
            "domain_skeleton": {"domain": "t", "categories": [{"slug": "new-cat"}]},
            "remodel_report": {
                "report_id": "RM-0003",
                "proposals": [{
                    "type": "reclassify",
                    "rationale": "category 부정합",
                    "target_entities": ["t:old-cat:item"],
                    "params": {"from_category": "old-cat", "to_category": "new-cat"},
                    "expected_delta": {"metric": "category_validity", "before": 0.0, "after": 1.0},
                }],
                "approval": {"status": "approved"},
            },
            "phase_number": 0,
            "phase_history": [],
        }

        orch._apply_remodel_proposals(state, cycle_num=10)

        assert state["knowledge_units"][0]["entity_key"] == "t:new-cat:item"
        assert state["phase_number"] == 1


# ---------------------------------------------------------------------------
# P2-B4: Rollback (rejection → state diff = ∅)
# ---------------------------------------------------------------------------

class TestRollback:
    def test_rejection_no_state_change(self, tmp_path):
        """remodel 거부 → state 무변경 (phase_number, KU entity_key 불변)."""
        from src.config import EvolverConfig, OrchestratorConfig
        from src.orchestrator import Orchestrator

        domain_path = tmp_path / "test-domain"
        state_dir = domain_path / "state"
        state_dir.mkdir(parents=True)
        for fname in ("knowledge-units.json", "gap-map.json", "domain-skeleton.json",
                       "metrics.json", "policies.json"):
            (state_dir / fname).write_text("{}", encoding="utf-8")

        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                audit_interval=10,
                bench_root=str(domain_path),
            ),
        )
        orch = Orchestrator(cfg)
        orch._hitl_response = {"action": "reject", "reason": "불필요"}

        state = {
            "knowledge_units": [
                {"ku_id": "KU-0001", "entity_key": "t:cat:a", "field": "p", "value": "1",
                 "status": "active", "evidence_links": ["EU-0001"], "confidence": 0.8,
                 "observed_at": "2026-04-12"},
                {"ku_id": "KU-0002", "entity_key": "t:cat:b", "field": "p", "value": "1",
                 "status": "active", "evidence_links": ["EU-0002"], "confidence": 0.8,
                 "observed_at": "2026-04-12"},
            ],
            "gap_map": [],
            "domain_skeleton": {"domain": "t", "categories": [{"slug": "cat"}], "axes": [], "aliases": {}},
            "metrics": {"cycle": 10, "rates": {}},
            "policies": {},
            "current_cycle": 10,
            "hitl_pending": None,
            "phase_number": 0,
            "phase_history": [],
            "remodel_report": None,
            "audit_history": [{
                "audit_cycle": 10,
                "window": [1, 10],
                "findings": [{
                    "finding_id": "F-COV-X",
                    "category": "coverage_gap",
                    "severity": "critical",
                    "description": "test",
                    "evidence": {"category": "x", "ku_count": 0},
                }],
                "recommendations": [],
                "policy_patches": [],
            }],
        }

        # 원본 entity_key 보존 확인용
        original_ek_0 = state["knowledge_units"][0]["entity_key"]
        original_ek_1 = state["knowledge_units"][1]["entity_key"]

        orch._maybe_run_remodel(state, 10, cfg.orchestrator)

        # 거부 → state 무변경
        assert state["phase_number"] == 0
        assert state["knowledge_units"][0]["entity_key"] == original_ek_0
        assert state["knowledge_units"][1]["entity_key"] == original_ek_1
        assert len(state["phase_history"]) == 0

    def test_rollback_payload_has_skeleton_snapshot(self):
        """rollback_payload 에 skeleton_snapshot 이 포함."""
        kus = [
            {"ku_id": "KU-0001", "entity_key": "t:cat:a", "field": "p",
             "value": "1", "status": "active", "evidence_links": ["EU-0001"], "confidence": 0.8},
        ]
        state = _make_state(kus=kus)
        proposals = [{"type": "merge", "target_entities": ["t:cat:a"], "params": {}}]
        payload = _build_rollback_payload(state, proposals)
        assert "skeleton_snapshot" in payload
        assert payload["skeleton_snapshot"] == state["domain_skeleton"]


# ---------------------------------------------------------------------------
# P2-C5: S7 trigger 경로 테스트 (저novelty → audit → remodel)
# ---------------------------------------------------------------------------

class TestS7TriggerPath:
    """S7 시나리오: 저novelty 5 cycle → plateau 감지 → audit 발동 → remodel 제안.

    여기서는 trigger 경로만 assert. coverage 근거는 P4-C에서.
    """

    def test_plateau_triggers_audit_which_triggers_remodel(self, tmp_path):
        """plateau 감지 → audit critical finding → remodel 실행."""
        from src.config import EvolverConfig, OrchestratorConfig
        from src.orchestrator import Orchestrator
        from src.utils.plateau_detector import PlateauDetector

        domain_path = tmp_path / "test-domain"
        state_dir = domain_path / "state"
        state_dir.mkdir(parents=True)
        for fname in ("knowledge-units.json", "gap-map.json", "domain-skeleton.json",
                       "metrics.json", "policies.json"):
            (state_dir / fname).write_text("{}", encoding="utf-8")

        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                audit_interval=5,
                plateau_window=5,
                bench_root=str(domain_path),
            ),
        )
        orch = Orchestrator(cfg)

        # 5 cycle 동안 동일 KU/GU 상태 (plateau)
        state = {
            "knowledge_units": [
                {"ku_id": "KU-0001", "entity_key": "t:transport:a", "field": "p",
                 "value": "1", "status": "active", "evidence_links": ["EU-0001"],
                 "confidence": 0.8, "observed_at": "2026-04-12"},
            ],
            "gap_map": [],
            "domain_skeleton": {
                "domain": "t",
                "categories": [
                    {"slug": "transport", "description": ""},
                    {"slug": "food", "description": ""},
                ],
                "axes": [],
                "aliases": {},
            },
            "metrics": {"cycle": 5, "rates": {}},
            "policies": {},
            "current_cycle": 5,
            "hitl_pending": None,
            "phase_number": 0,
            "phase_history": [],
            "remodel_report": None,
            "conflict_ledger": [],
            "dispute_queue": [],
            "coverage_map": {},
            "novelty_history": [],
            "net_gap_changes": [],
        }

        # plateau detector에 5 cycle 동일 상태 기록
        detector = PlateauDetector(window=5)
        for c in range(1, 6):
            detector.record(c, state)
        assert detector.is_plateau(), "5 cycle 동일 → plateau"

        # audit 실행 → critical finding (food 카테고리 KU 0개)
        from src.nodes.audit import run_audit
        trajectory = [
            {"cycle": c, "ku_active": 1, "llm_calls": 5, "avg_confidence": 0.8,
             "multi_evidence_rate": 0.0}
            for c in range(1, 6)
        ]
        audit_report = run_audit(state, trajectory, audit_cycle=5)
        # food 카테고리 KU 0개 → critical coverage_gap
        critical_findings = [
            f for f in audit_report["findings"] if f.get("severity") == "critical"
        ]
        assert len(critical_findings) >= 1, "food 카테고리 KU 0개 → critical finding"

        # audit_history에 추가
        state["audit_history"] = [audit_report]

        # remodel 트리거 (cycle=5, interval=5)
        orch._maybe_run_remodel(state, 5, cfg.orchestrator)

        # remodel 실행됨 → phase bump
        assert state["phase_number"] == 1, "remodel 제안 → 자동 승인 → phase bump"
        assert len(state["phase_history"]) == 1
        assert state["phase_history"][0]["cycle"] == 5

    def test_plateau_without_critical_skips_remodel(self, tmp_path):
        """plateau 감지되어도 critical finding 없으면 remodel 스킵."""
        from src.config import EvolverConfig, OrchestratorConfig
        from src.orchestrator import Orchestrator

        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                audit_interval=5,
                bench_root=str(tmp_path),
            ),
        )
        orch = Orchestrator(cfg)

        state = {
            "knowledge_units": [
                {"ku_id": "KU-0001", "entity_key": "t:cat:a", "field": "p",
                 "value": "1", "status": "active", "evidence_links": ["EU-0001"],
                 "confidence": 0.8, "observed_at": "2026-04-12"},
            ],
            "gap_map": [],
            "domain_skeleton": {
                "domain": "t",
                "categories": [{"slug": "cat", "description": ""}],
                "axes": [],
                "aliases": {},
            },
            "metrics": {"cycle": 5, "rates": {}},
            "policies": {},
            "current_cycle": 5,
            "hitl_pending": None,
            "phase_number": 0,
            "phase_history": [],
            "remodel_report": None,
            "audit_history": [{
                "audit_cycle": 5,
                "window": [1, 5],
                "findings": [{
                    "finding_id": "F-COV-01",
                    "category": "axis_imbalance",
                    "severity": "warning",  # warning, not critical
                    "description": "균등도 부족",
                    "evidence": {},
                }],
                "recommendations": [],
                "policy_patches": [],
            }],
        }

        orch._maybe_run_remodel(state, 5, cfg.orchestrator)
        assert state["phase_number"] == 0, "critical 없으면 remodel 스킵"

    def test_s7_full_path_plateau_to_remodel_proposal(self):
        """S7 전체 경로: plateau state → audit findings → remodel proposals 생성."""
        # 1. 저novelty state 구성 (1개 entity, 2개 category 중 1개만 채움)
        kus = [
            {"ku_id": "KU-0001", "entity_key": "t:transport:a", "field": "price",
             "value": "1000", "status": "active", "evidence_links": ["EU-0001"],
             "confidence": 0.8, "observed_at": "2026-04-12"},
        ]
        skeleton = {
            "domain": "t",
            "categories": [
                {"slug": "transport", "description": ""},
                {"slug": "food", "description": ""},
            ],
            "axes": [],
            "aliases": {},
        }

        # 2. audit 실행
        from src.nodes.audit import run_audit
        state = {
            "knowledge_units": kus,
            "gap_map": [],
            "domain_skeleton": skeleton,
            "policies": {},
        }
        trajectory = [
            {"cycle": c, "ku_active": 1, "llm_calls": 5, "avg_confidence": 0.8,
             "multi_evidence_rate": 0.0}
            for c in range(1, 6)
        ]
        audit_report = run_audit(state, trajectory, audit_cycle=5)

        # 3. remodel 실행
        report = run_remodel(state, audit_report)

        # 4. gap_rule 제안이 food 카테고리에 대해 생성되는지 확인
        gap_rules = [p for p in report["proposals"] if p["type"] == "gap_rule"]
        assert len(gap_rules) >= 1, "food 카테고리 critical gap → gap_rule 제안"
        assert any("food" in str(p.get("params", {})) for p in gap_rules)
