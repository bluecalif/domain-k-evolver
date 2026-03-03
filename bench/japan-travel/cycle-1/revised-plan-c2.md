# Revised Plan — Cycle 2

> **단계**: (PM) Plan Modify | **도메인**: japan-travel
> **생성일**: 2026-03-03
> **입력**: Critique Report Cycle 1

---

## 1. Critique→Plan 추적성 (Traceability)

| 처방 ID | 실패모드 | 처방 내용 | 반영 방법 | 반영 위치 |
|---------|----------|-----------|-----------|-----------|
| RX-07 | Epistemic | KU-0016 Tokyo Subway Ticket 가격 교차확인 | GU-0030을 Cycle 2 최우선 타겟으로 배정. 공식 출처(도쿄메트로/토에이) 필수. | Plan §2 (순위 1), §6 (Target Gaps) |
| RX-08 | Consistency | KU-0011 면세 최소금액 disputed 해결 | 정부 관보/관세청 공식 출처 추가 수집. Cycle 2에서 별도 검증 태스크로 편성 (Target Gap 외 추가 검증). | Plan §3 (추가 검증 쿼리) |
| RX-09 | Consistency | KU-0007 SIM condition_split 안정화 | GU-0019를 Cycle 2 타겟에 포함. eSIM 전문 비교 사이트에서 추가 출처 확보. | Plan §2 (순위 5), §6 (Target Gaps) |
| RX-10 | Integration | entity_key alias 매핑 규칙 도입 | Collect 전 entity_key 참조 지침 추가. 기존 Skeleton 키 목록 사전 확인 의무화. | Plan §5 (Policy Updates) |
| RX-11 | Temporal | KU-0016 가격 인상 후 모니터링 | GU-0030 해결 시 인상 후 가격 정확성 확인 포함. TTL 180일 유지. | Plan §4 (검증 기준) |

---

## 2. 변경된 Gap 우선순위

| 순위 | GU ID | 이전 순위 | 변경 사유 (처방 ID) |
|------|-------|-----------|---------------------|
| 1 | GU-0030 | 신규(C1) | RX-07: financial 교차확인 필수. 단일출처 해소. |
| 2 | GU-0006 | 미선정 | financial + accommodation 카테고리 커버 |
| 3 | GU-0014 | 미선정 | payment 카테고리. 현금 문화가 일본 여행 핵심. |
| 4 | GU-0009 | 미선정 | financial + attraction 카테고리 커버 |
| 5 | GU-0019 | C1-6위 | RX-09: disputed 해결 위한 eSIM 추가 출처 |
| 6 | GU-0020 | 미선정 | financial + transport 카테고리 커버 |
| 7 | GU-0029 | 신규(C1) | 인접 Gap(KU-0016). 구매처 정보로 실용성 보완. |
| 8 | GU-0022 | 미선정 | regulation 카테고리. 짐 배송 실용정보. |

### 카테고리 분포 확인

| 카테고리 | Gap 수 | GU ID |
|----------|--------|-------|
| pass-ticket | 1 | GU-0030 |
| accommodation | 1 | GU-0006 |
| payment | 1 | GU-0014 |
| attraction | 1 | GU-0009 |
| connectivity | 1 | GU-0019 |
| transport | 1 | GU-0020 |
| pass-ticket | 1 | GU-0029 |
| regulation | 1 | GU-0022 |

→ **7개 카테고리 커버** (RX-03 계승). 편향 없음 ✓

---

## 3. 변경된 Source Strategy

| 변경 항목 | 이전 (C1) | 이후 (C2) | 사유 (처방 ID) |
|-----------|-----------|-----------|----------------|
| financial 출처 | 독립 2개 이상 | 유지 + 공식 출처 1개 필수 포함 강화 | RX-07 |
| SIM 가격 출처 | 독립 2개 | eSIM 전문 비교 사이트(Airalo, Holafly 등) + 리뷰 사이트 교차 | RX-09 |
| entity_key 참조 | 미고려 | Collect 전 기존 Skeleton entity_key 목록 사전 참조 | RX-10 |
| 면세 추가 검증 | 미해당 | 관보/관세청/국세청 공식 발표 탐색 | RX-08 |

---

## 4. 변경된 검증 기준

| GU ID | 이전 기준 | 이후 기준 | 사유 (처방 ID) |
|-------|-----------|-----------|----------------|
| GU-0030 | (신규) | 2026.3.14 이후 적용 가격. 공식 출처(도쿄메트로 or 토에이) 필수 1 + 독립 1. | RX-07, RX-11 |
| GU-0019 | 독립 2개, 2025+ | eSIM primary. 2026년 1월 이후 데이터. 3개 이상 eSIM 제공사 가격 포함. | RX-09 |
| 전체 financial Gap | min_eu 2 | min_eu 2 유지 + 공식 출처 1개 필수 포함 | RX-07 강화 |

---

## 5. Policy Updates

| 정책 항목 | 이전 값 | 이후 값 | 사유 (처방 ID) |
|-----------|---------|---------|----------------|
| collect.pre_check | 없음 | Collect 전 domain-skeleton.json의 entity_key 목록을 참조. 유사 키 존재 시 기존 키 사용 우선. | RX-10 |
| cross_validation.financial.official_required | 없음 (암묵적) | true — financial Gap 해결 시 공식 출처 1개 필수 포함 | RX-07 |

---

## 6. Revised Collection Plan (Cycle 2)

### Target Gaps

| 순위 | GU ID | 유형 | 대상 | 기대효용 | 리스크 | 선정 이유 |
|------|-------|------|------|----------|--------|-----------|
| 1 | GU-0030 | uncertain | tokyo-subway-ticket:price | medium | financial | RX-07: 단일출처 교차확인. 가격 인상 반영. |
| 2 | GU-0006 | missing | ryokan:price | medium | financial | accommodation 카테고리 financial Gap |
| 3 | GU-0014 | missing | cash:tips | medium | convenience | ATM/환전/현금 실용 정보. 핵심 여행 지식. |
| 4 | GU-0009 | missing | tokyo-skytree:price | medium | financial | attraction financial. 관광지 입장료. |
| 5 | GU-0019 | stale | sim-card:price | medium | financial | RX-09: disputed 해결. eSIM 추가 출처. |
| 6 | GU-0020 | missing | taxi:price | medium | financial | transport financial. 요금 체계. |
| 7 | GU-0029 | missing | tokyo-subway-ticket:where_to_buy | medium | convenience | 인접 Gap. 구매처 실용 정보. |
| 8 | GU-0022 | missing | luggage-forwarding:how_to_use | medium | convenience | regulation. 짐 배송 실용 정보. |

### 추가 검증 태스크 (Target Gap 외)

| 대상 | 목적 | 사유 (처방 ID) |
|------|------|----------------|
| KU-0011 면세 최소금액 | disputed 해결: "5,000엔 유지" vs "철폐" 확정 | RX-08 |

### Source Strategy

- **공식 사이트 최우선**: 도쿄메트로, 토에이교통, 도쿄스카이트리, JR East, 국세청/관세청
- **japan-guide.com, LIVE JAPAN** 보조
- **eSIM 비교**: Airalo, Holafly, Ubigi 공식 가격표 + 리뷰 사이트
- **료칸 가격**: Booking.com, じゃらん, JNTO 가이드
- **financial 정보: 공식 출처 1개 + 독립 1개 이상 필수** (RX-07 반영)
- **Collect 전**: domain-skeleton.json entity_key 목록 사전 확인 (RX-10 반영)

### Query/Discovery Strategy

| GU ID | 검색 쿼리 | 기대 출처 | 언어 |
|-------|-----------|-----------|------|
| GU-0030 | "Tokyo Subway Ticket price 2026 March increase" | 도쿄메트로 공식, 토에이교통 | en/ja |
| GU-0006 | "ryokan price range per night Japan 2026" | Booking.com, じゃらん, JNTO | en |
| GU-0014 | "Japan ATM cash withdrawal tourist 7-Eleven convenience store" | japan-guide, JNTO | en |
| GU-0009 | "Tokyo Skytree admission fee 2026 observation deck" | 스카이트리 공식 | en |
| GU-0019 | "Japan eSIM comparison price 2026 tourist Airalo Holafly" | eSIM 비교 사이트 | en |
| GU-0020 | "Japan taxi fare base rate 2026 Tokyo" | 택시 협회, japan-guide | en |
| GU-0029 | "Tokyo Subway Ticket where to buy airport station" | 도쿄메트로 공식 | en |
| GU-0022 | "Japan luggage forwarding takkyubin tourist hotel" | japan-guide, yamato | en |
| (추가) | "Japan tax free minimum amount 5000 yen 2026 official" | 관세청, 국세청 | en/ja |

### Acceptance Tests

| GU ID | 해결 조건 | 최소 EU 수 | 독립성 | 신선도 |
|-------|-----------|------------|--------|--------|
| GU-0030 | 인상 후 가격(24h/48h/72h) 공식 출처 확인 | 2 | 공식 1 + 독립 1 | 2026.3+ |
| GU-0006 | 지역별(교토/하코네/아타미 등) 가격대, 시즌 영향 | 2 | 독립 2 | 2024+ |
| GU-0014 | ATM 종류(7-Eleven/우체국), 수수료, 환전소, 현금 필요 장소 | 1 | - | 2024+ |
| GU-0009 | 350m/450m 전망대 가격, 할인 정보 | 2 | 공식 1 + 독립 1 | 2025+ |
| GU-0019 | eSIM 3개+ 제공사 가격 비교. disputed 해결 판단 근거 | 2 | 독립 2 | 2026+ |
| GU-0020 | 기본요금, 심야할증, 호출앱(GO/JapanTaxi) | 2 | 독립 2 | 2025+ |
| GU-0029 | 공항(나리타/하네다), 역, 온라인 판매처 목록 | 1 | - | 2025+ |
| GU-0022 | 접수처(편의점/호텔/역), 요금, 소요일수, 사이즈 제한 | 1 | - | 2024+ |

### Budget & Stop Rules

- 수집 상한: **15회 검색**
- 중복 상한: 동일 출처 3회 초과 시 전환
- 품질 미달 중단: 신뢰도 0.5 미만 EU 3개 연속 시 Gap 보류
- 조기 종료: 8개 Target Gap + 추가 검증 태스크 모두 resolved/deferred 시
- **disputed 해결 기준**: 2개 이상 독립 공식 출처가 동일 값 보고 시 해결 판정

---

## 7. Critique→Plan 컴파일 규칙 (메타, 누적)

> Cycle 0~1에서 도출된 일반화 가능한 변환 규칙.

| 실패모드 | → Plan 변경 유형 | 규칙 |
|----------|------------------|------|
| Epistemic | Source Strategy 강화 + 추가 검증 쿼리 | 단일 출처 financial/safety KU → 해당 Gap 재타겟 또는 추가 EU 수집. min_eu ≥ 2 강제. 공식 출처 필수 포함. |
| Temporal | Gap Priority 상향 | expires_at 접근 KU → 관련 Gap 우선순위 상향. TTL 기준일 - 30일 이내면 critical 승격. 가격 변동 과도기 주의. |
| Structural | Schema deferred → Outer Loop | 3단계+ 중첩 → 엔티티 분리 검토 플래그. 3 Cycle 축적 후 Outer Loop에서 결정. |
| Consistency | 추가 수집 + 조건 분석 | hold → Cycle N+1에서 독립 출처 추가 수집. condition_split → 조건별 데이터 검증. **disputed 해결 시 공식 출처 2개+ 일치 필요.** |
| Planning | Gap Selection 기준 확대 | 카테고리 분포 체크. 미커버 비율 > 50%면 강제 포함. |
| Integration | Entity Resolution 강화 | **Collect 전 entity_key 사전 참조.** 유사 키 발견 시 기존 키 우선. is_a/part_of 관계 필요 시 Structural 에스컬레이션. |

---

## 8. design-v2 피드백 (Cycle 1 경험)

| 항목 | 현행 (design-v2) | 개선 제안 | 긴급도 |
|------|-------------------|-----------|--------|
| Entity Resolution §6 | 캐노니컬 키 기반 매칭만 | **alias 매핑** 추가 필요. 동일 상품의 다중 명칭(metro-pass ↔ subway-ticket) 처리. | medium |
| Conflict Resolution | hold / condition_split / coexist 3가지 | Cycle 1에서 두 가지 모두 실전 검증 완료. **해결 판정 기준**(공식 출처 N개 일치 시 해결) 명문화 필요. | medium |
| 동적 GU 발견 | gu-bootstrap-spec §2 참조 | Cycle 1에서 첫 실용성 검증 성공 (3개 발견, 상한 이내, 트리거 분류 기록). **검증 결과 양호 — 현행 유지.** | - |
| Metrics 임계치 | 충돌률 주의 0.06~0.15 | Cycle 1 충돌률 0.095 — 주의 구간. 충돌이 구조적 보존이므로 자연스러운 현상. **임계치 자체는 적절.** | - |
