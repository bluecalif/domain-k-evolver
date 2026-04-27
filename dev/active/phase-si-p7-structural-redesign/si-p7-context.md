# SI-P7 Structural Redesign — Context (rebuild)

> Last Updated: 2026-04-26
> 본 문서는 **구현 착수 시 코드 + 문서 + attempt 1 lessons 맥락** 을 빠르게 복원하기 위한 포인터 모음.

---

## 1. 핵심 파일 — 진입점 우선순위

### 1.1 단일 진실 소스 (현 브랜치)
1. **`docs/structural-redesign-tasks_CC.md` v2** — 5축 task breakdown, D-181~D-188, 테스트 3-layer
2. `si-p7-plan.md` — 본 phase plan (axis-gated rebuild)
3. `si-p7-tasks.md` — task checklist + L1/L2/L3 checkpoint
4. `si-p7-debug-history.md` — 본 phase 디버깅 이력 (생성 시점부터 누적)

### 1.2 Attempt 1 자료 (main 브랜치, 사전 review 의무)
- `git show main:dev/active/phase-si-p7-structural-redesign/v5-sequential-ablation-report.md` — 5-trial 결과 + D-194/195/196
- `git show main:dev/active/phase-si-p7-structural-redesign/v3-isolation-report.md` — V3 ablation 분석
- `git show main:dev/active/phase-si-p7-structural-redesign/si-p7-debug-history.md` — attempt 1 issue/원인/해결 이력
- `git show main:bench/silver/japan-travel/p7-seq-{pre-a,s1,s2,s3,s4}/trajectory/trajectory.json` — 5-trial 원본 데이터

### 1.3 V-T11 토글 인프라 (cherry-pick 후보)
- `git show main:f61c864 -- src/config.py src/nodes/integrate.py tests/test_si_p7_v2_instrumentation.py`
- T6/T7/T8 sub-rule 토글 + `SI_P7_RULE_OFF` env var

### 1.4 관련 skill
| Skill | 용도 |
|---|---|
| `silver-structural-redesign` | 5축 구현 가이드 (본 phase 전용) |
| `silver-e2e-test-layering` | L1/L2/L3 테스트 + trial-id 규약 |
| `silver-trial-scaffold` | L3 `p7-*-on|off` trial 디렉토리 생성 |
| `silver-phase-gate-check` | phase 전체 readiness-report (15c 통합) |
| `evolver-framework` | 5대 불변원칙 guardrail |
| `langgraph-dev` | graph/node 패턴 (S5a 신설 시) |

---

## 2. 데이터 인터페이스

### 2.1 입력 (읽기)
- `bench/japan-travel/state/domain-skeleton.json` — Pre-P7 baseline skeleton
- `bench/silver/japan-travel/p0-20260412-baseline/state/` — Silver P0 baseline state (real snapshot fixture)
- 5-trial 데이터 (main): `bench/silver/japan-travel/p7-seq-*/` — Pre-A/S1/S2/S3/S4 trajectory 비교 기준

### 2.2 출력 (쓰기)
- `bench/silver/japan-travel/p7-rebuild-{axis}-smoke/` — axis 별 5c L2 smoke
- `bench/silver/japan-travel/p7-rebuild-on|off/` — phase 전체 15c L3 A/B
- `dev/active/phase-si-p7-structural-redesign/readiness-report.md` — 최종 gate 판정

### 2.3 코드 수정 영역 (axis 별)
| 파일 | 위치 | 담당 axis |
|---|---|---|
| `src/nodes/plan.py` | 155-161 (정렬 제거), reason code | S1, S2 |
| `src/nodes/collect.py` | 218-230 (defer), `_build_parse_prompt` | S1, S2-a |
| `src/nodes/mode.py` | `mode_node` target_count | S1 |
| `src/nodes/integrate.py` | 80-132 (`_detect_conflict`) | S2 condition_split |
| `src/nodes/integrate.py` | 176-253 (`_generate_dynamic_gus`) | S3 rule engine + **S3-T9/T13/T14** |
| `src/nodes/integrate.py` | claim loop 이후 (~line 570) | **S3-T10** new-KU adj sweep |
| `src/nodes/integrate.py` | 282-286 (`_compute_dynamic_gu_cap`) | **S3-T14** cap 공식 |
| `src/nodes/seed.py` | 185-191 (`_get_per_category_cap`) | **S3-T12** per_cat_cap 제거 |
| `src/nodes/seed.py` | 259-292 (entity-specific 브랜치) | **S3-T11** wildcard 병행 생성 |
| `src/nodes/seed.py` | 324-330 (cap 적용 루프) | **S3-T12** cap 루프 제거 |
| `src/nodes/critique.py` | 187-269 (balance + feedback) | S2 feedback, S4 virtual 제거, S5a β |
| `src/utils/entity_resolver.py` | similarity | S5a pre-filter (0.85) |
| `src/utils/metrics.py` | — | S2 distribution, S3 yield, S5a 수명 |
| `src/state.py` | — | `deferred_targets`, `recent_conflict_fields`, `entity_candidates` |
| `src/config.py` | `SearchConfig`, 신규 `SIP7AxisToggles` | S1 budget, V-T11 cherry-pick |
| `src/graph.py` | graph builder | S5a 노드 삽입, 위치 B |
| `bench/japan-travel/state/domain-skeleton.json` | — | S2 condition_axes, S3 field_adjacency, S5a entity_frame |

### 2.4 신설 파일
- `src/nodes/entity_discovery.py` (S5a)
- `src/nodes/entity_reconcile.py` (S5b — 다음 phase)

---

## 3. 주요 결정사항 (attempt 2 신규 + attempt 1 계승)

### 3.1 Attempt 2 신규 (rebuild 결정)

- **D-200 (rebuild 전략)**: attempt 1 일괄 구현 후 ablation → axis-gated 재구현 + per-axis 5c smoke gate 의무로 전환. 이유: attempt 1 의 c3+ 고착이 root cause 추적 어려움 (D-189 단정 보류 → V1~V5 audit ~$2.0 소비).
  - **How to apply**: 각 axis 완료 → 5c smoke gate → 통과 시 다음 axis. 실패 시 axis 내부 narrowing (V-T11 패턴).
- **D-201 (per-axis pitfall pre-declare)**: v5 분석 결과 (D-194/195/196) 를 axis 별 plan.md 에 사전 명시 + mitigation task 신설. 이유: attempt 1 이 lessons 없이 진행해 동일 pathology 발생 위험 차단.
  - **How to apply**: S1 plan = D-196 mitigation (S1-T9 critique rx), S2 plan = T5~T8 보수화, S3 plan = suppress/blocklist 임계 보수화.
- **D-202 (V-T11 cherry-pick 시점)**: S2-T5~T8 재구현 시점에 V-T11 토글 인프라 cherry-pick (S2 narrowing 도구). 이유: 사전에 cherry-pick 하면 baseline 변경, 사후엔 fail 시 즉시 narrowing 불가.
  - **How to apply**: S2-T6 시작 직전 `git cherry-pick f61c864` (또는 `git show f61c864 -- src/config.py`).
  - **예외 (2026-04-27)**: pre-merge Phase 1 정리 시 narrowing 인프라 보존 우선으로 사전 cherry-pick 수행. commit `176d2c0` + `913ae47`. 토글 인프라 이미 적용 완료 — S2-T6 시작 시 재cherry-pick 불필요.

### 3.2 Attempt 1 계승 (D-181~D-196)

- **D-181** F2 = α (plan query 재작성) + β (aggressive mode) — `added_ratio<0.3×3c` trigger 시 entity_discovery mode 전환
- **D-182** S5a = C3-a 전체 (적재 + 승격 + 후속 GU)
- **D-183** graph 위치 = B (plan_modify → entity_discovery → plan)
- **D-184** discovery target 신호 = `coverage_map.deficit_score` 공유 (S4 와)
- **D-185** candidate 수명 = last_seen+5c stale / +10c purge
- **D-186** 유사 후보 = similarity≥0.85 pre-filter → S5b alias
- **D-187** 테스트 3-layer + mock 금지. **L3 만 Gate 공식 판정**
- **D-188** Skill 2종 (`silver-structural-redesign`, `silver-e2e-test-layering`)
- **D-189 ~ D-193** (attempt 1 issue/audit) — 본 attempt 에서 mitigation 적용 완료
- **D-194** Primary Introducer = S2 (5-trial sequential ablation)
- **D-195** S2 내부 primary subtask = T5~T8 (condition_split 강화)
- **D-196** S1 adj_gen oscillation 메커니즘 = 1단계 adj chain 억제 + sort 제거 + FIFO batch clustering

### 3.2-B S3 GU Generation Extension (신규, 2026-04-26)

entity-field-matrix 분석으로 확인된 3가지 vacant 패턴과 구조적 GU 생성 제약 4가지 제거:

- **D-203 (P1 fix — Bug A/B)**: `_generate_dynamic_gus`가 `claim.get("entity_key")` (raw) 사용 → canonical entity_key 사용으로 수정. `existing_slots`에 KU 슬롯 미포함 → `existing_ku_slots` 파라미터 추가. `integrate_node` 호출부에서 canonical key 전달.
  - **Why:** wildcard GU 해소 시 claim entity_key = `attraction:*` → adj GU도 wildcard 단위로만 생성. named entity별 hours/tips/price adj GU 불가.
  - **How to apply:** S3-T9 구현 시 `_generate_dynamic_gus` 시그니처 변경 + 호출부 수정.

- **D-204 (P1 fix — new-KU sweep)**: post-cycle `adds` 리스트 기반 adj sweep 추가. claim이 없어도 신규 KU 생성 시 adj GU 자동 발견.
  - **Why:** wildcard 해소로 파생된 named entity KU (`kitakami:location`)에 대해 adj GU 트리거 기회가 없음. claim loop 종료 후 `adds` 순회로 해결.
  - **How to apply:** S3-T10 구현, `sweep_entity_seen` set으로 중복 방지, 기존 `dynamic_cap` 공유.

- **D-205 (P2 fix — seed wildcard 병행)**: seed.py entity-specific 브랜치에서 wildcard GU도 함께 생성. `transport:*/price` 등 wildcard 슬롯 영구 미등록 문제 해결.
  - **Why:** named entity 존재 시 `elif ENTITY_SPECIFIC_FIELDS and known_entities:` 브랜치만 진입, wildcard(`*`) 슬롯 건너뜀.
  - **How to apply:** S3-T11 구현, `(cat, field)` wildcard가 이미 `seen`에 있으면 skip.

- **D-206 (P3 fix — per_cat_cap 제거)**: `_get_per_category_cap` 및 cap 적용 루프 완전 제거. regulation/price, suica/eligibility 등 15개 슬롯 영구 미등록 문제 해결.
  - **Why:** n_categories=8 → per_cat_cap=4. regulation이 eligibility 4개(critical)로 cap 소진 → price/tips 미등록.
  - **How to apply:** S3-T12 구현. 최소 커버리지 보장 로직(`seed.py:332-353`)은 유지.

- **D-207 (field_adjacency 규칙 제거)**: `_generate_dynamic_gus`의 field_adjacency 조회 브랜치 제거 → 항상 `applicable_fields` 전체 사용.
  - **Why:** field_adjacency는 "speed mitigator"로 설계됐으나 실제로는 direct pair에 대한 ultimate blocker. `location → price` 직접 생성 불가. applicable_fields 전체가 더 단순하고 dynamic_cap이 실질적 rate control.
  - **How to apply:** S3-T13 구현. skeleton의 `field_adjacency` 데이터 자체는 보존.

- **D-208 (dynamic_cap 공식 수정)**: `open_count * 0.2` 제거 → 고정 cap: normal=8, jump=20.
  - **Why:** 현재 공식 `min(max(4, ceil(open_count * 0.2)), 12)` — open GU 감소 시 adj GU cap이 위축. GU pool이 수렴할수록 adj GU 생성이 제한되는 음의 피드백 루프 → vacant 슬롯 영구 미해결.
  - **How to apply:** S3-T14 구현. `_compute_dynamic_gu_cap(mode)` 인자에서 `open_count` 제거.

### 3.3 이전 phase 계승
- D-67/D-68/D-69/D-70 (observed_at, evidence-count weighting, multi-evidence boost)
- D-129 target_count cap 재도입 금지
- D-180 dev-docs `_CC` suffix 제거 (spec 문서만 유지)

---

## 4. 컨벤션 체크리스트

### 4.1 5대 불변원칙
- [ ] **Gap-driven**: Plan 은 Gap 이 구동
- [ ] **Claim→KU 착지성**: 모든 Claim 은 KU 로 변환
- [ ] **Evidence-first**: KU 는 EU 없이 미완성 (active KU 는 evidence_links ≥ 1)
- [ ] **Conflict-preserving**: 충돌 보존 (disputed KU 삭제 금지, conflict_ledger append-only)
- [ ] **Prescription-compiled**: Critique 처방은 Plan 에 반영

### 4.2 Metrics 임계치
- [ ] 근거율 ≥ 0.95
- [ ] 다중근거율 ≥ 0.50
- [ ] 충돌률 ≤ 0.05

### 4.3 Schema 정합성
- [ ] entity_key 형식: `{domain}:{category}:{slug}` (예: `japan-travel:transport:jr-pass`)
- [ ] JSON Schema (KU/EU/GU/PU) 준수
- [ ] schema validator 통과

### 4.4 인코딩 (Windows + Korean)
- [ ] CSV read: `encoding='utf-8-sig'`
- [ ] File write: `encoding='utf-8'` 명시
- [ ] JSON read/write: `encoding='utf-8'`
- [ ] PYTHONUTF8=1 환경변수

### 4.5 Phase 운영 규칙 (이전 phase 교훈)
- [ ] **D-34**: 실 벤치 trial (real API) 필수, 합성 E2E 만으로 gate 불가
- [ ] **D-129**: `target_count` cap 재도입 금지 — S1-T7 regression guard
- [ ] **D-180**: dev-docs `_CC` suffix 사용 안 함 (본 docs 는 no-suffix)
- [ ] **D-187**: mock 금지, fixture real snapshot 만
- [ ] **per-axis gate**: 5c smoke 통과 전 다음 axis 진입 금지 (D-200 신규)

---

## 5. 주의사항 / 제약

- **Attempt 1 자료 위치**: main 브랜치 + tag `si-p7-attempt-1`. force-delete 금지
- **bench data 보존**: `git show main:bench/silver/japan-travel/p7-seq-*/` — 비교 기준
- **V-T11 인프라**: 사전에 cherry-pick 하지 말 것 — S2-T5~T8 시점에 cherry-pick (D-202)
- **`_CC` suffix scaffolding**: `si-p7-{plan,context,tasks,debug-history}_CC.md` 는 baseline `2ebd435` 의 pre-D-180 artifact. 본 docs 가 supersede. 정리 시 삭제 가능
- **Remodel**: 본 phase 범위 외, 별도 재설계 예정
- **S5b**: 본 phase 범위 외 (다음 phase 후보)
- **F1**: S1-T6 smoke 5c 후 결정 (budget 완전 제거 여부)
- **F4**: S5b 임계치 → 다음 phase
