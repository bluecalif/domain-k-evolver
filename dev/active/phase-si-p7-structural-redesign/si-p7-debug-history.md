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
