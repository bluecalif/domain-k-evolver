# Silver P5: Telemetry Contract & Dashboard
> Last Updated: 2026-04-17
> Status: Complete (15/15, 814 tests, Gate 판정 대기)

---

## 1. Summary (개요)

**목적**: 운영자가 JSON 파일을 직접 열지 않고도 Evolver 의 실행 상태를 파악하고 개입할 수 있도록,
(1) telemetry 계약(schema + emitter)을 먼저 고정하고
(2) 그 위에 단일 운영자용 FastAPI + htmx 로컬 대시보드를 구축한다.

**핵심 제약 (D-77)**: P5-A (telemetry schema + emit) 완료 전 P5-B (UI) 착수 금지.

**범위**:
- `schemas/telemetry.v1.schema.json` [NEW] — cycle 단위 snapshot 계약
- `src/obs/telemetry.py` [NEW] — jsonl atomic append-only emitter
- `src/obs/dashboard/` [NEW] — FastAPI + htmx + Chart.js 로컬 대시보드
- Views: overview / cycle timeline / gap coverage map / source reliability / conflict ledger / HITL inbox (3탭) / remodel review
- `docs/operator-guide.md` (≤ 20 페이지)

**예상 결과물**:
- `schemas/telemetry.v1.schema.json` — 전 cycle emit 필드 계약
- `src/obs/__init__.py`, `src/obs/telemetry.py`
- `src/obs/dashboard/app.py` + views + templates
- `tests/test_obs/test_telemetry_schema.py` — S10 blocking test
- `tests/test_obs/test_dashboard_load.py` — 100-cycle fixture load
- `docs/operator-guide.md` — 운영자 walkthrough

**단일 진실 소스**: `docs/silver-masterplan-v2.md` §4 P5, `docs/silver-implementation-tasks.md` §9

---

## 2. Current State (현재 상태)

### P4 완료 이후 인계 상태 (2026-04-17)

| 항목 | 상태 |
|------|------|
| 테스트 수 | **797** (Phase 5 468 → Silver P0~P4 누적) |
| `src/obs/` 디렉토리 | **없음** — P5에서 신규 생성 |
| `schemas/telemetry.v1.schema.json` | **없음** — P5-A1에서 신규 생성 |
| `pyproject.toml` dashboard 의존성 | **없음** — P5-B2에서 추가 |
| P0 reliability metrics emit | ✅ `collect_failure_rate` emit 확인 (`timeout_count`/`retry_success_rate`는 실제 코드에 없음 — D-154) |
| P3R provenance 필드 | ✅ `provider`, `domain`, `retrieved_at`, `trust_tier` |
| P4 novelty / reason_code / coverage_map | ✅ `novelty_history`/`external_novelty_history` 선언됨 — emit은 P5-A3에서 추가 |
| P4 external_novelty / reach_ledger | ✅ Stage E에서 완료. `reach_history`/`probe_history`/`pivot_history`는 TypedDict 미선언 — P5-Prep에서 수정 |
| `bench/silver/` telemetry 디렉토리 | ✅ `p0-*` trial에 `telemetry/` 디렉토리 존재 — `cycles.jsonl` 없음 (P5-A3 이후 생성) |
| HITL-S/R/D/E 체제 | ✅ P0에서 전환 완료 |
| dispute_queue state 필드 | ✅ P0-C7에서 추가 |
| conflict_ledger.json | ✅ P1에서 영속화 완료 |
| remodel_report.json | ✅ P2에서 schema 정의 완료 |

### 블로킹 항목 없음
- P0, P3R, P4 모두 완료 — P5 착수 조건 충족
- `docs/silver-implementation-tasks.md` §2 dependency table: P5 시작 조건 = "P0, P3 인터페이스 고정 후 (schema 먼저)"

---

## 3. Target State (목표 상태)

완료 후 달성되어야 할 상태:

- **telemetry.v1 계약 확립**: 모든 cycle emit 데이터가 JSON Schema로 검증 가능
- **운영 관찰성**: 운영자가 대시보드만으로 현재 Phase/cycle/metric 상태 파악 가능
- **HITL 가시화**: HITL inbox 3탭 (Seed/Remodel 승인 / Dispute 배치 검토 / Exception 알림) 실운용
- **장애 진단**: "왜 진행이 느려졌나" 를 대시보드만으로 3분 내 식별 (S10 self-test)
- **스프롤 방지**: dashboard LOC ≤ 2,000 (R4 리스크 완화)
- **테스트 수**: ≥ 812 (797 + 15 P5 신규)

---

## 4. Implementation Stages

### Stage A: Telemetry 계약 (P5-A, 5 tasks)

telemetry schema 정의 → emitter 구현 → orchestrator hook → 출력 경로 → schema 계약 테스트.

**반드시 Stage B 착수 전 merge 완료.**

주요 파일:
- `schemas/telemetry.v1.schema.json` [NEW]
- `src/obs/__init__.py` [NEW], `src/obs/telemetry.py` [NEW]
- `src/orchestrator.py` (cycle emit hook 단일 call site)
- `tests/test_obs/test_telemetry_schema.py` [NEW]

### Stage B: Dashboard 구현 (P5-B, 5 tasks)

FastAPI bootstrap → 의존성 추가 → Views 구현 → 실제 artifact 연결 → 운영자 가이드 작성.

**전제**: Stage A 완료 + P3/P4 interfaces merge 확인.

주요 파일:
- `src/obs/dashboard/__init__.py` [NEW], `app.py` [NEW]
- `src/obs/dashboard/views/*.py` [NEW]
- `src/obs/dashboard/templates/*.html` [NEW]
- `src/obs/dashboard/static/` [NEW]
- `docs/operator-guide.md` [NEW]

### Stage C: 검증 (P5-C, 4 tasks)

schema 재검증 → 100-cycle fixture load ≤ 10s → slowdown self-test → LOC 측정.

---

## 5. Task Breakdown

| Task | 설명 | Size | 의존 |
|------|------|------|------|
| P5-Prep | `src/state.py` EvolverState 3 필드 추가 (`reach_history`, `probe_history`, `pivot_history`) | S | P4 완료 |
| P5-A1 | `schemas/telemetry.v1.schema.json` 필수 필드 정의 (코드 기반, 없는 필드 제외) | M | P5-Prep |
| P5-A2 | `src/obs/telemetry.py` emitter (jsonl atomic write) | M | P5-A1 |
| P5-A3 | `orchestrator.py` 노드 경계 emit hook (단일 call site) | M | P5-A2 |
| P5-A4 | 출력 경로 `bench/silver/{domain}/{trial}/telemetry/cycles.jsonl` | S | P5-A3 |
| P5-A5 | 스키마 계약 테스트 `test_telemetry_schema.py` (positive/negative, S10) | M | P5-A1 |
| P5-B1 | FastAPI 앱 bootstrap (localhost, no auth) | M | Stage A 완료 |
| P5-B2 | 의존성 `fastapi/uvicorn/jinja2/htmx/chart.js` → `pyproject.toml [dashboard]` extras | S | P5-B1 |
| P5-B3 | Views 7종 구현 (masterplan §4 verbatim) | L | P5-B1 |
| P5-B4 | Data source: 실제 artifact 연결 (stub 금지) | M | P5-B3 |
| P5-B5 | `docs/operator-guide.md` 작성 (≤ 20페이지) | M | P5-B3 |
| P5-C1 | schema 계약 재검증 (P5-A5 결과 재확인) | S | P5-A5 |
| P5-C2 | 100-cycle fixture load ≤ 10s `test_dashboard_load.py` | M | P5-B3 |
| P5-C3 | Self-test "slowdown" walkthrough — 3분 내 원인 식별 | M | P5-B5 |
| P5-C4 | LOC 측정: `cloc src/obs/dashboard` ≤ 2,000 | S | P5-B3 |

**합계**: 15 tasks (S: 4, M: 9, L: 1, XL: 0)

---

## 6. Risks & Mitigation

| ID | 리스크 | L | I | 완화 |
|----|--------|---|---|------|
| R4 | 대시보드 스프롤 → LOC 폭발 | M | M | 2,000 LOC 하드 리밋 (cloc 측정), htmx 단일 운영자 범위, 인증/모바일 비범위 |
| R10 | HITL-D dispute_queue 적체 → inbox 과부하 | M | M | dispute_queue > 20 → HITL-E 자동 승격 (P0-C4), 배치 뷰 Day 1 구현 |
| P5-X1 | UI-first 착수로 schema 계약 사후 맞춤 | H | H | D-77 엄수: Stage A merge 전 Stage B PR 금지 |
| P5-X2 | 100-cycle fixture 부재 → 성능 테스트 불가 | M | M | P5-C2 전 `scripts/gen_fixture.py` 작성 (API 미호출 분석 스크립트 — Scripts Policy 허용 범위) |
| P5-X3 | stub 데이터 혼입 | M | M | P5-B4 코드리뷰 필수: `bench/silver/**/telemetry/*.jsonl` 실경로 확인 |
| **P5-X4** | **Schema Drift**: metrics_logger·state·telemetry 값 불일치 → 화면 수치와 실제 불일치 | **H** | **H** | telemetry.py에서 metrics_logger entry를 직접 참조 (재계산 금지). P5-A5 positive test가 실 emit 경로 end-to-end 커버. B3 구현 후 주요 수치 manual cross-check 필수 |

---

## 7. Dependencies

### 내부 (완료된 선행 조건)

| 모듈 | 의존 사유 | 상태 |
|------|----------|------|
| P0 metrics emit | `collect_failure_rate`, `timeout_count`, `retry_success_rate` → telemetry.v1 필드 | ✅ |
| P3R provenance 필드 | `provider`, `domain`, `retrieved_at`, `trust_tier` → telemetry `providers_used` | ✅ |
| P4 novelty / reason_code | `novelty_score`, `overlap_score`, `coverage_deficit` → telemetry metrics | ✅ |
| P4 external_novelty / reach_ledger | `ext_novelty`, `probe_history` → telemetry gaps | ✅ |
| P1 conflict_ledger.json | dashboard Conflict ledger view 데이터 소스 | ✅ |
| P2 remodel_report.json | dashboard Remodel review view 데이터 소스 | ✅ |
| P0 dispute_queue | dashboard HITL inbox Dispute 탭 데이터 소스 | ✅ |

### 외부 (신규 추가)

| 패키지 | 용도 | extras |
|--------|------|--------|
| `fastapi` | API 서버 | `[dashboard]` |
| `uvicorn` | ASGI runner | `[dashboard]` |
| `jinja2` | 템플릿 렌더링 | `[dashboard]` |
| `htmx` | 동적 UI (CDN via HTML) | — |
| `chart.js` | 차트 (CDN via HTML) | — |

### 문서 의존성
- `docs/silver-masterplan-v2.md` §4 P5, §7 S10, §14 (HITL inbox 3탭)
- `docs/silver-implementation-tasks.md` §9
- `bench/silver/japan-travel/*/telemetry/cycles.jsonl` — 실 trial 데이터 (Stage B 착수 전 존재 확인)

---

## 8. Gate (정량 조건)

masterplan §4 P5 verbatim:

- [ ] Telemetry schema 가 emit 데이터를 validate (positive + negative 테스트)
- [ ] Dashboard 가 100-cycle fixture 를 모든 view 에서 **10 s 이내** 로드
- [ ] HITL/dispute/remodel view 가 **실제** telemetry/ledger artifact 소비 (stub 금지)
- [ ] Dashboard LOC ≤ **2,000** (cloc 측정)
- [ ] S10 scenario pass (`tests/test_obs/test_telemetry_schema.py`)
- [ ] `docs/operator-guide.md` 존재, **5 페이지 이상** walkthrough 포함
- [ ] "왜 진행이 느려졌나" 대시보드만으로 **3분 이내** 식별 (self-test 기록)
- [ ] 테스트 수 ≥ **812** (797 + 15)
