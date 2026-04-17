# Silver P5: Telemetry Contract & Dashboard — Context
> Last Updated: 2026-04-17
> Status: Complete

---

## 1. 핵심 파일

### 이 Phase에서 읽어야 할 기존 파일

#### 설계 참조
| 파일 | 참조 이유 |
|------|----------|
| `docs/silver-masterplan-v2.md` §4 P5, §7 S10, §14.6 | Gate 정량 조건 · S10 blocking test · HITL inbox 3탭 구조 |
| `docs/silver-implementation-tasks.md` §9 | task 상세 + touched files |

#### Orchestrator / 상태 관리 (emit hook 삽입 위치)
| 파일 | P5 관련성 |
|------|----------|
| `src/orchestrator.py` | cycle 루프 구조 (L114~L192), `_update_novelty_and_coverage` (L225~L267), `_domain_path` 속성, `_cost_guard`, `self.logger.entries` |
| `src/utils/metrics_logger.py` | 현재 emit 키 전체 목록 (하단 §2 참조) — telemetry.v1 필드와 동기화 필수 |
| `src/utils/metrics_guard.py` | `should_auto_pause` 5개 조건 (하단 §2 참조) — HITL-E 연결 |
| `src/state.py` | EvolverState TypedDict — P5 착수 전 누락 필드 3개 추가 필요 (§2 참조) |
| `src/config.py` | `OrchestratorConfig.bench_root` 경로 처리 방식, `ExternalAnchorConfig` |

#### P4 Stage E 신규 파일 (telemetry 필드 소스)
| 파일 | telemetry 관련 값 |
|------|----------------|
| `src/utils/novelty.py` | `novelty_history[-1]` → telemetry metrics.novelty |
| `src/utils/external_novelty.py` | `external_novelty_history[-1]` → telemetry metrics.external_novelty |
| `src/utils/reach_ledger.py` | `reach_history[-1]` → telemetry gaps (domains_per_100ku) |
| `src/utils/cost_guard.py` | `CostGuard._killed` → telemetry failures 참고 |
| `src/nodes/universe_probe.py` | `probe_history` — state에 누적 (TypedDict 미선언) |
| `src/nodes/exploration_pivot.py` | `pivot_history` — state에 누적 (TypedDict 미선언) |

#### P0~P4 결과물 (Dashboard 데이터 소스)
| 파일/경로 | Dashboard view |
|----------|---------------|
| `bench/silver/{domain}/{trial_id}/telemetry/cycles.jsonl` | 모든 view (P5에서 생성) |
| `bench/silver/{domain}/{trial_id}/trajectory/trajectory.json` | Cycle timeline 보조 |
| `bench/silver/{domain}/{trial_id}/state/conflict_ledger.json` | Conflict ledger view |
| `bench/silver/{domain}/{trial_id}/state/phase_{N}/remodel_report.json` | Remodel review view |
| `src/state.py dispute_queue` | HITL inbox Dispute 탭 |

#### 참조 스키마
| 파일 | 참조 이유 |
|------|----------|
| `schemas/knowledge-unit.json` | telemetry gaps.open/resolved 항목 구조 |
| `schemas/remodel_report.schema.json` | Remodel review view 데이터 형식 |

---

## 2. 데이터 인터페이스

### 현재 코드 상태 vs P5 요구 — 정확한 현황

#### 2-A. state.py EvolverState TypedDict 현황 (2026-04-17)

P5 착수 전 수정 필요:

| 필드 | TypedDict 선언 | orchestrator 사용 | 조치 |
|------|--------------|----------------|------|
| `dispute_queue` | ✅ 선언됨 (L220) | ✅ | — |
| `conflict_ledger` | ✅ 선언됨 (L223) | ✅ | — |
| `phase_number` | ✅ 선언됨 (L224) | ✅ | — |
| `phase_history` | ✅ 선언됨 (L225) | ✅ | — |
| `remodel_report` | ✅ 선언됨 (L226) | ✅ | — |
| `coverage_map` | ✅ 선언됨 (L227) | ✅ | — |
| `novelty_history` | ✅ 선언됨 (L228) | ✅ | — |
| `external_novelty_history` | ✅ 선언됨 (L229) | ✅ | — |
| `external_observation_keys` | ✅ 선언됨 (L230) | ✅ | — |
| **`reach_history`** | ❌ 미선언 | orchestrator L251~L252 | **P5-Prep 추가 필수** |
| **`probe_history`** | ❌ 미선언 | orchestrator L327~L329 | **P5-Prep 추가 필수** |
| **`pivot_history`** | ❌ 미선언 | orchestrator L347~L354 | **P5-Prep 추가 필수** |

#### 2-B. metrics_logger.py 현행 emit 키 (실제 코드 L49~L69)

```python
entry = {
    "cycle": int,
    "ku_total": int,   "ku_active": int,   "ku_disputed": int,
    "gu_total": int,   "gu_open": int,     "gu_resolved": int,
    "evidence_rate": float,   "multi_evidence_rate": float,
    "conflict_rate": float,   "avg_confidence": float,
    "gap_resolution_rate": float,   "staleness_risk": int,
    "mode": str,
    "collect_failure_rate": float,   # state["collect_failure_rate"]에서
    "llm_calls": int,   "llm_tokens": int,
    "search_calls": int,   "fetch_calls": int,
}
```

**P5-A1/A3에서 추가 emit 필요한 값** (현재 metrics_logger에 없음):
- `novelty` — `state["novelty_history"][-1]` (orchestrator L231~L233)
- `external_novelty` — `state["external_novelty_history"][-1]` (orchestrator L243~L244)
- `wall_clock_s` — orchestrator cycle 루프에서 `time.monotonic()` 측정 가능
- `probe_history_count` — `len(state.get("probe_history", []))` (state TypedDict 추가 후)
- `pivot_history_count` — `len(state.get("pivot_history", []))` (state TypedDict 추가 후)
- `dispute_queue_size` — `len(state.get("dispute_queue", []))`

**실제로 없는 값** (dev-docs 초안에서 잘못 가정):

| 필드 | 실제 상태 | 처리 방안 |
|------|---------|---------|
| `timeout_count` | metrics_logger 없음 | telemetry schema에서 제외 또는 collect.py 확장 |
| `retry_success_rate` | metrics_logger 없음 | telemetry schema에서 제외 |
| `domain_entropy` | P3R 이후 제거됨 (D-124), SearchConfig에 entropy_floor만 남음 | telemetry schema에서 제외 |
| `provider_entropy` | 단일 Tavily provider, emit 없음 | telemetry schema에서 제외 |
| `fetch_bytes` | metrics_logger 없음 | telemetry schema에서 제외 |
| `fetch_failure_rate` | metrics_logger 없음 (`collect_failure_rate`만 있음) | telemetry schema에서 제외 |
| `cost_regression_flag` | CostGuard._killed 내부 flag, state에 저장 안 됨 | telemetry failures[]로 표현 |

#### 2-C. metrics_guard.should_auto_pause 실제 5개 조건 (L79~L138)

```python
AUTO_PAUSE_THRESHOLDS = {
    "conflict_rate_max": 0.25,
    "evidence_rate_min": 0.55,
    "collect_failure_rate_max": 0.50,
    "staleness_ratio_max": 0.30,
    "avg_confidence_min": 0.60,
}
```

> **dev-docs 초안 수정**: `cost_regression_flag`, `fetch_failure_rate > 0.5`, `dispute_queue > 20` 조건은 코드에 없음. 실제 5개 조건으로 교체.

#### 2-D. bench/silver trial 실제 구조 (2026-04-17 확인)

```
bench/silver/japan-travel/p0-20260412-baseline/
├── trial-card.md
├── readiness-report.md
├── readiness-report.json
├── config.snapshot.json
├── state/
├── state-snapshots/
├── trajectory/
│   ├── trajectory.json
│   └── trajectory.csv
└── telemetry/             ← 디렉토리 있으나 cycles.jsonl 없음 (P5에서 생성)
```

→ **bench/silver/** 구조는 이미 존재. telemetry/ 디렉토리도 scaffold됨. **cycles.jsonl만 없음**.

### Telemetry Emit 흐름 (P5 목표)

```
orchestrator.py (cycle 루프 끝, L167 _post_cycle 전후)
    → src/obs/telemetry.py::emit_cycle(state, trial_root, cycle_elapsed_s)
    → bench/silver/{domain}/{trial_id}/telemetry/cycles.jsonl
       (jsonl append-only, atomic tmp→rename)
```

### Telemetry Schema 필드 (P5-A1 실제 코드 기반)

```json
{
  "trial_id": "p5-20260417-...",
  "phase": "si-p5",
  "cycle": 3,
  "mode": "explore",
  "timestamp": "2026-04-17T...",

  "metrics": {
    "evidence_rate": 0.97,
    "multi_evidence_rate": 0.61,
    "conflict_rate": 0.03,
    "avg_confidence": 0.85,
    "gap_resolution_rate": 0.88,
    "staleness_risk": 0,
    "collect_failure_rate": 0.04,
    "novelty": 0.31,
    "external_novelty": 0.44,
    "wall_clock_s": 38.2,
    "llm_calls": 23,
    "llm_tokens": 45000,
    "search_calls": 8,
    "fetch_calls": 0
  },

  "gaps": {
    "open": 12,
    "resolved": 8,
    "plateau": false,
    "probe_history_count": 2,
    "pivot_history_count": 0
  },

  "failures": [],

  "audit_summary": {
    "has_critical": false,
    "findings_count": 0,
    "last_audit_cycle": 5
  },

  "hitl_queue": {
    "seed": 0,
    "remodel": 0,
    "exception": 0
  },

  "dispute_queue_size": 0
}
```

> `domain_entropy`, `provider_entropy`, `fetch_bytes`, `fetch_failure_rate`, `cost_regression_flag`는 **코드에 없으므로 스키마에서 제외**.

### trial_id 추출 로직 (P5-A3 구현 시 주의)

```python
# orchestrator._domain_path 기반
trial_root = self._domain_path  # bench_root 설정 시 직접 경로
# trial_id는 Path의 마지막 component
trial_id = trial_root.name  # 예: "p5-20260417-telemetry-v1"
```

---

## 3. 주요 결정사항

### 확정된 결정 (masterplan + 코드 반영)

| # | 결정 | 근거 | 코드 위치 |
|---|------|------|---------|
| D-77 | P5-A (telemetry schema) 가 P5-B (UI) 엄격 선행 | v1 UI-first 실패 재발 방지 | masterplan §11 |
| D-79 | Silver 완료 테스트 목표 ≥ 588. P5 목표 797+15=812 | silver-implementation-tasks §14 | — |
| R4 | Dashboard LOC ≤ 2,000 하드 리밋 | masterplan §8 R4 | cloc src/obs/dashboard |
| D-124 | provider_entropy 메트릭 제거 (Tavily 단일) | P3R 결정 | SearchConfig에 없음 |
| D-148 | ext_novelty 분모 = delta_kus (전체 KU 아닌 신규 KU) | 0 수렴 방지 | orchestrator L235 |

### P5에서 결정해야 할 항목

| # | 결정 대상 | 권장 방향 | 근거 |
|---|----------|---------|------|
| D-151 | telemetry schema 버저닝 | `telemetry.v1` 고정, v2는 별도 파일 | Silver 범위 내 변경 없음 |
| **D-152** | **Dashboard 실행 방식** | **`run_readiness.py --serve-dashboard` 플래그 추가** | CLAUDE.md Scripts Policy — 신규 실행 스크립트 금지. 별도 `run_dashboard.py` 불가. `run_readiness.py` 옵션으로 확장 |
| D-153 | 100-cycle fixture 생성 | 실 trial 데이터 우선. 부족 시 `scripts/gen_fixture.py` 허용 (API 미호출 분석 스크립트 — Scripts Policy 허용 범위) | stub 금지 원칙 |
| D-154 | timeout_count/retry_success_rate emit | telemetry schema에서 제외 (현재 코드 없음). Gold에서 추가 | P0 가정값이었으나 미구현 |

---

## 4. 컨벤션 체크리스트

### P5 착수 전 체크 (코드 상태 기반)

- [ ] **state.py** `reach_history`, `probe_history`, `pivot_history` 3 필드 TypedDict 추가 완료 (P5-Prep)
- [ ] `bench/silver/{trial_id}/telemetry/` 디렉토리 존재 확인 (p0-20260412-baseline에 확인됨 ✅)

### 5대 불변원칙 (P5 관련성)

| 원칙 | P5 관련 체크 |
|------|------------|
| Gap-driven | telemetry `gaps.open` 카운트가 실 GU open 수와 정합 |
| Claim→KU 착지성 | dashboard에서 KU 변화가 cycle별로 추적 가능 |
| Evidence-first | `metrics.evidence_rate` ≥ 0.95 위반 시 dashboard 경고 표시 |
| Conflict-preserving | Conflict ledger view가 resolved KU도 삭제 없이 표시 (append-only) |
| Prescription-compiled | HITL inbox Remodel 탭이 remodel_report proposals 표시 |

### Metrics 임계치 (dashboard 경고 기준 — metrics_guard 코드 기반)

| 지표 | 건강 | HITL-E 트리거 임계치 |
|------|------|---------------------|
| evidence_rate | ≥ 0.95 | < 0.55 (AUTO_PAUSE_THRESHOLDS) |
| conflict_rate | ≤ 0.05 | > 0.25 |
| collect_failure_rate | ≤ 0.10 | > 0.50 |
| staleness_ratio | — | > 0.30 |
| avg_confidence | ≥ 0.85 | < 0.60 |

### Silver Blocking Scenario

| ID | 시나리오 | 테스트 파일 |
|----|----------|----------|
| S10 | 1 cycle emit → telemetry.v1 schema validate pass | `tests/test_obs/test_telemetry_schema.py` |

### 인코딩
- jsonl 파일: `encoding='utf-8'` 명시
- atomic write: `cycles.jsonl.tmp` → `os.replace()` (Windows 호환)
- dashboard HTML: `<meta charset="utf-8">` 명시

### 코드 컨벤션
- `src/obs/` — 관찰성 전용 모듈, 비즈니스 로직 의존 금지
- telemetry emitter — orchestrator에서 단일 call site (per-node hook 과설계)
- dashboard — read-only viewer, state 직접 수정 기능 없음
- LOC 측정: 200 LOC 단위로 모니터링

### HITL 의미론적 경계 (P5-B3 구현 시 필수 — 혼용 금지)

| 개념 | 의미 | 데이터 소스 | Dashboard view |
|------|------|-----------|---------------|
| `conflict_ledger` | **이력 기록** — 충돌 발생·해소 모두 영속 보관, 삭제 없음 | `state/conflict_ledger.json` | Conflict ledger |
| `dispute_queue` | **처리 대기 묶음** — 아직 해결되지 않은 dispute 목록 | state 필드 (memory) | HITL inbox Dispute 탭 |
| `remodel_report` | **구조 변경 제안서** — merge/split/reclassify 제안 + rollback_payload | `state/phase_{N}/remodel_report.json` | Remodel review / HITL inbox Remodel 탭 |
| HITL exception | **즉시 개입 경고** — auto-pause 조건 충족 시 발생 | metrics_guard `should_auto_pause` 결과 | HITL inbox Exception 탭 |

> **규칙**: 위 4가지는 화면에서 반드시 분리 표시. 뭉뚱그리면 운영자가 오해함 (예: ledger를 pending으로 착각, dispute를 exception으로 혼동).

### Stage B 착수 전 체크리스트 (D-77)

- [ ] `schemas/telemetry.v1.schema.json` merge 완료
- [ ] `src/obs/telemetry.py` merge 완료
- [ ] `orchestrator.py` emit hook merge 완료
- [ ] `tests/test_obs/test_telemetry_schema.py` green
- [ ] `bench/silver/japan-travel/*/telemetry/cycles.jsonl` 실 데이터 1개 이상 존재 (trial 재실행으로 생성)
