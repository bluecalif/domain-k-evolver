# Project Overall Context
> Last Updated: 2026-04-11
> Status: Bronze 세대 완료 (Phase 0~5, 468 tests, commit `b122a23`) → **Silver 세대 착수 대기** (Silver P0 즉시 가능)

## 1. 핵심 파일

### 설계 문서 (현행)
| 파일 | 내용 | 참조 시점 |
|------|------|-----------|
| `docs/silver-masterplan-v2.md` | **Silver 단일 진실 소스** — Phase 표(§4) / HITL 정책(§14) / Provider 상세(§13) / 벤치 관리(§12) / 리스크(§8) | Silver 전 Phase |
| `docs/silver-implementation-tasks.md` | **Silver 실행 backlog** — Phase별 task + touched files + 정량 gate + blocking scenario S1~S11 (119 tasks) | Silver 전 Phase |
| `docs/session-compact.md` | 세션 간 진행 상태 추적 | 세션 시작 시 |
| `dev/active/p0-p1-remediation-plan.md` | v1 시대 P0/P1 remediation 8건 — Silver P0 에 흡수, P0 gate pass 시 deprecated 표기 (X2) | Silver P0 |

### 설계 문서 (아카이브)
| 파일 | 내용 |
|------|------|
| `docs/archive/draft.md` | 원본 설계 — State Machine, Inner Loop 6단계, 5대 불변원칙 |
| `docs/archive/design-v2.md` | Cycle 0 검증 반영 정교화 — Schema, Metrics, Critique→Plan 규칙 |
| `docs/archive/gu-bootstrap-spec.md` | GU Bootstrap 명세 — 생성 알고리즘, 동적 발견 규칙 |
| `docs/archive/gu-bootstrap-expansion-policy.md` | GU 확장 정책 — Axis Coverage Matrix, Quantum Jump |
| `docs/archive/phase{2,3}-analysis.md` | Phase 2·3 심층 분석 보고서 |
| `docs/archive/phase{4,5}-readiness-report.md` | Readiness Gate 판정 보고서 |
| `docs/archive/silver-masterplan.md` | Silver v1 — v2 에 의해 supersede |

### 데이터 정의
| 파일 | 내용 |
|------|------|
| `schemas/knowledge-unit.json` | KU JSON Schema |
| `schemas/evidence-unit.json` | EU JSON Schema |
| `schemas/gap-unit.json` | GU JSON Schema |
| `schemas/patch-unit.json` | PU JSON Schema |
| `schemas/remodel_report.schema.json` | **[Silver P2 NEW]** |
| `schemas/telemetry.v1.schema.json` | **[Silver P5 NEW]** |

### Bronze Phase Dev-Docs (모두 완료)
| Phase | 디렉토리 | 상태 |
|-------|----------|------|
| Phase 0B | `dev/active/phase0b-cycle1-validation/` | ✅ |
| Phase 0C | `dev/active/phase0c-gu-strategy/` | ✅ |
| Phase 1 | `dev/active/phase1-langgraph-core/` | ✅ 16/16, 191 tests |
| Phase 2 | `dev/active/phase2-bench-validation/` | ✅ 16/16, 272 tests |
| Phase 3 | `dev/active/phase3-cycle-remodeling/` | ✅ 9/9, 301 tests |
| Phase 4 | `dev/active/phase4-self-governing/` | ✅ 11/11, 420 tests (Gate FAIL → Phase 5 삽입) |
| Phase 5 | `dev/active/phase5-inner-loop-quality/` | ✅ 23/23, 468 tests, Gate #5 PASS |

### Silver Phase Dev-Docs (예정)
| Phase | 디렉토리 | 선행 조건 |
|-------|----------|-----------|
| Silver P0 | `dev/active/phase-si-p0-foundation/` | 즉시 착수 가능 (**dev-docs 생성 완료**) |
| Silver P1 | `dev/active/phase-si-p1-entity-resolution/` | P0 gate pass |
| Silver P2 | `dev/active/phase-si-p2-remodel/` | P1 |
| Silver P3 | `dev/active/phase-si-p3-acquisition/` | P0 gate pass (P1 과 병렬 가능) |
| Silver P4 | `dev/active/phase-si-p4-coverage/` | P2 + P3 |
| Silver P5 | `dev/active/phase-si-p5-telemetry-dashboard/` | P3 + P4 |
| Silver P6 | `dev/active/phase-si-p6-multidomain/` | P1~P5 전부 (Silver exit gate) |

### Bronze 구현 파일 (현행)
| 파일 | 내용 |
|------|------|
| `src/state.py` | EvolverState TypedDict |
| `src/graph.py` | StateGraph 빌드 + 엣지 라우팅 |
| `src/config.py` | 환경 설정 (gpt-4.1-mini 확정) |
| `src/orchestrator.py` | Outer Loop — metrics log → rollback → audit → save |
| `src/nodes/*.py` | seed, mode, plan, collect, integrate, critique, plan_modify, hitl_gate, audit, dispute_resolver |
| `src/adapters/llm_adapter.py` | LLMCallCounter + retry + MockLLM |
| `src/adapters/search_adapter.py` | Tavily 래퍼 + retry + 카운터 |
| `src/utils/state_io.py` | State JSON I/O |
| `src/utils/schema_validator.py` | JSON Schema 검증 |
| `src/utils/invariant_checker.py` | 5대 불변원칙 I1~I5 |
| `src/utils/metrics_logger.py` | 사이클별 Metrics + API calls/tokens |
| `src/utils/plateau_detector.py` | 수렴 감지 |
| `src/utils/policy_manager.py` | Policy 자동 수정/롤백/credibility 학습 |
| `src/utils/readiness_gate.py` | 3-Viewpoint Readiness Gate |
| `src/utils/llm_parse.py` | LLM 응답 JSON 추출 |
| `src/tools/search.py` | WebSearch/WebFetch 도구 래퍼 |
| `scripts/run_one_cycle.py` | 1사이클 Real API 실행 |
| `scripts/run_bench.py` | N사이클 CLI 벤치 실행 |
| `scripts/run_readiness.py` | Readiness 벤치마크 + Gate 판정 |

### Silver 신규 구현 파일 (예정)
| 파일 | Phase |
|------|-------|
| `src/utils/entity_resolver.py` | P1 |
| `src/nodes/remodel.py` | P2 |
| `src/adapters/providers/{base,tavily,ddg,curated}_provider.py` | P3 |
| `src/adapters/fetch_pipeline.py` | P3 |
| `src/utils/novelty.py`, `src/utils/coverage_map.py` | P4 |
| `src/obs/telemetry.py`, `src/obs/dashboard/` | P5 |

### 벤치 데이터
| 경로 | 내용 |
|------|------|
| `bench/japan-travel/` | Bronze 수동 실행 원본 (read-only, Cycle 0~2 Deliverable + state snapshots) |
| `bench/japan-travel-auto/` | Phase 3 최종 10 Cycle 자동 실행 결과 |
| `bench/japan-travel-auto-phase2-baseline/` | Phase 2 10 Cycle 백업 |
| `bench/japan-travel-readiness/` | Phase 4·5 Readiness Gate 벤치마크 |
| `bench/silver/{domain}/{trial_id}/` | **[Silver P0 NEW]** — trial-card.md + readiness-report.md 의무 |

### 템플릿
| 파일 | 내용 |
|------|------|
| `templates/seed-pack.md` ~ `templates/revised-plan.md` | 6대 Deliverable 템플릿 |
| `templates/si-trial-card.md` | **[Silver P0 NEW]** |
| `templates/si-readiness-report.md` | **[Silver P0 NEW]** |
| `templates/si-index-row.md` | **[Silver P0 NEW]** |

---

## 2. 데이터 인터페이스

### State (K, G, P, M, D) — JSON 파일 기반
```
읽기/쓰기: bench/{domain}/state/*.json  (Silver: bench/silver/{domain}/{trial_id}/state/)
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
    current_mode: dict | None       # {mode, cap, explore/exploit budget, trigger_set}
    axis_coverage: dict | None      # Axis Coverage Matrix
    jump_history: list[int]
    # Silver 확장 예정:
    # dispute_queue: list[dict]      # P0-C HITL-D batch
    # conflict_ledger: list[dict]    # P1
    # phase_state_version: int       # P2 remodel
    # telemetry_snapshot: dict       # P5
```

---

## 3. 주요 결정사항

### Bronze (D-01 ~ D-70)
| # | 결정 | Phase |
|---|------|-------|
| D-01~D-05 | JSON 파일 State + JSON Schema + entity_key 규칙 + 6 Metrics + Critique→Plan 컴파일 규칙 | 0 |
| D-06~D-08 | LangGraph StateGraph + Claude LLM(초기) + Hook 인코딩 | 1 |
| D-09~D-15 | Cycle 1 수동 검증 + GU Bootstrap 공식화 + SIM condition_split + 면세 disputed | 0B |
| D-16~D-28 | Phase 0C 신설 + Axis Coverage Matrix + Quantum Jump + T1 임계치 + Entity Hierarchy | 0C |
| D-29~D-39 | OpenAI GPT + Tavily + Orchestrator 외부 + Real API First + config fallback + LLMCallCounter | 2 |
| D-40~D-43 | Phase 3 = Cycle Quality Remodeling + hybrid conflict + Evidence-weighted resolution + C6 threshold=0.15 | 3 |
| D-44~D-52 | Phase 4 = Self-Governing + 3-Viewpoint Readiness Gate + Credibility 학습 + T6 audit trigger + C7 수렴 유보 | 4 |
| D-53~D-61 | VP1-R1 Gini + geography 규칙 추론 + refresh cap 10 + field 억제 + fresh start + target_count 비례 스케일 | 5 |
| D-62~D-70 | Staleness observed_at today + adaptive cap + T7 trigger + closed_loop 세분화 + evidence 가중 + multi-evidence boost | 5 |

### Silver (D-71 ~ D-80, 잠정)
| # | 결정 | Phase |
|---|------|-------|
| D-71 | Silver masterplan v2 = 단일 진실 소스 (Phase 표 / 정량 gate / blocking scenario) | Silver 전체 |
| D-72 | HITL 축소 — inline A/B/C 제거, HITL-S/R/D/E 4세트 + `dispute_queue` 배치 | P0 |
| D-73 | Provider 플러그인 3개 — Tavily 기본 + DDG optional + CuratedSource | P3 |
| D-74 | SEARCH / FETCH / PARSE 3단계 분리 (collect.py 리팩터) | P3 |
| D-75 | `bench/silver/{domain}/{trial_id}/` 격리 + trial-card / readiness-report 2종 의무 | P0 |
| D-76 | P0 scope-locked — 8 remediation + 벤치 + HITL + 인터페이스 고정 외 추가 금지 | P0 |
| D-77 | P5-A (telemetry schema) 가 P5-B (UI) 엄격 선행 — UI-first 금지 | P5 |
| D-78 | 비용 가드 — `cycle_llm_token_budget` + `cycle_fetch_bytes_budget` + degrade 모드 | P3 |
| D-79 | Silver 완료 test 목표 ≥ 588 (Bronze 468 + 120) | Silver 전체 |
| D-80 | 2차 도메인 선정 기준 — japan-travel 대비 time horizon / hierarchy depth / source language 3축 중 2축 이상 이질 | P6 |

---

## 4. 컨벤션 체크리스트

### 5대 불변원칙
- [ ] **Gap-driven**: `Plan.target_gaps ⊆ G.open`
- [ ] **Claim→KU 착지성**: `count(claims) == count(adds + updates + rejected_with_reason)`
- [ ] **Evidence-first**: `all(len(ku.evidence_links) ≥ 1 for active KU)`
- [ ] **Conflict-preserving**: disputed KU 삭제 불가, hold / condition_split / coexist 만 허용
- [ ] **Prescription-compiled**: `all(rx.id in revised_plan.traceability)`

### Metrics 건강 임계치
| 지표 | 건강 | 주의 | 위험 |
|------|------|------|------|
| 근거율 | ≥ 0.95 | 0.80–0.94 | < 0.80 |
| 다중근거율 | ≥ 0.50 | 0.30–0.49 | < 0.30 |
| 충돌률 | ≤ 0.05 | 0.06–0.15 | > 0.15 |
| 평균 confidence | ≥ 0.85 | 0.70–0.84 | < 0.70 |
| 신선도 리스크 | 0 | 1–3 | > 3 |

### Silver 추가 Metrics (emit 목표)
- **P0**: `collect_failure_rate`, `timeout_count`, `retry_success_rate`
- **P3**: `domain_entropy` (≥ 2.5 bits), `provider_entropy`, `fetch_success_rate` (≥ 80%), `avg_eu_per_claim` (≥ 1.8)
- **P4**: `novelty_avg` (≥ 0.25), `coverage_deficit`, plan 의 `reason_code` (100% 부여)
- **P5**: telemetry.v1 jsonl append-only

### Silver Blocking Scenario (`docs/silver-implementation-tasks.md`)
| ID | 시나리오 | Phase |
|----|----------|-------|
| S1 | adapter kill → hang 없음 | P0 |
| S2 | timeout 연쇄 | P0 |
| S3 | HITL 배치 큐 | P0 |
| S4 | alias / is_a | P1 |
| S5 | conflict ledger 영구 보존 | P1 |
| S6 | 중복 KU 15%+ 감소 | P1 |
| S7 | remodel trigger → HITL-R → rollback | P2 / P4 |
| S8 | robots.txt 차단 | P3 |
| S9 | 비용 budget degrade | P3 |
| S10 | 100 cycle dashboard load ≤ 10s | P5 |
| S11 | 2차 도메인 10 cycle Gate #5 동등 | P6 |

### 인코딩
- JSON read/write: `encoding='utf-8'`
- CSV read: `encoding='utf-8-sig'`
- Python stdout: `PYTHONUTF8=1`
- PS1 파일: Bash heredoc 으로 작성 (BOM 방지)

### 코드 컨벤션
- `entity_key`: `{domain}:{category}:{slug}` (lowercase + hyphen)
- ID 패턴: `KU-NNNN`, `EU-NNNN`, `GU-NNNN`, `PU-NNNN`
- 노드 함수: `def node_name(state: EvolverState) -> dict` (변경 필드만 반환)
- 커밋: `[phase-name] Step X.Y: 설명`
- 브랜치: `feature/[phase-name]`
- Silver 커밋 prefix: `[si-p{N}]` (예: `[si-p0] Step A.1: bench scaffolding`)
