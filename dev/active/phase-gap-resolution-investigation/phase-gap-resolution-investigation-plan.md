# Phase: Gap-Resolution 병목 조사
> Last Updated: 2026-04-14
> Status: Planning

## 1. Summary (개요)

**목적**: SI-P3R Gate PASS 후 발견된 gap_resolution_rate 병목 (0.517@15c, Bronze P5 대비 0.909)의 근본 원인을 특정하고 수정안을 도출한다.

**범위**:
- Primary bottleneck 수정 (target_count cap regression)
- Secondary bottleneck 조사 (target→resolve conversion loss ~50%)
- 재현 trial을 통한 수정 효과 검증

**예상 결과물**:
- `src/nodes/mode.py` — Phase 5 target_count 공식 복원
- `src/nodes/collect.py`, `src/nodes/integrate.py` — 진단 로깅 추가
- 재현 trial `bench/silver/japan-travel/gap-res-fix-trial/`
- readiness-report.md + 수정 전후 비교 분석
- Secondary bottleneck에 대한 fix 또는 별도 Phase 이관 결정

## 2. Current State (현재 상태)

### 진입 상태 (SI-P3R 완료 후)
- **commit**: `15ce9d5` [si-p3] D-120 historical evidence 보존 (+ `981ffd6` T8 PASS)
- **tests**: 608 passed, 3 skipped
- **Phase 상태**: SI-P3R **완료** (Gate PASS, D-125) | SI-P2 **REVOKED** (재판정 필요, D-127)
- **메트릭 상태**: gap_resolution_rate 0.517@15c (p3r-gate-trial-15c)

### 문제 발견 경로
1. SI-P3R T8 Gate trial 15c 실행 → VP2 4/6 (gap_res 0.517)
2. D-125 판정: P3R Gate는 acquisition 검증 기준이므로 PASS (gap_res 병목은 분리)
3. D-126: gap_resolution 병목 별도 조사 필요
4. 본 Phase 착수 → 두 독립 병목 발견

### 확정된 사실 (context.md 참조)

**B1 — Primary (throughput cap)**:
- `src/nodes/mode.py:204-212`에 `NORMAL_TARGET_CAP=10`, `JUMP_TARGET_CAP=10` 적용
- Phase 5 (commit `b122a23`)에서 **의도적으로 제거**했던 cap이 SI-P3 디버그 commit (`b12545d`)에서 재도입됨 = regression
- 영향: open=70이어도 target_count=10만 선정 → 이론 상한 10 resolve/cycle

**B2 — Secondary (conversion rate)**:
- 15c trial 누적: 150 target 시도 → 78 resolve = **52% conversion**
- 원인 가설 H1~H4 (context.md §B2)
- 유력: H1 (LLM parse가 target field를 snippet에서 찾지 못해 `[]` 반환)

## 3. Target State (목표 상태)

### 성공 기준
- [ ] Primary fix 적용 → target_count 공식이 Phase 5 상태로 복원
- [ ] Secondary 원인 확증 (H1~H4 중 주원인 특정)
- [ ] 재현 trial 결과: **gap_resolution ≥ 0.85@15c** (Bronze P5 수준 근접)
- [ ] LLM 비용 ≤ baseline × 2.5 (R1 리스크 가드)
- [ ] 기존 608 테스트 유지 + 신규 진단 테스트 추가
- [ ] Secondary 대응: 본 Phase 내 fix OR 별도 Phase 이관 결정 문서화

### 최종 산출물
- 코드: `mode.py` 복원, `collect.py`/`integrate.py` 진단 로깅
- Trial: `bench/silver/japan-travel/gap-res-fix-trial/` + readiness-report
- 결정: D-129 (cap regression 확정), D-130 (LLM parse 수율 대응), D-131 (SI-P2 착수 조건)

## 4. Implementation Stages

### Stage A — 진단 로깅 + 기존 데이터 재분석 (선행)

목적: Secondary bottleneck (B2)의 원인 확증 — 재현 trial 전에 가설 검증.

**A1**. `src/nodes/collect.py` 진단 로깅 강화
- `_parse_claims_llm` 수율 측정: target GU별 `(snippets_count, claims_count)` 기록
- logger.info 레벨로 `parse_yield: gu=%s snippets=%d claims=%d` 추가
- `collect` 종료 시 누적 분포 로그 (avg claims/target, 0-claim ratio)

**A2**. `src/nodes/integrate.py` integration_result 분포 로깅
- cycle 종료 시 `integration_results: {added: N, updated: N, conflict_hold: N, ...}` 로그
- GU resolve 실패 원인 분류 (source_gu_id 없음 / integration_result 부적합 / 기타)

**A3**. 기존 15c trial 데이터 재분석 (Python 스크립트)
- KU evidence_links 분포 → 평균 claims/cycle 역산
- GU resolved_by → claim_id 매핑 검증
- cycle별 target_count 실측값 집계

**Size**: A1 S, A2 S, A3 M

### Stage B — Primary Fix (target_count cap 제거)

**B1**. `src/nodes/mode.py:204-212` Phase 5 복원
- `NORMAL_TARGET_CAP`, `JUMP_TARGET_CAP` 상수 제거
- `target_count = max(10, ceil(open_count * 0.5))` (jump)
- `target_count = max(4, ceil(open_count * 0.4))` (normal)

**B2**. 단위 테스트 갱신
- `tests/test_mode.py` target_count 공식 관련 테스트 수정
- open_count 변화에 따른 target_count 비례 스케일 검증 (Phase 5 원복 의도)

**B3**. 관련 테스트 영향 분석 + 수정
- grep으로 `target_count=10` / `TARGET_CAP` 가정한 테스트 식별
- 영향 범위 최소화, 회귀 방지

**Size**: B1 S, B2 S, B3 M

### Stage C — 재현 Trial + 효과 검증

**전제**: Stage A 로깅 적용 + Stage B fix 완료 후 실행 (API 비용 ~$1-3 예상)

**C1**. Trial 설정 + 실행
- `bench/silver/japan-travel/gap-res-fix-trial/` 생성 (silver-trial-scaffold)
- cycles=15, audit_interval=3 (15c trial과 동일 조건)
- trial-card.md: "Primary fix 적용 후 gap_res 재측정 + B2 가설 검증"

**C2**. 결과 분석
- trajectory.csv 비교: B1 fix 전(0.517) vs 후
- LLM 비용 측정 (tokens, calls) vs 15c trial baseline
- A1/A2 로깅으로 conversion rate 재측정

**C3**. readiness-report 작성
- VP1/VP2/VP3 점수
- Primary fix 효과 정량화 (target_count 평균, resolve/cycle)
- Secondary bottleneck 수치 (LLM parse yield rate, integration_result 분포)

**Size**: C1 M, C2 M, C3 S

### Stage D — Secondary 대응 결정

**D1**. B2 가설 확증/기각
- Stage C 데이터로 H1~H4 중 주원인 특정
- 예상: H1 우세 시 → LLM parse 개선 (프롬프트/query/rety) 필요
- 예상: H2 우세 시 → query generation 개선 필요

**D2**. 수정안 결정 — 본 Phase 내 fix OR 별도 Phase
- 본 Phase 내 fix 조건: 수정 범위 ≤ 2파일, 리스크 Low
- 별도 Phase 이관 조건: 프롬프트 엔지니어링, retry 로직 등 L+ 규모

**D3**. 결정 문서화 + Phase 종결
- D-130/D-131 등록
- SI-P2 재판정 착수 가능 여부 판정

**Size**: D1 S, D2 S, D3 S

## 5. Task Breakdown

| ID | Task | Size | 의존 |
|----|------|------|------|
| A1 | collect.py parse_yield 로깅 | S | — |
| A2 | integrate.py integration_result 로깅 | S | — |
| A3 | 기존 15c trial 정적 분석 스크립트 | M | — |
| B1 | mode.py target_count cap 제거 | S | — |
| B2 | test_mode.py 공식 테스트 갱신 | S | B1 |
| B3 | 영향 받는 테스트 수정 (grep 기반) | M | B1 |
| C1 | gap-res-fix-trial 생성 + 실행 | M | A1, A2, B1~B3 |
| C2 | trajectory before/after 분석 | M | C1 |
| C3 | readiness-report 작성 | S | C2 |
| D1 | B2 가설 확증 | S | C3 |
| D2 | Secondary 수정안 결정 | S | D1 |
| D3 | Decision 문서화 + Phase 종결 | S | D2 |

**합계**: 12 tasks (S: 8, M: 4)

## 6. Risks & Mitigation

| ID | 리스크 | L | I | 완화 |
|----|--------|---|---|------|
| G1 | target_count 증가로 LLM 비용 3x↑ | H | H | audit_interval=3 유지, R1 리스크 가드 (baseline×2.5) 준수 |
| G2 | B3 테스트 수정 누락 → 회귀 | M | M | grep 철저, CI 실행 전 pytest 전체 실행 |
| G3 | Stage C trial 실패 (D-120 재발) | L | H | A1 로깅으로 collect_failure_rate 감시, SI-P3R smoke 조건 유지 |
| G4 | H1~H4 모두 부분 기여 → 주원인 불명확 | M | M | A1/A2 로깅 데이터 기반 정량화. 상대 비율로 우선순위 결정 |
| G5 | Primary fix만으로 gap_res 0.85 미달 | M | M | Secondary 대응을 별도 Phase (`phase-llm-parse-yield`)로 이관 |

## 7. Dependencies

### 내부
| 모듈 | 의존 대상 |
|------|-----------|
| Stage B fix | SI-P3R 완료 (`981ffd6`), Phase 5 target_count 공식 (`b122a23` 참조) |
| Stage C trial | SI-P3R T8 재현 가능성 (`3d8d76d` smoke PASS 상태) |
| SI-P2 재판정 | 본 Phase 종결 + D-131 결정 |

### 외부
- OpenAI API (gpt-4.1-mini), Tavily API — 기존 사용
- 신규 패키지 없음

### 문서 의존성
- `docs/session-compact.md` §res_rate 조사 포인트 (본 Phase 출발점)
- `bench/silver/japan-travel/p3r-gate-trial-15c/` (원본 데이터)
- commit `b122a23` (Phase 5 target_count 공식 — 복원 원본)
- commit `b12545d` (regression 도입 — 롤백 대상 변경)
