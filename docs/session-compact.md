# Session Compact

> Generated: 2026-04-14
> Source: Gap-Resolution Investigation Phase 착수 + dev-docs 생성 완료. 다음: Stage A1부터 실행

## Goal

SI-P3R Gate PASS 후 발견된 gap_resolution_rate 병목 (0.517@15c, Bronze P5 0.909 대비 -42%) 원인 특정 + 수정. 2개 독립 병목 확인, Phase 착수.

## Completed

- [x] **SI-P3R T8 커밋** (`981ffd6`): Gate PASS — 15c trial, acquisition 검증 기준 (D-125)
- [x] **D-120 historical evidence 커밋** (`15ce9d5`): p3-20260413-llm-diag/, p3-20260413-llm-verify/ 보존 (D-122)
- [x] **Primary 병목 근본 원인 확정**: commit `b12545d` [si-p3]에서 target_count cap (=10) regression 재도입 — Phase 5 (`b122a23`)에서 의도적으로 제거했던 공식을 무효화
- [x] **Secondary 병목 발견**: target 10개 중 resolve 3-7개 = 52% conversion rate. LLM parse 수율 추정
- [x] **Phase dev-docs 생성** (`dev/active/phase-gap-resolution-investigation/`):
  - plan.md (4 stages, 12 tasks, Size S:8 M:4)
  - context.md (B1/B2 병목 분석, git blame, 가설 H1~H4)
  - tasks.md (12 tasks 체크리스트)
  - debug-history.md (2 entries: Primary 확정, Secondary 가설)
- [x] **project-overall 동기화**:
  - plan.md: SI-P3R 완료 반영, 새 Phase 추가, 실행 순서 업데이트
  - context.md: dev-docs 테이블 업데이트, D-120~D-131 등록
  - tasks.md: Gap-Res Investigation 섹션 신설 (GR-A1~D3)

## Current State

- **Git**: branch `main`, latest commits:
  - `15ce9d5` [si-p3] D-120 historical evidence 보존 (D-122)
  - `981ffd6` [si-p3r] T8: Gate PASS — 15c trial, acquisition 검증 기준 (D-125)
- **Tests**: 608 passed, 3 skipped
- **Phase 상태**: SI-P3R ✅ 완료 | SI-P2 REVOKED (D-127) | **Gap-Res Investigation 착수**
- **Unstaged changes** (phase dev-docs + project-overall 갱신):
  - `dev/active/phase-gap-resolution-investigation/*.md` (4개 파일 신규)
  - `dev/active/project-overall/project-overall-plan.md`
  - `dev/active/project-overall/project-overall-context.md`
  - `dev/active/project-overall/project-overall-tasks.md`
  - `docs/session-compact.md` (본 파일)
- **Untracked**: `bash.exe.stackdump` (shell crash dump, gitignore 또는 삭제 대상)

### Changed Files (미커밋)
- `dev/active/phase-gap-resolution-investigation/phase-gap-resolution-investigation-plan.md` — 신규
- `dev/active/phase-gap-resolution-investigation/phase-gap-resolution-investigation-context.md` — 신규
- `dev/active/phase-gap-resolution-investigation/phase-gap-resolution-investigation-tasks.md` — 신규
- `dev/active/phase-gap-resolution-investigation/debug-history.md` — 신규
- `dev/active/project-overall/project-overall-plan.md` — 상태/Phase 구조 갱신
- `dev/active/project-overall/project-overall-context.md` — D-120~D-131 등록, dev-docs 테이블 갱신
- `dev/active/project-overall/project-overall-tasks.md` — Gap-Res 섹션 추가, Summary 갱신

## Remaining / TODO

### 즉시 다음 액션 (Next Action 참조)

- [ ] **Stage A 착수** — 진단 로깅 + 정적 분석 (재현 trial 전 가설 검증 준비)
  - GR-A1 [S]: `src/nodes/collect.py` parse_yield 로깅 (`gu=%s snippets=%d claims=%d`)
  - GR-A2 [S]: `src/nodes/integrate.py` integration_result 분포 로깅
  - GR-A3 [M]: 기존 15c trial 정적 분석 스크립트 (`scripts/analyze_p3r_gap.py`)

### 중기 단계

- [ ] **Stage B — Primary Fix** (target_count cap 제거, D-129)
  - GR-B1 [S]: `src/nodes/mode.py` Phase 5 복원 — NORMAL_TARGET_CAP/JUMP_TARGET_CAP 제거
  - GR-B2 [S]: `tests/test_mode.py` target_count 공식 테스트 갱신
  - GR-B3 [M]: 영향 테스트 전수 검사 + 수정 (grep `target_count`, `TARGET_CAP`)

- [ ] **Stage C — 재현 Trial** (API 비용 ~$1-3, 사전 확인 필수)
  - GR-C1 [M]: `bench/silver/japan-travel/gap-res-fix-trial/` 생성 + 15c 실행
  - GR-C2 [M]: trajectory before/after 비교 (p3r-gate-trial-15c vs gap-res-fix-trial)
  - GR-C3 [S]: readiness-report 작성

- [ ] **Stage D — Secondary 대응 결정**
  - GR-D1 [S]: B2 가설 H1~H4 확증 (Stage C 데이터 기반)
  - GR-D2 [S]: Secondary fix 본 Phase 내 적용 OR 별도 Phase 이관
  - GR-D3 [S]: Decision 문서화 (D-129~D-131) + Phase 종결

### 후속

- [ ] **커밋 필요**: phase dev-docs + project-overall 동기화를 `[gap-res] Phase 착수` 커밋으로 (Stage A 시작 전 권장)
- [ ] **SI-P2 재판정** (D-127/D-131): 본 Phase 결과 기준 착수 조건 결정
- [ ] **P4~P6**: P2 완료 후

## Key Decisions

- **D-125** (확정): P3R Gate PASS = acquisition 검증 기준. full readiness gate(VP2 gap_res)와 분리
- **D-126** (확정): gap_resolution 병목 별도 조사 필요 — remodel 이전에도 0.437@10c
- **D-127** (확정): P2 Gate는 remodel on/off 비교 실험으로 재설계
- **D-128** (확정): 우선순위 res_rate → P2 → P4~P6
- **D-129** (예정, Stage B 완료 시): target_count cap은 Phase 5(`b122a23`)에서 의도적 제거 — 재도입 금지
- **D-130** (예정, Stage D): LLM parse 수율 대응 방향 — 본 Phase fix OR 별도 Phase
- **D-131** (예정, Stage D): SI-P2 재판정 착수 조건 (Gap-Res 결과 기준)
- **조사 전략 (B)**: Primary fix + 진단 로깅을 함께 적용한 후 1회 trial로 B1 효과 + B2 데이터 동시 확보 — API 비용 최소화

## Context

다음 세션에서는 답변에 **한국어** 사용.

### 두 개의 병목 (context.md 요약)

| | Primary (B1) | Secondary (B2) |
|---|---|---|
| 병목 | target_count cap=10 | target→resolve 전환 52% |
| 원인 | `b12545d` commit regression (D-37 cap 재도입) | LLM parse 수율 (추정 H1) |
| 수정 난이도 | 1-line (Phase 5 복원) | 조사 필요 (로깅 추가) |
| 예상 효과 | open=67 기준 target 10→34 | 현 50% → ?% |
| Risk | LLM 비용 3x↑ (G1) | 미정 |

### Git blame 핵심 (mode.py:204-212)

```python
# 현재 (regression)
NORMAL_TARGET_CAP = 10
JUMP_TARGET_CAP = 10
target_count = min(max(10, ceil(open_count * 0.5)), JUMP_TARGET_CAP)  # jump
target_count = min(max(4, ceil(open_count * 0.4)), NORMAL_TARGET_CAP)  # normal

# Phase 5 `b122a23` 원본 (B1 복원 대상)
target_count = max(10, ceil(open_count * 0.5))  # jump
target_count = max(4, ceil(open_count * 0.4))   # normal
```

### Secondary 가설 (H1~H4)

- **H1 (유력)**: LLM parse가 target field를 snippet에서 못 찾아 `[]` 반환
- **H2**: query 품질 — `{slug} {field}` 단순 조합이 관련 snippet 미회수
- **H3**: LLM이 source_gu_id를 누락/변조 (prompt에 hard-coded지만 준수율)
- **H4 (약함)**: conflict_hold로 open 유지 — conflict_rate 낮아 주원인 아님

### 핵심 코드 경로
- `src/nodes/mode.py:204-212` — target_count cap (수정 대상)
- `src/nodes/collect.py:109-145` — `_parse_claims_llm` (A1 로깅 대상)
- `src/nodes/integrate.py:500-505` — GU resolve 1:1 조건 (A2 로깅 대상)
- `src/utils/metrics.py:35-56` — gap_resolution_rate 산식 `resolved / (resolved + open)`

### 15c trial 핵심 데이터
- 150 target 시도 (10×15) → 78 resolve = 52% conversion
- cycle 10: open=67, resolved=52, target=10 고정
- active KU 105개, 평균 evidence 3.76개 (누적 395 links)
- path: `bench/silver/japan-travel/p3r-gate-trial-15c/trajectory/trajectory.csv`

### 제약
- **커밋 prefix**: `[gap-res]` (본 Phase)
- **Bash 절대경로 필수**, `cd` 금지
- **PYTHONUTF8=1 + encoding='utf-8'** 명시
- **완료 요약**: what + so what(효과) 필수
- **API 비용 신중** (feedback_api_cost_caution.md): Stage C trial 전 사용자 사전 확인
- **테스트 실제 경로 검증** (feedback_test_real_path.md): mock/fallback만 테스트 금지
- **Phase gate = 합성 E2E + 실 벤치 trial 필수** (feedback_phase_gate.md)

### 참조 파일
- `dev/active/phase-gap-resolution-investigation/` (4개 파일)
- `docs/silver-masterplan-v2.md` (Silver 단일 진실 소스)
- commit `b122a23` (Phase 5 원형 — B1 복원 원본)
- commit `b12545d` (regression 도입 — 롤백 대상)
- commit `981ffd6` (SI-P3R T8 Gate PASS)
- commit `15ce9d5` (D-120 historical evidence)

## Next Action

**1단계: phase dev-docs + project-overall 동기화 커밋 (Stage A 착수 전)**

```bash
git -C "C:/Users/User/Learning/KBs-2026/domain-k-evolver" add \
  dev/active/phase-gap-resolution-investigation/ \
  dev/active/project-overall/ \
  docs/session-compact.md
git -C "C:/Users/User/Learning/KBs-2026/domain-k-evolver" commit -m "[gap-res] Phase 착수: dev-docs + project-overall 동기화 (D-126)"
```

**2단계: Stage A1 — `src/nodes/collect.py` parse_yield 로깅**

- `_parse_claims_llm` 내부에 `logger.info("parse_yield: gu=%s snippets=%d claims=%d")` 추가
- `collect_node` 종료 시 누적 분포 (avg claims/target, zero_claims_ratio) 로그
- 기존 로깅과 prefix 구분 (`parse_yield:`)
- Commit: `[gap-res] A1: collect parse_yield 로깅`

**3단계: Stage A2 — `src/nodes/integrate.py` integration_result 분포 로깅**

- cycle 종료 시 Counter 집계 → logger.info
- GU resolve 실패 원인 3분류 (no_source_gu_id / invalid_result / other)
- Commit: `[gap-res] A2: integrate result 분포 로깅`

**4단계: Stage A3 — 기존 15c trial 정적 분석 스크립트**

- `scripts/analyze_p3r_gap.py` 신규 (CLAUDE.md scripts policy: 분석용 신규 허용)
- 입력: `bench/silver/japan-travel/p3r-gate-trial-15c/`
- 출력: KU evidence 분포, GU resolved_by 매핑 검증, cycle별 target/resolve 비교
- Commit: `[gap-res] A3: p3r 정적 분석 스크립트`
