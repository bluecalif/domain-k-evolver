# Trial Card: p0-20260412-baseline

| 항목 | 값 |
|------|-----|
| trial_id | p0-20260412-baseline |
| domain | japan-travel |
| phase | si-p0-foundation |
| date | 2026-04-12 |
| goal | P0 gate baseline — fresh seed + 15 cycle + Orchestrator (audit 포함) |
| status | running |

## Config

- **Seed**: `bench/japan-travel/state-snapshots/cycle-0-snapshot/` (13 KU, cycle 0)
- **Model**: gpt-4.1-mini (via `EvolverConfig.from_env()`)
- **Search**: Tavily
- **Cycles**: 15
- **Orchestrator**: `run_readiness.py --bench-root` (audit_interval=5)
- **Plateau**: disabled (stop_on_convergence=False)

## Hypothesis

Fresh seed 에서 시작하면:
1. staleness 문제 해소 (observed_at = today)
2. VP1 blind_spot 개선 (15 cycle 동안 균형 잡힌 확장)
3. VP3 audit 실행 (Orchestrator 경유)

## Config Diff (vs 첫 시도)

| 항목 | 첫 시도 | 이번 시도 |
|------|---------|-----------|
| seed | Bronze (cycle 14, 90 KU) | Fresh (cycle 0, 13 KU) |
| script | run_bench.py | run_readiness.py |
| cycles | 5 | 15 |
| audit | 없음 | interval=5 |

## Results

> 실행 후 채움
