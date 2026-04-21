# Trial Card: p6-diag-smoke-5c

| 항목 | 값 |
|------|-----|
| trial_id | p6-diag-smoke-5c |
| domain | japan-travel |
| phase | si-p6-consolidation |
| date | 2026-04-18 |
| goal | D3 진단 로깅 검증 — 5c smoke, stage-e-off, gu_trace.jsonl 생성 확인 |
| status | pending |

## Config

- **Seed**: fresh seed (bench/japan-travel/state-snapshots/cycle-0-snapshot/)
- **Model**: gpt-4.1-mini
- **Search**: Tavily
- **Cycles**: 5
- **Stage-E (External Anchor)**: OFF (`--no-external-anchor`)
- **Audit interval**: 5

## Hypothesis

D1 진단 로깅이 올바르게 동작하면:
1. telemetry/gu_trace.jsonl 생성됨
2. cycles.jsonl에 cycle_trace 블록 포함
3. wildcard GU의 search_yield vs concrete GU 차이 측정 가능

## Results

> 실행 후 채움
