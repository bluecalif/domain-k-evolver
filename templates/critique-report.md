# Critique Report — Cycle {N}

> **단계**: (R) Critique | **도메인**: {DOMAIN_NAME}
> **생성일**: {DATE}
> **입력**: KB Patch Cycle {N} + 전체 State

---

## 1. Metrics Delta

### 현재 State 수치

| 지표 | Cycle {N-1} 종료 | Cycle {N} 종료 | Delta | 방향 |
|------|------------------|----------------|-------|------|
| KU 수 (active) | {prev} | {curr} | {delta} | {↑/↓/→} |
| 근거율 (EU≥1인 KU / 전체 KU) | {prev} | {curr} | {delta} | |
| 다중근거율 (EU≥2인 KU / 전체 KU) | {prev} | {curr} | {delta} | |
| Gap 수 (open) | {prev} | {curr} | {delta} | |
| Gap 해소율 (resolved / 초기 open) | {prev} | {curr} | {delta} | |
| 충돌 수 (disputed KU) | {prev} | {curr} | {delta} | |
| 평균 confidence | {prev} | {curr} | {delta} | |
| 신선도 리스크 (TTL 초과 KU 수) | {prev} | {curr} | {delta} | |

### Metrics 계산 공식

```
근거율 = count(KU where len(evidence_links) >= 1 and status == 'active') / count(KU where status == 'active')
다중근거율 = count(KU where len(evidence_links) >= 2 and status == 'active') / count(KU where status == 'active')
Gap해소율 = count(GU where status == 'resolved' in this cycle) / count(GU where status == 'open' at cycle start)
충돌률 = count(KU where status == 'disputed') / count(KU where status in ['active', 'disputed'])
평균confidence = mean(confidence for KU where status == 'active')
신선도리스크 = count(KU where observed_at + ttl_days < today)
```

---

## 2. Failure Modes 탐지

### Epistemic (근거 빈약/출처 편향/독립성 부족)
- **발견**: {있으면 기술}
- **심각도**: {high/medium/low}
- **영향 KU**: [{ku_ids}]

### Temporal (신선도 취약/TTL 설계 부적절)
- **발견**: {기술}
- **심각도**: {level}

### Structural (스키마가 표현 못함)
- **발견**: {기술}
- **심각도**: {level}

### Consistency (충돌 다발/해결 불가)
- **발견**: {기술}
- **심각도**: {level}

### Planning (Gap 우선순위 비효율/검색전략 부정확)
- **발견**: {기술}
- **심각도**: {level}

### Integration (정규화 오류/엔티티 해상도 문제)
- **발견**: {기술}
- **심각도**: {level}

---

## 2.5 Structural Deficit Analysis (축 커버리지)

> Axis Coverage Matrix 기반 구조적 결손 분석. Phase 0C에서 도입.

### Axis Coverage Summary

| 축 | deficit_ratio | 결손 값 | 비고 |
|----|---------------|---------|------|
| category | {ratio} | {values} | |
| geography | {ratio} | {values} | |
| condition | {ratio} | {values} | |
| risk | {ratio} | {values} | |

### Jump Mode 판정

| Trigger | 충족 여부 | 근거 |
|---------|-----------|------|
| Axis Under-Coverage | {yes/no} | {detail} |
| Spillover | {yes/no} | {detail} |
| High-Risk Blindspot | {yes/no} | {detail} |
| Prescription | {yes/no} | {detail} |
| Domain Shift | {yes/no} | {detail} |

**판정**: {Base Mode / Jump Mode} | **jump_cap**: {N/A 또는 수치}

---

## 3. Root Cause Hypotheses

| 실패모드 | 가설 | 근거 |
|----------|------|------|
| {mode} | {hypothesis} | {evidence} |

---

## 4. Prescriptions (→ 다음 Plan 반영)

| ID | 실패모드 | 처방 | 우선순위 | 반영 대상 |
|----|----------|------|----------|-----------|
| RX-01 | {mode} | {prescription} | {high/medium/low} | Plan / Policy / Schema |

---

## 5. Remodeling Triggers (Outer Loop)

| 조건 | 충족 여부 | 권고 |
|------|-----------|------|
| 스키마 확장 필요 | {yes/no} | {내용} |
| 정책 수정 필요 | {yes/no} | {내용} |
| 평가 루브릭 개편 | {yes/no} | {내용} |
