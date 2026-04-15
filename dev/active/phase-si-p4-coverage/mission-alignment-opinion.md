x# P4 미션 정렬 의견서

> 작성일: 2026-04-15
> 기준 문서: `mission-alignment-critique.md`
> 목적: 기존 비판 내용을 더 정돈된 의사결정 메모 형태로 재정리

## 1. 의견

기존 비판은 대체로 타당하다.

현재 P4는 의미 없는 작업은 아니지만, 본질적으로는 **외부 세계를 넓게 개척하는 계층**이라기보다 **내부 커버리지 최적화 계층**에 가깝다.

현재 P4가 잘하는 일:
- cycle 간 novelty 측정
- deficit, Gini 기반의 기존 카테고리 균형 조정
- planning reason code 부여
- 반응형 category 관리 지원

현재 P4가 아직 충분히 못하는 일:
- 전체 누적 이력 기준 novelty 측정
- 현재 skeleton 바깥의 미개척 영역 추정
- 빠진 category/axis를 선제적으로 탐색
- 시스템이 이미 아는 공간만 재배열하고 있을 때 바깥으로 피벗

핵심 문제는 이것이다.  
현재 구조에서는 내부 지표가 좋아져도, 실제 미션인 **지식 프런티어 확장**에는 실패할 수 있다.

## 2. 달성 가능한 목표

가까운 목표를 다음처럼 잡는 것은 무리다.

> "universe coverage를 해결한다"  
> "P4만으로 완전한 미션 정렬을 증명한다"

대신 현실적인 목표는 다음이어야 한다.

> 시스템이 지금 하고 있는 일이 단지 이미 아는 영역 내부의 균형 조정인지, 아니면 실제로 새 영역으로 나가고 있는지 구분할 수 있게 만든다

즉, 달성 가능한 목표는 다음과 같다.

- 현재 P4는 **내부 커버리지 기반층**으로 유지한다
- 그 위에 최소한의 **external anchor 계층**을 추가한 뒤에야 P4를 완전 통과로 본다

이 목표가 가능한 이유는 현재 코드베이스에 이미 필요한 접점이 있기 때문이다.
- novelty 유틸리티
- planning reason code
- plateau detector
- remodel hook
- coverage 및 metrics 상태 저장 구조

## 3. 권장 재정의

P4는 두 층으로 나눠서 보는 것이 맞다.

### A. Internal Coverage Foundation

여기에는 현재 P4의 주요 작업이 포함된다.
- cycle novelty
- coverage deficit map
- Gini imbalance 감지
- machine-readable critique 출력
- reason-code 기반 planning
- 보수적 category addition 지원

이 작업은 계속 가치가 있다.  
다만 이것을 **내부 유도 인프라**로 정직하게 규정해야 한다.

### B. External Anchor

미션 정렬을 주장하려면, 최소한 다음 질문에 답할 수 있어야 한다.

- 이번 cycle의 결과가 과거 전체 이력에도 없던 새로운 영역인가?
- 더 다양한 출처와 맥락으로 뻗고 있는가?
- 현재 skeleton 밖에 중요한 category나 axis가 남아 있는가?
- 성장이 멈췄을 때, known space 정리만 하는가 아니면 바깥으로 피벗하는가?

## 4. 달성 방법

올바른 방법은 전면 재설계가 아니다.  
현재 P4 위에 얇은 external layer를 하나 더 얹는 방식이 가장 현실적이다.

### 4.1 External novelty metric

novelty를 단순히
- 이전 cycle vs 현재 cycle

로만 보지 말고,
- 현재 발견물 vs 전체 누적 이력

도 함께 봐야 한다.

첫 구현은 다음 정도면 충분하다.
- entity-key 기준 history novelty

후속 확장 후보:
- claim 단위 novelty
- semantic novelty

### 4.2 Universe probe

주기적으로 넓은 survey를 돌려서 다음을 묻는 단계가 필요하다.
- 현재 skeleton에 빠진 중요한 category/subdomain/axis가 무엇인가?

가능한 입력원:
- broad Tavily query
- Wikipedia category enumeration
- 기존 provider/domain 요약
- LLM 기반 survey prompt

여기서 중요한 점은 자동 확장이 아니라 **제안 생성**이어야 한다는 것이다.

### 4.3 Reach diversity ledger

탐색 폭은 cycle 단위가 아니라 전체 run 단위로 기록해야 한다.

유용한 추적 축:
- distinct domain
- publisher / author 다양성
- language 다양성
- time-range 다양성
- provider 다양성

이 지표가 있어야 시스템이 같은 세계 조각만 반복 탐색하는지 드러난다.

### 4.4 Plateau pivot action

novelty가 정체됐을 때의 액션도 바꿔야 한다.

현재처럼 audit/remodel 중심으로 known structure만 정리하면 미션과 어긋난다.  
정체 시에는 명시적인 exploration pivot가 필요하다.

예시:
- 더 넓은 query
- 다른 provider 사용
- 다른 언어 창구 사용
- 다른 시간 구간 탐색
- long-tail query 생성

이 부분이 미션과 가장 직접적으로 연결되는 행동 변화다.

### 4.5 Planning integration

외부 신호는 planning reason code로 흘려보내면 된다.

예시:
- `external_novelty:deficit`
- `universe_probe:missing_category`
- `reach_diversity:low`
- `plateau:exploration_pivot`

이렇게 하면 전체 시스템을 갈아엎지 않고도 기존 planning 계층이 external-anchor 신호를 사용할 수 있다.

## 5. 구체적 권고

현재 상태의 P4를 **완전한 미션 정렬 통과**로 선언하면 안 된다.

대신 다음 둘 중 하나로 정리하는 것이 맞다.

### 옵션 1. 권장

현재 P4 범위는 유지하되 이름을 다음처럼 바꾼다.

> Internal Coverage Foundation

그 다음 짧은 Stage E / External Anchor gate를 추가한 뒤 최종 통과를 판정한다.

### 옵션 2. 차선

P4 안에 external-anchor 최소 집합만 바로 포함한다.
- external novelty
- universe probe
- reach diversity
- plateau exploration pivot

그리고 더 어려운 항목, 예를 들어 더 정교한 universe estimation이나 semantic novelty는 P5로 넘긴다.

## 6. 최소 성공 기준

의미 있는 미션 정렬 진전을 주장하려면, 최소한 아래는 가능해야 한다.

- cycle 차이와 history-level novelty를 구분한다
- 전체 run 기준 reach diversity 부족을 감지한다
- 기존 skeleton 밖의 누락 category를 일정 수준 이상 표면화한다
- plateau 조건에서 outward exploration을 트리거한다
- 이 상태를 machine-readable reason으로 planning에 연결한다

## 7. 즉시 다음 단계

가장 현실적인 다음 스텝은 다음과 같다.

1. 기존 P4 구현 작업은 유지한다
2. 다만 상태 명칭은 internal-foundation 성격으로 조정한다
3. 작은 External Anchor slice를 정의한다
4. 최종 pass 기준은 internal balance만이 아니라 그 slice까지 포함해 잡는다

## 8. 결론

이 비판의 요지는 "P4가 쓸모없다"가 아니다.

요지는 "현재 P4가 실제 역할보다 과장되어 있다"는 것이다.

달성 가능한 목표는 시스템이 지금 known territory 최적화만 하고 있는지, 실제로 바깥으로 확장 중인지 구분하게 만드는 것이다.  
그 방법은 history-aware novelty, universe probe, reach-diversity tracking, plateau 시 exploration pivot를 추가하는 얇은 external-anchor 계층을 올리는 것이다.
