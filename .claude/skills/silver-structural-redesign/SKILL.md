---
name: silver-structural-redesign
description: Domain-K-Evolver Silver SI-P7 구조 설계 5축 (S1 Target/Collect, S2 KU 병합 + condition_split, S3 adjacent rule engine, S4 category_balance, S5a Entity Discovery Node, S5b Entity 정규화·통합) 구현 가이드. codex 검토 통합 (defer/queue, rule engine, integration_result 제어 입력화), Q1~Q14 + D-181~D-188 결정, F1~F4 handling, `_CC` suffix 규칙을 단일 진실 소스 (`docs/structural-redesign-tasks_CC.md` v2) 와 정렬한다. "SI-P7", "structural redesign", "S1~S5", "S5a", "S5b", "entity discovery node", "entity_candidates", "condition_split", "field_adjacency", "adjacent rule engine", "integration_result 제어 입력", "deferred_targets", "defer/queue", "rule yield tracker", "aggressive mode", "β mode", "virtual entity 제거", "alias pre-filter", "_CC suffix", "si-p7-*" 같은 요청이 나오면 반드시 사용한다. SI-P7 외 Silver Phase (P0~P6) 나 Bronze 리팩터링에는 사용하지 않는다.
---

# Silver SI-P7 Structural Redesign

## 목적

SI-P2 까지 Silver Phase 완료 이후 드러난 구조적 pain-point 4건 (R1 target drop, R2 integration noop, R3 adjacent noise, R4 entity 파편화) 을 해결하기 위한 **5축 (S1~S5)** 구조 설계를 실제 코드로 옮길 때 쓰는 가이드.

단일 진실 소스: **`docs/structural-redesign-tasks_CC.md` v2** (이하 baseline v2).
전제 plan: `C:\Users\User\.claude\plans\ancient-seeking-sphinx.md` (plan v2 Part A/B/C/D/E), `C:\Users\User\.claude\plans\ok-curious-naur.md` (최종 plan).
codex 검토: `docs/phase-next-refactor-task-review_codex.md`.

이 skill 은 baseline v2 의 규칙을 실행 가능한 단계로 풀어낸다. **baseline v2 와 충돌 시 baseline v2 가 옳다.**

## 언제 쓰는가

- SI-P7 5축 (S1~S5) 의 구현 task 시작 / 디버그 / PR 검토 시
- `src/nodes/{plan,collect,integrate,critique,entity_discovery,entity_reconcile}.py` 수정 시
- `src/state.py` 의 `deferred_targets` / `recent_conflict_fields` / `entity_candidates` / `entity_fragmentation_signals` 건드릴 때
- `bench/japan-travel/state/domain-skeleton.json` 의 `condition_axes` / `field_adjacency` / `entity_frame` 작업 시
- dev-docs (`dev/active/phase-si-p7-structural-redesign/`, `_CC` suffix) 작성 / 갱신 시
- trial_id `si-p7-*` 또는 `p7-<축>-on|off` 로 벤치 trial 구성 시
- Decision D-181~D-188 중 하나를 언급하거나 β aggressive mode 설정 만질 때

## 언제 쓰지 않는가

- 이전 Silver Phase (SI-P0~P3R, SI-P2) 의 구현/디버그 — 해당 phase dev-docs 가 우선
- Bronze (`bench/japan-travel/` read-only) 레거시 작업
- SI-P7 외 phase 의 Readiness Gate 판정 — `silver-phase-gate-check` 가 담당
- 벤치 trial 스캐폴딩 자체 — `silver-trial-scaffold` 가 담당

---

## 5축 개요

| 축 | 주제 | 주 변경 |
|---|---|---|
| **S1** | Target / Collect 자유화 (**defer/queue**) | `target_count` 상한 제거, utility skip 제거, budget 초과 시 **drop 대신 defer**. `state.deferred_targets` 신설. 다음 cycle 우선 소진. |
| **S2** | KU 병합 피드백 + condition_split 강화 | `integration_result` 분포를 **plan_modify/critique 입력으로 승격**. condition_split 을 **값 구조/axis_tags 차이** 로 재정의. plan reason code 추가. F2 = α+β(aggressive mode) 구현. |
| **S3** | adjacent **rule engine** | `field_adjacency = {source_field: [next_fields]}` + category override. `recent_conflict_fields` blocklist. **rule yield tracker** — 낮은 yield rule 약화/중지. |
| **S4** | category_balance 정교화 | virtual `balance-N` entity **즉시 제거** (과도기 없음). `coverage_map.deficit_score` 기반 동적 하한. 실제 validated entity 만 대상. |
| **S5a** | **Entity Discovery Node** (매 cycle 기본 노드) | `state.entity_candidates` 신설 + skeleton `entity_frame`. rule-first query + LLM 보강. **similarity≥0.85 pre-filter** → S5b alias 경로 분기. candidate 수명 `last_seen+5c/+10c`. 승격 `source_count≥2 AND distinct_domain≥2` → skeleton 등록 + 후속 GU 자동. graph 위치 **B** (`plan_modify → entity_discovery → plan`). |
| **S5b** | Entity 정규화·통합 | similarity 기반 auto-alias (≥0.90), auto-merge (≥0.95 AND gap 조건). duplicate KU → `entity_fragmentation_signals` 누적. `entity_fragmentation_report` metric. |

---

## 본 Phase 확정 결정 (D-181 ~ D-188)

| ID | 내용 | 핵심 의미 |
|---|---|---|
| **D-181** | F2 = **α (plan query 재작성) + β (aggressive mode)** | β 는 D-173 "매 cycle 실행" 과 구별되는 **mode 전환**. trigger cycle + 다음 2c 지속. target 수 3-5 확장, LLM query 즉시 활성, source_count≥1 임시 적재, GU 우선순위 상향. |
| **D-182** | S5a 범위 = **C3-a 전체** | 적재 + 승격 + 후속 GU 자동 오픈 모두 포함. codex §6 (승격 다음 phase) 기각. |
| **D-183** | graph 위치 = **B** | `plan_modify → entity_discovery → plan`. |
| **D-184** | discovery target 신호 = **C1-a** | `coverage_map.deficit_score` 를 S4 와 공유. |
| **D-185** | candidate 수명 = **C2-a** | `last_seen+5c → stale`, `+10c → purge`, 재등장 시 `last_seen` 갱신. |
| **D-186** | 유사 후보 pre-filter = **C4-a** | `entity_resolver.similarity≥0.85` 이면 candidate 차단 → S5b alias 경로. |
| **D-187** | 테스트 3-layer + mock 금지 | L1 (단위) / L2 (single-cycle e2e) / L3 (15c A/B). fixture real snapshot 만. **L3 만 Gate 공식 판정**. |
| **D-188** | Skill 2종 신설 | 본 skill + `silver-e2e-test-layering`. |

---

## β aggressive mode (D-181) — 상세 파라미터

| 설정 | 정상 cycle | **β aggressive** |
|---|---|---|
| discovery target 수 | 1-2개 (deficit 상위) | **3-5개** |
| query 생성 | rule-first template | **LLM-assisted 즉시 활성** |
| candidate 적재 임계 | source_count≥2 AND distinct_domain≥2 (승격) | **source_count≥1 임시 적재** (승격 표준 불변) |
| 후속 GU 우선순위 | 기본 | **상향** (다음 plan 우선 소진) |
| 지속 기간 | N/A | trigger cycle + **다음 2c** |

Trigger: `added_ratio<0.3×3c` 감지 → critique rx → entity_discovery 파라미터 override.

---

## 권장 착수 순서 (baseline v2)

```
Step A: S1 (defer/queue) + S2-T1/T2 (integration_result 제어 입력)
        제어 루프 복구. 이후 모든 축이 이 루프에 의존.

Step B: S2-T5~T8 (condition_split 재정의) + S3 (adjacent rule engine) + S4 (virtual 즉시 제거)
        KU/field 품질 개선.

Step C: S5a (candidate 적재 + 승격 + 후속 GU, graph 위치 B)
        entity 유입 경로 개통. β mode 측정 가능 시점.

Step D (다음 phase 후보): S5b 전체 정교화
```

---

## F1~F4 handling

| # | 주제 | 상태 | 처리 시점 |
|---|---|---|---|
| F1 | S1 budget 완전 제거 | **구현 중 결정** | S1-T6 smoke 5c 결과 후 |
| F2 | S2 aggressive feedback | **확정 (D-181)** α + β | Step A/B 구현 시 반영 |
| F3 | S5a graph 위치 | **확정 (D-183)** B | Step C 구현 시 반영 |
| F4 | S5b auto-alias/merge 임계치 | **구현 중 결정** | 초기값 0.85 pre-filter / 0.90 alias / 0.95 merge, L3 tuning |

---

## 파일 네이밍 (D-180)

- SI-P7 설계 산출 task doc 은 모두 **`_CC` suffix** 필수.
  - 예: `docs/structural-redesign-tasks_CC.md`, `dev/active/phase-si-p7-structural-redesign/si-p7-plan_CC.md`
- Commit prefix: `[si-p7] Step X.Y: description` (또는 `[si-p7] SN-TN: description`)
- Branch: `feature/si-p7-structural-redesign` 또는 축별 `feature/si-p7-s1-defer` 등

---

## 주요 Critical Files

| 파일 | 담당 축 |
|---|---|
| `src/nodes/plan.py:155-161` | S1 (target 선정), S2 (reason code), S5a (plan_modify 연동) |
| `src/nodes/collect.py:218-230` | S1 (defer/queue), S2-a (parse prompt) |
| `src/nodes/integrate.py:80-132` | S2 (condition_split 재설계) |
| `src/nodes/integrate.py:176-253` | S3 (adjacent rule engine) |
| `src/nodes/critique.py:187-269` | S2 (feedback), S4 (virtual 즉시 제거), S5a (β mode 연동) |
| `src/nodes/entity_discovery.py` | S5a **신설** |
| `src/nodes/entity_reconcile.py` | S5b **신설** |
| `src/utils/entity_resolver.py` | S5a pre-filter + S5b alias/merge |
| `src/utils/metrics.py` | S2 distribution, S3 yield, S5a candidate 수명, S5b fragmentation |
| `src/state.py` | `deferred_targets` (S1) / `recent_conflict_fields` (S3) / `entity_candidates` (S5a) / `entity_fragmentation_signals` (S5b) |
| `src/graph.py` | S5a 노드 삽입 — 위치 B |
| `bench/japan-travel/state/domain-skeleton.json` | S2 `condition_axes`, S3 `field_adjacency` + `default_risk/utility`, S5a `entity_frame` |

---

## Anti-Patterns

| 패턴 | 문제 | 교정 |
|---|---|---|
| budget 초과 target 을 drop | S1 R1 pain-point 재발, defer_reason 집계 불가 | `deferred_targets` 에 기록 + 다음 cycle 우선 소진 |
| condition_split 을 "conditions 필드 있으면 split" 수준으로 유지 | codex §1.2 재정의 위반, 값 구조 차이 미감지 | S2-T6 `_detect_value_shape_diff` (axis_tags/conditions/값 format 비교) |
| virtual `balance-N` entity 과도기 유지 | D-182 / codex §1.3 Phase 2-5 위반, S5a 와 중복 | S4-T1 에서 **즉시 제거**, S5a 가 같은 phase 로 들어옴 |
| entity_candidates 에 pre-filter 없이 다 적재 | D-186 위반, S5a/S5b 경계 무너짐, 중복 후보 폭증 | similarity≥0.85 차단 → S5b alias 경로 |
| β aggressive mode 를 "매 cycle 실행" 과 혼동 | D-181/D-173 구분 무너짐 | β 는 **동작 방식 전환** (target 수/LLM/임계/GU 우선순위), 지속 trigger+2c |
| graph 위치 A (critique → entity_discovery → plan_modify) 선택 | D-183 위반. candidate 적재 중심인데 같은 cycle 반영은 latency 증가 | 위치 B 고수 |
| mock 으로 e2e 테스트 | D-187 / memory `feedback_test_real_path` 위반 | real API L2 smoke (`si-p7-*-smoke`) 또는 L3 A/B |
| 파일명 `_CC` suffix 누락 | D-180 위반 | `si-p7-*_CC.md` 로 통일 |

---

## 관련 skill

- **`silver-e2e-test-layering`** — L1/L2/L3 테스트 레이어와 trial-id 규약 (본 skill 과 쌍)
- **`evolver-framework`** — 5대 불변원칙 (KU/EU/GU/PU) 위반 가드
- **`langgraph-dev`** — graph/node 패턴. S5a 노드 신설 시 함께 참조
- **`silver-trial-scaffold`** — L3 A/B trial 디렉토리 생성 (`p7-*-on|off`)
- **`silver-phase-gate-check`** — SI-P7 완료 시 readiness-report 작성 (축별이 아닌 phase 전체)

---

## 관련 문서

1. **`docs/structural-redesign-tasks_CC.md` v2** — 본 skill 의 단일 진실 소스
2. `C:\Users\User\.claude\plans\ancient-seeking-sphinx.md` — plan v2 전문
3. `C:\Users\User\.claude\plans\ok-curious-naur.md` — 최종 실행 plan (본 skill 포함)
4. `docs/phase-next-refactor-task-review_codex.md` — codex 검토 원문 (통합 근거)
5. `docs/entity-acquisition-strategy-draft.md` — S5 근거
6. `docs/core-pipeline-spec-v1.md` — 기준 pipeline spec
