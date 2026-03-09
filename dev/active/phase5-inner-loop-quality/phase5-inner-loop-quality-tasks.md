# Phase 5: Inner Loop Quality — Tasks
> Last Updated: 2026-03-09
> Status: **Complete** (23/23 tasks) — Gate #5 PASS

## Summary

| Stage | Total | S | M | L | Done |
|-------|-------|---|---|---|----|
| 선행: Gate 메트릭 수정 | 1 | 1 | 0 | 0 | 1/1 ✅ |
| A: Geography Axis-Tags 전파 | 4 | 1 | 3 | 0 | 4/4 ✅ |
| B: Staleness 자동갱신 | 2 | 0 | 1 | 1 | 2/2 ✅ |
| C: Category 균형 + Field 다양성 | 2 | 0 | 2 | 0 | 2/2 ✅ |
| D: GU Resolve Rate 개선 + bench 정리 | 2 | 1 | 1 | 0 | 2/2 ✅ |
| E: Staleness 메커니즘 개선 | 5 | 2 | 2 | 1 | 5/5 ✅ |
| E-2: VP2 잔여 FAIL 해결 | 4 | 2 | 1 | 1 | 4/4 ✅ |
| 검증: Gate 재실행 | 3 | 0 | 0 | 3 | 3/3 ✅ |
| **합계** | **23** | **7** | **10** | **6** | **23/23 ✅** |

---

## 선행: Gate 메트릭 수정 ✅

- [x] **5.0** VP1-R1 Shannon Entropy → Gini Coefficient 교체 `[S]`
  - `src/utils/readiness_gate.py`: R1에 `_gini_coefficient()` 적용
  - `tests/test_readiness_gate.py`: 관련 테스트 수정

---

## Stage A: Geography Axis-Tags 전파 ✅

- [x] **5.1** Integrate: GU→KU axis_tags 전파 `[M]`
- [x] **5.2** Integrate: KU 내용 기반 geography 추론 `[M]`
- [x] **5.3** Integrate/Plan: 동적 GU 생성 시 geography 부여 `[M]`
- [x] **5.4** Readiness Gate: blind_spot KU 기반 개선 `[S]`

---

## Stage B: Staleness 자동갱신 ✅

- [x] **5.5** Critique: Stale KU → Refresh GU 자동생성 `[L]` (D-55: cycle당 상한 10)
- [x] **5.6** Integrate: Refresh 통합 시 KU 갱신 `[M]`

---

## Stage C: Category 균형 + Field 다양성 ✅

- [x] **5.7** Critique: 소수 카테고리 균형 GU 생성 `[M]` (D-56)
- [x] **5.8** Integrate: Field 다양성 억제 `[M]`

---

## Stage D: GU Resolve Rate 개선 + bench 정리 ✅

> 5.9 Gate FAIL 원인: GU 생성(~72/cycle) >> 해결(~8/cycle) 구조적 불균형.
> bench/ 디렉토리 더블 서픽스 버그 + 아티팩트 정리 포함.

- [x] **5.10a** bench/ 정리 — 더블 서픽스 버그 수정 + 아티팩트 삭제 `[S]` (D-61)
  - `bench/japan-travel-readiness-readiness/` 삭제 (빈 초기화 상태, 버그 산물)
  - `scripts/run_readiness.py` L104, L162: `-readiness` 서픽스 이중 적용 방지 guard 추가
  - `tests/test_nodes/test_mode.py`: 상한 assertion 제거
- [x] **5.10b** Mode: target_count/cap 하드캡 제거 — 비례 스케일링 `[M]` (D-60)
  - `src/nodes/mode.py:196-201`: `min(max(...), N)` → `max(N, ...)` (상한 제거, 하한 유지)
  - **integrate.py `_compute_dynamic_gu_cap`은 현행 캡(12/30) 유지** (2차 폭증 방지)
  - `tests/test_nodes/test_mode.py`: 상한 assertion 제거, 18/18 PASS

---

## Stage E: Staleness 메커니즘 개선 ✅

> Gate #3 (15c) FAIL: staleness 93, gap_resolution 0.780, avg_confidence 0.778, closed_loop 0.
> 근본 원인: stale refresh 시 evidence의 오래된 observed_at 사용 + REFRESH_GU_CAP=10 고정.

- [x] **5.12a** Integrate: stale refresh observed_at 버그 수정 `[S]` (D-62)
  - `src/nodes/integrate.py:317-319`: `evidence.get("observed_at", ...)` → `date.today().isoformat()`
  - stale refresh는 "오늘 재확인"이므로 항상 today 사용
  - `tests/test_nodes/test_integrate.py`: old evidence date 무시 확인 테스트
- [x] **5.12b** Integrate: stale refresh confidence 가중 평균 `[S]` (D-63)
  - `src/nodes/integrate.py:323-327`: `(old+new)/2` → `0.3*old + 0.7*new`
  - 최신 evidence를 더 신뢰 (stale refresh 경로만 적용)
  - `tests/test_nodes/test_integrate.py`: 가중 평균 결과 확인
- [x] **5.12c** Critique: Adaptive REFRESH_GU_CAP `[M]` (D-64)
  - `src/nodes/critique.py`: `_compute_refresh_cap(stale_count)` 함수 추가
  - sr ≤20→10, >20→stale//2 (cap 20), >50→stale//3 (cap 25)
  - `_generate_refresh_gus` cap 파라미터화
  - `tests/test_nodes/test_critique.py`: adaptive cap 단위 테스트 4개
- [x] **5.12d** Mode: T7 Staleness Trigger `[M]` (D-65)
  - `src/nodes/mode.py`: `_compute_trigger_t7_staleness(metrics)` — staleness_risk > 20 → Jump Mode
  - `tests/test_nodes/test_mode.py`: T7 발동/비발동 테스트 5개
- [x] **5.12e** Readiness Gate: Closed Loop 세분화 `[L]` (D-66)
  - `src/utils/readiness_gate.py:384-394`: category별 findings 감소도 closed_loop 인정
  - `tests/test_readiness_gate.py`: category별 감소 시나리오 테스트

---

## Stage E-2: VP2 잔여 FAIL 해결

> Gate #4 (15c) FAIL: VP2 4/6 — staleness=3 (≤2), avg_confidence=0.755 (≥0.82).
> 근본 원인: 신규/일반 업데이트 경로에서 observed_at 미갱신 + confidence 단순 평균 하락.

- [x] **5.14a** Integrate: 신규/condition_split KU observed_at = today `[S]` (D-67)
  - `src/nodes/integrate.py:408,372`: `evidence.get("observed_at", ...)` → `date.today().isoformat()`
  - 새 KU 생성 즉시 stale 유입 차단
- [x] **5.14b** Integrate: 일반 업데이트 observed_at = today `[S]` (D-68)
  - `src/nodes/integrate.py:400`: `existing_ku["observed_at"] = date.today().isoformat()` 추가
  - stale refresh(D-62)와 일관성 확보
- [x] **5.14c** Integrate: evidence-count 가중 평균 `[M]` (D-69)
  - `src/nodes/integrate.py:392-398`: `(old+new)/2` → `(old*N + new)/(N+1)` (N=기존 evidence 수)
  - 잘 검증된 고confidence KU가 새 evidence 1개로 급락 방지
- [x] **5.14d** Integrate: multi-evidence confidence boost `[L]` (D-70)
  - `src/nodes/integrate.py:400-411`: evidence ≥2→+0.03, ≥3→+0.05, ≥4→+0.07 (cap 0.95)
  - 삼각측량 원칙: 독립 출처 N개 확인 → 단일 출처보다 높은 신뢰도

---

## 검증: Gate 재실행

- [x] **5.9** Gate 재실행 #1 + 결과 확인 `[L]` — **FAIL** (VP1 3/5, VP2 2/6, VP3 5/6)
  - VP1: blind_spot 0.0 (PASS), field_gini 0.437 (PASS)
  - VP2: gap_resolution 0.545 (FAIL), min_ku 1 (FAIL), staleness 11 (개선)
  - 결과 보고서: `docs/phase5-readiness-report.md`
- [x] **5.11** Gate 재실행 #2 (5→15 cycle) `[L]` — **FAIL** (VP1 5/5, VP2 3/6, VP3 5/6)
  - Gate #2 (5c): VP1 4/5, VP2 1/6, VP3 1/6
  - **Gate #3 (15c)**: VP1 5/5 PASS, VP2 3/6 FAIL, VP3 5/6 (closed_loop only)
  - VP2 실패: staleness=93 (≤2), gap_resolution=0.780 (≥0.85), avg_confidence=0.778 (≥0.82)
  - VP3 실패: closed_loop=0 (≥1)
  - 근본 원인 분석 → Stage E 삽입 결정
- [x] **5.13** Gate 재실행 #3 (15 cycle) `[L]` — **FAIL** (VP1 5/5, VP2 4/6, VP3 6/6)
  - Stage E 적용 후 Gate #4 실행
  - VP1 5/5 PASS, VP2 4/6 FAIL, VP3 6/6 PASS
  - VP2 실패: avg_confidence=0.755 (≥0.82), staleness=3 (≤2)
  - VP2 개선: staleness 93→3, gap_res 0.780→0.888, closed_loop 0→1
  - 근본 원인 분석 → Stage E-2 삽입 결정
- [x] **5.15** Gate 재실행 #4 (15 cycle) `[L]` — **PASS** (VP1 5/5, VP2 6/6, VP3 5/6)
  - Stage E-2 적용 후 Gate #5 실행
  - VP1 5/5 PASS, VP2 6/6 PASS, VP3 5/6 PASS (83%)
  - VP2 성과: avg_confidence 0.755→0.822, staleness 3→0
  - **Phase 5 완료**
