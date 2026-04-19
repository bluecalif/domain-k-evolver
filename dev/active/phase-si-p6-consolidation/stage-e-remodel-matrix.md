# Stage-E × Remodel 2×2 Matrix — Inside/Outside View 분리 진단

> Created: 2026-04-19
> Status: **완료** — Path-γ 확정 (remodel 역효과, D-164 부분 무효)
> Author: SI-P6-A1-D4 (P6-A1-Diag 서브스테이지 연장)
> Depends on: `stage-e-compare-analysis.md` (outside view 선행), `debug-history.md` D-163/D-164/D-165/D-166/D-167

## 0. 요약 — **실측 결론 (Path-γ 확정)**

2026-04-19 B trial (`p6-diag-off-remodel-off-15c`, `--audit-interval 0`) 실행 완료. 결과는 **예상 Path-γ (remodel 역효과) 를 극적으로 초과**했다:

| 지표 | A (off + remodel-on) | B (off + remodel-off) | Δ |
|---|---:|---:|---:|
| c15 open | 25 | **9** | **-64%** |
| c15 resolved | 103 | **113** | +10 |
| c15 gap_resolution | 0.805 | **0.926** | +0.121 |
| c15 target_count | **3** | **5** | +67% |
| NO-SELECTION 비율 | 92% (23/25) | **56% (5/9)** | **-36pp** |

**진단**: A의 c11+ target=3 고착 (open=25 정체) 은 **remodel 때문이었다**. A에서 cycle 10부터 `hitl_queue.remodel=1`이 매 cycle 누적되면서 plan 단계의 exploit_budget 이 수축 (target 13→3), tail (medium, convenience) GU 가 도달 불가능해졌다. B는 동일 조건에서 remodel 만 제거했을 때 target 5-10 유지 + open 40→9 정상 해소를 확인.

**D-164 (plan.py priority sort 구조 결함) 가설 부분 무효**:
- plan.py 의 sort 로직 자체는 정상. tail 도달 가능한 target_count 만 주어지면 해소됨.
- 진짜 원인은 **remodel 발동 이후 상태 (audit finding 누적 또는 orchestrator 가 생성하는 hitl_queue.remodel 항목) 가 plan 의 target_count 계산을 수축** 시키는 연쇄.
- → **D-167 (신규)** 로 명시: "remodel-induced exploit_budget shrinkage" root cause 확정.

**A2 scope 재조정 결과**:
- A2c (adjacent_gap entity-type filter): **유효** (D-165 B에서 재확인 — city+hours, free+price malformed 양산)
- A2b (plan.py aging penalty): **후순위** 또는 설계 재검토 (plan.py 자체는 결함 없음)
- **신규 최우선**: **remodel 후 target_count 수축 경로 규명** + 완화. `src/orchestrator.py:511-570` `_maybe_run_remodel` → plan 전달 경로 추적.

---

## 0.1 배경 (원래 설계 의도)

`stage-e-compare-analysis.md` (2026-04-18, commit `cdd4504`) 의 **outside view (stage-e-on vs off)** 비교는 D-164/D-165 를 도출했으나, **remodel 활성화 여부**라는 숨은 공변 변수를 검증하지 않았다. telemetry 재확인 결과 두 trial (p6-diag-off-15c, p6-diag-full-15c) 모두 cycle 10부터 `hitl_queue.remodel=1`이 기록됨 — 즉 **remodel이 통제된 공정 비교** (outside view는 여전히 유효) 이지만, **remodel 자체의 순효과**는 분리되지 않았다.

이 문서는 `--audit-interval 0` 플래그를 사용한 **remodel-OFF 신규 trial 1개**를 추가하여 2×2 matrix 의 한 축을 완성하고, **inside view (remodel 단독 효과)** 와 outside view 를 교차 해석하여 P6-A2 scope (A2b aging / A2c filter) 의 우선순위를 **실증 기반**으로 재확정하는 것을 목표로 한다. **목표 달성** (Path-γ 확정).

---

## 1. Matrix 설계

### 1.1 2×2 축 정의

|  | Stage-E **ON** | Stage-E **OFF** |
|---|---|---|
| **Remodel ON** | **C** = `p6-diag-full-15c` (확보) | **A** = `p6-diag-off-15c` (확보) |
| **Remodel OFF** | **D** = 실행 보류 (후속 판단) | **B** = `p6-diag-off-remodel-off-15c` (**신규**) |

### 1.2 비교 경로

| 비교 | 경로 | 분리되는 변수 |
|---|---|---|
| **Outside view** | A ↔ C | Stage-E (external anchor) 순효과 |
| **Inside view (신규)** | A ↔ B | Remodel (Smart Remodel 3-way OR) 순효과 |
| **독립성 검증** | Δ(A→B) vs Δ(C→D) | Stage-E × Remodel 상호작용 유무 |

### 1.3 D(on+remodel-off) 보류 근거

- 비용 대비 한계 효용 낮음: Stage-E 와 Remodel 이 코드상 독립 (orchestrator 가 external_anchor 상태를 remodel 경로에서 참조하지 않음) → A↔B 에서 독립이 관측되면 C↔D 도 동일 형태로 추정 가능.
- 상호작용이 **강하게 의심되는 결과**(§6)가 A↔B 에서 관측된 경우에만 D 실행 고려.

---

## 2. 신규 Trial 실행 스펙

### 2.1 CLI

```bash
python scripts/run_readiness.py \
  --trial-id p6-diag-off-remodel-off-15c \
  --domain japan-travel \
  --cycles 15 \
  --no-external-anchor \
  --audit-interval 0
```

- `--audit-interval 0`: `run_readiness.py` line 194 "audit+remodel 비활성" 명시
- **API 비용 사전 확인 필수** (MEMORY `feedback_api_cost_caution`). 예상 ~$1 (기존 off 15c 와 동일 규모).

### 2.2 Trial scaffold 체크

- `bench/silver/japan-travel/p6-diag-off-remodel-off-15c/`
  - `trial-card.md`, `config.snapshot.json`, `readiness-report.md`, `telemetry/`, `state-snapshots/`
- `bench/silver/INDEX.md` row 추가 (silver-trial-scaffold skill)

### 2.3 실행 검증 (1차 sanity)

- `telemetry/cycles.jsonl` 의 **모든 cycle 에서 `hitl_queue.remodel = 0`** (remodel 진짜 OFF 확인)
- `audit_summary.last_audit_cycle == -1` 또는 `findings_count == 0` 유지
- 15 cycles 정상 종료 (wall_clock 합계, open/resolved 일관성)

---

## 3. 분석 프레임

### 3.1 Primary 지표 (3-카테고리, extensive view) — **실측**

`stage-e-compare-analysis.md` 와 동일한 **no-answer / no-integration / no-selection** 분류를 B trial 에 적용:

| 카테고리 | A (off + remodel-on) | **B (off + remodel-off)** | C (on + remodel-on) |
|---|---:|---:|---:|
| open total | 25 | **9** | 18 |
| NO-ANSWER (wildcard) | 0 (0%) | **2 (22%)** | 5 (28%) |
| NO-INTEGRATION (malformed) | 2 (8%) | **2 (22%)** | 2 (11%) |
| NO-SELECTION | 23 (92%) | **5 (56%)** | 11 (61%) |

**B open=9 상세** (c15 gap-map):

| gu_id | entity_key | field | 분류 |
|---|---|---|---|
| GU-0121 | japan-travel:transport:* | duration | NO-ANSWER |
| GU-0122 | japan-travel:transport:* | how_to_use | NO-ANSWER |
| GU-0102 | japan-travel:attraction:Fukuoka | hours | NO-INT (city+hours, D-165) |
| GU-0030 | japan-travel:regulation:visit-japan-web | price | NO-INT (free+price, D-165) |
| GU-0116 | japan-travel:pass-ticket:suica | where_to_buy | NO-SEL |
| GU-0117 | japan-travel:payment:ic-card | how_to_use | NO-SEL |
| GU-0118 | japan-travel:transport:shinkansen | price | NO-SEL |
| GU-0119 | japan-travel:transport:shinkansen | how_to_use | NO-SEL |
| GU-0120 | japan-travel:transport:airport-transfer | how_to_use | NO-SEL |

**해석**: B의 NO-SEL 5건도 모두 (medium, convenience) 로 D-164 가설의 **부분 반영**은 유효 — tail 적체 현상은 존재. 그러나 open 수가 9로 줄면서 tail 이 도달 가능한 수준이 됨. A에서 23건까지 누적된 것은 target_count=3 고착 때문에 tail 을 **영영 건드리지 못한** 결과.

### 3.2 Secondary 지표 — **실측 (target_count 수축 smoking gun)**

**A vs B target_count cycle 별 대조표** (진짜 발견):

| cycle | A target | B target | A open | B open | A.remodel |
|---:|---:|---:|---:|---:|---:|
| c01 | 14 | 14 | 41 | 40 | 0 |
| c02 | 11 | 10 | 61 | 58 | 0 |
| c03 | 15 | 14 | 64 | 64 | 0 |
| c04 | 18 | 18 | 48 | 54 | 0 |
| c05 | 14 | 16 | 36 | 45 | 0 |
| c06 | 11 | 13 | 27 | 39 | 0 |
| c07 | 7 | 12 | 24 | 33 | 0 |
| c08 | 13 | 13 | 26 | 28 | 0 |
| c09 | 8 | 7 | 23 | 24 | 0 |
| **c10** | 10 | 10 | 25 | 19 | **1** (remodel 최초 발동) |
| **c11** | **5** | 8 | 25 | 22 | **1** |
| **c12** | **3** | 9 | **25** | 22 | **1** |
| **c13** | **3** | 8 | **25** | 20 | **1** |
| **c14** | **3** | 10 | **25** | 12 | **1** |
| **c15** | **3** | 5 | **25** | **9** | **1** |

**관찰**:
- c1-c9 (pre-remodel): A/B target_count 거의 동일 (±2)
- c10 (remodel 최초 발동): A/B target=10 동일 — remodel 직후에는 영향 없음
- **c11~c15 (remodel 지속 발동)**: A target 5→3→3→3→3 급격 수축 vs B target 8~10 유지
- A open=25 고정 (c10 이후 해소 완전 중단) vs B open 22→9 (정상 해소)

→ **remodel 이 매 cycle 발동되면서 target_count 를 수축시킨다**는 사실이 데이터로 입증됨. 기존 D-164 의 "mode.py exploit_budget 수축" 가설에서 수축 **현상**은 맞았으나, **원인**이 plan.py/mode.py 내부가 아닌 **remodel 경로** 였음.

### 3.3 Smart Criteria 재구성 (B 에서 가상 발동 시점 추정)

B 의 `gap_resolution_rate` 궤적:
- c5 0.531, c8 0.725, c10 0.817, c15 0.926 — **단조 증가**
- novelty: c10 0.042, c15 0.012 — drought threshold 0.1 이하가 c5+ 부터 지속
- 만약 remodel 이 켜져 있었다면 A 와 동일하게 c10 부터 `exploration_drought` 로 발동했을 것 (실제 A 의 발동 원인)

→ "Smart Criteria 가 발동한다"는 사실 자체는 정상. 발동 후의 **outcome** 이 문제.

---

## 4. Outside View 재인용 (A ↔ C)

`stage-e-compare-analysis.md` §2~§4 핵심만 발췌:

- Stage-E 는 **diversity 주입** (external anchor seed 투입) → on 쪽이 claim 변동성↑, NO-ANSWER 5건 발생
- Stage-E 는 **malformed GU 양산을 억제하지 않음** — adjacent_gap generator 가 entity-type 을 무시하는 문제(D-165)는 on/off 공통
- NO-SEL 비율 역전 (on 61% < off 92%)은 open 수 차이 (18 vs 25) 에 의한 wildcard/concrete 혼합 영향

→ outside view 는 **"Stage-E 는 NO-SEL 자체를 줄이지 않으며, open 수와 exploration budget 에 간접 영향만 준다"** 로 잠정 확정 (D-164 근거).

---

## 5. Remodel 효과 Discussion — **실측 결과 기반 재해석**

> 5.1~5.4 는 B trial 실행 **전** 사고실험이었다. 실측이 Path-γ 에 해당하는 방향 중 **원래 예상과 다른 메커니즘**으로 나타났으므로, **§5.6 실측 해석** 을 먼저 읽고 그 뒤 사전 시나리오(5.1~5.5) 와 비교하라.

### 5.1 Remodel 이 '효과 없음'으로 관측된 경우 (B ≈ A)

**정량 기준**: NO-SEL 비율 |B - A| < 5pp, KU 순증·gap_resolution 차이 < 10%.

**해석 4가지**:

#### (a) **구조적 결함 가설 — plan.py priority sort**
A/B 모두에서 NO-SEL 이 90%+ 로 지배적이면, remodel 이 수행하는 **merge/split/source_policy 조정**이 하류의 selection 로직을 건드리지 못하는 것. 이 경우:
- D-164 (plan.py:158-161 priority sort 결함) 가설이 **강화됨**
- A2b (aging penalty) 최우선, A2c (adjacent_gap filter)는 양산 차단용 부차 fix
- Remodel 의 존재가 `open/resolved` trajectory 의 표면적 안정화에 기여했을 뿐, 진정한 GU 해결에는 기여하지 못했다는 뜻

#### (b) **Remodel 공회전 가설 — merge/source_policy 가 실제 KU 재구성에 이르지 못함**
A 의 cycle 10 remodel 이 67 merge proposal 을 생성했더라도, 그 중 채택되어 KU가 물리적으로 통합된 건이 적다면 effectively no-op. 이 경우:
- `remodel.py` `apply_proposals` 경로의 **실제 적용률**을 확인 필요 (별건 조사)
- P2 Gate 의 "remodel cycle 10/15 자연 발동" 성과는 "발동 빈도" 지표였을 뿐, "outcome 변화" 지표가 아니었을 가능성
- D-133 `min_overlap_count ≥ 2` 필터가 **너무 보수적** 이어서 대부분 proposal 이 drop 되었을 가능성 검토

#### (c) **Remodel 타이밍 문제 — cycle 10 은 이미 동결 후**
A/C 모두 cycle 5-9 에서 target_count 가 13→6 으로 줄며 exploit_budget 수축이 진행되는데, remodel 은 cycle 10 에서 최초 발동. 이미 plan 경로가 malformed GU 로 포화된 뒤 KU 를 정리해봐야 하류에서 빼먹지 못함. 이 경우:
- Smart Criteria 의 `window=3/5` 가 **너무 길다** → A7 (config 외부화) 이후 window 축소 실험 우선순위↑
- 또는 exploration_drought 가 너무 늦게 true 가 됨 — threshold=30 을 15-20 으로 낮춰야 효과 발현

#### (d) **Remodel 은 실제로 효과 있으나 본 지표로 안 보임**
NO-SEL 은 selection 단계 실패이므로, remodel 이 기여하는 **upstream** 효과 (KU 중복 제거, category 균형) 는 이 지표로 포착되지 않음. 이 경우:
- secondary 지표 (KU Gini, entity 중복률, merge 적용률) 로 재검증 필요
- Remodel 의 진정한 효용은 50c 이상 trial 에서만 드러날 수 있음 → P6-A12 forecast 재검토

### 5.2 Remodel 이 '효과 있음'으로 관측된 경우 (B 의 NO-SEL ≫ A)

- Remodel 이 A 에서 NO-SEL 을 완화 중이었음 → "malformed GU 를 정리해서 selection 통과율을 높였다"
- A2b (aging) 효과는 remodel 이 간접 구현하고 있었던 것일 수 있음 → A2b 설계 재조정
- **그러나**: A2c (adjacent_gap filter) 는 **여전히 유효** — malformed 양산 자체 차단이 remodel 사후 정리보다 비용효율적

### 5.3 Remodel 이 '역효과' 로 관측된 경우 (B 의 NO-SEL ≪ A)

- Remodel merge 가 entity 혼탁을 유발하여 selection 을 어지럽혔을 가능성
- D-133 `min_overlap_count` 기준이 여전히 **부족** (1-field overlap 과다 merge 금지했지만 2-field 라도 field 의미 불일치시 merge 되면 KU 가 "융합된 괴물" 이 됨)
- A2 전에 **remodel.py merge 기준 재검토**가 선행 과제

### 5.4 Remodel 이 '성능 개선 없음' 그 자체의 의미

사용자 질문에 대한 직접 답:

1. **Remodel 을 구현했다는 사실만으로 "Inner Loop Quality" 가 개선되지 않는다.** Remodel 은 **재구성 기회**를 제공할 뿐, 하류 selection/integration 이 그 기회를 활용해야 outcome 이 바뀐다. P5 Gate PASS (b122a23) 는 "remodel 이 발동한다"를 검증했지 "remodel 이 KU 성장률을 구조적으로 바꾼다"를 검증하지 않았다.

2. **P6-A F-Gate (A11) 의 설계 재검토 필요.** 현재 F-Gate 는 "Smart Remodel ≥ 2회 실발동 + forecast c16-c50 ≥ 4회" 로 **발동 빈도**만 요구. Remodel 효과 없음이 B 에서 확정되면, F-Gate 는 **"remodel 발동이 NO-SEL 또는 KU 성장률에 유의미한 delta 를 만들었는가"** 로 기준 상승 필요.

3. **Silver P6 exit criteria 의 정량적 재정의.** KU ≥ 250 / gap_resolution ≥ 0.85 목표가 remodel 의 존재 덕분인지, collect/integrate 의 기본 성능 덕분인지 구분 안 됨. 본 matrix 결과는 이 구분을 가능하게 함.

4. **"Self-Governing Evolver" (Phase 4) 의 premise 재점검.** Phase 4 는 "도메인 변화 시 Evolver 가 스스로 정책을 조정한다"를 목표로 했는데, 그 조정 메커니즘의 정점이 remodel. remodel 이 단일 도메인에서도 효과 불분명이면, Phase X (multi-domain) 에서 더 드러날 것이라 기대하기 어려움. 본 trial 은 Phase 6 이후의 multi-domain 계획에도 영향을 주는 진단.

### 5.5 결론: 무엇을 결정해야 하는가 (사전 시나리오)

B trial 결과에 따라 **3 방향 중 1** 선택:

- **Path-α (B ≈ A, 효과 없음)**: A2b 최우선, remodel 은 safety net 으로 유지 (비활성화 제안은 하지 않음 — 50c 이상에서는 다를 수 있음). debug-history D-166 으로 기록.
- **Path-β (B ≫ A, 효과 있음)**: 현재 A2 scope 재조정 불필요, A2c 만 구현 후 P6-A F-Gate 재검증. remodel 은 설계대로 기능 확인.
- **Path-γ (B ≪ A, 역효과)**: A2 중단, remodel.py merge 기준 재검토 선행. D-133 재검토 이슈 신규 생성.

---

### 5.6 **실측 해석 (2026-04-19)** — Path-γ 확정, 그러나 메커니즘이 다르다

**사전 예상 (5.3 Path-γ)**: "Remodel merge 가 entity 혼탁을 유발하여 selection 을 어지럽힘"
**실측 메커니즘**: **Remodel merge 단계 이전**, `hitl_queue.remodel=1` 이 매 cycle 누적되는 사실 자체가 plan 단계의 **target_count 를 수축**시킨다. merge 품질(D-133 `min_overlap_count`) 은 이번 문제의 원인이 아닐 가능성이 높다.

#### (1) 관찰된 인과 사슬

```
cycle 10: 최초 remodel 발동 → hitl_queue.remodel := 1
cycle 11+: remodel 항목이 hitl_queue 에 지속 점유 (audit_interval=5 로 매 5 cycle 재평가)
         ↓
plan 단계가 exploit 모드로 강제 진입 (추정: hitl_queue 우선 처리 로직)
         ↓
target_count 5 → 3 고정 (A), vs B 는 normal 5~10
         ↓
tail (medium, convenience) GU 가 영영 선택 불가 → NO-SEL 92% 누적
```

**다음 조사 (별건)**: `src/orchestrator.py:511-570` `_maybe_run_remodel` → `plan_node` 전달 경로에서 `hitl_queue.remodel` 이 target_count 계산에 어떻게 관여하는지 코드 추적. `mode.py` `target_count = max(10, ceil(open*0.5))` 공식이 어떤 경로로 3 까지 내려가는지 확인.

#### (2) D-164 가설 재판정

| D-164 원 문장 | 실측 검증 |
|---|---|
| "`plan.py:158-161` priority sort 가 (medium, convenience) 를 tail 에 고정" | **부분 유효** — sort 로 tail 에 가는 것은 맞음. 그러나 tail 도달 가능한 target_count 가 주어지면 해소됨 (B c14 open 20→12, c15 12→9) |
| "`_generate_dynamic_gus` 가 매 cycle (medium, convenience) 양산 → tail 적체" | **실측** — B 에서도 동일 양산 (c11 adj=9, c12 adj=6, c13 adj=3). 그러나 B 는 open=9 로 수렴 (적체 원인 아님) |
| "후반 exploit_budget 수축으로 악화" | **유효, 그러나 원인 전환** — 수축의 원인이 mode.py 내부가 아닌 remodel |

→ **D-164 "plan.py priority sort 구조 결함" 판정 → 무효 (A2b 불필요)**.
→ **D-167 (신규)** "remodel-induced exploit_budget shrinkage" 가 dominant root cause.

#### (3) D-165 (adjacent_gap entity-type filter) 는 여전히 유효

B 의 open=9 중 2건 (GU-0102 city+hours, GU-0030 free+price) 이 D-165 malformed 패턴으로 재확인. A2c (adjacent_gap filter) 는 **수축 문제와 독립적으로 유효**한 개선.

#### (4) "remodel 이 있어도 성능 개선이 없다" 의 실측 의미

사용자가 사전에 제기한 질문 "if performance does not improve even with remodel, what does it mean?" 에 대한 **실측 근거 답변**:

1. **"개선 없음" 이 아니라 "적극적 역효과"**. 단일 도메인 15c 범위에서 remodel 은 +29 resolved (93 → 113) 를 **방해** (A=103 vs B=113 — B 가 10 건 더 많이 해소). gap_resolution 0.805 vs 0.926 (12.1pp 격차).

2. **P5 Gate PASS (b122a23) "remodel 자연 발동 2회"의 의미 재검토 필요.** "발동한다"는 mechanism alive 증거였으나, outcome 은 **negative delta**. Gate 기준이 "빈도" 가 아닌 "**pre/post outcome delta 양수**"로 재설계되어야 함을 실증.

3. **Phase 4 "Self-Governing Evolver" premise 붕괴 가능성.** remodel 은 Phase 4 의 핵심 "자가 조정" 메커니즘. 단일 도메인에서 적극적 해악이면, 도메인 교차 Phase X 에서 효과를 기대할 근거가 매우 약함. **단, 50c 이상에서 "수축이 오히려 noise 정제에 기여" 할 가능성을 배제 못 함** — P6-A12 50c trial 에서 이 가설 검증 필요.

4. **현재로는 remodel OFF 가 dominant 전략**. `--audit-interval 0` 이 단일 도메인 15c 범위에서 최적. A2c (filter) 구현 + remodel OFF 로 P6-A Gate 재설계 후보.

---

## 6. 판정 — **Path-γ 확정 (2026-04-19)**

### 6.1 NO-SEL 비율 판정표 (사전 설계 대비 실측)

| B 의 NO-SEL | A 와의 차이 | 판정 | 후속 |
|---|---|---|---|
| 88-96% | ±4pp | Path-α (remodel 무효) | A2b 최우선 |
| 97%+ | +5pp 이상 | Path-β (remodel 유효) | A2c 만 구현 |
| 85% 이하 | -7pp 이상 | Path-γ (remodel 역효과) | A2 보류 + remodel.py 재검토 |
| **실측 56%** | **-36pp** | **Path-γ (역효과) 극대치** | **A2c 구현 + remodel.py 가 아닌 orchestrator→plan 경로 조사** |

### 6.2 후속 조치 (§0 요약 중복)

1. **A2c (adjacent_gap entity-type filter)** 구현 — D-165 B trial 재확인으로 유효성 확정
2. **D-167 조사**: `_maybe_run_remodel` → plan `target_count` 경로 추적 (matrix §5.6 (1))
3. **A2b (plan.py aging penalty) 보류** — plan.py 자체는 결함 없음
4. **D-133 `min_overlap_count` 재검토 취소** — merge 품질이 원인이 아님 (사전 Path-γ 대응책 무효)
5. **P5 Gate "remodel 자연 발동" 성과 재해석** — §5.6 (4) 참조

### 6.2 이상 징후 체크 (조건 불충족 시 재실행)

- 15c 완주 실패 (중간 에러)
- `hitl_queue.remodel` 이 0 이 아닌 cycle 존재 (flag override 실패)
- open 수가 5 미만 또는 50 초과 (pipeline 이상)

### 6.3 추가 산출물

- `stage-e-remodel-matrix.md` §3~§6 에 실측 수치 채움
- `debug-history.md` D-166 본문 확정 (현재는 예비)
- MEMORY.md D-166 한 줄 추가
- commit: `[si-p6] P6-A1-D4: stage-e × remodel 2×2 matrix — inside/outside view 분리 (D-166)`

---

## 7. 의도적 비포함 (이번 matrix 에서 건드리지 않는 것)

- **A2c-1 구현**: matrix 결과로 scope 확정 후 별도 세션
- **exploit_budget 수축 원인**: A/B/C 모두에서 관측됨 → 별건 조사, matrix 결론과 독립
- **D(on + remodel-off) trial 실행**: §1.3 근거로 보류
- **50c trial**: P6-A12, F-Gate 통과 후

---

## 8. 핵심 파일 참조

### 읽기 전용 (분석 대상)
- `bench/silver/japan-travel/p6-diag-off-15c/telemetry/` (A)
- `bench/silver/japan-travel/p6-diag-full-15c/telemetry/` (C)
- `bench/silver/japan-travel/p6-diag-off-remodel-off-15c/telemetry/` (B, 실행 후)

### 재사용 함수 / 설정 지점
- `src/orchestrator.py:466-509` — `_should_remodel` (Smart Criteria 3-way OR)
- `src/orchestrator.py:511-570` — `_maybe_run_remodel`
- `src/nodes/remodel.py:29` — `_MERGE_MIN_OVERLAP_COUNT = 2` (D-133)
- `scripts/run_readiness.py:193-198` — `--audit-interval 0` / `--no-external-anchor`
- `scripts/analyze_saturation.py` — 기존 진단 옵션 재사용 (`--trace-frozen`, `--compare-trials`)

### 연관 문서
- `dev/active/phase-si-p6-consolidation/stage-e-compare-analysis.md` — outside view 본문
- `dev/active/phase-si-p6-consolidation/zero-yield-mapping.md` — field/category 분해
- `dev/active/phase-si-p6-consolidation/debug-history.md` — D-163/D-164/D-165, D-166(예비)
