# Phase 3 심층 분석 보고서

> 생성 시각: 2026-03-06 22:30
> 대상: 10 Cycles (Cycle 2~11)
> 벤치 도메인: japan-travel
> Phase 3 개선사항: Semantic Conflict Detection + Dispute Resolution + C6 수렴조건

## 1. Executive Summary

| 항목 | 값 |
|------|-----|
| 총 Cycle | 10 |
| KU (active/disputed/total) | 77/0/77 |
| Evidence Rate | 100.0% |
| Multi-Evidence Rate | 89.6% |
| Conflict Rate | 0.0% |
| Gap Resolution | 84.0% |
| Health Grade | **B** |
| 불변원칙 위반 | 0 |

### Phase 2 대비 개선

| 지표 | Phase 2 | Phase 3 | 변화 |
|------|---------|---------|------|
| Active KU | 31 | 77 | **+148%** |
| Disputed KU | 54 | 0 | **-100%** |
| conflict_rate | 63.5% | 0.0% | **-63.5pp** |
| Active 성장률 | 0.3/cycle | 4.3/cycle | **14.3x** |
| Multi-Evidence | 32.3% | 89.6% | **+57.3pp** |
| Entities | 39 | 36 | -3 (FP 제거) |
| Categories | 8/8 | 8/8 | 유지 |

## 2. Cycle-by-Cycle Trajectory

| Cycle | KU Total | Active | Disputed | GU Open | Resolved | Conflict% | LLM | Search | Fetch | Mode |
|------:|---------:|-------:|---------:|--------:|---------:|----------:|----:|-------:|------:|------|
| 2 | 34 | 34 | 0 | 28 | 24 | 14.7% | 29 | 18 | 12 | jump |
| 3 | 40 | 40 | 0 | 22 | 30 | 2.5% | 21 | 18 | 12 | jump |
| 4 | 45 | 45 | 0 | 17 | 35 | 4.4% | 21 | 15 | 10 | jump |
| 5 | 50 | 50 | 0 | 22 | 40 | 4.0% | 22 | 15 | 10 | jump |
| 6 | 55 | 55 | 0 | 17 | 45 | 3.6% | 37 | 15 | 10 | jump |
| 7 | 63 | 63 | 0 | 19 | 54 | 4.8% | 35 | 27 | 18 | jump |
| 8 | 66 | 66 | 0 | 16 | 57 | 1.5% | 19 | 9 | 6 | jump |
| 9 | 69 | 69 | 0 | 13 | 60 | 2.9% | 12 | 9 | 6 | jump |
| 10 | 74 | 74 | 0 | 16 | 65 | 2.7% | 30 | 15 | 10 | jump |
| 11 | 77 | 77 | 0 | 13 | 68 | 0.0% | 12 | 9 | 6 | jump |

## 3. Trend Analysis

### 성장률 비교 (전반부 vs 후반부)

| Metric | 1st Half (C2~6) | 2nd Half (C7~11) | Ratio |
|--------|----------------:|-----------------:|------:|
| ku_total | +21 | +14 | 0.67x |
| ku_active | +21 | +14 | 0.67x |
| ku_disputed | 0 | 0 | — |
| gu_resolved | +21 | +14 | 0.67x |
| conflict_rate | -11.1pp | -4.8pp | — |

### Phase 2 대비 변곡점 해소

- Phase 2: active KU Cycle 5에서 정체 (31에서 고착)
- Phase 3: **10 Cycle 연속 성장** (34→77), 정체 없음
- conflict_rate: Cycle 2에서 14.7% → 이후 안정적 5% 이하

## 4. Knowledge Unit 분석

- 총 KU: 77
- Active: 77 (100%)
- Disputed: 0 (0%)

- 카테고리: 8개 (accommodation, attraction, connectivity, dining, pass-ticket, payment, regulation, transport)
- Entity: 36개

### Evidence 분포

| 항목 | 값 |
|------|-----|
| 평균 Evidence/KU | 3.7 |
| 최소 | 1 |
| 최대 | 9 |
| Multi-evidence (≥2 EU) | 69/77 (89.6%) |

## 5. Disputed KU 분석

| 항목 | Phase 2 | Phase 3 |
|------|---------|---------|
| Total Disputed | 54 | 0 |
| True Conflicts | 0 | 0 |
| False Positives | 54 | 0 |
| FP Rate | 100% | 0% |

### 해소 메커니즘

Phase 3에서 도입된 3단계 전략으로 disputed KU 문제를 근본 해결:

1. **Stage A — Semantic Conflict Detection (D-41)**: LLM이 실제 의미적 충돌인지 판정. update/equivalent → 충돌 아님으로 분류. Phase 2의 FP 100% 문제 제거.
2. **Stage B — Dispute Resolution (D-42)**: Evidence-weighted resolution. evidence ≥ 2×disputes이면 자동 해소. LLM 중재 fallback.
3. **Stage C — C6 수렴조건 (D-43)**: conflict_rate < 0.15 수렴 조건 추가. Plateau 시 stuck vs converged 분류.

## 6. Gap Map 분석

| 항목 | Phase 2 | Phase 3 |
|------|---------|---------|
| 총 Gap | 94 | 81 |
| Resolved | 75 | 68 |
| Open | 19 | 13 |
| Resolution Rate | 79.8% | 84.0% |

## 7. API 비용 효율성

| 항목 | Phase 2 | Phase 3 | 변화 |
|------|---------|---------|------|
| LLM calls | 69 | 238 | +245% |
| LLM tokens | 196,559 | 222,961 | +13.4% |
| Search calls | 177 | 150 | -15.3% |
| Fetch calls | 118 | 100 | -15.3% |
| Tokens/KU (total) | 2,312 | 2,896 | +25.3% |
| Tokens/KU (active) | 6,341 | 2,896 | **-54.3%** |
| Active ratio | 36.5% | 100% | **+63.5pp** |
| Waste ratio | 63.5% | 0% | **-63.5pp** |

### 비용 효율성 분석

- LLM 호출 수는 238로 3.4배 증가했으나, 이는 conflict detection의 semantic 판정 때문
- **토큰 총량은 13.4%만 증가** (196K→223K): 호출당 토큰이 적음 (짧은 conflict check 프롬프트)
- **Active KU당 토큰은 54.3% 감소**: 생산 효율이 크게 개선
- Phase 2의 waste ratio 63.5% → 0%: 모든 KU가 active로 전환되어 낭비 제거

## 8. Health Score

| Metric | Phase 2 | Phase 3 | Grade |
|--------|------:|------:|-------|
| evidence_rate | 100.0% | 100.0% | HEALTHY |
| multi_evidence_rate | 32.3% | 89.6% | HEALTHY |
| conflict_rate | 63.5% | 0.0% | HEALTHY |
| avg_confidence | 87.4% | 80.0% | WARNING |
| staleness_risk | 4 | 48 | DANGER |

**Overall Grade: B** (Phase 2: D → Phase 3: B)

- avg_confidence 87.4%→80.0% 하락: dispute resolution에서 resolved dispute의 confidence 재계산 영향
- staleness_risk 4→48: 10 Cycle 동안 77개 KU 생성으로 TTL 만료 대상 증가 (Cycle 순서상 자연 현상)

## 9. Phase 3 기술 결정 요약

| ID | 결정 | 근거 |
|----|------|------|
| D-40 | Phase 3 = Cycle Quality Remodeling | Phase 2 분석 결과 FP가 유일 병목 |
| D-41 | hybrid conflict detection (rule + LLM) | 동일값 skip, 값차이 LLM semantic |
| D-42 | Evidence-weighted resolution | evidence ≥ 2×disputes → 자동 resolve |
| D-43 | C6 conflict_rate threshold = 0.15 | 수렴 조건에 충돌률 상한 추가 |

## 10. 잔여 과제

1. **avg_confidence 개선**: 80.0%로 C4 수렴 조건(≥85%) 미달. Confidence 갱신 로직 검토 필요.
2. **staleness_risk 관리**: TTL 만료 대상 48개. Temporal 실패모드 처리 강화 또는 TTL 정책 재검토.
3. **후반부 성장률 둔화**: 1H +21 vs 2H +14. Gap 고갈에 의한 자연 현상이지만, Outer Loop 확장 시 고려.

## 11. 결론

Phase 3에서 Domain-K-Evolver의 Cycle 품질을 근본적으로 개선했다.

**핵심 성과:**
- False Positive dispute 문제를 완전 해결 (54개 → 0개)
- Active KU 성장률 14.3배 개선 (0.3 → 4.3/cycle)
- 생산 효율 2.2배 개선 (Active KU당 토큰 54.3% 감소)
- Health Grade D → B 달성

**구조적 개선:**
- Semantic conflict detection: 의미적 동치 판정으로 FP 제거
- Dispute resolution: Evidence-weighted 자동 해소 경로
- 수렴 조건 C6: conflict_rate 상한으로 stuck 상태 방지

Phase 2에서 발견된 6개 권고(R1~R6)를 모두 해결하여, 프레임워크가 자기확장 루프를 안정적으로 수행할 수 있음을 10 Cycle 실증으로 확인했다.
