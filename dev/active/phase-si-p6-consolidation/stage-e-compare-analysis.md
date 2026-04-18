# Stage-E On vs Off — Strict Comparison & Hidden Root Cause

> 작성일: 2026-04-18
> Trials: `bench/silver/japan-travel/p6-diag-full-15c/` (stage-e-on) vs `bench/silver/japan-travel/p6-diag-off-15c/` (stage-e-off)
> 둘 다 15 cycles, 동일 seed, gpt-4.1-mini + Tavily
> 목적: D-163 재검토 (wildcard slug 부분원인) 확정 + 숨겨진 dominant root cause 정량 식별 → A2 scope 최종 확정

---

## 1. 상위 요약

| 지표 | stage-e-on | stage-e-off | 해석 |
|------|---------:|---------:|------|
| Active KU @ c15 | 106 | **116** | off 가 +10 KU 더 큼 |
| c11-15 KU 성장률/cycle | 0.4 | **3.2** | off 가 8배 빠름 (포화 아님) |
| Open GU @ c15 | 18 | 25 | off 가 더 많이 남음 |
| Resolved GU @ c15 | 78 | 97 | off 가 +19 더 많이 해소 |
| 동결 cycle 수 | 3 (c11-13) | 3 (c3, c7, c9) | on 만 후반 4 cycle 연속 동결 |
| dispute_queue @ c15 | 큼 | 큼 | (별도 조사 필요) |

**1줄 결론**: off 가 KU 성장/해소 모두 우수. on 은 c11-15 후반에 거의 완전 동결 (KU +2 in 5 cycles).

---

## 2. 3-카테고리 분포 비교 (c15 open GU)

| 카테고리 | stage-e-on | stage-e-off | 변화 |
|----------|---------:|---------:|------|
| open total | 18 | 25 | +7 |
| **NO-ANSWER** (yield=0) | 5 (28%) | **0 (0%)** | **wildcard slug 버그가 off 에서 안 드러남** |
| **NO-INTEGRATION** (yield>0, unresolved) | 2 (11%) | 2 (8%) | 같은 패턴 (city/hours, free service/price) |
| **NO-SELECTION** (Plan 미선정) | 11 (61%) | **23 (92%)** | off 에서 압도적 dominant |

**중대 발견**: off 에서 NO-ANSWER=0 인 이유는 wildcard GU 들이 애초에 NO-SELECTION 버킷으로 빠져 한 번도 query 되지 않아서지, slug 버그가 사라져서가 아님. 따라서 wildcard slug 버그는 stage-e-on 환경 + Plan 이 (medium, convenience) wildcard 를 우연히 골랐을 때만 표출.

---

## 3. 가설 검증

### H1: NO-SELECTION 은 External Anchor (universe_probe) 가 만든 신규 entity GU 산물 → External Anchor 끄면 해소
- **결과**: **FAIL**
- on NO-SEL = 11, off NO-SEL = **23 (오히려 2배 증가)**
- External Anchor 가 만든 attraction:Shirakawa 등은 off 에서도 attraction:Mt_Fuji / Himeji_Castle / Kitakami_Tenshochi_Park 등으로 다수 NO-SEL. trigger 통계는 22/23 = `A:adjacent_gap` (External Anchor 와 무관, integrate.py `_generate_dynamic_gus` 산물).
- **함의**: External Anchor 제거가 NO-SEL 을 해결하지 못함. 진짜 원인은 plan.py priority sort + adjacent_gap 양산의 상호작용.

### H2: (medium, convenience) sort tail 문제는 stage-e 무관한 구조적 결함
- **결과**: **PASS**
- off NO-SEL 23/23 = 모두 (medium, convenience). on NO-SEL 11/11 = 모두 (medium, convenience).
- plan.py `_select_targets` 의 `_UTILITY_ORDER × _RISK_ORDER` 고정 sort 가 stage-e 와 독립적으로 dominant root cause.

### H3: wildcard slug 버그는 off 에서도 NO-ANSWER 로 표출
- **결과**: **FAIL**
- off NO-ANSWER = 0. wildcard GU 5개 (transport:*/tips, connectivity:*/price, payment:*/price/how_to_use/acceptance) 모두 NO-SELECTION 버킷에 안주.
- **함의**: wildcard slug 버그는 "Plan 이 wildcard 를 우연히 선택한 cycle" 에서만 NO-ANSWER 로 표출 → 부분 원인 (28% in on, 0% in off, 평균 ~14%).

---

## 4. 숨겨진 Root Cause 확정

### D-164 (신규): NO-SELECTION 이 dominant root cause
- **근거**: off 에서 92% (23/25), on 에서 61% (11/18). Stage-E 변경과 독립적으로 압도적 비중.
- **메커니즘**: `plan.py:158-161`
  ```python
  open_gus.sort(key=lambda g: (
      _UTILITY_ORDER.get(g.get("expected_utility", "low"), 99),
      _RISK_ORDER.get(g.get("risk_level", "informational"), 99),
  ))
  exploit_targets = open_gus[:exploit_budget]
  ```
  (medium, convenience) = sort key (2, 3) → list tail 고정 → exploit_budget 안에 들어가지 않으면 영원히 unselected.
- **악화 요인**:
  1. integrate.py `_generate_dynamic_gus` (adjacent_gap) 가 cycle 마다 (medium, convenience) GU 양산 (off 에서 c1~c10 누적 6+21+16+0+0+0+1+13+1+8 = 66건). high/critical 처방 → list head 점유 → tail 의 (medium, convenience) 영원히 밀려남.
  2. mode.py exploit_budget 이 후반 cycle 에서 작아짐 (아래 §5).

### D-165 (신규): adjacent_gap generator 가 entity-type 무관 field 조합을 양산 → 두 가지 결함 동시 유발
- **결함 A (NO-INTEGRATION)**: city-type entity + hours, free service + price → semantically malformed → 영구 yield>0 unresolved.
  - on: GU-0033 visit-japan-web/price, GU-0090 attraction:Fukuoka/hours
  - off: GU-0107 attraction:Shirakawa/hours, GU-0109 attraction:Choshi_City/hours (yields=[15]×6, [15]×2)
  - 패턴 일치: `attraction:City + hours` 가 두 trial 에서 모두 발현 → adjacent_gap 의 구조적 결함 확정
- **결함 B (NO-SELECTION 양산)**: cycle 마다 (medium, convenience) 분량 양산 → priority tail 적체 가속화 → §4 D-164 의 악화 요인.
- **off 의 adjacent_gap 누적**: c1=6, c2=21, c3=16, c8=13, c10=8 → 총 ~66건 생성, 그 중 23건이 끝까지 NO-SELECTION 으로 잔존.

### D-163 최종 확정 (재검토 종료)
- 이전 (4-18 초기): "wildcard slug 버그 = root cause"
- 최종: "wildcard slug 버그는 부분 원인 (on 28%, off 0%). dominant root cause 는 plan.py priority sort + adjacent_gap (medium, convenience) 양산의 상호작용 (NO-SEL on 61%, off 92%). Stage-E 와 무관."

---

## 5. exploit_budget 수축 조사 (off c11-c15 target=3 미스터리)

### 데이터
| trial | c11 | c12 | c13 | c14 | c15 |
|-------|----:|----:|----:|----:|----:|
| on  target | 5 | 5 | 8 | 5 | 5 |
| off target | 5 | **3** | **3** | **3** | **3** |
| off open   | 25 | 25 | 25 | 25 | 25 |

### mode.py 계산
`mode == "jump"` & `open_count = 25`:
```python
target_count = max(10, ceil(25 * 0.5)) = max(10, 13) = 13
```
이론상 target=13 이어야 함. 실제 cycle_trace.target_count=3 → plan.py 단계에서 8 cycle 동안 13→3 으로 수축.

### 원인 추정 (미확정 — 후속 조사 필요)
- **A**: plan_node 가 `state["jump_explore_candidates"]` 가 비어 있고 (high/critical) open 후보가 모두 (medium, convenience) 으로 밀려나 explore_targets=0 + exploit_targets=3 (wildcard 제외 등 추가 필터 적용된 결과). 13 → 3 으로 8개를 잃는 명확한 코드 경로 미파악.
- **B**: audit_bias 가 yield_decline 누적으로 -0.15 까지 떨어지면 jump converging 단계 explore_ratio = 0.4 - 0.15 = 0.25 → explore=3, exploit=10. 그래도 target=13 이어야 정상.
- **C**: 별도 cap 로직 또는 LLM 응답 단계에서 sub-list 추려진 결과 (ll plan.py 중 LLM 호출 부분 검사 필요).

**결론**: target=3 고착의 정확한 코드 경로는 plan_node 내부 추가 디버깅 필요. P6-A2 단계에서 plan.py 전수 조사 권장.

---

## 6. NO-SELECTION 23건 (off) 전수 분류

| 카테고리 | wildcard | concrete | 합계 |
|----------|---------:|---------:|----:|
| transport | 1 (`*`/tips) | 4 (shinkansen×2, airport-transfer×2) | 5 |
| attraction | 0 | 5 (Miyazaki_City, Mt_Fuji, Nasu, Kitakami, Himeji_Castle) | 5 |
| regulation | 0 | 4 (emergency×2, visit-japan-web×2) | 4 |
| pass-ticket | 0 | 4 (jr-pass×1, suica×3) | 4 |
| payment | 3 (`*`/price/how_to_use/acceptance) | 1 (ic-card/how_to_use) | 4 |
| connectivity | 1 (`*`/price) | 0 | 1 |
| **합계** | **5 (22%)** | **18 (78%)** | **23** |

### Field 분포
| field | count | 의미 |
|-------|------:|------|
| price | 11 | 압도적 1위 — adjacent_gap 이 price 를 무차별 생성 |
| how_to_use | 4 | |
| tips | 2 | |
| hours | 2 | |
| acceptance/eligibility/policy/where_to_buy | 각 1 | |

### Trigger
- `A:adjacent_gap`: 22/23 (95.7%) — 거의 전부 adjacent_gap 산물
- `?` (trigger 누락): 1/23 (GU-0029 transport:*/tips — seed 단계 wildcard)

### 함의
- **price 11/23 (48%)** 가 NO-SEL 의 거의 절반 — adjacent_gap generator 의 price field 가 무차별 생성.
  - city entity (Miyazaki_City/Mt_Fuji/Nasu/Kitakami/Himeji_Castle) + price → 도시는 입장료 단일 값 없음 → semantically malformed
  - free service (visit-japan-web) + price → 무료 → malformed
- **city + hours 패턴 반복**: NO-INTEGRATION on/off 양쪽 모두 attraction:City/hours → adjacent_gap 의 entity-type aware filter 필수.

---

## 7. 다음 cycle 별 target/resolved 궤적 (참조)

| cycle | on target/resolved | off target/resolved | adj_gap on/off |
|------:|:------------------:|:------------------:|:--------------:|
| 1 | 13/11 | 14/12 | 6/6 |
| 2 | 20/17 | 11/9 | 9/21 |
| 3 | 14/6 | 15/13 | 7/16 |
| 4 | 12/5 | 18/16 | 0/0 |
| 5 | 11/6 | 14/12 | 7/0 |
| 6 | 11/6 | 11/9 | 0/0 |
| 7 | 6/4 | 7/4 | 4/1 |
| 8 | 12/10 | 13/11 | 7/13 |
| 9 | 6/4 | 8/4 | 4/1 |
| 10 | 6/2 | 10/6 | 0/8 |
| 11 | 5/2 | 5/1 | 0/1 |
| 12 | 5/2 | **3**/1 | 0/1 |
| 13 | 8/1 | **3**/1 | 0/1 |
| 14 | 5/1 | **3**/2 | 0/2 |
| 15 | 5/1 | **3**/2 | 0/2 |

### 핵심 패턴
- **on**: c11-13 동결 (resolved=2,2,1, open 20→20→20). c14-15 minimal (1, 1).
- **off**: c11-15 target=3~5 수축, resolved=1~2. open=25 고착.
- 두 trial 모두 후반에 `adjacent_gap` 생성이 거의 멈춤 (on 0~0~0, off 1~1~1~2~2). → integrate.py 가 새 claims 로부터 adj_gap 을 생성하지만, 후반 cycle 의 claims 가 작아 adj_gap 도 작아짐.

---

## 8. A2 Scope 최종 확정 (3-pronged, 우선순위 조정)

### A2b (최우선 — NO-SELECTION 해소)
**대상**: 11 GU on / 23 GU off (61%/92%)

수정 항목:
1. **plan.py `_select_targets` aging penalty**
   - sort key 에 `-min(N, age_in_cycles) × 0.05` 추가 → 5 cycle 이상 unselected GU 가 head 로 승격
   - regression 테스트: medium/convenience GU 가 5 cycle 안에 1회 이상 선택됨

2. **plan.py `_boost_deficit_categories` 임계 완화**
   - 현재 `category_gini > 0.45`. on/off Gini 는 0.24 수준 → 임계 미충족. 임계 0.30 으로 완화 또는 "underselected_count" 기준 추가.

3. **mode.py exploit_budget 수축 원인 조사 (off c12+ target=3)**
   - plan_node 내부에서 target_count 가 13 → 3 으로 줄어드는 코드 경로 식별
   - audit_bias / explore_candidates 비어있음 / LLM 응답 등 후보

**기대 효과**: NO-SEL 11~23 GU 의 다수 선택되어 closing. open 18→7 (on), 25→10 (off) 가능성.

### A2c (중요 — NO-INTEGRATION + adjacent_gap 결함)
**대상**: 2 GU on / 2 GU off (11%/8%) + adjacent_gap 양산 자체

수정 항목:
1. **`_generate_dynamic_gus` entity-type aware filter**
   - city entity → hours/price 제외 (단일 값 없음)
   - free-service entity → price 제외
   - skeleton 정의에 entity_subtype 추가 (city/object/service/free) 또는 LLM gate

2. **N cycle 이상 yield>0 + unresolved → `skeleton_mismatch` 마킹 + HITL-E**

**기대 효과**: NO-INTEGRATION 4건 (on+off 합) 해소 + 향후 malformed GU 양산 차단 → NO-SEL 적체도 자연 감소.

### A2a (보조 — NO-ANSWER query 개선)
**대상**: 5 GU on / 0 GU off (28%/0%)

수정 항목:
1. wildcard slug="*" → 카테고리 경로 우회 (`japan-travel dining hours`)
2. field naturalization (snake_case → 공백, hyphen → 공백, 도메인 prefix)

**기대 효과**: on 환경에서 5 GU 해소. off 환경에서는 효과 없음 (애초에 NO-ANSWER 0).
**우선순위 하향**: D-163 재검토에 따라 부분 원인 확정. A2b/A2c 완료 후 진행.

### 권장 실행 순서
1. **A2c-1 (`_generate_dynamic_gus` filter)** — 가장 저비용, malformed GU 양산 차단으로 다른 결함 자연 감소
2. **A2b-1 (aging penalty)** — 코드 변경 작음, on/off 동시 효과
3. **A2b-3 (exploit_budget 수축 원인 조사)** — plan.py 디버깅
4. **A2a (query builder)** — A2b/A2c 완료 후 stage-e-on 5c trial 로 검증

---

## 9. KU 성장률 미스터리 — on 이 왜 후반에 동결되는가

| trial | c1-5 rate | c6-10 rate | c11-15 rate |
|-------|----------:|-----------:|------------:|
| on  | 7.6 | 4.4 | **0.4** |
| off | 8.8 | 4.4 | **3.2** |
| p2-smart-remodel | 8.8 | 9.0 | 4.2 |

- on c11-15 = 0.4/cycle → KU +2 in 5 cycles (104 → 106). 거의 완전 동결.
- off c11-15 = 3.2/cycle → KU +16 in 5 cycles (100 → 116). 정상 진행.

### 가설
- on 의 External Anchor (universe_probe) 가 c1-c8 까지 다수의 entity (Shirakawa, Himeji 등) 를 Skeleton 에 추가 → claim density 가 c10 까지 빠르게 포화.
- 후반 c11-15 에 External Anchor 가 만들 수 있는 신규 entity 고갈 + 기존 entity 의 (medium, convenience) field 들이 NO-SELECTION 적체 → KU 신규 추가 거의 0.
- off 는 External Anchor 없음 → 처음부터 천천히 entity 추가 → 후반에도 신규 추가 여지 보존.

### 함의
- External Anchor 의 효과는 **초중반 (c1-c10) novelty boost** 로 명확. 후반 동결은 External Anchor 자체 결함이 아니라 NO-SELECTION 적체에 잡아먹힘.
- A2b 수정 후 on 재실행 시 KU 성장률 회복 가능성 존재.

---

## 10. 미답 항목 (P6-A3 이후 조사)

1. **plan.py 내부 target=3 수축 코드 경로** — exploit_budget 13 → 3 의 정확한 사유 식별
2. **dispute_queue @ c15 비교** — on/off 각각 누적 dispute 수 (일치 conflict 처리 효율 비교)
3. **Domain Skeleton 변화 비교** — on 이 universe_probe 로 추가한 entity 수 vs off 의 신규 entity 수 (KU growth 의 기여도 정량)
4. **A2 fix 후 stage-e-off 5c 재검증** — A2b aging penalty 만 적용한 채 off 5c 돌려 NO-SEL 변화 측정 ($1)

---

## 변경 이력

- 2026-04-18: 초안 작성. D-163 최종 확정, D-164/D-165 신규 정식 기록. A2 우선순위 A2b > A2c > A2a 로 조정.
