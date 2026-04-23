# Project Overall Context
> Last Updated: 2026-04-18
> Status: Bronze 완료 (468) → SI-P0~P5 완료 (821) → **SI-P6 (Consolidation & KB Release) 착수**

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

### Silver Phase Dev-Docs
| Phase | 디렉토리 | 선행 조건 |
|-------|----------|-----------|
| Silver P0 | `dev/active/phase-si-p0-foundation/` | ✅ **완료** (32/32, Gate PASS, 510 tests) |
| Silver P1 | `dev/active/phase-si-p1-entity-resolution/` | ✅ **완료** (12/12, 544 tests, S4/S5/S6 pass) |
| Silver P2 | `dev/active/phase-si-p2-remodel/` | **REVOKED** → remodel on/off 비교 실험으로 재설계 (D-127) |
| Silver P3 | `dev/active/phase-si-p3-acquisition/` | **REVOKED** (D-120, 2026-04-13) |
| Silver P3R | `dev/active/phase-si-p3r-snippet-refactor/` | ✅ **완료** (8/8, Gate PASS, D-125, 608 tests) |
| **Gap-Res Investigation** | `dev/active/phase-gap-resolution-investigation/` | ✅ **완료** (12/12, D-129~D-131) |
| Silver P4 | `dev/active/phase-si-p4-coverage/` | ✅ **완료** (42/42, 797 tests, VP4 PASS 4/5, D-147~D-150 해소) |
| Silver P5 | `dev/active/phase-si-p5-telemetry-dashboard/` | ✅ **완료** (15/15, Gate PASS, 821 tests) |
| Silver P6 | `dev/active/phase-si-p6-consolidation/` | **Planning** (0/16) — P5 ✅ |
| SI-P7 Structural Redesign | `dev/active/phase-si-p7-structural-redesign/` | **진행 중** — Step A/B 완료, **Step V 검증 착수 전** (D-190), Step C (S5a) 는 Step V 결과 의존 |
| M1 Multi-Domain | `dev/active/phase-m1-multidomain/` (예정) | suspended — P6 완료 후 활성화 |

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
| `src/utils/novelty.py`, `src/utils/coverage_map.py` | P4 Stage A (✅ 완료) |
| `src/utils/external_novelty.py`, `src/utils/reach_ledger.py`, `src/utils/cost_guard.py` | P4 Stage E (신규) |
| `src/nodes/universe_probe.py`, `src/nodes/exploration_pivot.py` | P4 Stage E (신규) |
| `src/obs/__init__.py`, `src/obs/telemetry.py`, `src/obs/dashboard/app.py`, `src/obs/dashboard/views/*.py` | P5 ← 현재 |

### 벤치 데이터
| 경로 | 내용 |
|------|------|
| `bench/japan-travel/` | Bronze 수동 실행 원본 (read-only, Cycle 0~2 Deliverable + state snapshots) |
| `bench/japan-travel-auto/` | Phase 3 최종 10 Cycle 자동 실행 결과 |
| `bench/japan-travel-auto-phase2-baseline/` | Phase 2 10 Cycle 백업 |
| `bench/japan-travel-readiness/` | Phase 4·5 Readiness Gate 벤치마크 |
| `bench/silver/{domain}/{trial_id}/` | **[Silver P0 NEW]** — trial-card.md + readiness-report.md 의무 |
| `bench/japan-travel-external-anchor/` | **[P4 Stage E]** — stage-e-off / stage-e-on 15c 비교 벤치. COMPARISON.md 포함 |

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
| D-88~D-95 | P0 진행 중 결정: collect/integrate I/O shape 동결, HITL-E 임계치, config snapshot, provenance, EvolverState 5필드, fresh seed 전략 | P0 |
| D-96 (예정) | alias map 은 skeleton 정적 선언 (LLM 동적 생성 아님) — 결정론적 매칭 보장 | P1 |
| D-97 (예정) | is_a depth limit = 5 — 순환 방지 | P1 |
| D-98 (예정) | conflict_ledger = append-only (삭제 불가, status 변경만) — 감사 추적성 | P1 |
| D-99 (예정) | dispute_queue = 휘발성, conflict_ledger = 영속 감사 로그 — 독립 구조 | P1 |
| D-120 | P3/P2 Gate REVOKED — LLM parse 경로 미검증, 실 벤치 0 claims | P3/P2 |
| D-121 | SI-P3 (3단계) 폐기 → SI-P3R (snippet-first 2단계)로 대체 | P3R |
| D-122 | silver `p3-*` trial 디렉터리 historical evidence로 보존 | P3R |
| D-123 | Bronze `bench/japan-travel/` read-only 유지 | P3R |
| D-124 | provider_entropy 메트릭 제거 (Tavily 단일) | P3R |
| D-125 | P3R Gate PASS = acquisition 검증 기준. full readiness gate와 분리 | P3R |
| D-126 | gap_resolution 병목 별도 조사 (remodel 이전 0.437@10c) | Gap-Res |
| D-127 | P2 Gate는 remodel on/off 비교 실험으로 재설계 | P2 재판정 |
| D-128 | 우선순위: res_rate 조사 → P2 비교 → P4~P6 | 전체 |
| D-129 | target_count cap은 Phase 5(`b122a23`)에서 의도적 제거 — 재도입 금지 | Gap-Res B1 `2a01197` |
| D-130 | Secondary 병목 실체 없음 — `resolved/claims`는 snippet-first(1:N fan-out) 구조상 낮음, `resolved/targets` ≈ 90-100%. 추가 fix 불필요 | Gap-Res C+D |
| D-131 | SI-P2 재판정 착수 조건: Gap-Res PASS (0.99) 달성 → P2 remodel on/off 비교 실험 착수 가능 | Gap-Res D |
| D-132 | Smart Remodel Criteria: has_critical → 3-way OR (audit_critical, growth_stagnation KU<5/3c, exploration_drought GU<30/5c) | P2 재판정 |
| D-133 | merge min_overlap_count ≥ 2 필터 — 1-field overlap 과다 merge 방지 | P2 재판정 |
| D-134 | Gini criteria는 P4 category management로 연기 | P2 → P4 |
| D-135 | P4 scope reframe — Internal Foundation(A~D) PASS + External Anchor(Stage E) 분리. novelty 0.127 은 cycle-diff 수렴 신호로 재해석 (L3 gap_rule 의 category_gini 0.37→0.20 + 신규 KU 로 미션 기여 입증). Stage E 는 skeleton 외부 미탐 해결 | P4 |
| D-136 | gap_rule(L3) + exploration_pivot(L5) 상보 관계 — 4-계층 메커니즘 스펙트럼(L1 재배열 / L2 meta / L3 내부 축 증폭 / L4 skeleton 확장 / L5 외부 전략). 중복 아닌 보완 | P4 Stage E |
| D-137 | Universe probe → tiered skeleton (candidate vs active). candidate 는 통계만 유지, active 승격 시에만 HITL-R. HITL 루프 지연 회피 | P4 Stage E |
| D-138 | Exploration pivot 1 cycle 지속 + gap_rule 우선. 동일 cycle 내 L3(GU 생성→다음 cycle) + L5(이번 cycle targets 치환) 중복 발동 금지 | P4 Stage E |
| D-139 | Semi-front 진입 조건 = Stage E Gate PASS. Internal-only 판정만으로 UI 에 "수렴" 표시 시 사용자 기만 | P4 Stage E → semi-front |
| D-144 | collect.py as_completed timeout 120→300s, future.result 60→120s (cycle 진행에 따른 parse 시간 증가 대응) | P4 E7-2 |
| D-145 | as_completed TimeoutError catch → graceful degradation (기존 uncaught → cycle abort) | P4 E7-2 |
| D-146 | --external-anchor / --no-external-anchor 플래그 env override (벤치 비교 시 config 오염 방지) | P4 E7-2 |
| D-147 | llm_budget kill-switch 수정: budget 3→12 (probe 1회 3 LLM calls, 3+3+여유 = 12) | P4 E7-3 |
| D-148 | ext_novelty 산식 재설계: `novel/all_kus` → delta_kus 분모 (이번 cycle 신규 KU만) — 0 수렴 방지 | P4 E7-3 |
| D-149 | exploration_pivot `reach_degraded` 조건 제거 (domains_per_100ku<15 실측 52~57, 구조적 unreachable) | P4 E7-3 |
| D-150 | VP4 R5: category_addition HITL-R → probe_history 실행 횟수 기준 (자동 벤치 경로 허용). 런타임 HITL 로직(promote_candidate) 은 미구현 — future work | P4 E7-3 |
| D-151 후보 | telemetry schema 버저닝: `telemetry.v1` 고정, v2 필요 시 별도 schema 파일 | P5 |
| D-152 후보 | Dashboard 실행 방식: CLAUDE.md Scripts Policy — `run_readiness.py --serve-dashboard` 옵션 통합 or `uvicorn` 직접 실행 (신규 스크립트 금지) | P5 |
| D-153 후보 | 100-cycle fixture: 실 trial 데이터 우선 (stub 금지 원칙), 부재 시 gen_fixture.py 허용 검토 | P5 |
| D-154 | 기존 P6(Multi-Domain)을 **M1**으로 분리 (suspended). 신규 P6 = Consolidation & KB Release (A→B→C) | P6 재구조화 |
| D-155 | KU saturation 작업을 P6-A Inside에 흡수 (별도 phase 없음) | P6-A |
| D-156 | D-151 후보(slug collision) → P6-A5로 확정 실행 | P6-A Outside |
| D-157 | P6-A 실행 순서 (초안): 진단(A1) → Inside(A2~A4) → Outside(A5~A6) → 50c trial. **D-158로 개정됨** | P6-A |
| D-158 | **P6-A Forecastability F-Gate 신설 (A7~A11)**. Smart Remodel + Exploration Pivot 15c 내 충분 발동 + 15c 이후 지속 발동을 15c 데이터로 forecast — 50c A12 선행 조건. A1~A13 재번호 | P6-A |
| D-159 | Remodel/Pivot 임계값 **config 외부화 필수** (`SmartRemodelConfig`, `ExternalAnchorConfig.novelty_*`). 하드코딩 유지 불가 | P6-A7, A8 |
| D-160 | Trigger telemetry는 **log 파싱 아니라 JSON 필드 emit** (`trigger_event` optional). schema backward compat 유지 | P6-A10 |
| D-161 | **Forecast 모델 금지 사항**: Prophet/ARIMA 등 블랙박스 모델 금지. 선형/지수 projection + damping + bootstrap confidence 한정 (설명가능성 우선) | P6-A11 |
| D-171~D-188 | SI-P7 5축 구조 설계 (S1~S5) + Q1~Q14 결정 + F2 α/β + S5a 범위 + graph 위치 + candidate 수명 + 3-layer 테스트 + Skill 2종 | SI-P7 |
| D-189 (잠정 보류) | S5a = critical path blocker (`p7-ab-on` L3 FAIL 기반). Step V 검증 후 재판정 — 단독 원인 단정 금지 | SI-P7 Step V |
| D-190 | Step V 삽입 — Step A/B 전 항목 동작 검증 (V1 snapshot 재파싱 → V2 계측 → V3 ablation → V4 확정) 을 S5a 착수 전에 선결 | SI-P7 Step V |
| D-191 | V3 ablation 설계 — `p7-ab-minus-{axis}` **8c** (cycle 15→8 축소), baseline 재사용 (`p7-ab-on` 상한 / `p7-ab-off` 하한), 의심 축 1~2 개만 1차 실행. 실행 전 사용자 재승인 필수 | SI-P7 Step V |
| D-180 (갱신 2026-04-23) | SI-P7 spec 문서만 `_CC` suffix 유지. dev-docs 는 suffix 없이 네이밍 | SI-P7 |

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
