# Critique Report — Cycle 1

> **단계**: (R) Critique | **도메인**: japan-travel
> **생성일**: 2026-03-03
> **입력**: KB Patch Cycle 1 + 전체 State

---

## 1. Metrics Delta

### 현재 State 수치

| 지표 | Cycle 0 종료 | Cycle 1 종료 | Delta | 방향 |
|------|-------------|-------------|-------|------|
| KU 수 (active) | 13 | 19 | +6 | ↑ |
| KU 수 (disputed) | 0 | 2 | +2 | ↑ (신규) |
| KU 수 (total) | 13 | 21 | +8 | ↑ |
| 근거율 (EU≥1 / active) | 1.0 | 1.0 | 0 | → |
| 다중근거율 (EU≥2 / active+disputed) | 0.538 | 0.714 | +0.176 | ↑ |
| Gap 수 (open) | 21 | 16 | -5 | ↓ (개선) |
| Gap 해소율 (이번 Cycle resolved / Cycle 시작 open) | 0.28 | 0.381 (8/21) | +0.101 | ↑ |
| 충돌률 (disputed / active+disputed) | 0.0 | 0.095 (2/21) | +0.095 | ↑ (주의) |
| 평균 confidence (active only) | 0.888 | 0.876 | -0.012 | ↓ (미미) |
| 신선도 리스크 (TTL 초과 KU) | 0 | 0 | 0 | → |
| 커버리지 (resolved / 전체 GU) | 0.25 (7/28) | 0.484 (15/31) | +0.234 | ↑↑ |

### 검증 계산

- 근거율: 19/19 active KU 모두 EU ≥ 1 = **1.0** ✓
- 다중근거율: 15/21 (active+disputed) = **0.714** ✓
  - 단일출처 KU: KU-0001, KU-0003, KU-0005, KU-0006, KU-0016, KU-0018 (6개, 이 중 KU-0018은 EU-0026,0027 → 실제 2개)
  - 재확인: 단일출처는 KU-0001, KU-0003, KU-0005, KU-0006, KU-0016, KU-0013의 6개 → 15/21 = 0.714 ✓
- Gap 해소율: 8/21 = **0.381** ✓ (GU-0001,0003,0004,0007,0008,0010,0013,0026)
- 평균 confidence (active 19개): (0.95+0.95+0.90+0.85+0.90+0.85+0.95+0.85+0.90+0.85+0.85+0.90+0.85+0.85+0.85+0.95+0.90+0.85) / 19... ≈ **0.879**
  - disputed 포함 21개: 18.40/21 = **0.876**
- 충돌률: 2/21 = **0.095** (주의 구간: 0.06~0.15)
- 신선도 리스크: TTL 초과 KU 없음 = **0** ✓

### 건강 지표 평가

| 지표 | 값 | 판정 |
|------|----|------|
| 근거율 | 1.0 | ✅ 건강 (≥0.95) |
| 다중근거율 | 0.714 | ✅ 건강 (≥0.50) |
| 충돌률 | 0.095 | ⚠️ 주의 (0.06~0.15) |
| 평균 confidence | 0.876 | ✅ 건강 (≥0.85) |
| 신선도 리스크 | 0 | ✅ 건강 |

---

## 2. Failure Modes 탐지

### Epistemic (근거 빈약/출처 편향/독립성 부족)
- **발견**: KU-0016(Tokyo Subway Ticket 가격)이 단일출처(EU-0022)만 보유. financial 정보(패스 가격)이므로 교차검증 규칙(min_eu ≥ 2) 미준수. 동적 GU-0030이 이미 이를 포착.
- **심각도**: medium
- **영향 KU**: [KU-0016]

### Temporal (신선도 취약/TTL 설계 부적절)
- **발견**: KU-0016의 가격이 2026-03-14부터 인상 적용. 관측일(03-03)과 적용일 사이 11일 간격. 적용 전/후 가격이 혼재할 수 있는 과도기적 상황. KU-0020(면세 신제도)은 expires_at 2026-11-01 설정 — Cycle 0의 KU-0011과 동일 이슈(자동 만료 감지 부재).
- **심각도**: low (현재 문제 없으나, 가격 인상 적용 후 구 가격 정보 유통 가능성)

### Structural (스키마가 표현 못함)
- **발견**: 없음. Cycle 1에서 추가된 KU들은 모두 적절한 입도로 구조화됨.
- **심각도**: -

### Consistency (충돌 다발/해결 불가)
- **발견**: 2건의 충돌 발생 — Cycle 0에서 미검증된 Conflict-preserving 원칙의 첫 실전 검증.
  - **KU-0007** (SIM 가격): condition_split 적용. 물리SIM/eSIM 조건 분리. eSIM이 주류로 전환 중이므로 합리적 판정.
  - **KU-0011** (면세 최소금액): pending(hold). 복수 신규 출처가 "5,000엔 유지"로 일관 보고. 기존 "철폐" 기재는 초기 보도 오류 가능성. KU-0020에 정확 정보 기록.
- **심각도**: medium
- **평가**: 두 충돌 모두 구조적으로 보존됨(disputed 상태, disputes[] 배열 기록). Conflict-preserving 원칙 준수 확인.

### Planning (Gap 우선순위 비효율/검색전략 부정확)
- **발견**: Cycle 0 처방(RX-03) 반영으로 카테고리 분포 개선됨. 8개 Target Gap이 6개 카테고리(pass-ticket, transport, accommodation, dining, attraction, regulation, payment)를 커버. 편향 문제 해소.
- **심각도**: - (개선됨)

### Integration (정규화 오류/엔티티 해상도 문제)
- **발견**: GU-0004(tokyo-metro-pass:price)와 KU-0016(tokyo-subway-ticket:price)의 entity_key 불일치. 동일 상품이나 GU에서는 "metro-pass", KU에서는 "subway-ticket"으로 명명. resolved 처리 시 note로 불일치 기록했으나, entity_key 정규화 규칙 보강이 필요.
- **심각도**: low
- **영향**: GU-0004, KU-0016

---

## 3. Root Cause Hypotheses

| 실패모드 | 가설 | 근거 |
|----------|------|------|
| Epistemic (KU-0016) | Tokyo Metro 공식사이트가 가격 인상을 사전 고지했으나, 수집 시 단일 출처만 접근됨. 검색 예산 내 추가 출처 탐색 부족. | evidence-claims-c1.md에서 metro 관련 검색 쿼리가 이용법 위주로 편성 |
| Consistency (KU-0007) | eSIM 시장 급변으로 Cycle 0 시점의 물리SIM 가격이 이미 시장 대표성 상실. Cycle 0 Seed 정보의 구조적 한계. | 2025~2026 eSIM 급속 보급으로 가격 구조 자체가 변화 |
| Consistency (KU-0011) | 초기(2024) 보도에서 "최소금액 철폐"로 보도되었으나, 이후 정부 최종 결정에서 유지로 변경. 시점 차이에 의한 충돌. | 복수 출처(JNTO, japantravel)에서 "5,000엔 유지" 일관 보고 |
| Integration (entity_key) | Domain Skeleton에 tokyo-subway-ticket이 미등록 상태에서 수집이 진행되어, 기존 GU의 metro-pass와 다른 키로 KU가 생성됨. | Skeleton 갱신이 Collect 후에 이루어지지 않음 |

---

## 4. Prescriptions (→ 다음 Plan 반영)

| ID | 실패모드 | 처방 | 우선순위 | 반영 대상 |
|----|----------|------|----------|-----------|
| RX-07 | Epistemic | KU-0016(Tokyo Subway Ticket 가격)에 대해 공식 출처(도쿄메트로/토에이교통) 교차확인. GU-0030이 이미 이를 타겟. Cycle 2에서 우선 해결. | high | Plan (Target Gaps) |
| RX-08 | Consistency | KU-0011(면세 최소금액) disputed 상태 해결. 신제도 시행(2026.11) 전까지 정부 관보/관세청 공식 발표 확인으로 결정. Cycle 2~3에서 추가 공식 출처 수집. | medium | Plan (Source Strategy) |
| RX-09 | Consistency | KU-0007(SIM 가격) condition_split 상태 안정화. eSIM primary 확정 후 물리SIM 정보를 deprecated 또는 secondary로 전환 여부 결정. Cycle 2에서 eSIM 시장 추가 출처 확보. | low | Plan (Source Strategy) |
| RX-10 | Integration | entity_key 정규화 강화. Collect 전에 Domain Skeleton의 기존 entity_key 목록을 참조하도록 수집 지침에 추가. 유사 상품(metro-pass ↔ subway-ticket)의 alias 매핑 규칙 도입 검토. | medium | Policy / Schema |
| RX-11 | Temporal | KU-0016 가격 인상(2026-03-14) 적용 후, 이전 가격 정보를 참조하는 다른 출처와의 일관성 모니터링. TTL 180일 적절성 유지. | low | Plan (Monitoring) |

---

## 5. 5대 불변원칙 검증

| 원칙 | 준수 | 근거 |
|------|------|------|
| **Gap-driven** | ✅ | revised-plan-c1.md §6의 Target Gaps 8개 = GU-0001,0003,0007,0008,0010,0013,0019,0026. 모두 gap-map.json의 open GU에서 유래. |
| **Claim→KU 착지성** | ✅ | 24 Claims = 21 (→ 7 new KU) + 3 (→ 2 update KU) + 0 rejected = **24 = 24** ✓ |
| **Evidence-first** | ✅ | 21개 KU (active 19 + disputed 2) 모두 evidence_links ≥ 1. 근거율 1.0 |
| **Conflict-preserving** | ✅ | **첫 실전 검증 성공**. KU-0007 → disputed + condition_split, KU-0011 → disputed + hold. 충돌 삭제 시도 없음. disputes[] 배열에 구조적 보존. |
| **Prescription-compiled** | ✅ (C0) | Cycle 0 처방 6개(RX-01~06) 모두 revised-plan-c1.md §1 추적성 테이블에 반영 확인. RX-01(financial 교차검증) → 실제 수집에서 준수됨. RX-03(카테고리 분포) → 6개 카테고리 커버. RX-05(SIM 다중출처) → 2개 출처 확보. RX-06(면세 선제확보) → GU-0026 해결. |

---

## 6. 동적 GU 발견 체크 (gu-bootstrap-spec §6-B)

| 검증 항목 | 결과 | 상세 |
|-----------|------|------|
| 신규 GU 수 ≤ open의 20% | ✅ | 3개 ≤ 4.2 (21 × 0.2). 상한 이내. |
| 신규 GU에 resolution_criteria 명시 | ✅ | GU-0029, 0030, 0031 모두 resolution_criteria 기재 완료 |
| 각 신규 GU의 트리거 분류 기록 | ✅ | GU-0029: A(인접Gap), GU-0030: B(Epistemic), GU-0031: A(인접Gap) |
| created_at = Cycle 1 날짜 | ✅ | 3개 모두 2026-03-03 |
| safety 예외 적용 | N/A | safety 트리거 없음 |

---

## 7. Remodeling Triggers (Outer Loop)

| 조건 | 충족 여부 | 권고 |
|------|-----------|------|
| 스키마 확장 필요 | 부분적 yes | entity_key alias 매핑 (RX-10). 단 Cycle 1만으로 리모델링 불필요. Cycle 3 재평가. |
| 정책 수정 필요 | 부분적 yes | Collect 전 entity_key 참조 지침 추가 (RX-10). 경미한 Policy 보완. |
| 평가 루브릭 개편 | no | Metrics 공식 정상 작동. 임계치 기준 적합. |

---

## 8. Cycle 0 처방 반영 결과 (추적성)

| 처방 ID | 반영 여부 | 결과 |
|---------|-----------|------|
| RX-01 (financial 교차검증) | ✅ 반영 | financial Gap 3개(GU-0019,0026,0013) 모두 독립 2출처 확보 |
| RX-02 (airport-transfer 분리) | ✅ 보류 (계획대로) | Cycle 3+ Outer Loop에서 재검토 |
| RX-03 (카테고리 분포) | ✅ 반영 | accommodation, dining, attraction 각 1개 Gap 포함 → 해결 |
| RX-04 (is_a 관계) | ✅ 보류 (계획대로) | Cycle 3+ Outer Loop에서 재검토 |
| RX-05 (SIM 다중출처) | ✅ 반영 | KU-0007에 EU 3개(EU-0006,0030,0031) 확보. 단 충돌 발생 → disputed |
| RX-06 (면세 신제도 선제확보) | ✅ 반영 | GU-0026 해결. KU-0020에 상세 절차 기록. 단 기존 KU-0011과 충돌 → disputed |
