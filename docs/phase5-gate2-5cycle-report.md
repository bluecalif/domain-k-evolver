# Phase 5 Gate #2 — 5 Cycle 검증 보고서

> Generated: 2026-03-08
> Benchmark: japan-travel 5 Cycles (cycle-0 seed → fresh start, plateau 비활성)
> Gate Verdict: **FAIL** (VP1 4/5 PASS, VP2 1/6 FAIL, VP3 1/6 FAIL)
> 변경사항: Task 5.10a bench 정리 + Task 5.10b target_count/cap 하드캡 제거 (D-60)

---

## 1. 실행 요약 — 3회 Gate 비교

| 항목 | Gate #0 (Phase 4) | Gate #1 (Phase 5, 15c) | **Gate #2 (5c, 캡 제거)** |
|------|-------------------|------------------------|---------------------------|
| 실행 Cycles | 13 (plateau 조기종료) | 15 (강제 완주) | **5** |
| Active KU | 90 | 30 | **78** |
| Disputed KU | 0 | 0 | **0** |
| Total GU | 96 | 232 | **138** |
| Open GU | 15 | 110 | **77** |
| Resolved GU | 81 | 122 | **61** |
| collect 처리량/cycle | ~8 | ~8 | **~16** |
| KU 성장률/cycle | 4.8 | 1.1 | **13.0** |
| conflict_rate (최종) | 0.000 | 0.000 | **0.064** |

### 핵심 변화: 하드캡 제거 효과

- **collect 처리량 2배**: target_count 하드캡 8→비례 스케일링 (open=77 → target=max(4, ceil(77×0.4))=31)
  - 실제 cycle 5에서 16 GU 처리 (seed state에서 시작이므로 초기 open 적음)
- **KU 성장률 13.0/cycle** (Gate #1의 11.8배): 5 cycle 만에 78 KU 달성
- **GU 총량 억제**: Gate #1의 232에서 138으로 (-40.5%) — collect 처리량 증가로 해결 속도 개선

---

## 2. Trajectory (Cycle-over-Cycle)

```
Cycle  KU_active  GU_total  GU_open  GU_res  Mode    gap_res    conf     conflict
  C1       33        61       49       12   normal   0.343    0.791     0.121
  C2       43        98       76       22   jump     0.268    0.777     0.116
  C3       53       117       85       32   jump     0.299    0.768     0.038
  C4       65       127       82       45   jump     0.385    0.765     0.046
  C5       78       138       77       61   jump     0.477    0.757     0.064
```

### Cycle별 GU 동역학

| Cycle | 신규 GU | 해결 GU | 순증 open | KU 증가 |
|-------|---------|---------|-----------|---------|
| C1 | 61 | 12 | +49 | +33 (seed) |
| C2 | +37 | +10 | +27 | +10 |
| C3 | +19 | +10 | +9 | +10 |
| C4 | +10 | +13 | **-3** | +12 |
| C5 | +11 | +16 | **-5** | +13 |

**전환점**: C4부터 open GU 순감소 (해결 > 생성). C2의 GU 폭증(+37)은 balance/refresh GU 초기 대량 생성 때문이며, 이후 안정화.

### 추세선 분석

- **GU 생성**: C1 61 → C2 +37 → C3 +19 → C4 +10 → C5 +11 (감소 후 안정)
- **GU 해결**: C1 12 → C2 +10 → C3 +10 → C4 +13 → C5 +16 (**증가 추세**)
- **예측**: C6 이후 해결/생성 비율 역전 지속 → 15 cycle 시 gap_resolution 개선 기대

---

## 3. Gate 판정 상세

### VP1: Expansion with Variability — **PASS (4/5)**

| 기준 | Gate #0 | Gate #1 | **Gate #2** | 임계치 | 판정 |
|------|---------|---------|-------------|--------|------|
| R1 category_gini | 0.862 (Shannon) | 0.367 | **0.151** | ≤ 0.45 | **PASS** ↑ |
| R2 blind_spot | 0.85 | 0.0 | **0.0** | ≤ 0.40 | **PASS** = |
| R3 late_discovery | 3 | 0 | **0** | ≥ 2 | FAIL |
| R4 field_gini | 0.518 | 0.437 | **0.301** | ≤ 0.45 | **PASS** ↑ |
| R5 explore_yield | 1.0 | 0.067 | **0.8** | ≥ 0.20 | **PASS** ↑ |

**개선:**
- **category_gini 0.151** — 8개 카테고리 분포 거의 균등 (dining 15, connectivity 12, 최소 pass-ticket 5)
- **field_gini 0.301** — 필드 다양성 대폭 개선
- **explore_yield 0.8** — Jump mode 4회 연속 발동(C2~C5), explore 활발

**미달:** late_discovery=0 — 5 cycle이므로 후반 cycle(C8+) 신규 발견 판정 불가

### VP2: Completeness — **FAIL (1/6)** ⚠️ CRITICAL

| 기준 | Gate #0 | Gate #1 | **Gate #2** | 임계치 | 판정 |
|------|---------|---------|-------------|--------|------|
| R1 gap_resolution | 0.844 | 0.545 | **0.477** | ≥ 0.85 | **FAIL** ↓ |
| R2 min_ku_per_cat | 3 | 1 | **5** | ≥ 5 | **PASS** ↑↑ |
| R3 multi_evidence | — | — | **0.699** | ≥ 0.80 | FAIL |
| R4 avg_confidence | — | — | **0.757** | ≥ 0.82 | FAIL |
| R5 health_grade | — | — | **1.2** | ≥ 1.4 | FAIL |
| R6 staleness | 59 | 11 | **55** | ≤ 2 | FAIL |

**개선:**
- **min_ku_per_cat 1→5** — balance GU + 캡 제거 효과로 모든 카테고리 5+ KU 달성

**악화/미달:**
- **gap_resolution 0.477** — 총 GU 138개 중 61개 해결. 5 cycle만으로 부족. 단, 해결 속도 증가 추세.
- **staleness 55** — seed state(2026-03-02 기준 KU)가 갱신 안 된 상태. 5 cycle로는 전체 stale KU 갱신 불가.
- **avg_confidence 0.757** — 새 KU가 대량 추가되면서 평균 하락

### VP3: Self-Governance — **FAIL (1/6)** (5 cycle 한계)

| 기준 | Gate #0 | Gate #1 | **Gate #2** | 임계치 | 판정 |
|------|---------|---------|-------------|--------|------|
| R1 audit_count | 2 | 3 | **1** | ≥ 2 | FAIL |
| R2 policy_changes | 2 | 3 | **0** | ≥ 1 | FAIL |
| R3 threshold_adapt | — | — | **0** | ≥ 1 | FAIL |
| R4 adapted_ratio | — | — | **4** | ≥ 3 | PASS |
| R5 rollback | — | 0 | **0** | ≥ 0 | FAIL |
| R6 closed_loop | — | — | **0** | ≥ 1 | FAIL |

**원인**: audit_interval=5이므로 5 cycle에서 audit 1회만 실행. Policy 수정/롤백은 audit 2회+ 필요. 15 cycle에서는 3회 audit 예상.

---

## 4. 카테고리별 상세 분석

### KU 분포

| Category | KU | % | Conf(avg) | Multi-Ev | Stale(>7d) |
|----------|-----|------|-----------|----------|------------|
| dining | 15 | 19.2% | — | 93.3% | 93.3% |
| connectivity | 12 | 15.4% | — | 91.7% | 91.7% |
| accommodation | 10 | 12.8% | — | 20.0% | **100%** |
| attraction | 10 | 12.8% | — | 60.0% | 80.0% |
| regulation | 9 | 11.5% | — | 66.7% | 44.4% |
| transport | 9 | 11.5% | — | 66.7% | 66.7% |
| payment | 8 | 10.3% | — | 87.5% | 62.5% |
| pass-ticket | 5 | 6.4% | — | 80.0% | 40.0% |

**위험 카테고리**: accommodation — multi-evidence 20% (최하위), staleness 100%

### GU 상태 분석

| gap_type | total | open | resolved | 해결률 |
|----------|-------|------|----------|--------|
| missing | 88 | 30 | 58 | **65.9%** |
| stale | 50 | 47 | 3 | **6.0%** |

**핵심 발견**: stale GU 해결률 6.0% — 47/50개가 여전히 open. Refresh 메커니즘이 stale GU를 생성하지만, collect→integrate에서 실제 KU 갱신(observed_at 갱신)이 충분히 이루어지지 않음.

---

## 5. 캡 제거 효과 정량 평가

### 5.1 처리량 비교 (Gate #1 vs Gate #2)

| 지표 | Gate #1 (캡 8) | Gate #2 (캡 제거) | 변화 |
|------|---------------|-------------------|------|
| Cycle당 GU 해결 | ~8 | C4: 13, C5: 16 | **+100%** |
| Cycle당 KU 생성 | 1.1 | 13.0 | **+1082%** |
| Open GU 추세 | 증가→안정 | 증가→**감소** | ✅ 전환 |
| Jump mode 빈도 | 1/15 cycle | 4/5 cycle | ✅ 활발 |

### 5.2 GU 균형 달성 시점 추정

C4~C5 추세(순감 -3, -5/cycle)로 extrapolation:
- **C10 예상**: open GU ~52, resolved ~86, gap_resolution ~0.62
- **C15 예상**: open GU ~27, resolved ~111, gap_resolution ~0.80

→ 15 cycle에서도 gap_resolution 0.85 미달 가능성 있음. 이유:
1. stale GU 해결률 극저(6%)가 전체 gap_resolution 하락의 주 원인
2. missing GU 해결률은 65.9%로 양호

---

## 6. 구조적 문제 진단

### 6.1 Staleness 병목 (가장 심각)

- stale GU 50개 중 47개 open — Critique가 stale GU를 대량 생성하나 Integrate에서 갱신 실패
- 원인 추정: stale GU의 target이 기존 KU인데, collect에서 "새 정보"를 찾으면 **신규 KU로 생성**하지 기존 KU를 갱신하지 않음
- staleness_risk = 55 (건강 임계치 0) → VP2-R6 FAIL

### 6.2 Confidence 하락

- C1(0.791) → C5(0.757) 지속 하락
- balance GU로 생성된 KU(entity_key에 `balance-N` 포함)의 confidence가 0.5~0.7으로 낮음
- 기존 seed KU(0.85~0.95)보다 평균을 끌어내림

### 6.3 late_discovery = 0

- 5 cycle 한계이므로 판단 보류
- 15 cycle에서는 C8+ 이후 신규 entity 발견 여부로 판정

### 6.4 gap_resolution 구조적 한계

- 분모(total GU)가 계속 증가: balance GU(캡 없음) + refresh GU(10/cycle) + dynamic GU(12/30)
- 분자(resolved GU) 증가 속도가 분모를 따라잡지 못함
- **핵심**: balance GU 생성량 제한이 없으면, min_ku_per_cat ≥5 달성 후에도 계속 생성됨

---

## 7. 15 Cycle 실행 전 판단 기준

### 낙관 시나리오 (15 cycle PASS 가능)

- open GU 감소 추세 유지 → gap_resolution 0.85+ 도달
- stale GU가 점진적으로 해결됨
- audit 3회 → policy 변경 → VP3 개선

### 비관 시나리오 (15 cycle에도 FAIL)

- balance GU 무제한 생성이 분모를 계속 키움
- stale GU 해결률 6%가 개선되지 않으면 staleness 유지
- gap_resolution이 0.80 근처에서 정체

### 권장 판단

| 항목 | 15c 실행 시 예상 | 근거 |
|------|-----------------|------|
| VP1 | **PASS (4~5/5)** | 이미 4/5, late_discovery만 미달 |
| VP2 gap_res | **0.75~0.82** (미달 가능) | stale GU 해결률 병목 |
| VP2 staleness | **개선 but 미달** | 5c에 55 → 15c에 ~30 예상 |
| VP3 | **PASS (4~5/6)** | audit 3회 → policy 변경 기대 |

---

## 8. 요약

| 평가 항목 | 결과 |
|-----------|------|
| **캡 제거 효과** | ✅ 명확 — collect 처리량 2배, KU 성장 11.8배, open GU 감소 전환 |
| **VP1 개선** | ✅ 3/5→4/5, category/field gini 대폭 개선 |
| **VP2 gap_resolution** | ⚠️ 0.477 — stale GU 미해결이 주 병목 |
| **VP2 min_ku_per_cat** | ✅ 1→5 (PASS 달성) |
| **VP3** | ⏳ 5 cycle 한계 — 15 cycle 필요 |
| **15 cycle PASS 확률** | ⚠️ 50~60% — stale GU 해결 메커니즘에 의존 |
