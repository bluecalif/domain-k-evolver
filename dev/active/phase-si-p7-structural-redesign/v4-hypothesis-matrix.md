# V-T10 · v4 Hypothesis Matrix

> Generated: 2026-04-23 (Step V / V-T10)
> Purpose: SI-P7 c3+ exploit-only 고착의 root cause 를 **extensive** 관점에서 전체 가설 매트릭스 + 검증 plan + Clear-gate 판정으로 종합. `feedback_extensive_problem_solving.md` default 적용.
> Predecessors: `v1-signal-audit.md` (17-item ✓11/✗2/~6/N/A 2), `v2-instrumentation-design.md`, `v3-ablation-design.md`, `v3-isolation-report.md` (H5c CONFIRMED)

---

## §A — 전체 가설 매트릭스

### 관찰 데이터 요약 (3-trial, `bench/silver/japan-travel/p7-ab-{on,off,minus-s2}/telemetry/cycles.jsonl` 재파싱)

| trial | c | gu_open | gu_resolved | adj_gen | target | wsy | csy | resolved_n |
|---|---|---|---|---|---|---|---|---|
| p7-ab-on | c1 | 26 | 9 | 6 | 29 | 45 | 90 | 9 |
| p7-ab-on | c2 | 2 | 35 | 2 | 28 | 180 | 210 | 26 |
| p7-ab-on | c3 | 0 | 37 | 0 | 2 | 0 | 30 | 2 |
| p7-ab-on | c4~c15 | 0 | 37 | 0 | 0 | 0 | 0 | 0 |
| p7-ab-minus-s2 | c1 | 17 | 18 | 6 | 29 | 165 | 135 | 18 |
| p7-ab-minus-s2 | c2 | 2 | 35 | 2 | 19 | 60 | 195 | 17 |
| p7-ab-minus-s2 | c3 | 0 | 37 | 0 | 2 | 0 | 30 | 2 |
| p7-ab-minus-s2 | c4~c8 | 0 | 37 | 0 | 0 | 0 | 0 | 0 |
| p7-ab-off | c1 | 40 | 11 | 6 | 13 | 75 | 105 | 11 |
| p7-ab-off | c2 | 55 | 23 | **24** | 14 | 0 | 180 | 12 |
| p7-ab-off | c3~c7 | 50→27 | 33→60 | 5,3,1,0,0 | 14→8 | 0 | 180→90 | 10→6 |
| p7-ab-off | c8 | 35 | 69 | **17** | 11 | 75 | 60 | 9 |
| p7-ab-off | c9 | 31 | 83 | **10** | 20 | 60 | 210 | 14 |
| p7-ab-off | c10~15 | 28→14 | 86→103 | 0,0,0,2,1,0 | 7→10 | 0→30 | 75→120 | 3→6 |

- **핵심 관찰 1**: ab-on 과 minus-s2 의 c3+ 패턴이 완전 동일 (open=0, resolved=37, adj_gen=0, tgt=0) → H5c 재확인
- **핵심 관찰 2**: ab-off 는 c2·c8·c9·c13·c14 에 **adj_gen burst 재발** (17, 10, 24, …). S3 off 에서는 GU 재생이 살아있음
- **핵심 관찰 3**: 고갈 연쇄 `adj_gen=0 → gu_open=0 → target=0 → claim=0`. c3 의 2개 claim 에서도 adj 가 0 생성되는 것이 실제 이탈 지점

### GU creation path 전수 (V-T10c 코드 리뷰 결과)

| # | Site | 조건 | c3+ 발화 가능? | S3 gating? |
|---|---|---|---|---|
| G1 | `seed.py:374` | cycle 0 초기 seed | No (1회) | No |
| G2 | `integrate.py:736` (`_generate_dynamic_gus`) | claim 당 1회 · S3-T8 blocklist(source) → S3-T1 suppress(mean×1.5) → S3-T2 blocklist(adj) → existing_slots → dynamic_cap | Yes (claim 있을 때) | **Yes (S3 전면 gating)** |
| G3 | `critique.py:561` (`_generate_refresh_gus`) | stale KU 발견 시 | Yes | No |
| G4 | `orchestrator.py:675` (gap_rule `prioritize_category`) | remodel 처방 compile 시 | Yes (remodel 발동 조건부) | No |
| G5 | `plan_modify.py:181` | gap_map 복사만, **신규 없음** | N/A | N/A |

→ **c3+ 유의미한 공급원은 G2 + G3 + G4 의 3경로**. 사용자 가설 "S5a 는 GU 생성의 유일 path" 는 **이 관점에서 REJECTED**. 다만 S5a 는 "새 entity 도입" 유일 경로이므로, **entity-anchor 가 고정된 상태에서의 adj 확장 한계** 는 여전히 성립.

### 매트릭스

| H# | 설명 | Status | 증거 / 출처 |
|---|---|---|---|
| **H1** | S3 adjacent rule engine 커버리지 한계 (field_adjacency 정의 부족) | **UNTESTED** | S3-off trial 부재. 코드상 `_get_adjacency_fields` fallback 이 전체 applicable field 반환하므로 "커버리지 한계"는 rule engine 부분에만 해당 |
| **H2** | S3-T1 suppress 과다 (`mean × 1.5`) | **UNTESTED** (WEAK signal) | V2 계측: p7-ab-on 에서 c1-c2 에 3건 suppress event 기록됨. c3+ 부재는 **claim=0 때문**으로 suppress 의 c3+ 효과 확증 불가 |
| **H3** | S3-T2/T8 blocklist 고착 (`recent_conflict_fields`) | **UNTESTED** | `recent_conflict_fields` persist 확인 (V-T6). 그러나 blocklist 가 c3+ 에 남아 adj 를 차단하는지 vs claim=0 이 원인인지 분리 미완 |
| **H4** | S3-T7 yield tracker 조기 약화 (rule-level attempted/resolved) | **UNTESTED** | `adjacency_yield` 6 rules 추적 중. 임계 효과 관찰 없음 |
| **H5c** | S2-T4 β (aggressive) = S5a coupled dead code | **CONFIRMED** | `v3-isolation-report.md` §B: p7-ab-on c3+ ≡ p7-ab-minus-s2 c3+. S2 off 시 c3+ 거동 불변 |
| **H6** | S5a 부재 = primary cause | **UNTESTED (by construction)** | S5a 구현 전 검증 불가. 단 H9 결과로 **"유일 경로" 전제가 REJECTED 되었으므로 primary 여부는 재평가 필요** |
| **H7** | S4-T1 balance-* 제거 단독 원인 | **WEAKENED** | p7-ab-off (balance-* **포함**) 에서도 KU=147 로 성장 → balance-* 복구는 단독 해답 아님. 단 seed 단계 open GU 가 ab-off=40 vs ab-on=26 으로 차이 → 초기 GU pool 의 총량 효과는 별도 변수 |
| **H8** | adj_gen death in S3-on (S3 가 adj 생성을 죽여 c3+ 에서 GU 재생 정지) | **STRONGLY SUPPORTED · UNTESTED (S3-off trial 부재)** | ab-on/minus-s2 adj_gen 합계 c1-c15 = **8** vs ab-off = **69** (8.6×). 단 기제는 당초 예상한 "S3 가 c3+ 에서 adj 를 직접 차단" 이 아니라 **"S3 가 c1-c2 에 adj 공급을 조기 위축 → target 조기 고갈 → c3+ claim 0 → adj loop 미실행"** (수정판) |
| **H9** | GU 재생 path enumeration (S5a 가 유일 경로인가) | **PARTIALLY REJECTED · CONTEXT-DEPENDENT** | c3+ 공급 가능 site = G2(adj)·G3(refresh)·G4(gap_rule) 3개. "S5a 만이 유일 경로" 라는 narrow claim 은 REJECTED. 단 **새 entity-anchor 도입** 관점에서는 S5a 가 유일 — 기존 anchor 내에서 G2/G3/G4 가 adj 공간을 소진하면 S5a 만 남음 |
| **H10 (신규)** | Target 고갈 = 실질적 root cause, adj_gen=0 은 귀결 | **STRONGLY SUPPORTED** | c3+ 에서 target=0 이 관찰됨. target 은 open GU 에서 생성되므로 `open=0 → target=0 → claim=0 → _generate_dynamic_gus 호출 0 → adj_gen=0` 의 연쇄. c3 자체 (open=0 직후) 에서는 csy=30 로 claim 2건 있으나 **이 2건으로부터 adj 가 0 생성됨** — 이것이 진짜 gate. 기제는 existing_slots / suppress 중 하나로 추정. 미확증 |

### 매트릭스 요약
- **CONFIRMED**: 1 (H5c)
- **STRONGLY SUPPORTED (require S3-off trial)**: 2 (H8, H10)
- **WEAKENED**: 1 (H7)
- **PARTIALLY REJECTED**: 1 (H9 "only path" claim)
- **UNTESTED**: 5 (H1, H2, H3, H4, H6)

---

## §B — 미해소 가설 검증 plan

### B.1 Trial #2 `p7-ab-minus-s3` 8c (H1~H4, H8 동시 검증)

- **목적**: S3 전체 off 시 c3+ adj_gen / target / KU 성장 회복 여부 관찰
- **실행 도구**: `SI_P7_AXIS_OFF=s3 PYTHONUTF8=1 python scripts/run_readiness.py --bench-root bench/silver/japan-travel/p7-ab-minus-s3 --cycles 8`
- **비용 예상**: ~$0.60–0.80 (9분 내외, V-T8 참고)
- **선결**: `SIP7AxisToggles` 에 `s3_enabled` 필드 추가 필요 (V-T7b 에서 `s2_enabled` 만 구현됨). 1~2 hour dev + L1 테스트
- **Expected outcomes** (3-way):
  | outcome | 조건 | 해석 |
  |---|---|---|
  | R1 | c3+ adj_gen > 0, open > 0 유지, KU 점진 성장 | H8 CONFIRMED. S3 가 adj 공급 죽임. H1~H4 중 1+ 가 효과적 |
  | R2 | c3+ 여전히 adj_gen=0, KU 고착 | H8 REJECTED. S3 외 요인 (seed pool? S2 c1 차이?) 주범. H9 path G3/G4 fallback 검증 필요 |
  | R3 | 부분 회복 (adj_gen 간헐 burst, KU 중간 성장) | H8 PARTIAL. 다른 요인과 결합 |
- **Decision rule**: R1 → S5a 착수 조건 미충족 (S3 수정이 우선). R2 → H6(S5a) 로 범위 이동. R3 → H3 (blocklist window 축소) 등 S3 subitem 조정 실험 추가

### B.2 `p7-ab-minus-s4` 8c (H7 완전 배제, optional)

- **목적**: balance-* 단독 효과 확인
- **예상 비용**: ~$0.60–0.80
- **조건**: B.1 R2/R3 시에만. R1 시 불필요

### B.3 H6 (S5a 부재) — 순서상 **최후**

- **조건**: H1~H4, H7, H8, H10 모두 REJECTED 되어 잔여 가설이 H6 만 남을 때
- **방법**: S5a 구현 → p7-s5a-on 15c + baseline 비교

### B.4 H10 (target 고갈 기제 pinpoint) — 0 cost 분석

- **방법**: ab-on c3 시점의 claim 2건 entity_key/field 와 해당 시점 gap_map snapshot 수동 조사. existing_slots / suppress / blocklist 중 어느 게이트가 c3 adj=0 을 초래했는지 확정
- **Pre-requisite**: `state/cycle-2-snapshot.json` 또는 유사한 중간 스냅샷이 persist 되어 있는지 확인 필요. 없으면 V-T11 전에 smoke 로 재포착
- **Expected**: G2 의 5가지 gate 중 1개를 점검 포인트로 확정 → B.1 이후 최소 코드 수정 범위 결정

### Plan 요약 순서
1. **B.4** (0 cost, 자료 조사) — target 고갈 gate 확정
2. **S3 toggle 구현 확장** (`s3_enabled`)
3. **B.1** Trial #2 `p7-ab-minus-s3` 8c — **핵심 Gate**
4. (R2/R3 시) **B.2** Trial #3 `p7-ab-minus-s4` 8c
5. (전부 소거 시) **B.3** S5a 구현

---

## §C — Clear-gate 판정

### 현재 상태 (2026-04-23)

| 가설군 | 상태 | S5a 착수에 미치는 영향 |
|---|---|---|
| H5c | CONFIRMED | β aggressive 는 dead code 확정 — 착수 전 정리 대상 |
| H7 | WEAKENED | 단독 원인 아님 — 우선순위 낮음 |
| H8/H10 | STRONGLY SUPPORTED · UNTESTED | **B.1 선결 없이 S5a 착수 금지**. S3 수정이 더 저렴한 해답일 수 있음 |
| H9 | PARTIALLY REJECTED | S5a 의 "유일 해답" narrative 부정. 대체 경로 존재 가능 |
| H1~H4, H6 | UNTESTED | **B.1 로 H1~H4 일괄 검증, H6 는 최후** |

### Clear-gate 결론: **❌ NOT CLEARED**

- **모든 가설 해소 전 S5a 착수 금지** (사용자 명시 조건 재확인)
- 특히 **B.1 (Trial #2 p7-ab-minus-s3)** 결과 없이는 S3 수정 vs S5a 구현 중 어느 쪽이 ROI 높은지 비교 불가
- **다음 필수 단계**: B.4 (0 cost 분석) → s3 toggle 구현 → B.1 실행 → 결과에 따라 B.2 또는 B.3 또는 S3 코드 수정

### S5a 착수 자격 체크리스트 (모두 ✓ 시에만 진행)
- [ ] B.1 실행 및 R2 outcome 확정 (H8 REJECTED)
- [ ] H10 기제 pinpoint (B.4) — target 고갈 원인이 S5a 부재임을 확정
- [ ] H9 context 재검토 — G2/G3/G4 중 c3+ 회복 경로가 **없음** 을 코드+trial 로 확증
- [ ] H6 가 잔여 최후 가설로 남음을 공식 기록

### 사용자 결정 요청

다음 행동 선택지 (default 포함, 선택지 2~3개):

- **A (권장, 저비용 선행)** — B.4 먼저 수행 (0 cost, ~30분). target 고갈 gate pinpoint 후 s3 toggle 구현 착수 → B.1 승인 요청
- **B (병렬)** — s3 toggle 구현 & B.4 를 병렬로 진행 후 B.1 바로 실행

둘 다 S3 실험 (B.1) 이 공통 gate. B.4 결과가 toggle 구현 스코프에 영향을 줄 수 있어 A 권장.
