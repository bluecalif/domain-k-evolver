---
name: silver-trial-scaffold
description: Domain-K-Evolver Silver 세대 벤치 trial 스캐폴딩. `bench/silver/{domain}/{trial_id}/` 디렉토리, `trial-card.md`, `config.snapshot.json`, `readiness-report.md`, INDEX.md row 를 masterplan v2 §12 규칙 그대로 생성한다. Silver Phase P0~P6 readiness 벤치마크를 새로 시작하거나, "silver trial 만들어줘", "p0 baseline 돌려보자", "새 도메인 스모크", "fetch-first 실험 trial", "trial-card 쓰자", "readiness 디렉토리 만들기", "bench/silver 세팅" 같은 요청이 나오면 반드시 이 skill 을 사용하여 구조 누락·격리 위반·재현성 손실을 막는다. Bronze `bench/japan-travel/` 작업이거나 단발 cycle 디버깅에는 사용하지 않는다.
---

# Silver Trial Scaffold

## 목적

Silver 세대의 모든 readiness 측정은 **trial 단위로 격리된 디렉토리** 안에서만 이루어진다. 이 skill 은 그 trial 을 생성하는 결정론적 절차를 제공한다.

masterplan v2 §12 가 단일 진실 소스다. 이 skill 은 §12 의 규칙을 실행 가능한 단계로 풀어낸다 — 새 규칙을 만들지 않는다.

## 언제 쓰는가

- Silver Phase P0~P6 의 readiness 벤치마크 시작 시
- 동일 config 재실행(run2) trial 생성 시
- 2차 도메인 (P6) smoke run 시작 시
- P0-A1, P0-A6, P0-D1, P6-B1 task 수행 시
- "trial-card 작성", "readiness-report 작성", "INDEX.md 추가" 요청 시

## 언제 쓰지 않는가

- Bronze 레거시 `bench/japan-travel/` (read-only, 수정 금지)
- 단발 디버깅 cycle (`scripts/run_one_cycle.py` 1회 실행)
- Phase 5 이전의 회귀 재현 (Bronze 영역)

---

## 6 가지 운영 규칙 (masterplan v2 §12.3 verbatim)

1. **Baseline 의무** — `p0-{date}-baseline` trial 은 P0 완료 gate 의 요건. 모든 이후 trial 은 이 baseline 과 diff 가능해야 한다.
2. **격리** — trial 내부 파일은 다른 trial 이 절대 쓰지 않는다. 모든 스크립트는 `--bench-root` 플래그로 경로를 받아야 한다.
3. **전·후 문서 2종** — `trial-card.md` (실행 전: goal / config diff / 가설) → `readiness-report.md` (실행 후: gate 결과 / 권고). **`trial-card` 없이 실행 금지.**
4. **재현성 snapshot** — `config.snapshot.json` 은 자동 기록 (`config.py` dataclass + git HEAD + provider list + seed skeleton hash). 실행 시작 시 1회.
5. **Phase gate 는 trial 내부 판정** — cross-trial 비교는 INDEX.md 와 개별 readiness-report.md 에만. Phase 표 (§4) 의 gate 체크는 "어느 trial 에서 통과했나" 가 기록된다.
6. **폐기 ≠ 삭제** — 실패/폐기 trial 은 `status = archived` 로 두고 디렉토리 보존 (실험 실패도 증거).

이 6 항은 **위반 시 trial 을 무효 처리한다**. trial-card 없이 시작했거나 다른 trial 의 state 를 덮어썼다면, gate 결과는 폐기한다.

---

## trial_id 네이밍 (§12.2)

```
trial_id = {phase}-{YYYYMMDD}-{short_tag}[-run{N}]

  phase      ∈ {p0, p1, p2, p3, p4, p5, p6}
  date       실행 시작일 (KST)
  short_tag  kebab-case, ≤ 20 chars
             예: baseline, fetchfirst-v1, ddg-fallback, remodel-merge, alias-is-a
  run{N}     동일 config 재실행 시 (크래시 복구·통계 표본)
```

검증 정규식: `^p[0-6]-\d{8}-[a-z0-9-]{1,20}(-run\d+)?$`

**오용 패턴 (거부)**:
- `phase0-...` → `p0-...` 로 정규화
- `P0-...` → 대문자 금지, lowercase only
- `p3-baseline` → 날짜 누락
- `p3-20260420-fetch_first` → snake_case 금지

---

## 디렉토리 구조 (§12.1)

```
bench/silver/{domain}/{trial_id}/
├── trial-card.md              # 실행 전 (필수)
├── config.snapshot.json       # 실행 시작 시 자동 기록
├── state/                     # KU / GU / conflict_ledger
├── trajectory/                # cycle 별 planned vs actual
├── telemetry/                 # telemetry.v1.jsonl (P5 이후)
├── entity-field-matrix.json   # 실행 후 (필수) — standard matrix
└── readiness-report.md        # 실행 후 (gate 결과)
```

### entity-field-matrix.json 규격

실행 완료 후 **최종 cycle snapshot 기준**으로 자동 생성. 모든 trial 에 필수.

```json
{
  "trial_id": "...",
  "cycle": 5,
  "generated_at": "...",
  "categories": {
    "{category}": {
      "entities": ["slug-a", "slug-b", "*"],
      "fields": ["price", "hours", ...],
      "matrix": {
        "{slug}": {
          "{field}": {
            "state": "ku_gu | ku_only | gu_open | vacant",
            "ku_ids": ["KU-xxxx"],
            "gu_ids": ["GU-xxxx"]
          }
        }
      }
    }
  },
  "summary": {
    "total_slots": 0,
    "ku_gu": 0,
    "ku_only": 0,
    "gu_open": 0,
    "vacant": 0
  }
}
```

**state 값 정의**:
- `ku_gu`   — KU + GU 모두 존재 (GU resolved, KU 생성됨)
- `ku_only` — KU 존재, 해당 entity-field GU 없음 (seed 또는 wildcard GU 파생)
- `gu_open` — GU open, KU 미생성 (수집 진행 중)
- `vacant`  — KU·GU 모두 없음 (미탐색 슬롯)

**생성 명령**:
```bash
python scripts/analyze_trajectory.py \
  --bench-root bench/silver/{domain}/{trial_id} \
  --matrix
```

**상위 레지스트리**: `bench/silver/INDEX.md` — 모든 trial 1행 1trial.

---

## 5단계 실행 절차

다음 순서를 그대로 따른다. 각 단계는 사용자 확인 없이 진행 가능하지만, **3단계(실행 전) 와 5단계(실행 후) 는 반드시 사람이 손을 대야 한다** — gate 결정이 들어가기 때문.

### Step 1. 입력 확인

다음 4 가지가 결정되어야 한다:

| 항목 | 예시 | 출처 |
|------|------|------|
| `domain` | `japan-travel`, `realestate` | 사용자 / Phase 컨텍스트 |
| `phase` | `p0`~`p6` | 현재 작업 중인 Silver Phase |
| `short_tag` | `baseline`, `fetchfirst-v1` | trial 의 가설/실험 라벨 |
| `goal` | "P0 완료 증명 baseline" | INDEX.md / trial-card 의 한 줄 |

누락이 있으면 사용자에게 묻는다. 임의로 채우지 않는다 (특히 `goal` — 가설이 없는 trial 은 §12.3 규칙 1·3 위반).

### Step 2. 디렉토리 + 빈 artifact 생성

```bash
TRIAL_ID="${PHASE}-$(date +%Y%m%d)-${SHORT_TAG}"
TRIAL_DIR="bench/silver/${DOMAIN}/${TRIAL_ID}"
mkdir -p "${TRIAL_DIR}"/{state,trajectory,telemetry}
```

`bench/silver/${DOMAIN}/` 가 없으면 생성. `bench/silver/INDEX.md` 가 없으면 P0-A1 의 일부로 동시에 생성한다.

### Step 3. trial-card.md 작성 (사람 손 필요)

사용자에게 다음 4 항목을 받아 채운다:

```markdown
# Trial Card — {trial_id}

> Created: {YYYY-MM-DD}
> Phase: {phase}
> Domain: {domain}
> Status: planned

## Goal
{한 줄. INDEX.md 에 그대로 들어감}

## Config Diff
이전 trial 대비 변경된 config / code 항목. 없으면 "baseline (no diff)".

- `SearchConfig.enable_ddg_fallback`: false → true
- `policy.entropy_floor`: 1.5 → 2.0
- commit: `{git short sha}` (vs baseline `{baseline sha}`)

## 가설
이 trial 이 통과해야 할 가설을 1~3 개 bullet 로. Phase gate 항목과 매핑되어야 한다.

- H1: DDG fallback 활성화 시 `domain_entropy ≥ 2.5 bits` 달성 (P3 gate)
- H2: cycle 당 LLM 비용 ≤ baseline × 1.8 (cost regression 없음)

## 측정 대상
- `domain_entropy`, `provider_entropy`, `cycle_llm_token`, `fetch_failure_rate`

## 실행 명령
{실행에 사용할 정확한 명령. --bench-root 포함}

```bash
PYTHONUTF8=1 python scripts/run_readiness.py \
  --bench-root bench/silver/{domain}/{trial_id} \
  --cycles 15
```

## 상태
- [ ] config.snapshot.json 기록됨
- [ ] 실행 완료
- [ ] entity-field-matrix.json 생성됨
- [ ] readiness-report.md 작성됨
- [ ] INDEX.md row 갱신
```

**가설이 비어있거나 측정 대상이 비어있으면 작성 거부.** 이 두 칸은 trial 의 존재 이유다.

### Step 4. config.snapshot.json 자동 기록

실행 시작 시 (orchestrator/scripts 에서) 다음을 직렬화한다:

```json
{
  "trial_id": "p0-20260412-baseline",
  "created_at": "2026-04-12T09:00:00+09:00",
  "git_head": "b122a23",
  "git_dirty": false,
  "config": {
    "llm": { "model": "gpt-4.1-mini", "request_timeout": 60, "max_retries": 3 },
    "search": { "provider": "tavily", "request_timeout": 30, "fetch_top_n": 5 },
    "orchestrator": { "max_cycles": 15, "enable_audit": true }
  },
  "providers": ["tavily"],
  "seed_skeleton_sha": "{sha256 of skeleton json}"
}
```

`git_dirty=true` 인 trial 은 INDEX.md 에 `notes` 로 표시한다 (재현성 약함).

### Step 5. INDEX.md row append

```markdown
| {trial_id} | {domain} | {phase} | {date} | {goal} | running | - | - |
```

실행 완료 후 해당 row 를 update:

```markdown
| {trial_id} | {domain} | {phase} | {date} | {goal} | complete | VP1=5/5 VP2=6/6 | {짧은 노트} |
```

`status` 값: `planned` → `running` → `complete` | `failed` | `archived`.

**기존 row 를 절대 삭제하지 않는다** (§12.3 규칙 6 — 폐기 ≠ 삭제).

---

## readiness-report.md 의 지점

이 skill 은 **빈 readiness-report.md 를 만들지 않는다**. 결과 기록은 `silver-phase-gate-check` skill 의 책임이다. 둘은 의도적으로 분리되어 있다 — scaffold 는 실행 전, gate-check 는 실행 후.

trial-card 작성 후, 실행이 끝나면 다음을 안내한다:

> trial 실행이 끝나면 `silver-phase-gate-check` skill 로 readiness-report.md 를 생성하세요.

---

## Anti-Patterns

| 패턴 | 문제 | 교정 |
|------|------|------|
| trial-card 없이 곧장 실행 | §12.3 규칙 3 위반, gate 결과 무효 | Step 3 강제 |
| `run2` 만들면서 baseline 디렉토리 덮어쓰기 | 격리(규칙 2) 위반 | 새 trial_id 로 별도 디렉토리 |
| 실패 trial 디렉토리 삭제 | 규칙 6 위반, 실험 증거 손실 | `status=archived` 로 보존 |
| `goal` 을 "테스트", "확인" 같이 비움 | 가설 없는 trial → diff 불가 | 측정 대상까지 함께 받기 |
| INDEX.md 직접 수정 (run 후 row 만 추가) | 추적 누락, status=running 단계 부재 | Step 5 의 2단계 update 그대로 |
| 다른 phase 의 trial 에 cross-write | 규칙 2 위반 | `--bench-root` 플래그 필수 |
| `entity-field-matrix.json` 없이 trial 완료 선언 | coverage 공백 불가시 — 집계 지표(adj_yield, gap_resolution)만으로는 vacant 슬롯 탐지 불가 | 실행 후 `--matrix` 옵션으로 소급 생성 |

---

## 관련

- **masterplan v2 §12** — 단일 진실 소스. 이 skill 과 충돌이 발견되면 masterplan 이 옳다.
- **silver-phase-gate-check** — readiness-report.md 작성과 gate 판정. 이 skill 의 후속.
- **silver-implementation-tasks.md §4 P0-A** — P0-A1~A6 task 가 이 skill 의 첫 호출 트리거.
- **`templates/si-trial-card.md`, `templates/si-readiness-report.md`** — Silver 에서 신규 추가될 템플릿 (현재 없음 → P0-A2 가 만든다).
