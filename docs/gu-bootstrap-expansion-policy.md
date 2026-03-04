# GU Bootstrap Expansion Policy (Generalized)

> Version: 0.1 (proposal)  
> Date: 2026-03-04  
> Scope: domain-agnostic policy for broad aspect/category expansion in knowledge build-up

---

## 1. Problem Definition

현재 GU 생성 규칙은 "기존 open GU 대비 일정 비율" 같은 국소 제약에 강하게 의존한다.  
이 방식은 안정적이지만, 도메인 지식이 **넓은 축(aspect/category)** 으로 확장되어야 하는 시점에 탐색 폭을 구조적으로 제한한다.

핵심 문제는 다음 3가지다.

1. **국소 최적화 편향**: 이미 열려 있는 Gap 주변만 반복 탐색하고, 아직 표면화되지 않은 축을 놓친다.
2. **초기 스켈레톤 불완전성**: Seed/Cycle 0에서 축 정의가 얕으면 이후 Cycle도 그 편향을 상속한다.
3. **상한 경직성**: 고정 상한(예: 20%)은 안전하지만, 구조적 결손이 클 때는 회복 속도가 너무 느리다.

---

## 2. Design Goal

목표는 "무한 확장"이 아니라, 다음을 동시에 달성하는 것이다.

1. **Breadth 확보**: 도메인의 주요 축을 빠르게 드러내기
2. **Depth 확보**: 고효용/고위험 Gap을 우선 해결하기
3. **Control 유지**: 토큰/비용/품질 붕괴 없이 수렴시키기

즉, "천천히만"도 아니고 "무제한 확장"도 아닌, **조건부 대역폭 확장(quantum jump 포함)** 이 필요하다.

---

## 3. Core Model: Axis Coverage Matrix

카테고리(category)만으로는 부족하다. 도메인 지식은 보통 다차원 축으로 구성된다.

권장 축 예시:
- category (무엇에 대한 지식인가)
- entity cluster (어떤 대상군인가)
- condition axis (시간/시즌/채널/사용자 세그먼트 등)
- geography axis (지역성 있는 도메인일 때)
- risk axis (safety/financial/policy/convenience)

각 Cycle에서 Gap Map을 다음 매트릭스로 요약한다.

- `coverage[axis_value] = {open, resolved, critical_open, evidence_density}`

이 매트릭스를 기반으로 "현재 부족한 축"을 정량 판정한다.

---

## 4. Bootstrap 2-Layer Strategy

### Layer A: Structural Bootstrap (Seed/Cycle 0)

Seed 단계에서 최소한 아래를 만족해야 한다.

1. **축 선언**: domain-skeleton에 최소 축 세트 명시 (category만 단독 사용 금지)
2. **축별 최소 대표값(anchor) 확보**: 각 축에서 최소 N개 대표값 선정
3. **교차 슬롯 샘플링**: 모든 조합을 다 열지 않되, high-risk/high-utility 교차 슬롯은 강제 포함

권장 기준:
- category coverage: 100% (모든 카테고리 최소 1개 GU)
- high-risk axis coverage: 100% (safety/financial/policy 축 누락 금지)
- 기타 축 coverage: 최소 60% anchor

### Layer B: Operational Bootstrap (Cycle 1+)

Cycle 중에는 "현재 해결"과 "새 축 개척"을 분리 관리한다.

- `exploit_budget`: 기존 open GU 해결 중심
- `explore_budget`: 신규 GU 생성 중심

초기 Cycle(1~2)은 explore 비중을 높이고, 이후 수렴 단계에서 줄인다.

---

## 5. Dynamic GU Expansion Modes

## Mode 1: Base Mode (기본)

- 신규 GU 상한: `min(max(4, ceil(open * 0.2)), 12)`
- 목적: 과도한 진동 없이 안정 운영

## Mode 2: Quantum Jump Mode (조건부 확장)

다음 중 하나라도 충족하면 해당 Cycle에서 상한을 상향한다.

1. **Axis Under-Coverage Trigger**
- 축 커버리지 미달 (예: 선언된 axis value 중 resolved/open이 0인 비율이 임계치 초과)

2. **Spillover Trigger**
- Collect/Integrate 결과에서 "현재 Gap Map에 없는 슬롯" 참조가 연속적으로 다수 발생

3. **High-Risk Blindspot Trigger**
- safety/financial/policy 계열에서 단일출처/불확실 KU가 임계치 초과

4. **Prescription Trigger**
- Critique 처방(RX)이 구조 보강(축 확장/스켈레톤 보완)을 명시

5. **Domain Shift Trigger**
- 신규 엔티티 클러스터(새 sub-domain) 발견이 누적 임계치 초과

Quantum Jump 상한(권장):
- `jump_cap = min(max(10, ceil(open * 0.6)), 30)`
- 단, 한 Cycle 내 생성분의 최소 40%는 high/critical utility여야 함

---

## 6. Guardrails (Explosion Control)

양자 점프는 허용하되, 반드시 가드레일을 건다.

1. **Quality Guard**
- 신규 GU 100%에 `resolution_criteria` 필수
- high/critical GU는 evidence acquisition plan 필수

2. **Cost Guard**
- Cycle별 search/fetch/LLM budget 상한 유지
- 상한 도달 시 low utility GU 생성 중단

3. **Balance Guard**
- 단일 category/axis가 신규 GU의 50% 초과 금지 (핵심 예외만 허용)

4. **Convergence Guard**
- 연속 2 Cycle jump_mode 진입 시 HITL 검토 필수
- `net_gap_change`가 장기간 양수면 jump 강도 자동 감쇠

---

## 7. Adoption Rules for Current Project

이 프로젝트에 바로 적용 가능한 최소 규칙:

1. Seed/Cycle 0 산출물 검증 시 "카테고리 수"가 아니라 "축 커버리지"를 같이 기록
2. 동적 GU 체크리스트에 `jump_mode_entered`, `trigger_set`, `jump_cap` 필드 추가
3. Critique 보고서에 "구조 결손(Structural Deficit)" 섹션 신설
4. Revised Plan에 `explore_budget` / `exploit_budget` 비율을 명시
5. 상한 정책을 단일 값이 아닌 `base_cap + conditional_jump_cap` 이원화

---

## 8. Example (Travel Domain, but Generalizable)

여행 도메인에서는 region이 대표 축이지만, 본 정책은 region 전용이 아니다.

- 전자상거래: category × vendor × price-tier × season
- 의료 정보: condition × severity × age-group × regulation-zone
- B2B SaaS: feature-area × customer-segment × deployment-model × compliance

공통점은 동일하다.
- 초기에는 축을 충분히 선언하지 않으면 Gap 탐색이 편향된다.
- 어느 시점에는 점진 확장만으로는 부족해 "구조 점프"가 필요하다.

---

## 9. Checklist (Cycle 종료 시)

- [ ] 현재 Cycle이 Base/Jump 어느 모드였는가?
- [ ] Jump였다면 어떤 trigger 조합으로 진입했는가?
- [ ] 신규 GU 중 high/critical 비율이 기준 이상인가?
- [ ] 축 커버리지 결손이 실제로 감소했는가?
- [ ] 비용/품질 가드레일 위반 없이 종료했는가?

---

## 10. Summary

사용자 우려는 타당하다. 문제의 본질은 "region 누락"이 아니라,
**도메인 지식의 광범위한 축 확장 문제를 고정 상한 정책이 흡수하지 못한다**는 점이다.

해결 방향은 다음 한 줄로 요약된다.

- "상한 제거"가 아니라, **축 기반 결손 탐지 + 조건부 양자 점프 + 강한 가드레일**로 정책을 이원화한다.
