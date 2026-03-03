# Seed Pack v{VERSION}

> **단계**: (S) Seed | **도메인**: {DOMAIN_NAME}
> **생성일**: {DATE}

## 1. 도메인 Scope Boundary

### 포함 범위
- {범위 항목 1}
- {범위 항목 2}

### 제외 범위
- {제외 항목 1}
- {제외 항목 2}

### Scope 경계 판정 규칙
- {규칙: 예 — "국내 이동수단은 포함, 출발국 → 일본 항공편은 제외"}

---

## 2. Domain Skeleton v0

### 엔티티 유형 (Categories)

| Category | 설명 | 슬러그 예시 |
|----------|------|-------------|
| {category} | {설명} | {slug-example} |

### 주요 필드 정의

| 필드명 | 타입 | 적용 카테고리 | 설명 |
|--------|------|---------------|------|
| {field} | {type} | {categories} | {desc} |

### 관계 정의

| 관계 | 소스 → 타겟 | 설명 |
|------|-------------|------|
| {relation} | {source} → {target} | {desc} |

### 캐노니컬 키 규칙
- 형식: `{domain}:{category}:{slug}`
- slug 규칙: 영문 소문자, 하이픈 구분, 공식 명칭 기반

---

## 3. Seed Knowledge Units

> 최소 5개 이상. 각 KU는 최소 1개 EU를 포함해야 함.

### KU-0001: {entity_key} — {field}
- **값**: {value}
- **조건**: {conditions 또는 "무조건"}
- **신뢰도**: {0.0–1.0} ({근거})
- **출처**: EU-0001

*(반복)*

---

## 4. Seed Evidence Units

### EU-0001
- **출처**: {URL 또는 문서}
- **유형**: {official|public|platform|personal}
- **수집일**: {date}
- **스니펫**: "{원문 발췌}"

*(반복)*

---

## 5. Gap Map v0

> 최소 20개 이상의 초기 Gap. missing/uncertain/conflicting/stale 유형 혼합.
> **생성 방법**: [`docs/gu-bootstrap-spec.md`](../docs/gu-bootstrap-spec.md) §1 알고리즘 참조
> (Category × Field 매트릭스 → gap_type 판정 → 엔티티 확장 → 우선순위 산정 → Scope 필터)

### 빠른 체크
- [ ] 총 GU >= 20
- [ ] critical/high GU >= 3
- [ ] 모든 카테고리에 최소 1개 GU 존재
- [ ] 모든 GU에 `resolution_criteria` 명시
- [ ] `scope_boundary.excludes` 해당 GU 없음

| GU ID | 유형 | 대상 (entity_key:field) | 기대효용 | 리스크 | 해결기준 |
|-------|------|-------------------------|----------|--------|----------|
| GU-0001 | missing | {key}:{field} | {critical/high/medium/low} | {유형} | {기준} |

---

## 6. Policy Priors v0

### 출처 유형별 신뢰도

| 출처 유형 | 기본 신뢰도 | 비고 |
|-----------|-------------|------|
| official | 0.95 | 공식 사이트, 정부 기관 |
| public | 0.80 | 위키, 공공 데이터 |
| platform | 0.65 | 리뷰 사이트, 블로그 |
| personal | 0.40 | 개인 경험담 |

### TTL 기본값

| 정보 유형 | TTL (일) | 근거 |
|-----------|----------|------|
| {type} | {days} | {reason} |

### 교차검증 규칙
- 안전/정책/금전 관련: 독립 출처 2개 이상 필수
- 일반 정보: 1개 출처 + 신뢰도 0.7 이상이면 수용
- 충돌 발생 시: disputed 상태로 보존, 추가 수집 요청

### 충돌해결 규칙
- 공식 > 공공 > 플랫폼 > 개인 (출처 우선순위)
- 최신 정보 우선 (동일 출처 유형 내)
- 조건 차이로 설명 가능하면 condition_split
