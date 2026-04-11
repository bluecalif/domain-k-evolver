# Readiness Report — {trial_id}

> Generated: {YYYY-MM-DD}
> Phase: {phase}
> Domain: {domain}
> Trial Card: `trial-card.md`

## 실행 요약

| 항목 | 값 |
|------|-----|
| trial_id | {trial_id} |
| config.snapshot.json | {존재 여부} |
| git HEAD | `{sha}` |
| git dirty | {true/false} |
| cycles run | {N} |
| 총 소요 시간 | {minutes}m |

## Gate 판정

### VP1 — Variability ({score}/5)

| 항목 | 기준 | 실측값 | PASS/FAIL |
|------|------|--------|-----------|
| {vp1_item_1} | {threshold} | {value} | {result} |

### VP2 — Completeness ({score}/6)

| 항목 | 기준 | 실측값 | PASS/FAIL |
|------|------|--------|-----------|
| {vp2_item_1} | {threshold} | {value} | {result} |

### VP3 — Self-Governance ({score}/6)

| 항목 | 기준 | 실측값 | PASS/FAIL |
|------|------|--------|-----------|
| {vp3_item_1} | {threshold} | {value} | {result} |

## Phase-specific 항목

| 항목 | 기준 | 실측값 | PASS/FAIL |
|------|------|--------|-----------|
| {phase_gate_item} | {threshold} | {value} | {result} |

## Regression 비교

| 지표 | Baseline | 이번 trial | Delta |
|------|----------|-----------|-------|
| VP1 | {baseline_vp1} | {vp1} | {delta} |
| VP2 | {baseline_vp2} | {vp2} | {delta} |
| VP3 | {baseline_vp3} | {vp3} | {delta} |

## 판정

- **Gate 결과**: {PASS / FAIL}
- **권고**: {다음 액션 — PASS 시 Phase 종료, FAIL 시 재실행/수정 방향}

## 비고
{특이사항, 경고, 알려진 문제}
