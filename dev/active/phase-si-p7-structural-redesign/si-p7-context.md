# SI-P7 Structural Redesign — Context

> 작성: 2026-04-21 | 최종 업데이트: 2026-04-23
> 이 문서는 **구현 착수 시 코드 + 문서 맥락** 을 빠르게 복원하기 위한 포인터 모음.

## 진입점 — 읽기 우선순위

1. **`docs/structural-redesign-tasks_CC.md` v2** — 단일 진실 소스 (5축 task breakdown, D-181~D-188, 테스트 3-layer)
2. `C:\Users\User\.claude\plans\ancient-seeking-sphinx.md` — plan v2 전문 (Part A/B/C/D/E)
3. `C:\Users\User\.claude\plans\ok-curious-naur.md` — 최종 실행 plan (Step A/B 까지)
4. `C:\Users\User\.claude\plans\review-project-status-with-elegant-island.md` — Step V 검증 plan (V1~V4, D-190/D-191)
5. `docs/phase-next-refactor-task-review_codex.md` — codex 검토 원문 (통합 근거)
6. `docs/entity-acquisition-strategy-draft.md` — S5 근거
7. `docs/core-pipeline-spec-v1.md` — 기준 pipeline spec
8. `si-p7-plan.md`, `si-p7-tasks.md`, `si-p7-debug-history.md` — 본 phase dev-docs

## 관련 skill

- `silver-structural-redesign` — 5축 구현 가이드 (본 phase 전용)
- `silver-e2e-test-layering` — L1/L2/L3 테스트 + trial-id 규약
- `evolver-framework` — 5대 불변원칙 guardrail
- `langgraph-dev` — graph/node 패턴 (S5a 신설 시)
- `silver-trial-scaffold` — L3 `p7-*-on|off` trial 디렉토리 생성
- `silver-phase-gate-check` — phase 전체 완료 시 readiness-report

## 현재 상태 (2026-04-23)

- **브랜치**: `main` (최신 `2c54001`)
- **테스트**: 926 passed, 3 skipped
- **완료**: Step A (S1 + S2-T1/T2) + Step B (S2-T3~T8 + S3 + S4-T1/T2) + L3 `p7-ab-on|off` trial
- **다음**: **Step V (V1~V4 검증)** — Step A/B 전 항목 동작 검증 후 Step C 착수 여부 결정 (D-190)
- **주요 관찰**:
  - `p7-ab-on` L3 FAIL (KU 82 고정, GU 고갈 c3+), `p7-ab-off` PASS (KU 147)
  - 항목별 판정 — ✓10 / ✗1 (S2-T4 β) / ~7 (계측 부재) / N/A 2
  - ✗/~ 해소 전 balance-* 단독 root cause 단정 금지 (D-190)

### 커밋 이력 (이번 phase)

| 커밋 | 내용 |
|------|------|
| `a6bc80e` | S1-T1~T3: target 자유화 |
| `97e2ef5` | S1-T4: collect defer |
| `defc3a0` | S1-T5: max_search_calls_per_cycle |
| `2db7448` | S1-T7: D-129 regression guard |
| `4e5988c` | S1-T8: deferred_targets FIFO + telemetry |
| `6b8d9d2` | S1-T6: budget smoke 5c |
| `7bd9f2b` | S2-T1: integration_result_dist |
| `c6ba740` | S2-T2: ku_stagnation_signals + 3종 trigger |
| `87d7603` | S2-T4: F2 α+β |
| `f3a0be0` | S2-T5~T8: condition_split 강화 |
| `2631c38` | S4-T1/T2: balance-* 제거 + deficit_score |
| `2d252f3` | S3: adjacent rule engine (T1~T8) |

## 관련 코드 경로 (수정 예정)

### 기존 수정
| 파일 | 위치 | 담당 축 |
|---|---|---|
| `src/nodes/plan.py` | 155-161 (정렬 제거), 그 외 (reason code) | S1, S2 |
| `src/nodes/collect.py` | 218-230 (budget skip → defer) | S1 |
| `src/nodes/collect.py` | `_build_parse_prompt` | S2-a |
| `src/nodes/mode.py` | `mode_node` target_count 공식 | S1 |
| `src/nodes/integrate.py` | 80-132 (`_detect_conflict`) | S2 condition_split 재설계 |
| `src/nodes/integrate.py` | 176-253 (`_generate_dynamic_gus`) | S3 rule engine |
| `src/nodes/critique.py` | 187-269 (`_generate_balance_gus` + feedback) | S2 feedback, S4 virtual 제거, S5a β 연동 |
| `src/utils/entity_resolver.py` | similarity | S5a pre-filter (0.85), S5b alias/merge |
| `src/utils/metrics.py` | — | S2 distribution, S3 yield, S5a 수명, S5b fragmentation |
| `src/state.py` | — | `deferred_targets`, `recent_conflict_fields`, `entity_candidates`, `entity_fragmentation_signals` |
| `src/config.py` | `SearchConfig` | S1 `max_search_calls_per_cycle` |
| `src/graph.py` | graph builder | S5a 노드 삽입, 위치 **B** |
| `bench/japan-travel/state/domain-skeleton.json` | — | S2 `condition_axes`, S3 `field_adjacency` + `default_risk/utility`, S5a `entity_frame` |

### 신설 파일
- `src/nodes/entity_discovery.py` (S5a)
- `src/nodes/entity_reconcile.py` (S5b)

### Step V 계측 대상 (V2 조건부)
- `src/state.py` — `aggressive_mode_history`, `suppress_event_log`, `query_rewrite_rx_log`, `condition_split_trigger_log` 등 관찰용 필드
- `src/nodes/integrate.py` — S3-T1 suppress 발동, S3-T7 adjacency_yield, S2-T6 `_value_structure_type` 판정 이벤트 로그
- `src/nodes/critique.py` — S2-T4 α `query_rewrite` rx 발행 로그
- `src/nodes/entity_discovery.py` — S2-T4 β `aggressive_mode_entered` 이벤트

### Step V 데이터 경로
- `bench/silver/japan-travel/p7-ab-on/state-snapshots/cycle-*-snapshot/state.json` (V1 파싱 소스)
- `bench/silver/japan-travel/p7-ab-on/run.log` (V1 grep 소스)
- `bench/silver/japan-travel/p7-ab-minus-{axis}/` (V3 신규 trial, 1~2 개)
- `dev/active/phase-si-p7-structural-redesign/v1-signal-audit.md`, `v3-isolation-report.md` (산출물)

## 주의사항 / 제약

- **D-34**: 실 벤치 trial (real API) 필수. 합성 E2E 만으로 gate 불가.
- **D-129**: `target_count` cap 재도입 **금지**. S1-T7 regression guard 테스트로 보호.
- **D-168**: Track 1 Pain Point 9건 개별 리뷰로 돌아가지 말 것 — 본 phase 는 구조 설계.
- **D-180** (갱신 2026-04-23): dev-docs `_CC` suffix 제거. `structural-redesign-tasks_CC.md` (spec) 만 유지.
- **D-187**: **mock 금지** — fixture real snapshot 만, function stub 금지.
- **D-189 잠정 보류**: Step V 결과 전까지 `S5a = critical path` 가정 사용 금지.
- **D-190**: Step V 검증 선결. balance-* 단독 원인 단정 금지.
- **D-191**: V3 ablation cycle=8, baseline 재사용, 의심 축 1~2 개만.
- **Remodel**: 본 phase 범위 외, 별도 재설계 예정.

## 핵심 Decisions (이전 phase 계승)

- D-67 observed_at today / D-68 일반 update observed_at today / D-69 evidence-count 가중 평균 / D-70 multi-evidence boost
- D-120 P3 REVOKED / D-121 P3R / D-124 provider_entropy 제거 / D-129 target_count cap 재도입 금지 / D-131 P2 비교 실험
- D-132 Smart Remodel Criteria / D-133 merge min_overlap ≥ 2 / D-134 Gini P4 연기
- D-163~D-167 Remodel-induced exploit_budget shrinkage root cause

## 본 phase 신규 Decisions

- D-171 ~ D-180 (5축 구조 + Q1~Q14)
- D-181 F2 = α + β / D-182 S5a C3-a 전체 / D-183 graph B
- D-184 C1-a deficit 공유 / D-185 C2-a 5c stale/10c purge / D-186 C4-a similarity≥0.85 alias
- D-187 3-layer mock 금지 / D-188 skill 2종
- **D-189** (잠정 보류) S5a critical path — Step V 후 재판정
- **D-190** Step V 삽입 — Step A/B 항목별 동작 검증 선결
- **D-191** V3 ablation 8c + baseline 재사용 + `p7-ab-minus-{axis}` 방식
