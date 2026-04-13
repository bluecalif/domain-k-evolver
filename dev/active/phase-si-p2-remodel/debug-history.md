# Silver P2: Outer-Loop Remodel — Debug History
> Last Updated: 2026-04-13
> Status: **Gate REVOKED**

---

## D-P2-1: P3 연쇄 무효화로 Gate REVOKED

**증상**: P2 실 벤치 trial 준비 중 collect LLM parse가 모든 GU에서 0 claims 반환 발견.

**원인**: P3 D-120 참조. P3의 SEARCH→FETCH→PARSE(LLM) 통합 경로 미검증.
P2의 remodel 구현은 정상이지만, 그 위에서 동작하는 collect 파이프라인이 실제 claims를 생산하지 못하므로 실 벤치 trial 결과를 신뢰할 수 없음.

**영향**: P2 Gate PASS 무효 → P3 수정 후 순차 재판정 필요.

**조치**: P3 문제 해결 → P3 Gate 재판정 → P2 실 벤치 재실행 → P2 Gate 재판정.
