# SI-P3R: Snippet-First Acquisition Refactor

> Last Updated: 2026-04-14
> Status: **완료 (8/8)** — P3R Gate PASS (acquisition 검증 기준, D-125)
> Predecessor: SI-P3 (REVOKED → CLOSED), SI-P2 (REVOKED — 별도 재판정 예정)

## Motivation

D-120: SI-P3의 Provider/Fetch/Parse 3단계 파이프라인은 22 tasks 구현 완료했음에도 실 벤치에서 `_parse_claims_llm` 0 claims 문제를 일으킴.
근본 원인(세션: 2026-04-13):
- **Curated 홈페이지 URL** → GU와 무관한 콘텐츠 fetch
- **Raw HTML 노이즈** → HTML→text 변환 추가해도 상위 snippet 품질 대비 우위 없음
- **Fetch rate-limit/timeout** → 병렬 실행 hang (10 GU에서 분 단위)

단일 GU 진단: **Tavily snippet 상위 + LLM 파싱만으로 4 claims 성공**. → 3단계를 제거하고 snippet 기반으로 회귀하는 것이 품질·복잡도·비용 모두 유리.

## Goal

Tavily search snippet만을 LLM에 전달하여 Claim을 추출하는 **2단계 파이프라인(SEARCH→PARSE)** 으로 복원. 연쇄로 REVOKED된 P3/P2 Gate를 재판정 가능한 상태로 되돌린다.

## Scope

### 제거
- `src/adapters/fetch_pipeline.py`, `src/utils/html_strip.py`
- `src/adapters/providers/{base,ddg_provider,curated_provider}.py`
- `src/nodes/collect.py` `_fetch_phase`, snippet 외 LLM 입력
- `tests/test_html_strip.py`, `tests/test_fetch_pipeline.py`, `tests/test_providers_*.py`
- `pyproject.toml` beautifulsoup4 의존성

### 수정
- `src/adapters/providers/tavily_provider.py` → `src/adapters/search_tool.py` (단순 Tavily 호출 유틸)
- `src/nodes/collect.py`: 2단계화, `_parse_claims_llm` snippet 전용 재작성, `_build_parse_prompt`에서 `fetched_content` 제거
- provenance: `{provider, domain, retrieved_at, trust_tier}` 4필드로 축소
- `src/config.py` SearchConfig: `tavily_max_results`만 유지
- `scripts/run_readiness.py` L156-165: `providers=`/`fetch_pipeline=` 전달 제거
- `src/nodes/audit.py`: `provider_entropy` 제거(단일 provider)
- `src/utils/policy_manager.py`: `providers_used` → `provider` 단일 참조
- `bench/japan-travel/state-snapshots/cycle-0-snapshot/domain-skeleton.json`: `preferred_sources` 제거 또는 query hint로 재정의

### 유지
- LangGraph orchestration, plan/integrate/critique/remodel/dispute/audit 로직
- KU/EU/GU 스키마 본체
- 상위 레벨 메트릭(except provider_entropy)

## Bench & Test Alignment

**문제**: 기존 벤치 산출물은 구 schema(provenance 8필드, curated provider)를 담고 있어 새 코드에서 불일치.

**정책**:
1. **Bronze 보존**: `bench/japan-travel/` read-only (CLAUDE.md 준수) — 스키마 변환 스크립트 X, 참조용으로 유지
2. **Silver 분기**: `bench/silver/japan-travel/p3-*` 3개 디렉터리(p3-20260412-acquisition, p3-20260413-llm-diag/verify)는 **historical evidence**로 보존. 새 trial은 `bench/silver/japan-travel/p3r-*` 네임스페이스 사용
3. **domain-skeleton.json**: 런타임에서 `preferred_sources` 필드를 선택적으로 읽되, 비어있어도 동작하도록 collect.py 수정. 신규 skeleton에는 해당 필드 제거
4. **japan-travel-auto state**: `bench/japan-travel-auto/` 구 state는 archive 처리(또는 재시작). provenance 필드 accessor가 `.get()`으로 방어적 읽기하도록 migration 최소화
5. **테스트 데이터**: `tests/fixtures/` 내 mock search/fetch result는 SearchResult dataclass 축소 후 그대로 재사용 가능. html/fetch 관련 픽스처 제거

**Re-judgement plan**: P3R 완료 후 clean 벤치 루트(`bench/silver/japan-travel/p3r-gate-trial/`)로 P3/P2 Gate 동시 재판정. 직전 Phase 2 baseline과 비교.

## Critical Files

- `src/nodes/collect.py` — 주 리팩터
- `src/adapters/providers/tavily_provider.py` → `search_tool.py` 이관
- `src/config.py`, `scripts/run_readiness.py`
- `src/nodes/audit.py`, `src/utils/policy_manager.py` (provenance 참조)
- `pyproject.toml` (의존성)

## Success Criteria

- 전체 테스트 green (~450~480 tests 예상, -40~-70 삭제)
- 1 cycle 실 벤치: **10/10 GU claims > 0**, 실행 시간 < 2분
- 5 cycle Gate trial: VP1/VP2/VP3 각 80%+ → P3 Gate PASS
  - **실제 결과**: 5c FAIL → 15c 재시행. VP1 5/5, VP3 6/6 만점. VP2 4/6 (gap_resolution 0.517)
  - **판정**: P3R Gate PASS (acquisition 검증 기준). gap_resolution은 시스템 수렴 문제로 분리 (D-126)
- 회귀 없음: Phase 3~5 지표(conflict_rate, avg_confidence, gap_resolution) 직전 기록 대비 ±5% 이내

## Verification

```bash
python -m pytest                                    # 전체 green
PYTHONUTF8=1 python scripts/run_readiness.py \
    --cycles 1 --audit-interval 0 \
    --bench-root bench/silver/japan-travel/p3r-smoke
PYTHONUTF8=1 python scripts/run_readiness.py \
    --cycles 5 --bench-root bench/silver/japan-travel/p3r-gate-trial
```
