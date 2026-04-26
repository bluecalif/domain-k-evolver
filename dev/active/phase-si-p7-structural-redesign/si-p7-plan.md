# SI-P7 Structural Redesign — Plan (rebuild / attempt 2)

> Last Updated: 2026-04-26
> Status: Planning (착수 전, attempt 1 v5 분석 입력 반영)
> Branch: `feature/si-p7-rebuild` (from `2ebd435` Pre-P7 baseline)
> Single source of truth: **`docs/structural-redesign-tasks_CC.md` v2**
> Attempt 1 archive: `main` branch + tag `si-p7-attempt-1` — v5 5-trial sequential ablation, V-T11 토글 인프라 포함
> 관련 skill: `silver-structural-redesign`, `silver-e2e-test-layering`

---

## 1. Summary

SI-P7 attempt 1 (main `a33dfdb`) 은 5축 (S1~S4) 일괄 구현 후 c3+ 고착 (`p7-ab-on` 15c trial) 을 발견했으나 **per-axis gate 부재** 로 root cause 추적이 어려웠다. v5 sequential ablation (5-trial, ~$2.0) 으로 원인 isolate (D-194 S2=Primary, D-195 T5~T8 의심, D-196 S1 oscillation) 후 attempt 2 (rebuild) 로 전환.

**attempt 2 핵심 차별점**:
1. **Axis-gated**: 각 axis 완료 시 5c L3 smoke gate 통과 의무. 실패 시 다음 axis 진입 금지
2. **Pitfall 사전 명시**: v5 분석으로 알려진 위험을 axis 별로 pre-declare 후 mitigation 함께 구현
3. **Subtask 토글 인프라 cherry-pick**: V-T11 (T6/T7/T8 sub-rule 토글) 을 S2 재구현 시 활용 → 실패 시 narrowing

**범위**: baseline v2 §권장 착수 순서 그대로. Step A (S1 + S2-T1/T2) → Step B (S2-T5~T8 + S3 + S4) → Step C (S5a). S5b/Remodel 재설계는 다음 phase.

---

## 2. Current State (2026-04-25)

- **브랜치**: `feature/si-p7-rebuild` @ `2ebd435` Pre-P7 baseline
- **테스트**: 824 passed, 3 skipped (Pre-P7 깨끗한 상태)
- **Attempt 1 보존**:
  - `main` branch HEAD: `a33dfdb` (S1~S4 구현 + V-T5~V-T11 instrumentation/toggle)
  - `si-p7-attempt-1` tag (영구 archive)
  - `bench/silver/japan-travel/p7-seq-{pre-a,s1,s2,s3,s4}/` (5-trial 데이터)
  - dev-docs (main): `si-p7-{plan,context,tasks,debug-history}.md` + `v1`~`v5` 분석 6종
- **단일 진실 소스**: `docs/structural-redesign-tasks_CC.md` v2 (현 브랜치에 존재)
- **베이스라인 spec scaffolding**: `_CC` suffix 4종 (D-180 이전, 본 docs 로 supersede)

---

## 3. Target State

phase 종료 시:
1. Step A/B/C 의 모든 axis (S1, S2, S3, S4, S5a) 5c L3 smoke gate **PASS**
2. 각 axis 의 v5-known-pitfall 회피 검증 (S1 oscillation 0 cycle, S2 c1 KU 폭증 ≤ 30%, S3 GU pool 고갈 0 cycle)
3. `silver-phase-gate-check` 로 phase 전체 readiness-report **PASS** (15c trial, VP1/VP2/VP3 기준)
4. v6 final report 작성 (rebuild 결과 + attempt 1 대비 개선)
5. dev-docs → `dev/archive/`, project-overall 동기화

---

## 4. Implementation Stages

### Stage A — S1 (defer/queue) + S2-T1/T2 (integration_result 제어 입력화)

**v5 known-pitfall**: D-196 — S1 sort 제거 + deferred FIFO 가 만든 A:adj batch clustering → adj_gen oscillation (c3 plunge, c5 zero). 1단계 adj chain 억제 정책과 결합 시 GU pool 고갈 가속.

**Mitigation (S1-T9 신설)**: critique 처방 `stagnation:no_adj_source` 추가 — adj_gen=0 감지 시 다음 cycle 에 `?` (seed) / `E:cat_balance` GU 우선 선정. v5 §8.6 Option 4.

**Tasks**: baseline v2 §S1 (T1~T8) + S1-T9 (mitigation) + S2-T1/T2.

**Gate (5c smoke)**:
- adj_gen: c3+ 0 cycle 없음 (Pre-A trajectory 6/9/8/7/4 와 비교)
- defer 분포: defer_reason 다양성 (단일 reason 80% 미만)
- KU c5: pre-A 72 ±20% 이내

### Stage B — S3-T9~T14 (GU generation extension) + S2-T5~T8 + S4

**Stage B 구성**:
```
B-1/B-2 (S3, 완료) → B-1 Extension (S3-T9~T14) → B-3 (S2) → B-4 (S4)
```

#### Stage B-1 Extension — GU 생성 범위 확장 (S3-T9~T14) ← 신규

entity-field-matrix 분석으로 확인된 3가지 vacant 패턴 수정 + 구조적 제약 제거 (D-203~D-208):

| 결정 | 변경 내용 | 파일 |
|---|---|---|
| D-203 Bug A/B | `_generate_dynamic_gus` canonical entity_key + KU 슬롯 포함 | `integrate.py:193` |
| D-204 new-KU sweep | claim loop 이후 `adds` 기반 adj sweep | `integrate.py` |
| D-205 wildcard 병행 | seed entity-specific GU 생성 시 wildcard GU도 추가 | `seed.py:259` |
| D-206 per_cat_cap 제거 | cap 없이 전체 eligible GU 등록 | `seed.py:185,324` |
| D-207 field_adjacency 제거 | applicable_fields 전체 사용, direct pair 차단 해제 | `integrate.py:221` |
| D-208 dynamic_cap 고정 | `open_count * 0.2` 제거, normal=8/jump=20 고정 | `integrate.py:282` |

**Gate (5c smoke — M-Gate, V/O composite + M1~M8 mechanistic)**:
- ⚠️ 종전 G1~G5 narrative Gate 폐기 (false PASS 발급, 2026-04-26 재판정 → FAIL).
- 신 Gate 정의/임계값/근거: **`si-p7-gate-mechanistic.md`** (V/O 의미론, M criteria 임계값, exit code 정책).
- 구현: `scripts/check_s3_gu_gate.py` (V1/V2/V3, O1/O2, VxO + M1~M8 + telemetry-deferred M5b/M9/M10/M11)
- 1차 신호: Vacant 감소 + Open GU 분포 (V/O FAIL = unconditional FAIL).
- 보조 신호: T9~T14 fix 직접 검증 (M1=T9, M2=T11, M3=T12, M4=T13, M5=T14).

#### Stage B-3 — condition_split 재정의 (S2-T5~T8)

**v5 known-pitfall**: T5~T8 강제 condition_split → c1 KU +59 폭증 → KU/GU 불균형 → c3+ 고착.

**Conservatization (S2-T5~T8)**:
- T6: value 길이 임계 (≥ 2 chars), set/range 변환 시 명시적 marker 필요
- T7: claim.conditions 비어있지 않을 때만 split
- T8: 단일 axis 차이만 (geography), 다중 axis → hold

**Gate**: c1 ΔKU ≤ +35, GU 양산 ≥ 65, adj_gen c3+ 0 cycle 없음

#### Stage B-4 — balance 대체 (S4-T2~T4)

**Gate**: virtual entity = 0, deficit_score 발동률 ≥ 50%, KU c5 ≥ 75

### Stage C — S5a (Entity Discovery Node)

**Pitfall**: attempt 1 미도달. 새 영역. β aggressive mode 의 dead code 위험 (attempt 1 V1 audit 에서 H5c 확정).

**Mitigation**: S5a-T11 (β mode) 구현 시 logger.info 명시 + state field `aggressive_mode_remaining` snapshot persist 의무.

**Tasks**: baseline v2 §S5a (T1~T12) 그대로.

**Gate (5c smoke)**:
- entity_candidates 누적 ≥ 5
- 승격 entity ≥ 1 (5c 내)
- β mode trigger 시 `aggressive_mode_remaining` snapshot 에 기록

### Stage D — Phase 전체 L3 15c (공식 Gate)

각 axis 5c smoke 통과 후 통합 15c A/B trial:
- `bench/silver/japan-travel/p7-rebuild-on/` vs `p7-rebuild-off/` (Pre-P7)
- `silver-phase-gate-check` skill 로 readiness-report 작성
- VP1/VP2/VP3 기준

---

## 5. Task Breakdown

| Stage | Axis | Tasks | Size |
|---|---|---|---|
| A | S1 | T1~T9 (T9 mitigation 신설) | M (8 tasks) |
| A | S2-T1/T2 | T1, T2 | S (2 tasks) |
| B | S2-T3~T8 | T3 (design only), T4 (α+β), T5~T8 (조건 보수화) | L (6 tasks) |
| B | S3 | T1~T8 (T1/T2/T7 보수화) | M (8 tasks) |
| B | S4 | T1~T4 | S (4 tasks) |
| C | S5a | T1~T12 | XL (12 tasks) |
| D | L3 | 15c trial + readiness-report | M (3 tasks) |

**Total**: ~43 tasks (attempt 1 대비 +1: S1-T9 mitigation, +0 cherry-pick V-T11)

---

## 6. Risks & Mitigation

| Risk | 영향 | Mitigation |
|---|---|---|
| S1 D-196 oscillation 재발 | adj_gen=0 cycle, GU pool 고갈 | S1-T9 critique rx, 5c smoke gate 의무 |
| S2 T5~T8 폭증 미해소 | KU c1 +59 재발 | V-T11 토글 cherry-pick, 보수화 + smoke 후 narrowing |
| S3 GU 고갈 재발 | c4/c5 skip | suppress/blocklist/yield 임계 보수화, 5c gate |
| S5a β dead code | aggressive mode no-op | snapshot persist + logger.info 의무 |
| Attempt 1 lessons 반영 미흡 | 동일 pathology 반복 | per-axis gate 의무, v5 report 사전 review |
| 비용 초과 | 누적 ~$5 가능 | per-axis $0.4 × 5 = ~$2.0 + 통합 15c ~$0.8 = ~$2.8 예산 |

---

## 7. Dependencies

### 내부
- baseline v2 spec: `docs/structural-redesign-tasks_CC.md`
- v5 분석 (main): `git show main:dev/active/phase-si-p7-structural-redesign/v5-sequential-ablation-report.md`
- V-T11 토글 인프라: `git show main:src/config.py` (SIP7AxisToggles t6/t7/t8 fields)
- attempt 1 bench: `git show main:bench/silver/japan-travel/p7-seq-*/`

### 외부 (skills)
- `silver-structural-redesign` — 5축 가이드
- `silver-e2e-test-layering` — L1/L2/L3 + trial-id 규약
- `silver-trial-scaffold` — `p7-*-on|off` trial 디렉토리
- `silver-phase-gate-check` — phase 종료 시 readiness-report
- `evolver-framework` — 5대 불변원칙 가드
- `langgraph-dev` — graph/node 패턴 (S5a 노드 신설 시)

### 의존성 라이브러리
- 신규 추가 없음 (S5b 의 `rapidfuzz` 는 다음 phase)

---

## 참조

- baseline v2: `docs/structural-redesign-tasks_CC.md`
- v5 분석 (attempt 1): `git show main:dev/active/phase-si-p7-structural-redesign/v5-sequential-ablation-report.md`
- attempt 1 debug-history: `git show main:dev/active/phase-si-p7-structural-redesign/si-p7-debug-history.md`
- context: `si-p7-context.md`
- tasks: `si-p7-tasks.md`
- debug history: `si-p7-debug-history.md`
