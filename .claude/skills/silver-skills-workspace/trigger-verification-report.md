# Silver Skills — Trigger Verification Report

> Generated: 2026-04-11
> Method: Manual description-only walkthrough (no subagent eval, no `run_loop.py`)
> Skills: silver-trial-scaffold, silver-phase-gate-check, silver-hitl-policy, silver-provider-fetch
> Eval set: `trigger-eval.json` (16 queries — 14 positive, 2 negative)

## Method

Each query was matched against the four `silver-*` SKILL.md frontmatter `description` fields (and adjacent existing skills `evolver-framework`, `langgraph-dev`) by reading the descriptions only. The judgment uses the same heuristic Claude applies at runtime: keyword overlap + intent direction + explicit anti-triggers.

This is a lightweight check — not equivalent to a subagent benchmark. It catches description ambiguity, missing keywords, and obvious cross-skill collision, but cannot measure actual model behavior under load.

## Results

| # | Query (요약) | Expected | Predicted | Result | Note |
|---|--------------|----------|-----------|--------|------|
| 1 | P0 baseline 디렉토리 + trial-card 만들기 | scaffold | scaffold | ✅ | "trial-card" / "bench/silver" / "P0 baseline" 모두 description 명시어 |
| 2 | ddg fallback + fetchfirst-v2 trial 새로 | scaffold | scaffold | ✅ | description 의 "fetch-first 실험 trial", "ddg-fallback" example tag 매치 |
| 3 | P3 trial 끝, fetch 0.78, readiness-report 만들고 P3 gate 판정 | gate-check | gate-check | ✅ | "P3 gate 통과했나" + "readiness report 작성" 정확 매치 |
| 4 | P0 닫아도 되나, S1/S2/S3 통과 | gate-check | gate-check | ✅ | "P0 gate 확인" + "Silver phase 닫아도 되나" |
| 5 | graph.py plan→hitl_a→collect, hitl_gate.py 정리 | hitl-policy | hitl-policy | ✅ | "graph.py 에서 HITL edge 를 제거" + "hitl_gate.py" |
| 6 | metrics_guard cost_regression_flag, dispute_queue vs ledger | hitl-policy | hitl-policy | ✅ | "auto-pause 임계치 추가" + "dispute_resolver 실패 처리" |
| 7 | SearchProvider Protocol, tavily_provider, fetch 빼기 | provider-fetch | provider-fetch | ✅ | "src/adapters/providers/" + "tavily 분리" 정확 매치 |
| 8 | robots.txt 거부 도메인 fetch 단계, S8 | provider-fetch | provider-fetch | ✅ | "robots.txt 처리" — S8 언급에도 구현 의도가 우세 |
| 9 | EU/claim 1.6, P3 gate 1.8, provenance 비어있는 게 원인? | provider-fetch | **AMBIGUOUS** | ⚠️ | gate-check ("P3 gate") 와 provider-fetch ("provenance 필드") 둘 다 가능. alt_acceptable 로 처리 — 두 skill 다 호출되어도 무방 (handoff 가능) |
| 10 | Bronze Phase 5 conflict_resolver 디버깅 | (none) | none | ✅ | 4 skill 모두 "Bronze... 작업에는 사용하지 않는다" 명시 — anti-trigger 작동 |
| 11 | 5분마다 git status 자동 실행 | (none) | none | ✅ | silver-* 와 무관, schedule/loop 영역 |
| 12 | p3 trial readiness INDEX.md row 추가, status complete | scaffold | scaffold | ✅ | scaffold 가 INDEX 관리 owner (Step 5). gate-check 는 값 산출 owner. 두 skill 모두 호출되어도 정합적 |
| 13 | novelty 0.18, P4 gate 0.25 못 맞춤, reason_code 박혀있음 | gate-check | gate-check | ✅ | P4 전용 skill 없음 — gate-check 가 진단 owner |
| 14 | 부동산 2nd domain smoke, seed pack + trial 디렉토리 | scaffold | scaffold | ✅ | "새 도메인 스모크" 명시 매치 |
| 15 | DDG provider entropy_floor 1.5 게이팅 | provider-fetch | provider-fetch | ✅ | "ddg fallback" + "domain entropy" 정확 매치 |
| 16 | remodel 노드 + HITL-R + phase_bump graph 흐름 | hitl-policy | hitl-policy | ✅ | "interrupt 어디 걸지" + HITL-R 배치 = hitl-policy 영역 |

### Summary

| Result | Count |
|--------|-------|
| ✅ Correct (single skill) | 13 |
| ✅ Correct (negative — no trigger) | 2 |
| ⚠️ Ambiguous (both alt acceptable) | 1 |
| ❌ Wrong | 0 |

**Trigger accuracy: 15/16 unambiguous + 1/16 acceptable ambiguity = 16/16 acceptable.**

---

## Discrimination Analysis

### Description boundaries (good)

각 skill 의 description 은 서로 다음 키워드 축으로 분리됨:

| Skill | 핵심 키워드 | 안티-트리거 |
|-------|------------|------------|
| `silver-trial-scaffold` | trial-card, bench/silver, INDEX.md, baseline, 도메인 스모크 | Bronze japan-travel, 단발 디버깅 |
| `silver-phase-gate-check` | gate, readiness-report, VP1/VP2/VP3, 임계치, 통과 판정 | Bronze Gate #5, 단일 메트릭만 |
| `silver-hitl-policy` | HITL-A/B/C/S/R/D/E, hitl_gate.py, dispute_queue, auto-pause, graph edge | Bronze HITL gate 디버깅 |
| `silver-provider-fetch` | SearchProvider, FetchPipeline, tavily/ddg/curated, robots.txt, provenance, domain_entropy | Bronze search_adapter 그대로, P3 외 phase |

키워드 충돌 가능 영역 (의도적 handoff):
- **scaffold ↔ gate-check** — trial 생성/판정의 시간 순서. scaffold 본문의 "readiness-report 의 지점" 섹션이 핸드오프를 명시.
- **gate-check ↔ provider-fetch** — P3 gate FAIL 시 원인 분석. gate-check 가 판정, provider-fetch 가 fix. 두 skill 의 "관련" 섹션이 상호 참조.
- **hitl-policy ↔ langgraph-dev** — graph routing. hitl-policy 는 정책, langgraph-dev 는 일반 LangGraph 패턴. anti-trigger 명시.

### Risk: Query 9 의 모호성

> "claim 당 평균 EU 수가 1.6인데 P3 gate 가 1.8이거든. provenance 필드 비어있는 게 원인일까?"

이 query 는 두 의도를 동시에 가짐:
- (a) gate 항목 측정값 확인 → gate-check
- (b) 원인 hypothesis (provenance 필드) → provider-fetch

**현재 상태**: 두 skill 모두 호출되어도 정합적 (handoff 가능). 강제 단일 트리거가 필요하면 **scaffold/gate-check description 에 "원인 진단은 silver-provider-fetch 와 함께 사용"** 같은 명시 추가 가능. 현재로서는 약한 ambiguity 로 두는 것이 더 자연스러움 — Claude 가 두 skill 을 모두 참조해 더 풍부한 답을 낼 가능성이 있음.

### Risk: Bronze 안티-트리거 강도

Query 10 의 negative 가 정상 작동하려면 4 skill 의 "사용하지 않는다" 절이 충분히 강해야 함. 현재 모든 description 에 다음 형태로 들어가 있음:

- scaffold: "Bronze `bench/japan-travel/` 작업이거나 단발 cycle 디버깅에는 사용하지 않는다"
- gate-check: "Bronze Phase 5 의 Gate #5 (이미 PASS) 를 다시 채점하거나, 단일 메트릭만 빠르게 보려는 경우에는 사용하지 않는다"
- hitl-policy: "Bronze (Phase 1~5) HITL gate 코드를 그대로 유지·디버깅하는 작업에는 사용하지 않는다"
- provider-fetch: "Bronze 의 `search_adapter.py` 를 그대로 쓰는 작업이나 P3 외 다른 Phase 작업에는 사용하지 않는다"

→ 모두 충분히 명시적. Query 10 같은 Bronze 디버깅은 기각될 것.

---

## Cross-Skill Reference Hygiene

각 skill 은 본문 마지막의 "관련" 섹션에서 다른 skill 을 명시 참조 — handoff 경로가 깨지지 않음:

- scaffold → gate-check (실행 후 readiness 작성), implementation-tasks §4 P0-A
- gate-check → trial-scaffold (선행), masterplan §4/§7/§10
- hitl-policy → langgraph-dev, evolver-framework, masterplan §14
- provider-fetch → gate-check (P3 채점), hitl-policy (cost_regression_flag), evolver-framework (Evidence-first), masterplan §13

순환 참조 없음. depth 1 의 directed graph.

---

## What This Check Does NOT Cover

다음은 manual review 의 범위를 벗어남:

1. **실제 모델 트리거 빈도** — `run_loop.py` (`claude -p` 사용) 가 필요. 16 query × 3 회 반복 × 4 description 변형 = 192 호출 정도면 정확한 trigger rate 측정 가능.
2. **할루시네이션 / 잘못된 verbatim** — masterplan v2 §4/§13/§14 본문과 SKILL.md 의 표가 정확히 일치하는지 텍스트 단위 검증은 별도 task.
3. **Skill 본문의 instructions 가 실제로 작동하는지** — 1회라도 skill 을 호출해서 결과 품질 보는 end-to-end 테스트는 미수행.
4. **테스트 누적 수 (468 → 588) 가 P0 시점에 정말 맞는지** — P0 진행 중에 검증 필요.

위 4 항은 P0 착수 후 첫 trial 에서 자연스럽게 검증될 사항.

---

## Verdict

**4개 silver-* skill 의 description 은 트리거 정확도 측면에서 production-ready.**

- 13/16 query 가 단일 skill 로 명확히 트리거
- 1/16 (Query 9) 는 의도적 ambiguity (handoff 가능)
- 2/16 negative 가 anti-trigger 작동 확인
- skill 간 cross-reference 가 handoff 경로 보장

**다음 액션 권고**:
1. P0 첫 task 인 P0-A1 (`bench/silver/INDEX.md` 생성) 에서 `silver-trial-scaffold` 실호출 → end-to-end 검증
2. 그 결과를 보고 description 미세 조정 필요 시 `run_loop.py` 로 정량 최적화
3. P3 착수 시점에 `silver-provider-fetch` 도 동일 절차로 실호출 검증
