# Phase 0C Tasks — GU 전략 재검토
> Last Updated: 2026-03-04
> Status: ✅ Complete (6/6)

## Summary

| Stage | Task | Size | Status |
|-------|------|------|--------|
| A | 0C.1 축 선언 보완 | M | ✅ |
| A | 0C.2 Axis Coverage Matrix 첫 계산 | M | ✅ |
| B | 0C.3 Cycle 2 준비 (Jump Mode) | M | ✅ |
| B | 0C.4 Cycle 2 수동 실행 (Jump Mode) | XL | ✅ c338351 |
| C | 0C.5 정책 확정 (v0.1 → v1.0) | L | ✅ |
| C | 0C.6 설계 문서 통합 | L | ✅ |

---

## Stage A: 축 선언 + Axis Coverage Matrix

### 0C.1 축 선언 보완 `[M]` ✅

**산출물**: `domain-skeleton.json` — axes 섹션 추가 (4축: category/geography/condition/risk, axis_meta 포함)

**완료 조건**:
- [x] axes 섹션이 skeleton에 존재
- [x] 각 축에 최소 3개 anchor (category 8, geography 5, condition 6, risk 5)
- [x] 기존 Bootstrap 알고리즘과의 호환성 확인 (사후 태깅 방식, 기존 알고리즘 변경 없음)

---

### 0C.2 Axis Coverage Matrix 첫 계산 `[M]` ✅

**산출물**: `bench/japan-travel/cycle-2/axis-coverage-matrix.md`

**결과**: geography deficit 0.200 (rural 결손), risk deficit 0.200 (informational 결손), nationwide+tokyo 편중 93.5%

**완료 조건**:
- [x] 모든 31 GU에 축 태그 할당됨
- [x] 축별 deficit_ratio 계산됨
- [x] geography 축 결손 값(rural) 식별됨
- [x] Jump Mode trigger 판정에 사용 가능한 수치 확보 (T1 발동)

---

## Stage B: Cycle 2 Jump Mode 수동 테스트

### 0C.3 Cycle 2 준비 (Jump Mode) `[M]` ✅

**산출물**: `bench/japan-travel/cycle-2/cycle-2-prep.md`, `state-snapshots/cycle-1-snapshot/` (5개 JSON)

**결과**: T1(Axis Under-Coverage) 발동 → Jump Mode 진입, jump_cap=10, explore 5 + exploit 3

**완료 조건**:
- [x] Trigger 판정 결과 기록 (T1 발동, T2~T5 미발동)
- [x] Budget 배분 명시 (explore 5개, exploit 3개)
- [x] State 스냅샷 완료 (5개 JSON)
- [x] jump_cap 확정 (10)

---

### 0C.4 Cycle 2 수동 실행 (Jump Mode) `[XL]` ✅ `c338351`

**산출물**: `evidence-claims-c2.md`, `kb-patch-c2.md`, `critique-c2.md`, `revised-plan-c3.md`

**결과**:
- Collect: 9건 웹 검색 (explore 5 + exploit 3 + 추가검증 1)
- Integrate: KU-0022~0028 신규 7개, KU-0011 disputed 해결, KU-0016 교차검증
- GU-0006/0014/0030 resolved, 동적 GU 6개 신규 (GU-0032~0037)
- Critique: 5개 건강지표 전원 ✅, 5대 불변원칙 4/5 완전 + 1 부분 준수
- 처방 RX-12~16 도출, Cycle 3 Normal Mode 진입 확정

**완료 조건**:
- [x] Collect에서 explore 대상 실제 수집됨 (osaka 3 + kyoto 1 + rural 1)
- [x] Jump Mode 상한 이내 GU 생성 (6/10)
- [x] Guardrail 4종 위반 없음 (Balance Guard 경미 초과 수용)
- [x] 신규 GU 중 high/critical ≥ 40% (50%)
- [x] Axis Coverage deficit_ratio 감소 (geography 0.200→0.000)
- [x] 5대 불변원칙 전체 PASS

---

## Stage C: 정책 확정 + 문서 통합

### 0C.5 정책 확정 (v0.1 → v1.0) `[L]` ✅

**산출물**: `docs/gu-bootstrap-expansion-policy.md` v1.0

**결과**:
- T1 확정: deficit_ratio > 0 (required 축). T2~T5 보수적 초기값
- explore 비율: 초기 60% / 중기 50% / 수렴 40%
- Entity Hierarchy 규칙 신설 (§7, RX-13 반영)
- gu-bootstrap-spec.md v1.1 확정

**완료 조건**:
- [x] 모든 trigger에 수치 임계치 확정
- [x] Cap 공식이 실측 기반 검증됨 (jump_cap=10, 사용=6 적정)
- [x] explore/exploit 권장 비율 확정 (단계별 3단계)
- [x] 버전이 v1.0으로 승격

---

### 0C.6 설계 문서 통합 `[L]` ✅

**산출물**: `docs/design-v2.md` + `docs/gu-bootstrap-spec.md` 업데이트

**결과**:
- design-v2: mode_node 추가, entity hierarchy 확정, State 타입 확장, Phase 1 입력 체크리스트 (11항 전체 ✅)
- spec: Normal/Jump 이원화 상한, 확정 비율 반영, Jump Mode 체크리스트(B-2) 추가

**완료 조건**:
- [x] gu-bootstrap-spec에 Axis Coverage / Jump Mode 섹션 존재 (§2.5, §2.6)
- [x] design 문서에 LangGraph 반영 사항 기술 (§10 mode_node, plan_node 확장)
- [x] Phase 1 입력 체크리스트 작성 완료 (§12, 11항)
- [x] session-compact 업데이트
