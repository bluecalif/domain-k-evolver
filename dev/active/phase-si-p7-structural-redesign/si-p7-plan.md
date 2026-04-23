# SI-P7 Structural Redesign — Plan (_CC)

> 작성: 2026-04-21 | 최종 업데이트: 2026-04-23
> 상태: Step B 완료 — **Step V (항목 동작 검증) 착수 전** — Step C (S5a) 는 Step V 결과에 따라 결정
> 단일 진실 소스: **`docs/structural-redesign-tasks_CC.md` v2**
> 전제 plan: `C:\Users\User\.claude\plans\ancient-seeking-sphinx.md`, `C:\Users\User\.claude\plans\ok-curious-naur.md`, `C:\Users\User\.claude\plans\review-project-status-with-elegant-island.md`
> 관련 skill: `silver-structural-redesign`, `silver-e2e-test-layering`, `silver-trial-scaffold`

## 왜

SI-P2 까지 Silver Phase 가 완료됐으나 bench trial (`p6-*`) 에서 구조적 pain-point 4건이 드러났다:

- **R1 target drop** — `_UTILITY_ORDER/_RISK_ORDER` 정렬 + collect budget skip 이 target 우선순위를 무력화. 중요 GU 가 실행되지 않는 현상.
- **R2 integration noop** — `integration_result` 분포가 로그에만 남고 다음 cycle 제어에 반영 안 됨. stagnation 감지 후 교정 루프 부재.
- **R3 adjacent noise** — `_generate_dynamic_gus` 가 entity 의 모든 applicable field 에 대해 `expected_utility=medium, risk_level=convenience` 고정으로 GU 양산. conflict 이력 field 배제 없음.
- **R4 entity 파편화** — 새 concrete entity 유입 경로 부재. virtual `balance-N` entity 가 진짜 entity discovery 를 대체하며 파편화 진행.

이를 구조 설계 **5축 (S1~S5)** + F1~F4 follow-up + Q1~Q14 결정 으로 재구성하고, codex 검토 (`docs/phase-next-refactor-task-review_codex.md`) 를 통합해 baseline v2 로 확정.

## 무엇을

**이번 phase 범위** (baseline v2 §권장 착수 순서 + Step V 삽입, D-190):

```
Step A:  S1 (defer/queue) + S2-T1/T2 (integration_result 제어 입력) — 완료
Step B:  S2-T5~T8 (condition_split 재정의) + S3 (adjacent rule engine) + S4 (virtual 즉시 제거) — 완료
Step V:  Step A/B 전 항목 동작 검증 (V1 snapshot 재파싱 → V2 계측 → V3 ablation → V4 확정)
Step C:  S5a (candidate 적재 + 승격 + 후속 GU, graph 위치 B) — Step V 결과 의존
```

**이번 phase 제외** (다음 phase 후보): S5b 전체 정교화, Remodel 재설계.

## 핵심 확정 (D-181 ~ D-191)

- **D-181** F2 = α (plan query 재작성) + **β (aggressive mode)** — `added_ratio<0.3×3c` trigger 시 entity_discovery mode 전환. target 3-5 확장 / LLM query 즉시 / source_count≥1 임시 적재 / GU 우선순위 상향 / trigger+2c 지속.
- **D-182** S5a = **C3-a 전체** (적재 + 승격 + 후속 GU). codex §6 기각.
- **D-183** graph 위치 = **B** (plan_modify → entity_discovery → plan).
- **D-184** discovery target 신호 = **coverage_map.deficit_score 공유** (C1-a).
- **D-185** candidate 수명 = **last_seen+5c stale / +10c purge** (C2-a).
- **D-186** 유사 후보 = **similarity≥0.85 pre-filter → S5b alias** (C4-a).
- **D-187** 테스트 3-layer (L1/L2/L3) + **mock 금지**. **L3 만 Gate 공식 판정**.
- **D-188** Skill 2종 신설 완료 (`silver-structural-redesign`, `silver-e2e-test-layering`).
- **D-189** (잠정 보류) S5a = critical path blocker. `p7-ab-on` L3 FAIL 분석 기반, 단 **Step V 검증 후 재판정** (balance-* 제거 단독 원인 단정 금지).
- **D-190** Step V 삽입 — L3 gate 결과를 단일 원인으로 단정하지 않고, Step A/B 각 item 의 신호 수준 동작 검증 후 S5a 착수 여부 결정. 현재 ✓10 / ✗1 / ~7 / N/A 2 중 7개 미확증 항목이 계측 부재로 확증 불가하므로 선결.
- **D-191** V3 ablation 설계 — `p7-ab-minus-{axis}` **8c** (cycle 15→8 축소, GU 고갈 재현 충분선), baseline 재사용 (`p7-ab-on` 상한 / `p7-ab-off` 하한), 의심 축 1~2개만 1차 실행. 비용 ~800–1,500 LLM call. 실행 전 사용자 재승인 필수.

## 어떻게

각 Step 의 task 분해는 baseline v2 §S1~§S5b 참조. L1/L2/L3 테스트 전략은 baseline v2 §검증 방식 참조.

**commit prefix**: `[si-p7] Step X.Y: description` 또는 `[si-p7] SN-TN: description`
**branch**: `feature/si-p7-structural-redesign` (축별 분기 시 `feature/si-p7-<축>-<요지>`)
**파일명 규칙**: 본 phase 산출 doc 은 `_CC` suffix 필수 (D-180)

## 산출물 기대

1. **제어 루프 복구** (Step A) — budget 초과 target 이 drop 아닌 defer 로 다음 cycle 소진. integration_result 가 critique/plan 입력으로 주입. `added_ratio<0.3×3c` trigger 작동.
2. **KU/field 품질** (Step B) — condition_split 이 값 구조 차이를 감지. adjacent rule engine 이 낮은 yield rule 약화. conflict field 재생성 0. virtual `balance-N` 생성 0.
3. **항목별 동작 확증** (Step V) — Step A/B 전 17개 task (N/A 2 개 제외 15 개) 의 signal-level 동작 확인. root cause 확정 (D-192 예정). S5a 착수 여부 결정.
4. **entity 유입 경로** (Step C) — concrete entity candidate 가 적재되고 승격되어 skeleton 등록 + 후속 GU 자동 오픈. β mode 가 stagnation 시 동작.

## 검증

- **L1** (각 task 직후): `pytest` green, real snapshot fixture 사용
- **L2** (task 묶음 완료): `scripts/run_readiness.py --cycles 1 --trial-id si-p7-<task-id>-smoke`, real API
- **L3** (축 완료): `bench/silver/japan-travel/p7-<축>-on|off/` A/B. **15c 는 Step B 까지. Step V ablation 은 8c** (D-191). **L3 만 Gate 공식 판정**
- **Step V 전용**:
  - V1: snapshot 재파싱 만 (신규 실행 없음)
  - V2: 1-cycle smoke (real API) 로 신호 발생 확인
  - V3: `p7-ab-minus-{axis}` 8c ablation (baseline 재사용, 사용자 재승인 후)

## 참조

- baseline v2: `docs/structural-redesign-tasks_CC.md`
- plan v2: `C:\Users\User\.claude\plans\ancient-seeking-sphinx.md`
- 최종 plan: `C:\Users\User\.claude\plans\ok-curious-naur.md`
- codex 검토: `docs/phase-next-refactor-task-review_codex.md`
- entity 전략: `docs/entity-acquisition-strategy-draft.md`
- core spec: `docs/core-pipeline-spec-v1.md`
- context: `si-p7-context.md`
- tasks: `si-p7-tasks.md`
- debug history: `si-p7-debug-history.md`
