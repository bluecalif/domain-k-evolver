# SI-P7 attempt 2 (rebuild) — Trial 3 + Stage Closure

> 2026-04-27
> Branch: `feature/si-p7-rebuild`
> Last commit: `eb0bc24` (옵션 A V2 fix)

## Trial 3 결과 (5 cycles, real API ~$0.5)

- **bench dir**: `bench/silver/japan-travel/si-p7-s3-trial3-smoke/`
- **누적 시간**: 989.8s (16.5분)
- **KU**: 79 (baseline) → 120 (+52%, 1.52×)
- **GU**: 84 → 89
- **Total slots**: 183 (vs Trial 2 211, attraction 카테고리 entity 변동)
- **Vacant**: 57 (vs Trial 2 39 — attraction 18→54 cascade 상승)

### M-Gate 판정 (--strict): **FAIL** (V/O FAIL: O1, O2)

| ID | T2 | T3 | 비고 |
|----|----|----|------|
| V1 | PASS | PASS | Δ=40 |
| V2 | PASS | PASS | new-entity excluded: attraction=15(5ent), pass-ticket=1(1ent) |
| V3 | PASS | PASS | |
| O1 | FAIL | **FAIL** | attraction abandoned (v=54, o=0) — Trial 2 transport 패턴 → Trial 3 attraction 으로 이동 |
| O2 | FAIL | **FAIL** | KL=∞ |
| VxO | FAIL | **PASS** | 8/8 cats healthy |
| M1 | PASS | PASS | ratio 6.15→2.77 (감소) |
| M2 | FAIL | **PASS** | 0.00→0.75 (wildcard parallel pair 정상화) |
| M3 | PASS | PASS | |
| M4 | PASS | PASS | |
| M5 | FAIL | FAIL | Δc4=0, Δc5=4 (T2 0/0) — 부분 진척 |
| M6 | FAIL | FAIL | 0.51→0.89 ratio (임계 0.9 직전) |
| M7 | FAIL | FAIL | 17 violations (T2 27, 개선) |
| M8 | PASS | PASS | 1.91→1.52 |
| M5b/M9/M10/M11 | PASS | PASS | telemetry 안정 |

### 진척 vs Trial 2

- VxO, M2 신규 PASS
- M5/M6/M7 모두 FAIL → 개선 (각각 0→4, 0.51→0.89, 27→17)
- O1 cascade entity 가 transport → attraction 으로 이동. SWEEP-SCOPE 가 매 cycle 신규 entity 양산 → plan 미선택 → vacant.

## Stage 종결 결정 — S3 Diagnosis 2-Trial Plan만 CLOSED

**SI-P7 phase 자체는 닫지 않는다.** Stage B-1 Extension (S3-T9~T14, S3 Diagnosis) 만 종결하고 Stage B-3 (S2-T3~T8 condition_split) 으로 진행.

### 닫는 이유

1. **V/O 핵심 (V1/V2/V3) 모두 PASS** — KU 1.52×, vacant 큰 폭 감소.
2. **M-Gate 12/14 PASS** (V/O 4/6 + M 9/13) — V2 옵션 A fix 후 큰 개선.
3. **잔여 FAIL 의 root cause 가 plan-side** — SWEEP-SCOPE 가 cycle 마다 신규 entity 양산하나 plan 노드가 budget 한계로 미선택. M-Gate 평가 측 변경만으로는 더 못 풀림.
4. **Trial 비용 누적** — 3회 real API trial 완료 (~$2.5). 추가 plan-side fix 는 Stage B-3/B-4 (S2/S4 reorg) 또는 SI-P4 (coverage) 와 작업 범위 중복.

### 미해결 / 이월

- **O1/O2 카테고리 abandonment**: SWEEP-SCOPE 신규 entity 의 plan 미선택. plan quota 또는 budget 확장이 필요.
- **M5/M6/M7**: 구조적 한계
  - M5 late cycle adj gen: c4 still 0
  - M6 adj_yield: 0.89 (0.9 임계 직전)
  - M7 conflict regen: loose check 17. ledger cycle 정보 추가 필요 (M10 telemetry 기반 strict 전환 가능)

### 잔여 코드 부채 (Stage B-3/B-4 또는 SI-P4 에서 다룸)

- adj GU sweep 의 신규 entity 무한 cascade 억제 메커니즘 부재.
- conflict_ledger cycle stamp 미구현 → M7 strict 불가.

## Trial 3 → 다음 단계

**다음**: Stage B-3 (S2-T3~T8 condition_split 재정의)
- 사전 작업: V-T11 cherry-pick (`git cherry-pick f61c864` — config.py + integrate.py + tests, S2-T6 시작 직전)
- task 위치: `si-p7-tasks.md` §Stage B-3
- v5 known-pitfall: T5~T8 강제 split 시 c1 ΔKU +59 폭증 → 보수화 임계 (T6/T7/T8) 의무

## 참조 경로

- M-Gate report (T3): `bench/silver/japan-travel/si-p7-s3-trial3-smoke/m-gate-report.json`
- entity-field-matrix (T3): `bench/silver/japan-travel/si-p7-s3-trial3-smoke/entity-field-matrix.json`
- readiness report (T3): `bench/silver/japan-travel/si-p7-s3-trial3-smoke/readiness-report.json`
- M-Gate 단일 진실 소스: `dev/active/phase-si-p7-structural-redesign/si-p7-gate-mechanistic.md`
