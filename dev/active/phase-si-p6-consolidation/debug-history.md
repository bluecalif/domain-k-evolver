# Silver P6: Consolidation & Knowledge DB Release — Debug History
> Phase: phase-si-p6-consolidation
> Started: 2026-04-18

디버깅 이력은 Phase 진행 중 발생한 버그/결정/교훈을 기록한다.

## 형식

```
### [날짜] 제목

**증상**: 
**원인**: 
**수정**: 
**교훈**: 
**commit**: 
```

---

<!-- P6 진행 중 이슈 발생 시 여기에 추가 -->

---

### 2026-04-18 A1 후속 조사: Wildcard Entity 동결 원인 분석 (가설 단계)

**증상**: stage-e-on c10-c13 4사이클 완전 동결 (open=20 불변). `adjacent_gap` GU 신규 생성 0.

**코드 추적 결과 (`integrate.py:524-533`)**:
- `adjacent_gap` 생성은 `plan.py`가 아닌 `integrate.py`의 `_generate_dynamic_gus`에서 발생
- 생성 조건: `for claim in claims` 루프 내부 → **claims=0이면 호출 자체 불가**
- dynamic_cap = `min(max(4, ceil(open_count*0.2)), 12)` = open=20 → cap=4

**Wildcard Entity_Key 기원 (`seed.py`)**:
- Case A (정상): `WILDCARD_FIELDS = {"tips", "etiquette"}` → `{domain}:{cat}:*` GU 의도적 생성
- Case B (버그 후보): `ENTITY_SPECIFIC_FIELDS` (`price`, `hours`, `how_to_use`, `where_to_buy` 등) 인데 `known_entities == []`이면 wildcard fallback (`seed.py:293-306`)

**plan.py:268의 쿼리 생성 문제**:
```python
slug = entity_key.split(":")[-1]  # "japan-travel:connectivity:*" → "*"
queries = ["* how_to_use", "* how_to_use 2026"]  # 의미 없는 쿼리
```
Tavily API로 `"* how_to_use"` 전송 → 의미 없는 결과 → claims=0 가능성.

**stage-e-off 차이 가설**:
- stage-e-on: External Anchor(universe_probe) 활성화 → 새 attraction entity GU flood (Shirakawa, Himeji 등) → 이 GU들도 collect로 해소 어려움 → wildcard 6개 + hard-concrete GU 14개 = open 20 고정
- stage-e-off: External Anchor 비활성화 → 일반 concrete GU만 존재 → collect가 일부 매 cycle 해소 → 성장 지속

**교훈**: 코드 읽기만으로는 실제 claims=0인지, search yield가 얼마인지 확인 불가. **실 데이터 없이 fix 구현 위험**.

**결정 (D-162)**: 진단 로깅 추가 → 실 bench 재실행 → 데이터로 root cause 확정 후 fix 구현.

**다음 스텝**: A1-D1 (진단 로깅) → A1-D2 (분석 스크립트) → A1-D3 (실 bench + 확정)


---

### 2026-04-18 A1-D3: 15c Full Bench Root Cause 확정

**데이터**: `p6-diag-full-15c` (stage-e-on, 15 cycles, `--external-anchor`)

**query-patterns 결과**:
| type | count | avg_yield | zero_yield |
|------|-------|-----------|------------|
| wildcard | 46 | 5.54 | 29/46 (63%) |
| concrete | 93 | 12.1 | 18/93 (19%) |

cycle별: wildcard c2~c4, c9, c11~c15 avg_yield = **0.0** (반복)

**trace-frozen (3c 이상 고착)**:
- `dining:*/hours` (8c, yield=0.0), `payment:*/tips` (3c, yield=0.0) — wildcard, 완전 동결
- `accommodation:*/tips` (7c, yield=1.9), `attraction:*/hours` (6c, yield=2.1) — wildcard, 불완전 해소

**compare-trials 핵심**:
- p6-diag-full-15c frozen wildcard=29, **wildcard_zero_yield=29 (100%)**
- 고착된 wildcard GU 전원 zero_yield → slug 버그 단독 원인 확정

**Root Cause 확정 (D-163, 초기)**:
```python
# src/nodes/plan.py:268
slug = entity_key.split(":")[-1]  # "japan-travel:dining:*" → "*"
# 생성 쿼리: "* hours", "* 2026" → Tavily 무의미한 쿼리 → yield=0
# → claims=0 → resolve 불가 → pool 동결
```

**Fix 방향 (A2)**:
- wildcard entity (`"*"` slug)는 category를 쿼리 주어로 사용
- 예: `entity_key = "japan-travel:dining:*"` → slug = `"dining"` + field = "hours" → `"dining hours japan"`
- 또는 wildcard GU를 Plan 단계에서 category-level query로 특수 처리

**commit**: TBD (A2 구현 시)

---

### 2026-04-18 D-163 재검토: Local view → Extensive view

**재검토 계기**: 사용자 지적 "wildcard 버그만 보고 concrete 는 안 봤다. c11-15 remaining 이 모두 wildcard 냐? 모든 GU 데이터로 보라". "zero yield = no answer. separate no answer from no integration".

**데이터 재분석 결과** (c15 remaining 18 open GU, `gu_trace.jsonl` + `gap-map.json` 전수):

| 카테고리 | 개수 | 비율 |
|---|---:|---:|
| NO-ANSWER (search_yield=0) | 5 | 28% |
|  └ wildcard (slug="*") | 3 | 17% |
|  └ concrete (부자연 query) | 2 | 11% |
| NO-INTEGRATION (yield>0, unresolved) | 2 | 11% |
| **NO-SELECTION (Plan 미선정)** | **11** | **61%** |

**D-163 수정된 결론**:
- wildcard slug 버그는 **NO-ANSWER 의 3/5** = 전체 18 중 **17% 부분 원인**일 뿐
- **최대 미해결 버킷은 NO-SELECTION (61%)** — (medium, convenience) priority 11 GU 가 `plan.py:158-165` 고정 sort 탓에 14 cycle 동안 한 번도 target 으로 선정되지 않음
- NO-INTEGRATION 2건 (GU-0033 visit-japan-web/price, GU-0090 attraction:Fukuoka/hours) 은 adjacent_gap generator 의 malformed field 생성 문제 — slug 버그와 무관

**A2 Scope 재설계** (3-pronged):
- A2a (NO-ANSWER, 5 GU 28%): plan.py query builder — wildcard slug 우회 + field/slug naturalization
- A2b (NO-SELECTION, 11 GU 61%): plan.py target_gaps 선택 로직 — aging penalty + deficit_boost 완화
- A2c (NO-INTEGRATION, 2 GU 11%): integrate.py `_generate_dynamic_gus` entity-type filter + `_detect_conflict` 오판 점검

**교훈**: **Root cause 분석 시 샘플 데이터(특정 유형) 만 본 뒤 "확정" 하지 말 것**. 반드시 전체 open/unresolved 데이터로 3 카테고리(search 성공/실패, integrate 성공/실패, Plan 선정/비선정) 매핑 후 bucket 별 비율을 확인.

**참조 문서**: `dev/active/phase-si-p6-consolidation/zero-yield-mapping.md`

**commit**: TBD

---

### 2026-04-18 D-163 최종 확정 + D-164/D-165 신규 (stage-e on/off 15c 비교)

**근거 데이터**: `bench/silver/japan-travel/p6-diag-off-15c/` (15c, --no-external-anchor) vs `p6-diag-full-15c/` (15c, --external-anchor)

**3-카테고리 비교 (c15 open GU)**:
| 카테고리 | on | off | 함의 |
|----------|----:|----:|------|
| open total | 18 | 25 | off 가 더 많음 |
| NO-ANSWER | 5 (28%) | **0 (0%)** | wildcard 버그 안 드러남 |
| NO-INTEGRATION | 2 (11%) | 2 (8%) | 같은 패턴 (city/hours, free/price) |
| NO-SELECTION | 11 (61%) | **23 (92%)** | dominant root cause |

**가설 검증**:
- H1 (NO-SEL = External Anchor 산물): **FAIL** — off 에서 NO-SEL 23 으로 오히려 증가. trigger 22/23 = adjacent_gap (External Anchor 무관)
- H2 ((medium, convenience) sort tail 문제 stage-e 무관): **PASS** — on/off 양쪽 NO-SEL 모두 (medium, convenience)
- H3 (wildcard 버그 off 에서도 발생): **FAIL** — wildcard GU 들이 NO-SELECTION 버킷으로 안주, query 도 안 됨

**D-163 최종 확정** (이전: "wildcard slug = root cause"):
- wildcard slug 버그는 **부분 원인** (on 28%, off 0%, 평균 ~14%)
- dominant root cause 는 **plan.py priority sort + adjacent_gap (medium, convenience) 양산의 상호작용** (NO-SEL on 61%, off 92%)
- Stage-E (External Anchor) 와 무관한 구조적 결함

**D-164 (신규) — NO-SELECTION dominant root cause**:
- `plan.py:158-161` `_select_targets` 의 고정 sort `_UTILITY_ORDER × _RISK_ORDER` 가 (medium, convenience) GU 를 list tail 에 영구 고정
- `_generate_dynamic_gus` (adjacent_gap) 가 cycle 마다 (medium, convenience) GU 양산 (off c1-c10 누적 ~66건) → tail 적체 가속
- 후반 cycle 에서 mode.py exploit_budget 수축 (off c12+ target=3 고착) 으로 더욱 악화 — 정확한 코드 경로는 후속 조사 필요

**D-165 (신규) — adjacent_gap entity-type 무관 field 양산**:
- city entity + hours/price → semantically malformed (도시는 단일 입장료/시간 없음)
- free service + price → malformed
- `_generate_dynamic_gus` 에 entity-type aware filter 필수
- on/off 양쪽에서 attraction:City/hours 패턴 동일 발현 (on: GU-0090 Fukuoka, off: GU-0107 Shirakawa, GU-0109 Choshi_City)

**A2 Scope 최종 확정** (우선순위 조정 — A2b 최우선):
1. A2b (NO-SELECTION 해소): aging penalty + deficit_boost 임계 완화 + exploit_budget 수축 조사
2. A2c (NO-INTEGRATION + adjacent_gap filter): entity-type aware filter + skeleton_mismatch 마킹
3. A2a (NO-ANSWER query 개선): wildcard 우회 + field naturalization (보조)

**참조 문서**: `dev/active/phase-si-p6-consolidation/stage-e-compare-analysis.md`

**교훈**: 단일 trial 데이터로 root cause 확정 금지. 비교 trial (control) 로 가설별 PASS/FAIL 검증해야 dominant cause 식별 가능. wildcard 버그는 "Plan 이 wildcard 를 우연히 선택한 cycle" 에서만 표출 — 하나의 trial 만 보면 dominant 처럼 보였으나 off 비교에서 부분 원인 확정.

**commit**: TBD

---
<!-- analyze_saturation.py output -->

# KU Saturation 진단 리포트 (P6-A1)

> 분석 대상: stage-e-on, stage-e-off, p2-smart-remodel-trial


## stage-e-on

### 1. KU 성장률 (window별)

| window | ku_start | ku_end | delta | rate/cycle |
| ------ | -------- | ------ | ----- | ---------- |
| c1-5   | 35       | 73     | 38    | 7.6        |
| c6-10  | 82       | 104    | 22    | 4.4        |
| c11-15 | 104      | 106    | 2     | 0.4        |



### 2. gap_map 동결 분석

**동결 사이클 수**: 3 / 15

| cycle | open | resolved | delta_open | note     |
| ----- | ---- | -------- | ---------- | -------- |
| 1     | 38   | 12       | -          |          |
| 2     | 54   | 23       | 16         |          |
| 3     | 52   | 32       | -2         |          |
| 4     | 39   | 45       | -13        |          |
| 5     | 33   | 51       | -6         |          |
| 6     | 24   | 60       | -9         |          |
| 7     | 26   | 68       | 2          |          |
| 8     | 24   | 72       | -2         |          |
| 9     | 21   | 75       | -3         |          |
| 10    | 20   | 76       | -1         |          |
| 11    | 20   | 76       | 0          | 🔴 FROZEN |
| 12    | 20   | 76       | 0          | 🔴 FROZEN |
| 13    | 20   | 76       | 0          | 🔴 FROZEN |
| 14    | 19   | 77       | -1         |          |
| 15    | 18   | 78       | -1         |          |



### 3. GU 해소율 + LLM 호출 추이

| cycle | gu_open | gu_resolved | gap_res | llm_calls | search_calls |
| ----- | ------- | ----------- | ------- | --------- | ------------ |
| 1     | 38      | 12          | 0.343   | 0         | 0            |
| 2     | 54      | 23          | 0.315   | 0         | 0            |
| 3     | 52      | 32          | 0.381   | 0         | 0            |
| 4     | 39      | 45          | 0.536   | 0         | 0            |
| 5     | 33      | 51          | 0.607   | 0         | 0            |
| 6     | 24      | 60          | 0.714   | 0         | 0            |
| 7     | 26      | 68          | 0.723   | 0         | 0            |
| 8     | 24      | 72          | 0.75    | 0         | 0            |
| 9     | 21      | 75          | 0.781   | 0         | 0            |
| 10    | 20      | 76          | 0.792   | 0         | 0            |
| 11    | 20      | 76          | 0.792   | 0         | 0            |
| 12    | 20      | 76          | 0.792   | 0         | 0            |
| 13    | 20      | 76          | 0.792   | 0         | 0            |
| 14    | 19      | 77          | 0.802   | 0         | 0            |
| 15    | 18      | 78          | 0.812   | 0         | 0            |



### 4. KU Gini 추이

| cycle | gini   | total_ku | num_categories |
| ----- | ------ | -------- | -------------- |
| 1     | 0.425  | 35       | 8              |
| 2     | 0.2391 | 46       | 8              |
| 3     | 0.1667 | 54       | 8              |
| 4     | 0.1399 | 67       | 8              |
| 5     | 0.1592 | 73       | 8              |
| 6     | 0.1646 | 82       | 8              |
| 7     | 0.2152 | 97       | 8              |
| 8     | 0.21   | 100      | 8              |
| 9     | 0.2294 | 103      | 8              |
| 10    | 0.2356 | 104      | 8              |
| 11    | 0.2356 | 104      | 8              |
| 12    | 0.2356 | 104      | 8              |
| 13    | 0.2356 | 104      | 8              |
| 14    | 0.2417 | 105      | 8              |
| 15    | 0.2406 | 106      | 8              |



### 5. Entity Dedup 비율

| cycle | unique_entities | multi_ku | dedup_ratio |
| ----- | --------------- | -------- | ----------- |
| 1     | 24              | 9        | 0.375       |
| 2     | 35              | 9        | 0.257       |
| 3     | 39              | 13       | 0.333       |
| 4     | 39              | 18       | 0.462       |
| 5     | 39              | 20       | 0.513       |
| 6     | 39              | 22       | 0.564       |
| 7     | 47              | 26       | 0.553       |
| 8     | 48              | 27       | 0.562       |
| 9     | 48              | 30       | 0.625       |
| 10    | 48              | 31       | 0.646       |
| 11    | 48              | 31       | 0.646       |
| 12    | 48              | 31       | 0.646       |
| 13    | 48              | 31       | 0.646       |
| 14    | 48              | 32       | 0.667       |
| 15    | 48              | 33       | 0.688       |



## stage-e-off

### 1. KU 성장률 (window별)

| window | ku_start | ku_end | delta | rate/cycle |
| ------ | -------- | ------ | ----- | ---------- |
| c1-5   | 27       | 71     | 44    | 8.8        |
| c6-10  | 75       | 97     | 22    | 4.4        |
| c11-15 | 100      | 116    | 16    | 3.2        |



### 2. gap_map 동결 분석

**동결 사이클 수**: 3 / 15

| cycle | open | resolved | delta_open | note     |
| ----- | ---- | -------- | ---------- | -------- |
| 1     | 40   | 12       | -          |          |
| 2     | 57   | 24       | 17         |          |
| 3     | 57   | 34       | 0          | 🔴 FROZEN |
| 4     | 43   | 48       | -14        |          |
| 5     | 33   | 58       | -10        |          |
| 6     | 29   | 62       | -4         |          |
| 7     | 29   | 71       | 0          | 🔴 FROZEN |
| 8     | 27   | 75       | -2         |          |
| 9     | 27   | 75       | 0          | 🔴 FROZEN |
| 10    | 26   | 78       | -1         |          |
| 11    | 27   | 81       | 1          |          |
| 12    | 28   | 85       | 1          |          |
| 13    | 27   | 88       | -1         |          |
| 14    | 28   | 93       | 1          |          |
| 15    | 26   | 97       | -2         |          |



### 3. GU 해소율 + LLM 호출 추이

| cycle | gu_open | gu_resolved | gap_res | llm_calls | search_calls |
| ----- | ------- | ----------- | ------- | --------- | ------------ |
| 1     | 40      | 12          | 0.343   | 0         | 0            |
| 2     | 57      | 24          | 0.316   | 0         | 0            |
| 3     | 57      | 34          | 0.374   | 0         | 0            |
| 4     | 43      | 48          | 0.527   | 0         | 0            |
| 5     | 33      | 58          | 0.637   | 0         | 0            |
| 6     | 29      | 62          | 0.681   | 0         | 0            |
| 7     | 29      | 71          | 0.71    | 0         | 0            |
| 8     | 27      | 75          | 0.735   | 0         | 0            |
| 9     | 27      | 75          | 0.735   | 0         | 0            |
| 10    | 26      | 78          | 0.75    | 0         | 0            |
| 11    | 27      | 81          | 0.75    | 0         | 0            |
| 12    | 28      | 85          | 0.752   | 0         | 0            |
| 13    | 27      | 88          | 0.765   | 0         | 0            |
| 14    | 28      | 93          | 0.769   | 0         | 0            |
| 15    | 26      | 97          | 0.789   | 0         | 0            |



### 4. KU Gini 추이

| cycle | gini   | total_ku | num_categories |
| ----- | ------ | -------- | -------------- |
| 1     | 0.3657 | 27       | 8              |
| 2     | 0.1891 | 39       | 8              |
| 3     | 0.1144 | 47       | 8              |
| 4     | 0.125  | 61       | 8              |
| 5     | 0.1567 | 71       | 8              |
| 6     | 0.1383 | 75       | 8              |
| 7     | 0.1778 | 90       | 8              |
| 8     | 0.1915 | 94       | 8              |
| 9     | 0.1915 | 94       | 8              |
| 10    | 0.2126 | 97       | 8              |
| 11    | 0.22   | 100      | 8              |
| 12    | 0.2284 | 104      | 8              |
| 13    | 0.2371 | 107      | 8              |
| 14    | 0.2433 | 112      | 8              |
| 15    | 0.2435 | 116      | 8              |



### 5. Entity Dedup 비율

| cycle | unique_entities | multi_ku | dedup_ratio |
| ----- | --------------- | -------- | ----------- |
| 1     | 16              | 9        | 0.562       |
| 2     | 28              | 9        | 0.321       |
| 3     | 33              | 12       | 0.364       |
| 4     | 33              | 19       | 0.576       |
| 5     | 33              | 22       | 0.667       |
| 6     | 33              | 23       | 0.697       |
| 7     | 41              | 26       | 0.634       |
| 8     | 41              | 29       | 0.707       |
| 9     | 41              | 29       | 0.707       |
| 10    | 41              | 31       | 0.756       |
| 11    | 42              | 33       | 0.786       |
| 12    | 43              | 35       | 0.814       |
| 13    | 43              | 36       | 0.837       |
| 14    | 43              | 36       | 0.837       |
| 15    | 43              | 37       | 0.86        |



## p2-smart-remodel-trial

### 1. KU 성장률 (window별)

| window | ku_start | ku_end | delta | rate/cycle |
| ------ | -------- | ------ | ----- | ---------- |
| c1-5   | 25       | 69     | 44    | 8.8        |
| c6-10  | 81       | 126    | 45    | 9.0        |
| c11-15 | 131      | 152    | 21    | 4.2        |



### 2. gap_map 동결 분석

**동결 사이클 수**: 1 / 15

| cycle | open | resolved | delta_open | note     |
| ----- | ---- | -------- | ---------- | -------- |
| 1     | 42   | 12       | -          |          |
| 2     | 62   | 21       | 20         |          |
| 3     | 69   | 34       | 7          |          |
| 4     | 58   | 45       | -11        |          |
| 5     | 46   | 57       | -12        |          |
| 6     | 34   | 69       | -12        |          |
| 7     | 29   | 74       | -5         |          |
| 8     | 38   | 83       | 9          |          |
| 9     | 37   | 88       | -1         |          |
| 10    | 37   | 93       | 0          | 🔴 FROZEN |
| 11    | 35   | 98       | -2         |          |
| 12    | 31   | 103      | -4         |          |
| 13    | 27   | 107      | -4         |          |
| 14    | 23   | 111      | -4         |          |
| 15    | 17   | 119      | -6         |          |



### 3. GU 해소율 + LLM 호출 추이

| cycle | gu_open | gu_resolved | gap_res | llm_calls | search_calls |
| ----- | ------- | ----------- | ------- | --------- | ------------ |
| 1     | 42      | 12          | 0.343   | 0         | 0            |
| 2     | 62      | 21          | 0.284   | 0         | 0            |
| 3     | 69      | 34          | 0.33    | 0         | 0            |
| 4     | 58      | 45          | 0.437   | 0         | 0            |
| 5     | 46      | 57          | 0.553   | 0         | 0            |
| 6     | 34      | 69          | 0.67    | 0         | 0            |
| 7     | 29      | 74          | 0.718   | 0         | 0            |
| 8     | 38      | 83          | 0.686   | 0         | 0            |
| 9     | 37      | 88          | 0.704   | 0         | 0            |
| 10    | 37      | 93          | 0.715   | 0         | 0            |
| 11    | 35      | 98          | 0.737   | 0         | 0            |
| 12    | 31      | 103         | 0.769   | 0         | 0            |
| 13    | 27      | 107         | 0.799   | 0         | 0            |
| 14    | 23      | 111         | 0.828   | 0         | 0            |
| 15    | 17      | 119         | 0.875   | 0         | 0            |



### 4. KU Gini 추이

| cycle | gini   | total_ku | num_categories |
| ----- | ------ | -------- | -------------- |
| 1     | 0.415  | 25       | 8              |
| 2     | 0.2941 | 34       | 8              |
| 3     | 0.1033 | 46       | 8              |
| 4     | 0.1031 | 57       | 8              |
| 5     | 0.0996 | 69       | 8              |
| 6     | 0.1713 | 81       | 8              |
| 7     | 0.2006 | 86       | 8              |
| 8     | 0.3233 | 116      | 8              |
| 9     | 0.3337 | 121      | 8              |
| 10    | 0.3552 | 126      | 8              |
| 11    | 0.375  | 131      | 8              |
| 12    | 0.3934 | 136      | 8              |
| 13    | 0.4018 | 140      | 8              |
| 14    | 0.4149 | 144      | 8              |
| 15    | 0.4276 | 152      | 8              |



### 5. Entity Dedup 비율

| cycle | unique_entities | multi_ku | dedup_ratio |
| ----- | --------------- | -------- | ----------- |
| 1     | 14              | 9        | 0.643       |
| 2     | 23              | 9        | 0.391       |
| 3     | 33              | 11       | 0.333       |
| 4     | 33              | 20       | 0.606       |
| 5     | 33              | 25       | 0.758       |
| 6     | 33              | 27       | 0.818       |
| 7     | 33              | 27       | 0.818       |
| 8     | 55              | 29       | 0.527       |
| 9     | 55              | 32       | 0.582       |
| 10    | 43              | 35       | 0.814       |
| 11    | 47              | 36       | 0.766       |
| 12    | 49              | 38       | 0.776       |
| 13    | 49              | 38       | 0.776       |
| 14    | 51              | 38       | 0.745       |
| 15    | 52              | 43       | 0.827       |



---

## 비교 요약

| trial                  | final_ku_active | c11-15_rate/cyc | frozen_cycles | final_open | final_resolved |
| ---------------------- | --------------- | --------------- | ------------- | ---------- | -------------- |
| stage-e-on             | 106             | 0.4             | 3             | 18         | 78             |
| stage-e-off            | 116             | 3.2             | 3             | 26         | 97             |
| p2-smart-remodel-trial | 152             | 4.2             | 1             | 17         | 119            |



## 진단 결론

- **stage-e-on**: gap_map 완전 동결 3사이클 — core loop 마비 의심; c11-15 KU 성장률 0.4/cyc — 포화 진입

- **stage-e-off**: gap_map 완전 동결 3사이클 — core loop 마비 의심

- **p2-smart-remodel-trial**: 포화 징후 없음
