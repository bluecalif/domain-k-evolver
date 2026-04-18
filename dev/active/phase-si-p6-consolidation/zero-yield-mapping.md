# Zero-Yield & Unresolved GU Mapping — p6-diag-full-15c

> 작성일: 2026-04-18
> Trial: `bench/silver/japan-travel/p6-diag-full-15c/` (stage-e-on, 15c, 824 tests passed)
> 목적: c15 remaining 18 open GU 를 3 카테고리로 완전 분리하여 A2 fix scope 결정
> 데이터 소스: `telemetry/gu_trace.jsonl` (139 events, 85 unique GUs) + `state-snapshots/cycle-*-snapshot/gap-map.json` (96 GUs)

## 요약 표

| 카테고리 | 정의 | 개수 | 비율 | 주 원인 |
|----------|------|-----:|-----:|---------|
| **NO-ANSWER** | Plan이 선택했으나 Tavily search_yield=0 지속 | 5 | 28% | wildcard slug(3) + 부자연스러운 concrete query(2) |
| **NO-INTEGRATION** | search_yield>0 인데도 resolve 실패 | 2 | 11% | adjacent_gap generator 의 malformed field (semantic mismatch) |
| **NO-SELECTION** | Plan이 어느 cycle 에서도 target 으로 선정하지 않음 | 11 | **61%** | (medium, convenience) priority 고정 sort 탓 — 항상 list tail |
| **합계** | open @ c15 | 18 | 100% | |

**D-163 재해석**: wildcard slug 버그는 NO-ANSWER 의 3/5 (= 전체 18 의 17%) 부분 원인이며, 최대 미해결 버킷은 **NO-SELECTION (61%)**.

---

## 1. NO-ANSWER (5/18, 28%)

Plan 이 GU 를 선택해 query 를 생성했지만 Tavily 가 모든 attempt 에서 0 결과 반환.

### 1.1 wildcard 3건 (slug 버그 — plan.py:268)

| GU | entity_key / field | cycles attempted | query (재현) |
|---|---|---|---|
| GU-0020 | `dining:*` / hours | 8 (c8~c15) | `"* hours"`, `"* hours 2026"` |
| GU-0021 | `dining:*` / location | 2 (c3, c13) | `"* location"`, `"* location 2026"` |
| GU-0025 | `payment:*` / tips | 3 (c3, c5, c13) | `"* tips"`, `"* tips 2026"` |

**원인**: `plan.py:268`
```python
slug = entity_key.split(":")[-1] if ":" in entity_key else entity_key
queries[gu_id] = [f"{slug} {field}", f"{slug} {field} 2026"]
```
wildcard entity_key (`dining:*`) 를 split → slug=`*` → query 가 `"* hours"` 형태로 나가 Tavily 무결과.

**fix 방향**: plan.py 에서 slug=="*" 이면 (a) 카테고리 전체 search (`japan-travel dining hours`) 로 대체하거나, (b) 해당 GU 를 query 대상에서 제외 + seed/universe_probe 에만 의존.

### 1.2 concrete 2건 (부자연스러운 query)

| GU | entity_key / field | cycles | query (재현) |
|---|---|---|---|
| GU-0019 | `connectivity:sim-card` / where_to_buy | 8 (c8~c15) | `"sim-card where_to_buy"` |
| GU-0026 | `payment:ic-card` / acceptance | 2 (c5, c13) | `"ic-card acceptance"` |

**원인**: plan.py 가 entity_key 의 hyphen-slug 와 snake_case field 를 그대로 공백 연결 → 실제 사람이 검색할 표현과 괴리.
- `"sim-card where_to_buy"` → 기대 표현은 `"SIM card where to buy in Japan"` / `"Japan SIM card store"`
- `"ic-card acceptance"` → 기대 표현은 `"IC card accepted stores Japan"` / `"Suica Pasmo acceptance"`

**fix 방향**:
- field 사전 기반 번역 (`where_to_buy` → `"where to buy"`, `acceptance` → `"accepted"`)
- hyphen → 공백 (`sim-card` → `"SIM card"`)
- 도메인 키워드 prefix (`"japan"` / `"japan-travel"`)

### 공통 조치
- LLM Plan 경로 실패 시 deterministic fallback 이 query 를 만들기 때문에, fallback query builder 자체를 수리해야 함.
- fix 후 stage-e-off 5c 재검증 (≤$0.5) 권장.

---

## 2. NO-INTEGRATION (2/18, 11%)

Search 는 15 snippet 을 가져왔지만 claims 가 resolve 로 이어지지 않은 GU.

| GU | entity_key / field | cycles | yields | 추정 원인 |
|---|---|---|---|---|
| GU-0033 | `regulation:visit-japan-web` / price | 3 (c13~c15) | [15,15,15] | Visit Japan Web 은 **무료 서비스** — "price" 필드 자체가 semantically malformed |
| GU-0090 | `attraction:Fukuoka` / hours | 6 (c10~c15) | [15,15,15,15,15,15] | Fukuoka 는 **도시** (attraction 단일 객체 아님) — "hours" 필드가 malformed |

### 경로 분석 (integrate.py)

`integrate.py:510` resolvable set = `("added", "updated", "condition_split", "refreshed")`.
claims 가 생성되어도 `integration_result` 가 이 set 에 들어가지 않으면 GU 는 open 유지.

**GU-0033 추정 흐름**:
- LLM 이 price 관련 claim 추출 시도 → visit-japan-web 무료 속성 때문에 "free"/"no fee" 로 응답
- `_find_matching_ku(visit-japan-web, price)` → None → 신규 KU `added` 경로
- **하지만 실제 KU 목록**에 visit-japan-web 엔 `how_to_use/eligibility/policy/tips` 4개만 있고 price 는 **없음** → 신규 KU 가 만들어졌어야 했는데 안 된 경우 = LLM 이 0 claims 반환 또는 LLM 이 field 를 price 가 아닌 how_to_use/policy 등으로 추출 → 기존 KU 와 충돌 판정 → `conflict_hold` → resolve 실패.

**GU-0090 추정 흐름**:
- Fukuoka 의 hours 검색 결과는 "opening hours of Fukuoka Tower" 등 하위 속성 전파 → claim 이 여러 entity 에 분산
- 같은 이유로 field 불일치 → `conflict_hold` 또는 0 claims.

### 근본 원인: adjacent_gap generator

두 GU 모두 `trigger="A:adjacent_gap"` + `trigger_source="CL-XXXX-XX"`:
- GU-0033: `CL-0004-01` (tourist-visa 주변 전파)
- GU-0090: `CL-0015-05` (Kyoto 주변 전파 추정)

**adjacent_gap generator (integrate.py: `_generate_dynamic_gus`) 가 entity 의 의미를 고려하지 않고 skeleton field 조합을 기계적으로 생성** → ill-formed GU 양산 → 영구 open.

### fix 방향
1. adjacent_gap generator 에 entity-type aware 필터 추가 (e.g., 서비스/무료 entity 는 price 제외, 도시 entity 는 hours 제외)
2. integrate.py `_detect_conflict` 가 "same entity, different field" 케이스에 `conflict_hold` 남발하지 않는지 검증
3. N cycle (≥3) 동안 yield>0 이지만 unresolved 인 GU 는 자동 `skeleton_mismatch` 마킹 후 HITL-E 로 escalate

---

## 3. NO-SELECTION (11/18, **61% — 최대 버킷**)

Plan 이 15 cycle 동안 한 번도 target_gaps 에 넣지 않은 GU.

| GU | entity_key / field | created_cycle | trigger_source |
|---|---|---:|---|
| GU-0030 | `regulation:emergency` / price | c1 | CL-0003-01 |
| GU-0031 | `regulation:emergency` / policy | c1 | CL-0003-01 |
| GU-0056 | `transport:balance-0` / how_to_use | c2 | CL-0036-01 |
| GU-0057 | `transport:balance-0` / tips | c2 | CL-0036-01 |
| GU-0058 | `payment:ic-card` / how_to_use | c2 | CL-0008-01 |
| GU-0059 | `payment:ic-card` / tips | c2 | CL-0008-01 |
| GU-0060 | `accommodation:balance-0` / etiquette | c2 | CL-0038-01 |
| GU-0061 | `accommodation:balance-0` / tips | c2 | CL-0038-01 |
| GU-0062 | `transport:balance-1` / duration | c2 | CL-0037-01 |
| GU-0063 | `transport:balance-1` / tips | c2 | CL-0037-01 |
| GU-0064 | `accommodation:balance-1` / location | c2 | CL-0039-01 |

**공통점**:
- 모두 (`expected_utility=medium`, `risk_level=convenience`) — **priority 최저 버킷**
- 모두 adjacent_gap 으로 c1~c2 에 자동 생성
- `expansion_mode` 없음 (jump 아님) → jump mode 의 explore_candidates 진입 불가

### 원인: plan.py `_select_targets` 고정 sort

```python
# plan.py:158-161
open_gus.sort(key=lambda g: (
    _UTILITY_ORDER.get(g.get("expected_utility", "low"), 99),
    _RISK_ORDER.get(g.get("risk_level", "informational"), 99),
))
# plan.py:165
exploit_targets = open_gus[:exploit_budget]
```

`_UTILITY_ORDER = {critical:0, high:1, medium:2, low:3}`
`_RISK_ORDER = {safety:0, financial:1, policy:2, convenience:3, informational:4}`

(medium, convenience) = sort key (2, 3) → (critical/high) 뒤, (high, informational) 뒤로 밀림.

### 증거

c15 start: 19 open GU 모두 (medium, convenience) → tiebreak 이 **list 원 순서** 뿐 → 앞쪽 5개만 target 으로 선정됨. 뒤쪽 11개는 영원히 제외.

c2 에서는 20 GU 선정됐으나 모두 (`high`, `informational`) 의 GU-0036~0052 에 집중 → (medium, convenience) 전원 skip.

이후 c3~c15 (13 cycle 누적) 동안:
- jump mode 가 대부분이지만 exploit_budget 이 작고 (3~10),
- remaining_explore 보충 시에도 `expansion_mode=="jump"` GU 우선 → "-" 인 11 GU 들은 보충 경로로도 잡히지 않음.

### fix 방향

1. **Aging / starvation 방지**: 생성 후 N cycle 이상 unselected GU 는 sort key 에 `-age_penalty` 추가
2. **deficit coverage-based 승격**: `_boost_deficit_categories` 는 이미 존재하나 (plan.py:112~138) `category_gini > 0.45` 조건이 충족 안 되면 작동 안 함 → 임계치 재조정 또는 "underselected" 기준 추가
3. **explore_budget 확장**: jump mode 의 explore 가 (medium, convenience) 도 무작위 포함하도록 (기존 "jump only" 필터 완화)
4. **target_count cap 점검**: D-129 에서 cap 제거했으나 실측 상 target_count 는 5~14 로 제한 → mode decision 단계에서 open GU 대비 cap 로직 재검토

---

## 4. Cycle 별 zero-yield 분포 (참조)

| cycle | mode | target | resolved | wc_yield | cc_yield | 주요 zero-yield GU |
|---:|---|---:|---:|---:|---:|---|
| c1 | normal | 13 | 11 | 75 | 105 | — |
| c2 | normal | 20 | 17 | 0 | 270 | wildcard 2 모두 0 |
| c3 | jump | 14 | 6 | 0 | 105 | wildcard 5 모두 0 (포함 GU-0021, 0025 신규) |
| c4 | jump | 12 | 5 | 0 | 90 | wildcard 2 모두 0 |
| c5 | jump | 11 | 6 | 15 | 75 | wildcard 3/4 zero + GU-0026 신규 zero |
| c6 | jump | 11 | 6 | 15 | 75 | wildcard 4/5 zero |
| c7 | jump | 6 | 4 | 15 | 45 | — |
| c8 | jump | 12 | 10 | 105 | 45 | GU-0019, GU-0020 신규 zero |
| c9 | jump | 6 | 4 | 0 | 60 | GU-0019, GU-0020 지속 zero |
| c10 | jump | 6 | 2 | 30 | 30 | GU-0090 신규 (yield=15) + GU-0019/0020 zero |
| c11 | jump | 5 | 2 | 0 | 45 | GU-0090 지속 yield>0 unresolved |
| c12 | jump | 5 | 2 | 0 | 45 | 동일 |
| c13 | jump | 8 | 1 | 0 | 45 | GU-0033 신규 (yield=15) 추가 |
| c14 | jump | 5 | 1 | 0 | 45 | GU-0033/0090 지속 |
| c15 | jump | 5 | 1 | 0 | 45 | GU-0033/0090 지속 |

---

## 5. A2 Fix Scope 재설계

### A2a: plan.py query builder 수리 (NO-ANSWER — 5 GU, 28%)
- **A2a-1**: wildcard slug="*" 검출 → 카테고리 경로 / seed 전담으로 우회
- **A2a-2**: field naturalization (hyphen → 공백, snake_case → 공백, 도메인 prefix)
- **비용**: 코드 수정 중, stage-e-off 5c 검증 ~$0.5
- **기대 효과**: wildcard 3 + concrete 2 해소 가능성 → 18 중 5 resolve (28% 감소)

### A2b: plan.py target_gaps 선택 로직 (NO-SELECTION — 11 GU, 61% — **최대 효과**)
- **A2b-1**: aging penalty (cycle 별 -0.05 per unselected cycle)
- **A2b-2**: deficit_boost 조건 완화 (current gini 임계 0.45 → 0.30 또는 underselected 조건 추가)
- **A2b-3**: jump mode explore 의 "jump only" 필터 완화 — (medium, convenience) 샘플링 포함
- **비용**: 코드 수정 + 15c full re-run ($1)
- **기대 효과**: 11 GU 중 다수 선택되어 closing 가능. 단 NO-ANSWER/NO-INTEGRATION 문제도 동시 해결 필요.

### A2c: integrate.py resolve 디버깅 + adjacent_gap 필터 (NO-INTEGRATION — 2 GU, 11%)
- **A2c-1**: `_generate_dynamic_gus` entity-type aware filter (service=무료면 price 제외 등)
- **A2c-2**: `_detect_conflict` 오판 체크 (same entity different field)
- **A2c-3**: yield>0 + N cycle unresolved → skeleton_mismatch 마킹 + HITL-E
- **비용**: 코드 수정 중
- **기대 효과**: 2 GU 해소 + 향후 malformed GU 양산 감소

### 권장 실행 순서
1. **A2a (query builder)** — 가장 저비용, stage-e-off 검증 가능
2. **A2c (adjacent_gap filter)** — 중간 비용, 구조적 개선
3. **A2b (selection logic)** — 실측 검증 $1 필요, A2a/A2c fix 이후 효과 최대

---

## 6. 미답변 항목 (stage-e-on vs off)

사용자 지적: "stage-e-off 가 왜 0 으로 가지 않는가 미답변".

- 현재 보유 데이터: stage-e-on 15c (p6-diag-full-15c), stage-e-off **5c** (p6-diag-smoke-5c, p6-b1-smoke-5c)
- **stage-e-off 15c 부재** — 공정 비교 불가
- External Anchor 가 생성하는 GU 유형 (balance-0, balance-1 계열) 이 stage-e-off 에서도 동일하게 NO-SELECTION 버킷에 빠지는지 확인 필요
- **판단**: A2 fix 후 stage-e-off 15c 1회 추가 trial ($1) — fix 효과 측정 겸.

---

## 7. 부록: 분석 재현 커맨드

```bash
# 3-카테고리 분류
python -c "
import json
from collections import defaultdict
trace = [json.loads(l) for l in open('bench/silver/japan-travel/p6-diag-full-15c/telemetry/gu_trace.jsonl', encoding='utf-8')]
gm = json.load(open('bench/silver/japan-travel/p6-diag-full-15c/state-snapshots/cycle-15-snapshot/gap-map.json', encoding='utf-8'))
open_gus = set(g['gu_id'] for g in gm if g.get('status')=='open')
by_gu = defaultdict(list)
for r in trace: by_gu[r['gu_id']].append(r)
no_sel = open_gus - set(by_gu.keys())
no_ans = [g for g in open_gus & set(by_gu) if not any(e['search_yield']>0 for e in by_gu[g])]
no_int = [g for g in open_gus & set(by_gu) if any(e['search_yield']>0 for e in by_gu[g])]
print(f'NO-SELECTION: {len(no_sel)} {sorted(no_sel)}')
print(f'NO-ANSWER: {len(no_ans)} {sorted(no_ans)}')
print(f'NO-INTEGRATION: {len(no_int)} {sorted(no_int)}')
"
```

---

## 변경 이력

- 2026-04-18: 초안 작성 (P6 A1-D3 후속). D-163 재검토 반영, 3-카테고리 분리.
