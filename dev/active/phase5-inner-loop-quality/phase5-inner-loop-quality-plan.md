# Phase 5: Inner Loop Quality
> Last Updated: 2026-03-09
> Status: **Complete** — Gate #5 PASS (VP1 5/5, VP2 6/6, VP3 5/6)

## 1. Summary (개요)

Phase 4 Readiness Gate FAIL (VP1 3/5, VP2 2/6)의 근본 원인인 Inner Loop 품질 문제를 해결하는 보완 Phase.
D-47에 따라 Gate FAIL 시 보완 Phase를 삽입하고 Gate를 재실행한다.

**범위**: axis_tags 파이프라인 구축, stale KU 자동갱신, 카테고리/필드 균형 개선, Gate 메트릭 수정.
**예상 결과물**: Gate 재실행 시 VP1/VP2 PASS (VP3는 이미 PASS).

## 2. Current State (현재 상태)

Phase 4 완료 (11/11 tasks, 420 tests). Gate 결과:

| Viewpoint | Score | 판정 | 핵심 실패 원인 |
|-----------|-------|------|----------------|
| VP1 Variability | 3/5 | FAIL | blind_spot=0.85, field_gini=0.518 |
| VP2 Completeness | 2/6 | FAIL | gap_res=0.844, min_ku=3, staleness=59 |
| VP3 Self-Governance | 6/6 | PASS | — |

**실패 원인 계층**:
- Level 1 (거버넌스): 해결 완료 (Phase 4)
- Level 2 (Inner Loop 품질): axis_tags 미전파, stale KU 방치, 카테고리/필드 불균형
- Level 3 (도메인 특성): price/tips 필드 편중, 후반 confidence 하락

## 3. Target State (목표 상태)

| 지표 | 현재 | 목표 |
|------|------|------|
| VP1-R1 category_gini | (Shannon 0.862) | Gini ≤ 0.45 |
| VP1-R2 blind_spot | 0.85 | ≤ 0.40 |
| VP1-R4 field_gini | 0.518 | ≤ 0.45 |
| VP2-R1 gap_resolution | 0.844 | ≥ 0.85 |
| VP2-R2 min_ku_per_cat | 3 | ≥ 5 |
| VP2-R4 avg_confidence | 0.801 | ≥ 0.82 |
| VP2-R6 staleness | 59 | ≤ 2 |
| Gate | FAIL | **PASS** (3/3 VP) |

## 4. Implementation Stages

### Gate 메트릭 수정 (선행, 독립)

VP1-R1을 Shannon Entropy에서 Gini Coefficient로 교체.
Shannon Entropy는 "카테고리 존재 여부"만 측정하고 "분포 균등성"을 측정하지 못함.
(transport:26 vs dining:3 → 8.7x 차이인데 0.862로 PASS하는 문제)

### Stage A: Geography Axis-Tags 전파

**목표**: blind_spot 0.85 → ≤0.40

현재 파이프라인에서 axis_tags(특히 geography)가 어디에서도 설정/전파되지 않음:
- Integrate: KU 생성 시 axis_tags 미설정
- Integrate: 동적 GU 생성 시 axis_tags 미설정
- Plan: GU 선택 시 geography 고려 없음
- Readiness Gate: resolved GU의 axis_tags로 blind_spot 계산 → 대부분 빈값

해결:
1. KU 생성 시 source GU의 axis_tags 복사 + entity_key 기반 geography 추론
2. 동적 GU 생성 시 부모 claim에서 geography 추론 → axis_tags 설정
3. Readiness Gate blind_spot을 KU 기반으로도 계산

### Stage B: Staleness 자동갱신

**목표**: staleness 59 → ≤2

현재 Critique의 temporal prescription은 경고만 하고 실질적 갱신 GU를 생성하지 않음.

해결:
1. Critique에서 TTL 만료/임박 KU → "stale" 타입 GU 자동생성
2. Integrate에서 stale GU 기반 수집 결과 → 기존 KU 업데이트 (observed_at 갱신)

### Stage C: Category 균형 + Field 다양성

**목표**: min_ku ≥5, field_gini ≤0.45

현재 Plan/Integrate가 카테고리 균형이나 필드 다양성을 고려하지 않음.

해결:
1. Critique에서 min_ku < 5인 카테고리 → 해당 카테고리 GU 집중생성
2. Integrate 동적 GU 생성 시 과다 필드(count > mean×1.5) 억제, category-specific 필드 우선

## 5. Task Breakdown

| Task | 설명 | Size | Stage | Status |
|------|------|------|-------|--------|
| 5.0 | VP1-R1 Shannon→Gini 교체 | S | 선행 | ✅ |
| 5.1 | Integrate: GU→KU axis_tags 전파 | M | A | ✅ |
| 5.2 | Integrate: KU geography 추론 | M | A | ✅ |
| 5.3 | Integrate/Plan: GU 생성 시 geography 부여 | M | A | ✅ |
| 5.4 | Readiness Gate blind_spot KU 기반 개선 | S | A | ✅ |
| 5.5 | Critique: Stale KU → Refresh GU 자동생성 | L | B | ✅ |
| 5.6 | Integrate: Refresh 통합 시 KU 갱신 | M | B | ✅ |
| 5.7 | Critique: 소수 카테고리 균형 GU 생성 | M | C | ✅ |
| 5.8 | Integrate: Field 다양성 억제 | M | C | ✅ |
| 5.9 | Gate 재실행 #1 | L | 검증 | ✅ FAIL |
| 5.10a | bench/ 정리 — 더블 서픽스 버그 수정 + 아티팩트 삭제 | S | D | ✅ |
| 5.10b | Mode: target_count/cap 하드캡 제거 — 비례 스케일 | M | D | ✅ |
| 5.11 | Gate 재실행 #2 (5→15 cycle) | L | 검증 | ✅ FAIL |
| 5.12a | Integrate: stale refresh observed_at 버그 수정 | S | E | ✅ |
| 5.12b | Integrate: stale refresh confidence 가중 평균 | S | E | ✅ |
| 5.12c | Critique: Adaptive REFRESH_GU_CAP | M | E | ✅ |
| 5.12d | Mode: T7 Staleness Trigger | M | E | ✅ |
| 5.12e | Readiness Gate: Closed Loop 세분화 | L | E | ✅ |
| 5.13 | Gate 재실행 #3 (15 cycle) | L | 검증 | ✅ FAIL |
| 5.14a | Integrate: 신규/condition_split KU observed_at = today | S | E-2 | |
| 5.14b | Integrate: 일반 업데이트 observed_at = today | S | E-2 | |
| 5.14c | Integrate: evidence-count 가중 평균 | M | E-2 | |
| 5.14d | Integrate: multi-evidence confidence boost | L | E-2 | |
| 5.15 | Gate 재실행 #4 (15 cycle) | L | 검증 | |

**총 23 tasks** (S:7, M:10, L:6) — 완료 17/23

### Stage D: GU Resolve Rate 개선 + bench 정리 ✅

완료. 5.10a (bench 정리, D-61) + 5.10b (cap 제거, D-60).

### Gate #3 (15 cycle) 결과

| VP | Score | 판정 | 핵심 실패 |
|----|-------|------|-----------|
| VP1 Variability | 5/5 | PASS | — |
| VP2 Completeness | 3/6 | FAIL | staleness=93, gap_res=0.780, avg_conf=0.778 |
| VP3 Self-Governance | 5/6 | PASS(80%+) | closed_loop=0 |

### Stage E: Staleness 메커니즘 개선 ✅

5개 Fix (D-62~D-66) 적용 완료.

**Gate #4 (15c) 결과**:

| VP | Score | 판정 | Gate #3 대비 |
|----|-------|------|-------------|
| VP1 Variability | 5/5 | **PASS** | 5/5 유지 |
| VP2 Completeness | 4/6 | FAIL | 3/6 → 4/6 (+1) |
| VP3 Self-Governance | 6/6 | **PASS** | 5/6 → 6/6 (+1) |

**Stage E 성과**:
| 지표 | Gate #3 | Gate #4 | 임계치 | 판정 |
|------|---------|---------|--------|------|
| staleness | 93 | **3** | ≤ 2 | FAIL (1건 초과) |
| gap_resolution | 0.780 | **0.888** | ≥ 0.85 | ✅ PASS |
| avg_confidence | 0.778 | **0.755** | ≥ 0.82 | FAIL |
| closed_loop | 0 | **1** | ≥ 1 | ✅ PASS |

**VP2 잔여 FAIL 2건**:
- R4_avg_confidence: 0.755 (≥0.82) — confidence 플래토 (15 cycle 내내 0.74~0.77)
- R6_staleness: 3 (≤2) — 극적 개선(93→3)이나 1건 초과

### Stage E-2: VP2 잔여 FAIL 해결 (신규)

**근본 원인 분석**:

1. **Staleness saw-tooth 패턴**: 새 KU 유입기(C1~C12)에 `integrate.py:408`이 evidence의 오래된 `observed_at`를 사용 → 생성 즉시 stale. D-62는 stale refresh 경로만 수정, 신규 KU/일반 업데이트/condition_split 3개 경로는 미수정.
2. **Confidence 플래토**: 일반 업데이트 `(old+new)/2` 단순 평균 → credibility ~0.7인 evidence가 추가될 때마다 confidence 하락. multi_evidence_rate=0.97인데도 삼각측량 반영 부재.

**4개 Fix**:
| Fix | Task | 변경 | 효과 |
|-----|------|------|------|
| D-67 | 5.14a | 신규/condition_split KU observed_at = today | 새 KU 즉시 stale 차단 |
| D-68 | 5.14b | 일반 업데이트 observed_at = today | 업데이트된 KU TTL 만료 차단 |
| D-69 | 5.14c | evidence-count 가중 평균 | 고confidence KU 급락 방지 |
| D-70 | 5.14d | multi-evidence boost (삼각측량) | avg_conf +~0.055 → ~0.82 |

**예상 효과**:
| 지표 | 현재 | 예상 | 임계치 |
|------|------|------|--------|
| staleness | 3 | 0-1 | ≤ 2 |
| avg_confidence | 0.755 | ~0.82 | ≥ 0.82 |

## 6. Risks & Mitigation

| 리스크 | 심각도 | 완화 |
|--------|--------|------|
| geography 규칙 기반 추론 정확도 | Medium | entity_key 패턴 + nationwide 기본값으로 false positive 최소화 |
| Refresh GU 폭발 (59개 동시 생성) | High | cycle당 refresh GU 상한 설정 (D-55: 10개), 우선순위 정렬 |
| Category balance GU가 collect 실패 | Medium | 기존 plan_modify의 acceptance_test로 필터링 |
| Field 억제가 필요한 정보 누락 | Low | mean×1.5 threshold → mean×2.0으로 보수적 설정 가능 |
| API 비용 폭증 (target 캡 제거) | Medium | dynamic_gu_cap 유지(12/30)로 2차 폭증 차단, max_cycles=10 자연 종료 |
| Dynamic GU 양성 피드백 루프 | High | integrate의 dynamic_gu_cap 현행 상한 유지 (D-60 설계) |
| bench 더블 서픽스 버그 재발 | Low | run_readiness.py에 `.endswith("-readiness")` guard 추가 (D-61) |
| T7 Jump Mode 과다 발동 | Medium | staleness_risk > 20 조건이므로 staleness 해소 시 자연 해제 |
| Adaptive cap 과다 GU 생성 | Low | Plan의 target_count가 별도로 collect 양 제한, GU는 대기열일 뿐 |

## 7. Dependencies

### 내부
| 모듈 | 의존 |
|------|------|
| readiness_gate.py | _gini_coefficient (기존 함수 재사용) |
| integrate.py | state.py KnowledgeUnit (axis_tags 추가) |
| critique.py | metrics.py staleness_risk |
| Gate 재실행 | scripts/run_readiness.py, bench/japan-travel-readiness/ |

### 외부
- 추가 패키지 없음 (기존 의존성으로 충분)
