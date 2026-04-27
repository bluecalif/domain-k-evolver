# SI-P7 Structural Redesign — Debug History (rebuild)

> Last Updated: 2026-04-27
> Status: Stage B-1 Extension (S3 Diagnosis 2-Trial Plan) CLOSED. 엔트리 누적 중.
> Attempt 1 history (참조): `git show main:dev/active/phase-si-p7-structural-redesign/si-p7-debug-history.md`

---

## 템플릿

```markdown
### YYYY-MM-DD — [축/Task ID] 제목 한 줄

**증상**: 관찰된 이상 (로그, 메트릭, 테스트 결과)
**환경**: commit / trial_id / cycle
**원인**: root cause 분석. 가설 → 검증 과정
**해결**: 수정 내용 + 파일/라인
**검증**: L1/L2/L3 결과
**Decision**: (해당 시) D-XXX 기록. baseline v2 반영 필요 여부
```

---

## 본 phase 시작 전 알려진 위험 (Pre-Implementation Known Pitfalls)

attempt 1 v5 sequential ablation 으로 사전 식별된 axis 별 pitfall 과 mitigation. **각 axis 구현 시 plan.md §4 의 mitigation 그대로 적용 의무**.

### Pitfall #1 — S1 adj_gen oscillation (D-196)

**기원**: attempt 1 V-T8/T9 V3 ablation 후 v5 §8 분석
**증상**: c2~c5 jump mode 진입 후 c3/c5 에 adj_gen=0 plunge
**메커니즘**:
1. 1단계 adj chain 억제 정책 (`A:adjacent_gap` resolved → 새 adjacent GU 생성 안 함)
2. S1 sort 제거 + deferred FIFO → A:adj batch clustering → 특정 cycle 에 resolved 가 전부 A:adj
3. (1) + (2) 결합 → adj source 고갈 → adj_gen=0
**위험**: S2 condition_split 강제 + S3 adjacent rule engine 결합 시 GU pool 즉시 고갈
**Mitigation (S1-T9 신설)**: critique 처방 `stagnation:no_adj_source` — adj_gen=0 감지 시 다음 cycle `?` (seed) / `E:cat_balance` GU 우선 선정 (v5 §8.6 Option 4)

### Pitfall #2 — S2 T5~T8 강제 condition_split 폭증 (D-194/D-195)

**기원**: v5 5-trial sequential ablation (s2-attempt-1 c1 KU=72, +59 폭증)
**증상**:
- c1 ΔKU = +59 (s1-attempt-1 +33 대비 +26 추가)
- GU 양산 c5 = 49 (s1-attempt-1 79 대비 −30 감소)
- c3+ 고착 (KU c5=88 정체, adj_gen=0)
**메커니즘**: 기존 conflict/update 로 처리될 claim 이 강제 condition_split 으로 재분류 → 1 KU 가 N KU 로 분할 → KU 폭증 + GU 매칭 불일치 → GU 양산 급감
**Mitigation (보수화 임계)**:
- T6 (값 구조 차이): existing/claim 모두 ≥ 2 chars, set/range 변환 시 명시적 marker
- T7 (condition_axes 강제): claim 의 conditions 필드 비어있지 않을 때만
- T8 (axis_tags 차이): 단일 axis 차이만 (geography), 다중 axis 차이는 hold
**Fail-safe**: V-T11 cherry-pick 후 토글 narrowing 가능 (`SI_P7_RULE_OFF=t6` 등)

### Pitfall #3 — S3 GU pool 고갈 (D-194 Aggravator)

**기원**: v5 5-trial (s3-attempt-1 GU_open c3+ = 0, target_count c4/c5 = 0)
**증상**: S2 + S3 결합 시 c4/c5 cycle 완전 skip (1-2s 실행)
**메커니즘**: S2 condition_split 으로 GU 양산 부족 + S3 adjacent rule engine + suppress + blocklist + yield tracker 의 추가 억제 → pool 고갈
**Mitigation (보수화 임계)**:
- suppress: category 별 `mean × 2.0` (1.5 → 2.0)
- blocklist window: N=2 (3 → 2)
- yield tracker 약화 임계: 5c 평균 < 0.05 (강한 신호만)

### Pitfall #4 — S2-T4 β aggressive mode dead code (H5c, attempt 1 V1)

**기원**: attempt 1 V1 signal audit (`p7-ab-on` 15c)
**증상**: `aggressive_mode_remaining=3` 설정되지만 mode 효과 경로 (target 확장, source_count≥1 임시 적재, LLM query) 가 S5a-T11 에 배정되어 있어 S5a 미구현 시 no-op
**Mitigation (S5a-T11 동반 구현 의무)**:
- β 효과 경로를 S5a-T11 와 함께 구현 (S2-T4 단독 구현 시 dead code 보장)
- `logger.info` 명시
- `state.aggressive_mode_remaining` snapshot persist 의무
- L2 smoke 에서 β 강제 trigger 후 snapshot 확인

---

## 엔트리

### 2026-04-27 — [S3 Diagnosis] Trial 3 + V2 옵션 A + Stage closure

**증상**: Trial 2 M-Gate FAIL. V2 transport+10/pass-ticket+1/connectivity+1, O1 transport abandoned (v=15,o=0), O2 KL=∞, VxO 2-cat 불건전, M2 0.00, M5/M6/M7 FAIL.
**환경**: commit `d287a17` (Trial 2 fix 누적), trial 결과 `bench/silver/japan-travel/si-p7-s3-trial2-smoke/`
**원인**:
- transport cascade: SWEEP-SCOPE fix 가 transport wildcard `:*:duration` resolve → 4 신규 entity (osaka-universal-studios-japan 등) 등장 → adj GU 받았으나 plan 미선택 → vacant 누적
- M-Gate eval_v2 가 summary by_category 수준 비교 → 신규 entity vacant 를 regression 으로 오판
**해결 (옵션 A)**: `eval_v2()` per-entity 기반 재작성, baseline matrix 미존재 entity 의 vacant 제외
- 변경: `scripts/check_s3_gu_gate.py:260-302` — `_per_entity_vacant_by_cat` helper + 새 eval_v2
- L1 +5 (`TestEvalV2`): `tests/scripts/test_check_s3_gu_gate.py`
**검증**:
- L1: 919 PASS (+5 from baseline 914)
- L3 Trial 3 (5c, 16.5분, ~$0.5): KU 79→120 (+52%, 1.52×). M-Gate 결과 V/O 4/6 + M 9/13 PASS (Trial 2 대비 VxO·M2 신규 PASS, M5/M6/M7 부분 진척: Δc5 0→4, M6 0.51→0.89, M7 27→17)
- 잔여 FAIL: O1 attraction abandoned (v=54, o=0) — transport 패턴이 attraction 으로 이동, plan 미선택 동일 root cause
**Decision (사용자, 2026-04-27)**: Stage B-1 Extension (S3 Diagnosis 2-Trial Plan) CLOSED. plan-side budget 한계 root cause 는 Stage B-3 (condition_split) 와 SI-P4 (coverage) 에서 동반 처리.
**Commits**: `eb0bc24` (옵션 A V2), `9a832d1` (closure 문서)
**Trial 결과 디스크**: `bench/silver/japan-travel/si-p7-s3-trial{1,2,3}-smoke/` (untracked)
**잔여 코드 부채**:
- adj GU sweep 신규 entity 무한 cascade 억제 (plan budget / quota 정책) — Stage B-3/B-4 또는 SI-P4
- `conflict_ledger` cycle stamp → M7 strict check 활성화 가능

---

## 참조

- attempt 1 debug-history (전체): `git show main:dev/active/phase-si-p7-structural-redesign/si-p7-debug-history.md`
- v5 final report: `git show main:dev/active/phase-si-p7-structural-redesign/v5-sequential-ablation-report.md`
- attempt 1 V1 signal audit: `git show main:dev/active/phase-si-p7-structural-redesign/v1-signal-audit.md`
- attempt 1 V3 isolation report: `git show main:dev/active/phase-si-p7-structural-redesign/v3-isolation-report.md`
