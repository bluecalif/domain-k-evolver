# Session Compact

> Generated: 2026-04-25
> Source: SI-P7 rebuild dev-docs 기반 갱신

## Goal

SI-P7 Structural Redesign **attempt 2 (rebuild)** — axis-gated 재구현.

- attempt 1 은 5축 일괄 구현 후 c3+ 고착 발생 → v5 sequential ablation (~$2.0) 으로 D-194/195/196 root cause 확정
- rebuild 핵심 전략: per-axis 5c smoke gate 의무 + pitfall pre-declare + V-T11 토글 cherry-pick

---

## 진실 소스 (세션 시작 시 이것부터 읽기)

1. `dev/active/phase-si-p7-structural-redesign/si-p7-tasks.md` ← **task checklist + L1/L2/L3 checkpoint**
2. `dev/active/phase-si-p7-structural-redesign/si-p7-plan.md` ← axis-gated rebuild 전략 전문
3. `dev/active/phase-si-p7-structural-redesign/si-p7-context.md` ← 코드/결정 포인터
4. `dev/active/phase-si-p7-structural-redesign/si-p7-debug-history.md` ← known pitfall 4종 포함

> **주의**: 본 파일(session-compact.md) 보다 위 dev-docs 가 항상 최신 진실 소스.

---

## Current State (2026-04-25)

- **브랜치**: `feature/si-p7-rebuild` @ `2ebd435` (Pre-P7 baseline)
- **최신 커밋**: `9c21eb4 [si-p7] rebuild: new phase dev-docs + project-overall sync`
- **테스트**: 824 passed, 3 skipped (깨끗한 상태)
- **dev-docs 생성**: 완료 (commit `9c21eb4`)

### Attempt 1 보존

- `main` 브랜치 HEAD: `a33dfdb` (S1~S4 구현 + V-T5~V-T11 instrumentation/toggle)
- `si-p7-attempt-1` tag (영구 archive)
- `bench/silver/japan-travel/p7-seq-{pre-a,s1,s2,s3,s4}/` (5-trial 데이터)

---

## Completed

- [x] SI-P6 root cause 확정 (D-167: Remodel-induced exploit_budget shrinkage)
- [x] SI-P7 attempt 1 구현 (S1~S4, V-T11 토글 인프라)
- [x] v5 sequential ablation (5-trial, ~$2.0)
- [x] D-194/195/196 root cause 확정
- [x] rebuild 전략 전환 결정 (D-200)
- [x] `feature/si-p7-rebuild` 브랜치 생성 @ Pre-P7 baseline
- [x] dev-docs 생성 완료 (`si-p7-plan.md`, `si-p7-context.md`, `si-p7-tasks.md`, `si-p7-debug-history.md`)
- [x] baseline v2 (`docs/structural-redesign-tasks_CC.md`) + skills 2종 (`silver-structural-redesign`, `silver-e2e-test-layering`) 확인

---

## Next Action (즉시 착수)

### Stage A — S1-T1 (첫 번째 task)

**`src/nodes/plan.py:155-161` `_select_targets` 정렬 로직 제거**

```
S1-T1: _UTILITY_ORDER / _RISK_ORDER 제거, _select_targets 정렬 제거
S1-T2: _select_targets 가 open_gus 전체 반환 (cycle cap 만 적용)
S1-T3: mode_node target_count 공식 → cycle cap 으로 대체 (src/nodes/mode.py)
```

Stage A 전체 순서: S1-T1 → T2 → T3 → T4 (defer/queue) → T5 → T6 (budget smoke) → T7 (regression guard) → T8 (deferred FIFO) → T9 (D-196 mitigation) → S2-T1 → S2-T2

### Stage A Gate (S1 완료 후 5c smoke)

```
trial: bench/silver/japan-travel/p7-rebuild-s1-smoke/
PASS: adj_gen c3+ 0 cycle 없음, defer_reason 다양성 ≤80%, KU c5 60~85
```

---

## Key Decisions (rebuild 신규 + 계승)

### Rebuild 신규 (D-200~D-202)

- **D-200**: axis-gated rebuild — per-axis 5c smoke gate 의무, 실패 시 axis 내부 narrowing
- **D-201**: v5 pitfall pre-declare + mitigation task 신설 (S1-T9, S2 보수화, S3 보수화)
- **D-202**: V-T11 cherry-pick 시점 = S2-T6 시작 직전 (`git cherry-pick f61c864`)

### Attempt 1 계승 (D-181~D-196)

- **D-181**: F2 = α (plan query 재작성) + β (aggressive mode, S5a-T11 동반 구현 필수)
- **D-182**: S5a = C3-a 전체 (적재 + 승격 + 후속 GU)
- **D-183**: graph 위치 = B (plan_modify → entity_discovery → plan)
- **D-184**: discovery target = `coverage_map.deficit_score` 공유
- **D-185**: candidate 수명 = last_seen+5c stale / +10c purge
- **D-186**: 유사 후보 similarity≥0.85 pre-filter → S5b alias
- **D-194**: Primary Introducer = S2 (T5~T8 condition_split 강화)
- **D-195**: S2 T5~T8 보수화 필수 (임계 강화)
- **D-196**: S1 adj_gen oscillation — S1-T9 critique rx mitigation

---

## Stage 구조 요약

```
Stage A → S1 5c gate → S2-T1/T2 1c gate
Stage B → S2-T3~T8 5c gate → S3 5c gate → S4 5c gate
Stage C → S5a 5c gate
Stage D → 15c L3 통합 trial → readiness-report (Gate 공식 판정)
```

**비용 예산**: per-axis ~$0.4 × 5 = ~$2.0 + 통합 15c ~$0.8 = **~$2.8**

---

## 제약 / 주의사항

- **D-34**: real API 필수, 합성 E2E 만으로 gate 불가
- **D-129**: `target_count` cap 재도입 금지 (S1-T7 regression guard)
- **D-187**: mock 금지, fixture real snapshot 만
- **D-200**: per-axis 5c smoke gate 통과 전 다음 axis 진입 금지
- **D-202**: V-T11 cherry-pick 은 S2-T6 시작 직전에 (사전 cherry-pick 금지)
- **_CC suffix**: `si-p7-{plan,context,tasks,debug-history}_CC.md` 는 구식 artifact, 본 docs 가 supersede
- **Attempt 1 보존**: main 브랜치 + tag `si-p7-attempt-1` force-delete 금지
- **S5b / Remodel**: 본 phase 범위 외, 다음 phase
- **F1**: S1-T6 smoke 5c 후 결정 (budget 완전 제거 여부)
