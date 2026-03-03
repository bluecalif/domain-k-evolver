# Phase 0B: Cycle 1 수동 검증 — Tasks
> Last Updated: 2026-03-03 (GU Bootstrap 명세 반영)
> Status: Planning

## Summary

| Total | S | M | L | XL | Done |
|-------|---|---|---|----|----|
| 5 | 1 | 2 | 2 | 0 | 0/5 |

---

## Stage A: 준비

- [ ] **0B.1** Cycle 1 디렉토리 준비 + State 스냅샷 `[S]`
  - `bench/japan-travel/cycle-1/` 디렉토리 생성
  - `bench/japan-travel/state-snapshots/cycle-0-snapshot/` 에 현재 State 5종 백업
  - `revised-plan-c1.md` 최종 리뷰 — 8개 Target Gap, Source Strategy, Acceptance Tests 확인
  - 충돌 시나리오 계획 수립 (GU-0019 SIM 가격, GU-0001 JR Pass 소요시간 등)
  - Commit: `[phase0b] Step 0B.1: Cycle 1 directory setup + state snapshot`

---

## Stage B: 수집 + 통합

- [ ] **0B.2** Collect — 8개 Gap 수집, Evidence Claim Set 작성 `[L]`
  - revised-plan-c1.md §6 기반 수집 실행
  - 8개 Target Gap에 대해 WebSearch/WebFetch로 정보 수집
  - 각 Claim에 EU 번들 첨부 (source_id, retrieved_at, snippet, source_type)
  - **Financial Gap (GU-0019, GU-0026, GU-0013)**: 반드시 독립 출처 2개 이상 (RX-01 반영)
  - **카테고리 보충 (GU-0007, GU-0010, GU-0008)**: accommodation, dining, attraction (RX-03 반영)
  - **충돌 의도적 포함**: 기존 KU와 상이한 정보 발견 시 명시적 태깅
  - Claim 간 중복/상충 후보 사전 태깅
  - Budget: 15회 검색 상한, 동일 출처 3회 초과 시 전환
  - 산출물: `bench/japan-travel/cycle-1/evidence-claims-c1.md`
  - Commit: `[phase0b] Step 0B.2: Cycle 1 evidence collection`

- [ ] **0B.3** Integrate — Claims → KB Patch 적용, State 업데이트 `[L]`
  - Evidence Claim Set → KB Patch 변환
  - Entity Resolution: 캐노니컬 키 기반 매칭 (design-v2.md §6)
    - 기존 KU entity_key 완전 일치 → update
    - 불일치 → new (신규 KU 생성)
    - 유사 매칭 (레벤슈타인 ≤ 2) → 수동 확인
  - **충돌 처리**: 기존 KU와 상이한 값 발견 시
    - `status: "disputed"` 설정
    - `disputes[]` 필드에 충돌 정보 기록
    - hold / condition_split / coexist 판정
  - State 파일 업데이트:
    - `knowledge-units.json`: 신규 KU 추가 + 기존 KU 업데이트 + disputed 설정
    - `gap-map.json`: 해결된 Gap → `status: "resolved"`, 신규 Gap 추가
  - **동적 GU 발견** (gu-bootstrap-spec §2):
    - 트리거 A: 새 KU가 미지 슬롯 참조 시 → missing GU 생성
    - 트리거 B: 단일출처 + safety/financial/policy KU → uncertain GU 생성
    - 트리거 C: Skeleton에 없는 entity_key 등장 → 핵심 필드 GU 배치 생성
    - 상한: 신규 GU ≤ 4개 (open 21의 20%, safety 예외)
    - 신규 GU의 expected_utility/risk_level → §3 매핑 테이블 적용
  - Schema 검증: `schemas/*.json` 기반 모든 추가/수정 KU/GU 검증
  - 산출물: `bench/japan-travel/cycle-1/kb-patch-c1.md`
  - Commit: `[phase0b] Step 0B.3: Cycle 1 integration + state update`

---

## Stage C: 비평 + 계획수정

- [ ] **0B.4** Critique — Metrics delta, 5대 불변원칙 전체 검증 `[M]`
  - Metrics 계산 (design-v2.md §4 공식):
    - 근거율, 다중근거율, Gap 해소율, 충돌률, 평균 confidence, 신선도 리스크, 커버리지
  - Metrics Delta 분석: Cycle 0 종료 → Cycle 1 종료 비교
  - 실패모드 탐지 (6개 분류):
    - Epistemic, Temporal, Structural, Consistency, Planning, Integration
  - **5대 불변원칙 검증**:
    - [ ] Gap-driven: target_gaps ⊆ G.open 확인
    - [ ] Claim→KU 착지성: claims == adds + updates + rejected_with_reason
    - [ ] Evidence-first: all active KU에 EU ≥ 1
    - [ ] **Conflict-preserving**: disputed KU 존재 확인, 삭제 시도 없음, hold/split/coexist 적용
    - [ ] Prescription-compiled: 모든 RX가 revised-plan에 추적 가능
  - **동적 GU 발견 체크** (gu-bootstrap-spec §6-B):
    - [ ] 신규 GU 수 ≤ open의 20% (safety 예외)
    - [ ] 신규 GU에 resolution_criteria 명시
    - [ ] 각 신규 GU의 트리거(A/B/C) 분류 기록
    - [ ] created_at = Cycle 1 날짜
  - 처방(Prescriptions) 생성
  - Remodeling Trigger 평가
  - State 업데이트: `metrics.json` 갱신
  - 산출물: `bench/japan-travel/cycle-1/critique-c1.md`
  - Commit: `[phase0b] Step 0B.4: Cycle 1 critique + invariant validation`

- [ ] **0B.5** Plan Modify — Revised Plan C2 작성, design-v2 피드백 반영 `[M]`
  - Critique 처방 → Revised Plan 컴파일 (design-v2.md §5 규칙 적용)
  - 추적성 테이블 작성: 처방 ID → 반영 방법 → 반영 위치
  - Revised Collection Plan C2 작성:
    - 변경된 Gap 우선순위
    - 변경된 Source Strategy
    - 변경된 검증 기준
    - Budget & Stop Rules
  - Policy Update (필요 시)
  - design-v2.md 피드백: Cycle 1 경험에서 설계 수정 필요 항목 정리
  - 산출물: `bench/japan-travel/cycle-1/revised-plan-c2.md`
  - Commit: `[phase0b] Step 0B.5: Revised Plan C2 + design feedback`

---

## Completion Criteria

- [ ] `bench/japan-travel/cycle-1/` 에 4개 Deliverable 존재
- [ ] State 파일 5종 Cycle 1 반영 완료
- [ ] 5대 불변원칙 전체 검증 PASS (특히 Conflict-preserving)
- [ ] Metrics delta 문서화 (critique-c1.md §1)
- [ ] revised-plan-c2.md 존재 → Phase 1 입력 준비 완료
- [ ] RX-01, RX-03, RX-05, RX-06 처방 반영 확인
- [ ] 동적 GU 발견 규칙 준수 (gu-bootstrap-spec §2/§6-B) — Phase 0B가 첫 실용성 검증
