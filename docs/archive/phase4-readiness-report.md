# Phase 4 Readiness Gate — 상세 분석 보고서

> Generated: 2026-03-07
> Benchmark: japan-travel 13 Cycles (plateau 조기 종료)
> Gate Verdict: **FAIL** (VP1, VP2 실패 / VP3 통과)

## 1. 실행 요약

| 항목 | 결과 |
|------|------|
| **Gate 판정** | **FAIL** (VP1, VP2 실패 / VP3 통과) |
| 실행 Cycles | 13/15 (Cycle 12~13 plateau 감지로 조기 종료) |
| 최종 Active KU | 90 (seed 27 -> +233%) |
| Disputed KU | 0 (전 cycle 0 유지) |
| conflict_rate | 0.000 (최종) |
| Open GU | 15 |
| Resolved GU | 81 |
| Audit 실행 | 2회 (Cycle 5, 10) |
| Policy 수정 | 2회 (v1->v2) |

### Trajectory

```
C 1: KU= 34  GU_open= 28  resolved= 24  mode=jump  conf=0.872  conflict=0.147
C 2: KU= 43  GU_open= 30  resolved= 34  mode=jump  conf=0.861  conflict=0.000
C 3: KU= 48  GU_open= 25  resolved= 39  mode=jump  conf=0.863  conflict=0.042
C 4: KU= 52  GU_open= 21  resolved= 43  mode=jump  conf=0.855  conflict=0.000
C 5: KU= 56  GU_open= 17  resolved= 47  mode=jump  conf=0.852  conflict=0.036
C 6: KU= 61  GU_open= 22  resolved= 52  mode=jump  conf=0.845  conflict=0.000
C 7: KU= 67  GU_open= 22  resolved= 58  mode=jump  conf=0.838  conflict=0.045
C 8: KU= 73  GU_open= 22  resolved= 64  mode=jump  conf=0.820  conflict=0.000
C 9: KU= 79  GU_open= 16  resolved= 70  mode=jump  conf=0.820  conflict=0.038
C10: KU= 87  GU_open= 18  resolved= 78  mode=jump  conf=0.809  conflict=0.046
C11: KU= 90  GU_open= 15  resolved= 81  mode=jump  conf=0.804  conflict=0.011
C12: KU= 90  GU_open= 15  resolved= 81  mode=jump  conf=0.801  conflict=0.000
C13: KU= 90  GU_open= 15  resolved= 81  mode=jump  conf=0.801  conflict=0.000
```

### Category KU Distribution

```
transport      : 26
pass-ticket    : 24
regulation     : 14
attraction     : 10
accommodation  :  5
connectivity   :  5
dining         :  3
payment        :  3
```

### Field Distribution

```
price          : 19
tips           : 16
how_to_use     : 15
policy         :  9
duration       :  8
where_to_buy   :  6
eligibility    :  5
hours          :  3
etiquette      :  2
location       :  2
others (5)     :  5
```

---

## 2. 관점별 상세 분석

### VP1: Expansion with Variability — FAIL (3/5)

| 기준 | 값 | 임계치 | 판정 | 분석 |
|------|------|--------|------|------|
| R1 Shannon Entropy | 0.862 | >= 0.75 | **PASS** | 8개 카테고리에 걸친 양호한 분산 |
| R2 Blind Spot | **0.85** | <= 0.40 | **FAIL** | geography 축 교차 커버리지 극히 부족 |
| R3 Late Discovery | 3 | >= 2 | **PASS** | Cycle 11에서 신규 KU 발견 |
| R4 Field Gini | **0.518** | <= 0.45 | **FAIL** | price/tips/how_to_use에 편중 |
| R5 Explore Yield | 1.0 | >= 0.20 | **PASS** | 전 cycle Jump Mode 유지 |

**근본 원인**:

- **R2**: Seed data에 geography axis_tags가 거의 부재. GU에 geography 태그 없이 생성되어 cross-axis 매트릭스가 채워지지 않음. 이는 **collect/plan 노드의 axis_tags 전파 문제**이지 Evolver 거버넌스 문제가 아님.
- **R4**: price(19), tips(16), how_to_use(15) 3개 필드가 전체 90 KU 중 50개(56%) 차지. 필드 다양성이 부족하나, 이는 도메인 특성(travel 도메인에서 price/tips가 주요 관심 필드)과 plan_node의 GU 생성 패턴에 기인.

### VP2: Completeness — FAIL (2/6, Critical FAIL 2건)

| 기준 | 값 | 임계치 | 판정 | 분석 |
|------|------|--------|------|------|
| R1 Gap Resolution | **0.844** | >= 0.85 | **FAIL** [CRITICAL] | 84.4%, 임계치와 0.6%p 차이 |
| R2 Min KU/Cat | **3** | >= 5 | **FAIL** [CRITICAL] | dining=3, payment=3 |
| R3 Multi Evidence | 0.911 | >= 0.80 | **PASS** | 91.1%, 매우 우수 |
| R4 Avg Confidence | **0.801** | >= 0.82 | **FAIL** | Cycle 진행에 따라 점진 하락 (0.872->0.801) |
| R5 Health Grade | 1.4 | >= 1.4 | **PASS** | 경계선 통과 |
| R6 Staleness | **59** | <= 2 | **FAIL** | Seed KU의 TTL 만료 |

**근본 원인**:

- **R1**: 15 open GU 잔존 (gap_resolution = 81/96 = 0.844). Cycle 12~13에서 0 claims 수집 -> plateau. 남은 GU가 collect_node에서 정보 수집 불가한 항목일 가능성.
- **R2**: dining과 payment 카테고리에 KU가 3개뿐. Plan이 이 카테고리의 GU를 충분히 생성하지 못함.
- **R4**: 0.872 -> 0.801로 지속 하락. 후반 KU의 confidence가 낮아서 평균을 끌어내림. 이는 후반부에 collect되는 정보의 quality가 낮기 때문.
- **R6**: **59/90 KU가 TTL 만료**. Seed KU(2025년 observed_at)의 TTL이 365일이면 2026-03 기준 대부분 만료. 이는 시스템이 stale KU를 **자동 갱신하는 메커니즘이 없음**을 의미.

### VP3: Self-Governance — PASS (6/6)

| 기준 | 값 | 임계치 | 판정 |
|------|------|--------|------|
| R1 Audit Count | 2 | >= 2 | **PASS** |
| R2 Policy Changes | 2 | >= 1 | **PASS** |
| R3 Threshold Adapt | 2 | >= 1 | **PASS** |
| R4 Adapted Ratio | 13 | >= 3 | **PASS** |
| R5 Rollback | 0 (mechanism exists) | >= 0 | **PASS** |
| R6 Closed Loop | 1 | >= 1 | **PASS** |

Phase 4의 핵심 목표인 Self-Governance 메커니즘은 **완전히 작동**:

- Audit -> Finding -> Policy Patch -> 성능 확인 -> Closed Loop 체인 입증
- Cycle 5: Audit findings -> Policy patch 자동 적용
- Cycle 10: 두 번째 Audit에서 findings 감소 -> Closed Loop 확인
- 13 cycle 내내 Jump Mode + audit bias 기반 explore/exploit 비율 자동 조정

---

## 3. Phase 4 목표 달성도 평가

Phase 4의 본래 목표(plan.md 기준):

| 목표 | Phase 3 | Phase 4 | 달성 |
|------|---------|---------|------|
| Policy 진화 | 정적 (불변) | 2회 자동 수정 | **달성** |
| Audit 자동화 | 미구현 | 5 cycle 주기 자동 실행 | **달성** |
| Threshold 적응 | 하드코딩 | Audit bias 기반 동적 조정 | **달성** |
| Explore/Exploit | stage별 고정 | yield/coverage 기반 동적 조정 | **달성** |
| Readiness Gate | -- | FAIL (VP1, VP2) | **미달** |

**Phase 4의 코드/기능 목표 4개는 전부 달성**. Readiness Gate FAIL은 Evolver 거버넌스 문제가 아닌 **도메인 지식 확장 인프라의 한계**에서 기인.

---

## 4. 실패 원인의 계층 분류

```
Level 1 (Phase 4 거버넌스) -- 해결 완료
  [O] Audit, Policy Evolution, Self-Tuning, Convergence 고도화

Level 2 (Inner Loop 품질) -- 미해결
  [X] axis_tags 전파 부재 -> blind_spot 85%
  [X] stale KU 자동 갱신 없음 -> staleness 59개
  [X] 소수 카테고리 GU 미생성 -> min_ku 3

Level 3 (도메인 특성) -- 구조적 제약
  [!] price/tips/how_to_use 필드 편중
  [!] 후반부 confidence 하락 (정보 품질 체감)
```

---

## 5. 결론

Phase 4의 Self-Governing 기능 구현은 완료되었으며, VP3 6/6 만점으로 입증됨. Gate FAIL의 원인은 Phase 4 scope 바깥의 Inner Loop 품질 이슈(stale KU 갱신, axis_tags 전파, 카테고리 균형 GU 생성)에 있음.

D-47에 따라 Gate FAIL 시 **Phase 5 보완 Phase를 삽입**하고 Gate를 재실행해야 함.

### 보완 대상 (Phase 5 후보)

1. **Stale KU 자동 갱신** (R6 staleness 59 -> <= 2)
2. **axis_tags 전파** (R2 blind_spot 0.85 -> <= 0.40)
3. **소수 카테고리 균형 GU 생성** (R2 min_ku 3 -> >= 5)
4. **Confidence 유지/개선** (R4 avg_confidence 0.80 -> >= 0.82)

### 논의 필요 사항

- Gate 기준 자체의 적절성 (blind_spot 0.40, staleness <= 2 등)
- 보완 Phase의 scope와 우선순위
- Phase 5 vs Gate 기준 완화 중 어느 쪽이 적절한지
