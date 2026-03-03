# Seed Pack v0

> **단계**: (S) Seed | **도메인**: japan-travel
> **생성일**: 2026-03-02

## 1. 도메인 Scope Boundary

### 포함 범위
- 일본 국내 교통수단 (철도, 버스, 택시, 국내선)
- 숙박 유형 및 예약 관련 정보
- 주요 관광지 입장/운영 정보
- 식당/음식 문화 (주문, 에티켓, 결제)
- 입국/비자/세관 규정
- 패스/티켓 상품 (교통패스, 관광패스)
- 통신 (SIM/eSIM, Wi-Fi)
- 결제 수단 (현금, IC카드, 신용카드)

### 제외 범위
- 출발국 → 일본 항공권 가격/예약 비교
- 여행 보험 상품 비교
- 일본어 학습/회화
- 일본 역사/문화 심층 해설 (관광 목적 이상)
- 장기 체류/취업/유학 비자

### Scope 경계 판정 규칙
- "일본 도착 후부터 출국까지" 여행자가 직접 필요로 하는 실용 정보
- 가격 정보는 정가/공식가 기준 (할인 비교 제외)
- 2024년 이후 유효한 정보만 대상

---

## 2. Domain Skeleton v0

### 엔티티 유형 (Categories)

| Category | 설명 | 슬러그 예시 |
|----------|------|-------------|
| transport | 교통수단/노선/서비스 | jr-pass, suica, shinkansen |
| accommodation | 숙박 유형/서비스 | ryokan, capsule-hotel, airbnb |
| attraction | 관광지/명소 | fushimi-inari, tokyo-skytree |
| dining | 식당/음식 유형/에티켓 | conveyor-sushi, izakaya, tipping |
| regulation | 입국/비자/세관/법규 | tourist-visa, customs-allowance |
| pass-ticket | 교통패스/관광패스 상품 | jr-pass, tokyo-metro-pass |
| connectivity | 통신/인터넷 | sim-card, pocket-wifi |
| payment | 결제수단 | ic-card, credit-card, cash |

### 주요 필드 정의

| 필드명 | 타입 | 적용 카테고리 | 설명 |
|--------|------|---------------|------|
| price | object | all | 가격 정보 {amount, currency, unit} |
| hours | string | attraction, dining | 운영시간 |
| policy | string | regulation, pass-ticket | 규정/조건 텍스트 |
| location | object | attraction, dining, accommodation | 위치 {region, address} |
| duration | string | transport, pass-ticket | 소요시간/유효기간 |
| eligibility | string | pass-ticket, regulation | 이용 자격/조건 |
| how_to_use | string | transport, payment, connectivity | 이용 방법 |
| tips | string | all | 실용 팁 |

### 관계 정의

| 관계 | 소스 → 타겟 | 설명 |
|------|-------------|------|
| covers_route | transport → transport | 노선이 커버하는 구간 |
| valid_for | pass-ticket → transport | 패스로 이용 가능한 교통 |
| located_in | attraction/dining → region | 위치 관계 |
| accepted_at | payment → transport/dining/attraction | 결제수단 사용처 |

### 캐노니컬 키 규칙
- 형식: `japan-travel:{category}:{slug}`
- slug 규칙: 영문 소문자, 하이픈 구분, 공식 영문 명칭 기반
- 예: `japan-travel:transport:jr-pass`, `japan-travel:regulation:tourist-visa`

---

## 3. Seed Knowledge Units

### KU-0001: japan-travel:pass-ticket:jr-pass — eligibility
- **값**: "일본 국외 거주 외국인 여권 소지자. 'Temporary Visitor' 체류자격으로 입국한 자만 구매 가능. 일본 국적자 또는 일본 거주 외국인은 구매 불가."
- **조건**: 무조건
- **신뢰도**: 0.95 (JR 공식 사이트 확인)
- **출처**: EU-0001

### KU-0002: japan-travel:pass-ticket:jr-pass — price
- **값**: {"7일권": {"ordinary": 50000, "green": 70000}, "14일권": {"ordinary": 80000, "green": 110000}, "21일권": {"ordinary": 100000, "green": 140000}, "currency": "JPY"}
- **조건**: {"channel": "일본 국내 구매 기준", "traveler_type": "temporary-visitor"}
- **신뢰도**: 0.90 (2023년 10월 가격 인상 후 기준, 최신 확인 필요)
- **출처**: EU-0001

### KU-0003: japan-travel:regulation:tourist-visa — policy
- **값**: "한국 국적자는 90일 이내 관광 목적 무비자 입국 가능. 여권 잔여 유효기간 제한 없음 (체류 기간 이상 권장). Visit Japan Web 사전 등록 권장."
- **조건**: {"traveler_type": "korean-citizen"}
- **신뢰도**: 0.90 (외무성 기준이나 수시 변경 가능)
- **출처**: EU-0002

### KU-0004: japan-travel:payment:ic-card — how_to_use
- **값**: "Suica/PASMO 등 IC카드로 전철, 버스, 편의점 결제 가능. 2023년부터 물리 카드 재고 부족으로 모바일 Suica(Apple/Google) 권장. 충전은 역 내 기기 또는 앱에서 가능."
- **조건**: 무조건
- **신뢰도**: 0.85 (플랫폼 다수 확인)
- **출처**: EU-0003

### KU-0005: japan-travel:transport:shinkansen — how_to_use
- **값**: "지정석(Reserved)과 자유석(Non-reserved) 구분. JR Pass 소지 시 지정석 무료 예약 가능 (Nozomi/Mizuho 제외). 자유석은 선착순 탑승."
- **조건**: 무조건
- **신뢰도**: 0.90 (JR 공식 + 다수 출처)
- **출처**: EU-0004

### KU-0006: japan-travel:regulation:customs-allowance — policy
- **값**: "면세 범위: 주류 3병(760ml 이하), 담배 200개비(거주자)/400개비(비거주자), 향수 2oz, 기타 품목 20만엔 이하. 초과 시 신고 및 관세 부과."
- **조건**: 무조건
- **신뢰도**: 0.85 (세관 공식 기준이나 세부 변경 가능)
- **출처**: EU-0005

### KU-0007: japan-travel:connectivity:sim-card — price
- **값**: {"7일_3GB": "약 1500-3000 JPY", "15일_무제한(저속)": "약 3000-5000 JPY", "구매처": "공항 자판기, 편의점, 온라인 사전주문"}
- **조건**: 무조건
- **신뢰도**: 0.70 (플랫폼 정보, 업체별 차이 큼)
- **출처**: EU-0006

---

## 4. Seed Evidence Units

### EU-0001
- **출처**: https://www.japanrailpass.net/
- **유형**: official
- **수집일**: 2026-03-02
- **스니펫**: "The Japan Rail Pass is available for purchase by foreign tourists visiting Japan under 'Temporary Visitor' entry status. Prices updated October 2023."

### EU-0002
- **출처**: https://www.mofa.go.jp/j_info/visit/visa/index.html
- **유형**: official
- **수집일**: 2026-03-02
- **스니펫**: "Nationals of the Republic of Korea: General visa exemption for short-term stay up to 90 days for tourism."

### EU-0003
- **출처**: https://www.jreast.co.jp/multi/en/suica/
- **유형**: official
- **수집일**: 2026-03-02
- **스니펫**: "Due to global semiconductor shortage, sales of physical Suica and PASMO cards are limited. Mobile Suica is recommended."

### EU-0004
- **출처**: https://www.jrpass.com/shinkansen
- **유형**: public
- **수집일**: 2026-03-02
- **스니펫**: "JR Pass holders can reserve seats on most Shinkansen trains for free, except Nozomi and Mizuho services."

### EU-0005
- **출처**: https://www.customs.go.jp/english/summary/passenger.htm
- **유형**: official
- **수집일**: 2026-03-02
- **스니펫**: "Duty-free allowances for non-residents: 3 bottles of spirits (760ml each), 400 cigarettes, 2 oz perfume, other goods up to 200,000 JPY."

### EU-0006
- **출처**: https://www.japan-guide.com/e/e2286.html
- **유형**: public
- **수집일**: 2026-03-02
- **스니펫**: "Prepaid SIM cards are available at airports, convenience stores, and online. Typical plans range from 1,500-5,000 yen depending on data and duration."

---

## 5. Gap Map v0

| GU ID | 유형 | 대상 (entity_key:field) | 기대효용 | 리스크 | 해결기준 |
|-------|------|-------------------------|----------|--------|----------|
| GU-0001 | missing | japan-travel:pass-ticket:jr-pass:nozomi-alternative | high | convenience | Nozomi 대신 Hikari/Kodama 시간표 비교 정보 |
| GU-0002 | uncertain | japan-travel:pass-ticket:jr-pass:price | high | financial | 2026년 현재 공식 가격 확인 |
| GU-0003 | missing | japan-travel:transport:tokyo-metro:how_to_use | high | convenience | 노선도, 패스 종류, IC카드 호환성 |
| GU-0004 | missing | japan-travel:pass-ticket:tokyo-metro-pass:price | medium | financial | 1일/2일/3일권 가격 |
| GU-0005 | missing | japan-travel:transport:airport-transfer:how_to_use | critical | convenience | 나리타/하네다 → 시내 교통편 비교 |
| GU-0006 | missing | japan-travel:accommodation:ryokan:price | medium | financial | 가격대, 예약 시기, 지역별 차이 |
| GU-0007 | missing | japan-travel:accommodation:ryokan:etiquette | medium | convenience | 이용 에티켓/매너 |
| GU-0008 | missing | japan-travel:attraction:fushimi-inari:hours | medium | convenience | 운영시간 (24시간 개방 여부) |
| GU-0009 | missing | japan-travel:attraction:tokyo-skytree:price | medium | financial | 전망대 입장료 |
| GU-0010 | missing | japan-travel:dining:izakaya:etiquette | medium | convenience | 주문 방법, 오토시, 결제 관습 |
| GU-0011 | missing | japan-travel:dining:conveyor-sushi:how_to_use | low | convenience | 이용 방법, 주문 시스템 |
| GU-0012 | missing | japan-travel:regulation:tax-free:policy | high | financial | 면세 쇼핑 조건 (5000엔 이상 등) |
| GU-0013 | missing | japan-travel:payment:credit-card:acceptance | medium | financial | 신용카드 사용 가능 범위 |
| GU-0014 | missing | japan-travel:payment:cash:tips | medium | convenience | 현금 사용 팁, ATM 이용법 |
| GU-0015 | missing | japan-travel:connectivity:pocket-wifi:price | low | convenience | 포켓와이파이 대여 가격/방법 |
| GU-0016 | missing | japan-travel:transport:bus:how_to_use | medium | convenience | 시내버스/고속버스 이용법 |
| GU-0017 | missing | japan-travel:regulation:visit-japan-web:how_to_use | high | policy | VJW 등록 절차, 필수 여부 |
| GU-0018 | missing | japan-travel:pass-ticket:suica:where_to_buy | high | convenience | 2026년 기준 Suica 구매/충전 방법 |
| GU-0019 | stale | japan-travel:connectivity:sim-card:price | medium | financial | SIM 가격 최신 확인 필요 |
| GU-0020 | missing | japan-travel:transport:taxi:price | medium | financial | 택시 기본요금, 할증, 호출앱 |
| GU-0021 | missing | japan-travel:accommodation:capsule-hotel:how_to_use | low | convenience | 캡슐호텔 이용법, 가격대 |
| GU-0022 | missing | japan-travel:regulation:luggage-forwarding:how_to_use | medium | convenience | 짐 배송 서비스 (다쿠하이빈) |
| GU-0023 | missing | japan-travel:attraction:universal-studios-japan:price | medium | financial | USJ 입장료, 익스프레스패스 |
| GU-0024 | missing | japan-travel:transport:shinkansen:price | high | financial | JR Pass 외 개별 구매 시 요금 |
| GU-0025 | missing | japan-travel:regulation:emergency:policy | critical | safety | 긴급 연락처, 의료기관 이용법 |

---

## 6. Policy Priors v0

### 출처 유형별 신뢰도

| 출처 유형 | 기본 신뢰도 | 비고 |
|-----------|-------------|------|
| official | 0.95 | JR, 정부기관, 시설 공식 사이트 |
| public | 0.80 | japan-guide.com, 위키, 공공 데이터 |
| platform | 0.65 | 블로그, 리뷰 사이트, 커뮤니티 |
| personal | 0.40 | 개인 경험담, SNS |

### TTL 기본값

| 정보 유형 | TTL (일) | 근거 |
|-----------|----------|------|
| 가격 (price) | 180 | 연 1-2회 개정 일반적 |
| 규정 (policy/regulation) | 90 | 수시 변경 가능, 보수적 설정 |
| 운영시간 (hours) | 90 | 시즌별 변동 |
| 이용방법 (how_to_use) | 365 | 시스템 변경이 드묾 |
| 위치 (location) | 730 | 거의 변동 없음 |
| 에티켓/팁 (etiquette/tips) | 730 | 문화적 관습은 느리게 변화 |

### 교차검증 규칙
- safety/policy/financial 리스크: 독립 출처 2개 이상 필수
- convenience/informational: 1개 출처 + 신뢰도 ≥ 0.7이면 수용
- 충돌 발생 시: disputed 상태로 보존, 추가 수집 요청

### 충돌해결 규칙
- 출처 우선순위: official > public > platform > personal
- 동일 유형 내: 최신 정보 우선 (retrieved_at 비교)
- 조건 차이로 설명 가능: condition_split
- 해결 불가: hold + 다음 Cycle에서 추가 수집
