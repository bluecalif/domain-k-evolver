# Cycle 2 Prep — Jump Mode 판정 + Budget 배분

> Generated: 2026-03-04
> Mode: **Jump Mode** (trigger 발동)
> Input: Axis Coverage Matrix (Cycle 1 종료 시점) + Critique C1 처방 (RX-07~11)

---

## 1. Jump Mode Trigger 판정

### Trigger 평가

| # | Trigger | 조건 | 입력 데이터 | 판정 |
|---|---------|------|------------|------|
| T1 | **Axis Under-Coverage** | deficit_ratio > 0 (required 축) | geography: 0.200 (rural 결손), risk: 0.200 (informational 결손) | **✅ 발동** |
| T2 | Spillover | Cycle N에서 Gap Map 외 슬롯 참조 3건+ | Cycle 1 동적 GU 3개, 모두 기존 슬롯 범위 (tokyo metro/subway) | ❌ 미발동 |
| T3 | High-Risk Blindspot | safety/financial 단일출처 KU | safety: KU-0008 (EU 2개 = 다중출처). financial 단일출처 KU 없음 | ❌ 미발동 |
| T4 | Prescription (구조 보강) | Critique에서 구조적 보강 처방 | RX-07~11: epistemic/consistency/integration/temporal. 구조적 보강(structural) 처방 없음 | ❌ 미발동 |
| T5 | Domain Shift | 신규 entity cluster 출현 | Cycle 1에서 신규 entity cluster 없음 | ❌ 미발동 |

### 판정 결과

**T1(Axis Under-Coverage) 발동 → Jump Mode 진입.**

발동 근거:
- geography 축: rural 완전 결손 (0 GU), osaka/kyoto 극소 (각 1 GU)
- risk 축: informational 완전 결손 (0 GU)
- nationwide+tokyo 편중 93.5% → 구조적 다양성 부족

---

## 2. Budget 배분

### jump_cap 계산

```
open_gu = 16
jump_cap = min(max(10, ceil(16 * 0.6)), 30) = min(max(10, 10), 30) = 10
```

→ Cycle 2에서 동적 GU 최대 **10개** 생성 가능.

### explore / exploit 배분

| 유형 | 배분 | Target 수 | 설명 |
|------|------|-----------|------|
| **explore** | 60% | 5 | 신규 축 영역 탐색 (geography: osaka, kyoto, rural) |
| **exploit** | 40% | 3 | 기존 open GU 해결 (revised-plan-c2 기반) |
| **합계** | 100% | **8** | Cycle 당 Target Gap 수 유지 |

### explore Target (신규 — geography 결손 보완)

| 순위 | 제안 GU | 대상 entity_key | field | geography | risk | 선정 근거 |
|------|---------|----------------|-------|-----------|------|-----------|
| E1 | (신규) | japan-travel:transport:osaka-metro | how_to_use | osaka | convenience | osaka 교통 정보 부재. 관광객 필수. |
| E2 | (신규) | japan-travel:attraction:kinkaku-ji | price | kyoto | financial | kyoto 관광지 정보 부재. 대표 명소. |
| E3 | (신규) | japan-travel:transport:rural-bus | how_to_use | rural | convenience | rural 교통 완전 결손. 지방 버스 이용법. |
| E4 | (신규) | japan-travel:accommodation:minshuku | price | rural | financial | rural 숙박 완전 결손. 민박 가격대. |
| E5 | (신규) | japan-travel:pass-ticket:icoca | where_to_buy | osaka | convenience | 관서 지역 IC카드. Suica(도쿄) 대응. |

### exploit Target (기존 open GU — revised-plan-c2에서 선별)

| 순위 | GU ID | 대상 | 처방 근거 |
|------|-------|------|-----------|
| X1 | GU-0030 | tokyo-subway-ticket:price | RX-07: 단일출처 교차확인 (최우선) |
| X2 | GU-0006 | ryokan:price | financial + accommodation |
| X3 | GU-0014 | cash:tips | payment. 현금 문화 핵심. |

### 추가 검증 태스크 (revised-plan-c2 계승)

| 대상 | 목적 | 처방 |
|------|------|------|
| KU-0011 면세 최소금액 | disputed 해결 | RX-08 |

---

## 3. Source Strategy (Jump Mode 확장)

### explore 영역 검색 전략

| Target | 검색 쿼리 | 기대 출처 | 언어 |
|--------|-----------|-----------|------|
| E1 osaka-metro | "Osaka Metro tourist guide lines fare 2026" | Osaka Metro 공식, japan-guide | en |
| E2 kinkaku-ji | "Kinkakuji Temple admission fee hours 2026" | 공식, japan-guide | en |
| E3 rural-bus | "Japan rural bus local transport tourist how to use IC card" | japan-guide, JNTO | en |
| E4 minshuku | "Japanese minshuku price range budget accommodation rural" | JNTO, Booking.com | en |
| E5 icoca | "ICOCA card where to buy tourist Osaka Kansai 2026" | JR West 공식 | en |

### exploit 영역 검색 전략

revised-plan-c2.md §6 Query/Discovery Strategy를 그대로 적용:
- GU-0030: 도쿄메트로/토에이 공식 (RX-07)
- GU-0006: Booking.com, じゃらん, JNTO
- GU-0014: japan-guide, JNTO

---

## 4. Guardrail 설정

| Guardrail | 규칙 | 임계치 |
|-----------|------|--------|
| **Quality Guard** | 신규 GU는 resolution_criteria + expected_utility 필수 | 미기재 시 GU 무효 |
| **Cost Guard** | 총 검색 횟수 상한 | **20회** (exploit 10 + explore 10) |
| **Balance Guard** | explore GU 비율 상한 | explore ≤ 60% (초과 시 exploit 우선) |
| **Convergence Guard** | 연속 2 Cycle Jump 시 HITL | Cycle 3도 Jump이면 사람 개입 |

---

## 5. State Snapshot

- **위치**: `bench/japan-travel/state-snapshots/cycle-1-snapshot/`
- **파일**: domain-skeleton.json, gap-map.json, knowledge-units.json, metrics.json, policies.json
- **시점**: Cycle 1 종료, Phase 0C 축 선언 보완(0C.1) 반영

---

## 6. Acceptance Criteria (Cycle 2 전체)

### 불변원칙 검증

| 원칙 | Cycle 2 검증 포인트 |
|------|-------------------|
| Gap-driven | explore/exploit 모두 GU에서 출발 |
| Claim→KU 착지성 | 수집 Claim → KU 전환율 100% |
| Evidence-first | 신규 KU 모두 EU ≥ 1 |
| Conflict-preserving | 충돌 발견 시 disputed 처리 |
| Prescription-compiled | RX-07~11 반영 여부 추적 |

### Jump Mode 고유 검증

| 항목 | 기준 |
|------|------|
| 동적 GU 생성 | ≤ jump_cap (10) |
| 신규 GU 중 high/critical | ≥ 40% |
| explore GU가 결손 축 커버 | geography: osaka, kyoto, rural 중 ≥ 2개 신규 커버 |
| Axis Coverage deficit 감소 | geography deficit_ratio < 0.200 |
| Guardrail 위반 | 0건 |

---

## 7. 실행 순서 (0C.4 참조)

```
1. Collect (explore 5 → exploit 3 → 추가검증 1)
2. Integrate (Claims → KB Patch, 동적 GU 발견, jump_cap 적용)
3. Critique (Structural Deficit Analysis, Axis Coverage 재계산, 5대 불변원칙)
4. Plan Modify (trigger 재평가, Convergence Guard, revised-plan-c3)
```
