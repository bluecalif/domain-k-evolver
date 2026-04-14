# Phase: Gap-Resolution 병목 조사

> Created: 2026-04-14
> Trigger: D-126 — SI-P3R Gate PASS 후 gap_resolution_rate 0.437@10c 병목 조사
> Source trial: `bench/silver/japan-travel/p3r-gate-trial-15c/`

## Goal

Silver P3R 15c trial에서 gap_resolution_rate이 0.517@15c로 Phase 5 Bronze(0.909)에 크게 미달.
병목 원인을 특정하고 수정안을 도출한다.

## 조사 요약

**두 개의 독립 병목 확인**:

1. **Primary (throughput cap)**: `mode.py`에서 target_count 상한 10으로 고정 — regression
2. **Secondary (conversion rate)**: target 10개 중 실제 resolve 3-7개 (30-70%) — LLM parse 수율 문제

## B1: Primary Bottleneck — target_count 상한 Regression

### 증상
- Jump mode에서 open_count=67이어도 target_count=10만 선정
- 이론 최대 resolve/cycle = 10 (실측 3-7)
- gap_res=0.9 도달 필요 이론 cycle 수: 11+ cycles (cycle 10 기준)

### 근본 원인 (git blame 확정)

| Commit | 변경 | 결과 |
|--------|------|------|
| `b122a23` [phase5] | `target_count = max(10, ceil(open_count * 0.5))` | Phase 5 Gate PASS (0.909) |
| `b12545d` [si-p3] 디버그 로그 정리 | `NORMAL_TARGET_CAP=10`, `JUMP_TARGET_CAP=10` 재도입 + `min(..., cap)` 재적용 | SI-P3R regression (0.517) |

### 핵심 코드 (src/nodes/mode.py:204-212)

```python
# 현재 (regression)
NORMAL_TARGET_CAP = 10
JUMP_TARGET_CAP = 10
if mode == "normal":
    target_count = min(max(4, ceil(open_count * 0.4)), NORMAL_TARGET_CAP)
else:
    target_count = min(max(10, ceil(open_count * 0.5)), JUMP_TARGET_CAP)
```

### Phase 5 의도 (commit b122a23)

```python
# Phase 5 — cap 제거
target_count = max(10, ceil(open_count * 0.5))  # jump
target_count = max(4, ceil(open_count * 0.4))    # normal
```

D-37 "jump target_count 상한 10"은 Phase 1-2 Bronze 초기 맥락. Phase 5에서 gap_resolution 0.909 달성 목표로 제거. SI-P3 디버그 중 D-37 원문만 보고 cap을 재도입하면서 Phase 5 해제 의도를 놓친 것.

### 수치 시뮬레이션

cycle 10 기준 (open=67, resolved=52):
- **현재**: target=10, resolve ≤ 10/cycle → 0.9 도달 11+ cycle
- **Phase 5 로직**: target = max(10, 67*0.5) = **34** → 0.9 도달 3-4 cycle 가능 (conversion 유지 시)

## B2: Secondary Bottleneck — target→resolve Conversion Loss

### 증상
- 15c 누적: 150 target 시도 (10×15), 78 resolve → **conversion rate 52%**
- active KU 105개, 평균 evidence 3.76개 = 395 evidence links
- 해석: ~50% target이 0 claims 반환 (search는 성공, LLM parse 수율 저하)

### 코드 경로 (loss 포인트)

1. **collect.py:166-175** — `_parse_claims_llm`
   - snippet 없으면 LLM 호출 skip (line 117-119)
   - LLM 호출 실패 시 deterministic fallback (line 134-136)
   - 성공해도 LLM이 `[]` 반환 가능 (snippet이 target field 정보 없을 때)

2. **integrate.py:500-505** — GU resolve 조건
   ```python
   if source_gu_id and claim.get("integration_result") in ("added", "updated", "condition_split", "refreshed"):
       for gu in gap_map:
           if gu.get("gu_id") == source_gu_id and gu.get("status") == "open":
               gu["status"] = "resolved"
               break
   ```
   - 1:1 매칭. source_gu_id 틀리거나 없으면 resolve 안 됨.
   - "conflict_hold" 결과는 resolve 안 됨 (단, conflict_rate=0-17%로 주원인 아님)

3. **plan.py:145-149** — 결정론적 query 생성
   ```python
   queries[gu_id] = [
       f"{slug} {field}",
       f"{slug} {field} 2026",
   ]
   ```
   - 단순 키워드 조합. field가 복잡하거나 slug가 영어가 아니면 snippet 적중률↓

### 가설 (우선순위)

- **H1 (유력)**: LLM parse가 target field를 snippet에서 못 찾아 `[]` 반환
- **H2**: query 품질 — `{slug} {field}` 단순 조합이 관련 snippet 미회수
- **H3**: LLM이 source_gu_id를 누락/변조 (prompt에 hard-coded지만 GPT 출력 준수율)
- **H4 (약함)**: conflict_hold로 open 유지 — conflict_rate 낮아 주요 원인 아님

### Open GU 분포 (cycle 10 snapshot)
- 67 all `gap_type=missing`
- 63 medium utility, 4 high (high 우선 처리됨)
- 48 `A:adjacent_gap` (integrate에서 동적 생성)
- 4 `E:category_balance`, 15 seed (trigger="?")

adjacent_gap은 entity_key + field 조합이 특이한 경우 多 → 검색 결과 부족 가능성↑

## 수정 방향

### Fix 1 (primary, 1-line): cap 제거
- `src/nodes/mode.py:204-212` Phase 5 상태로 복원
- 예상 효과: target_count 10 → ~30 (open=60 기준)
- Risk: LLM 호출량 3x↑ (비용 고려)

### Fix 2 (secondary, 별도 조사 필요)
- LLM parse 수율 측정 로깅 추가 (target → claims 수 분포)
- query 품질 개선 (field 동의어, 한국어 쿼리 혼합)
- 또는 snippet 부족 시 다른 query로 retry

## Validation Plan

1. mode.py Phase 5 복원 (cap 제거)
2. 단위 테스트 — target_count 공식 검증
3. 15c trial 재실행 — gap_resolution 0.9 도달 cycle 수 확인
4. 비용 추적: LLM calls, tokens (목표: Phase 5 수준, ~5c 대비 3x 초과 금지)

## References

- session-compact.md § res_rate 조사 포인트
- `p3r-gate-trial-15c/trajectory/trajectory.csv`
- `src/nodes/mode.py:204-212` (current bug)
- commit `b122a23` (Phase 5 원형)
- commit `b12545d` (regression 도입)
- D-37, D-125, D-126
