# Session Compact

> Generated: 2026-04-15
> Source: Conversation compaction via /compact-and-go

## Goal

SI-P4 Coverage Intelligence — Stage E (External Anchor) 순차 구현.
이번 세션: **Task #8 (E2) 착수** — E2-1 skeleton tiered ✅ + E2-2 universe_probe LLM survey ✅.
다음 차례: E2-3 (broad Tavily probe) 또는 E2-4 (evidence validator).

계획: `C:\Users\User\.claude\plans\lovely-imagining-popcorn.md` (29-task 4-계층 스펙트럼).
Phase tasks: `dev/active/phase-si-p4-coverage/si-p4-coverage-tasks.md`.

## Completed

### 누적 (이전 세션까지)
- [x] Stage A~D 완료, Internal Foundation Gate PASS (D-135)
- [x] Task #1~#7: Scope reframe / cost_guard / reach-axes survey / external_novelty / state 영속화 / plan reason_code
- [x] **Checkpoint commit `df219e5`**: `[si-p4] Stage E E0-2/E1/E5: external_novelty + state 영속화 + reason_code 통합` (12 files, 690 tests)

### 이번 세션 (Task #8 진행)
- [x] **E2-1 skeleton tiered** — `src/utils/skeleton_tiers.py` 신규
  - `TIER_ACTIVE` / `TIER_CANDIDATE` 상수
  - `get_active_categories / get_candidate_categories / get_active_category_slugs / get_candidate_category_slugs`
  - `find_category(slug) → (tier, entry) | None`
  - `add_candidate_category` — schema 검증 (`slug, name, rationale, type, proposed_at_cycle`), slug collision 검사 (active/candidate)
  - `promote_candidate` — HITL-R 승인 경로 (candidate → active)
  - `reject_candidate`
  - **Candidate entry schema**: `{slug, name, rationale, expected_source, type: NEW_CATEGORY|NEW_AXIS, proposed_at_cycle, status: pending_validation|validated|promoted|rejected, evidence}`
  - **불변 준수 (D-139)**: 기존 `skeleton.get("categories", [])` 호출 경로 변경 없음 — candidate 는 별도 field 로 분리
- [x] **E2-1 tests** — `tests/test_utils/test_skeleton_tiers.py` (10 tests, all PASS)
- [x] **E2-2 universe_probe LLM survey** — `src/nodes/universe_probe.py` 신규
  - `run_universe_probe(state, llm, config, cost_guard, cycle=None) → dict`
  - Returns `{status: ok|skipped|error, reason, proposals, rejected, cycle}`
  - `UNIVERSE_PROBE_PROMPT` 상수 (plan Prompt 2 verbatim)
  - Skip 조건: `external_anchor.enabled=False` or `cost_guard.allow("universe_probe", llm=1)=False`
  - Filter: missing_slug / invalid_type / collision_active / collision_candidate / duplicate_in_batch / not_a_dict
  - Accepted proposal 에 `proposed_at_cycle`, `status="pending_validation"`, `evidence=None` 자동 주입
  - `_ku_count_by_category`, `_top_entities`, `_build_prompt`, `_validate_and_filter_proposals` 보조
  - LLM 호출 실패 시 `status="error"` + `cost_guard.record` (실 호출 시도되었으므로)
- [x] **E2-2 tests** — `tests/test_nodes/test_universe_probe.py` (12 tests, all PASS)
  - disabled/budget_exceeded skip, happy path, collision (active/candidate), invalid_type, duplicate_in_batch, LLM error, malformed JSON, proposals_not_list, slug 정규화 (lowercase+strip), non-dict filter

### 테스트 수
- Pre-session: 690 passed
- Post-session (skeleton_tiers 10 + universe_probe 12 = +22): **712 passed 예상**
  (확인 필요: 마지막 full suite 실행 `python -m pytest` 는 사용자가 interrupt 함)

## Current State

- Branch: `main`. 마지막 commit `df219e5` (Stage E E0-2/E1/E5).
- **Uncommitted**: 이번 세션 변경 (E2-1 + E2-2) 아직 commit 안 함.
- Stage E 진행: E0-1 ✅ E0-2 ✅ E1 ✅ E5 ✅ **E2-1 ✅ E2-2 ✅** → 다음 E2-3 or E2-4.

### Changed Files (이번 세션, uncommitted)

- `src/utils/skeleton_tiers.py` (신규) — tiered skeleton helpers
- `tests/test_utils/test_skeleton_tiers.py` (신규) — 10 tests
- `src/nodes/universe_probe.py` (신규) — LLM survey 노드
- `tests/test_nodes/test_universe_probe.py` (신규) — 12 tests

### Untracked (이전 세션부터 남은)
- `bash.exe.stackdump` — stray 파일 (무시)

## Remaining / TODO

### 즉시 다음 (Task #8 = E2 계속)
session-compact 내부 번호 기준:
- [x] E2-1 skeleton tiered (candidate_categories 필드)
- [x] E2-2 universe_probe 노드 (LLM survey)
- [ ] **E2-3 broad Tavily probe** (budget guard) — 각 proposal 에 대해 Tavily query 발행, evidence snippets 수집
- [ ] **E2-4 evidence validator + candidate_promotion** — LLM validator (Prompt 3), 통과 proposal 을 `add_candidate_category` 로 skeleton 에 등록 (HITL-R 대기 상태, D-139)
- [ ] **E2-5 통합 테스트** + budget kill-switch 테스트

### Phase tasks 파일 기준 매핑 (si-p4-coverage-tasks.md)
- [ ] E2-1 universe_probe.py (LLM + Tavily + validator 3-step) `[L]` — 부분 진행 중 (LLM survey 부분만 완료)
- [ ] E2-2 tiered skeleton — **완료** (session-compact 번호로는 E2-1)
- [ ] E2-3 트리거 조건 (cycle N 주기 or external_novelty<0.15×3c)
- [ ] E2-4 graph.py universe_probe 노드 삽입
- [ ] E2-5 통합 테스트 5개 + budget kill-switch

### Stage E 잔여
- E3 reach_ledger (4 tasks)
- E4 exploration_pivot (3 tasks)
- E6 cost_guard wire-up (3 tasks)
- E7 validation (3 tasks)
- E8 VP4 gate + 판정 commit (3 tasks)

## Key Decisions

- **D-139 재확인**: candidate_categories 는 HITL-R 승인 전 active 아님. 기존 `skeleton.get("categories", [])` 경로는 불변. promotion 은 `promote_candidate` 만 경유.
- **universe_probe 책임 분리**: E2-2 (이 세션) = **survey 생성만**. Tavily probe / validator / skeleton 등록은 E2-3/E2-4 의 책임. 현재 노드는 proposal 을 생성하되 skeleton 에 쓰지 않음 — caller 가 이후 단계에서 `add_candidate_category` 호출.
- **cost_guard 기록 규칙**: LLM 호출을 *시도* 하면 `record` (성공/실패 무관). `allow=False` 면 호출 안 하므로 record 도 안 함.
- **Slug 정규화**: `strip().lower()`. LLM 이 공백/대문자로 반환해도 일관된 키로 저장.
- **Rejection reason 명시**: `_reject_reason` 필드로 디버깅/로그 추적 가능 (`collision_active`, `collision_candidate`, `duplicate_in_batch`, `invalid_type:{v}`, `missing_slug`, `not_a_dict`).

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 핵심 참조 파일

- 상위 계획: `C:\Users\User\.claude\plans\lovely-imagining-popcorn.md`
  - Prompt 2 (universe_probe): 라인 306-341
  - Prompt 3 (evidence validator, E2-3/E2-4 용): 라인 343-363
- Phase tasks: `dev/active/phase-si-p4-coverage/si-p4-coverage-tasks.md` (E2 체크리스트 라인 182-188)
- Phase context: `dev/active/phase-si-p4-coverage/si-p4-coverage-context.md`
- Reach axes 조사: `dev/active/phase-si-p4-coverage/reach-axes-survey.md`

### 코드 베이스 핵심 (Stage E)

- `src/utils/cost_guard.py` — `CostGuard.allow(op, llm=, tavily=) → bool`, `record(op, llm=, tavily=)`
- `src/utils/external_novelty.py` — `compute_external_novelty`, `extract_observation_keys`
- `src/utils/skeleton_tiers.py` ✨ — active/candidate 분리 helpers
- `src/nodes/universe_probe.py` ✨ — LLM survey (proposal 생성만)
- `src/config.py:ExternalAnchorConfig` — `enabled`, `probe_interval_cycles`, `llm_budget_per_run`, `tavily_budget_per_run`, `candidate_promotion_min_confidence`
- `src/utils/llm_parse.py:extract_json` — markdown fence 제거 + JSON 파싱

### 다음 (E2-3) 구현 가이드

1. `src/adapters/search_adapter.py` — 이미 Tavily client 존재. `search(query) → [{url, title, snippet}]` 형태 재사용.
2. 각 accepted proposal 마다:
   - `cost_guard.allow("universe_probe_validator", tavily=1)` 체크
   - Query 생성: proposal.name + domain + "overview" 정도
   - Tavily 호출, top-5 snippets 수집
   - Proposal 에 `evidence.snippets = [...]` 주입
3. Tavily 예산 초과 시 해당 proposal skip (전체 probe 는 유지).
4. E2-4 (validator) 에서 LLM call 2회째로 snippets 를 `{exists, confidence, source_diversity}` 검증.

### 제약/주의

- API 비용 발생 작업 신중 (memory rule). 실 벤치는 Stage E 전체 완성 후.
- Phase Gate = 합성 E2E + 실 벤치 trial 비교 필수.
- VP4 기준: external_novelty avg ≥ 0.25, distinct_domains_per_100ku ≥ 15, universe_probe proposals ≥ 2/15c, exploration_pivot ≥ 1, category_addition via universe_probe ≥ 1.
- 전체 테스트 목표 ≥ 700 (현재 700+ 이미 달성, 정확한 수치는 full suite 재실행 필요).

### 작업 흐름

E0-1 ✅ → E0-2 ✅ → E1 ✅ → E5 ✅ → **E2-1 ✅ E2-2 ✅** → **E2-3 (다음)** → E2-4 → E2-5 → E3 → E4 → E6 → E7 → E8

## Next Action

**우선: 사용자 interrupt 로 full-suite 재확인 필요.**

1. `python -m pytest 2>&1 | tail -5` 로 regression 없는지 검증 (690 → 712 예상).
2. 그 후 사용자 결정:
   - **Option A**: E2-1 + E2-2 checkpoint commit (권장 — E2 submodule 단위 커밋)
     - 메시지: `[si-p4] Stage E E2-1/E2-2: tiered skeleton + universe_probe LLM survey`
     - 스테이징: 4 신규 파일
   - **Option B**: E2-3 (Tavily probe) 계속 진행 후 bundle commit
3. E2-3 착수 시: `src/adapters/search_adapter.py` 확인 → `universe_probe.py` 에 `_gather_evidence(proposals, search_client, cost_guard)` 함수 추가 → 기존 `run_universe_probe` 확장 (survey + evidence 단계 모두 실행) 또는 별도 함수 분리.

사용자 마지막 지시: `/compact-and-go` — 이 파일 저장 후 `/clear` 대기.
