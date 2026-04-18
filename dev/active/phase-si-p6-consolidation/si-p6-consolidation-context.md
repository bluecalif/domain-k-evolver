# Silver P6: Consolidation & Knowledge DB Release — Context
> Last Updated: 2026-04-18
> Status: Planning

## 1. 핵심 파일

### P6-A에서 읽어야 할 파일

| 파일 | 내용 | P6 관련성 |
|------|------|-----------|
| `bench/silver/japan-travel/stage-e-on/trajectory/` | 15c 실행 결과 — KU 성장률 분석 | A1 saturation 진단 |
| `bench/silver/japan-travel/stage-e-off/trajectory/` | stage-e-off 비교 baseline | A1 |
| `bench/silver/japan-travel/p2-smart-remodel/trajectory/` (있는 경우) | p2-remodel 성장률 — A-Inside 효과 baseline | A1 |
| `bench/japan-travel-external-anchor/COMPARISON.md` | P4 Stage E on/off 비교 (VP4 PASS 4/5, KU saturation 분석) | A1 진단 근거 |
| `src/nodes/universe_probe.py` | probe slug 등록 로직 — collision 원인 | A5 |
| `src/nodes/exploration_pivot.py` | pivot 발동 조건 + 50c 검증 대상 | A7 |
| `src/nodes/seed.py` | 현행 seed pack 구조 — re-seed 확장 기준점 | A2 |
| `src/nodes/plan.py` | GU 생성 우선순위 로직 | A3 |
| `src/nodes/critique.py` | stale/disputed KU → GU 재투입 경로 현황 | A4 |
| `src/utils/plateau_detector.py` | 현행 plateau 감지 조건 | A2 re-seed 트리거 |

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
| 읽기 (진단) | `bench/silver/japan-travel/*/telemetry/cycles.jsonl` | telemetry jsonl |
| 쓰기 (50c trial) | `bench/silver/japan-travel/p6a-stage-e-on-50c/` | silver-trial-scaffold 생성 |
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
| D-157 | P6-A 실행 순서: 진단 우선 (A1) → Inside fix (A2~A4) → Outside fix (A5~A7) → 50c trial (A8) | A1 root cause 없이 A2~A4 설계 불가 |

### 미결 결정사항 (P6-A1 완료 후 결정)

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

### P6-A Gate 임계치 (masterplan §4 P6 verbatim + 신규 P6-A 기준)

> 주의: masterplan §4의 P6 gate는 Multi-Domain(M1) 기준. 신규 P6-A gate는 본 plan §4 P6-A Gate에 정의.

| 지표 | 임계치 | 측정 방법 |
|------|--------|-----------|
| KU@50c (stage-e-on) | ≥ 250 | 50c trial 최종 state |
| gap_resolution@50c | ≥ 0.85 | 50c trial readiness gate |
| collision_active @50c | 0 또는 stable | trajectory 확인 |
| 테스트 수 | ≥ 821 (현재 유지) | pytest |

### API 비용 주의 (feedback_api_cost_caution)

- **50c trial 실행 전**: 비용 추정 + 사전 확인 필수
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
[si-p6] Step B.1: LLM batch 호출 도입
[si-p6] Step C.2: evolver-kb-japan-travel packaging
```
