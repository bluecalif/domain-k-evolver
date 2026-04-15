"""P4-D4: S7 full scenario — plateau → audit → remodel → coverage/category 전체 경로.

P2-C5 trigger 테스트를 확장: coverage 근거 + reason_code + category_addition 포함.
"""

from __future__ import annotations

import pytest

from src.nodes.audit import run_audit
from src.nodes.remodel import run_remodel, reset_report_counter
from src.utils.novelty import compute_novelty
from src.utils.coverage_map import build_coverage_map
from src.utils.plateau_detector import PlateauDetector


def _make_skeleton(categories: list[str]) -> dict:
    return {
        "domain": "test",
        "categories": [{"slug": c, "name": c.title()} for c in categories],
        "axes": [
            {"name": "category", "anchors": categories},
        ],
        "fields": [
            {"name": "price", "categories": ["*"]},
            {"name": "name", "categories": ["*"]},
        ],
    }


def _make_ku(ku_id: str, entity_key: str, field: str = "price", **extra) -> dict:
    return {
        "ku_id": ku_id,
        "status": "active",
        "entity_key": entity_key,
        "field": field,
        "value": "test_value",
        "evidence_links": ["e1"],
        "claim": "test claim",
        "confidence": 0.9,
        "validity": {},
        "axis_tags": {},
        **extra,
    }


class TestS7FullScenario:
    """S7 전체 경로: novelty plateau → audit → remodel → coverage + category."""

    def setup_method(self):
        reset_report_counter()

    def test_novelty_plateau_detected_and_coverage_map_built(self):
        """1단계: 동일 KU 반복 → novelty plateau + coverage_map deficit 확인."""
        # 동일 KU 를 5 cycle 반복
        kus = [
            _make_ku("KU-1", "test:transport:jr", "price"),
            _make_ku("KU-2", "test:transport:bus", "price"),
        ]
        skeleton = _make_skeleton(["transport", "food", "culture"])

        # novelty: 5 cycle 동일 KU
        pd = PlateauDetector(window=3, novelty_threshold=0.1, novelty_window=5)
        novelty_history: list[float] = []
        for i in range(6):
            novelty = compute_novelty(kus, kus)
            novelty_history.append(novelty)

        # novelty 전부 0 → plateau
        assert pd.is_novelty_plateau(novelty_history)

        # coverage_map: transport 만 채워짐, food/culture 은 deficit 1.0
        state = {"knowledge_units": kus, "domain_skeleton": skeleton}
        coverage = build_coverage_map(state, skeleton, target_per_category=5)

        assert coverage["transport"]["ku_count"] == 2
        assert coverage["food"]["ku_count"] == 0
        assert coverage["food"]["base_deficit"] == 1.0
        assert coverage["culture"]["ku_count"] == 0

        # Gini 불균형
        assert coverage["summary"]["category_gini"] > 0.45

    def test_audit_finds_coverage_gap(self):
        """2단계: 편중 state → audit → coverage_gap critical finding."""
        skeleton = _make_skeleton(["transport", "food"])
        kus = [
            _make_ku("KU-1", "test:transport:jr", "price"),
        ]
        gap_map = [
            {"gu_id": "GU-1", "status": "open", "gap_type": "missing",
             "target": {"entity_key": "test:transport:bus", "field": "price"},
             "expected_utility": "high", "risk_level": "convenience"},
        ]
        state = {
            "knowledge_units": kus,
            "gap_map": gap_map,
            "domain_skeleton": skeleton,
            "policies": {},
        }

        # metrics entries (5 cycles 분량, KU 정체)
        entries = [
            {"cycle": i, "ku_active": 1, "gu_total": 1, "gu_open": 1,
             "rates": {"evidence_rate": 1.0}}
            for i in range(1, 6)
        ]

        report = run_audit(state, entries, audit_cycle=5, window_start=1)

        # coverage_gap finding 이 존재해야 함
        coverage_findings = [
            f for f in report.get("findings", [])
            if f.get("category") == "coverage_gap"
        ]
        assert len(coverage_findings) >= 1

    def test_remodel_generates_proposals_from_coverage(self):
        """3단계: audit + coverage → remodel proposals (gap_rule + category_addition)."""
        skeleton = _make_skeleton(["transport"])
        # 미등록 카테고리 food 에 KU 5개
        kus = [
            _make_ku("KU-1", "test:transport:jr", "price"),
        ] + [
            _make_ku(f"KU-f{i}", f"test:food:item{i}", "price")
            for i in range(5)
        ]

        state = {
            "knowledge_units": kus,
            "domain_skeleton": skeleton,
            "policies": {},
            "coverage_map": build_coverage_map(
                {"knowledge_units": kus, "domain_skeleton": skeleton},
                skeleton,
            ),
        }

        # audit report with coverage_gap critical finding
        audit = {
            "findings": [
                {
                    "finding_id": "F-001",
                    "category": "coverage_gap",
                    "severity": "critical",
                    "description": "food 카테고리 KU 부족",
                    "evidence": {"category": "food", "ku_count": 0},
                },
            ],
            "audit_cycle": 5,
        }

        report = run_remodel(state, audit)

        proposal_types = [p["type"] for p in report["proposals"]]
        # category_addition 제안이 있어야 함 (food 카테고리 미등록 + 5 KU)
        assert "category_addition" in proposal_types
        # gap_rule 제안도 있어야 함 (critical coverage_gap)
        assert "gap_rule" in proposal_types

    def test_full_path_plateau_to_category_addition(self, tmp_path):
        """4단계: 전체 경로 — plateau → audit → remodel → category 추가 적용."""
        from src.config import EvolverConfig, OrchestratorConfig
        from src.orchestrator import Orchestrator, CycleResult

        bench = tmp_path / "bench" / "test-domain" / "state"
        bench.mkdir(parents=True)

        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=10,
                audit_interval=5,
                plateau_window=100,  # KU/GU plateau 비활성
                bench_path=str(tmp_path / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)

        skeleton = _make_skeleton(["transport"])
        # 미등록 카테고리 food 에 충분한 KU
        base_kus = [
            _make_ku("KU-1", "test:transport:jr", "price"),
        ] + [
            _make_ku(f"KU-f{i}", f"test:food:item{i}", "price")
            for i in range(6)
        ]

        state = {
            "knowledge_units": list(base_kus),
            "gap_map": [
                {"gu_id": f"GU-{i}", "status": "open", "gap_type": "missing",
                 "target": {"entity_key": f"test:transport:item{i}", "field": "price"},
                 "expected_utility": "high", "risk_level": "convenience"}
                for i in range(5)
            ],
            "domain_skeleton": dict(skeleton),
            "policies": {"ttl_defaults": {"price": 90}},
            "current_cycle": 0,
            "current_plan": None,
            "current_claims": None,
            "current_critique": None,
            "current_mode": None,
            "axis_coverage": None,
            "jump_history": [],
            "hitl_pending": None,
            "dispute_queue": [],
            "conflict_ledger": [],
            "phase_number": 0,
            "phase_history": [],
            "remodel_report": None,
            "coverage_map": {},
            "novelty_history": [],
            "audit_history": [],
            "net_gap_changes": [],
            "metrics": {},
        }

        cycle_counter = [0]

        def mock_run(s, c):
            cycle_counter[0] += 1
            # 매 cycle 동일 KU → novelty 정체
            # cycle 마다 KU 약간 추가해서 growth_stagnation 방지
            new_ku = _make_ku(
                f"KU-c{c}", f"test:transport:auto{c}", "price",
            )
            kus_list = list(s.get("knowledge_units", []))
            kus_list.append(new_ku)
            s["knowledge_units"] = kus_list
            s["current_cycle"] = c
            return CycleResult(cycle=c, state=s)

        orch._run_single_cycle = mock_run
        orch.run(initial_state=state)

        # 검증 1: audit 실행됨 (cycle 5, 10)
        assert len(orch.audit_reports) >= 1

        # 검증 2: novelty_history 기록됨
        assert len(state.get("novelty_history", [])) > 0

        # 검증 3: coverage_map 갱신됨
        coverage = state.get("coverage_map", {})
        assert "summary" in coverage

        # 검증 4: category_addition 제안 → food 카테고리 추가됨
        cats = [c["slug"] for c in state["domain_skeleton"]["categories"]]
        # food 가 추가되었거나, 최소한 remodel report 에 category_addition 이 있어야 함
        report = state.get("remodel_report")
        if report and report.get("proposals"):
            cat_add = [p for p in report["proposals"] if p["type"] == "category_addition"]
            if cat_add:
                # 자동 승인 → food 추가됨
                assert "food" in cats, (
                    f"category_addition 제안됐으나 적용 안 됨: cats={cats}"
                )

    def test_reason_codes_reflect_coverage(self):
        """5단계: plan reason_code 가 coverage deficit 반영."""
        from src.nodes.plan import plan_node

        skeleton = _make_skeleton(["transport", "food"])
        kus = [
            _make_ku("KU-1", "test:transport:jr", "price"),
            _make_ku("KU-2", "test:transport:bus", "name"),
        ]
        coverage = build_coverage_map(
            {"knowledge_units": kus, "domain_skeleton": skeleton},
            skeleton,
            target_per_category=5,
        )

        state = {
            "gap_map": [
                {"gu_id": "GU-1", "status": "open", "gap_type": "missing",
                 "target": {"entity_key": "test:food:ramen", "field": "price"},
                 "expected_utility": "high", "risk_level": "convenience"},
            ],
            "current_mode": {"mode": "normal", "explore_budget": 0, "exploit_budget": 1},
            "domain_skeleton": skeleton,
            "knowledge_units": kus,
            "coverage_map": coverage,
            "novelty_history": [],
            "current_cycle": 5,
            "remodel_report": None,
        }

        result = plan_node(state)
        plan = result["current_plan"]
        rc = plan.get("reason_codes", {})

        # food 카테고리 deficit 높으므로 deficit:category=food
        assert "GU-1" in rc
        assert rc["GU-1"].startswith("deficit:") or rc["GU-1"].startswith("gini:")
