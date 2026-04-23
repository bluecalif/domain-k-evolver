# Session Compact

> Generated: 2026-04-23
> Source: Conversation compaction via /compact-and-go

## Goal

SI-P7 Step A/B L3 trial(`p7-ab-on` FAIL) 결과를 `balance-* 제거` 단독 원인으로 단정하지 말고, Step A/B 각 item의 signal-level 동작 검증을 선결하도록 **Step V(V1~V4 검증 절차)** 를 S4와 S5 사이에 삽입. dev-docs 갱신 → commit → V-T1 snapshot 재파싱 스크립트 작성·실행.

---

## Completed

- [x] L3 trial 신호 세부 분석 — p7-ab-on vs p7-ab-off 비교, 항목별 ✓10 / ✗1 (S2-T4 β) / ~7 / N/A 2 매트릭스 작성
- [x] 검증 plan 작성 — `C:\Users\User\.claude\plans\review-project-status-with-elegant-island.md` (V1~V4 전략, 비용 최적화)
- [x] SI-P7 dev-docs에 **Step V 삽입** (V-T1~V-T11, 11개 task) — `si-p7-tasks.md`
- [x] Plan/context/debug-history 갱신 — D-189(잠정 보류), D-190, D-191 추가
- [x] dev-docs 파일명에서 `_CC` suffix 제거 (D-180 갱신) — 4개 파일 git mv
- [x] project-overall 3개 파일 동기화 — SI-P7 entry + D-171~D-191 decisions
- [x] 외부 참조 업데이트 — session-compact.md, structural-redesign-tasks_CC.md, skill 2개, skill-rules.json
- [x] 커밋 `8d794a1 [si-p7] docs: Step V 삽입 + dev-docs _CC suffix 제거 (D-190/D-191)`
- [x] V-T1 스크립트 초안 작성 — `scripts/analyze_p7_ab_signals.py`
- [x] V-T1 초기 실행 — cycle 매핑 버그 수정 (telemetry cycle=0 문제 → enumerate index 사용)
- [x] LOG_KEYWORDS 확장 (growth_stagnation, exploration_drought, Remodel 트리거, axis_tags, integration_result, conflict_blocklist, aggressive_mode)
- [x] verdict matrix 의 ku_stagnation/aggressive 집계도 확장 키워드 반영

---

## Current State

- **브랜치**: `main` (최신 `8d794a1`)
- **테스트**: 926 passed, 3 skipped
- **Step A/B**: 완료 (commits `a6bc80e`~`2d252f3`)
- **Step V**: 착수 중 (V-T1 스크립트 반복 작성)
- **Step C**: 대기 (Step V 결과 의존)

### Changed Files (uncommitted)
- `scripts/analyze_p7_ab_signals.py` (신규, V-T1 재파싱 스크립트)

### V-T1 초기 실행 결과 요약

**p7-ab-on**:
- cycle 1: KU 26, GU open 26, defer 20 (budget exceeded), adj_gen 6
- cycle 2: KU 82, GU open 2, defer FIFO 소진, adj_gen 2
- cycle 3~15: **완전 정체** (KU 82 고정, GU open 0, adj_gen 0, target_count 0)
- Gap_res=1.0 (c3+), conflict_rate=0 (c3+) — 둘 다 오도 신호 (GU 고갈로 인한)

**p7-ab-off**:
- cycle 1~7: 점진 성장 (KU 31→80, GU open 40→27)
- cycle 8: entity 급증 (KU 80→109, adj_gen 17)
- cycle 15: KU 147, GU open 14, gap_res 0.88 — 건전한 수렴

### 현재 판정 (V-T1 중간)
- ✓ S1-T4/T5/T8 defer mechanism (cycle 1 defer=20, cycle 2 FIFO 소진 확인)
- ✓ S1-T8 defer_reason telemetry (budget_exceeded 기록)
- ✓ S3-T3~T6 adjacent rule engine (adj_gen 생성 확인)
- ✗ S2-T4 β aggressive_mode_remaining (기본 키워드 `aggressive` 0건 — 확장 키워드 결과 미확인)
- ✗ S2-T4 α query_rewrite rx (0건)
- ~ S2-T1 integration_result_dist (state 필드 부재)
- ~ S2-T2 ku_stagnation (확장 키워드 `growth_stagnation`·`exploration_drought` 로 재검증 예정)
- ~ S2-T5~T8 condition_split (로그 0건)
- ~ S3-T1 suppress, S3-T2/T8 blocklist, S3-T7 yield (전부 state 필드 부재)
- ~ S4-T2 coverage_map.deficit_score (state 필드 부재)

### 핵심 구조 발견
**state-snapshots/cycle-*-snapshot/** 은 `conflict-ledger/domain-skeleton/external-anchor/gap-map/knowledge-units/metrics/policies` 7개 JSON으로 분리 저장. **단일 `state.json`은 없음**. Step A/B 신규 state 필드(aggressive_mode_remaining, adjacency_yield, recent_conflict_fields, coverage_map, ku_stagnation_signals, integration_result_dist)는 **어떤 스냅샷 파일에도 persist되지 않음**. telemetry/cycles.jsonl에는 `deferred_targets`, `defer_reason`, `cycle_trace` 만 기록.

→ **V2 계측 보강 거의 필연**. state_io.py 혹은 telemetry emit 에 이 필드들 추가 필요.

---

## Remaining / TODO

### 즉시 (V-T1 마무리)
- [ ] 확장 키워드 반영된 스크립트 재실행 → `growth_stagnation`·`exploration_drought`·`Remodel 트리거` 등이 검증 매트릭스에 반영되는지 확인
- [ ] **V-T3**: `dev/active/phase-si-p7-structural-redesign/v1-signal-audit.md` 작성 (스크립트 출력 + ✓/✗/~ 최종 재판정 + V2 계측 필요 항목 식별)
- [ ] V-T1 스크립트 커밋 (`[si-p7] V-T1: signal re-parse script + v1-signal-audit.md`)

### V2 (V1 결과에 따라)
- [ ] V-T4 계측 필드 설계 — 최소한 `aggressive_mode_remaining`, `adjacency_yield`, `recent_conflict_fields`, `coverage_map`, `ku_stagnation_signals`, `integration_result_dist` 를 state snapshot 또는 telemetry 에 emit
- [ ] V-T5 계측 코드 구현 + L1 테스트
- [ ] V-T6 1-cycle smoke (`--trial-id p7-v2-smoke`) 로 신호 발생 확인

### V3 (V2 후, 사용자 재승인)
- [ ] V-T7 `p7-ab-minus-{axis}` 8c ablation 조합·비용 추정 + 승인 요청
- [ ] V-T8 실행 (1~2 쌍)
- [ ] V-T9 `v3-isolation-report.md` 작성

### V4
- [ ] V-T10 root cause 확정 (D-192 기록)
- [ ] V-T11 S5a 착수 / Step A/B 수정 / 양자 병행 중 택 1

---

## Key Decisions

- **D-189 잠정 보류**: Step V 결과 전까지 "S5a = critical path" 가정 사용 금지.
- **D-190**: Step V 삽입 — Step A/B 각 item signal-level 검증 선결. balance-* 단독 root cause 단정 금지. 현재 ✓10 / ✗1 / ~7 / N/A 2 중 7개 미확증이 계측 부재로 확증 불가하므로.
- **D-191**: V3 ablation = `p7-ab-minus-{axis}` **8c** (cycle 15→8, GU 고갈 재현 충분선), baseline 재사용 (`p7-ab-on` 상한 / `p7-ab-off` 하한), 의심 축 1~2 개만. 비용 ~800–1,500 LLM call. 실행 전 사용자 재승인 필수.
- **D-180 갱신 (2026-04-23)**: dev-docs `_CC` suffix 제거 (`si-p7-{plan,context,tasks,debug-history}.md`). spec 문서(`docs/structural-redesign-tasks_CC.md`) 만 `_CC` 유지.
- **V3 비용 최적화 원칙**: gate pass 가 아닌 **신호 분리**가 목적이므로 15c 불필요. cycle 축소 + ablation 방식 + baseline 재사용 으로 원안 대비 ~10% 비용.

---

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 진입점 — 읽기 우선순위
1. `dev/active/phase-si-p7-structural-redesign/si-p7-plan.md` — Step A/B/V/C 범위 + D-181~D-191
2. `dev/active/phase-si-p7-structural-redesign/si-p7-tasks.md` — V-T1~V-T11 checklist
3. `dev/active/phase-si-p7-structural-redesign/si-p7-debug-history.md` — 2026-04-23 엔트리 (Step V 삽입 배경)
4. `scripts/analyze_p7_ab_signals.py` — V-T1 스크립트 (iteration 중)
5. `bench/silver/japan-travel/p7-ab-on/` — trial 데이터
6. `C:\Users\User\.claude\plans\review-project-status-with-elegant-island.md` — 전체 검증 plan

### 검증 매트릭스 (V-T1 중간 기준)
- ✓ 10개: S1-T1~T8, S3-T3/T4/T5/T6, S4-T1
- ✗ 의심 1개: S2-T4 β (stagnation trigger 후 aggressive mode 흔적 없음)
- ~ 7개: S2-T4 α, S2-T5~T8, S3-T1/T2/T7/T8, S4-T2 (계측 부재)
- N/A 2개: S4-T3, S4-T4 (Step C 대기)

### 스크립트 실행
```bash
PYTHONUTF8=1 python scripts/analyze_p7_ab_signals.py
PYTHONUTF8=1 python scripts/analyze_p7_ab_signals.py --json-out /tmp/signals.json
PYTHONUTF8=1 python scripts/analyze_p7_ab_signals.py --trial p7-ab-on
```

### 제약·주의
- **D-187**: mock 금지 — fixture real snapshot 만, function stub 금지
- **D-34**: real-API-first — L3 trial 실 API 필수
- **feedback_api_cost_caution**: V3 실행 전 비용 사전 확인·승인
- **feedback_root_cause_extensive_view**: root cause 는 샘플이 아닌 extensive view (전체 데이터 3-카테고리 분리) 로 확정
- dev-docs 파일명: `_CC` 없이 (D-180 갱신)

---

## Next Action

1. `scripts/analyze_p7_ab_signals.py` 재실행 (`PYTHONUTF8=1 python scripts/analyze_p7_ab_signals.py`) — 확장 키워드 (`growth_stagnation`, `exploration_drought`, `Remodel 트리거`, `axis_tags`, `integration_result`, `conflict_blocklist`, `aggressive_mode`) 집계 확인. 특히 `ku_stagnation_in_log` 와 `aggressive_in_log` 가 확장 키워드 반영으로 0 에서 변화하는지 체크.
2. 스크립트 출력을 `dev/active/phase-si-p7-structural-redesign/v1-signal-audit.md` 로 정리 (V-T3):
   - [A] Cycle × 신호 표 (p7-ab-on / p7-ab-off)
   - [B] run.log keyword 빈도 표
   - [C] Step A/B 항목별 V1 재판정 (✓/✗/~)
   - [D] V2 계측이 필요한 ~ 항목 목록 + state.py/telemetry emit 위치 제안
3. V-T1/V-T3 완료 후 커밋: `[si-p7] V-T1/V-T3: signal re-parse + v1-signal-audit`.
4. 커밋 후 사용자에게 V2 계측 범위 확인 요청 (어떤 필드를 state snapshot 에 emit 할지 우선순위 결정).
