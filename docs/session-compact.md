# Session Compact

> Generated: 2026-04-26
> Source: Conversation compaction via /compact-and-go

## Goal

Trial 1 B (telemetry M5b/M9/M10/M11 emit) + Gate 활성화 + Trial 1 A (DIAG-ATTRACTION fix) → Trial 1 실행 + M-Gate 판정. 2-Trial Diagnosis Plan 의 S3 closure 목적.

## Completed

- [x] **M9: gu['origin'] attribution** (`2734bc1`)
  - `schemas/gap-unit.json`: origin enum 추가
  - `src/nodes/seed.py`: `origin: "seed_bootstrap"`
  - `src/nodes/integrate.py`: `origin: "claim_loop"` / `"post_cycle_sweep"`
- [x] **M10: gu['created_cycle'] int** (`2734bc1`, 896 tests PASS)
- [x] **M11: trajectory adj_gen_count + wildcard_gen_count** (`8e20377`)
  - `src/state.py`: `_diag_wildcard_gen_count` 추가
  - `src/nodes/seed.py`: wildcard count 반환
  - `src/utils/metrics_logger.py`: `adj_gen_count`, `wildcard_gen_count` entry
- [x] **M5b: cap_hit_count** (`8e20377`, 902 tests PASS)
  - `src/state.py`: `_diag_cap_hit_count` 추가
  - `src/utils/metrics_logger.py`: `cap_hit_count` entry
  - L1 tests: `test_m5b_*` 2개
- [x] **Task #5: Gate 활성화** (`4833186`, 910 tests PASS)
  - `scripts/check_s3_gu_gate.py`: `eval_m5b/m9/m10/m11` 4개 함수 추가
  - `_na_result` 4개 → 실 평가 함수 교체
  - L2 tests: 8개 (PASS/FAIL pair × 4)
- [x] **DIAG-ATTRACTION root cause 확인 + fix** (현재 세션, 911 tests PASS)
  - **Root cause**: attraction seed GU = 전부 wildcard. Cycle 1에서 regulation/payment 클레임이 `dynamic_cap=8` 선점 → sweep도 cap 공유로 차단 → attraction adj GU 0개.
  - **Fix**: S3-T10 sweep에 claim loop와 독립된 자체 budget(`_sweep_budget = dynamic_cap`) 부여
  - `src/nodes/integrate.py`: `_claim_loop_gu_count` 캡처, sweep 독립 budget, `_cap_hit = _claim_loop_gu_count >= dynamic_cap`
  - L1 tests: `test_sweep_respects_combined_cap`, `test_sweep_independent_budget_when_claim_loop_full`

## Current State

### Branch
`feature/si-p7-rebuild`

### Recent Commits (본 세션)
```
4833186 [si-p7] Task #5: Gate 활성화 — M5b/M9/M10/M11 _na_result → 실 평가 함수
8e20377 [si-p7] Trial 1 B: M11/M5b telemetry — adj/wildcard/cap_hit 기록
2734bc1 [si-p7] Trial 1 B: M9/M10 telemetry — gu origin + created_cycle 부여
```

### Uncommitted (DIAG-ATTRACTION fix)
- `src/nodes/integrate.py` — S3-T10 sweep 독립 budget + `_cap_hit` 수정
- `tests/test_nodes/test_integrate.py` — 기존 cap test 갱신 + 2개 신규

### Test Count
**911 PASS**, 3 skipped

## Remaining / TODO

### 즉시 (이번 세션 연속)

- [ ] **DIAG-ATTRACTION commit** — 911 tests PASS 확인됨
- [ ] **Trial 1 실행** — `python scripts/run_readiness.py --cycles 5 --trial-id si-p7-s3-trial1-smoke`
  - 실행 전: API 키 확인, bench 디렉토리 확인
  - 주의: real API 비용 발생
- [ ] **Trial 1 M-Gate 판정**
  ```bash
  python scripts/analyze_trajectory.py \
    --bench-root bench/silver/japan-travel/si-p7-s3-trial1-smoke --matrix
  python scripts/check_s3_gu_gate.py \
    --baseline bench/silver/japan-travel/p7-rebuild-s3-smoke \
    --target   bench/silver/japan-travel/si-p7-s3-trial1-smoke \
    --json     bench/silver/japan-travel/si-p7-s3-trial1-smoke/m-gate-report.json \
    --strict
  ```
  - M1 목표: ≥ 26 named entity adj GU (2× baseline 13)
  - M5b/M9/M10/M11: 이제 실 평가 (new trial에서 PASS 예상)
  - V1 목표: Δ ≥ 29 vacant 감소

### Trial 1 PASS 후 → Trial 2

- [ ] **SI-P7-S3-DIAG-YIELD** (C) — M6 0.72 (adj_yield 28% 후퇴) + dynamic_cap ablation
- [ ] **SI-P7-S3-DIAG-M7** (D) — conflict field adj GU 재생성 6건 정책 위반
- [ ] **SI-P7-S3-DIAG-CONNECTIVITY** (E) — connectivity vacant +1 regression
- [ ] **Trial 2 실행 + M-Gate** → V/O 6/6 PASS → S3 closure

## Key Decisions

- **DIAG-ATTRACTION fix = S3-T10 독립 budget**: sweep이 claim loop cap 소진과 무관하게 자체 `dynamic_cap` budget 보유. total max = 2 × dynamic_cap per cycle.
- **_cap_hit = claim loop count 기반**: sweep adj GU는 cap_hit 카운트에 포함 안 됨.
- **Trial 1 = A+B 누적 적용**: DIAG-ATTRACTION fix + telemetry 4종 모두 포함.

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 절대 경로 참조 (필독)

- **M-Gate 단일 진실 소스**: `dev/active/phase-si-p7-structural-redesign/si-p7-gate-mechanistic.md`
- **M-Gate 구현**: `scripts/check_s3_gu_gate.py` + `scripts/_gate_helpers.py`
- **M-Gate L1 tests**: `tests/scripts/test_gate_helpers.py` (20), `tests/scripts/test_check_s3_gu_gate.py` (21)
- **M-Gate 실 재판정 JSON**: `bench/silver/japan-travel/p7-rebuild-s3-gu-smoke/m-gate-report.json`
- **Telemetry 파일**: `src/nodes/integrate.py`, `src/nodes/seed.py`, `src/state.py`, `src/utils/metrics_logger.py`
- **베이스라인 trial**: `bench/silver/japan-travel/p7-rebuild-s3-smoke/`
- **타겟 trial (Trial 1)**: `bench/silver/japan-travel/si-p7-s3-trial1-smoke/` (미생성)

### Trial 1 실행 전 확인 사항

```bash
# 미커밋 파일 commit 먼저
git -C "C:\Users\User\Learning\KBs-2026\domain-k-evolver" add src/nodes/integrate.py tests/test_nodes/test_integrate.py
git -C "C:\Users\User\Learning\KBs-2026\domain-k-evolver" commit -m "[si-p7] DIAG-ATTRACTION: S3-T10 sweep 독립 budget — attraction adj GU 생성 블로커 해소"

# API 키 확인
echo $OPENAI_API_KEY | head -c 10
echo $TAVILY_API_KEY | head -c 10

# Trial 실행
python scripts/run_readiness.py --cycles 5 --trial-id si-p7-s3-trial1-smoke
```

### M-Gate 사용법
```bash
python scripts/check_s3_gu_gate.py \
  --baseline bench/silver/japan-travel/p7-rebuild-s3-smoke \
  --target   bench/silver/japan-travel/si-p7-s3-trial1-smoke \
  --json     bench/silver/japan-travel/si-p7-s3-trial1-smoke/m-gate-report.json \
  --strict
```

### DIAG-ATTRACTION fix 상세

**근본 원인**:
1. attraction seed GU = 전부 wildcard (`japan-travel:attraction:*` × 4 fields)
   - 이유: 최초 seed 시 attraction entity 없음 → `known_entities = []` → `else` 브랜치 → wildcard
2. Cycle 1 claim loop: regulation/payment 클레임이 `dynamic_cap=8` 먼저 소진
3. attraction 클레임이 처리될 때 `len(new_dynamic_gus) >= dynamic_cap` → adj GU 생성 불가
4. S3-T10 sweep도 `len(new_dynamic_gus) >= dynamic_cap` → `break` → attraction sweep 불가
5. Cycle 2-5: attraction wildcard GU 전부 resolved → plan에서 attraction target 없음 → 영구 방치

**Fix 내용**:
- `_claim_loop_gu_count = len(new_dynamic_gus)` (sweep 시작 전 캡처)
- sweep에 `_sweep_budget = dynamic_cap`, `_sweep_added = 0` 독립 카운터
- `_cap_hit = 1 if _claim_loop_gu_count >= dynamic_cap else 0`
- 효과: cycle 1에서 sweep이 attraction senso-ji 등 named entity adj GU를 독립 budget으로 생성

### 사용자 피드백/원칙
- "no bullshit" — 모든 임계값에 정량 근거 명시
- 답변은 한국어, 단답 선호 (verbose 금지)
- 선택지는 2~3개로 축소
- bench/silver 의 trial 은 real API 비용 발생 → 신중히 진행
- entity-field-matrix.json 은 모든 trial 완료 시 필수

## Next Action

**DIAG-ATTRACTION commit 직후 Trial 1 실행**:

1. commit:
   ```bash
   git add src/nodes/integrate.py tests/test_nodes/test_integrate.py
   git commit -m "[si-p7] DIAG-ATTRACTION: S3-T10 sweep 독립 budget — attraction adj GU 생성 블로커 해소"
   ```

2. Trial 1 실행 (real API, ~$0.5 예상):
   ```bash
   python scripts/run_readiness.py --cycles 5 --trial-id si-p7-s3-trial1-smoke
   ```

3. matrix 생성:
   ```bash
   python scripts/analyze_trajectory.py \
     --bench-root bench/silver/japan-travel/si-p7-s3-trial1-smoke --matrix
   ```

4. M-Gate 판정:
   ```bash
   python scripts/check_s3_gu_gate.py \
     --baseline bench/silver/japan-travel/p7-rebuild-s3-smoke \
     --target   bench/silver/japan-travel/si-p7-s3-trial1-smoke \
     --json     bench/silver/japan-travel/si-p7-s3-trial1-smoke/m-gate-report.json \
     --strict
   ```

5. 결과에 따라:
   - PASS → Trial 2 준비 (DIAG-YIELD/M7/CONNECTIVITY)
   - FAIL → 추가 root cause 분석
