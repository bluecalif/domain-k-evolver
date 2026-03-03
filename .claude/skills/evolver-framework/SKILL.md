---
name: evolver-framework
description: Domain-K-Evolver 5대 불변원칙 + Metrics 임계치 + Schema 정합성 가드레일. 코드 작성/리뷰 시 자동 검증.
---

# Evolver Framework Guardrail

## Purpose

Domain-K-Evolver의 핵심 제약조건을 강제하는 guardrail skill.
모든 구현 코드가 5대 불변원칙을 위반하지 않도록 보장.

## When to Use This Skill

- LangGraph 노드 구현 시 (plan, collect, integrate, critique, plan_modify)
- KU/EU/GU/PU 생성·수정 코드 작성 시
- Metrics 계산·검증 로직 작성 시
- State 읽기/쓰기 코드 작성 시
- 코드 리뷰 또는 PR 검토 시

---

## 5대 불변원칙 체크리스트

### 1. Gap-driven
- Plan 노드는 반드시 Gap Map(open GU)을 입력으로 사용
- Gap 없이 수집 계획을 생성하면 **위반**

### 2. Claim→KU 착지성
- collect_node가 수집한 모든 Claim은 integrate_node에서 KU로 변환
- Claim이 KU로 변환되지 않고 버려지면 **위반** (명시적 reject 사유 필요)

### 3. Evidence-first
- KU 생성 시 evidence_links가 비어있으면 status='unverified' 강제
- evidence_links ≥ 1이어야 status='active' 가능

### 4. Conflict-preserving
- 동일 entity_key에 대해 모순되는 KU 발견 시 status='disputed' 설정
- 충돌을 삭제/무시하면 **위반** — 반드시 구조적으로 보존

### 5. Prescription-compiled
- critique_node의 처방(prescription)은 plan_modify_node에서 추적 가능하게 반영
- 처방이 무시되면 **위반**

---

## Metrics 임계치

```python
THRESHOLDS = {
    'evidence_rate':       {'warn': 0.6, 'fail': 0.4},
    'multi_evidence_rate': {'warn': 0.3, 'fail': 0.1},
    'gap_resolution_rate': {'warn': 0.2, 'fail': 0.0},
    'conflict_rate':       {'warn': 0.15, 'fail': 0.3},  # 높을수록 나쁨
    'avg_confidence':      {'warn': 0.5, 'fail': 0.3},
}
```

- **warn**: 경고 출력, 계속 진행
- **fail**: 에러 출력, 리뷰 필요

---

## Schema 정합성 규칙

| 객체 | ID 패턴 | entity_key 형식 |
|------|---------|-----------------|
| KU | `KU-NNNN` | `{domain}:{category}:{slug}` |
| EU | `EU-NNNN` | — |
| GU | `GU-NNNN` | `{domain}:{category}:{slug}` |
| PU | `PU-NNNN` | — |

- `schemas/` 디렉토리의 JSON Schema 참조
- entity_key 슬러그는 lowercase + hyphen only
- KU.evidence_links의 EU ID는 실제 존재하는 EU를 참조해야 함

---

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Gap 없이 Plan 생성 | 불변원칙 1 위반 | Gap Map 기반으로만 계획 |
| KU에 EU 없이 active 설정 | 불변원칙 3 위반 | unverified로 생성 후 EU 연결 시 active |
| 충돌 KU 삭제 | 불변원칙 4 위반 | disputed 상태로 보존 |
| Critique 처방 누락 | 불변원칙 5 위반 | PU에 prescription 매핑 기록 |
| entity_key 대소문자 혼용 | 데이터 불일치 | lowercase + hyphen only |

---

## Related

- `docs/design-v2.md` §3-5: Schema, Metrics, Critique→Plan 규칙
- `schemas/`: JSON Schema 원본
- `langgraph-dev` skill: 노드/엣지 구현 가이드
