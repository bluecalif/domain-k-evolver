# Session Compact

> Generated: 2026-04-14
> Source: Gap-Resolution Investigation Phase **완료** (12/12 tasks). 다음: SI-P2 remodel on/off 비교 실험 착수

## Goal

SI-P3R Gate PASS 후 발견된 gap_resolution_rate 병목 (0.517@15c) 원인 특정 + 수정. 이 세션에서 Stage A~D 전체 완료.

## Completed

### Gap-Res Investigation (12/12 tasks, 8 commits)

- [x] **Phase 착수 커밋** (`46dfc16`): dev-docs + project-overall 동기화 (D-126)
- [x] **Stage A — 진단 로깅 + 정적 분석**
  - A1 (`fc1d994`): `src/nodes/collect.py` parse_yield 로깅 — `_parse_claims_llm` 반환 지점 + `collect_node` 종료 시 누적 분포
  - A2 (`a61b5d8`): `src/nodes/integrate.py` integrate_result 로깅 — resolved/no_source_gu/invalid_result/other 4분류
  - A3 (`acbda34`): `scripts/analyze_p3r_gap.py` 신규 — KU evidence 분포, GU resolved_by 검증, cycle별 target/resolve
- [x] **Stage B — Primary Fix** (D-129 확정)
  - B1+B2 (`2a01197`): `src/nodes/mode.py` target_count cap 제거 (Phase 5 `b122a23` 복원) + regression guard 테스트 2개 추가
  - B3: `src`/`tests` 전수 검색 결과 추가 수정 없음
- [x] **Stage C — 재현 Trial** (`9d9c8c5`)
  - `bench/silver/japan-travel/gap-res-fix-trial/` 15c 실행 → **Gate PASS**
  - `gap_resolution_rate: 0.517 → 0.990` (+91%), `gu_open final: 73 → 1`
  - readiness-report.md 작성 (before/after 비교)
- [x] **Stage D — Phase 종결** (`d96705d`)
  - D-129 확정 / D-130 Secondary 실체 없음 / D-131 P2 착수 조건 충족
  - debug-history.md, tasks.md, project-overall-context.md 갱신
  - MEMORY.md: Gap-Res 완료 등록 + D-129/130/131 추가

### 테스트 상태
- 608 → **610 passed** (+2 regression guards), 3 skipped

## Current State

- **Git**: branch `main`, 최신 커밋 `d96705d`
- **Phase 상태**:
  - SI-P3R ✅ 완료
  - **Gap-Res Investigation ✅ 완료** (2026-04-14)
  - SI-P2 REVOKED → **재판정 가능** (D-131 충족)
- **Clean working tree**: `bash.exe.stackdump`만 untracked (shell crash dump, 삭제 대상)

### Changed Files (이 세션에서 커밋됨)
- `src/nodes/collect.py` — parse_yield 로깅 (A1)
- `src/nodes/integrate.py` — integrate_result 4분류 로깅 (A2)
- `scripts/analyze_p3r_gap.py` — 신규 (A3)
- `src/nodes/mode.py` — target_count cap 제거 (B1)
- `tests/test_nodes/test_mode.py` — regression guard 2개 (B2)
- `bench/silver/japan-travel/gap-res-fix-trial/` — 전체 신규 (C)
- `dev/active/phase-gap-resolution-investigation/*.md` — 4개 파일 업데이트
- `dev/active/project-overall/project-overall-context.md` — D-129~131 확정 반영
- `docs/session-compact.md` — 본 파일

## Remaining / TODO

### 즉시 다음 단계

- [x] **SI-P2 remodel on/off 비교 실험** (D-127, D-131) — **Gate PASS** (2026-04-15)
  - Smart Remodel Criteria 구현 (D-132): 3-way OR (growth_stagnation, exploration_drought, audit_critical)
  - Merge 과다 수정 (D-133): min_overlap_count ≥ 2
  - 15c trial: remodel cycle 10/15 자연 발동, category_gini +180%, KU +23%
  - Gini criteria → P4 연기 (D-134)

### 후속

- [ ] SI-P4~P6
- [ ] `bash.exe.stackdump` 삭제 또는 gitignore

### Out of scope (본 Phase에서 종결)
- Secondary 병목 처리 — D-130으로 실체 없음 판명, 추가 작업 불필요
- VP2 R3 multi_evidence (0.758 < 0.80) — Gap-Res 범위 밖, 별도 관심사
- VP3 R6 closed_loop (0) — 별도 관심사

## Key Decisions

- **D-129 (확정)**: `target_count` cap은 Phase 5 (`b122a23`)에서 의도적 제거 — 재도입 금지. commit `2a01197`에서 Phase 5 공식 복원 + regression guard 테스트 추가
- **D-130 (확정)**: Secondary "52% conversion" 병목 실체 없음. snippet-first(1:N fan-out) 구조상 `resolved/claims` 분모가 구조적으로 낮음. `resolved/targets` ≈ 90-100%가 실제 지표. 추가 fix 불필요
- **D-131 (확정)**: Gap-Res PASS (0.99) 달성 → SI-P2 remodel on/off 비교 실험 착수 가능
- **D-132**: Smart Remodel Criteria — has_critical → 3-way OR (audit_critical, growth_stagnation KU<5/3c, exploration_drought GU<30/5c)
- **D-133**: merge min_overlap_count ≥ 2 필터 — 1-field overlap 과다 merge 방지
- **D-134**: Gini criteria는 P4 category management로 연기

### 가설 판정 요약 (B2)
- H1 (LLM parse 수율 낮음) → **기각**: parse_yield 로그 avg 3.5-5 claims/target 일관
- H3 (source_gu_id 변조) → **완전 기각**: integrate_result 전 cycle `no_source_gu=0`
- H2/H4 → 검증 불필요 (B1만으로 수렴)

## Context

다음 세션에서는 답변에 **한국어** 사용.

### 핵심 수치 (Before → After)

| 지표 | p3r-gate-trial-15c | gap-res-fix-trial | Δ |
|---|---|---|---|
| gap_resolution_rate | 0.517 | 0.990 | +91% |
| gu_open (final) | 73 | 1 | −98.6% |
| gu_resolved | 78 | 99 | +27% |
| KU active | 105 | 124 | +18% |
| Gate | FAIL | **PASS** | — |

### 핵심 코드 변경
- `src/nodes/mode.py:204-212` — `NORMAL_TARGET_CAP`, `JUMP_TARGET_CAP` 제거, `min(..., cap)` 제거
- `src/nodes/collect.py` — parse_yield 로깅 3 reset points + summary
- `src/nodes/integrate.py` — integrate_result 4-분류 카운터 + summary

### 제약
- **커밋 prefix**: 다음 Phase 부터는 `[si-p2]` 또는 상응
- **Bash 절대경로 필수**, `cd` 금지
- **PYTHONUTF8=1 + encoding='utf-8'** 명시
- **완료 요약**: what + so what(효과) 필수
- **API 비용 신중** (feedback_api_cost_caution.md): 새 trial 전 사용자 사전 확인
- **테스트 실제 경로 검증** (feedback_test_real_path.md)
- **Phase gate = 합성 E2E + 실 벤치 trial 필수** (feedback_phase_gate.md)

### 참조 파일
- `dev/active/phase-gap-resolution-investigation/` (4개 파일, 모두 Complete)
- `dev/active/phase-si-p2-remodel/` (기존 dev-docs, 재판정 전 검토 필요)
- `bench/silver/japan-travel/gap-res-fix-trial/readiness-report.md`
- `bench/silver/japan-travel/p3r-gate-trial-15c/` (before trial 보존)
- `scripts/analyze_p3r_gap.py` (정적 분석 도구, 재사용 가능)
- `docs/silver-masterplan-v2.md` (Silver 단일 진실 소스)
- MEMORY.md: Gap-Res 완료 등록, D-129/130/131 저장됨

### 최근 commit 체인
```
d96705d [gap-res] D3: Phase 종결 — D-129 확정, D-130 실체 없음, D-131 P2 착수 조건
9d9c8c5 [gap-res] C1+C2+C3: gap-res-fix-trial 15c Gate PASS, gap_res 0.517→0.99
2a01197 [gap-res] B1+B2: target_count cap 제거 (D-129) + regression guard
acbda34 [gap-res] A3: p3r 정적 분석 스크립트
a61b5d8 [gap-res] A2: integrate result 분포 로깅
fc1d994 [gap-res] A1: collect parse_yield 로깅
46dfc16 [gap-res] Phase 착수: dev-docs + project-overall 동기화 (D-126)
15ce9d5 [si-p3] D-120 historical evidence 보존 (D-122)
981ffd6 [si-p3r] T8: Gate PASS — 15c trial, acquisition 검증 기준 (D-125)
```

## Next Action

**SI-P2 remodel on/off 비교 실험 Phase 착수 준비**

1단계: 기존 dev-docs 상태 확인
```bash
ls -la "C:/Users/User/Learning/KBs-2026/domain-k-evolver/dev/active/phase-si-p2-remodel/"
```
- plan/context/tasks/debug-history 파일이 있는지 확인
- 내용이 D-127 (remodel on/off 비교로 재설계) 반영되었는지 검토

2단계: Phase 재설계 필요 여부 결정
- 기존 내용이 Remodel 단일 노드 구현 중심이라면 **비교 실험** 중심으로 재작성
- 신규 task 구조 제안: A (기존 코드 현황 파악) → B (비교 trial 2회 실행) → C (결과 분석 + Gate 판정) → D (Phase 종결)

3단계: 사용자와 Phase 범위 합의
- "기존 remodel 노드 유지한 채 on/off flag만 추가"인지 "remodel 재구현"인지 확인
- 비교 trial 비용 (15c × 2회 × ~$3 = ~$6) 사전 확인

**첫 명령**: 기존 SI-P2 dev-docs 읽고 상태 리포트 후 재설계 제안
