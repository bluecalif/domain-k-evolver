# SI-P7 S3 GU Mechanistic Gate (M-Gate)

> 도입: 2026-04-26
> 대체: `si-p7-plan.md` G1~G5 narrative Gate (false PASS 발급 확인)
> 구현: `scripts/check_s3_gu_gate.py` (+ `scripts/_gate_helpers.py`)
> L1 tests: `tests/scripts/test_gate_helpers.py` (20), `tests/scripts/test_check_s3_gu_gate.py` (13)
> 의미론·임계값 근거: `.claude/plans/b-plann-very-carefully-breezy-flame.md`

---

## 1. 도입 배경

기존 G1~G5 narrative Gate 가 `p7-rebuild-s3-gu-smoke` 에 PASS 발급. 그러나 entity-field-matrix 분석 결과:

- vacant 11 만 감소 (목표 −97 의 11%)
- attraction `vacant=77 ∧ open_gu=0` (시스템이 카테고리 포기)
- adj_yield 0.500 → 0.362 (−28%)
- adj_gen c4=0, c5=2 (후반 collapse)

G1~G5 결함:
- "코드 돌았나" 만 측정. 베이스라인 비교 없음.
- 임계값 absurd 낮음 (G2 ≥5, G4 ≥1).
- attraction abandoned 같은 패턴 미탐지.
- 후반 cycle collapse 를 hand-wave (KU 포화) 로 정당화.

**판단**: G1~G5 는 거짓 PASS 발급 도구. 폐기.

---

## 2. 신호 의미론

### V (Vacant) — true blind spot
KU·GU 모두 부재인 entity-field 슬롯. 시스템이 **인지조차 못 한 영역**.

### O (Open GU) — active frontier
시스템이 gap 인식 + 투자 큐잉했으나 미해소된 GU. **능동 frontier**.

### 파생 상태
`ku_only` (KU 있고 GU 없음), `ku_gu` (둘 다), `gu_resolved_no_wildcard_ku` 는 V·O 변동의 결과.

### 시스템 건강 판정표

| 상태 | Vacant 추세 | Open GU | 판정 |
|------|------------|---------|------|
| Healthy progress | ↓ | mid (활성 조사) | PASS |
| Premature done | low | 0 | FAIL — 탐색 중단 |
| **Abandoned category** | **high (≥5)** | **0** | **FAIL — 카테고리 포기** |
| Stalled discovery | high, 정체 | low | FAIL — 진척 없음 |
| Backlog overflow | high | very high | FAIL — 해소 불능 |
| Active conversion | ↓ | ↑ then ↓ | PASS — frontier flowing |

---

## 3. V/O Criteria (1차 신호, 6개)

| ID | 측정 | 임계값 | 근거 |
|----|------|--------|------|
| **V1** vacant_total_reduction | `summary.vacant` 비교 | `target ≤ baseline − 29` (= P-zone 97 × 30%) | 5c 한계로 100% 달성 불가, 30% 미만이면 fix 작동 의심 |
| **V2** per_category_vacant_no_regression | 모든 cat 에 대해 vacant 비교 | 어떤 cat 도 vacant 증가 금지 | aggregate 개선이 per-cat 후퇴를 가려서는 안 됨 |
| **V3** untouched_entity_bound | 모든 field=vacant 인 entity 수 | `target ≤ baseline` | 신규 entity 발견 후 진입 못 한 카운트 추적 |
| **O1** active_frontier_existence | per-cat (vacant ≥ 5 ∧ open_gu = 0) ∨ total open ≤ budget×1.5 | hard fail 시 즉시 FAIL | 5c 시점 open=0 = "수렴 또는 포기", 진짜 수렴 아니면 포기 |
| **O2** open_gu_category_coverage | KL(vacant_share \|\| open_share) | `≤ 0.5` | 완전 일치 비현실적, 0.5 이상이면 시스템이 vacant 큰 곳 무시 |
| **VxO** frontier_health | 모든 cat 이 (done ∨ active ∨ improving) 하나 만족 | 0 cat 실패 | done=vacant ≤ entity×0.5, active=open/vacant ≥ 0.05, improving=Δvacant/baseline ≥ 20% |

### V/O 합산 정책
**V/O FAIL 어느 하나라도 → unconditional FAIL (exit=1).** M 결과 무관.

---

## 4. M Criteria (보조 신호, 8개)

T9~T14 fix 의 직접 증거 + regression guard.

| ID | 검증 대상 | 측정 | 임계값 | 근거 |
|----|-----------|------|--------|------|
| **M1** | T9 named-entity adj | `gap-map` 의 trigger=adjacent_gap ∧ entity_key.slug ≠ '*' 카운트 | `≥ 12 ∧ ≥ baseline × 2.0` | T9 fix 가 P1=75 슬롯 대상. 부분 작동(16%)이라도 12개. 2× 는 noise 차단 |
| **M2** | T11 wildcard parallel | WPF 5 fields 별 entity-specific GU 와 wildcard GU 짝지어진 비율 | `≥ 0.70` | seed 단계 wildcard 있을 수 있어 100% 미만 허용. 70% 미만 = T11 미작동 |
| **M3** | T12 cap 제거 | regulation+pass-ticket 카테고리 GU 총수 | `≥ 18 ∧ ≥ baseline × 1.5` | per_cat_cap=4 제거 효과. baseline 은 cap 내 4 GU/cat |
| **M4** | T13 field diversity | adj GU 의 distinct field 수 | `≥ baseline + 2 ∧ ≥ 6` | skeleton 9 fields. baseline 은 hard-coded 3-4. T13 후 6+ 정상 |
| **M5** | T14 late cycle | snapshot Δc4, Δc5 (adj count) | weak: `Δc4>0 ∨ Δc5>0` / strict (`--strict`): `Δc4>0 ∧ Δc5>0` | 한 cycle 0 가능, 둘 다 0 = T14 cap 또는 candidate exhaustion 결함 |
| **M6** | adj_yield regression guard | `adjacency-yield.json` 5c 평균 | `≥ baseline × 0.9` | 10% 미만 변동은 cycle noise. 절대 임계 단독 사용 시 후퇴 은폐 |
| **M7** | S5 inheritance invariant | conflict ledger field 와 adj GU target 교집합 | 0건 | 하드 invariant. (현재 loose check; M10 telemetry 후 strict) |
| **M8** | KU regression guard | `trajectory[-1].ku_active` | `≥ baseline × 0.95` | 5% 는 LLM stochastic variance |

### Self-mode 처리
`--baseline` 과 `--target` 경로 동일 시 비교형 criteria (V1, V3, M1, M3, M4, M6, M8) 는 "no-regression" 만 체크 (target ≥ baseline). 절대형 (O1/O2/VxO/M2/M5/M7) 은 그대로 평가.

---

## 5. Telemetry-Deferred (4개)

현재 데이터로 측정 불가 → NA. **Gate 통과의 선행 조건 아님.** 별도 task 로 보강.

| ID | 검증 대상 | 필요 telemetry | 영향 파일 |
|----|-----------|---------------|-----------|
| M5b | T14 strong (cap_hit) | `cap_hit_count` per cycle in trajectory | `integrate.py:280`, `state.py`, `run_readiness.py` |
| M9 | T10 sweep attribution | `gu['origin'] ∈ {claim_loop, post_cycle_sweep}` | `integrate.py:570-597`, `gap-unit.json` |
| M10 | created_cycle 정확도 | `gu['created_cycle']: int` (ISO date 대체) | `state.py`, `integrate.py:255`, `seed.py` |
| M11 | per-cycle adj/wildcard | `adj_gen_count`, `wildcard_gen_count` in trajectory | `integrate.py`, `seed.py`, `run_readiness.py` |

---

## 6. Exit Code 정책

| Code | 의미 | 조건 |
|------|------|------|
| 0 | PASS | V/O 모두 PASS ∧ M FAIL 0 |
| 1 | FAIL | V/O FAIL 어느 하나 (V/O 우선) |
| 2 | ERROR | 파일 부재, schema 파싱 오류 |
| 3 | CONDITIONAL | V/O PASS ∧ M 일부 FAIL — diagnosis 필요하나 release-blocker 아님 |

---

## 7. 본 Trial 적용 결과 (2026-04-26)

### Self-Sanity (baseline=target=`p7-rebuild-s3-smoke`)
- **비교형 9개 모두 PASS** → Gate 로직 정상 (no-regression 체크 OK)
- **절대형 5개 FAIL** → 베이스라인 자체 unhealthy 정확 포착:
  - O1: regulation(v=12), transport(v=5), attraction(v=72) 3개 cat 모두 open_gu=0 abandoned
  - O2: KL=∞ (전 cat open_gu=0)
  - VxO: 5/8 cats fail
  - M2: 0/7=0.00 (T11 fix 가 baseline 에는 없음, 정상)
  - M7: violations=9 (베이스라인에서 conflict 해소 후 재생성 패턴)
- **Plan §7.1 의 self-sanity PASS 가정은 무효** — 베이스라인이 완전 healthy 라는 전제가 틀림. 비교형 PASS 만으로 Gate 로직 정상 확인.

### 실 재판정 (`p7-rebuild-s3-smoke` → `p7-rebuild-s3-gu-smoke`)

**VERDICT: FAIL exit=1** (V/O 5/6 FAIL)

| ID | 결과 | 측정 | 해석 |
|----|------|------|------|
| V1 | FAIL | Δ=11 (need ≥29) | vacant 11% 만 감소 |
| V2 | FAIL | attraction +5, **connectivity +1** | connectivity 신규 regression |
| V3 | PASS | target=0, baseline=0 | 모든 entity 최소 1 슬롯 채움 |
| O1 | FAIL | attraction(v=77, o=0) | 시스템이 attraction 포기 |
| O2 | FAIL | KL=∞ | open GU=2 인데 attraction 에 0 |
| VxO | FAIL | 7/8 healthy, attraction 단독 | 다른 cats 는 healthy 확인 |
| M1 (T9) | FAIL | 14/13=**1.08×** | T9 거의 무작동 — attraction abandoned root cause 후보 |
| M2 (T11) | PASS | 3/4=0.75 | **T11 작동 확인** |
| M3 (T12) | PASS | 31/12=**2.58×** | **T12 작동 확인** |
| M4 (T13) | PASS | 7 vs 5 | **T13 작동 확인** |
| M5 (T14) | PASS weak | Δc4=0, Δc5=2 | strict 모드 FAIL — T14 부분 작동 |
| M6 | FAIL | 0.362/0.500=0.72 | adj_yield 28% 후퇴 |
| M7 | FAIL | violations=6 | conflict 해소 field 에 adj GU 재생성 (정책 위반 신호) |
| M8 | PASS | 101/79=1.28 | KU 정상 성장 |

JSON 리포트: `bench/silver/japan-travel/p7-rebuild-s3-gu-smoke/m-gate-report.json`

### Plan §4 예시 출력 vs 실측 차이

| 항목 | Plan §4 예시 | 실측 | 시사점 |
|------|--------------|------|--------|
| M1 baseline | 7 | **13** | plan 추정 부정확 — baseline 에 wildcard 제외 13 |
| M3 baseline / target | 16 / 29 | 12 / 31 | 비슷한 결론 (PASS) |
| M5 Δc4, Δc5 | 0, 0 (FAIL) | 0, 2 (weak PASS) | c5 에서 rebound 발견 |

---

## 8. Diagnosis Sub-tasks (S3 FAIL 후속)

S3 FAIL → Stage B-3 진입 보류. 다음 sub-task 로 root cause 추적:

- **SI-P7-S3-DIAG-ATTRACTION** (1순위 후보) — attraction 카테고리에서 entity discovery 후 GU 생성 블로커 추적. M1 1.08× 의 직접 원인.
- **SI-P7-S3-DIAG-T10-T14** — telemetry M5b/M9/M10/M11 추가. T10 sweep 동작 + T14 c4 zero 정밀 진단.
- **SI-P7-S3-DIAG-YIELD** — M6 0.72 (yield 28% 후퇴). dynamic_cap 8/15/20 ablation.
- **SI-P7-S3-DIAG-M7** (신규) — conflict 해소 field 에 adj GU 재생성 6건. 정책 위반 패턴 분석.
- **SI-P7-S3-DIAG-CONNECTIVITY** (신규) — connectivity vacant +1 regression 원인.

순서·범위는 user 협의 후 결정.

---

## 9. Telemetry Task (별도)

`SI-P7-S3-GATE-TEL` — M5b/M9/M10/M11 telemetry 추가. Gate 의 strict 모드 + diagnosis 정밀화에 필요. **Gate 의 선행 조건은 아님** (NA 처리로 통과 가능).
