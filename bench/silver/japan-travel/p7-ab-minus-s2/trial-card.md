# Trial Card — p7-ab-minus-s2

> Created: 2026-04-23
> Phase: p7 (SI-P7 Structural Redesign)
> Domain: japan-travel
> Status: planned

## Goal

SI-P7 V3 Trial #1 — S2 축 ablation. H5c (β aggressive mode = S5a-coupled dead code) 정량 검증.

## Config Diff

- `SI_P7_AXIS_OFF=s2` (env var) → `SIP7AxisToggles.s2_enabled=False`
- p7-ab-on 대비 변경점:
  - critique.py: S2-T1 integration_bottleneck 처방 skip + S2-T2 ku_stagnation 3종 trigger 전부 skip
  - plan.py: `is_stagnation=False` 강제 → S2-T4α query_rewrite + S2-T4β aggressive mode 효과 경로 모두 no-op
  - integrate.py: `_detect_conflict` Rule 2b (value_shape) / 2c (axis_tags) / 2d (condition_axes) skip → pre-SI-P7 baseline (Rule 2 conditions only) 회귀
- S1, S3, S4 는 on 유지 (기존 p7-ab-on 과 동일)
- git HEAD: `61e5514` (V-T7b axis toggle)
- seed: `bench/japan-travel/state-snapshots/cycle-0-snapshot` (KU=13, GU=28) — p7-ab-on 과 동일

## 가설

- **H5c (primary)**: β aggressive mode 는 S5a (entity_discovery) 미구현 상태에서 dead code. 즉 `p7-ab-on` 에서도 `aggressive_mode_history=∅` 관찰됨 (V2 계측 추가 후). minus-s2 에서도 동일 → β 의 state set 존재 여부와 무관하게 효과 경로 부재 확정
- **H5c-collary**: `growth_stagnation` / `exploration_drought` trigger 발동 패턴이 p7-ab-on 과 minus-s2 에서 유사 (minus-s2 는 trigger 자체 skip 이라 0건). p7-ab-on 에서 trigger 발동에도 KU 고정 유지 = trigger→action 단절 정량 증거
- **대안 가설 (배제 후보)**: S2 전체가 효과 있음. minus-s2 에서 p7-ab-on 보다 뚜렷한 후퇴 (KU 성장 < p7-ab-on) 관찰되면 H5c 기각 방향

## 측정 대상

- `aggressive_mode_history` (V2 계측, si-p7-signals.json) — 0 vs >0
- `growth_stagnation` / `exploration_drought` / `Remodel 트리거` log 빈도
- `condition_split_events` — minus-s2 는 reason=conditions only, p7-ab-on 은 value_shape/condition_axes/axis_tags 포함
- KU 성장 (c1→c8), GU open 추이, gap_resolution
- `query_rewrite_rx_log` — minus-s2 에서 0 보장 (S2-T4α off)
- `integration_result_dist.cycle_history` — minus-s2 는 plan 주입 skip 효과

## Baseline 비교

- **상한**: `p7-ab-on` (15c, FAIL, KU=82 고착)
- **하한**: `p7-ab-off` (15c, PASS, KU=147)
- minus-s2 는 상한과 하한 사이 어디에 위치하는가 + pattern 유사성 분석

## 실행 명령

```bash
SI_P7_AXIS_OFF=s2 PYTHONUTF8=1 python scripts/run_readiness.py \
  --bench-root bench/silver/japan-travel/p7-ab-minus-s2 \
  --cycles 8
```

## 비용 예산

- 예상 LLM: ~200-250 calls
- 예상 Search: ~100-150 calls
- 예상 시간: ~30-40분 real API
- 예산 상한: 없음 (사용자 승인)

## 상태

- [x] config.snapshot.json 기록됨 (본 trial-card + git HEAD 명시)
- [ ] 실행 완료
- [ ] v3-isolation-report.md 작성됨 (V-T9)
- [ ] INDEX.md row complete 로 갱신
- [ ] D-192 root cause 확정 (V-T10)

## 관련 문서

- `dev/active/phase-si-p7-structural-redesign/v3-ablation-design.md` (V-T7 설계)
- `dev/active/phase-si-p7-structural-redesign/v1-signal-audit.md` (H5c 가설 근거)
- D-189 (S5a=critical path 보류) / D-190 (Step V 삽입) / D-191 (V3 설계 원칙)
- Memory: `feedback_l3_trial_item_signal_audit.md`, `feedback_foreground_execution.md`
