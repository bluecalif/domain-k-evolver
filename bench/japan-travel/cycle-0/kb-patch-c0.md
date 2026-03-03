# KB Patch — Cycle 0

> **단계**: (I) Integration | **도메인**: japan-travel
> **생성일**: 2026-03-02
> **입력**: Evidence Claim Set Cycle 0

---

## 패치 요약

| 항목 | 수량 |
|------|------|
| 신규 KU 추가 | 6 |
| 기존 KU 수정 | 2 |
| KU 폐기 | 0 |
| 충돌 처리 | 0건 |
| Gap 해결 | 7 |
| 신규 Gap 발견 | 3 |

---

## 1. Adds (신규 KU)

### KU-0008: japan-travel:regulation:emergency — policy
- **entity_key**: japan-travel:regulation:emergency
- **field**: policy
- **value**: {"경찰": "110", "소방/구급": "119", "해상긴급": "118", "의료상담": "#7119", "관광헬프라인": "050-3816-2787", "재해전언다이얼": "171", "비고": "구급차 무료, 치료비는 별도. 119/110은 일본어 우선이나 통역 연결 가능."}
- **conditions**: 무조건
- **confidence**: 0.95
- **evidence**: [EU-0007, EU-0008]
- **출처 Claim**: C0-01

### KU-0009: japan-travel:transport:airport-transfer — how_to_use
- **entity_key**: japan-travel:transport:airport-transfer
- **field**: how_to_use
- **value**: {"나리타": {"Narita_Express": {"소요": "60분→도쿄역", "가격": "3070 JPY", "JR_Pass": true}, "Skyliner": {"소요": "36분→닛포리", "가격": "약 2520 JPY"}, "리무진버스": {"소요": "75-90분", "가격": "약 1500-3200 JPY"}}, "하네다": {"모노레일": {"소요": "20분→하마마츠초", "가격": "약 500-600 JPY"}, "게이큐선": {"소요": "15분→시나가와", "가격": "약 300 JPY"}, "리무진버스": {"소요": "약 45분", "가격": "약 1000-1500 JPY"}}}
- **conditions**: 무조건
- **confidence**: 0.85
- **evidence**: [EU-0009, EU-0010]
- **출처 Claim**: C0-02

### KU-0010: japan-travel:regulation:visit-japan-web — how_to_use
- **entity_key**: japan-travel:regulation:visit-japan-web
- **field**: how_to_use
- **value**: "Visit Japan Web은 웹 기반 서비스(앱 불필요). 여권 정보, 입국심사(하선카드), 세관신고, 면세쇼핑 3개 항목 사전 등록. 등록 후 QR코드 발급 → 공항 도착 시 제시. 2026년 현재 필수는 아니나 강력 권장 (심사 시간 대폭 단축). 스크린샷 불가, 라이브 접속 필요."
- **conditions**: 무조건
- **confidence**: 0.90
- **evidence**: [EU-0012, EU-0013]
- **출처 Claim**: C0-04

### KU-0011: japan-travel:regulation:tax-free — policy
- **entity_key**: japan-travel:regulation:tax-free
- **field**: policy
- **value**: {"현행_2025": {"최소금액": "5000 JPY (세전, 1일 1매장)", "대상": "비소모품+소모품 각 5000-500000 JPY", "절차": "여권 제시 → 매장 즉시 면세", "제한": "국제소포 발송 품목 면세 불가 (2025.4~)"}, "신제도_2026_11월": {"방식": "환급형 (구매 시 세금 포함 → 출국 시 환급)", "최소금액_제한": "철폐", "봉인포장": "폐지"}}
- **conditions**: 무조건
- **confidence**: 0.90
- **evidence**: [EU-0014, EU-0015]
- **출처 Claim**: C0-05
- **비고**: validity TTL 주의 — 2026년 11월 제도 변경 예정

### KU-0012: japan-travel:pass-ticket:suica — where_to_buy
- **entity_key**: japan-travel:pass-ticket:suica
- **field**: where_to_buy
- **value**: {"Welcome_Suica": {"판매처": "JR East Travel Service Center (나리타/하네다/도쿄/우에노/이케부쿠로/시부야/시나가와)", "보증금": "없음", "유효기간": "28일", "환불": "불가"}, "Welcome_Suica_Mobile": {"대상": "iPhone", "유효기간": "180일"}, "대안": "PASMO Passport, ICOCA (관서)"}
- **conditions**: 무조건
- **confidence**: 0.85
- **evidence**: [EU-0016, EU-0017]
- **출처 Claim**: C0-06

### KU-0013: japan-travel:transport:shinkansen — price
- **entity_key**: japan-travel:transport:shinkansen
- **field**: price
- **value**: {"도쿄-교토": {"자유석": 13320, "지정석_Hikari": 14570, "Platt_Kodama": 10700}, "도쿄-신오사카": {"지정석": 14720, "Platt_Kodama": 11110}, "currency": "JPY", "구성": "기본운임 + 특급요금", "Nozomi추가": "210-1060 JPY"}
- **conditions**: 무조건
- **confidence**: 0.85
- **evidence**: [EU-0018]
- **출처 Claim**: C0-07

---

## 2. Updates (기존 KU 수정)

### KU-0002 수정
- **변경 필드**: confidence — 0.90 → 0.95
- **사유**: 공식 사이트(japanrailpass.net)에서 2026년 기준 가격 동일 확인. 2025-2026 추가 인상 없음 확인.
- **추가 근거**: [EU-0011]

### KU-0004 수정
- **변경 필드**: value — "물리 카드 재고 부족" 부분 업데이트
- **새 값**: "Suica/PASMO 등 IC카드로 전철, 버스, 편의점 결제 가능. 물리 카드 재고 부족은 2025.3월 공식 해소. Welcome Suica(관광객용, 28일 유효) 주요 역에서 판매 재개. 모바일 Suica(Apple/Google) 및 Welcome Suica Mobile(iPhone, 180일 유효) 이용 가능."
- **사유**: 반도체 부족 해소 및 Welcome Suica Mobile 출시 반영
- **추가 근거**: [EU-0016, EU-0017]

---

## 3. Deprecates (KU 폐기)

없음.

---

## 4. Conflict Decisions

없음. (이번 Cycle에서 충돌 발생하지 않음)

---

## 5. Gap Map Update

### 해결된 Gap
| GU ID | 해결 KU | 비고 |
|-------|---------|------|
| GU-0025 | KU-0008 | 긴급 연락처 + 관광헬프라인 확보. 2개 독립 출처 교차검증 완료. |
| GU-0005 | KU-0009 | 나리타/하네다 각각 3개 교통편 정리 |
| GU-0002 | KU-0002 (update) | 공식 가격 확인, confidence 상향 |
| GU-0017 | KU-0010 | VJW 등록 절차 + 필수 여부 확인 |
| GU-0012 | KU-0011 | 현행+2026 신제도 병기 |
| GU-0018 | KU-0012 | Welcome Suica 판매처 + Mobile 대안 |
| GU-0024 | KU-0013 | 도쿄-교토/오사카 구간 가격 |

### 신규 Gap
| GU ID | 유형 | 대상 | 기대효용 | 발견 경위 |
|-------|------|------|----------|-----------|
| GU-0026 | missing | japan-travel:regulation:tax-free:procedure_2026_nov | high | C0-05 수집 중 2026.11 제도 변경 발견. 시행 후 구체 절차 필요 |
| GU-0027 | missing | japan-travel:transport:airport-transfer:ic_card_compatibility | medium | C0-02 수집 중 — 공항 교통편에서 IC카드/JR Pass 호환성 상세 필요 |
| GU-0028 | uncertain | japan-travel:pass-ticket:suica:android_support | medium | C0-06 — Welcome Suica Mobile이 iPhone 전용. Android 대안 불명확 |

---

## 6. Entity Resolution 기록

| Claim 엔티티 | 매칭 결과 | 캐노니컬 키 | 방법 |
|--------------|-----------|-------------|------|
| 긴급 연락처 | new | japan-travel:regulation:emergency | Seed skeleton category 매칭 |
| 공항교통 | new | japan-travel:transport:airport-transfer | 신규 엔티티 생성 |
| Visit Japan Web | new | japan-travel:regulation:visit-japan-web | Seed skeleton category 매칭 |
| 면세 쇼핑 | new | japan-travel:regulation:tax-free | Seed skeleton category 매칭 |
| Suica 구매 | new | japan-travel:pass-ticket:suica | Seed의 ic-card와 별도 엔티티로 분리 (IC카드=일반, Suica=특정 상품) |
| 신칸센 가격 | matched | japan-travel:transport:shinkansen | 기존 엔티티에 field 추가 |
| JR Pass 가격 | matched | japan-travel:pass-ticket:jr-pass | 기존 KU-0002 update |
