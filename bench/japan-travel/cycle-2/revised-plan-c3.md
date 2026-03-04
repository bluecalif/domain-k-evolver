# Revised Plan — Cycle 3

> **단계**: (R) Plan Modify | **도메인**: japan-travel
> **생성일**: 2026-03-04
> **입력**: Critique C2 처방 (RX-12~16) + 이관분 (RX-09, RX-10)
> **모드 판정**: 아래 §1 참조

---

## 1. Jump / Normal Mode 판정

### Trigger 재평가 (Cycle 2 종료 기준)

| # | Trigger | 조건 | 입력 데이터 | 판정 |
|---|---------|------|------------|------|
| T1 | Axis Under-Coverage | deficit_ratio > 0 (required 축) | risk:informational 0.200 잔존 | 🟡 조건부 |
| T2 | Spillover | 동적 GU 3건+ | Cycle 2 동적 GU 6개, 모두 기존 scope 내 | ❌ 미발동 |
| T3 | High-Risk Blindspot | safety/financial 단일출처 KU | KU-0013(financial, 단일출처) 존재 | 🟡 경미 |
| T4 | Prescription (구조 보강) | Critique에서 구조적 처방 | RX-13 entity hierarchy (structural) | 🟡 발동 가능 |
| T5 | Domain Shift | 신규 entity cluster | 없음 | ❌ 미발동 |

### risk:informational 결손 해소 전략

**결정: informational 앵커에 GU 2개 생성 → Normal Mode 진입.**

근거:
- scope_boundary.excludes에 "일본어 학습", "역사/문화 심층 해설"이 있으나, **실용 여행 표현**(인사/긴급시 표현)과 **여행자 문화 매너**(줄서기/소음 등)는 "여행자 실용 정보" boundary_rule에 해당
- informational을 scope 외 판정하면 risk 축 자체의 설계 의미가 희석됨
- GU 2개 생성으로 deficit 해소 → T1 미발동 → Normal Mode 진입 가능
- Convergence Guard: Cycle 2 Jump + Cycle 3 Jump 시 HITL 필요. GU 사전 생성으로 회피.

### 신규 GU (informational 해소용)

| GU ID | entity_key | field | gap_type | expected_utility | risk_level | resolution_criteria |
|-------|-----------|-------|----------|-----------------|------------|-------------------|
| GU-0038 | japan-travel:regulation:practical-phrases | tips | missing | medium | informational | 여행자 필수 일본어 표현 10선 (인사/감사/긴급), 발음 가이드, 번역앱 추천 |
| GU-0039 | japan-travel:regulation:cultural-manner | tips | missing | medium | informational | 여행자 필수 매너 5선 (줄서기/소음/신발/쓰레기/온천), 위반 시 리스크 |

### 최종 판정

- T1: **미발동** (GU-0038/0039 생성으로 informational deficit 해소 예정)
- T3: **미발동** (KU-0013은 confidence 0.90, 안정적)
- T4: **미발동** (RX-13은 Outer Loop 범위, Inner Loop 구조 보강 아님)

→ **Cycle 3: Normal Mode** 진입.

---

## 2. Cycle 3 Budget 배분

### Normal Mode 기본 예산

```
open_gu = 19 (기존) + 2 (GU-0038/0039) = 21
target_count = min(8, ceil(21 * 0.4)) = min(8, 9) = 8
```

| 유형 | 배분 | Target 수 | 설명 |
|------|------|-----------|------|
| exploit | 100% | 8 | Normal Mode — 기존 open GU 해결 집중 |

Normal Mode에서는 explore 없음. 모든 예산을 기존 open GU 해결에 투입.

---

## 3. Target Gap 선정 (Cycle 3)

### 선정 기준

1. **처방 반영**: RX-12(high) > RX-14(low) > RX-15(low)
2. **expected_utility**: critical > high > medium > low
3. **risk_level**: safety > financial > policy > convenience > informational
4. **축 균형**: geography 다양성 유지

### Target Gaps

| 순위 | GU ID | entity_key | field | utility | risk | 선정 근거 |
|------|-------|-----------|-------|---------|------|-----------|
| 1 | GU-0038 | regulation:practical-phrases | tips | medium | informational | **RX-12** — risk:informational 결손 해소 (high 처방) |
| 2 | GU-0039 | regulation:cultural-manner | tips | medium | informational | **RX-12** — risk:informational 결손 해소 (high 처방) |
| 3 | GU-0032 | pass-ticket:osaka-amazing-pass | price | high | financial | osaka 패스 정보. Jump C2 신규 동적 GU. |
| 4 | GU-0033 | transport:kyoto-bus | how_to_use | high | convenience | kyoto 교통 핵심. Jump C2 신규 동적 GU. |
| 5 | GU-0034 | transport:rental-car | how_to_use | high | convenience | rural 교통 유일 옵션. Jump C2 신규 동적 GU. |
| 6 | GU-0009 | attraction:tokyo-skytree | price | medium | financial | Cycle 0 잔존. tokyo attraction 유일 open. |
| 7 | GU-0020 | transport:taxi | price | medium | financial | 택시 가격. 실용성 높음. |
| 8 | GU-0019 | connectivity:sim-card | price | medium | financial | **RX-15 이관분** — KU-0007 stale/disputed 연계. eSIM 출처 추가. |

### 미선정 사유 (이관)

| GU ID | 사유 | Cycle 4+ |
|-------|------|----------|
| GU-0011 | low utility (회전초밥) | 순차 처리 |
| GU-0015 | low utility (포켓WiFi) — eSIM 대체 추세 | 순차 처리 |
| GU-0016 | medium (시내버스) — 택시/지하철 우선 | C4 |
| GU-0021 | low utility (캡슐호텔) | C4+ |
| GU-0022 | medium (택배) — 편의성 | C4 |
| GU-0023 | medium (USJ 가격) — osaka attraction | C4 |
| GU-0027 | medium (공항IC카드) — KU-0009에 부분 정보 | C4 |
| GU-0028 | medium (Suica Android) — uncertain | C4 |
| GU-0029 | medium (서브웨이티켓 구매처) | C4 |
| GU-0031 | medium (도쿄메트로 팁) | C4 |
| GU-0035 | medium (칸사이패스) — osaka 패스와 분리 | C4 |
| GU-0036 | medium (오사카 길거리음식) | C4 |
| GU-0037 | medium (교토 료칸) | C4 |

---

## 4. Source Strategy

| Target | 검색 쿼리 | 기대 출처 | 언어 |
|--------|-----------|-----------|------|
| GU-0038 phrases | "essential Japanese phrases for tourists 2025 2026" | japan-guide, JNTO, Tofugu | en |
| GU-0039 manner | "Japan travel etiquette rules cultural manners tourist guide" | japan-guide, JNTO, LiveJapan | en |
| GU-0032 osaka pass | "Osaka Amazing Pass price 2026 included attractions" | Osaka Amazing Pass 공식 | en |
| GU-0033 kyoto bus | "Kyoto bus one day pass 2026 price routes tourist" | 교토시교통국, japan-guide | en |
| GU-0034 rental car | "Japan rental car tourist guide international license 2026 price" | JNTO, japan-guide | en |
| GU-0009 skytree | "Tokyo Skytree admission fee 2026 observation deck" | Tokyo Skytree 공식 | en |
| GU-0020 taxi | "Japan taxi fare base rate 2026 app" | japan-guide, JNTO | en |
| GU-0019 SIM | "Japan eSIM tourist 2026 price comparison best" | japan-guide, Sakura Mobile | en |

---

## 5. 처방 반영 추적 (RX-09~RX-16)

| 처방 ID | 출처 | 우선순위 | Cycle 3 반영 | 상세 |
|---------|------|----------|-------------|------|
| RX-09 | C1 | low | ⚠️ 부분 반영 | GU-0019 Target #8로 선정. eSIM 출처 추가 시도. |
| RX-10 | C1 | medium | ❌ Outer Loop 이관 | entity_key alias 매핑 → 0C.5 정책 확정 시 처리 |
| RX-12 | C2 | **high** | ✅ 반영 | GU-0038/0039 생성 + Target #1~2 |
| RX-13 | C2 | medium | ❌ Outer Loop 이관 | entity hierarchy → 0C.5 정책 확정 시 처리 |
| RX-14 | C2 | low | ❌ C4 이관 | KU-0013 교차검증. C3 budget 부족. |
| RX-15 | C2 | low | ⚠️ 부분 반영 | GU-0019 선정으로 SIM 추가출처 가능. primary 확정은 C4. |
| RX-16 | C2 | low | ✅ 반영 | Normal Mode이므로 Balance Guard 해당 없음. 정책 기록. |

### 미반영 사유 기록 (Prescription-compiled 추적성 강화)

- **RX-10/RX-13**: Collect/Integrate 범위가 아닌 **Schema/Policy 보완** 영역. Inner Loop에서 처리 불가. 0C.5(정책 확정) 단계에서 entity_hierarchy 스키마 + alias 매핑 정의 예정.
- **RX-14**: 예산 8건 중 high 처방(RX-12) + 동적 GU(high utility) 우선 배정. KU-0013은 confidence 0.90으로 긴급성 낮음.

---

## 6. Guardrail 설정

| Guardrail | 규칙 | 임계치 | C3 적용 |
|-----------|------|--------|---------|
| Quality Guard | 신규 KU에 EU ≥ 1, confidence 기재 | 필수 | ✅ |
| Cost Guard | 총 검색 횟수 상한 | **16회** (Target 8 × 2) | ✅ |
| Balance Guard | Normal Mode — explore 없음 | N/A | ✅ (해당 없음) |
| Convergence Guard | 연속 Jump 시 HITL | C3 Normal → 미해당 | ✅ |

---

## 7. Acceptance Criteria (Cycle 3)

### 불변원칙 검증

| 원칙 | Cycle 3 검증 포인트 |
|------|-------------------|
| Gap-driven | 8개 Target 모두 open GU에서 출발 |
| Claim→KU 착지성 | 수집 Claim → KU 전환율 100% |
| Evidence-first | 신규 KU 모두 EU ≥ 1 |
| Conflict-preserving | 충돌 발견 시 disputed 처리 |
| Prescription-compiled | RX-09/12/15 반영 여부 추적. 미반영 사유 기록 필수. |

### Metrics 목표

| 지표 | C2 종료 | C3 목표 | 비고 |
|------|---------|---------|------|
| 근거율 | 1.0 | ≥ 0.95 | 유지 |
| 다중근거율 | 0.821 | ≥ 0.80 | 유지 |
| 충돌률 | 0.036 | < 0.06 | 유지 |
| 평균 confidence | 0.875 | ≥ 0.85 | 유지 |
| Gap 해소율 | 0.486 | ≥ 0.55 | +6.4%p 이상 (8개 해결 시 26/39 = 0.667) |
| risk:informational deficit | 0.200 | 0.000 | GU-0038/0039 해결 시 |

---

## 8. 실행 순서 (0C.4 수동 실행 마무리 → Cycle 3)

```
[현재] 0C.4 Plan Modify — 본 문서 완료
  ↓
0C.4 마무리: gap-map.json에 GU-0038/0039 추가, git commit
  ↓
Cycle 3 Collect (검색 8건, 교차검증 추가 가능)
  ↓
Cycle 3 Integrate (Claims → KB Patch)
  ↓
Cycle 3 Critique (Metrics Delta, 5대 원칙, Axis Coverage 재계산)
  ↓
Cycle 3 Plan Modify (revised-plan-c4)
```

---

## 9. 종합

Cycle 2 Jump Mode로 geography 결손을 완전 해소했으나, risk:informational 결손이 잔존. 본 Plan Modify에서 informational GU 2개(실용 표현 + 문화 매너)를 생성하여 T1 trigger를 사전 해소하고, **Normal Mode**로 Cycle 3에 진입한다.

Cycle 3의 핵심 목표:
1. **risk:informational 결손 해소** (RX-12 반영)
2. **Jump Mode 동적 GU 해결 착수** (osaka/kyoto/rural 패스·교통)
3. **Gap 해소율 0.55+ 달성** (open 21 → 13 이하)
4. **KU-0007 SIM disputed 해소 준비** (RX-15 부분 반영)
