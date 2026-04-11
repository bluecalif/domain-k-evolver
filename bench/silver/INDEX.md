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
| p0-20260411-baseline | japan-travel | p0 | 2026-04-11 | P0 Foundation Hardening 완료 증명 — Phase 4·5 동등 스모크 재현 | planned | - | - |
