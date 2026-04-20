# Core Pipeline Spec v1

## 문서 목적

이 문서는 프로젝트의 변하지 않는 기준 문서다.  
설명보다 기준을 우선한다. 상세 배경은 생략하고, 각 단계의 입력, 결정 로직, 산출물, 리스크만 고정한다.

## 전제

- 표의 `KU 단계`와 `GU 단계`는 개념상 분리해 적는다.
- 실제 실행은 둘 다 `integrate_node` 내부에서 함께 일어난다.
- 상태 저장 기준 파일:
  - `state/domain-skeleton.json`
  - `state/knowledge-units.json`
  - `state/gap-map.json`

---

## 1. 프로젝트 주요 단계 Overview

| 단계 | 핵심 목표 | 주 입력 | 주 출력 | 상태 변화 |
|---|---|---|---|---|
| 해결할(Open) GU | 현재 해결 가능한 질문 집합 유지 | `gap_map`, `domain_skeleton`, `knowledge_units`, `seed` 결과 | `status=open` 인 GU 집합 | Seed와 이전 cycle 결과를 반영해 Open GU 풀 유지 |
| Target 설정 | 비용 효율적으로 이번 cycle에서 다룰 GU 수와 우선순위 결정 | Open GU, `current_mode`, `coverage_map`, `novelty_history`, `external_novelty_history`, `current_critique`, `remodel_report` | `current_plan` | Open GU 중 일부만 `target_gaps`로 선별. GU의 `risk_level`은 주로 `field + category` 규칙으로, `expected_utility`는 주로 `risk_level + core category` 규칙으로 정해진다. `plan_node`는 이를 기준으로 target 우선순위를 정하고 `explore_budget`/`exploit_budget`에 따라 분배한다 |
| Collect | 선택된 GU에 대한 사실 수집 | `current_plan`, `gap_map`, search tool, LLM(optional) | `current_claims` | Plan의 `target_gaps`를 그대로 모두 실행하지 않고, query 수와 budget을 기준으로 실제 검색 대상을 다시 압축한다. budget 초과 시 `expected_utility=low/medium` GU는 스킵하고 `high/critical`은 우선 유지한 뒤 query 실행과 Claim 생성을 진행 |
| Integrate | Claim을 KB 상태로 반영 | `current_claims`, `knowledge_units`, `gap_map`, `domain_skeleton`, `policies` | 갱신된 `knowledge_units`, `gap_map` | KU 생성/갱신/보류, GU resolve, dispute/ledger 기록 |
| KU 단계 | 수집된 fact를 KU로 확정 | Claim, 기존 KU, Skeleton, 정책 | KU add/update/refresh/condition_split/conflict_hold | `knowledge_units.json`에 반영 |
| GU 단계 | 해결된 GU 정리 및 신규 GU 발굴 | 통합 결과 KU/Claim, 기존 GU, Skeleton | resolved GU + 신규 GU | `gap-map.json`에 반영 |

---

## 2. 주요 단계 SPEC

| 단계 | 목표 | 결정 인자(Input) | 내부 결정 로직 | 결과 내용(Output) | 주요 Risk | 개선/통제 포인트 |
|---|---|---|---|---|---|---|
| Target 생성 | 비용 효율적으로 이번 cycle의 대상 수와 우선순위 결정 | Open GU, `current_mode`, `coverage_map`, `novelty_history`, `external_novelty_history`, `current_critique`, `remodel_report` | cycle 전체 Open GU를 기준으로 계산한다. `mode_node`가 먼저 `target_count`, `explore_budget`, `exploit_budget`을 정한다. GU의 `risk_level`은 주로 `field + category` 규칙으로, `expected_utility`는 주로 `risk_level + core category` 규칙으로 정해진다. 이후 `plan_node`가 Open GU를 `expected_utility` 우선, 동률 시 `risk_level` 기준으로 정렬하고 `expansion_mode=="jump"` GU를 explore 후보로, 나머지를 exploit 후보로 나눈 뒤 budget만큼 채운다 | `current_plan`<br>핵심 필드: `target_gaps`, `queries`, `budget`, `reason_codes`, `explore_targets`, `exploit_targets` | target 수 과소 선정; explore 후보 부족으로 exploit 편향; high-risk/high-utility GU가 뒤로 밀림; query가 GU 의미를 약하게 반영 | Open GU 외 target 금지; `current_mode.mode`와 `expansion_mode`를 혼동하지 않기; `explore_targets`/`exploit_targets` 수 추적; novelty 정체 시 `jump`/pivot 연계 |
| Collect | 선택된 GU에 대한 사실 수집 | `current_plan`, `gap_map`, `queries`, `budget`, search tool, LLM(optional) | `collect_node`는 plan의 `target_gaps`를 입력으로 받되, 이를 그대로 모두 검색하지 않는다. 먼저 GU별 query 수를 계산해 실제 검색 task를 다시 압축하고, `search_calls_used + needed > budget`이면 `expected_utility`가 `low/medium`인 GU는 skip하고 `high/critical`은 유지한다. 남은 GU에 대해 query 실행 후 claim을 생성하며, LLM parse 실패 시 fallback을 사용한다 | `current_claims`<br>핵심 필드: `claim_id`, `entity_key`, `field`, `value`, `source_gu_id`, `evidence`, `provenance` | 검색 실패; usable claim 생성 실패; evidence 품질 부족; 동일 출처 반복; GU semantics 손실; budget 압박 시 저효용 GU 과다 탈락 | `collect_failure_rate` 추적; parse 실패율 확인; source 다양성 추적; high-risk GU evidence 품질 점검; budget skip된 GU 수 관찰 |
| KU | 수집된 fact를 KU로 확정 | `current_claims`, `knowledge_units`, `domain_skeleton`, `policies`, `gap_map` | `integrate_node`가 `entity canonicalize -> 기존 KU 매칭 -> stale refresh 확인 -> conflict detection -> 결과 분기` 순서로 처리. 결과는 `added / updated / refreshed / condition_split / conflict_hold` 중 하나이며 `claim["integration_result"]`에 기록된다 | `knowledge_units`<br>핵심 필드: `ku_id`, `entity_key`, `field`, `value`, `observed_at`, `validity.ttl_days`, `evidence_links`, `confidence`, `status`<br>부산물: `dispute_queue`, `conflict_ledger`, `integration_result` | `conflict_hold` 또는 no-op로 KU 확정 실패; 중복 entity로 중복 KU 생성; 조건 차이를 분리 못해 잘못된 conflict 발생; evidence 약한 KU 누적; `collect`가 source GU의 `entity_key`를 거의 그대로 넘기므로 seed 밖 새 entity가 KU로 잘 안 들어옴 | `integration_result` 분포 관찰; canonicalize/alias 강화; 조건부 값은 `condition_split` 우선 검토; active KU는 evidence 1개 이상 강제; wildcard GU에는 `discovered_entity_key` 허용 여부를 별도 점검 |
| GU | 해결된 GU 정리 및 신규 GU 발굴 | Claim + 기존 `gap_map` + `domain_skeleton` + source GU 정보 | `integrate_node`가 `added / updated / refreshed / condition_split`이면 source GU를 `resolved` 처리한다. `adjacent` GU는 `conflict_hold` 및 invalid 결과에서는 생성하지 않고, 그 외 유효한 integration 결과에만 연동한다. 이후 claim의 `entity_key` 기준으로 후속 field를 탐색해 새 `missing` GU를 생성하고 suppression/cap으로 양을 제어한다. 별도 경로로 `critique`의 `stale_refresh`, `category_balance`가 GU를 추가한다 | `gap_map`<br>핵심 필드: `gu_id`, `gap_type`, `target(entity_key, field)`, `expected_utility`, `risk_level`, `resolution_criteria`, `status`<br>추적 필드: `trigger`, `trigger_source`, `resolved_by`, `expansion_mode`, `created_at` | Open GU가 오래 닫히지 않음; adjacent GU가 적어 frontier가 안 열림; GU 과다 생성으로 중요 GU가 묻힘; 잘못된 entity/field 기준으로 저품질 GU 연쇄 생성; 새 entity를 열더라도 그 entity 기준 GU 확장이 약해 frontier가 기존 entity 주변에 머무름 | resolve 수와 신규 GU 수를 함께 관찰; dynamic GU cap 유지; `coverage_map`으로 category/field 편향 점검; 생성 유형별 성과를 주기적으로 점검; 새 entity 발견형 GU와 일반 adjacent GU를 구분 관찰 |

---

## 3. KU 또는 GU 중요 Key

| Key | 역할 | 생성 지점 | 결정 인자 | 리스크 | 개선 대책 |
|---|---|---|---|---|---|
| Category | 어떤 지식 영역인지 구분하는 상위 축 | 최초는 `domain_skeleton.categories`, 이후 remodel에서 추가/재분류 가능 | Seed는 category x field 매트릭스로 GU를 만든다. Integrate 이후 GU 확장도 category에 종속된다. `category_balance`는 category별 coverage deficit을 보고 발동하며, 이후 어떤 field를 먼저 열지 정하는 `category -> priority fields` 규칙이 중요하다 | 특정 category가 비거나 과포화될 수 있음. 잘못된 category 체계면 이후 GU/KU 전체가 왜곡됨 | `coverage_map` 기반 deficit 보정, category별 target/resolve 분포 모니터링, `category_balance` field 우선순위 규칙 보강 |
| Entity | 실제 지식의 대상 식별자 | Seed KU에서 시작한다. 이후 Collect claim과 Integrate를 거치지만, 현재 collect는 보통 source GU의 `entity_key`를 claim에 그대로 복사한다. Integrate는 새 entity를 추론하지 않고 canonicalize만 수행한다 | `entity_key`, alias/is-a 해상도, source GU의 target, wildcard GU 여부, skeleton canonical key rule | 같은 entity가 분리 저장되거나 다른 entity가 합쳐질 수 있음; seed 밖 새 entity가 구조적으로 잘 유입되지 않을 수 있음; wildcard/balance용 가상 entity가 실제 entity discovery를 대체할 수 있음 | canonicalize 강화, merge/split remodel 경로 유지, duplicate KU 패턴 점검, wildcard GU의 `discovered_entity_key` 허용과 신규 entity 후속 GU 생성 여부를 별도 점검 |
| Field | entity에 대해 무엇을 알고 싶은지 정의 | `domain_skeleton.fields`에서 시작, Collect claim과 Integrate 결과가 해당 field에 착지 | category별 applicable field, claim.field, adjacent gap 규칙, `category_balance` field 우선순위, suppress/cap 규칙 | field가 잘 안 채워지거나 과잉 생성될 수 있음. 조건부 field를 평면 field로 처리하면 conflict 증가 | field coverage 추적, condition_split 강화, over-produced field suppress, adjacent 및 balance field 규칙 주기적 재점검 |

---

## 4. 영역별 우선순위 재정리 (`상태` + `knowledge evolution 영향도`)

재정리 기준:
- 1차 축은 `knowledge evolution` 영향도이다. 즉, "새 지식이 들어오는가", "잘못된 지식이 누적되는가", "탐색이 정체되는가", "coverage 왜곡이 장기 누적되는가"를 우선 본다.
- 2차 축은 각 항목의 `상태`이다. 같은 영향도라면 `미반영 > 부분 반영 > 반영됨` 순으로 본다.
- 따라서 `부분 반영`이라도 evolution 관점의 구조 리스크가 크면, 일부 `미반영` 계측 항목보다 우선순위가 높을 수 있다.

#### Target

| 우선 | 개선책 | 상태 | evolution 영향도 | 판단 근거 |
|---|---|---|---|---|
| 1 | novelty 정체 시 `jump`/pivot 연계 | 부분 반영 | 높음 | 탐색 정체가 길어지면 high-risk/high-utility GU가 계속 뒤로 밀려 KB 외연 확장이 멈출 수 있음 |
| 2 | `explore_targets` / `exploit_targets` 분리 기록 | 반영됨 | 중간 | 탐색/활용 편향을 진단하는 기반 지표로 의미가 있으나 직접적인 진화 정지 요인은 아님 |
| 3 | `reason_codes` 유지 | 반영됨 | 중간 | target 선택 근거를 남겨 drift를 설명 가능하게 하지만, 직접적인 KB 확장 경로를 만들지는 않음 |
| 4 | Open GU 외 target 금지 | 반영됨 | 중간 | 무결성에는 중요하지만, 현재는 이미 강하게 통제되고 있어 추가 우선순위는 낮음 |

#### Collect

| 우선 | 개선책 | 상태 | evolution 영향도 | 판단 근거 |
|---|---|---|---|---|
| 1 | high-risk GU evidence 품질 점검 | 부분 반영 | 높음 | 약한 evidence가 고위험 GU에 유입되면 이후 KU 확정과 GU 확장이 함께 왜곡될 수 있음 |
| 2 | source 다양성 추적 | 부분 반영 | 중간~높음 | 동일 출처 반복은 apparent novelty만 늘리고 실제 지식 진화를 약화시킬 수 있음 |
| 3 | parse 실패율 확인 | 부분 반영 | 중간 | claim 품질 저하의 선행 신호지만, fallback이 일부 완충하고 있어 구조 리스크는 한 단계 아래 |
| 4 | budget skip된 GU 수 관찰 | 미반영 | 중간 | 운영상 중요하나 본질적으로 계측 항목이며, 그 자체가 새 지식 유입 경로를 만들지는 않음 |
| 5 | `collect_failure_rate` 추적 | 반영됨 | 중간 | 이미 기본 관측 경로는 존재 |

#### KU

| 우선 | 개선책 | 상태 | evolution 영향도 | 판단 근거 |
|---|---|---|---|---|
| 1 | `integration_result` 분포 관찰 | 부분 반영 | 매우 높음 | `added / updated / refreshed / condition_split / conflict_hold` 분포와 cycle별 변화는 KB 외연 확장, 기존 지식 재순환, 충돌 누적, 조건 분기 성숙도를 함께 보여준다. 특히 `added` 강화가 목표일 때 가장 직접적인 진단 축이지만, 현재는 이를 집계해 target/collect/integrate 교정으로 연결하는 운영 루프가 약함 |
| 2 | 조건부 값 `condition_split` 우선 검토 | 부분 반영 | 높음 | 조건 차이를 평면값으로 접으면 잘못된 conflict 또는 잘못된 KU 확정이 누적되어 KB 품질이 장기 왜곡됨 |
| 3 | active KU evidence 1개 이상 강제 | 반영됨 | 높음 | 잘못된 KU 유입을 막는 핵심 방어선이지만 이미 반영되어 우선 추가 조치 필요성은 낮음 |
| 4 | conflict queue/ledger 보존 | 반영됨 | 중간 | 후속 검토 기반은 있으나 신규 진화 자체를 직접 촉진하지는 않음 |

#### GU

| 우선 | 개선책 | 상태 | evolution 영향도 | 판단 근거 |
|---|---|---|---|---|
| 1 | wildcard GU의 신규 entity 발견 경로 | 미반영 | 매우 높음 | seed 밖 새 entity가 구조적으로 KU/GU 체계에 잘 유입되지 않으면 knowledge evolution의 외연 확장이 막힘 |
| 2 | adjacent GU 규칙 재점검 루프 | 미반영 | 높음 | 한 번 생성된 adjacent 규칙이 누락/과생성 상태로 굳으면 후속 field coverage와 frontier 품질이 계속 왜곡됨 |
| 3 | GU 생성 원인 추적 | 부분 반영 | 중간~높음 | 어떤 경로가 noise인지 알아야 GU 확장을 개선할 수 있어 feedback loop 측면에서 중요 |
| 4 | resolve 수와 신규 GU 수 함께 관찰 | 부분 반영 | 중간 | frontier가 닫히는지 증식하는지 보는 핵심 진단값이지만 직접 교정 로직은 아님 |
| 5 | balance/refresh/remodel GU 구분 관찰 | 부분 반영 | 중간 | 확장 종류별 품질 차이를 볼 수 있으나 상위 두 항목보다 구조 영향은 작음 |
| 6 | category/field 편향 점검 | 반영됨 | 높음 | 장기 진화 균형에 중요하지만 이미 반영되어 있음 |
| 7 | dynamic GU cap 유지 | 반영됨 | 중간 | 과도한 GU 생성 억제에는 유효하나 외연 확장 자체의 병목은 아님 |

#### Category

| 우선 | 개선책 | 상태 | evolution 영향도 | 판단 근거 |
|---|---|---|---|---|
| 1 | remodel로 category 추가/재분류 | 부분 반영 | 높음 | category 체계가 잘못되면 이후 target, GU 확장, coverage 해석이 연쇄 왜곡됨 |
| 2 | category별 target/resolve 분포 모니터링 | 부분 반영 | 중간~높음 | 빈 category와 과포화 category를 조기에 식별해 진화 불균형을 완화할 수 있음 |
| 3 | `coverage_map` 기반 deficit 보정 | 반영됨 | 높음 | 구조적으로 중요하지만 핵심 보정 장치는 이미 존재 |

#### Entity

| 우선 | 개선책 | 상태 | evolution 영향도 | 판단 근거 |
|---|---|---|---|---|
| 1 | wildcard GU의 신규 entity 발견 경로 | 미반영 | 매우 높음 | 새 entity 유입 실패는 KB가 seed entity 주변만 맴도는 구조적 한계로 직결됨 |
| 2 | duplicate KU 패턴 점검 | 부분 반영 | 높음 | entity 분리 저장이 누적되면 knowledge evolution이 확장이 아니라 파편화로 변질될 수 있음 |
| 3 | canonicalize / alias 강화 | 반영됨 | 높음 | entity 품질의 중심축이지만 현재 핵심 경로는 이미 반영됨 |
| 4 | merge/split remodel 경로 유지 | 반영됨 | 중간~높음 | 장기 구조 보정에 필요하나 신규 entity 유입 문제보다 선행도는 낮음 |

#### Field

| 우선 | 개선책 | 상태 | evolution 영향도 | 판단 근거 |
|---|---|---|---|---|
| 1 | adjacent GU 규칙 재점검 루프 | 미반영 | 높음 | field 간 인접 규칙이 stale하면 누락 field가 계속 방치되거나 noise field가 반복 생성됨 |
| 2 | 조건부 값 `condition_split` 우선 검토 | 부분 반영 | 높음 | 조건형 field를 평면화하면 field 단위 conflict와 품질 저하가 누적됨 |
| 3 | field coverage 추적 | 반영됨 | 중간~높음 | coverage 불균형을 보는 핵심 지표이나 관측 기반은 이미 있음 |
| 4 | over-produced field suppress | 반영됨 | 중간 | 과생성 억제에는 유효하지만 진화 확장성 자체의 핵심 병목은 아님 |

요약:
- `미반영`이라도 단순 계측 성격이면 우선순위가 절대적으로 가장 높다고 보지 않는다.
- 반대로 `부분 반영`이라도 새 entity 유입, 조건 분기 정확도, 탐색 정체 해소처럼 evolution의 중심 경로에 걸린 항목은 최상위로 본다.
- 현재 최우선 구조 리스크는 `wildcard 기반 신규 entity 유입`, `condition_split 품질`, `novelty 정체 시 jump/pivot 연계`, `adjacent GU 재점검 루프`이다.

---

## 5. GU 생성 규칙 중요 메모

이 문서에서 GU 생성 문제는 단순 구현 세부가 아니라 `knowledge evolution`의 외연 확장과 frontier 품질을 직접 좌우하는 핵심 운영 이슈로 본다. 현재 POR에서는 `remodel off`를 전제로 하므로, cycle 중 실제로 중요한 GU 생성 유형은 `adjacent`, `stale_refresh`, `category_balance` 세 가지다.

### 5.1 생성 유형

1. `adjacent`
`Integrate` 단계에서 claim 처리 후 같은 entity의 후속 field를 열기 위해 생성하는 GU다.

2. `stale_refresh`
`Critique` 단계에서 stale 위험이 큰 KU를 갱신하기 위해 생성하는 GU다.

3. `category_balance`
`Critique` 단계에서 category coverage 부족을 보정하기 위해 생성하는 GU다.

4. `remodel`
구조 변경 제안에 따라 생성하는 GU다. 현재 POR에서는 `off`로 두므로 운영 논의에서는 제외한다.

### 5.2 핵심 문제

1. `adjacent`가 너무 평면적이다.
현재 규칙은 의미적 후속 관계라기보다 같은 category의 다른 field를 나열하는 수준에 가까워, 좋은 frontier 확장 규칙으로 보기 어렵다.

2. `adjacent` 생성 품질이 source integration 결과와 느슨하게 연결되어 있다.
`adjacent`는 최소한 유효한 integration 결과에만 연동되어야 하며, `conflict_hold` 및 invalid 결과에서는 생성하지 않는 것이 적절하다.

3. 신규 entity 확장과 기존 entity 보강이 구분되지 않는다.
새 entity discovery와 기존 entity 주변 확장이 같은 방식으로 처리되어, 외연 확장과 내부 보강을 다르게 제어하기 어렵다.
이 항목은 entity 관련 세션에서 별도 검토한다.

4. `adjacent` 생성 시 `risk_level`과 `expected_utility`가 충분히 반영되지 않는다.
dynamic adjacent GU에 risk/utility가 획일적으로 붙는 경향이 있어, 이후 target/collect 우선순위까지 왜곡될 수 있다. 1차 개선은 기존 risk/utility 판정 규칙을 재사용하는 방향이 적절하다.

5. 억제 규칙이 거칠고 전역적이다.
과생성 억제가 category, entity, 최근 cycle 성과를 보지 않고 전역 평균에 가까운 방식이라, 필요한 GU까지 막거나 반대로 noise를 제대로 못 막을 수 있다.

6. GU 생성 성과 모니터링과 피드백 루프가 약하다.
생성 유형별 `resolve율`, `added 기여율`, `integration_result` 분포를 지속 모니터링하고, 이를 바탕으로 `adjacent` 규칙, `category_balance` field 선택, suppress 규칙을 주기적으로 보정하는 루프가 약하다.

### 5.3 운영 메모

- `adjacent`는 `source field -> next field` 규칙으로 다루는 것이 적절하다.
- `category_balance`는 단순 count 하한보다 category 규모와 coverage deficit을 함께 보는 동적 기준이 바람직하다.
- `category_balance`의 field 선택도 결국 `category -> priority fields` 규칙이 필요하며, 현재는 이 부분이 `adjacent`와 유사하게 평면적이다.

---

## 구현 기준 메모

- Seed 구현: `src/nodes/seed.py::seed_node`
  입력은 `domain_skeleton + knowledge_units`, 출력은 첫 `gap_map`이다. Seed는 KU 생성이 아니라 초기 GU 생성 단계다.
- Fresh trial의 초기 state source:
  기본 원본 bench 절대경로는 `C:\Users\User\Learning\KBs-2026\domain-k-evolver\bench\japan-travel`.
  fresh 실행 시 `scripts/run_readiness.py`는 우선 `...\bench\japan-travel\state-snapshots\cycle-0-snapshot\` 전체를 seed state로 로드하고 `current_cycle=0`으로 되돌린다.
  snapshot이 없을 때만 `...\bench\japan-travel\state\`를 fallback으로 읽는다.
- 단계별 구현 위치:
  `mode.py::mode_node` -> cycle mode + explore/exploit budget
  `plan.py::plan_node` -> target selection
  `collect.py::collect_node` -> claim 생성
  `integrate.py::integrate_node` -> KU 확정 + GU resolve/생성 + `integration_result`
  `state_io.py` -> `state/*.json` 영속 저장
- explore/exploit 계산식:
  `normal`: `target_count=max(4, ceil(open_count*0.4))`, `explore=0`, `exploit=target_count`
  `jump`: `target_count=max(10, ceil(open_count*0.5))`, `explore=int(target_count*explore_ratio)`, `exploit=target_count-explore`
  `explore_ratio`: early `0.6`, mid `0.5`, converging `0.4`, 이후 `audit_bias` 반영 후 `0.2~0.8`로 clamp
- `expansion_mode="jump"` 부여 경로:
  `integrate.py`의 dynamic GU, `critique.py`의 category balance GU
  단, 현재 의미는 다르다.
  `integrate.py` 쪽은 생성 시점 메타데이터에 가까워 의미가 약하고, `critique.py` 쪽은 under-covered category 보정용 신호라 의미가 있다.
- 선정 이후 실행:
  `collect_node`는 `explore_targets`/`exploit_targets`를 직접 쓰지 않고 `target_gaps`만 사용한다.
  즉 explore/exploit는 선정 단계 분류이며, 선정 후 수집/통합 경로는 동일하다.
- 정책 저장 위치:
  `state/policies.json`
  핵심 필드: `credibility_priors`, `ttl_defaults`, `cross_validation`, `conflict_resolution`

---

## 용어

- `GU (Gap Unit)`: 아직 해결되지 않은 질문 단위. `gap_map`에 저장된다.
- `Open GU`: 현재 cycle에서 target 후보가 될 수 있는 `status="open"` GU.
- `Target`: 이번 cycle에서 실제로 수집 대상으로 선택된 Open GU.
- `Claim`: 수집 단계가 만든 주장 단위. 아직 KB 확정 전 상태다.
- `KU (Knowledge Unit)`: integrate를 통과해 KB에 반영된 지식 단위.
- `Seed`: 초기 GU 생성 단계. 입력으로 기존 `knowledge_units`를 읽지만, 산출물은 KU가 아니라 초기 `gap_map`이다.
- `Seed KU`: 첫 cycle 이전부터 존재하는 초기 사실 집합. seed 단계의 입력이다.
- `Skeleton`: domain의 category, field, axis, canonical key rule을 담는 구조 정의. `domain-skeleton.json`.
- `Mode`: 이번 cycle의 운영 태세. `normal` 또는 `jump`.
- `Explore/Exploit`: mode가 정해진 뒤 target을 분류하는 선정용 개념. 현재 구현에서는 실행 경로를 분리하지 않는다.
- `Policy`: 수집/통합 판단에 쓰는 운영 규칙. 예: 출처 신뢰도(`credibility_priors`), TTL 기본값(`ttl_defaults`), 교차검증 기준(`cross_validation`), 충돌 처리 규칙(`conflict_resolution`).
- `Accept 로직`: Claim이 KU로 `added`, `updated`, `refreshed`, `condition_split`, `conflict_hold` 중 어디로 분기되는지 결정하는 integrate 내부 규칙.
- `Dynamic GU`: integrate 이후 인접 field를 기준으로 새로 발굴되는 GU.
- `Entity Canonicalize`: claim의 `entity_key`를 표준형으로 맞추는 과정. 현재 구현은 소문자화, 공백→하이픈, alias 치환이다.
- `신규 Entity 발견`: seed에 없던 실제 entity를 claim에서 분리 추출해 새 `entity_key`로 승격하는 과정. 현재 구현은 이 경로가 약하다. 기본 collect prompt와 fallback은 대체로 source GU의 `entity_key`를 그대로 사용하고, integrate는 이를 canonicalize만 한다.
- `Alias 해상도`: `skeleton["aliases"]`를 사용해 동의어를 canonical entity_key로 치환하는 과정.
- `is_a 해상도`: `skeleton["is_a"]`를 사용해 특정 entity의 상위 개념 체인을 찾는 과정. 현재 `integrate_node`의 주 매칭에는 직접 쓰이지 않고, 구조 보강과 후속 규칙 확장용 기반이다.

---

## Entity 확보 전략 메모

`Entity`는 `knowledge evolution`의 외연 확장과 KB 일관성을 동시에 좌우하는 핵심 축이다. 표 4 기준으로 `Entity` 영역의 우선순위는 두 가지로 압축된다. 첫째는 seed 밖 실제 대상을 KB 안으로 들여오는 `신규 entity 유입`이고, 둘째는 같은 실체를 하나의 entity로 모아 파편화를 막는 `entity 정규화·통합`이다. 현재 POR에서는 전자가 사실상 비어 있고, 후자는 canonicalize 중심으로만 부분 반영되어 있어 두 축 모두 별도 전략이 필요하다. 즉 `Entity`는 단순 식별자 관리가 아니라, KB가 실제로 무엇을 알고 있으며 그 지식이 얼마나 확장 가능한지를 결정하는 핵심 구조다.

- `신규 entity 유입`: `entity`는 처음부터 전량 확정하지 않고, `category`, `field`, `entity frame`, 소수의 대표 seed entity로 시작한 뒤 cycle 중 `candidate -> validated entity` 단계를 거쳐 점진적으로 승격하는 것이 적절하다. discovery는 무차별 전체 수집이 아니라 현재 부족한 `category`, `field`, `geography`를 메우는 방향으로 frontier 인접 영역에서 일어나야 하며, 승격된 entity는 즉시 후속 GU 확장의 기준이 되어야 한다. 그렇지 않으면 field 확장은 generic knowledge 누적으로 흐르고 concrete entity 확장은 정체된다.
- `entity 정규화·통합`: `canonicalize`, `alias`, `merge`, `duplicate KU 패턴 점검`은 모두 “같은 실체를 한 entity로 모으는 능력”으로 묶어 관리하는 것이 적절하다. `duplicate KU`는 독립 문제가 아니라 entity 파편화의 관측 신호로 보고, KB 성장이 확장이 아니라 분산 저장으로 흐르지 않게 지속 점검해야 한다. 현재 단계에서는 세부 기법을 과도하게 분리하기보다, 정규화·통합이라는 하나의 운영 축으로 관리하는 편이 적절하다.
- `geography 처리`: `dining`, `accommodation`은 area와의 결합이 중요하지만 entity key에 area를 상시 포함하면 entity 수가 급격히 팽창하므로, 기본은 `entity 본체 + geography 축`으로 처리하는 것이 적절하다. area가 정체성의 핵심일 때만 예외적으로 area 포함 entity를 허용한다. 예를 들어 `ryokan`, `business-hotel`, `izakaya`, `ramen-shop` 같은 기본 entity에 `hakone`, `shinjuku` 같은 geography를 결합해 해석하고, `tsukiji-outer-market`, `dotonbori`처럼 area 자체가 정체성의 일부인 경우만 별도 entity로 둔다.
- `entity discovery 방향`: 현재의 `wildcard`라는 표현은 의미가 약하므로, 앞으로는 이를 `entity discovery node`로 재정의하는 것이 적절하다. 이 노드는 category 수준에서 concrete entity 후보를 찾고, 이를 누적·검증해 validated entity로 승격하는 역할을 맡아야 한다. query 생성은 `rule-first, LLM-assisted`가 적절하며, 기본 query는 `category + field intent + geography(optional) + source hint` 조합으로 생성한다. 기본은 규칙 기반 template으로 재현성과 비용 통제를 유지하고, search yield가 낮거나 novelty 정체가 길어질 때만 LLM이 보강하는 방식이 바람직하다.

참고: `Entity` 확보 전략의 확장 설계와 discovery query 예시는 `docs/entity-acquisition-strategy-draft.md`를 참조한다.
