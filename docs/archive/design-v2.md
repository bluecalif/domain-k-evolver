# Domain-K-Evolver: 설계 v2

> **기반**: draft.md (원본 설계) + Cycle 0~2 수동 실행 결과
> **갱신일**: 2026-03-04 (Phase 0C.6 통합)
> **상태**: Cycle 0~2 검증 완료, expansion-policy v1.0 확정, LangGraph 자동화 준비

---

## 1. 변경 이력

| 항목 | draft.md (v1) | design-v2 | 변경 근거 |
|------|---------------|-----------|-----------|
| 데이터 형식 | 서술적 정의만 | JSON Schema 확정 (schemas/) | Cycle 0에서 실제 저장/조회 수행 |
| Metrics 공식 | 없음 | 6개 공식 확정 | Cycle 0 Critique에서 실제 계산 검증 |
| Critique→Plan 규칙 | "처방을 컴파일" 서술 | 6개 실패모드별 변환 규칙 | Cycle 0 PM에서 실제 변환 수행 |
| Scope Boundary | 없음 | Seed Pack 필수 섹션으로 추가 | Gap Map 폭발 방지 필수 |
| Entity Resolution | "같은 대상 식별" 서술 | 캐노니컬 키 규칙 + is_a 관계 필요성 | Cycle 0 Integration에서 ic-card/suica 분리 문제 |
| 엔티티 입도 | 미정의 | 3단계 중첩 시 분리 규칙 | Cycle 0 airport-transfer 구조 문제 |
| Axis Coverage Matrix | 없음 | 다축 커버리지 정량 추적 + deficit_ratio | Phase 0C geography 편중 93.5% 발견 |
| Jump Mode | 없음 | 조건부 GU 상한 상향 (5종 trigger + 4종 guardrail) | Phase 0C Cycle 2 실측 검증 |
| explore/exploit 분리 | 없음 | Jump Mode 시 explore(신규 축)/exploit(기존 GU) budget 분리 | Cycle 2: 60/40 배분으로 geography deficit 해소 |
| Entity Hierarchy | "is_a 필요성" 서술 | alias/is_a 관계 정의 규칙 확정 | RX-04→RX-10→RX-13 누적 (3 Cycle) |
| expansion-policy | 없음 | v1.0 확정 (trigger 임계치 + guardrail 수치) | Phase 0C.5 Cycle 1~2 실측 기반 |

---

## 2. Evolver State 정의 (확정)

```
State = (K, G, P, M, D)
  K: knowledge-units.json  — KU[] (schemas/knowledge-unit.json)
  G: gap-map.json           — GU[] (schemas/gap-unit.json)
  P: policies.json          — 출처신뢰/TTL/교차검증/충돌해결 규칙
  M: metrics.json           — 정량 지표 + delta
  D: domain-skeleton.json   — 카테고리/필드/관계/키규칙/Scope/axes/entity_hierarchy
```

### 저장 형식 결정
- **현재**: JSON 파일 (파일 I/O)
- **이유**: LangGraph 노드에서 직접 읽기/쓰기 가능, 스키마 검증 용이, 디버깅 투명
- **추후**: 규모 확대 시 SQLite/PostgreSQL 전환. 인터페이스는 동일 (CRUD on typed objects)

---

## 3. 4대 객체 JSON Schema (확정)

`schemas/` 디렉토리에 JSON Schema Draft 2020-12로 정의 완료.

| 객체 | 파일 | ID 패턴 | required 필드 수 | optional 필드 수 |
|------|------|---------|------------------|------------------|
| KU | knowledge-unit.json | KU-NNNN | 8 | 3 (conditions, validity, disputes) |
| EU | evidence-unit.json | EU-NNNN | 5 | 3 (location, credibility_prior, language) |
| GU | gap-unit.json | GU-NNNN | 5 | 3 (risk_level, resolution_criteria, resolved_by) |
| PU | patch-unit.json | PU-NNNN | 6 | 3 (conflict_decisions, gap_updates, policy_updates) |

### Cycle 0 실용성 검증 결과
- required/optional 구분으로 Seed 단계에서 가벼운 KU 작성 가능 (형식주의 부담 감소 ✅)
- conditions 필드의 자유 구조(additionalProperties: true)가 도메인 적응에 유리
- entity_key 정규식 패턴이 Entity Resolution의 기반이 됨

---

## 4. Metrics 계산 공식 (확정)

Cycle 0에서 실제 계산하며 검증한 공식들.

```python
# 1. 근거율 — 모든 active KU 중 EU가 1개 이상인 비율
evidence_rate = count(ku for ku in K if len(ku.evidence_links) >= 1 and ku.status == 'active') / count(ku for ku in K if ku.status == 'active')

# 2. 다중근거율 — 독립 출처 2개 이상인 비율
multi_evidence_rate = count(ku for ku in K if len(ku.evidence_links) >= 2 and ku.status == 'active') / count(ku for ku in K if ku.status == 'active')

# 3. Gap 해소율 — 이번 Cycle에서 해결된 Gap 비율
gap_resolution_rate = count(gu for gu in G_cycle if gu.status_changed_to == 'resolved') / count(gu for gu in G_start if gu.status == 'open')

# 4. 충돌률
conflict_rate = count(ku for ku in K if ku.status == 'disputed') / count(ku for ku in K if ku.status in ['active', 'disputed'])

# 5. 평균 신뢰도
avg_confidence = mean(ku.confidence for ku in K if ku.status == 'active')

# 6. 신선도 리스크 — TTL 초과 KU 수
staleness_risk = count(ku for ku in K if date(ku.observed_at) + timedelta(days=ku.validity.ttl_days) < today)

# 7. 커버리지 (전체 Gap 대비 해결 비율)
coverage = count(gu for gu in G if gu.status == 'resolved') / count(G)
```

### 건강 지표 임계치 (권장)

| 지표 | 건강 | 주의 | 위험 |
|------|------|------|------|
| 근거율 | ≥ 0.95 | 0.80–0.94 | < 0.80 |
| 다중근거율 | ≥ 0.50 | 0.30–0.49 | < 0.30 |
| 충돌률 | ≤ 0.05 | 0.06–0.15 | > 0.15 |
| 평균 confidence | ≥ 0.85 | 0.70–0.84 | < 0.70 |
| 신선도 리스크 | 0 | 1–3 | > 3 |

---

## 5. Critique→Plan 컴파일 규칙 (확정)

Cycle 0에서 실제 변환을 수행하며 도출한 규칙.

| 실패모드 | 트리거 조건 | Plan 변경 유형 | 컴파일 규칙 |
|----------|-------------|----------------|-------------|
| **Epistemic** | 단일출처 financial/safety KU 존재 | Source Strategy 강화 | 해당 KU의 Gap을 재타겟하거나 추가 EU 수집 쿼리 추가. Acceptance Test에 min_eu ≥ 2 강제. |
| **Temporal** | expires_at - 30일 이내 KU 존재 | Gap Priority 상향 | 관련 Gap을 critical로 승격. expires_at 도래 후면 KU를 stale 처리하고 신규 Gap 생성. |
| **Structural** | 단일 KU에 3단계+ 중첩 객체 | Schema 플래그 (deferred) | 즉시 분리하지 않음. 3 Cycle 축적 후 Outer Loop에서 엔티티 입도 리모델링 결정. |
| **Consistency** | disputed KU 쌍 존재 | 추가 수집 + 조건 분석 | hold 판정 → Cycle N+1에서 독립 출처 추가 수집. 조건 분석으로 condition_split 시도. |
| **Planning** | 미커버 카테고리 > 50% | Gap Selection 보정 | 미커버 카테고리에서 최소 1 Gap씩 강제 포함. 기존 우선순위 기준에 카테고리 분포 보정 계수 추가. |
| **Integration** | 동일 실물의 다중 엔티티 발견 | 관계 추가 또는 병합 | is_a/part_of 관계 추가. 스키마에 관계 타입 부족하면 Structural로 에스컬레이션. |

---

## 6. Entity Resolution 방법 (구체화)

### 캐노니컬 키 기반 매칭

```
1. Claim의 엔티티 명칭을 정규화: 소문자화, 공백→하이픈, 공식 영문명 기준
2. {domain}:{category}:{slug} 패턴으로 키 생성
3. 기존 K에서 entity_key 완전 일치 검색
4. 일치 → matched (기존 KU에 field 추가/업데이트)
5. 불일치 → new (신규 엔티티 생성)
6. 유사 매칭 (레벤슈타인 거리 ≤ 2) → 수동 확인 또는 is_a 관계 검토
```

### 분류 계층 (is_a) 및 Entity Hierarchy (Phase 0C 확정)

기존 4개 관계(covers_route, valid_for, located_in, accepted_at)에 추가:

- **`is_a`**: 하위 entity는 상위의 필드를 상속하되 지역 특화 값으로 오버라이드 가능
  - 예: `kyoto-ryokan` is_a `ryokan` → ryokan의 nationwide 가격 정보를 상속, kyoto 특화 가격으로 오버라이드
- **`alias`**: 동일 entity의 다른 이름. canonical key로 통일
  - 예: `metro-pass` alias `subway-ticket` → canonical: `subway-ticket`

`domain-skeleton.json`에 `entity_hierarchy` 섹션으로 정의:
```json
{
  "entity_hierarchy": [
    {"parent": "ryokan", "child": "kyoto-ryokan", "relation": "is_a"},
    {"alias": ["metro-pass", "subway-ticket"], "canonical": "subway-ticket"}
  ]
}
```

Integrate 시 entity_key가 alias에 해당하면 canonical로 자동 변환.

> **근거**: RX-04(Cycle 0) → RX-10(Cycle 1) → RX-13(Cycle 2) 3 Cycle 누적 미해결. Phase 0C.5에서 규칙 확정.

---

## 7. Inner Loop 6단계 Deliverable 계약 (확정)

| 단계 | Deliverable | 필수 입력 | 산출물 | 검증 기준 |
|------|-------------|-----------|--------|-----------|
| (S) Seed | Seed Pack | 도메인 명세 | Skeleton + Seed KUs + Gap Map v0 + Policy | Skeleton에 키 규칙 있는가? Gap ≥ 20? 모든 카테고리에 GU 존재? (→ [`gu-bootstrap-spec.md`](gu-bootstrap-spec.md) §6-A) |
| (P) Plan | Collection Plan | Gap Map, Critique(cycle≥1) | Target Gaps + Source Strategy + Queries + Tests + Budget | Gap-driven인가? Stop Rule 있는가? |
| (C) Collect | Evidence Claim Set | Collection Plan | Claims + EU Bundles + 태깅 | 모든 Claim에 EU 있는가? 교차검증 충족? |
| (I) Integrate | KB Patch | Claims, State | Adds/Updates/Deprecates + Conflict Decisions + Gap Update | Patch 형식? 충돌 보존? |
| (R) Critique | Critique Report | Patch, State | Metrics Delta + Failure Modes + Prescriptions | 처방이 Plan으로 번역 가능한가? |
| (PM) Plan Modify | Revised Plan | Critique | 추적성 테이블 + Revised Collection Plan + Policy Update | 모든 처방에 반영 기록? |

---

## 8. 5대 불변원칙 (확정 + 검증 방법)

| 원칙 | 정의 | 자동 검증 방법 |
|------|------|----------------|
| Gap-driven | Plan의 Target Gap이 모두 Gap Map에서 유래 | Plan.target_gaps ⊆ G.open |
| Claim→KU 착지성 | 모든 Claim이 KU로 변환됨 | count(claims) == count(adds) + count(updates) + count(rejected_with_reason) |
| Evidence-first | KU는 EU 없으면 미완성 | all(len(ku.evidence_links) >= 1 for ku in K if ku.status == 'active') |
| Conflict-preserving | 충돌은 구조적 보존 | disputed KU는 삭제 불가, hold/condition_split/coexist만 허용 |
| Prescription-compiled | Critique 처방이 Plan에 반영 | all(rx.id in revised_plan.traceability for rx in critique.prescriptions) |

---

## 9. HITL Gate 설계 (Cycle 0 경험 반영)

| Gate | 시점 | 조건 | Cycle 0 관찰 |
|------|------|------|--------------|
| A: Plan 승인 | Plan 생성 후 | 항상 (경량) | Gap 선정 합리성 확인에 유용 |
| B: High-risk Claims | Collect 후 | safety/policy/financial Claim | Cycle 0에서 financial 교차검증 미준수 사례 → Gate B 강화 필요 |
| C: Conflict Adjudication | Integrate 후 | disputed KU 존재 시 | Cycle 0에서 충돌 없어 미발동 |
| D: Executive Audit | 10 Cycle마다 | 누적 Metrics 분석 | 미도달 |
| E: Convergence Guard | Jump Mode 2연속 시 | 연속 Jump의 정당성 재판정 | C2→C3: 사전 GU 생성으로 Normal 전환, 미발동 |

### Cycle 0에서의 교훈
- Gate B를 Collect 직후가 아니라 **Integration 전**에 배치하는 것이 효율적 (Claim 검토 후 통합)
- financial 교차검증 미준수를 Gate B에서 자동 탐지하는 규칙 추가 권장

---

## 10. LangGraph 자동화 설계 초안

### 노드 정의

```
Nodes:
  seed_node       → Seed Pack 생성 (도메인 입력 → State 초기화)
                     Bootstrap GU 생성: gu-bootstrap-spec.md §1 알고리즘 적용
                     입력: domain-skeleton.json, seed KUs, policies.json
                     출력: gap-map.json (Bootstrap GU 배열, ≥20개, 전 카테고리 커버)
  mode_node       → Normal/Jump Mode 판정 (Phase 0C 추가)
                     입력: gap-map (axis_tags), domain-skeleton (axes), metrics (jump_mode history)
                     로직: 5종 trigger 판정 → Mode 결정 → budget 배분
                     출력: {mode, cap, explore_budget, exploit_budget, trigger_set}
  plan_node       → Collection Plan 생성 (State + Mode → Plan)
                     Jump Mode 시: explore Target 선정 (deficit 축 기반) + exploit Target 선정
                     Normal Mode 시: exploit Target만 선정
  collect_node    → Evidence 수집 (Plan → Claims) [WebSearch/WebFetch 도구 사용]
  integrate_node  → KB Patch 적용 (Claims + State → Updated State)
                     동적 GU 생성 시: cap(base_cap/jump_cap) 준수, expansion_mode/trigger 기재
  critique_node   → Critique Report 생성 (State → Critique)
                     Structural Deficit Analysis 포함: Axis Coverage Matrix 재계산
                     Jump Mode 검증: high/critical ≥ 40%, deficit 감소 확인
  plan_modify_node → Revised Plan 생성 (Critique → Plan)
                     처방 추적성 테이블 + 미반영 사유 기록 필수
  hitl_gate_node  → 사람 검토 (조건부 중단)
                     Gate E 추가: Convergence Guard (연속 2 Cycle Jump 시)
```

### 엣지 정의

```
Edges:
  START → seed_node                     [최초 1회]
  seed_node → mode_node
  mode_node → plan_node                 [mode + budget 결정 후]
  plan_node → hitl_gate_node (Gate A)
  hitl_gate_node → collect_node         [승인 시]
  collect_node → hitl_gate_node (Gate B) [high-risk claim 존재 시]
  hitl_gate_node → integrate_node       [승인 시]
  integrate_node → critique_node
  critique_node → plan_modify_node
  plan_modify_node → mode_node          [다음 Cycle → Mode 재판정]

  # Convergence Guard (Phase 0C 추가)
  mode_node → hitl_gate_node (Gate E)   [연속 2 Cycle Jump 시]
  hitl_gate_node → plan_node            [HITL 승인 후]

  # 종료 조건
  critique_node → END                   [수렴 판정: gu-bootstrap-spec §5 조건 충족 OR max_cycles 도달]

  # Outer Loop
  critique_node → remodel_node          [remodeling_trigger == true, 매 10 Cycle]
  remodel_node → mode_node
```

### State 관리

```python
class EvolverState(TypedDict):
    knowledge_units: list[KnowledgeUnit]
    gap_map: list[GapUnit]
    policies: Policies
    metrics: Metrics
    domain_skeleton: DomainSkeleton  # axes, entity_hierarchy 포함
    current_cycle: int
    current_plan: CollectionPlan | None
    current_claims: list[Claim] | None
    current_critique: CritiqueReport | None
    # Phase 0C 추가
    current_mode: ModeDecision | None  # {mode, cap, explore_budget, exploit_budget, trigger_set}
    axis_coverage: AxisCoverageMatrix | None  # Critique에서 재계산
    jump_history: list[int]  # Jump Mode 진입 Cycle 번호 기록 (Convergence Guard용)
```

### 도구 바인딩

| 노드 | 필요 도구 |
|------|-----------|
| collect_node | WebSearch, WebFetch |
| integrate_node | 파일 I/O (JSON read/write) |
| hitl_gate_node | Human interrupt (LangGraph interrupt) |
| 기타 | LLM 추론만 |

---

## 11. Cycle 0 검증 체크리스트 결과

- [x] 6개 Deliverable이 모두 작성되었는가? → ✅ seed-pack, collection-plan, evidence-claims, kb-patch, critique, revised-plan
- [x] state/ JSON 파일들이 유효한 데이터로 채워졌는가? → ✅ 5개 파일 모두 유효
- [x] Gap Map이 Seed 대비 줄어들었거나 의미있게 재구성되었는가? → ✅ 25→21 (7 해결, 3 신규)
- [x] Critique가 실제로 Plan을 바꾸는 구체적 처방을 생산했는가? → ✅ 6개 처방, 모두 Revised Plan에 추적 가능하게 반영
- [x] 5대 불변원칙이 지켜졌는가? → ✅ (Conflict-preserving은 충돌 0건으로 미검증)
- [x] 스키마/템플릿이 실용적이었는가? → ✅ required/optional 구분으로 부담 적절

---

## 12. 다음 단계 (Phase 0C 완료 기준)

### 완료된 수동 검증
- [x] Cycle 0: 6단계 Deliverable 검증, 5대 불변원칙 확인
- [x] Cycle 1 (Phase 0B): Conflict-preserving 검증 (KU-0007 disputed), Prescription-compiled 검증
- [x] Cycle 2 (Phase 0C): Jump Mode 실측, Axis Coverage Matrix, 5종 trigger/4종 guardrail 검증
- [x] expansion-policy v1.0 확정 (trigger 임계치 + guardrail 수치)

### Phase 1: LangGraph 자동화
1. **mode_node 구현**: 5종 trigger 판정 + budget 배분 로직
2. **plan_node 확장**: explore/exploit Target 자동 선정 (deficit 축 기반)
3. **integrate_node 확장**: 동적 GU 생성 시 cap 준수 + axis_tags 자동 태깅
4. **critique_node 확장**: Structural Deficit Analysis 자동 계산 (Axis Coverage Matrix)
5. **hitl_gate_node 확장**: Gate E (Convergence Guard) 추가
6. **Entity Hierarchy 구현**: alias 자동 변환, is_a 상속 로직

### Phase 1 입력 조건 체크리스트
- [x] 4대 객체 JSON Schema (schemas/) — 확정
- [x] 6단계 Deliverable 계약 (§7) — 확정
- [x] Metrics 공식 + 건강 임계치 (§4) — 확정
- [x] Critique→Plan 컴파일 규칙 (§5) — 확정
- [x] Bootstrap 알고리즘 (gu-bootstrap-spec §1) — 확정
- [x] 동적 GU Normal/Jump 상한 (gu-bootstrap-spec §2) — 확정
- [x] Axis Coverage Matrix 계산 로직 (gu-bootstrap-spec §2.5) — 확정
- [x] Jump Mode trigger/guardrail (expansion-policy v1.0) — 확정
- [x] explore/exploit 비율 (expansion-policy v1.0 §5.2) — 확정
- [x] Entity Hierarchy 규칙 (expansion-policy v1.0 §7) — 확정
- [x] 수렴 조건 (gu-bootstrap-spec §5) — 확정
- [ ] japan-travel Cycle 3+ 수동 실행 (선택: 추가 검증 필요 시)

### 3. 새 도메인 테스트
japan-travel 외 도메인(예: 부동산, 기술 스택)으로 도메인 불문 작동 검증
