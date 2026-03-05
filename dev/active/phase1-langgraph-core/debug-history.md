# Phase 1 Debug History — LangGraph Core Pipeline
> Last Updated: 2026-03-05
> Status: ✅ Complete

---

## 디버깅 이력

Phase 1 진행 중 발생한 버그, 원인, 수정, 교훈을 기록한다.

| # | 날짜 | Task | 증상 | 원인 | 수정 | 교훈 |
|---|------|------|------|------|------|------|
| 1 | 2026-03-05 | 1.15 | `route_after_mode`에서 `AttributeError: 'NoneType'` | `state.get("current_mode", {})` — key가 `None`으로 존재하면 기본값 `{}`가 반환되지 않음 | `state.get("current_mode") or {}` 패턴으로 변경 | `dict.get(key, default)`는 key가 존재하면(값이 None이어도) default를 반환하지 않음. `or {}` 패턴 필수 |
| 2 | 2026-03-05 | 1.16 | `GraphRecursionError` — recursion_limit=25/100 모두 초과 | critique가 `converged: False` 반환 → 무한 루프 (cycle < 5이면 수렴 불가) | `graph.stream()` + `_stream_until()` 헬퍼로 1 Cycle만 실행하는 테스트 설계로 전환 | `graph.invoke()`는 종료 조건 없으면 무한 루프. 통합 테스트는 `stream()` 기반 단계별 검증이 안전 |
