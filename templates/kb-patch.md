# KB Patch — Cycle {N}

> **단계**: (I) Integration | **도메인**: {DOMAIN_NAME}
> **생성일**: {DATE}
> **입력**: Evidence Claim Set Cycle {N}

---

## 패치 요약

| 항목 | 수량 |
|------|------|
| 신규 KU 추가 | {count} |
| 기존 KU 수정 | {count} |
| KU 폐기 | {count} |
| 충돌 처리 | {count}건 |
| Gap 해결 | {count} |
| 신규 Gap 발견 | {count} |

---

## 1. Adds (신규 KU)

### KU-{NNNN}
- **entity_key**: {key}
- **field**: {field}
- **value**: {value}
- **conditions**: {conditions}
- **confidence**: {0.0–1.0}
- **evidence**: [{EU IDs}]
- **출처 Claim**: C{N}-{NN}

*(반복)*

---

## 2. Updates (기존 KU 수정)

### KU-{NNNN} 수정
- **변경 필드**: {field} — {old_value} → {new_value}
- **사유**: {reason}
- **추가 근거**: [{EU IDs}]

*(반복)*

---

## 3. Deprecates (KU 폐기)

| KU ID | 사유 | 대체 KU |
|-------|------|---------|
| {ku_id} | {reason} | {replacement_ku_id 또는 "없음"} |

---

## 4. Conflict Decisions

| 관련 KU | 결정 | 근거 |
|---------|------|------|
| {ku_ids} | {adopt_newest/condition_split/hold/request_more_evidence} | {rationale} |

---

## 5. Gap Map Update

### 해결된 Gap
| GU ID | 해결 KU | 비고 |
|-------|---------|------|
| {gu_id} | {ku_id} | {note} |

### 신규 Gap
| GU ID | 유형 | 대상 | 기대효용 | 발견 경위 |
|-------|------|------|----------|-----------|
| {gu_id} | {type} | {target} | {utility} | {how_discovered} |

---

## 6. Entity Resolution 기록

| Claim 엔티티 | 매칭 결과 | 캐노니컬 키 | 방법 |
|--------------|-----------|-------------|------|
| {claim_entity} | {new/merged/matched} | {canonical_key} | {method} |
