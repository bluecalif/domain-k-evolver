# Session Compact

> Generated: 2026-04-23 23:55
> Source: Conversation compaction via /compact-and-go

## Goal

SI-P7 c3+ KU 고착의 Primary Introducer 축을 **축별 순차 회귀 실험**으로 isolate → 5-trial 완료, v5 report 작성, worktree cleanup, **S1 GU plunge 원인 조사** 까지 수행. 남은 일: v5 report 에 S1 plunge 발견 보충 + 후속 action (S2-T5~T8 내부 세부 원인 확정).

---

## Completed (이번 세션)

### 5-Trial Sequential Ablation 완주
- [x] **Trial 3 (S3 complete, commit `2d252f3`) 5c** — 1차 시도 Tavily 433 rate limit 오염 → 재실행 → 정상 데이터 확보: KU 40,59,61,61,61 (c3+ 완전 no-op, wall c4=1.3s c5=1.5s)
- [x] **Trial 4 (S4 complete, commit `2631c38`) 5c** — OpenAI 502 자동 복구, KU 50,70,73,77,78 (c4/c5 slow but continuous: 109s, 48s)
- [x] 5-trial cycles.jsonl + trajectory.json 파싱 → KU/GU_open/GU_total/target/adj_gen/wall_clock 전체 비교표
- [x] Worktree × 5 (pre-a/s1/s2/s3/s4) cleanup — 최종 `main` 1개만

### S2 commit diff 분석 (f3a0be0 vs 4e5988c)
- [x] `src/nodes/integrate.py`, `plan.py`, `critique.py` diff 읽기 → 4 subtask 기능 확정
  - S2-T1: `integration_result_dist` 제어입력 (conv_rate<0.3 처방)
  - S2-T2: `ku_stagnation_signals` 3종 trigger
  - S2-T4 α+β: stagnation 시 query 재작성 + aggressive_mode_remaining=3
  - **S2-T5~T8: condition_split 강화 (구조 차이 T6, condition_axes 강제 T7, axis_tags T8)**

### v5 report 작성
- [x] `dev/active/phase-si-p7-structural-redesign/v5-sequential-ablation-report.md` — 5-trial 표, 축 역할 분류(S1 무해 / S2 Primary / S3 Aggravator / S4 Mitigator), S2 내부 subtask 분석, 후속 action 2 선택지

### S1 GU Generation Plunge 원인 조사 (사용자 추가 요청)
- [x] Pre-a vs S1 cycle-by-cycle 비교: **Pre-a 모든 cycle normal mode / S1 c2~c5 jump mode 진입**
- [x] State-snapshot 에서 resolved GU 의 trigger 분포 분석:
  - c3 resolved: ? 0, E:cat 1, A:adj 9 → adj source 빈곤 → adj_gen=1
  - c5 resolved: ? 0, E:cat 0, A:adj 11 → **전부 A:adj (non-source)** → adj_gen=0
- [x] **메커니즘 확정**: **1단계 adj chain 억제** (A:adj GU resolved 되어도 추가 adj 생성 안 함) + **S1 sort 제거 + deferred FIFO 가 만든 A:adj batch clustering** → 특정 cycle 에 adj_gen plunge
- [x] **v5 report 에 §8 Appendix B 추가** (S1 adj_gen Oscillation 분석) — 증상/증거/메커니즘/KU 영향/S2-S3 결합 위험/완화 옵션 4개

---

## Current State

- **브랜치**: `main` @ `257e2c7`
- **Uncommitted**: `docs/session-compact.md` (본 파일), `bash.exe.stackdump`, 신규 `v5-sequential-ablation-report.md`, 신규 5개 bench trial 디렉토리 (p7-seq-*), `dev/active/phase-si-p7-structural-redesign/v4-hypothesis-matrix.md` (이전 세션)
- **Worktrees**: 모두 제거 완료 (main 1개만)
- **Bench trials 완료**: `p7-seq-{pre-a,s1,s2,s3,s4}` 5개 (각 5c, readiness-report + telemetry + state-snapshots 완비)
- **비용**: 이번 세션 ~$1.2 (Trial 3 첫시도 오염 + 재실행 + Trial 4). 누적 ~$2.0 (5-trial 전체)
- **Primary Introducer 확정**: **S2** (condition_split 확장 + ku_stagnation + β)
- **S2 내부 유력 primary subtask**: **S2-T5~T8** (특히 T6/T7/T8 의 condition_split 강제 트리거)

### Changed Files (이번 세션)
- `dev/active/phase-si-p7-structural-redesign/v5-sequential-ablation-report.md` — NEW, 작성 완료
- `bench/silver/japan-travel/p7-seq-s3/` — NEW (재실행 최종본)
- `bench/silver/japan-travel/p7-seq-s4/` — NEW
- `docs/session-compact.md` — 본 compact 로 overwrite

---

## Remaining / TODO

### 즉시 (다음 세션 첫 작업)

- [ ] 사용자에게 Action A (S2-T5~T8 토글 wiring + smoke) vs B (추가 ablation trial) 최종 선택 질의 → 권장 A 먼저

### 후속 선택지 (v5 report §6 에 명시)

**A. S2-T5~T8 코드 토글 wiring + 1c smoke (API 비용 0)**
- `src/nodes/integrate.py::_detect_conflict` 의 T6 (값 구조 차이), T7 (condition_axes 강제), T8 (axis_tags) 각각 opt-out 토글
- config 에 `t6_struct_split`, `t7_axes_forced_split`, `t8_axis_tags_split` 개별 on/off
- 단위 smoke (1c `run_readiness.py --cycles 1`) 로 KU 폭증이 어느 rule 에서 오는지 narrowing
- 확정되면 해당 rule 보수화 (value 길이 임계, evidence count 하한 등)

**B. S2 내부 추가 ablation trial (API 비용 ~$0.40)**
- `87d7603` (S2-T4 직후, T5~T8 직전) 을 6번째 worktree 체크아웃 → 5c trial
- c1 KU +59 폭증 재현 유무로 T5~T8 vs T1~T4 기여도 확정

**권장**: A 먼저. 코드 분석으로 narrowing 후 필요하면 B.

### 추가 제안 (사용자 승인 필요)

- [ ] **S3 snapshot trigger 분포 검증** — S3 c3+ no-op 이 S1 과 **동일한 batch clustering 메커니즘** 에서 오는지 확인 (state-snapshots/cycle-3-snapshot/gap-map.json 의 trigger 분포). 확인만이면 API 비용 0

### 최종 정리

- [ ] Git commit — v5 report + bench trials + session-compact
- [ ] project-overall 업데이트 (D-194, D-195, D-196 추가)

---

## Key Decisions

### 본 세션 신규

- **D-194**: Primary Introducer = **S2** (condition_split + ku_stagnation + β). Secondary Aggravator = S3. Mitigator = S4. 기준 = 5-trial Sequential Ablation (5c each) 의 KU/GU/target/adj_gen delta 비교
- **D-195**: S2 내부 primary subtask 유력 후보 = **S2-T5~T8 (condition_split 강화)**. c1 KU +59 폭증을 기존 conflict/update → 강제 condition_split 재분류로 설명. 확정은 Action A (코드 토글) 또는 B (추가 trial)
- **D-196 (신규)**: S1 adj_gen oscillation (c3 plunge, c5 zero) 원인 = **1단계 adj chain 억제 정책** + **S1 sort 제거 + deferred FIFO 가 만든 A:adj batch clustering**. 증거: c3/c5 에 resolved GU 가 A:adj trigger 위주 → adj source 빈곤. S1 단독 KU 성장 영향 없음 (resolved_count 11-15 유지), 하지만 S2/S3 GU 억제 환경에선 plunge cycle 이 pool 고갈을 가속 가능

### 기존 (유지)

- D-187 mock 금지 / D-34 real API first
- feedback_foreground_execution: Monitor tight filter 로 event stream
- feedback_option_count: 선택지 2~3개
- feedback_extensive_problem_solving: 하지만 매트릭스가 과도함, sequential ablation 이 더 단순

---

## Context

다음 세션에서는 답변에 **한국어**를 사용하세요.

### 진입점 — 읽기 우선순위

1. **이 파일** (session-compact.md) — 반드시 먼저
2. `dev/active/phase-si-p7-structural-redesign/v5-sequential-ablation-report.md` — 5-trial 확정 리포트
3. `bench/silver/japan-travel/p7-seq-*/telemetry/cycles.jsonl` — 원본 데이터
4. `bench/silver/japan-travel/p7-seq-s1/state-snapshots/cycle-N-snapshot/gap-map.json` — trigger 분포 원본 (S3 검증 시 활용)

### 5-Trial 데이터 핵심 (c1~c5)

```
=== KU total ===
pre-a  | 24  41  53  62  72    (건강)
s1     | 46  54  64  78  88    (건강)
s2     | 72  76  81  86  88    (c1 극폭증, c3+ 둔화)
s3     | 40  59  61  61  61    (c3+ 완전 no-op)
s4     | 50  70  73  77  78    (부분 회복)

=== GU total ===
pre-a  | 55  67  75  82  86    (+31)
s1     | 45  62  64  79  79    (+34, c3/c5 plunge)
s2     | 39  47  47  49  49    (+10, 급감)
s3     | 35  39  39  39  39    (+4, 최저)
s4     | 35  45  45  46  46    (+11)

=== adj_gen ===
pre-a  |  6   9   8   7   4    (consistent)
s1     |  6  15   1  15   0    (oscillation, c3/c5 plunge)
s2     |  6   8   0   2   0
s3     |  6   4   0   0   0
s4     |  6  10   0   1   0
```

### S1 plunge resolved trigger 분포 (중요 발견)

```
cycle | resolved delta by trigger           | adj_gen
------|-------------------------------------|--------
c1    | ?:+20                               |   6
c2    | E:cat:+8                            |  15
c3    | ?:+0, E:cat:+1, A:adj:+9            |   1  ← plunge
c4    | ?:+4, E:cat:+4, A:adj:+7            |  15
c5    | ?:+0, E:cat:+0, A:adj:+11           |   0  ← plunge
```

### Reference Commits

| Step | commit | 설명 |
|---|---|---|
| Pre-Step-A | `2ebd435` | baseline |
| S1 complete | `4e5988c` | defer/queue, sort 제거, FIFO |
| S2 complete | `f3a0be0` | condition_split 강화 + ku_stagnation + β + axis_tags |
| S2-T4 직후 | `87d7603` | T5~T8 직전 — Action B 후보 worktree |
| S3 complete | `2d252f3` | adjacent rule engine + suppress + blocklist + yield |
| S4 complete | `2631c38` | balance-* 제거 + deficit_score |

### 제약·주의

- Tavily 433 rate limit: 발생 시 재실행. `search failed` 필터로 실시간 감지 가능
- OpenAI 502: 자동 복구 (단일 502 는 무시 가능)
- Exit code 1 = readiness gate FAIL (5c<15c) = 정상 완주

---

## Next Action

1. **새 세션 시작 직후**: 이 파일 + v5 report (§8 포함) 읽기. 사용자에게 "Action A (S2-T5~T8 토글 + smoke, 권장) 로 갈까요, B (추가 trial, ~$0.40) 를 먼저 할까요?" 질의
2. **Action A 선택 시**: `src/nodes/integrate.py::_detect_conflict` 에 T6/T7/T8 개별 토글 (config 플래그 3개) 추가 → 1c smoke 3회 (각각 on/off 조합) → KU 폭증이 어느 rule 에서 오는지 narrowing. API 비용 ~$0.12 × 3 = ~$0.36
3. **Action B 선택 시**: `git worktree add _evolver-worktrees/s2-t4 87d7603` → 기존 Monitor 패턴 그대로 5c trial → 결과 비교
4. **추가 제안 실행 가능 (S3 trigger 분포 검증)**: 이미 데이터 있음, API 비용 0. `bench/silver/japan-travel/p7-seq-s3/state-snapshots/cycle-*/gap-map.json` trigger 분포 파싱만으로 D-196 메커니즘이 S3 c3 collapse 까지 연결되는지 확인
5. **최종**: git commit (v5 report + bench trials + session-compact), project-overall 에 D-194/195/196 기록
