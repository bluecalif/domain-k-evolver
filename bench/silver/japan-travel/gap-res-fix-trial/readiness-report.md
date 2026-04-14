# Gap-Res Fix Trial — Readiness Report

> 생성: 2026-04-14
> 목적: D-129 (target_count cap 제거) 효과 재현 검증 + B2 Secondary 가설 확증
> 대상: `bench/silver/japan-travel/gap-res-fix-trial/` (15 cycles)

## Gate Verdict: **PASS** ✅

| Viewpoint | Result | Before (p3r-gate-trial-15c) | After |
|---|---|---|---|
| VP1 expansion_variability | 5/5 PASS | 5/5 PASS | 5/5 PASS |
| VP2 completeness | 5/6 PASS | 4/6 | **5/6 (R1 전환)** |
| VP3 self_governance | 5/6 PASS | 6/6 | 5/6 (R6 closed_loop=0) |

**전체 gate_passed=true** (JSON 참조).

## Primary 수정 효과 (B1, D-129)

| 지표 | Before | After | Δ |
|---|---|---|---|
| final gap_resolution_rate | **0.517** | **0.990** | +91% |
| gu_open (final) | 73 | 1 | −98.6% |
| gu_resolved (final) | 78 | 99 | +27% |
| gu_total | 151 | 100 | −51 (jump 누적 dynamic GU 감소) |
| KU active | 105 | 124 | +18% |
| avg_evidence_active | 3.76 | 3.52 | −6% |
| LLM 비용 | baseline | ≈1.5x (추정) | 예측 3x보다 낮음 |

**해석**: cap 제거 → jump 모드에서 open 대비 ~50% target 허용 → 15 cycle 내 거의 완전 수렴.

## Secondary 가설 (B2) 확증 — H1 기각

### parse_yield_summary (15 cycles)
- avg_claims per target: **3.5~5.0** (일관)
- zero_claims ratio: 대부분 0.0, 간헐 0.08~0.14
- **H1 (LLM parse가 []반환)**: 기각 — LLM은 target당 평균 3-5 claims 안정적 생성

### integrate_result 분류
- no_source_gu_id: **0** 전 cycle (H3 완전 기각)
- invalid_result: cycle당 0~17 (conflict 처리 등 정상)
- **other** (source_gu_id 유효, GU 이미 resolved): 다수 → 1 target = N claims fan-out의 자연스러운 결과

### 결론 (D-130 근거)
"52% conversion rate"은 `resolved / claims` 기준으로는 구조적으로 낮을 수밖에 없음 (target:claim ≈ 1:4).
**per-target 관점에서 conversion ≈ 90-100%** — cap 제거만으로 병목 해소.

## Failure modes (cross-trial)

| Rule | Before | After | 상태 |
|---|---|---|---|
| VP2 R1 gap_resolution | 0.517 < 0.85 | 0.99 ≥ 0.85 | **FIXED** |
| VP2 R3 multi_evidence | 0.755 | 0.758 | 여전히 0.80 미만 (별도) |
| VP3 R6 closed_loop | 0 < 1 | 0 < 1 | 여전 (별도 관심사) |

## 참조
- trial: `bench/silver/japan-travel/gap-res-fix-trial/`
- Before trial: `bench/silver/japan-travel/p3r-gate-trial-15c/`
- Fix commit: `2a01197` (B1+B2)
- 정적 분석: `scripts/analyze_p3r_gap.py`
- Related decisions: D-126 (gap_res 조사), D-129 (cap 제거), D-130 (H1 기각)
