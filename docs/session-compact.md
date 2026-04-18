# Session Compact

> Generated: 2026-04-18
> Source: Conversation compaction via /compact-and-go

## Goal

A1-D3 완료 (15c full bench + root cause 확정) → A2~A4 착수

## Completed

- [x] **dev-docs 커밋** (e31b531) — A1 후속 조사 완료: wildcard 분석 + D-162 진단 로깅 전략
- [x] **A1-D1: 진단 로깅 추가** (320caf0)
  - `src/nodes/collect.py` — `_collect_single_gu` → `(claims, search_count)` 튜플, `_diag_search_by_gu` state 전달
  - `src/nodes/integrate.py` — `_diag_resolved_gus`, `_diag_adjacent_gap_count` return 추가
  - `src/orchestrator.py` — `_extract_cycle_ctx()` + `_diag_*` 필드 state 정리 + `emit_cycle` 전달
  - `src/obs/telemetry.py` — `cycle_trace` 블록 + `emit_gu_trace()` (gu_trace.jsonl append)
  - `src/state.py` — `_diag_*` 3개 필드 추가
  - `schemas/telemetry.v1.schema.json` — `cycle_trace` 필드 추가
  - 테스트: 821 passed 유지
- [x] **A1-D2: analyze_saturation.py 옵션 4종** (5232155)
  - `--trace-frozen N`: N cycle 이상 open GU + yield (gu_trace/스냅샷 fallback)
  - `--query-patterns`: wildcard vs concrete search yield 분포
  - `--cycle-diff C1 C2`: gap_map 상태 변화 상세
  - `--compare-trials A B`: 두 trial open GU entity:field 집합 비교
- [x] **A1-D3 일부: p6-diag-smoke-5c 실행** (stage-e-off, 5c)
  - `bench/silver/japan-travel/p6-diag-smoke-5c/` trial 완료
  - `telemetry/gu_trace.jsonl` 155행 생성 확인
  - `--query-patterns` 결과: **wildcard avg_yield = 0.0 (cycle 2~5)**, concrete avg_yield = 11.95
  - wildcard zero_yield 비율: 17/27 (63%) — 가설 강하게 지지

## Current State

**브랜치**: `main`
**최신 commit**: `5232155` (`[si-p6] A1-D2: analyze_saturation.py 진단 옵션 4종 추가`)
**테스트**: 821 passed, 3 skipped

### Changed Files (미커밋 없음)

- `bench/silver/japan-travel/p6-diag-smoke-5c/` — 5c smoke trial 완료
- `bench/silver/japan-travel/p6-diag-full-15c/trial-card.md` — 생성됨 (bench 미실행)

### 주요 진단 데이터 (p6-diag-smoke-5c)

| type     | count | avg_yield | zero_yield |
|----------|-------|-----------|------------|
| wildcard | 27    | 5.56      | 17/27 (63%) |
| concrete | 128   | 11.95     | 26/128 (20%) |

cycle별 wildcard avg_yield: c1=12.5, c2=0.0, c3=0.0, c4=0.0, c5=0.0

## Remaining / TODO

### A1-D3 나머지

- [ ] **15c full bench 실행** (stage-e-on, `p6-diag-full-15c`) — 비용 ≈ $1
  ```bash
  PYTHONUTF8=1 python scripts/run_readiness.py \
    --cycles 15 \
    --bench-root bench/silver/japan-travel/p6-diag-full-15c \
    --audit-interval 5 \
    --external-anchor
  ```
  **주의**: exit code 1이어도 로그에 "Orchestrator 완료: 15 cycles" 있으면 재실행 금지
- [ ] **진단 분석 실행**
  ```bash
  python scripts/analyze_saturation.py --query-patterns --trials p6-diag-full-15c
  python scripts/analyze_saturation.py --trace-frozen 3 --trials p6-diag-full-15c
  python scripts/analyze_saturation.py --compare-trials p6-diag-smoke-5c p6-diag-full-15c
  ```
- [ ] **Root cause 확정** — wildcard GU의 search_yield, stage-e-on vs off 비교, debug-history.md 업데이트

### A2~A4 (root cause 확정 후 착수)

계획은 `dev/active/phase-si-p6-consolidation/si-p6-consolidation-tasks.md` 참조

## Key Decisions

### D-162 (2026-04-18)
진단 로깅 우선 전략 — 실 bench 데이터로 확정 후 fix

### 5c smoke 결과 (2026-04-18)
- wildcard GU: cycle 2~5 search_yield = **0.0** (zero_yield 63%)
- concrete GU: avg_yield = 11.95
- **plan.py slug 버그 가설 강하게 지지**: `entity_key.split(":")[-1]` → `"*"` → 의미없는 쿼리 → Tavily 결과 없음

### run_readiness.py exit code 교훈 (2026-04-18)
- **exit code 1 = Gate FAIL, bench 완료와 무관**
- 동일 명령 재실행 → 5c 두 번 실행, API 비용 ≈ $0.35 중복 낭비
- **교훈**: exit code 1 시 로그에서 "Orchestrator 완료: N cycles" 먼저 확인 후 재실행 여부 판단
- cycles.jsonl에 중복 행 주의 (10행 = 5+5 중복)

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

- **API 비용**: D3 15c ≈ $1. 실행 전 확인 필수. exit code 1 시 재실행 금지
- **핵심 가설**: wildcard GU → 의미없는 쿼리(plan.py slug 버그) → search_yield=0 → claims=0 → resolve 불가 → pool 동결
- **확인된 사실**: smoke 5c에서 wildcard zero_yield 63%, cycle 2~5 avg=0.0
- **미확인 (15c full에서 확정 필요)**: stage-e-on에서 External Anchor → attraction entity flood → wildcard GU 증폭 여부
- **핵심 코드**:
  - `src/nodes/plan.py:268` — slug 버그 (`split(":")[-1]` → `"*"`)
  - `src/nodes/seed.py:293-306` — fallback wildcard (버그 후보)
  - `src/obs/telemetry.py` — `emit_gu_trace`, `_build_cycle_trace` (D1 구현)
  - `scripts/analyze_saturation.py` — D2 옵션 4종

## Next Action

**Step 1: 15c full bench 실행** (stage-e-on)

```bash
PYTHONUTF8=1 python scripts/run_readiness.py \
  --cycles 15 \
  --bench-root bench/silver/japan-travel/p6-diag-full-15c \
  --audit-interval 5 \
  --external-anchor \
  2>&1 | tail -60
```

exit code 1이어도 "Orchestrator 완료: 15 cycles" 있으면 성공. 재실행 금지.

**Step 2: 진단 분석**

```bash
PYTHONUTF8=1 python scripts/analyze_saturation.py --query-patterns --trials p6-diag-full-15c
PYTHONUTF8=1 python scripts/analyze_saturation.py --trace-frozen 3 --trials p6-diag-full-15c
PYTHONUTF8=1 python scripts/analyze_saturation.py --compare-trials p6-diag-smoke-5c p6-diag-full-15c
```

**Step 3: Root cause 확정 → debug-history.md 업데이트 → dev-docs 커밋**
