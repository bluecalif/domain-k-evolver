# SI-P3R: Context

> Last Updated: 2026-04-14

## Phase 전환 배경

- 2026-04-13 세션에서 SI-P3 LLM parse 경로 버그(D-120) 확정
- 단일 GU 진단: snippet-only 경로로 4 claims 생성 성공
- 결정: 3단계 복잡도 제거 → snippet-first 2단계 파이프라인으로 회귀

## Pipeline — Target

```
Gap
  │
  ▼ STEP 1: SEARCH (Tavily)
  │   returns: [{url, title, snippet}] × N
  │
  ▼ STEP 2: PARSE (LLM)
  │   input: GU target + snippet array (top-N)
  │   output: Claim JSON array
  │
  ▼ integrate → KU
```

## Upstream/Downstream 영향

| 영역 | 영향 | 조치 |
|------|------|------|
| plan_node / remodel_node | 무관 | 유지 |
| integrate_node | claim 구조는 유지, provenance 필드 축소만 반영 | `.get()` 방어적 접근 |
| conflict/dispute (P3 main) | 무관 | 유지 |
| audit (P4) | `provider_entropy` 제거, `domain_entropy` 유지 | 삭제 |
| policy_manager (P4) | credibility 학습 시 `providers_used` 리스트 순회 → 단일 `provider` 참조 | 리팩토링 |
| staleness/axis_tags (P5) | 무관 | 유지 |

## Bench & Test Alignment 정책

### Bronze (`bench/japan-travel/`)
- **read-only 유지**. 구 provenance schema가 섞여 있으나 reference용
- 새 실행에는 사용하지 않음

### Silver 분기
- **Historical evidence 보존**:
  - `p3-20260412-acquisition/` (구 P3 원본 trial)
  - `p3-20260413-llm-diag/`, `p3-20260413-llm-verify/` (진단 trial)
  - 삭제 금지. D-120 증거 체인
- **신규 trial namespace**: `p3r-*`
  - `p3r-smoke/` — 1 cycle 검증
  - `p3r-gate-trial/` — 5 cycle Gate 재판정

### domain-skeleton.json
- `preferred_sources` 처리 방침: **옵션 B 채택 (2026-04-14, T6)**
  - 코드(`src/`) 및 스키마(`schemas/`)에서 `preferred_sources` 참조 grep = 0
  - runtime 무시 상태 → Bronze read-only 원칙 유지 가능
  - 필드는 `bench/japan-travel/state-snapshots/*/domain-skeleton.json`에 보존 (historical)
  - 신규 도메인 skeleton 설계 시 `preferred_sources` 미포함 권장

### japan-travel-auto state
- Phase 5 완료 시점의 구 state 보존(archive)
- 신규 파이프라인 smoke test는 clean root에서 시작

### Tests
- `tests/test_collect_p3.py` (25 tests): fetch/html 관련 제거, snippet 경로 보강
- `tests/test_collect.py`: `_parse_claims_llm` happy-path 유지 및 확장
- `tests/fixtures/` 내 FetchResult/HTML 픽스처 삭제
- integrate/dispute/audit/policy 테스트: provenance 축소 필드만 반영(대부분 `.get()` 이므로 무영향)

## Changed/Created Files (초안)

### 신규
- `src/adapters/search_tool.py` (tavily_provider 이관)

### 삭제
- `src/adapters/fetch_pipeline.py`
- `src/utils/html_strip.py`
- `src/adapters/providers/base.py`
- `src/adapters/providers/ddg_provider.py`
- `src/adapters/providers/curated_provider.py`
- `src/adapters/providers/tavily_provider.py` (이관 후)
- `tests/test_fetch_pipeline.py`
- `tests/test_html_strip.py`
- `tests/test_providers_base.py` (존재 시)
- `tests/test_providers_ddg.py` (존재 시)
- `tests/test_providers_curated.py` (존재 시)

### 수정
- `src/nodes/collect.py`
- `src/config.py`
- `scripts/run_readiness.py`
- `src/nodes/audit.py`
- `src/utils/policy_manager.py`
- `tests/test_collect_p3.py`
- `tests/test_collect.py`
- `pyproject.toml`
- `bench/japan-travel/state-snapshots/cycle-0-snapshot/domain-skeleton.json` (옵션 A 채택 시)

## Decisions

- D-121 (2026-04-14): SI-P3 (Provider/Fetch/Parse 3단계) 전면 폐기 → SI-P3R(snippet-first 2단계)로 대체
- D-122: Historical silver trial 디렉터리 보존. 신규 trial은 `p3r-*` namespace
- D-123: Bronze read-only 원칙 유지, skeleton 변경 시 snapshot만 수정
- D-124: `provider_entropy` 메트릭 제거 (단일 provider), `domain_entropy` 유지
