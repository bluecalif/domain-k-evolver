# Session Compact

> Generated: 2026-04-16
> Source: Conversation compaction via /compact-and-go

## Goal

SI-P4 Stage E 잔여 코드 작업 완료 — **E6-3 / E7-1 / E8-1** (실 벤치 의존 없음).
계획: `C:\Users\User\.claude\plans\lovely-imagining-popcorn.md` (29-task 4-계층).
Phase tasks: `dev/active/phase-si-p4-coverage/si-p4-coverage-tasks.md`.

## Completed

### 누적 (이전 세션까지)
- [x] Stage A~D, Internal Foundation Gate PASS (D-135)
- [x] Stage E E0-1/E0-2/E1/E5 — `df219e5`
- [x] Stage E E2 (universe_probe 3-step pipeline) — `618bb21`
- [x] Stage E E3 (reach_ledger) — `cf83733`
- [x] Stage E E4 (exploration_pivot) — `47a798f`
- [x] 총 775 tests

### 이번 세션 (3개 코드 작업)

- [x] **E6-3** budget kill-switch orchestrator 통합 테스트 (+2 tests)
  - `tests/test_orchestrator.py::TestStageEKillSwitchIntegration`
  - `test_pre_killed_skips_all_stage_e_nodes` — 강제 _trip 후 universe_probe + exploration_pivot 모두 skip, core loop 5c 정상
  - `test_budget_exhausted_mid_run_blocks_subsequent_probes` — 첫 probe 가 LLM budget(=1) 소진, 다음 probe trigger cycle 에서 kill-switch 로 skip
- [x] **E7-1** Synthetic injection 테스트 (+4 tests, 신규 파일)
  - `tests/integration/test_synthetic_injection.py` — universe_probe 4-step pipeline 의 ground-truth 발견 검증
  - `test_single_hidden_category_surfaced` — accessibility 1개
  - `test_multiple_hidden_categories_surfaced` — accessibility/seasonality/budget-extremes 3개
  - `test_noise_proposals_filtered_by_validator` — noise는 validator 단계에서 reject
  - `test_collision_with_active_skeleton_rejected_in_survey` — active slug collision 은 survey 단계에서 reject
- [x] **E8-1** readiness_gate.py VP4 추가 (+12 tests)
  - `src/utils/readiness_gate.py::evaluate_vp4` — 5 criteria
  - `evaluate_readiness(..., external_anchor_enabled=False)` 신규 파라미터 — 기본 False 로 기존 호출자 호환성 유지, True 시 viewpoints 에 VP4 포함
  - `tests/test_readiness_gate.py::TestVP4` (9) + `TestEvaluateReadinessWithVP4` (3)

### 테스트 수
- Pre-session: 775
- Post-session: **793** (+18, +2.3%)

## Current State

- Branch: `main`. 마지막 commit `47a798f`.
- **Uncommitted** (이번 세션 변경, 4 files):
  - `src/utils/readiness_gate.py` (수정 — evaluate_vp4 + 모듈 docstring + evaluate_readiness 파라미터)
  - `tests/test_readiness_gate.py` (수정 — import + TestVP4 + TestEvaluateReadinessWithVP4)
  - `tests/test_orchestrator.py` (수정 — TestStageEKillSwitchIntegration class 추가)
  - `tests/integration/test_synthetic_injection.py` (신규)
- Stage E 진행: E0-1 ✅ E0-2 ✅ E1 ✅ E2 ✅ E3 ✅ E4 ✅ E5 ✅ **E6 ✅ E7-1 ✅ E8-1 ✅** → 다음 E7-2/E7-3/E8-2/E8-3 (실 벤치).

### Stage E 완료 코드 베이스 (참조)

- `src/utils/cost_guard.py` — CostGuard (allow/record/_trip kill-switch)
- `src/utils/external_novelty.py` — compute_external_novelty
- `src/utils/skeleton_tiers.py` — active/candidate 분리 helpers
- `src/utils/reach_ledger.py` — publisher_domain/tld 추적, distinct_domains_per_100ku, is_reach_degraded
- `src/utils/readiness_gate.py` — VP1/VP2/VP3 + **VP4** (외부 anchor)
- `src/nodes/universe_probe.py` — 3-step pipeline + should_run trigger
- `src/nodes/exploration_pivot.py` — should_pivot + query rewriter + candidate axis probe
- `src/orchestrator.py` — _maybe_run_universe_probe, _maybe_run_exploration_pivot, _cost_guard, reach_history
- `src/config.py:ExternalAnchorConfig` — enabled, probe_interval_cycles, budgets

## Remaining / TODO

### E7 Validation (실 벤치)
- [ ] **E7-2** Stage-E-on vs off 15c trial × 2 비교 — `scripts/run_readiness.py` 에 `--external-anchor` 플래그 추가 또는 config override. **API 비용 발생** (실 OpenAI/Tavily). 사용자 확인 필수.
- [ ] **E7-3** `bench/japan-travel-external-anchor/` 디렉터리 + 비교 리포트 MD

### E8 Stage E Gate Judgment
- [ ] **E8-2** E7-2 결과로 VP4 실측 + readiness-report.md 갱신
- [ ] **E8-3** Gate 판정 commit `[si-p4] Stage E Gate PASS/FAIL: {근거}`

### 즉시 결정 필요
- [ ] 이번 세션 4 files commit — **이번 세션 사용자에게 commit 결정 묻고 답변 대기 중**

## Key Decisions

### VP4 (E8-1) 설계 결정
- **5 criteria** (lovely-imagining-popcorn 계획 verbatim):
  - R1 external_novelty avg ≥ 0.25 (**critical**)
  - R2 distinct_domains_per_100ku ≥ 15 (마지막 cycle 기준)
  - R3 validated_proposals ≥ 2 (**critical**, candidate_categories 누적)
  - R4 exploration_pivot ≥ 1 (pivot_history 누적)
  - R5 category_addition ≥ 1 (phase_history 의 proposal_types 카운트)
- **80% 통과 + critical 무실패** → VP4 PASS (기존 VP1~3 패턴 일치)
- **Cold-start 보정**: ext_history[0] (cycle 1) 은 평균 계산에서 제외 — 모든 key 가 신규라 1.0 이 항상 나오기 때문
- **검증된 proposals = candidate_categories count**: HITL-R 대기 큐. 미검증 proposals 따로 추적 안 함.
- **opt-in via flag**: `evaluate_readiness(..., external_anchor_enabled=False)` 기본 False — 기존 Phase 4 게이트 호환성 유지. Stage E 실 벤치 평가에서 `True` 로 호출.

### E6-3 테스트 전략
- 강제 `_trip()` 호출로 kill-switch pre-trigger → cleaner 테스트 (실 budget 시뮬레이션 vs pre-killed 두 갈래로 분리)
- mock_llm/mock_search 가 호출 안 되는 것을 `assert_not_called()` 로 직접 검증
- core loop 정상 진행은 `len(orch.results) == max_cycles` 로 확인

### E7-1 Synthetic Injection 패턴
- mock LLM 이 ground-truth slug 을 encode (실제 LLM 지능 검증 아님 — pipeline 메커니즘 검증)
- validator mock 은 prompt 의 `Proposed category:` 라인을 파싱해 ground-truth set 멤버십으로 분기 → 진짜와 noise 구별 시뮬레이션
- `tests/integration/` 디렉토리에 배치 (단위 vs 통합 분리)

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 핵심 참조 파일
- 상위 계획: `C:\Users\User\.claude\plans\lovely-imagining-popcorn.md` (VP4 기준 라인 ~400)
- Phase tasks: `dev/active/phase-si-p4-coverage/si-p4-coverage-tasks.md` (E6-E8 라인 208-224)

### E7-2 실 벤치 가이드
- 진입점: `scripts/run_readiness.py` (single entrypoint, CLAUDE.md 정책)
- 옵션 추가 필요: `--external-anchor` 플래그 OR `EVOLVER_EXTERNAL_ANCHOR_ENABLED=true` env override
- 15c × 2 trial (Stage-E-on, Stage-E-off) → API 비용 ≈ 일반 15c 의 2배 + Stage E 추가 호출
- evaluate_readiness 호출 시 `external_anchor_enabled=cfg.external_anchor.enabled` 로 전달 — run_readiness.py 에 한 줄 수정 필요
- 결과 디렉토리: `bench/japan-travel-external-anchor/{trial_id}/` (E7-3)

### 제약/주의 (memory rule)
- API 비용 발생 작업 신중. E7-2 는 사용자 확인 필수.
- Phase Gate = 합성 E2E + 실 벤치 trial 비교 필수.
- 전체 테스트 ≥ 700 (현재 793).
- Bash 절대경로 (cd 금지).

### 작업 흐름
E0-1 ✅ → E0-2 ✅ → E1 ✅ → E5 ✅ → E2 ✅ → E3 ✅ → E4 ✅ → E6-3 ✅ → E7-1 ✅ → E8-1 ✅ → **이번 세션 commit 결정 → E7-2 (실 벤치 — 사용자 확인)**

## Next Action

1. **이번 세션 변경분 commit 결정** — 4 files (`readiness_gate.py`, `test_readiness_gate.py`, `test_orchestrator.py`, `tests/integration/test_synthetic_injection.py`). 사용자 답변 대기 중. 제안 commit message:
   ```
   [si-p4] Stage E E6-3/E7-1/E8-1: kill-switch + synthetic injection + VP4 gate
   ```
2. **E7-2 실 벤치 준비** — `run_readiness.py` 에 `--external-anchor` 플래그 + `evaluate_readiness` 호출에 `external_anchor_enabled=cfg.external_anchor.enabled` 전달. **사용자 확인 후 실행 (API 비용)**.
3. **E7-3 / E8-2 / E8-3** — 벤치 결과 후 진행.
