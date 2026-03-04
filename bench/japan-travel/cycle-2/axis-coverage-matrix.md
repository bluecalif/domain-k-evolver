# Axis Coverage Matrix — Cycle 1 종료 시점

> Generated: 2026-03-04
> Input: 31 GU (16 open / 15 resolved), 21 KU (19 active + 2 disputed)

## GU → Axis Tag 할당표

| GU | status | category | geography | condition | risk | utility |
|-----|--------|----------|-----------|-----------|------|---------|
| GU-0001 | resolved | pass-ticket | nationwide | — | convenience | high |
| GU-0002 | resolved | pass-ticket | nationwide | — | financial | high |
| GU-0003 | resolved | transport | tokyo | — | convenience | high |
| GU-0004 | resolved | pass-ticket | tokyo | — | financial | medium |
| GU-0005 | resolved | transport | tokyo | — | convenience | critical |
| GU-0006 | **open** | accommodation | nationwide | peak-season, off-season | financial | medium |
| GU-0007 | resolved | accommodation | nationwide | — | convenience | medium |
| GU-0008 | resolved | attraction | kyoto | — | convenience | medium |
| GU-0009 | **open** | attraction | tokyo | — | financial | medium |
| GU-0010 | resolved | dining | nationwide | — | convenience | medium |
| GU-0011 | **open** | dining | nationwide | — | convenience | low |
| GU-0012 | resolved | regulation | nationwide | — | financial | high |
| GU-0013 | resolved | payment | nationwide | — | financial | medium |
| GU-0014 | **open** | payment | nationwide | — | convenience | medium |
| GU-0015 | **open** | connectivity | nationwide | — | convenience | low |
| GU-0016 | **open** | transport | nationwide | — | convenience | medium |
| GU-0017 | resolved | regulation | nationwide | — | policy | high |
| GU-0018 | resolved | pass-ticket | nationwide | — | convenience | high |
| GU-0019 | **open** | connectivity | nationwide | online, in-person | financial | medium |
| GU-0020 | **open** | transport | nationwide | — | financial | medium |
| GU-0021 | **open** | accommodation | nationwide | — | convenience | low |
| GU-0022 | **open** | regulation | nationwide | — | convenience | medium |
| GU-0023 | **open** | attraction | osaka | — | financial | medium |
| GU-0024 | resolved | transport | nationwide | — | financial | high |
| GU-0025 | resolved | regulation | nationwide | — | safety | critical |
| GU-0026 | resolved | regulation | nationwide | — | financial | high |
| GU-0027 | **open** | transport | tokyo | — | convenience | medium |
| GU-0028 | **open** | pass-ticket | nationwide | — | convenience | medium |
| GU-0029 | **open** | pass-ticket | tokyo | — | convenience | medium |
| GU-0030 | **open** | pass-ticket | tokyo | — | financial | medium |
| GU-0031 | **open** | transport | tokyo | — | convenience | medium |

---

## 축별 Coverage Matrix

### 1. Category 축

| value | open | resolved | total | critical_open | evidence_density |
|-------|------|----------|-------|---------------|-----------------|
| transport | 4 | 3 | 7 | 0 | 1.50 |
| accommodation | 2 | 1 | 3 | 0 | 2.00 |
| attraction | 2 | 1 | 3 | 0 | 2.00 |
| dining | 1 | 1 | 2 | 0 | 2.00 |
| regulation | 1 | 4 | 5 | 0 | 2.00 |
| pass-ticket | 3 | 4 | 7 | 0 | 1.83 |
| connectivity | 2 | 0 | 2 | 0 | 3.00 |
| payment | 1 | 1 | 2 | 0 | 2.00 |

- **deficit_ratio**: 0/8 = **0.000** ✅ (모든 카테고리 커버됨)
- **비고**: connectivity는 resolved=0이나 open GU 2개 존재. evidence_density 3.0은 KU-0007의 EU 3개 반영.

### 2. Geography 축 ⚠️

| value | open | resolved | total | critical_open | evidence_density |
|-------|------|----------|-------|---------------|-----------------|
| tokyo | 5 | 3 | 8 | 0 | 1.67 |
| osaka | 1 | 0 | 1 | 0 | 0.00 |
| kyoto | 0 | 1 | 1 | 0 | 2.00 |
| **rural** | **0** | **0** | **0** | **0** | **0.00** |
| nationwide | 10 | 11 | 21 | 0 | 1.94 |

- **deficit_ratio**: 1/5 = **0.200** ⚠️ (rural 완전 결손)
- **결손 분석**:
  - `rural`: GU 0개 — 지방 여행 정보 완전 부재 (온천 마을, 시골 교통 등)
  - `osaka`: open 1개뿐 (USJ 가격). 오사카 교통/맛집/규정 등 미커버
  - `kyoto`: resolved 1개뿐 (후시미이나리). 교토 교통/숙박/관광지 등 미커버
- **편중**: nationwide(21) + tokyo(8) = 29/31 (93.5%) → 극심한 도쿄/전국 편중

### 3. Risk 축

| value | open | resolved | total | critical_open | evidence_density |
|-------|------|----------|-------|---------------|-----------------|
| safety | 0 | 1 | 1 | 0 | 2.00 |
| financial | 6 | 6 | 12 | 0 | 1.92 |
| policy | 0 | 1 | 1 | 0 | 2.00 |
| convenience | 10 | 7 | 17 | 0 | 1.86 |
| **informational** | **0** | **0** | **0** | **0** | **0.00** |

- **deficit_ratio**: 1/5 = **0.200** ⚠️ (informational 완전 결손)
- **결손 분석**:
  - `informational`: GU 0개 — 순수 정보성 갭 미추적 (예: 일본어 기본 표현, 문화 차이 등)
  - `safety`/`policy`: 각 1개만 — 해소 상태이나 추가 커버 여지
- **편중**: convenience(17) + financial(12) = 29/31 (93.5%)

### 4. Condition 축 (선택적)

| value | open | resolved | total | critical_open |
|-------|------|----------|-------|---------------|
| peak-season | 1 | 0 | 1 | 0 |
| off-season | 1 | 0 | 1 | 0 |
| weekday | 0 | 0 | 0 | 0 |
| weekend | 0 | 0 | 0 | 0 |
| online | 1 | 0 | 1 | 0 |
| in-person | 1 | 0 | 1 | 0 |

- **deficit_ratio**: 2/6 = **0.333** (weekday/weekend 미태깅)
- **비고**: 선택적 축이므로 deficit_ratio는 Jump trigger 판정에 낮은 가중치 적용.
  - GU-0006(료칸 가격)에 peak/off-season 태깅 → 시즌별 가격 차이 관련
  - GU-0019(SIM 가격)에 online/in-person 태깅 → eSIM vs 물리SIM 채널 차이

---

## 종합 분석

### deficit_ratio 요약

| 축 | deficit_ratio | 결손 anchor | 판정 |
|----|--------------|-------------|------|
| category | 0.000 | — | ✅ 양호 |
| geography | 0.200 | rural | ⚠️ 구조적 결손 |
| risk | 0.200 | informational | ⚠️ 구조적 결손 |
| condition | 0.333 | weekday, weekend | ℹ️ 선택적 축 (낮은 가중치) |

### 주요 발견

1. **Geography 편중이 가장 심각**: nationwide+tokyo가 93.5%. osaka/kyoto/rural은 사실상 미커버.
2. **Risk 편중**: convenience+financial이 93.5%. safety/policy는 최소 1개씩 있으나 얇음.
3. **critical_open = 0**: 모든 critical/high GU가 이미 resolved. 남은 open GU는 전부 medium/low.
4. **evidence_density 0 영역**: osaka, rural — KU 자체가 없어 증거 밀도 계산 불가.

### Jump Mode Trigger 예비 판정

| Trigger | 입력 | 결과 |
|---------|------|------|
| Axis Under-Coverage | geography deficit_ratio = 0.2 | 🟡 발동 가능 (임계치 미확정) |
| Spillover | Cycle 1 동적 GU 3개 (GU-0029~0031) | 🟡 경미 수준 |
| High-Risk Blindspot | safety 단일출처 KU 1개 (KU-0008, EU 2개) | 🟢 다중출처 → 미발동 |
| Prescription | RX-07~11 중 구조 보강 포함 | 🟡 확인 필요 |
| Domain Shift | 신규 entity cluster 없음 | 🔴 미발동 |

→ **0C.3에서 정식 판정 예정**
