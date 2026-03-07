# Phase 4: Self-Governing Evolver — Plan
> Created: 2026-03-07
> Last Updated: 2026-03-07
> Status: Suspended (11/11 tasks complete, Gate FAIL — Phase 5 보완 논의 필요)

## 1. 목적

단일 도메인(japan-travel)에서 **자기 진화 Evolver**로서의 완성도를 보장한다.
현재 시스템은 전술적 적응(per-cycle mode/budget 조정)은 강하지만,
**전략적 자기 진화**(정책 재설계, 임계치 자동 조율, 다축 균형 자기 진단)가 없다.

Multi-Domain 전환(Phase X) 전에 이 갭을 해소하지 않으면,
매 도메인마다 수동 튜닝이 필요한 "자동화 도구"에 불과하게 된다.

**프로젝트 궁극 목표**: Self-guided KU expansion — 어떤 도메인이든 Seed Pack만으로 자기 진화가 보장되는 Evolver.

## 2. 입력 조건

- Phase 3 완료 (301 tests, 9/9 tasks)
- 10 Cycle 실행 데이터: `bench/japan-travel-auto/`
- Phase 3 분석: Active 77, Disputed 0, conflict_rate 0.000, Health B
- 현재 결손 진단:
  - Policy 완전 정적 (전 cycle 불변)
  - Metrics → 행동 변경 피드백 루프 없음
  - Threshold/파라미터 자기 조율 없음
  - Outer Loop (Executive Audit) 미구현
  - 다축 교차 커버리지 자기 진단 없음

## 3. Phase 번호 체계 (갱신)

| Phase | 이름 | 성격 | 비고 |
|-------|------|------|------|
| 1~3 | Core → Bench → Quality | 확정 완료 | |
| **4** | **Self-Governing Evolver** | 확정 | 본 Phase |
| **X** | **Multi-Domain & Robustness** | **잠정(tentative)** | Stage D Gate 통과 후 번호 확정 |

- Phase X는 Stage D Gate 결과에 따라 번호가 결정된다:
  - **PASS** → Phase X = Phase 5
  - **FAIL** → 추가 Phase 5 삽입 (보완), Phase X = Phase 6

## 4. Stage 구성

### Stage A: Outer Loop Audit (Executive Audit 구현)
> **목표**: "무엇이 부족한지 스스로 안다"

- **4.1** Executive Audit 프레임워크 구현 `[L]`
  - N-cycle 단위 (기본 5 cycle) 자동 실행되는 Audit 노드
  - 입력: trajectory 전체 (metrics history, KU/GU 변화)
  - 출력: AuditReport (findings, recommendations, policy_patches)
  - Orchestrator에 audit 주기 통합

- **4.2** 다축 교차 커버리지 진단 `[M]`
  - category × geography × condition × risk 교차 매트릭스 계산
  - 셀별 KU 밀도 + 빈 셀(blind spot) 식별
  - "어떤 축 조합이 빈약한지" 정량화

- **4.3** KU Yield/Cost 효율 분석 `[M]`
  - cycle당 KU yield (new active / LLM calls)
  - category별 수확 체감 감지 (diminishing returns)
  - 탐색 방향 전환 근거 생성

### Stage B: Policy Evolution (정책 자동 재설계)
> **목표**: "진단 결과로 규칙을 스스로 바꾼다"

- **4.4** Policy 스키마 + 버전 관리 구현 `[M]`
  - `schemas/policy.json` 신규 (JSON Schema)
  - `policies.version` 필드 + 변경 이력 추적
  - 정책 변경 전/후 diff 로깅

- **4.5** Audit → Policy 자동 수정 경로 구현 `[L]`
  - AuditReport.policy_patches → policies.json 반영
  - 수정 가능 정책: TTL defaults, min_sources, credibility_priors, cross_validation 규칙
  - Safety: 변경 범위 상한 (한 Audit당 최대 3 필드)
  - Rollback: 변경 후 1 cycle 성능 악화 시 자동 복원

- **4.6** Source Credibility 학습 `[M]`
  - EU 정합성 추적: 어떤 source_type이 conflict/stale KU를 많이 생산하는지
  - credibility_priors 자동 조정 (상한/하한 guardrail)

### Stage C: Strategic Self-Tuning (파라미터 자기 조율)
> **목표**: "자기 파라미터를 스스로 조율한다"

- **4.7** Threshold 적응 메커니즘 `[L]`
  - C6 conflict_rate threshold, guard limits, convergence conditions
  - 방법: 최근 N cycle 실적 기반 이동 평균 + 표준편차
  - Guardrail: healthy 범위 내에서만 조정 (hard min/max)

- **4.8** Explore/Exploit 비율 학습 `[M]`
  - 현재: stage별 고정 (60/40 → 50/50 → 40/60)
  - 개선: KU yield by mode (explore vs exploit) 추적 → 비율 자동 조정
  - 탐색 수확 체감 시 exploit 증가, 새 axis gap 발견 시 explore 증가

- **4.9** Cost-Aware Budget 관리 `[M]`
  - LLM call / token budget per cycle 설정
  - Budget 초과 시 graceful degradation (수집 범위 축소)
  - Cycle당 비용 효율 추적 (KU/dollar proxy)

### Stage D: Evolver Readiness Gate (필수 체크포인트)
> **목표**: Multi-Domain 전환 자격 검증 — **이 Gate를 통과해야만 Phase X 진행**

- **4.10** Readiness 검증 벤치마크 실행 `[L]`
  - japan-travel에서 **Phase 4 기능 포함 15 Cycle** 재실행
  - Audit 최소 2회, Policy 수정 최소 1회 자동 발생 확인
  - 결과 데이터 수집 + 분석 보고서 생성

- **4.11** 3-Viewpoint Readiness 판정 `[M]`
  - 아래 3대 관점별 PASS/FAIL 판정
  - **전체 PASS → Phase X = Phase 5**
  - **1개 이상 FAIL → Phase 5 보완 삽입, Phase X = Phase 6**

## 5. Stage D: Evolver Readiness Gate — 3대 관점 상세

### Viewpoint 1: Expansion with Variability (다양성 있는 확장)

> KU 확장이 단일 방향 집중이 아닌 다축 분산인가?

| 기준 | 측정 방법 | PASS 조건 |
|------|-----------|-----------|
| 카테고리 균등도 | Shannon Entropy of KU per category | H ≥ 0.75 × H_max (H_max = log2(N_categories)) |
| 교차축 커버리지 | category × geography 매트릭스 비어있는 셀 비율 | blind_spot_ratio ≤ 0.40 |
| 신규 엔티티 발견률 | 후반 5 cycle에서도 새 entity 등장 여부 | ≥ 2 new entities in cycle 11~15 |
| 필드 다양성 | Gini coefficient of KU per field | Gini ≤ 0.45 |
| Explore 수확 | explore mode에서 생산된 KU 비율 | explore_yield ≥ 20% of total |

### Viewpoint 2: Completeness of Domain Knowledge (도메인 지식 완전성)

> 도메인 스켈레톤 기준으로 지식이 충분히 채워졌는가?

| 기준 | 측정 방법 | PASS 조건 |
|------|-----------|-----------|
| Gap 해소율 | resolved GU / (resolved + open GU) | gap_resolution_rate ≥ 0.85 |
| 카테고리별 최소 KU | 각 카테고리 최소 KU 수 | min(KU per category) ≥ 5 |
| Evidence 밀도 | multi_evidence_rate (2+ source) | ≥ 0.80 |
| Confidence 수준 | avg_confidence across active KU | ≥ 0.82 |
| Health Grade | Metrics Health 종합 | ≥ B (1.4/2.0) |
| Staleness | stale KU (TTL 초과) | staleness_risk ≤ 2 |

### Viewpoint 3: Self-Governance on System Evolution (시스템 진화 자기 통치)

> 시스템이 스스로 진단 → 정책 수정 → 행동 변경을 수행하는가?

| 기준 | 측정 방법 | PASS 조건 |
|------|-----------|-----------|
| Audit 자동 실행 | 15 cycle 중 Audit 실행 횟수 | ≥ 2 audits |
| Policy 자동 수정 | Audit에 의한 policy_patches 적용 횟수 | ≥ 1 policy change |
| Threshold 적응 | C6/guard threshold가 초기값에서 변경 | ≥ 1 threshold adaptation |
| Explore/Exploit 자동 조정 | 비율이 고정값에서 벗어난 cycle 수 | ≥ 3 cycles with adapted ratio |
| Policy Rollback 작동 | 악화 시 복원 메커니즘 테스트 통과 | rollback_test = PASS |
| Closed Loop 입증 | Audit finding → Policy patch → Behavior change → Metric improvement 체인 | ≥ 1 complete chain |

### Gate 판정 절차

```
1. 15 Cycle 실행 완료
2. 3대 관점 각각 기준 평가
3. 관점별 PASS = 모든 기준 충족 (또는 기준의 80% 이상 + 치명적 FAIL 없음)
4. 전체 판정:
   - 3/3 PASS → Phase X = Phase 5 확정
   - 1~2 FAIL → 실패 관점 분석 → Phase 5 보완 Phase 자동 생성
   - Phase 5 완료 후 Gate 재실행 → Phase X = Phase 6
```

## 6. 성공 기준 (Phase 4 전체)

| 지표 | Phase 3 (현재) | Phase 4 목표 |
|------|---------------|-------------|
| Policy 진화 | 정적 (불변) | ≥ 1 자동 수정 발생 |
| Audit 자동화 | 미구현 | N-cycle 주기 자동 실행 |
| Threshold 적응 | 하드코딩 | 실적 기반 자동 조정 |
| Explore/Exploit | stage별 고정 | yield 기반 동적 조정 |
| Readiness Gate | — | 3/3 PASS |

## 7. 리스크

| 리스크 | 심각도 | 완화 |
|--------|--------|------|
| Policy 자동 수정이 성능 악화 유발 | High | Rollback 메커니즘 + 변경 범위 상한 |
| Threshold 적응이 발산 | Medium | Hard min/max guardrail |
| 15 Cycle API 비용 | Medium | Budget cap + gpt-4.1-mini |
| Gate 기준이 너무 엄격/느슨 | Medium | 80% 기준 충족 + 치명적 FAIL 없음 규칙 |
| Audit 주기 최적값 불확실 | Low | 5 cycle 시작, 결과 보고 조정 |
