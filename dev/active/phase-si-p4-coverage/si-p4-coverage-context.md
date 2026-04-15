# Silver P4: Coverage Intelligence — Context
> Last Updated: 2026-04-15
> Status: **Stage A~D Complete · Stage E Planning**

## 1. 핵심 파일

### 읽어야 할 기존 코드
| 파일 | 내용 | 이유 |
|------|------|------|
| `src/nodes/plan.py` | target 선택 로직 (explore/deficit 기반) | reason_code 추가 위치 |
| `src/nodes/critique.py` | 6대 실패모드 분석 + 처방 | machine-readable 처방 변환 |
| `src/utils/plateau_detector.py` | KU/GU 기반 plateau, conflict_rate 복합 | novelty trigger 확장 |
| `src/utils/readiness_gate.py` | `_gini_coefficient` (line 20), VP1 category_gini/field_gini | Gini 함수 재사용, 임계치 참조 |
| `src/utils/metrics.py` | `compute_metrics`, `compute_axis_coverage`, `compute_deficit_ratios` | coverage_map 이 활용할 기존 메트릭 |
| `src/nodes/remodel.py` | merge/split/reclassify/alias/source_policy/gap_rule | category_addition proposal 추가 |
| `src/orchestrator.py` | Outer Loop, _maybe_run_remodel, MetricsLogger | novelty_history/coverage_map 채움 + Gini criteria 연동 |
| `src/state.py` | EvolverState (coverage_map: dict, novelty_history: list) | 필드 활용 |
| `src/nodes/audit.py` | 4 분석함수 (cross_axis_coverage 등) | coverage 데이터 소비 |

### 설계 문서
| 파일 | 참조 섹션 |
|------|-----------|
| `docs/silver-masterplan-v2.md` | §4 P4, §7 S7 scenario |
| `docs/silver-implementation-tasks.md` | §8 Phase P4 (11 tasks → 17 tasks 확장) |

---

## 2. 데이터 인터페이스

### 입력 (어디서 읽는가)
| 데이터 | 소스 | 형태 |
|--------|------|------|
| knowledge_units | `EvolverState` | `list[dict]` — entity_key, claims, evidence_links |
| gap_map | `EvolverState` | `list[dict]` — status, entity_key, axis_tag |
| domain_skeleton | `EvolverState` | `dict` — categories, axes, fields |
| metrics_log | `MetricsLogger.entries` | `list[dict]` — ku_active, gu_total per cycle |
| audit_history | `EvolverState` | `list[dict]` — findings, severity |

### 출력 (어디에 쓰는가)
| 데이터 | 대상 | 형태 |
|--------|------|------|
| novelty_score | `state["novelty_history"]` append | `float` (0~1) |
| coverage_map | `state["coverage_map"]` | `dict` — `{axis: {bucket: {ku_count, deficit_score, gini_weight}}}` |
| reason_code | plan output 각 target | `str` enum |
| category_addition proposal | `remodel_report.proposals[]` | `dict` — type="category_addition" |
| machine-readable 처방 | critique output prescriptions | `dict` — rule, action, threshold |

### Coverage Map 구조 (Gini 통합)
```json
{
  "transport": {
    "ku_count": 15,
    "deficit_score": 0.25,
    "field_coverage": {"price": 5, "schedule": 3, "route": 7}
  },
  "accommodation": {
    "ku_count": 3,
    "deficit_score": 0.70,
    "field_coverage": {"price": 2, "location": 1}
  },
  "summary": {
    "category_gini": 0.42,
    "field_gini": 0.38,
    "gini_deficit_adjustment": 0.15
  }
}
```

### Reason Code Enum
| code | 의미 | 발동 조건 |
|------|------|-----------|
| `deficit:category={cat}` | 해당 카테고리 coverage 부족 | deficit_score > 0.5 |
| `deficit:field={field}` | 해당 필드 coverage 부족 | field deficit > 0.5 |
| `plateau:novelty<{thr}` | novelty 정체 | novelty < 0.1 × 5c |
| `gini:category_imbalance` | 카테고리 Gini 불균형 | category_gini > 0.45 |
| `gini:field_imbalance` | 필드 Gini 불균형 | field_gini > 0.45 |
| `audit:merge_pending` | 감사 merge 대기 | audit finding severity=critical |
| `remodel:pending` | 리모델 대기 | remodel_report.approval.status="pending" |
| `seed:initial` | 초기 시드 | cycle 0 |

---

## 3. 주요 결정사항

| # | 결정 | 근거 |
|---|------|------|
| D-134 | Gini criteria 는 P4 coverage management 로 연기 | P2 범위 밖, category addition 과 함께 설계 |
| (신규) | Gini 를 coverage_map deficit 산정에 가중 반영 (기본 가중 0.3) | readiness_gate 임계치 0.45 기준 재활용 |
| (신규) | category_addition 보수적 조건: ≥5 KU + LLM 의미 판단 + 사이클당 1개 + HITL 승인 | 공격적 추가 방지 (D-P2-3 과다 merge 교훈) |
| (신규) | reason_code 는 plan output 모든 target 에 필수 (fallback: seed:initial) | masterplan §4 P4 gate 조건 |
| (신규) | novelty 정체 판정: 5c 연속 novelty < 0.1 | masterplan §8 P4 gate |
| (신규) | _gini_coefficient 함수는 readiness_gate.py 에서 공유 유틸로 추출 | 중복 구현 방지 |

---

## 4. 컨벤션 체크리스트

### 5대 불변원칙
- [x] **Gap-driven**: coverage deficit → plan target → gap 해소. Gini 불균형도 gap 의 한 형태
- [x] **Claim→KU 착지성**: category_addition 은 KU 구조 변경 아님 (skeleton 카테고리 추가만)
- [x] **Evidence-first**: 카테고리 추가는 ≥5 KU 증거 기반
- [x] **Conflict-preserving**: 카테고리 추가는 기존 KU 의 entity_key 변경 없음 (reclassify 와 별개)
- [x] **Prescription-compiled**: critique 처방 → plan reason_code → 실행

### Metrics 임계치 (P4 직접 관련)
| 지표 | 건강 | 비고 |
|------|------|------|
| novelty 평균 (10c) | ≥ 0.25 | P4 Gate 필수 |
| reason_code coverage | 100% | P4 Gate 필수 |
| category_gini | ≤ 0.45 | readiness_gate 기준 동일 |
| field_gini | ≤ 0.45 | readiness_gate 기준 동일 |

### Schema 정합성
- `state.py` EvolverState — coverage_map: dict, novelty_history: list[float] (기존 필드 활용)
- `remodel_report.schema.json` — category_addition proposal type 추가 필요

### 인코딩
- JSON read/write: `encoding='utf-8'` explicit
- 커밋: `[si-p4] Step X.Y: 설명`

---

## 5. Stage E: External Anchor 추가 컨텍스트

### 5.1 신규 파일 (Stage E)

| 파일 | 역할 | 참조 재사용 |
|---|---|---|
| `src/utils/external_novelty.py` | 누적 이력 대비 novelty 측정 (entity_key+field+claim-hash) | 기존 `novelty.py` 는 cycle-diff 유지 |
| `src/utils/reach_ledger.py` | distinct_domains/languages/time-range 누적 집계 | `readiness_gate._gini_coefficient` normalization |
| `src/utils/cost_guard.py` | Stage E 기능별 per-cycle/per-run budget + kill-switch | — |
| `src/nodes/universe_probe.py` | LLM survey + broad Tavily → candidate_categories 제안 | `remodel.py` category_addition 경로 |
| `src/nodes/exploration_pivot.py` | LLM query rewriter + candidate axis probe (1 cycle 치환) | `plateau_detector.py` 조건 확장 |

### 5.2 수정 파일 (Stage E)

| 파일 | 변경 |
|---|---|
| `src/nodes/remodel.py` | category_addition 이 universe_probe evidence 도 입력으로 받도록 확장 |
| `src/nodes/plan.py` | reason_code 3종 추가 (external_novelty/universe_probe/reach_diversity), 우선순위 재조정 |
| `src/utils/plateau_detector.py` | external_novelty + reach_degraded 조건 통합 |
| `src/utils/readiness_gate.py` | VP4_exploration_reach 추가 |
| `src/graph.py` | universe_probe + exploration_pivot 노드 삽입 |
| `src/config.py` | `external_anchor_enabled`, `probe_interval_cycles`, budget 필드 |
| `src/state.py` | `external_novelty_history`, `reach_ledger`, `candidate_categories` 필드 |

### 5.3 Stage E 데이터 인터페이스

| 데이터 | 출력 대상 | 형태 |
|---|---|---|
| external_novelty | `state.external_novelty_history` | `float` (0~1) |
| reach_ledger | `state.reach_ledger` | `{distinct_domains, distinct_languages, time_range_bins, per_cycle_delta}` |
| candidate_categories | `state.skeleton.candidate_categories` | `list[{slug, name, rationale, evidence_count, confidence}]` |
| universe_probe_report | `state.universe_probe_history[-1]` | `{proposals, validated, cost}` |
| pivot_reason | `state.pivot_reason_code` | 1 cycle 용 `plateau:exploration_pivot` |

### 5.4 신규 Reason Code (Stage E 추가분)

| code | 발동 조건 |
|---|---|
| `external_novelty:deficit` | history_novelty < 0.2 |
| `universe_probe:missing_category={slug}` | candidate_categories evidence 검증 통과 |
| `reach_diversity:low={axis}` | reach_ledger axis 정체 |
| `plateau:exploration_pivot` | pivot node 활성 시 1 cycle 용 |

### 5.5 우선순위 재조정

**변경 전 (Stage A~D)**: `deficit > gini > plateau > audit > seed`

**변경 후 (Stage E)**: `external_novelty > deficit > gini > plateau > audit > seed`

근거: 외부 미탐 신호가 내부 균형 신호보다 우선. 단 **L3 gap_rule (audit coverage_gap critical) 은 우선순위와 별도로 항상 먼저 consume** (별도 경로).

### 5.6 주요 결정사항 (Stage E 추가)

| # | 결정 | 근거 |
|---|---|---|
| D-135 | P4 scope reframe — Internal Foundation PASS + External Anchor 분리 | novelty 0.127 은 L3 gap_rule 효과로 미션 기여 이미 입증. Stage E 는 skeleton 외부 미탐 해결 |
| D-136 | gap_rule(L3) + exploration_pivot(L5) 상보 관계 (4-계층 스펙트럼) | L3 은 내부 축 증폭, L5 는 외부 쿼리 피벗. 중복 아닌 보완. |
| D-137 | Universe probe → tiered skeleton (candidate vs active) | HITL 루프 지연 회피 + skeleton 오염 방지. active 승격만 HITL-R. |
| D-138 | Exploration pivot 1 cycle 지속 + gap_rule 우선 | core loop 교란 최소화. L3 가 이번 cycle consume 한 경우 L5 skip. |
| D-139 | Semi-front 진입 조건 = Stage E Gate PASS | Stage A~D만으로는 UI 에서 "수렴" 주장이 사용자 기만 |

### 5.7 검증 방법 (Stage E 전용)

- **E7-1 Synthetic Injection**: skeleton 에 없는 fixture 카테고리 삽입 → universe_probe 가 표면화하는지 측정 (ground truth 비교)
- **E7-2 Regression bench**: japan-travel 15c 를 Stage-E-on/off 양쪽 실행 → external_novelty / distinct_domains / candidate 제안 수 비교

### 5.8 Stage E 컨벤션 체크

- [ ] **Gap-driven**: external_novelty 낮음도 gap 의 한 형태로 reason_code 반영
- [ ] **Claim→KU**: candidate skeleton 은 KU 영향 없음 (active 승격 시에만)
- [ ] **Evidence-first**: universe_probe 제안은 broad Tavily evidence validator 통과 필수
- [ ] **Conflict-preserving**: exploration_pivot 은 targets 만 치환, 기존 KU 불변
- [ ] **Prescription-compiled**: critique machine_rule 에 external_novelty 하한 포함
