# Phase 0B: Cycle 1 수동 검증 — Context
> Last Updated: 2026-03-03 (GU Bootstrap 명세 반영)
> Status: Planning

## 1. 핵심 파일

### 설계 문서 (Phase 0B 작업 시 참조)
| 파일 | 내용 | 참조 시점 |
|------|------|-----------|
| `docs/design-v2.md` §4 | Metrics 6개 공식 + 건강 임계치 | Critique 작성 시 |
| `docs/design-v2.md` §5 | Critique→Plan 컴파일 6개 규칙 | Plan Modify 시 |
| `docs/design-v2.md` §6 | Entity Resolution 캐노니컬 키 방법 | Integrate 시 |
| `docs/design-v2.md` §7 | Inner Loop 6단계 Deliverable 계약 | 모든 단계 |
| `docs/design-v2.md` §8 | 5대 불변원칙 + 자동 검증 방법 | Critique 시 |
| `docs/design-v2.md` §9 | HITL Gate 설계 | Gate B 적용 시 |
| `docs/design-v2.md` §12 | 다음 단계 — Cycle 1 수동 실행 권장 근거 | Phase 0B 전체 |
| `docs/gu-bootstrap-spec.md` §2 | 동적 GU 발견 규칙 — 트리거 A/B/C + Cycle당 상한(open의 20%) | Integrate 시 |
| `docs/gu-bootstrap-spec.md` §3 | 우선순위 산정 규칙 — risk_level → expected_utility 매핑 | Integrate 시 (신규 GU) |
| `docs/gu-bootstrap-spec.md` §6-B | 동적 발견 체크리스트 — 상한 준수, resolution_criteria, 트리거 분류 | Critique 시 |
| `docs/draft.md` §3~§6 | Inner Loop 각 단계 목표/불변조건/Deliverable 계약 | 모든 단계 |

### Cycle 0 결과물 (입력)
| 파일 | 내용 | 용도 |
|------|------|------|
| `bench/japan-travel/cycle-0/revised-plan-c1.md` | Cycle 1 Collection Plan — 8 Target Gaps, 강화 Source Strategy | Collect 입력 |
| `bench/japan-travel/cycle-0/critique-c0.md` | Critique Report — 6 실패모드, 6 처방(RX-01~06) | Collect/Integrate 시 처방 반영 확인 |
| `bench/japan-travel/cycle-0/kb-patch-c0.md` | KB Patch — 6 adds, 2 updates | 기존 패치 패턴 참고 |
| `bench/japan-travel/cycle-0/evidence-claims-c0.md` | Evidence Claim Set — 7 Claims, EU 번들 | Claim 작성 형식 참고 |

### State 파일 (읽기 + 쓰기)
| 파일 | 내용 | Cycle 0 종료 수치 |
|------|------|-------------------|
| `bench/japan-travel/state/knowledge-units.json` | KU 13개 (active) | Seed 7 + 신규 6 |
| `bench/japan-travel/state/gap-map.json` | GU 28개 (21 open + 7 resolved) | 초기 25 - 해결 7 + 신규 3 |
| `bench/japan-travel/state/metrics.json` | Metrics 스냅샷 | 근거율 1.0, 다중근거율 0.538 |
| `bench/japan-travel/state/domain-skeleton.json` | 카테고리/필드/관계/키규칙 | 7 카테고리, 4 관계 타입 |
| `bench/japan-travel/state/policies.json` | 출처신뢰/TTL/교차검증/충돌해결 | financial min_sources: 2 |

### 템플릿
| 파일 | 용도 |
|------|------|
| `templates/evidence-claim-set.md` | Collect Deliverable 형식 |
| `templates/kb-patch.md` | Integrate Deliverable 형식 |
| `templates/critique-report.md` | Critique Deliverable 형식 |
| `templates/revised-plan.md` | Plan Modify Deliverable 형식 |

### Schema (검증용)
| 파일 | 용도 |
|------|------|
| `schemas/knowledge-unit.json` | KU 추가/수정 시 검증 |
| `schemas/evidence-unit.json` | EU 추가 시 검증 |
| `schemas/gap-unit.json` | GU 상태 변경 시 검증 |
| `schemas/patch-unit.json` | KB Patch 형식 검증 |

---

## 2. 데이터 인터페이스

### 입력 (어디서 읽는가)

```
revised-plan-c1.md     → Collect: Target Gaps, Source Strategy, Queries, Acceptance Tests
state/knowledge-units  → Integrate: 기존 KU와 충돌 비교, Entity Resolution
state/gap-map          → Collect: 타겟 Gap 확인 / Integrate: Gap 상태 업데이트
state/policies         → Collect: 교차검증 규칙 / Integrate: 충돌해결 규칙
state/domain-skeleton  → Integrate: 캐노니컬 키 규칙, 카테고리 구조
state/metrics          → Critique: Cycle 0 수치 (delta 계산 기준)
critique-c0.md         → Plan Modify: 이전 처방 반영 확인
```

### 출력 (어디에 쓰는가)

```
bench/japan-travel/cycle-1/
├── evidence-claims-c1.md   ← Collect 산출물
├── kb-patch-c1.md          ← Integrate 산출물
├── critique-c1.md          ← Critique 산출물
└── revised-plan-c2.md      ← Plan Modify 산출물

bench/japan-travel/state/
├── knowledge-units.json    ← Integrate 후 업데이트
├── gap-map.json            ← Integrate 후 업데이트
├── metrics.json            ← Critique 후 업데이트
├── policies.json           ← Plan Modify 후 업데이트 (필요 시)
└── domain-skeleton.json    ← 변경 없음 (deferred → Phase 3)

bench/japan-travel/state-snapshots/
└── cycle-0-snapshot/       ← 0B.1에서 백업
```

### Deliverable 흐름도

```
                    revised-plan-c1.md
                           │
                    ┌──────▼──────┐
                    │  Collect    │ ← WebSearch/WebFetch
                    │  (0B.2)    │
                    └──────┬──────┘
                           │ evidence-claims-c1.md
                    ┌──────▼──────┐
                    │  Integrate  │ ← State 파일 읽기/쓰기
                    │  (0B.3)    │
                    └──────┬──────┘
                           │ kb-patch-c1.md + State 업데이트
                    ┌──────▼──────┐
                    │  Critique   │ ← Metrics 계산
                    │  (0B.4)    │
                    └──────┬──────┘
                           │ critique-c1.md
                    ┌──────▼──────┐
                    │ Plan Modify │ ← Critique→Plan 규칙
                    │  (0B.5)    │
                    └──────┬──────┘
                           │ revised-plan-c2.md
                           ▼
                    Phase 1 입력
```

---

## 3. 주요 결정사항

| # | 결정 | 대안 | 선택 근거 | 관련 처방 |
|---|------|------|-----------|-----------|
| D-0B-01 | Cycle 1 수동 실행 (LangGraph 전) | 바로 Phase 1 진행 | Conflict-preserving 미검증, design-v2 §12 권장 | - |
| D-0B-02 | 충돌 KU 의도적 탐색 | 자연 발생 대기 | Cycle 0에서 충돌 0건, 능동적 검증 필요 | critique-c0 §2 |
| D-0B-03 | Seed/Plan 단계 스킵 | 전체 Inner Loop 재실행 | Seed Pack은 Cycle 0에서 확정, Plan은 revised-plan-c1로 대체 | design-v2 §12 |
| D-0B-04 | State 스냅샷 백업 후 작업 | 백업 없이 진행 | State 오염 방지, 롤백 가능성 확보 | - |
| D-0B-05 | Financial KU min_eu ≥ 2 enforcement | 기존 min_eu 1 유지 | RX-01 처방 반영, Cycle 0 KU-0013 교차검증 미준수 | RX-01 |
| D-0B-06 | 카테고리 분포 보정 적용 | 기존 utility/risk 기준만 | RX-03 처방 반영, 3개 카테고리 미수집 | RX-03 |
| D-0B-07 | 동적 GU 발견 시 gu-bootstrap-spec §2 규칙 준수 | 자유 GU 생성 | 알고리즘 수준 규약 확립됨, Phase 0B가 첫 실용성 검증 | D-10 |

---

## 4. 컨벤션 체크리스트

### 5대 불변원칙 — Phase 0B 검증 목표

| 원칙 | 자동 검증 방법 | Cycle 0 상태 | Phase 0B 목표 |
|------|---------------|-------------|--------------|
| Gap-driven | Plan.target_gaps ⊆ G.open | ✅ 검증됨 | 재검증 (revised-plan-c1 기반) |
| Claim→KU 착지성 | count(claims) == count(adds + updates + rejected_with_reason) | ✅ 검증됨 | 재검증 |
| Evidence-first | all(len(ku.evidence_links) ≥ 1 for active KU) | ✅ 검증됨 | 재검증 |
| **Conflict-preserving** | **disputed KU 삭제 불가, hold/condition_split/coexist만 허용** | **❌ 미검증 (충돌 0건)** | **✅ 반드시 검증** |
| Prescription-compiled | all(rx.id in revised_plan.traceability) | ✅ 검증됨 | 재검증 |

### Metrics 건강 임계치

| 지표 | Cycle 0 종료 | 건강 기준 | Phase 0B 예상 |
|------|-------------|-----------|-------------|
| 근거율 | 1.0 | ≥ 0.95 | 유지 (1.0) |
| 다중근거율 | 0.538 | ≥ 0.50 | ↑ (≥ 0.60) |
| 충돌률 | 0.0 | ≤ 0.05 | ↑ (> 0, 의도적) |
| 평균 confidence | 0.888 | ≥ 0.85 | 유지 |
| 신선도 리스크 | 0 | 0 | 유지 |

### RX 처방 반영 체크리스트 (Cycle 0 → Cycle 1)

| 처방 ID | 내용 | 반영 위치 | 확인 |
|---------|------|-----------|------|
| RX-01 | KU-0013 신칸센 가격 교차확인 (min_eu ≥ 2) | Collect: Source Strategy | [ ] |
| RX-02 | airport-transfer 엔티티 분리 → deferred (Cycle 3+) | N/A (보류) | [ ] |
| RX-03 | accommodation/dining/attraction 각 1+ Gap 선정 | Collect: Target Gaps | [ ] |
| RX-04 | is_a 관계 추가 → deferred (Outer Loop) | N/A (보류) | [ ] |
| RX-05 | GU-0019 SIM 가격 다중출처 | Collect: Target Gaps + Strategy | [ ] |
| RX-06 | GU-0026 면세 신제도 우선순위 상향 | Collect: Target Gaps | [ ] |

### 동적 GU 발견 규칙 (gu-bootstrap-spec §2 — Phase 0B 적용)

| 체크 | 기준 | 참조 |
|------|------|------|
| [ ] 신규 GU 수 ≤ 기존 open GU의 20% | 현재 open 21개 → 상한 4개 (safety 예외) | §2 상한 |
| [ ] 신규 GU에 resolution_criteria 명시 | 필수 | §6-B |
| [ ] 각 신규 GU의 트리거 분류 (A/B/C) | 명확히 기록 | §2 트리거 |
| [ ] 신규 GU의 expected_utility + risk_level 규칙 준수 | §3 매핑 테이블 적용 | §3 |
| [ ] created_at = Cycle 1 날짜 | 타임스탬프 정확성 | §6-B |

### 인코딩
- JSON read/write: `encoding='utf-8'`
- MD 파일: UTF-8 (BOM 없음)
- entity_key: `{domain}:{category}:{slug}` (lowercase + hyphen)
- ID 패턴: KU-NNNN, EU-NNNN, GU-NNNN, PU-NNNN (기존 번호 이어서)
