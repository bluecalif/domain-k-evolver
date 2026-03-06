# Phase 2 심층 분석 보고서

> 생성 시각: 2026-03-06 18:51
> 대상: 10 Cycles (Cycle 2~11)
> 벤치 도메인: japan-travel

## 1. Executive Summary

| 항목 | 값 |
|------|-----|
| 총 Cycle | 10 |
| KU (active/disputed/total) | 31/54/85 |
| Evidence Rate | 100.0% |
| Conflict Rate | 63.5% |
| Gap Resolution | 79.8% |
| Health Grade | **D** |
| 권고 수 | 6 (2 critical) |

## 2. Cycle-by-Cycle Trajectory

| Cycle | KU Total | Active | Disputed | GU Open | Resolved | Conflict% | Mode |
|------:|---------:|-------:|---------:|--------:|---------:|----------:|------|
| 2 | 34 | 27 | 7 | 28 | 24 | 20.6% | jump |
| 3 | 37 | 28 | 9 | 25 | 27 | 24.3% | jump |
| 4 | 42 | 29 | 13 | 20 | 32 | 31.0% | jump |
| 5 | 47 | 29 | 18 | 15 | 37 | 38.3% | jump |
| 6 | 51 | 29 | 22 | 21 | 41 | 43.1% | jump |
| 7 | 59 | 30 | 29 | 26 | 49 | 49.2% | jump |
| 8 | 68 | 31 | 37 | 33 | 58 | 54.4% | jump |
| 9 | 72 | 31 | 41 | 29 | 62 | 56.9% | jump |
| 10 | 76 | 31 | 45 | 25 | 66 | 59.2% | jump |
| 11 | 85 | 31 | 54 | 19 | 75 | 63.5% | jump |

## 3. Trend Analysis

### 성장률 비교 (전반부 vs 후반부)

| Metric | 1st Half | 2nd Half | Ratio |
|--------|----------:|----------:|------:|
| ku_total | +25 | +26 | 1.04x |
| ku_active | +3 | +1 | 0.33x |
| ku_disputed | +22 | +25 | 1.14x |
| gu_resolved | +25 | +26 | 1.04x |
| conflict_rate | +28.6% | +14.4% | 0.50x |

### 변곡점

- **ku_active**: Cycle [5, 9]
- **gu_open**: Cycle [6, 9]
- **multi_evidence_rate**: Cycle [5, 9]
- **avg_confidence**: Cycle [5, 8, 9]
- **gap_resolution_rate**: Cycle [6, 9]
- **staleness_risk**: Cycle [5, 9]

## 4. Knowledge Unit 분석

- 총 KU: 85
- Active: 31 (36%)
- Disputed: 54 (64%)

- 카테고리: 8개
- Entity: 39개

## 5. Disputed KU 심층 분석

| 항목 | 값 |
|------|-----|
| Total Disputed | 54 |
| True Conflicts | 0 |
| False Positives | 54 |
| FP Rate | 100.0% |

### Resolution 유형

- `hold`: 53
- `condition_split`: 1

### 근본 원인

`integrate` 노드의 `_detect_conflict()`가 단순 문자열 비교를 사용하여, 동일 entity_key+field에 대한 새 claim이 기존 값과 조금만 달라도 conflict로 판정. semantic 동치 여부를 판단하지 못하므로 대부분 오탐(false positive)이 발생.

## 6. Gap Map 분석

- 총 Gap: 94
- resolved: 75
- open: 19

## 7. API 비용 효율성

| 항목 | 값 |
|------|-----|
| LLM calls | 69 |
| LLM tokens | 196,559 |
| Search calls | 177 |
| Fetch calls | 118 |
| Tokens/KU (total) | 2,312 |
| Tokens/KU (active) | 6,341 |
| Active ratio | 36.5% |
| Waste ratio | 63.5% |

## 8. Health Score

| Metric | Value | Grade |
|--------|------:|-------|
| evidence_rate | 100.0% | HEALTHY |
| multi_evidence_rate | 71.0% | HEALTHY |
| conflict_rate | 63.5% | DANGER |
| avg_confidence | 87.4% | HEALTHY |
| staleness_risk | 4 | DANGER |

**Overall Grade: D** (score: 0.7/2.0)

- Active KU Plateau 감지 (3+ 사이클 정체)

## 9. 개선 권고

### [R1] Integrate 노드 semantic conflict detection 필요

- **심각도**: CRITICAL
- Disputed KU 오탐률 100%. _detect_conflict()의 단순 문자열 비교가 원인. LLM 기반 semantic similarity 판정으로 교체 권고.

### [R2] Dispute resolution mechanism 필요

- **심각도**: HIGH
- Active KU가 31에서 3+ 사이클 정체. 새 claim이 모두 disputed로 분류되어 active로 전환 불가. disputed KU 자동 재평가 메커니즘 필요.

### [R3] Dispute resolution workflow 필요

- **심각도**: CRITICAL
- Conflict rate 63.5% (임계치 15%). 해소 없이 누적만 진행 → positive feedback loop. Critique 노드에 dispute resolution 단계 추가 권고.

### [R4] disputed -> active 전환 경로 필요

- **심각도**: HIGH
- Resolution 유형 중 hold가 98%. disputed KU의 98%가 방치 상태. 조건부 승격(promote) 또는 근거 보강 후 재판정 경로 필요.

### [R5] 수렴 조건에 conflict_rate 상한 추가 (C6)

- **심각도**: MEDIUM
- Conflict rate 63.5%로 danger인데 현재 수렴 조건(C1-C5)에 conflict_rate 미포함. C6: conflict_rate < 0.15 조건 추가 권고.

### [R6] Early stopping 강화 필요

- **심각도**: MEDIUM
- 후반부 평균 new active KU: 0.4/cycle. 사실상 성장 정지. active KU 정체 N사이클 연속 시 조기 종료 로직 강화 권고.

## 10. 결론

Phase 2 벤치 검증을 통해 Domain-K-Evolver 프레임워크의 기본 루프가 정상 동작함을 확인했다. 10 Cycle 동안 85개 KU를 생성하고, evidence rate 100%, gap resolution 80%를 달성했다.

그러나 **false positive dispute 문제**가 시스템의 핵심 병목으로 드러났다. Disputed KU 54개 중 true conflict는 0개에 불과하며, conflict rate는 63.5%까지 상승했다.

Phase 3에서는 다음을 우선 해결해야 한다:

1. **Integrate 노드 semantic conflict detection 필요** (R1)
1. **Dispute resolution workflow 필요** (R3)
2. **Dispute resolution mechanism 필요** (R2)
2. **disputed -> active 전환 경로 필요** (R4)

