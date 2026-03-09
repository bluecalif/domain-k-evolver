# Project Overall Context
> Last Updated: 2026-03-08 (Phase 5 Stage D)
> Status: In Progress — Phase 5 Stage D (GU Resolve Rate 개선)

## 1. 핵심 파일

### 설계 문서
| 파일 | 내용 | 참조 시점 |
|------|------|-----------|
| `docs/draft.md` | 원본 설계 — State Machine, 핵심 객체, Inner Loop 6단계, 5대 불변원칙 | 항상 |
| `docs/design-v2.md` | Cycle 0 검증 반영 정교화 — Schema, Metrics, Critique→Plan 규칙, LangGraph 설계 | 항상 |
| `docs/gu-bootstrap-spec.md` | GU Bootstrap 명세 — 생성 알고리즘 5단계, 동적 발견 규칙, 우선순위, Scope 제어, 수렴 조건 | Seed/Plan 단계 |
| `docs/gu-bootstrap-expansion-policy.md` | GU 확장 정책 — Axis Coverage Matrix, Quantum Jump, Guardrail | Phase 0C |
| `docs/gu-from-scratch.md` | GU Bootstrap 문제 인식 + 해결 방향 (gu-bootstrap-spec의 기반) | 참고용 |
| `docs/session-compact.md` | 세션 간 진행 상태 추적 | 세션 시작 시 |

### 데이터 정의
| 파일 | 내용 |
|------|------|
| `schemas/knowledge-unit.json` | KU JSON Schema (KU-NNNN, 8 required + 3 optional) |
| `schemas/evidence-unit.json` | EU JSON Schema (EU-NNNN, 5 required + 3 optional) |
| `schemas/gap-unit.json` | GU JSON Schema (GU-NNNN, 5 required + 3 optional) |
| `schemas/patch-unit.json` | PU JSON Schema (PU-NNNN, 6 required + 3 optional) |

### Phase 0B Dev-Docs (✅ Complete)
| 파일 | 내용 |
|------|------|
| `dev/active/phase0b-cycle1-validation/phase0b-cycle1-validation-plan.md` | Phase 0B 종합 계획 |
| `dev/active/phase0b-cycle1-validation/phase0b-cycle1-validation-context.md` | Phase 0B 컨텍스트 |
| `dev/active/phase0b-cycle1-validation/phase0b-cycle1-validation-tasks.md` | Phase 0B 태스크 추적 |
| `dev/active/phase0b-cycle1-validation/debug-history.md` | Phase 0B 디버깅 이력 |

### Phase 0C Dev-Docs
| 파일 | 내용 |
|------|------|
| `dev/active/phase0c-gu-strategy/phase0c-gu-strategy-plan.md` | Phase 0C 종합 계획 |
| `dev/active/phase0c-gu-strategy/phase0c-gu-strategy-context.md` | Phase 0C 컨텍스트 |
| `dev/active/phase0c-gu-strategy/phase0c-gu-strategy-tasks.md` | Phase 0C 태스크 추적 |
| `dev/active/phase0c-gu-strategy/debug-history.md` | Phase 0C 디버깅 이력 |

### Phase 1 Dev-Docs (✅ Complete)
| 파일 | 내용 |
|------|------|
| `dev/active/phase1-langgraph-core/phase1-langgraph-core-plan.md` | Phase 1 종합 계획 |
| `dev/active/phase1-langgraph-core/phase1-langgraph-core-context.md` | Phase 1 컨텍스트 |
| `dev/active/phase1-langgraph-core/phase1-langgraph-core-tasks.md` | Phase 1 태스크 추적 (16/16 완료) |
| `dev/active/phase1-langgraph-core/debug-history.md` | Phase 1 디버깅 이력 (2건) |

### Phase 2 Dev-Docs
| 파일 | 내용 |
|------|------|
| `dev/active/phase2-bench-validation/phase2-bench-validation-plan.md` | Phase 2 종합 계획 |
| `dev/active/phase2-bench-validation/phase2-bench-validation-context.md` | Phase 2 컨텍스트 |
| `dev/active/phase2-bench-validation/phase2-bench-validation-tasks.md` | Phase 2 태스크 추적 (11/16) |
| `dev/active/phase2-bench-validation/debug-history.md` | Phase 2 디버깅 이력 |

### Phase 1 구현 파일
| 파일 | 내용 |
|------|------|
| `src/state.py` | EvolverState TypedDict + 보조 타입 |
| `src/graph.py` | StateGraph 빌드 + 엣지 라우팅 (14노드) |
| `src/nodes/*.py` | 8개 노드 (seed, mode, plan, collect, integrate, critique, plan_modify, hitl_gate) |
| `src/utils/*.py` | state_io, schema_validator, metrics |
| `src/tools/search.py` | WebSearch/WebFetch 도구 래퍼 |
| `tests/test_graph.py` | Graph 통합 테스트 36개 |
| `tests/test_nodes/*.py` | 노드 단위 테스트 |

### Phase 2 코드 (Stage A'+B' 완료, 254 tests)
| 파일 | 내용 |
|------|------|
| `src/config.py` | 환경 설정 (gpt-4.1-mini 확정) |
| `src/adapters/llm_adapter.py` | LLMCallCounter 래퍼 + max_retries=3 + MockLLM |
| `src/adapters/search_adapter.py` | Tavily 래퍼 + retry 백오프 + 호출 카운터 |
| `src/orchestrator.py` | 사이클 관리 Orchestrator |
| `src/utils/metrics_logger.py` | 사이클별 Metrics + API calls/tokens 기록 |
| `src/utils/invariant_checker.py` | 5대 불변원칙 자동검증 (I1~I5) |
| `src/utils/llm_parse.py` | LLM 응답 JSON 추출 (markdown fence 제거) |
| `scripts/run_one_cycle.py` | 1사이클 Real API 실행 |
| `scripts/run_bench.py` | N사이클 CLI 벤치 실행 + 불변원칙 + trajectory |
| `tests/test_config.py` | Config 단위 테스트 |
| `tests/test_adapters.py` | Adapter + retry + 카운터 테스트 |
| `tests/test_invariant_checker.py` | 불변원칙 8 tests |
| `tests/test_orchestrator.py` | Orchestrator 단위 테스트 |
| `tests/test_metrics_logger.py` | Metrics Logger 단위 테스트 |

### Phase 3 코드 (완료, 301 tests)
| 파일 | 내용 |
|------|------|
| `src/nodes/dispute_resolver.py` | Dispute Resolution 모듈 (D-42) |
| `src/nodes/integrate.py` | hybrid conflict detection (D-41) |
| `src/nodes/critique.py` | dispute resolution 통합 + C6 수렴조건 (D-43) |
| `src/nodes/plan_modify.py` | dispute_resolved 처방 타입 |
| `src/utils/plateau_detector.py` | conflict_rate 복합 조건 확장 |
| `tests/test_nodes/test_dispute_resolver.py` | Dispute resolver 15 tests |
| `tests/test_nodes/test_critique.py` | critique 확장 테스트 |
| `tests/test_plateau_detector.py` | plateau 복합 조건 테스트 |

### 벤치 자동 실행 결과
| 파일 | 내용 |
|------|------|
| `bench/japan-travel-auto/state/*.json` | Phase 3 최종 10 Cycle State |
| `bench/japan-travel-auto/trajectory/` | Phase 3 10 Cycle trajectory (JSON + CSV) |
| `bench/japan-travel-auto-phase2-baseline/` | Phase 2 10 Cycle 원본 백업 |
| `docs/phase2-analysis.md` | Phase 2 심층 분석 보고서 |
| `docs/phase3-analysis.md` | Phase 3 심층 분석 보고서 |

### Phase 4 Dev-Docs (✅ Complete — Gate FAIL)
| 파일 | 내용 |
|------|------|
| `dev/active/phase4-self-governing/phase4-self-governing-plan.md` | Phase 4 종합 계획 (4 Stage, 11 tasks, Readiness Gate) |
| `dev/active/phase4-self-governing/phase4-self-governing-context.md` | Phase 4 컨텍스트 (갭 분석, 변경 대상) |
| `dev/active/phase4-self-governing/phase4-self-governing-tasks.md` | Phase 4 태스크 추적 (11/11 완료) |
| `dev/active/phase4-self-governing/debug-history.md` | Phase 4 디버깅 이력 |

### Phase 5 Dev-Docs
| 파일 | 내용 |
|------|------|
| `dev/active/phase5-inner-loop-quality/phase5-inner-loop-quality-plan.md` | Phase 5 종합 계획 (4 Stage + 선행/검증, 13 tasks) |
| `dev/active/phase5-inner-loop-quality/phase5-inner-loop-quality-context.md` | Phase 5 컨텍스트 (axis_tags 흐름, 결정사항) |
| `dev/active/phase5-inner-loop-quality/phase5-inner-loop-quality-tasks.md` | Phase 5 태스크 추적 (10/13) |
| `dev/active/phase5-inner-loop-quality/debug-history.md` | Phase 5 디버깅 이력 |

### Phase 4 코드 (완료, 420 tests)
| 파일 | 내용 |
|------|------|
| `src/nodes/audit.py` | Executive Audit — run_audit() + 4개 분석 함수 |
| `src/utils/policy_manager.py` | Policy 자동 수정/롤백/credibility 학습 |
| `src/utils/readiness_gate.py` | 3-Viewpoint Readiness Gate (VP1/VP2/VP3) |
| `scripts/run_readiness.py` | Readiness 벤치마크 + Gate 판정 |
| `bench/japan-travel-readiness/` | Phase 4 Gate 벤치마크 결과 |
| `docs/phase4-readiness-report.md` | Gate FAIL 상세 보고서 |

### 벤치 데이터 (Cycle 2 결과 — 최신)
| 파일 | 내용 |
|------|------|
| `bench/japan-travel/state/knowledge-units.json` | KU 28개 (active 27 + disputed 1) |
| `bench/japan-travel/state/gap-map.json` | GU 21 open + 18 resolved (axes 포함) |
| `bench/japan-travel/state/domain-skeleton.json` | 카테고리/필드/관계/키규칙/axes |
| `bench/japan-travel/state/policies.json` | 출처신뢰/TTL/교차검증/충돌해결 |
| `bench/japan-travel/state/metrics.json` | 6개 지표 + jump_mode 실측 |
| `bench/japan-travel/cycle-0/` | 6대 Deliverable 원본 |
| `bench/japan-travel/cycle-1/` | 5대 Deliverable (Cycle 1 수동 실행 결과) |
| `bench/japan-travel/cycle-2/` | 6대 Deliverable (Cycle 2 Jump Mode 수동 실행 결과) |
| `bench/japan-travel/state-snapshots/cycle-0-snapshot/` | Cycle 0 State 스냅샷 |
| `bench/japan-travel/state-snapshots/cycle-1-snapshot/` | Cycle 1 State 스냅샷 |

### 템플릿
| 파일 | 내용 |
|------|------|
| `templates/seed-pack.md` | Seed Pack 템플릿 |
| `templates/collection-plan.md` | Collection Plan 템플릿 |
| `templates/evidence-claim-set.md` | Evidence Claim Set 템플릿 |
| `templates/kb-patch.md` | KB Patch 템플릿 |
| `templates/critique-report.md` | Critique Report 템플릿 |
| `templates/revised-plan.md` | Revised Plan 템플릿 |

---

## 2. 데이터 인터페이스

### State (K, G, P, M, D) — JSON 파일 기반
```
읽기: bench/{domain}/state/*.json
쓰기: bench/{domain}/state/*.json (노드 실행 후 업데이트)
검증: schemas/*.json (JSON Schema Draft 2020-12)
```

### Cycle Deliverables — MD 파일
```
읽기/쓰기: bench/{domain}/cycle-{n}/*.md
템플릿: templates/*.md
```

### EvolverState — LangGraph 내부
```python
class EvolverState(TypedDict):
    knowledge_units: list[dict]     # K
    gap_map: list[dict]             # G
    policies: dict                   # P
    metrics: dict                    # M
    domain_skeleton: dict            # D (axes, entity_hierarchy 포함)
    current_cycle: int
    current_plan: dict | None
    current_claims: list[dict] | None
    current_critique: dict | None
    current_mode: dict | None       # {mode, cap, explore_budget, exploit_budget, trigger_set}
    axis_coverage: dict | None      # Axis Coverage Matrix
    jump_history: list[int]         # Jump Mode 진입 Cycle 번호
```

---

## 3. 주요 결정사항

| # | 결정 | 대안 | 선택 근거 | Phase |
|---|------|------|-----------|-------|
| D-01 | JSON 파일 기반 State 관리 | SQLite/PostgreSQL | 디버깅 투명성, 스키마 검증 용이, 규모 작음 | 0 |
| D-02 | JSON Schema Draft 2020-12 | Pydantic only | 언어 무관 검증, 템플릿 자동 생성 가능 | 0 |
| D-03 | entity_key = `{domain}:{category}:{slug}` | UUID, 자연어 키 | Entity Resolution 가능, 인간 판독 가능 | 0 |
| D-04 | 6개 Metrics + 건강 임계치 | 사용자 정의 | Cycle 0 실측으로 확정, 실용적 | 0 |
| D-05 | Critique→Plan 6개 컴파일 규칙 | LLM 자유 변환 | 추적성 보장, 자동화 가능 | 0 |
| D-06 | LangGraph StateGraph | 자체 구현, CrewAI | 공식 interrupt 지원, State 관리 내장 | 1 |
| D-07 | Claude (Anthropic) LLM | OpenAI GPT | 프로젝트 일관성, 한국어 성능 | 1 |
| D-08 | Hook 인코딩: Bash heredoc 작성 | Write 도구 | PS1 BOM 문제 회피 | Prep |
| D-09 | Cycle 1 수동 실행 추가 (Phase 0B) | 바로 LangGraph 구현 | Conflict-preserving 미검증, design-v2 §12 권장 | 0B |
| D-10 | GU Bootstrap 알고리즘 공식화 | LLM 자유 생성 | Category×Field 매트릭스 기반 결정론적 생성, Cycle 0 역검증으로 정합성 확인 | 0B 전 |
| D-11 | SIM 가격 충돌 → condition_split | 단일값 선택 | 물리SIM vs eSIM 조건 분리가 정확 | 0B |
| D-12 | 면세 최소금액 충돌 → disputed + hold | 삭제 | Conflict-preserving 원칙 준수 | 0B |
| D-13 | 동적 GU 3개 발견 (GU-0029~0031) | 상한 초과 허용 | 상한(4개) 이내, 트리거 A/B/C 적합 | 0B |
| D-14 | GU-0004 entity_key 불일치 해결 | 별개 KU 유지 | metro-pass = subway-ticket 동일 상품 확인 | 0B |
| D-15 | Cycle 1 처방 5개 (RX-07~11) 도출 | — | Critique 분석 결과 | 0B |
| D-16 | Phase 0C 신설 (GU 전략 재검토) | Phase 1 바로 진입 | expansion-policy v0.1의 진단 타당하나 수치 미확정, 실전 테스트 필요 | 0C 전 |
| D-17 | Axis Coverage Matrix 도입 | category만 관리 | 다축(geography/condition/risk) 커버리지 추적으로 편향 해소 | 0C |
| D-18 | Quantum Jump Mode 도입 | 고정 20% 상한만 | 구조 결손 시 조건부 확장, guardrail로 통제 | 0C |
| D-19 | Jump Mode T1(Axis Under-Coverage) 단독 발동 | 복수 trigger 발동 대기 | geography deficit 0.200 단일 발동으로 해소 성공 | 0C |
| D-20 | explore 60%/exploit 40% 배분 | 50:50, 70:30 | C2 실측 62.5% → 60% 상한 확정 | 0C |
| D-21 | KU-0011 disputed 해결 (5,000엔 유지) | 철폐 보도 수용 | 4개 독립 출처 일치, 초기 "철폐" 보도는 오류 | 0C |
| D-22 | 동적 GU 6개 생성 (jump_cap 10 이내) | — | high/critical 50% ≥ 40% 준수 | 0C |
| D-23 | Critique 5대 불변원칙 전원 PASS | — | Prescription-compiled 부분 준수 (미반영 사유 합리적) | 0C |
| D-24 | 처방 RX-12~16 도출 | — | risk:informational 해소, entity hierarchy, 홀수 배분 규칙 | 0C |
| D-25 | Cycle 3 Normal Mode 진입 | Jump 연속 | 사전 GU 생성(GU-0038/0039)으로 T1 해소 → Normal 전환 | 0C |
| D-26 | T1 임계치 = deficit_ratio > 0 확정 | 20%, 30% | C2 실측: 0.200 발동 → 해소 성공 | 0C |
| D-27 | explore 비율 단계별 확정 | 단일 비율 | 초기 60%, 중기 50%, 수렴 40% | 0C |
| D-28 | Entity Hierarchy 규칙 신설 | Phase 1 defer | is_a + alias 관계 정의, Phase 1 schema 반영 예정 | 0C |
| D-29 | LLM → OpenAI GPT (langchain-openai) | Claude (Anthropic) | 범용 API 호환성, 비용 효율 | 2 |
| D-30 | Search → Tavily Search (langchain-community) | SerpAPI, Google | 무료 tier 1000 req/month, LangChain 통합 | 2 |
| D-31 | Phase 2를 4 Stage 25 tasks로 확대 | 기존 7 tasks | 10+ 사이클 검증 + Orchestrator + Plateau Detection 등 미포함 | 2 |
| D-32 | Orchestrator가 Graph 외부에서 사이클 관리 | Graph 내부 루프 | 사이클 간 save/snapshot/invariant check 삽입 필요 | 2 |
| D-33 | Stage별 세션 분리 진행 | 단일 세션 | A→commit→B→commit→C→commit, 컨텍스트 관리 | 2 |
| D-34 | Real API First 전략 | Mock 위주(Task 19에서야 Real) | 즉시 Real 검증, 문제 조기 발견 | 2 |
| D-35 | 25→16 tasks 축소 | 기존 25 tasks | Over-engineering 삭제 (녹화/재생, 시각화, Memory Guard 등) | 2 |
| D-36 | config fallback gpt-4.1-mini 확정 | gpt-4o | 비용 효율, 충분한 성능 | 2 |
| D-37 | jump target_count 상한 10 | 무제한 | API 비용 통제 | 2 |
| D-38 | LLMCallCounter 래퍼 패턴 | 직접 호출 | 호출 횟수/토큰 추적 필요 | 2 |
| D-39 | Metrics Guard warning-only | halt 모드 | halt 시 Cycle 5에서 조기 중단 | 2 |
| D-40 | Phase 3 = Cycle Quality Remodeling | Multi-Domain 바로 | Phase 2 분석 결과 FP가 유일 병목 | 3 |
| D-41 | hybrid conflict detection (rule + LLM) | pure LLM | 동일값 skip, 값차이 LLM semantic | 3 |
| D-42 | Evidence-weighted resolution | 다수결/최신우선 | evidence ≥ 2×disputes → 자동 resolve, 미달 시 LLM 중재 | 3 |
| D-43 | C6 conflict_rate threshold = 0.15 | 0.20 | 수렴 조건에 충돌률 상한 추가 | 3 |
| D-44 | Phase 4 = Self-Governing Evolver | Multi-Domain 바로 | 단일 도메인 자기 진화 보장이 multi-domain 전제 | 4 |
| D-45 | Multi-Domain = Phase X (잠정) | Phase 5 확정 | Readiness Gate 통과 후 번호 확정 | 4 |
| D-46 | 3-Viewpoint Readiness Gate 필수 | 없음 | Variability + Completeness + Self-Governance | 4 |
| D-47 | Gate FAIL 시 Phase N+1 삽입 | 무시하고 진행 | 보완 Phase 후 Gate 재실행 | 4 |
| D-48 | Orchestrator 순서 = metrics log → rollback → audit → save | — | 순서 보장 필요 | 4 |
| D-49 | Credibility 학습 — bad_ratio >30% → prior↓ | — | 출처 품질 자동 학습 | 4 |
| D-50 | T6 동적 trigger — Audit axis_imbalance → Jump Mode | — | Audit→Mode 연동 | 4 |
| D-51 | C7 수렴 조건 — critical audit findings 시 수렴 유보 | — | 미해결 문제 시 조기 수렴 방지 | 4 |
| D-52 | Readiness Gate — 관점별 80%+ + critical FAIL 없음 → PASS | — | 3-Viewpoint 판정 규칙 | 4 |
| D-53 | VP1-R1 Shannon Entropy → Gini Coefficient | threshold 상향 | Shannon은 분포 균등성 미측정 (8.7x 차이도 PASS) | 5 |
| D-54 | Geography 추론 = 규칙 기반 (entity_key 패턴) | LLM 추론 | 비용 없이 충분한 정확도 | 5 |
| D-55 | Refresh GU cycle당 상한 (최대 10개) | 무제한 | 59개 동시 생성 방지 | 5 |
| D-56 | Field 다양성 = count > mean×1.5 억제 | Gini 기반 | 단순 규칙으로 `*` 필드 편중 해소 | 5 |
| D-57 | Readiness Gate seed state(cycle-0) fresh start | resume | Phase 5 코드 효과 독립 측정 | 5 |
| D-58 | Orchestrator plateau_window=0 비활성화 | 유지 | Gate 벤치 시 plateau 간섭 방지 | 5 |
| D-59 | run_readiness.py japan-travel-readiness 분리 저장 | 덮어쓰기 | 원본 bench 데이터 보호 | 5 |
| D-60 | target_count/cap 하드캡 제거 — 비례 스케일 | 캡 유지+GU 제한 | GU 생성>>해결 불균형 해소, dynamic_gu_cap은 유지 | 5 |
| D-61 | bench/ 더블 서픽스 버그 수정 + 아티팩트 정리 | — | run_readiness.py `-readiness` 이중 적용 → `japan-travel-readiness-readiness` 생성 | 5 |

---

## 4. 컨벤션 체크리스트

### 5대 불변원칙
- [ ] **Gap-driven**: Plan.target_gaps ⊆ G.open
- [ ] **Claim→KU 착지성**: count(claims) == count(adds + updates + rejected_with_reason)
- [ ] **Evidence-first**: all(len(ku.evidence_links) ≥ 1 for active KU)
- [ ] **Conflict-preserving**: disputed KU 삭제 불가, hold/condition_split/coexist만 허용
- [ ] **Prescription-compiled**: all(rx.id in revised_plan.traceability)

### Metrics 건강 임계치
| 지표 | 건강 | 주의 | 위험 |
|------|------|------|------|
| 근거율 | ≥ 0.95 | 0.80–0.94 | < 0.80 |
| 다중근거율 | ≥ 0.50 | 0.30–0.49 | < 0.30 |
| 충돌률 | ≤ 0.05 | 0.06–0.15 | > 0.15 |
| 평균 confidence | ≥ 0.85 | 0.70–0.84 | < 0.70 |
| 신선도 리스크 | 0 | 1–3 | > 3 |

### 인코딩
- JSON read/write: `encoding='utf-8'`
- CSV read: `encoding='utf-8-sig'`
- Python stdout: `PYTHONUTF8=1`
- PS1 파일: Bash heredoc으로 작성 (BOM 방지)

### 코드 컨벤션
- entity_key: `{domain}:{category}:{slug}` (lowercase + hyphen)
- ID 패턴: `KU-NNNN`, `EU-NNNN`, `GU-NNNN`, `PU-NNNN`
- 노드 함수: `def node_name(state: EvolverState) -> dict` (변경 필드만 반환)
- 커밋: `[phase-name] Step X.Y: 설명`
- 브랜치: `feature/[phase-name]`
