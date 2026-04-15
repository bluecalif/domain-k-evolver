# Silver P4: Coverage Intelligence — Context
> Last Updated: 2026-04-15
> Status: **Planning**

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
