# SI-P7 Step V — V3 Isolation Report (V-T9)

> 작성: 2026-04-23
> 대상: p7-ab-minus-s2 8c 실제 데이터 (V-T8 결과)
> Baseline: p7-ab-on 15c (상한) + p7-ab-off 15c (하한)
> 목적: S2 축 효과 isolate → H5c (β = S5a coupled dead code) 정량 판정

## 실행 조건 검증

- **git HEAD**: `61e5514` (V-T7b axis toggle)
- **config**: `SI_P7_AXIS_OFF=s2` → `SIP7AxisToggles.s2_enabled=False` 검증 완료 (로그 첫 줄)
- **seed**: `bench/japan-travel/state-snapshots/cycle-0-snapshot` (KU=13, GU=28) — p7-ab-on/off 와 동일
- **실행 시간**: 9분 (19:55~20:04, 10분 timeout 내)
- **8 cycles 완주** (snapshots 8개 + cycles.jsonl 8행 + readiness-report.json)

---

## [A] 핵심 지표 Cycle×Trial 비교표

KU count per cycle (state-snapshots/cycle-N/knowledge-units.json):

| c | p7-ab-on (S all ON) | p7-ab-minus-s2 (S2 OFF) | p7-ab-off (pre-SI-P7) |
|---|---|---|---|
| 1 | 26 | **48** | 31 |
| 2 | **82** | **64** | 43 |
| 3 | 82 | 64 | 53 |
| 4 | 82 | 64 | 61 |
| 5 | 82 | 64 | 68 |
| 6 | 82 | 64 | 74 |
| 7 | 82 | 64 | 80 |
| 8 | 82 | 64 | **109** |

GU open per cycle (telemetry):

| c | ab-on | minus-s2 | ab-off |
|---|---|---|---|
| 1 | 26 | 17 | 40 |
| 2 | 2 | 2 | 55 |
| 3 | **0** | **0** | 50 |
| 4 | 0 | 0 | 45 |
| 5 | 0 | 0 | 39 |
| 6 | 0 | 0 | 33 |
| 7 | 0 | 0 | 27 |
| 8 | 0 | 0 | 35 |

gap_resolution_rate per cycle:

| c | ab-on | minus-s2 | ab-off |
|---|---|---|---|
| 1 | 0.257 | 0.514 | 0.314 |
| 2 | 0.946 | 0.946 | 0.307 |
| 3+ | 1.000 (misleading, GU 고갈) | 1.000 (misleading) | 0.4~0.9 점진 |

---

## [B] H5c 정량 판정

### 가설 복기
β aggressive mode (S2-T4β) 는 `critique.py:664` 에서 `aggressive_mode_remaining=3` 설정을 수행하지만, **효과 경로 (target 확장, source_count 완화, LLM query — S5a-T11 에 배정)** 가 S5a 미구현으로 인해 실제 GU 생성을 유발하지 못한다 (D-181 β 정의 = S5a coupled).

### 판정 논리

1. **Pattern A (ab-on 과 minus-s2 의 c3+ 동일)**:
   - Both trials show `open=0, resolved=37, target=0, adj_gen=0` from c3 onwards
   - Both trials flat KU count from c2 (82 / 64)
   - Difference at c2: **18 KU** (ab-on condition_split 재정의 효과 = Rule 2b/2c/2d 로 17개 추가 split)
   - c3+: **완전 동일 trajectory** — 둘 다 복구 불가

2. **Pattern B (β 가 실제 기능이었다면 예상)**:
   - ab-on 에서 c5+ 에 stagnation 감지 → β 발동 → entity_discovery 경로로 신규 target/GU 생성
   - KU 가 82 → 90 → 100 등으로 complex 회복 예상
   - 관찰: ab-on c3+ 는 완전 정체. Pattern B 예상과 **직접 충돌**

3. **Ruling in via p7-ab-minus-s2**:
   - S2 OFF 는 β set 자체를 skip → aggressive_mode_history=0 (관찰 확인)
   - 그런데도 ab-on 과 c3+ trajectory 일치 → β 가 활성화됐든 안 됐든 결과 동일
   - = β 의 **효과 경로가 부재** = dead code

### 결과

**H5c — CONFIRMED** (정량 증거 확보).

---

## [C] 세부 Signal 분석

### p7-ab-minus-s2 `si-p7-signals.json` 요약

| 필드 | 값 | 해석 |
|---|---|---|
| `aggressive_mode_history` | **0 건** | S2 off 로 β set 경로 skip (설계대로) |
| `query_rewrite_rx_log` | **0 건** | S2-T4α 경로 skip (설계대로) |
| `condition_split_events` | 4 건 (reason=conditions only) | Rule 2 (baseline) 만 작동. Rule 2b/2c/2d skip 확인 |
| `suppress_event_log` | 3 건 (cycle 1-2) | S3-T1 suppress 정상 (s3 on 유지) |
| `adjacency_yield` | 6 rules tracked | S3-T7 yield tracker 정상 |
| `coverage_map` | 9 categories | S4-T2 deficit_score 정상 |
| `ku_stagnation_signals.added_history` | c3+ 모두 added=0, ratio=0 | **stagnation 조건 자연 충족** (만약 s2 on 이었다면 trigger 발동했을 것) |

**결정적 관찰 — `added_ratio` per cycle**:
```
[(c1, 0.265), (c2, 0.174), (c3+, 0.000)]
```
c3 부터 added=0 유지 = stagnation 정의 그대로 충족. s2 on 이었다면 `ku_stagnation:added_low` rx + `aggressive_mode_remaining=3` 이 c5~c8 에 fire 했을 것. 그러나 **c3+ GU=0 고착 → β set 해도 entity discovery 가 없어 GU 생성 불가** → H5c 일치.

### p7-ab-on 비교 (V2 계측 부재라 직접 aggressive_mode_history 추출 불가)
- 기존 run.log grep: `growth_stagnation` 3회 (lines 491/546/601 ≈ c5/c10/c15), `aggressive` 키워드 **0회**
- `ku_stagnation:added_low` 가 **prescription 으로 생성되었으나** 로그에 "aggressive" 흔적 없음 = 추가 action 없음
- V-T1 findings 와 일치: trigger 있음, action 없음 = dead code

---

## [D] Trial #1 로 밝혀진 부가 결과

### S2 의 실제 기여 (c2 시점 KU +18)

- S2 축 전체의 **유일한 관찰 가능 효과**는 **c1-c2 초기 확장 중 condition_split Rule 2b/2c/2d 로 인한 추가 KU 생성** (~+18개)
- ab-on: 82, minus-s2: 64 (@c2). 이 차이는 **c3+ 회복과 무관**
- S2-T5~T8 (condition_split 재정의) 는 초기 기록 다변화에만 기여, 시스템 복원력에는 무력

### S2 가 **아닌** 것: c3+ GU 고갈의 원인

- S2 OFF 에서도 c3+ GU=0 → S2 가 GU 고갈을 **유발하지 않음**
- S2 ON 에서도 회복 불가 → S2 가 고갈을 **해소하지도 못함**
- 고갈의 실제 원인은 S1/S3/S4 조합 (특히 S5a 부재) 에 있음

### 남은 후보 root cause (이번 V3 로 배제 불가)

- **H6 (S5a 부재)**: entity discovery node 가 없어 새 entity 발견 불가 → existing entities 의 field adjacency 로만 GU 생성 → 결국 수렴 + 고갈. **최유력**.
- **H7 (S4 balance-\* 제거 단독)**: 이번 ablation 은 S4 on 유지. S4 off trial 미수행으로 배제 못함. 그러나 p7-ab-off (SI-P7 이전 = S4 balance-\* 있음) 는 KU 147 까지 확장 → balance-\* 의 기여 크지 않아 보임
- **H1~H4 (S3 세부)**: suppress/blocklist/yield tracker 각각 정상 작동 (suppress 3회, yield 6 rule). 고갈 유발 증거 없음

---

## [E] 비용 결산

- **p7-ab-minus-s2 8c**: 실제 소요 시간 9분. 예상 (30-40분) 대비 큼지게 빠름 (c3+ GU=0 로 integrate/collect 호출 수 급감)
- readiness-report.json 기준: FAIL (8c 로 gate 통과 불가, 예상)

---

## [F] V-T10 입력 — D-192 root cause 확정 후보

### 확정 사항

1. **H5c CONFIRMED**: β aggressive mode 는 S5a coupled dead code. p7-ab-on 의 `ku_stagnation:added_low` 발동이 observable 효과를 내지 않음
2. **H7 (S4 balance-\* 단독) 약화**: p7-ab-off 가 balance-\* 포함 상태에서 KU 147 까지 확장 — balance-\* 제거가 단독 원인일 가능성 낮음 (D-190 재확인)
3. **S2 영향 범위 확정**: c1-c2 condition_split 확장 기여 (~+18 KU), c3+ 회복 무관

### 최유력 root cause (V-T10 D-192 에서 확정 예정)

**H6 (S5a 부재) + S1 defer 의 과공격성 조합**:
- SI-P7 Step A/B 가 S5a 없이 활성화되면 — S1 defer/queue 로 target 쏟아내고 c1-c2 에 초기 GU 를 모두 소진 → c3+ 새 entity 탐색 경로 (S5a) 부재 → 영구 고착
- ab-on, minus-s2 모두 S1 활성 → 동일한 "초기 burst + 영구 고착" 패턴
- ab-off (SI-P7 전체 off) 는 defer 없이 점진 처리 + 우발적 adjacent_gap (c2 24개, c8 17개, c9 10개) 로 지속 확장

### 다음 Step

- **V-T11**: S5a 착수를 main recovery path 로 결정 (D-189 복권). Step A/B 수정은 S5a 구현 완료 후 필요성 재판단
- (선택) Trial #2 `p7-ab-minus-s1` 으로 S1 과공격성 가설 직접 검증 — 필요시 사용자 승인 후

---

## 관련 문서

- `v1-signal-audit.md` — V1 재파싱 (H5c 가설 도출 근거)
- `v2-instrumentation-design.md` — V2 계측 설계
- `v3-ablation-design.md` — V3 Trial #1 설계
- `bench/silver/japan-travel/p7-ab-minus-s2/trial-card.md` — 실행 config + 가설
- D-181 (β 정의 = S5a coupled), D-189 (S5a = critical path, 보류중), D-190 (balance-* 단독 단정 금지)
