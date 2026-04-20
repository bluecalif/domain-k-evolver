# Entity 확보 전략 드래프트

## 목적

`Entity`는 이 시스템에서 단순 식별자 관리 문제가 아니라, `knowledge evolution`의 외연 확장과 KB 일관성을 동시에 좌우하는 핵심 축이다. 현재 POR에서는 field 수집과 generic knowledge 누적은 어느 정도 진행되지만, seed 밖 concrete entity를 점진적으로 확보하는 경로는 사실상 비어 있다. 따라서 본 문서는 `Entity` 확보 전략을 별도 축으로 정의한다.

## 문제 정의

현재 POR의 구조는 다음 한계를 가진다.

1. `신규 entity 유입`이 구조적으로 약하다.  
collect는 대체로 source GU의 `entity_key`를 claim에 그대로 복사하고, integrate는 이를 canonicalize 중심으로만 처리한다. 그 결과 seed 밖 concrete entity가 자연스럽게 유입되기 어렵다.

2. `entity 파편화`를 막는 능력이 제한적이다.  
같은 실체가 여러 `entity_key` 아래 분산 저장되면 KB가 성장한 것처럼 보여도 실제로는 파편화일 수 있다. 현재 canonicalize는 일부 표기 정리에 머무르며, duplicate KU는 entity 문제의 신호로 해석돼야 한다.

3. `field 확장`과 `entity 확장`이 분리되어 있다.  
entity가 늘지 않으면 field 확장은 generic knowledge 누적으로 흐르기 쉽고, 반대로 entity만 늘고 field가 붙지 않으면 KB는 얕은 목록에 머문다.

## Entity 우선순위 축

표 4 기준으로 `Entity` 영역의 우선순위는 두 가지로 압축된다.

1. `신규 entity 유입`  
seed 밖 실제 대상을 KB 안으로 들여오는 문제

2. `entity 정규화·통합`  
같은 실체를 하나의 entity로 모아 파편화를 막는 문제

이 두 축은 별개가 아니라, 함께 작동해야 한다. 신규 entity 유입이 늘어도 정규화·통합이 약하면 KB는 파편화되고, 정규화·통합만 강하고 신규 entity 유입이 없으면 KB는 기존 entity 주변만 맴돈다.

## Entity 진화 원칙

1. `entity`는 처음부터 전량 확정하지 않는다.  
초기에는 `category`, `field`, `entity frame`, 소수의 대표 seed entity만 둔다.

2. `entity`는 `candidate -> validated entity` 단계를 거쳐 승격한다.  
한 번 검색에 등장한 이름을 바로 entity로 확정하지 않고, 반복 등장과 source 다양성을 확인한 뒤 승격한다.

3. `entity discovery`는 frontier 인접 영역에서만 일어난다.  
무차별 전체 수집이 아니라, 현재 부족한 `category`, `field`, `geography`를 메우는 방향으로 후보를 찾는다.

4. `entity`와 `geography`는 분리하되 필요시 결합해 평가한다.  
기본은 `entity 본체 + geography 축`이며, area가 정체성의 핵심일 때만 area 포함 entity를 허용한다.

5. `entity`가 승격되면 즉시 해당 entity 기준 후속 GU를 연다.  
entity discovery는 끝이 아니라 `price`, `hours`, `location`, `how_to_use` 등 후속 수집의 시작점이어야 한다.

## Entity 정규화·통합 원칙

이 문서에서는 `canonicalize`, `alias`, `merge`, `duplicate KU 패턴 점검`을 세부 기술로 분리하지 않고 모두 `entity 정규화·통합`으로 묶어 본다.

핵심 원칙은 다음과 같다.

1. `duplicate KU`는 독립 문제가 아니라 entity 파편화의 관측 신호로 본다.
2. 같은 실체를 한 entity로 모으는 능력을 우선 강화한다.
3. `canonicalize`, `alias`, `merge`는 구현 단계에서 구분 가능하지만, 현재 운영 논의에서는 하나의 정규화·통합 축으로 다루는 것이 적절하다.

## 카테고리별 entity 모델 원칙

### 기본 원칙

- `attraction`, `transport`, `pass-ticket`, `connectivity`, `payment`, `regulation`은 concrete entity 중심으로 본다.
- `dining`, `accommodation`은 geography와의 결합이 중요하지만, entity key에 area를 상시 포함하지 않는다.
- 기본 모델은 `entity 본체 + geography 축`이며, area가 정체성의 핵심일 때만 예외적으로 area 포함 entity를 허용한다.

### 예시

- 기본 entity: `ryokan`, `business-hotel`, `izakaya`, `ramen-shop`
- geography 결합 표현: `ryokan @ hakone`, `izakaya @ shinjuku`
- 예외적 area 포함 entity: `tsukiji-outer-market`, `dotonbori`

## Entity Discovery Node

현재의 `wildcard`라는 표현은 의미가 약하므로, 앞으로는 이를 `entity discovery node`로 재정의하는 것이 적절하다. 이 노드는 category 수준에서 concrete entity 후보를 찾고, 이를 누적·검증해 validated entity로 승격하는 역할을 맡는다.

### 기본 흐름

1. 부족한 `category`, `field`, `geography`를 기준으로 discovery target을 정한다.
2. 규칙 기반 query template으로 기본 discovery query를 만든다.
3. 필요 시 LLM이 query를 보강하거나 재작성한다.
4. 검색 결과에서 concrete entity 후보를 추출해 `entity_candidates`에 적재한다.
5. 독립 source, 반복 등장, category 적합성을 확인한 뒤 validated entity로 승격한다.
6. 승격된 entity를 기준으로 후속 GU를 생성한다.

## Discovery Query 생성 방식

`entity discovery` query 생성은 `rule-first, LLM-assisted`가 적절하다.

### 기본 원칙

- 기본은 규칙 기반 template으로 생성한다.
- search yield가 낮거나 novelty 정체가 길어질 때만 LLM이 보강한다.
- query는 `category + field intent + geography(optional) + source hint` 조합으로 만든다.

### 예시

- `attraction / hours / kyoto`
  - `major attractions in Kyoto official opening hours`
  - `Kyoto temples shrines visitor hours official`

- `connectivity / where_to_buy`
  - `Japan eSIM tourist where to buy official`
  - `Japan pocket wifi airport pickup official`

- `dining / location / shinjuku`
  - `best izakaya areas in Shinjuku guide`
  - `popular ramen spots near Shinjuku Station`

- `accommodation / etiquette / hakone`
  - `ryokan etiquette in Hakone guide`
  - `Hakone ryokan stay rules official`

## Discovery 출력 구조

discovery node의 출력은 곧바로 KU가 아니라 `entity candidate`가 적절하다.

예:

- `name`
- `proposed_slug`
- `category`
- `geography`
- `candidate_type`
- `source_count`
- `supporting_sources`

이후 기준을 만족할 때 `entity_key`로 승격한다.

## 기대 효과

이 전략을 따르면 entity를 전량 사전 크롤링하는 방식으로 고정하지 않으면서도, cycle이 지날수록 KB가 실제 concrete entity를 점진적으로 확보하는 구조를 만들 수 있다. 즉 `knowledge evolution`은 단순 KU 누적이 아니라, `entity candidate`, `validated entity`, `후속 GU 확장`이 함께 진화하는 구조로 이해해야 한다.
