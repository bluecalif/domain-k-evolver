# Phase: Gap-Resolution 병목 조사 — Debug History
> Last Updated: 2026-04-14

## Entries

### 2026-04-14 — Primary bottleneck 근본 원인 확정

**증상**
- SI-P3R 15c trial에서 gap_resolution_rate 0.517@15c (Phase 5 Bronze 0.909 대비 -42%)
- cycle 10: open=67, resolved=52, target=10 → 이론 상한 10 resolve/cycle

**조사 과정**
1. trajectory.csv 분석: cycle당 resolve 3-7개로 매우 일정 → rate-limited 패턴 확인
2. cycle 5~10 구간 신규 GU 생성 ~0, 그럼에도 open 67 유지 → resolve throughput이 병목임 확증
3. `src/nodes/mode.py:204-212` 읽기 → `JUMP_TARGET_CAP=10` + `min(..., cap)` 패턴 발견
4. `git log src/nodes/mode.py` → Phase 5 commit `b122a23`에서 cap 제거 이력 확인
5. `git show b12545d` → SI-P3 "디버그 로그 정리" 커밋에서 D-37 참조로 cap **재도입** 확정

**근본 원인**
- commit `b12545d` ([si-p3] 디버그 로그 정리): D-37 "jump target_count 상한 10" 원문만 보고 cap을 재도입
- Phase 5 (`b122a23`)에서 gap_resolution 0.909 달성을 위해 의도적으로 cap을 제거했던 사실을 놓침
- regression 경로: Phase 5 `target_count = max(10, ceil(open*0.5))` → SI-P3 `target_count = min(max(10, ceil(open*0.5)), 10) = 10` 고정

**수정 방향**
- `src/nodes/mode.py:204-212` Phase 5 상태로 복원
- `NORMAL_TARGET_CAP`, `JUMP_TARGET_CAP` 상수 삭제
- 로깅은 유지 (b12545d의 `mode:...` 로그는 유용)

**교훈 (Lesson)**
- **Phase 간 의도 전승 실패**: D-37이 Phase 1-2 맥락에서 유효했으나 Phase 5에서 해제되었다는 사실이 결정 로그에 명시되지 않았음
- **Git diff만 보는 디버깅의 한계**: commit history를 거슬러 올라가 원래 의도를 확인해야 함
- **Phase 5 PASS 결과가 재현 안 될 때 먼저 regression 의심**: mode/plan 관련 공식 변경이 있었는지 검증

**Action Items**
- [ ] MEMORY.md에 D-129 등록: "target_count cap은 Phase 5에서 의도적으로 제거됨. 재도입 금지"
- [ ] D-37 항목에 "Phase 5 (`b122a23`)에서 철회됨" 주석 추가 고려
- [ ] Phase 전환 시 핵심 공식/상수 변경 목록을 dev-docs context.md에 명시하는 컨벤션 검토

---

### 2026-04-14 — Secondary bottleneck 발견 (target→resolve conversion ~50%)

**증상**
- Primary fix만으로는 설명 안 되는 잔여 손실
- 사용자 지적: "even if target_count=10, resolved target was only 3-5"

**조사 과정**
1. cycle 10 snapshot gap-map 분석 — 67 open GU 분포 확인
   - 63 medium / 4 high utility
   - 48 `A:adjacent_gap` 동적 GU, 4 `E:category_balance`, 15 seed
2. 15c 최종 state 분석:
   - 78 resolved GU (target 150 대비 52%)
   - 105 active KU, 평균 evidence 3.76 → 누적 ~395 evidence links
3. collect.py + integrate.py 코드 경로 추적:
   - LLM 프롬프트에 `source_gu_id: "{gu_id}"` hard-coded → 이론상 100% 유지되어야 함
   - 실측은 50% → LLM이 `[]` 반환하거나 source_gu_id 누락 추정

**가설 (미확증)**
- H1 (유력): LLM parse가 target field 정보 없는 snippet에 대해 `[]` 반환
- H2: query 품질 — `{slug} {field}` 단순 조합이 관련 snippet 미회수
- H3: LLM의 source_gu_id 변조 (prompt 준수율)
- H4 (약함): conflict_hold로 open 유지 — conflict_rate 0-17%로 주원인 아님

**확증 경로 (계획)**
- Stage A1 (parse_yield 로깅) + A2 (integration_result 로깅) 추가
- Stage C 재현 trial에서 정량 데이터 수집
- Stage D1에서 가설 확증/기각

**교훈 (잠정)**
- **단일 trial 데이터로 병목 수치는 측정 가능, 원인은 불확정**: 진단 로깅 선제적 추가 필요
- **"LLM이 프롬프트를 따를 것"이라는 가정은 위험**: source_gu_id 등 critical 필드는 후검증 또는 무효화 카운트 필요

---

### 2026-04-14 — Stage C 재현 Trial 결과 (B1 Fix + B2 가설 확증)

**Trial**: `bench/silver/japan-travel/gap-res-fix-trial/` 15c, commit `9d9c8c5`

**Primary 수정 효과 (D-129 확정)**
- gap_resolution_rate: 0.517 → **0.990** (+91%)
- gu_open final: 73 → **1** (−98.6%)
- Gate PASS (VP1 5/5, VP2 5/6, VP3 5/6) — Bronze 기준 초과 달성
- LLM 비용 ~1.5x 증가 (3x 예측 대비 낮음 — target 증가분 만큼 빠르게 수렴)

**Secondary 가설 확증 (H1~H4)**
- **H1 (LLM parse 수율 낮음) 기각**: parse_yield_summary 로그 avg_claims 3.5~5.0 per target, zero_ratio 대부분 0. LLM은 target당 안정적으로 3-5 claims 생성.
- **H3 (source_gu_id 누락/변조) 완전 기각**: integrate_result 15 cycles 전체 `no_source_gu=0`. LLM의 prompt 준수율 100%.
- **H2/H4**: 검증 불필요 (B1 fix만으로 수렴 달성)
- **"52% conversion"의 실체**: snippet-first 구조상 target당 N claims fan-out. `resolved/claims` 기준은 구조적으로 낮을 수밖에 없으며, `resolved/targets` ≈ 90-100%로 실제 conversion 병목 없음.

**결정 (D-130)**
- Secondary fix 불필요 — 병목의 실체가 없음이 확인됨
- 별도 Phase 이관도 불필요

**교훈 (Lesson)**
- **구조적 분모 오해의 함정**: `resolved/claims` 지표는 1:1 target→claim 가정 하에서만 유효. snippet-first(1:N fan-out)로 전환되면 분모 정의를 재검토해야 함.
- **진단 로깅의 힘**: A1(parse_yield)+A2(integrate_result) 추가로 재현 trial 1회에 B1 확증 + B2 가설 기각 동시 달성 — API 비용 최소화

---

## Phase 종결 (2026-04-14)

**전체 결과 요약**
- Primary 병목 (B1): commit 1개로 해소, gap_resolution 0.517→0.99
- Secondary 병목 (B2): 실체 없음 확인, 추가 작업 불필요
- 관련 Decisions: D-126, D-129, D-130, D-131

## Pending Investigations (완료)

| ID | 주제 | Stage | Status |
|----|------|-------|--------|
| INV-1 | LLM parse yield rate 정량 측정 | A1, C2 | ✅ avg 3.5~5 per target (H1 기각) |
| INV-2 | integration_result 분포 | A2, C2 | ✅ no_source_gu=0 (H3 완전 기각) |
| INV-3 | Primary fix 효과 정량화 | C1~C3 | ✅ 0.517→0.99 확증 |
| INV-4 | Secondary fix 범위 결정 | D1, D2 | ✅ Fix 불필요 (D-130) |
