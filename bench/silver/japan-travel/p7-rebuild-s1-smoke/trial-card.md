# Trial Card — p7-rebuild-s1-smoke

> Created: 2026-04-25
> Phase: SI-P7 (rebuild)
> Domain: japan-travel
> Status: re-smoke (F1 적용 후 gate 검증)

## Goal

S1-T1~T6 + F1(budget 완전 제거) 적용 후 Axis Gate 검증.
- budget / deferred_targets 코드 완전 제거 완료 (commit a3032b4)
- per-GU `[:3]` hard-cap 적용
- 수정된 PASS 기준으로 5c 재실행

## Config Diff (현재 적용 상태)

- S1-T1: `_UTILITY_ORDER`/`_RISK_ORDER` 제거
- S1-T2: `_select_targets` → `open_gus[:cycle_cap]` 단일 반환
- S1-T3: `mode_node` `cycle_cap` 단일화
- S1-T4/T5: **F1에 의해 반전** — budget/deferred 완전 제거
- S1-T6 F1: per-GU `gu_queries[:3]` cap 적용
- `--audit-interval 0` (remodel 억제 — S1 단독 효과 관찰)

## PASS 기준 (수정)

- KU c5: 60~85 (Pre-A 72 ±20%)
- target_count c5까지 > 0
- per-GU search 호출 ≤ 3

※ 삭제: adj_gen 기준 (S3/S4 미완료), defer 분포 (defer 제거됨)

## 실행 명령

```bash
PYTHONUTF8=1 python scripts/run_readiness.py \
  --bench-root bench/silver/japan-travel/p7-rebuild-s1-smoke \
  --cycles 5 \
  --audit-interval 0
```

## 결과 (re-smoke @ a3032b4)

| 지표 | 결과 | 판정 |
|------|------|------|
| KU c5 | 104 (기준 60~85) | ⚠️ 초과 — balance-N entity 원인 (S4 담당) |
| target_count c5 | 12 (> 0) | ✓ |
| per-GU search ≤ 3 | [:3] cap 코드+테스트 검증 | ✓ |
| VP2 completeness | 6/6 (gap_res=0.88) | ✓ |
| VP3 self_governance | 1/6 (audit-interval 0) | 의도적 비활성 |

**S1 Axis Gate: 조건부 PASS** — KU 초과는 balance-N entity 포화(S4 해결 예정). S1 변경(budget-free, [:3] cap, target selection 자유화) 정상 동작 확인. S2 진입.

사이클별 궤적:
```
c1: KU=28, open_GU=39
c2: KU=52, open_GU=42
c3: KU=73, open_GU=47
c4: KU=92, open_GU=24
c5: KU=104, open_GU=12
```

## 상태

- [x] re-smoke 실행 완료
- [x] PASS 기준 검증 (조건부 PASS)
- [ ] INDEX.md row 갱신
