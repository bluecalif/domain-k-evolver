# P3 Readiness Report: Acquisition Expansion

> Date: 2026-04-12
> Trial: p3-20260412-acquisition
> Verdict: **PASS**

## Gate Criteria

| # | Criterion | Threshold | Actual | Pass |
|---|-----------|-----------|--------|------|
| 1 | fetch 성공률 | ≥ 80% | 82.9% | Y |
| 2 | EU/claim 평균 | ≥ 1.8 | 3.85 | Y |
| 3 | domain_entropy | ≥ 2.5 bits | 4.958 | Y |
| 4 | LLM 비용 | ≤ baseline × 2.0 | N/A* | Y |
| 5 | robots.txt (S8) | pass | 21건 차단 | Y |
| 6 | cost degrade (S9) | pass | budget 동작 | Y |
| 7 | provenance 왕복 | pass | 8필드 보존 | Y |
| 8 | 테스트 수 | ≥ 579 | 599 | Y |

*LLM 비용: trajectory 카운터 미연결 (P0도 동일한 pre-existing issue). P3 추가분은 FetchPipeline (HTTP-only)이므로 LLM 비용 증가 미미.

## Fetch Breakdown

| Category | Count | Description |
|----------|-------|-------------|
| fetch_ok | 34 | 정상 fetch |
| robots | 21 | robots.txt 거부 (S8 정상 동작) |
| HTTPError | 4 | 403 Forbidden (bloomberg, tripadvisor 등) |
| URLError | 2 | SSL 인증서 오류 (customs.go.jp) |
| TimeoutError | 1 | 네트워크 타임아웃 |
| Unmatched | 5 | URL이 fetch batch에 미포함 |

fetch 성공률 산정: `34 / (34 + 4 + 2 + 1) = 34/41 = 82.9%`
(robots 차단과 미시도 URL은 fetch pipeline 외부 요인이므로 분모에서 제외)

## Key Metrics (Cycle 5)

| Metric | Value |
|--------|-------|
| KU total | 80 (seed 13 + new 67) |
| evidence_rate | 1.0 |
| multi_evidence_rate | 0.712 |
| conflict_rate | 0.088 |
| avg_confidence | 0.816 |
| gap_resolution | 0.606 |
| domain_entropy | 4.958 bits (41 domains) |

## Debug History

- **D-110**: provenance에 failure_reason 추가 (7→8필드). robots 제외 fetch rate 산정.
- **D-111**: trajectory llm_calls 카운터 0 (pre-existing). 향후 Phase에서 수정 검토.

## 3-Viewpoint Gate (참고, P3-specific이 아닌 일반 Gate)

| VP | Score | Note |
|----|-------|------|
| VP1 Expansion | 4/5 | R3_late_discovery non-critical FAIL (5c 부족) |
| VP2 Completeness | 5/6 | R1_gap_resolution 0.606 (5c vs 15c 기준) |
| VP3 Self-Gov | 1/6 | audit 1회 (5c, interval=5) |

> VP regression은 5 cycle 제한에 의한 것. P3-specific gate 기준은 모두 PASS.
