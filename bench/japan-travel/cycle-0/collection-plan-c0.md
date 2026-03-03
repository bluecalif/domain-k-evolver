# Collection Plan — Cycle 0

> **단계**: (P) Plan | **도메인**: japan-travel
> **생성일**: 2026-03-02
> **기반**: Gap Map 상태 Seed (v0)

---

## 1. Target Gaps (우선순위순)

| 순위 | GU ID | 유형 | 대상 | 기대효용 | 리스크 | 선정 이유 |
|------|-------|------|------|----------|--------|-----------|
| 1 | GU-0025 | missing | emergency:policy | critical | safety | 안전 최우선. 긴급 연락처는 모든 여행자 필수 |
| 2 | GU-0005 | missing | airport-transfer:how_to_use | critical | convenience | 도착 직후 필요한 핵심 정보 |
| 3 | GU-0002 | uncertain | jr-pass:price | high | financial | 기존 KU 신뢰도 확인 필요 (가격 변동 가능) |
| 4 | GU-0017 | missing | visit-japan-web:how_to_use | high | policy | 입국 전 필수 절차 가능성 |
| 5 | GU-0012 | missing | tax-free:policy | high | financial | 쇼핑 시 즉시 적용 가능한 절약 정보 |
| 6 | GU-0018 | missing | suica:where_to_buy | high | convenience | IC카드 구매 상황 변동 중 |
| 7 | GU-0024 | missing | shinkansen:price | high | financial | JR Pass 외 개별 구매 비용 비교 필요 |

---

## 2. Source Strategy

### 출처군 우선순위

| 순위 | 출처군 | 대상 Gap | 기대 신뢰도 | 접근 방법 |
|------|--------|----------|-------------|-----------|
| 1 | 공식 사이트 (JR, 정부) | GU-0002, 0025, 0017 | 0.95 | 직접 URL 접근 |
| 2 | japan-guide.com | GU-0005, 0012, 0018, 0024 | 0.80 | WebSearch → WebFetch |
| 3 | 여행 정보 포털 | 전체 보조 | 0.65 | WebSearch |

### 교차확인 규칙 (이번 Cycle 적용)
- GU-0025 (safety): 반드시 공식 출처 + 1개 이상 독립 확인
- GU-0002 (financial): 공식 사이트 가격 우선, 블로그 교차확인
- 나머지: 1개 신뢰 출처 + 신뢰도 ≥ 0.7이면 수용

---

## 3. Query/Discovery Strategy

| GU ID | 검색 쿼리 | 기대 출처 | 언어 |
|-------|-----------|-----------|------|
| GU-0025 | "Japan emergency numbers tourists 2025 2026" | 정부/대사관 | en |
| GU-0005 | "Narita Haneda airport to Tokyo transport options 2025 2026" | japan-guide | en |
| GU-0002 | "Japan Rail Pass price 2025 2026" | JR 공식 | en |
| GU-0017 | "Visit Japan Web registration guide 2025 2026" | 정부 | en |
| GU-0012 | "Japan tax free shopping rules tourists 2025 2026" | 관세청/관광청 | en |
| GU-0018 | "Suica card buy 2025 2026 tourist" | JR East | en |
| GU-0024 | "Shinkansen ticket price Tokyo Osaka 2025 2026" | JR | en |

---

## 4. Acceptance Tests

| GU ID | 해결 조건 | 최소 EU 수 | 독립성 요건 | 신선도 요건 |
|-------|-----------|------------|-------------|-------------|
| GU-0025 | 경찰/소방/구급 번호 + 외국인 의료기관 | 2 | 독립 2개 | 2024년 이후 |
| GU-0005 | 나리타/하네다 각각 2개 이상 교통편 | 1 | - | 2024년 이후 |
| GU-0002 | 공식 가격표 확인 | 1 | 공식 필수 | 2025년 이후 |
| GU-0017 | 등록 절차 + 필수 여부 확인 | 1 | - | 2024년 이후 |
| GU-0012 | 면세 조건 (금액/물품/절차) | 1 | - | 2024년 이후 |
| GU-0018 | 구매 가능 여부 + 대안 | 1 | - | 2025년 이후 |
| GU-0024 | 주요 구간 2개 이상 요금 | 1 | - | 2024년 이후 |

---

## 5. Budget & Stop Rules

- **수집 상한**: 15회 검색
- **시간 상한**: 이번 세션 내 완료
- **중복 상한**: 동일 출처 3회 초과 시 다른 출처 탐색
- **품질 미달 중단**: 신뢰도 0.5 미만 EU 3개 연속 시 해당 Gap 보류
- **조기 종료**: 7개 Target Gap 모두 resolved/deferred 시 종료
