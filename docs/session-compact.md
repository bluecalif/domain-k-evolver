# Session Compact

> Generated: 2026-04-18
> Source: Conversation compaction via /compact-and-go

## Goal

P6-A Plan 강화 — 사용자 피드백 3개 항목 검증 후 Forecastability F-Gate 신설 및 dev-docs 반영

## Completed

- [x] **실 데이터 분석 (bench 조사)**
  - stage-e-on/off trajectory.csv 비교: c10-c13 gap_map 완전 동결 확인 (open=20, resolved=76 불변 4사이클)
  - p2-smart-remodel 분석: c10 Remodel 발동 (exploration_drought, 67 merges) + c15 1회 = 15c 내 2회
  - LLM 단발 호출 지점 확정: `src/nodes/collect.py:130` (GU당 parse invoke)
  - 임계값 하드코딩 실측: `src/orchestrator.py:454-458` (GROWTH_STAGNATION=5, DROUGHT=30), `src/nodes/exploration_pivot.py:25-26` (WINDOW=5, THRESHOLD=0.1)
  - `tests/test_nodes/test_exploration_pivot.py` 에 synthetic `_stagnant_state` 주입 패턴 존재 확인

- [x] **Plan 파일 작성** — `C:\Users\User\.claude\plans\a10-p2-remodel-indexed-duckling.md` (F-Gate 전체 설계)

- [x] **P6 dev-docs 업데이트** (6개 파일)
  - `dev/active/phase-si-p6-consolidation/si-p6-consolidation-plan.md` — pain points 업데이트 + Stage 재구조화 (Forecastability 추가) + task 재번호 (A1~A13) + 위험 목록 보강
  - `dev/active/phase-si-p6-consolidation/si-p6-consolidation-tasks.md` — A1~A13 전면 재작성 (20 tasks), F-Gate 조건 추가, A7~A11 상세 spec
  - `dev/active/phase-si-p6-consolidation/si-p6-consolidation-context.md` — D-158~D-161 추가, 파일 참조 갱신, F-Gate 임계치 표 추가
  - `dev/active/project-overall/project-overall-tasks.md` — P6-A 목록 A1~A13 반영
  - `dev/active/project-overall/project-overall-context.md` — D-158~D-161 추가
  - `dev/active/project-overall/project-overall-plan.md` — P6 개요 Forecastability 섹션 추가

## Current State

**브랜치**: `main`
**최신 commit**: `ce5ebba` (`[si-p6] session-compact 최종 갱신`)
**테스트**: **821 passed** (3 skipped)

### P6 task 구조 (개정 후)

| Stage | Tasks | Size |
|-------|-------|------|
| P6-A Inside (A1~A4) | KU saturation 진단 + re-seed + field 다양화 + KU 재해소 | M×4 |
| P6-A Outside (A5~A6) | probe slug 정규화 + accept rate 튜닝 | M+S |
| **P6-A Forecastability (A7~A11)** | Remodel config 외부화 + Pivot config 외부화 + Pivot 단위테스트 + trigger telemetry + F-Gate 판정 | S×3+M×2 |
| P6-A Gate (A12~A13) | 50c trial + COMPARISON-v2.md | L+S |
| P6-B (B1~B3) | LLM batch + state_io delta + wall_clock | L+M+S |
| P6-C (C1~C4) | external schema + packaging + query API + operator guide | M×3+S |
| **합계** | **20 tasks** | S:7 M:11 L:2 |

### Changed Files (이번 세션)

- `dev/active/phase-si-p6-consolidation/si-p6-consolidation-plan.md` — F-Gate 추가, A1~A13 재번호, 위험/의존성 보강
- `dev/active/phase-si-p6-consolidation/si-p6-consolidation-tasks.md` — 전면 재작성 (20 tasks)
- `dev/active/phase-si-p6-consolidation/si-p6-consolidation-context.md` — D-158~D-161, F-Gate 임계치
- `dev/active/project-overall/project-overall-tasks.md` — P6-A A1~A13 반영
- `dev/active/project-overall/project-overall-context.md` — D-158~D-161
- `dev/active/project-overall/project-overall-plan.md` — P6 개요 갱신

## Remaining / TODO

- [ ] **미커밋 변경사항 커밋** — `[si-p6] P6-A 재구조화: F-Gate + A1~A13 재번호 (D-158~D-161)`
- [ ] **session-compact.md 갱신 커밋** — `[si-p6] session-compact 갱신`

### P6-A 착수 대기 (커밋 후)

- [ ] **P6-A1**: KU saturation 진단 스크립트 작성 (`scripts/analyze_saturation.py`)
  - gap_map delta=0 cycle 수 측정 포함
  - stage-e-on/off/p2-remodel 비교
- [ ] **P6-A2~A4**: A1 root cause 기반 Inside fix
- [ ] **P6-A5~A6**: Stage E 보강
- [ ] **P6-A7~A11**: Forecastability F-Gate (config 외부화 → trigger telemetry → 15c rerun → forecast → 판정)
- [ ] **P6-A12**: stage-e-on 50c trial (F-Gate PASS 이후, API 비용 사전 확인 필수)
- [ ] **P6-A13**: COMPARISON-v2.md

## Key Decisions

### 핵심 피드백 검증 결과 (2026-04-18)

| 항목 | 확인된 사실 |
|------|-------------|
| stage-e-on 0.5/cyc 원인 | probe slug collision 단독 아님. c10-c13 gap_map 완전 동결 (4사이클 open=20 불변) — core loop 마비 |
| LLM 단발 호출 | `src/nodes/collect.py:130` — GU당 parse invoke (claim→KU 변환 아님) |
| Exploration Pivot 50c 미검증 | 조건(WINDOW=5 연속 <0.1)이 15c 내 달성 불가 구조 → **50c 이전에 15c 내 검증 필수** |
| stage-e-off 4.0 vs p2-remodel 5.2 | p2-remodel c10 Remodel 발동(67 merges)이 원인. remodel 없이는 saturation 불가피 |
| 5.2/cyc 지속 가능성 | Remodel event 단발에 의존 → 장기 보장 없음. Forecast 필요 |

### 신규 결정사항

| # | 결정 |
|---|------|
| D-158 | Forecastability F-Gate 신설 (A7~A11) — 50c A12 선행 조건 |
| D-159 | Remodel/Pivot 임계값 config 외부화 필수 (`SmartRemodelConfig`, `ExternalAnchorConfig.novelty_*`) |
| D-160 | Trigger telemetry JSON 필드 emit (`trigger_event` optional) — log 파싱 금지 |
| D-161 | Forecast 모델 = 선형/지수 projection + damping + bootstrap confidence 한정 (블랙박스 금지) |

### F-Gate 판정 기준 (A11)
- Remodel ≥ 2회 + Pivot ≥ 1회 실발동 (15c rerun)
- forecast c16-c50: Remodel ≥ 4회 + Pivot ≥ 2회 + confidence ≥ 0.6
- 미달 시 A2~A6 재설계 루프 (A12 50c 진행 차단)
- 비용: 15c rerun ≈ $1 (50c $3~5 ROI 보증)

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

- **P6 dev-docs**: `dev/active/phase-si-p6-consolidation/` — plan/context/tasks 참조
- **분석 대상 데이터 (A1용)**:
  - `bench/silver/japan-travel/stage-e-on/trajectory/trajectory.csv` (15c)
  - `bench/silver/japan-travel/stage-e-off/trajectory/trajectory.csv` (15c)
  - `bench/silver/japan-travel/p2-smart-remodel-trial/trajectory/trajectory.csv` (15c)
  - `bench/silver/japan-travel/*/state-snapshots/cycle-N-snapshot/gap-map.json` (gap_map delta 측정)
  - `bench/japan-travel-external-anchor/COMPARISON.md` (P4 분석)
- **핵심 코드 위치**:
  - `src/orchestrator.py:454-503` (_should_remodel, 임계값 하드코딩)
  - `src/nodes/exploration_pivot.py:25-90` (WINDOW/THRESHOLD 하드코딩)
  - `src/nodes/collect.py:130` (LLM 단발 호출 지점)
  - `tests/test_nodes/test_exploration_pivot.py` (synthetic injection 패턴)
- **스크립트 정책**: `scripts/analyze_saturation.py` 분석 스크립트 (API 미호출) 허용. A11에서 forecast 모드 확장.
- **API 비용 주의**: A11 15c rerun ≈ $1 사전 확인 필수 / A12 50c ≈ $3~5 사전 확인 필수 + **F-Gate PASS 선행 조건**
- **테스트 현황**: 821 passed, 3 skipped. 목표: ≥ 840
- **미커밋 상태**: 6개 dev-docs 파일 수정됨. 커밋 먼저.

## Next Action

**Step 1: 미커밋 변경사항 커밋**

```bash
git -C "C:/Users/User/Learning/KBs-2026/domain-k-evolver" add \
  dev/active/phase-si-p6-consolidation/ \
  dev/active/project-overall/
git -C "C:/Users/User/Learning/KBs-2026/domain-k-evolver" commit -m "[si-p6] P6-A 재구조화: F-Gate + A1~A13 재번호 (D-158~D-161)"
```

**Step 2: session-compact.md 커밋**

```bash
git -C "C:/Users/User/Learning/KBs-2026/domain-k-evolver" add docs/session-compact.md
git -C "C:/Users/User/Learning/KBs-2026/domain-k-evolver" commit -m "[si-p6] session-compact 갱신 (P6-A F-Gate 재구조화 완료)"
```

**Step 3: P6-A1 착수 — KU saturation 진단 스크립트 작성**

`scripts/analyze_saturation.py` 작성:
1. stage-e-on/off/p2-remodel 세 trial의 trajectory.csv 로드
2. window별 KU 성장률 계산 (c1-5, c6-10, c11-15)
3. **gap_map delta = 0 cycle 수** 측정 (state-snapshots 순회)
4. parse_yield 추이 (GU당 claims 생성 수)
5. GU 생성/해소 비율 추이
6. entity dedup 비율
7. KU 카테고리별 Gini 추이
결과 → `dev/active/phase-si-p6-consolidation/debug-history.md` 기록 → A2~A6 scope 결정
