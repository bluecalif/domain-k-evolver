# Trial Card — p7-s4-t1-smoke

| 항목 | 값 |
|---|---|
| **trial-id** | p7-s4-t1-smoke |
| **task** | SI-P7 Pre-Stage B / S4-T1: virtual balance-N entity 완전 제거 |
| **날짜** | 2026-04-25 |
| **브랜치** | feature/si-p7-rebuild |
| **cycles** | 1 (real API) |
| **목적** | L2 gate — gap_map 에 balance-* GU 0건 검증 |

## PASS 기준 vs 결과

| 기준 | 결과 | 판정 |
|---|---|---|
| gap_map 내 `balance-*` GU = 0 | 0건 (total GU=35) | ✓ |
| critique_node 정상 완료 | KU 13→24, 에러 없음 | ✓ |
| GU ID 연속성 유지 | GU-0001~GU-0035 연속 | ✓ |
| refresh_gus 정상 동작 | 0건 (stale 없음) | ✓ |

## 판정: ✅ PASS

balance-N virtual entity 가 완전히 제거되었음을 실 API 경로에서 검증.
S1 5c re-smoke 에서 KU c5=104 초과의 원인이었던 측정 오염원 제거 완료.

## 주요 수치

```
seed: KU=13, GU=28
c1 후: KU=24 (active), GU=35 (open=24)
balance-* GU: 0
```

## 변경 파일 (이번 task)

- `src/nodes/critique.py`: `_generate_balance_gus` 함수 삭제, `MIN_KU_PER_CAT` 상수 삭제, 호출 블록 삭제
- `tests/test_nodes/test_critique.py`: `TestGenerateBalanceGus` 5 tests 삭제 → `TestBalanceGuRegression` 3 tests (835 passed)
- `dev/active/phase-si-p7-structural-redesign/si-p7-tasks.md`: Stage B Option B 재구성 (Pre-B → B-1/B-2 S3 → B-3 S2 → B-4 S4-T2~T4)

## Next

Stage B-1: S3-T1 (suppress 임계 1.5 → 2.0, D-56 보수화)
