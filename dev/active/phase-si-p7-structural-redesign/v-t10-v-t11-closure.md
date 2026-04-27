# V-T10 / V-T11 Closure

> Created: 2026-04-27 (pre-merge 정리)
> Branch: `feature/si-p7-rebuild` 에 기록. 원본 작업은 `archive/si-p7-attempt-1` (commit `02f7653`, `f61c864`).

---

## V-T10 — Sequential Ablation Root Cause Analysis

**완료 위치**: main (attempt 1) commit `02f7653`
**산출물**: `v5-sequential-ablation-report.md`, `v4-hypothesis-matrix.md` (archive 내)

### 수행 내용

v4 가설 매트릭스 접근(D-192)이 Clear-gate NOT CLEARED 판정을 받아 폐기. 대신 5-trial Sequential Ablation (Pre-A / S1 / S2 / S3 / S4, 5c each)으로 root cause 를 직접 격리.

| Trial | s1 | s2 | s3 | s4 | KU_final | GU_open_c5 |
|---|---|---|---|---|---|---|
| Pre-A | off | off | off | off | 37 | 0 |
| S1 | **on** | off | off | off | 39 | 0 |
| S2 | on | **on** | off | off | 37 | 0 |
| S3 | on | on | **on** | off | 37 | 0 |
| S4 | on | on | on | **on** | 37 | 0 |

→ **c3+ pool 고갈은 S1 단독 on 에서 이미 발생. S2 on 이 악화. S3 추가 억제. S4 mitigator.**

### 결정 (D-192, D-194, D-195, D-196)

| ID | 내용 |
|---|---|
| **D-192** | v4 가설 매트릭스 접근 폐기 → Sequential Ablation 채택 |
| **D-194** | Primary Introducer = **S2**. Secondary Aggravator = S3. Mitigator = S4 |
| **D-195** | S2 내부 primary subtask 유력 후보 = **S2-T5~T8 (condition_split 확장)** |
| **D-196** | S1 adj_gen oscillation 원인 = 1단계 adj chain 억제 + sort 제거 + FIFO batch clustering |

### 이 branch 에서의 접근

`v5-sequential-ablation-report.md` 의 결론이 rebuild 계획 (`si-p7-context.md` Pitfall #1~#4) 에 반영 완료.
원본 보고서는 `git show archive/si-p7-attempt-1:dev/active/phase-si-p7-structural-redesign/v5-sequential-ablation-report.md` 로 접근.

---

## V-T11 — T6/T7/T8 Condition_split Sub-rule Toggles

**원본 위치**: main (attempt 1) commit `f61c864`
**cherry-pick 결과**: commit `176d2c0` (branch HEAD, 충돌 해결 commit `913ae47`)

### 내용

`SIP7AxisToggles` 에 `t6_struct_split / t7_axes_forced_split / t8_axis_tags_split` 3개 필드 추가.
`SI_P7_RULE_OFF=t6,t7,t8` env var 로 S2-T5~T8 재구현 후 개별 rule 비활성화 가능.

| 토글 | Rule | 동작 |
|---|---|---|
| `t6_struct_split` | Rule 2b | 값 구조 차이 (scalar vs range vs set) → condition_split |
| `t7_axes_forced_split` | Rule 2d | skeleton condition_axes 정의 → 강제 condition_split |
| `t8_axis_tags_split` | Rule 2c | axis_tags 차이 → condition_split |

### D-202 예외 처리

D-202 는 "V-T11 cherry-pick 은 S2-T5~T8 재구현 시점에 수행" 이 원칙이나,
**pre-merge 단계에서 예외 적용**: branch 를 main 으로 reset (force-push) 시 narrowing 인프라 부재 위험 회피.
merge 완료 후 D-202 원칙은 유지 (재구현 시 기존 인프라 활용).

### 충돌 해결 요약

| 항목 | 처리 |
|---|---|
| `src/config.py` | `SIP7AxisToggles` 클래스 완전 수용 (f61c864 버전) |
| `src/nodes/integrate.py` | 함수 시그니처 + Rule 2b/2c/2d 수용. conflict 4 는 branch 구현 우선 + toggle loading 만 추가 |
| `_value_structure_type` | cherry-pick 과정에서 누락 → 수동 복구 (commit `913ae47`) |
| `tests/test_si_p7_v2_instrumentation.py` | V-T11 toggle tests 15개 PASS, V2 instrumentation 15개 skip |

### 검증

- **934 passed, 18 skipped** (기존 919 대비 +15 toggle tests 신규 PASS)

---

## 현재 상태

| 항목 | 상태 |
|---|---|
| V-T10 결론 | rebuild 계획에 반영 완료 |
| D-192 | debug-history 등록 |
| V-T11 cherry-pick | ✅ 완료 (commit `176d2c0` + `913ae47`) |
| 원본 archive | `archive/si-p7-attempt-1` branch + `si-p7-attempt-1` tag |
