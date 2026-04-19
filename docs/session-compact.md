# Session Compact

> Generated: 2026-04-18
> Source: Conversation compaction via /compact-and-go

## Goal

stage-e on/off 15c trial 엄밀 비교 → 숨겨진 root cause 정량 식별 → A2 scope 최종 확정 → 결과 commit. (이전 세션의 Step 1~4 모두 수행 완료)

---

## Completed

- [x] **stage-e-compare-analysis.md 신규 작성 (10 섹션)**
  - `dev/active/phase-si-p6-consolidation/stage-e-compare-analysis.md`
  - 상위 요약, 3-카테고리 비교표 (on 18 / off 25 open)
  - H1/H2/H3 가설 검증 (PASS/FAIL 정량 근거 첨부)
  - D-164/D-165 본문 + exploit_budget 수축 미스터리 §5
  - NO-SEL 23건 (off) 전수 분류 (category/field/wildcard 비율)
  - cycle 별 target/resolved 궤적 + KU 성장률 미스터리 분석
  - A2 fix 우선순위 재조정 (A2b > A2c > A2a)

- [x] **debug-history.md D-163 최종 확정 + D-164/D-165 정식 엔트리 추가**
  - 이전: "wildcard slug = root cause" → 최종: "부분원인 (on 28%, off 0%)"
  - D-164: NO-SELECTION dominant root cause (off 92%, on 61%)
  - D-165: adjacent_gap entity-type 무관 field 양산 (city/hours, free/price)

- [x] **MEMORY.md 갱신**
  - D-163 / D-164 / D-165 한 줄 인덱스 추가

- [x] **NO-SEL 23건 (off) 전수 데이터 추출 + 분류**
  - wildcard 5/23 (transport, connectivity, payment×3)
  - city-type 5/23 (Miyazaki_City, Mt_Fuji, Nasu, Kitakami_Tenshochi_Park, Himeji_Castle)
  - field 분포: price 11/23 (48% 압도적), how_to_use 4, tips/hours 각 2
  - trigger: A:adjacent_gap 22/23 (95.7%)

- [x] **mode.py 코드 분석 (exploit_budget 수축)**
  - target_count 공식: jump 모드 max(10, ceil(open*0.5)) → open=25 시 13 이어야 함
  - off c12+ cycle_trace.target_count=3 — 13→3 으로 줄어드는 plan_node 내부 코드 경로 미파악 (후속 조사 항목)

- [x] **commit `cdd4504` 생성 (144 files)**
  - `[si-p6] stage-e-off 15c trial + on/off 비교 분석 (D-163 재확정, D-164/D-165 신규)`
  - bench/silver/japan-travel/p6-diag-off-15c/ + dev-docs + docs/session-compact

---

## Current State

**브랜치**: `main`
**최신 commit**: `cdd4504` (이번 세션 분석 + commit 완료)
**테스트**: 824 passed (이전 세션 동일, 코드 변경 없음)

### 미커밋 잔존 (이번 세션 범위 외)
- `bash.exe.stackdump` (무시)
- `bench/silver/japan-travel/p0-20260412-baseline/telemetry/` (별건)
- `bench/silver/japan-travel/p6-b1-smoke-5c/` (이전 trial)
- `bench/silver/japan-travel/p6-diag-full-15c/` (on trial — 별도 commit 필요)
- `bench/silver/japan-travel/p6-diag-smoke-5c/` (이전 smoke trial)
- `docs/data-generation-end-to-end-review.md`
- `docs/si-p5-review-hangul.md`

### 핵심 결과 표 (변경 없음)

| 카테고리 | stage-e-on | stage-e-off |
|----------|---------:|---------:|
| open total | 18 | 25 |
| NO-ANSWER | 5 (28%) | **0 (0%)** |
| NO-INTEGRATION | 2 (11%) | 2 (8%) |
| NO-SELECTION | 11 (61%) | **23 (92%)** |

### Changed Files (commit `cdd4504`)
- `dev/active/phase-si-p6-consolidation/stage-e-compare-analysis.md` (신규)
- `dev/active/phase-si-p6-consolidation/zero-yield-mapping.md` (이전 세션 작업분 함께 commit)
- `dev/active/phase-si-p6-consolidation/debug-history.md` (D-163 재확정 + D-164/D-165)
- `bench/silver/japan-travel/p6-diag-off-15c/` (전체 telemetry/state-snapshots/trajectory/trial-card)
- `docs/session-compact.md` (이전 세션의 next-action 문서)

---

## Remaining / TODO

### 다음 세션 1순위: A2c-1 구현 (adjacent_gap entity-type aware filter)

**파일**: `src/nodes/integrate.py` `_generate_dynamic_gus`

**작업**:
1. **entity-type 식별 메커니즘 결정**
   - 옵션 A: domain_skeleton 에 `entity_subtype` 필드 추가 (city/object/service/free)
   - 옵션 B: LLM gate (per claim adjacent_gap 생성 전에 검증)
   - 옵션 C: 휴리스틱 (entity_key 의 slug 가 capitalized → city, "*" → wildcard, 등)
   - 권장: **C → A 점진** (휴리스틱 먼저, 후속에 skeleton 정식 필드)

2. **필터 규칙 (D-165 근거)**
   - city entity → hours/price 제외
   - free service entity (visit-japan-web 등) → price 제외
   - wildcard slug → adjacent_gap 생성 자체 금지

3. **테스트 추가**
   - test 파일: `tests/nodes/test_integrate.py` (또는 별도 파일)
   - city + hours malformed 시 GU 생성 안 됨
   - free service + price malformed 시 GU 생성 안 됨
   - regression: 정상 케이스는 그대로 생성

4. **검증**: `pytest tests/nodes/test_integrate.py -v` 통과 후 824 → 826~830 passed 기대

### 2순위: A2b-1 (plan.py aging penalty)

**파일**: `src/nodes/plan.py` `_select_targets` (l.158~165)

**작업**:
1. GU 별 unselected_cycles 추적 (gap_map 에 `last_selected_cycle` 필드 추가)
2. sort key 에 `-min(N, age) × 0.05` 추가 (N=10 권장)
3. regression test: medium/convenience GU 가 5 cycle 안에 1회 이상 선택됨

### 3순위: stage-e-off 5c 검증 trial ($1)

A2c-1 + A2b-1 fix 후:
```bash
python scripts/run_readiness.py --trial-id p6-a2-fix-off-5c \
  --domain japan-travel --cycles 5 --no-external-anchor
```
기대: NO-SEL 비율 92% → ~70% 감소, malformed adjacent_gap 양산 0건.

### 보조 (저우선): A2b-3 (exploit_budget 수축 원인 식별)

plan_node 내부 디버깅 — `state["jump_explore_candidates"]`, audit_bias, LLM 응답 등 확인.

### 미커밋 정리

- p6-diag-full-15c (on trial) commit 여부 결정
- bash.exe.stackdump 삭제
- 다른 미커밋 docs (data-generation-review, si-p5-review-hangul) 정리

---

## Key Decisions

### D-163 최종 확정 (2026-04-18, commit `cdd4504`)
- 이전: "wildcard slug 버그 = root cause"
- 최종: "부분 원인 (on 28%, off 0%, 평균 ~14%). dominant 는 NO-SELECTION."

### D-164 (신규, commit `cdd4504`)
- NO-SELECTION 이 dominant root cause (off 92%, on 61%)
- `plan.py:158-161` priority sort + adjacent_gap 양산 상호작용
- Stage-E (External Anchor) 와 무관한 구조적 결함

### D-165 (신규, commit `cdd4504`)
- adjacent_gap generator entity-type 무관 field 양산
- city + hours/price → malformed
- free service + price → malformed
- on/off 양쪽에서 attraction:City/hours 패턴 동일 발현

### A2 우선순위 재조정
- 이전: A2a (query) > A2b (selection) > A2c (integrate)
- 최종: **A2c (filter) > A2b (aging) > A2a (query)**
- 근거: A2c 는 adjacent_gap 양산 차단으로 NO-SEL/NO-INT 자연 감소. A2a 는 부분 원인 (28%, off 에선 0%) 으로 보조.

---

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 핵심 파일

- **분석 문서**: `dev/active/phase-si-p6-consolidation/stage-e-compare-analysis.md` (10 섹션)
- **매핑 문서**: `dev/active/phase-si-p6-consolidation/zero-yield-mapping.md`
- **debug-history**: `dev/active/phase-si-p6-consolidation/debug-history.md`
- **A2c 대상**: `src/nodes/integrate.py` `_generate_dynamic_gus` (l.510 근방)
- **A2b 대상**: `src/nodes/plan.py` `_select_targets` (l.141~194), `_boost_deficit_categories` (l.112~138)
- **mode.py**: `src/nodes/mode.py` (target_count 공식 l.205~210)

### 데이터 소스

- **off trial**: `bench/silver/japan-travel/p6-diag-off-15c/`
  - telemetry/cycles.jsonl, telemetry/gu_trace.jsonl
  - state-snapshots/cycle-15-snapshot/gap-map.json
- **on trial**: `bench/silver/japan-travel/p6-diag-full-15c/`

### NO-SEL 23 (off) 핵심 패턴 (memo)

| field | count | 비고 |
|-------|------:|------|
| price | 11 (48%) | adjacent_gap price field 무차별 생성 |
| how_to_use | 4 | |
| tips, hours | 각 2 | |

| 카테고리 | wildcard | concrete |
|----------|---------:|---------:|
| transport (5) | 1 | 4 |
| attraction (5) | 0 | 5 (모두 city) |
| regulation (4) | 0 | 4 (emergency, visit-japan-web) |
| pass-ticket (4) | 0 | 4 (suica×3, jr-pass) |
| payment (4) | 3 | 1 |
| connectivity (1) | 1 | 0 |

### NO-INT 패턴 일치
- on: GU-0033 visit-japan-web/price (free service), GU-0090 attraction:Fukuoka/hours (city)
- off: GU-0107 attraction:Shirakawa/hours, GU-0109 attraction:Choshi_City/hours

### 미답 항목
- plan_node 내부 target_count 13→3 수축 코드 경로 (off c12+)
- dispute_queue @ c15 비교 (on/off)
- Domain Skeleton entity 수 비교 (universe_probe 기여 정량)

---

## Next Action (2026-04-19 갱신 — P6-A1-D4 실행 완료, Path-γ 확정 후)

> **매트릭스 결과**: B trial (p6-diag-off-remodel-off-15c) 실행 완료. **Path-γ (remodel 역효과) 극적 초과 관측**. open A=25 → B=9 (-64%), gap_res 0.805 → 0.926 (+12.1pp), NO-SEL 92% → 56% (-36pp). D-167 신규 (remodel-induced exploit_budget shrinkage = dominant root cause). D-164 (plan.py priority sort 구조 결함) **부분 무효 판정**. 자세한 분석은 `stage-e-remodel-matrix.md` §0/§3.2/§5.6/§6 + `debug-history.md` D-167.

### Step 1: commit P6-A1-D4 결과

```bash
git add bench/silver/japan-travel/p6-diag-off-remodel-off-15c/ \
  bench/silver/INDEX.md \
  dev/active/phase-si-p6-consolidation/ \
  docs/session-compact.md
git commit -m "[si-p6] P6-A1-D4: stage-e × remodel 2×2 matrix — Path-γ 확정 (D-166/D-167)"
```

### Step 2: D-167 코드 경로 조사 (새 세션, 별건 조사)

**대상**: `_maybe_run_remodel` 발동 후 `hitl_queue.remodel=1` 이 plan 단계의 `target_count` 를 어떻게 수축시키는지 추적

- `src/orchestrator.py:511-570` `_maybe_run_remodel` return / state 변경
- `src/nodes/plan.py` 에서 `hitl_queue` 참조 여부 + target 계산 로직
- `src/nodes/mode.py` `target_count = max(10, ceil(open*0.5))` 공식에서 3 까지 내려가는 경로

**기대 결과**: 수축 유발 코드 라인 식별 → 완화 fix 설계 또는 `--audit-interval 0` 을 단일 도메인 기본값으로 채택 결정

### Step 3: A2c-1 구현 (기존 계획 유지)

D-165 가 B 에서 재확인되어 **여전히 유효** (city+hours, free+price malformed 2건). 구현 내용은 이전 Next Action 참고 섹션 그대로.

### Step 4 (중요): P6-A F-Gate 재설계 (A11)

기존 기준 "Smart Remodel ≥ 2회 실발동" 은 **발동 빈도 only** — outcome 이 negative 여도 PASS 가능한 결함. 실측으로 증명됨.

**신규 기준 제안**:
- Remodel 발동 pre/post 3 cycle 의 `open` 또는 `gap_resolution` 의 **delta 가 양수** 여야 PASS
- 또는 remodel-on vs remodel-off 15c trial 에서 B outcome 이 A 이상 (회귀 없음) 일 때만 PASS
- P5 Gate 재확인 제안 — 현재 상태로는 "remodel 자연 발동" 성과가 outcome 에 기여하지 않았다는 확신

### Step 5 (보류): A2b-1 (plan.py aging penalty)

D-167 에 의해 **plan.py 자체 결함 아님**으로 판정. 보류. D-167 fix 완료 후 재평가.

---

## (참고) 이전 Next Action — A2c-1 직진 (matrix Path-β 시 복귀 예정이었음)

### Step 1: A2c-1 구현 (adjacent_gap entity-type aware filter)

`src/nodes/integrate.py` `_generate_dynamic_gus`:

1. 휴리스틱 entity-type 식별 함수 추가
   ```python
   def _is_city_entity(slug: str) -> bool:
       # capitalized + 도시 명사 (City/Tower/Castle 등 접미사 또는 단순 cap)
       return bool(slug) and slug[0].isupper() and slug != "*"

   def _is_free_service(entity_key: str) -> bool:
       # visit-japan-web 등 화이트리스트 또는 KU lookup
       FREE_SERVICES = {"visit-japan-web"}
       slug = entity_key.split(":")[-1] if ":" in entity_key else entity_key
       return slug in FREE_SERVICES

   def _is_wildcard(entity_key: str) -> bool:
       return entity_key.endswith(":*")
   ```

2. `_generate_dynamic_gus` 안에서 GU 생성 직전 필터:
   - city + (hours, price) 제외
   - free service + price 제외
   - wildcard entity_key 의 adjacent_gap 생성 금지

3. 로깅: 차단된 GU 수를 cycle_trace 에 `adj_gap_filtered: N` 추가 (후속 검증용)

### Step 2: 단위 테스트 추가

`tests/nodes/test_integrate.py` (있으면 추가, 없으면 신규):
- test_adjacent_gap_filters_city_hours
- test_adjacent_gap_filters_free_service_price
- test_adjacent_gap_filters_wildcard_entity
- test_adjacent_gap_keeps_normal_combinations (regression)

### Step 3: 전체 테스트 + commit

```bash
python -m pytest -q
git -C /c/Users/User/Learning/KBs-2026/domain-k-evolver add \
  src/nodes/integrate.py \
  tests/nodes/test_integrate.py \
  dev/active/phase-si-p6-consolidation/
git -C /c/Users/User/Learning/KBs-2026/domain-k-evolver commit -m "[si-p6] A2c-1: adjacent_gap entity-type filter (city/free/wildcard)"
```

### Step 4: stage-e-off 5c 검증 trial (사용자 승인 후, $1)

```bash
python scripts/run_readiness.py --trial-id p6-a2c-fix-off-5c \
  --domain japan-travel --cycles 5 --no-external-anchor
```

비교 지표:
- adj_gap_filtered count (양수 기대)
- NO-INT 카테고리 0건 기대
- NO-SEL 23 → 17 이하 기대 (city/free/wildcard 산물 제거 효과)
