# Session Compact

> Generated: 2026-04-19 (P6-A1-D4 이후 inflection point)
> Source: Conversation compaction via /compact-and-go

## Goal (이 시점까지)

Stage-E × Remodel 2×2 matrix 진단 → Path-γ (remodel 역효과) 확정 → 다음 세션에서 **세 갈래 재정렬** (POR / Remodel / Explore-Pivot) 논의 준비.

---

## Completed (누적)

### 이전 세션 (commit `cdd4504`)
- [x] stage-e-compare-analysis.md (10 섹션) + D-163/D-164/D-165
- [x] NO-SEL 23 (off) 전수 분류

### 이번 세션 (commit `a8dfe0e`, 132 files)
- [x] **B trial 실행 완료**: `p6-diag-off-remodel-off-15c` (`--audit-interval 0`, 15 cycles, exit 0)
- [x] **Path-γ 확정 (극적 초과)**:
  - open c15: A=25 → **B=9** (-64%)
  - gap_resolution c15: 0.805 → **0.926** (+12.1pp)
  - NO-SEL 비율: 92% → **56%** (-36pp)
  - target_count c12~c15: A=**3 고착** vs B=**5~10 유지**
- [x] **D-166 확정** (Stage-E × Remodel 독립성 — 기존 on/off 모두 c10+ remodel 자연 발동)
- [x] **D-167 신규** (Remodel-induced exploit_budget shrinkage = dominant root cause)
- [x] D-164 부분 무효 판정 (plan.py sort 자체 결함 아님)
- [x] MEMORY.md + INDEX.md 갱신, tasks.md 5/24

### 다음 세션 첫머리 이전 미완
- [x] **D-167 코드 경로 부분 조사 (진행 중)**:
  - `target_count` 가 cycles.jsonl 에 기록되는 값 = `len(plan["target_gaps"])` (telemetry.py:147, cycle_ctx)
  - mode.py 공식은 open=25 시 `max(10, ceil(25*0.5))=13` 산출. **3 은 mode.py 가 만든 값 아님**
  - `plan.py:319-321` `has_remodel_pending` 은 `status=="pending"` 만 매치 → hitl auto-approve 는 `status=="approved"` → **matches False**
  - 결론 미완: target_count 10→5→3 수축 경로가 plan 내부 어디인지 아직 특정 안 됨 (LLM 응답 필터링? `_extract_cycle_ctx` 에서 gu_id 소실?)

---

## Current State

**브랜치**: `main` | **최신 commit**: `a8dfe0e` | **테스트**: 824 passed

### 3-Trial 매트릭스 (c15 요약)

| 지표 | A (off+remodel-on) | B (off+remodel-off, **POR**) | C (on+remodel-on) |
|---|---:|---:|---:|
| open | 25 | **9** | 18 |
| resolved | 103 | **113** | 78 |
| gap_resolution | 0.805 | **0.926** | 0.812 |
| target_count c12~c15 | **3 고착** | 5~10 유지 | 5~8 |
| NO-SELECTION | 92% | **56%** | 61% |
| dispute_queue | 133 | 109 | 97 |

### 미커밋 잔존
- bash.exe.stackdump, p0-20260412-baseline/telemetry, p6-b1-smoke-5c, p6-diag-full-15c, p6-diag-smoke-5c
- docs/data-generation-end-to-end-review.md, docs/si-p5-review-hangul.md

---

## Key Decisions (누적)

- **D-163**: wildcard slug = 부분원인 (28% / 0%)
- **D-164**: NO-SEL dominant — **D-167 에 의해 부분 무효** (plan.py sort 자체 결함 아님)
- **D-165**: adjacent_gap entity-type 무관 field 양산 (city+hours, free+price) — B 에서 재확인 (2/9)
- **D-166**: Stage-E × Remodel 독립성 — 기존 on/off 모두 c10+ 자연 발동
- **D-167**: **Remodel-induced exploit_budget shrinkage = dominant root cause** — B 에서 target 5-10 유지 입증

---

# ▶ Next Session Agenda — Inflection Point 3-Track 재정렬

> **CRUCIAL**: 이번 inflection point 는 "A2c 직진" 이 아닌 **근본 전략 재검토**. 다음 세션에서 아래 3 track 을 이 순서로 논의.

## Track 1. POR (Point of Reference) 확정 — `remodel-off`

### 1-1. POR 선언
- **현재 baseline = `--audit-interval 0` (remodel 완전 비활성)**
- Silver P6 모든 후속 비교·튜닝은 POR 대비 delta 로 판정
- **Remodel 은 "proper renovation 전까지 금지"** — P2 Gate 통과 이력 있더라도 현 시점부터 off 가 기본값

### 1-2. POR Pain Points 리뷰 (다음 세션 1순위)
POR 에서 여전히 해소되지 않은 9 건 (c15 open) 세부 분류:

| 카테고리 | 건수 | 원인 추정 |
|---|---:|---|
| NO-ANSWER (wildcard) | 2/9 | GU-0121, GU-0122 (transport:*) — D-163 잔여 |
| NO-INTEGRATION (malformed) | 2/9 | GU-0102 (Fukuoka/hours), GU-0030 (visit-japan-web/price) — **D-165 재확인** |
| NO-SELECTION | 5/9 | suica/where_to_buy, ic-card/how_to_use, shinkansen/price·how_to_use, airport-transfer/how_to_use (medium/convenience) |

**리뷰 포인트**:
1. 5 건 NO-SEL 은 POR 에서도 tail 에 남음 → aging / priority 보강이 필요한가, 아니면 **15c 범위의 자연 잔여**로 수용 가능한가 판단
2. 2 건 NO-INT (D-165) 는 A2c-1 (filter) 로 해결 가능 — 이 fix 는 **remodel 과 무관**하므로 Track 1 안에서 진행 가능
3. 2 건 wildcard → query fallback 전략으로 처리 가능한가

### 1-3. POR 내 작업 범위
Remodel 을 건드리지 않는 개선만:
- **A2c-1** (adjacent_gap entity-type filter) — B 에서 malformed 2/9 재확인 → **여전히 유효**
- D-163 wildcard query fallback (선택)
- aging penalty (A2b) — 효과 크지 않을 가능성, 검토 후 결정

### 1-4. Pain Point 검토 결과 → Track 2 전이 조건
Pain point 정량 분석이 "POR 만으로는 KU evolution 한계" 를 증명하면 → Track 2 (remodel revive) 발동.
증명 못 하면 → POR 가 target state, remodel 영구 비활성.

---

## Track 2. Remodel 의 본래 목적 부활 — **CRUCIAL**

### 2-1. 현재 관측된 side effect (이미 확인)
- `exploit_budget shrinkage` → target_count 10→5→3 수축 → open 25 고착
- outcome delta 음수: -10 resolved, -12.1pp gap_resolution, +36pp NO-SEL
- 단일 도메인 15c 범위에서 "개선 없음" 이 아닌 **적극적 역효과**

### 2-2. Countermeasure (수정 필요)
이전 세션에서 제안했던 조치:
- D-167 코드 경로 식별 → 수축 유발 라인에서 완화
- `target_count = max(5, ceil(open*0.5))` 최소 하한 강제 (회귀 가드)
- 또는 `hitl_queue.remodel` 플래그가 plan 단계에 전파되지 않도록 차단

**수정 필요 포인트** (사용자 지시):
- 위 조치는 "remodel 이 있을 때 수축 방지" 에 국한. **remodel 의 효과 자체를 복원하지 않음**.
- 단순 "부작용 제거" → target baseline 복원에 그침. **PASS 요건 미달**.

### 2-3. ⚠ 부활의 CRUCIAL POINT
> **Remodel 은 KU evolution 을 유의미하게 개선해야 한다.**
> "부작용 제거 후 중립" 이 아닌 "적극적 기여" 가 설계 목적.

구체적으로 다음 중 하나 이상을 달성해야 remodel 부활 정당화:
- (a) **KU 순증 가속**: remodel-on 이 remodel-off 대비 15c 안에서 active KU +N% 이상
- (b) **카테고리 균형 개선**: category_gini 가 POR 보다 유의미하게 낮음
- (c) **충돌/노후 해소**: merge/split/reclassify 가 conflict_rate 또는 staleness 해소에 순기여
- (d) **Plateau 돌파**: POR 가 자연 수렴하는 cycle 이후에도 remodel-on 이 추가 탐색 가능

**현재 A trial 은 (a)(b)(c)(d) 전부 negative** — 부활을 위해서는 remodel 의 설계 자체 재검토 필요:
- `_should_remodel` 3-way OR criteria 재조정 (너무 빈번한가?)
- `_apply_remodel_proposals` merge 가 오히려 target_count 수축의 원인? → merge 후 gap_map 축소의 2차 효과 조사
- remodel 발동 조건을 **outcome-gated** 로 (사전 시뮬레이션에서 순기여 예상 시만 적용)
- 또는 **merge 를 제외한 proposal types** (reclassify, alias_canonicalize, source_policy) 만 허용

### 2-4. 다음 세션 논의 포인트
1. 위 (a)~(d) 중 현재 Silver 가 필요로 하는 최우선 효과는?
2. Remodel 부활을 위한 A/B/C 설계 스케치 (각각 trial 으로 검증 필요)
3. "Proper renovation" 의 범위 — 코드 수정이냐, criteria 수정이냐, 아예 trigger 재설계냐

---

## Track 3. Explore-Pivot (Universe Probe) 역할 재검토

### 3-1. 현재 상태
- Stage-E (External Anchor / Universe Probe) 는 `--no-external-anchor` 로 3-trial 모두에서 비활성
- 외부 anchor 가 없는 상태에서 A/B/C 비교 완료 → universe_probe 단독 효과는 **이번 데이터로 판정 불가**
- 과거 (stage-e-compare-analysis.md §5) 에서 on/off 비교 시 outside view 는 **remodel 변수에 오염** 상태 (D-166 에 의해 판정)

### 3-2. Remodel 재설계와의 관계
- Remodel 이 "KU evolution 가속" 으로 부활하려면 **탐색 소스가 필요** → explore_pivot 이 그 소스 후보
- 현재 explore_pivot 의 역할:
  - universe_probe: 외부 snippet 으로 domain skeleton 을 넓힘
  - 새 entity 후보를 KU 에 투입 → remodel 이 이를 merge/split/reclassify 하는 재료 공급
- **논리 연쇄**: explore_pivot (탐색) → KU/entity 증가 → remodel (재조직) → KU evolution 가속
- Remodel 이 "부활" 하려면 explore_pivot 이 **의미 있는 신규 재료를 공급하는 상태**여야 함

### 3-3. 다음 세션 리뷰 포인트
1. **현재 explore_pivot 효과 측정**: D-167 조사 후 remodel 부작용 제거 상태에서 stage-e-on vs off 15c trial 1회 재실행 (예산 $1)
   - remodel 비활성 조건에서 explore_pivot 순효과 분리 가능
2. **기여 정량**: explore_pivot on 이 domain_skeleton entity 수, novelty, axis_coverage 에 순기여하는가
3. **역할 결정**:
   - (α) explore_pivot 을 remodel 의 전제조건으로 고정 — remodel renovation 에 편입
   - (β) explore_pivot 독립 track — POR 에 통합, remodel 과 분리
   - (γ) 현재 조건에서는 기여 부족 → 폐기 또는 연기

### 3-4. Dev Direction 결정 기준
- 리뷰 결과 (α) → explore-pivot + remodel 을 단일 묶음 renovation 으로 추진
- (β) → POR 에 안정 기여 시 채택, 없으면 보류
- (γ) → Silver P6 범위 내 폐기, P7+ 로 재검토

---

## Context (다음 세션용)

다음 세션에서는 답변에 한국어를 사용하세요.

### 핵심 파일
- **매트릭스 분석**: `dev/active/phase-si-p6-consolidation/stage-e-remodel-matrix.md`
- **debug-history**: D-166/D-167 확정본
- **POR (B trial) 데이터**: `bench/silver/japan-travel/p6-diag-off-remodel-off-15c/`
- **A (remodel-on, side effect 증거)**: `bench/silver/japan-travel/p6-diag-off-15c/`
- **D-167 조사 대상**: `src/orchestrator.py:511-576` (`_maybe_run_remodel`, `_apply_remodel_proposals`), `src/nodes/plan.py:306-397` (plan_node, has_remodel_pending), `src/nodes/mode.py:180-250` (target_count 공식)

### D-167 조사 진행 상황 (다음 세션 이어서)
- `target_count` (cycles.jsonl) = `len(plan["target_gaps"])` — telemetry/orchestrator._extract_cycle_ctx 경로 확정
- mode.py 공식은 3 을 만들지 않음 (open=25 → formula=13)
- `has_remodel_pending` 은 "pending" 만 매치 → auto-approve 후 "approved" → False
- **미확정**: LLM 응답이 target 을 줄이는가? `_extract_cycle_ctx` 에서 gu_by_id 필터로 빠지는가? `_boost_deficit_categories` 또는 다른 경로?

### Track 1 Pain Points 데이터
- POR open 9 건: NO-ANSWER 2 (transport:*), NO-INT 2 (Fukuoka/hours, visit-japan-web/price), NO-SEL 5 (suica/where_to_buy, ic-card/how_to_use, shinkansen/price·how_to_use, airport-transfer/how_to_use)
- 모두 medium/convenience 우선순위

### Track 2 Remodel 부활 후보 설계
- Option A: Criteria 보수화 (trigger 간격 10c → 15c)
- Option B: Proposal type 제한 (merge 제외)
- Option C: Outcome-gated (사전 시뮬레이션 필수)
- Option D: Outer-loop 이관 (inner loop 에서 제거)

---

## Next Action

**다음 세션 시작 시 수행할 것**:

1. 이 session-compact.md Track 1/2/3 을 그대로 반영하여 논의 진입
2. 사용자와 **Track 1 Pain Point 리뷰부터** 시작 (POR 9 건 세부 분석 + A2c-1 즉시 진행 여부 결정)
3. Track 1 결과에 따라 Track 2 발동 조건 확인 → Track 2 발동 시 Remodel 부활 설계 (CRUCIAL)
4. Track 3 은 Track 2 설계안과 연동하여 마지막 리뷰

**직접적 code action 은 Track 1 Pain Point 리뷰 완료 후에만 시작.** D-167 조사 미완 이어받기보다 **3-Track 재정렬이 우선**.
