# KB Patch — Cycle 1

> **단계**: (IN) Integrate | **도메인**: japan-travel
> **생성일**: 2026-03-03
> **입력**: Evidence Claim Set C1 (24 Claims, 15 EU)

---

## 패치 통계

| 항목 | 값 |
|------|----|
| 신규 KU (add) | 7 (KU-0014 ~ KU-0020) |
| 기존 KU 업데이트 (update) | 2 (KU-0007, KU-0011) |
| 충돌 KU (disputed) | 2 (KU-0007, KU-0011) |
| rejected Claim | 0 |
| Gap resolved | 7 (GU-0001,0003,0007,0008,0010,0013,0026) |
| Gap partially resolved | 1 (GU-0019 → disputed로 전환) |
| 동적 GU 신규 | 3 (GU-0029,0030,0031) |

---

## 1. Entity Resolution 결과

| Claim | entity_key | 매칭 결과 | 판정 |
|-------|-----------|-----------|------|
| C1-01~04 | japan-travel:pass-ticket:jr-pass | nozomi-alternative: 기존 KU 없음 | **new** (KU-0014) |
| C1-05~07 | japan-travel:transport:tokyo-metro | how_to_use: 기존 KU 없음 | **new** (KU-0015) |
| C1-06 | japan-travel:pass-ticket:tokyo-subway-ticket | price: 기존 KU 없음 | **new** (KU-0016) |
| C1-08~10 | japan-travel:accommodation:ryokan | etiquette: 기존 KU 없음 | **new** (KU-0017) |
| C1-11~13 | japan-travel:dining:izakaya | etiquette: 기존 KU 없음 | **new** (KU-0018) |
| C1-14~15 | japan-travel:attraction:fushimi-inari | hours: 기존 KU 없음 | **new** (KU-0019) |
| C1-16~17 | japan-travel:connectivity:sim-card | price: **KU-0007** 일치 | **update + disputed** |
| C1-18~21 | japan-travel:regulation:tax-free | procedure_2026_nov: 기존 필드 없음 | **new** (KU-0020) |
| C1-20 | japan-travel:regulation:tax-free | policy: **KU-0011** 일치 | **update + disputed** |
| C1-22~24 | japan-travel:payment:credit-card | acceptance: 기존 KU 없음 | **new** (KU-0021) |

---

## 2. 신규 KU (add)

### KU-0014: JR Pass Nozomi 대안 비교
```json
{
  "ku_id": "KU-0014",
  "entity_key": "japan-travel:pass-ticket:jr-pass",
  "field": "nozomi-alternative",
  "value": {
    "도쿄-신오사카": {
      "Nozomi": {"소요": "2시간 21분", "JR_Pass": false},
      "Hikari": {"소요": "약 3시간", "JR_Pass": true},
      "Kodama": {"소요": "약 4시간", "JR_Pass": true}
    },
    "도쿄-교토": {
      "Hikari": {"소요": "약 2시간 40분", "JR_Pass": true}
    },
    "Hikari_운행": "약 30분 간격, 06:00~21:30",
    "요약": "JR Pass 이용 시 Hikari가 최적. Nozomi 대비 약 30-40분 추가 소요."
  },
  "observed_at": "2026-03-03",
  "validity": {"ttl_days": 365},
  "evidence_links": ["EU-0019", "EU-0020"],
  "confidence": 0.85,
  "status": "active"
}
```

### KU-0015: 도쿄 메트로 이용법
```json
{
  "ku_id": "KU-0015",
  "entity_key": "japan-travel:transport:tokyo-metro",
  "field": "how_to_use",
  "value": "도쿄 메트로 9개 노선 + 토에이 지하철 4개 노선 = 13개 지하철 노선. IC카드(Suica/PASMO) 사용 가능. 관광객용 Tokyo Subway Ticket으로 무제한 이용 가능. 자동 운임 계산. Welcome Suica/PASMO 이용 시 지하철+버스+편의점 결제 가능.",
  "observed_at": "2026-03-03",
  "validity": {"ttl_days": 365},
  "evidence_links": ["EU-0021", "EU-0023"],
  "confidence": 0.90,
  "status": "active"
}
```

### KU-0016: Tokyo Subway Ticket 가격
```json
{
  "ku_id": "KU-0016",
  "entity_key": "japan-travel:pass-ticket:tokyo-subway-ticket",
  "field": "price",
  "value": {
    "24시간": 1000,
    "48시간": 1500,
    "72시간": 2000,
    "currency": "JPY",
    "적용일": "2026-03-14~",
    "이전_가격": {"24시간": 600, "48시간": 1200, "72시간": 1500},
    "대상_노선": "도쿄 메트로 전 노선 + 토에이 지하철 전 노선"
  },
  "observed_at": "2026-03-03",
  "validity": {"ttl_days": 180},
  "evidence_links": ["EU-0022"],
  "confidence": 0.80,
  "status": "active"
}
```

### KU-0017: 료칸 에티켓
```json
{
  "ku_id": "KU-0017",
  "entity_key": "japan-travel:accommodation:ryokan",
  "field": "etiquette",
  "value": {
    "입실": "현관에서 신발 벗기. 석식 제공 시 18:00까지 도착 권장.",
    "유카타": "실내 착용. 왼쪽이 위 (오른쪽 위는 고인용).",
    "온천": "완전 탈의 필수, 입수 전 세신, 머리카락 물 접촉 금지, 수건 욕조 반입 불가. 남녀 분리 (교대 운영 가능).",
    "매너": "22시 이후 소음 자제 (종이벽). 팁 불필요, 전달 시 봉투 사용."
  },
  "observed_at": "2026-03-03",
  "validity": {"ttl_days": 730},
  "evidence_links": ["EU-0024", "EU-0025"],
  "confidence": 0.85,
  "status": "active"
}
```

### KU-0018: 이자카야 에티켓
```json
{
  "ku_id": "KU-0018",
  "entity_key": "japan-travel:dining:izakaya",
  "field": "etiquette",
  "value": {
    "오토시": "착석 시 자동 제공되는 작은 안주. 테이블 차지 겸용 300~700엔. 거절 불가.",
    "주문법": "먼저 음료 주문 (맥주 관습). 메뉴 가리키기 OK. 터치패널 영어 전환 가능.",
    "결제": "출구 레지에서 계산. 팁 불필요."
  },
  "observed_at": "2026-03-03",
  "validity": {"ttl_days": 730},
  "evidence_links": ["EU-0026", "EU-0027"],
  "confidence": 0.85,
  "status": "active"
}
```

### KU-0019: 후시미이나리 운영시간
```json
{
  "ku_id": "KU-0019",
  "entity_key": "japan-travel:attraction:fushimi-inari",
  "field": "hours",
  "value": {
    "경내": "24시간 연중무휴, 입장료 없음",
    "상점": "09:00~17:00",
    "추천_시간": "이른 아침(일출) 또는 18시 이후 (혼잡 회피). 야간 등롱 조명."
  },
  "observed_at": "2026-03-03",
  "validity": {"ttl_days": 365},
  "evidence_links": ["EU-0028", "EU-0029"],
  "confidence": 0.95,
  "status": "active"
}
```

### KU-0020: 면세 신제도 절차 (2026.11)
```json
{
  "ku_id": "KU-0020",
  "entity_key": "japan-travel:regulation:tax-free",
  "field": "procedure_2026_nov",
  "value": {
    "방식": "환급형 — 구매 시 세금 포함 결제 → 출국 시 공항 세관에서 환급",
    "절차": [
      "1. 구매 시 여권 제시 (필수)",
      "2. 매장이 구매기록을 면세판매관리시스템에 등록",
      "3. 세금 포함 가격으로 결제",
      "4. 출국 시 공항 세관에서 여권+영수증+물품 확인",
      "5. 세관 확인 후 환급 승인"
    ],
    "변경점": {
      "소모품_비소모품_구분": "폐지",
      "봉인포장": "폐지",
      "구매_상한_50만엔": "폐지 (100만엔 초과 시 상세 등록)",
      "최소금액": "5,000엔 (세전) 유지"
    },
    "환급_방법": "소매점별 상이 — 신용카드 1~2주, 은행이체 2~4주",
    "유효기간": "구매 후 90일 이내 출국"
  },
  "observed_at": "2026-03-03",
  "validity": {"ttl_days": 90, "expires_at": "2026-11-01"},
  "evidence_links": ["EU-0032", "EU-0033"],
  "confidence": 0.90,
  "status": "active"
}
```

### KU-0021: 신용카드 사용 범위
```json
{
  "ku_id": "KU-0021",
  "entity_key": "japan-travel:payment:credit-card",
  "field": "acceptance",
  "value": {
    "통용_브랜드": "Visa, Mastercard (최광범위), AMEX, JCB, Diners Club, Discover",
    "사용_가능": "주요 호텔, 백화점, 대형 쇼핑몰, 체인 레스토랑, 편의점, 관광지",
    "현금_필요": "소규모 음식점 (라멘집, 가족경영), 노점/축제, 신사/사찰, 소도시 택시, 소규모 의원, 코인세탁소, 가챠폰",
    "교통": "단거리 전철/지하철 요금은 카드 불가 → IC카드(Suica/PASMO) 권장",
    "추세": "대도시 캐시리스 결제 급속 확대 중이나, 현금 항시 소지 권장"
  },
  "observed_at": "2026-03-03",
  "validity": {"ttl_days": 180},
  "evidence_links": ["EU-0034", "EU-0035"],
  "confidence": 0.85,
  "status": "active"
}
```

---

## 3. 기존 KU 업데이트 (update + disputed)

### KU-0007 (sim-card:price) → disputed
**변경 사항**: eSIM 보급으로 가격 구조 크게 변화. 기존 물리SIM 가격 범위와 eSIM 가격 불일치.

```json
{
  "ku_id": "KU-0007",
  "entity_key": "japan-travel:connectivity:sim-card",
  "field": "price",
  "value": {
    "eSIM_2026": {
      "저용량_3GB_30일": "$3.50~$9 USD (약 525~1,350 JPY)",
      "중용량_10-20GB_30일": "$17~$26 USD (약 2,550~3,900 JPY)",
      "무제한_7일": "$19~$25 USD (약 2,850~3,750 JPY)",
      "무제한_30일": "$55~$66 USD (약 8,250~9,900 JPY)",
      "주요_제공사": "Ubigi, Airalo, Saily, Mobal, Sakura Mobile, Holafly"
    },
    "물리SIM_기존": {
      "7일_3GB": "약 1500-3000 JPY",
      "15일_무제한_저속": "약 3000-5000 JPY",
      "구매처": "공항 자판기, 편의점, 온라인 사전주문"
    }
  },
  "observed_at": "2026-03-03",
  "validity": {"ttl_days": 180},
  "evidence_links": ["EU-0006", "EU-0030", "EU-0031"],
  "confidence": 0.80,
  "status": "disputed",
  "disputes": [
    {
      "conflicting_ku_id": "KU-0007_v0",
      "nature": "eSIM 보급으로 가격 구조 변화. 기존 물리SIM 가격 범위와 eSIM 가격 불일치 (eSIM이 대폭 저렴)",
      "resolution": "condition_split"
    }
  ]
}
```

> **판정: condition_split** — 물리SIM과 eSIM을 조건 분리. eSIM 가격이 주류로 전환 중이므로, eSIM 정보를 primary로 업데이트하되 물리SIM 정보도 보존.

### KU-0011 (tax-free:policy) → disputed
**변경 사항**: 기존 KU-0011에 "최소금액_제한: 철폐"로 기재 → 신규 수집에서 "5,000엔 유지"로 확인.

```json
변경 필드: value.신제도_2026_11월.최소금액_제한
기존: "철폐"
신규: "5,000엔 (세전) 유지"
```

```json
{
  "disputes": [
    {
      "conflicting_ku_id": "KU-0020",
      "nature": "신제도 최소금액 — KU-0011은 '철폐'로 기재, 복수 출처(JNTO+japantravel)에서 '5,000엔 유지' 확인",
      "resolution": "pending"
    }
  ]
}
```

> **판정: hold** — 복수 신규 출처가 "5,000엔 유지"를 일관 보고. KU-0011의 "철폐" 기재는 초기 보도 기반 오류 가능성. KU-0020에 정확한 정보 기록 완료. KU-0011은 disputed로 전환하되, 신제도 시행(2026.11) 전까지 hold.

---

## 4. 동적 GU 발견 (gu-bootstrap-spec §2)

### 트리거 분석

| # | 트리거 | 원인 | 신규 GU |
|---|--------|------|---------|
| 1 | A: 인접 Gap | KU-0016 (tokyo-subway-ticket:price) — Skeleton에 없는 엔티티. 구매처 정보 미확보 | GU-0029 |
| 2 | B: Epistemic | KU-0016 단일출처 + financial (패스 가격) | GU-0030 |
| 3 | A: 인접 Gap | KU-0015 (tokyo-metro:how_to_use) 참조하는 노선별 환승/혼잡도 미확보 | GU-0031 |

**상한 체크**: open GU 21개 → 20% = 4.2 → 상한 4개. 신규 3개 → **상한 이내** ✓

### GU-0029: Tokyo Subway Ticket 구매처
```json
{
  "gu_id": "GU-0029",
  "gap_type": "missing",
  "target": {"entity_key": "japan-travel:pass-ticket:tokyo-subway-ticket", "field": "where_to_buy"},
  "expected_utility": "medium",
  "risk_level": "convenience",
  "resolution_criteria": "판매 장소(공항, 역, 온라인), 구매 방법",
  "status": "open",
  "created_at": "2026-03-03"
}
```

### GU-0030: Tokyo Subway Ticket 가격 교차확인
```json
{
  "gu_id": "GU-0030",
  "gap_type": "uncertain",
  "target": {"entity_key": "japan-travel:pass-ticket:tokyo-subway-ticket", "field": "price"},
  "expected_utility": "medium",
  "risk_level": "financial",
  "resolution_criteria": "2026.3.14 이후 가격 변경 공식 출처 확인",
  "status": "open",
  "created_at": "2026-03-03"
}
```

### GU-0031: 도쿄 메트로 노선 가이드
```json
{
  "gu_id": "GU-0031",
  "gap_type": "missing",
  "target": {"entity_key": "japan-travel:transport:tokyo-metro", "field": "tips"},
  "expected_utility": "medium",
  "risk_level": "convenience",
  "resolution_criteria": "주요 노선별 관광지 연결, 환승 팁, 혼잡 시간대",
  "status": "open",
  "created_at": "2026-03-03"
}
```

---

## 5. Gap 해결 상태 변경

| GU ID | 이전 | 이후 | resolved_by |
|-------|------|------|-------------|
| GU-0001 | open | **resolved** | KU-0014 |
| GU-0003 | open | **resolved** | KU-0015 |
| GU-0007 | open | **resolved** | KU-0017 |
| GU-0008 | open | **resolved** | KU-0019 |
| GU-0010 | open | **resolved** | KU-0018 |
| GU-0013 | open | **resolved** | KU-0021 |
| GU-0026 | open | **resolved** | KU-0020 |
| GU-0019 | open | open (disputed) | KU-0007 update, 충돌 발생으로 완전 해결 미달 |

---

## 6. Claim→KU 착지성 검증

| 항목 | 수 | 비고 |
|------|----|------|
| 총 Claim | 24 | |
| → 신규 KU (add) | 7건 (21 Claims 반영) | C1-01~04, C1-05~07, C1-08~10, C1-11~13, C1-14~15, C1-18~21, C1-22~24 |
| → 기존 KU 업데이트 | 2건 (3 Claims 반영) | C1-16~17 → KU-0007, C1-20 → KU-0011 |
| → rejected (사유 명시) | 0 | |
| **합계** | 24 = 21 + 3 + 0 ✓ | 불변원칙 #2 준수 |
