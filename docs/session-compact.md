# Session Compact

> Generated: 2026-04-18
> Source: Conversation compaction via /compact-and-go

## Goal

Dashboard 개선 + P4 평가 + 프로젝트 Phase 재구조화 계획 수립.

## Completed

- [x] **Dashboard: trial 드롭다운 추가** — `bench/silver/japan-travel/` 아래 모든 trial을 드롭다운으로 전환 가능 (`?trial=` query param)
- [x] **stage-e-off/on 이동** — `bench/japan-travel-external-anchor/` → `bench/silver/japan-travel/` (각각 개별 trial로 분리)
- [x] **Loader: conflict-ledger.json 버그 수정** — 언더스코어(`conflict_ledger.json`) 대신 하이픈(`conflict-ledger.json`) 모두 지원. 12/13 trial에서 ledger 복구
- [x] **Loader: trajectory.json fallback** — P5 이전 trial (12개) 이 cycles.jsonl 없어도 자동 변환해 dashboard 표시
- [x] **Loader: load_ku_progression()** — KU snapshot에서 cycle별 KU/category/Gini 계산
- [x] **Loader: derive_remodel_events()** — cycles에서 mode='jump' or hitl_queue.remodel=1 이벤트 사후 추출
- [x] **Timeline 보강** — KU & Category Growth 차트, Variability & Diversity 차트(novelty + external_novelty + category_gini), Quality Metrics(+ gap_resolution 추가), Gap Map
- [x] **Overview 보강** — KU Evolution 섹션 추가 (Total KU, KU Growth/5c, Categories, Category Gini, External Novelty)
- [x] **Remodel Review 보강** — derived events 테이블 (mode='jump' + delta_gap_resolved + delta_res_rate)
- [x] **테스트 추가** — `tests/test_obs/test_loader_legacy_fallback.py` 24개 테스트 (5개 추가)
- [x] **P4 재평가** — COMPARISON.md 정독 → VP4 4/5 PASS 확인, narrow goal 달성
- [x] **KU saturation 분석** — 50c 외삽 데이터 도출
- [x] **Phase 재구조화 계획 수립** — plan 파일 작성 + 사용자 의사결정 4개 수집

## Current State

**브랜치**: `main`  
**서버**: PID 15988, `http://127.0.0.1:8000`  
**테스트**: **24 passed** (test_obs/)

### 사용자 확정 결정

| 결정 | 내용 |
|------|------|
| 기존 P6 (Multi-Domain) | **M1 으로 분리 (보류)** — task 보존 |
| 신규 P6 순서 | **A → B → C** (Pain Point 먼저) |
| KU saturation 위치 | **신규 P6-A 안에 흡수** |
| P5 Gate 판정 시점 | **P6 재구조화 전에 먼저** |

### Changed Files

- `src/obs/dashboard/loader.py` — conflict-ledger 양방향 호환, _from_trajectory, load_ku_progression, derive_remodel_events 추가
- `src/obs/dashboard/app.py` — trial 드롭다운, KU/Gini series, remodel events 라우트
- `src/obs/dashboard/templates/base.html` — trial 드롭다운 select 추가
- `src/obs/dashboard/templates/overview.html` — KU Evolution 섹션
- `src/obs/dashboard/templates/timeline.html` — 차트 4개로 확장
- `src/obs/dashboard/templates/remodel.html` — derived events 테이블
- `tests/test_obs/test_loader_legacy_fallback.py` — 5개 테스트 추가
- `bench/silver/japan-travel/stage-e-off/` — 이동됨
- `bench/silver/japan-travel/stage-e-on/` — 이동됨
- `C:\Users\User\.claude\plans\crystalline-imagining-snowflake.md` — Phase 재구조화 plan

## Remaining / TODO

- [x] **미커밋 변경사항 commit** — commit `009e52f` (dashboard 개선 279 files)
- [x] **P5 Gate 공식 판정** — **GATE PASS** (`7ed21b5`). G5-1~6 전항목, S10, 821 tests
- [x] **project-overall + masterplan 갱신** — P6 → M1 분리 + 신규 P6 추가 (`bfa6d9e`)
- [x] **신규 P6 dev-docs 생성** — `dev/active/phase-si-p6-consolidation/` 생성 (`bfa6d9e`)
- [ ] **기존 P6 디렉토리 rename** — `phase-si-p6-multidomain/` 디렉토리 미존재 (skip)
- [ ] **신규 P6 착수** — A1 (KU saturation 진단) 시작

## Key Decisions

### Dashboard
- **Gini 정의**: variability가 아니라 *diversity/concentration* 지표. `category_gini (1=편중, 0=균등)` 명시
- **legacy trial 처리**: trajectory.json → cycles.jsonl 스키마 메모리 변환 (파일 생성 없음). phase="legacy" 라벨
- **conflict-ledger**: 하이픈(실제 P1-B1 schema)과 언더스코어(P5 초기 버그) 양쪽 지원

### P4 재평가
- **VP4 PASS 확인**: D-147~D-150 fix 적용된 commit `10bc58a` 기준 4/5 PASS
- **Stage E on KU < off (106 < 116)**: probe overhead trade-off, 의도된 동작. gap_resolution 향상으로 보상 (0.789→0.813)
- **Overall Gate FAIL**: VP2 gap_resolution 0.85 미달 — Stage E 책임 아님, core loop 문제
- **잔존 이슈**: D-151 (universe probe slug collision), exploration pivot 50c 검증 필요

### KU Saturation
| Trial | c1-5/cyc | c11-15/cyc | 50c 외삽 |
|---|---|---|---|
| stage-e-off | 11.0 | 4.0 | 256 |
| stage-e-on | 9.5 | **0.5** | 124 ⚠️ |
| p2-smart-remodel | 11.0 | 5.2 | **336** ✅ |
- P2 remodel 단독으로는 50c sustained growth 부족 → P6-A Inside 작업 필요

### 신규 P6 = "Consolidation & Knowledge DB Release"
- **P6-A (Inside)**: KU saturation 진단, re-seed, field 다양화, stale 재해소
- **P6-A (Outside/Stage E)**: D-151 slug 정규화, probe accept rate 튜닝, pivot 50c 검증
- **P6-B**: LLM batch, state_io 증분 저장, wall_clock 측정
- **P6-C**: japan-travel KB external packaging + query API + operator guide

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

- **P5 완료 상태**: 코드+docs 완료. Gate 공식 판정(silver-phase-gate-check) 이 최우선
- **Dashboard 서버**: `python -m src.obs.dashboard.app --trial-root bench/silver/japan-travel/p0-20260412-baseline`
- **미커밋 변경**: dashboard 관련 파일 전체 (loader.py, app.py, 4개 templates, test file, bench 디렉토리 이동)
- **plan 파일**: `C:\Users\User\.claude\plans\crystalline-imagining-snowflake.md` 참조
- **bench/japan-travel-external-anchor/**: stage-e-off/on 이동 후 COMPARISON.md만 남아있음 (빈 디렉토리 아님)
- **API 비용 주의**: 실 trial 재실행 전 사전 확인 필수 (feedback_api_cost_caution)

## Next Action

**Step 1: 미커밋 변경사항 commit**

```bash
git -C /c/Users/User/Learning/KBs-2026/domain-k-evolver add \
  src/obs/dashboard/loader.py \
  src/obs/dashboard/app.py \
  src/obs/dashboard/templates/ \
  tests/test_obs/test_loader_legacy_fallback.py \
  bench/silver/japan-travel/stage-e-off \
  bench/silver/japan-travel/stage-e-on
git -C /c/Users/User/Learning/KBs-2026/domain-k-evolver commit -m "[si-p5] Dashboard 개선: trial 드롭다운 + legacy 호환 + KU/Gini/Remodel 뷰 추가"
```

**Step 2: P5 Gate 공식 판정**

`silver-phase-gate-check` skill 실행

**Step 3: Phase 재구조화 + 신규 P6 dev-docs**

1. project-overall-tasks.md / project-overall-plan.md / masterplan-v2.md 갱신
2. `dev-docs` skill → phase-si-p6-consolidation
3. `phase-si-p6-multidomain/` → `phase-m1-multidomain/` rename
