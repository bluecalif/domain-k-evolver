# Phase 0C Tasks — GU 전략 재검토
> Last Updated: 2026-03-04
> Status: Not Started

## Summary

| Stage | Task | Size | Status |
|-------|------|------|--------|
| A | 0C.1 축 선언 보완 | M | ⬜ |
| A | 0C.2 Axis Coverage Matrix 첫 계산 | M | ⬜ |
| B | 0C.3 Cycle 2 준비 (Jump Mode) | M | ⬜ |
| B | 0C.4 Cycle 2 수동 실행 (Jump Mode) | XL | ⬜ |
| C | 0C.5 정책 확정 (v0.1 → v1.0) | L | ⬜ |
| C | 0C.6 설계 문서 통합 | L | ⬜ |

---

## Stage A: 축 선언 + Axis Coverage Matrix

### 0C.1 축 선언 보완 `[M]`

**목적**: domain-skeleton에 category 외 축을 명시적으로 선언한다.

**작업 내용**:
1. `bench/japan-travel/state/domain-skeleton.json`에 `axes` 섹션 추가
2. 축 정의:
   - `category`: 기존 8개 카테고리 (변경 없음)
   - `geography`: tokyo, osaka, kyoto, rural, nationwide
   - `condition`: peak-season, off-season, weekday, weekend, online, in-person
   - `risk`: safety, financial, policy, convenience, informational (기존 risk_level 재활용)
3. 각 축별 anchor 확정 (context.md §3 초안 기반)
4. 기존 Category×Field 매트릭스와 다축 매트릭스의 관계 문서화

**산출물**: 수정된 `domain-skeleton.json`

**완료 조건**:
- [ ] axes 섹션이 skeleton에 존재
- [ ] 각 축에 최소 3개 anchor
- [ ] 기존 Bootstrap 알고리즘과의 호환성 확인

---

### 0C.2 Axis Coverage Matrix 첫 계산 `[M]`

**목적**: 현재 31 GU를 다축으로 분류하고 결손을 정량화한다.

**작업 내용**:
1. 31 GU 각각에 축 태그 할당:
   - `geography`: entity_key와 KU 내용 기반 추론 (대부분 nationwide 예상)
   - `condition`: 해당되는 경우만 (선택적)
   - `risk`: 기존 `risk_level` 필드 활용
   - `category`: 기존 entity_key에서 추출
2. 축별 coverage 계산:
   ```
   coverage[axis][value] = {
     open: count(GU where tag == value and status == 'open'),
     resolved: count(GU where tag == value and status == 'resolved'),
     critical_open: count(GU where tag == value and expected_utility in ['critical', 'high'] and status == 'open'),
     evidence_density: mean(len(KU.evidence_links) for KU in value scope)
   }
   ```
3. deficit_ratio 계산: `count(values where open + resolved == 0) / count(all values)`
4. 결손 축/값 목록 도출

**산출물**: `bench/japan-travel/cycle-2/axis-coverage-matrix.md`

**완료 조건**:
- [ ] 모든 GU에 축 태그 할당됨
- [ ] 축별 deficit_ratio 계산됨
- [ ] geography 축의 결손 값(osaka, kyoto, rural)이 식별됨
- [ ] Jump Mode trigger 판정에 사용 가능한 수치 확보

---

## Stage B: Cycle 2 Jump Mode 수동 테스트

### 0C.3 Cycle 2 준비 (Jump Mode) `[M]`

**목적**: Axis Coverage Matrix를 기반으로 Jump Mode 진입 여부를 판정하고 Cycle 2를 구성한다.

**작업 내용**:
1. Jump Mode trigger 판정:
   - Axis Under-Coverage: geography deficit_ratio > 임계치? → 예상 YES
   - Spillover: Cycle 1에서 Gap Map 외 슬롯 참조? → 확인
   - High-Risk Blindspot: safety/financial 단일출처 KU? → 확인
   - Prescription: RX-07~11 중 구조 보강 처방? → 확인
   - Domain Shift: 신규 entity cluster? → 확인
2. explore/exploit budget 배분:
   - explore: 신규 축 영역 GU (geography 등)
   - exploit: 기존 open GU 해결 (revised-plan-c2 기반)
   - 비율 초안: explore 60% / exploit 40% (초기 Cycle)
3. jump_cap 계산: `min(max(10, ceil(16 * 0.6)), 30)` = 10
4. State 스냅샷 → `bench/japan-travel/state-snapshots/cycle-1-snapshot/`
5. Cycle 2 디렉토리 생성 → `bench/japan-travel/cycle-2/`

**산출물**: `bench/japan-travel/cycle-2/cycle-2-prep.md`

**완료 조건**:
- [ ] Trigger 판정 결과 기록 (어떤 trigger가 발동/미발동)
- [ ] Budget 배분 명시 (explore N개, exploit M개)
- [ ] State 스냅샷 완료
- [ ] jump_cap 확정

---

### 0C.4 Cycle 2 수동 실행 (Jump Mode) `[XL]`

**목적**: Jump Mode로 전체 Inner Loop를 실행하여 trigger/guardrail 작동을 검증한다.

**작업 내용**:
1. **Collect**: explore budget에 따라 신규 축 영역 포함 수집
   - geography 축: osaka, kyoto 관련 정보 수집
   - 기존 revised-plan-c2의 exploit 대상도 수집
2. **Integrate**: Claims → KB Patch 적용
   - 동적 GU 발견: Jump Mode 상한(jump_cap) 적용
   - Guardrail 체크: Quality, Cost, Balance, Convergence
3. **Critique**: Structural Deficit Analysis 포함
   - Axis Coverage Matrix 재계산 (Cycle 2 후)
   - deficit_ratio 변화 확인
   - 5대 불변원칙 검증
4. **Plan Modify**: explore/exploit budget 명시
   - trigger 재평가 (다음 Cycle도 Jump 필요?)
   - Convergence Guard 확인 (연속 2 Cycle jump 시 HITL)

**산출물**: Cycle 2 Deliverables (`evidence-claims-c2.md`, `kb-patch-c2.md`, `critique-c2.md`, `revised-plan-c3.md`)

**완료 조건**:
- [ ] Collect에서 explore 대상이 실제로 수집됨
- [ ] Jump Mode 상한 이내 GU 생성
- [ ] Guardrail 4종 위반 없음
- [ ] 신규 GU 중 high/critical ≥ 40%
- [ ] Axis Coverage deficit_ratio가 감소함
- [ ] 5대 불변원칙 전체 PASS

---

## Stage C: 정책 확정 + 문서 통합

### 0C.5 정책 확정 (v0.1 → v1.0) `[L]`

**목적**: Cycle 2 실측 결과를 반영하여 expansion-policy를 확정한다.

**작업 내용**:
1. Trigger별 발동/미발동 실측 → 임계치 확정
   - Axis Under-Coverage: deficit_ratio > X% → Jump 진입
   - Spillover: 연속 N건 → Jump 진입
   - High-Risk Blindspot: M건 이상 → Jump 진입
2. Cap 공식 실측 검증:
   - Base Mode: `min(max(4, ceil(open * 0.2)), 12)` 적정성
   - Jump Mode: `min(max(10, ceil(open * 0.6)), 30)` 적정성
3. explore/exploit 비율 확정 (Cycle 단계별 권장)
4. Guardrail 수치 확정 (Balance Guard 50% 등)
5. expansion-policy.md v0.1 → v1.0 개정

**산출물**: 수정된 `docs/gu-bootstrap-expansion-policy.md` (v1.0)

**완료 조건**:
- [ ] 모든 trigger에 수치 임계치 확정
- [ ] Cap 공식이 실측 기반 검증됨
- [ ] explore/exploit 권장 비율 확정
- [ ] 버전이 v1.0으로 승격

---

### 0C.6 설계 문서 통합 `[L]`

**목적**: 확정된 정책을 기존 설계 문서에 통합하여 Phase 1 입력으로 준비한다.

**작업 내용**:
1. `docs/gu-bootstrap-spec.md` 업데이트:
   - §2 동적 GU 발견 규칙에 Jump Mode 통합
   - §4 Scope 제어에 Axis Coverage Matrix 반영
   - §6 검증 체크리스트에 Jump Mode 항목 추가
2. `docs/design-v2.md` 업데이트 (또는 design-v3):
   - LangGraph 노드 설계에 Jump Mode 분기 반영
   - plan_node에 explore/exploit budget 로직
   - critique_node에 Structural Deficit Analysis 로직
3. Phase 1 입력 조건 최종 정리:
   - 어떤 문서/데이터가 Phase 1에 필요한지 목록화
   - LangGraph 자동화 시 구현해야 할 Jump Mode 로직 명세

**산출물**: 수정된 spec/design 문서 + Phase 1 입력 체크리스트

**완료 조건**:
- [ ] gu-bootstrap-spec에 Axis Coverage / Jump Mode 섹션 존재
- [ ] design 문서에 LangGraph 반영 사항 기술
- [ ] Phase 1 입력 체크리스트 작성 완료
- [ ] session-compact 업데이트
