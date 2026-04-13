# Session Compact

> Generated: 2026-04-13 23:15
> Source: P3 LLM parse 경로 수정 재시작 + Scripts Policy 정리

## Goal

P3 Gate 무효화 → P3 LLM parse 경로 수정 → P3/P2 Gate 재판정

## Completed

- [x] P3/P2 Gate REVOKED 공식 반영 (이전 세션)
- [x] D-120 문서화: LLM parse 0 claims 근본 원인 분석 (이전 세션)
- [x] 코드 분석: collect.py, graph.py, orchestrator.py, run scripts 전체 읽기
- [x] **근본 원인 특정**: run_one_cycle.py/run_bench.py가 P3 providers/fetch_pipeline 미전달 → legacy 경로만 사용
- [x] **Scripts Policy 수립** (CLAUDE.md): run_readiness.py 단일 진입점 규칙
- [x] run_one_cycle.py → deprecated thin wrapper (run_readiness.py --cycles 1 위임)
- [x] run_bench.py → deprecated thin wrapper (run_readiness.py --cycles N 위임)
- [x] 커밋: `edca3ed` [si-p3] Scripts Policy: 단일 진입점 규칙 + deprecated 스크립트 정리
- [x] 673 tests passed, 3 skipped 확인

## Current State

- **Git**: branch `main`, latest commit `edca3ed`
- **Tests**: 673 passed, 3 skipped
- **P3 Status**: **REVOKED** — LLM parse 경로 미검증 (D-120)
- **P2 Status**: **REVOKED** — P3 연쇄 무효
- **핵심 블로커**: `_parse_claims_llm` happy-path 미검증 + snippet fallback 미보강

### Changed Files (uncommitted — 이전 세션 디버그 로그)
- `scripts/run_readiness.py` — `--audit-interval` 옵션 추가
- `src/orchestrator.py` — cycle별 타이밍 로그 (time.monotonic)
- `src/nodes/mode.py` — target_count 상한 10 + 로그
- `src/nodes/plan.py` — targets/queries/no_query 로그
- `src/nodes/collect.py` — 0 claims 진단 로그 + parse 진단 로그

### Scripts 현황 (정리 완료)
| 스크립트 | 상태 | 역할 |
|---------|------|------|
| `run_readiness.py` | **정상 (유일한 진입점)** | P3 providers+fetch_pipeline 연결, Orchestrator 사용 |
| `run_one_cycle.py` | deprecated → wrapper | run_readiness.py --cycles 1 위임 |
| `run_bench.py` | deprecated → wrapper | run_readiness.py --cycles N 위임 |
| `run_p2_bench.py` | 유지 (비교 스크립트) | subprocess로 run_readiness.py 호출 |
| `analyze_trajectory.py` | 유지 (분석) | API 미호출, 결과 분석용 |

## Remaining / TODO

### 즉시 작업: LLM parse 경로 검증 + 보강
- [ ] `_parse_claims_llm` happy-path 단위 테스트 (mock LLM → valid JSON 반환)
- [ ] collect_node LLM 통합 테스트 (llm + providers + fetch_pipeline 동시 전달)
- [ ] snippet fallback 보강: fetch 실패 시 prompt에서 snippet 활용 강조
- [ ] 이전 세션 디버그 로그 변경분 커밋 정리 (uncommitted 5 files)

### P3 Gate 재판정
- [ ] P3 실 벤치 trial 재실행 (real API, LLM parse 경로 검증)
- [ ] LLM parse claims > 0 확인
- [ ] Gate 기준 재검증

### P2 Gate 재판정
- [ ] P2 실 벤치 trial (OFF/ON 비교)
- [ ] Gate 기준 재검증

## Key Decisions

- D-120: P3/P2 Gate REVOKED — LLM parse 경로 미검증 (2026-04-13)
- **Scripts Policy**: run_readiness.py 단일 진입점. 새 실행 스크립트 금지, 옵션으로 확장. (CLAUDE.md)
- run_bench.py의 직접 graph.invoke 루프가 D-120 원인 중 하나 (P3 infra 누락)

## Context

다음 세션에서는 답변에 **한국어** 사용.

### 핵심 제약
- **Bash 절대경로 필수** (CLAUDE.md) — `cd` 금지, 단일 명령어 우선
- **Bronze 보호**: `bench/japan-travel/` read-only
- **커밋 prefix**: `[si-p3]` (P3 수정 시), `[si-p2]` (P2 수정 시)
- **인코딩**: `PYTHONUTF8=1`, `encoding='utf-8'` 명시
- **Phase Gate 규칙**: 실 API로 E2E 검증 필수. 합성 E2E만으로 gate 불가
- **API 비용 주의**: 실행 전 기존 결과 확인 + 유저 확인 필수

### 테스트 파일 위치
- `tests/test_nodes/test_collect.py` — legacy collect 테스트 (llm=None / bad_llm fallback)
- `tests/test_collect_p3.py` — P3 collect 테스트 (providers, fetch, entropy — 모두 llm=None)
- **둘 다 `_parse_claims_llm` happy-path 미검증** — 이것이 핵심 gap

### D-120 핵심 문제 (P3 LLM parse 0 claims)

**데이터 흐름**:
```
SEARCH (snippet ✓) → FETCH (fetch_pipeline) → PARSE (llm)
```

**`_parse_claims_llm` 코드 흐름** (`collect.py:194-242`):
1. `fetched_bodies` = fetch_results 중 `fetch_ok and body` 있는 것들
2. `fetched_content` = bodies 합침 (fetch 실패 시 빈 문자열)
3. `raw_results` = search_results를 dict로 변환 (snippet 포함)
4. prompt = `_build_parse_prompt(gu, raw_results, fetched_content)`
5. prompt에 snippet은 Sources 섹션, fetched_content는 "Fetched Content" 섹션
6. fetch 실패 시 "(no content fetched)" 표시 → LLM이 빈 배열 반환 가능성

**검증 필요 사항**:
- mock LLM이 valid JSON 반환 시 claims 정상 파싱되는지
- fetch 실패(빈 content) + snippet만 있을 때 LLM이 claims 생성하는지
- prompt 개선: snippet만으로도 claim 추출 가능함을 명시

## Next Action

**`_parse_claims_llm` happy-path 테스트 작성** — `tests/test_collect_p3.py`에 추가:
1. mock LLM → valid JSON array 반환 → claims 정상 파싱 + provenance 주입 확인
2. mock LLM + providers + fetch_pipeline → collect_node 전체 경로 통합 테스트
3. snippet fallback: prompt 보강 (fetch 실패 시 snippet에서 추출 명시)
