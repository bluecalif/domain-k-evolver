# Phase 5 Readiness Gate — 상세 분석 보고서

> Generated: 2026-03-08
> Benchmark: japan-travel 15 Cycles (seed state → full run, plateau 비활성)
> Gate Verdict: **FAIL** (VP1 3/5, VP2 2/6 실패 / VP3 5/6 통과)
> 비교 기준: Phase 4 Gate 결과 (2026-03-07)

---

## 1. 실행 요약

| 항목 | Phase 4 | Phase 5 | 변화 |
|------|---------|---------|------|
| **Gate 판정** | FAIL (VP1, VP2) | FAIL (VP1, VP2) | — |
| 실행 Cycles | 13/15 (plateau 조기종료) | 15/15 (강제 완주) | +2 |
| 최종 Active KU | 90 | 30 | **-67%** |
| Disputed KU | 0 | 0 | — |
| Total GU | 96 | 232 | **+142%** |
| Open GU | 15 | 110 | **+633%** |
| Resolved GU | 81 | 122 | +51% |
| Audit 실행 | 2회 | 3회 | +1 |
| Policy 수정 | 2회 (v1→v2) | 3회 (v1→v3) | +1 |
| conflict_rate | 0.000 (최종) | 0.000 (C3 이후) | — |

### 핵심 차이: KU 30 vs 90

Phase 4는 기존 auto-run 결과(cycle 14, 90 KU)에서 연속 실행된 반면, Phase 5는 **cycle-0 seed state(13 KU)에서 fresh start**. 15 cycle 동안 +17 KU 성장으로, Phase 4의 13 cycle +63 KU 대비 **성장률이 1/4 수준**.

원인: Phase 5에서 추가된 refresh/balance GU 생성이 GU 총량을 폭증시켰고(96→232), collect 노드의 처리량은 cycle당 8 GU로 동일. 결과적으로 **GU 생성 속도 > GU 해결 속도** 불균형 발생.

---

## 2. Trajectory

```
Cycle  GU_open  GU_res  Mode    Confidence  Conflict
  C1      57       8   normal   0.851       0.182
  C2      94      18   jump     0.816       0.167
  C3     108      26   normal   0.787       0.000
  C4     112      34   normal   0.781       0.000
  C5     113      42   normal   0.777       0.000
  C6     113      50   normal   0.769       0.000
  C7     113      58   normal   0.764       0.000
  C8     112      66   normal   0.782       0.000
  C9     112      74   normal   0.786       0.000
 C10     112      82   normal   0.777       0.000
 C11     111      90   normal   0.776       0.000
 C12     110      98   normal   0.787       0.000
 C13     110     106   normal   0.786       0.000
 C14     110     114   normal   0.779       0.000
 C15     110     122   normal   0.772       0.000
```

**관찰:**
- C1→C2에서 GU 57→94 급증 (refresh/balance GU 대량 생성)
- C3 이후 GU_open 안정화 (~110), 매 cycle 8 GU resolved
- Jump mode는 C2에서 1회만 발동 — explore 부족의 원인
- Confidence 0.85→0.77로 지속 하락

---

## 3. 관점별 상세 분석

### VP1: Expansion with Variability — FAIL (3/5)

| 기준 | Phase 4 | Phase 5 | 임계치 | 판정 | 분석 |
|------|---------|---------|--------|------|------|
| R1 Category Gini | 0.862 (Shannon) | **0.367** | ≤ 0.45 | **PASS** | Gini 교체 효과 + 카테고리 분산 양호 |
| R2 Blind Spot | **0.85** | **0.0** | ≤ 0.40 | **PASS** | axis_tags 전파 완전 해결 |
| R3 Late Discovery | 3 | **0** | ≥ 2 | FAIL | 후반 cycle에서 신규 KU 발견 없음 |
| R4 Field Gini | **0.518** | **0.437** | ≤ 0.45 | **PASS** | field 다양성 억제 효과 |
| R5 Explore Yield | 1.0 | **0.067** | ≥ 0.20 | FAIL | Jump 1회(C2)뿐, explore 극히 부족 |

**Phase 5 해결 항목 (2개):**
- **R2 blind_spot 0.85→0.0**: `_copy_axis_tags()`, `_infer_geography()` 코드가 KU에 geography axis_tags를 전파. 17/30 KU에 geography 태그 부여.
- **R4 field_gini 0.518→0.437**: `_generate_dynamic_gus()`의 과다 필드 억제(count > mean×1.5) 효과.

**미해결 항목 (2개):**
- **R3 late_discovery=0**: 30 KU 중 C2 이후 신규 KU가 거의 없음. GU는 생성되지만 collect→integrate에서 KU로 전환되는 비율 저조. 이는 entity_key가 `*`(와일드카드)인 GU의 collect 성공률 문제.
- **R5 explore_yield=0.067**: Jump mode가 C2에서 1회만 발동. 이후 normal mode 고정. Phase 4에서는 전 cycle Jump이었으나, Phase 5의 GU 폭증으로 open GU가 충분하여 Jump trigger가 미발동.

### VP2: Completeness — FAIL (2/6, Critical FAIL 2건)

| 기준 | Phase 4 | Phase 5 | 임계치 | 판정 | 분석 |
|------|---------|---------|--------|------|------|
| R1 Gap Resolution | 0.844 | **0.545** | ≥ 0.85 | **FAIL** [CRITICAL] | 122/232, GU 폭증이 원인 |
| R2 Min KU/Cat | 3 | **1** | ≥ 5 | **FAIL** [CRITICAL] | connectivity=1, dining=1 |
| R3 Multi Evidence | 0.911 | **0.800** | ≥ 0.80 | PASS | 경계선 통과 |
| R4 Avg Confidence | 0.801 | **0.772** | ≥ 0.82 | FAIL | 지속 하락 |
| R5 Health Grade | 1.4 | **1.4** | ≥ 1.4 | PASS | 경계선 통과 |
| R6 Staleness | 59 | **11** | ≤ 2 | FAIL | 개선됨 (59→11) but 미통과 |

**R1 gap_resolution 악화 분석 (0.844→0.545):**

```
GU 구성 (232개):
  gap_type: stale=117, missing=115
  open GU trigger 분포:
    category_balance: 44  (balance GU 미해결)
    adjacent_gap:     36  (동적 GU 미해결)
    stale_refresh:    11  (refresh GU 미해결)
    기타:             19
```

Phase 5의 `_generate_refresh_gus()`와 `_generate_balance_gus()`가 매 cycle GU를 생성하지만, collect 노드가 cycle당 8 GU만 처리. **117개 stale GU** 중 대부분이 미해결 상태로 누적.

**R2 min_ku_per_cat 악화 분석 (3→1):**

```
Category KU Count:
  regulation   :  9 [OK]
  accommodation:  5 [OK]
  pass-ticket  :  5 [OK]
  transport    :  5 [OK]
  attraction   :  2 [FAIL]
  payment      :  2 [FAIL]
  connectivity :  1 [FAIL]  ← min
  dining       :  1 [FAIL]  ← min
```

Balance GU가 44개 open으로 잔존 — 생성은 되었으나 collect에서 해당 카테고리의 정보 수집 실패. connectivity/dining은 도메인 특성상 검색 결과가 부족한 카테고리.

**R6 staleness 개선 분석 (59→11):**

Phase 5의 `_generate_refresh_gus()`가 stale KU를 감지하여 refresh GU를 생성. 일부는 실제로 갱신되었으나 (59→11), 나머지 11개는 collect에서 최신 정보를 찾지 못해 미갱신. seed KU의 `observed_at`이 2025년이므로 TTL(365일) 기준 대부분 만료.

### VP3: Self-Governance — PASS (5/6)

| 기준 | Phase 4 | Phase 5 | 임계치 | 판정 |
|------|---------|---------|--------|------|
| R1 Audit Count | 2 | 3 | ≥ 2 | **PASS** |
| R2 Policy Changes | 2 | 3 | ≥ 1 | **PASS** |
| R3 Threshold Adapt | 2 | 3 | ≥ 1 | **PASS** |
| R4 Adapted Ratio | 13 | **1** | ≥ 3 | FAIL |
| R5 Rollback | 0 | 0 | ≥ 0 | **PASS** |
| R6 Closed Loop | 1 | 1 | ≥ 1 | **PASS** |

VP3는 Phase 4, 5 모두 핵심 거버넌스 기능 작동 확인. R4 adapted_ratio만 미달 — policy 변경 후 성능 개선 비율이 낮음 (patch가 TTL 연장 위주라 즉시 효과 미미).

---

## 4. Phase 5 코드 변경 효과 평가

### 해결된 문제 (3/4)

| Phase 5 Task | 대상 | Phase 4 값 | Phase 5 값 | 효과 |
|-------------|------|-----------|-----------|------|
| Task 5.0: Gini 교체 | VP1-R1 | 0.862 (Shannon) | 0.367 (Gini) | **PASS** |
| Task 5.1~5.4: axis_tags 전파 | VP1-R2 blind_spot | 0.85 | 0.0 | **PASS** |
| Task 5.7~5.8: Field 다양성 | VP1-R4 field_gini | 0.518 | 0.437 | **PASS** |

### 부분 해결

| Phase 5 Task | 대상 | Phase 4 값 | Phase 5 값 | 효과 |
|-------------|------|-----------|-----------|------|
| Task 5.5~5.6: Staleness 갱신 | VP2-R6 staleness | 59 | 11 | 개선 but 미통과 |

### 부작용 (의도치 않은 악화)

| 현상 | 원인 | 영향 |
|------|------|------|
| GU 폭증 (96→232) | refresh/balance GU 생성 제어 없음 | gap_resolution 0.84→0.54 |
| KU 성장 둔화 (90→30) | GU 다수가 collect 불가 + fresh start | min_ku 3→1 |
| Explore 부족 | open GU 충분→Jump 미발동 | explore_yield 1.0→0.07 |
| Confidence 하락 | 수집 KU 품질 저하 | avg_conf 0.80→0.77 |

---

## 5. 실패 원인의 계층 분류

```
Level 0 (실행 환경)
  [!] Fresh start (seed) vs Resume (Phase 4) — KU 30 vs 90
  [!] Tavily API 한도 초과로 이전 실행 3회 실패 (API 업그레이드 후 해결)

Level 1 (Phase 5 코드 효과 — 해결됨)
  [O] blind_spot 0.85 → 0.0 (axis_tags 전파)
  [O] field_gini 0.518 → 0.437 (과다 필드 억제)
  [O] staleness 59 → 11 (refresh GU 메커니즘)

Level 2 (Phase 5 부작용 — 신규 문제)
  [X] GU 폭증: refresh(117) + balance(44) GU가 collect 처리량 초과
  [X] gap_resolution 급락: 0.844 → 0.545 (open GU 누적)
  [X] explore 부족: Jump trigger 미발동 (open GU 과잉으로)

Level 3 (구조적 한계 — Phase 4부터 미해결)
  [X] min_ku: connectivity/dining 카테고리 collect 성공률 저조
  [X] avg_confidence: 후반부 KU 품질 체감적 하락
  [X] late_discovery: 도메인 포화 후 신규 발견 어려움
```

---

## 6. 정량 비교표

| 지표 | Phase 4 | Phase 5 | 임계치 | Phase 5 판정 | 변화 방향 |
|------|---------|---------|--------|-------------|----------|
| VP1-R1 category_gini | 0.862* | 0.367 | ≤ 0.45 | PASS | 지표 변경 |
| VP1-R2 blind_spot | 0.85 | 0.0 | ≤ 0.40 | **PASS** | 개선 |
| VP1-R3 late_discovery | 3 | 0 | ≥ 2 | FAIL | 악화 |
| VP1-R4 field_gini | 0.518 | 0.437 | ≤ 0.45 | **PASS** | 개선 |
| VP1-R5 explore_yield | 1.0 | 0.067 | ≥ 0.20 | FAIL | 악화 |
| VP2-R1 gap_resolution | 0.844 | 0.545 | ≥ 0.85 | FAIL | **악화** |
| VP2-R2 min_ku_per_cat | 3 | 1 | ≥ 5 | FAIL | **악화** |
| VP2-R3 multi_evidence | 0.911 | 0.800 | ≥ 0.80 | PASS | 하락 |
| VP2-R4 avg_confidence | 0.801 | 0.772 | ≥ 0.82 | FAIL | 악화 |
| VP2-R5 health_grade | 1.4 | 1.4 | ≥ 1.4 | PASS | 유지 |
| VP2-R6 staleness | 59 | 11 | ≤ 2 | FAIL | 개선 |
| VP3-R1 audit_count | 2 | 3 | ≥ 2 | PASS | 개선 |
| VP3-R2 policy_changes | 2 | 3 | ≥ 1 | PASS | 개선 |
| VP3-R3 threshold_adapt | 2 | 3 | ≥ 1 | PASS | 개선 |
| VP3-R4 adapted_ratio | 13 | 1 | ≥ 3 | FAIL | 악화 |
| VP3-R5 rollback | 0 | 0 | ≥ 0 | PASS | 유지 |
| VP3-R6 closed_loop | 1 | 1 | ≥ 1 | PASS | 유지 |

*Phase 4 R1은 Shannon Entropy, Phase 5는 Gini Coefficient로 지표 자체가 변경됨

---

## 7. 논의 필요 사항

### 7.1 GU 생성 속도 제어 (핵심 이슈)

Phase 5의 refresh/balance GU 생성이 **rate-limiting 없이** 매 cycle 실행되어 GU 총량이 232까지 증가. collect는 cycle당 8 GU만 처리하므로 **구조적 불균형**. 선택지:

- **A. GU 생성 상한 강화**: refresh 상한 10→3, balance 상한 도입 (예: cycle당 2)
- **B. collect 처리량 증가**: workers 5→10, budget 확대
- **C. GU 우선순위 정리**: 장기 미해결 open GU 자동 deferred 처리
- **D. 복합**: A+C 조합

### 7.2 Fresh Start vs Resume 문제

Phase 4 Gate는 기존 auto-run 결과(90 KU)에서 시작했으나, Phase 5는 seed(13 KU)에서 시작. 공정한 비교를 위해:

- **Option 1**: Phase 4와 동일하게 기존 결과에서 resume (코드 변경 효과만 측정)
- **Option 2**: 항상 seed에서 시작 (end-to-end 능력 측정)
- **Option 3**: 두 모드 모두 실행하여 각각 보고

### 7.3 Gate 임계치 적정성 재검토

일부 임계치가 현재 시스템 능력 대비 과도할 수 있음:

| 기준 | 현재 임계치 | Phase 5 값 | 조정 후보 | 근거 |
|------|-----------|-----------|----------|------|
| gap_resolution | ≥ 0.85 | 0.545 | ≥ 0.65 | GU 생성 메커니즘 추가로 분모 증가 불가피 |
| min_ku_per_cat | ≥ 5 | 1 | ≥ 3 | 도메인 특성상 일부 카테고리 정보 희소 |
| staleness | ≤ 2 | 11 | ≤ 10 | seed KU TTL 만료는 구조적 |
| explore_yield | ≥ 0.20 | 0.067 | ≥ 0.05 | open GU 충분 시 Jump 미발동은 정상 동작 |
| late_discovery | ≥ 2 | 0 | ≥ 1 | 15 cycle 내 KU 포화 가능 |

### 7.4 Explore/Jump Mode 발동 조건 재검토

현재 Jump trigger는 open GU가 부족할 때 발동. Phase 5에서는 GU가 과잉이라 항상 normal. 하지만 balance/refresh GU가 실제로 해결 불가능한 GU라면, "유효 open GU" 기준으로 trigger를 판정해야 함.

### 7.5 다음 단계 선택지

| 선택지 | 내용 | 예상 효과 |
|--------|------|----------|
| **Phase 5.5**: GU rate-limiting | refresh/balance 상한 축소 + deferred 처리 | gap_res ↑, KU 성장 집중 |
| **Gate 기준 조정** | 현실적 임계치로 완화 | 즉시 PASS 가능 but 기준 신뢰도 ↓ |
| **Phase 6 진행** | Gate FAIL 수용, Multi-Domain으로 이동 | 빠른 진행 but 품질 부채 |
| **Hybrid**: 기준 일부 조정 + GU 제어 | 합리적 임계치 + 코드 보완 | 균형잡힌 접근 |

---

## 8. 결론

Phase 5의 핵심 목표였던 **axis_tags 전파, staleness 갱신, field 다양성**은 코드 수준에서 성공적으로 구현되었으며, blind_spot(0.85→0.0)과 field_gini(0.518→0.437)의 극적 개선으로 입증됨.

그러나 **GU 생성 속도 제어 부재**로 인한 부작용(gap_resolution 급락, KU 성장 둔화)이 전체 Gate 판정을 악화시킴. 이는 Phase 5 설계 시 "생성 메커니즘 추가"에만 집중하고 "생성-해결 균형"을 고려하지 않은 결과.

**Gate PASS를 위한 최소 조치:**
1. GU rate-limiting (refresh ≤3/cycle, balance ≤2/cycle) — gap_resolution 개선
2. 장기 미해결 GU deferred 처리 — open GU 정리
3. Gate 임계치 중 explore_yield, late_discovery는 현실적 조정 필요

이 조치만으로 VP1 PASS, VP2는 gap_resolution + min_ku 개선 시 PASS 가능.
