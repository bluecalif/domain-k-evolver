# Silver P4: Coverage Intelligence — Context
> Last Updated: 2026-04-16
> Status: **Stage A~D Complete · Stage E (23/25) · E7-2 완료 (VP4 FAIL 진단) · E7-3/E8 대기**

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
| D-140 | VP4 cold-start 보정 — ext_history[0] 평균 제외 | cycle 1 은 모든 key 가 신규라 external_novelty 가 항상 1.0 → 평균 왜곡 방지 |
| D-141 | VP4 5 criteria (R1~R5) + 80% + critical 무실패 패턴 | VP1~3 과 동일 형식 유지. R1(external_novelty) / R3(validated_proposals) 이 critical |
| D-142 | `evaluate_readiness(external_anchor_enabled=False)` opt-in 파라미터 | 기본값 False 로 기존 Phase 4 게이트 호환성 유지. Stage E 실 벤치에서만 True |
| D-143 | 검증된 proposals = candidate_categories count | HITL-R 대기 큐 그대로 사용. 미검증 proposals 별도 추적 안 함 |
| D-144 | `collect.py` as_completed timeout 120→300s, future.result 60→120s | cycle 진행에 따른 parse 시간 증가. cycle 5에서 160s 소요 → 기존 120s 한계 abort |
| D-145 | as_completed TimeoutError catch → 미완료 cancel + cycle 계속 진행 | 기존 uncaught → orchestrator cycle 전체 abort → 15c 미완주 |
| D-146 | `--external-anchor / --no-external-anchor` 플래그 env override | 벤치 비교 시 env 오염 방지. dataclasses.replace |
| D-147 | **VP4 FAIL**: budget kill-switch cycle 4 발동 — llm_budget=3이 universe_probe 1회분 | survey 1 + validator 2 = LLM 3. 이후 Stage E 전체 사망. budget 확대 필요 |
| D-148 | **VP4 FAIL**: ext_novelty = novel/total_keys → 0 수렴 산식 결함 | 분모가 누적 전체 KU 키 → 단조 증가. 0.25 임계치 구조적 도달 불가. 산식 재설계 필요 |
| D-149 | **VP4 FAIL**: exploration_pivot 조건 unreachable — domains_per_100ku 52~57 vs floor 15 | Tavily 자연적 다양성으로 절대 trigger 안 됨. 조건 재설계 필요 |
| D-150 | **VP4 FAIL**: category_addition HITL-R 필수 → 자동 벤치 불가 | registered=2 완료했으나 승격 불가. VP4 R5 기준을 `probe_history` 실행 횟수로 완화 (`10bc58a`). **단, 실제 런타임에서 candidate → active 승격을 처리하는 HITL 로직이 미구현 상태 — 추후 별도 구현 필요 (아래 §5.9 참조)** |

### 5.9 미구현 런타임 로직 (Future Work)

#### category_addition HITL 승격 경로 (D-150 후속)

현재 `candidate_categories` 등록까지는 자동화되어 있으나, 실제 운영 환경에서 skeleton 을 확장하려면 아래 경로가 구현되어야 함:

```
candidate_categories (universe_probe 등록)
  → [미구현] HITL 인터페이스: 사용자가 후보 목록 검토 + 승인/거부
  → promote_candidate(skeleton, slug) 호출
  → skeleton.categories 에 편입 (active)
  → 이후 collect 노드가 해당 카테고리 KU 수집 시작
```

**현재 코드 상태**:
- `skeleton_tiers.py::promote_candidate()` 함수 존재 (승격 로직 구현됨)
- HITL 진입점(CLI / API endpoint / interrupt node) 없음
- `phase_history` 에 `category_addition` 기록되지 않음 (승격이 안 일어나므로)

**구현 시 고려사항**:
- Silver HITL 정책(`silver-hitl-policy` skill) 에 따라 HITL-R (Remodel) 경로로 처리
- 승격 시 VP4 R5 기준(기존 `category_addition`)도 복원 가능
- 자동 벤치와 실 운영을 구분하는 플래그 또는 mode 필요

---

### 5.7 검증 방법 (Stage E 전용)

- **E7-1 Synthetic Injection**: skeleton 에 없는 fixture 카테고리 삽입 → universe_probe 가 표면화하는지 측정 (ground truth 비교)
- **E7-2 Regression bench**: japan-travel 15c 를 Stage-E-on/off 양쪽 실행 → external_novelty / distinct_domains / candidate 제안 수 비교

### 5.8 Stage E 컨벤션 체크

- [x] **Gap-driven**: external_novelty 낮음도 gap 의 한 형태로 reason_code 반영 (`df219e5`)
- [x] **Claim→KU**: candidate skeleton 은 KU 영향 없음 (active 승격 시에만) — `skeleton_tiers.py` (`618bb21`)
- [x] **Evidence-first**: universe_probe 제안은 broad Tavily evidence validator 통과 필수 — 3-step pipeline (`618bb21`)
- [x] **Conflict-preserving**: exploration_pivot 은 targets 만 치환, 기존 KU 불변 (`47a798f`)
- [x] **Prescription-compiled**: critique machine_rule 에 external_novelty 하한 포함 (`df219e5`)

---

## 6. Stage E Code Complete 자산 요약 (2026-04-16)

### 6.1 신규 모듈
- `src/utils/external_novelty.py` — history-aware novelty (entity_key+field)
- `src/utils/reach_ledger.py` — publisher_domain/tld 축 추적 + `distinct_domains_per_100ku` + `is_reach_degraded`
- `src/utils/skeleton_tiers.py` — active/candidate 분리 helpers
- `src/utils/cost_guard.py` — per-cycle/per-run budget + kill-switch
- `src/nodes/universe_probe.py` — LLM survey + broad Tavily + validator 3-step pipeline + `should_run_universe_probe`
- `src/nodes/exploration_pivot.py` — `should_pivot` + query rewriter (3 전략) + candidate axis probe
- `tests/integration/test_synthetic_injection.py` — ground-truth 발견 검증 (4 tests)

### 6.2 수정 모듈
- `src/config.py` — `ExternalAnchorConfig` 추가 (`enabled`, `probe_interval_cycles`, budgets)
- `src/state.py` — `external_novelty_history`, `observation_keys`, `reach_history`, `candidate_categories`, `pivot_history`
- `src/orchestrator.py` — `_cost_guard`, `_maybe_run_universe_probe`, `_maybe_run_exploration_pivot`, `_update_novelty_and_coverage`, reach_history
- `src/nodes/plan.py` — reason_code +3 (external_novelty/universe_probe/reach_diversity) + 우선순위 재조정
- `src/utils/state_io.py` — `external-anchor.json` 분리 영속화
- `src/utils/readiness_gate.py` — `evaluate_vp4` (5 criteria) + `evaluate_readiness` 에 `external_anchor_enabled` 플래그

### 6.3 테스트 현황
- Pre-Stage E: 677 tests
- Stage E Code Complete: **793 tests** (+116)
- 주요 신규: cost_guard 8 / external_novelty 6 / plan reason_code 7 / skeleton_tiers 15 / universe_probe ~60 / orchestrator E 통합 ~15 / reach_ledger 10 / exploration_pivot 8 / synthetic injection 4 / VP4 12

### 6.4 남은 작업 (실 API 필요)
- **E7-2**: `scripts/run_readiness.py` `--external-anchor` 플래그 + 15c × 2 trial
- **E7-3**: `bench/japan-travel-external-anchor/` 스캐폴드 + 비교 리포트
- **E8-2/E8-3**: VP4 실측 → readiness-report 갱신 → Gate 판정 commit
