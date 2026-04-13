# Session Compact

> Generated: 2026-04-13 21:30
> Source: P3/P2 Gate REVOKED 공식 반영

## Goal

P3 Gate 무효화 → P3 LLM parse 경로 수정 → P3/P2 Gate 재판정

## Completed

- [x] P3/P2 Gate REVOKED 공식 반영 (dev-docs, debug-history, MEMORY)
- [x] D-120 문서화: LLM parse 0 claims 근본 원인 분석
- [x] P2 실 벤치 준비 작업 (run_readiness --audit-interval, run_p2_bench, orchestrator 타이밍 로그 등)

## Current State

- **Git**: branch `main`, latest commit `d89ffb0`
- **Tests**: 673 passed, 3 skipped
- **P3 Status**: **REVOKED** — 22/22 구현 완료했으나 LLM parse 경로 미검증으로 gate 무효
- **P2 Status**: **REVOKED** — P3 연쇄 무효
- **핵심 블로커**: collect `_parse_claims_llm` 0 claims 문제 (D-120)

### Changed Files (uncommitted)
- `scripts/run_readiness.py` — `--audit-interval` 옵션 추가
- `scripts/run_p2_bench.py` — 신규 (off/on 비교 스크립트)
- `src/orchestrator.py` — cycle별 타이밍 로그 (time.monotonic)
- `src/nodes/mode.py` — target_count 상한 10 + 로그
- `src/nodes/plan.py` — targets/queries/no_query 로그
- `src/nodes/collect.py` — 0 claims 진단 로그 + parse 진단 로그
- `docs/session-compact.md` — 현 상태 반영
- `dev/active/phase-si-p3-acquisition/*` — Gate REVOKED 반영
- `dev/active/phase-si-p2-remodel/*` — Gate REVOKED 반영

## Remaining / TODO

### Phase 1: P3 LLM parse 경로 수정 (블로커)
- [ ] 실제 API로 단일 GU SEARCH→FETCH→PARSE 수동 검증 (문제 원인 특정)
- [ ] fetch body가 실제로 비어있는지 확인 (tavily snippet vs fetch body)
- [ ] LLM parse prompt + response 내용 디버깅
- [ ] 코드 수정 (원인에 따라 fetch/parse/prompt 중 해당 부분)
- [ ] P3 테스트에 LLM parse 경로 통합 테스트 추가

### Phase 2: P3 Gate 재판정
- [ ] P3 실 벤치 trial 재실행 (real API, LLM parse 경로 검증)
- [ ] LLM parse claims > 0 확인
- [ ] Gate 기준 재검증

### Phase 3: P2 Gate 재판정
- [ ] P2 실 벤치 trial 재실행 (OFF/ON 비교)
- [ ] Gate 기준 재검증
- [ ] trial-card.md + tasks.md 결과 반영

## Key Decisions

- D-120: P3/P2 Gate REVOKED — LLM parse 경로 미검증 (2026-04-13)
- target_count 상한 10 적용 (Normal + Jump 동일) — D-37
- API 비용 작업은 기존 결과 확인 + 사전 확인 필수 (피드백 메모리)

## Context

다음 세션에서는 답변에 **한국어** 사용.

### 핵심 제약
- **Bash 절대경로 필수** (CLAUDE.md) — `cd` 금지, 단일 명령어 우선
- **Bronze 보호**: `bench/japan-travel/` read-only
- **커밋 prefix**: `[si-p3]` (P3 수정 시), `[si-p2]` (P2 수정 시)
- **인코딩**: `PYTHONUTF8=1`, `encoding='utf-8'` 명시
- **Phase Gate 규칙**: 실 API로 E2E 검증 필수. 합성 E2E만으로 gate 불가
- **API 비용 주의**: 실행 전 기존 결과 확인 + 유저 확인 필수

### D-120 핵심 문제 (P3 LLM parse 0 claims)

**문제**: P3 테스트가 전부 `llm=None`/`fetch_pipeline=None`으로 호출 → deterministic fallback만 검증.

**데이터 흐름 실패 지점**:
```
SEARCH (snippet ✓) → FETCH (fetch_pipeline=None → 빈 리스트) → PARSE (llm=None → deterministic fallback)
```

**테스트에서 안 보이는 이유**:
- `collect_node(state, providers=[mock])` — fetch_pipeline, llm 미전달
- `llm=None` → `_parse_claims_deterministic()` 사용 → claims 생성 → 테스트 통과
- 실제 운영에서는 llm 전달 → `_parse_claims_llm()` 사용 → 0 claims

**확인 필요 파일**:
- `src/adapters/providers/tavily_provider.py` — snippet 내용/길이
- `src/adapters/fetch_pipeline.py` — fetch body 내용/길이
- `src/nodes/collect.py:_parse_claims_llm` — prompt + LLM response
- `src/utils/llm_parse.py:extract_json` — 빈 배열 처리

### Silver 의존성 그래프
```
P0 ✅ ─┬── P1 ✅ ──┐
       │           ├── P2 (REVOKED) ──┐
       ├── P3 (REVOKED) ──┼──────────┤
                   └─ P4 ──┼── P5 ── P6
```

## Next Action

**P3 LLM parse 경로 수정 시작** — 실제 API로 문제 원인 특정 후 코드 수정
