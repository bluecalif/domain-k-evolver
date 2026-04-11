---
name: silver-phase-gate-check
description: Domain-K-Evolver Silver Phase (P0~P6) gate 정량 판정 + readiness-report.md 작성. masterplan v2 §4 의 정량 임계치, §7 의 S1~S11 blocking scenario, 누적 테스트 수 (468 → 588) 를 verbatim 검증한다. "P0 gate 확인", "P3 gate 통과했나", "Silver phase 닫아도 되나", "readiness report 작성", "VP1/VP2/VP3 점수", "gate 판정", "phase 완료 선언", "fetch 성공률 확인", "domain entropy 측정" 같은 phase 종료 시점의 모든 요청에 반드시 사용한다. Bronze Phase 5 의 Gate #5 (이미 PASS) 를 다시 채점하거나, 단일 메트릭만 빠르게 보려는 경우에는 사용하지 않는다.
---

# Silver Phase Gate Check

## 목적

Silver Phase 가 "완료" 라고 선언되려면 masterplan v2 §4 의 정량 gate 와 §7 의 blocking scenario 가 **모두** 통과해야 한다. 이 skill 은 그 판정을 결정론적으로 수행하고, 결과를 trial 의 `readiness-report.md` 로 기록한다.

> Phase gate 는 trial 내부 판정 — cross-trial 비교는 INDEX.md 와 개별 readiness-report 에만. (§12.3 규칙 5)

## 언제 쓰는가

- Silver Phase Pn 의 마지막 task 가 끝났을 때
- "이 phase 닫아도 되나?" 라는 질문이 나왔을 때
- `silver-trial-scaffold` 로 만든 trial 의 실행이 끝났을 때
- 정기 readiness 벤치마크 결과 채점 시
- Gate FAIL 의 정확한 원인을 분리해야 할 때

## 언제 쓰지 않는가

- Phase 작업 중간 진행 점검 (이건 metrics_logger 만으로 충분)
- Bronze Phase 5 Gate #5 재채점 (이미 commit `b122a23` 으로 PASS, 변경 금지)
- 단발 cycle 디버깅
- Critical FAIL 만 확인하면 되는 정신적 sanity check

---

## 핵심 원칙

1. **§4 의 체크박스가 단일 진실 소스.** 이 skill 의 표는 §4 의 거울일 뿐이며, 충돌 시 §4 가 옳다.
2. **모든 항목이 PASS 여야 PASS.** "거의 통과" 는 FAIL 이다. 정량 임계치는 협상 대상이 아니다.
3. **Blocking scenario 의 위치.** §7 의 S1~S11 은 Phase gate 의 **일부** 이지 별도 검증이 아니다. 미통과 시 해당 Phase 는 complete 선언 불가 (§7 마지막 줄).
4. **누적 테스트 수.** Phase n 의 gate 는 Phase n-1 의 테스트 수에 신규 테스트를 더한 누적값을 본다. baseline = Phase 5 의 **468 tests**.
5. **trial 격리.** 측정은 반드시 `silver-trial-scaffold` 로 만든 trial 디렉토리 안에서. 임의의 working state 로 측정하면 결과 무효.

---

## Phase 별 Gate 표 (masterplan v2 §4 verbatim)

### P0. Foundation Hardening
| # | 항목 | 임계치 |
|---|------|--------|
| G0-1 | bare-except 0 건 | `grep "except Exception:" src/nodes/` 결과 0 |
| G0-2 | 신규 metric emit | `collect_failure_rate`, `timeout_count`, `retry_success_rate` 3 개 |
| G0-3 | 테스트 누적 | ≥ **488** (468 baseline + ≥ 20 신규) |
| G0-4 | 48h soak | 임의 adapter kill 주입 → 그래프 hang 없음 |
| G0-5 | baseline trial 재현 | `bench/silver/japan-travel/p0-{date}-baseline/` 에서 VP1 ≥ 4/5, VP2 ≥ 5/6 |
| G0-6 | HITL 축소 | 일반 cycle 인라인 HITL-A/B/C 호출 0, HITL-S 첫 cycle 1회, HITL-E 트리거 시만 |
| **scenarios** | S1, S2, S3 | blocking |

### P1. Entity Resolution & State Safety
| # | 항목 | 임계치 |
|---|------|--------|
| G1-1 | alias 단위 테스트 | JR-Pass / 재팬레일패스 양방향 pass |
| G1-2 | is_a 단위 테스트 | shinkansen is_a train pass |
| G1-3 | 중복 KU 감소 | japan-travel 재실행에서 P0 baseline 대비 ≥ **15% 감소** |
| G1-4 | conflict ledger | 충돌 KU **100%** ledger 영구 보존 (resolve 후 감사 가능) |
| G1-5 | 테스트 누적 | ≥ 488 + 20 = **508** |
| **scenarios** | S4, S5, S6 | blocking |

### P2. Outer-Loop Remodel 완결
| # | 항목 | 임계치 |
|---|------|--------|
| G2-1 | remodel report schema validate | positive + negative 양방향 pass |
| G2-2 | 합성 시나리오 | entity 중복률 30%+ 상황을 remodel 이 탐지·제안 |
| G2-3 | HITL-R 승인 → 반영 | 다음 cycle skeleton 이 실제 변경됨 |
| G2-4 | rollback 경로 | 승인 거부 → state diff = ∅ |
| G2-5 | 테스트 누적 | ≥ 508 + 15 = **523** |
| **scenarios** | S7 (trigger 부분) | blocking |

### P3. Acquisition Expansion
| # | 항목 | 임계치 |
|---|------|--------|
| G3-1 | fetch 성공률 | ≥ **80%** on japan-travel seed queries |
| G3-2 | claim 당 평균 EU 수 | ≥ **1.8** (baseline ≈ 1.0) |
| G3-3 | `domain_entropy` | ≥ **2.5 bits** on ref cycle (≥ 6 고유 도메인 평형) |
| G3-4 | cycle 비용 | ≤ baseline × **2.0** (cost regression 방지) |
| G3-5 | 테스트 누적 | ≥ 508 + 35 = **558** (P2 와 병렬 시 중복 집계 주의) |
| **scenarios** | S8, S9 | blocking |

### P4. Coverage Intelligence
| # | 항목 | 임계치 |
|---|------|--------|
| G4-1 | reason_code 커버리지 | plan output 의 **모든** target 이 reason_code 보유 (100%) |
| G4-2 | novelty 평균 | 10 cycle 연속 run 에서 ≥ **0.25** |
| G4-3 | plateau trigger | 인위 plateau (동일 seed 5 cycle) → audit/remodel trigger 발동 |
| G4-4 | telemetry 노출 | novelty/overlap/coverage 가 telemetry 계약 필드로 노출 |
| G4-5 | 테스트 누적 | ≥ 558 + 10 = **568** |
| **scenarios** | S7 (full) | blocking |

### P5. Telemetry Contract & Dashboard
| # | 항목 | 임계치 |
|---|------|--------|
| G5-1 | schema validate | telemetry emit → schema validate (positive + negative) |
| G5-2 | dashboard load | 100-cycle fixture 로 모든 view ≤ **10s** |
| G5-3 | stub 금지 | HITL/dispute/remodel view 가 **실제** artifact 를 소비 |
| G5-4 | LOC 하드 리밋 | `cloc src/obs/dashboard` ≤ **2000** |
| G5-5 | 운영자 가이드 | `docs/operator-guide.md` 5 페이지 이상 walkthrough |
| G5-6 | 테스트 누적 | ≥ 568 + 15 = **583** |
| **scenarios** | S10 | blocking |

### P6. Multi-Domain Validation
| # | 항목 | 임계치 |
|---|------|--------|
| G6-1 | 2nd 도메인 readiness | 10 cycle 내 Gate #5 동등 — VP1 ≥ 4/5, VP2 ≥ 5/6, VP3 ≥ 4/6 |
| G6-2 | framework 수정 | ≤ **5 건** (초과 시 일반화 미흡, P1~P4 재방문) |
| G6-3 | 한글 출처 처리 | 에러 **0** (CLAUDE.md 인코딩 규칙 준수) |
| G6-4 | 테스트 누적 | ≥ 583 + 5 = **588** |
| **scenarios** | S11 | blocking |

### Silver 완료 (Gate #6, masterplan §10)
- 위 P0~P6 모든 gate 항목 PASS
- 11개 시나리오 (S1~S11) 전부 pass
- 5대 불변원칙 machine-check green
- 누적 테스트 ≥ **588**, 비용 regression 없음
- `bench/silver/INDEX.md` 에 P0 baseline + 2nd 도메인 smoke 행 존재
- 운영자 가이드 5+ 페이지 walkthrough

---

## Blocking scenario → Phase 매핑 (§7 verbatim)

| # | 시나리오 | 기대 동작 | Phase |
|---|----------|----------|-------|
| S1 | search timeout (mocked 60s hang) | retry → fail → metric emit → cycle 계속 | P0 |
| S2 | malformed LLM JSON | deterministic fallback, claims ≥ 1 | P0 |
| S3 | corrupt state.json | backup 복구 또는 empty 시작 + warning | P0 |
| S4 | 동의어 2개 (JR-Pass / 재팬레일패스) | 단일 KU 로 병합 | P1 |
| S5 | is_a (shinkansen → train) | parent metric 상속 | P1 |
| S6 | conflict 보존 후 resolve | ledger 에 before/after 모두 조회 가능 | P1 |
| S7 | 저 novelty 5 cycle | audit trigger → remodel 제안 | P2 / P4 |
| S8 | robots.txt 차단 도메인 | fetch skip + 로그, 다른 소스 대체 | P3 |
| S9 | 비용 예산 초과 | degrade 모드 (fetch depth ↓) | P3 |
| S10 | dashboard 텔레메트리 1 cycle | schema validate pass | P5 |
| S11 | 2nd 도메인 10 cycle | Gate #5 통과 | P6 |

각 scenario 는 **Phase gate 의 blocking test**. 미통과 시 해당 Phase 는 complete 선언 불가.

---

## 4단계 판정 절차

### Step 1. Trial 식별

판정은 항상 특정 trial 에 대해 한다.

```
- trial_id : 어느 trial 인가?
- phase    : P0~P6 중 무엇의 gate 를 보는가?
- domain   : japan-travel 인가 2nd 도메인인가?
```

trial 디렉토리가 없거나 `trial-card.md` 가 없으면 즉시 거부 — `silver-trial-scaffold` 로 먼저 trial 을 만들어야 한다.

### Step 2. Gate 항목별 측정값 수집

각 항목을 위 표 순서대로 본다. 측정 출처는 다음 우선순위:

1. `bench/silver/{domain}/{trial_id}/telemetry/cycles.jsonl` (P5 이후)
2. `bench/silver/{domain}/{trial_id}/state/` 파일들
3. `pytest` 실행 결과 (테스트 누적 항목)
4. `git log` / `cloc` (LOC 항목)

**중간 working state 로 측정하면 결과 무효** — 반드시 trial 내부에서.

### Step 3. PASS/FAIL/UNKNOWN 판정

각 항목당 3 값:
- `PASS` — 임계치 충족, 증거(파일/명령) 기록
- `FAIL` — 임계치 미달, 정확한 측정값 + 미달폭 기록
- `UNKNOWN` — 측정 불가 (스크립트/데이터 부재). UNKNOWN 은 PASS 가 아니다 — gate 는 FAIL 처리.

전체 verdict 규칙:
- 모든 항목 PASS + 모든 blocking scenario PASS → **GATE PASS**
- 1 개라도 FAIL/UNKNOWN → **GATE FAIL**
- "거의 통과" 는 PASS 가 아니다.

### Step 4. readiness-report.md 작성

trial 디렉토리에 `readiness-report.md` 를 다음 템플릿대로 채운다:

```markdown
# Readiness Report — {trial_id}

> Trial: {trial_id}
> Phase: {phase}
> Verdict: **{PASS|FAIL}**
> Reported: {YYYY-MM-DD HH:MM KST}
> Trial card: ./trial-card.md
> Config snapshot: ./config.snapshot.json

## Verdict Summary

| Phase | Items | PASS | FAIL | UNKNOWN | Verdict |
|-------|-------|------|------|---------|---------|
| {phase} | {N} | {p} | {f} | {u} | {PASS\|FAIL} |

## Gate Items

| # | 항목 | 임계치 | 측정값 | 결과 | 증거 |
|---|------|--------|--------|------|------|
| G{n}-1 | ... | ... | ... | PASS | telemetry/cycles.jsonl L42 |
| G{n}-2 | ... | ... | ... | FAIL | 측정값 0.78, 임계 0.85 (-0.07) |
...

## Blocking Scenarios

| # | scenario | 결과 | 증거 |
|---|----------|------|------|
| S{x} | ... | PASS | tests/test_.../test_....py::test_... |

## 가설 평가 (trial-card 의 H1~Hn)

- H1: ... → 검증됨 / 반증됨 / 측정 불가
- H2: ...

## Phase 5 baseline 대비 변화

| 메트릭 | baseline | 이번 | Δ |
|--------|----------|------|---|
| tests | 468 | {n} | +{n-468} |
| avg_confidence | 0.822 | ... | ... |
| ...

## 권고

GATE PASS 시:
- Phase {n} 완료 선언 가능. INDEX.md status=complete, readiness 컬럼 갱신.
- 다음 Phase {n+1} 의존 항목 unlock 확인 (§5 의존성 그래프).

GATE FAIL 시:
- 실패 항목별 root cause hypothesis 1~3 개.
- 추가 task 가 필요한지 / config 만 조정하면 되는지 분리.
- 신규 trial id 로 재실행 권고 (`{phase}-{date}-{tag}-run2` 또는 새 tag).

## Cross-trial 비교 메모

INDEX.md row 갱신 내용 (Step 5 에서 사용):
```
| {trial_id} | {domain} | {phase} | {date} | {goal} | {status} | {short readiness} | {notes} |
```
```

작성 후 INDEX.md 의 해당 row 도 동일 정보로 update 한다 (`silver-trial-scaffold` Step 5 와 일치).

---

## Phase 5 baseline 참조값

Bronze Phase 5 Gate #5 (commit `b122a23`) 의 PASS 결과 — Silver 의 모든 비교 기준점.

| 지표 | Phase 5 |
|------|---------|
| tests | **468** |
| VP1 | 5/5 |
| VP2 | 6/6 |
| VP3 | 5/6 |
| avg_confidence | 0.822 |
| staleness | 0 |
| gap_resolution | 0.909 |

Silver gate 가 이 값보다 후퇴하면 (예: VP1 < 5/5, avg_confidence < 0.82) **regression** 으로 간주하고 GATE FAIL.

---

## Anti-Patterns

| 패턴 | 문제 | 교정 |
|------|------|------|
| 일부 항목 PASS 만 보고 phase complete 선언 | "모두 PASS 여야 PASS" 위반 | 표 전체 재검 |
| trial 외부 working state 에서 측정 | 격리(§12.3 규칙 2) 위반 | trial 디렉토리 안으로 |
| blocking scenario 를 별도 검증으로 미루기 | §7 마지막 문장 위반 | gate 의 일부로 같이 채점 |
| FAIL 을 "거의 통과" 로 표현 | 정량 gate 무력화 | 측정값 + 미달폭 그대로 기록 |
| Phase 5 baseline 보다 후퇴한 값을 PASS | regression 미식별 | baseline 비교 표 필수 |
| readiness-report 없이 INDEX.md 만 update | 증거 부재 | report 먼저, INDEX 는 그 후 |

---

## 관련

- **masterplan v2 §4** — 단일 진실 소스. 이 표가 여기와 충돌하면 §4 가 옳다.
- **masterplan v2 §7** — S1~S11 scenario 정의 + Phase 매핑.
- **masterplan v2 §10** — Silver 완료 수용 기준.
- **silver-trial-scaffold** — gate 채점 대상 trial 을 만드는 선행 skill.
- **silver-implementation-tasks.md §4~§11** — 각 Phase 의 task list 와 gate 체크박스.
- **`docs/archive/phase4-readiness-report.md`, `phase5-gate2-5cycle-report.md`** — Bronze readiness 보고 형식 참고.
