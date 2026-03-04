# KB Patch — Cycle 2

> **단계**: (I) Integrate | **도메인**: japan-travel
> **생성일**: 2026-03-04
> **모드**: Jump Mode (explore 5 + exploit 3)

---

## 1. New Knowledge Units (KU-0022 ~ KU-0028)

### KU-0022: Osaka Metro 이용법 [explore — E1]

| 항목 | 값 |
|------|----|
| entity_key | `japan-travel:transport:osaka-metro` |
| field | `how_to_use` |
| confidence | 0.85 |
| evidence_links | [EU-0036, EU-0037] |
| geography | osaka |

```json
{
  "노선": "9개 노선, 130개+ 역",
  "결제": "IC카드(ICOCA/Suica/PASMO) 사용 가능",
  "1일권_Enjoy_Eco_Card": {"평일": 800, "주말공휴일": 600, "currency": "JPY"},
  "운행시간": "약 05:30~00:15",
  "배차간격": {"평일": "2~5분", "주말": "4~8분"},
  "관광지할인": "Enjoy Eco Card 제시 시 약 30개 관광지 할인"
}
```

### KU-0023: 킨카쿠지 입장 정보 [explore — E2]

| 항목 | 값 |
|------|----|
| entity_key | `japan-travel:attraction:kinkaku-ji` |
| field | `price` |
| confidence | 0.85 |
| evidence_links | [EU-0038, EU-0039] |
| geography | kyoto |

```json
{
  "입장료": {"성인": 500, "초중학생": 300, "currency": "JPY"},
  "운영시간": "09:00~17:00 (최종 입장 16:30)",
  "휴무": "연중무휴",
  "비고": "입장권이 부적(お札) 형태 — 기념품 겸용"
}
```

### KU-0024: 지방 버스 이용법 [explore — E3]

| 항목 | 값 |
|------|----|
| entity_key | `japan-travel:transport:rural-bus` |
| field | `how_to_use` |
| confidence | 0.80 |
| evidence_links | [EU-0040, EU-0041, EU-0042] |
| geography | rural |

```json
{
  "탑승방식": "후방 승차 → 전방 하차 (정리권 방식)",
  "IC카드": "대부분 지역 사용 가능. 일부 지방 예외 있음.",
  "IC_락_주의": "하차역이 IC 미지원 시 카드 잠금. 주요 역에서 리셋 필요.",
  "배차간격": "1~2시간 단위 가능. 사전 시간표 확인 필수.",
  "산간지역": "버스가 유일한 대중교통인 경우 다수",
  "팁": "현금 소액(동전) 준비 권장. IC 미지원 지역 대비."
}
```

### KU-0025: 민박(Minshuku) 가격 [explore — E4]

| 항목 | 값 |
|------|----|
| entity_key | `japan-travel:accommodation:minshuku` |
| field | `price` |
| confidence | 0.85 |
| evidence_links | [EU-0043, EU-0044] |
| geography | rural |

```json
{
  "식사포함": {"범위": "5000~14000 JPY/인/박", "내용": "석식+조식 (가정식)"},
  "숙박만": {"범위": "3000~5000 JPY/인/박"},
  "특징": "다다미 방 + 이불, 공용 욕실, 가정 운영",
  "체험": "농업 체험, 향토 요리 학습 등 가능",
  "currency": "JPY"
}
```

### KU-0026: ICOCA 구매 정보 [explore — E5]

| 항목 | 값 |
|------|----|
| entity_key | `japan-travel:pass-ticket:icoca` |
| field | `where_to_buy` |
| confidence | 0.90 |
| evidence_links | [EU-0045, EU-0046] |
| geography | osaka |

```json
{
  "가격": {"총액": 2000, "보증금": 500, "이용가능": 1500, "currency": "JPY"},
  "구매처": [
    "JR West 역 자판기 (오사카, 교토 등)",
    "간사이 국제공항 (KIX)",
    "한큐/한신/게이한/난카이/긴테쓰 역",
    "오사카/교토/고베 지하철역"
  ],
  "결제": "현금만 가능 (자판기, 신용카드 불가)",
  "관광객용": "Kansai One Pass — 관광지 할인 특전 포함",
  "환불": "보증금 ¥500 환불 가능 (수수료 ¥220 공제)"
}
```

### KU-0027: 료칸 가격 [exploit — X2, resolves GU-0006]

| 항목 | 값 |
|------|----|
| entity_key | `japan-travel:accommodation:ryokan` |
| field | `price` |
| confidence | 0.85 |
| evidence_links | [EU-0048, EU-0049] |
| geography | nationwide |

```json
{
  "예산형": "5000~10000 JPY/인/박",
  "중급": "15000~25000 JPY/인/박 (조식+석식, 공용온천)",
  "고급": "30000~70000 JPY/인/박 (전용온천, 가이세키)",
  "초고급": "100000+ JPY/인/박",
  "평균대": "15000~30000 JPY/인/박 (식사 포함)",
  "지역별": {
    "교토": "¥15,000 이하 가능 (기온/니시키 인근)",
    "하코네": "약 ¥12,600부터"
  },
  "비고": "성수기/비수기 가격 차이 큼. 식사 포함 여부가 가격 좌우.",
  "currency": "JPY"
}
```

### KU-0028: 현금/ATM 팁 [exploit — X3, resolves GU-0014]

| 항목 | 값 |
|------|----|
| entity_key | `japan-travel:payment:cash` |
| field | `tips` |
| confidence | 0.85 |
| evidence_links | [EU-0050, EU-0051, EU-0052] |
| geography | nationwide |

```json
{
  "ATM_7Eleven": {
    "수수료": "주간(07~19시) 무료, 야간 ¥110",
    "인출한도": "1회 ¥100,000",
    "설치수": "전국 20,000개+",
    "운영": "24시간",
    "카드별": {"Mastercard": "무료", "Visa": "¥110~220"}
  },
  "우체국ATM": "외국 카드 사용 가능. 주요 우체국.",
  "환전": "공항이 가장 유리. 은행, 일부 편의점도 가능.",
  "현금필요장소": "소규모 음식점, 노점, 지방 버스, 신사/사찰, 코인세탁소",
  "권장": "항시 1~2만엔 현금 소지"
}
```

---

## 2. Updated Knowledge Units

### KU-0016 업데이트 (교차검증 완료)

- **변경**: evidence_links에 EU-0047 추가 → [EU-0022, EU-0047]
- **confidence**: 0.80 → **0.90** (교차검증 성공)
- **비고**: TRAICY 보도(도쿄메트로+토에이 공식 발표 기반)가 기존 가격 정보와 완전 일치.

### KU-0011 업데이트 (disputed 해결)

- **변경**: disputes[0].resolution: "pending" → **"resolved_as_maintain"**
- **evidence_links**: 기존 + [EU-0053, EU-0054, EU-0055]
- **confidence**: 0.85 → **0.90** (4개 독립 출처 일치)
- **status**: "disputed" → **"active"**
- **판정**: "5,000엔 유지"가 정확. 기존 "철폐" 기재는 초기 보도 오류. JNTO, japantravel, vatcalc, kixdutyfree 4개 출처 일치.

---

## 3. GU Resolutions

| GU ID | 해결 방법 | resolved_by |
|-------|-----------|-------------|
| GU-0030 | KU-0016 교차검증 완료 (EU-0047) | KU-0016 |
| GU-0006 | KU-0027 신규 생성 | KU-0027 |
| GU-0014 | KU-0028 신규 생성 | KU-0028 |

---

## 4. 동적 GU 발견 (Jump Mode)

Jump Mode에서 explore 영역 수집 중 발견된 인접/심화 Gap:

| GU ID | gap_type | entity_key | field | geography | risk | utility | trigger | trigger_source |
|-------|----------|-----------|-------|-----------|------|---------|---------|---------------|
| GU-0032 | missing | japan-travel:pass-ticket:osaka-amazing-pass | price | osaka | financial | **high** | A:adjacent_gap | KU-0022 |
| GU-0033 | missing | japan-travel:transport:kyoto-bus | how_to_use | kyoto | convenience | **high** | A:adjacent_gap | KU-0023 |
| GU-0034 | missing | japan-travel:transport:rental-car | how_to_use | rural | convenience | **high** | A:adjacent_gap | KU-0024 |
| GU-0035 | missing | japan-travel:pass-ticket:kansai-area-pass | price | osaka | financial | medium | A:adjacent_gap | KU-0026 |
| GU-0036 | missing | japan-travel:dining:osaka-street-food | tips | osaka | convenience | medium | A:adjacent_gap | KU-0022 |
| GU-0037 | missing | japan-travel:accommodation:kyoto-ryokan | price | kyoto | financial | medium | A:adjacent_gap | KU-0023 |

### 동적 GU 검증 (Jump Mode)

| 검증 항목 | 결과 | 상세 |
|-----------|------|------|
| 신규 GU 수 ≤ jump_cap | ✅ | 6개 ≤ 10 (jump_cap) |
| 신규 GU 중 high/critical ≥ 40% | ✅ | 3/6 = 50% ≥ 40% |
| 모든 GU에 resolution_criteria | ✅ | 아래 참조 |
| explore GU가 결손 축 커버 | ✅ | osaka: 3, kyoto: 2, rural: 1 |

### Resolution Criteria

| GU ID | resolution_criteria |
|-------|-------------------|
| GU-0032 | Osaka Amazing Pass 가격(1일/2일), 포함 시설, 구매처 |
| GU-0033 | 교토 시버스 노선 개요, 1일 승차권 가격, 주요 관광지 접근 노선 |
| GU-0034 | 렌터카 이용법, 국제면허증, 가격대, 주요 업체, 좌측통행 주의사항 |
| GU-0035 | Kansai Area Pass 가격(1~4일), 적용 노선, JR Pass와 차이 |
| GU-0036 | 도톤보리 먹거리, 가격대, 추천 스트리트푸드, 에티켓 |
| GU-0037 | 교토 료칸 가격대, 추천 지역(히가시야마 등), 예약 팁 |

---

## 5. Patch 요약

| 항목 | Cycle 1 종료 | Cycle 2 Patch 후 | Delta |
|------|-------------|-----------------|-------|
| KU (active) | 19 | 26 | +7 |
| KU (disputed) | 2 | 1 | -1 (KU-0011 해결) |
| KU (total) | 21 | 27 | +6 |
| EU (total) | 35 | 55 | +20 |
| GU (open) | 16 | 19 | +3 (해결 3, 신규 6) |
| GU (resolved) | 15 | 18 | +3 |
| GU (total) | 31 | 37 | +6 |

### Axis Coverage 변동 (geography)

| value | Cycle 1 total | Cycle 2 total | Delta |
|-------|--------------|--------------|-------|
| tokyo | 8 | 8 | 0 |
| osaka | 1 | **4** | +3 (GU-0032, 0035, 0036) |
| kyoto | 1 | **3** | +2 (GU-0033, 0037) |
| rural | 0 | **1** | +1 (GU-0034) |
| nationwide | 21 | 22 | +1 (KU-0027, KU-0028) |

→ geography deficit_ratio: 0.200 → **0.000** (rural 결손 해소) ✅
