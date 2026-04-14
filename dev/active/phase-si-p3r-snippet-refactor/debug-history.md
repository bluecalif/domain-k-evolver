# SI-P3R: Debug History

> 전신 Phase(SI-P3)의 debug-history는 `dev/active/phase-si-p3-acquisition/debug-history.md` 참조.
> D-120 진단 세부 기록은 `docs/session-compact.md` (2026-04-13).

## Pre-refactor (상속)

- **D-120** (2026-04-13): `_parse_claims_llm` 0 claims
  - 진단 trial 2회 (`p3-20260413-llm-diag`, `p3-20260413-llm-verify`)
  - 확정 근본 원인: curated 홈페이지 URL + raw HTML 노이즈
  - 부분 완화(html_to_text, URL 정렬) 후에도 구조적 문제 잔존
  - 최종 결정: 3단계 자체를 폐기 (→ SI-P3R)

## SI-P3R 신규 이슈

(작업 진행 중 기록)
