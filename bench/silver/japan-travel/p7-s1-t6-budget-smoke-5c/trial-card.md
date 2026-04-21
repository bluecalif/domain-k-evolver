# Trial Card: p7-s1-t6-budget-smoke-5c

| 항목 | 값 |
|------|-----|
| trial_id | p7-s1-t6-budget-smoke-5c |
| domain | japan-travel |
| phase | si-p7 |
| date | 2026-04-21 |
| goal | S1-T6: budget 제거 smoke — utility skip 제거 + deferred 구조(S1-T4~T8) 첫 실 벤치. 비용/실패율/noise 측정 → F1 결정 |
| status | complete |

## Config

- **Seed**: fresh seed (bench/japan-travel/state-snapshots/cycle-0-snapshot/)
- **Model**: gpt-4.1-mini
- **Search**: Tavily
- **Cycles**: 5
- **Stage-E (External Anchor)**: OFF (`--no-external-anchor`)
- **Audit interval**: 5
- **max_search_calls_per_cycle**: 500 (default, 사실상 제한 없음)

## Hypothesis

S1 변경(T1~T8) 후 첫 실 벤치:
1. deferred_targets > 0 발생 여부 (budget 초과 시 drop → defer 전환 동작 확인)
2. search_calls / cycle 분포 — 기존 대비 증가 여부
3. collect_failure_rate — 안정 유지 여부
4. claims / cycle — noise 증가 없음 확인

## F1 결정 기준

- search_calls/cycle > 50 → budget 유지 검토
- collect_failure_rate > 0.3 → 원인 분석 필요
- deferred_targets > 0 → defer 메커니즘 작동 확인 (정상)

## Results

| Cycle | targets | deferred_first | collected | deferred | claims | wall_s |
|-------|---------|----------------|-----------|----------|--------|--------|
| 1 | 29 | 0 | 20 | 9 | 107 | 502 |
| 2 | 10 | 9 | 8 | 2 | 47 | 126 |
| 3 | 15 | 2 | 11 | 4 | 50 | 146 |
| 4 | 15 | 4 | 9 | 6 | 36 | 105 |
| 5 | 5 | 6 | 5 | 0 | 21 | 94 |

- KU 최종: 84 (seed 13 → +71)
- GU open 최종: 16 (seed 28 → +45 신규 생성, 다수 적재)
- gap_resolution_rate: 0.754 (5c 기준)
- Gate: FAIL (VP2 gap_res 0.754 / multi_ev 0.598, VP3 audit_count 1 — 5c 기대)

## F1 결정

**budget 완전 제거 불필요. 현재 plan budget + defer 구조 유지.**

근거:
1. **defer 메커니즘 정상 동작** — 매 cycle budget 초과 GU가 deferred_targets에 기록되고 다음 cycle deferred_first로 우선 소진 (C2 deferred_first=9 확인)
2. **C1 502초 병목은 budget 문제 아님** — `balance-*` wildcard 엔티티(S4 미제거)가 accommodation/tips 슬롯에 모든 accommodation 타입과 conflict check 유발. integrate LLM 호출 폭발이 원인
3. **search_calls는 plan budget 수준(20~29 GU×2 query)** — max_search_calls_per_cycle=500은 실질 미발동
4. **claims/cycle 감소 추세** (107→47→50→36→21) — GU 해소되며 자연 수렴

추가 이슈 (별도 트래킹):
- telemetry cycles.jsonl의 cycle 번호가 모두 0, search/llm_calls 모두 0 → telemetry 버그 (D-new)
- `balance-0/tips`에 accommodation 타입 전부 충돌 → S4 가속 필요
