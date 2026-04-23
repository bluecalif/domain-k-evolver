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
| p7-ab-on | japan-travel | p7 | 2026-04-22 | SI-P7 Step A+B 전체 on — S1+S2+S3+S4 합산 효과 측정 | complete | VP1=3/5 VP2=4/6 VP3=5/6 FAIL | GU 고갈: cycle3 이후 open=0. KU=82 정체. gap_res=1.0 (misleading). S5a 없이는 동작 불가 |
| p7-ab-off | japan-travel | p7 | 2026-04-22 | SI-P7 Step A+B baseline off — P7 이전 코드 (c300b3c) | complete | VP1=5/5 VP2=5/6 VP3=5/6 PASS | baseline. KU=141, GU=117, late_discovery=21, min_ku_per_cat=8 |
| p7-v2-smoke | japan-travel | p7 | 2026-04-23 | SI-P7 V-T6 V2 계측 1c smoke — si-p7-signals.json emit 검증 | complete | - (smoke) | V2 계측 7 필드 persist 확인, condition_split=5, suppress=3. R1(cycle_count offset) fix 유도. 사후 등록 |
| p7-ab-minus-s2 | japan-travel | p7 | 2026-04-23 | SI-P7 V-T8 V3 Trial #1 — S2 축 ablation (H5c 검증) | complete | - (ablation, gate 대상 아님) | **H5c CONFIRMED**. c3+ GU=0 패턴 ab-on 과 동일. S2 유일 효과: c1-c2 condition_split +18 KU. KU=48→64(c2)→64 고착. 9분 완주. git 61e5514 |
