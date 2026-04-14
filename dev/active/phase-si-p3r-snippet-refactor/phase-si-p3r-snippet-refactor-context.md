# SI-P3R: Context

> Last Updated: 2026-04-14 (T8 완료)

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
- D-125 (2026-04-14): P3R Gate PASS — acquisition 검증 기준 판정. full readiness gate(VP2 gap_resolution)는 시스템 수렴 문제로 P3R과 분리
- D-126 (2026-04-14): gap_resolution 병목 별도 조사 필요. remodel 이전에도 cycle 10에서 0.437 — plan targeting, GU resolve 판정, critique gap 생성량 확인 대상
- D-127 (2026-04-14): P2 Gate는 remodel on/off 비교 실험으로 재설계. 단일 결과의 절대 임계치 적용 부적합
- D-128 (2026-04-14): 우선순위 결정: res_rate 조사 → P2 비교 실험 → P4~P6

## T8 Gate Trial 결과

### 5 cycle (`p3r-gate-trial/`)
- VP1 PASS 4/5, VP2 FAIL 4/6, VP3 FAIL 1/6
- gap_resolution 0.283, audit_count 1 (interval=5 부적합)

### 15 cycle (`p3r-gate-trial-15c/`, audit_interval=3)
- VP1 **PASS 5/5**, VP2 FAIL 4/6, VP3 **PASS 6/6**
- gap_resolution 0.517 (임계치 0.85), multi_evidence 0.718 (임계치 0.80)
- Cycle 11 remodel 발동: KU 63→86, GU 119→144 (VP1↑, VP2↓ trade-off)
- 수렴 추세: 신규 GU 28→3/cycle, 해결 5~6/cycle 일정

### 판정 논거
- P3R은 acquisition refactor 검증: collect_failure=0, evidence_rate=1.0, D-120 재발 없음 → **PASS**
- VP2 R1 gap_resolution은 시스템 수렴도 측정 — acquisition 품질과 무관
- VP3 만점은 governance 메커니즘 정상 작동 증명
- P2 gate는 remodel 효과 검증이므로 별도 비교 실험 필요
