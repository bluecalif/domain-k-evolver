# Critique Report — Cycle 2

> **단계**: (R) Critique | **도메인**: japan-travel
> **생성일**: 2026-03-04
> **입력**: KB Patch Cycle 2 + 전체 State
> **모드**: Jump Mode (explore 5 + exploit 3)

---

## 1. Metrics Delta

### 현재 State 수치

| 지표 | Cycle 1 종료 | Cycle 2 종료 | Delta | 방향 |
|------|-------------|-------------|-------|------|
| KU 수 (active) | 19 | 27 | +8 | ↑ |
| KU 수 (disputed) | 2 | 1 | -1 | ↓ (개선) |
| KU 수 (total) | 21 | 28 | +7 | ↑ |
| EU 수 (total) | 35 | 55 | +20 | ↑ |
| 근거율 (EU≥1 / active) | 1.0 | 1.0 | 0 | → |
| 다중근거율 (EU≥2 / active+disputed) | 0.714 | 0.821 | +0.107 | ↑ |
| Gap 수 (open) | 16 | 19 | +3 | ↑ (신규 6, 해결 3) |
| Gap 해소율 (resolved / total) | 0.484 | 0.486 | +0.002 | → (정체) |
| 충돌률 (disputed / active+disputed) | 0.095 | 0.036 | -0.059 | ↓ (개선) |
| 평균 confidence (active) | 0.876 | 0.875 | -0.001 | → |
| 신선도 리스크 | 0 | 0 | 0 | → |

### 검증 계산

- **근거율**: 27/27 active KU 모두 EU ≥ 1 = **1.0** ✅
- **다중근거율**: 23/28 (active+disputed) = **0.821** ✅
  - 단일출처 KU: KU-0001(EU×1), KU-0003(EU×1), KU-0005(EU×1), KU-0006(EU×1), KU-0013(EU×1) = 5개
  - 28 - 5 = 23 → 23/28 = 0.821
- **충돌률**: 1/28 = **0.036** ✅ (KU-0007만 disputed)
- **평균 confidence (active 27개)**: (0.95+0.95+0.90+0.85+0.90+0.85+0.95+0.85+0.90+0.90+0.85+0.85+0.90+0.85+0.95+0.90+0.85+0.85+0.85+0.80+0.85+0.90+0.85+0.85) / 27... ≈ **0.875** ✅
  - (정밀: Σconfidence = 23.65 / 27 = 0.876 — 반올림 차이 허용)
- **Gap 해소율**: 18/37 = **0.486** ✅

### 건강 지표 평가

| 지표 | 값 | 임계치 | 판정 |
|------|----|--------|------|
| 근거율 | 1.0 | ≥ 0.95 | ✅ 건강 |
| 다중근거율 | 0.821 | ≥ 0.50 | ✅ 건강 |
| 충돌률 | 0.036 | < 0.06 | ✅ 건강 (주의→건강 전환) |
| 평균 confidence | 0.875 | ≥ 0.85 | ✅ 건강 |
| 신선도 리스크 | 0 | = 0 | ✅ 건강 |

### Metrics 종합 평가

5개 건강 지표 **전원 ✅**. Cycle 1 대비 주요 개선:
- 충돌률 0.095 → 0.036 (⚠️→✅ 전환). KU-0011 disputed 해결이 핵심 기여.
- 다중근거율 0.714 → 0.821 (+0.107). KU-0016 교차검증 + 신규 KU 다중출처 확보.
- Gap 해소율은 0.486으로 거의 정체 — 해결 3건이나 신규 6건으로 상쇄.

---

## 2. Failure Modes 탐지

### Epistemic (근거 빈약/출처 편향/독립성 부족)

- **발견 1**: 단일출처 KU 5개 잔존 (KU-0001, KU-0003, KU-0005, KU-0006, KU-0013). 모두 Cycle 0 Seed 출발이라 교차검증 기회 부재. 이 중 KU-0013(신칸센 가격, financial)은 교차검증 규칙(min_eu ≥ 2) 미준수.
- **심각도**: low (해당 KU들의 confidence ≥ 0.85, 정보 안정성 높음)
- **발견 2**: KU-0024(지방 버스) confidence 0.80으로 Cycle 2 신규 KU 중 최저. EU-0042(JNTO)가 공식출처이나 직접적 가격/시간표 정보 부재.
- **심각도**: low

### Temporal (신선도 취약)

- **발견**: KU-0016(Tokyo Subway Ticket 가격) — 2026-03-14 인상 적용 임박. 교차검증으로 confidence 0.90 확보했으나, 적용일 이후 현장 혼란 가능성(구권/신권 병행기). 이전 가격(24h ¥600)이 여전히 유통 중인 가이드 존재 가능.
- **심각도**: low (교차검증 완료, TTL 180일 적절)

### Structural (스키마 표현력 부족)

- **발견**: entity_key 해상도 불일치 지속.
  - `ryokan:price`(KU-0027, nationwide) ↔ `kyoto-ryokan:price`(GU-0037, kyoto): 동일 accommodation 유형이 지역별로 세분화. 상위 entity(ryokan)와 하위 entity(kyoto-ryokan)의 관계 미정의.
  - Cycle 1의 `metro-pass` ↔ `subway-ticket` 불일치 미해결(RX-10).
- **심각도**: medium (GU 증가 시 entity 충돌 가능성 증가)

### Consistency (충돌)

- **발견**: KU-0007(SIM 가격) condition_split 상태 지속 (Cycle 1 RX-09). Cycle 2에서 추가 출처 수집 없음. eSIM primary 확정 판단 보류 중.
- **심각도**: low (condition_split은 안정적 상태, 급한 해결 불필요)

### Planning (전략 편향)

- **발견**: Jump Mode의 explore가 geography 축에만 집중. **risk:informational 축 결손(deficit 0.200) 미해결**. Cycle 2 prep에서 T1 발동 근거에 risk deficit도 포함되었으나, 실제 explore 배분은 geography만 타겟.
- **심각도**: medium (구조적 결손 1개 축 잔존)
- **원인**: explore 5건 모두 geography 보정에 투입. risk:informational은 scope_boundary의 excludes("역사/문화 심층 해설")와 겹치는 영역이라 GU 생성이 어려웠을 수 있음.

### Integration (정규화)

- **발견**: Cycle 2 신규 KU의 entity_key는 모두 정규화 규칙 준수. 그러나 Cycle 1 RX-10(entity_key alias 매핑)은 미구현.
- **심각도**: low

---

## 3. Root Cause Hypotheses

| 실패모드 | 가설 | 근거 |
|----------|------|------|
| Planning (risk:informational 미해결) | Jump Mode의 trigger가 T1(Axis Under-Coverage)인데, geography와 risk 결손이 동시에 존재할 때 geography를 우선시한 결과. 배분 기준에 "축 간 우선순위" 규칙이 부재. | cycle-2-prep.md의 explore 배분이 전부 geography 관련 |
| Structural (entity 해상도 불일치) | Domain Skeleton에 entity 간 계층관계(is_a, part_of)가 미정의. region-specific entity(kyoto-ryokan)와 generic entity(ryokan)의 관계 표현 불가. | domain-skeleton.json에 entity hierarchy 없음. RX-04(Cycle 0)에서 이미 지적 |
| Epistemic (단일출처 KU 5개) | Cycle 0 Seed KU는 Bootstrap 단계에서 단일출처로 시작. 이후 Cycle에서 교차검증 대상으로 선정되지 않으면 영구 단일출처로 남음. | 5개 KU 모두 Cycle 0 origin |

---

## 4. Structural Deficit Analysis — Axis Coverage 재계산

### Geography 축 (Cycle 2 종료)

| value | open | resolved | total | C1 total | Delta |
|-------|------|----------|-------|----------|-------|
| tokyo | 4 | 4 | 8 | 8 | 0 |
| osaka | 4 | 0 | 4 | 1 | **+3** |
| kyoto | 2 | 1 | 3 | 1 | **+2** |
| rural | 1 | 0 | 1 | 0 | **+1** |
| nationwide | 8 | 13 | 21 | 21 | 0 |

- **deficit_ratio**: 0/5 = **0.000** ✅ (C1: 0.200 → 해소)
- **편중**: nationwide+tokyo = 29/37 = 78.4% (C1: 93.5% → 15.1%p 개선)

### Category 축 (Cycle 2 종료)

| value | open | resolved | total |
|-------|------|----------|-------|
| transport | 6 | 3 | 9 |
| accommodation | 2 | 2 | 4 |
| attraction | 2 | 1 | 3 |
| dining | 2 | 1 | 3 |
| regulation | 1 | 4 | 5 |
| pass-ticket | 3 | 6 | 9 |
| connectivity | 2 | 0 | 2 |
| payment | 0 | 2 | 2 |

- **deficit_ratio**: 0/8 = **0.000** ✅
- **비고**: payment open=0 (모두 resolved). connectivity resolved=0이나 open GU 2개 존재.

### Risk 축 (Cycle 2 종료)

| value | open | resolved | total | C1 total | Delta |
|-------|------|----------|-------|----------|-------|
| safety | 0 | 1 | 1 | 1 | 0 |
| financial | 7 | 9 | 16 | 12 | +4 |
| policy | 0 | 1 | 1 | 1 | 0 |
| convenience | 11 | 7 | 18 | 17 | +1 |
| **informational** | **0** | **0** | **0** | **0** | **0** |

- **deficit_ratio**: 1/5 = **0.200** ⚠️ (변동 없음)
- **잔존 결손**: informational 앵커에 GU 0개 — 미해결

### Condition 축 (선택적)

| value | open | resolved | total |
|-------|------|----------|-------|
| peak-season | 0 | 1 | 1 |
| off-season | 0 | 1 | 1 |
| weekday | 0 | 0 | 0 |
| weekend | 0 | 0 | 0 |
| online | 1 | 0 | 1 |
| in-person | 1 | 0 | 1 |

- **deficit_ratio**: 2/6 = **0.333** (변동 없음, 선택적 축)
- **비고**: GU-0006(peak/off-season) resolved → open에서 resolved로 이동

### Deficit 요약

| 축 | C1 deficit | C2 deficit | 변동 |
|----|-----------|-----------|------|
| category | 0.000 | 0.000 | → |
| geography | **0.200** | **0.000** | ✅ 해소 |
| risk | 0.200 | **0.200** | → (미해결) |
| condition | 0.333 | 0.333 | → (선택적) |

---

## 5. 5대 불변원칙 검증

| 원칙 | 준수 | 근거 |
|------|------|------|
| **Gap-driven** | ✅ | explore 5개: cycle-2-prep.md §2 explore Target에서 출발. exploit 3개: 기존 open GU(0030, 0006, 0014). 추가검증 1건: KU-0011 disputed(RX-08). 모두 Gap 기반. |
| **Claim→KU 착지성** | ✅ | 31 Claims → 7 신규 KU(KU-0022~0028) + 2 기존 KU 업데이트(KU-0016, KU-0011) + 0 rejected. 모든 Claim이 KU 필드 내 착지. **31 Claims = 31 착지** ✓ |
| **Evidence-first** | ✅ | 28개 KU (active 27 + disputed 1) 모두 evidence_links ≥ 1. 근거율 1.0. 신규 KU 7개 모두 EU ≥ 2 (다중출처). |
| **Conflict-preserving** | ✅ | KU-0011 disputed → resolved_as_maintain (구조적 해결: 4개 독립출처 일치 확인 후 판정). disputes[] 배열에 해결 과정 기록. KU-0007 condition_split 상태 유지. 충돌 삭제 시도 없음. |
| **Prescription-compiled** | ⚠️ 부분 | 아래 §8 상세. RX-07, RX-08, RX-11 반영. **RX-09(SIM eSIM 추가출처), RX-10(entity_key alias) 미반영**. |

### Prescription-compiled 상세 평가

Prescription-compiled 원칙은 "Critique 처방은 다음 Plan에 반영"을 요구한다. RX-09/RX-10은 Cycle 2 Plan(cycle-2-prep.md)에서 명시적으로 다루지 않았으며, exploit 배분에도 미포함. 다만:
- RX-09(low 우선순위): exploit 배분 3건 중 high/medium 우선 할당으로 low가 탈락한 것은 합리적 판단.
- RX-10(medium 우선순위): 정책/스키마 보완이므로 Collect/Integrate가 아닌 Outer Loop에서 처리가 적절.

→ **위반은 아니나 추적성 기록이 부족**. Plan에 "미반영 사유" 명시 필요.

---

## 6. 동적 GU 검증 (Jump Mode)

| 검증 항목 | 기준 | 결과 | 상세 |
|-----------|------|------|------|
| 신규 GU 수 ≤ jump_cap | ≤ 10 | ✅ | 6개 ≤ 10 |
| 신규 GU 중 high/critical | ≥ 40% | ✅ | 3/6 = 50% (GU-0032:high, GU-0033:high, GU-0034:high) |
| 모든 GU에 resolution_criteria | 필수 | ✅ | 6개 모두 기재 완료 |
| explore GU가 결손 축 커버 | ≥ 2개 신규 축 | ✅ | osaka(3), kyoto(2), rural(1) — 3개 축 신규 커버 |
| geography deficit 감소 | < 0.200 | ✅ | 0.200 → **0.000** |
| axis_tags 기재 | 필수 | ✅ | 6개 모두 geography axis_tag 보유 |
| expansion_mode 기재 | 필수 | ✅ | 6개 모두 "jump" 기재 |
| trigger + trigger_source 기재 | 필수 | ✅ | 모두 A:adjacent_gap + 출처 KU 명시 |

---

## 7. Guardrail 점검

| Guardrail | 규칙 | 결과 | 판정 |
|-----------|------|------|------|
| **Quality Guard** | 신규 GU에 resolution_criteria + expected_utility 필수 | 6/6 충족 | ✅ |
| **Cost Guard** | 총 검색 ≤ 20회 | 9회 | ✅ |
| **Balance Guard** | explore ≤ 60% | 62.5% (5/8) | ⚠️ 경미 초과 |
| **Convergence Guard** | 연속 2 Cycle Jump 시 HITL | Cycle 2 = 첫 Jump. C3 판정 대기. | ℹ️ 미해당 (아직) |

### Balance Guard 분석

explore 5 / exploit 3 = 62.5%. 상한 60% 대비 2.5%p 초과. 원인:
- 전체 Target 8건 중 explore 5건. exploit을 4로 늘리면 총 9건 → 예산 초과.
- 또는 explore를 4로 줄이면 rural이 탈락 → geography deficit 해소 불가.

**판정**: 경미한 초과이며, geography deficit 해소라는 Jump Mode 목적 달성에 필수적이었으므로 수용 가능. 단, Plan Modify에서 향후 Jump 시 balance 규칙 준수 강화 필요.

---

## 8. Cycle 1 처방 반영 결과 (RX-07~RX-11 추적성)

| 처방 ID | 우선순위 | 반영 | 결과 |
|---------|----------|------|------|
| RX-07 (KU-0016 교차확인) | high | ✅ 반영 | EU-0047 추가, confidence 0.80→0.90, GU-0030 resolved |
| RX-08 (KU-0011 disputed 해결) | medium | ✅ 반영 | EU-0053~55 추가, 4개 독립출처 일치 확인, resolved_as_maintain |
| RX-09 (KU-0007 eSIM 추가출처) | low | ❌ 미반영 | exploit 배분에서 탈락 (low 우선순위). Cycle 3 이관. |
| RX-10 (entity_key alias 매핑) | medium | ❌ 미반영 | Collect/Integrate 범위 밖. Outer Loop 정책 보완 대상. Cycle 3 이관. |
| RX-11 (KU-0016 모니터링) | low | ✅ 반영 | 교차검증으로 사실상 모니터링 완료. 적용일(03-14) 이후 추가 확인은 TTL 자동 감시. |

---

## 9. Prescriptions — Cycle 3 반영 (RX-12 ~)

| ID | 실패모드 | 처방 | 우선순위 | 반영 대상 |
|----|----------|------|----------|-----------|
| RX-12 | Planning | **risk:informational 축 결손 해소**. informational 앵커에 해당하는 GU 최소 2개 생성 필요. 후보: 일본어 기본 표현(인사/숫자/긴급시 표현), 문화차이 팁(줄서기/소음 매너). scope_boundary의 "일본어 학습" exclude와 충돌하지 않는 범위(실용 여행 표현)로 한정. | **high** | Plan (Target Gaps) |
| RX-13 | Structural | **entity 계층관계 정의**. Domain Skeleton에 `entity_hierarchy` 섹션 추가. `ryokan` → `kyoto-ryokan`, `metro-pass` → `subway-ticket` 등 alias/is_a 관계 명시. RX-04(C0) + RX-10(C1) 통합 해결. | medium | Schema / Outer Loop |
| RX-14 | Epistemic | **Cycle 0 단일출처 KU 교차검증 우선순위 설정**. KU-0013(신칸센 가격, financial)을 Cycle 3 exploit 최우선 대상으로. KU-0001, KU-0003, KU-0005, KU-0006은 안정 정보이므로 Cycle 4+ 순차 처리. | low | Plan (Target Gaps) |
| RX-15 | Consistency | **KU-0007(SIM) eSIM primary 확정 판정**. RX-09 이관분. 최신 eSIM 시장 출처 1개 이상 추가 확보 후, 물리SIM 정보를 deprecated로 전환할지 결정. | low | Plan (Source Strategy) |
| RX-16 | Planning | **Balance Guard 준수 강화**. Jump Mode에서 explore/exploit 배분 시 60% 상한을 엄격 적용. 총 Target이 홀수일 때는 exploit에 추가 1건 배분. | low | Policy |

---

## 10. Remodeling Triggers (Outer Loop)

| 조건 | 충족 여부 | 권고 |
|------|-----------|------|
| 스키마 확장 필요 | 부분적 yes | entity hierarchy 정의 필요 (RX-13). Cycle 3 Plan Modify 또는 Outer Loop에서 처리. |
| 정책 수정 필요 | 부분적 yes | Balance Guard 배분 규칙 보완 (RX-16). 경미. |
| 평가 루브릭 개편 | no | Metrics 공식 정상 작동. 5개 건강 지표 전원 ✅. |

---

## 11. Convergence Guard 예비 판정

### Cycle 3 Jump Mode 가능성 평가

| Trigger | Cycle 2 종료 데이터 | 예상 판정 |
|---------|-------------------|-----------|
| T1 (Axis Under-Coverage) | risk:informational deficit 0.200 | 🟡 발동 가능 |
| T2 (Spillover) | 동적 GU 6개 (jump_cap 이내) | 🟢 미발동 |
| T3 (High-Risk Blindspot) | safety KU-0008 (EU 2개, 다중출처) | 🟢 미발동 |
| T4 (Prescription 구조보강) | RX-13 entity hierarchy (구조적) | 🟡 발동 가능 |
| T5 (Domain Shift) | 신규 entity cluster 없음 | 🔴 미발동 |

**예비 결론**: T1이 risk:informational 결손으로 재발동할 가능성 있음. **Cycle 3도 Jump Mode 진입 시 Convergence Guard에 의해 HITL(Human-In-The-Loop) 개입 필요.**

대안:
1. **informational을 scope 외 판정**: scope_boundary.excludes에 "일본어 학습", "역사/문화 심층 해설"이 포함되어 있으므로, informational 앵커 자체를 optional로 전환하면 deficit 해소. → Plan Modify에서 검토.
2. **실용 표현 GU 2~3개 생성 후 Normal Mode**: scope 내 "실용 여행 표현"으로 한정하면 GU 생성 가능. → Normal Mode로 Cycle 3 진입 가능.

---

## 12. 종합 평가

### 성과
- geography deficit **완전 해소** (0.200 → 0.000). Jump Mode의 핵심 목표 달성.
- 충돌률 **건강 구간 진입** (0.095 → 0.036). KU-0011 disputed 해결 기여.
- 다중근거율 **0.821** — 목표 대비 충분. 신규 KU 7개 모두 다중출처.
- 5대 불변원칙 4/5 완전 준수, 1개(Prescription-compiled) 부분 준수.

### 잔존 과제
1. **risk:informational 결손** — 유일한 축 결손. Convergence Guard 직결.
2. **entity hierarchy 미정의** — 3 Cycle 누적 미해결 (RX-04 → RX-10 → RX-13).
3. **RX-09 이관** (KU-0007 SIM) — 3 Cycle 연속 이관. 우선순위 재평가 필요.

### 다음 단계

→ **Plan Modify** (`revised-plan-c3.md`)에서:
1. risk:informational 결손 해소 전략 결정 (scope 재판정 vs GU 생성)
2. Convergence Guard: Jump vs Normal 판정
3. RX-12~16 반영 + RX-09/10 이관분 처리 방안
4. Cycle 3 Target Gap 선정 + Budget 배분
