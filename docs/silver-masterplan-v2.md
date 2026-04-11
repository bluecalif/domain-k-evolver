# Domain-K-Evolver Silver Masterplan (v2)

> Status: Draft for implementation
> Date: 2026-04-11
> Supersedes: `docs/silver-masterplan.md` (v1)
> Inputs: v1 masterplan, `docs/silver-masterplan-sketch.md`, `dev/active/p0-p1-remediation-plan.md`, `docs/design-v2.md`, Phase 4·5 결과

---

## 0. v1 에 대한 비판적 검토

v1 (`silver-masterplan.md`) 은 큰 그림은 정확하지만 실행 문서로서 다음 문제가 있다.

| # | 문제 | 결과 |
|---|------|------|
| 1 | WS(§6) / Phases(§7) / Deliverables(§8) / Acceptance(§9) / Checklist(§15) 가 같은 항목을 4~5번 재진술 | 분량 573 줄, 단일 진실 소스 없음 |
| 2 | "extraction quality improves", "diversity can be reported" 등 **정량 임계치 없는 Gate** | 완료 여부 판정 불가 |
| 3 | Phase 4·5 에서 이미 구현된 audit / policy evolution / staleness 를 무시하고 "Bronze 기준선" 전제 | WS5 (Outer-Loop) 중복, WS1 (Foundation) 의 일부는 이미 완료 |
| 4 | Dashboard 를 §5.3 / WS6 / Phase 5 에 나열만, **기술 스택·API 계약·데이터 프레시니스**는 미정의 | 스프롤 위험 (v1 §12 이 스스로 경고) |
| 5 | Fetch/crawl 확장 계획에 **robots.txt·저작권·레이트 리밋·JS 렌더링·한글 소스** 이슈 전무 | 2차 도메인 검증 시 폭발 |
| 6 | LLM/검색 **비용 예산** 개념이 없음. "fetch-first" 로 가면 cycle 당 비용 3~5배 증가 가능 | 운영 불가 |
| 7 | WS ↔ Phase ↔ 우선순위의 **의존성 그래프**가 없음. §13 의 7 단계 권장순서는 있으나 블로커 관계 미표시 | 병렬화·리스크 관리 불가 |
| 8 | "secondary domain 통과" 가 §9 에만 고립 — 어느 Phase 의 exit gate 인지 불명 | 검증 누락 위험 |
| 9 | Non-goals(§2.2) 가 추상적 4 줄. scope creep 방어력 부족 | Gold 범주 유입 위험 |
| 10 | Risks(§12) 는 5 개 문장뿐. likelihood/impact/완화책 매트릭스 없음 | 거버넌스 근거 없음 |

v2 는 이 10 가지를 모두 처리하며, **단일 진실 소스 = Phase 표** 원칙으로 재구성한다.

---

## 1. 목적 및 Silver 정의

**Silver = Bronze 루프를 운영 가능 (production-grade) 한 형태로 굳힌 세대.**

완료 조건 (요지):

1. **수집 폭 ↑** — snippet-only → search + fetch + (선택) 대체 provider
2. **무결성 ↑** — silent failure 제거, alias/is_a 해상도, state I/O 복구
3. **자기개선 ↑** — outer-loop remodel (audit 확장) 이 실제 graph path 로 실행
4. **가시성 ↑** — 운영자용 대시보드 + telemetry 계약
5. **도메인 무관성 검증** — 2 nd 도메인에서 smoke cycle 통과

### Non-Goals (엄격)

- 비즈니스 패키징·수익화·다중 테넌시 (→ Gold)
- 완전 자율 (HITL 제거) — Silver 는 HITL 우선순위 큐 개선만
- 도메인별 온톨로지 완전성 — 프레임워크 레벨 일반화만
- 모바일 UI·권한 관리·SSO — 대시보드는 단일 운영자 데스크탑 기준

---

## 2. 현재 상태 Δ (v1 이 누락한 것)

메모리·코드 스캔 (2026-04-11) 기준, Phase 4·5 완료 이후의 **실제 gap** 은 다음과 같다.

| 영역 | 완료 | 부분 | 미착수 |
|------|------|------|--------|
| Outer-Loop | `audit.py` (4 분석함수), `policy_manager` (apply/rollback/credibility), `readiness_gate` (VP1~3), 동적 T6/T7 trigger | — | `nodes/remodel.py` (구조 변경 제안 노드), phase transition 저장 모델 |
| Inner-Loop Quality | axis_tags 전파, staleness refresh (D-62~D-66), adaptive cap, multi-evidence boost | — | — |
| Collection | search_adapter retry, ThreadPoolExecutor 병렬 | top-2 URL fetch, 3000 chars 컷오프 (`collect.py:88-95`) | fetch-first 파이프라인, 대체 provider, 소스 provenance 스키마, robots.txt 가드 |
| Foundation (P0/P1) | — | — | P0-1 collect 로깅, P0-2 timeout, P0-3 retry 정규표현, P0-4 remodel, P1-1 conflict evidence, P1-2 alias/is_a, P1-3 테스트, P1-4 state I/O 복구 |
| Observability | metrics_logger, metrics_guard, plateau_detector | — | telemetry 계약 (JSON schema), 대시보드 UI, HITL 큐 뷰 |
| Multi-Domain | japan-travel 단일 | — | 2 nd 도메인 선정·smoke run |

**결론**: v1 이 "Phase 0 = P0/P1 remediation" 으로 묶은 8 건은 **여전히 전부 열려 있다**. 단 WS5 의 audit / policy evolution 부분은 이미 Phase 4 에서 마무리됐고, Silver 에서는 **remodel 노드와 phase transition** 만 남는다.

---

## 3. 아키텍처 (요지)

```
Inner Loop (Silver v2):
  seed → [HITL-S: phase 첫 cycle 만] → mode → plan → collect →
  integrate → critique → plan_modify → (next)

  • HITL-E : collect_failure / conflict_rate / fetch_failure / cost_regression
             임계 위반 시에만 auto-pause (예외 기반, 일반 cycle 은 무개입)
  • HITL-D : dispute_resolver auto-resolve 실패 KU 를 state.dispute_queue 에
             append — 비블로킹, 대시보드에서 배치 검토

Silver 추가:
  • collect: SEARCH (provider) + FETCH (공용 pipeline) + PARSE 3 단계 분리
  • integrate: alias/is_a 해상도, conflict ledger
  • critique: novelty / overlap / coverage deficit 근거 제시

Outer Loop:
  inner × N → audit (기존) → remodel (신규) → [HITL-R]
              → phase bump → (다음 phase 의 첫 cycle)

Observability:
  모든 노드 → telemetry stream (JSON) → aggregate store → dashboard

→ HITL 정책 상세 §14, Provider 구조 상세 §13, 테스트 벤치 규칙 §12.
```

**핵심 불변**: Bronze 의 5 대 원칙 (Gap-driven, Claim→KU, Evidence-first, Conflict-preserving, Prescription-compiled) 은 Silver 에서도 machine-checkable 로 유지.

---

## 4. Phase 표 (단일 진실 소스)

각 Phase 행은 **Goal → Deliverables → Gate (정량) → Depends on** 을 담는다. WS 는 Phase 에 매핑된 라벨이며 별도 계획이 아니다.

### P0. Foundation Hardening

- **Goal**: silent failure 제거, Silver 의 모든 후속 작업이 의지할 안전 기반 확보
- **WS**: WS1
- **Deliverables**:
  - **P0-0 Silver 테스트 벤치 스캐폴딩** — `bench/silver/` 디렉토리, `INDEX.md` 템플릿, `p0-{date}-baseline` trial 생성 (§12 참조). P0 의 첫 task.
  - P0-1 collect 예외 로깅 + `collect_failure_rate` metric
  - P0-2 `LLMConfig.request_timeout=60`, `SearchConfig.request_timeout=30`, ThreadPoolExecutor timeout
  - P0-3 retry 판정 정규표현 수정 (`429|5\d\d|rate`)
  - P1-1 integrate conflict evidence ValueError 로깅
  - P1-3 collect 테스트 확장 (timeout / malformed JSON / empty / 중복)
  - P1-4 state_io JSON 복구 + 필수필드 검증 + `--bench-root` 플래그
  - **P0-H HITL 축소** — `graph.py` 에서 inline HITL-A/B/C edge 제거, `HITL-E` 조건부 분기 추가, `hitl_gate.py` 를 HITL-S/R 전용으로 축소 (§14 참조)
- **Gate (정량)**:
  - [ ] 대상 모듈 bare-except 0 건 (`grep "except Exception:" src/nodes/` 결과)
  - [ ] `collect_failure_rate`, `timeout_count`, `retry_success_rate` 3 지표가 metrics_logger 에 emit
  - [ ] 신규/수정 테스트 ≥ 20 건, 전체 green (현재 468 → ≥ 488)
  - [ ] 48h soak: 임의 adapter kill → 그래프 hang 없음
  - [ ] `bench/silver/japan-travel/p0-{date}-baseline/` 가 존재하고 Phase 4·5 동등 스모크를 해당 trial 로 재현 (VP1 ≥ 4/5, VP2 ≥ 5/6)
  - [ ] 일반 cycle 실행 시 인라인 HITL-A/B/C 호출 0 건 (graph edge 기준), HITL-S 는 첫 cycle 1 회, HITL-E 는 예외 시만
- **Depends on**: 없음 (즉시 착수)

### P1. Entity Resolution & State Safety

- **Goal**: 구조적 무결성 — alias / is_a / conflict ledger
- **WS**: WS3 일부
- **Deliverables**:
  - P1-2 `src/utils/entity_resolver.py` (`resolve_alias`, `resolve_is_a`)
  - `integrate.py._find_existing_ku` 에 resolver 연동
  - conflict ledger 파일 (`state/conflict_ledger.json`) — 해결/미해결 분리
  - skeleton `aliases` / `is_a` 필드 validator
- **Gate (정량)**:
  - [ ] 단위 테스트: 동의어 (JR-Pass / 재팬레일패스), 상속 (shinkansen is_a train) 각각 pass
  - [ ] japan-travel 재실행: 중복 KU 수 ≥ 15% 감소
  - [ ] 충돌 KU 100% 가 ledger 에 영구 보존 (해결 후에도 감사 가능)
- **Depends on**: P0 (state_io 안전성)

### P2. Outer-Loop Remodel 완결

- **Goal**: audit 결과를 실제 구조 변경 액션으로 compile
- **WS**: WS5
- **Deliverables**:
  - `src/nodes/remodel.py` — entity merge/split, 카테고리 재분류, source 정책 변경, gap 생성 규칙 변경 제안 생성
  - `schemas/remodel_report.schema.json`
  - `graph.py` — `cycle % 10 == 0 and audit.has_critical` → remodel 경로, HITL-R 승인 gate
  - phase transition 저장 (`state/phase_{N}/...`) — 과거 phase 보존
  - 테스트: merge / split / reclassify / rollback 4 시나리오
- **Gate (정량)**:
  - [ ] 합성 시나리오에서 entity 중복률 30%+ 상황을 remodel 이 탐지·제안
  - [ ] HITL 승인 → 다음 cycle skeleton 이 실제 변경됨
  - [ ] rollback 경로가 승인 전 상태로 복귀 (state diff = ∅)
- **Depends on**: P0, P1

### P3. Acquisition Expansion

- **Goal**: snippet 의존 탈피, 소스 다양성 측정 가능화
- **WS**: WS2
- **Deliverables**:
  - **Provider 플러그인 구조** — `src/adapters/providers/` 신설 (`base.py` Protocol, `tavily_provider.py`, `ddg_provider.py`, `curated_provider.py`). **SEARCH 단계만 담당** (§13 참조).
    - `TavilyProvider` — 기본, `search_adapter.py` 의 retry/backoff 재사용
    - `DuckDuckGoProvider` — optional fallback, `domain_entropy < 2.0` 또는 Tavily 실패 시에만
    - `CuratedSourceProvider` — v2 초안의 `FetchOnlyProvider` **개명**. 검색 안 함, skeleton 의 `preferred_sources` 중 `axis_tags`/`category` 매칭 URL 반환, `trust_tier="primary"`
  - **공용 `FetchPipeline`** (`src/adapters/fetch_pipeline.py`) — provider 무관, robots.txt / content-type allowlist / timeout / max_bytes / trust_tier 태깅을 한 곳에서 처리 (FETCH 단계)
  - `collect.py` — SEARCH (providers) → FETCH (pipeline) → PARSE (claims) 3 단계로 리팩터. fetch top-K, 본문 최대 길이, 병렬 처리
  - Provenance 스키마 확장: `{providers_used, domain, fetch_ok, fetch_depth, content_type, retrieved_at, trust_tier}`
  - `SearchConfig` 확장: `enable_tavily`, `enable_ddg_fallback`, `fetch_top_n`, `max_bytes_per_url`, `entropy_floor`, `k_per_provider`
  - Source diversity metric: `domain_entropy`, `provider_entropy` per cycle
  - 비용 가드: `cycle_llm_token_budget`, `cycle_fetch_bytes_budget` — 초과 시 경고 + degrade
- **Gate (정량)**:
  - [ ] fetch 성공률 ≥ 80% on japan-travel seed queries
  - [ ] claim 당 평균 EU 수 ≥ 1.8 (현재 ≈ 1.0 추정)
  - [ ] `domain_entropy` ≥ 2.5 bits (≥ 6 고유 도메인 평형 기여) on ref cycle
  - [ ] cycle 당 LLM 비용 ≤ baseline × 2.0 (비용 regression 방지)
  - [ ] robots.txt 거부 도메인 차단 테스트 pass
- **Depends on**: P0 (timeout/retry)

### P4. Coverage Intelligence

- **Goal**: plan 이 novelty · overlap · deficit 를 근거로 target 선택
- **WS**: WS4
- **Deliverables**:
  - `src/utils/novelty.py` — cycle-to-cycle Jaccard / token-overlap / entity-overlap
  - `coverage_map` — 축 × 엔티티 그리드, deficit score
  - `plan.py` — target 선택 시 reason code (`deficit:category=food`, `plateau:novelty<0.1`, `audit:merge_pending`)
  - critique 에 metric 기반 처방 (overlap > 0.8 → jump mode, coverage < 0.3 → explore)
- **Gate (정량)**:
  - [ ] plan output 의 모든 target 이 reason code 보유
  - [ ] 10 cycle 연속 run 에서 novelty 평균 ≥ 0.25
  - [ ] 인위적 plateau (동일 seed 5 cycle 반복) → audit/remodel trigger 발동
- **Depends on**: P2 (remodel), P3 (provenance)

### P5. Telemetry Contract & Dashboard

- **Goal**: 운영자가 JSON 파일 없이 상태 파악·개입
- **WS**: WS6
- **Deliverables**:
  - `schemas/telemetry.v1.schema.json` — cycle 단위 snapshot (run_id, phase, cycle, mode, metrics{}, gaps{}, failures{}, hitl_queue[], audit_summary)
  - `src/obs/telemetry.py` — 노드 훅 → aggregate 파일 (`state/telemetry/*.jsonl`)
  - Dashboard: **FastAPI + htmx + Chart.js** (또는 Streamlit 재평가). 단일 운영자용, 인증 없음, localhost 바인딩
  - Views: overview / cycle timeline / gap coverage map / source reliability / conflict ledger / **HITL inbox (3 탭: Seed·Remodel 승인 / Dispute 배치 검토 / Exception 알림, §14 참조)** / remodel review
  - 운영자 가이드 (`docs/operator-guide.md`) — 최대 20 페이지
- **Gate (정량)**:
  - [ ] 모든 view 가 10 s 내 로드 (로컬, 100 cycle 데이터)
  - [ ] telemetry schema contract 테스트 pass (노드 emit → schema validate)
  - [ ] "왜 진행이 느려졌나" 를 대시보드만으로 3 분 내 식별 가능 (기록된 시나리오 기반 self-test)
  - [ ] dashboard 코드 LOC ≤ 2,000 (스프롤 방지 하드 리밋)
- **Depends on**: P0 (metric emit), P3 (provenance), P4 (novelty)

### P6. Multi-Domain Validation

- **Goal**: 프레임워크 도메인 무관성 실증
- **WS**: 검증
- **Deliverables**:
  - 2 nd 도메인 선정 (후보: 국내 부동산 / 오픈소스 LLM 생태계 / 한국 세법) — **선정 기준: 구조가 japan-travel 과 다를 것 (시간축·계층 깊이·출처 언어 중 2 개 이상 이질)**
  - Seed skeleton 작성, 최소 10 cycle smoke run
  - 회고 리포트 (framework 수정 필요항목 vs 도메인 설정으로 처리 가능한 항목 분류)
- **Gate (정량)**:
  - [ ] 10 cycle 내 Gate #5 동등 기준 (VP1 ≥ 4/5, VP2 ≥ 5/6, VP3 ≥ 4/6) 통과
  - [ ] 프레임워크 레벨 코드 수정 ≤ 5 건 (초과 시 프레임워크 일반화 미흡)
  - [ ] 한글 출처 처리 에러 0
- **Depends on**: P3, P4, P5

---

## 5. 의존성 그래프

```
P0 ──┬── P1 ──┐
     │        ├── P2 ──┐
     ├── P3 ──┼────────┤
              └─ P4 ──┼── P5 ── P6
```

병렬화 가능 구간:
- **P1 & P3** — P0 완료 후 동시 착수 (entity resolver ↔ fetch 파이프라인은 독립)
- **P5 의 telemetry contract (schema 부분)** 은 P3 와 동시 정의 가능 (provenance 필드가 공유)

직렬 제약:
- P2 는 P1 필요 (alias 정리가 remodel 제안 품질의 전제)
- P4 는 P2 + P3 필요 (remodel trigger + 소스 다양성이 coverage 계산 근거)
- P6 는 모든 선행 Phase 필요

---

## 6. 공통 측정 (Silver 전반)

### Reliability
`collect_failure_rate`, `fetch_failure_rate`, `timeout_count{adapter}`, `retry_success_rate`, `state_recovery_events`

### Knowledge Quality
`evidence_rate`, `multi_evidence_rate`, `conflict_rate`, `avg_confidence`, `staleness_risk`, `alias_dedup_count`

### Coverage Intelligence
`coverage_by_axis{axis}`, `novelty_score`, `overlap_score_recent`, `domain_entropy`, `provider_entropy`, `unresolved_deficit_count`

### Governance
`hitl_pending`, `dispute_aging_days`, `remodel_proposed`, `remodel_approved`, `phase_transitions_total`

### Cost (v1 에 없던 축)
`llm_tokens_per_cycle`, `fetch_bytes_per_cycle`, `wall_clock_per_cycle_s`, `cost_regression_flag`

---

## 7. 시나리오 테스트 매트릭스

| # | 시나리오 | 기대 | Phase |
|---|----------|------|-------|
| S1 | search timeout (mocked 60 s hang) | retry → fail → metric emit → cycle 계속 | P0 |
| S2 | malformed LLM JSON | deterministic fallback, claims ≥ 1 | P0 |
| S3 | corrupt state.json | backup 복구 or empty 시작 + warning | P0 |
| S4 | 동의어 2 개 (JR-Pass / 재팬레일패스) | 단일 KU 로 병합 | P1 |
| S5 | is_a (shinkansen → train) | parent metric 상속 | P1 |
| S6 | conflict 보존 후 resolve | ledger 에 before/after 모두 조회 가능 | P1 |
| S7 | 저novelty 5 cycle | audit trigger → remodel 제안 | P2/P4 |
| S8 | robots.txt 차단 도메인 | fetch 스킵 + 로그, 다른 소스로 대체 | P3 |
| S9 | 비용 예산 초과 | degrade 모드 (fetch depth ↓) | P3 |
| S10 | dashboard 텔레메트리 1 cycle | schema validate pass | P5 |
| S11 | 2 nd 도메인 10 cycle | Gate #5 통과 | P6 |

각 시나리오는 **Phase gate 의 blocking test**. 미통과 시 해당 Phase 는 complete 선언 불가.

---

## 8. 리스크 레지스터

| ID | 리스크 | L | I | 완화 | Owner |
|----|--------|---|---|------|-------|
| R1 | fetch 확장으로 LLM 비용 3~5 배 증가 | H | H | P3 의 cycle 비용 예산 + degrade 모드, baseline × 2.0 upper cap | P3 |
| R2 | robots.txt / 저작권 위반 | M | H | robots 체크 모듈, content-type 필터, trust_tier 차등 저장, 공개 redistribute 금지 | P3 |
| R3 | remodel 이 state 구조를 파괴 | M | H | phase transition 저장 모델, HITL-R 승인 gate, rollback 경로 (P2 Gate 에 포함) | P2 |
| R4 | 대시보드 스프롤 → 별도 제품화 | M | M | LOC 2000 하드 리밋, htmx 단일 운영자 범위, 인증 / 모바일 비범위 | P5 |
| R5 | 2 nd 도메인 선정이 japan-travel 과 너무 유사 | M | M | 선정 기준 3 개 중 2 개 이질 강제, 회고 시 프레임워크 수정 건수 ≤ 5 | P6 |
| R6 | P0/P1 이 급격히 커져 다른 Phase 지연 | M | M | P0 은 scope-locked (위 8 건 외 추가 금지), 새 발견은 P1 Phase 로 이관 | P0 |
| R7 | DuckDuckGo / alt-provider 의 rate limit / TOS 위반 | M | M | alt-provider 는 optional fallback 으로만, 기본은 Tavily | P3 |
| R8 | 한글 출처 처리에서 인코딩·형태소 이슈 | M | M | P6 에 `utf-8` 강제 + 한글 테스트 케이스 포함 (CLAUDE.md 인코딩 규칙 준수) | P6 |
| R9 | Phase 병렬화가 conflict 유발 | L | M | P1/P3 동시 착수 시 공유 모듈 (`integrate.py`, `collect.py`) 의 인터페이스 계약을 P0 종료 시점에 고정 | P0 |
| R10 | HITL-D 배치 큐 (`dispute_queue`) 적체 | M | M | 배치 검토 UI 를 P5 대시보드 Day 1 기능으로 포함, `dispute_queue > 20` 시 자동 HITL-E 로 승격 (=auto-pause), 큐 aging 메트릭 경보 | P5 |

L/I = Low / Med / High. 리스크는 Phase gate review 때마다 재평가.

---

## 9. 실행 순서 권장

```
week  1- 2 : P0 (scope-locked, 8 건)
week  3- 5 : P1 + P3 병렬
week  6- 7 : P2 (P1 완료 후)
week  8- 9 : P4
week 10-12 : P5 (telemetry schema 는 P3 와 함께 선정의)
week 13-14 : P6 (2 nd 도메인)
week 15    : Silver readiness review (Gate #6)
```

주차는 순서 기준이며 캘린더 약속은 아님. Phase gate 통과가 진행의 trigger.

---

## 10. 수용 기준 (Silver 완료)

다음이 모두 true 일 때 Silver 를 닫는다.

- [ ] P0~P6 **모든 Phase gate 의 정량 조건** 통과 (§4 체크박스)
- [ ] 11 개 시나리오 (§7) 전부 pass
- [ ] 5 대 불변원칙 machine-check 가 Silver 브랜치에서 green
- [ ] LOC·비용·테스트 수 regression 없음 (Phase 5 baseline: 468 tests, cycle 비용 baseline 기록)
- [ ] 운영자 가이드 존재, 5 페이지 이상 손으로 따라 할 수 있음
- [ ] 2 nd 도메인 smoke run 이 framework 수정 ≤ 5 건으로 통과
- [ ] Silver readiness 리포트 (Gate #6) 승인

---

## 11. v1 대비 변경 요약

| 영역 | v1 | v2 |
|------|----|----|
| 분량 | 573 줄 | ~500 줄 |
| 구조 | WS / Phase / Deliv / Acceptance / Checklist 5 중 재진술 | Phase 표 단일 진실 소스 |
| Gate 조건 | 정성적 ("improves", "visible") | 정량 임계치 + blocking test |
| 현재 상태 인식 | Bronze 기준선 가정 | Phase 4·5 완료 Δ 반영, remodel 만 잔여 |
| 비용·윤리 | 없음 | 비용 예산 가드, robots.txt, 저작권, 한글 인코딩 |
| 리스크 | 5 문장 | 10 건 레지스터 (L/I/완화/Owner) |
| 의존성 | §13 권장 순서만 | 명시 그래프, 병렬화·직렬 제약 구분 |
| 대시보드 스코프 | 뷰 나열만 | 스택 후보·LOC 리밋·비범위 고정 |
| 2 nd 도메인 | §9 에 orphan | P6 Phase + 선정 기준 + gate |
| Non-goals | 추상 4 줄 | scope creep 방어 구체화 |
| **테스트 벤치 관리** | 규정 없음 (`japan-travel-auto` 1 벌) | `bench/silver/{domain}/{trial_id}/` + `INDEX.md` + 네이밍 규칙 (§12) |
| **Provider 구조** | `FetchOnlyProvider` 명명 + fetch 혼재 | SEARCH / FETCH / PARSE 3 단계 분리, `CuratedSourceProvider` 개명 (§13) |
| **HITL 구조** | cycle 당 HITL-A/B/C 3 회 + HITL-R | HITL-S / HITL-R (blocking) + HITL-D (배치) + HITL-E (예외) 4 세트, 인라인 0 (§14) |

---

## 12. Silver 테스트 벤치 관리 (pre-P0)

**목적**: Phase × Trial 단위로 독립·재현 가능한 벤치 저장소. v2 초안이 비워둔 공백을 메운다. P0 의 첫 task 로 스캐폴딩, 이후 모든 Silver 측정은 trial 디렉토리 내부에서만 이루어진다.

### 12.1 디렉토리 구조

```
bench/
├── japan-travel/                           # Bronze 레거시, read-only
├── japan-travel-auto/                      # Phase 4·5 산출물 (archive 포인터만 유지)
└── silver/
    ├── INDEX.md                            # 모든 trial 레지스트리
    ├── japan-travel/                       # 1 차 도메인
    │   ├── p0-20260412-baseline/
    │   │   ├── trial-card.md               # 실행 전: goal + config diff + 가설
    │   │   ├── config.snapshot.json        # src/config.py + git sha + provider list + seed hash
    │   │   ├── state/                      # KU / GU / conflict_ledger
    │   │   ├── trajectory/                 # cycle 별 planned/actual
    │   │   ├── telemetry/                  # telemetry.v1 jsonl
    │   │   └── readiness-report.md         # 실행 후: VP1/VP2/VP3 결과 + diff 해석
    │   ├── p3-20260420-fetchfirst-v1/
    │   └── p3-20260420-fetchfirst-v1-run2/ # 동일 config 재실행
    └── realestate/                         # 2 차 도메인 (P6)
        └── p6-20260510-smoke/
```

### 12.2 네이밍 규칙

```
trial_id = {phase}-{YYYYMMDD}-{short_tag}[-run{N}]

  phase      ∈ {p0, p1, p2, p3, p4, p5, p6}
  date       실행 시작일 (KST)
  short_tag  kebab-case, ≤ 20 chars
             예: baseline, fetchfirst-v1, ddg-fallback, remodel-merge, alias-is-a
  run{N}     동일 config 재실행 시 (크래시 복구·통계 표본)
```

### 12.3 운영 규칙

1. **Baseline 의무** — `p0-{date}-baseline` 은 P0 완료 gate 의 요건. 모든 이후 trial 은 이 baseline 과 diff 가능해야 한다.
2. **격리** — trial 내부 파일은 다른 trial 이 절대 쓰지 않는다. `state_io` 에 `--bench-root` 플래그 (P1-4 deliverable 에 포함) 로 경로 격리.
3. **전·후 문서 2 종** — `trial-card.md` (실행 전: goal / config diff / 가설) → `readiness-report.md` (실행 후: gate 결과 / 권고). `trial-card` 없이 실행 금지.
4. **재현성 snapshot** — `config.snapshot.json` 은 `src/config.py` dataclass 직렬화 + `git rev-parse HEAD` + 활성 provider list + seed skeleton hash. 실행 시작 시 자동 기록.
5. **Phase gate 는 trial 내부 판정** — cross-trial 비교는 `INDEX.md` 와 개별 `readiness-report.md` 에만. Phase 표 (§4) 의 gate 체크는 "어느 trial 에서 통과했나" 가 기록됨.
6. **폐기 ≠ 삭제** — 실패/폐기 trial 은 `status = archived` 로 두고 디렉토리 보존 (실험 실패도 증거).

### 12.4 INDEX.md 스키마

```
| trial_id                          | domain       | phase | date       | goal                          | status   | readiness       | notes |
|-----------------------------------|--------------|-------|------------|-------------------------------|----------|-----------------|-------|
| p0-20260412-baseline              | japan-travel | p0    | 2026-04-12 | P0 완료 증명 baseline           | complete | VP1=5/5 VP2=6/6 | -     |
| p3-20260420-fetchfirst-v1         | japan-travel | p3    | 2026-04-20 | fetch-first 파이프라인 초도검증    | running  | -               | -     |
| p3-20260420-fetchfirst-v1-run2    | japan-travel | p3    | 2026-04-21 | 동일 config 통계표본             | complete | VP1=5/5 VP2=5/6 | 분산 측정 |
```

---

## 13. Provider 플러그인 상세

### 13.1 개념 분리 (v2 초안의 혼란 제거)

v2 초안은 "provider" 와 "fetch" 를 한 추상에 넣어 혼란을 유발했다. 실제 collect 흐름은 3 단계이며, provider 는 Step 1 만 책임진다.

```
Step 1. SEARCH  : query → [SearchResult]          (provider 의 책임)
Step 2. FETCH   : url → body                      (공용 FetchPipeline 의 책임)
Step 3. PARSE   : (results + bodies) → claims    (collect_node 의 책임)
```

### 13.2 인터페이스

```python
class SearchProvider(Protocol):
    provider_id: str  # "tavily" | "ddg" | "curated"

    def search(
        self,
        query: str,
        k: int,
        context: PlanContext,  # category, axis_tags, cycle
    ) -> list[SearchResult]: ...

@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str       # 제공사 제공 요약 (없으면 "")
    score: float       # provider 고유 랭킹, 0~1 정규화
    provider_id: str
    trust_tier: str    # "primary" | "secondary" | "community"
```

### 13.3 3 개 구현

| Provider | 동작 | 사용 트리거 | trust_tier 기본 | 비용 | Rate limit |
|----------|------|-------------|-----------------|------|------------|
| **TavilyProvider** (기본) | Tavily API 호출, LLM 친화적 snippet. `tavily-python` + `search_adapter.py` 의 `_retry_with_backoff` 재사용 | 모든 cycle 기본 활성 | allowlist (gov/official → primary, 그 외 secondary) | 월 크레딧 유료 | O (초·월) |
| **DuckDuckGoProvider** (optional) | `duckduckgo-search` 라이브러리, HTML scraping, API key 없음 | (a) Tavily 실패 fallback, (b) `domain_entropy < entropy_floor` 일 때 다양성 보강 | secondary | free | 엄격 (IP 기반), 기본 off |
| **CuratedSourceProvider** (v2 초안 `FetchOnlyProvider` **개명**) | **검색 안 함**. skeleton 의 `preferred_sources` 중 `context.axis_tags` / `category` 매칭 URL 반환. `snippet="curated"`, `score=1.0` | `preferred_sources` 가 정의된 category 조회 시 항상 우선 | primary | free | 사실상 없음 (공식 사이트 ToS) |

### 13.4 호출 패턴 (`collect_node`)

```python
# 1. Provider 선택 (policy 기반)
providers = [CuratedSourceProvider(skeleton)]
if policy.enable_tavily:
    providers.append(TavilyProvider(config.search))

# 2. 검색 병렬 실행
all_results: list[SearchResult] = []
for p in providers:
    try:
        all_results.extend(p.search(query, k=policy.k_per_provider, context=ctx))
    except ProviderError as e:
        logger.warning("provider %s failed: %s", p.provider_id, e)

# 3. 다양성 부족 시 DDG fallback
if domain_entropy(all_results) < policy.entropy_floor and policy.enable_ddg_fallback:
    all_results.extend(DuckDuckGoProvider().search(query, k=3, context=ctx))

# 4. URL dedupe + top-N 선정
urls = dedupe_and_rank(all_results, top_n=policy.fetch_top_n)

# 5. FETCH 파이프라인 (provider 무관, 공용 단계)
bodies = FetchPipeline.fetch_many(
    urls,
    robots_check=True,
    max_bytes=policy.max_bytes_per_url,
    content_type_allowlist={"text/html", "application/xhtml+xml"},
    timeout=config.search.request_timeout,
)

# 6. PARSE — claims 추출 + provenance 태깅
claims = parse_claims(gu, all_results, bodies, provenance={
    "providers_used": [p.provider_id for p in providers],
    "fetch_ok_count": sum(1 for b in bodies if b.ok),
    "domain_set": {urlparse(r.url).netloc for r in all_results},
})
```

### 13.5 개명 근거

`FetchOnlyProvider` 라는 이름은 "provider 가 fetch 를 한다" 고 읽혀 Step 1 / Step 2 경계를 흐린다. `CuratedSourceProvider` 는 "큐레이션된 소스 제공자 = 검색 안 하고 이미 알려진 URL 을 돌려준다" 는 의도가 명확하다. FetchPipeline 은 그 뒤에 공용 단계로 작동하므로 어떤 provider 도 fetch 를 "소유" 하지 않는다.

### 13.6 P3 에 추가될 파일

- `src/adapters/providers/__init__.py`
- `src/adapters/providers/base.py` — `SearchProvider` Protocol + `SearchResult`
- `src/adapters/providers/tavily_provider.py` — 기존 `search_adapter.py` 리팩터
- `src/adapters/providers/ddg_provider.py` — 신규
- `src/adapters/providers/curated_provider.py` — 신규
- `src/adapters/fetch_pipeline.py` — robots / content-type / timeout / max_bytes 가드
- `src/config.py` — `SearchConfig` 에 `enable_tavily`, `enable_ddg_fallback`, `fetch_top_n`, `max_bytes_per_url`, `entropy_floor`, `k_per_provider` 추가

---

## 14. HITL 정책 축소

### 14.1 원칙

HITL 은 다음 3 조건 중 하나를 만족할 때만 유지한다. 나머지는 자동화하거나 배치 검토로 이연한다.

1. **Irreversible** — structural 변경, policy 영구 수정 (돌이키는 비용 > 개입 비용)
2. **Auto-resolver 실패** — 결정론적·통계적 처리가 먼저 시도되고, 결과가 불확실할 때만 사람에게 넘김
3. **Trust boundary crossing** — 새 domain / provider / skeleton 등록

### 14.2 기존 HITL 현황과 조치

| HITL | 위치 (graph edge) | 빈도 | 본질 | 조치 |
|------|-------------------|------|------|------|
| HITL-A (plan) | `plan → HITL-A → collect` | 매 cycle | plan 승인 | ❌ **제거** — critique/mode 가 rationale 보유, 결과는 다음 cycle 에서 복구 가능 (reversible) |
| HITL-B (collect) | `collect → HITL-B → integrate` | 매 cycle | 수집 결과 승인 | ❌ **제거** → `HITL-E` 예외로 이관 |
| HITL-C (integrate) | `integrate → HITL-C → critique` | 매 cycle | 통합 결과 승인 | ❌ **제거** → `HITL-D` 배치 + `HITL-E` 예외로 분리 |
| HITL-R (remodel) | outer-loop, 미구현 | audit 후 | 구조 변경 승인 | ✅ **유지** (irreversible) |

### 14.3 Silver v2 HITL 세트

| HITL | 트리거 | 인터럽트 | 근거 | 구현 |
|------|--------|----------|------|------|
| **HITL-S** (Seed) | phase 시작 1 회 (새 도메인 / remodel 후 phase bump) | blocking | skeleton 정의 = trust boundary + irreversible | `seed_node` 직후 1 회 gate |
| **HITL-R** (Remodel) | `remodel_node` 가 제안 생성 시 | blocking | structural, irreversible | P2 의 `remodel_node` 직후 gate |
| **HITL-D** (Dispute batch) | `dispute_resolver` auto-resolve 실패 KU 누적 | **non-blocking** — cycle 계속, state 의 `dispute_queue` 에 append | auto-resolver 실패 (조건 2) | 대시보드 inbox (P5), 체크박스 일괄 승인 |
| **HITL-E** (Exception) | 임계치 위반 시에만: `collect_failure_rate > 0.3` / `conflict_rate > 0.4` / `fetch_failure_rate > 0.5` / `cost_regression_flag=true` / `dispute_queue > 20` | blocking (auto-pause + 대시보드 알림) | 예외 상황만 개입 | `metrics_guard` 확장, `graph.py` 조건부 edge |

### 14.4 효과

- **일반 cycle = 100% 자동 진행** — `HITL-S` / `HITL-R` 는 cycle 내부가 아니라 경계 이벤트
- 운영자 개입 빈도: cycle 당 3~4 회 → **Phase 당 2~3 회 + 예외 발생 시**
- `HITL-D` 의 배치 검토는 P5 대시보드의 **핵심 view** 로 승격 (R10 리스크 연결)

### 14.5 Graph 변경 (P0 에 포함)

- `graph.py` 에서 `plan → HITL-A → collect` edge 를 `plan → collect` 로 단순화
- `collect → HITL-B → integrate` 를 `collect → integrate` 로, `HITL-E` 조건부 분기 추가
- `integrate → HITL-C → critique` 를 `integrate → critique` 로, dispute 는 `state.dispute_queue` append
- `src/nodes/hitl_gate.py` 는 `HITL-S` / `HITL-R` 전용으로 축소. 호출 지점만 줄이고 인터페이스는 보존 (backward 안전)

### 14.6 Dashboard 연결 (P5 에 반영)

- `HITL inbox` view 에 탭 3 개: `[Seed/Remodel 승인]` / `[Dispute 배치 검토]` / `[Exception 알림]`
- 배치 검토는 체크박스 다중 선택 → `approve all` / `reject all` / `edit selected`
- Exception 알림은 실시간 push 없음 (운영자가 대시보드 열 때 표시). `HITL-E` 트리거 시 CLI 알림 (`stderr`) 만.

---

## 15. 다음 액션

1. `bench/silver/` 스캐폴딩 + `INDEX.md` 템플릿 + `trial-card.md` / `readiness-report.md` 템플릿 작성 (P0 첫 task).
2. P0 backlog 를 `dev/active/phase-si-p0-foundation/` 로 이전 (기존 `p0-p1-remediation-plan.md` 를 base 로 재구조화, P0-0 / P0-H 신규 항목 반영).
3. `src/adapters/providers/base.py` Protocol 초안을 P3 인터페이스 동결 목적으로 stub 작성 — P3/P5 동시 정의를 가능케.
4. Telemetry schema 초안 (`schemas/telemetry.v1.schema.json`) 에 `dispute_queue`, `providers_used`, `trial_id` 필드 포함.
5. `graph.py` 의 HITL-A/B/C edge 제거 계획을 P0 후반부 task 로 분리 (graph 테스트 회귀 최소화).
6. Silver readiness 리포트 템플릿을 `templates/si-readiness-report.md` 에 작성.
7. 2 nd 도메인 후보 3 개 (부동산 / OSS LLM 생태계 / 세법) 를 Phase 5 완료 시점까지 scoping.
8. `dev/active/p0-p1-remediation-plan.md` 를 deprecated 표기하고 링크를 v2 로 갱신.
