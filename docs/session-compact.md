# Session Compact

> Generated: 2026-04-15
> Source: Conversation compaction via /compact-and-go

## Goal

SI-P4 Coverage Intelligence — Stage E (External Anchor) 순차 구현.
이번 세션에서 E0-2 ~ E5 완료. 다음 차례는 E2 (universe_probe).

계획: `C:\Users\User\.claude\plans\lovely-imagining-popcorn.md` (29-task 4-계층 스펙트럼).

## Completed

### 누적 (이전 세션까지)
- [x] Stage A~D 완료, Internal Foundation Gate PASS (D-135)
- [x] dev-docs 동기화 완료, mission-alignment critique + external-anchor plan
- [x] **Task #1 (P4-R)**: Scope reframe commit `f69fd01` + bench `ee67104`
- [x] **Task #2 (E0-1)**: Stage E budget + kill-switch (`ExternalAnchorConfig`, `cost_guard.py`, 8 tests)

### 이번 세션
- [x] **Task #3 (E0-2)**: Reach axes 실측 조사 → `dev/active/phase-si-p4-coverage/reach-axes-survey.md`
  - 채택: `publisher_domain` (primary, 100% 추출 via `provenance.domain`), `tld` (secondary proxy)
  - 이월: `published_date` (E3 에서 Tavily adapter 확장 후 실측)
  - 기각: `language` (dep 비용 대비 diversity 낮음), `author` (fetch 재도입 D-121 위반)
- [x] **Task #4 (E1-1)**: `src/utils/external_novelty.py` 신규
  - `compute_external_novelty(items, history) → (score, new_keys)`
  - `extract_observation_keys`, `claim_value_hash` 보조 함수
  - granularity = `(entity_key, field)` (D-138)
- [x] **Task #5 (E1-2/3)**: orchestrator + state_io 통합
  - `state.py`: `external_novelty_history: list[float]`, `external_observation_keys: list[str]` 필드 추가
  - `state_io.py`: `external-anchor.json` optional 파일 load/save + snapshot_state/phase 포함
  - `orchestrator.py`: `_update_novelty_and_coverage` 에서 external_novelty 계산/누적/로그
  - **게이팅 없음** (tracking cost 0, Stage E disabled 여도 before/after 비교 가능)
- [x] **Task #6 (E1-4)**: `tests/test_utils/test_external_novelty.py` — 6 tests (완전새/중복/부분/빈/필드누락/해시안정성)
- [x] **Task #7 (E5-1/2)**: `plan.py` reason_code +3 + 우선순위 재조정
  - 신규: `external_novelty:stagnation(avg=...)`, `universe_probe:candidate`, `reach_diversity:degraded`
  - 임계치: `EXTERNAL_NOVELTY_STAGNATION_THRESHOLD=0.1`, `_WINDOW=5`
  - 우선순위: **external_novelty > universe_probe > reach_diversity > deficit > gini > plateau > remodel > audit > seed**
  - 테스트 +7개 (stagnation 발동/비발동, override, 짧은 history 등)

## Current State

- Branch: `main`. Stage E 구현: E0-1 ✅ E0-2 ✅ E1 ✅ E5 ✅. 다음은 **E2 (universe_probe)**.
- 테스트 수: **690 passed, 3 skipped** (677 → +13: cost_guard 8 포함 누적)
- Internal Foundation Gate PASS. VP4 는 Stage E 완료 후 판정.
- **Uncommitted 상태**. 이번 세션 커밋 안 함.

### Changed Files (이번 세션)

- `src/utils/external_novelty.py` (신규) — compute_external_novelty, extract_observation_keys, claim_value_hash
- `tests/test_utils/test_external_novelty.py` (신규) — 6 tests
- `src/state.py` — EvolverState 에 `external_novelty_history`, `external_observation_keys` 필드
- `src/utils/state_io.py` — `external-anchor.json` (load/save/snapshot_state/snapshot_phase)
- `src/orchestrator.py` — `compute_external_novelty` import + `_update_novelty_and_coverage` 안에 external tracking + 로그 `ext_novelty=%.3f`
- `src/nodes/plan.py` — `_assign_reason_code` 에 external_novelty/universe_probe/reach_diversity 블록 (최상위 우선순위), `plan_node` 가 external_novelty_history 전달, 임계치 상수 추가
- `tests/test_nodes/test_plan_reason_code.py` — `TestExternalAnchorReasonCodes` 클래스 +7 tests
- `dev/active/phase-si-p4-coverage/reach-axes-survey.md` (신규)
- (이전 세션) `src/config.py`, `src/utils/cost_guard.py`, `tests/test_utils/test_cost_guard.py`

## Remaining / TODO

### 즉시 다음
- [ ] **Checkpoint commit** — E0-2 / E1 / E5 번들 (또는 E2 완료 후 한 번에 할지 사용자 결정)
- [ ] **Task #8 (E2-1~5)**: `src/nodes/universe_probe.py` 신규 + skeleton tiered (`candidate_categories` 필드 도입) + LLM survey + broad Tavily probe + HITL-R 연동 → category_addition 선제형 경로
  - E2-1 skeleton tiered 구조 (candidate_categories 필드)
  - E2-2 universe_probe 노드 (LLM survey)
  - E2-3 broad Tavily probe (budget guard)
  - E2-4 evidence → candidate_promotion (HITL-R 승인 전 active 아님, D-139)
  - E2-5 단위 테스트

### Stage E 잔여 (Task 미생성)
- E3 reach_ledger (4 tasks) — publisher_domain/tld 축 누적, `distinct_domains_per_100ku` API
- E4 exploration_pivot (3 tasks) — LLM query rewriter, plateau_detector 확장, graph edge
- E6 cost_guard wire-up (3 tasks) — orchestrator/노드에 guard.allow/record 삽입
- E7 validation (3 tasks) — synthetic injection + regression bench
- E8 VP4 gate 추가 + 판정 commit (3 tasks)

## Key Decisions

- **D-138 재확인**: external_novelty granularity = `(entity_key, field)` 튜플. `claim_value_hash` 는 향후 disambiguation 보조 (v1 score 에 미사용).
- **E1 tracking 항상 on**: `ExternalAnchorConfig.enabled` 게이팅 없이 external_novelty tracking 수행. 이유: cost 0, before/after 비교용 데이터 수집. 게이팅은 *actions* (probe/pivot) 에만 적용.
- **State 영속화**: 별도 파일 `external-anchor.json = {novelty_history, observation_keys}` 로 분리 (metrics.json 오염 회피, migration-safe).
- **관찰 키 저장 형식**: `sorted(set(prev_keys) | new_keys)` 결정론적, `"entity_key|field"` 스트링.
- **Reason code 우선순위**: external_novelty 계열이 deficit/gini 보다 *위*. 이유: cycle-level 외부 신호가 category-level 국소 신호보다 근본 원인에 가까움.
- **universe_probe/reach_diversity 라우팅**: GU 의 `trigger_source` 문자열 match 로 판정. E2/E3 가 populate.

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 핵심 참조 파일

- 상위 계획: `C:\Users\User\.claude\plans\lovely-imagining-popcorn.md` (29 tasks, 4-계층 스펙트럼, 다이어그램, 프롬프트 템플릿)
- Phase tasks: `dev/active/phase-si-p4-coverage/si-p4-coverage-tasks.md` (E0-E8 체크리스트)
- Phase context: `dev/active/phase-si-p4-coverage/si-p4-coverage-context.md` (D-135~139)
- Reach axes 조사: `dev/active/phase-si-p4-coverage/reach-axes-survey.md` (E3 에서 참조)

### 코드 베이스 핵심

- 기 구현 (Stage E): `src/utils/cost_guard.py`, `src/utils/external_novelty.py`
- 기존 재사용: `src/nodes/remodel.py:230-282` (gap_rule 로직, 수정 금지), `src/orchestrator.py:505-546` (gap_rule 적용)
- 내부 novelty (유지): `src/utils/novelty.py`
- 다음 신규: `src/utils/reach_ledger.py` (E3), `src/nodes/universe_probe.py` (E2), `src/nodes/exploration_pivot.py` (E4)
- Plan reason_code: `src/nodes/plan.py:_assign_reason_code` (external 계열 최상위)
- Tavily 응답 구조: `src/adapters/search_adapter.py:73-78` 는 `{url, title, snippet}` 만 유지. E3 에서 `published_date` 보존 옵션 검토.

### 제약/주의

- API 비용 발생 작업 신중 (memory rule). 실 벤치는 Stage E 전체 완성 후 한 번에.
- Phase Gate = 합성 E2E + 실 벤치 trial 비교 필수.
- VP4_exploration_reach 기준: external_novelty avg ≥ 0.25, distinct_domains_per_100ku ≥ 15, universe_probe proposals ≥ 2/15c, exploration_pivot triggered ≥ 1, category_addition via universe_probe ≥ 1.
- 전체 테스트 ≥ 700 목표 (현재 690).
- Legacy bench `bench/japan-travel/` read-only (D-123).

### 작업 흐름

E0-1 ✅ → E0-2 ✅ → E1 ✅ → **E5 ✅** → **E2 (다음)** → E3 → E4 → E6 → E7 → E8

## Next Action

**우선: 사용자에게 checkpoint commit 여부 확인.** 이번 세션 변경이 누적 상당 (8개 파일, 13 신규 테스트) — 사용자 반응 "ok/go" 흐름상 아직 commit 승인 없음.

사용자가 commit 원하면:
1. 메시지: `[si-p4] Stage E E0-2/E1/E5: external_novelty + state 영속화 + reason_code 통합`
2. 스테이징: 위 "Changed Files" 8개 + `docs/session-compact.md`

사용자가 E2 계속 원하면 **Task #8 (E2-1 skeleton tiered)** 시작:
1. `domain-skeleton.json` schema 에 `candidate_categories` 필드 추가 (tier: "active" vs "candidate")
2. `src/nodes/universe_probe.py` 신규 — LLM survey prompt 는 plan 파일 라인 ~280-295 참조
3. D-139: candidate 는 HITL-R 승인 전 active 아님
4. 단위 테스트 ≥5 추가 목표

commit 승인 없이 E2 진행 시, E2 완료 후 한 번에 bundle commit 하는 것을 제안.
