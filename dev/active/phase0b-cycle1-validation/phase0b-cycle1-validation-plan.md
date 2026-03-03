# Phase 0B: Cycle 1 수동 검증
> Last Updated: 2026-03-03
> Status: ✅ Complete

## 1. Summary (개요)

**목적**: Cycle 0에서 미검증된 **Conflict-preserving 원칙**을 포함한 5대 불변원칙 전체 검증 + Revised Plan C1 실행을 통한 Inner Loop 2회차 완주.

**근거**: design-v2.md §12 — "Revised Plan C1 기반으로 한 번 더 수동 실행하여 Conflict-preserving 원칙 검증" 권장.

**범위**: japan-travel 벤치에서 Revised Plan C1(8개 Target Gap) 기반 수동 Inner Loop 실행.
- Collect → Integrate → Critique → Plan Modify (4단계, Seed는 Cycle 0에서 완료)
- State 파일 업데이트 (knowledge-units, gap-map, metrics)
- Cycle 1 Deliverable 4종 저장
- **GU 생성/확장**: `docs/gu-bootstrap-spec.md` §2 동적 발견 규칙 적용 (트리거 A/B/C + 상한 준수)

**기대 결과물**:
- `bench/japan-travel/cycle-1/` — 4개 Deliverable (evidence-claims-c1, kb-patch-c1, critique-c1, revised-plan-c2)
- `bench/japan-travel/state/` — 업데이트된 State 파일 5종
- Conflict-preserving 원칙 검증 보고 (최소 1건 충돌 시나리오)
- Cycle 0 → Cycle 1 Metrics delta 분석

---

## 2. Current State (현재 상태)

### Cycle 0 완료 상태
| 항목 | 값 | 비고 |
|------|-----|------|
| KU (active) | 13 | Seed 7 + Cycle 0 추가 6 |
| EU (total) | 18 | Seed 6 + Cycle 0 추가 12 |
| GU (open) | 21 | 초기 25 - 해결 7 + 신규 3 |
| GU (resolved) | 7 | |
| 근거율 | 1.0 | 건강 |
| 다중근거율 | 0.538 | 건강 |
| 충돌률 | 0.0 | 건강 (단, 미검증) |
| 평균 confidence | 0.888 | 건강 |
| 신선도 리스크 | 0 | 건강 |

### Cycle 1 완료 상태
| 항목 | 값 | 비고 |
|------|-----|------|
| KU (total) | 21 | active 19 + disputed 2 |
| EU (total) | 33 | +15 from Cycle 1 |
| GU (open) | 16 | 8 resolved + 3 new in Cycle 1 |
| GU (resolved) | 15 | 누적 |
| 근거율 | 1.0 | 건강 ✅ |
| 다중근거율 | 0.714 | 건강 ✅ |
| 충돌률 | 0.095 | 주의 ⚠️ (의도적) |
| 평균 confidence | 0.876 | 건강 ✅ |
| 신선도 리스크 | 0 | 건강 ✅ |

### 검증 완료 항목
- ✅ **Conflict-preserving**: KU-0007(condition_split), KU-0011(hold) — 첫 실전 검증 성공
- ✅ **Financial 교차검증 enforcement**: financial Gap 3개 모두 독립 2출처 확보
- ✅ **카테고리 커버리지**: 7개 카테고리 커버 (accommodation, dining, attraction 포함)

### 입력 자산
- `bench/japan-travel/cycle-0/revised-plan-c1.md` — 8개 Target Gap, 강화된 Source Strategy
- `bench/japan-travel/state/` — Cycle 0 결과 State 5종
- `templates/` — 6대 Deliverable 템플릿

---

## 3. Target State (목표 상태)

Phase 0B 완료 시:
- Cycle 1 Inner Loop 완주 (Collect → Integrate → Critique → Plan Modify)
- **최소 1건 disputed KU 존재** → Conflict-preserving 원칙 실증
- 5대 불변원칙 **전원 검증 완료** (Cycle 0에서 미검증 항목 해소)
- Financial KU의 교차검증 enforcement 실증 (min_eu ≥ 2)
- 카테고리 커버리지 편향 해소 (accommodation, dining, attraction 최소 각 1 Gap 해결)
- Metrics 개선: Gap 해소율 ↑, 다중근거율 ↑
- `bench/japan-travel/cycle-1/` 디렉토리에 Deliverable 4종 저장
- `revised-plan-c2.md` 생성 → LangGraph 자동화(Phase 1) 입력으로 활용 가능

### 정량 목표

| 지표 | Cycle 0 종료 | Cycle 1 목표 | 근거 |
|------|-------------|-------------|------|
| Gap 해소율 (누적) | 7/28 = 0.25 | ≥ 12/28 = 0.43 | 8개 Target 중 최소 5개 해결 |
| 다중근거율 | 0.538 | ≥ 0.60 | 기존 단일출처 KU 보강 + 신규 KU |
| 충돌률 | 0.0 | > 0 (의도적) | Conflict-preserving 검증 필수 |
| 카테고리 커버리지 | 3/7 | ≥ 5/7 | accommodation, dining 추가 |

---

## 4. Implementation Stages

### Stage A: 준비 (Preparation)
- Cycle 1 디렉토리 생성
- Cycle 0 State 스냅샷 (백업)
- Revised Plan C1 최종 확인 + 충돌 시나리오 계획

### Stage B: 수집 + 통합 (Collect → Integrate)
- revised-plan-c1 기반 8개 Gap 정보 수집
- Evidence Claim Set 작성 (EU 포함)
- KB Patch 적용 + State 업데이트
- **충돌 KU 의도적 생성**: 기존 KU와 상이한 정보 수집 시 disputed 처리
- **동적 GU 발견**: gu-bootstrap-spec §2 적용 — 트리거 A(인접 Gap)/B(Epistemic)/C(새 엔티티) + 상한(open의 20% = 최대 4개)

### Stage C: 비평 + 계획수정 (Critique → Plan Modify)
- Metrics delta 계산 (Cycle 0 vs Cycle 1)
- 5대 불변원칙 전체 검증 (Conflict-preserving 포함)
- **동적 GU 발견 체크**: 신규 GU 상한 준수 + resolution_criteria 명시 + 트리거 분류 (gu-bootstrap-spec §6-B)
- Critique 처방 → Revised Plan C2 컴파일
- design-v2.md 피드백 반영 (필요 시)

---

## 5. Task Breakdown

| Task | 내용 | Size | 의존성 | Stage |
|------|------|------|--------|-------|
| 0B.1 | Cycle 1 디렉토리 준비 + State 스냅샷 | S | - | A |
| 0B.2 | Collect — 8개 Gap 수집, Evidence Claim Set 작성 | L | 0B.1 | B |
| 0B.3 | Integrate — Claims → KB Patch 적용, State 업데이트 | L | 0B.2 | B |
| 0B.4 | Critique — Metrics delta, 5대 불변원칙 검증 | M | 0B.3 | C |
| 0B.5 | Plan Modify — Revised Plan C2 작성 | M | 0B.4 | C |

### 총계: 5개 (S:1, M:2, L:2, XL:0)

---

## 6. Risks & Mitigation

| 리스크 | 심각도 | 완화 전략 |
|--------|--------|-----------|
| 충돌 KU 자연 발생 안함 | Medium | 의도적으로 상충 정보 포함 영역(예: SIM 가격, 신칸센 소요시간) 집중 수집. 최소 1건 미발생 시 시나리오 기반 검증. |
| WebSearch 결과 품질 불안정 | Medium | 재시도 + 공식 사이트 우선. Budget/Stop Rule 준수. |
| Cycle 0 State 오염 | Low | 0B.1에서 State 스냅샷 백업 후 작업. |
| 수동 실행 일관성 | Low | 템플릿 기반 작업, Deliverable 형식 준수. |

---

## 7. Dependencies

### 내부
| 모듈 | 의존 대상 |
|------|-----------|
| Collect (0B.2) | revised-plan-c1.md, State 파일, templates/ |
| Integrate (0B.3) | Evidence Claim Set (0B.2), schemas/, State 파일 |
| Critique (0B.4) | KB Patch (0B.3), Metrics 공식 (design-v2.md §4) |
| Plan Modify (0B.5) | Critique Report (0B.4), Critique→Plan 규칙 (design-v2.md §5) |

### 규약 문서
| 문서 | 의존 영역 |
|------|-----------|
| `docs/gu-bootstrap-spec.md` §2 | Integrate (0B.3): 동적 GU 발견 규칙 (트리거 A/B/C + 상한) |
| `docs/gu-bootstrap-spec.md` §3 | Integrate (0B.3): 신규 GU 우선순위 산정 |
| `docs/gu-bootstrap-spec.md` §6-B | Critique (0B.4): 동적 발견 체크리스트 |

### 외부
- WebSearch/WebFetch (수집 시 사용)
- JSON Schema 검증 (schemas/ 파일)

---

## 8. Conflict-preserving 검증 전략 (Phase 0B 고유)

### 왜 중요한가
- Cycle 0에서 충돌 0건 → 5대 불변원칙 중 유일하게 실증 안 됨
- LangGraph 자동화(Phase 1) 구현 시 충돌 처리 로직이 핵심
- 충돌 처리 경험 없이 자동화하면 edge case 대응 불가

### 충돌 발생 기대 영역

| GU ID | 대상 | 충돌 가능성 | 예상 시나리오 |
|-------|------|------------|--------------|
| GU-0019 | sim-card:price | High | 통신사별/판매 플랫폼별 가격 차이 → 기존 KU-0007과 상이한 가격 |
| GU-0001 | jr-pass:nozomi-alternative | Medium | Hikari vs Kodama 소요시간 출처별 차이 |
| GU-0013 | credit-card:acceptance | Medium | 지역/업종별 사용 가능률 출처 간 차이 |

### 충돌 처리 절차 (design-v2.md §5 Consistency 규칙)
1. disputed KU 쌍 식별 → `status: "disputed"` 설정
2. hold 판정 (즉시 해결 불가 시)
3. 추가 독립 출처 수집 → condition_split 또는 coexist 결정
4. Critique에서 Consistency 실패모드 보고
5. Plan Modify에서 추적 가능하게 반영

### 검증 기준
- [x] 최소 1건 disputed KU 존재 → 2건 (KU-0007, KU-0011)
- [x] disputed KU에 대해 hold/condition_split/coexist 중 하나 적용 → condition_split + hold
- [x] Critique에서 Consistency 실패모드 탐지 → critique-c1.md §2
- [x] Plan Modify에서 해당 처방의 추적성 확인 → revised-plan-c2.md §1 (RX-08, RX-09)
