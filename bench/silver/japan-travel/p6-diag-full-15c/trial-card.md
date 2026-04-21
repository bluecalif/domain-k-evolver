# Trial Card: p6-diag-full-15c

| 항목 | 값 |
|------|-----|
| trial_id | p6-diag-full-15c |
| domain | japan-travel |
| phase | si-p6-consolidation |
| date | 2026-04-18 |
| goal | D3 root cause 확정 — 15c full, stage-e-on, --trace-frozen 3으로 동결 GU 분석 |
| status | pending |

## Config

- **Seed**: fresh seed (bench/japan-travel/state-snapshots/cycle-0-snapshot/)
- **Model**: gpt-4.1-mini
- **Search**: Tavily
- **Cycles**: 15
- **Stage-E (External Anchor)**: ON (`--external-anchor`)
- **Audit interval**: 5

## Hypothesis

stage-e-on에서 wildcard GU가 pool을 동결시킨다면:
1. gu_trace에서 wildcard GU search_yield ≈ 0 확인
2. c10+ 동결 GU의 wildcard 구성비 측정
3. External Anchor probe → attraction entity flood → GU 누적 가설 검증

## Results

> 실행 후 채움
