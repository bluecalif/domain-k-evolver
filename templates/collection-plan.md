# Collection Plan — Cycle {N}

> **단계**: (P) Plan | **도메인**: {DOMAIN_NAME}
> **생성일**: {DATE}
> **기반**: Gap Map 상태 Cycle {N-1} 종료 시점

---

## 1. Target Gaps (우선순위순)

| 순위 | GU ID | 유형 | 대상 | 기대효용 | 리스크 | 선정 이유 |
|------|-------|------|------|----------|--------|-----------|
| 1 | {gu_id} | {type} | {entity:field} | {utility} | {risk} | {reason} |

---

## 2. Source Strategy

### 출처군 우선순위

| 순위 | 출처군 | 대상 Gap | 기대 신뢰도 | 접근 방법 |
|------|--------|----------|-------------|-----------|
| 1 | {source_group} | {gu_ids} | {credibility} | {method} |

### 교차확인 규칙 (이번 Cycle 적용)
- {규칙 1}
- {규칙 2}

---

## 3. Query/Discovery Strategy

| GU ID | 검색 쿼리 / 탐색 경로 | 기대 출처 | 언어 |
|-------|------------------------|-----------|------|
| {gu_id} | {query} | {expected_source} | {lang} |

---

## 4. Acceptance Tests

| GU ID | 해결 조건 | 최소 EU 수 | 독립성 요건 | 신선도 요건 |
|-------|-----------|------------|-------------|-------------|
| {gu_id} | {criteria} | {min_eu} | {independence} | {freshness} |

---

## 5. Budget & Stop Rules

- **수집 상한**: {max_queries}회 검색
- **시간 상한**: {max_time}
- **중복 상한**: 동일 출처 {max_same_source}회 초과 시 다른 출처 탐색
- **품질 미달 중단**: {min_quality_threshold} 미만 EU {count}개 연속 시 해당 Gap 보류
- **조기 종료**: 모든 Target Gap이 resolved/deferred 시 종료
