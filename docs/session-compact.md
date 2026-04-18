# Session Compact

> Generated: 2026-04-18
> Source: Conversation compaction via /compact-and-go

## Goal

stage-e-off 15c trial 실행 → stage-e-on (p6-diag-full-15c) 과 엄밀 비교 → 숨겨진 low-yield root cause 발견 → A2 scope 최종 확정.

---

## Completed

- [x] **3-카테고리 매핑 파일 (stage-e-on 분석)**
  - `dev/active/phase-si-p6-consolidation/zero-yield-mapping.md` 신규
  - c15 remaining 18 open GU: NO-ANSWER 5(28%), NO-INTEGRATION 2(11%), NO-SELECTION 11(61%)

- [x] **NO-SELECTION 원인 조사 (plan.py)**
  - `plan.py:158-165` 고정 sort (utility→risk). (medium, convenience) = sort tail → 14 cycle 동안 미선정
  - 11 GU 모두 adjacent_gap 산물, 9개는 External Anchor balance-0/1 계열

- [x] **NO-INTEGRATION 원인 조사 (integrate.py)**
  - GU-0033 visit-japan-web/price: 서비스 무료 → "price" malformed
  - GU-0090 attraction:Fukuoka/hours: 도시 entity → "hours" malformed
  - 근본원인: `_generate_dynamic_gus` entity-type 무관 field 조합 생성

- [x] **NO-ANSWER 원인 조사**
  - wildcard 3건: plan.py:268 slug="*" → query `"* hours"` → Tavily 무결과
  - concrete 2건 (GU-0019 sim-card/where_to_buy, GU-0026 ic-card/acceptance): 부자연스러운 query 문자열

- [x] **D-163 재검토 + debug-history.md 수정**
  - "wildcard slug = root cause" → "부분 원인 17%, 주범 NO-SELECTION 61%" 로 재정의
  - `debug-history.md` D-163 재검토 엔트리 추가

- [x] **p6-diag-off-15c trial 실행 ($1)**
  - `bench/silver/japan-travel/p6-diag-off-15c/` (--no-external-anchor, 15c, exit code 0)
  - `telemetry/cycles.jsonl` 15 rows, `gu_trace.jsonl` 138 events

- [x] **메모리 갱신**
  - `feedback_root_cause_extensive_view.md` 신규 (3-카테고리 분리 원칙)
  - `MEMORY.md` 포인터 추가

---

## Current State

**브랜치**: `main`
**최신 commit**: `ef3b0b7` (변경 없음 — 이번 세션은 분석/문서 작업)
**테스트**: 824 passed, 3 skipped

### p6-diag-off-15c 결과 (핵심 발견)

| 지표 | stage-e-on | stage-e-off | 비고 |
|------|--------:|--------:|---|
| open @ c15 | 18 | **25** | off 가 더 많음 |
| NO-ANSWER | 5 (28%) | **0 (0%)** | wildcard slug 버그 안 드러남 |
| NO-INTEGRATION | 2 (11%) | **2 (8%)** | 같은 패턴 유지 |
| NO-SELECTION | 11 (61%) | **23 (92%)** | off 에서 압도적으로 지배 |

**충격적 발견 (숨겨진 root cause)**:
1. stage-e-off 에서 NO-ANSWER=0 → wildcard slug 버그가 stage-e-on 에서만 드러난 이유: off 환경에서 wildcard GU(dining:*, payment:*) 들이 애초에 NO-SELECTION 버킷에 빠져 한 번도 query 되지 않음 (GU-0029 transport:*/tips 등)
2. **NO-SELECTION 이 92% (23/25) → External Anchor 문제가 아니라 plan.py priority sort 의 구조적 결함**이 dominant root cause
3. c11~c15 target=3 (25 open 중 3개만): mode_decision exploit_budget 이 후반에 급격히 수축 → 별도 조사 필요 (미답)
4. NO-INTEGRATION off 2건: Shirakawa/hours (yield=15×6), Choshi_City/hours (yield=15×2) → attraction:City/hours 패턴 반복 → adjacent_gap의 city-type entity + hours field 조합이 항상 malformed

### p6-diag-off-15c cycle 특이 패턴

```
c11-c15: target=3, wc=0, cc=3, resolved=1~2, cc_yield=45, open=25 (고착)
```
후반 5 cycle 연속 target=3 고착 (왜 exploit_budget=3 으로 수축했는지 미조사).

### Changed Files

- `dev/active/phase-si-p6-consolidation/zero-yield-mapping.md` (신규)
- `dev/active/phase-si-p6-consolidation/debug-history.md` (D-163 재검토 엔트리)
- `bench/silver/japan-travel/p6-diag-off-15c/trial-card.md` (신규)
- `bench/silver/japan-travel/p6-diag-off-15c/` (trial 전체 — 미커밋)
- `memory/feedback_root_cause_extensive_view.md` (신규)
- `memory/MEMORY.md` (포인터 추가)
- `docs/session-compact.md` (이 파일)

### 미커밋

- `bench/silver/japan-travel/p6-diag-off-15c/` (new trial)
- `docs/session-compact.md`
- `dev/active/phase-si-p6-consolidation/zero-yield-mapping.md`
- `dev/active/phase-si-p6-consolidation/debug-history.md`

---

## Remaining / TODO

### 다음 세션 1순위: stage-e-on vs off 엄밀 비교 분석 + root cause 확정

**`dev/active/phase-si-p6-consolidation/stage-e-compare-analysis.md` 작성**

포함 내용:
1. **3-카테고리 비교 표** (위 표 포함)
2. **H1/H2/H3 가설 검증 결과**:
   - H1 (NO-SEL은 External Anchor 산물): **FAIL** — off 에서 NO-SEL 오히려 23(92%)으로 증가. External Anchor 제거가 도움 안 됨
   - H2 ((medium, convenience) sort 문제는 stage-e 무관): **PASS** — off 에서 확인됨
   - H3 (wildcard 3건은 off 에서도 발생): **FAIL** — off 에서 NO-ANSWER=0. wildcard GU 들이 NO-SELECTION 버킷으로 이동 (한 번도 query 안 됨)
3. **숨겨진 root cause 확정**:
   - plan.py priority sort 구조적 결함이 dominant cause (92% in off)
   - c11-c15 exploit_budget=3 급격 수축 원인 조사 필요
4. **Adjacent_gap malformed 패턴** (city/hours): Shirakawa, Choshi_City, Fukuoka, Miyazaki_City 모두 같은 패턴 → entity_type = city → "hours" field malformed

### 조사 항목

1. **exploit_budget 급격 수축 (c11~c15=3)** — mode_decision 에서 왜 jump mode 에서 budget 이 3으로 고착되는지 `src/nodes/mode.py` 조사
2. **NO-SELECTION 23건 전체 분류** — entity_key/field/trigger_source 리스트업 (pass-ticket, connectivity, payment wildcards 등)
3. **A2 scope 재확정** (3-pronged 우선순위):
   - **A2b (NO-SELECTION 해소, 최우선)**: aging penalty + exploit_budget 수축 방지 + city-entity filter
   - **A2c (NO-INTEGRATION, adjacent_gap filter)**: attraction:City + service:free 필터
   - **A2a (NO-ANSWER query 개선)**: wildcard → category 우회 + field naturalization

---

## Key Decisions

### D-163 재검토 (확정 대기)
- 이전: "wildcard slug 버그 = root cause"
- 수정: "부분 원인(17%). 주범은 plan.py priority sort (NO-SELECTION). stage-e 무관."
- stage-e-off 비교로 구조적 근거 확보됨. 다음 세션에서 D-163 최종 확정 후 debug-history 기록.

### D-164 (신규 — 다음 세션에서 정식 기록)
- NO-SELECTION 이 dominant root cause (92% in off, 61% in on)
- External Anchor 제거 시 오히려 악화 → stage-e 는 novelty 기여 효과가 있지만 NO-SELECTION 문제는 별개
- plan.py `_select_targets` 의 고정 sort + exploit_budget 수축 = 구조적 결함

### D-165 (신규 후보)
- city-type entity (Fukuoka/Shirakawa/Choshi_City/Miyazaki_City) 의 "hours" 필드는 항상 malformed
- `_generate_dynamic_gus` 에 entity category-aware 필터 필요

---

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 핵심 파일

- **off trial 데이터**: `bench/silver/japan-travel/p6-diag-off-15c/telemetry/`
- **on trial 데이터**: `bench/silver/japan-travel/p6-diag-full-15c/telemetry/`
- **매핑 파일**: `dev/active/phase-si-p6-consolidation/zero-yield-mapping.md`
- **디버그 이력**: `dev/active/phase-si-p6-consolidation/debug-history.md`
- **plan.py**: `src/nodes/plan.py` (`_select_targets` l.141~194, `_boost_deficit_categories` l.112~138)
- **mode.py**: `src/nodes/mode.py` (exploit_budget 결정 로직)

### 미조사 항목

- `src/nodes/mode.py` exploit_budget 수축 로직 (c11~c15 budget=3 원인)
- stage-e-off NO-SEL 23건 전체 entity_key 목록 (pass-ticket, connectivity wildcards 포함)
- External Anchor 의 KU growth 기여도 정량 비교 (on vs off KU 성장률)

### 분석 재현 커맨드

```bash
# off trial 3-카테고리
python -c "
import json; from collections import defaultdict
trace = [json.loads(l) for l in open('bench/silver/japan-travel/p6-diag-off-15c/telemetry/gu_trace.jsonl', encoding='utf-8')]
gm = json.load(open('bench/silver/japan-travel/p6-diag-off-15c/state-snapshots/cycle-15-snapshot/gap-map.json', encoding='utf-8'))
open_ = set(x['gu_id'] for x in gm if x.get('status')=='open')
by = defaultdict(list)
for r in trace: by[r['gu_id']].append(r)
no_sel = open_ - set(by); no_ans = [x for x in open_&set(by) if not any(e['search_yield']>0 for e in by[x])]; no_int = [x for x in open_&set(by) if any(e['search_yield']>0 for e in by[x])]
print(f'NO-SEL={len(no_sel)} NO-ANS={len(no_ans)} NO-INT={len(no_int)}')
"

# 비교 스크립트
python scripts/analyze_saturation.py --compare-trials p6-diag-full-15c p6-diag-off-15c
```

---

## Next Action

### Step 1: stage-e-compare-analysis.md 작성

`dev/active/phase-si-p6-consolidation/stage-e-compare-analysis.md` 신규 작성:

1. **비교 표 (on vs off)**: 3-카테고리 분포, open count, KU 성장률, cycle별 target/resolved 궤적
2. **H1/H2/H3 가설 검증**: 결과 및 근거
3. **숨겨진 root cause 확정**: D-164/D-165 정식 기록
4. **exploit_budget 수축 조사**: mode.py 코드 분석 → c11~c15 budget=3 원인 파악
5. **NO-SEL 23건 전체 분류**: entity_key/field/trigger_source 완전 리스트
6. **A2 scope 최종 확정**: 3-pronged 우선순위 조정

### Step 2: analyze_saturation.py --compare-trials 실행

```bash
python scripts/analyze_saturation.py --compare-trials p6-diag-full-15c p6-diag-off-15c --trace-frozen 3 --query-patterns
```

### Step 3: debug-history.md 갱신

- D-163 최종 확정 (stage-e 비교 근거 포함)
- D-164, D-165 신규 엔트리 추가

### Step 4: 커밋

```bash
git -C /c/Users/User/Learning/KBs-2026/domain-k-evolver add \
  bench/silver/japan-travel/p6-diag-off-15c/ \
  dev/active/phase-si-p6-consolidation/ \
  docs/session-compact.md \
  memory/
git -C /c/Users/User/Learning/KBs-2026/domain-k-evolver commit -m "[si-p6] stage-e-off 15c trial + on/off 비교 분석 (D-163 재확정, D-164/D-165 신규)"
```
