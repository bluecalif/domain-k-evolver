# Silver P6: Consolidation & Knowledge DB Release — Context
> Last Updated: 2026-04-18 (rev: F-Gate 추가, A1~A13 재번호)
> Status: Planning

## 1. 핵심 파일

### P6-A에서 읽어야 할 파일

| 파일 | 내용 | P6 관련성 |
|------|------|-----------|
| `src/obs/telemetry.py` | `_build_snapshot`, `emit_cycle` — A1-D1 `cycle_trace` 블록 추가 대상 | A1-D1 |
| `src/orchestrator.py` | cycle 루프 — A1-D1 `cycle_ctx` 수집 훅 삽입 위치 | A1-D1 |
| `src/nodes/collect.py` | `_collect_single_gu` — search_count 반환 확장 | A1-D1 |
| `src/nodes/integrate.py:524-533` | `new_dynamic_gus` → return에 `_diag_*` 메타필드 추가 | A1-D1 |
| `scripts/analyze_saturation.py` | 기존 분석 스크립트 — A1-D2에서 `--trace-frozen` 등 확장 | A1-D2 |
| `bench/silver/japan-travel/stage-e-on/trajectory/` | 15c 실행 결과 — KU 성장률 분석 | A1 saturation 진단 |
| `bench/silver/japan-travel/stage-e-off/trajectory/` | stage-e-off 비교 baseline | A1 |
| `bench/silver/japan-travel/p2-smart-remodel/trajectory/` (있는 경우) | p2-remodel 성장률 — A-Inside 효과 baseline | A1 |
| `bench/japan-travel-external-anchor/COMPARISON.md` | P4 Stage E on/off 비교 (VP4 PASS 4/5, KU saturation 분석) | A1 진단 근거 |
| `src/nodes/universe_probe.py` | probe slug 등록 로직 — collision 원인 | A5 |
| `src/nodes/exploration_pivot.py:25-90` | pivot 발동 조건 (WINDOW=5, THRESHOLD=0.1 하드코딩) | A8, A9 |
| `src/orchestrator.py:454-503` (`_should_remodel`) | Smart Remodel 임계값 하드코딩 (GROWTH_STAGNATION=5, DROUGHT=30) | A7 |
| `src/config.py:74-106` (`ExternalAnchorConfig`) | Pivot config 확장 기준점 + 신규 `SmartRemodelConfig` | A7, A8 |
| `src/nodes/seed.py` | 현행 seed pack 구조 — re-seed 확장 기준점 | A2 |
| `src/nodes/plan.py` | GU 생성 우선순위 로직 | A3 |
| `src/nodes/critique.py` | stale/disputed KU → GU 재투입 경로 현황 | A4 |
| `src/utils/plateau_detector.py` | 현행 plateau 감지 조건 | A2 re-seed 트리거 |
| `src/obs/telemetry.py:56-100` + `schemas/telemetry.v1.schema.json` | trigger_event optional 필드 emit 대상 | A10 |
| `src/utils/metrics.py:105-125` (`compute_metrics`) | forecast signal (delta_from_prev_cycle) | A11 |
| `tests/test_nodes/test_exploration_pivot.py` | synthetic `_stagnant_state` 주입 패턴 재사용 | A9 |
| `tests/test_nodes/test_remodel.py` | Remodel 단위 테스트 레퍼런스 | A7 |
| `bench/silver/japan-travel/p2-smart-remodel-trial/run.log` | Remodel 실발동 로그 (c10 drought 67 merges, c15 drought 1 source_policy) | A1, A11 |

### P6-B에서 읽어야 할 파일

| 파일 | 내용 | P6 관련성 |
|------|------|-----------|
| `src/adapters/llm_adapter.py` | LLMCallCounter + 현행 단발 invoke | B1 batch 래퍼 위치 |
| `src/utils/state_io.py` | save_state / load_state 전체 rewrite 로직 | B2 delta write |
| `src/obs/telemetry.py` | emit_cycle 구조 — wall_clock 추가 emit 위치 | B3 |
| `src/orchestrator.py` | cycle 루프 — time.monotonic() 측정 위치 | B3 |

### P6-C에서 읽어야 할 파일

| 파일 | 내용 | P6 관련성 |
|------|------|-----------|
| `schemas/knowledge-unit.json` | KU schema — external schema 기반 | C1 |
| `schemas/gap-unit.json` | GU schema | C1 |
| `bench/silver/japan-travel/stage-e-off/state/` (또는 최종 trial state) | japan-travel KB 실 데이터 | C2 packaging 대상 |
| `docs/operator-guide.md` | 현행 operator-guide — §9 추가 기준점 | C4 |
| `pyproject.toml` | 의존성 + 패키지 선언 기준 | C2 |

### Silver 공통 참조

| 파일 | 내용 |
|------|------|
| `docs/silver-masterplan-v2.md` | §4 P6 gate 정량 조건 |
| `dev/active/phase-si-p4-coverage/` | Stage E 코드/테스트 상세 |
| `dev/active/phase-si-p5-telemetry-dashboard/readiness-report.md` | P5 Gate PASS 증거 |

---

## 2. 데이터 인터페이스

### P6-A

| 방향 | 경로 | 형식 |
|------|------|------|
| 읽기 (진단) | `bench/silver/japan-travel/*/trajectory/*.json` | trajectory JSON |
| 읽기 (진단) | `bench/silver/japan-travel/*/state/knowledge-units.json` | KU list |
| 읽기 (진단) | `bench/silver/japan-travel/*/state-snapshots/cycle-N-snapshot/gap-map.json` | GU list (A1 gap_map delta 측정) |
| 읽기 (진단) | `bench/silver/japan-travel/*/telemetry/cycles.jsonl` | telemetry jsonl |
| 읽기 (forecast) | `bench/silver/japan-travel/p2-smart-remodel-trial/run.log` | Remodel 발동 로그 (baseline 참조) |
| 쓰기 (F-Gate 15c) | `bench/silver/japan-travel/p6a-fgate-15c/` | silver-trial-scaffold 생성 (신규, A11) |
| 쓰기 (F-Gate 결과) | `bench/silver/japan-travel/p6a-fgate-15c/telemetry/cycles.jsonl` | trigger_event 포함 telemetry |
| 쓰기 (50c trial) | `bench/silver/japan-travel/p6a-stage-e-on-50c/` | silver-trial-scaffold 생성 (A12) |
| 쓰기 (결과) | `bench/silver/japan-travel/p6a-stage-e-on-50c/telemetry/cycles.jsonl` | 50c telemetry |

### P6-B

| 방향 | 경로 | 형식 |
|------|------|------|
| 수정 | `src/adapters/llm_adapter.py` | Python |
| 수정 | `src/utils/state_io.py` | Python |
| 수정 | `src/obs/telemetry.py` | Python (wall_clock 필드 추가) |
| 수정 | `schemas/telemetry.v1.schema.json` | JSON Schema (wall_clock_s 필드 확인) |

> 주의: telemetry schema에 `wall_clock_s` 필드는 P5-A1에서 이미 정의됨. orchestrator에서 emit만 추가.

### P6-C

| 방향 | 경로 | 형식 |
|------|------|------|
| 쓰기 | `src/kb/` (신규) | Python 패키지 |
| 쓰기 | `schemas/kb-export.schema.json` (신규) | JSON Schema |
| 쓰기 | `bench/silver/japan-travel/kb-export/` (신규) | exported KB 데이터 |
| 수정 | `docs/operator-guide.md` | Markdown (§9 추가) |
| 수정 | `pyproject.toml` | packaging 선언 |

---

## 3. 주요 결정사항

### P6 구조 결정 (2026-04-18 확정)

| # | 결정 | 근거 |
|---|------|------|
| D-154 | 기존 P6(Multi-Domain)를 **M1**으로 분리 (suspended). 신규 P6 = Consolidation & KB Release (A→B→C) | P5 Gate PASS 후 사용자 의사결정 |
| D-155 | KU saturation 작업을 P6-A Inside에 흡수 (별도 phase 없음) | saturation과 Stage E 보강은 동일 trial 검증 필요 |
| D-156 | D-151 후보 (slug collision) → P6-A5로 확정 실행 | COMPARISON.md stage-e-on c11-15 0.5/cyc 근거 |
| D-157 | P6-A 실행 순서 (초안): 진단(A1) → Inside(A2~A4) → Outside(A5~A6) → 50c trial | D-158로 개정됨 |
| D-158 | **P6-A Forecastability F-Gate 신설** (A7~A11). "Smart Remodel + Exploration Pivot 15c 내 충분 발동 + 15c 이후 지속 발동을 15c 데이터로 forecast"를 50c A12 선행 조건으로 둠. 미달 시 A2~A6 재설계 | 사용자 피드백 (2026-04-18): 50c 결과 의존 판정은 API 비용 노출. p2-remodel 5.2/cyc이 c10 remodel event 1회에 의존한 일시적 효과일 가능성. stage-e-on c10-c13 gap_map 동결은 probe collision 단독 설명 불가 — core loop 마비 |
| D-159 | Remodel/Pivot 임계값 **config 외부화 필수** (A7 `SmartRemodelConfig`, A8 `ExternalAnchorConfig.novelty_*`). 하드코딩 유지 불가 — sensitivity 실험/forecast 불가 | `src/orchestrator.py:454-458`, `src/nodes/exploration_pivot.py:25-26` 실측 |
| D-160 | Trigger telemetry는 **log 파싱 아니라 JSON 필드 emit** (A10 `trigger_event`). optional 필드로 schema backward compat 유지 | A11 forecast 자동화를 위해 구조화 필요 |
| D-161 | **Forecast 모델 금지 사항**: Prophet/ARIMA 등 블랙박스 모델 사용 금지. 선형/지수 projection + damping + bootstrap confidence 한정 | 투명성/설명가능성 우선. 예측 정확도 < forecast 논리 검증가능성 |

| D-162 | **진단 로깅 우선 전략**: A1 코드 분석은 가설 수준. 진단 로깅(telemetry `cycle_trace` + `gu_trace.jsonl`) → 실 bench 재실행 → 데이터로 root cause 확정 후 A2~A4 fix 구현. 가설 기반 일괄 fix 금지 | A1 후속 조사 (2026-04-18): claims=0 여부, search yield, wildcard 쿼리 효과 실측 불가 |

### 미결 결정사항 (A1-D3 완료 후 결정)

| # | 결정 | 트리거 |
|---|------|--------|
| D-? | re-seed pack 크기 / 생성 LLM 비용 상한 | A1 root cause 확인 후 |
| D-? | state_io delta write: jsonpatch vs 자체 구현 vs no-op | B2 전 벤치마크 |
| D-? | KB query API: FastAPI 통합 vs 별도 CLI vs static JSON export | C3 전 scope 결정 |

---

## 4. 컨벤션 체크리스트

### 5대 불변원칙 (P6 적용 포인트)

- [ ] **Gap-driven**: re-seed (A2) 로 생성된 GU가 Plan에 구동되는지 확인
- [ ] **Claim→KU 착지성**: A4 재해소 시 KU 재투입 경로가 claims 처리를 거치는지 확인
- [ ] **Evidence-first**: 재해소된 KU의 evidence_links 유지 여부
- [ ] **Conflict-preserving**: slug 정규화(A5) 가 기존 collision_active KU 삭제하지 않는지 확인
- [ ] **Prescription-compiled**: A4 critique 처방이 plan에 추적 가능한지 확인

### P6-A F-Gate 임계치 (신규, D-158 — A12 50c 선행)

| 지표 | 임계치 | 측정 방법 |
|------|--------|-----------|
| Remodel 실발동 @15c rerun | ≥ 2회 | A10 trigger_event 카운트 |
| Pivot 실발동 @15c rerun | ≥ 1회 (완화 실험 포함) | A10 trigger_event 카운트 |
| Remodel forecast c16-c50 | ≥ 4회 | A11 forecast 모델 |
| Pivot forecast c16-c50 | ≥ 2회 | A11 forecast 모델 |
| Forecast confidence | ≥ 0.6 | c1-c12 학습 → c13-c15 bootstrap hit/miss |

### P6-A Gate 임계치 (A12 이후, masterplan §4 P6 verbatim + 신규 P6-A 기준)

> 주의: masterplan §4의 P6 gate는 Multi-Domain(M1) 기준. 신규 P6-A gate는 본 plan §4 P6-A Gate에 정의.

| 지표 | 임계치 | 측정 방법 |
|------|--------|-----------|
| KU@50c (stage-e-on) | ≥ 250 | 50c trial 최종 state |
| gap_resolution@50c | ≥ 0.85 | 50c trial readiness gate |
| collision_active @50c | 0 또는 stable | trajectory 확인 |
| Remodel/Pivot 예측 vs 실측 | ± 2회 이내 | A13 COMPARISON-v2.md 오차 분석 |
| 테스트 수 | ≥ 840 (+19 예상) | pytest |

### API 비용 주의 (feedback_api_cost_caution)

- **A11 F-Gate 15c rerun 실행 전**: 비용 추정 ≈ $1 (15c × 약 $0.07/cyc) + 사전 확인 필수
- **A12 50c trial 실행 전**: 비용 추정 ≈ $3~5 + 사전 확인 필수. **F-Gate PASS가 선행 조건** — 15c $1 투자로 50c $3~5 ROI 보증
- 기존 trial (15c ≈ $0.8~1.2 추정) 기준 50c ≈ $3~5 추정 (모델/쿼리 수 의존)
- 중간 결과 확인 가능한 checkpoint 로직 활용 (run_readiness.py --cycles 25 → 확인 → 25)

### Silver 인코딩 규칙

- JSON write: `encoding='utf-8'` 명시
- CSV read: `encoding='utf-8-sig'`
- 신규 파일: BOM 없음

### 커밋 prefix

```
[si-p6] Step A.1: KU saturation 진단 분석
[si-p6] Step A.5: universe probe slug 정규화
[si-p6] Step A.7: Smart Remodel 임계값 config 외부화
[si-p6] Step A.8: Exploration Pivot 임계값 config 외부화
[si-p6] Step A.10: trigger telemetry 구조화 (trigger_event emit)
[si-p6] Step A.11: Forecastability F-Gate (15c rerun + forecast + 판정)
[si-p6] Step A.12: stage-e-on 50c trial 실행
[si-p6] Step B.1: LLM batch 호출 도입
[si-p6] Step C.2: evolver-kb-japan-travel packaging
```
