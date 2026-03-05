"""Task 2.9 테스트: 불변원칙 자동검증."""

from src.utils.invariant_checker import check_invariants


class TestInvariantChecker:
    def test_all_pass(self):
        state = {
            "gap_map": [
                {"gu_id": "GU-0001", "status": "open"},
                {"gu_id": "GU-0002", "status": "resolved"},
            ],
            "knowledge_units": [
                {"ku_id": "KU-001", "status": "active", "evidence_links": ["EU-001"]},
            ],
            "current_plan": {"target_gaps": ["GU-0001"]},
            "current_critique": {"prescriptions": []},
            "current_claims": [],
        }
        result = check_invariants(state)
        assert result.passed is True
        assert result.violations == []

    def test_i1_gap_driven_violation(self):
        state = {
            "gap_map": [{"gu_id": "GU-0001", "status": "open"}],
            "knowledge_units": [],
            "current_plan": {"target_gaps": ["GU-0001", "GU-9999"]},
            "current_critique": {},
        }
        result = check_invariants(state)
        assert result.passed is False
        assert any("[I1]" in v for v in result.violations)

    def test_i1_resolved_gu_allowed(self):
        """plan_modify가 추가한 resolved GU는 허용."""
        state = {
            "gap_map": [
                {"gu_id": "GU-0001", "status": "resolved"},
            ],
            "knowledge_units": [],
            "current_plan": {"target_gaps": ["GU-0001"]},
            "current_critique": {},
        }
        result = check_invariants(state)
        assert result.passed is True

    def test_i3_evidence_first_violation(self):
        state = {
            "gap_map": [],
            "knowledge_units": [
                {"ku_id": "KU-001", "status": "active", "evidence_links": []},
            ],
            "current_plan": {},
            "current_critique": {},
        }
        result = check_invariants(state)
        assert result.passed is False
        assert any("[I3]" in v for v in result.violations)

    def test_i3_disputed_no_evidence_ok(self):
        """disputed KU는 evidence 체크 안 함."""
        state = {
            "gap_map": [],
            "knowledge_units": [
                {"ku_id": "KU-001", "status": "disputed", "evidence_links": []},
            ],
            "current_plan": {},
            "current_critique": {},
        }
        result = check_invariants(state)
        assert result.passed is True

    def test_i5_prescription_compiled_violation(self):
        state = {
            "gap_map": [],
            "knowledge_units": [],
            "current_plan": {"traceability": []},
            "current_critique": {
                "prescriptions": [{"rx_id": "RX-0001", "type": "epistemic"}],
            },
        }
        result = check_invariants(state)
        assert result.passed is False
        assert any("[I5]" in v for v in result.violations)

    def test_i5_all_traced(self):
        state = {
            "gap_map": [],
            "knowledge_units": [],
            "current_plan": {
                "traceability": [{"rx_id": "RX-0001", "applied": True}],
            },
            "current_critique": {
                "prescriptions": [{"rx_id": "RX-0001", "type": "epistemic"}],
            },
        }
        result = check_invariants(state)
        assert not any("[I5]" in v for v in result.violations)

    def test_empty_state(self):
        result = check_invariants({})
        assert result.passed is True
