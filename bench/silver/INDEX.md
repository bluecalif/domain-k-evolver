# Silver Trial Registry

> 모든 Silver 세대 trial 의 단일 레지스트리. 1행 = 1 trial.
> masterplan v2 §12.4 verbatim 컬럼.
>
> **규칙**:
> - 기존 row 절대 삭제 금지 (§12.3 규칙 6 — 폐기 != 삭제, `status=archived` 로 보존)
> - `status` 값: `planned` | `running` | `complete` | `failed` | `archived`
> - `readiness` 컬럼: gate 판정 요약 (예: `VP1=5/5 VP2=6/6`), 미판정 시 `-`
> - cross-trial 비교는 이 파일과 개별 `readiness-report.md` 에서만 (§12.3 규칙 5)

| trial_id | domain | phase | date | goal | status | readiness | notes |
|----------|--------|-------|------|------|--------|-----------|-------|
| p0-20260411-baseline | japan-travel | p0 | 2026-04-11 | P0 Foundation Hardening — Bronze seed + 5 cycle (첫 시도) | archived | VP1=3/5 VP2=3/6 FAIL | Bronze seed staleness 이슈, run_bench 사용 (audit 미포함) |
| p0-20260412-baseline | japan-travel | p0 | 2026-04-12 | P0 Foundation Hardening — fresh seed + 15 cycle + Orchestrator | complete | VP1=5/5 VP2=5/6 VP3=5/6 PASS | Gate PASS. R3_multi_evidence, R6_closed_loop non-critical FAIL |
| p5-infra | japan-travel | p5 | 2026-04-18 | Telemetry Contract & Dashboard — schema+emitter+7 views | complete | G5-1~6 PASS S10 PASS | 코드/인프라 phase, 전용 trial 없음. 821 tests, LOC 986 |
| p6-diag-off-remodel-off-15c | japan-travel | p6 | 2026-04-19 | P6-A1-D4 matrix B 조합 — stage-e off + remodel off 15c (inside view 비교용) | complete | VP1=5/5 VP2=5/6 VP3=1/6 (의도된 FAIL) | Path-γ 확정, D-167. gap_res 0.926 (A 0.805), open 9 (A 25), NO-SEL -36pp |
