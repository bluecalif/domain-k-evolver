# Phase 0C Plan — GU 전략 재검토
> Last Updated: 2026-03-04
> Status: Not Started

## 1. Summary (개요)

Phase 0B 완료 후 Phase 1(LangGraph 자동화) 진입 전에 GU 확장 전략의 구조적 한계를 해결한다.

**문제 인식** (gu-bootstrap-expansion-policy.md v0.1):
1. **국소 최적화 편향** — 기존 open GU 주변만 반복 탐색, 미표면화 축 누락
2. **초기 스켈레톤 불완전성** — category 축만 관리, geography/condition/risk 미추적
3. **상한 경직성** — 고정 20% 상한은 구조 결손 회복에 너무 느림

**목표**: Axis Coverage Matrix + Quantum Jump Mode를 수동 테스트하여 정책 v1.0을 확정하고, Phase 1 자동화에 투입 가능한 명세를 만든다.

---

## 2. 입력

| 자산 | 위치 | 용도 |
|------|------|------|
| Cycle 1 State | `bench/japan-travel/state/` | 현재 31 GU, 21 KU 기준선 |
| expansion-policy v0.1 | `docs/gu-bootstrap-expansion-policy.md` | 제안된 정책 — 검증 대상 |
| revised-plan-c2.md | `bench/japan-travel/cycle-1/revised-plan-c2.md` | Cycle 2 수집 계획 (처방 RX-07~11) |
| gu-bootstrap-spec.md | `docs/gu-bootstrap-spec.md` | 현행 Bootstrap/동적 발견 명세 |
| design-v2.md | `docs/design-v2.md` | 전체 설계 문서 |

---

## 3. 산출물

| 산출물 | 형태 | 설명 |
|--------|------|------|
| 보완된 domain-skeleton.json | JSON | geography/condition/risk 축 명시 추가 |
| Axis Coverage Matrix | MD | 31 GU의 다축 분류 + 결손 정량화 |
| Cycle 2 Deliverables | MD × 5 | Jump Mode 수동 실행 결과 |
| expansion-policy v1.0 | MD | 수치 임계치 확정, trigger 조건 확정 |
| gu-bootstrap-spec v1.1 | MD | Axis Coverage / Jump Mode 섹션 흡수 |
| design-v2 업데이트 (또는 v3) | MD | 정책 통합 반영 |

---

## 4. Stage 구성

### Stage A: 축 선언 + Axis Coverage Matrix (Task 0C.1~0C.2)

**목적**: 현재 gap-map의 다축 커버리지를 처음으로 정량화한다.

1. **0C.1 축 선언 보완**
   - domain-skeleton.json에 `axes` 필드 추가
   - 축 정의: category (기존), geography, condition, risk
   - 각 축별 anchor 값 정의 (예: geography → tokyo, osaka, kyoto, rural)
   - 기존 Category×Field 매트릭스와의 관계 정리

2. **0C.2 Axis Coverage Matrix 첫 계산**
   - 31 GU 각각에 축 태그 할당 (geography, condition, risk)
   - 축별 coverage 계산: `{open, resolved, critical_open, evidence_density}`
   - 결손 축 식별 (예: geography=osaka → GU 0개)
   - Matrix를 Cycle 2 Jump Mode trigger 판정의 입력으로 사용

### Stage B: Cycle 2 Jump Mode 수동 테스트 (Task 0C.3~0C.4)

**목적**: Quantum Jump를 실전에서 한 번 돌려보고, trigger/guardrail이 작동하는지 검증한다.

1. **0C.3 Cycle 2 준비**
   - Axis Coverage Matrix 기반 Jump Mode trigger 판정
   - explore/exploit budget 배분 (단위: GU 개수)
   - jump_cap 계산: `min(max(10, ceil(open * 0.6)), 30)`
   - State 스냅샷 (Cycle 1 → cycle-1-snapshot)

2. **0C.4 Cycle 2 수동 실행 (Jump Mode)**
   - Collect: explore budget으로 신규 축 GU 포함 수집
   - Integrate: Claims → KB Patch, 동적 GU 발견 (Jump Mode 상한 적용)
   - Critique: Structural Deficit Analysis 포함
   - Plan Modify: explore/exploit budget 명시, trigger 재평가

### Stage C: 정책 확정 + 문서 통합 (Task 0C.5~0C.6)

**목적**: 실전 검증 결과를 반영하여 정책을 확정하고 설계 문서에 통합한다.

1. **0C.5 정책 확정**
   - Cycle 2 결과 기반으로 수치 임계치 확정
   - Trigger 조건별 발동 여부 실측 → 임계치 조정
   - Guardrail 작동 여부 검증 → 미작동 항목 보완
   - expansion-policy v0.1 → v1.0 승격

2. **0C.6 설계 문서 통합**
   - gu-bootstrap-spec.md에 Axis Coverage Matrix 계산 로직, Jump Mode 규칙 흡수
   - design-v2.md 업데이트 (또는 design-v3 작성)
   - Phase 1 LangGraph 설계에 반영 사항 정리

---

## 5. 완료 조건

- [ ] domain-skeleton.json에 `axes` 필드가 명시되어 있다
- [ ] Axis Coverage Matrix가 계산되고 결손 축이 식별되었다
- [ ] Cycle 2가 Jump Mode로 실행되었다
- [ ] Jump Mode trigger가 최소 1개 발동되었다
- [ ] Guardrail 4개(Quality/Cost/Balance/Convergence) 중 위반 없이 완료되었다
- [ ] expansion-policy v1.0이 수치 임계치와 함께 확정되었다
- [ ] gu-bootstrap-spec에 Axis Coverage / Jump Mode가 통합되었다
- [ ] Phase 1 입력 조건이 이 산출물로 충족된다

---

## 6. 리스크

| 리스크 | 심각도 | 완화 |
|--------|--------|------|
| Cycle 2 Jump Mode에서 GU 폭발 | Medium | Guardrail 4개 엄격 적용, HITL 개입 |
| 축 정의가 과도하게 세밀 → 슬롯 폭발 | Medium | anchor 수를 축당 3~5개로 제한 |
| Jump Mode trigger가 하나도 발동 안 됨 | Low | Axis Coverage Matrix 결손이 이미 확인됨 (geography 0) |
| Cycle 2 수동 실행 비용 (시간) | Medium | 핵심 검증 포인트에 집중, 전체 Gap 해결 불필요 |
