# Session Compact

> Generated: 2026-04-16 23:00
> Source: Step-update 후 갱신

## Goal

SI-P4 Stage E 벤치 검증 (E7-2) + VP4 실패 근본 원인 분석 → VP4 fix 방안 + E7-3 비교 리포트 + E8 Gate 판정.
계획: `C:\Users\User\.claude\plans\lovely-imagining-popcorn.md`.
Phase tasks: `dev/active/phase-si-p4-coverage/si-p4-coverage-tasks.md`.

## Completed

### 이번 세션

- [x] **commit `b2aafc5`** — collect.py timeout fix (300s/120s + TimeoutError graceful handling) + run_readiness.py --external-anchor 플래그
- [x] **E7-2 stage-e-off 15c 실행** — 완주 성공 (1378.6s, KU 116). VP1 PASS 5/5, VP2 FAIL 4/6 (gap_res 0.789), VP3 PASS 5/6
- [x] **E7-2 stage-e-on 15c 실행** — 완주 성공 (1335.4s, KU 97). VP1 PASS 5/5, VP2 FAIL 4/6 (gap_res 0.750), VP3 PASS 5/6, VP4 FAIL 2/5
- [x] **VP4 FAIL 근본 원인 분석** — 4건 독립적 원인 진단 (D-147~D-150):
  1. Budget kill-switch cycle 4 발동 → 이후 11c Stage E 사실상 off
  2. ext_novelty 산식 = novel/total_keys → 0 수렴 (0.25 임계치 구조적 불가)
  3. exploration_pivot 조건 unreachable (domains_per_100ku 52~57 vs floor 15)
  4. category_addition HITL-R 필수 → 자동 벤치 원천 불가
- [x] **Step-update + project-overall 동기화** — commit + push

### 누적 (이전 세션까지)
- Stage A~D Internal Foundation Gate PASS (D-135, `f69fd01`)
- Stage E E0-2/E1/E5/E6-1/E6-2 — `df219e5`
- Stage E E2 (universe_probe 3-step pipeline) — `618bb21`
- Stage E E3 (reach_ledger) — `cf83733`
- Stage E E4 (exploration_pivot) — `47a798f`
- Stage E E6-3/E7-1/E8-1 — `a4df15d`
- Stage E Step-update docs — `d2f6c7c`
- 총 793 tests

## Current State

- Branch: `main`. 마지막 commit **`b2aafc5`** (+ step-update commit 추가 예정).
- **bench 결과 디렉토리** (uncommitted):
  - `bench/japan-travel-external-anchor/stage-e-off/` — readiness-report.json + state + trajectory
  - `bench/japan-travel-external-anchor/stage-e-on/` — readiness-report.json + state + trajectory

## Remaining / TODO

### VP4 Fix 방안 설계 (다음 세션 첫 단계)
- [ ] **D-147 fix**: llm_budget 확대 (3 → 최소 9~12) — universe_probe 2~3회 + exploration_pivot 여유
- [ ] **D-148 fix**: ext_novelty 산식 재설계 — `novel / delta_keys` (이번 cycle 신규 KU 키만 분모) 또는 sliding window
- [ ] **D-149 fix**: exploration_pivot 조건 재설계 — `domains_per_100ku < 15` 대신 novelty+growth 복합 정체 조건
- [ ] **D-150 fix**: category_addition 자동 벤치 경로 — candidate_categories 등록 자체를 점수화 (HITL 승격 불요) 또는 VP4 기준에서 제외/완화
- [ ] VP4 fix 코드 반영 후 stage-e-on 재실행 (15c, API 비용 ~$1-1.5)

### E7-3 비교 리포트
- [ ] `bench/japan-travel-external-anchor/COMPARISON.md` 작성 — on vs off 지표 + VP4 failure analysis

### E8 Gate 판정
- [ ] **E8-2** VP4 fix 후 재실행 결과로 readiness-report 갱신
- [ ] **E8-3** Gate 판정 commit `[si-p4] Stage E Gate PASS/FAIL: {근거}`

## Key Decisions

### 이번 세션 신규

| # | 결정 | 근거 |
|---|------|------|
| D-144 | collect.py as_completed timeout 120→300s, future.result 60→120s | cycle 진행에 따른 parse 시간 증가. cycle 5에서 160s 초과 |
| D-145 | as_completed TimeoutError catch → graceful degradation | 기존 uncaught → cycle 전체 abort → 15c 미완주 |
| D-146 | --external-anchor / --no-external-anchor 플래그 env override | 벤치 비교 시 config 오염 방지 |
| D-147 | **VP4 FAIL**: budget kill-switch — llm_budget=3이 probe 1회분 | 이후 11c Stage E 사망. budget 확대 필요 |
| D-148 | **VP4 FAIL**: ext_novelty novel/total_keys → 0 수렴 | 분모 단조 증가 → 0.25 구조적 불가. 산식 재설계 |
| D-149 | **VP4 FAIL**: pivot 조건 domains_per_100ku<15 unreachable | 실측 52~57, floor의 3.5배. 조건 재설계 |
| D-150 | **VP4 FAIL**: category_addition HITL-R 필수 → 자동 벤치 불가 | registered=2 완료했으나 승격 불가. 기준 재설계 |

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 사용자 승인 사항
- "commit and bench test" → "both" = 코드 작업 + 벤치 실행 모두 승인
- 벤치 재실행은 fix 적용 후 **사용자 재확인 필수**

### 제약 / 주의
- API 비용 발생 작업 신중. 재실행 전 사용자 재확인 (memory rule)
- **Bash 절대경로 필수** (cd 금지)
- Tavily rate limit 주의 — 이번 세션에서 1회 초과로 오염 결과 발생 경험

### 핵심 참조 파일
- 상위 계획: `C:\Users\User\.claude\plans\lovely-imagining-popcorn.md`
- Phase tasks: `dev/active/phase-si-p4-coverage/si-p4-coverage-tasks.md` (E7-3/E8-2/E8-3 남음)
- Phase context: `dev/active/phase-si-p4-coverage/si-p4-coverage-context.md` (D-144~D-150 추가)
- VP4 구현: `src/utils/readiness_gate.py::evaluate_vp4` (R1~R5 + 80%+ critical 패턴)
- External Anchor config: `src/config.py::ExternalAnchorConfig` (enabled, probe_interval_cycles, budgets)
- Orchestrator 통합: `src/orchestrator.py::_maybe_run_universe_probe` / `_maybe_run_exploration_pivot`
- Cost Guard: `src/utils/cost_guard.py` — kill-switch 로직 (D-147 핵심)
- External Novelty: `src/utils/external_novelty.py` — novel/total_keys 산식 (D-148 핵심)
- Reach Ledger: `src/utils/reach_ledger.py` — is_reach_degraded floor=15 (D-149 핵심)
- Universe Probe: `src/nodes/universe_probe.py` — registered=2 but HITL-R 필요 (D-150 핵심)

### VP4 Failure Summary (quick reference)

| VP4 기준 | 실측 | 임계치 | 상태 | 근본 원인 |
|---------|------|--------|------|-----------|
| R1 external_novelty | 0.085 | ≥ 0.25 | **CRITICAL** | 산식 0 수렴 (D-148) |
| R2 distinct_domains | 54.6 | ≥ 15 | PASS | — |
| R3 validated_proposals | 2 | ≥ 2 | PASS | — |
| R4 exploration_pivot | 0 | ≥ 1 | FAIL | 조건 unreachable (D-149) + kill-switch (D-147) |
| R5 category_addition | 0 | ≥ 1 | FAIL | HITL-R 필수 (D-150) |

## Next Action

1. **VP4 fix 방안 설계** — D-147~D-150 각각 fix 코드 작성
2. **stage-e-on 재실행** (VP4 fix 적용 후, 사용자 확인 필수)
3. **E7-3** 비교 리포트 작성
4. **E8-2** readiness-report VP4 실측 갱신
5. **E8-3** Gate 판정 + commit
6. **최종 commit 묶음** — bench 결과 + dev-docs 업데이트
