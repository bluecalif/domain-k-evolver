# Silver P5: Telemetry Contract & Dashboard — Context
> Last Updated: 2026-04-17
> Status: Planning

---

## 1. 핵심 파일

### 이 Phase에서 읽어야 할 기존 파일

#### 설계 참조
| 파일 | 참조 이유 |
|------|----------|
| `docs/silver-masterplan-v2.md` §4 P5 | Gate 정량 조건 (단일 진실 소스) |
| `docs/silver-masterplan-v2.md` §7 S10 | blocking scenario 정의 |
| `docs/silver-masterplan-v2.md` §14.4 / §14.6 | HITL inbox 3탭 구조 (Seed/Remodel·Dispute·Exception) |
| `docs/silver-implementation-tasks.md` §9 | task 상세 + touched files |

#### 의존 구현 파일 (읽기 전용)
| 파일 | P5 관련성 |
|------|----------|
| `src/orchestrator.py` | emit hook 단일 call site 추가 위치 |
| `src/utils/metrics_logger.py` | 기존 metrics key 목록 — telemetry.v1 필드와 동기화 |
| `src/utils/metrics_guard.py` | cost_regression_flag, dispute_queue_size → telemetry `failures` 필드 |
| `src/utils/readiness_gate.py` | VP1/VP2/VP3 판정 로직 — gate 결과를 telemetry에 포함 여부 확인 |
| `src/state.py` | `dispute_queue`, `conflict_ledger`, `phase_history`, `coverage_map`, `novelty_history` 필드 |
| `src/nodes/hitl_gate.py` | HITL-S/R/E 케이스 — inbox 탭 구조와 매핑 |
| `src/utils/novelty.py` | novelty_score 계산 — telemetry metrics에 포함 |
| `src/utils/coverage_map.py` | coverage_deficit — telemetry gaps에 포함 |
| `src/utils/external_novelty.py` | ext_novelty — telemetry 필드 후보 |
| `src/utils/reach_ledger.py` | probe_history — telemetry gaps에 포함 |
| `src/nodes/collect.py` | collect_failure_rate, providers_used — P0에서 emit, telemetry에 포함 |

#### 데이터 소스 파일 (Dashboard에서 읽는 artifact)
| 파일/경로 | Dashboard view |
|----------|---------------|
| `bench/silver/{domain}/{trial_id}/telemetry/cycles.jsonl` | 모든 view |
| `bench/silver/{domain}/{trial_id}/state/conflict_ledger.json` | Conflict ledger view |
| `bench/silver/{domain}/{trial_id}/state/phase_{N}/remodel_report.json` | Remodel review view |
| `src/state.py` dispute_queue | HITL inbox Dispute 탭 |

#### 스키마 참조
| 파일 | 참조 이유 |
|------|----------|
| `schemas/knowledge-unit.json` | telemetry의 gaps.open/resolved 항목 구조 |
| `schemas/remodel_report.schema.json` | Remodel review view 데이터 형식 |

---

## 2. 데이터 인터페이스

### Telemetry Emit 흐름

```
orchestrator.py (cycle 루프 끝)
    → src/obs/telemetry.py::emit_cycle(state, trial_id)
    → bench/silver/{domain}/{trial_id}/telemetry/cycles.jsonl
       (jsonl append-only, atomic tmp→rename)
```

### Telemetry Schema 필드 (P5-A1 정의 기준)

```json
{
  "trial_id": "p5-20260417-telemetry-v1",
  "phase": "si-p5",
  "cycle": 3,
  "mode": "explore",
  "timestamp": "2026-04-17T...",
  "metrics": {
    "evidence_rate": 0.97,
    "conflict_rate": 0.03,
    "novelty": 0.31,
    "overlap": 0.12,
    "domain_entropy": 2.8,
    "provider_entropy": 1.0,
    "llm_tokens": 45000,
    "fetch_bytes": 2400000,
    "wall_clock_s": 38.2,
    "collect_failure_rate": 0.04,
    "fetch_failure_rate": 0.07,
    "cost_regression_flag": false
  },
  "gaps": {
    "open": 12,
    "resolved": 8,
    "plateau": false,
    "ext_novelty": 0.44,
    "probe_history_count": 2
  },
  "failures": [],
  "providers_used": ["tavily"],
  "audit_summary": {"has_critical": false, "findings": []},
  "hitl_queue": {
    "seed": 0,
    "remodel": 0,
    "exception": 0
  },
  "dispute_queue": []
}
```

> **주의**: `metrics_logger.py` key 목록과 반드시 동기화. 신규 key 추가 시 telemetry schema도 갱신.

### Dashboard 데이터 읽기 흐름

```
FastAPI app
    → bench/silver/{domain}/{trial_id}/telemetry/cycles.jsonl  (primary)
    → state/conflict_ledger.json                               (Conflict ledger view)
    → state/phase_{N}/remodel_report.json                      (Remodel review view)
    → state.dispute_queue (직접 state 파일)                     (HITL inbox Dispute 탭)
```

### Dashboard Views 목록 (masterplan §4 verbatim)

| View | 데이터 소스 | 핵심 기능 |
|------|------------|---------|
| Overview | cycles.jsonl | 현재 phase/cycle/mode/주요 메트릭 1장 요약 |
| Cycle timeline | cycles.jsonl | novelty/conflict_rate/gap_open 시계열 차트 |
| Gap coverage map | cycles.jsonl `.gaps` | axis × bucket 커버리지 히트맵 |
| Source reliability | cycles.jsonl `.metrics` | provider별 collect_failure_rate / fetch_failure_rate |
| Conflict ledger | conflict_ledger.json | KU별 충돌 이력 (open/resolved 필터) |
| HITL inbox (3탭) | hitl_queue + dispute_queue | [Seed/Remodel 승인] / [Dispute 배치 검토] / [Exception 알림] |
| Remodel review | remodel_report.json | 제안 목록 + 승인/거부 상태 |

---

## 3. 주요 결정사항

### 확정된 결정 (masterplan 기반)

| # | 결정 | 근거 |
|---|------|------|
| D-77 | P5-A (telemetry schema) 가 P5-B (UI) 엄격 선행 | v1 UI-first 실패 재발 방지 — masterplan §11 |
| D-79 | Silver 완료 테스트 목표 ≥ 588. P5 목표 797+15=812 | silver-implementation-tasks §14 |
| R4 | Dashboard LOC ≤ 2,000 하드 리밋 | 스프롤 방지 — masterplan §8 R4 |
| R10 | dispute_queue > 20 → HITL-E 자동 승격 | P0-C4 should_auto_pause 조건 |

### P5에서 결정해야 할 항목

| # | 결정 대상 | 옵션 | 비고 |
|---|----------|------|------|
| D-151 후보 | telemetry schema 버저닝 정책 | `telemetry.v1` 고정 vs 마이너 버전 | 일단 v1 고정, v2 필요 시 별도 schema 파일 |
| D-152 후보 | Dashboard 실행 방식 | `uvicorn src/obs/dashboard/app.py` vs scripts/run_dashboard.py | scripts 정책상 run_readiness.py --dashboard 옵션 가능 |
| D-153 후보 | 100-cycle fixture 생성 | scripts/gen_fixture.py 신규 vs 실 trial 데이터 활용 | 실 trial 선호 (P5-B4 stub 금지 원칙) |

> **D-152 주의**: CLAUDE.md Scripts Policy — 새 실행 스크립트 금지, 옵션/플래그로 확장. `run_readiness.py --serve-dashboard` 형태로 통합하거나 `src/obs/dashboard/app.py` 를 직접 uvicorn으로 실행하는 방식 선택.

---

## 4. 컨벤션 체크리스트

### 5대 불변원칙 (P5 관련성)

| 원칙 | P5 관련 체크 |
|------|------------|
| Gap-driven | telemetry `gaps.open` 카운트가 coverage_map 기반 GU 목록과 정합 |
| Claim→KU 착지성 | dashboard에서 KU 수 변화가 cycle별로 추적 가능 |
| Evidence-first | telemetry `metrics.evidence_rate` ≥ 0.95 임계치 위반 시 dashboard 경고 표시 |
| Conflict-preserving | Conflict ledger view가 resolved KU도 삭제 없이 표시 |
| Prescription-compiled | HITL inbox Remodel 탭이 remodel_report.json 의 proposal을 표시 |

### Metrics 건강 임계치 (dashboard 경고 기준)

| 지표 | 건강 | 주의 표시 | 위험 표시 |
|------|------|----------|---------|
| 근거율 | ≥ 0.95 | 0.80–0.94 | < 0.80 |
| 다중근거율 | ≥ 0.50 | 0.30–0.49 | < 0.30 |
| 충돌률 | ≤ 0.05 | 0.06–0.15 | > 0.15 |
| collect_failure_rate | ≤ 0.10 | 0.10–0.30 | > 0.30 (HITL-E) |
| fetch_failure_rate | ≤ 0.20 | 0.20–0.50 | > 0.50 (HITL-E) |
| novelty_avg | ≥ 0.25 | 0.10–0.24 | < 0.10 (plateau) |

### Silver Blocking Scenario

| ID | 시나리오 | 관련 Phase |
|----|----------|----------|
| S10 | dashboard telemetry 1 cycle → schema validate pass | **P5 (이 Phase)** |

### 인코딩
- jsonl 파일: `encoding='utf-8'` 명시
- telemetry.py atomic write: `*.jsonl.tmp` → rename (Windows에서는 `os.replace` 사용)
- dashboard HTML templates: `charset=utf-8` 명시

### 코드 컨벤션
- `src/obs/` 는 관찰성 전용 모듈 — 비즈니스 로직 (cycle, plan 등) 의존 금지
- telemetry emitter는 orchestrator에서 단일 call site (per-node hook은 과설계)
- dashboard는 read-only viewer — state 직접 수정 기능 없음
- LOC 측정: `cloc src/obs/dashboard` — 200 LOC 단위로 진행 상황 모니터링

### Stage B 착수 전 체크리스트 (D-77)

- [ ] `schemas/telemetry.v1.schema.json` merge 완료
- [ ] `src/obs/telemetry.py` merge 완료
- [ ] `orchestrator.py` emit hook merge 완료
- [ ] `tests/test_obs/test_telemetry_schema.py` green
- [ ] `bench/silver/japan-travel/*/telemetry/cycles.jsonl` 실 데이터 1개 이상 존재
