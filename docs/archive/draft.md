좋아요. “일본 여행”을 **벤치 도메인**으로만 두고, **도메인-불문(General) 자기확장 지식 Evolver**가 성립하려면 무엇이 핵심인지, 각 단계의 **목표·불변조건·산출물 계약(Deliverable Contract)** 을 더 정교하게 재설계하겠습니다.

아래 설계는 “기술 구현”이 아니라 **딥에이전트가 작동하기 위한 운영/지식 프레임워크**입니다.

---

# 1) Evolver를 ‘지식의 상태 기계(State Machine)’로 정의

Evolver는 결국 다음을 반복합니다:

> **부분적으로만 알려진 세계(Seed + Gaps)** 에서 시작해
> “어떤 지식을 더 가져오면 가치가 큰지”를 계획하고,
> “근거 있는 주장(Claims)”을 수집하고,
> “기존 정리 틀(Ontology/Schema)에 맞춰 통합”하고,
> “실패모드를 비판적으로 평가”해서,
> “다음 수집 전략 자체를 개선”하며 확장한다.

이걸 엄밀하게 만들려면, 시스템이 매 순간 가지는 상태는 최소 아래로 구성됩니다.

### Evolver State (Cycle t의 상태)

* **K**: Knowledge Units (정규화된 지식 단위들)
* **G**: Gaps (결손/불확실/충돌/노후화 슬롯들)
* **P**: Policies (출처 신뢰 priors, 충돌해결 규칙, 신선도 규칙, 품질 루브릭)
* **M**: Metrics (커버리지/근거율/충돌률/신선도 리스크/비용 등)
* **D**: Domain Skeleton (엔티티/관계/필드/캐노니컬 키)

> 사이클은 “문서”를 생산하는 게 아니라, **상태(State)를 업데이트하는 연산**입니다.

---

# 2) 핵심 개념(객체) 정의: “수집→통합→비평”을 자동화하려면 지식의 최소 단위가 필요함

문서/요약 중심으로는 자동 확장이 불가능합니다. 그래서 아래 단위가 **반드시** 있어야 합니다.

## 2.1 Knowledge Unit (KU) = “정규화된 주장”

KU는 *어떤 엔티티의 어떤 필드가 어떤 값이며, 어떤 조건에서 성립하는지*를 가진 원자 단위입니다.

* `entity_key` (캐노니컬 키)
* `field` (예: 운영시간, 규정, 가격, 위치…)
* `value`
* `conditions` (시즌/요일/언어/구매채널/지역 등)
* `observed_at` (확인 시점)
* `validity` (TTL/유효기간 정책)
* `evidence_links[]` (증거 단위들)
* `confidence` (정량/정성)
* `status` (active / disputed / deprecated)

## 2.2 Evidence Unit (EU) = “근거”

* `source_id` (URL/문서/DB)
* `retrieved_at`
* `snippet/location` (근거 위치)
* `source_type` (공식/공공/플랫폼/개인 등)
* `credibility_prior`

## 2.3 Gap Unit (GU) = “확장 대상(학습 과제)”

확장 계획의 입력은 ‘지식’이 아니라 **결손 지도(Gaps)** 입니다.

* `gap_type`: missing / uncertain / conflicting / stale
* `target`: (entity_key, field) 또는 “관계/개념”
* `expected_utility` (채웠을 때 가치)
* `risk_level` (안전/정책/금전 등)
* `resolution_criteria` (어떤 근거면 해결로 인정?)

## 2.4 Patch Unit (PU) = “통합 결과(차분)”

통합은 “새 문서”가 아니라 **KB에 적용 가능한 패치(diff)** 를 만들어야 다음 사이클이 자동화됩니다.

* `adds` / `updates` / `deprecates`
* `conflict_decisions`
* `gap_updates`
* `policy_updates` (필요 시)

---

# 3) Inner Loop를 ‘목표/불변조건/산출물 계약’으로 재정의

사용자가 강조한 “각 단계 핵심 + deliverable 명확”을 **계약 수준**으로 고정합니다.

---

## (S) Seed: “초기 지식”이 아니라 **초기 ‘표현 체계 + 결손 지도’**

### 핵심 목표

* 도메인을 표현할 **골격(Domain Skeleton)** 을 만든다.
* Seed는 “조금 아는 것”이 아니라 “**어떤 방식으로 확장할지**가 가능한 상태”가 목표.

### 불변조건(없으면 다음 단계가 무너짐)

* 캐노니컬 키 규칙(엔티티 식별)이 있어야 함
* 필드/관계(스키마)가 최소라도 정의되어야 함
* Gap이 “명시적으로” 존재해야 함(무엇을 모르는지 시스템이 알아야 계획 가능)

### Deliverable: **Seed Pack v0**

1. Domain Skeleton v0 (엔티티/관계/필드/키 규칙)
2. Seed KUs (아주 소수여도 됨, 단 EU 포함)
3. Gap Map v0 (missing/uncertain/conflict/stale 초기화)
4. Policy Priors v0 (출처 신뢰 priors, TTL 기본값)

---

## (P) Plan: “여행계획”이 아니라 **정보 획득 계획(수집 설계)**

### 핵심 목표

* 다음 Collect에서 “무엇을 어떤 순서로 어떤 출처로 어떤 검증 기준으로” 확보할지 결정
* 즉 **Active Learning / Exploration Planning** 단계

### Plan의 본질: *가치가 큰 Gap을 우선 해결*

Plan은 다음의 최적화 문제에 가깝습니다.

* 최대화: (커버리지 증가 + 리스크 감소 + 충돌 해소) / 비용
* 제약: 시간/검색량/검수 가능량/출처 접근성

### 불변조건

* Plan은 **Gap에 의해 구동**되어야 함(“수집하고 싶은 것”이 아니라 “비어있는/불확실한 것”)
* 각 타깃은 “KU로 귀결될 수 있는 형태”여야 함(그래야 Integration이 가능)
* 종료조건(Stop Rule)이 있어야 무한 수집을 막음

### Deliverable: **Collection Plan (Cycle t)**

1. Target Gaps (우선순위 + 이유 + 기대효용/리스크)
2. Source Strategy (출처군 우선순위 + 대체 출처 + 교차확인 규칙)
3. Query/Discovery Strategy (검색 키워드/질문 프레임/탐색 경로)
4. Acceptance Tests (해결로 인정되는 증거 기준: EU 개수/독립성/신선도)
5. Budget & Stop Rules (수집 상한/중복 상한/품질 미달 시 중단)

---

## (C) Collect: **웹/외부 소스를 스스로 찾고 ‘Claim+Evidence’로 반환**

### 핵심 목표

* 문서가 아니라 **KU로 변환 가능한 Claim 묶음**을 생산
* “검색/발견/교차검증”이 Collect의 필수 내장 기능

### 불변조건

* 모든 Claim은 **EU(근거) 없이는 미완성**으로 취급
* 중요 필드(정책/안전/금전)는 **독립 출처 2개 이상**을 기본 규칙으로(정책은 더 보수적)
* “원문 보존”이 있어야 Integration에서 충돌 해결이 가능

### Deliverable: **Evidence Claim Set**

* Claim 리스트(각 claim은 target KU 형태를 갖춤)
* 각 claim의 EU 번들(출처/스니펫/시점)
* claim 간 중복/상충 후보 태깅(사전 표시)

---

## (I) Integration: **맥락을 가진 입체적 정리(정규화 + 관계화 + 충돌해결)**

### 핵심 목표

* Claim을 Domain Skeleton에 맞춰 KU로 “착지”
* 단순 병합이 아니라 **컨텍스트화(조건/시간/범위)** + **충돌 처리 정책 적용**

### Integration의 3대 연산

1. **Entity Resolution**: 같은 대상 식별/병합(캐노니컬 키 확정)
2. **Normalization**: 값 단위/표현 통일(통화, 시간, 주소, 명칭 등)
3. **Conflict Handling**: 상충 KU를 “조건부 공존/우선순위/보류”로 처리

### 불변조건

* 결과는 “문서”가 아니라 **Patch(diff)** 여야 함
* 상충을 숨기면 Critique가 무력화됨 → 상충은 반드시 구조적으로 남겨야 함
* KU마다 TTL/observed_at가 있어야 신선도 관리 가능

### Deliverable: **KB Patch + Updated Gap Map**

1. Patch Unit (adds/updates/deprecates)
2. Conflict Decisions (채택/조건부/보류/추가수집 요구)
3. Context Layer Updates (조건/범위/버전)
4. Gap Map Update (해결/축소/새로운 gap 생성)

---

## (R) Critique: “좋다/나쁘다”가 아니라 **실패모드 탐지 + 다음 확장 규칙 개선**

### 핵심 목표

* Integration 결과를 비판적으로 평가해 **다음 Cycle의 Plan이 더 똑똑해지도록** 만든다
* 즉 Critique는 “품질검사”가 아니라 **학습 신호(learning signal) 생산기**

### 실패모드 분류(프레임워크 핵심)

* **Epistemic**: 근거 빈약/출처 편향/독립성 부족
* **Temporal**: 신선도 취약/TTL 설계 부적절
* **Structural**: 스키마가 표현 못함(필드/관계 결손)
* **Consistency**: 충돌 다발/해결 불가(정책/규칙 부족)
* **Planning**: Gap 우선순위가 비효율/검색전략 부정확
* **Integration**: 정규화 오류/엔티티 해상도 문제

### 불변조건

* Critique는 반드시 “다음 Plan으로 번역 가능한 처방”을 포함해야 함
* Critique가 정책(P)이나 스키마(D) 변경 필요를 감지하면 **Outer Loop 트리거**를 낼 수 있어야 함

### Deliverable: **Critique Report (Actionable)**

1. Metrics Delta (M의 변화: 근거율↑? 충돌↓?)
2. Failure Modes (빈도/심각도/영향)
3. Root Cause Hypotheses
4. Prescriptions (다음 Plan에 반영할 지시사항)
5. Remodeling Triggers (스키마/정책 개편 필요 신호)

---

## (PM) Plan Modify: Critique를 **구체 수집 계획으로 변환**

### 핵심 목표

* 처방을 “실행 가능한 Collection Plan”으로 바꾸는 **컴파일 단계**
* 특히 Plan Modify는 “다음에 뭘 수집할지”뿐 아니라
  “어떤 규칙으로 수집/검증/통합할지(Policy P)”도 갱신할 수 있어야 함

### 불변조건

* 처방 → 계획 변경의 **추적성(Traceability)** 필수
  (어떤 실패모드가 어떤 계획 변경을 낳았는지)

### Deliverable: **Revised Collection Plan (Cycle t+1) + Policy Update (optional)**

* 변경된 Gap 우선순위/출처전략/검증기준/중단규칙
* 필요 시 P 업데이트(출처 priors, TTL 규칙, 충돌해결 규칙)

---

# 4) “스스로 확장”을 가능하게 하는 5가지 설계 불변원칙(정교화 버전)

이 원칙이 빠지면 루프는 “반복 작업”이 됩니다.

1. **Gap-driven**: Plan은 지식이 아니라 Gap이 구동해야 함
2. **Claim→KU 착지성**: Collect 산출은 Integration이 자동으로 KU로 변환 가능해야 함
3. **Evidence-first**: KU는 EU 없으면 임시 상태로만 존재(품질/신뢰의 기반)
4. **Conflict-preserving**: 충돌은 숨기지 않고 구조적으로 보존(학습과 개선의 연료)
5. **Prescription-compiled**: Critique는 반드시 다음 Plan/Policy 변경으로 컴파일되어야 함(학습 루프)

---

# 5) Human-in-the-loop을 “효율적으로” 배치하는 정교한 방식

사람은 전체를 검수하지 않습니다. **리스크·신규성·충돌·설계변경 지점**에만 투입합니다.

### HITL Gate 설계(권장)

* **Gate A (Plan 승인, 경량/매회)**

  * “이번 사이클 Gap 선택이 합리적이냐”만 본다
* **Gate B (High-risk Claims, 조건부)**

  * 정책/안전/금전 관련 KU는 샘플링이 아니라 “규칙 기반 전수”로 검수 가능
* **Gate C (Conflict Adjudication, 조건부)**

  * 충돌이 일정 임계치 넘거나 핵심 필드면 사람 결정(채택/보류/추가수집)
* **Gate D (Executive Audit, 10 cycles)**

  * Inner Loop 성능을 보고 스키마/정책/루브릭을 리모델링

> 핵심은 “사람이 보는 이유가 명확한 게이트”여야 하고,
> 게이트의 결과도 Policy(P)로 환원되어야 다음부터 자동화가 강화됩니다.

---

# 6) Outer Loop(Executive Audit → Remodeling)가 진짜 ‘진화’를 만든다

Inner Loop는 지식을 늘리지만, **확장 방식 자체**는 Outer Loop에서 진화합니다.

### Executive Audit에서 보는 것(프레임워크 관점)

* Gap이 줄어드는 속도가 둔화되는가? (확장 병목)
* 충돌이 특정 영역에서 반복되는가? (스키마/정책 결함)
* 근거율/독립성/신선도 리스크가 개선되는가? (수집 전략 성능)
* 비용 대비 정보 가치가 떨어지는가? (Plan 최적화 필요)

### Remodeling Design 산출물

* 스키마 개편(D 업데이트): 필드/관계 추가, 키 규칙 개선
* 정책 개편(P 업데이트): 출처 priors, TTL, conflict policy, gate policy
* 평가 루브릭 개편: 실패모드 분류/임계치/샘플링 전략 조정

---

# 7) 일본 여행(벤치 도메인)을 “프레임워크 검증 장치”로 쓰는 법

일본은 도메인이 아니라 **테스트 하네스**입니다.

* 변동 필드(운영시간/가격/규정)에서 TTL이 제대로 작동하는지
* 상충 정보가 많은 영역(패스/환불/규칙)에서 conflict policy가 작동하는지
* 지역/시즌/조건에 따라 조건부 KU(conditions)가 제대로 축적되는지
* Critique가 실제로 Plan을 바꾸는지(추적성)

---

# 8) 최종 요약: “정교화된 전체 그림”

* **State**: (K, G, P, M, D)
* **Inner Loop**:
  Seed Pack → Collection Plan → Evidence Claim Set → KB Patch(+Gap Update) → Critique Report → Revised Plan(+Policy Update) → Next Cycle
* **HITL**: Plan gate + High-risk/Conflict gate + Executive Audit
* **Outer Loop**: Audit → Remodeling(D/P/루브릭) → 더 강한 Inner Loop

---

원하면 다음으로, 위 프레임워크를 바로 운영 가능한 형태로 만들기 위해 **각 Deliverable을 “필수 필드 템플릿”**으로 만들어 드리겠습니다(복붙 가능한 MD).
특히 “Collection Plan 템플릿(수집 설계서)”과 “Critique Report 템플릿(처방 컴파일용)”이 있으면 Evolver가 진짜로 돌아가기 시작합니다.
