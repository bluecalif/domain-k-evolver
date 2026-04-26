# Session Compact

> Generated: 2026-04-26
> Source: Conversation compaction via /compact-and-go

## Goal

S3 GU Gate (narrative G1~G5) 가 false PASS 를 발급한 문제를 발견 → mechanistic 검증 가능한 새 Gate (V/O composite + M criteria) 를 설계하고 차후 세션에서 구현.

## Completed

- [x] `scripts/analyze_trajectory.py --matrix` 포맷 수정:
  - `by_category` 필드 순서: `total` 먼저, `gu_resolved_no_wildcard_ku` 는 비-0 일 때만 포함
  - `state_definitions.gu_resolved_no_wildcard_ku` 텍스트 보강 (`— wildcard 슬롯 자체에는 KU 없음`)
  - 최상위 `note` 일본어 `で` → 한국어 `로` 수정
  - `make_note` ku_only 노트: `seed KU — entity-specific GU 미생성` → `seed`
  - `by_category` 각 엔트리 single-line 포맷 (placeholder injection)
  - `categories.[cat].matrix.[entity].[field]` cell single-line 포맷 (`_cat_str` 헬퍼)
- [x] s3-gu-smoke `entity-field-matrix.json` 재생성 (s3-smoke 와 동일 포맷)
- [x] s3-smoke vs s3-gu-smoke 정량 비교 → S3-T9~T14 사실상 미작동 확인:
  - vacant: 97 → 86 (Δ=−11, 목표 −97 의 11%)
  - **attraction REGRESSION**: vacant 72→77 (+5), ku_gu 5→2 (−3)
  - **attraction abandoned**: vacant=77 ∧ open_gu=0
  - adj_yield 0.500 → 0.362 (−28%)
- [x] G1~G5 Gate critical review — "코드 돌았나" 만 측정, mechanistic claim 무검증
- [x] **Plan 파일 작성**: `C:\Users\User\.claude\plans\b-plann-very-carefully-breezy-flame.md`
  - V/O composite (V1/V2/V3/O1/O2 + V×O Frontier Health) 1차 신호
  - M1~M8 mechanistic criteria 보조 신호
  - Telemetry-deferred (M5b/M9/M10/M11) 별도 task 분리
  - `scripts/check_s3_gu_gate.py` 설계 + exit code 정책
  - 재판정 절차 + diagnosis sub-task 분기
  - Hand-off 섹션 (다음 세션 실행 진입점)

## Current State

### Branch
`feature/si-p7-rebuild` (Plan mode active 상태로 종료됨)

### Changed Files (uncommitted)
- `scripts/analyze_trajectory.py` — `generate_entity_field_matrix` 포맷 개선 (위 6개 변경)
- `bench/silver/japan-travel/p7-rebuild-s3-gu-smoke/entity-field-matrix.json` — 새 포맷으로 재생성
- `docs/session-compact.md` — 본 파일 (방금 갱신)

### Created (out-of-tree)
- `C:\Users\User\.claude\plans\b-plann-very-carefully-breezy-flame.md` — 새 Gate 설계 plan (10개 섹션)

### Untracked
- `bash.exe.stackdump` (무시)

## Remaining / TODO

순서는 plan 파일 §10.2 참조.

- [ ] (다음 세션 시작) **plan 파일 검토** → user 승인 → ExitPlanMode (Plan mode 잔존 시)
- [ ] **Step 1**: `git status` 로 미커밋 변경 확인. matrix 포맷 fix 를 별도 commit 으로 분리할지 결정.
- [ ] **Step 2**: `scripts/_gate_helpers.py` 신규 작성 (count_adj_gus, slot_state_count, snapshot_diff_adj, kl_divergence). `tests/scripts/test_check_s3_gu_gate.py` TDD 작성.
- [ ] **Step 3**: `scripts/check_s3_gu_gate.py` 구현 — V1/V2/V3/O1/O2/V×O composite + M1~M8 + 출력 포맷 + exit code (0/1/2/3).
- [ ] **Step 4**: Self-sanity test (baseline=target=`p7-rebuild-s3-smoke`) 모든 비교 PASS 확인.
- [ ] **Step 5**: 실 재판정 (baseline=`p7-rebuild-s3-smoke`, target=`p7-rebuild-s3-gu-smoke`). FAIL 예측.
- [ ] **Step 6**: 문서 갱신 — `dev/active/phase-si-p7-structural-redesign/si-p7-tasks.md` lines 202-239 교체 + `si-p7-gate-mechanistic.md` 신규.
- [ ] **Step 7**: Diagnosis sub-task 진입 결정 (user 협의):
  - `SI-P7-S3-DIAG-ATTRACTION` (attraction abandoned root cause)
  - `SI-P7-S3-DIAG-T10-T14` (telemetry M5b/M9 추가 → c4-c5 collapse 진단)
  - `SI-P7-S3-DIAG-YIELD` (dynamic_cap ablation)

## Key Decisions

- **Gate 1차 신호 = Vacant# + Open GU#**: ku_gu/ku_only 는 파생. 이유: V·O 가 시스템 진행 상태(blind spot vs active frontier) 를 직접 측정.
- **Abandoned-category 패턴(vacant ≥ 5 ∧ open_gu = 0) 은 hard FAIL**: attraction(77,0) 같은 케이스 즉시 차단.
- **Telemetry 추가는 Gate 의 선행 조건 아님**: M5b/M9/M10/M11 NA 처리 후 V/O + 측정 가능 M1~M8 만으로 판정. Telemetry 는 diagnosis 단계에서 추가.
- **임계값은 항상 베이스라인 상대 비교 + 절대 floor 병행**: 절대 임계 단독(`≥0.3` 등) 은 후퇴 은폐 → 금지.
- **bullshit 금지 원칙**: "looks reasonable" 같은 표현 사용 안 함. 모든 임계값에 정량 근거(P-zone 슬롯 수, LLM noise band, KL divergence 의미) 명시.
- **G1~G5 narrative Gate 폐기**: 본 plan 의 새 Gate 결과로 `dev/active/phase-si-p7-structural-redesign/si-p7-tasks.md` lines 202-239 전면 교체.

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 절대 경로 참조 (필독)
- **Plan 파일**: `C:\Users\User\.claude\plans\b-plann-very-carefully-breezy-flame.md` (10개 섹션, V/O 신호 의미론, M criteria 임계값 근거 모두 포함)
- **베이스라인 trial**: `C:\Users\User\Learning\KBs-2026\domain-k-evolver\bench\silver\japan-travel\p7-rebuild-s3-smoke\`
- **타겟 trial**: `C:\Users\User\Learning\KBs-2026\domain-k-evolver\bench\silver\japan-travel\p7-rebuild-s3-gu-smoke\`
- **수정 대상 dev-docs**: `dev\active\phase-si-p7-structural-redesign\si-p7-tasks.md` lines 202-239 (S3 GU Gate 블록)
- **Skeleton**: `bench\japan-travel\state-snapshots\cycle-0-snapshot\domain-skeleton.json`

### 데이터 가용성 요약 (이미 조사 완료)
- **즉시 측정 가능**: gap-map.json, knowledge-units.json, trajectory.json, entity-field-matrix.json, state-snapshots/cycle-N-snapshot/gap-map.json, conflict-ledger.json, adjacency-yield.json
- **측정 불가** (telemetry 부재):
  - GU 의 sweep-origin 식별 불가 (T10 검증 보류)
  - GU 의 created_cycle 부재 (ISO date 만 — multi-cycle/day 충돌)
  - per-cycle adj_gen / wildcard_gen / cap_hit 카운트 부재
- **현재 코드 위치**:
  - `_generate_dynamic_gus`: `src/nodes/integrate.py:195-280`
  - post-cycle sweep: `src/nodes/integrate.py:570-597`
  - WILDCARD_PARALLEL_FIELDS: `src/nodes/seed.py:40`
  - dynamic_cap 고정값: `src/nodes/integrate.py:280-281`
  - readiness_gate (재사용 불가): `src/utils/readiness_gate.py:40-156`

### 사용자 피드백/원칙
- "no bullshit" — 모든 임계값에 정량 근거 명시. "looks reasonable" 류 표현 금지.
- "G1~G5 are all jerks" — 기존 narrative Gate 거짓 PASS 발급 동의.
- Vacant# 와 Open GU# 가 가장 중요한 Gate criteria.

### 미해결 질문 (다음 세션 user 와 협의)
- matrix 포맷 fix commit 을 별도 분리할지, Gate 작업과 묶을지.
- diagnosis sub-task 진입 순서 (attraction → T10/T14 → yield 가 자연스러우나 user 확인 필요).
- 새 `si-p7-gate-mechanistic.md` 문서 위치 확정 (`dev/active/phase-si-p7-structural-redesign/` vs `docs/`).

## Next Action

**다음 세션 시작 직후 수행할 1차 액션**:

1. 본 `docs/session-compact.md` 와 `C:\Users\User\.claude\plans\b-plann-very-carefully-breezy-flame.md` 모두 읽고 컨텍스트 복원.
2. `git status` + `git log -5` 로 현재 brnach 및 미커밋 변경 확인.
3. User 에게 다음 옵션 제시 (선택 응답 후 진행):
   - **A**: Plan 의 §10.2 Step 1 (matrix 포맷 fix commit 분리) 부터 순차 진행.
   - **B**: matrix 포맷 fix 를 Gate 구현과 묶어 한 번에 commit (Step 1 생략).
   - **C**: Plan 자체를 다시 검토/수정 (구현 시작 전 추가 결정 필요한 경우).
4. User 선택에 따라 Plan §10.2 Step 2 (Gate helpers + TDD unit tests) 부터 구현 진입.

**구현은 plan 파일 §10.2 의 Step 1~7 순서를 그대로 따른다.** 임계값/판정 로직은 plan 파일 §1, §2, §3 에서 인용.
