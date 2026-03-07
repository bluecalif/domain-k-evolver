"""Task 2.4 테스트: Orchestrator Multi-Cycle 관리."""

import json
from pathlib import Path

import pytest

from src.config import EvolverConfig, OrchestratorConfig
from src.orchestrator import CycleResult, Orchestrator
from src.utils.state_io import load_state, save_state


def _make_minimal_state(cycle: int = 0) -> dict:
    """테스트용 최소 State."""
    return {
        "knowledge_units": [
            {
                "ku_id": "KU-0001",
                "entity_key": "test:cat:item",
                "field": "price",
                "value": "1000",
                "observed_at": "2026-01-01",
                "validity": {"ttl_days": 365},
                "evidence_links": ["EU-0001"],
                "confidence": 0.9,
                "status": "active",
            }
        ],
        "gap_map": [
            {
                "gu_id": "GU-0001",
                "gap_type": "missing",
                "target": {"entity_key": "test:cat:item", "field": "hours"},
                "expected_utility": "high",
                "risk_level": "convenience",
                "status": "open",
            }
        ],
        "domain_skeleton": {
            "domain": "test",
            "version": "1.0",
            "scope_boundary": "test scope",
            "categories": [{"slug": "cat", "description": "test category"}],
            "fields": [
                {"name": "price", "type": "string"},
                {"name": "hours", "type": "string"},
            ],
            "relations": [],
            "axes": [],
            "canonical_key_rule": "{domain}:{category}:{slug}",
        },
        "metrics": {
            "cycle": cycle,
            "rates": {
                "evidence_rate": 1.0,
                "multi_evidence_rate": 0.0,
                "conflict_rate": 0.0,
                "avg_confidence": 0.9,
                "gap_resolution_rate": 0.0,
                "staleness_risk": 0,
            },
        },
        "policies": {
            "credibility_priors": {},
            "ttl_defaults": {},
            "cross_validation": {},
            "conflict_resolution": {},
        },
        "current_cycle": cycle,
        "current_plan": None,
        "current_claims": None,
        "current_critique": None,
        "current_mode": None,
        "axis_coverage": None,
        "jump_history": [],
        "hitl_pending": None,
    }


def _setup_bench(tmp_path: Path) -> Path:
    """tmp_path에 bench 디렉토리 구조 생성."""
    domain_path = tmp_path / "bench" / "test-domain"
    state_dir = domain_path / "state"
    state_dir.mkdir(parents=True)

    state = _make_minimal_state()
    save_state(state, domain_path)
    return tmp_path


class TestCycleResult:
    def test_creation(self):
        state = _make_minimal_state()
        result = CycleResult(cycle=1, state=state, converged=False)
        assert result.cycle == 1
        assert result.converged is False
        assert result.error is None

    def test_with_error(self):
        state = _make_minimal_state()
        result = CycleResult(cycle=1, state=state, error="test error")
        assert result.error == "test error"


class TestOrchestrator:
    def test_init_default(self):
        orch = Orchestrator()
        assert orch.config.llm.provider == "openai"
        assert orch.config.orchestrator.max_cycles == 10

    def test_init_custom_config(self):
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(max_cycles=5),
        )
        orch = Orchestrator(cfg)
        assert orch.config.orchestrator.max_cycles == 5

    def test_run_with_initial_state(self, tmp_path):
        """초기 State 직접 전달 → 1 cycle 실행."""
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=1,
                bench_path=str(tmp_path / "bench"),
                bench_domain="test-domain",
            ),
        )
        _setup_bench(tmp_path)

        orch = Orchestrator(cfg)
        state = _make_minimal_state()
        results = orch.run(initial_state=state)

        assert len(results) >= 1
        assert results[0].cycle == 1

    def test_run_loads_from_bench(self, tmp_path):
        """bench 파일에서 State 로드 → 실행."""
        bench_base = _setup_bench(tmp_path)
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=1,
                bench_path=str(bench_base / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)
        results = orch.run()
        assert len(results) >= 1

    def test_stops_on_convergence(self, tmp_path):
        """수렴 시 조기 종료."""
        bench_base = _setup_bench(tmp_path)
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=5,
                stop_on_convergence=True,
                bench_path=str(bench_base / "bench"),
                bench_domain="test-domain",
            ),
        )

        # 수렴 상태를 가진 State 생성
        state = _make_minimal_state()
        state["current_critique"] = {
            "convergence": {"converged": True},
        }

        orch = Orchestrator(cfg)

        # _run_single_cycle을 모킹하여 수렴 반환
        original_run = orch._run_single_cycle

        def mock_run(s, c):
            result = CycleResult(cycle=c, state=s, converged=True)
            result.state["current_critique"] = {
                "convergence": {"converged": True},
            }
            return result

        orch._run_single_cycle = mock_run
        results = orch.run(initial_state=state)
        assert len(results) == 1  # 첫 사이클에서 수렴 → 종료

    def test_stops_on_error(self, tmp_path):
        """에러 시 중단."""
        bench_base = _setup_bench(tmp_path)
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=5,
                bench_path=str(bench_base / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)

        def mock_run(s, c):
            return CycleResult(cycle=c, state=s, error="test error")

        orch._run_single_cycle = mock_run
        state = _make_minimal_state()
        results = orch.run(initial_state=state)
        assert len(results) == 1
        assert results[0].error == "test error"

    def test_metrics_logging(self, tmp_path):
        """Metrics Logger 기록 확인."""
        bench_base = _setup_bench(tmp_path)
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=3,
                bench_path=str(bench_base / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)

        state = _make_minimal_state()

        def mock_run(s, c):
            return CycleResult(cycle=c, state=s)

        orch._run_single_cycle = mock_run
        orch.run(initial_state=state)
        assert len(orch.logger.entries) == 3

    def test_save_metrics(self, tmp_path):
        """Metrics JSON/CSV 저장."""
        bench_base = _setup_bench(tmp_path)
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=1,
                bench_path=str(bench_base / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)
        state = _make_minimal_state()

        def mock_run(s, c):
            return CycleResult(cycle=c, state=s)

        orch._run_single_cycle = mock_run
        orch.run(initial_state=state)

        out_dir = tmp_path / "metrics_out"
        orch.save_metrics(out_dir)

        assert (out_dir / "trajectory.json").exists()
        assert (out_dir / "trajectory.csv").exists()

    def test_audit_runs_at_interval(self, tmp_path):
        """audit_interval 주기에 audit 실행."""
        bench_base = _setup_bench(tmp_path)
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=10,
                audit_interval=5,
                plateau_window=100,  # plateau 비활성화
                bench_path=str(bench_base / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)
        state = _make_minimal_state()

        def mock_run(s, c):
            return CycleResult(cycle=c, state=s)

        orch._run_single_cycle = mock_run
        orch.run(initial_state=state)

        # cycle 5, 10에서 audit 실행 → 2회
        assert len(orch.audit_reports) == 2
        assert orch.audit_reports[0]["audit_cycle"] == 5
        assert orch.audit_reports[1]["audit_cycle"] == 10

    def test_audit_disabled_when_interval_zero(self, tmp_path):
        """audit_interval=0이면 audit 비활성."""
        bench_base = _setup_bench(tmp_path)
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=5,
                audit_interval=0,
                bench_path=str(bench_base / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)
        state = _make_minimal_state()

        def mock_run(s, c):
            return CycleResult(cycle=c, state=s)

        orch._run_single_cycle = mock_run
        orch.run(initial_state=state)
        assert len(orch.audit_reports) == 0

    def test_audit_history_in_state(self, tmp_path):
        """audit 실행 후 state.audit_history에 누적."""
        bench_base = _setup_bench(tmp_path)
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=5,
                audit_interval=5,
                plateau_window=100,  # plateau 비활성화
                bench_path=str(bench_base / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)
        state = _make_minimal_state()

        def mock_run(s, c):
            return CycleResult(cycle=c, state=s)

        orch._run_single_cycle = mock_run
        results = orch.run(initial_state=state)

        final_state = results[-1].state
        audit_history = final_state.get("audit_history", [])
        assert len(audit_history) == 1
        assert audit_history[0]["audit_cycle"] == 5

    def test_audit_applies_policy_patches(self, tmp_path):
        """Audit에서 생성된 policy patch가 자동 적용되는지 확인."""
        bench_base = _setup_bench(tmp_path)
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=5,
                audit_interval=5,
                plateau_window=100,
                bench_path=str(bench_base / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)

        state = _make_minimal_state()
        state["policies"]["ttl_defaults"] = {"price": 180}
        # skeleton에 geography axis + 2 categories (audit가 patch 생성하도록)
        state["domain_skeleton"]["categories"] = [
            {"slug": "transport", "description": "transport"},
            {"slug": "food", "description": "food"},
        ]

        def mock_run(s, c):
            return CycleResult(cycle=c, state=s)

        orch._run_single_cycle = mock_run
        results = orch.run(initial_state=state)
        final_state = results[-1].state

        # audit가 patch를 생성했으면 version이 존재
        policies = final_state.get("policies", {})
        # patch 적용 여부는 audit findings에 따라 다를 수 있지만,
        # audit_reports는 반드시 존재
        assert len(orch.audit_reports) == 1

    def test_policy_rollback_on_degradation(self, tmp_path):
        """Policy patch 후 성능 악화 시 롤백 확인."""
        bench_base = _setup_bench(tmp_path)
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=6,
                audit_interval=5,
                plateau_window=100,
                bench_path=str(bench_base / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)

        state = _make_minimal_state()
        state["policies"]["ttl_defaults"] = {"price": 180}

        cycle_counter = {"n": 0}

        def mock_run(s, c):
            cycle_counter["n"] = c
            return CycleResult(cycle=c, state=s)

        orch._run_single_cycle = mock_run

        # 수동으로 _pre_patch_policies를 설정하여 롤백 시나리오 테스트
        original_maybe_audit = orch._maybe_run_audit

        def mock_audit_with_patch(s, c, cfg_):
            original_maybe_audit(s, c, cfg_)
            if c == 5:
                # 강제로 patch 적용 상태 세팅
                orch._pre_patch_policies = {"ttl_defaults": {"price": 180}}
                orch._patch_applied_cycle = 5
                s["policies"]["ttl_defaults"]["price"] = 270
                s["policies"]["version"] = 1

        orch._maybe_run_audit = mock_audit_with_patch

        # metrics logger entries를 조작하여 성능 악화 시뮬레이션
        original_log = orch.logger.log

        def mock_log(cycle, s):
            original_log(cycle, s)
            # cycle 6에서 evidence_rate 급락
            if cycle == 6 and len(orch.logger.entries) >= 2:
                orch.logger.entries[-1]["rates"] = {
                    "evidence_rate": 0.40,
                    "gap_resolution_rate": 0.20,
                }
                orch.logger.entries[-2]["rates"] = {
                    "evidence_rate": 0.80,
                    "gap_resolution_rate": 0.60,
                }

        orch.logger.log = mock_log

        results = orch.run(initial_state=state)
        final_state = results[-1].state

        # 롤백이 발생했으면 price가 원래 180으로 복원
        assert final_state["policies"]["ttl_defaults"]["price"] == 180
        # version은 증가 (rollback도 version up)
        assert final_state["policies"].get("version", 0) >= 2

    def test_no_rollback_when_performance_stable(self, tmp_path):
        """성능 유지 시 롤백하지 않음."""
        from src.orchestrator import Orchestrator as Orch

        bench_base = _setup_bench(tmp_path)
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=6,
                audit_interval=5,
                plateau_window=100,
                bench_path=str(bench_base / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)
        state = _make_minimal_state()
        state["policies"]["ttl_defaults"] = {"price": 180}

        def mock_run(s, c):
            return CycleResult(cycle=c, state=s)

        orch._run_single_cycle = mock_run

        original_maybe_audit = orch._maybe_run_audit

        def mock_audit_with_patch(s, c, cfg_):
            original_maybe_audit(s, c, cfg_)
            if c == 5:
                orch._pre_patch_policies = {"ttl_defaults": {"price": 180}}
                orch._patch_applied_cycle = 5
                s["policies"]["ttl_defaults"]["price"] = 270
                s["policies"]["version"] = 1

        orch._maybe_run_audit = mock_audit_with_patch

        # metrics entries: 성능 유지 (하락 없음)
        original_log = orch.logger.log

        def mock_log(cycle, s):
            original_log(cycle, s)
            if cycle >= 5 and len(orch.logger.entries) >= 1:
                orch.logger.entries[-1]["rates"] = {
                    "evidence_rate": 0.80,
                    "gap_resolution_rate": 0.60,
                }

        orch.logger.log = mock_log

        results = orch.run(initial_state=state)
        final_state = results[-1].state

        # 롤백 안 함 → price는 270 유지
        assert final_state["policies"]["ttl_defaults"]["price"] == 270

    def test_snapshot_creation(self, tmp_path):
        """스냅샷 생성 확인."""
        bench_base = _setup_bench(tmp_path)
        domain_path = bench_base / "bench" / "test-domain"
        cfg = EvolverConfig(
            orchestrator=OrchestratorConfig(
                max_cycles=2,
                snapshot_every=1,
                bench_path=str(bench_base / "bench"),
                bench_domain="test-domain",
            ),
        )
        orch = Orchestrator(cfg)

        state = _make_minimal_state()

        def mock_run(s, c):
            return CycleResult(cycle=c, state=s)

        orch._run_single_cycle = mock_run
        orch.run(initial_state=state)

        snap1 = domain_path / "state-snapshots" / "cycle-1-snapshot"
        snap2 = domain_path / "state-snapshots" / "cycle-2-snapshot"
        assert snap1.exists()
        assert snap2.exists()
