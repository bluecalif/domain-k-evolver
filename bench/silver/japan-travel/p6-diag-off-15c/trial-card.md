# Trial Card: p6-diag-off-15c

| 항목 | 값 |
|------|-----|
| trial_id | p6-diag-off-15c |
| domain | japan-travel |
| phase | si-p6-consolidation |
| date | 2026-04-18 |
| goal | stage-e-off 15c full — p6-diag-full-15c 와 공정 비교, External Anchor 차단 시 3-카테고리(NO-ANSWER/NO-INTEGRATION/NO-SELECTION) 분포 변화 측정 및 숨겨진 low-yield root cause 발견 |
| status | pending |

## Config

- **Seed**: fresh seed (bench/japan-travel/state-snapshots/cycle-0-snapshot/)
- **Model**: gpt-4.1-mini
- **Search**: Tavily
- **Cycles**: 15
- **Stage-E (External Anchor)**: **OFF** (`--no-external-anchor`)
- **Audit interval**: 5

## Hypothesis

**비교 기준**: p6-diag-full-15c (stage-e-on, 18 open @ c15, NO-SELECTION 11/61%).

- **H1**: NO-SELECTION 은 External Anchor 가 생성한 balance-0/1 계열 9개 탓 → off 에서 크게 감소
- **H2**: (medium, convenience) priority 고정 sort 문제는 stage-e 무관 → 다른 concrete (medium, convenience) GU 가 있으면 off 에서도 NO-SELECTION 발생
- **H3**: NO-ANSWER wildcard 3건 (dining:*/hours, dining:*/location, payment:*/tips) 은 seed wildcard fallback 산물 → off 에서도 동일 발생
- **Hidden RC**: 위 3 가설로 설명되지 않는 yield 저조 패턴이 stage-e-off 단독 환경에서 드러날 수 있음 (사용자 시사점)

## Command

```bash
python scripts/run_readiness.py \
  --bench-root bench/silver/japan-travel/p6-diag-off-15c \
  --cycles 15 \
  --no-external-anchor \
  --audit-interval 5
```

## Results

> 실행 후 채움
