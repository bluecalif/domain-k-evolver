# V5 — Sequential Ablation Report

> 2026-04-23
> SI-P7 c3+ 고착 (p7-ab-on) 의 Primary Introducer 축 확정 보고서
> V-T10 가설 매트릭스 접근(v4) 대신 **축별 순차 회귀 실험** 으로 수행

---

## 1. 실험 개요

### 1.1 배경

- **증상**: `p7-ab-on` 15c trial 의 c3+ 고착 (KU 82 정체, adj_gen=0, GU_graph 정체)
- **대안 가설 매트릭스(v4)** 는 "너무 복잡" 판정 (사용자) → Sequential Ablation 으로 전환
- **핵심 질문**: S1~S4 축 중 어느 축이 c3+ 고착 introducer 인가?

### 1.2 방법

각 축 완료 commit 을 `git worktree` 로 체크아웃 → 5c trial 각각 실행 → Pre-Step-A (baseline) 에서 순차적으로 축을 도입해 가며 c3+ 성장 패턴 변화를 관찰.

| Trial | 축 | commit |
|---|---|---|
| Pre-A | baseline (S1~S4 전) | `2ebd435` |
| S1    | S1-T1~T8 (defer/queue, target 자유화) | `4e5988c` |
| S2    | + S2-T1~T8 (integration_dist 제어입력 + ku_stagnation + β + condition_split 확장) | `f3a0be0` |
| S3    | + S3-T1~T8 (adjacent rule engine + suppress + blocklist + yield tracker) | `2d252f3` |
| S4    | + S4-T1/T2 (balance-* virtual entity 제거 + deficit_score) | `2631c38` |

- 각 trial: `run_readiness.py --cycles 5`, bench `p7-seq-{pre-a,s1,s2,s3,s4}`
- S3 Tavily 433 rate limit 오염 → 재실행 (정상 데이터 확보)
- 총 비용: ~$2.0 (5 trials)

---

## 2. 5-Trial 데이터

### 2.1 KU / GU 요약 (c1~c5)

```
=== KU total ===
trial   | c1 | c2 | c3 | c4 | c5
------------------------------------
pre-a   | 24 | 41 | 53 | 62 | 72    (건강 성장)
s1      | 46 | 54 | 64 | 78 | 88    (건강 성장)
s2      | 72 | 76 | 81 | 86 | 88    (c1 극폭증, c3+ 둔화)
s3      | 40 | 59 | 61 | 61 | 61    (c3+ 완전 no-op)
s4      | 50 | 70 | 73 | 77 | 78    (부분 회복)

=== GU total (누적 생성량) ===
pre-a   | 55 | 67 | 75 | 82 | 86    (+31)
s1      | 45 | 62 | 64 | 79 | 79    (+34)
s2      | 39 | 47 | 47 | 49 | 49    (+10, 급감)
s3      | 35 | 39 | 39 | 39 | 39    (+4,  최저)
s4      | 35 | 45 | 45 | 46 | 46    (+11, 소폭 회복)

=== GU open (source pool 잔량) ===
pre-a   | 44 | 39 | 34 | 32 | 23
s1      | 25 | 34 | 26 | 26 | 15
s2      | 13 | 17 | 12 | 11 |  8
s3      | 15 |  4 |  0 |  0 |  0    (c3+ 완전 고갈)
s4      | 15 | 10 |  7 |  2 |  1
```

### 2.2 성장 지표 (ΔKU per cycle)

```
pre-a  : +11 +17 +12  +9 +10   → 건강한 꾸준한 성장
s1     : +33  +8 +10 +14 +10   → c1 중폭증 후 안정
s2     : +59  +4  +5  +5  +2   → c1 극폭증 + c3+ 정지 패턴 도입
s3     : +27 +19  +2  +0  +0   → c3+ 완전 no-op
s4     : +37 +20  +3  +4  +1   → c4/c5 cycle 유지 (slow growth)
```

### 2.3 target_count (cycle 활동성 signal)

```
pre-a  : 13 20 16 14 15    (안정)
s1     : 29 12 17 17 13    (안정)
s2     : 29  9 10  5  6    (감소)
s3     : 29 17  4  0  0    (c4/c5 target 0 → cycle skip)
s4     : 29 17 10  8  2    (유지)
```

### 2.4 wall_clock (s) c4/c5

- s3: **1s / 2s** (완전 no-op)
- s4: 109s / 48s (slow 하지만 정상 cycle)

---

## 3. 축 역할 분류

| 축 | 분류 | 증거 |
|---|---|---|
| **S1** | **무해** | KU c5=88 건강 성장, GU total=79, c3+ 계속 성장 (c4 adj_gen=15) |
| **S2** | **Primary Introducer** | c1 KU 폭증 (+59 vs s1 +33) → GU 양산 급감 (79→49, **−30**) → c3+ 정지 패턴 **최초 도입** |
| **S3** | **Secondary Aggravator** | S2 억제 위에 rule engine 추가 → GU 39 (s2 −10), GU_open c3+ zero → target_count 0 → c4/c5 완전 no-op (1-2s) |
| **S4** | **Mitigator** | deficit_score 로 GU 양산 부분 회복 (39→46) → cycle skip 방지. 원인 아님 |

---

## 4. S2 내부 의심 Subtask

### 4.1 S2 src/ diff 요약 (4e5988c → f3a0be0)

```
src/nodes/collect.py          |   6 lines
src/nodes/critique.py         | 103 lines
src/nodes/entity_discovery.py |  42 lines
src/nodes/integrate.py        |  98 lines
src/nodes/plan.py             | 103 lines
src/state.py                  |  16 lines
src/utils/metrics.py          |  48 lines
```

### 4.2 Subtask별 기능

- **S2-T1**: `integration_result_dist` state 승격 → plan/critique 제어 입력화
  - critique: `conv_rate < 0.3` → `integration_bottleneck` 처방
  - plan: `conv_rate < 0.3` → `reason_code: integration:low_conversion`
- **S2-T2**: `ku_stagnation_signals` state 추가 + 3종 trigger
  - T1: `added_ratio < 0.3` 최근 3c 평균 → `ku_stagnation:added_low`
  - T2: `conflict_hold` 증가 추세 → `ku_stagnation:conflict_rising`
  - T3: 최근 3c `condition_split = 0` → `ku_stagnation:no_condition_split`
- **S2-T4 α+β**:
  - α: stagnation 활성 시 plan 쿼리 재작성 (`new X options 2026`, `best X alternatives Y`)
  - β: `added_low` 발동 시 `aggressive_mode_remaining = 3` (3 cycles)
- **S2-T5~T8 (`integrate.py`, `_detect_conflict`)**: `condition_split` 강화
  - T5: parse 조건어
  - T6: **값 구조 차이** (range vs scalar vs set) → `condition_split`
  - T7: skeleton `condition_axes` 정의된 field → **값 차이 시 강제 `condition_split`**
  - T8: **axis_tags 차이** → `condition_split`

### 4.3 Primary Subtask 유력 후보: **S2-T5~T8 (condition_split 확장)**

**근거**:
1. **c1 KU +59 폭증** 이 condition_split 폭증으로 직접 설명됨
   - 기존 `conflict/update` 로 처리됐을 claim 이 **강제 `condition_split` 으로 재분류**
   - 1 KU 가 될 것이 여러 KU 로 **분할** → KU total 급증
2. **GU 양산 동반 급감 (79→49)** 도 같은 메커니즘으로 설명됨
   - condition_split 된 KU 는 원래 GU 의 `source_gu_id` 로 완전 매칭 안 됨
   - → GU `resolved` 못 하고, 동시에 condition 이 분리된 KU 는 **새 GU 를 유발하지도 않음**
3. **c3+ 고착 signal (adj_gen=0, stagnation trigger)** 은 이후 S2-T2 + S2-T4 β 가 받아서 *증상* 으로 surface 시키지만, **주원인은 T5~T8 이 만든 GU/KU 불균형**
4. S2-T1 `integration:low_conversion` reason_code 는 flag 만 부여, target 생성은 억제 안 함 → 직접 원인 아님
5. S2-T4 β aggressive query 재작성은 3c 제한 + entity_discovery 로 흘러감 → c3+ 정지의 *주원인* 아님 (증상 증폭 후 회복 기전)

### 4.4 Secondary 의심: S2-T2 + S2-T4 β

- `added_low` trigger 가 자주 발동되면 β mode 가 지속적으로 query 를 일반화 (`new X options`, `best X alternatives`)
- 일반화된 query 는 specific entity field 매칭에 불리 → collect yield 저하 → KU 재증가 못 함 → 악순환

### 4.5 왜 S3 가 더 심해졌는가 (Aggravator 메커니즘)

- S3 adjacent rule engine (`field_adjacency` + `conflict blocklist` + `yield tracker`) 는 GU 양산을 **추가로 억제**
- S2 가 만든 GU 부족 상태 + S3 의 blocklist/yield 차단 → GU pool 이 c3 에 완전 0
- target_count = 0 → cycle skip (1-2s no-op)

### 4.6 왜 S4 가 회복시켰는가 (Mitigator 메커니즘)

- S4-T1: balance-* virtual entity 제거 → 무의미 GU 제거되지만, **real entity 발굴 여지 확보**
- S4-T2: deficit_score 로 **category 불균형 기반 GU 생성** → pool 이 고갈 전 새 GU 주입
- 결과: s3 의 c4/c5 no-op 이 s4 에서 slow but continuous cycle 로 복원

---

## 5. Primary Introducer 판정

**S2 (condition_split 확장 + ku_stagnation + β aggressive)** 가 c3+ 고착 Primary Introducer.

**내부 primary subtask 유력 후보**: **S2-T5~T8 (condition_split 강화)**. 검증 방법:
- S2-T4 직후 commit (`87d7603`, T5~T8 이전) 을 추가 worktree 로 체크아웃 → 5c trial → c1 KU 폭증 재현 여부로 확정 (추가 ~$0.40 필요, Option 2 수준)

---

## 6. 다음 Action 선택지

**A. S2-T5~T8 코드 내 세부 수정 (API 비용 0)**
- `integrate.py::_detect_conflict` 의 T6/T7/T8 rule 을 **opt-out 토글** 로 wiring
- `t6_struct_split`, `t7_axes_forced_split`, `t8_axis_tags_split` 개별 on/off
- 단위 smoke (1c) 로 KU 폭증이 어느 rule 에서 오는지 narrowing
- 확정되면 해당 rule 의 적용 **보수화** (예: value 길이 임계, evidence count 하한)

**B. 추가 ablation trial — S2 내부 분해 (API 비용 ~$0.40)**
- `87d7603` (S2-T4 직후, T5~T8 직전) 을 6번째 worktree 로 체크아웃 → 5c trial
- c1 폭증 유무로 T5~T8 vs T1~T4 기여도 확정
- 확정 데이터 위에서 A 진행

**권장**: **A 먼저**. 코드 분석으로 narrowing 후 필요하면 B. Option A 가 동일 비용 0 으로 T6/T7/T8 separable isolation 제공.

---

## 7. Appendix

### 7.1 Trial 실행 로그 핵심

- Tavily 433 rate limit: 첫 s3 run (22:38) — 재실행으로 해결
- OpenAI 502 Bad Gateway: s4 c4 (23:16) — 자동 복구, 영향 없음
- Gate: 5개 trial 모두 5c 기준 FAIL 정상 (15c 기준 gate)
- VP1 expansion_variability: s2 만 FAIL (3/5), pre-a/s1/s3/s4 PASS

### 7.2 Reference

- Plan: `C:/Users/User/.claude/plans/your-solution-is-too-glowing-dijkstra.md`
- 폐기된 V-T10 매트릭스: `v4-hypothesis-matrix.md`
- V3 ablation 원본: `v3-ablation-design.md`, `v3-isolation-report.md`
- Worktrees (cleanup 완료): `_evolver-worktrees/{pre-a,s1,s2,s3,s4}` 모두 제거, main 1개만
- Bench: `bench/silver/japan-travel/p7-seq-{pre-a,s1,s2,s3,s4}/`

### 7.3 Decisions

- **D-194 (신규)**: Primary Introducer = **S2** 확정. Secondary Aggravator = S3. Mitigator = S4. 기준 = 5-trial Sequential Ablation (5c each) KU/GU/target/adj_gen delta
- **D-195 (신규)**: S2 내부 primary subtask 유력 후보 = **S2-T5~T8 (condition_split 확장)**. 확정은 Action A (코드 토글) 또는 B (추가 trial)
- **D-196 (신규)**: S1 adj_gen oscillation 원인 = 1단계 adj chain 억제 + S1 sort/FIFO 의 A:adj batch clustering. §8 상세
- **D-192 (이전)**: V-T10 가설 매트릭스 접근 폐기. Sequential Ablation 채택

---

## 8. Appendix B — S1 adj_gen Oscillation 분석

### 8.1 증상

Pre-a (all cycles `normal` mode) 는 adj_gen 이 consistent (6, 9, 8, 7, 4). S1 (c2~c5 `jump` mode) 은 oscillation (6, 15, **1**, 15, **0**). c3/c5 에 GU generation plunge.

```
           | c1 | c2 | c3 | c4 | c5
-------------------------------------
pre-a mode |normal normal normal normal normal
pre-a adj  |  6 |  9 |  8 |  7 |  4   ← consistent

s1 mode    |normal| jump | jump | jump | jump
s1 adj     |  6 | 15 |  1 | 15 |  0   ← oscillation
s1 ΔGU_tot |+45 |+17 | +2 |+15 | +0
```

### 8.2 증거 — Resolved GU Trigger 분포 (state-snapshots 에서 파싱)

```
cycle | resolved 누적 delta by trigger      | adj_gen
------|------------------------------------|--------
c1    | ?: +20                             |   6
c2    | E:cat_balance: +8                  |  15
c3    | ?: +0, E:cat: +1, A:adj: +9        |   1  ← plunge
c4    | ?: +4, E:cat: +4, A:adj: +7        |  15
c5    | ?: +0, E:cat: +0, A:adj: +11       |   0  ← plunge
```

- `?` = seed GU (skeleton baseline)
- `E:cat_balance` = category_balance trigger 로 생성된 GU
- `A:adjacent_gap` = adjacency rule 로 생성된 GU

### 8.3 메커니즘

**두 factor 의 상호작용**:

1. **1단계 adj chain 억제** (설계된 정책으로 추정)
   - `A:adjacent_gap` trigger 로 생성된 GU 가 resolved 돼도 **새 adjacent GU 를 생성하지 않음**
   - 2단계 chain 폭발 방지 목적
   - → resolved 가 A:adj type 위주면 adj_gen=0
2. **S1 이 도입한 trigger clustering**
   - S1-T1~T3: utility/risk 정렬 제거 (open GU 전체 반환, cap 만 적용)
   - S1-T5: max_search_calls_per_cycle 에서 초과 target → defer
   - S1-T8: 다음 cycle 에서 **prev_deferred 선-FIFO**
   - 결과: 같은 trigger 의 GU batch 가 특정 cycle 에 clustering

**Pre-a vs S1**:
- Pre-a (sorted utility/risk): 매 cycle 에 `?` / `E:cat` / `A:adj` 가 골고루 resolved → adj source 항상 존재 → adj_gen consistent
- S1 (unsorted + FIFO): A:adj batch 가 c3/c5 에 clustering → adj source 고갈 → adj_gen plunge

### 8.4 KU 성장 영향

- c3, c5 모두 `resolved_count = 10, 11` 정상 → KU 는 +10 씩 꾸준히 증가
- adj_gen=0 은 즉시 KU 타격 **아님** — resolved 된 기존 GU 에서 KU 는 정상 생성
- **하지만 open GU pool 보충은 감소** (새 GU 를 거의 안 만드는 cycle)
- S1 단독에선 open GU 충분 → 문제 잠복

### 8.5 S2/S3 와의 결합 위험

S2 는 condition_split 강제로 GU 양산 자체를 억제. 여기에 S1 의 batch clustering 이 겹치면:
- GU 양산이 이미 저조한 상태 → 특정 cycle 에 adj_gen=0 plunge 시 **pool 이 즉시 고갈 가능**
- S3 c3 의 `GU_open=0` collapse 가 이 결합 메커니즘의 결과일 가능성 (확인 필요: S3 state-snapshots 의 trigger 분포 검증)

### 8.6 완화 정책 옵션

후보 접근 4개 (상호 배타 아님):

1. **Trigger 다양성 최소 보장**: plan 에서 cycle 당 `?/E:cat/A:adj` 각 trigger 를 최소 N 개씩 포함하도록 보정. sort 제거 철학과 일부 충돌
2. **2단계 adj chain 조건부 허용**: 특정 category 에 한해 A:adj resolved → adj 생성 허용. 폭발 방지 위해 depth cap 추가
3. **FIFO + LIFO 혼합**: prev_deferred 의 일부만 FIFO, 나머지 slot 은 최신 신규 우선. batch clustering 완화
4. **critique 처방 추가**: adj_gen=0 감지 시 `stagnation:no_adj_source` 처방 → 다음 cycle 에 `?`/`E:cat` GU 우선 선정

**권장**: D-196 은 관찰 사항으로 기록. 즉시 조치는 필요 없음. S2 primary subtask 확정 (Action A/B) 후 S2 해결과 함께 재평가 권장. Option 4 가 부작용이 가장 적어서 우선 고려
