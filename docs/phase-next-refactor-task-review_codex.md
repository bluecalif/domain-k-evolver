# Next Phase Refactor Task Review

## 목적

이 문서는 다음 두 문서를 기준으로, 사용자가 제시한 핵심 리팩토링 항목의 정합성과 구현 가능성을 점검하고 다음 phase의 구현 task를 초안까지 정리한다.

- `docs/core-pipeline-spec-v1.md`
- `docs/entity-acquisition-strategy-draft.md`

추가로 실제 구현 상태는 다음 코드를 기준으로 점검했다.

- `src/nodes/plan.py`
- `src/nodes/collect.py`
- `src/nodes/integrate.py`
- `src/nodes/critique.py`

---

## 1. 핵심 정합성 검토

### 1.1 Target / Collect

문서 정합성:

- `core-pipeline-spec-v1`는 Target 단계에서 Open GU 전체를 기준으로 우선순위를 정하고, Collect 단계에서 다시 query 수와 budget 기준으로 실행 대상을 압축한다고 명시한다.
- 같은 문서는 동시에 `high-risk/high-utility GU가 뒤로 밀리는 것`, `budget skip된 GU 관찰`, `novelty 정체 시 jump/pivot 연계`를 주요 리스크로 적고 있다.

현재 구현:

- `plan.py`는 open GU를 `expected_utility -> risk_level`로 정렬하고, `expansion_mode=="jump"`만 explore로 분류한다.
- `collect.py`는 `target_gaps`를 다시 예산 기준으로 잘라내며, 예산 초과 시 `low/medium`을 즉시 skip한다.

판단:

- 사용자의 우려대로 현재 구조에서는 Target 우선순위가 Collect 재필터링에 의해 다시 약화된다.
- 특히 "query 수가 많은 GU"가 불리해지고, 실제로는 Target에서 선정된 GU 집합이 Collect에서 다시 바뀌므로 phase 기준 책임이 흐려진다.
- 문서 내부에서도 이 리스크를 이미 인정하고 있으므로, 다음 phase에서는 `Target 선정`과 `Collect 실행 압축`의 책임을 다시 자를 필요가 있다.

결론:

- `Target GU 우선순위`는 유지하되, `Collect`는 target 재선별이 아니라 실행 단위 조정과 진단 중심으로 바꾸는 쪽이 정합적이다.
- 사용자가 말한 "우선순위 무의미할 수도 있으니 모두 풀기"는 완전 해제보다, `Target은 모두 보존 + Collect는 defer만 하고 drop하지 않음`으로 구현하는 편이 안전하다.

### 1.2 KU 병합

문서 정합성:

- `core-pipeline-spec-v1`는 `integration_result` 분포 관찰을 KU 영역 최우선 개선책으로 둔다.
- 같은 문서는 `condition_split`을 평면 충돌 방지의 핵심으로 본다.

현재 구현:

- `integrate.py`는 `added / updated / refreshed / condition_split / conflict_hold`를 기록한다.
- 하지만 이 결과를 다음 cycle의 Target/Collect 교정으로 연결하는 운영 루프는 없다.
- `condition_split`은 사실상 `claim.conditions` 또는 `existing_ku.conditions`가 이미 있을 때만 작동한다. 즉 조건부 값 탐지보다 "이미 조건이 들어온 경우 분기"에 가깝다.

판단:

- `integration_result` 기록 자체는 되어 있으나, 사용자가 요구한 "add가 잘 안되면 feedback loop"는 미구현이다.
- `condition_split`도 문서 의도 대비 약하다. 현재는 "조건 차이를 탐지하는 체계"가 아니라 "조건 필드가 이미 있으면 분기" 수준이다.

결론:

- 다음 phase의 KU 핵심은 `integration_result`를 단순 로그가 아니라 제어 입력으로 승격하는 것과, `condition_split` 판단 기준을 값 구조/axis 차이까지 보도록 재설계하는 것이다.

### 1.3 GU 생성 - field

문서 정합성:

- `core-pipeline-spec-v1`는 `adjacent`를 현재 너무 평면적이라고 직접 지적한다.
- 같은 문서는 `adjacent`는 유효한 integration 결과에서만 생성해야 하며, `risk_level`과 `expected_utility`를 재사용해야 한다고 적는다.
- `category_balance`는 단순 count 하한보다 category 규모와 coverage deficit을 함께 보는 동적 기준이 바람직하다고 적는다.

현재 구현:

- `integrate.py::_generate_dynamic_gus()`는 같은 entity의 applicable field를 거의 전수 열고, `expected_utility="medium"`, `risk_level="convenience"`를 고정으로 부여한다.
- suppress도 전역 field 빈도 평균 기반이라 카테고리/엔티티/최근 성과를 반영하지 않는다.
- `critique.py::_generate_balance_gus()`는 `balance-{n}` 가상 entity를 만들고 category별 KU 최소 개수만 맞춘다.

판단:

- 사용자가 지적한 `adjacent 억제/촉진`, `category balance 하한 차등`, `field는 adjacent 개선사항 반영`은 문서와 정확히 맞닿아 있다.
- 특히 `balance-{n}` 가상 entity는 `entity discovery`를 대체할 위험이 있다는 spec 경고와 충돌한다.

결론:

- 다음 phase에서 field GU는 `adjacent rule engine`과 `category balance policy`로 분리해 재설계해야 한다.
- `conflict field 배제`, `seed/validated entity 기반 field map`, `category별 priority field`, `동적 하한`이 핵심이다.

### 1.4 GU 생성 - entity

문서 정합성:

- 두 문서 모두 현재 최상위 구조 리스크를 `새 entity 유입 부재`로 본다.
- `entity-acquisition-strategy-draft`는 `wildcard`를 `entity discovery node`로 재정의하고 `candidate -> validated entity -> 후속 GU 생성` 흐름을 제안한다.
- `canonicalize, alias, merge, duplicate KU 패턴 점검`은 하나의 `정규화·통합` 축으로 관리하라고 적고 있다.

현재 구현:

- `collect.py` 결정론 경로는 source GU의 `entity_key`를 그대로 claim에 넣는다.
- `integrate.py`는 canonicalize만 하고 새 entity를 만든 뒤 확장하는 경로가 없다.
- 저장 구조상 `entity_candidates` 상태도 아직 없다.
- `critique.py`의 category balance는 가상 entity를 열 뿐 실 entity discovery와 연결되지 않는다.

판단:

- 이 부분은 문서 정합성이 매우 높고, 현재 구현과의 갭도 가장 크다.
- 사용자가 가장 중요하다고 본 `new Entity 생성`은 실제로 phase의 별도 epic으로 분리해야 한다.

결론:

- 다음 phase에서 가장 먼저 설계해야 할 것은 `entity discovery node/state`다.
- 그 다음이 `validated entity 승격`, `후속 GU 생성`, `entity 정규화·통합` 루프다.

---

## 2. 구현 관점 결론

### 바로 구현 가능한 항목

- Collect의 재필터링을 drop 대신 defer/queue로 바꾸기
- `integration_result` 분포 집계 및 cycle 피드백 입력화
- `adjacent` 생성 조건을 `integration_result` 기반으로 엄격화
- `adjacent`의 `risk_level/expected_utility`를 seed 규칙 재사용으로 변경
- `category_balance`를 category별 priority field 기반으로 바꾸기

### 중간 난이도 항목

- `condition_split` 판정 기준을 axis/conditions 중심으로 재설계
- conflict된 field의 adjacent 억제 규칙 도입
- category별 다른 count 하한과 coverage deficit 기반 balance 정책
- duplicate KU 패턴을 entity 정규화 신호로 집계

### 별도 축으로 설계해야 할 항목

- `entity discovery node`
- `entity_candidates` 상태 모델
- `candidate -> validated entity` 승격 규칙
- validated entity 생성 직후 후속 GU 자동 오픈
- entity canonicalize/alias/merge/duplicate KU 진단을 묶는 통합 파이프라인

---

## 3. Task Draft

초기 draft는 일부러 넓게 잡는다.

### Draft A. Target / Collect 재설계

1. `plan.py`에서 target 선정 기준을 정리하고 reason code를 보강한다.
2. `collect.py`에서 budget 초과 시 target을 drop하지 않고 실행 순서만 조정한다.
3. target 대비 collect 실제 실행량, defer량, skip 사유를 메트릭으로 남긴다.
4. novelty 정체 시 `jump/pivot` 연계 기준을 Target 단계에서 명확히 적용한다.

### Draft B. KU 병합 강화

1. `integration_result` 분포를 cycle 메트릭으로 집계한다.
2. `added` 비율 저하, `conflict_hold` 증가, `condition_split` 부족 시 피드백 규칙을 만든다.
3. `condition_split` 판단 기준을 conditions/axis 중심으로 재설계한다.
4. duplicate KU 패턴을 entity 파편화 신호로 연결한다.

### Draft C. GU field 생성 재설계

1. `adjacent`를 `source field -> next field` 규칙 기반으로 바꾼다.
2. conflict된 field는 adjacent 대상에서 배제한다.
3. seed field 연관 맵을 만들어 adjacent 후보 생성에 사용한다.
4. adjacent GU의 risk/utility를 seed 규칙으로 다시 계산한다.
5. category balance의 count 하한을 카테고리별로 다르게 둔다.
6. category balance field 선택을 priority field 규칙으로 바꾼다.

### Draft D. GU entity 생성 재설계

1. `wildcard`를 `entity discovery node`로 대체한다.
2. discovery query를 `rule-first, LLM-assisted` 방식으로 생성한다.
3. 검색 결과에서 `entity candidate`를 추출해 별도 상태에 적재한다.
4. 반복 등장/독립 source/category 적합성 기준으로 validated entity로 승격한다.
5. 승격된 entity에 대해 후속 GU를 자동 생성한다.

### Draft E. entity 정규화·통합

1. canonicalize/alias/merge/duplicate KU 점검을 하나의 운영 축으로 묶는다.
2. entity merge 후보 진단을 강화한다.
3. duplicate KU 패턴을 주기적으로 리포트한다.
4. geography 축과 entity 본체를 분리한 key 정책을 정리한다.

---

## 4. Draft 수정 포인트

초기 draft는 방향은 맞지만 다음 문제가 있다.

- 범위가 너무 넓어 한 phase에 모두 넣으면 `entity discovery` 때문에 일정이 깨질 가능성이 높다.
- `Target/Collect`, `KU`, `GU field`, `GU entity`가 서로 의존하므로 구현 순서를 다시 정해야 한다.
- `entity discovery node`를 먼저 넣더라도 `entity_candidates` 상태와 후속 GU 생성 규약이 없으면 수집 경로만 늘고 통합 경로가 없다.
- 반대로 `adjacent`와 `condition_split`을 먼저 바로잡지 않으면 새 entity를 넣어도 low-quality GU와 conflict가 함께 증가한다.

따라서 phase task는 `제어 루프 복구 -> field/GU 품질 개선 -> entity discovery 도입` 순으로 재구성하는 편이 현실적이다.

---

## 5. Final Task Proposal

다음 phase의 구현 task는 아래 순서가 가장 정합적이고 실현 가능하다.

### Phase 1. Control Loop 복구

목표:

- Target 선정이 Collect에서 무력화되지 않게 하고, Integrate 결과가 다음 cycle 제어 입력으로 다시 들어오게 만든다.

구현 task:

1. `collect.py`의 budget 처리 변경
   - `target_gaps` 재선별 대신 `execution_queue` 또는 `deferred_targets` 개념을 둔다.
   - budget 초과 target은 drop하지 말고 defer 기록을 남긴다.
   - 산출 메트릭에 `executed_targets`, `deferred_targets`, `defer_reason`을 추가한다.

2. `integration_result` 피드백 루프 추가
   - cycle별 `added / updated / refreshed / condition_split / conflict_hold / no_source_gu` 분포를 집계한다.
   - `added` 저하, `conflict_hold` 상승, `condition_split` 부재를 critique/plan 입력으로 연결한다.

3. `plan.py` reason code 보강
   - `integration_result` 기반 reason code를 추가한다.
   - `collect defer 과다`, `adjacent 성과 저하`, `entity discovery 부족` 같은 운영 신호를 target 이유로 반영한다.

완료 기준:

- Target으로 선정된 GU는 같은 cycle에서 실행되거나 명시적으로 defer된다.
- 다음 cycle plan이 직전 cycle의 `integration_result` 요약을 입력으로 사용한다.

### Phase 2. KU + Field GU 품질 개선

목표:

- `condition_split`과 `adjacent`를 문서 의도에 맞게 재설계해 low-quality expansion을 줄인다.

구현 task:

1. `condition_split` 판정 로직 재설계
   - claim/existing KU의 `conditions`, `axis_tags`, 값 구조 차이를 함께 비교한다.
   - 단순 "conditions가 이미 있으면 split"이 아니라 "조건 차이로 공존 가능한 값"을 판정한다.

2. `adjacent` 규칙 엔진 도입
   - `source field -> next field` 맵을 도입한다.
   - 기본 맵은 seed/skeleton 기반으로 시작하고 category별 override를 허용한다.
   - `conflict_hold` 또는 invalid source에서는 adjacent를 만들지 않는다.

3. adjacent 억제/촉진 규칙 추가
   - conflict 이력 field는 adjacent 후보에서 제외한다.
   - validated seed field 연관 맵에 있는 경로는 우선 허용한다.
   - 최근 `added` 기여가 낮은 adjacent rule은 약화하거나 중지한다.

4. adjacent risk/utility 재계산
   - seed의 `_determine_risk_level`, `_determine_expected_utility` 규칙을 재사용한다.
   - 현재의 고정 `medium/convenience`를 제거한다.

5. `category_balance` 정책 교체
   - `balance-{n}` 가상 entity 기반 보충을 중단한다.
   - category별 최소 하한, category 규모, coverage deficit을 함께 보는 동적 하한으로 변경한다.
   - field 선택은 `category -> priority fields` 규칙으로 정한다.

완료 기준:

- dynamic GU 생성이 `same entity + all fields` 방식에서 `rule-based next field` 방식으로 바뀐다.
- `category_balance`가 가상 entity가 아니라 실제 부족 field 보정 신호로 동작한다.

### Phase 3. Entity Discovery 도입

목표:

- seed 밖 concrete entity를 `candidate -> validated entity` 경로로 편입시킨다.

구현 task:

1. 상태 모델 추가
   - `entity_candidates` 저장 구조를 정의한다.
   - 필수 필드: `candidate_id`, `name`, `proposed_slug`, `category`, `geography`, `candidate_type`, `source_count`, `supporting_sources`, `status`.

2. `entity discovery node` 신설
   - 기존 wildcard 의미를 이 노드로 치환한다.
   - 입력은 `coverage deficit + category + field intent + geography + source hint`다.
   - query 생성은 rule-first, yield 저하 시만 LLM-assisted로 확장한다.

3. candidate 승격 규칙 구현
   - 독립 source 수, 반복 등장, category 적합성, geography 일관성을 기준으로 validated entity로 승격한다.

4. validated entity 후속 GU 생성
   - 승격 즉시 `price`, `hours`, `location`, `how_to_use` 등 priority field GU를 연다.
   - 이 경로는 일반 adjacent와 구분된 trigger/type으로 기록한다.

완료 기준:

- collect/integrate 경로 밖 별도 `entity discovery -> candidate -> validated entity -> GU expansion` 체인이 생긴다.
- 새 entity는 seed 밖에서도 지속적으로 KB에 편입될 수 있다.

### Phase 4. Entity 정규화·통합 강화

목표:

- 새 entity 유입이 파편화로 변질되지 않게 만든다.

구현 task:

1. canonicalize/alias/merge/duplicate KU를 통합 진단 축으로 묶는다.
2. duplicate KU 패턴 리포트를 추가한다.
3. merge 후보를 validated entity와 기존 entity 사이에서도 탐지한다.
4. geography 포함 entity 예외 규칙을 skeleton/policy에 명시한다.

완료 기준:

- duplicate KU가 단순 데이터 이상이 아니라 merge 검토 신호로 연결된다.
- validated entity 유입 후 entity 파편화가 관측 가능해진다.

---

## 6. Phase 범위 제안

한 phase에 모두 넣기보다 아래 범위가 현실적이다.

### 이번 phase에 포함

- Phase 1 전체
- Phase 2 전체
- Phase 3 중 `상태 모델 + discovery node skeleton + candidate 적재`

### 다음 phase로 넘길 항목

- Phase 3의 정교한 validated 승격 정책
- Phase 4 전체

이유:

- 지금 가장 큰 병목은 `제어 루프 부재`와 `adjacent/condition_split 품질`이다.
- 이를 고치지 않은 채 entity discovery를 크게 열면 noise와 conflict가 같이 늘 가능성이 높다.
- 반면 entity discovery의 최소 골격은 이번 phase에 같이 넣어야 이후 phase가 실제 데이터를 갖고 보정할 수 있다.

---

## 7. 최종 우선순위

1. `integration_result` 기반 제어 루프 복구
2. `condition_split` 기준 재설계
3. `adjacent` 규칙 엔진 도입
4. `category_balance`의 가상 entity 제거
5. `entity_candidates` 상태와 discovery node 골격 도입
6. validated entity 후속 GU 생성
7. entity 정규화·통합 고도화

