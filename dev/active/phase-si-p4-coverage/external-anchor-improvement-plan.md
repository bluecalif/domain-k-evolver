# External Anchor Improvement Plan (Stage E)

> 작성일: 2026-04-15
> 기준 문서:
> - `mission-alignment-critique.md` (내 비판)
> - `mission-alignment-opinion.md` (그에 대한 피드백)
> 목적: 두 문서를 결합해 **구현 가능한** 개선 계획 수립. P4 Gate 재판정 근거 제공.

---

## 0. Opinion 문서에 대한 비판적 평가

### 받아들이는 제안 (Accept)

| # | Opinion 주장 | 수용 이유 |
|---|---|---|
| 1 | P4를 "Internal Coverage Foundation" 으로 정직하게 재명명 | 기존 구현 가치 보존 + 미션 정렬 명확화. 둘 다 달성. |
| 2 | 전면 재설계 아닌 "얇은 external layer 추가" | 기존 `novelty.py`, `plan.py` reason_code, `plateau_detector.py`, remodel hook이 이미 접점 제공. 재사용이 합리적. |
| 3 | Stage E (External Anchor) 별도 게이트 후 최종 통과 판정 (Option 1) | Option 2 (P4 안에 흡수)는 범위 혼탁 + 실 벤치 비교 불가. Stage E 분리가 깔끔. |
| 4 | External novelty 첫 구현은 entity_key 기준 history | 구현 난이도 낮음 + 검증 용이. 의미가 아닌 정체성 기준 → 신뢰 가능. |
| 5 | Universe probe 결과는 **제안 생성**이어야 (자동 확장 아님) | skeleton 오염 방지. 기존 category_addition HITL-R 경로 재사용 가능. |
| 6 | Reason_code 로 external 신호를 planning 에 주입 | 기존 B1 구조 완성도 덕분. 배관 이미 있음. |
| 7 | 7개 minimum success criteria 프레임 | gate 정량 기준 재구성에 그대로 사용 가능. |

### 유지 또는 보강해야 할 지점 (Pushback)

| # | Opinion 주장 | 내 반박 / 보강 |
|---|---|---|
| P1 | "entity_key 기준이면 충분" | **불충분.** 같은 entity 에 새 field/claim/evidence 가 붙는 경우를 놓친다. 최소 `(entity_key, field)` 튜플 수준 + claim-hash 병행. |
| P2 | "Universe probe 는 제안 생성" (HITL 경유) | HITL 매번 경유하면 피드백 루프 사망. **tiered gate** 필요: probe → LLM self-validate → **candidate skeleton** 자동 등재, **active skeleton** 승격만 HITL. |
| P3 | "reach diversity: domain/publisher/language/time/provider 5축" | 현재 Tavily 단일 provider (D-124 폐기 결정). provider 다양성 = 항상 1. publisher/author 도 Tavily snippet 에서 추출 가능한지 실측 전엔 불명. **실제 얻을 수 있는 축만** 확정하고 나머지는 placeholder. |
| P4 | "plateau pivot: 더 넓은 query, 다른 provider..." | **"더 넓은 query" 를 어떻게 생성하는가** 가 빠짐. LLM query-rewriter + axis-swap 규칙 같은 구체 메커니즘 없으면 hand-waving. 구현 스펙 필요. |
| P5 | Opinion 은 비용 고려 없음 | feedback_api_cost_caution 에 정면 충돌. Universe probe × cycle × 도메인 → LLM + broad Tavily 비용 비선형. **per-cycle 예산 상한 + kill-switch** 필수. |
| P6 | "현재 P4 Gate FAIL → 이름 바꾸고 PASS" 가 암묵적 | 그냥 이름 바꾸는 건 회계적 조작. **internal scope 한정 PASS** 는 허용하되 근거 명시 (novelty 실측 0.127 의 해석을 "internal cycle-diff 정체 = 구조 올바름" 으로 재기술). |
| P7 | Minimum criteria 가 전부 시스템 내부 지표 | 새 측정이 **정말로 측정하고자 한 것을 측정하는지** 검증 없음. **synthetic injection test** 필요 (숨긴 카테고리 삽입 → universe probe 가 표면화하는지). |
| P8 | Run 단위 reach diversity ledger | multi-run 비교 기준 없음. regression 판정 불가. **normalization (per-target KU 기준)** 필요. |

---

## 1. 합의된 방향

1. 현재 P4 는 **Internal Coverage Foundation** 으로 재명명. 현재 Gate 판정은 **internal scope 한정 PASS** (novelty 0.127 을 "cycle-diff 수렴 정상"으로 재해석 + 근거 문서화).
2. **Stage E: External Anchor** 를 P4 의 마지막 stage 로 추가. Stage E gate 통과 후에야 P4 전체를 "mission-aligned PASS" 로 선언.
3. 전면 재설계 금지. 기존 `novelty.py`, `coverage_map.py`, `plan.py`, `plateau_detector.py`, `remodel.py` 에 **wrapper / extension** 방식으로 부착.
4. 전체 비용 예산 먼저 정의, kill-switch 필수.

---

## 2. Stage E 작업 분해 (Task Breakdown)

### E0. 전제 & 예산 (선행)

- [ ] **E0-1** Stage E 전용 API 예산 정의
  - Universe probe: cycle 당 LLM 1회 + broad Tavily 3 queries 상한
  - cycle N 마다 1회 실행 (기본 N=5)
  - 15-cycle bench 총 비용 상한: LLM 3 calls + Tavily 9 queries
  - kill-switch: 예산 초과 시 Stage E 기능 skip, core loop 계속
- [ ] **E0-2** reach-diversity 축 실측 확인
  - Tavily snippet 에서 실제 추출 가능한 필드 조사 (domain 확실, publisher/author 불명, language 일부, time 간헐)
  - **확정 축만** ledger 에 포함, 나머지 placeholder 로 남김

### E1. External Novelty Metric [M]

- [ ] **E1-1** `src/utils/external_novelty.py` 신규
  - 입력: 현재 cycle 의 새 KU 목록 + 전체 누적 이력 (`state.knowledge_units` 전부)
  - 정의:
    ```
    history_novelty = |new_pairs \ historical_pairs| / |new_pairs|
      where pair = (entity_key, field_name) + claim-hash 보조
    ```
  - 반환: `{history_novelty: float, new_entity_count: int, new_pair_count: int}`
- [ ] **E1-2** `orchestrator.py` cycle 종료 시 채움
  - `external_novelty_history` 리스트에 append (state 필드 추가)
- [ ] **E1-3** `state_io.py` save/load 에 새 필드 반영
- [ ] **E1-4** 단위 테스트 6개
  - 완전 새 entity, 완전 기존 entity + 새 field, 완전 중복, 부분 중복, 빈 state 초기, claim-hash edge

### E2. Universe Probe [L]

- [ ] **E2-1** `src/nodes/universe_probe.py` 신규 (새 노드)
  - 단계 1: 현재 skeleton categories + top entity_keys 요약 생성
  - 단계 2: LLM prompt — "이 skeleton 에서 빠진 {domain} 관련 **주요 카테고리/축** 3-5개 를 JSON 으로 제안하라" (broad coverage bias)
  - 단계 3: 각 제안에 대해 broad Tavily query 1회 → snippet 5개 → "실제 존재 증거" 로 evidence 수집
  - 출력: `universe_probe_report` (제안 리스트 + evidence + confidence)
- [ ] **E2-2** tiered skeleton 도입
  - `skeleton.categories` (active) vs `skeleton.candidate_categories` (probe 결과)
  - candidate 는 **수집에 영향 없음**, 통계만 유지
  - active 승격은 `category_addition` proposal 경로 (기존 C1-C3 재사용) + HITL-R
- [ ] **E2-3** 트리거 조건 (cycle N 마다 or external_novelty < 0.15 × 3c)
- [ ] **E2-4** graph 에 universe_probe_node 삽입 (audit 다음, remodel 이전)
- [ ] **E2-5** 통합 테스트 5개 + budget kill-switch 테스트

### E3. Reach Diversity Ledger [M]

- [ ] **E3-1** `src/utils/reach_ledger.py` 신규
  - 축 (E0-2 결과 기반 확정):
    - **distinct_domains** (확실, Tavily result 의 domain)
    - **distinct_languages** (가능, Tavily response 의 language 또는 heuristic)
    - **time_range_bins** (evidence retrieved_at 누적 분포)
    - publisher/author: placeholder, 추출 가능성 확인 후 추가
  - 누적 집계 (run 전체) + per-cycle delta
- [ ] **E3-2** `orchestrator.py` 에 cycle 종료 시 ledger 업데이트
- [ ] **E3-3** normalization: `diversity_per_100ku = axis_count / (total_ku / 100)` 로 run-size 무관 비교
- [ ] **E3-4** low-reach 감지 함수 (`is_reach_degraded(ledger, threshold)`) — plateau detector 에서 사용
- [ ] **E3-5** 단위 테스트 8개

### E4. Exploration Pivot Node [L]

- [ ] **E4-1** `src/nodes/exploration_pivot.py` 신규
  - 트리거 신호 (plateau_detector 에서 전달):
    - `external_novelty < 0.1 × 5c` **AND/OR**
    - `reach_degraded` **AND/OR**
    - 기존 `is_plateau_detected` (internal)
  - 액션 후보 (구체 메커니즘):
    - **query rewriter (LLM)**: 현재 target 을 받아 axis-swap / abstraction-raise / long-tail 변형 3개 생성
    - **axis override**: 기존 reason_code 우선순위를 temporarily `coverage_deficit < 0.2 axis` 로 강제
    - **time-shift**: 쿼리에 연도 qualifier 추가 (예: "2020 이전", "최신 2026")
  - 1 cycle 지속, 다음 cycle 은 normal loop 복귀
- [ ] **E4-2** `plateau_detector.py` 확장
  - 기존 plateau → remodel 경로와 **별도** 경로 추가: plateau + reach_degraded → exploration_pivot
  - 둘 다 발동 시 우선순위: exploration_pivot > remodel (외향 먼저)
- [ ] **E4-3** `graph.py` 에 exploration_pivot edge 추가
- [ ] **E4-4** 통합 테스트 4개 (reach degraded 시 pivot 발동, query rewriter 출력 검증, 복귀 확인)

### E5. Planning Integration [S]

- [ ] **E5-1** `plan.py` reason_code enum 확장:
  - `external_novelty:deficit`
  - `universe_probe:missing_category={slug}`
  - `reach_diversity:low={axis}`
  - `plateau:exploration_pivot`
- [ ] **E5-2** 우선순위 재조정: external_novelty > deficit > gini > plateau > audit > seed
  - 이유: 외부 미탐 신호가 내부 균형보다 우선
- [ ] **E5-3** reason_code 테스트 확장 (기존 D3 + 새 4개 enum)

### E6. Cost & Safety [S]

- [ ] **E6-1** `src/utils/cost_guard.py` 신규 (또는 기존 확장)
  - Stage E 기능별 per-cycle/per-run budget tracking
  - 초과 시 Stage E 기능만 skip, core loop 보호
- [ ] **E6-2** 설정 가능화: `config.py` 에 `external_anchor_enabled`, `probe_interval_cycles`, budget 필드
- [ ] **E6-3** 테스트: budget 초과 시 skip 확인 + core loop 지속 확인

### E7. Validation (Ground-Truth) [M]

**미션 정렬 주장의 경험적 검증.** Opinion 문서에 빠진 부분.

- [ ] **E7-1** Synthetic injection test
  - 의도적으로 skeleton 에 없는 카테고리 (예: "accessibility") 관련 KU 만 담긴 fixture 생성
  - Stage E 포함 파이프라인 1-cycle 실행
  - 기대: universe_probe 가 "accessibility" 를 candidate 로 제안 OR external_novelty 가 ≥0.8 기록
  - 실패 시 Stage E 미션 정렬 실패 증거
- [ ] **E7-2** Regression bench on japan-travel
  - Stage E off: 기존 internal-only (P4 현재)
  - Stage E on: full
  - 15c 비교 metrics:
    - external_novelty avg
    - distinct_domains 누적
    - candidate_category 제안 건수
    - active_category 승격 건수 (HITL 시뮬레이션)
    - 비용 실측
- [ ] **E7-3** `bench/japan-travel-external-anchor/` 디렉터리 생성

### E8. Stage E Gate Judgment [S]

- [ ] **E8-1** `readiness_gate.py` 확장 — Stage E 기준 추가
  - 새 VP: `VP4_exploration_reach`
    - `external_novelty_avg ≥ 0.25` (정의 교체 후 임계치 유지)
    - `distinct_domains_per_100ku ≥ 15` (실측 후 조정)
    - `universe_probe_proposals ≥ 2 per 15c`
    - `exploration_pivot_triggered ≥ 1` (if plateau occurred)
- [ ] **E8-2** E7-2 bench 결과로 VP4 실측
- [ ] **E8-3** Gate 판정 commit `[si-p4] Stage E Gate PASS/FAIL: {근거}`

---

## 3. 전체 타임라인 & 사이즈

| Stage | Tasks | Size 총합 | 비고 |
|---|---|---|---|
| E0 | 2 | S+S | 선행 |
| E1 | 4 | M+S+S+S | novelty 핵심 |
| E2 | 5 | L+M+S+S+M | universe probe 최대 |
| E3 | 5 | M+S+S+S+S | ledger |
| E4 | 4 | L+M+S+M | pivot 노드 최대 |
| E5 | 3 | S+S+S | planning 연결 |
| E6 | 3 | S+S+S | cost guard |
| E7 | 3 | M+M+S | validation |
| E8 | 3 | S+S+S | gate |
| **합계** | **32** | 2L + 7M + 21S + 2(S+S) | ~P4 원래 17 tasks 의 2배 |

**Size 분포**: S: 21 / M: 7 / L: 2

---

## 4. Gate 재판정 프레임

### 4.1 즉시 조치 — P4 Internal Scope Gate 재기술

현재 `readiness-report.json` 의 P4 FAIL 을 **유지하되**, 판정 근거를 재기술:

- **새 판정**: "Internal Coverage Foundation: PASS" + "External Anchor: NOT_YET_SCOPED"
- novelty 0.127 은 cycle-diff 정체 신호로 재분류 (internal 측면에서는 정상 수렴).
- Commit: `[si-p4] Scope reframe: Internal Foundation PASS + External Anchor 추가 Stage E 로 분리`

### 4.2 Stage E 완료 후 — 최종 Mission-Aligned Gate

- VP1/VP2/VP3 (기존) + VP4 (새) 모두 PASS 시 P4 전체 통과 선언.
- Semi-front 진입은 Stage E 통과 이후.

---

## 5. 리스크

| ID | 리스크 | L | I | 완화 |
|---|---|---|---|---|
| R-E1 | Universe probe LLM 비용 폭발 | M | H | E0-1 예산 상한 + kill-switch |
| R-E2 | Candidate skeleton 이 active 로 자동 승격되며 오염 | L | H | tiered gate + HITL-R 필수 |
| R-E3 | External novelty 측정이 실제로 외부를 측정 못 함 (측정 환상) | M | H | E7-1 synthetic injection 으로 검증 |
| R-E4 | Reach diversity 축 확보 실패 (Tavily metadata 부족) | M | M | E0-2 선행 조사, 실측 가능 축만 확정 |
| R-E5 | Exploration pivot 이 core loop 를 혼란시킴 (targets 급변) | M | M | 1 cycle 만 지속 + 즉시 복귀 규칙 |
| R-E6 | Stage E 가 P5/P6 범위 잠식 | M | L | P5 = telemetry, P6 = multi-domain 로 명시 (중복 없음) |

---

## 6. 수용 기준 (Acceptance Criteria)

Stage E 완료 선언을 위해 **모두** 충족:

1. `external_novelty.py` + history-aware 측정 + 단위 테스트 PASS
2. `universe_probe.py` + tiered skeleton + 15c bench 에서 ≥ 2 candidate 제안
3. `reach_ledger.py` + 확정된 ≥2 축 (distinct_domains + 1개 이상) 실측
4. `exploration_pivot.py` + japan-travel 15c 에서 최소 1회 발동 (또는 plateau 미발생 시 synthetic 테스트로 증명)
5. `plan.py` reason_code 에 external 4종 추가 + 우선순위 반영
6. Cost guard 실측: 15c run 에서 LLM ≤ 3 calls + Tavily ≤ 9 queries (E0-1 예산 내)
7. E7-1 synthetic injection 테스트 PASS (숨긴 카테고리 표면화 확인)
8. E7-2 bench Stage-E-on vs Stage-E-off 비교에서 external_novelty avg 상승 확인
9. 전체 테스트 수 ≥ 700 (669 + ~30)

---

## 7. 다음 액션 (사용자 승인 필요 지점)

1. **이 plan 을 진행할지 승인** — Stage E 32 tasks 착수 vs 축소 vs 다른 우선순위
2. **E0-1 예산 승인** — LLM 3 calls + Tavily 9 queries / 15c bench 허용 여부
3. **Gate 재기술 먼저 commit 할지** — §4.1 즉시 조치를 먼저 할지, Stage E 완료 후 한 번에 할지
4. **축소 대안 고려**:
   - Minimum Viable External Anchor (MVEA): E1 + E3 + E5 만 (12 tasks). Universe probe / pivot 은 P5 로 이관
   - 트레이드오프: 미션 정렬 주장은 약해지지만, 비용/시간 절반

---

## 8. 요약

Opinion 문서의 핵심 틀(Internal Foundation + External Anchor 분리, 얇은 layer 추가, 기존 배관 재사용)은 타당하므로 수용.

단 Opinion 이 빠뜨린 4가지 — **claim-hash 수준 granularity, tiered skeleton + kill-switch, 실제 얻을 수 있는 reach 축 사전 검증, synthetic injection 으로 측정 신뢰성 검증** — 을 보강해 32-task 계획으로 구체화.

P4 Gate 는 즉시 "Internal Foundation PASS" 로 재기술하되, Mission-Aligned PASS 는 Stage E 통과 시점까지 보류. Semi-front 진입은 Stage E 이후.
