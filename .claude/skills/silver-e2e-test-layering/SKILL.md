---
name: silver-e2e-test-layering
description: Domain-K-Evolver 테스트 3-layer (L1 단위 / L2 single-cycle e2e / L3 15c A/B trial) 정의 + mock 금지 원칙 + trial-id 규약. `scripts/run_readiness.py --cycles 1 --trial-id si-p7-<task-id>-smoke` (L2) 와 `bench/silver/japan-travel/p7-<축>-on|off/` (L3) 을 표준화한다. D-34 (real-API-first) + D-187 (mock 금지) + memory rule `feedback_test_real_path` 위배 없이 축별 효과 측정. "e2e 테스트", "mock 금지", "trial-id", "real API first", "L1/L2/L3", "single-cycle e2e", "task checkpoint 테스트", "real snapshot fixture", "15c A/B trial", "축 완료 판정", "Gate 공식 판정", "si-p7-*-smoke", "p7-*-on/off" 같은 요청이 나오면 반드시 사용한다. 단순 pytest 단위 테스트 추가나 Bronze 레거시 테스트에는 사용하지 않는다.
---

# Silver E2E Test Layering

## 목적

Silver 세대 구조 리팩터 (특히 SI-P7) 의 **중간 단계별 검증** 을 누락/오염 없이 수행하기 위한 3-layer 테스트 전략. mock 에 의존한 테스트는 운영 경로 버그를 놓친다 (P3 교훈, memory: `feedback_test_real_path`). 이 skill 은 실 실행 경로를 검증하는 결정론적 레이어 정의를 제공한다.

단일 진실 소스: **`docs/structural-redesign-tasks_CC.md` v2 §검증 방식** + D-34 (real-API-first) + D-187 (mock 금지).

## 언제 쓰는가

- SI-P7 의 각 축 task 구현 중 / 직후 검증 계획 수립 시
- L2 single-cycle e2e 실행 시 (`scripts/run_readiness.py --cycles 1 --trial-id si-p7-<task-id>-smoke`)
- L3 15c A/B trial 구성 시 (`bench/silver/japan-travel/p7-<축>-on|off/`)
- PR 에 테스트 레이어 배정 (L1 자동 / L2 수동 / L3 Gate) 결정 시
- "이 task 의 효과를 어떻게 검증하지" 질문이 나올 때
- fixture 작성 시 real snapshot 방침 확인 필요할 때
- Gate 판정 근거가 L1 또는 L2 인지 논쟁이 생길 때 (정답: **L3 만 Gate 공식**)

## 언제 쓰지 않는가

- Bronze 레거시 테스트 (`tests/test_bronze_*.py` 계열, mock 혼재 허용)
- 단발 pytest 단위 테스트 추가 (real snapshot 불필요한 pure logic)
- Readiness gate 전체 판정 — `silver-phase-gate-check` 가 담당
- 벤치 trial 디렉토리 생성 자체 — `silver-trial-scaffold` 가 담당

---

## 3-Layer 정의

| 레이어 | 실행 시점 | 목적 | Gate 근거 | mock 허용 여부 |
|---|---|---|---|---|
| **L1 단위** | task 완료 즉시 (PR 내) | 단위 함수 로직 (숫자, 조건 분기, state transition) | ❌ | fixture 는 **real snapshot** 만. function stub/mock **금지** |
| **L2 single-cycle e2e** | task 묶음 완료 시 (수동 trigger) | 해당 task 가 파이프라인에서 의도한 **state 변화** 를 실제로 유발하는지 | ❌ | **real API 필수** (D-34) |
| **L3 15c A/B trial** | 축 전체 완료 시 | before/after metric 비교로 **축별 효과 판정** | ✅ **공식 Gate** | **real API 필수** |

### 원칙 (D-187)

1. **mock 금지** — production 함수는 직접 호출. fixture 는 real snapshot (`bench/*/state/*.json`) 만 사용.
2. **real API first (D-34)** — L2/L3 는 실제 LLM + search provider 호출. 합성 E2E 만으로 Gate 판정 불가.
3. **L3 가 유일한 Gate 근거** — L1 은 회귀 방지, L2 는 논리 확인. 공식 Gate 통과 선언은 L3 15c A/B 결과만.

---

## trial-id 규약

### L2 smoke (single-cycle e2e)

```
si-p7-<task-id>-smoke

  task-id  S<축숫자>-T<번호> 의 lowercase
           예: s1-t4, s2-t6, s3-t7, s5a-t6, s5a-t11
```

**예시**:
- `si-p7-s1-t4-smoke` — S1 defer/queue L2
- `si-p7-s2-t6-smoke` — S2 condition_split 재정의 L2
- `si-p7-s5a-t11-smoke` — S5a β aggressive mode override L2

**실행 명령**:

```bash
PYTHONUTF8=1 python scripts/run_readiness.py \
  --bench-root bench/silver/japan-travel/si-p7-<task-id>-smoke \
  --cycles 1
```

### L3 A/B trial

```
p7-<축>-on
p7-<축>-off

  축  s1, s2, s3, s4, s5a, s5b
```

**예시**:
- `bench/silver/japan-travel/p7-s1-on/` vs `p7-s1-off/`
- `bench/silver/japan-travel/p7-s5a-on/` vs `p7-s5a-off/`

**실행 명령** (각각):

```bash
PYTHONUTF8=1 python scripts/run_readiness.py \
  --bench-root bench/silver/japan-travel/p7-<축>-<on|off> \
  --cycles 15
```

### 오용 패턴 (거부)

| 패턴 | 문제 | 교정 |
|---|---|---|
| `si-p7-smoke` | task-id 누락, 여러 task 섞임 | `si-p7-s1-t4-smoke` 로 task 단위 |
| `p7-s1-test` | on/off 구분 누락 | `p7-s1-on` / `p7-s1-off` 쌍으로 |
| `p7-s1-on-run2` | 축 A/B 에 run2 혼입 | L3 재실행은 `p7-s1-on-run2` 는 허용 (통계 표본), 그러나 Gate 판정은 **최초 pair** 만 |
| `si-p7-s1-t4-smoke` 에 3 cycle 돌리기 | smoke 는 1c 원칙 (D-34 비용) | `--cycles 1` 고정. 3c 필요하면 trial-id 를 `si-p7-s1-t4-3c` 로 분리 |

---

## L1 원칙 (fixture = real snapshot)

### 허용
```python
def test_detect_value_shape_diff():
    state = load_real_snapshot("bench/japan-travel/state/cycle-5.json")
    result = _detect_value_shape_diff(state.ku_list[0], state.ku_list[1])
    assert result.split is True
```

### 금지
```python
def test_detect_value_shape_diff_bad():
    mock_ku_a = Mock(spec=KU)  # ❌ function stub 금지
    mock_ku_a.axis_tags = ["peak"]
    # ...
    result = _detect_value_shape_diff(mock_ku_a, mock_ku_b)  # ❌ mock 으로 경로 건너뜀
```

이유: mock 이면 `_detect_value_shape_diff` 내부의 진짜 분기/검증이 가려진다. P3 에서 mock 테스트는 green 이었으나 운영에서 0 claims 가 나온 사례 (D-120 REVOKED).

---

## L2 checkpoint 패턴

L2 는 task 완료 직후 "**실제 파이프라인에서 state 가 의도대로 변하는가**" 를 1 cycle 로 확인.

SI-P7 축별 L2 checkpoint 는 `docs/structural-redesign-tasks_CC.md` v2 §검증 방식 의 **Task 단위 Checkpoint 테이블** 참조. 예시:

| Task | L1 (단위) | L2 (1c e2e) | 관찰할 artifact |
|---|---|---|---|
| S1-T4 | `_calc_execution_queue()` defer 반환 | budget 낮춰 defer 유발 | `state.deferred_targets` ≠ 0, `metrics.deferred_count > 0` |
| S2-T6 | `_detect_value_shape_diff()` unit | 조건값 claim 주입 | `integration_result` 에 `condition_split` 출현 |
| S5a-T6 | candidate 적재 + similarity pre-filter | `--cycles 3` | `state.entity_candidates` 크기 증가 |
| S5a-T11 | β mode parameter override | β 강제 trigger + `--cycles 3` | target 수 3-5 / source_count≥1 적재 |

**L2 실행 1회 규칙**: 각 task 의 L2 는 고유 `trial_id` 로 **1회만 실행** (memory: `feedback_api_cost_caution`). artifact 재사용, 중복 실행 금지.

### 관찰 artifact 는 반드시 persist 된 필드로

"관찰할 artifact" 컬럼의 필드는 **snapshot JSON 또는 telemetry 에 실제 기록되는 필드** 여야 한다. 런타임 내부 state 변수에만 존재하고 emit 되지 않는 필드는 L2 checkpoint 로 **불가** (재파싱 수단 없음).

emit 되지 않는 필드가 checkpoint 에 포함되면 → **L3 launch 전에 계측 선결 요건 (아래 섹션) 을 먼저 이행**.

---

## 계측 선결 요건 (Instrumentation Prerequisite)

**D-190 교훈 (2026-04-23)**: SI-P7 Step A/B L3 trial 은 `aggressive_mode_remaining`, `adjacency_yield`, `recent_conflict_fields`, `coverage_map`, `ku_stagnation_signals`, `integration_result_dist` 등 축 신규 state 필드가 **어떤 snapshot 파일에도 persist 되지 않아** item-level 검증 불능 상태에서 launch → FAIL 결과가 나왔을 때 item 별 root cause 추적이 불가능했고, `balance-*` 제거 단독 원인으로 오귀인할 뻔했다.

### 규칙

**L3 15c trial launch 전, 축이 새로 도입하는 state 필드 / behavior signal 은 모두 아래 두 경로 중 하나에 emit 되어야 한다**:

1. **state snapshot**: `bench/.../state-snapshots/cycle-N-snapshot/<part>.json` 에 직렬화
2. **telemetry**: `bench/.../telemetry/cycles.jsonl` 에 cycle 별 기록 (또는 `run.log` 에 구조화된 키워드)

### 선결 체크리스트 (L3 launch 직전)

- [ ] 축 task 별 "관찰할 artifact" 필드가 실제 snapshot 또는 telemetry 에 기록되는지 **1-cycle smoke 로 확인**
- [ ] state 에만 존재하고 persist 되지 않는 필드가 있으면 **state_io.py 또는 telemetry emit 에 추가** (미이행 시 L3 금지)
- [ ] 로그 기반 signal (keyword in `run.log`) 은 로그 출력 문자열을 grep 가능하도록 확정 (변경 시 재파싱 스크립트 깨짐)
- [ ] signal 재파싱 스크립트 (예: `scripts/analyze_p7_ab_signals.py`) 는 **L3 launch 전** 에 초안이 존재해야 함

### 계측 부재 상태 L3 의 결과물

- `gap_resolution=1.0`, `conflict_rate=0` 같은 수렴 지표가 **GU 고갈** 로 인한 misleading PASS 처럼 보이는 경우 식별 불가
- 축 내 어떤 item 이 발현되었고 어떤 item 이 죽었는지 미구분 → 축 전체 on/off 결과만 남음 → 단일 root cause 로 단정할 위험

---

## L3 결과 분석 프로토콜

L3 결과가 FAIL / UNEXPECTED (수렴 너무 빠름, 성장 정체, metric 역전 등) 일 때 **축 단일 원인 단정 금지**. 다음 순서를 따른다:

### Step 1 — Item-level signal 재파싱

축 내 모든 item (S<n>-T<m>) 에 대해 trial 기간 (예: 15 cycle) 동안 **signal 이 실제 발현되었는가** 를 snapshot + telemetry + `run.log` 에서 재파싱.

결과를 3-카테고리로 분류 (memory: `feedback_root_cause_extensive_view` 와 동일 정신):

| 분류 | 의미 | 다음 조치 |
|---|---|---|
| ✓ 발현 확인 | signal 이 기대대로 관찰됨 | 정상 동작 |
| ✗ 발현 실패 (의심) | signal 기록 경로 존재, 값 0/부재 | 구현 버그 후보 |
| ~ 계측 부재 | signal 기록 경로 자체 없음 | **판정 유보** — 계측 보강 → 재실행 |

### Step 2 — 비율 기반 판단

- `~` 가 절반 이상이면 root cause 판정 **중단** → 계측 보강 후 재실행 (예: SI-P7 Step V 삽입 패턴)
- `✗` 가 명확히 식별되면 해당 item 부터 수정, 축 전체 롤백 / 제거 결정 **유보**
- `✓` 만 나오면 그때 축 외부 원인 (설정, 환경, 의도치 않은 side-effect) 조사

### Step 3 — 계측 보강이 필요한 경우 (Step V 패턴)

1. `dev/active/<phase>/` 에 **검증 Step 삽입** (예: Step V between S4/S5)
2. 계측 항목 설계 → state_io / telemetry emit 구현 → L1 테스트
3. 1-cycle smoke (`--trial-id <phase>-v2-smoke`) 로 신호 발생 확인
4. 그 다음 축별 ablation trial (`p7-<phase>-minus-<axis>` 8c 등, cycle 축소 + baseline 재사용 으로 비용 최적화, memory: `feedback_api_cost_caution`)
5. 사용자 재승인 후 실행

### Step 4 — Decision 기록

root cause 확정 시 `debug-history.md` 에 `D-NNN` 으로 기록, `extensive view` 3-카테고리 수치 명시.

---

---

## L3 A/B 판정 구조

```
bench/silver/japan-travel/
├── p7-<축>-on/       # 해당 축 변경 적용
│   ├── trial-card.md       (가설: 해당 축 효과)
│   ├── config.snapshot.json
│   ├── state/
│   ├── trajectory/
│   ├── telemetry/
│   └── readiness-report.md (Gate 판정)
└── p7-<축>-off/      # baseline (변경 없음)
    └── (동일 구조)
```

### 판정 절차

1. `silver-trial-scaffold` skill 로 on/off 각각 trial-card 작성 — **가설이 `on` 쪽에만 있어야** (off 는 baseline)
2. 양쪽 15c 실행
3. `silver-phase-gate-check` skill 로 양쪽 readiness-report 작성
4. **축별 고유 지표 diff**:
   - S1: defer_count distribution, 실행 GU 수, API 호출 수
   - S2: `added / updated / condition_split / conflict_hold` 분포
   - S3: `adjacency_yield[rule_id]`, conflict field 재생성 = 0 confirm
   - S4: category Gini, virtual entity 수 = 0 confirm
   - S5a: validated entity 승격 수, 신규 파생 KU 수, candidate stale/purge 비율, pre-filter 차단 수
   - S5b: auto-alias / duplicate KU / fragmentation_report 추이
5. **VP1/VP2/VP3 + 축별 지표 조합** 으로 PASS 판정

---

## Anti-Patterns

| 패턴 | 문제 | 교정 |
|---|---|---|
| L2 를 합성 fixture + mock API 로 | D-34 + D-187 위반. 운영 경로 미검증. | real API 호출, real snapshot fixture |
| L1 만 통과했으니 Gate 통과 선언 | L3 가 유일한 Gate 근거 (D-187) | 축 완료 후 L3 15c A/B 필수 |
| 같은 trial_id 로 L2 smoke 재실행 (artifact overwrite) | 재현성 손실, 비용 중복 | run2 필요 시 trial-id 에 `-run2` |
| `p7-s1-on` 만 만들고 `p7-s1-off` 생략 | A/B 비교 불가, before/after 판정 무효 | 반드시 pair 로 |
| smoke 에 `--cycles 3` 이상 | smoke 는 1c 원칙, 비용 증가 | 3c 필요 시 trial-id 분리 (`si-p7-s1-t4-3c`) |
| L3 의 on/off 사이에 config 외 다른 코드 diff | A/B independence 위반, 축 효과 분리 불가 | git 분기 관리 — off 는 이전 `main` HEAD, on 은 feature branch |
| L2 가 L3 의 대체로 취급 | Gate 공식 근거 혼동, 15c 재현성 손실 | L2 는 **구현 논리 확인**, L3 는 **효과 판정** — 역할 분리 |
| function stub 을 L1 에 사용 (speedup 핑계) | 운영 경로 미검증 | fixture real snapshot 로 대체 — 느리면 snapshot 축소 |
| 축 신규 state 필드 emit 없이 L3 launch | L3 FAIL 시 item-level root cause 추적 불가, 축 단일 원인 오귀인 | **계측 선결 요건** 이행 — snapshot/telemetry emit 확인 후 launch (D-190) |
| L3 FAIL 을 축 단일 원인으로 단정 (item 재파싱 없이) | 계측 부재 item 과 구현 실패 item 혼동, root cause 오귀인 | **L3 결과 분석 프로토콜** 적용 — item-level signal 재파싱 → ✓/✗/~ 분류 후 판정 |
| `gap_resolution=1.0` / `conflict_rate=0` 을 수렴 PASS 로 해석 | GU 고갈에 의한 misleading 지표일 수 있음 | KU 성장 정체 + GU open 0 동반 여부 확인, item signal 재파싱 병행 |
| 계측 부재 (`~`) 비율 높은 상태로 root cause 확정 | 판정 근거 부족 | Step V 패턴 (검증 Step 삽입 → 계측 보강 → 재실행) 먼저 |

---

## 관련 skill

- **`silver-structural-redesign`** — SI-P7 축별 task ID 와 checkpoint 매핑 (본 skill 과 쌍)
- **`silver-trial-scaffold`** — L3 A/B trial 디렉토리 + trial-card (Step 3 의 선행)
- **`silver-phase-gate-check`** — readiness-report + VP1/VP2/VP3 판정 (L3 결과 소비)
- **`evolver-framework`** — 5대 불변원칙 guardrail (L1 에서 함께 확인)

---

## 관련 문서

1. **`docs/structural-redesign-tasks_CC.md` v2 §검증 방식** — Task 단위 checkpoint 테이블 포함
2. D-34 — Real API First (Tech Decisions)
3. D-187 — 테스트 3-layer + mock 금지 (본 skill 핵심)
4. D-189/D-190/D-191 — Step V 삽입 배경 (계측 부재로 인한 root cause 오귀인 회피). `dev/active/phase-si-p7-structural-redesign/si-p7-debug-history.md` 2026-04-23 엔트리
5. Memory `feedback_test_real_path.md` — P3 교훈
6. Memory `feedback_api_cost_caution.md` — L2 1회 실행 규칙
7. Memory `feedback_root_cause_extensive_view.md` — 3-카테고리 분류 원칙 (L3 결과 분석 프로토콜 Step 1 에서 사용)
8. Memory `feedback_l3_trial_item_signal_audit.md` — L3 FAIL 시 item-level 재파싱 선결 규칙
