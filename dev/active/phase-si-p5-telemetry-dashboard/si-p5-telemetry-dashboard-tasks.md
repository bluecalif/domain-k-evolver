# Silver P5: Telemetry Contract & Dashboard — Tasks
> Last Updated: 2026-04-17
> Status: In Progress (6/15)

## Summary

| Stage | Tasks | Done | Status |
|-------|-------|------|--------|
| P5-Prep state.py TypedDict 보완 | 1 | 1 | ✅ 완료 |
| P5-A Telemetry 계약 | 5 | 5 | ✅ 완료 |
| P5-B Dashboard 구현 | 5 | 0 | 대기 (Stage A 완료 후) |
| P5-C 검증 | 4 | 0 | 대기 (Stage B 완료 후) |
| **합계** | **15** | **0** | — |

Size: S:4 / M:9 / L:1 / XL:0

테스트 목표: 797 → ≥ **812** (+15)

---

## Gate 조건 (masterplan §4 P5 verbatim)

- [ ] Telemetry schema 가 emit 데이터를 validate (positive + negative 테스트)
- [ ] Dashboard 가 100-cycle fixture 를 모든 view 에서 **10 s 이내** 로드
- [ ] HITL/dispute/remodel view 가 **실제** telemetry/ledger artifact 소비 (stub 금지)
- [ ] Dashboard LOC ≤ **2,000** (cloc 측정)
- [ ] S10 scenario pass
- [ ] `docs/operator-guide.md` 존재, **5 페이지 이상** walkthrough 포함
- [ ] "왜 진행이 느려졌나" 대시보드만으로 **3분 이내** 식별 (self-test 기록)
- [ ] 테스트 수 ≥ **812** (797 + 15)

---

## Stage Prep: state.py TypedDict 보완

> **[CRITICAL]** Stage A 착수 전 완료 필수 — emit 코드가 state 필드를 읽기 전에 TypedDict 선언 필수

### P5-Prep `src/state.py` EvolverState TypedDict 3 필드 추가 `[S]`

**파일**: `src/state.py`

**배경**: `orchestrator.py`에서 `reach_history`(L251~L252), `probe_history`(L327~L329), `pivot_history`(L347~L354)를 state dict에 직접 write하지만, `EvolverState` TypedDict에 선언되지 않음. P5 emit 코드가 `state.get("reach_history", [])` 등으로 읽기 전에 타입 정합성 확보 필요.

**추가 필드** (`external_observation_keys` 선언 직후, L230 이후):
```python
reach_history: list[dict]     # P4-Stage-E reach targets per cycle
probe_history: list[dict]     # P4-Stage-E universe probe results
pivot_history: list[dict]     # P4-Stage-E exploration pivot records
```

**Cross-check**: 추가 후 `orchestrator.py` 기존 코드(L251, L327, L347)와 key 이름 일치 확인.

- [x] P5-Prep 완료 — commit: `dbefadc`

---

## Stage A: Telemetry 계약

> **[CRITICAL]** Stage B 착수 전 Stage A 전체 merge 완료 필수 (D-77)

### P5-A1 `schemas/telemetry.v1.schema.json` 필수 필드 정의 `[M]`

**파일**: `schemas/telemetry.v1.schema.json` [NEW]

**필수 필드** (코드 실제 상태 기반 — 코드에 없는 필드 제외, context.md §2-B 참조):
```json
{
  "trial_id": str, "phase": str, "cycle": int, "mode": str, "timestamp": str,

  "metrics": {
    "evidence_rate": float, "multi_evidence_rate": float,
    "conflict_rate": float, "avg_confidence": float,
    "gap_resolution_rate": float, "staleness_risk": int,
    "collect_failure_rate": float,
    "novelty": float,          // state["novelty_history"][-1]  ← 추가 emit
    "external_novelty": float, // state["external_novelty_history"][-1]  ← 추가 emit
    "wall_clock_s": float,     // orchestrator time.monotonic() 측정  ← 추가 emit
    "llm_calls": int, "llm_tokens": int,
    "search_calls": int, "fetch_calls": int
  },

  "gaps": {
    "open": int, "resolved": int, "plateau": bool,
    "probe_history_count": int,   // len(state.get("probe_history", []))
    "pivot_history_count": int    // len(state.get("pivot_history", []))
  },

  "failures": [str],

  "audit_summary": {
    "has_critical": bool, "findings_count": int, "last_audit_cycle": int
  },

  "hitl_queue": {"seed": int, "remodel": int, "exception": int},

  "dispute_queue_size": int
}
```

**제외 필드** (코드에 없음 — schema에 넣지 말 것):
`domain_entropy`, `provider_entropy`, `fetch_bytes`, `fetch_failure_rate`, `cost_regression_flag`, `timeout_count`, `retry_success_rate`
→ 상세 사유: context.md §2-B "실제로 없는 값" 표 참조.

**Cross-check**: `metrics_logger.py` L49~L69 현행 key 목록과 field 이름 동기화. `novelty`/`external_novelty`/`wall_clock_s`는 emitter에서 직접 추가 (metrics_logger 확장 or telemetry.py 자체 수집).

- [x] P5-A1 완료 — commit: `e81765e`

---

### P5-A2 `src/obs/telemetry.py` emitter 구현 `[M]`

**파일**: `src/obs/__init__.py` [NEW], `src/obs/telemetry.py` [NEW]

**구현 요건**:
- jsonl append-only (`cycles.jsonl`)
- atomic write: `cycles.jsonl.tmp` → `os.replace` (Windows 호환)
- `emit_cycle(state: EvolverState, trial_id: str, trial_root: Path) -> None`
- 실패 시 warning log + 무시 (telemetry 실패가 cycle을 블로킹하면 안 됨)
- 인코딩: `encoding='utf-8'` 명시

**Cross-check (X4)**: `src/obs/__init__.py` 생성 필수 (Python import).

- [x] P5-A2 완료 — commit: `f6739ce`

---

### P5-A3 `orchestrator.py` 노드 경계 emit hook `[M]`

**파일**: `src/orchestrator.py`

**요건**:
- cycle 루프 끝 단일 call site: `telemetry.emit_cycle(state, trial_id, trial_root)`
- per-node hook은 과설계 — orchestrator 1곳에서만 호출
- `trial_id`, `trial_root`는 `--bench-root` 경로 기반으로 추출 (P0-A4/A5에서 확립된 패턴)
- telemetry 비활성 시 (trial_root 없음) 무시

- [x] P5-A3 완료 — commit: `f6739ce`

---

### P5-A4 출력 경로 설정 `[S]`

**파일**: `src/obs/telemetry.py` (경로 로직)

**요건**:
- Primary: `bench/silver/{domain}/{trial_id}/telemetry/cycles.jsonl`
- 필요 시 `events.jsonl` (per-event 로그, 선택)
- `telemetry/` 디렉토리 없을 시 자동 생성
- trial-card.md 없이 실행 시 경고 (§12.3 규칙 3)

- [x] P5-A4 완료 — commit: `f6739ce` (A2에 포함: mkdir + trial-card 경고)

---

### P5-A5 스키마 계약 테스트 (S10) `[M]`

**파일**: `tests/test_obs/__init__.py` [NEW], `tests/test_obs/test_telemetry_schema.py` [NEW]

**테스트 내용**:
- Positive: emit_cycle 결과가 telemetry.v1 schema validate pass
- Negative: 필수 필드 (`trial_id`, `cycle`, `metrics`) 누락 시 validate fail
- Positive: 100-cycle fixture emit → 모든 행 schema validate pass
- S10 scenario: 1 cycle emit → schema validate pass

**최소 5 개 테스트**.

- [x] P5-A5 완료 — commit: `TBD`

---

**Stage A 완료 체크** (Stage B 착수 전):
- [x] 위 5 tasks 모두 merge 완료
- [x] `tests/test_obs/test_telemetry_schema.py` green (7/7)
- [ ] `bench/silver/japan-travel/*/telemetry/cycles.jsonl` 실 데이터 1개 이상 생성 확인 (trial 재실행 후)

---

## Stage B: Dashboard 구현

> **전제**: Stage A 전체 완료 확인 후 착수

### P5-B1 FastAPI 앱 bootstrap `[M]`

**파일**: `src/obs/dashboard/__init__.py` [NEW], `src/obs/dashboard/app.py` [NEW]

**요건**:
- localhost 바인딩만 (`127.0.0.1`), 인증 없음, 단일 운영자
- `--trial-root` CLI 인자 — 어느 trial 데이터를 보는지 지정
- 기본 라우트 `/` → overview view
- 정적 파일 서빙 (`/static/`)
- htmx 기반 partial update (full-page reload 최소화)

**Cross-check (X4)**: `src/obs/dashboard/__init__.py` 생성 필수.

- [ ] P5-B1 완료 — commit: ___

---

### P5-B2 의존성 추가 `[S]`

**파일**: `pyproject.toml`

**추가 의존성**:
```toml
[project.optional-dependencies]
dashboard = ["fastapi", "uvicorn[standard]", "jinja2"]
```
- `htmx`, `chart.js` 는 CDN 링크 (HTML template에서 직접 참조) — 패키지 추가 불필요
- `duckduckgo-search` 는 P3에서 추가됨 — 여기서는 dashboard extras만

- [ ] P5-B2 완료 — commit: ___

---

### P5-B3 Views 7종 구현 `[L]`

**파일**: `src/obs/dashboard/views/*.py` [NEW], `src/obs/dashboard/templates/*.html` [NEW], `src/obs/dashboard/static/` [NEW]

**Views 목록** (masterplan §4 P5 verbatim, masterplan §14.6 HITL inbox):

| View | 경로 | 핵심 내용 |
|------|------|---------|
| Overview | `/` | 현재 phase/cycle/mode, 주요 메트릭 요약, 이상 경고 |
| Cycle timeline | `/timeline` | novelty/conflict_rate/gap_open/cost 시계열 (Chart.js) |
| Gap coverage map | `/coverage` | axis × bucket 커버리지 히트맵 |
| Source reliability | `/sources` | provider별 `collect_failure_rate` (코드에 있음). `fetch_failure_rate`는 미구현 — **이 view에서 제외**, 대신 `search_calls`/`fetch_calls` 추이 표시 |
| Conflict ledger | `/conflicts` | KU별 충돌 이력 (open/resolved 필터링, ledger_id 검색) |
| HITL inbox | `/hitl` | 탭 3: `[Seed/Remodel 승인]` / `[Dispute 배치 검토]` / `[Exception 알림]` |
| Remodel review | `/remodel` | 제안 목록 (merge/split/reclassify), 승인 상태, rollback_payload |

**LOC 경계**: 구현 중 `cloc src/obs/dashboard` 200 LOC 단위 체크.

- [ ] P5-B3 완료 — commit: ___

---

### P5-B4 실제 artifact 연결 (stub 금지) `[M]`

**파일**: `src/obs/dashboard/app.py` (data loading 로직)

**요건**:
- `bench/silver/{domain}/{trial_id}/telemetry/cycles.jsonl` — 실제 파일 읽기
- `state/conflict_ledger.json` — 실제 파일 읽기
- `state/phase_{N}/remodel_report.json` — 실제 파일 읽기
- hardcoded dummy data / in-memory mock **절대 금지**
- trial 데이터 없으면 "데이터 없음" 메시지 표시 (빈 fixture 생성 금지)

**Cross-check**: P5-C2 실행 전 실 trial cycles.jsonl 존재 확인 필수.

- [ ] P5-B4 완료 — commit: ___

---

### P5-B5 `docs/operator-guide.md` 작성 `[M]`

**파일**: `docs/operator-guide.md` [NEW]

**요건** (masterplan §4 P5, silver-implementation-tasks §9 P5-B5):
- ≤ 20 페이지 (섹션 8~10개 수준)
- 5 페이지 이상 walkthrough 포함 (손으로 따라할 수 있는 시나리오)
- gate 정의 재진술 금지 — canonical artifact 링크 (Cross-check X5)
- "왜 진행이 느려졌나" 진단 시나리오 walkthrough 포함 (P5-C3 self-test 근거)

**구성 제안**:
1. 시작하기 (의존성 설치, 대시보드 실행)
2. Trial 구조 이해 (bench/silver/ 경로 안내)
3. Overview view 읽는 법
4. Cycle timeline 에서 이상 탐지
5. "진행이 느려진 경우" 진단 walkthrough (S10 시나리오)
6. HITL inbox 처리 (Seed/Remodel 승인, Dispute 배치, Exception)
7. Conflict ledger 읽기
8. Remodel review 승인/거부

- [ ] P5-B5 완료 — commit: ___

---

## Stage C: 검증

### P5-C1 schema 계약 재검증 `[S]`

**파일**: `tests/test_obs/test_telemetry_schema.py` (재실행)

- P5-A5 에서 작성한 테스트가 Stage B 통합 후에도 green인지 확인
- B3 views가 emit 경로를 건드리지 않았는지 regression 체크

- [ ] P5-C1 완료 — commit: ___

---

### P5-C2 100-cycle fixture load ≤ 10s `[M]`

**파일**: `tests/test_obs/test_dashboard_load.py` [NEW]

**요건**:
- 100개 cycle 항목을 가진 `cycles.jsonl` fixture 생성 (또는 실 trial 활용)
- 모든 7개 view 의 HTTP 응답이 **10 s 이내** (로컬 기준)
- `pytest --timeout=10` 으로 각 view 엔드포인트 GET 요청 측정

**주의**: fixture 생성 시 실 telemetry schema 준수 필수 (stub 데이터 아닌 valid schema 데이터).

- [ ] P5-C2 완료 — commit: ___

---

### P5-C3 Self-test "slowdown" walkthrough `[M]`

**파일**: `docs/operator-guide.md` (walkthrough 섹션 업데이트)

**요건**:
- "진행이 느려졌나" fixture 시나리오:
  - novelty 급감 (cycle 7~10: novelty < 0.10)
  - collect_failure_rate 상승 (cycle 8~10: > 0.15)
- 운영자가 Overview → Cycle timeline → Source reliability 순서로 3분 내 원인 추적
- 결과를 operator-guide.md 의 walkthrough 섹션에 스크린샷/설명으로 기록

**판정 기준**: 시나리오 fixture 로드 → 3단계 내 원인 식별 가능 여부 (manual 검증).

- [ ] P5-C3 완료 — commit: ___

---

### P5-C4 LOC 하드 리밋 측정 `[S]`

**파일**: `src/obs/dashboard/` (cloc 측정)

**요건**:
- `cloc src/obs/dashboard` 실행 결과 **≤ 2,000 LOC** (Python + HTML + JS 합산)
- 초과 시 scope 컷 전 사용자 확인 필수
- 측정 결과를 `debug-history.md` 에 기록

- [ ] P5-C4 완료 — commit: ___

---

## Cross-phase 제어

- [ ] **X1** Stage C 완료 후 `bench/silver/INDEX.md` 에 P5 trial row 추가 `[S]`
- [ ] **X3** `schemas/telemetry.v1.schema.json` positive + negative 테스트 (P5-A5에 포함) `[S]`
- [ ] **X4** `src/obs/__init__.py`, `src/obs/dashboard/__init__.py`, `tests/test_obs/__init__.py` 생성 확인 `[S]`
- [ ] **X5** `docs/operator-guide.md` 에서 gate 정의 재진술 없음 확인 `[S]`
- [ ] **X6** P5 완료 시 masterplan §8 리스크 레지스터 R4/R10 재평가 `[S]`
