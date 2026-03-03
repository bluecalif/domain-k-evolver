# Evidence Claim Set — Cycle 0

> **단계**: (C) Collect | **도메인**: japan-travel
> **생성일**: 2026-03-02
> **Collection Plan 참조**: Cycle 0

---

## 수집 요약

- **타겟 Gap 수**: 7
- **수집된 Claim 수**: 7
- **수집된 EU 수**: 11
- **중복/상충 후보**: 1건 (JR Pass 가격 — 기존 KU-0002와 교차확인)

---

## Claims

### Claim C0-01: japan-travel:regulation:emergency — policy (GU-0025)

- **대상 Gap**: GU-0025
- **값**: {"경찰": "110", "소방/구급": "119", "해상긴급": "118", "의료상담": "#7119", "관광헬프라인": "050-3816-2787", "재해전언다이얼": "171", "비고": "구급차 무료, 치료비는 별도. 119/110은 일본어 우선이나 통역 연결 가능."}
- **조건**: 무조건
- **신뢰도 (추정)**: 0.95

#### Evidence Bundle
| EU ID | 출처 | 유형 | 수집일 | 스니펫 |
|-------|------|------|--------|--------|
| EU-0007 | https://www.japan-guide.com/e/e2229.html | public | 2026-03-02 | "Police: 110, Fire/Ambulance: 119. Ambulance service is free of charge." |
| EU-0008 | https://discoverjapansites.com/emergency-safety-guide-japan-2025/ | public | 2026-03-02 | "Tourist Info Helpline: 050-3816-2787. Medical consultation: #7119." |

#### 사전 태깅
- **중복 후보**: 없음 (신규)
- **상충 후보**: 없음
- **비고**: safety 등급 — 2개 독립 출처 확보로 교차검증 충족

---

### Claim C0-02: japan-travel:transport:airport-transfer — how_to_use (GU-0005)

- **대상 Gap**: GU-0005
- **값**: {"나리타": {"Narita_Express": {"소요": "60분→도쿄역", "가격": "3070 JPY", "비고": "JR Pass 이용 가능"}, "Skyliner": {"소요": "36분→닛포리", "가격": "약 2520 JPY"}, "리무진버스": {"소요": "75-90분", "가격": "약 1500-3200 JPY"}}, "하네다": {"모노레일": {"소요": "20분→하마마츠초", "가격": "약 500-600 JPY"}, "게이큐선": {"소요": "15분→시나가와", "가격": "약 300 JPY"}, "리무진버스": {"소요": "약 45분", "가격": "약 1000-1500 JPY"}}}
- **조건**: 무조건
- **신뢰도 (추정)**: 0.85

#### Evidence Bundle
| EU ID | 출처 | 유형 | 수집일 | 스니펫 |
|-------|------|------|--------|--------|
| EU-0009 | https://tokyocheapo.com/travel/transport/cheapest-transport-to-and-from-narita-airport/ | public | 2026-03-02 | "N'EX to Tokyo Station ~60 min ¥3,070. Skyliner to Nippori 36 min." |
| EU-0010 | https://trulytokyo.com/tokyo-airport-transport/ | public | 2026-03-02 | "Haneda: Monorail ~20 min ¥500-600, Keikyu ~15 min to Shinagawa." |

#### 사전 태깅
- **중복 후보**: 없음
- **상충 후보**: 없음
- **비고**: 가격은 개략치, 시기별 변동 가능

---

### Claim C0-03: japan-travel:pass-ticket:jr-pass — price (GU-0002)

- **대상 Gap**: GU-0002
- **값**: {"7일권": {"ordinary": 50000, "green": 70000}, "14일권": {"ordinary": 80000, "green": 110000}, "21일권": {"ordinary": 100000, "green": 140000}, "currency": "JPY", "비고": "2023년 10월 인상 후 가격 유지 중. 2025-2026년 추가 인상 없음."}
- **조건**: {"traveler_type": "temporary-visitor"}
- **신뢰도 (추정)**: 0.95

#### Evidence Bundle
| EU ID | 출처 | 유형 | 수집일 | 스니펫 |
|-------|------|------|--------|--------|
| EU-0011 | https://japanrailpass.net/en/purchase/price/ | official | 2026-03-02 | "7-day Ordinary ¥50,000, 14-day ¥80,000, 21-day ¥100,000." |

#### 사전 태깅
- **중복 후보**: KU-0002 (기존 — 가격 동일, 확인 완료)
- **상충 후보**: 없음
- **비고**: 기존 KU-0002 가격 확인됨. confidence 0.90→0.95 상향 가능.

---

### Claim C0-04: japan-travel:regulation:visit-japan-web — how_to_use (GU-0017)

- **대상 Gap**: GU-0017
- **값**: "Visit Japan Web은 웹 기반 서비스(앱 불필요). 여권 정보, 입국심사(하선카드), 세관신고, 면세쇼핑 3개 항목 사전 등록. 등록 후 QR코드 발급 → 공항 도착 시 제시. 2026년 현재 필수는 아니나 강력 권장 (심사 시간 대폭 단축). 스크린샷 불가, 라이브 접속 필요."
- **조건**: 무조건
- **신뢰도 (추정)**: 0.90

#### Evidence Bundle
| EU ID | 출처 | 유형 | 수집일 | 스니펫 |
|-------|------|------|--------|--------|
| EU-0012 | https://services.digital.go.jp/en/visit-japan-web/ | official | 2026-03-02 | "Visit Japan Web: immigration, customs, tax-exemption online registration." |
| EU-0013 | https://www.klook.com/blog/visit-japan-web-guide/ | platform | 2026-03-02 | "Not strictly mandatory but strongly encouraged. QR code must be accessed live." |

#### 사전 태깅
- **중복 후보**: 없음
- **상충 후보**: 없음
- **비고**: 필수/권장 여부에 대해 공식 사이트는 "recommended"로 표현

---

### Claim C0-05: japan-travel:regulation:tax-free — policy (GU-0012)

- **대상 Gap**: GU-0012
- **값**: {"현행_2025": {"최소금액": "5000 JPY (세전, 1일 1매장)", "대상": "비소모품(전자기기/의류) + 소모품(식품/화장품) 각각 5000-500000 JPY", "절차": "여권 제시 → 매장에서 즉시 면세", "제한": "국제 소포 발송 품목 면세 불가 (2025.4~)"}, "신제도_2026_11월": {"방식": "환급형 (구매 시 세금 포함 결제 → 출국 시 환급 신청)", "최소금액": "제한 철폐", "봉인포장": "폐지", "비고": "2026년 11월 1일 시행 예정"}}
- **조건**: 무조건
- **신뢰도 (추정)**: 0.90

#### Evidence Bundle
| EU ID | 출처 | 유형 | 수집일 | 스니펫 |
|-------|------|------|--------|--------|
| EU-0014 | https://www.japan.travel/en/plan/japans-tax-exemption/ | official | 2026-03-02 | "Tax exemption for purchases over ¥5,000 at licensed stores." |
| EU-0015 | https://en.japantravel.com/article/tax-free-shopping-in-japan-2026-changes/72305 | public | 2026-03-02 | "From Nov 2026, shift to refund-based system. Sealed packaging requirement abolished." |

#### 사전 태깅
- **중복 후보**: 없음
- **상충 후보**: 없음 (현행+신제도 병기, 시간 조건으로 분리)
- **비고**: 2026년 11월 제도 변경 예정 — TTL 관리 중요

---

### Claim C0-06: japan-travel:pass-ticket:suica — where_to_buy (GU-0018)

- **대상 Gap**: GU-0018
- **값**: {"Welcome_Suica": {"판매처": "JR East Travel Service Center (나리타/하네다/도쿄/우에노/이케부쿠로/시부야/시나가와)", "보증금": "없음", "유효기간": "28일", "환불": "불가", "비고": "2025.3월 반도체 부족 공식 해소. 2026.1월 기준 주요 거점 판매 재개."}, "Welcome_Suica_Mobile": {"대상": "iPhone (Apple Pay 지원)", "유효기간": "180일", "비고": "2025.3월 출시. 물리카드보다 긴 유효기간."}, "대안": "PASMO Passport (사철 역), ICOCA (관서 지역)"}
- **조건**: 무조건
- **신뢰도 (추정)**: 0.85

#### Evidence Bundle
| EU ID | 출처 | 유형 | 수집일 | 스니펫 |
|-------|------|------|--------|--------|
| EU-0016 | https://www.jreast.co.jp/en/multi/welcomesuica/purchase.html | official | 2026-03-02 | "Welcome Suica available at JR East Travel Service Centers." |
| EU-0017 | https://www.getaroundjapan.jp/archives/9146 | platform | 2026-03-02 | "Chip shortage ended March 2025. Welcome Suica Mobile app launched March 2025, valid 180 days." |

#### 사전 태깅
- **중복 후보**: KU-0004 (IC카드 일반 사용법 — 보완 관계)
- **상충 후보**: 없음
- **비고**: KU-0004의 "물리 카드 재고 부족" 정보 업데이트 필요

---

### Claim C0-07: japan-travel:transport:shinkansen — price (GU-0024)

- **대상 Gap**: GU-0024
- **값**: {"도쿄-교토": {"자유석": "13320 JPY", "지정석_Hikari": "약 14570 JPY", "Platt_Kodama": "10700 JPY"}, "도쿄-신오사카": {"지정석": "약 14720 JPY", "Platt_Kodama": "11110 JPY"}, "구성": "기본운임 + 특급요금. Nozomi 추가 210-1060 JPY.", "비고": "JR Pass(7일 50000 JPY)로 도쿄-교토 왕복만 해도 가격 비슷."}
- **조건**: 무조건
- **신뢰도 (추정)**: 0.85

#### Evidence Bundle
| EU ID | 출처 | 유형 | 수집일 | 스니펫 |
|-------|------|------|--------|--------|
| EU-0018 | https://tokyocheapo.com/travel/transport/how-much-does-it-cost-to-ride-the-shinkansen/ | public | 2026-03-02 | "Tokyo-Kyoto non-reserved ¥13,320. Base fare ¥8,360 + surcharge ¥4,960." |

#### 사전 태깅
- **중복 후보**: 없음
- **상충 후보**: 없음
- **비고**: 개별 구매 vs JR Pass 비교 데이터로 활용 가능

---

## 수집 메타데이터

| 항목 | 값 |
|------|-----|
| 총 검색 횟수 | 7 |
| 사용 출처 수 | 12 (중복 제외) |
| 품질 미달 폐기 | 0건 |
| Stop Rule 발동 | 없음 |
