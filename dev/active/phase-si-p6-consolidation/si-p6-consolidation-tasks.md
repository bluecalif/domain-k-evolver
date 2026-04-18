# Silver P6: Consolidation & Knowledge DB Release — Tasks
> Last Updated: 2026-04-18 (rev: B1 선행 실행 결정 — A1-D3 15c bench 전 배치 최적화 먼저)
> Status: In Progress (1/23)

## Summary

| Stage | Tasks | Done | Status |
|-------|-------|------|--------|
| **P6-B1 (선행)** | **1** | **0** | **진행 중 (A1-D3 bench 전 최적화 우선)** |
| P6-A Inside (KU saturation) | 4 (A1~A4) | 1 | 진행 중 |
| **P6-A1-Diag (진단 로깅 → root cause 확정)** | **3 (D1~D3)** | **2** | **D3 대기 (B1 완료 후)** |
| P6-A Outside (Stage E 보강) | 2 (A5~A6) | 0 | 대기 |
| **P6-A Forecastability (F-Gate)** | **5 (A7~A11)** | **0** | **대기 (신규, D-158)** |
| P6-A Gate (50c trial) | 2 (A12~A13) | 0 | 대기 |
| P6-B Performance | 3 (B1~B3) | 0 | 대기 |
| P6-C KB Release | 4 (C1~C4) | 0 | 대기 |
| **합계** | **23** | **1** | — |

> **실행 순서 변경**: P6-B1 (LLM batch) → A1-D3 smoke 재실행 → A1-D3 15c full bench → A2~A4

Size: S:8 / M:13 / L:2 / XL:0

테스트 목표: 821 (현재) → ≥ **840** (+19 예상)

---

## Gate 조건 (P6-A F-Gate / P6-A Gate / P6-B / P6-C)

### P6-A F-Gate (A12 50c 선행, D-158) — 신규

- [ ] A1~A10 반영 완료 + 821 tests green 유지
- [ ] stage-e-on 15c rerun 실행 (A11, ~$1) — API 비용 사전 확인 필수
- [ ] **Smart Remodel ≥ 2회 실발동** 관측 (trigger_event 로그)
- [ ] **Exploration Pivot ≥ 1회 실발동** 관측 (임계값 완화 실험 포함, forecast는 원복된 기준)
- [ ] forecast 산출: **c16-c50 Remodel ≥ 4회 + Pivot ≥ 2회** 예측 + **confidence ≥ 0.6**
- [ ] 미달 시 A2~A6 재설계 루프 (A12 진행 차단)

### P6-A Gate (A12 이후)

- [ ] stage-e-on 50c trial: **KU ≥ 250**
- [ ] stage-e-on 50c trial: **gap_resolution ≥ 0.85**
- [ ] collision_active 반복 없음 (A5 효과 확인)
- [ ] Exploration pivot 실발동 1회 이상 (A11 forecast 검증)
- [ ] COMPARISON-v2.md 작성 완료 (A13) — forecast vs 실측 오차 포함

### P6-B Gate

- [ ] LLM batch 도입 후 wall_clock ≥ 10% 개선 측정값 기록
- [ ] state_io delta write로 cycle 저장 성능 개선 확인

### P6-C Gate

- [ ] `evolver-kb-japan-travel` 외부 import e2e PASS
- [ ] KU lookup query API 동작 확인
- [ ] operator-guide §9 외부 사용자 섹션 추가 완료

---

## Stage A-Inside: KU Saturation 해소

> **선행**: A1 root cause 확인 → A2~A4 scope 최종 결정

### P6-A1 KU saturation 진단 `[M]`

**목표**: c11-15 정체의 root cause를 데이터로 특정

**분석 항목**:
- parse_yield 추이 (claims 생성 수 per cycle)
- GU 생성 수 추이 (신규 GU vs 해소 GU 비율)
- entity dedup 비율 (통합 시 skip/reject 비율)
- KU 카테고리별 포화도 (Gini 추이)
- **gap_map delta = 0 cycle 수** — stage-e-on c10-c13 4사이클 완전 동결 현상 정량화

**파일**: `scripts/analyze_saturation.py` (신규, API 미호출, 기존 데이터 분석). A11에서 forecast 모드 확장.

- [x] P6-A1 완료 — commit: `398cf9f`

**A1 진단 결론** (debug-history 참조):
- stage-e-on c11-c13 연속 동결: open=20개 고정 (delta=0 × 3)
- 동결 GU 중 wildcard entity (`*`) 포함 다수 확인
- **현재 분석은 코드 읽기 기반 가설** — 진단 로깅(A1-D1~D3) 완료 후 실 데이터로 확정 필요

---

## Stage A1-Diag: Root Cause 실증 (진단 로깅 → 실 Bench)

> **선행**: A1 완료 (✅ `398cf9f`) → D1~D3 순서대로 실행 → A2~A4 scope 최종 결정

### P6-A1-D1 진단 로깅 추가 `[M]`

**목적**: 어느 GU가 왜 미해소되는지 cycle 단위로 추적 가능하게 만들기

**수정 파일**:
- `src/obs/telemetry.py` — `_build_snapshot`에 `cycle_trace` 블록 추가
  - `targets_selected`: 선정된 GU별 `{gu_id, entity_key, field, is_wildcard, age_cycles}`
  - `queries_by_gu`: GU별 실제 쿼리 텍스트 (plan이 생성한 것)
  - `search_yield_by_gu`: GU별 search results 개수
  - `claims_by_gu`: GU별 claim 생성 개수
  - `resolved_gus`: 이 cycle에서 resolved된 GU 목록
  - `adjacent_gap_generated`: 신규 adjacent_gap GU 개수
- `src/obs/telemetry.py` — `emit_gu_trace()` 신규 함수: `telemetry/gu_trace.jsonl`에 open GU별 행 append
- `src/orchestrator.py` — cycle 루프에 `cycle_ctx` dict 수집 훅 추가 (node 동작 변경 없음)
- `src/nodes/collect.py` — `_collect_single_gu` return에 `search_count` 포함
- `src/nodes/integrate.py` — return dict에 `_diag_adjacent_gap_count`, `_diag_resolved_gus` 추가

**주의**: 외부 인터페이스 (`current_claims`, `collect_failure_rate`) 및 기존 node 동작 불변. 로깅만 추가.

- [ ] P6-A1-D1 완료 — commit: TBD

---

### P6-A1-D2 분석 스크립트 확장 `[S]`

**파일**: `scripts/analyze_saturation.py` 확장

**추가 옵션**:
- `--trace-frozen [N]`: N cycle 이상 연속 open인 GU 목록 + 쿼리/yield/원인 요약
- `--query-patterns`: wildcard vs concrete의 search/claims yield 분포 비교
- `--cycle-diff C1 C2`: 두 cycle 간 gap_map 변화 (resolved/added/unchanged)
- `--compare-trials <A> <B>`: 두 trial의 frozen GU 집합 비교

**입력**: `telemetry/gu_trace.jsonl` (D1에서 신규 생성)

- [ ] P6-A1-D2 완료 — commit: TBD

---

### P6-A1-D3 실 Bench 재실행 + Root Cause 확정 `[M]`

> **API 비용 주의**: 5c smoke ≈ $0.35 + 15c full ≈ $1. 실행 전 사전 확인 필수.

**실행 순서**:
1. 5c smoke run (stage-e-off 설정) → `gu_trace.jsonl` 생성 확인
2. 15c full run (stage-e-on 설정) → `--trace-frozen 3`으로 동결 GU 분석
3. 다음 질문에 **실제 숫자로** 답:
   - 동결 GU 중 wildcard / hard-concrete / 기타 각 몇 개?
   - wildcard 쿼리의 실제 search yield (0인지 아닌지)
   - adjacent_gap_generated 추이 (c10 이후 0이 되는 시점)

**결과 → A2~A4 scope 결정**:
- wildcard query yield=0 확정 → `plan.py` slug 수정 우선 (A3)
- hard-concrete GU 누적 확정 → `critique.py` age-based deferred (A4 재설계)
- seed fallback wildcard 확정 → `seed.py` Case B 개선 (A2 연계)

- [ ] P6-A1-D3 완료 — commit: TBD

---

### P6-A2 Plateau-driven re-seed `[M]`

**전제**: **A1-D3 완료 후** root cause = 신규 entity/topic 부재 확인 시 실행

**파일**: `src/nodes/seed.py` 확장

**요건**:
- plateau 감지 후 N cycle (기본 3) 경과 시 re-seed 트리거
- `plateau_detector.py` re-seed flag 신호 활용
- re-seed pack = LLM-driven: 현재 skeleton의 미충족 axis를 입력으로 신규 seed 생성
- 생성된 seed → 다음 cycle plan에 반영 (Gap-driven 원칙 준수)

- [ ] P6-A2 완료 — commit: TBD

---

### P6-A3 Field 다양화 강화 `[M]`

**전제**: **A1-D3 완료 후** root cause 확정 시 실행. wildcard query yield=0 확인 시 `plan.py:268` slug 수정도 포함

**파일**: `src/nodes/plan.py` 확장

**요건**:
- entity_key별 미충족 field 목록 계산 (skeleton field 선언 대비 KU 실제 field 분포)
- 미충족 field를 우선 GU 생성 대상으로 지정
- plan target 선택 시 field 다양화 가중치 적용 (기존 novelty 가중치와 병행)

- [ ] P6-A3 완료 — commit: TBD

---

### P6-A4 Active KU 재해소 `[M]`

**전제**: **A1-D3 완료 후** root cause = hard-to-resolve GU 누적 또는 unresolvable GU open pool 점거 확인 시 실행

**파일**: `src/nodes/critique.py` 확장

**요건**:
- disputed KU 중 evidence가 충분한 것 → auto-resolve 또는 GU 재생성
- stale KU 중 observed_at이 오래된 것 → refresh GU 재투입 (1회 refresh 후에도 stale 지속 시 재투입)
- 재투입 횟수 제한: KU당 최대 3회 (무한 루프 방지)
- **critique가 새 GU를 생성하지 못하는 조건 진단 추가** (A1 결과 기반)

- [ ] P6-A4 완료 — commit: TBD

---

## Stage A-Outside: Stage E 보강

### P6-A5 Universe probe slug 정규화 `[M]`

**배경**: D-151 확정 — stage-e-on c9/c13 collision_active 5건 실측. slug 정규화만으로는 0.5/cyc → 4.0/cyc 회복 불가 (gap_map 동결은 core loop 문제). collision 해소는 별도 기여.

**파일**: `src/nodes/universe_probe.py`

**요건**:
- probe slug 생성 시 유사도 필터 적용 (기존 exact match → fuzzy/edit-distance)
- collision_active 상태의 probe가 반복 발동되는 경우 skip
- slug 정규화: lowercase, stopword 제거, 단수화 (간단한 규칙 기반)

- [ ] P6-A5 완료 — commit: TBD

---

### P6-A6 Probe accept rate 튜닝 `[S]`

**배경**: 15c에 1개 skeleton candidate 승격 → 너무 느림

**파일**: `src/nodes/universe_probe.py`, `src/config.py`

**요건**:
- accept rate 임계치 (현행 config 값 확인 후 조정)
- 목표: 5c당 1개 이상 candidate 승격 (단, quality < threshold 시 skip 유지)
- config에 `probe_accept_threshold` 명시 (하드코딩 제거)

- [ ] P6-A6 완료 — commit: TBD

---

## Stage A-Forecastability: 메커니즘 발동 보장 (신규, D-158)

### P6-A7 Smart Remodel 임계값 config 외부화 `[S]`

**배경**: `src/orchestrator.py:454-458` 에 하드코딩 (GROWTH_STAGNATION_THRESHOLD=5, WINDOW=3; EXPLORATION_DROUGHT_THRESHOLD=30, WINDOW=5). sensitivity 실험 불가.

**파일**: 신규 `SmartRemodelConfig` (`src/config.py`), `src/orchestrator.py:454-503` 리팩터

**요건**:
- `SmartRemodelConfig`: `growth_stagnation_threshold`, `growth_stagnation_window`, `exploration_drought_threshold`, `exploration_drought_window`
- `config.py` from_env / Silver trial snapshot에 dump
- 기본값 = 현재 상수와 동일 (breaking change 아님)
- 단위 테스트: config 기본값 injection → 기존 동작 보존 검증
- 기존 821 tests green 유지 필수

- [ ] P6-A7 완료 — commit: TBD

---

### P6-A8 Exploration Pivot 임계값 config 외부화 `[S]`

**배경**: `src/nodes/exploration_pivot.py:25-26` 에 하드코딩 (WINDOW=5, THRESHOLD=0.1). 15c 내 발동 조건 실험 불가.

**파일**: `src/config.py` `ExternalAnchorConfig` 확장, `src/nodes/exploration_pivot.py:25-90` 리팩터

**요건**:
- `ExternalAnchorConfig.novelty_threshold`, `.novelty_window` 추가
- 기본값 = 0.1, 5 (기존 상수와 동일)
- from_env / trial snapshot에 dump
- 기존 테스트 전부 green 유지

- [ ] P6-A8 완료 — commit: TBD

---

### P6-A9 Pivot 발동 조건 단위 테스트 확장 `[S]`

**배경**: `tests/test_nodes/test_exploration_pivot.py` 에 synthetic `_stagnant_state` 주입 패턴 확립됨. 15c 내 발동 시나리오 커버 부족.

**파일**: `tests/test_nodes/test_exploration_pivot.py`

**요건**:
- 15c 내 발동 시나리오 5개 이상 (synthetic `ext_novelty_history` 주입):
  1. window 경계 (정확히 window 길이만큼 stagnant)
  2. threshold 경계 (0.099 vs 0.101 갈림)
  3. 중간 회복 (c3에서 novelty↑ → 리셋)
  4. audit 소비 교차 (stagnant + audit_consumed → skip)
  5. config override (novelty_window=3 → 발동, =5 → 미발동)
- 모든 테스트는 실제 LLM/API 호출 없이 순수 단위 테스트

- [ ] P6-A9 완료 — commit: TBD

---

### P6-A10 Trigger telemetry 구조화 `[M]`

**배경**: 현재 Remodel/Pivot 발동은 orchestrator log line (`Remodel 완료: audit_cycle=10, proposals=67 (merge, ...)`) 텍스트로만 남음. forecast를 위해 JSON 필드로 구조화 필요.

**파일**: `src/obs/telemetry.py:56-100`, `schemas/telemetry.v1.schema.json`, `src/orchestrator.py`, `src/nodes/exploration_pivot.py`

**요건**:
- `trigger_event` optional 필드: `{cycle: int, mechanism: "remodel"|"pivot", reason: str, leading_indicators: {ext_novelty: float, drought_counter: int, stagnation_counter: float, ku_delta: int, gu_open: int}}`
- Remodel 발동 시 / Pivot 발동 시 emit
- schema validate PASS (G5-1 회귀 방지)
- Dashboard loader backward compat (없어도 동작)
- 단위 테스트: emit 누락 / 중복 방지

- [ ] P6-A10 완료 — commit: TBD

---

### P6-A11 Forecastability F-Gate (15c rerun + forecast + 판정) `[M]`

> **API 비용 주의**: 15c rerun ≈ $1 예상. 실행 전 사전 확인 필수. 이 비용으로 A12 50c ($3~5) ROI 보증.

**배경**: 사용자 bottomline — "Smart Remodel + Exploration Pivot 15c 내 충분 발동 + 15c 이후 지속 발동 보장을 15c 데이터만으로 forecast. A8 50c 전 완료." (D-158)

**파일**: `bench/silver/japan-travel/p6a-fgate-15c/` [NEW], `scripts/analyze_saturation.py` forecast 모드 확장

**실행 순서**:
1. A1~A10 반영 + 821 tests green 확인
2. stage-e-on 15c rerun (silver-trial-scaffold) — trigger_event emit 확인
3. forecast 모델 적용:
   - **Input**: `ku_delta[t]`, `gu_open[t]`, `ext_novelty[t]`, `drought_counter[t]`, `stagnation_counter[t]` 시계열 + 실발동 이벤트 목록
   - **Method (단순/투명)**:
     - (a) 관측 빈도 외삽: 15c 내 N회 → 50c 기대 = N × (35/15) × damping (growth slope 감쇠 시 drought↑)
     - (b) Leading indicator threshold crossing: `drought_counter` 선형 회귀 → 임계값 30 미달 cycle 예측 / `ext_novelty` 이동평균 → WINDOW 연속 < THRESHOLD cycle 예측
     - (c) Confidence: c1-c12 학습 → c13-c15 예측 bootstrap hit/miss → confidence 산출
   - **Output (readiness-report 섹션)**:
     ```
     forecast.remodel: observed=N, projected_c16_c50=M, confidence=0.XX
     forecast.pivot: observed=N, projected_c16_c50=M, confidence=0.XX
     verdict: PASS/FAIL/RETRY
     ```
4. **Gate 판정**:
   - [ ] Remodel ≥ 2회 + Pivot ≥ 1회 실발동 (Pivot 미발동 시 임계값 완화 실험 허용 — forecast는 원복된 기준으로 평가)
   - [ ] forecast c16-c50 Remodel ≥ 4회 + Pivot ≥ 2회
   - [ ] confidence ≥ 0.6
   - [ ] 미달 시 A2~A6 재설계 루프

**금지**: Prophet/ARIMA 등 블랙박스 모델. 선형/지수 projection + damping + bootstrap confidence 한정.

- [ ] P6-A11 완료 — commit: TBD

---

## Stage A-Gate: 50c Trial

### P6-A12 stage-e-on-50c trial 생성 + 실행 `[L]`

> **선행 조건**: **P6-A F-Gate PASS (A11)**. API 비용 주의 (≈ $3~5 예상).

**파일**: `bench/silver/japan-travel/p6a-stage-e-on-50c/` [NEW]

**요건**:
- silver-trial-scaffold skill로 trial 생성
- trial card에 A11 forecast 예측 횟수 기입 (실측과 비교용)
- `--external-anchor --cycles 50` 실행
- 중간 체크포인트: 25c 후 KU/gap_resolution 확인 → 계속 여부 결정
- 완료 후 readiness-report.md 작성

**목표 지표**:
- KU ≥ 250
- gap_resolution ≥ 0.85
- collision_active = 0 or stable
- Remodel / Pivot 실발동 = forecast ± 2회 (예측 정확도 검증)

- [ ] P6-A12 완료 — commit: TBD

---

### P6-A13 COMPARISON-v2.md 작성 `[S]`

**파일**: `bench/japan-travel-external-anchor/COMPARISON-v2.md` 또는 `bench/silver/japan-travel/COMPARISON-v2.md`

**내용**:
- 15c vs 50c KU 성장률 비교 (per-window)
- stage-e-on vs stage-e-off 50c 비교
- P6-A5/A6 fix 효과 (collision_active, accept rate 변화)
- **Remodel / Pivot 실발동 횟수 vs forecast 예측 비교** (오차 분석)
- P6-A Gate 달성 여부 판정

- [ ] P6-A13 완료 — commit: TBD

---

## Stage B: Performance Optimization

### P6-B1 LLM 호출 batch `[L]`

**배경**: 주 호출 지점 = `src/nodes/collect.py:130` (GU당 parse invoke). ThreadPool 병렬이나 batch API 아님. cycle당 최대 12회 → batch 1회로.

**파일**: `src/adapters/llm_adapter.py`, `src/nodes/collect.py`

**요건**:
- claim별 단발 invoke → `ainvoke` batch 활용 (langchain `abatch`)
- 배치 크기 config (`llm_batch_size`, 기본 5)
- fallback: batch 실패 시 단발 invoke 유지 (안전한 degradation)
- LLMCallCounter 배치 호출 집계 (`batch_call_count` metric)

- [ ] P6-B1 완료 — commit: TBD

---

### P6-B2 state_io 증분 저장 `[M]`

**파일**: `src/utils/state_io.py`

**요건**:
- `save_state_delta(state, prev_state, path)` 신규 함수
- changed fields만 delta write (list append / dict diff)
- 전체 snapshot은 N cycle마다 1회 (기본 5cycle) 유지 (복구 anchor)
- `load_state` 는 기존 방식 유지 (호환성)

- [ ] P6-B2 완료 — commit: TBD

---

### P6-B3 cycle wall_clock 측정 `[S]`

**파일**: `src/orchestrator.py`, `src/obs/telemetry.py`

**요건**:
- `wall_clock_s` 이미 telemetry.v1 schema에 선언됨 → orchestrator에서 emit 연결
- `time.monotonic()` cycle 시작/종료 측정
- baseline: 현 cycle 평균 wall_clock 측정 후 B1/B2 적용 전후 비교 기록

- [ ] P6-B3 완료 — commit: TBD

---

## Stage C: Knowledge DB Release

### P6-C1 External-consumable schema `[M]`

**파일**: `schemas/kb-export.schema.json` [NEW]

**요건**:
- `knowledge_units.json` → read-only export 스키마 정의
- 내부 필드(dispute_queue, ledger_id 등) 제외
- `entity_key`, `claim`, `confidence`, `category`, `evidence_links` 핵심 필드만
- JSON Schema Draft 2020-12 준수

- [ ] P6-C1 완료 — commit: TBD

---

### P6-C2 KB packaging `[M]`

**파일**: `pyproject.toml` 수정, `src/kb/__init__.py` [NEW]

**요건**:
- `evolver-kb-japan-travel` optional package 선언 (또는 별도 dist-packages)
- japan-travel KB 데이터 포함 (`package_data`)
- `from evolver_kb import japan_travel; ku = japan_travel.get_ku("japan-travel:transport:jr-pass")`
- 외부 프로젝트에서 `pip install -e ".[kb]"` 후 import 가능

- [ ] P6-C2 완료 — commit: TBD

---

### P6-C3 Query API / static export `[M]`

**파일**: `src/kb/query.py` [NEW]

**요건**:
- `lookup_by_key(entity_key: str) -> dict | None`
- `list_by_category(category: str) -> list[dict]`
- `search_by_text(query: str, top_k: int = 10) -> list[dict]` (간단한 substring 매칭)
- `list_open_gaps() -> list[dict]`
- CLI: `python -m src.kb.query lookup japan-travel:transport:jr-pass`

- [ ] P6-C3 완료 — commit: TBD

---

### P6-C4 Operator guide 외부 사용자 섹션 `[S]`

**파일**: `docs/operator-guide.md` §9 추가

**내용**:
- 외부 소비 목적 KB 로드 방법
- `lookup_by_key` / `list_by_category` 사용 예제
- KB 버전 관리 (trial_id 기반)
- 라이선스/출처 표기 안내

- [ ] P6-C4 완료 — commit: TBD

---

## Cross-phase 제어

- [ ] **X1** P6-A Gate 완료 후 `bench/silver/INDEX.md` 에 p6a-fgate-15c + p6a-stage-e-on-50c trial row 추가
- [ ] **X2** A10 `trigger_event` schema 변경 시 dashboard loader regression 테스트
- [ ] **X3** `schemas/kb-export.schema.json` positive + negative 테스트 (C1 포함)
- [ ] **X4** `src/kb/__init__.py` 생성 확인
- [ ] **X5** A7/A8 config 외부화 후 기존 snapshot의 config dump 필드 backward compat 확인
- [ ] **X6** P6 완료 시 masterplan §8 리스크 레지스터 재평가
