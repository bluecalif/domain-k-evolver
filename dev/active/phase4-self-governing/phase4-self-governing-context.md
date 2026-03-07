# Phase 4: Self-Governing Evolver — Context
> Created: 2026-03-07
> Status: Suspended (Gate FAIL — 보완 Phase 논의 필요)

## 변경/생성 파일

### Stage A (commit `cebd47e`)
| 파일 | 변경 내용 |
|------|-----------|
| `src/nodes/audit.py` | **신규** — run_audit() + 4개 분석함수 |
| `src/state.py` | AuditFinding, PolicyPatch, AuditReport 타입 추가 |
| `src/config.py` | audit_interval 파라미터 (기본 5, 0=비활성) |
| `src/orchestrator.py` | _maybe_run_audit() + audit_reports + audit_history |
| `tests/test_nodes/test_audit.py` | **신규** 23개 테스트 |
| `tests/test_orchestrator.py` | 3개 audit 통합 테스트 추가 |

### Stage B (commit `816fb2d`)
| 파일 | 변경 내용 |
|------|-----------|
| `src/utils/policy_manager.py` | **신규** apply_patches, rollback, credibility 학습 |
| `tests/test_policy_manager.py` | **신규** 37개 테스트 |
| `src/orchestrator.py` | policy apply/rollback 통합, 실행 순서 재배치 |
| `src/nodes/audit.py` | credibility 학습 연동 |
| `src/nodes/integrate.py` | KU 생성 시 source_type 전파 |
| `schemas/policy.json` | **신규** Policy JSON Schema |

### Stage C (commit `31ef46d`)
| 파일 | 변경 내용 |
|------|-----------|
| `src/nodes/mode.py` | _compute_audit_bias(), _compute_trigger_t6_audit(), _compute_budget() bias |
| `src/nodes/critique.py` | _check_convergence() C7 조건 + audit_history 전달 |
| `tests/test_nodes/test_stage_c.py` | **신규** 27개 테스트 |

### Stage D (commit `62915de`)
| 파일 | 변경 내용 |
|------|-----------|
| `src/utils/readiness_gate.py` | **신규** VP1/VP2/VP3 평가 + evaluate_readiness() |
| `tests/test_readiness_gate.py` | **신규** 26개 테스트 |
| `scripts/run_readiness.py` | **신규** 벤치마크 + Gate 평가 스크립트 |
| `docs/phase4-readiness-report.md` | **신규** Gate 결과 상세 보고서 |
| `bench/japan-travel-readiness/` | 13 Cycle 벤치마크 결과 (state + trajectory + report) |

## 결정사항

| ID | 결정 | 근거 | 날짜 |
|----|------|------|------|
| D-44 | Phase 4 = Self-Governing Evolver | 단일 도메인 자기 진화 보장이 multi-domain 전제 | 2026-03-07 |
| D-45 | Multi-Domain = Phase X (잠정) | Readiness Gate 통과 후 번호 확정 | 2026-03-07 |
| D-46 | 3-Viewpoint Readiness Gate 필수 | Variability + Completeness + Self-Governance | 2026-03-07 |
| D-47 | Gate FAIL 시 Phase N+1 삽입 | 보완 Phase 후 Gate 재실행 | 2026-03-07 |
| D-48 | Orchestrator 순서 = metrics log -> rollback -> audit -> save | rollback이 metrics 이후여야 판정 가능 | 2026-03-07 |
| D-49 | Credibility 학습 guardrail | bad_ratio >30% -> prior 하향, <10%+고신뢰 -> 상향 | 2026-03-07 |
| D-50 | T6 동적 trigger | Audit axis_imbalance -> Jump Mode 발동 | 2026-03-07 |
| D-51 | C7 수렴 조건 | critical audit findings 시 수렴 유보 | 2026-03-07 |
| D-52 | Readiness Gate 판정 규칙 | 관점별 80%+ 기준 + critical FAIL 없음 -> PASS | 2026-03-07 |

## Readiness Gate 결과 요약

| Viewpoint | 결과 | Score | 주요 실패 |
|-----------|------|-------|-----------|
| VP1 Variability | FAIL | 3/5 | blind_spot=0.85, field_gini=0.518 |
| VP2 Completeness | FAIL | 2/6 | gap_res=0.844, min_ku=3, staleness=59 |
| VP3 Self-Governance | PASS | 6/6 | -- |

## 참조 문서

| 문서 | 용도 |
|------|------|
| `docs/phase4-readiness-report.md` | Gate 결과 상세 분석 |
| `bench/japan-travel-readiness/readiness-report.json` | Gate 판정 데이터 |
| `docs/design-v2.md` §9 | Outer Loop / Executive Audit 원안 |
| `bench/japan-travel-readiness/trajectory/` | 13 Cycle trajectory 데이터 |
