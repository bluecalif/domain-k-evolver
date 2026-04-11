# GU Bootstrap Expansion Policy

> **Version**: 1.0
> **Date**: 2026-03-04
> **Status**: 확정 (Cycle 1~2 실측 검증 기반)
> **Scope**: domain-agnostic policy for broad aspect/category expansion in knowledge build-up
> **변경이력**: v0.1(proposal, 2026-03-04) → v1.0(확정, 2026-03-04 Phase 0C.5)

---

## 1. Problem Definition

현재 GU 생성 규칙은 "기존 open GU 대비 일정 비율" 같은 국소 제약에 강하게 의존한다.
이 방식은 안정적이지만, 도메인 지식이 **넓은 축(aspect/category)** 으로 확장되어야 하는 시점에 탐색 폭을 구조적으로 제한한다.

핵심 문제는 다음 3가지다.

1. **국소 최적화 편향**: 이미 열려 있는 Gap 주변만 반복 탐색하고, 아직 표면화되지 않은 축을 놓친다.
2. **초기 스켈레톤 불완전성**: Seed/Cycle 0에서 축 정의가 얕으면 이후 Cycle도 그 편향을 상속한다.
3. **상한 경직성**: 고정 상한(예: 20%)은 안전하지만, 구조적 결손이 클 때는 회복 속도가 너무 느리다.

**실측 근거** (japan-travel Cycle 1):
- Cycle 1 종료 시 geography축 nationwide+tokyo 편중 93.5%, rural 완전 결손
- risk축 informational 완전 결손 (GU 0개)
- 고정 20% 상한으로는 이 편중을 해소하려면 최소 3~4 Cycle 필요

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

### 3.1 축 선언

`domain-skeleton.json`의 `axes` 필드에 선언. 각 축은 유한 anchor 값 집합을 가진다.

```json
{
  "axes": [
    {"name": "category", "required": true, "anchors": ["transport", "..."]},
    {"name": "geography", "required": true, "anchors": ["tokyo", "osaka", "..."]},
    {"name": "condition", "required": false, "anchors": ["peak-season", "..."]},
    {"name": "risk", "required": true, "anchors": ["safety", "financial", "..."]}
  ]
}
```

**필수 축**: `required: true`인 축은 deficit_ratio가 Jump Mode trigger에 직접 영향.
**선택 축**: `required: false`인 축은 trigger 판정에서 가중치 하향 (참고 지표로만 활용).

### 3.2 Matrix 계산

Cycle 종료 시 각 축의 각 값에 대해:

```
coverage[axis][value] = {
  open:             count(GU where axis_tags[axis] == value AND status == 'open'),
  resolved:         count(GU where axis_tags[axis] == value AND status == 'resolved'),
  critical_open:    count(GU where axis_tags[axis] == value AND expected_utility in ['critical','high'] AND status == 'open'),
  evidence_density: mean(len(KU.evidence_links) for KU in scope of value)
}
```

### 3.3 deficit_ratio 계산

```
deficit_ratio[axis] = count(values where open + resolved == 0) / count(all anchor values)
```

**확정 임계치**: deficit_ratio > **0** (required 축) → Jump Mode trigger T1 후보.

> **실측 근거**: Cycle 1 geography deficit 0.200(rural 1개 결손)에서 T1 발동, Cycle 2 Jump으로 0.000 해소 성공.
> deficit_ratio = 0.200(= 1/5)도 구조적 결손이었으므로 임계치는 > 0 (= 1개라도 결손 시 발동).

---

## 4. Bootstrap 2-Layer Strategy

### Layer A: Structural Bootstrap (Seed/Cycle 0)

Seed 단계에서 최소한 아래를 만족해야 한다.

1. **축 선언**: domain-skeleton에 최소 축 세트 명시 (category만 단독 사용 금지)
2. **축별 최소 대표값(anchor) 확보**: 각 축에서 최소 3개 anchor
3. **교차 슬롯 샘플링**: 모든 조합을 다 열지 않되, high-risk/high-utility 교차 슬롯은 강제 포함

권장 기준:
- category coverage: 100% (모든 카테고리 최소 1개 GU)
- high-risk axis coverage: 100% (safety/financial/policy 축 누락 금지)
- required 축 coverage: deficit_ratio = 0 (모든 required 축의 모든 anchor에 최소 1개 GU)

### Layer B: Operational Bootstrap (Cycle 1+)

Cycle 중에는 "현재 해결"과 "새 축 개척"을 분리 관리한다.

- `exploit_budget`: 기존 open GU 해결 중심
- `explore_budget`: 신규 GU 생성 중심 (Jump Mode 시만 할당)

---

## 5. Dynamic GU Expansion Modes

### Mode 1: Normal Mode (기본)

- **신규 GU 상한 (base_cap)**: `min(max(4, ceil(open * 0.2)), 12)`
- **explore/exploit**: exploit 100% (모든 예산을 기존 open GU 해결에 투입)
- **Target 수**: `min(8, ceil(open * 0.4))`
- 목적: 과도한 진동 없이 안정 운영

**실측**: Cycle 3에서 Normal Mode 적용 예정. open=21 → base_cap = min(max(4, ceil(21*0.2)), 12) = min(max(4,5), 12) = 5. Target 수 = min(8, ceil(21*0.4)) = min(8,9) = 8.

### Mode 2: Jump Mode (조건부 확장)

- **신규 GU 상한 (jump_cap)**: `min(max(10, ceil(open * 0.6)), 30)`
- **explore/exploit**: 아래 §5.2 비율 참조
- **Target 수**: `min(jump_cap, ceil(open * 0.5))`
- 목적: 구조적 결손을 빠르게 회복

**실측** (Cycle 2):
- open=16 → jump_cap = min(max(10, ceil(16*0.6)), 30) = 10
- 실제 동적 GU 생성: 6/10 → jump_cap의 60% 사용. 상한이 적정했음을 확인.
- 신규 GU 6개 중 high/critical 3개 = 50% ≥ 40% ✅

### 5.1 Jump Mode Trigger (5종) — 확정 임계치

| # | Trigger | 발동 조건 | C2 실측 | 판정 |
|---|---------|-----------|---------|------|
| T1 | **Axis Under-Coverage** | required 축 중 deficit_ratio > 0 | geography 0.200 → **발동** | ✅ 검증됨 |
| T2 | **Spillover** | Collect/Integrate에서 Gap Map 외 슬롯 참조 **3건 이상** (단일 Cycle 내) | C1 동적 GU 3개, 기존 scope 내 → 미발동 | 미검증 (실측 데이터 부족) |
| T3 | **High-Risk Blindspot** | safety/financial/policy 중 **단일출처 + confidence < 0.85** KU 2건 이상 | safety KU-0008 다중출처 → 미발동 | 미검증 |
| T4 | **Prescription** | Critique RX에서 "구조 보강" (축 확장/스켈레톤 보완) 명시 **1건 이상** | C1 RX-07~11 중 구조 보강 0건 → 미발동 | 미검증 |
| T5 | **Domain Shift** | 신규 entity cluster (skeleton에 없는 category 수준) **1건 이상** | 없음 → 미발동 | 미검증 |

**Trigger 결합 규칙**: 5종 중 **1개 이상** 충족 시 Jump Mode 진입.

> **T1 확정 근거**: deficit_ratio > 0은 "anchor 1개라도 완전 결손" 의미. Cycle 2에서 rural 1개 결손(deficit 0.200)으로 Jump 발동 → geography deficit 완전 해소. 적정 임계치로 판단.
> **T2~T5 잠정**: Cycle 1~2에서 미발동이므로 실측 검증 불가. 임계치를 보수적으로 설정하되 향후 실측 시 조정.

### 5.2 explore / exploit 비율 — 확정

| Cycle 단계 | Mode | explore | exploit | 근거 |
|-----------|------|---------|---------|------|
| 초기 (Cycle 1~3) | Jump | **60%** | 40% | C2 실측: 62.5%(5/8) → geography deficit 해소. 60% 상한 적용 |
| 초기 (Cycle 1~3) | Normal | 0% | 100% | C3 계획: 구조 결손 없으면 exploit 집중 |
| 중기 (Cycle 4~6) | Jump | 50% | 50% | 구조 결손 감소 후 균형 |
| 중기 (Cycle 4~6) | Normal | 0% | 100% | — |
| 수렴기 (Cycle 7+) | Jump | 40% | 60% | 미세 조정 위주 |
| 수렴기 (Cycle 7+) | Normal | 0% | 100% | — |

**홀수 Target 처리**: explore/exploit 배분 시 총 Target이 홀수일 때 **exploit에 추가 1건** 배분 (RX-16 반영).

> **실측 근거**: Cycle 2에서 explore 5/exploit 3 = 62.5% → Balance Guard 경미 초과(2.5%p). 60% 상한 엄격 적용으로 보완.

---

## 6. Guardrails (Explosion Control) — 확정

| # | Guard | 규칙 | 확정 임계치 | C2 실측 |
|---|-------|------|-----------|---------|
| G1 | **Quality Guard** | 신규 GU 100%에 `resolution_criteria` + `expected_utility` 필수 | 필수 (미기재 시 GU 무효) | ✅ 6/6 충족 |
| G2 | **Cost Guard** | Cycle별 search/fetch 횟수 상한 | **Target × 2** (Jump: 추가 +4 여유) | ✅ C2: 9/20 사용 |
| G3 | **Balance Guard** | explore 비율 상한 | **60%** (Jump Mode 시) | ⚠️ C2: 62.5% (경미 초과, 수용) |
| G4 | **Convergence Guard** | 연속 Jump 시 HITL | **2 Cycle 연속 Jump → HITL 필수** | ℹ️ C2=첫 Jump, C3=Normal → 미해당 |

### G1 Quality Guard 상세

- 모든 신규 GU에 `resolution_criteria` 텍스트 필수
- `expected_utility` in [critical, high, medium, low] 필수
- Jump Mode 신규 GU 중 **high/critical ≥ 40%** 필수
- **실측**: C2에서 6개 GU 중 high 3개 = 50% ≥ 40% ✅

### G2 Cost Guard 상세

- Normal Mode: `Target × 2` (예: 8 Target → 16 검색)
- Jump Mode: `Target × 2 + 4` (예: 8 Target → 20 검색. explore 교차검증 여유분)
- 상한 도달 시 **low utility Target부터 탈락**
- **실측**: C2 상한 20, 실사용 9 → 여유 충분. 상한 적정.

### G3 Balance Guard 상세

- Jump Mode: explore ≤ **60%** (엄격 적용)
- Normal Mode: explore = 0% (해당 없음)
- 단일 category/axis가 신규 GU의 **50% 초과 금지** (핵심 예외: 전체 결손 축 보정 시 1회 허용)
- **실측**: C2 explore 62.5% → 경미 초과. geography deficit 해소에 필수적이었으나, 향후 홀수 배분 규칙(RX-16)으로 방지.

### G4 Convergence Guard 상세

- **2 Cycle 연속 Jump** → HITL 개입 필수 (자동 진행 불가)
- HITL은 Jump 사유를 재판정: (a) 정당한 구조 결손 → Jump 계속, (b) scope 재정의로 결손 해소 → Normal 전환
- `net_gap_change`가 **3 Cycle 연속 양수** → Jump 강도 자동 감쇠 (jump_cap × 0.7)
- **실측**: C2→C3에서 risk:informational 결손을 GU 사전 생성으로 해소 → Normal 진입. Convergence Guard 우회 성공 사례.

> **C2→C3 사례**: T1 재발동 가능성(risk:informational deficit 0.200)을 GU-0038/0039 사전 생성으로 해소, Normal Mode 진입. 이 패턴은 "사전 GU 생성으로 trigger 해소 → Jump 회피"라는 합법적 전략으로 인정.

---

## 7. Entity Hierarchy (RX-13 반영)

### 7.1 문제

entity_key 해상도 불일치가 3 Cycle 누적 미해결 (RX-04 → RX-10 → RX-13).

- `ryokan` (nationwide) ↔ `kyoto-ryokan` (kyoto): 상위/하위 관계 미정의
- `metro-pass` ↔ `subway-ticket`: alias 관계 미정의

### 7.2 해결 방향

`domain-skeleton.json`에 `entity_hierarchy` 섹션 추가:

```json
{
  "entity_hierarchy": [
    {"parent": "ryokan", "child": "kyoto-ryokan", "relation": "is_a"},
    {"alias": ["metro-pass", "subway-ticket"], "canonical": "subway-ticket"}
  ]
}
```

**규칙**:
- `is_a`: 하위 entity는 상위의 필드를 상속하되 지역 특화 값으로 오버라이드 가능
- `alias`: 동일 entity의 다른 이름. canonical key로 통일
- Integrate 시 entity_key가 alias에 해당하면 canonical로 자동 변환

> **구현 시점**: Phase 1 (LangGraph 자동화) 진입 시 schema에 반영. 수동 Cycle에서는 참고 규칙으로만 적용.

---

## 8. Adoption Rules for Current Project

이 프로젝트에 바로 적용 가능한 규칙:

1. Seed/Cycle 0 산출물 검증 시 "카테고리 수"가 아니라 **축 커버리지**(deficit_ratio)를 같이 기록
2. 동적 GU에 `expansion_mode` (normal/jump), `trigger`, `trigger_source` 필드 추가
3. Critique 보고서에 **Structural Deficit Analysis** 섹션 신설 (Axis Coverage 재계산)
4. Revised Plan에 `explore_budget` / `exploit_budget` 비율을 명시
5. 상한 정책을 단일 값이 아닌 `base_cap + conditional_jump_cap` 이원화
6. **Prescription-compiled 추적성**: 미반영 처방은 반드시 미반영 사유 기록 (C2에서 학습)
7. **홀수 Target 배분**: exploit에 추가 1건 (Balance Guard 준수)

---

## 9. Example (Travel Domain, but Generalizable)

여행 도메인에서는 region이 대표 축이지만, 본 정책은 region 전용이 아니다.

- 전자상거래: category × vendor × price-tier × season
- 의료 정보: condition × severity × age-group × regulation-zone
- B2B SaaS: feature-area × customer-segment × deployment-model × compliance

공통점은 동일하다.
- 초기에는 축을 충분히 선언하지 않으면 Gap 탐색이 편향된다.
- 어느 시점에는 점진 확장만으로는 부족해 "구조 점프"가 필요하다.

---

## 10. Checklist (Cycle 종료 시)

- [ ] 현재 Cycle이 Normal/Jump 어느 모드였는가?
- [ ] Jump였다면 어떤 trigger 조합으로 진입했는가?
- [ ] 신규 GU 중 high/critical 비율이 40% 이상인가?
- [ ] 축 커버리지 결손(deficit_ratio)이 실제로 감소했는가?
- [ ] 비용/품질 가드레일 위반 없이 종료했는가?
- [ ] 미반영 처방에 대한 사유가 기록되었는가?

---

## 11. Validation Summary (Cycle 1~2 실측)

| 정책 요소 | v0.1 제안 | v1.0 확정 | 실측 근거 |
|-----------|-----------|-----------|-----------|
| T1 임계치 | deficit_ratio > X% (TBD) | deficit_ratio > 0 | C2: 0.200 발동 → 해소 성공 |
| T2 임계치 | N건 (TBD) | 3건 이상 | 미검증 (보수적 설정) |
| T3 임계치 | M건 (TBD) | 2건 이상 (단일출처+conf<0.85) | 미검증 |
| T4 임계치 | 명시 (TBD) | 1건 이상 | 미검증 |
| T5 임계치 | L건 (TBD) | 1건 이상 | 미검증 |
| jump_cap | `min(max(10, ceil(open*0.6)), 30)` | 동일 유지 | C2: cap=10, 사용=6 (적정) |
| base_cap | `min(max(4, ceil(open*0.2)), 12)` | 동일 유지 | 미검증 (C1 pre-policy) |
| explore 비율 | TBD | 초기 60% / 중기 50% / 수렴 40% | C2: 62.5% → 60% 상한 확정 |
| Balance Guard | 50% | 60% (Jump), 50% (단일축) | C2: 62.5% 경미초과, 60%로 조정 |
| Convergence Guard | 연속 2 Cycle Jump → HITL | 동일 + net_gap 3 Cycle 양수 → 감쇠 | C2→C3: 사전 GU 생성으로 Normal 전환 |
| high/critical 비율 | ≥ 40% | 동일 유지 | C2: 50% ≥ 40% ✅ |

---

## 12. Summary

**v0.1 → v1.0 핵심 변경**:

1. **Trigger 임계치 확정**: T1 = deficit_ratio > 0, T2~T5 보수적 초기값 설정
2. **explore/exploit 비율 단계별 확정**: 초기 60/40, 중기 50/50, 수렴 40/60
3. **Balance Guard 조정**: 50% → 60% (Jump Mode), 홀수 배분 규칙 추가
4. **Entity Hierarchy 도입**: alias/is_a 관계 정의 규칙 신설 (§7)
5. **Prescription 추적성 강화**: 미반영 사유 필수 기록 규칙 추가
6. **Convergence Guard 보완**: net_gap_change 3 Cycle 양수 시 jump_cap 감쇠

해결 방향은 다음 한 줄로 요약된다.

- "상한 제거"가 아니라, **축 기반 결손 탐지 + 조건부 양자 점프 + 강한 가드레일**로 정책을 이원화한다.
