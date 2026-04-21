# Session Compact

> Generated: 2026-04-21
> Source: Conversation compaction via /compact-and-go

## Goal

이전 세션에서 확정된 SI-P7 구조 설계 5축 (S1~S5, Q1~Q14) baseline (`docs/structural-redesign-tasks_CC.md`) 을 **v2 로 개선**한다. 보강 항목:

1. `docs/phase-next-refactor-task-review_codex.md` (다른 연구자 검토) 유용 사항 통합
2. **중간 단계별 e2e 검증 전략** 정교화 (mock 금지, real API)
3. **Entity Discovery Node 타당성·구체성 재검토** (사용자 질의 포함)
4. 필요한 skill 정의 (`skill-creator` 사용)
5. **F1~F4 순차 풀이** 제안

---

## Completed

- [x] `docs/session-compact.md` (이전) 읽기
- [x] `docs/structural-redesign-tasks_CC.md` baseline 전문 확인
- [x] `docs/phase-next-refactor-task-review_codex.md` 전문 확인 (codex 검토)
- [x] `docs/entity-acquisition-strategy-draft.md` 재확인
- [x] 코드 현황 검증:
  - `src/nodes/plan.py:155-161` 정렬 로직 (S1 제거 대상)
  - `src/nodes/collect.py:218-230` budget skip (S1 defer/queue 변경 대상)
  - `src/nodes/integrate.py:80-132` `_detect_conflict` (S2 condition_split 재설계 대상)
  - `src/nodes/integrate.py:176-253` `_generate_dynamic_gus` (S3 rule engine 대상)
  - `src/nodes/critique.py:187-269` `_generate_balance_gus` (S4 virtual entity 제거 대상)
- [x] 기존 skill 목록 확인 (`evolver-framework`, `langgraph-dev`, `silver-*` 6건)
- [x] **Plan 파일 v2 작성** (`C:\Users\User\.claude\plans\ancient-seeking-sphinx.md`) — Part A/B/C/D/E 전문
- [x] F2/C3 사용자 지적 재검토:
  - **F2 β**: "매 cycle 실행" (D-173) 과 구별되는 **aggressive mode** 로 재정의
  - **C3**: C3-b (후속 GU 지연) → **C3-a (전체: 적재+승격+후속 GU)** 로 정정. 이유: S5a loop 미완성 시 F2 β 및 15c trial 측정 불가
- [x] **D-183 (C5=F3) 확정**: graph 삽입 위치 = **B** (plan_modify → entity_discovery → plan)

---

## Current State

**브랜치**: `main` | **Plan Mode**: 종료됨 (ExitPlanMode 자동 발생)
**테스트**: 변경 없음 (plan 만 작성, 코드·doc 수정 안 함)

### Changed Files (신규만)
- `C:\Users\User\.claude\plans\ancient-seeking-sphinx.md` — Plan v2 전문 (Part A/B/C/D/E + Decisions)

### 핵심 baseline (기존)
- `docs/structural-redesign-tasks_CC.md` — SI-P7 task breakdown (S1~S5 + F1~F4), **v2 로 개선 필요**

---

## Remaining / TODO

### 즉시 다음 액션 (우선순위 순)

1. **F2 조합 최종 확정** — α + β(aggressive mode) 제안 사용자 승인 받기 (β 재정의 후 재확인 필요)
2. **C1 질문 답변 받기** — Entity Discovery target 선정 신호
   - C1-a: `coverage_map.deficit_score` 공유 (S4 와)
   - C1-b: 독립 `entity_coverage_deficit`
   - C1-c: critique 신호 `added_entity_ratio<X`
3. **C2 질문 답변 받기** — candidate 수명 정책
   - C2-a (제안): `last_seen+5c → stale`, `+10c → purge`, 재등장 시 갱신
   - C2-b: 다른 수치
   - C2-c: 정책 불필요 (영속)
4. **C4 질문 답변 받기** — 유사 후보 alias pre-filter
   - C4-a (제안): similarity ≥ 0.85 이면 candidate 차단 → alias 제안 경로 (S5b)
   - C4-b: candidate 로 들이고 승격 단계에서 alias 판정
   - C4-c: 완전 분리 유지

### baseline v2 작성 (C1~C4 해소 후)
- [ ] `docs/structural-redesign-tasks_CC.md` **v2 갱신**
  - Part A 전체: S1 defer/queue, S2 integration_result 제어 입력, condition_split 재설계, S3 rule engine + yield tracker, S4 virtual 즉시 제거, S5a 전체 범위 (C3-a), S5b duplicate→entity fragmentation 신호, 권장 착수 순서
  - Part B 전체: L1/L2/L3 테스트 레이어, task 단위 checkpoint 테이블, trial-id 규약
  - Part C 결과 반영: C1~C5 결정 + β aggressive mode 정의

### skill-creator 로 신설
- [ ] `.claude/skills/silver-structural-redesign/SKILL.md`
- [ ] `.claude/skills/silver-e2e-test-layering/SKILL.md`
- [ ] `.claude/skills/skill-rules.json` 두 항목 추가

### dev-docs 스캐폴딩 (이후)
- [ ] `dev/active/phase-si-p7-structural-redesign/` 신설
- [ ] `si-p7-plan_CC.md`, `si-p7-context_CC.md`, `si-p7-tasks_CC.md`, `si-p7-debug-history_CC.md` (모두 `_CC` suffix)

### 구현 단계 (F1, F4 는 구현 중 결정)
- [ ] F1 (budget 완전 제거) — S1-T6 smoke 5c 실험 후 결정
- [ ] F4 (auto-alias 0.90 / auto-merge 0.95 임계치) — 실 벤치로 tuning

---

## Key Decisions

### 이번 세션 신규

- **D-181 (F2)**: aggressive feedback = **α (plan query "new concrete entity" 재작성) + β (aggressive mode)**. β 는 "매 cycle 실행" (D-173) 과 구별되는 **mode 전환**:
  - discovery target 1-2 → 3-5개 확장
  - rule-first → LLM-assisted 즉시 활성
  - candidate 적재 임계 완화 (source_count≥1 임시 적재, 승격은 표준 유지)
  - 후속 GU 우선순위 상향
  - 지속: trigger cycle + 다음 2c
  - **상태**: 사용자 승인 대기 (재정의 후 확인)
- **D-182 (C3)**: S5a 이번 phase 범위 = **C3-a (전체: 적재 + 승격 + 후속 GU 자동 오픈)**. codex §6 (다음 phase 로 분할) 기각. 이유: S5a loop 미완성이면 F2 β 및 15c trial 측정 불가. 사용자 지적 수용.
- **D-183 (C5 = F3)**: entity_discovery graph 위치 = **B (plan_modify → entity_discovery → plan)**. candidate 적재 중심 설계에 자연. ✅
- **D-184~186 (C1/C2/C4)**: 예정
- **D-187**: 테스트 3-layer (L1 단위, L2 single-cycle e2e, L3 15c A/B). **mock 금지**, fixture 는 real snapshot 만. L3 만 Gate 공식 판정. **예정**
- **D-188**: 2개 신규 skill 도입 예정 (silver-structural-redesign, silver-e2e-test-layering). **예정**

### 이전 세션 (유지)

- D-171 ~ D-180 (5축 구조 + Q1~Q14 + `_CC` suffix 규칙)
- D-163~D-170 (POR pain-point / Remodel shrinkage)

---

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### codex 검토 주요 반영 사항

**Part A (baseline v2 에 직접 반영)**:
- A1. S1: "drop" → **"defer/queue"**. budget 초과 target 은 drop 금지, `deferred_targets` state 에 기록. 다음 cycle 우선 소진. `executed/deferred/defer_reason` 메트릭
- A2. S2: `integration_result` 를 로그가 아닌 **다음 cycle plan 제어 입력** 으로 승격. plan reason code 추가 (`collect_defer_excess`, `integration_added_low`, `adjacent_yield_low`, `entity_discovery_insufficient`)
- A3. S2 condition_split: 현재 구현 (`integrate.py:99-100`) 은 "conditions 필드 있으면 split" 수준. **값 구조/axis_tags 차이 기반 재설계** 필요
- A4. S3 adjacent: **rule engine** (source_field → next_field 맵) + rule yield tracker (낮은 yield rule 약화) + `recent_conflict_fields` 배제
- A5. S4 virtual entity: **과도기 옵션 없이 즉시 제거** (S5a 같은 phase 도입)
- A6. S5a 범위: C3-a 확정 (codex §6 기각)
- A7. S5b: duplicate KU 를 **entity 파편화 신호** 로 격상, fragmentation report metric 추가
- A8. 권장 착수 순서: `S1+S2(제어 루프) → S2-T5~T8+S3+S4(품질) → S5a(entity)`

**Part B (테스트 3-layer)**:

| 레이어 | 시점 | 목적 | mock |
|---|---|---|---|
| L1 | task 직후 | 단위 함수 로직 | fixture real snapshot, stub 금지 |
| L2 | task 묶음 | single-cycle e2e | real API 필수 (D-34) |
| L3 | 축 완료 | 15c A/B Gate 판정 | real API 필수 |

Task 단위 checkpoint 테이블 이미 plan v2 에 포함 (S1-T4 defer, S2-T1 distribution, S2-T6 condition_split, S3-T4/T7, S4-T1, S5a-T6/T7, S5b-T3).

**Part D (skill 신설)**:
- `silver-structural-redesign`: SI-P7 5축 가이드 + codex 통합 + F1~F4 handling + `_CC` suffix 규칙
- `silver-e2e-test-layering`: L1/L2/L3 + trial-id 규약 + mock 금지 원칙

**Part E (F1~F4 순차 풀이)**:
```
1. F2 (본 플로우, α+β aggressive mode — 승인 대기)
2. C1~C5 질문 답변 (C3/C5 확정됨. C1/C2/C4 대기)
3. baseline v2 작성 (Part A/B/C 반영)
4. skill-creator 로 2개 skill 신설
5. dev-docs 스캐폴딩
6. F1/F4 는 구현 중 결정
```

### 핵심 참고 파일 (읽기 우선순위)

1. **`C:\Users\User\.claude\plans\ancient-seeking-sphinx.md`** ← **plan v2 전문, 가장 먼저 읽기**
2. `docs/structural-redesign-tasks_CC.md` — 기존 baseline (v1)
3. `docs/phase-next-refactor-task-review_codex.md` — codex 검토
4. `docs/entity-acquisition-strategy-draft.md` — S5 근거
5. `docs/core-pipeline-spec-v1.md` — 기준 문서

### 제약/주의사항

- **D-34**: 실 벤치 trial (real API, 15c A/B) 필수. 합성 E2E 만으로 gate 불가
- **D-129**: `target_count` cap 재도입 금지
- **D-168**: Track 1 Pain Point 9건 개별 리뷰로 돌아가지 말 것
- **파일명 (D-180)**: 본 설계 산출 doc 은 `_CC` suffix 필수
- **mock 금지 (D-187 예정)**: fixture 는 real snapshot 만, function stub 금지
- **Remodel**: 본 설계 범위 외, 별도 재설계 예정

### 미커밋 잔존 (untracked)
- `bash.exe.stackdump` (무시)
- `bench/silver/japan-travel/p0-20260412-baseline/telemetry/`
- `bench/silver/japan-travel/p6-b1-smoke-5c/`, `p6-diag-full-15c/`, `p6-diag-smoke-5c/`
- `docs/phase-next-refactor-task-review_codex.md` (codex 검토 문서)
- `docs/structural-redesign-tasks_CC.md` (기존 baseline)
- `docs/session-compact.md` (본 파일로 갱신)

---

## Next Action

**다음 세션 시작 시 수행할 것:**

1. `C:\Users\User\.claude\plans\ancient-seeking-sphinx.md` 읽고 plan v2 전문 + Decisions (D-181~188) 확인
2. 사용자에게 **F2 β aggressive mode 정의** 재확인 요청 (D-181 승인 대기)
   - 제안: α + β(aggressive mode) — discovery target 확장/LLM query 즉시 활성/candidate 임계 완화/GU 상향
3. **C1 질문** 진행 (하나씩 이어서) — Entity Discovery target 선정 신호
   - 제안: C1-a (coverage_map.deficit_score S4 와 공유)
4. C1 해소 후 C2 (candidate 수명), 이어서 C4 (유사 후보 pre-filter) 질문
5. C1~C4 확정 후 **`docs/structural-redesign-tasks_CC.md` v2 작성**:
   - Part A 전체 반영 (S1 defer, S2 제어 입력+condition_split 재설계, S3 rule engine, S4 virtual 즉시 제거, S5a 전체, S5b fragmentation, 착수 순서)
   - Part B 전체 반영 (L1/L2/L3 + task checkpoint + trial-id 규약)
   - Part C 결과 반영 (C1~C5 + β aggressive mode 정의)
6. **skill-creator** 로 `silver-structural-redesign` + `silver-e2e-test-layering` 2개 skill 신설
7. **`dev/active/phase-si-p7-structural-redesign/`** dev-docs 스캐폴딩 (`_CC` suffix 4개)
8. 구현 착수 (codex 권장 순서: S1+S2 → S2+S3+S4 → S5a)
