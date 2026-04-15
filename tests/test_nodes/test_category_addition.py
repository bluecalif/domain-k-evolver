"""P4-C1/C2/C3 + D5: category_addition 보수적 조건 테스트."""

from __future__ import annotations

import pytest

from src.nodes.remodel import (
    _propose_category_additions,
    run_remodel,
    reset_report_counter,
    _CATEGORY_ADDITION_MIN_KUS,
)


def _make_skeleton(categories: list[str]) -> dict:
    return {
        "domain": "test",
        "categories": [{"slug": c, "name": c.title()} for c in categories],
        "axes": [],
        "fields": [],
    }


def _make_ku(ku_id: str, entity_key: str, field: str = "price") -> dict:
    return {
        "ku_id": ku_id,
        "status": "active",
        "entity_key": entity_key,
        "field": field,
        "value": "test",
        "evidence_links": ["e1"],
        "claim": "test claim",
        "confidence": 0.9,
        "validity": {},
    }


class TestProposeCategoryAdditions:
    """_propose_category_additions 단위 테스트."""

    def test_no_proposal_when_all_valid(self):
        """모든 KU 가 유효 카테고리 → 제안 0."""
        skeleton = _make_skeleton(["transport", "food"])
        kus = [
            _make_ku("KU-1", "d:transport:jr"),
            _make_ku("KU-2", "d:food:ramen"),
        ]
        proposals = _propose_category_additions(kus, skeleton)
        assert len(proposals) == 0

    def test_no_proposal_below_threshold(self):
        """미등록 카테고리 KU 가 4개 (< 5) → 제안 0."""
        skeleton = _make_skeleton(["transport"])
        kus = [_make_ku(f"KU-{i}", f"d:newcat:item{i}") for i in range(4)]
        proposals = _propose_category_additions(kus, skeleton)
        assert len(proposals) == 0

    def test_proposal_at_threshold(self):
        """미등록 카테고리 KU 가 5개 (= 임계치) → 제안 1."""
        skeleton = _make_skeleton(["transport"])
        kus = [_make_ku(f"KU-{i}", f"d:newcat:item{i}") for i in range(5)]
        proposals = _propose_category_additions(kus, skeleton)
        assert len(proposals) == 1
        assert proposals[0]["type"] == "category_addition"
        assert proposals[0]["params"]["new_category"]["slug"] == "newcat"
        assert proposals[0]["params"]["evidence_ku_count"] == 5

    def test_proposal_above_threshold(self):
        """미등록 카테고리 KU 가 8개 (> 5) → 제안 1."""
        skeleton = _make_skeleton(["transport"])
        kus = [_make_ku(f"KU-{i}", f"d:newcat:item{i}") for i in range(8)]
        proposals = _propose_category_additions(kus, skeleton)
        assert len(proposals) == 1
        assert proposals[0]["params"]["evidence_ku_count"] == 8

    def test_max_one_per_cycle(self):
        """여러 미등록 카테고리가 임계치 충족해도 사이클당 1개만."""
        skeleton = _make_skeleton(["transport"])
        kus = (
            [_make_ku(f"KU-a{i}", f"d:catA:item{i}") for i in range(6)]
            + [_make_ku(f"KU-b{i}", f"d:catB:item{i}") for i in range(7)]
        )
        proposals = _propose_category_additions(kus, skeleton)
        assert len(proposals) == 1
        # KU 많은 catB 가 선택되어야 함
        assert proposals[0]["params"]["new_category"]["slug"] == "catB"

    def test_inactive_kus_excluded(self):
        """inactive KU 는 카운트에서 제외."""
        skeleton = _make_skeleton(["transport"])
        kus = [
            _make_ku(f"KU-{i}", f"d:newcat:item{i}") for i in range(4)
        ] + [
            {"ku_id": "KU-x", "status": "superseded", "entity_key": "d:newcat:itemX",
             "field": "price"},
        ]
        proposals = _propose_category_additions(kus, skeleton)
        assert len(proposals) == 0  # 4 active < 5

    def test_category_name_formatting(self):
        """카테고리 slug → name 변환 (하이픈/언더스코어 → 공백 + title case)."""
        skeleton = _make_skeleton(["transport"])
        kus = [_make_ku(f"KU-{i}", f"d:local-food:item{i}") for i in range(5)]
        proposals = _propose_category_additions(kus, skeleton)
        assert proposals[0]["params"]["new_category"]["name"] == "Local Food"


class TestCategoryAdditionInRunRemodel:
    """run_remodel 에서 category_addition 통합 테스트."""

    def setup_method(self):
        reset_report_counter()

    def test_category_addition_in_report(self):
        """run_remodel 결과에 category_addition 포함."""
        skeleton = _make_skeleton(["transport"])
        kus = [_make_ku(f"KU-{i}", f"d:newcat:item{i}") for i in range(6)]
        state = {
            "knowledge_units": kus,
            "domain_skeleton": skeleton,
            "policies": {},
            "coverage_map": None,
        }
        audit = {"findings": [], "audit_cycle": 5}
        report = run_remodel(state, audit)

        cat_proposals = [p for p in report["proposals"] if p["type"] == "category_addition"]
        assert len(cat_proposals) == 1

    def test_schema_validates(self):
        """category_addition 포함 report 가 schema validate."""
        import json
        from jsonschema import validate

        schema_path = "C:/Users/User/Learning/KBs-2026/domain-k-evolver/schemas/remodel_report.schema.json"
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)

        skeleton = _make_skeleton(["transport"])
        kus = [_make_ku(f"KU-{i}", f"d:newcat:item{i}") for i in range(5)]
        state = {
            "knowledge_units": kus,
            "domain_skeleton": skeleton,
            "policies": {},
            "coverage_map": None,
        }
        audit = {"findings": [], "audit_cycle": 5}
        report = run_remodel(state, audit)

        validate(instance=report, schema=schema)


class TestCategoryAdditionApply:
    """P4-C3: orchestrator _apply_remodel_proposals category_addition 핸들러."""

    def test_category_added_to_skeleton(self, tmp_path):
        """승인된 category_addition → skeleton categories 에 추가."""
        from src.orchestrator import Orchestrator
        from src.config import EvolverConfig, OrchestratorConfig

        bench = tmp_path / "bench" / "test-domain" / "state"
        bench.mkdir(parents=True)

        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                bench_path=str(tmp_path / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)

        state = {
            "knowledge_units": [],
            "domain_skeleton": {
                "domain": "test",
                "categories": [{"slug": "transport", "name": "Transport"}],
            },
            "remodel_report": {
                "report_id": "RM-0001",
                "proposals": [
                    {
                        "type": "category_addition",
                        "rationale": "test",
                        "target_entities": ["test:food:*"],
                        "params": {
                            "new_category": {"slug": "food", "name": "Food"},
                            "evidence_ku_count": 6,
                        },
                        "expected_delta": {"metric": "category_count", "before": 1, "after": 2},
                    }
                ],
            },
            "phase_number": 0,
            "phase_history": [],
        }

        orch._apply_remodel_proposals(state, 10)

        cats = [c["slug"] for c in state["domain_skeleton"]["categories"]]
        assert "food" in cats
        assert state["phase_number"] == 1

    def test_duplicate_category_not_added(self, tmp_path):
        """이미 존재하는 카테고리는 중복 추가 안 됨."""
        from src.orchestrator import Orchestrator
        from src.config import EvolverConfig, OrchestratorConfig

        bench = tmp_path / "bench" / "test-domain" / "state"
        bench.mkdir(parents=True)

        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                bench_path=str(tmp_path / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)

        state = {
            "knowledge_units": [],
            "domain_skeleton": {
                "domain": "test",
                "categories": [
                    {"slug": "transport", "name": "Transport"},
                    {"slug": "food", "name": "Food"},
                ],
            },
            "remodel_report": {
                "report_id": "RM-0001",
                "proposals": [
                    {
                        "type": "category_addition",
                        "rationale": "test",
                        "target_entities": ["test:food:*"],
                        "params": {
                            "new_category": {"slug": "food", "name": "Food"},
                            "evidence_ku_count": 6,
                        },
                        "expected_delta": {"metric": "category_count", "before": 2, "after": 3},
                    }
                ],
            },
            "phase_number": 0,
            "phase_history": [],
        }

        orch._apply_remodel_proposals(state, 10)

        cats = [c["slug"] for c in state["domain_skeleton"]["categories"]]
        assert cats.count("food") == 1  # 중복 없음
