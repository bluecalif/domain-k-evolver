# Phase: Gap-Resolution 병목 조사 — Tasks
> Last Updated: 2026-04-14
> Status: Planning — 0/12 completed

## Progress

| Stage | Tasks | Done |
|-------|-------|------|
| A. 진단 로깅 + 정적 분석 | 3 | 0/3 |
| B. Primary Fix (cap 제거) | 3 | 0/3 |
| C. 재현 Trial + 효과 검증 | 3 | 0/3 |
| D. Secondary 대응 결정 | 3 | 0/3 |
| **합계** | **12** | **0/12** |

**Size 분포**: S 8 · M 4 · L 0 · XL 0

---

## Stage A — 진단 로깅 + 기존 데이터 재분석

> 목적: Secondary bottleneck (B2) 원인 확증 준비. 재현 trial 실행 전 가설 검증.

- [ ] **A1** [S] `src/nodes/collect.py` parse_yield 로깅
  - `_parse_claims_llm` 내부: `logger.info("parse_yield: gu=%s snippets=%d claims=%d")`
  - `collect_node` 종료 시 누적 분포: avg claims/target, zero_claims_ratio
  - 기존 로깅과 prefix 구분 (`parse_yield:`)
  - Commit: `[gap-res] A1: collect parse_yield 로깅`

- [ ] **A2** [S] `src/nodes/integrate.py` integration_result 분포 로깅
  - cycle 종료 시 `Counter`로 integration_result 집계 → logger.info
  - GU resolve 실패 원인 3분류 (no_source_gu_id / invalid_result / other)
  - Commit: `[gap-res] A2: integrate result 분포 로깅`

- [ ] **A3** [M] 기존 15c trial 정적 분석 스크립트
  - `scripts/analyze_p3r_gap.py` (analyze_trajectory.py 계열, 신규)
  - 입력: `bench/silver/japan-travel/p3r-gate-trial-15c/`
  - 출력: KU evidence 분포, GU resolved_by 매핑 검증, cycle별 target/resolve 비교
  - CLAUDE.md scripts policy 준수 — 분석용 신규 허용, 실행 스크립트는 `run_readiness.py` 유지
  - Commit: `[gap-res] A3: p3r 정적 분석 스크립트`

---

## Stage B — Primary Fix (target_count cap 제거)

> 목적: `b12545d` regression 롤백 → Phase 5 상태 복원.

- [ ] **B1** [S] `src/nodes/mode.py` target_count cap 제거
  - 삭제: `NORMAL_TARGET_CAP = 10`, `JUMP_TARGET_CAP = 10`
  - 변경: `target_count = max(4, ceil(open_count * 0.4))` (normal)
  - 변경: `target_count = max(10, ceil(open_count * 0.5))` (jump)
  - 로그 메시지 유지 (b12545d에서 추가한 `mode: %s | open=%d → target_count=%d` 는 보존)
  - Commit: `[gap-res] B1: target_count cap 제거 (Phase 5 복원, D-129)`

- [ ] **B2** [S] `tests/test_mode.py` target_count 공식 테스트 갱신
  - cap=10 가정 테스트 제거/수정
  - open_count 비례 스케일 검증 (e.g., open=70 → target_count=35 in jump)
  - Commit: `[gap-res] B2: test_mode target_count 공식 갱신`

- [ ] **B3** [M] 영향 테스트 전수 검사 + 수정
  - Grep `target_count`, `TARGET_CAP`, `10.*target` 등 패턴
  - 기존 통합 테스트에서 target_count=10 하드코딩된 곳 수정
  - pytest 전체 실행 → 608 유지/증가 확인
  - Commit: `[gap-res] B3: target_count 의존 테스트 정합성 수정`

---

## Stage C — 재현 Trial + 효과 검증

> 목적: Primary fix 효과 정량화 + Secondary 원인 수치 확보.
> **비용 가드**: audit_interval=3, 15c, baseline × 2.5 초과 시 중단.

- [ ] **C1** [M] gap-res-fix-trial 생성 + 실행
  - silver-trial-scaffold skill 사용
  - `bench/silver/japan-travel/gap-res-fix-trial/` 생성
  - trial-card.md: "Primary fix 적용 후 gap_res 재측정 + B2 가설 검증"
  - config.snapshot.json: cycles=15, audit_interval=3
  - 실행 전 API 비용 예상치 사용자 확인
  - Commit: `[gap-res] C1: gap-res-fix-trial 실행`

- [ ] **C2** [M] trajectory before/after 분석
  - 비교 대상: p3r-gate-trial-15c vs gap-res-fix-trial
  - 지표: target_count 평균, resolve/cycle, gap_resolution_rate cycle별
  - LLM 비용: tokens, calls (baseline × N 계산)
  - A1/A2 로깅 파싱 → LLM parse yield rate, integration_result 분포
  - Commit: `[gap-res] C2: trial before/after 비교`

- [ ] **C3** [S] readiness-report 작성
  - silver-phase-gate-check skill 사용
  - `bench/silver/japan-travel/gap-res-fix-trial/readiness-report.md`
  - VP1/VP2/VP3 점수 + Primary fix 효과 정량화 + Secondary 수치
  - Commit: `[gap-res] C3: readiness-report gap-res-fix-trial`

---

## Stage D — Secondary 대응 결정

> 목적: Secondary bottleneck 처리 방향 결정 + Phase 종결.

- [ ] **D1** [S] B2 가설 확증
  - C2 데이터로 H1~H4 (context.md §B2) 각 기여도 계산
  - H1 (LLM parse 0 claims) 가중치 추정
  - H2 (query 품질) — zero_claims GU의 query 패턴 분석
  - H3 (source_gu_id 변조) — A2 로깅의 invalid_result 카운트
  - 결과: "H1이 주원인 (XX%)" 또는 "H1+H2 복합" 등 정량 결론
  - 산출물: context.md §B2에 결론 추가

- [ ] **D2** [S] Secondary 수정안 결정
  - 본 Phase 내 fix 기준: ≤ 2파일, ≤ 50 LOC, 리스크 Low
  - 별도 Phase 이관 기준: 프롬프트 엔지니어링, retry 로직, provider 통합 등
  - 결정 + 근거를 context.md §수정 방향에 기록
  - 별도 Phase 시 phase 이름 후보 (e.g., `phase-llm-parse-yield`)

- [ ] **D3** [S] Decision 문서화 + Phase 종결
  - MEMORY.md D-129 등록: "target_count cap regression 확정 + Phase 5 복원"
  - MEMORY.md D-130 등록: B2 가설 주원인 + 처리 방향
  - MEMORY.md D-131 등록: SI-P2 재판정 착수 조건 (본 Phase 결과 기준)
  - session-compact.md 갱신 (Next Action: SI-P2 재판정 or B2 별도 phase)
  - project-overall 동기화
  - Phase 상태 → Complete
  - Final commit: `[gap-res] D3: Phase 종결 — D-129~D-131`

---

## Test Impact

- **현재**: 608 passed, 3 skipped
- **Stage A**: 신규 로깅 — 테스트 거의 불변
- **Stage B**: `test_mode.py` 공식 테스트 갱신 + 영향 테스트 수정. 목표: ≥ 608 유지
- **Stage D 종료 시**: 608-615 예상 (신규 진단 테스트 미미)

## Commit 체인 (예상)

```
981ffd6 (base: SI-P3R T8 PASS)
  ↓
[gap-res] A1: collect parse_yield 로깅
[gap-res] A2: integrate result 분포 로깅
[gap-res] A3: p3r 정적 분석 스크립트
  ↓
[gap-res] B1: target_count cap 제거 (D-129)
[gap-res] B2: test_mode 공식 갱신
[gap-res] B3: target_count 의존 테스트 수정
  ↓
[gap-res] C1: gap-res-fix-trial 실행
[gap-res] C2: trial before/after 비교
[gap-res] C3: readiness-report
  ↓
[gap-res] D3: Phase 종결 — D-129~D-131
```
