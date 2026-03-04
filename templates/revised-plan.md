# Revised Plan — Cycle {N+1}

> **단계**: (PM) Plan Modify | **도메인**: {DOMAIN_NAME}
> **생성일**: {DATE}
> **입력**: Critique Report Cycle {N}

---

## 1. Critique→Plan 추적성 (Traceability)

| 처방 ID | 실패모드 | 처방 내용 | 반영 방법 | 반영 위치 |
|---------|----------|-----------|-----------|-----------|
| RX-{NN} | {mode} | {prescription} | {how_applied} | {Plan섹션/Policy/Schema} |

---

## 2. 변경된 Gap 우선순위

| 순위 | GU ID | 이전 순위 | 변경 사유 (처방 ID) |
|------|-------|-----------|---------------------|
| 1 | {gu_id} | {prev_rank 또는 "신규"} | {RX-NN} |

---

## 3. 변경된 Source Strategy

| 변경 항목 | 이전 | 이후 | 사유 (처방 ID) |
|-----------|------|------|----------------|
| {item} | {before} | {after} | {RX-NN} |

---

## 4. 변경된 검증 기준

| GU ID | 이전 기준 | 이후 기준 | 사유 (처방 ID) |
|-------|-----------|-----------|----------------|
| {gu_id} | {before} | {after} | {RX-NN} |

---

## 5. Policy Updates

| 정책 항목 | 이전 값 | 이후 값 | 사유 (처방 ID) |
|-----------|---------|---------|----------------|
| {policy_item} | {before} | {after} | {RX-NN} |

---

## 6. Revised Collection Plan (Cycle {N+1})

> 아래는 Critique를 반영한 Cycle {N+1}의 완성된 Collection Plan.
> Collection Plan 템플릿 형식을 따른다.

### Target Gaps

| 순위 | GU ID | 유형 | 대상 | 기대효용 | 리스크 | 선정 이유 |
|------|-------|------|------|----------|--------|-----------|
| 1 | {gu_id} | {type} | {target} | {utility} | {risk} | {reason} |

### Source Strategy
{기술}

### Query/Discovery Strategy

| GU ID | 검색 쿼리 | 기대 출처 | 언어 |
|-------|-----------|-----------|------|
| {gu_id} | {query} | {source} | {lang} |

### Acceptance Tests

| GU ID | 해결 조건 | 최소 EU 수 | 독립성 | 신선도 |
|-------|-----------|------------|--------|--------|
| {gu_id} | {criteria} | {min} | {req} | {req} |

### Expansion Mode & Budget

| 항목 | 값 |
|------|----|
| Expansion Mode | {Base / Jump} |
| explore budget | {N} GU (신규 축 영역) |
| exploit budget | {M} GU (기존 open 해결) |
| jump_cap (Jump 시) | {cap 또는 N/A} |
| trigger (Jump 시) | {trigger 목록 또는 N/A} |

### Budget & Stop Rules
- {규칙들}

---

## 7. Critique→Plan 컴파일 규칙 (메타)

> Cycle 0에서 도출된 일반화 가능한 변환 규칙.

| 실패모드 | → Plan 변경 유형 | 규칙 |
|----------|------------------|------|
| Epistemic | {변경} | {규칙} |
| Temporal | {변경} | {규칙} |
| Structural | {변경} | {규칙} |
| Consistency | {변경} | {규칙} |
| Planning | {변경} | {규칙} |
| Integration | {변경} | {규칙} |
