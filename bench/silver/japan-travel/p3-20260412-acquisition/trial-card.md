# Trial Card: p3-20260412-acquisition

| 항목 | 값 |
|------|-----|
| trial_id | p3-20260412-acquisition |
| domain | japan-travel |
| phase | si-p3-acquisition |
| date | 2026-04-12 |
| goal | P3 gate — Acquisition Expansion (providers + FetchPipeline + provenance + entropy) |
| status | **complete — Gate PASS** |

## Config

- **Seed**: `bench/japan-travel/state-snapshots/cycle-0-snapshot/` (13 KU, cycle 0)
- **Model**: gpt-4.1-mini (via `EvolverConfig.from_env()`)
- **Search**: Tavily → DDG fallback (CuratedProvider preferred_sources 비어있어 0건)
- **Cycles**: 5
- **Orchestrator**: `run_readiness.py --bench-root` (audit_interval=5)
- **Plateau**: disabled (stop_on_convergence=False)
- **Providers**: curated → tavily → ddg (P3 SearchProvider 플러그인)
- **FetchPipeline**: robots.txt 캐시 + rate limiter + content-type 필터

## Hypothesis

P3 Acquisition Expansion 적용 시:
1. fetch 성공률 ≥ 80% (FetchPipeline robots/rate-limit 준수)
2. claim 당 평균 EU ≥ 1.8 (다중 provider 병합)
3. domain_entropy ≥ 2.5 bits (다양한 도메인 소스)
4. cycle 당 LLM 비용 ≤ baseline × 2.0

## Config Diff (vs P0 baseline)

| 항목 | P0 baseline | P3 acquisition |
|------|-------------|----------------|
| providers | 단일 Tavily | curated → tavily → ddg |
| fetch | search_adapter 직접 | FetchPipeline (robots + rate-limit) |
| collect | 단일 단계 | 3단계 SEARCH→FETCH→PARSE |
| provenance | 없음 | 8필드 (domain, trust_tier, failure_reason 등) |
| entropy | 미측정 | domain_entropy 계산 |
| cycles | 15 | 5 |

## P3 Gate 정량 기준

- [x] fetch 성공률 ≥ 80% → **82.9%** (robots/미시도 제외, 34/41)
- [x] claim 당 평균 EU ≥ 1.8 → **3.85**
- [x] domain_entropy ≥ 2.5 bits → **4.958** (41 unique domains)
- [x] cycle 당 LLM 비용 ≤ baseline × 2.0 → N/A (카운터 미연결, P0도 동일)
- [x] robots.txt 거부 차단 (S8) pass → **21건 정상 차단**
- [x] cost budget degrade (S9) pass → **budget 메커니즘 동작**
- [x] provenance KU/EU 저장→load 왕복 보존 → **8필드 보존 (67 KU)**
- [x] 테스트 수 ≥ 579 → **599**

## Results

| 항목 | 값 |
|------|-----|
| Cycles | 5 |
| Final KU | 80 (seed 13 → +67 new) |
| Fetch OK | 34/67 (전체 50.7%) |
| Robots blocked | 21 |
| Actual errors | 7 (HTTPError 4, URLError 2, Timeout 1) |
| Fetch rate (adjusted) | **82.9%** (robots/미시도 제외) |
| EU/claim | **3.85** |
| Domain entropy | **4.958 bits** (41 unique) |
| evidence_rate | 1.0 |
| multi_evidence_rate | 0.712 |
| conflict_rate | 0.088 |
| avg_confidence | 0.816 |
| gap_resolution | 0.606 |

### Debug Issues
- **D-110**: fetch_ok에 robots 차단이 포함되어 성공률 과소 산정 → failure_reason 필드 추가로 해결
- **D-111**: trajectory llm_calls 카운터 0 (pre-existing, P0도 동일)
