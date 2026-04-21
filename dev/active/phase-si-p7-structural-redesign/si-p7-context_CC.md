# SI-P7 Structural Redesign — Context (_CC)

> 작성: 2026-04-21
> 이 문서는 **구현 착수 시 코드 + 문서 맥락** 을 빠르게 복원하기 위한 포인터 모음.

## 진입점 — 읽기 우선순위

1. **`docs/structural-redesign-tasks_CC.md` v2** — 단일 진실 소스 (5축 task breakdown, D-181~D-188, 테스트 3-layer)
2. `C:\Users\User\.claude\plans\ancient-seeking-sphinx.md` — plan v2 전문 (Part A/B/C/D/E)
3. `C:\Users\User\.claude\plans\ok-curious-naur.md` — 최종 실행 plan (본 세션 산출)
4. `docs/phase-next-refactor-task-review_codex.md` — codex 검토 원문 (통합 근거)
5. `docs/entity-acquisition-strategy-draft.md` — S5 근거
6. `docs/core-pipeline-spec-v1.md` — 기준 pipeline spec
7. `si-p7-plan_CC.md`, `si-p7-tasks_CC.md` — 본 phase dev-docs

## 관련 skill

- `silver-structural-redesign` — 5축 구현 가이드 (본 phase 전용)
- `silver-e2e-test-layering` — L1/L2/L3 테스트 + trial-id 규약
- `evolver-framework` — 5대 불변원칙 guardrail
- `langgraph-dev` — graph/node 패턴 (S5a 신설 시)
- `silver-trial-scaffold` — L3 `p7-*-on|off` trial 디렉토리 생성
- `silver-phase-gate-check` — phase 전체 완료 시 readiness-report

## 현재 상태 (2026-04-21)

- **브랜치**: `main` (구현 착수 전)
- **테스트**: 기존 상태 유지 (Phase 5 468 tests + SI-P2 추가)
- **Silver Phase**: SI-P2 Gate PASS (2026-04-15). SI-P7 은 그 다음.
- **미커밋 변경**:
  - `docs/session-compact.md` (업데이트됨)
  - `docs/structural-redesign-tasks_CC.md` (v1 → v2)
  - `docs/phase-next-refactor-task-review_codex.md` (신규)
  - `.claude/skills/silver-structural-redesign/SKILL.md` (신규)
  - `.claude/skills/silver-e2e-test-layering/SKILL.md` (신규)
  - `.claude/skills/skill-rules.json` (2종 추가)
  - `dev/active/phase-si-p7-structural-redesign/` (본 디렉토리)

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

## 주의사항 / 제약

- **D-34**: 실 벤치 trial (real API) 필수. 합성 E2E 만으로 gate 불가.
- **D-129**: `target_count` cap 재도입 **금지**. S1-T7 regression guard 테스트로 보호.
- **D-168**: Track 1 Pain Point 9건 개별 리뷰로 돌아가지 말 것 — 본 phase 는 구조 설계.
- **D-180**: 본 phase 산출 doc `_CC` suffix 필수.
- **D-187**: **mock 금지** — fixture real snapshot 만, function stub 금지.
- **Remodel**: 본 phase 범위 외, 별도 재설계 예정.

## 핵심 Decisions (이전 phase 계승)

- D-67 observed_at today / D-68 일반 update observed_at today / D-69 evidence-count 가중 평균 / D-70 multi-evidence boost
- D-120 P3 REVOKED / D-121 P3R / D-124 provider_entropy 제거 / D-129 target_count cap 재도입 금지 / D-131 P2 비교 실험
- D-132 Smart Remodel Criteria / D-133 merge min_overlap ≥ 2 / D-134 Gini P4 연기
- D-163~D-167 Remodel-induced exploit_budget shrinkage root cause

## 본 phase 신규 Decisions

- D-171 ~ D-180 (5축 구조 + Q1~Q14 + `_CC` suffix)
- D-181 F2 = α + β / D-182 S5a C3-a 전체 / D-183 graph B
- D-184 C1-a deficit 공유 / D-185 C2-a 5c stale/10c purge / D-186 C4-a similarity≥0.85 alias
- D-187 3-layer mock 금지 / D-188 skill 2종
