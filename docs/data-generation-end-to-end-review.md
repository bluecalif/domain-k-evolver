# 데이터 생성 파이프라인 End-to-End 재구성 문서

## 0. 문서 목적

이 문서는 현재 `domain-k-evolver`의 데이터 생성 파이프라인을 "무엇이 실행되는가" 수준이 아니라 "왜 그 판단을 하는가", "어떤 상태를 다음 단계로 넘기는가", "어디서 실패하는가", "어떤 신호가 튜닝을 발동시키는가"까지 포함해 재구성한 설명서다.

핵심 초점은 다음 두 축이다.

1. `Open GU`를 중심으로 돌아가는 내부 파이프라인의 실제 논리
2. 파이프라인이 정체되거나 구조적으로 틀어질 때 발동되는 튜닝 프로세스

이 문서는 분량 자체를 목표로 하지 않는다. 대신 운영자, 설계자, 후속 구현자가 반드시 알아야 할 결정 기준과 실패 지점을 빠뜨리지 않는 것을 목표로 한다.

---

## 1. 한 줄 요약

현재 시스템은 단순한 `GU -> claim -> KU` 변환기가 아니다.  
정확히는 다음과 같은 2계층 시스템이다.

- 내부 루프: `Open GU`를 선택해 claim을 수집하고, 이를 KU로 통합하며, 그 결과로 다시 새로운 GU를 생성한다.
- 외부 루프: 내부 루프의 산출 품질과 정체 신호를 감시하다가, 필요하면 탐색 방향을 틀거나(`Explore Pivot`), 구조 자체를 손본다(`Remodel`).

즉 이 시스템의 본질은 "지식을 쌓는 시스템"이 아니라 "어떤 결손을 어떤 순서로 메우고, 메운 결과로 다음 결손을 재정의하는 시스템"이다.

---

## 2. 시스템을 읽는 기본 관점

### 2.1 핵심 객체

- `GU (Gap Unit)`: 아직 메워지지 않은 질문 또는 결손
- `Open GU`: 지금도 해결 대상인 GU
- `claim`: 외부 수집 결과에서 뽑아낸 주장 단위
- `KU (Knowledge Unit)`: 통합된 상태의 지식 단위
- `Evidence Unit`: claim을 지탱하는 증거 단위

### 2.2 핵심 상태

파이프라인을 이해할 때 가장 중요한 상태는 다음이다.

- `gap_map`: 전체 GU 집합
- `knowledge_units`: 현재까지 통합된 KU 집합
- `current_plan`: 이번 cycle에서 어떤 GU를 어떤 쿼리로 수집할지
- `current_claims`: 이번 cycle에서 수집된 claim 집합
- `coverage_map`: 어느 축/카테고리가 비어 있는지에 대한 커버리지 정보
- `remodel_report`: 구조 변경 제안
- `probe_history`, `pivot_history`: 외부 탐색 실험 이력

### 2.3 파이프라인의 실제 질문

각 cycle은 사실상 아래 질문을 순서대로 푼다.

1. 지금 해결할 `Open GU`는 무엇인가?
2. 그 GU를 해결하려면 어떤 claim이 필요하고, 어떤 방식으로 수집해야 하는가?
3. 수집한 claim 중 어떤 것은 KU가 되고, 어떤 것은 보류/충돌 처리되는가?
4. 방금 얻은 KU 때문에 새로 열려야 하는 GU는 무엇인가?
5. 최근 cycle들이 실제 진전을 만들고 있는가, 아니면 구조/탐색 전략을 바꿔야 하는가?

---

## 3. 전체 흐름

### 3.1 Inner Loop

```text
seed
  -> mode
  -> plan
  -> collect
  -> integrate
  -> critique
  -> plan_modify
```

### 3.2 Outer Loop

```text
inner loop 완료
  -> metrics/novelty/reach/coverage 재계산
  -> executive audit
  -> universe_probe
  -> exploration_pivot
  -> remodel
  -> state / snapshot / telemetry 저장
```

중요한 점은, inner loop는 "현재 열려 있는 질문을 푸는 루프"이고, outer loop는 "질문을 푸는 방식이 아직 유효한지 점검하는 루프"라는 점이다.

---

## 4. Core Logic on Pipeline

## 4.1 Open GU란 무엇인가

`Open GU`는 단순한 TODO가 아니다. 시스템이 다음 수집 cycle에서 다뤄도 된다고 승인한 결손 단위다.

일반적으로 GU는 다음 속성을 가진다.

- `gu_id`
- `gap_type`: `missing`, `stale`, `conflicting` 등
- `target`: 보통 `entity_key + field`
- `risk_level`
- `expected_utility`
- `resolution_criteria`
- `status`: `open`, `resolved`, `deferred`
- `trigger`, `trigger_source`

### Open GU가 중요한 이유

- plan은 임의 질문을 만들지 않고 `Open GU`만 대상으로 삼는다.
- collect는 쿼리 중심이 아니라 `GU 중심`으로 움직인다.
- integrate는 claim을 KU로 바꾸는 동시에 일부 GU를 닫고, 일부 GU를 새로 연다.

즉 `Open GU`는 내부 파이프라인의 입력 대기열이자, 시스템이 현재 무엇을 모르는지에 대한 공식 표현이다.

---

## 5. Target Setting: Open GU에서 실제 수집 대상을 정하는 논리

이 문맥에서 "Target Setting"은 `mode + plan`의 합성 결과로 보는 것이 맞다.  
즉 "이번 cycle에서 어떤 Open GU를 어떤 우선순위로 실제 수집 대상으로 삼을지"를 결정하는 단계다.

### 5.1 입력 데이터

- `gap_map`의 `open` 상태 GU
- `coverage_map`
- 현재 mode (`normal`, `jump`)
- novelty / external novelty / reach 관련 신호
- critique prescription
- pending 상태의 `remodel_report`
- universe probe 또는 pivot의 후보 신호

### 5.2 내부 판단 기준

#### 1. 대상은 반드시 Open GU여야 한다

이 시스템은 자유 검색기로 설계되지 않았다.  
따라서 target 선정의 1차 필터는 "지금 open 상태인가"다.

#### 2. 같은 Open GU라도 우선순위는 다르다

대표적으로 다음 요소가 우선순위에 관여한다.

- 커버리지 결손이 큰 카테고리인지
- `expected_utility`가 높은지
- `risk_level`이 높은지
- 최근 novelty 정체를 깨는 데 도움이 되는지
- universe probe가 제안한 신규 축/카테고리와 이어지는지
- remodel pending 상태에서 구조 검증상 의미가 있는지

#### 3. mode가 selection bias를 바꾼다

- `normal`: 이미 알려진 축 내부에서 커버리지/정밀도 개선 중심
- `jump`: 정체 구간 탈출을 위해 탐색 폭을 넓히는 쪽으로 가중

즉 target setting은 고정 정렬이 아니라, 현재 탐색 태세(mode)에 따라 exploit와 explore의 비중이 달라지는 가변 정렬이다.

### 5.3 데이터 흐름

```text
Open GU 집합
  -> coverage / novelty / pivot / remodel 신호 결합
  -> 우선순위 재정렬
  -> exploit 대상 + explore 대상 선택
  -> current_plan 생성
```

`current_plan`에는 보통 다음 정보가 들어간다.

- `target_gaps`
- `queries`
- `budget`
- selection reason에 해당하는 암묵적 또는 명시적 코드

### 5.4 가능한 실패 지점

#### 실패 1. Open GU는 많은데 실제로는 같은 지역만 계속 고르는 경우

원인:

- coverage 보정이 약함
- novelty 정체 신호가 plan에 충분히 반영되지 않음
- explore budget이 너무 낮음

결과:

- 수집은 계속되지만 새로운 영역으로 퍼지지 않음

#### 실패 2. high-risk나 high-utility GU가 묻히는 경우

원인:

- 정렬 기준이 단일 점수에 과도하게 압축됨
- risk/utility와 diversity 목표가 충돌함

결과:

- 중요하지만 어렵거나 비싼 질문이 영구적으로 뒤로 밀림

#### 실패 3. remodel pending인데도 plan이 이전 구조 가정대로 움직이는 경우

원인:

- 구조 변경이 아직 승인되지 않았는데 selection이 기존 skeleton에 과적합됨

결과:

- 틀린 구조 위에서 계속 데이터를 수집

#### 실패 4. target은 적절했지만 query 설계가 target semantics를 보존하지 못하는 경우

원인:

- GU의 `resolution_criteria`가 query로 번역되지 않음
- 조건부 필드가 단일 문장 검색으로 납작해짐

결과:

- collect는 결과를 가져오지만 integrate 가능한 claim이 적음

### 5.5 이 단계의 산출물이 좋아졌다고 볼 기준

- 선정된 target이 `Open GU`와 정확히 연결된다.
- 각 target이 왜 뽑혔는지 설명 가능하다.
- 특정 카테고리 정체 시 selection 분포가 실제로 이동한다.
- 정체 신호가 plan에 반영되어 target 세트가 달라진다.

---

## 6. KU Generation: claim -> integrate의 실제 내부 논리

사용자 관점에서 KU 생성은 한 단계처럼 보이지만, 실제로는 `collect`와 `integrate`의 결합이다.

### 6.1 단계 1: claim 생성

#### 입력

- `current_plan.target_gaps`
- `queries`
- 검색/수집 도구
- 현재 mode

#### 핵심 논리

collect는 "무엇을 검색할까?"보다 "어떤 GU를 해결하려는가?"를 우선으로 둔다.

동작은 대체로 아래 순서를 따른다.

1. target GU마다 query를 준비
2. search 수행
3. 결과 snippet 또는 fetch 결과를 확보
4. claim 파싱
5. 각 claim에 evidence 부착
6. `current_claims` 반환

claim 최소 단위는 대개 다음 정보를 포함한다.

- `claim_id`
- `entity_key`
- `field`
- `value`
- `source_gu_id`
- `evidence`
- `risk_flag`

#### claim 생성의 기준

- claim은 반드시 나중에 KU target에 매핑 가능해야 한다.
- evidence 없는 claim은 원칙적으로 약한 상태다.
- source GU와 연결되지 않는 claim은 downstream 추적성이 약해진다.

### 6.2 collect 단계의 실패 지점

#### 실패 1. search 성공, claim 실패

원인:

- 검색 결과는 많지만 target field와 직접 연관된 문장이 부족함
- LLM 파싱 실패
- 스니펫 수준 정보만으로 필드 값이 결정되지 않음

결과:

- `collect_failure_rate` 상승
- 수집 비용 대비 usable claim 수 저하

#### 실패 2. claim은 생기지만 evidence 질이 낮음

원인:

- 동일 출처 반복
- 독립 출처 부족
- observed_at 불명확

결과:

- integrate에서 confidence가 낮아지거나 충돌 해소가 안 됨

#### 실패 3. GU semantics 손실

원인:

- GU가 요구하는 것은 "조건부 값"인데 collect가 평면 claim만 추출

결과:

- integrate 단계에서 기존 KU와 충돌하거나 애매한 update가 됨

---

### 6.3 단계 2: integrate를 통한 KU 생성

integrate는 claim을 KB 상태 변화로 컴파일하는 단계다.  
실제 "KU generation"의 결정적 기준은 여기서 발생한다.

#### 입력

- `current_claims`
- `knowledge_units`
- `gap_map`
- `domain_skeleton`
- `current_mode`
- `dispute_queue`
- 정책 정보

#### 내부 판단 순서

##### 1. claim이 어떤 기존 KU와 연결되는지 찾는다

핵심 질문:

- 이 claim은 새로운 KU인가?
- 기존 KU의 update인가?
- stale refresh인가?
- 사실상 충돌인가?
- 조건 분기(`condition_split`)가 필요한가?

여기서 중요한 것은 문자열 동일성이 아니라 "같은 entity/field의 같은 사실을 말하는가"다.

##### 2. evidence와 조건을 보고 통합 방식을 정한다

대표 분기:

- `added`
- `updated`
- `refreshed`
- `condition_split`
- `conflict_hold`

##### 3. KU를 생성하거나 갱신한다

KU는 대체로 다음 요소를 가진다.

- `entity_key`
- `field`
- `value`
- `conditions`
- `observed_at`
- `validity`
- `evidence_links`
- `confidence`
- `status`

##### 4. source GU를 resolve할지 판단한다

모든 claim이 들어왔다고 GU가 닫히는 것은 아니다.  
`resolution_criteria`를 만족할 만큼 충분히 신뢰 가능한 통합이 일어났을 때만 GU가 resolved 되어야 한다.

### 6.4 integrate의 실제 데이터 흐름

```text
current_claims
  -> claim별 entity/field 매핑
  -> 기존 KU 대조
  -> add/update/refresh/conflict/condition_split 분기
  -> knowledge_units 갱신
  -> source GU resolve 여부 판단
  -> dynamic GU 생성
```

### 6.5 integrate 실패 지점

#### 실패 1. 동일 개체를 다른 entity로 보는 경우

원인:

- alias 해상도 부족
- entity canonicalization 실패

결과:

- 같은 사실이 중복 KU로 누적
- coverage는 늘어 보이나 실제 품질은 악화

#### 실패 2. 조건부 차이를 충돌로 오인

원인:

- "평일/주말", "시즌별", "구매 채널별" 같은 조건을 모델이 충분히 구조화하지 못함

결과:

- 실제론 공존 가능한 정보가 dispute로 밀림

#### 실패 3. 충돌을 숨기고 덮어씀

원인:

- update 규칙이 과도하게 공격적

결과:

- conflict-preserving 원칙이 붕괴
- critique와 remodel이 구조적 문제를 감지하기 어려워짐

#### 실패 4. evidence는 있는데 GU가 닫히지 않음

원인:

- `resolution_criteria`가 과도하게 강함
- integrate가 evidence sufficiency를 판단하는 규칙이 약함

결과:

- 같은 질문이 계속 open 상태로 남아 cycle 낭비 발생

#### 실패 5. claim은 많이 들어오는데 KU 증가가 거의 없음

원인:

- collect에서 애매한 claim을 과생산
- integrate가 대부분을 conflict 또는 no-op로 흡수

결과:

- 비용은 쓰지만 KB 진전이 작음

### 6.6 이 단계의 품질을 볼 때 중요한 지표

- claim 대비 실제 KU 반영 비율
- `conflict_hold` 비율
- `condition_split`의 필요 빈도
- source GU resolve 비율
- evidence가 1개 이상인 active KU 비율

---

## 7. GU Generation: 새로운 GU는 어떻게 생기는가

시스템의 핵심은 GU를 소비하는 것만이 아니라 GU를 재생성하는 것이다.  
즉 "질문을 푼 결과로 다음 질문을 생성하는 능력"이 있어야 진짜 evolver가 된다.

GU 생성 경로는 하나가 아니다.

### 7.1 경로 A: seed 기반 초기 생성

초기 skeleton의 category/field slot을 기준으로 bootstrap GU를 만든다.

역할:

- 첫 cycle에서 탐색할 결손 지도 생성

실패 지점:

- skeleton이 빈약하면 처음부터 잘못된 질문 공간이 생성됨

### 7.2 경로 B: integrate 기반 adjacent dynamic GU 생성

이 경로가 가장 중요하다.

어떤 claim이 특정 entity의 특정 field를 메웠을 때, 같은 entity의 인접 필드 중 아직 비어 있는 slot을 새로운 GU로 연다.

예:

- 어떤 장소의 `location`이 확보되면
- 같은 장소의 `hours`, `price`, `reservation_rule` 등이 새 Open GU가 될 수 있다

#### 내부 기준

- 같은 entity에 대해 아직 비어 있는 필드인가
- suppress 대상 필드는 아닌가
- 이미 커버된 slot은 아닌가
- mode와 현재 open GU 규모를 봤을 때 동적 GU cap을 넘지 않는가

#### 데이터 흐름

```text
새 claim/KU
  -> same entity 기준 adjacent field 탐색
  -> 이미 해결/억제된 슬롯 제거
  -> 새 missing GU 생성
  -> gap_map에 append
```

#### 실패 지점

##### 실패 1. adjacent expansion이 너무 공격적

결과:

- open GU 폭증
- target selection noise 증가
- 중요한 질문이 사소한 인접 질문에 묻힘

##### 실패 2. adjacent expansion이 너무 보수적

결과:

- 지식 확장이 끊김
- 새로운 frontier가 안 열려 plateau가 빨리 옴

##### 실패 3. 잘못된 entity 매핑 위에서 GU 생성

결과:

- 잘못된 entity에 대한 질문들이 연쇄적으로 퍼짐

### 7.3 경로 C: critique 기반 balance / refresh GU 생성

critique는 단순 평가가 아니라 corrective GU도 만든다.

대표 예:

- 특정 카테고리 커버리지가 낮을 때 balance GU 추가
- 오래된 KU를 다시 확인하기 위한 stale refresh GU 추가

이 경로의 역할은 "현재 파이프라인이 스스로 놓치는 질문"을 메우는 것이다.

실패 지점:

- critique가 너무 많은 corrective GU를 뿌리면 noise 증가
- 반대로 너무 약하면 정체 탈출이 안 됨

### 7.4 경로 D: remodel 기반 gap injection

구조 변경이 승인되면 새 카테고리, 새 필드, 새 관계에 대응하는 GU가 주입될 수 있다.

이 경로는 단순 운영 조정이 아니라 질문 공간 자체를 다시 정의한다는 점에서 가장 강한 개입이다.

실패 지점:

- remodel이 잘못된 가정을 도입하면 이후 Open GU 전체가 왜곡됨

---

## 8. Tuning Process

튜닝은 두 종류로 나눠 읽어야 한다.

1. 내부 구조를 손보는 `Inside: Remodel`
2. 바깥 탐색 방향을 틀어 주는 `Outside: Explore Pivot (+ Universe Probe)`

둘은 목적이 다르다.

- `Remodel`: 현재 skeleton/정책/분류 구조가 틀렸다고 판단될 때
- `Explore Pivot`: 구조는 유지하되, 탐색 방향이 막혔을 때

---

## 9. Inside Tuning: Remodel

Remodel은 "몇 개 target만 바꾸자"가 아니라 "현재 파이프라인이 세상을 자르는 방식 자체를 수정하자"는 제안이다.

### 9.1 Remodel이 다루는 대상

- entity merge / split
- category 재분류
- source policy 변경
- gap 생성 규칙 변경
- skeleton 필드/관계 보강

### 9.2 Activation Criteria

다음과 같은 신호가 누적될 때 remodel을 검토해야 한다.

#### 1. 구조적 중복이 반복된다

예:

- 같은 사실이 다른 entity에 중복 저장
- 같은 카테고리 경계가 계속 흔들림

이 경우 문제는 collect 품질이 아니라 표현 구조일 가능성이 높다.

#### 2. conflict가 특정 축에서 반복적으로 발생한다

예:

- 특정 field에서 조건 분리 없이 충돌만 누적

이 경우 field schema가 너무 평면적이거나 정책이 부족할 수 있다.

#### 3. coverage는 늘지만 설명력이 늘지 않는다

즉 KU 수는 증가하는데 실제로는 비슷한 내용만 반복 저장된다.  
이 경우 category 체계나 entity canonicalization이 잘못되었을 가능성이 있다.

#### 4. audit가 critical finding을 내고 cycle 정기 조건이 충족된다

실제 운용에서는 대개 "정기적 점검 + 임계 finding"의 결합으로 보는 것이 안전하다.

### 9.3 Tuning Parameter

Remodel에서 조절 가능한 실질 파라미터는 다음과 같다.

- merge 임계 기준
- split 허용 기준
- category 재배치 규칙
- alias / is-a 해상도 규칙
- source trust tier 정책
- stale 판정 및 TTL 규칙
- dynamic GU 생성 규칙
- 필드 suppress / allow 규칙

### 9.4 내부 로직

```text
audit findings
  -> 구조적 문제 유형화
  -> proposal 생성
  -> remodel_report 작성
  -> HITL 승인/거부
  -> 승인 시 skeleton/policy/gap generation 규칙 반영
```

중요한 점은 remodel은 자동 적용보다 "제안 -> 승인 -> 반영"의 성격이 강해야 한다는 점이다.  
잘못 적용되면 이후 모든 cycle의 기준면이 바뀌기 때문이다.

### 9.5 Expected Output Improvement

Remodel이 성공적으로 작동하면 기대되는 개선은 다음과 같다.

- 중복 KU 감소
- conflict의 의미 없는 반복 감소
- 조건부 공존 가능 데이터의 표현력 향상
- Open GU 분포의 품질 개선
- target selection의 설명 가능성 증가
- 동일 비용 대비 유효 KU 생성률 상승

### 9.6 Remodel 실패 지점

#### 실패 1. 증상은 구조 문제인데 remodel 대신 pivot만 반복

결과:

- 탐색 방향만 바뀌고 근본 문제는 남음

#### 실패 2. 구조 문제는 아닌데 remodel을 과잉 발동

결과:

- 안정된 표현 구조가 흔들리고 비교 가능성이 떨어짐

#### 실패 3. proposal 품질은 좋지만 승인 후 적용 단계가 약함

결과:

- `remodel_report`는 남지만 실제 state shape는 거의 안 바뀜

#### 실패 4. remodel 후 rollback 경로가 약함

결과:

- 잘못된 구조 변경이 누적

---

## 10. Outside Tuning: Explore Pivot (with Universe Probe)

이 튜닝은 구조 변경이 아니라 탐색 방향 변경이다.  
핵심 질문은 이것이다.

"현재 질문 공간 안에서만 파고드는 것이 아니라, 바깥쪽에서 다른 축이나 후보 카테고리를 발견해 다시 진입해야 하지 않는가?"

### 10.1 Universe Probe의 역할

Universe Probe는 현재 skeleton 바깥 또는 주변부를 훑어보며, 아직 현재 질문 공간에 충분히 반영되지 않은 candidate category나 candidate target을 제안한다.

즉 probe는 "새 후보를 관찰하는 단계"다.

### 10.2 Explore Pivot의 역할

Explore Pivot은 probe와 novelty/reach 신호를 바탕으로, 실제 다음 cycle들의 탐색 초점을 어디로 이동시킬지 정한다.

즉 pivot은 "후보를 실행 전략으로 전환하는 단계"다.

### 10.3 Activation Criteria

다음과 같은 상황에서 outside tuning이 필요하다.

#### 1. novelty stagnation

- 최근 cycle에서 새로운 claim/KU 패턴이 줄어듦
- 유사한 출처, 유사한 entity, 유사한 field만 반복됨

#### 2. reach stagnation

- open GU는 남아 있는데 닿는 범위가 넓어지지 않음

#### 3. external observation diversity 부족

- 외부 관찰 키나 domain entropy가 정체

#### 4. 기존 skeleton 내부 질문만으로는 새 frontier가 열리지 않음

- 즉 inside exploit만으로는 추가 진전이 없는 상태

### 10.4 Tuning Parameter

- probe 실행 주기
- probe가 볼 후보 수
- candidate promotion 최소 confidence
- pivot 시 explore budget 증가폭
- novelty / reach threshold
- 외부 탐색 비용 한도
- primary/secondary source mix

### 10.5 내부 로직

```text
novelty/reach 정체 감지
  -> universe_probe 실행 여부 판단
  -> candidate category / target 제안
  -> validation
  -> exploration_pivot 실행
  -> 다음 plan의 selection bias 조정
```

### 10.6 Expected Output Improvement

- 기존 카테고리 안에서만 맴도는 현상 완화
- 새로운 entity/field frontier 개방
- target 다양성 증가
- 외부 novelty 회복
- plateau 탈출

### 10.7 Outside tuning 실패 지점

#### 실패 1. probe는 후보를 많이 내지만 검증이 약함

결과:

- noise가 높은 candidate가 plan으로 유입

#### 실패 2. pivot이 너무 약함

결과:

- probe를 해도 실제 target 분포가 거의 안 바뀜

#### 실패 3. pivot이 너무 강함

결과:

- 기존 핵심 Open GU 해결이 중단되고, 시스템이 지나치게 탐색 편향으로 이동

#### 실패 4. 구조 문제를 outside tuning으로 해결하려 함

결과:

- 새 카테고리를 계속 건드려도 기존 conflict/중복 문제가 사라지지 않음

---

## 11. Remodel과 Explore Pivot의 경계

이 둘을 혼동하면 운영이 흔들린다.

### Pivot을 써야 할 경우

- 질문 공간은 대체로 맞다
- 다만 현재 수집 경로가 좁고 반복적이다
- 새로운 방향 시도가 필요하다

### Remodel을 써야 할 경우

- 질문 공간의 축 자체가 틀렸다
- entity/category/field 구조가 데이터를 제대로 받지 못한다
- conflict와 중복이 구조적으로 반복된다

간단히 말하면:

- `Pivot`은 "어디를 더 볼까"를 바꾸는 것
- `Remodel`은 "세상을 어떤 칸으로 나눠 볼까"를 바꾸는 것

---

## 12. 운영자가 반드시 봐야 하는 체크포인트

### 12.1 Target Setting 체크포인트

- 이번 cycle의 target은 모두 Open GU인가
- 왜 이 target들이 뽑혔는지 설명 가능한가
- 최근 정체 신호가 실제 selection에 반영되었는가

### 12.2 KU Generation 체크포인트

- claim 수는 충분한데 KU 반영이 낮지 않은가
- conflict_hold 비율이 비정상적으로 높지 않은가
- evidence 품질이 실제 통합을 지탱하는가

### 12.3 GU Generation 체크포인트

- dynamic GU가 너무 많이 늘지 않는가
- adjacent expansion이 실제 frontier를 여는가
- critique/remodel이 만든 GU가 noise를 증가시키지 않는가

### 12.4 Tuning 체크포인트

- 정체 문제를 pivot으로 풀어야 하는지, remodel로 풀어야 하는지 구분했는가
- tuning 발동 조건이 감각이 아니라 지표/패턴 기반인가
- 튜닝 후 실제 output 분포가 달라졌는가

---

## 13. 최종 정리

이 파이프라인의 핵심은 아래 세 문장으로 요약할 수 있다.

1. 시스템은 `Open GU`를 기준으로 무엇을 모르는지 공식화한다.
2. 그 Open GU를 target으로 삼아 claim을 수집하고, integrate를 통해 KU로 바꾸며, 그 결과로 다시 GU를 생성한다.
3. 이 순환이 정체되거나 왜곡되면, outside tuning은 탐색 방향을 바꾸고, inside tuning은 구조 자체를 바꾼다.

따라서 현재 파이프라인의 성패는 단순 수집량이 아니라 다음 네 가지에 달려 있다.

- 올바른 Open GU를 여는가
- 올바른 Open GU를 target으로 고르는가
- claim을 실제 KU로 안정적으로 통합하는가
- 생성된 결과를 바탕으로 다음 GU와 튜닝 결정을 제대로 내리는가

이 네 축이 맞물릴 때만, 시스템은 "많이 모으는 파이프라인"이 아니라 "스스로 질문 공간을 진화시키는 파이프라인"이 된다.
