# Revised Plan — Cycle 1

> **단계**: (PM) Plan Modify | **도메인**: japan-travel
> **생성일**: 2026-03-02
> **입력**: Critique Report Cycle 0

---

## 1. Critique→Plan 추적성 (Traceability)

| 처방 ID | 실패모드 | 처방 내용 | 반영 방법 | 반영 위치 |
|---------|----------|-----------|-----------|-----------|
| RX-01 | Epistemic | KU-0013 신칸센 가격 교차확인 | GU-0024를 재개방하지 않되, 추가 EU 확보를 별도 태스크로 편성 | Plan §3 (추가 검증 쿼리) |
| RX-02 | Structural | airport-transfer 엔티티 분리 | Cycle 1에서는 보류. 현 구조 유지. | Schema (deferred → Cycle 3+) |
| RX-03 | Planning | 카테고리 분포 고려 | accommodation, dining, attraction에서 각 1+ Gap 선정 | Plan §2 (Gap Selection) |
| RX-04 | Integration | is_a 관계 추가 | 보류. Outer Loop에서 검토. | Schema (deferred → Cycle 3+) |
| RX-05 | Epistemic | KU-0007 SIM 가격 다중출처 | GU-0019를 Cycle 1 타겟에 포함 | Plan §2 (Target Gaps) |
| RX-06 | Temporal | 면세 신제도 절차 선제 확보 | GU-0026 우선순위 상향 | Plan §2 (Gap Priority) |

---

## 2. 변경된 Gap 우선순위

| 순위 | GU ID | 이전 순위 | 변경 사유 (처방 ID) |
|------|-------|-----------|---------------------|
| 1 | GU-0001 | 미선정 | 기존 high — JR Pass 활용도 핵심 |
| 2 | GU-0003 | 미선정 | 기존 high — 도쿄 이동 핵심 |
| 3 | GU-0007 | 미선정 | RX-03: accommodation 카테고리 보충 |
| 4 | GU-0010 | 미선정 | RX-03: dining 카테고리 보충 |
| 5 | GU-0008 | 미선정 | RX-03: attraction 카테고리 보충 |
| 6 | GU-0019 | 미선정 | RX-05: SIM 가격 최신화 + 다중출처 |
| 7 | GU-0026 | 신규 | RX-06: 면세 신제도 선제 확보 |
| 8 | GU-0013 | 미선정 | 결제수단 — 실용성 high |

---

## 3. 변경된 Source Strategy

| 변경 항목 | 이전 | 이후 | 사유 (처방 ID) |
|-----------|------|------|----------------|
| financial 정보 출처 | public 1개 허용 | 공식 또는 public 2개 이상 필수 | RX-01 |
| 카테고리 분포 | 미고려 | 최소 5개 카테고리에서 1+ Gap 선정 | RX-03 |
| SIM 가격 출처 | 단일 | 최소 2개 독립 출처 (공식+platform) | RX-05 |

---

## 4. 변경된 검증 기준

| GU ID | 이전 기준 | 이후 기준 | 사유 (처방 ID) |
|-------|-----------|-----------|----------------|
| GU-0019 | 1개 출처 | 2개 독립 출처, 2025년 이후 데이터 | RX-05 |
| 전체 financial Gap | min_eu 1 | min_eu 2 (공식 1 + 독립 1) | RX-01 |

---

## 5. Policy Updates

| 정책 항목 | 이전 값 | 이후 값 | 사유 (처방 ID) |
|-----------|---------|---------|----------------|
| cross_validation.financial.min_independent_sources | 2 | 2 (유지, 단 enforcement 강화) | RX-01 |

> Cycle 0에서 정책 자체는 적절했으나, 실제 수집 시 financial 교차검증 규칙이 KU-0013에서 미준수됨. Cycle 1에서는 Acceptance Test에서 명시적으로 체크.

---

## 6. Revised Collection Plan (Cycle 1)

### Target Gaps

| 순위 | GU ID | 유형 | 대상 | 기대효용 | 리스크 | 선정 이유 |
|------|-------|------|------|----------|--------|-----------|
| 1 | GU-0001 | missing | jr-pass:nozomi-alternative | high | convenience | JR Pass 활용 핵심. Hikari/Kodama 비교 |
| 2 | GU-0003 | missing | tokyo-metro:how_to_use | high | convenience | 도쿄 내 이동 필수 |
| 3 | GU-0007 | missing | ryokan:etiquette | medium | convenience | RX-03: accommodation 보충 |
| 4 | GU-0010 | missing | izakaya:etiquette | medium | convenience | RX-03: dining 보충 |
| 5 | GU-0008 | missing | fushimi-inari:hours | medium | convenience | RX-03: attraction 보충 |
| 6 | GU-0019 | stale | sim-card:price | medium | financial | RX-05: 최신화 + 다중출처 |
| 7 | GU-0026 | missing | tax-free:procedure_2026_nov | high | financial | RX-06: 신제도 선제 확보 |
| 8 | GU-0013 | missing | credit-card:acceptance | medium | financial | 결제수단 핵심 |

### Source Strategy
- 공식 사이트 우선 (JR, 도쿄메트로, JNTO, 관세청)
- japan-guide.com, LIVE JAPAN 보조
- etiquette 류: japan-guide + 문화 가이드 사이트 교차
- **financial 정보: 반드시 2개 출처 확보 (RX-01 반영)**

### Query/Discovery Strategy

| GU ID | 검색 쿼리 | 기대 출처 | 언어 |
|-------|-----------|-----------|------|
| GU-0001 | "JR Pass Hikari Kodama vs Nozomi time comparison" | JR, japan-guide | en |
| GU-0003 | "Tokyo Metro guide tourist 2026 lines passes" | Tokyo Metro 공식 | en |
| GU-0007 | "ryokan etiquette guide tourist Japan" | japan-guide, JNTO | en |
| GU-0010 | "izakaya etiquette ordering Japan tourist guide" | japan-guide, LIVE JAPAN | en |
| GU-0008 | "Fushimi Inari Taisha opening hours 2026" | 공식, japan-guide | en |
| GU-0019 | "Japan SIM card tourist price 2026 comparison" | 통신사, japan-guide | en |
| GU-0026 | "Japan tax free refund system November 2026 details" | 관광청, JNTO | en |
| GU-0013 | "credit card acceptance Japan 2026 tourist" | japan-guide, JNTO | en |

### Acceptance Tests

| GU ID | 해결 조건 | 최소 EU 수 | 독립성 | 신선도 |
|-------|-----------|------------|--------|--------|
| GU-0001 | Hikari/Kodama 주요 구간 시간 비교 | 1 | - | 2024+ |
| GU-0003 | 노선 개요 + 패스 종류 + IC카드 호환 | 1 | - | 2024+ |
| GU-0007 | 입실/퇴실/온천/식사 에티켓 | 1 | - | - |
| GU-0010 | 오토시/주문법/결제 관습 | 1 | - | - |
| GU-0008 | 운영시간 + 24시간 여부 | 1 | - | 2024+ |
| GU-0019 | 최신 가격 (2025+) | 2 | 독립 2 | 2025+ |
| GU-0026 | 환급 절차 구체 내용 | 1 | 공식 필수 | 2025+ |
| GU-0013 | 사용 가능/불가 장소 + 비율 | 1 | - | 2024+ |

### Budget & Stop Rules
- 수집 상한: 15회 검색
- 중복 상한: 동일 출처 3회 초과 시 전환
- 품질 미달 중단: 신뢰도 0.5 미만 EU 3개 연속 시 Gap 보류
- 조기 종료: 8개 Target Gap 모두 resolved/deferred 시

---

## 7. Critique→Plan 컴파일 규칙 (메타)

> Cycle 0에서 도출된 일반화 가능한 변환 규칙.

| 실패모드 | → Plan 변경 유형 | 규칙 |
|----------|------------------|------|
| Epistemic (근거 부족) | Source Strategy 강화 + 추가 검증 쿼리 | 단일 출처 financial/safety KU → Cycle N+1에서 해당 Gap 재타겟 또는 추가 EU 수집 태스크 추가 |
| Temporal (TTL/만료) | Gap Priority 상향 | expires_at 접근 KU → 관련 Gap 우선순위 상향. TTL 기준일 - 30일 이내면 critical로 승격 |
| Structural (스키마 한계) | Schema deferred → Outer Loop | 단일 KU에 3단계 이상 중첩 → 엔티티 분리 검토 플래그. 즉시 분리하지 않고 3 Cycle 축적 후 Outer Loop에서 결정 |
| Consistency (충돌) | Policy 강화 + 추가 수집 | 충돌 KU 쌍 → hold 판정 후 Cycle N+1에서 추가 독립 출처 수집. 조건 분석으로 condition_split 시도 |
| Planning (편향) | Gap Selection 기준 확대 | 카테고리 분포 체크 추가. 전체 카테고리 중 미커버 비율 > 50%면 최소 1개씩 포함 강제 |
| Integration (해상도 오류) | Entity Resolution 규칙 보강 | 동일 실물의 다중 엔티티 발견 시 → is_a/part_of 관계 추가 또는 병합. 스키마에 관계 타입 부족 시 → Structural 실패모드로 에스컬레이션 |
