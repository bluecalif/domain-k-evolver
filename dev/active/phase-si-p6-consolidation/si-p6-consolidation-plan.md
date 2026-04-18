# Silver P6: Consolidation & Knowledge DB Release — Plan
> Last Updated: 2026-04-18
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
| stage-e-on c11-15 정지 | probe slug collision 추정 (D-151 후보) | P4 Stage E 분석 |
| Exploration pivot 50c 미검증 | 15c window만 확인 | P4 gate |
| LLM 단발 호출 | cycle당 개별 claim 처리 — batch 없음 | 코드 실측 미정 |
| state_io 전체 rewrite | KU 100+ 이상 시 I/O 병목 가능 | 추정 |

---

## 3. Target State (목표 상태)

| 단계 | 완료 조건 |
|------|-----------|
| P6-A | stage-e-on 50c trial: KU ≥ 250, gap_resolution ≥ 0.85, COMPARISON-v2.md 작성 |
| P6-B | LLM 호출 batch 도입 + wall_clock 기준 latency 10% 이상 개선 측정값 |
| P6-C | `evolver-kb-japan-travel` 패키지 외부 import e2e PASS, query API KU lookup 동작 |

---

## 4. Implementation Stages

### P6-A. Pain Point Resolution

**A-Inside: Core Loop (KU sustained growth)**

| # | Task | 내용 | Size |
|---|------|------|------|
| A1 | KU saturation 진단 | c11-15 정체 root cause: parse_yield / GU 생성 정체 / entity dedup 과다 분석 | M |
| A2 | Plateau-driven re-seed | plateau 감지 시 LLM-driven new seed pack 자동 생성 (`seed_node` 확장) | M |
| A3 | Field 다양화 강화 | 같은 entity_key 내 미충족 field를 우선 GU로 생성 (`plan_node` 확장) | M |
| A4 | Active KU 재해소 | disputed/stale KU → GU 재투입 (critique-refresh 1회 → 반복 재해소) | M |

**A-Outside: Stage E 보강**

| # | Task | 내용 | Size |
|---|------|------|------|
| A5 | Universe probe slug 정규화 | slug 유사도 필터 — collision_active 반복 방지 (D-151 확정) | M |
| A6 | Probe accept rate 튜닝 | 15c에 1개 → 5c당 1개 목표 (accept 임계치 조정) | S |
| A7 | Exploration pivot 50c 발동 검증 | 50c run에서 pivot 발동 여부 확인 | S |

**A-Gate**

| # | Task | 내용 | Size |
|---|------|------|------|
| A8 | stage-e-on-50c trial 실행 | silver-trial-scaffold → 50c run → KU ≥ 250, gap_resolution ≥ 0.85 | L |
| A9 | COMPARISON-v2.md 작성 | 15c vs 50c, e-on vs e-off 비교 리포트 | S |

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
| P6-A Outside | A5~A7 | 2 | 1 | 0 |
| P6-A Gate | A8~A9 | 1 | 0 | 1 |
| P6-B | B1~B3 | 1 | 1 | 1 |
| P6-C | C1~C4 | 1 | 3 | 0 |
| **합계** | **16** | **5** | **9** | **2** |

---

## 6. Risks & Mitigation

| 위험 | 확률 | 영향 | 완화 |
|------|------|------|------|
| 50c API 비용 초과 | 중 | 중 | 실행 전 사전 확인 필수 (feedback_api_cost_caution) |
| KU saturation root cause가 A1~A4와 다른 곳 | 중 | 고 | A1 진단 결과 기반 A2~A4 scope 조정 (A1 완료 후 재검토) |
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
| `src/nodes/exploration_pivot.py` | P6-A7 검증 대상 | A7 |
| `src/utils/state_io.py` | P6-B2 리팩터 대상 | B2 |
| `src/obs/telemetry.py` | P6-B3 wall_clock emit 추가 | B3 |
| `src/adapters/llm_adapter.py` | P6-B1 batch 래퍼 | B1 |
| `scripts/run_readiness.py` | P6-A8 50c trial 실행 진입점 | A8 |

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
