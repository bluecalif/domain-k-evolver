# GU Bootstrap 명세 (Seed GU Generator 규약)

> **버전**: 1.1 | **작성일**: 2026-03-04 (Phase 0C.5 — Axis Coverage, Jump Mode 임계치 확정)
> **기반**: `docs/gu-from-scratch.md` 인사이트 → 알고리즘 수준 공식화
> **관련**: `docs/design-v2.md` §7/§10, `schemas/gap-unit.json`

---

## 0. 핵심 명제

1. **GU = "정답 대비 결손"이 아니라 "현재 목적 대비 불충분성"**
   - 도메인 시작 시 완전한 이상형(ideal output image)은 없음
   - GU는 Domain Skeleton(구조적 프레임)의 빈 칸 스캔으로 생성

2. **Bootstrap은 프레임 기반, 운영은 점진 확장**
   - 초기: Category × Field 매트릭스에서 기계적으로 Gap 도출
   - 이후: 해결 과정에서 인접 Gap 발견 → 확장 (무작위가 아닌 우선순위 기반)

3. **완성이 아닌 수렴 조건으로 종료 판정**
   - 정해진 정답 지식지도에 도달하는 것이 아님
   - Metrics 임계치 기반으로 "충분히 건강한" 상태 판정

---

## 1. Bootstrap GU 생성 알고리즘 (5단계)

> **입력**: `domain-skeleton.json`, `knowledge-units.json` (Seed KU), `policies.json`
> **출력**: `gap-map.json` (Bootstrap GU 배열)

### 1단계: Category × Field 적용 매트릭스 구성

`domain-skeleton.json`의 `fields[].categories`로 적용 가능 슬롯을 열거한다.

- `"*"` → 전체 카테고리에 적용
- 명시된 카테고리 목록 → 해당 카테고리에만 적용

**예시 (japan-travel: 8 cat × 11 fields)**

| Field \ Category | transport | accommodation | attraction | dining | regulation | pass-ticket | connectivity | payment |
|---|---|---|---|---|---|---|---|---|
| price | O | O | O | O | O | O | O | O |
| hours | - | - | O | O | - | - | - | - |
| policy | - | - | - | - | O | O | - | - |
| location | - | O | O | O | - | - | - | - |
| duration | O | - | - | - | - | O | - | - |
| eligibility | - | - | - | - | O | O | - | - |
| how_to_use | O | - | - | - | - | - | O | O |
| etiquette | - | O | - | O | - | - | - | - |
| tips | O | O | O | O | O | O | O | O |
| acceptance | - | - | - | - | - | - | - | O |
| where_to_buy | - | - | - | - | - | O | O | - |

→ **적용 가능 슬롯**: 35개 (= 구조적 최대 Gap 공간)

### 2단계: 각 슬롯의 gap_type 판정

슬롯 (category, field) 마다 기존 KU를 조회하여 상태 판정:

| 조건 | gap_type |
|------|----------|
| 해당 슬롯에 active KU 없음 | `missing` |
| active KU 있으나 `confidence < 0.7` | `uncertain` |
| active KU 있으나 `status == 'disputed'` | `conflicting` |
| active KU 있으나 TTL 초과 (`observed_at + ttl_days < today`) | `stale` |
| active KU 있고 위 조건 모두 해당 없음 | **Gap 아님** (skip) |

> **복수 조건 중복 시**: `conflicting` > `stale` > `uncertain` > `missing` 순 우선 (더 심각한 유형)

### 3단계: 엔티티 인스턴스 확장

카테고리 수준의 슬롯을 구체 엔티티로 풀어내는 단계.

**원칙:**
- 카테고리 내 **핵심 엔티티 3~5개**를 우선 선택 (Seed KU에 이미 등장한 엔티티 + 도메인 필수 엔티티)
- 엔티티 독립적 필드(카테고리 수준 일반 규칙 등)는 **와일드카드** 사용: `{domain}:{category}:*`

**와일드카드 사용 기준:**
- 개별 엔티티별 값이 다를 수 있는 필드 → 엔티티별 GU 생성 (예: `price`, `hours`)
- 카테고리 공통 규칙 → 와일드카드 GU 1개 (예: `tips`, `etiquette`)

**예시:**
```
# 엔티티별 GU (값이 다름)
GU: japan-travel:transport:tokyo-metro / how_to_use → missing
GU: japan-travel:transport:bus / how_to_use → missing

# 와일드카드 GU (공통 규칙)
GU: japan-travel:dining:* / etiquette → missing
```

### 4단계: 우선순위 산정 후 GU ID 순번 할당

§3 우선순위 산정 규칙에 따라 `expected_utility`와 `risk_level`을 결정한 후, 다음 순서로 정렬하여 GU-NNNN 부여:

1. `expected_utility` 내림차순: critical > high > medium > low
2. 동일 utility 내 `risk_level` 내림차순: safety > financial > policy > convenience > informational
3. 동일 우선순위 내 카테고리 알파벳순

### 5단계: Scope 경계 판정

`domain-skeleton.scope_boundary`로 필터:

- GU의 `target.entity_key`가 `excludes` 항목에 해당 → 제외
- GU의 정보 범위가 `boundary_rule`을 벗어남 → 제외
- **판정 불확실** 시: GU를 생성하되 `expected_utility: low`로 하향

---

## 2. 동적 GU 발견 규칙 (Cycle 중)

Bootstrap 이후 Inner Loop 실행 중 새 GU가 발견되는 3가지 트리거.

### 트리거 A: Integration 중 인접 Gap 노출

새 KU 통합 시 미지 영역이 드러남.

- **조건**: Integration에서 생성된 KU의 `entity_key` 또는 `field`가 기존 Gap Map에 없는 슬롯을 참조
- **액션**: 해당 슬롯에 `missing` GU 자동 생성
- **예시**: airport-transfer KU 통합 시 ic_card_compatibility 필드 필요성 발견 → GU-0027 생성

### 트리거 B: Critique Epistemic 실패모드

- **조건**: Critique에서 단일출처 + `risk_level ∈ {safety, financial, policy}` KU 식별
- **액션**: 해당 KU의 슬롯에 `uncertain` GU 생성 (또는 기존 resolved GU를 재개)
- **resolution_criteria**: "독립 출처 2개 이상 확보"

### 트리거 C: 새 엔티티 발견

- **조건**: Collect/Integration에서 Skeleton에 없는 entity_key 등장
- **액션**: 해당 엔티티의 핵심 필드(price, how_to_use 등)에 대해 `missing` GU 배치 생성
- **부수 효과**: 필요 시 `domain-skeleton.json`에 엔티티 추가 제안 (HITL Gate)

### 동적 GU 생성 상한 (Normal/Jump 이원화)

Mode에 따라 상한이 달라진다. Mode 판정은 §2.6 Jump Mode Trigger 참조.

| Mode | Cap 공식 | 예시 (open=21) |
|------|----------|---------------|
| **Normal** | `base_cap = min(max(4, ceil(open * 0.2)), 12)` | 5 |
| **Jump** | `jump_cap = min(max(10, ceil(open * 0.6)), 30)` | 13 |

**Jump Mode 추가 조건**:
- 신규 GU 중 high/critical ≥ 40% 필수
- 모든 신규 GU에 `expansion_mode`, `trigger`, `trigger_source` 필드 필수

**공통 예외**: `risk_level == safety`인 GU는 상한에서 제외 (안전 정보는 항상 추가)

> **실측** (Cycle 2 Jump): open=16, jump_cap=10, 실사용=6. high/critical 3/6=50% ≥ 40% ✅

---

## 2.5 Axis Coverage Matrix (Phase 0C 추가 — v1.0 확정)

> **상태**: Phase 0C Cycle 2 실측 검증 완료. 확정 임계치는 `gu-bootstrap-expansion-policy.md` v1.0 참조.

### 목적

category 축만으로는 도메인 지식의 편향을 감지할 수 없다. 다축(geography, condition, risk 등) 커버리지를 정량 추적하여 **구조적 결손**을 조기 식별한다.

### 축 정의

`domain-skeleton.json`에 `axes` 필드로 선언. 각 축은 유한 anchor 값 집합을 가진다.

```json
{
  "axes": {
    "category": ["transport", "accommodation", "..."],
    "geography": ["tokyo", "osaka", "kyoto", "rural", "nationwide"],
    "condition": ["peak-season", "off-season", "..."],
    "risk": ["safety", "financial", "policy", "convenience", "informational"]
  }
}
```

### Matrix 계산

Cycle 종료 시 각 축의 각 값에 대해:

```
coverage[axis][value] = {
  open:             count(GU where axis_tags[axis] == value AND status == 'open'),
  resolved:         count(GU where axis_tags[axis] == value AND status == 'resolved'),
  critical_open:    count(GU where axis_tags[axis] == value AND expected_utility in ['critical','high'] AND status == 'open'),
  evidence_density: mean(len(KU.evidence_links) for KU in scope of value)
}
```

### deficit_ratio 계산

```
deficit_ratio[axis] = count(values where open + resolved == 0) / count(all anchor values)
```

- deficit_ratio > **0** (required 축) → Quantum Jump Mode trigger T1 발동 (v1.0 확정)

---

## 2.6 Quantum Jump Mode (Phase 0C 추가 — v1.0 확정)

> **상태**: Phase 0C Cycle 2 실측 검증 완료. 확정 수치는 `gu-bootstrap-expansion-policy.md` v1.0 §5 참조.

### 개요

구조적 결손이 클 때 고정 상한(20%)만으로는 회복이 느리다. 조건 충족 시 GU 생성 상한을 일시적으로 상향한다.

### Mode 구분

| Mode | Cap 공식 | 적용 조건 |
|------|----------|-----------|
| Base | `min(max(4, ceil(open * 0.2)), 12)` | 기본 (trigger 미충족) |
| Jump | `min(max(10, ceil(open * 0.6)), 30)` | trigger 1개 이상 충족 |

### Jump Mode Trigger (5종)

| # | Trigger | 조건 (v1.0 확정) |
|---|---------|-------------------|
| 1 | Axis Under-Coverage | required 축 deficit_ratio > 0 |
| 2 | Spillover | Collect/Integrate에서 Gap Map 외 슬롯 참조 3건 이상 |
| 3 | High-Risk Blindspot | safety/financial/policy 단일출처+conf<0.85 KU 2건 이상 |
| 4 | Prescription | Critique RX가 구조 보강 명시 1건 이상 |
| 5 | Domain Shift | 신규 entity cluster(skeleton 미등록 category 수준) 1건 이상 |

### Guardrail (4종)

| Guard | 규칙 |
|-------|------|
| Quality | 신규 GU 100% resolution_criteria 필수, high/critical은 evidence plan 필수 |
| Cost | Cycle별 search/fetch/LLM budget 상한 유지, 초과 시 low utility 중단 |
| Balance | 단일 category/axis가 신규 GU의 50% 초과 금지 |
| Convergence | 연속 2 Cycle Jump 시 HITL 검토 필수 |

### explore / exploit budget

| budget | 용도 | 단위 |
|--------|------|------|
| explore | 신규 축 영역 GU 생성 | GU 개수 |
| exploit | 기존 open GU 해결 | GU 개수 |

**확정 비율** (v1.0):

| Cycle 단계 | Jump Mode | Normal Mode |
|-----------|-----------|-------------|
| 초기 (1~3) | explore 60% / exploit 40% | exploit 100% |
| 중기 (4~6) | explore 50% / exploit 50% | exploit 100% |
| 수렴 (7+) | explore 40% / exploit 60% | exploit 100% |

홀수 Target 시 exploit에 +1 배분 (Balance Guard 준수).

---

## 3. 우선순위 산정 규칙

### expected_utility 결정

`risk_level`과 도메인 중요도의 조합으로 결정론적 할당.

| risk_level | expected_utility |
|------------|-----------------|
| safety | **critical** |
| financial + (price \| policy 필드) | **high** |
| financial + 기타 필드 | **medium** |
| policy | **high** |
| convenience + 핵심 카테고리* | **medium** |
| convenience + 기타 | **low** |
| informational | **low** |

> *핵심 카테고리: 도메인별 정의. japan-travel에서는 transport, regulation, pass-ticket.

### risk_level 결정

field 유형과 category의 매핑으로 결정.

| field | 기본 risk_level |
|-------|----------------|
| policy (regulation 카테고리) | safety 또는 policy (내용에 따라) |
| price | financial |
| eligibility | policy |
| hours, location, duration, how_to_use | convenience |
| tips, etiquette, acceptance, where_to_buy | convenience |

**카테고리 오버라이드:**
- `regulation` 카테고리: 기본 risk를 1단계 상향 (convenience → policy, policy → safety)
- `payment` 카테고리의 price/acceptance: financial 유지

---

## 4. Scope 제어 규칙 (GU 폭발 방지)

### 카테고리당 Bootstrap GU 상한

| 전체 카테고리 수 | 카테고리당 상한 |
|-----------------|----------------|
| 3~5 | 6 |
| 6~8 | 4 |
| 9~12 | 3 |

> japan-travel: 8 카테고리 → 카테고리당 최대 4개

### 총 Bootstrap GU 권장 범위

- **하한**: 20개 (최소 커버리지 보장)
- **상한**: 40개 (관리 가능 범위)
- 이 범위를 벗어나면 엔티티 선정 또는 와일드카드 수준을 조정

### 와일드카드 entity_key 사용 기준

| 조건 | 전략 |
|------|------|
| 카테고리 내 엔티티 < 3개 알려짐 | 와일드카드(`*`) 1개로 통합 |
| 카테고리 내 엔티티 3~5개 | 핵심 2~3개 개별 + 나머지 와일드카드 |
| 카테고리 내 엔티티 > 5개 | 핵심 3~4개 개별만 (나머지는 동적 발견에 위임) |

---

## 5. 수렴 조건

수렴 판정은 **최소 5 Cycle 실행 후**에만 적용 가능.

### 수렴 지표 (C1~C5)

| ID | 조건 | 임계치 | 근거 |
|----|------|--------|------|
| C1 | critical + high GU 중 open 비율 | < 10% | 고위험 Gap 해소 |
| C2 | stale GU 중 open 비율 | < 15% | 정보 신선도 유지 |
| C3 | 최근 3 Cycle `net_gap_change` | > -1 (= 순증 거의 0) | 탐색 범위 안정화 |
| C4 | `avg_confidence` | >= 0.85 | design-v2 §4 건강 임계치 |
| C5 | 카테고리 커버리지 (≥1 resolved GU 있는 카테고리 비율) | >= 80% | 편향 없는 커버 |

### net_gap_change 계산

```
net_gap_change = (신규 open GU) - (resolved GU) in Cycle N
```

- 양수: 탐색 영역 확장 중 (초기 Cycle에서 정상)
- 음수: 수렴 중
- 0 근처 지속: 안정 상태

### 수렴 판정 로직

```
converged = (cycle >= 5) AND C1 AND C2 AND C3 AND C4 AND C5
```

- 5개 조건 **모두** 충족 시 수렴 선언 가능
- 부분 충족 시: 미충족 조건을 다음 Cycle Plan에 우선 반영

---

## 6. 검증 체크리스트

### A. Bootstrap 완료 체크 (Seed 단계 출구)

- [ ] 총 GU 수 >= 20
- [ ] `expected_utility`가 critical 또는 high인 GU >= 3
- [ ] 모든 카테고리에 최소 1개 GU 존재
- [ ] `scope_boundary.excludes`에 해당하는 GU 없음
- [ ] 모든 GU에 `resolution_criteria` 명시
- [ ] GU ID가 연속 순번이고 우선순위 정렬에 부합

### B. 동적 발견 체크 (각 Cycle 종료 시)

- [ ] 신규 GU 수 <= base_cap (Normal) 또는 jump_cap (Jump) (safety 예외 적용)
- [ ] 신규 GU에 `resolution_criteria` 명시
- [ ] 트리거(A/B/C) 중 하나에 명확히 해당
- [ ] `created_at`이 해당 Cycle 날짜

### B-2. Jump Mode 체크 (Jump Mode Cycle 종료 시)

- [ ] Jump Mode trigger 판정 기록 (어떤 trigger가 발동/미발동)
- [ ] 신규 GU 중 high/critical ≥ 40%
- [ ] 신규 GU에 `expansion_mode`, `trigger`, `trigger_source` 필드 기재
- [ ] explore/exploit 배분이 Balance Guard(60%) 이내
- [ ] Axis Coverage deficit_ratio가 감소했는가
- [ ] Guardrail 4종(Quality/Cost/Balance/Convergence) 위반 없음
- [ ] Convergence Guard: 연속 2 Cycle Jump 시 HITL 발동했는가

### C. 수렴 판정 체크 (Cycle >= 5 이후)

- [ ] C1~C5 지표 모두 계산됨
- [ ] 5개 조건 충족 여부 명시
- [ ] 미충족 조건에 대한 다음 Cycle 우선 반영 계획 존재

---

## 부록: Cycle 0 역검증

### 알고리즘 적용 결과 vs 실제 Gap Map

- **domain-skeleton**: 8 카테고리 × 11 필드 = 35 적용 가능 슬롯
- **실제 Bootstrap GU**: 25개 (GU-0001 ~ GU-0025)
- **Cycle 0 후 동적 추가**: 3개 (GU-0026 ~ GU-0028)

### 카테고리 분포

| Category | 실제 GU 수 | 상한(4) 준수 |
|----------|-----------|-------------|
| transport | 5 (GU-0003,05,16,20,24) | 초과(5) — 핵심 도메인이므로 허용 범위 |
| accommodation | 3 (GU-0006,07,21) | O |
| attraction | 3 (GU-0008,09,23) | O |
| dining | 2 (GU-0010,11) | O |
| regulation | 4 (GU-0012,17,22,25) | O |
| pass-ticket | 4 (GU-0001,02,04,18) | O |
| connectivity | 2 (GU-0015,19) | O |
| payment | 2 (GU-0013,14) | O |

→ 전 카테고리 커버, 총 25개는 권장 범위(20~40) 내.
→ transport 초과(5)는 핵심 카테고리 특성상 허용 가능 (상한은 권장치).
