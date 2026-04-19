# Trial Card: p6-diag-off-remodel-off-15c

| 항목 | 값 |
|------|-----|
| trial_id | p6-diag-off-remodel-off-15c |
| domain | japan-travel |
| phase | si-p6-consolidation (P6-A1-D4) |
| date | 2026-04-19 |
| goal | Stage-E × Remodel 2×2 matrix 의 B 조합 확보 — Remodel 완전 비활성(`--audit-interval 0`) + Stage-E off 하에서 15c 결과 측정. A(off+remodel-on) 와의 inside view 비교로 remodel 순효과 분리, A2 scope (A2b aging vs A2c filter) 우선순위 실증 기반 확정 |
| status | planned |

## Config

- **Seed**: fresh seed (`bench/japan-travel/state-snapshots/cycle-0-snapshot/`)
- **Model**: gpt-4.1-mini
- **Search**: Tavily
- **Cycles**: 15
- **Stage-E (External Anchor)**: **OFF** (`--no-external-anchor`)
- **Audit interval**: **0** (`--audit-interval 0` → audit + remodel 완전 비활성)

## Config Diff (vs p6-diag-off-15c)

| 항목 | p6-diag-off-15c (A) | p6-diag-off-remodel-off-15c (B, 본 trial) |
|---|---|---|
| `--no-external-anchor` | Yes | Yes |
| `--audit-interval` | 5 (default) | **0** |
| remodel 발동 기대 | cycle 10 에서 자연 발동 | **전 cycle 비활성** |

commit 기준: `cdd4504` (공통 baseline)

## Hypothesis

**비교 기준**:
- **A** = p6-diag-off-15c (off + remodel-on, 15c) — `hitl_queue.remodel=1` from c10, open=25, NO-SEL 23 (92%)
- **C** = p6-diag-full-15c (on + remodel-on, 15c) — 동일하게 c10 부터 remodel-on, open=18, NO-SEL 11 (61%)

**검증 가설** (matrix §5 3가지 Path):

- **H-α (remodel 무효)**: B 의 NO-SEL 비율 |B - A| < 5pp 및 KU 순증 차이 < 10% → remodel 이 단일 도메인 15c 범위에서 outcome delta 무. **A2b (plan.py aging penalty) 최우선**.
- **H-β (remodel 유효)**: B 의 NO-SEL > A 의 NO-SEL + 5pp → remodel 이 malformed GU 정리로 selection 통과율을 끌어올리고 있었음. **A2c (filter) 만 구현**, A2b 는 후순위.
- **H-γ (remodel 역효과)**: B 의 NO-SEL < A 의 NO-SEL - 7pp → remodel merge 가 entity 혼탁을 유발. **A2 전면 보류, remodel.py 재검토**.

**추가 관측 대상**:
- cycle 10 에서 A 에서 발동된 Smart Remodel 의 3-way OR 중 true 조건 (growth_stagnation / exploration_drought / audit_critical) 을 B 의 동일 cycle 지표로 재구성
- target_count 수축 (c1 ~13 → c11+ ~3-6) 재현 여부 — remodel 유무와 독립 현상인지 확인
- dispute_queue 규모 (A c15 = 97)와 비교

## 측정 대상

- 3-카테고리 (NO-ANSWER / NO-INTEGRATION / NO-SELECTION) 비율 @ c15
- KU 성장 (window 별 Δ/cycle)
- GU: open / resolved / adjacent_gap_generated 추이
- target_count 추이
- `hitl_queue.remodel` 전 cycle 0 검증 (sanity)
- `audit_summary.last_audit_cycle == -1` 또는 `findings_count == 0` 유지 검증

## Command

```bash
python scripts/run_readiness.py \
  --bench-root bench/silver/japan-travel/p6-diag-off-remodel-off-15c \
  --cycles 15 \
  --no-external-anchor \
  --audit-interval 0
```

## 상태

- [ ] config.snapshot.json 기록됨
- [ ] 실행 완료
- [ ] `hitl_queue.remodel = 0` 전 cycle 검증
- [ ] readiness-report.md 작성됨 (silver-phase-gate-check skill)
- [ ] INDEX.md row `running` → `complete` 갱신
- [ ] `stage-e-remodel-matrix.md` §3~§6 실측 반영
- [ ] debug-history D-166 본문 확정

## Results

> 실행 후 채움
