# Evolver Operator Guide

> 대상: Evolver Silver 세대 운영자
> Gate 정의: `docs/silver-masterplan-v2.md` §4 P5, §7 S10 참조 (이 문서에서 재진술 없음)

---

## 1. 시작하기

### 의존성 설치

```bash
pip install -e ".[dashboard]"
```

dashboard extras: `fastapi`, `uvicorn[standard]`, `jinja2`

### 대시보드 실행

```bash
python scripts/run_readiness.py --serve-dashboard --bench-root bench/silver/japan-travel/p0-20260412-baseline
```

또는 직접:

```bash
python -m src.obs.dashboard.app --trial-root bench/silver/japan-travel/p0-20260412-baseline --port 8000
```

브라우저에서 `http://127.0.0.1:8000` 접속.

### 필요 조건

- trial_root 디렉토리에 `trial-card.md` 존재
- `telemetry/cycles.jsonl` 이 있어야 데이터 표시 (trial 실행 후 생성됨)
- 없으면 각 view가 "데이터 없음" 메시지 표시

---

## 2. Trial 구조 이해

```
bench/silver/{domain}/{trial_id}/
├── trial-card.md               ← 실험 메타데이터
├── config.snapshot.json        ← 실행 시 config 스냅샷
├── readiness-report.md         ← Phase gate 판정
├── state/
│   ├── conflict_ledger.json    ← Conflict Ledger view 소스
│   └── phase_{N}/
│       └── remodel_report.json ← Remodel Review view 소스
├── trajectory/
│   └── trajectory.json         ← Cycle Timeline 보조
└── telemetry/
    └── cycles.jsonl            ← 모든 view의 주 데이터 소스
```

`cycles.jsonl`: cycle 1행 = 1 snapshot (telemetry.v1 schema 준수).

---

## 3. Overview view 읽는 법

| 지표 | 건강 | 경고 | 위험 |
|------|------|------|------|
| evidence_rate | ≥ 0.95 | 0.55~0.95 | < 0.55 |
| conflict_rate | ≤ 0.05 | 0.05~0.25 | > 0.25 |
| avg_confidence | ≥ 0.85 | 0.60~0.85 | < 0.60 |
| collect_failure_rate | ≤ 0.10 | 0.10~0.50 | > 0.50 |
| gap_resolution_rate | ≥ 0.85 | 0.50~0.85 | < 0.50 |

색상 코드: 초록(ok) / 노랑(warn) / 빨강(crit).

**Critical Audit Finding 배너**: 최근 cycle에 critical severity audit 발견 시 표시.
바로 `/timeline` → `/conflicts` 순서로 원인 확인.

---

## 4. Cycle Timeline에서 이상 탐지

`/timeline` 에서 novelty/conflict_rate/evidence_rate/collect_failure 4개 지표를 한 화면에서 확인.

**정상 패턴**:
- novelty: 초기 높다가 완만히 하락 (지식 포화 진행)
- conflict_rate: 초기 발생 후 dispute resolution에 따라 감소
- collect_failure_rate: 일정하게 낮음 (< 0.10)

**이상 패턴 신호**:
- novelty 급락 (3 cycle 연속 < 0.10) → 탐색 정체, Probe/Pivot 필요
- conflict_rate 증가 → integrate 충돌 누적, dispute_queue 확인
- collect_failure_rate 급등 (> 0.20) → 검색 API 이상, source 확인

---

## 5. "진행이 느려진 경우" 진단 walkthrough (S10 시나리오)

> 목표: 3분 내에 병목 원인을 특정한다.

### 시나리오: novelty 급감 + collect_failure 상승

```
증상: cycle 7~10에서 novelty < 0.10, collect_failure > 0.15
```

**Step 1 — Overview** (30초)

- novelty, conflict_rate, collect_failure_rate 색상 확인
- Critical Audit 배너 여부 확인

**Step 2 — Cycle Timeline** (60초)

- `/timeline` 접속
- novelty 차트에서 급락 시작 cycle 특정 (예: cycle 7)
- 같은 구간에서 collect_failure_rate도 동시 상승 여부 확인
  - 동시 상승 → 수집 실패가 novelty 감소의 원인
  - novelty만 하락, failure 정상 → 탐색 범위 포화 (Probe/Pivot 결과 확인)

**Step 3 — Source Reliability** (60초)

- `/sources` 접속
- collect_failure_rate 추이 확인
  - cycle 7 이후 > 0.15 지속 → 검색 API 문제 or target GU 고갈
  - search_calls가 급감 → plan이 target GU를 못 찾고 있음

**판정 및 조치**:

| 관측 패턴 | 원인 | 조치 |
|----------|------|------|
| novelty↓ + collect_failure↑ | 검색 실패 | API 키 확인, Tavily 한도 확인 |
| novelty↓ + collect_failure 정상 | 탐색 범위 포화 | Probe/Pivot 발동 여부 확인 (`/coverage` → probe_history_count) |
| novelty 정상 + gaps_open↑ | resolve 지연 | dispute_queue 확인 (`/hitl` Dispute 탭) |

---

## 6. HITL Inbox 처리

`/hitl` 3탭:

### Seed/Remodel 승인 탭

- **Seed 승인**: 새 도메인 skeleton 승인. 현재 자동 처리 (Silver P6 이전).
- **Remodel 승인**: `/remodel` 링크 → Remodel Review에서 proposals 확인 후 판단.

### Dispute 배치 검토 탭

- dispute_queue_size > 0 이면 미해결 충돌 존재.
- 배치 검토: conflict_ledger (`/conflicts`) 에서 open 상태 항목 확인.
- dispute_queue는 in-memory — trial 재실행 시 초기화됨. 이력은 conflict_ledger에 영속 보관.

### Exception 알림 탭

- auto-pause 임계치 위반 cycle 목록 (metrics_guard 기준).
- 임계치: conflict_rate > 0.25, evidence_rate < 0.55, collect_failure > 0.50, avg_confidence < 0.60.
- Exception 발생 시 해당 cycle의 Cycle Timeline 확인 필수.

---

## 7. Conflict Ledger 읽기

`/conflicts` — `state/conflict_ledger.json` 을 직접 읽음.

- **ledger_id**: 충돌 식별자 (KU pair)
- **status**: `open` (미해결) / `resolved` (dispute resolution 완료)
- ledger는 append-only — resolved된 항목도 삭제되지 않음
- open 항목이 계속 증가하면 dispute resolution 경로 점검 필요

dispute_queue(처리 대기 묶음)와 다름:

| 개념 | 의미 | 수명 |
|------|------|------|
| conflict_ledger | 충돌 이력 기록 (영속) | 삭제 없음 |
| dispute_queue | 처리 대기 묶음 (임시) | trial 재시작 시 초기화 |

---

## 8. Remodel Review 승인/거부

`/remodel` — `state/phase_{N}/remodel_report.json` 을 읽음.

- **proposals**: merge / split / reclassify 제안 목록
- **rollback_payload**: 승인 취소 시 복원 데이터 (있으면 안전)
- **status**: pending / approved / rejected

현재 remodel 승인은 HITL-R 체제 (masterplan §14). 대시보드는 read-only viewer — 직접 상태 변경 없음.
승인/거부는 `run_readiness.py --approve-remodel` 플래그로 처리 (P6에서 구현 예정).
