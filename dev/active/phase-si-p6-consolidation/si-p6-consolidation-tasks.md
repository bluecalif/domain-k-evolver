# Silver P6: Consolidation & Knowledge DB Release — Tasks
> Last Updated: 2026-04-18
> Status: Planning (0/16)

## Summary

| Stage | Tasks | Done | Status |
|-------|-------|------|--------|
| P6-A Inside (KU saturation) | 4 | 0 | 대기 |
| P6-A Outside (Stage E 보강) | 3 | 0 | 대기 |
| P6-A Gate (50c trial) | 2 | 0 | 대기 |
| P6-B Performance | 3 | 0 | 대기 |
| P6-C KB Release | 4 | 0 | 대기 |
| **합계** | **16** | **0** | — |

Size: S:5 / M:9 / L:2 / XL:0

테스트 목표: 821 (현재) → ≥ **836** (+15 예상)

---

## Gate 조건 (P6-A / P6-B / P6-C)

### P6-A Gate
- [ ] stage-e-on 50c trial: **KU ≥ 250**
- [ ] stage-e-on 50c trial: **gap_resolution ≥ 0.85**
- [ ] collision_active 반복 없음 (A5 효과 확인)
- [ ] Exploration pivot 발동 1회 이상 (A7 확인)
- [ ] COMPARISON-v2.md 작성 완료 (A9)

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

**파일**: `scripts/analyze_saturation.py` [NEW] (API 미호출, 기존 데이터 분석)

- [ ] P6-A1 완료 — commit: TBD

---

### P6-A2 Plateau-driven re-seed `[M]`

**전제**: A1 root cause = 신규 entity/topic 부재 확인 시 실행

**파일**: `src/nodes/seed.py` 확장

**요건**:
- plateau 감지 후 N cycle (기본 3) 경과 시 re-seed 트리거
- `plateau_detector.py` re-seed flag 신호 활용
- re-seed pack = LLM-driven: 현재 skeleton의 미충족 axis를 입력으로 신규 seed 생성
- 생성된 seed → 다음 cycle plan에 반영 (Gap-driven 원칙 준수)

- [ ] P6-A2 완료 — commit: TBD

---

### P6-A3 Field 다양화 강화 `[M]`

**전제**: A1 root cause = 동일 entity에 편중된 field 확인 시 실행

**파일**: `src/nodes/plan.py` 확장

**요건**:
- entity_key별 미충족 field 목록 계산 (skeleton field 선언 대비 KU 실제 field 분포)
- 미충족 field를 우선 GU 생성 대상으로 지정
- plan target 선택 시 field 다양화 가중치 적용 (기존 novelty 가중치와 병행)

- [ ] P6-A3 완료 — commit: TBD

---

### P6-A4 Active KU 재해소 `[M]`

**전제**: A1 root cause = stale/disputed KU가 GU 생성을 막고 있는 경우

**파일**: `src/nodes/critique.py` 확장

**요건**:
- disputed KU 중 evidence가 충분한 것 → auto-resolve 또는 GU 재생성
- stale KU 중 observed_at이 오래된 것 → refresh GU 재투입 (1회 refresh 후에도 stale 지속 시 재투입)
- 재투입 횟수 제한: KU당 최대 3회 (무한 루프 방지)

- [ ] P6-A4 완료 — commit: TBD

---

## Stage A-Outside: Stage E 보강

### P6-A5 Universe probe slug 정규화 `[M]`

**배경**: D-151 확정 — stage-e-on c11-15 growth 0.5/cyc는 probe slug collision 때문

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

### P6-A7 Exploration pivot 50c 발동 검증 `[S]`

**배경**: 15c window만 확인 — pivot 조건(low_novelty × 5c)이 50c에서 실제 발동하는지 미검증

**파일**: A8 trial 결과 기반 (별도 코드 없음)

**요건**:
- A8 50c trial의 `pivot_history` 확인 → 발동 여부 기록
- 미발동 시 조건 완화 검토 (context.md 결정사항 기록)

- [ ] P6-A7 완료 — commit: TBD (A8 후 확인)

---

## Stage A-Gate: 50c Trial

### P6-A8 stage-e-on-50c trial 생성 + 실행 `[L]`

> **API 비용 주의**: 실행 전 사전 확인 필수 (≈ $3~5 예상)

**파일**: `bench/silver/japan-travel/p6a-stage-e-on-50c/` [NEW]

**요건**:
- silver-trial-scaffold skill로 trial 생성
- `--external-anchor --cycles 50` 실행
- 중간 체크포인트: 25c 후 KU/gap_resolution 확인 → 계속 여부 결정
- 완료 후 readiness-report.md 작성

**목표 지표**:
- KU ≥ 250
- gap_resolution ≥ 0.85
- collision_active = 0 or stable

- [ ] P6-A8 완료 — commit: TBD

---

### P6-A9 COMPARISON-v2.md 작성 `[S]`

**파일**: `bench/japan-travel-external-anchor/COMPARISON-v2.md` 또는 `bench/silver/japan-travel/COMPARISON-v2.md`

**내용**:
- 15c vs 50c KU 성장률 비교 (per-window)
- stage-e-on vs stage-e-off 50c 비교
- P6-A5/A6 fix 효과 (collision_active, accept rate 변화)
- Exploration pivot 발동 여부
- P6-A gate 달성 여부 판정

- [ ] P6-A9 완료 — commit: TBD

---

## Stage B: Performance Optimization

### P6-B1 LLM 호출 batch `[L]`

**파일**: `src/adapters/llm_adapter.py`

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

- [ ] **X1** P6-A gate 완료 후 `bench/silver/INDEX.md` 에 p6a-stage-e-on-50c trial row 추가
- [ ] **X3** `schemas/kb-export.schema.json` positive + negative 테스트 (C1 포함)
- [ ] **X4** `src/kb/__init__.py` 생성 확인
- [ ] **X6** P6 완료 시 masterplan §8 리스크 레지스터 재평가
