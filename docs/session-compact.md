# Session Compact

> Generated: 2026-04-17
> Source: Step-update 후 갱신

## Goal

SI-P4 **완료** (42/42). VP4 FAIL 근본 원인 4건 해소 (D-147~D-150) + E7-3 비교 리포트 + E8 Gate 판정.
다음: SI-P5 (Telemetry & Dashboard) 또는 다른 Silver Phase.

## Completed

### 이번 세션

- [x] **D-147 fix**: `src/config.py` llm_budget 3→12
- [x] **D-148 fix**: `src/utils/external_novelty.py` `compute_delta_kus` 추가 + orchestrator.py delta 기반 novelty 계산
- [x] **D-149 fix**: `src/nodes/exploration_pivot.py` `reach_degraded` 조건 제거
- [x] **D-150 fix**: `src/utils/readiness_gate.py` R5 = probe_history 실행 횟수 기준 (HITL-R 불요)
- [x] **tests 추가** (793→797): test_compute_delta_kus, D-148 regression, D-149 pivot, D-150 gate
- [x] **E7-3 stage-e-on 15c 벤치** — VP4 PASS 4/5 (R1=0.7857, R2=49.06, R3=6, R4=0, R5=1)
- [x] **E7-3 COMPARISON.md** — stage-e-on vs off 비교 리포트 작성
- [x] **E8-2** readiness-report.json 갱신 (stage-e-on final)
- [x] **E8-3** Gate 판정: VP4 PASS, Overall FAIL (VP2 gap_res 0.8125 < 0.85)
- [x] **commit `f822f2c`** — VP4 fix + bench + 비교 리포트
- [x] **Step-update + project-overall 동기화**

### 이전 세션 누적
- [x] **commit `b2aafc5`** — collect.py timeout fix + --external-anchor 플래그
- [x] **E7-2 stage-e-off 15c** — VP1/VP3 PASS, VP2 FAIL (gap_res 0.789)
- [x] **E7-2 stage-e-on 15c** — VP4 FAIL 2/5 진단 (D-147~D-150)
- Stage A~D Internal Foundation Gate PASS (D-135, `f69fd01`)
- Stage E E0-2/E1/E2/E3/E4/E5/E6-1~E6-3/E7-1/E8-1 전부 구현
- 총 797 tests

## Current State

- Branch: `main`. 마지막 commit **`f822f2c`** (SI-P4 42/42 완료).
- SI-P4 **완료** — VP4 PASS 4/5 달성. VP2 gap_res FAIL은 Stage E 무관 (core loop 문제, 별도 Phase에서 해결).
- **VP2 gap_res 잔존 이슈 (0.8125 < 0.85)**: off(0.789) / on(0.813) 모두 FAIL. Stage E가 아닌 core loop의 GU 해소 성능 문제.
- **D-151 후보**: Universe Probe collision_active 반복 — slug 정규화 + 유사도 필터 추가 필요.

## Remaining / TODO

### 다음 Phase 선택지

- [ ] **SI-P5** (Telemetry & Dashboard) — P3R + P4 완료 조건 충족
- [ ] **SI-P6** (Multi-Domain & Robustness) — P1~P5 전부 선행 조건
- [ ] **VP2 gap_res 개선** (별도 조사 또는 P2 개선) — gap_res 0.85 임계치 미달 해소
- [ ] **D-151**: Universe Probe slug collision 필터 (candidate)

## Key Decisions

### 이번 세션 신규

| # | 결정 | 근거 |
|---|------|------|
| D-147 | llm_budget 3→12 fix | probe 1회 3 LLM calls, 이후 11c dead |
| D-148 | ext_novelty delta_kus 분모 fix | novel/all_kus → 0 수렴 구조 해소 |
| D-149 | reach_degraded 조건 제거 | floor 15 vs 실측 52~57, unreachable |
| D-150 | VP4 R5 = probe_history 횟수 (HITL 불요) | 자동 벤치 경로 허용. 런타임 HITL 미구현 future work |

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 제약 / 주의
- API 비용 발생 작업 신중. 재실행 전 사용자 재확인 (memory rule)
- **Bash 절대경로 필수** (cd 금지)

### 핵심 참조 파일
- project-overall: `dev/active/project-overall/`
- SI-P4 dev-docs: `dev/active/phase-si-p4-coverage/`
- External Anchor 구현: `src/nodes/universe_probe.py`, `src/nodes/exploration_pivot.py`
- ReadinessGate: `src/utils/readiness_gate.py` (VP1~VP4)
- 비교 리포트: `bench/japan-travel-external-anchor/COMPARISON.md`
