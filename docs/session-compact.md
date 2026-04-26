# Session Compact

> Generated: 2026-04-26
> Source: Conversation compaction via /compact-and-go

## Goal

S3 GU Mechanistic Gate (M-Gate) 구현 + 실 재판정 + dev-docs 갱신. Plan §10.2 의 Step 1~6 완료, Step 7 (Diagnosis sub-task 진입 결정) 까지 도달. **결론: S3 narrative G1~G5 PASS 무효화 → M-Gate FAIL → 5개 diagnosis sub-task → 2-trial plan 확정.**

## Completed

- [x] **Step 1**: matrix 포맷 fix + session-compact 갱신을 별도 commit 으로 분리 (commits `662fbeb`, `21fb6e3`)
- [x] **Step 2**: `scripts/_gate_helpers.py` 신규 + L1 tests 20개 (commit `886d30c`)
  - count_adj_gus, slot_state_count, snapshot_diff_adj, kl_divergence (4개 순수 함수)
  - 베이스라인 실측 검증: attraction vacant=72, snapshot diffs=[2,6,2,0]
- [x] **Step 3**: `scripts/check_s3_gu_gate.py` 메인 스크립트 + 통합 tests 13개 (commit `9b9fc50`)
  - V1/V2/V3 + O1/O2 + VxO + M1~M8 + Telemetry-deferred 4개 평가
  - Exit code 0/1/2/3 (V/O 우선 정책)
  - --strict (M5 strong form), --json 리포트 출력
  - self-mode (path equality) 시 비교형 criteria → no-regression 체크
  - sys.path 조정 (직접 실행 + pytest 양쪽 호환)
  - Windows console UTF-8 강제
- [x] **Step 4**: Self-sanity test (baseline=target=`p7-rebuild-s3-smoke`)
  - 비교형 9개 모두 PASS → Gate 로직 정상
  - 절대형 5개 FAIL: O1 (3 cats abandoned), O2 (KL=∞), VxO 5/8 fail, M2 0/7=0.00, M7 violations=9
  - **결론**: Plan §7.1 의 self-sanity PASS 가정은 false assumption (베이스라인 자체 unhealthy 라는 사실 무시). Gate 자체에는 버그 없음.
- [x] **Step 5**: 실 재판정 (`p7-rebuild-s3-smoke` → `p7-rebuild-s3-gu-smoke`)
  - **VERDICT: FAIL exit=1** (V/O 5/6 FAIL)
  - JSON 리포트 보존: `bench/silver/japan-travel/p7-rebuild-s3-gu-smoke/m-gate-report.json`
  - T11/T12/T13 작동 확인 (M2/M3/M4 PASS)
  - T9 거의 무작동 (M1 1.08×) → attraction abandoned root cause 후보
  - T14 부분 작동 (Δc4=0, Δc5=2; weak PASS / strict FAIL)
  - T10 미검증 (M9 telemetry 부재)
  - 신규 발견: V2 connectivity +1, M7 violations=6
- [x] **Step 6**: dev-docs 갱신 (commit `bff1544`)
  - 신규 `dev/active/phase-si-p7-structural-redesign/si-p7-gate-mechanistic.md` (M-Gate 의미론·임계값·실측결과 단일 진실 소스)
  - `si-p7-tasks.md` lines 202-239 narrative G1~G5 PASS → M-Gate FAIL 결과 표 + diagnosis sub-tasks 5개 checklist
  - `si-p7-plan.md` lines 85-90 G1~G5 정의 → M-Gate reference
  - 892 tests PASS (847 → 859 → 892)
- [x] **Step 7**: Diagnosis sub-task 진입 결정 — **2-trial plan 확정** (Trial 3 F 폐기)

## Current State

### Branch
`feature/si-p7-rebuild`

### Recent Commits (본 세션)
```
bff1544 [si-p7] Step 6: dev-docs 갱신 — narrative G1~G5 폐기 + M-Gate 결과 반영
9b9fc50 [si-p7] Step 3+4: S3 GU M-Gate 메인 스크립트 + 통합 테스트 (892 tests PASS)
886d30c [si-p7] Step 2: S3 GU M-Gate helpers + L1 tests (20 tests PASS)
21fb6e3 docs: session-compact 갱신 (S3 GU Gate false PASS 발견 → M-Gate 설계 plan 작성)
662fbeb [si-p7] analyze_trajectory --matrix 포맷 정리 + s3-gu-smoke matrix 재생성
```

### Untracked
- `bash.exe.stackdump` (무시)

### Working Tree
`docs/session-compact.md` 본 파일만 변경 (방금 갱신).

## Remaining / TODO

### 2-Trial Diagnosis Plan (확정)

| Trial | 적용 fix (cumulative) | cycles | M-Gate 목적 |
|-------|----------------------|--------|-------------|
| **1** | A (DIAG-ATTRACTION) + B (DIAG-T10-T14 telemetry M5b/M9/M10/M11) | 5c | T9 root cause fix 작동 검증 + strict 모드 가능해짐 |
| **2** | A+B + C (DIAG-YIELD cap ablation) + D (DIAG-M7 정책) + E (DIAG-CONNECTIVITY) | 5c | 5개 fix 통합 효과 — V/O 모두 PASS 확인 (S3 closure) |

각 trial 종료 후 → entity-field-matrix.json 생성 → `python scripts/check_s3_gu_gate.py --baseline ... --target ... --json m-gate-report.json` 실행 → JSON 리포트 보존.

### After Trial 2 PASS
- **Stage B-3 + B-4 re-organization** — 현 dev-docs 의 B-3 (S2-T3~T8) / B-4 (S4-T2~T4) 는 narrative G1~G5 PASS 가정 기반 설계. M-Gate 도입 + telemetry 추가 + diagnosis 결과 반영하여 axis-gate 도 mechanistic 기준으로 재정의 필요.
  - Stage B-3 (S2 condition_split): T9 fix 후 attraction adj GU 생성 패턴이 condition_split 로직과 충돌 가능성 — 재검토.
  - Stage B-4 (S4 category_balance): VxO frontier_health 가 7/8 healthy 인 만큼 balance 기준도 mechanistic 으로 재정의.

### Sub-task 별 진입 순서 (Trial 1 부터)

1. **DIAG-ATTRACTION** (Trial 1 의 A 부분)
   - M1 1.08× 의 root cause = T9 가 attraction 에서 안 돎. attraction 단독 fail (V/O 5개 모두 attraction 때문).
   - root cause 추적 → fix 구현 → Trial 1 실행 (B 와 함께)
2. **DIAG-T10-T14 telemetry** (Trial 1 의 B 부분)
   - M5b/M9/M10/M11 telemetry 추가:
     - M5b: `cap_hit_count` per cycle in trajectory (`integrate.py:280`, `state.py`, `run_readiness.py`)
     - M9: `gu['origin']` field (`integrate.py:570-597`, `gap-unit.json`)
     - M10: `gu['created_cycle']: int` (`state.py`, `integrate.py:255`, `seed.py`)
     - M11: trajectory row 에 `adj_gen_count`, `wildcard_gen_count` (`integrate.py`, `seed.py`, `run_readiness.py`)
   - check_s3_gu_gate.py 의 M5b/M9/M10/M11 평가 로직 활성화 (현재 NA 처리)
3. **Trial 1 실행 + M-Gate 판정**
4. **DIAG-YIELD** (Trial 2 의 C) — dynamic_cap 8/15/20 ablation, 최적값 결정
5. **DIAG-M7** (Trial 2 의 D) — conflict 해소 field 에 adj GU 재생성 6건. seed/integrate 단계의 conflict_field 필터 추가
6. **DIAG-CONNECTIVITY** (Trial 2 의 E) — connectivity vacant +1 regression 원인 추적
7. **Trial 2 실행 + M-Gate 판정** → S3 PASS 시 Stage B-3/B-4 reorg 진입

## Key Decisions

- **G1~G5 narrative Gate 폐기 확정**: 거짓 PASS 발급 도구. `si-p7-plan.md` 와 `si-p7-tasks.md` 모두 갱신 완료. 신 Gate (M-Gate) 단일 진실 소스 = `si-p7-gate-mechanistic.md`.
- **Plan §7.1 self-sanity PASS 가정 무효**: 베이스라인 (s3-smoke) 자체가 3개 cat abandoned (regulation, transport, attraction). Gate 가 절대형 기준으로 baseline 의 실제 unhealthy 상태를 정확히 포착. self-sanity 는 비교형 9개 PASS 로 Gate 로직 정상 확인.
- **V/O 우선 정책**: V/O FAIL 어느 하나 → unconditional FAIL (exit=1). M FAIL 만 있으면 exit=3 (CONDITIONAL).
- **Self-mode 처리**: path equality 시 비교형 criteria (V1/V3/M1/M3/M4/M6/M8) → no-regression 체크. 절대형 (O1/O2/VxO/M2/M5/M7) 은 그대로.
- **Telemetry-deferred 는 Gate 통과 선행 조건 아님**: M5b/M9/M10/M11 NA 처리 후 V/O + M1~M8 만으로 판정.
- **Plan §4 예시 numbers 부정확**: M1 baseline plan=7 vs 실측=13, M5 plan Δc4=0∧Δc5=0 FAIL vs 실측 Δc5=2 weak PASS. 실측이 더 정확.
- **2-trial diagnosis plan**: Trial 1 (A+B) → Trial 2 (A~E 통합). Trial 3 (F) 폐기. 비용 절감 + 빠른 closure.
- **Stage B-3/B-4 reorg 후속**: Trial 2 PASS 후 진행. 현 design 이 narrative G1~G5 가정 기반이라 mechanistic 기준으로 재정의 필요.

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 절대 경로 참조 (필독)

- **M-Gate 단일 진실 소스**: `dev/active/phase-si-p7-structural-redesign/si-p7-gate-mechanistic.md` (V/O 의미론, M criteria 임계값 근거, 실측 결과, diagnosis sub-tasks)
- **M-Gate 구현**: `scripts/check_s3_gu_gate.py` + `scripts/_gate_helpers.py`
- **M-Gate L1 tests**: `tests/scripts/test_gate_helpers.py` (20), `tests/scripts/test_check_s3_gu_gate.py` (13) — 모두 PASS
- **M-Gate 실 재판정 JSON**: `bench/silver/japan-travel/p7-rebuild-s3-gu-smoke/m-gate-report.json`
- **Plan 파일**: `C:\Users\User\.claude\plans\b-plann-very-carefully-breezy-flame.md` (M-Gate 설계 원본 — Plan §4 예시 numbers 일부 부정확, gate-mechanistic.md 가 최신)
- **베이스라인 trial**: `bench/silver/japan-travel/p7-rebuild-s3-smoke/`
- **타겟 trial**: `bench/silver/japan-travel/p7-rebuild-s3-gu-smoke/`
- **dev-docs 폴더**: `dev/active/phase-si-p7-structural-redesign/`
  - `si-p7-tasks.md` (lines 202-239 부근 = M-Gate 결과 + diagnosis sub-tasks)
  - `si-p7-plan.md` (lines 85-90 부근 = M-Gate reference)
  - `si-p7-gate-mechanistic.md` (신규)

### M-Gate 사용법

```bash
# 실 재판정
python scripts/check_s3_gu_gate.py \
  --baseline bench/silver/japan-travel/p7-rebuild-s3-smoke \
  --target   bench/silver/japan-travel/<new-trial> \
  --json     bench/silver/japan-travel/<new-trial>/m-gate-report.json

# strict 모드 (M5 strong form)
python scripts/check_s3_gu_gate.py ... --strict

# self-sanity (Gate 로직 점검)
python scripts/check_s3_gu_gate.py \
  --baseline bench/silver/japan-travel/p7-rebuild-s3-smoke \
  --target   bench/silver/japan-travel/p7-rebuild-s3-smoke
```

Exit code: 0 PASS / 1 FAIL (V/O) / 2 ERROR / 3 CONDITIONAL (V/O PASS, M FAIL).

### 코드 변경 위치 (Trial 1 의 B 부분 - telemetry)

- `_generate_dynamic_gus`: `src/nodes/integrate.py:195-280` (cap_hit_count emit)
- post-cycle sweep: `src/nodes/integrate.py:570-597` (gu['origin'] = 'post_cycle_sweep')
- claim loop GU 생성: `src/nodes/integrate.py:255-260` (gu['origin'] = 'claim_loop', gu['created_cycle'])
- WILDCARD_PARALLEL_FIELDS: `src/nodes/seed.py:40`
- dynamic_cap 고정값: `src/nodes/integrate.py:280-281` (현재 normal=8, jump=20)
- trajectory row schema: `scripts/run_readiness.py` (adj_gen_count, wildcard_gen_count 추가)
- gap-unit schema: `schemas/gap-unit.json` (origin, created_cycle 필드 추가)
- M-Gate 활성화: `scripts/check_s3_gu_gate.py` 의 `_na_result("M5b", ...)` → 실제 평가 함수로 교체

### 사용자 피드백/원칙

- "no bullshit" — 모든 임계값에 정량 근거 명시.
- "G1~G5 are all jerks" — 기존 narrative Gate 폐기 동의. M-Gate 가 정확히 작동.
- "self-sanity 는 false assumption 일 뿐" — Gate 자체에 버그 없음, 베이스라인 unhealthy 가 사실.
- 답변은 한국어, 단답 선호 (verbose 금지).
- 선택지는 2~3개로 축소 (memory rule `feedback_option_count`).
- T9~T14 mechanistic 검증을 Gate 본질로 봄.
- Vacant# 와 Open GU# 가 가장 중요한 1차 신호.

### 주의사항

- bench/silver 의 trial 은 real API 비용 발생 → 신중히 진행 (memory rule `feedback_api_cost_caution`).
- entity-field-matrix.json 은 모든 trial 완료 시 필수 (memory rule `feedback_standard_matrix_artifact`).
- 5c smoke 는 `python scripts/run_readiness.py --cycles 5 --trial-id si-p7-<task-id>-smoke` 로 실행 (silver-e2e-test-layering skill 참조).

## Next Action

**다음 세션 시작 직후 수행할 1차 액션**:

1. 본 `docs/session-compact.md` + `dev/active/phase-si-p7-structural-redesign/si-p7-gate-mechanistic.md` 모두 읽고 컨텍스트 복원.
2. `git status` + `git log -5` 로 미커밋 변경 확인.
3. **2-Trial Diagnosis Plan 진입** — User 에게 다음 옵션 제시:
   - **a**: Trial 1 의 **A 부분 (DIAG-ATTRACTION)** 부터 root cause 추적 시작 (entity discovery → GU 생성 단계 코드 분석, `src/nodes/integrate.py:_generate_dynamic_gus` 부터)
   - **b**: Trial 1 의 **B 부분 (telemetry)** 부터 시작 (4개 telemetry 필드 emit 추가 → schema 갱신 → check_s3_gu_gate.py M5b/M9/M10/M11 활성화). A 부분의 root cause 진단을 telemetry 로 정밀화 가능
   - **c**: Trial 1 사전 작업으로 **B-3/B-4 reorg plan 미리 검토** — 현 dev-docs 의 narrative 가정 식별 + reorg 범위 sketch (실제 reorg 는 Trial 2 PASS 후)
4. User 선택에 따라 진입.

**구현 순서 (Trial 1 권장)**:
- B (telemetry) 먼저 → A (ATTRACTION root cause) 가 telemetry 로 정밀해짐 → 통합 fix → Trial 1 실행 + M-Gate (strict 모드 활성화 가능) → 결과 확인 후 Trial 2 진입.

**Trial 2 후속**:
- Stage B-3 (S2 condition_split) + Stage B-4 (S4 category_balance) re-organization 진입. mechanistic 기준 (M-Gate 의 V/O + M criteria 패턴) 으로 axis-gate 재정의.
