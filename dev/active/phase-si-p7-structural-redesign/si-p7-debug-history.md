# SI-P7 Structural Redesign — Debug History

> 작성: 2026-04-21 | 최종 업데이트: 2026-04-23
> 구현 착수 후 발견된 이슈·원인·해결·검증 을 시간순 누적.

---

## 템플릿

```markdown
### YYYY-MM-DD — [축/Task ID] 제목 한 줄

**증상**: 관찰된 이상 (로그, 메트릭, 테스트 결과)
**환경**: commit / trial_id / cycle
**원인**: root cause 분석. 가설 → 검증 과정
**해결**: 수정 내용 + 파일/라인
**검증**: L1/L2/L3 결과
**Decision**: (해당 시) D-XXX 기록. baseline v2 반영 필요 여부
```

---

## 엔트리

### 2026-04-23 — [Step B L3 / Step V 삽입] balance-* 단독 원인 단정 보류, 항목별 검증 선결

**증상**: `p7-ab-on` 15c trial 에서 gate FAIL (VP1 3/5, VP2 4/6). KU 82 고정 (c3~c15), GU open 0 고정. `p7-ab-off` 는 PASS (KU 147). 초기 분석에서 "S4-T1 balance-* 제거 + S3 adj 제한 → GU 고갈" 을 single root cause 로 단정 (D-189).

**환경**: commit `2c54001`. Trials `p7-ab-on` / `p7-ab-off` (15c A/B 통합 1쌍).

**원인 (재분석 결과)**: 단정 불가. Step A/B 17개 task 중:
- ✓ 10 (S1-T1~T8, S3-T3/T4/T5/T6, S4-T1) — 코드·skeleton·L1 테스트 반영 확인
- ✗ 의심 1 (S2-T4 β aggressive mode) — `ku_stagnation` trigger 가 cycle 5/10/15 에 발동되었으나 `aggressive_mode_remaining` 시계열 부재, entity_discovery mode 전환 흔적 0
- ~ 7 (S2-T4 α, S2-T5~T8, S3-T1/T2/T7/T8, S4-T2) — 계측 부재로 동작 확증 불가
- N/A 2 (S4-T3/T4) — Step C 대기

"balance-* 단독" 가설(H7) 을 지지할 직접 증거 없음. 가능한 원인 H1~H7 중 H5 (S2-T4 β 연결 실패) 가 가장 강한 ✗ 증거.

**해결 (삽입된 Step)**: Step B 와 Step C 사이에 **Step V (항목 동작 검증)** 삽입.
- V1 Snapshot 재파싱 (비용 0) — 7 개 ~ 의 ✓/✗ 재판정
- V2 계측 보강 (코드, API 비용 0) — 미관찰 신호에 logging/state field 추가
- V3 `p7-ab-minus-{axis}` 8c ablation (의심 축 1~2 개, 사용자 재승인 후)
- V4 root cause 확정 → S5a 착수 여부 결정

**검증 계획**: 각 V 단계 결과를 `v1-signal-audit.md`, `v3-isolation-report.md` 산출물로 기록. D-192 에서 최종 원인 확정.

**Decision**:
- **D-190** — Step V 삽입 확정. L3 gate 단일 원인 단정 금지.
- **D-191** — V3 ablation 설계 (`p7-ab-minus-{axis}`, 8c, baseline 재사용).
- **D-189 잠정 보류** — Step V 결과 후 재판정.
- D-180 갱신 — dev-docs `_CC` suffix 제거. spec 문서(`structural-redesign-tasks_CC.md`) 만 유지.

---

### 2026-04-23 — [Step V / V1 완료] V1 signal audit — ✓11 / ✗2 / ~6, S2-T4 β dead code 가설 (H5c)

**증상 (재판정 대상)**: V1 시작 전 ✓10 / ✗1 (의심) / ~7 / N/A 2 매트릭스. V1 목표는 `~7` 중 snapshot/log 로 관찰 가능한 항목을 ✓/✗ 로 승격.

**환경**: commit `8d794a1`. 도구 `scripts/analyze_p7_ab_signals.py` (cycle mapping 버그 수정 + LOG_KEYWORDS 확장: `growth_stagnation`, `exploration_drought`, `Remodel 트리거`, `axis_tags`, `integration_result`, `conflict_blocklist`, `aggressive_mode`).

**관찰**:
- `growth_stagnation`: on 3회 / off 0회 — S2-T2 ku_stagnation trigger **작동 확인**
- `exploration_drought`: on 2회 / off 2회
- `Remodel 트리거`: on 3회 / off 2회 (자연 발동 양쪽 모두)
- `aggressive` / `aggressive_mode`: on 0회 / off 0회 — S2-T4 β **dead code 가능성**
- `query_rewrite`: 0회 — S2-T4 α **기능 부재 확정**
- `condition_split`, `suppressed`, `adjacency_yield`, `recent_conflict_fields`, `coverage_map`, `integration_result`, `axis_tags`: 전부 0회 (state snapshot 에도 persist 안 됨)

**원인 (V1 완료 시점)**:
- `~7` → `~6` (S2-T2 ✓ 승격)
- `~6` 중 6 항목은 전부 state runtime 에만 존재, `state_io.py:_FILE_MAP` 에 매핑 없음 → snapshot 파일에 기록 자체 불가
- S2-T4 β 가설 H5c: `critique.py:655` 에서 `aggressive_mode_remaining=3` 설정되지만, β mode 효과 경로 (target 확장, source_count≥1 임시 적재, LLM query) 는 **S5a-T11 에 배정되어 있음** → S5a 미구현이라 β 는 **dead code** (no-op)
- `p7-ab-on` FAIL 의 실질 원인: (a) 초반 공격적 budget (c1 defer 20 → c2 소진), (b) GU 고갈, (c) S2-T4 β dead code 로 회복 불가. `balance-*` 단독 아님

**해결 (V2 필요 범위)**:
- V-T4/T5: 6개 ~ 항목을 관찰 가능하게 계측 보강
  - Option A: `_OPTIONAL_LIST_FILES` 에 `si-p7-signals.json` 추가 (recent_conflict_fields, adjacency_yield, coverage_map)
  - Option B: `telemetry/cycles.jsonl` snapshot 에 `integration_result_counts`, `aggressive_mode_remaining`, `condition_split_count` 추가
  - Option C: `critique.py:655`, `plan.py:345`, `integrate.py`, `plan.py (query_rewrite)` 에 `logger.info` 구조화 출력
- 원칙: 로직 변경 금지, 관찰만 추가

**산출물**: `dev/active/phase-si-p7-structural-redesign/v1-signal-audit.md`

**Decision**:
- H5c (S2-T4 β = S5a coupled no-op) **유력 가설** — V2 계측으로 `aggressive_mode_remaining` cycle 시계열 + 효과 경로 call count 확인 후 V-T10 (D-192) 에서 확정
- D-190 유지 강화: `balance-*` 단독 원인 가설 (H7) 은 V1 증거로도 기각에 가까움
- Next: V-T4 계측 범위 사용자 승인 요청

---

### 2026-04-23 — [Step V / V-T7b→T8→T9] V3 ablation 완료, H5c CONFIRMED

**배경**: V-T7b (axis toggle) → V-T8 (p7-ab-minus-s2 8c real API) → V-T9 (isolation report).

**V-T7b 구현**:
- `SIP7AxisToggles` dataclass (config.py) + `OrchestratorConfig.si_p7_toggles`
- `SI_P7_AXIS_OFF=s2` env var 지원
- S2 off wiring: critique (integration_bottleneck + ku_stagnation trigger skip), plan (is_stagnation force False), integrate (`_detect_conflict` Rule 2b/2c/2d skip)
- L1 테스트 8개, 전체 952 passed + 3 skipped 회귀 0

**V-T8 실행 과정**:

1. **최초 실패 (background, abort)**: `SI_P7_AXIS_OFF=s2` 설정 후 run_readiness.py 실행했으나 로그 첫 줄 `si_p7_toggles={'s2_enabled': True, ...}` — s2 off 미적용
2. **Root cause**: `run_readiness.py:58-68` 이 `OrchestratorConfig(...)` 재구성 시 `si_p7_toggles` 파라미터 미전달 → dataclass default (`SIP7AxisToggles()` = all True) 로 덮음
3. **Fix** (run_readiness.py:67, :82): `si_p7_toggles=config.orchestrator.si_p7_toggles` 명시적 전달
4. **재실행 (foreground, 10분 timeout)**: 9분 만에 8c 완주. exit code 1 은 readiness gate FAIL (예상, 8c 로 gate 불가능)
5. **오판 주의**: exit 1 + 출력 30000자 truncation 을 "timeout 중단" 으로 초기 오해 — 사용자가 파일시스템 상태 확인 유도. memory `feedback_foreground_execution.md` 갱신

**V-T9 주요 findings**:

KU count per cycle (state-snapshots 기반):
```
p7-ab-on       : [26, 82, 82, 82, 82, 82, 82, 82, ...]   c3+ 영구 고착 (15c)
p7-ab-minus-s2 : [48, 64, 64, 64, 64, 64, 64, 64]        c3+ 영구 고착 (8c)
p7-ab-off      : [31, 43, 53, 61, 68, 74, 80, 109, ...]  15c 에 걸쳐 점진 확장
```

GU open per cycle (telemetry):
- ab-on c3+ = 0 (고갈), minus-s2 c3+ = 0 (고갈 동일), ab-off = 14~55 유지

**H5c 확정 논거**:
1. ab-on 과 minus-s2 의 c3+ trajectory **완전 일치**: open=0, resolved=37, target=0, adj_gen=0
2. β 가 실제 효과 있었다면 ab-on 의 c5+ stagnation 감지 → KU 회복 패턴이 있었어야. 관찰: 회복 없음
3. minus-s2 에서 β set 경로 skip (aggressive_mode_history=0) 했음에도 ab-on 과 **결과 동일** → β 의 action path 부재 확증
4. V1 증거 (run.log 에 aggressive 키워드 0회) + V2 계측 0건 + V3 trajectory 일치 = 3중 증거

**S2 의 실제 기여 범위**:
- c1-c2 에 condition_split Rule 2b/2c/2d 로 +18 KU 추가 생성 (ab-on 82 vs minus-s2 64 @ c2)
- c3+ 회복/복원력에는 **완전 무관**
- S2-T5~T8 는 "초기 확장 기록 다변화" 기능만 있고 시스템 동역학에 영향 없음

**Decision**:
- **D-192 (예정, V-T10 확정)**: H5c CONFIRMED. β aggressive mode = S5a coupled dead code. SI-P7 Step A/B 의 S2-T4 은 S5a 구현 없이는 무효.
- **H7 약화 재확인**: p7-ab-off 가 balance-* 포함 상태에서 KU 147 까지 확장 → balance-* 제거 단독 원인 아님 (D-190 강화)
- **새 최유력 가설 H6 + S1 조합**: S5a 부재 + S1 defer/queue 과공격성 → c1-c2 초기 burst 로 모든 GU 소진 → c3+ 새 entity 탐색 경로 (S5a) 부재로 영구 고착
- **Next step**: V-T11 에서 S5a 착수 확정 또는 (선택) Trial #2 `p7-ab-minus-s1` 로 S1 과공격성 분리 검증

**관련 산출물**:
- `dev/active/phase-si-p7-structural-redesign/v3-isolation-report.md`
- `bench/silver/japan-travel/p7-ab-minus-s2/` (trial-card.md + 8c 결과)
- `bench/silver/INDEX.md` (p7-v2-smoke + p7-ab-minus-s2 row 추가)

**교훈 (memory 에 반영)**:
- `feedback_foreground_execution.md`: "출력 꼬리 ≠ 프로세스 상태", "exit 1 ≠ timeout", 오판 감지 3-step 체크리스트
- Pre-existing bug 발견: `telemetry.py:92` `cycle_count` 미설정 (top-level cycle=0). V-T6 에서 V2 계측용 cycle_num 은 `current_cycle` 로 전환했으나 top-level 수정은 post-SI-P7 과제

---

### 2026-04-23 — [Step V / V-T6] 1c smoke 성공 + R1 cycle_count offset 확정

**증상**: V-T5 구현 후 `p7-v2-smoke` 1c 실행. `state/si-p7-signals.json` 7개 필드 populate, stdout 에 `[si-p7] condition_split: cycle=1 events=5 reasons={'conditions', 'value_shape'}` emit 확인. 그러나 `telemetry/cycles.jsonl` 의 `si_p7.condition_split_count_cycle` = 0 (기대 5).

**환경**: commit `35c5bea`. trial `bench/silver/japan-travel/p7-v2-smoke`, 1 cycle real API (~250s, KU 13→39, GU 28→35).

**원인 (R1 확정)**:
- `telemetry.py:92` 의 최상위 `"cycle": state.get("cycle_count", 0)` 은 **pre-existing bug** — orchestrator 가 `cycle_count` 를 설정한 적 없음. `p7-ab-on` telemetry 도 모든 cycle `top-cycle=0` 으로 확인
- 내가 추가한 `_build_si_p7_subdict` 와 `critique.py:660` 도 동일하게 `cycle_count` 사용 → event 는 `current_cycle` (=1) 로 stamp, telemetry 는 `cycle_count` (=0) 로 count → 매칭 실패
- integrate.py / plan.py 등 다른 emit 지점은 `current_cycle` 을 이미 사용 → 정답 필드는 `current_cycle`

**해결**:
- `src/obs/telemetry.py:_build_si_p7_subdict` : `cycle_num = int(state.get("current_cycle", state.get("cycle_count", 0)))`
- `src/nodes/critique.py:660` : 동일 패턴
- `tests/test_si_p7_v2_instrumentation.py` : test fixture 에 `current_cycle` 도 주입 (기존 `cycle_count` 유지하여 fallback 검증)

**검증**:
- 수정 후 smoke state 를 load → `_build_si_p7_subdict(state_with_current_cycle=1)` 호출 시 `condition_split_count_cycle=5`, `suppress_count_cycle=3`, `integration_result_cycle` populate 확인 (smoke 재실행 없이 fix 검증)
- 전체 944 passed, 3 skipped 유지 (회귀 0)
- 기존 `telemetry.py:92` 최상위 `cycle_count` 버그는 V-T5 scope 밖 — **별도 후속 과제 (post-SI-P7)**

**V-T6 Acceptance 최종 매트릭스**:
- ✅ `si-p7-signals.json` 존재 (state/ + cycle-1-snapshot/ 양쪽)
- ✅ non-empty 필드 7개 (임계 ≥2 달성)
- ✅ telemetry `si_p7` 8 sub-field 정상 (fix 후)
- ✅ `[si-p7]` log 2종 emit (condition_split, suppress)
- ✅ 전체 테스트 944 pass, 회귀 0

**H5c 1차 판단**: c1 에서 `aggressive_mode_remaining=0`, `growth_stagnation=0` → c1 에서 stagnation 이 자연 발동하지 않는 것이 정상. **H5c 확정은 stagnation 자연 발동 조건 (p7-ab-on 에서 c5 근처) 이 포함된 multi-cycle trial 필요** → V3 ablation (D-191 8c) 으로 이월.

**Decision**:
- **R1 확정**: `cycle_count` 는 orchestrator 설정 미지원 — `current_cycle` 을 source of truth 로 사용. 별도 후속 과제로 orchestrator 가 `cycle_count` 도 sync 하도록 개선 고려
- H5c 확정 경로 = V3 ablation (`p7-ab-minus-{axis}` 8c) 로 결정
- Next: V-T7 ablation 설계 + 비용 추정 + 사용자 승인 요청
