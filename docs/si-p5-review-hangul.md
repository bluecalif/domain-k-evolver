# SI-P5 리뷰 정리

## 현재 SI-P5 상태

`SI-P5`는 **아직 구현 전**입니다. 현재 상태는 **Planning, 0/15 tasks**입니다.

핵심 사실 2개만 먼저 보면:

- `schemas/telemetry.v1.schema.json` 이 **아직 없음**
- `src/obs/` 자체가 **아직 없음**

즉, 이 단계의 본질은 새로운 진화 로직을 만드는 게 아니라,
**이미 있는 시스템을 관측 가능하게 만드는 것**입니다.

---

## SI-P5의 메인 목표

아주 쉽게 말하면:

> `SI-P5`의 목표는
> "시스템이 매 cycle마다 무엇을 했는지, 왜 그렇게 됐는지, 지금 건강한 상태인지"를
> 한눈에 보이게 만드는 것입니다.

지금도 시스템은 돌아갑니다.
하지만 정보가 여러 군데에 흩어져 있습니다.

- metrics
- state
- trajectory
- conflict ledger
- remodel report
- HITL 상태

그래서 지금은 이런 상태입니다:

```text
지금
실행은 됨
  -> 그런데 정보가 여기저기 흩어짐
  -> 왜 느려졌는지 보기 어려움
  -> 왜 멈췄는지 파악 어려움
  -> 운영자가 전체 상황을 한 번에 보기 어려움
```

SI-P5가 끝나면:

```text
SI-P5 이후
실행은 됨
  -> cycle마다 telemetry snapshot 1개 생성
  -> dashboard가 그것을 읽음
  -> 운영자가 상태/문제/흐름을 바로 이해 가능
```

즉, 한 줄로 말하면:

> **Evolver의 "계기판"을 만드는 단계**입니다.

---

## 비유로 이해하기

```text
P0 ~ P4 = 엔진 강화
P5      = 계기판 추가
P6      = 다른 도메인에서 실전 검증
```

또는:

```text
엔진 = P0~P4
운전석 대시보드 = P5
실도로 테스트 = P6
```

---

## 메인 워크플로우

SI-P5에서 만들려는 큰 흐름은 이것입니다.

```text
1. cycle 실행
2. 내부 상태/지표 계산
3. 그 결과를 telemetry로 표준화
4. telemetry를 jsonl로 저장
5. dashboard가 읽어서 시각화
```

조금 더 자세히 쓰면:

```text
orchestrator 실행
  -> MetricsLogger가 기본 지표 기록
  -> novelty / external novelty / coverage 계산
  -> audit / probe / pivot / remodel 수행 가능
  -> state 저장
  -> telemetry snapshot 1개 emit
  -> dashboard가 읽어서 화면 표시
```

시각적으로 표현하면:

```text
[Orchestrator Cycle]
        |
        v
[metrics / novelty / coverage / audit / remodel]
        |
        v
[telemetry.v1 snapshot 생성]
        |
        v
[bench/silver/.../telemetry/cycles.jsonl 저장]
        |
        v
[Dashboard]
  - overview
  - timeline
  - coverage
  - source reliability
  - conflict ledger
  - HITL inbox
  - remodel review
```

---

## 실제로 재사용되는 현재 코드 기반

이미 P5가 활용할 재료는 꽤 많습니다.

- `metrics_logger.py`
  - cycle별 기본 지표 수집 기능 있음
- `metrics_guard.py`
  - auto-pause 기준 이미 있음
- `orchestrator.py`
  - novelty, external_novelty, reach, probe, pivot, remodel 관련 state 갱신 중
- `state.py`
  - dispute_queue, conflict_ledger, remodel_report 등 이미 존재
- `state_io.py`
  - silver trial state 저장/로드 구조 이미 존재

즉:

```text
P5는 완전히 새 시스템을 만드는 단계가 아님
= 이미 있는 데이터를 "표준화 + 표시"하는 단계
```

이게 중요합니다.

---

## SI-P5에서 실제로 구현해야 하는 것

크게 2층 구조입니다.

### 1. Telemetry Contract

이건 "기계가 남기는 표준 기록 형식"입니다.

```text
내부 state / metrics
  -> telemetry.v1 스키마로 정리
  -> cycle마다 1줄씩 jsonl append
```

필요한 작업:

- `schemas/telemetry.v1.schema.json` 정의
- `src/obs/telemetry.py` 생성
- orchestrator에 emit hook 추가
- `bench/silver/{domain}/{trial_id}/telemetry/cycles.jsonl` 저장
- schema validation test 추가

즉:

> **먼저 기록 포맷을 고정하는 것**

### 2. Dashboard

이건 "사람이 읽는 화면"입니다.

```text
cycles.jsonl + conflict ledger + remodel report + trajectory
  -> 사람이 이해하기 쉬운 화면으로 보여줌
```

계획된 view:

- Overview
- Cycle timeline
- Gap coverage map
- Source reliability
- Conflict ledger
- HITL inbox
- Remodel review

즉:

> **그 다음 기록을 보기 쉽게 꺼내는 것**

---

## 왜 schema-first가 중요한가

이 단계에서 가장 중요한 설계 원칙은:

```text
UI 먼저 X
Schema 먼저 O
```

왜냐하면 UI를 먼저 만들면 거의 반드시 이런 일이 생깁니다:

```text
화면이 먼저 만들어짐
  -> 필요한 값이 중간에 바뀜
  -> 필드 이름이 바뀜
  -> source 위치가 바뀜
  -> dashboard 코드가 계속 흔들림
```

반대로 schema를 먼저 고정하면:

```text
기록 포맷 확정
  -> emit 구현
  -> test로 검증
  -> UI는 그 위에 얹기만 하면 됨
```

그래서 SI-P5의 진짜 핵심은:

> **대시보드보다 telemetry contract가 먼저**입니다.

---

## 장점

### 1. 기존 성과를 잘 재사용한다

이미 P0~P4에서 만들어둔 정보가 많습니다.
P5는 그걸 다시 계산하기보다 **정리해서 보여주는 단계**라서 구조적으로 효율적입니다.

### 2. 코어 로직 리스크가 상대적으로 낮다

append-only telemetry + read-only dashboard 구조라서,
잘 만들면 진화 엔진 자체를 크게 흔들지 않습니다.

### 3. 운영성이 크게 좋아진다

이전에는 "왜 지금 이 상태지?"를 파일 여러 개 열어서 추적해야 했다면,
P5 이후에는 한 화면에서 볼 수 있습니다.

### 4. 문제 진단 속도가 빨라진다

느려짐, conflict 증가, collect 실패율 증가, HITL 증가 같은 문제가
훨씬 빨리 드러납니다.

### 5. P6로 자연스럽게 연결된다

다중 도메인 검증(P6)을 하려면
결국 "어떻게 돌아갔는지"를 일관되게 비교해야 합니다.
P5는 그 기반입니다.

---

## 단점

### 1. 생각보다 범위가 넓다

겉보기에는 "대시보드 만들기" 같지만 실제로는:

- schema 설계
- 파일 저장 규약
- 성능
- view 설계
- 테스트
- 문서화

까지 다 포함됩니다.

### 2. 데이터 출처가 여러 군데다

dashboard가 읽어야 하는 데이터가 단일 파일이 아닙니다.

- telemetry
- trajectory
- conflict ledger
- remodel report
- state snapshot

그래서 단순 viewer가 아니라 **artifact 통합기** 성격이 있습니다.

### 3. 아직 안 맞춰진 필드가 있다

문서상 필요하지만 아직 현재 코드에서 안정적으로 안 나오는 필드들이 있습니다.

예:

- `domain_entropy`
- `provider_entropy`
- `fetch_bytes`
- `fetch_failure_rate`
- `cost_regression_flag`

즉, dashboard 전에 **데이터 공급 정합성 작업**이 필요합니다.

### 4. UI가 쉽게 커질 수 있다

대시보드는 원래 자꾸 욕심이 붙습니다.

```text
이것도 보고 싶다
저것도 필터링하자
비교 화면도 넣자
```

그래서 문서가 LOC 2000 제한을 강하게 두고 있습니다.

---

## 예상 리스크

여기서 제일 중요한 부분입니다.

### 1. 스키마 드리프트 리스크

가장 큽니다.

지금 지표가 여러 군데에 흩어져 있어서:

- metrics_logger 값
- state 값
- trajectory 값
- 앞으로의 telemetry 값

이 서로 조금씩 다를 가능성이 있습니다.

이게 생기면:

```text
화면은 그럴듯함
  -> 그런데 숫자가 실제와 다름
  -> 운영자가 잘못 판단함
```

이건 가장 위험합니다.

### 2. 부분 관측 리스크

문서에서는 필요한데 실제 코드 타입/저장소 쪽이 아직 완전하지 않은 부분이 있습니다.

예:

- `reach_history`
- `probe_history`
- `pivot_history`

orchestrator에서는 쓰고 있지만, 현재 `state.py` 타입 쪽은 아직 완성 정합성이 부족합니다.

즉:

```text
계산은 했는데
  -> 표준 state에 명확히 안 박혀 있음
  -> telemetry emit에서 빠지거나 흔들릴 수 있음
```

### 3. 대시보드 성능 리스크

P5 게이트에 **100-cycle fixture 모든 view 10초 이내** 조건이 있습니다.

이 말은 곧:

- 그냥 파일 막 읽으면 안 됨
- 매 화면마다 전체 artifact 재파싱하면 안 됨
- 데이터 로딩 구조를 생각해야 함

즉, UI보다 **읽기 구조 설계**가 중요합니다.

### 4. Windows 파일 처리 리스크

문서에서 굳이 적어둔 걸 보면 이미 문제를 의식하고 있습니다.

- UTF-8 인코딩
- atomic write
- tmp 파일 후 `os.replace()`

이건 특히 Windows에서 jsonl append 처리 시 깨짐/인코딩/rename 문제를 막으려는 의도입니다.

### 5. Stub 화면 리스크

문서에서 stub 금지를 여러 번 강조합니다.

즉, 이런 건 안 됩니다:

```text
화면은 예쁨
  -> 실제 artifact 안 읽음
  -> 임시 샘플 데이터로 보임
```

P5는 "보여주는 척"이 아니라
**실제 운영 artifact를 읽는 것**이 핵심입니다.

### 6. HITL 의미 혼동 리스크

dashboard에 보여줄 대상들이 비슷해 보여도 사실 다릅니다.

- dispute_queue
- conflict_ledger
- remodel_report
- hitl_pending
- exception pause

이걸 한데 뭉뚱그리면 운영자가 오해합니다.

예를 들면:

```text
conflict ledger = 이력이 남는 기록
dispute queue   = 아직 처리 대기 중인 묶음
remodel report  = 구조 변경 제안서
HITL exception  = 즉시 개입이 필요한 경고
```

이건 반드시 분리해서 보여줘야 합니다.

---

## 가장 핵심적인 결론

SI-P5의 본질은 대시보드가 아닙니다.
진짜 핵심은 아래 순서입니다:

```text
1. telemetry schema 정의
2. cycle마다 valid snapshot emit
3. schema test로 계약 보장
4. 그 위에 dashboard 구현
```

즉:

> **SI-P5의 메인 목표는 "보이는 화면"이 아니라,
> 신뢰할 수 있는 운영 기록 계약을 만드는 것**입니다.

dashboard는 그 위에 얹히는 결과물입니다.

---

## 한눈에 요약

```text
SI-P5는
"시스템을 더 똑똑하게 만드는 단계"가 아니라
"시스템이 어떻게 움직이는지 사람이 명확히 보게 만드는 단계"이다.
```

또 더 짧게 말하면:

```text
P0~P4 = 진화기 만들기
P5    = 진화기를 관측 가능하게 만들기
```
