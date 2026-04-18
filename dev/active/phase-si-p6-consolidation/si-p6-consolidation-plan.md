# Silver P6: Consolidation & Knowledge DB Release — Plan
> Last Updated: 2026-04-18 (rev: F-Gate 추가, task 재번호)
> Status: Planning

## 1. Summary (개요)

**목적**: P4/P5까지 드러난 핵심 Pain Point를 해소하고, japan-travel KB를 외부에서 소비 가능한 형태로 완성한다.

**범위**:
- **P6-A (Pain Point)**: KU saturation 진단 + re-seed 자동화 + Stage E collision/accept rate 보강
- **P6-B (Performance)**: LLM batch 호출 + state_io 증분 저장 + wall_clock 측정
- **P6-C (KB Release)**: japan-travel KB external schema + packaging + query API

**예상 결과물**:
- stage-e-on 50c rerun: KU ≥ 250, gap_resolution ≥ 0.85 (A gate)
- LLM 비용 / latency 개선 가시화 (B gate)
- `evolver-kb-japan-travel` importable package (C gate)

**P6 완료 후**: M1 (Multi-Domain Validation) 활성화 조건 충족

---

## 2. Current State (현재 상태)

### P5 완료 기준점 (2026-04-18)

| 지표 | 값 |
|------|---|
| tests | 821 |
| P5 Gate | PASS (G5-1~6 전항목, S10) |
| Dashboard | 7 views, 1.49s load |
| operator-guide | 184줄 |
| Telemetry | `schemas/telemetry.v1.schema.json` + emitter |

### 잔존 Pain Points

| 항목 | 데이터 | 출처 |
|------|--------|------|
| KU saturation | c11-15: stage-e-on 0.5/cyc, stage-e-off 4.0/cyc, p2-remodel 5.2/cyc | COMPARISON.md |
| stage-e-on c10-c13 gap_map 완전 동결 | open=20, resolved=76 불변 4사이클 (probe slug collision 단독 설명 불가) | snapshot 실측 (2026-04-18) |
| Smart Remodel 15c 발동 2회 | p2-remodel c10 (drought, 67 merges) + c15 (drought, 1 source_policy) | p2-smart-remodel run.log |
| Smart Remodel 임계값 하드코딩 | `src/orchestrator.py:454-458` (GROWTH_STAGNATION=5, DROUGHT=30) | 코드 실측 |
| Exploration Pivot 임계값 하드코딩 | `src/nodes/exploration_pivot.py:25-26` (WINDOW=5, THRESHOLD=0.1), 실 trial 15c 내 0회 발동 | 코드 실측 |
| LLM 단발 호출 지점 | `src/nodes/collect.py:130` — GU당 parse 개별 invoke (ThreadPool 병렬이나 batch API 아님) | 코드 실측 |
| state_io 전체 rewrite | KU 100+ 이상 시 I/O 병목 가능 | 추정 |

---

## 3. Target State (목표 상태)

| 단계 | 완료 조건 |
|------|-----------|
| P6-A F-Gate (신규, A12 50c 선행) | stage-e-on 15c rerun: Smart Remodel ≥ 2회 + Exploration Pivot ≥ 1회 실발동, forecast c16-c50 Remodel ≥ 4회 + Pivot ≥ 2회, confidence ≥ 0.6 |
| P6-A Gate | stage-e-on 50c trial: KU ≥ 250, gap_resolution ≥ 0.85, COMPARISON-v2.md 작성 |
| P6-B | LLM 호출 batch 도입 + wall_clock 기준 latency 10% 이상 개선 측정값 |
| P6-C | `evolver-kb-japan-travel` 패키지 외부 import e2e PASS, query API KU lookup 동작 |

---

## 4. Implementation Stages

### P6-A. Pain Point Resolution

**A-Inside: Core Loop (KU sustained growth)**

| # | Task | 내용 | Size |
|---|------|------|------|
| A1 | KU saturation 진단 | c11-15 정체 root cause: parse_yield / GU 생성 정체 / entity dedup 과다 + **gap_map delta=0 cycle 수** 측정 | M |
| A2 | Plateau-driven re-seed | plateau 감지 시 LLM-driven new seed pack 자동 생성 (`seed_node` 확장) | M |
| A3 | Field 다양화 강화 | 같은 entity_key 내 미충족 field를 우선 GU로 생성 (`plan_node` 확장) | M |
| A4 | Active KU 재해소 | disputed/stale KU → GU 재투입 (critique-refresh 1회 → 반복 재해소) | M |

**A-Outside: Stage E 보강**

| # | Task | 내용 | Size |
|---|------|------|------|
| A5 | Universe probe slug 정규화 | slug 유사도 필터 — collision_active 반복 방지 (D-151 확정) | M |
| A6 | Probe accept rate 튜닝 | 15c에 1개 → 5c당 1개 목표 (accept 임계치 조정) | S |

**A-Forecastability: 메커니즘 발동 보장 (신규, D-158)**

| # | Task | 내용 | Size |
|---|------|------|------|
| A7 | Smart Remodel 임계값 config 외부화 | `SmartRemodelConfig` 신설 — `growth_stagnation_{threshold,window}`, `exploration_drought_{threshold,window}`. `src/orchestrator.py:454-503` 하드코딩 제거, 기본값은 기존 상수와 동일 | S |
| A8 | Exploration Pivot 임계값 config 외부화 | `ExternalAnchorConfig.novelty_threshold`, `.novelty_window` 추가. `src/nodes/exploration_pivot.py:25-26` 하드코딩 제거, 기본값 유지 | S |
| A9 | Pivot 발동 조건 단위 테스트 확장 | `tests/test_nodes/test_exploration_pivot.py` 의 `_stagnant_state` synthetic 패턴 재사용 — 15c 내 발동 5+ 시나리오 커버 (window 경계, threshold 경계, audit consumed 교차) | S |
| A10 | Trigger telemetry 구조화 | Remodel/Pivot 발동 시 `trigger_event: {cycle, mechanism, reason, leading_indicators}` 를 cycles.jsonl에 emit. `schemas/telemetry.v1.schema.json` optional 필드 추가 (breaking change 아님) | M |
| A11 | Forecastability F-Gate (15c rerun + forecast + 판정) | A1~A10 반영 후 stage-e-on 15c rerun (~$1). `scripts/analyze_saturation.py` forecast 모드: 선행지표 선형/지수 projection + damping + bootstrap confidence. **Gate**: Remodel ≥ 2회 + Pivot ≥ 1회 실발동 & forecast c16-c50 Remodel ≥ 4회 + Pivot ≥ 2회 & confidence ≥ 0.6. 미달 시 A2~A6 재설계 루프 (A12 진행 차단) | M |

**A-Gate: 50c Trial**

| # | Task | 내용 | Size |
|---|------|------|------|
| A12 | stage-e-on-50c trial 실행 | F-Gate PASS 선행 조건. silver-trial-scaffold → 50c run → KU ≥ 250, gap_resolution ≥ 0.85. trial card에 forecast 예측 횟수 기입 (실측과 비교) | L |
| A13 | COMPARISON-v2.md 작성 | 15c vs 50c, e-on vs e-off 비교 + forecast vs 실측 오차 분석 | S |

### P6-B. Performance Optimization

| # | Task | 내용 | Size |
|---|------|------|------|
| B1 | LLM 호출 batch | claim별 단발 → 배치 (langchain batch API 활용) — 비용/latency 동시 개선 | L |
| B2 | state_io 증분 저장 | 매 cycle 전체 rewrite → changed fields만 delta write | M |
| B3 | wall_clock 측정 | cycle당 monotonic time 측정 + telemetry emit + 목표치 설정 | S |

### P6-C. Knowledge DB Release

| # | Task | 내용 | Size |
|---|------|------|------|
| C1 | External-consumable schema | `state/knowledge_units.json` → read-only external schema 정의 | M |
| C2 | KB packaging | `evolver-kb-japan-travel` — pyproject.toml package 선언 + 데이터 포함 | M |
| C3 | Query API / static export | KU lookup (entity_key / category / text search), GU enumeration | M |
| C4 | Operator guide 외부 사용자 섹션 | `docs/operator-guide.md` §9 추가: "외부 소비 가이드" | S |

---

## 5. Task Breakdown

| Stage | Tasks | S | M | L |
|-------|-------|---|---|---|
| P6-A Inside | A1~A4 | 0 | 4 | 0 |
| P6-A Outside | A5~A6 | 1 | 1 | 0 |
| P6-A Forecastability | A7~A11 | 3 | 2 | 0 |
| P6-A Gate | A12~A13 | 1 | 0 | 1 |
| P6-B | B1~B3 | 1 | 1 | 1 |
| P6-C | C1~C4 | 1 | 3 | 0 |
| **합계** | **20** | **7** | **11** | **2** |

---

## 6. Risks & Mitigation

| 위험 | 확률 | 영향 | 완화 |
|------|------|------|------|
| 50c API 비용 초과 | 중 | 중 | 실행 전 사전 확인 필수. **F-Gate (A11)** 로 선제 차단 — 15c rerun (~$1) 으로 50c ROI 보증 |
| KU saturation root cause가 A1~A4와 다른 곳 | 중 | 고 | A1 진단 결과 기반 A2~A4 scope 조정 (A1 완료 후 재검토) |
| Forecast 모델이 15c Remodel 2회를 50c 8회로 과대 예측 | 중 | 고 | damping factor + bootstrap confidence (<0.6 RETRY) + 선형/지수 모델 한정 (투명성) |
| A11 rerun에서 Pivot 0회 발동 (15c 내 5연속 < 0.1 미달) | 중 | 중 | A8에서 임계값 실험적 완화 (window 5→3 등) 후 발동 관찰 → forecast 시 원복하여 50c 기준 평가 |
| Remodel/Pivot config 외부화 중 기존 동작 깨짐 | 낮 | 고 | 기본값을 기존 상수와 동일 설정, 기존 821 tests 전부 green 유지 필수 |
| LLM batch API 비동기 복잡도 | 중 | 중 | 기존 단발 호출 fallback 유지, batch는 성능 최적화 레이어 |
| C2 packaging이 실제 외부 import 불가 | 저 | 중 | e2e 테스트로 사전 검증 (C2 완료 즉시) |

---

## 7. Dependencies

### 내부 의존성

| 컴포넌트 | 관계 | Phase |
|----------|------|-------|
| `src/nodes/seed.py` | P6-A2 확장 대상 | A2 |
| `src/nodes/plan.py` | P6-A3 확장 대상 | A3 |
| `src/nodes/critique.py` | P6-A4 확장 대상 | A4 |
| `src/nodes/universe_probe.py` | P6-A5/A6 수정 대상 | A5, A6 |
| `src/orchestrator.py:454-503` (`_should_remodel`) | Remodel 임계값 config 주입 | A7 |
| `src/nodes/exploration_pivot.py:25-90` | Pivot 임계값 config 주입 + 단위 테스트 | A8, A9 |
| `src/config.py:74-106` (`ExternalAnchorConfig`) + 신규 `SmartRemodelConfig` | 외부화된 config 클래스 | A7, A8 |
| `src/obs/telemetry.py:56-100` + `schemas/telemetry.v1.schema.json` | `trigger_event` optional 필드 emit | A10 |
| `scripts/analyze_saturation.py` (A1 신규) | A11 forecast 모드 확장 | A1, A11 |
| `tests/test_nodes/test_exploration_pivot.py` | synthetic injection 패턴 재사용 | A9 |
| `tests/test_nodes/test_remodel.py` | Remodel 단위 테스트 레퍼런스 | A7 |
| `src/utils/metrics.py:105-125` (`compute_metrics`) | `delta_from_prev_cycle` — forecast signal | A11 |
| `src/utils/state_io.py` | P6-B2 리팩터 대상 | B2 |
| `src/adapters/llm_adapter.py` | P6-B1 batch 래퍼 | B1 |
| `scripts/run_readiness.py` | 15c rerun (A11) + 50c trial (A12) 실행 진입점 | A11, A12 |

### 외부 의존성

| 라이브러리 | 용도 | 비고 |
|-----------|------|------|
| `langchain_openai` | LLM batch API | `abatch()` 또는 `batch()` |
| `jsonpatch` (선택) | state_io delta write | 선택 의존성 |
| `packaging` / `build` | C2 KB packaging | pyproject.toml 기반 |

### 선행 조건

- P5 Gate PASS ✅ (2026-04-18)
- `bench/silver/japan-travel/stage-e-on/` 데이터 존재 ✅
- `bench/silver/japan-travel/stage-e-off/` 데이터 존재 ✅
