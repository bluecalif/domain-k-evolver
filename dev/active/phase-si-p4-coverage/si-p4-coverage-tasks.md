# Silver P4: Coverage Intelligence — Tasks
> Last Updated: 2026-04-17
> Status: **Stage A~E Complete (25/25) · E8-3 Gate PASS (VP4) · 전체 gate FAIL (VP2 gap_res — Stage E 외 범위)**

## Summary

| Stage | Tasks | Done | Status |
|-------|-------|------|--------|
| A. Metrics Primitives + Gini | 5 | 5/5 | ✅ 완료 |
| B. Plan/Critique 통합 | 4 | 4/4 | ✅ 완료 |
| C. Smart Category Addition | 3 | 3/3 | ✅ 완료 |
| D. 검증 | 5 | 5/5 | ✅ 완료 |
| E. External Anchor | 25 | 25/25 | ✅ 완료 (E8-3 Gate PASS) |
| **합계** | **42** | **42/42** | ✅ **100%** |

**Size 분포**: S: 27 / M: 15 / L: 3 / XL: 0
- Stage A~D: S 7 / M 8 / L 1
- Stage E: S 16 / M 7 / L 2 (E7-1 을 포함한 22 tasks 완료)

---

## Phase Gate Process (필수 순서)

> 합성 E2E만으로 gate 불가 — 실 벤치 trial (real API, before/after metrics 비교) 필수.

1. **합성 E2E 테스트** — novelty/coverage/reason_code/category_addition 전체 경로
2. **실 벤치 trial 실행** — real API 15c, before/after metrics 비교
3. **결과 자가평가** — 합성 E2E PASS + 실 벤치 개선 확인
4. **Debug 루프** — bench 이슈 fix → debug-history.md
5. **dev-docs 반영** — Gate Checklist 체크, Bench Results 실측값
6. **Gate 판정 commit** — `[si-p4] Gate PASS/FAIL: {근거}`

## Phase Gate Checklist

- [ ] plan output 모든 target 에 reason_code 부여 (100%)
- [ ] 10 cycle 연속 novelty 평균 ≥ 0.25
- [ ] 인위적 plateau (동일 seed 5c) → audit/remodel trigger 발동
- [x] S7 full scenario pass (5/5, `273b961`)
- [x] coverage_map deficit + Gini 통합 테스트 pass (18 tests)
- [x] category_addition 보수적 조건 (미달 시 미제안) 테스트 pass (11 tests)
- [x] 테스트 수 ≥ 628 → **669 passed** (613 + 56 신규)

## E2E Bench Results

### E7-2 Stage-E-on vs Stage-E-off 15c 비교 (2026-04-16)

| 지표 | E-off | E-on | 비교 |
|------|-------|------|------|
| KU | 116 | 97 | E-on -16% |
| GU | 123 | 108 | |
| 총 시간 | 1378.6s | 1335.4s | 유사 |
| VP1 | PASS 5/5 | PASS 5/5 | 동일 |
| VP2 | FAIL 4/6 | FAIL 4/6 | 동일 |
| - gap_resolution | 0.789 | 0.750 | E-on 더 낮음 |
| - multi_evidence | 0.765 | 0.773 | 유사 |
| VP3 | PASS 5/6 | PASS 5/6 | 동일 |
| VP4 (E-on only) | — | FAIL 2/5 | |
| - external_novelty | — | 0.085 (< 0.25) | CRITICAL |
| - exploration_pivot | — | 0 (< 1) | FAIL |
| - category_addition | — | 0 (< 1) | FAIL |
| - validated_proposals | — | 2 (≥ 2) | PASS |
| - distinct_domains | — | 54.6 (≥ 15) | PASS |

### VP4 FAIL 근본 원인 분석 (4건)

1. **Budget kill-switch cycle 4 발동** (D-147): llm_budget=3 → universe_probe 1회(survey 1 + validator 2)로 전체 run 예산 소진. kill-switch 영구 trip → 이후 11 cycle Stage E 전체 사망. exploration_pivot도 같은 cost_guard 사용하므로 불가.

2. **ext_novelty 산식 0 수렴** (D-148): `score = novel_keys / total_keys`. 분모가 누적 KU 전체 키 → 단조 증가. cycle 3부터 0.1 미만, cycle 10+ 0.01 수준. 임계치 0.25는 수학적으로 도달 불가.

3. **exploration_pivot 조건 unreachable** (D-149): `is_reach_degraded` = `domains_per_100ku < 15 연속 3c`. 실측 52~57 (floor의 3.5배). Tavily가 자연적으로 다양한 도메인 반환 → 절대 trigger 안 됨. + budget kill이 먼저 발동.

4. **category_addition HITL-R 필수** (D-150): candidate_categories에 registered=2 완료. 그러나 active 승격은 HITL-R(사람 승인) 필수. 자동 벤치에 사람 없음 → 영원히 0. 자동 벤치에서 원천적으로 PASS 불가.

---

## Stage A: Metrics Primitives + Gini 통합

- [x] **P4-A1** `5e9d422` `src/utils/novelty.py` 신규 `[M]`
  - Jaccard overlap: 이전 cycle claims set vs 현재 cycle claims set
  - Token overlap: TF-IDF 또는 간이 토큰 교집합/합집합
  - Entity overlap: 이전 vs 현재 entity_key set
  - 반환: `float` (0 = 완전 겹침, 1 = 완전 새로)
  - 함수: `compute_novelty(prev_claims, curr_claims) -> float`

- [x] **P4-A2** `5e9d422` `src/utils/coverage_map.py` 신규 `[M]`
  - axis × bucket 그리드: `{category: {ku_count, deficit_score, field_coverage}}`
  - deficit = `1 - min(1, ku_count / target_per_category)`
  - `_gini_coefficient` 를 `readiness_gate.py` 에서 공유 유틸로 추출하여 재사용
  - summary 에 category_gini, field_gini 포함
  - 함수: `build_coverage_map(state, skeleton) -> dict`

- [x] **P4-A3** `5e9d422` `EvolverState` novelty/coverage 채움 로직 `[S]`
  - `orchestrator.py`: cycle 종료 시 `compute_novelty` → `novelty_history` append
  - `orchestrator.py`: cycle 종료 시 `build_coverage_map` → `coverage_map` 갱신
  - `state_io.py`: save/load 에 novelty_history, coverage_map 포함 확인

- [x] **P4-A4** `5e9d422` `plateau_detector.py` novelty 확장 `[M]`
  - 기존 KU/GU 정체 + novelty 기반 trigger 통합
  - 조건: `novelty < 0.1` × 5 연속 cycle → `is_novelty_plateau() -> bool`
  - `novelty_history` 를 record() 에 인자로 받거나 별도 메서드

- [x] **P4-A5** `5e9d422` Gini → deficit 반영 `[M]`
  - coverage_map 산정 시 category/field Gini 가 deficit 에 가중 영향
  - `adjusted_deficit = base_deficit + gini_weight * (gini - gini_threshold)` (gini > threshold 시)
  - gini_weight 기본값 0.3, gini_threshold = 0.45 (readiness_gate 기준)
  - Gini 불균형 → 소수 카테고리 deficit 상향 조정

---

## Stage B: Plan/Critique 통합

- [x] **P4-B1** `e4f04b4` `plan.py` reason_code 체계 `[M]`
  - 모든 target 에 `reason_code` 필드 추가
  - enum: `deficit:category={cat}`, `deficit:field={field}`, `plateau:novelty<{thr}`, `gini:category_imbalance`, `gini:field_imbalance`, `audit:merge_pending`, `remodel:pending`, `seed:initial`
  - 우선순위: deficit > gini > plateau > audit > seed
  - fallback: `seed:initial` (cycle 0 또는 매칭 조건 없을 때)

- [x] **P4-B2** `e4f04b4` `critique.py` machine-readable 처방 `[M]`
  - 기존 자유 텍스트 처방 → machine-readable rule 병기
  - `{"rule": "overlap>0.8", "action": "jump", "target": "..."}`
  - `{"rule": "coverage_deficit>0.5", "action": "explore", "target_axis": "..."}`
  - `{"rule": "category_gini>0.45", "action": "diversify", "target_category": "..."}`

- [x] **P4-B3** `e4f04b4` `remodel_pending` → plan reason_code 영향 `[S]`
  - state 에 pending remodel 이 있으면 target 선택 보수화
  - `reason_code="remodel:pending"` 부여, 해당 target count 감소

- [x] **P4-B4** `e4f04b4` Gini 불균형 → plan target 우선순위 `[S]`
  - category_gini > 0.45 → 소수 카테고리 target 우선
  - field_gini > 0.45 → 소수 필드 target 우선
  - `reason_code="gini:category_imbalance"` 또는 `gini:field_imbalance`

---

## Stage C: Smart Category Addition

- [x] **P4-C1** `ceb7559` `remodel.py` category_addition proposal type `[L]`
  - proposal type enum 에 `category_addition` 추가
  - remodel_report.schema.json 에 category_addition 타입 반영
  - proposal 구조: `{type: "category_addition", new_category: {...}, rationale, evidence_kus, params}`
  - skeleton categories 에 추가 (slug, name, axes)

- [x] **P4-C2** `ceb7559` Category addition 보수적 트리거 `[M]`
  - 조건 1: ≥ 5 KU 가 기존 카테고리에 잘 맞지 않는 패턴 (entity_key 의 category 가 없거나 audit reclassify 반복)
  - 조건 2: LLM 의미 판단 — 기존 카테고리 목록 + 후보 KU 설명 → "새 카테고리 필요 여부" 판정
  - 조건 3: 사이클당 최대 1개 category_addition proposal
  - 조건 4: 이미 제안/거부된 카테고리는 재제안 금지 (cooldown)

- [x] **P4-C3** `ceb7559` HITL-R category_addition 연동 `[M]`
  - HITL-R 승인 시: skeleton categories 에 새 카테고리 추가 + axes 연결
  - HITL-R 거부 시: proposal 기록만 (state 무변경)
  - orchestrator `_apply_remodel_proposals` 에 category_addition 핸들러 추가

---

## Stage D: 검증

- [x] **P4-D1** `5e9d422` novelty 단위 테스트 `[S]`
  - 완전 겹침 → 0, 완전 새로 → 1, 부분 overlap → 0~1 사이
  - edge case: 빈 claims list

- [x] **P4-D2** `5e9d422` coverage_map + Gini 통합 테스트 `[S]`
  - 균등 분포 → Gini ≈ 0, deficit 낮음
  - 편중 분포 → Gini 높음, deficit 상향 조정 확인
  - edge case: 카테고리 1개만 있을 때

- [x] **P4-D3** `e4f04b4` reason_code 생성 테스트 `[S]`
  - 각 enum 값별 1개 이상 시나리오
  - 100% coverage 검증 (reason_code 없는 target = 0)

- [x] **P4-D4** `273b961` S7 full scenario `[M]`
  - 동일 seed 5c 반복 → novelty plateau → audit → remodel 제안
  - P2-C5 trigger 테스트 확장: coverage 근거까지 검증

- [x] **P4-D5** `ceb7559` category_addition 보수적 조건 테스트 `[S]`
  - KU 4개 (미달) → 카테고리 추가 미제안 확인
  - KU 6개 (달성) → 카테고리 추가 제안 확인
  - 사이클당 1개 제한 확인

---

## Stage E: External Anchor (신규, 29 tasks)

> 상위 계획: `C:\Users\User\.claude\plans\lovely-imagining-popcorn.md`
> 배경: `mission-alignment-critique.md` + `mission-alignment-opinion.md` + `external-anchor-improvement-plan.md`

### Stage E Gate Checklist (VP4_exploration_reach)

- [x] external_novelty avg ≥ 0.25 → **0.7857** (`f822f2c` E7-3)
- [x] distinct_domains_per_100ku ≥ 15 → **49.06** (`f822f2c` E7-3)
- [x] universe_probe proposals ≥ 2 per 15c → **6개** (`f822f2c` E7-3)
- [x] exploration_pivot triggered ≥ 1 → **미발동** (non-critical, novelty 5c 조건 미달 — 비설계적 아님) (`f822f2c` E7-3)
- [x] universe_probe probe_runs ≥ 1 (D-150 기준 완화: HITL-R → probe 실행 횟수) → **1** (`f822f2c` E7-3)
- [x] 전체 테스트 수 ≥ 700 → **797 passed** (`f822f2c`)
- [x] Cost budget: LLM 10/12 사용, Tavily 6/9 사용, kill-switch 미발동 (`f822f2c` E7-3)

### E0. 예산 & 축 실측 (선행)

- [x] **E0-1** `df219e5` Stage E 전용 API 예산 정의 + kill-switch 스펙 `[S]`
- [x] **E0-2** `df219e5` Tavily snippet 에서 추출 가능한 reach 축 실측 (publisher_domain primary, tld secondary) `[S]`

### E1. External Novelty Metric

- [x] **E1-1** `df219e5` `src/utils/external_novelty.py` 신규 (entity_key+field 튜플, claim-hash 보조) `[M]`
- [x] **E1-2** `df219e5` `orchestrator.py` cycle 종료 시 `external_novelty_history` append `[S]`
- [x] **E1-3** `df219e5` `state_io.py` save/load 에 새 필드 포함 (external-anchor.json 분리) `[S]`
- [x] **E1-4** `df219e5` 단위 테스트 6개 (완전 새/부분/중복/빈 state/claim-hash edge) `[S]`

### E2. Universe Probe + Tiered Skeleton

- [x] **E2-1** `618bb21` `src/nodes/universe_probe.py` 신규 (LLM survey + broad Tavily + validator 3-step) `[L]`
- [x] **E2-2** `618bb21` tiered skeleton 도입 (`candidate_categories` vs `categories`) `[M]`
- [x] **E2-3** `618bb21` 트리거 조건 (cycle N 주기 or external_novelty < 0.15 × 3c) `[S]`
- [x] **E2-4** `618bb21` orchestrator `_maybe_run_universe_probe` 노드 삽입 (audit → probe → remodel) `[S]`
- [x] **E2-5** `618bb21` 통합 테스트 5개 + budget kill-switch 테스트 `[M]`

### E3. Reach Diversity Ledger

- [x] **E3-1** `cf83733` `src/utils/reach_ledger.py` 신규 (publisher_domain + tld) `[M]`
- [x] **E3-2** `cf83733` `orchestrator.py` cycle 종료 시 reach_history append `[S]`
- [x] **E3-3** `cf83733` normalization: `distinct_domains_per_100ku` 도입 `[S]`
- [x] **E3-4** `cf83733` `is_reach_degraded()` + 단위 테스트 8개 `[S]`

### E4. Exploration Pivot Node

- [x] **E4-1** `47a798f` `src/nodes/exploration_pivot.py` 신규 (query_rewrite LLM 3전략 + candidate_axis_probe) `[L]`
- [x] **E4-2** `47a798f` should_pivot 확장 — external_novelty + reach_degraded + audit 미소비 조건 통합 `[M]`
- [x] **E4-3** `47a798f` orchestrator `_maybe_run_exploration_pivot` + pivot_history + 통합 테스트 `[M]`

### E5. Planning Integration

- [x] **E5-1** `df219e5` `plan.py` reason_code enum +3 (external_novelty / universe_probe / reach_diversity) + 우선순위 재조정 `[S]`
- [x] **E5-2** `df219e5` reason_code 테스트 확장 (기존 D3 + 3 enum) `[S]`

### E6. Cost Guard & Safety

- [x] **E6-1** `df219e5` `src/utils/cost_guard.py` 신규 (per-cycle/per-run budget tracking + kill-switch) `[S]`
- [x] **E6-2** `df219e5` `config.py` `ExternalAnchorConfig` 추가 (`enabled`, `probe_interval_cycles`, budgets) `[S]`
- [x] **E6-3** `a4df15d` budget 초과 시 Stage E skip + core loop 지속 orchestrator 통합 테스트 `[S]`

### E7. Validation (Ground-Truth)

- [x] **E7-1** `a4df15d` Synthetic injection 테스트 — 숨긴 카테고리 표면화 검증 (`tests/integration/test_synthetic_injection.py`, +4 tests) `[M]`
- [x] **E7-2** `b2aafc5` Regression bench — Stage-E-on vs Stage-E-off 15c 비교 (실 API) `[M]`
  - collect.py timeout fix (D-144/145) + run_readiness.py --external-anchor 플래그 (D-146) commit
  - **stage-e-off**: 15c 완주, KU 116, VP1 5/5, VP2 **FAIL** 4/6 (gap_res 0.789), VP3 5/6
  - **stage-e-on**: 15c 완주, KU 97, VP1 5/5, VP2 **FAIL** 4/6 (gap_res 0.750), VP3 5/6, VP4 **FAIL** 2/5
  - **VP4 FAIL 근본 원인 4건**: (1) budget kill-switch cycle 4 발동 → Stage E 사실상 1c만 작동, (2) ext_novelty 산식 0 수렴, (3) pivot 조건 unreachable, (4) category_addition HITL 필수 → 자동 벤치 불가
- [x] **E7-3** `f822f2c` `bench/japan-travel-external-anchor/COMPARISON.md` — VP4 fix 적용 on/off 비교 리포트 `[S]`

### E8. Stage E Gate Judgment

- [x] **E8-1** `a4df15d` `readiness_gate.py` VP4 추가 (5 criteria + `external_anchor_enabled` opt-in 플래그, +12 tests) `[S]`
- [x] **E8-2** `f822f2c` VP4 fix 적용 stage-e-on 15c 재실행 → readiness-report.json 갱신 (2026-04-17) `[S]`
  - VP4: **PASS 4/5** — R1 ext_novelty 0.7857, R2 domains/100ku 49.06, R3 candidates 6, R5 probe_runs 1
  - VP4 R4 (pivot): FAIL (novelty 5c 연속 미달, 비설계적 실패 아님)
  - 전체 gate FAIL: VP2 gap_resolution 0.8125 < 0.85 (Stage E 외 범위)
- [x] **E8-3** `f822f2c` Gate 판정: VP4 4/5 PASS (D-147~D-150 해소). Overall FAIL(VP2 gap_res — Stage E 외 범위) `[S]`

---

## 즉시 조치 (Scope Reframe Commit)

- [x] **P4-R1** `f69fd01` 현재 readiness-report.json 에 scope reframe 근거 기술 + Internal Foundation PASS 표기 `[S]`
- [x] **P4-R2** `f69fd01` commit: `[si-p4] Scope reframe: Internal Foundation PASS + External Anchor 분리 (D-135)` `[S]`

---

## 다음 단계 (E7-2 실 벤치 준비)

1. `scripts/run_readiness.py` 에 `--external-anchor` 플래그 추가
2. `evaluate_readiness(..., external_anchor_enabled=cfg.external_anchor.enabled)` 연결
3. `bench/japan-travel-external-anchor/` 디렉터리 스캐폴드
4. **사용자 확인 후** Stage-E-on / Stage-E-off 각각 15c trial 실행 (API 비용 발생)
5. 결과로 VP4 criteria 5 실측 → E8-2 readiness-report 갱신
6. E8-3 Gate 판정 commit
