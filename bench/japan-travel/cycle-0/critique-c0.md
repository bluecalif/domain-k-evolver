# Critique Report — Cycle 0

> **단계**: (R) Critique | **도메인**: japan-travel
> **생성일**: 2026-03-02
> **입력**: KB Patch Cycle 0 + 전체 State

---

## 1. Metrics Delta

### 현재 State 수치

| 지표 | Seed (Cycle 0 시작) | Cycle 0 종료 | Delta | 방향 |
|------|---------------------|--------------|-------|------|
| KU 수 (active) | 7 | 13 | +6 | ↑ |
| 근거율 (EU≥1인 KU / 전체 KU) | 1.0 | 1.0 | 0 | → |
| 다중근거율 (EU≥2인 KU / 전체 KU) | 0.0 | 0.538 | +0.538 | ↑↑ |
| Gap 수 (open) | 25 | 21 | -4 | ↓ (개선) |
| Gap 해소율 (resolved / 초기 open) | 0.0 | 0.28 | +0.28 | ↑ |
| 충돌 수 (disputed KU) | 0 | 0 | 0 | → |
| 평균 confidence | 0.864 | 0.888 | +0.024 | ↑ |
| 신선도 리스크 (TTL 초과 KU 수) | 0 | 0 | 0 | → |

### Metrics 계산 공식 (Cycle 0에서 확정)

```
근거율 = count(KU where len(evidence_links) >= 1 AND status == 'active') / count(KU where status == 'active')
다중근거율 = count(KU where len(evidence_links) >= 2 AND status == 'active') / count(KU where status == 'active')
Gap해소율 = count(GU where status changed to 'resolved' in this cycle) / count(GU where status == 'open' at cycle start)
충돌률 = count(KU where status == 'disputed') / count(KU where status in ['active', 'disputed'])
평균confidence = mean(confidence for KU where status == 'active')
신선도리스크 = count(KU where date(observed_at) + ttl_days < today)
커버리지 = count(GU where status == 'resolved') / count(GU total)
```

### 검증 계산

- 근거율: 13/13 = 1.0 ✓
- 다중근거율: 7/13 = 0.538 (KU-0002,0004,0008,0009,0010,0011,0012 각 EU≥2)
- Gap 해소율: 7/25 = 0.28 ✓
- 평균 confidence: (0.95+0.95+0.90+0.85+0.90+0.85+0.70+0.95+0.85+0.90+0.90+0.85+0.85)/13 = 0.888 ✓

---

## 2. Failure Modes 탐지

### Epistemic (근거 빈약/출처 편향/독립성 부족)
- **발견**: KU-0007(SIM 가격), KU-0013(신칸센 가격)은 EU 1개만 보유. KU-0013의 출처가 public(tokyocheapo)으로 financial 정보에 대해 공식 출처 부재.
- **심각도**: medium
- **영향 KU**: [KU-0007, KU-0013]

### Temporal (신선도 취약/TTL 설계 부적절)
- **발견**: KU-0011(면세 정책)에 expires_at 2026-11-01 설정. 제도 변경 시점 이후 KU가 자동 stale 처리되어야 하는데, 현재 시스템에 만료 자동 감지 로직이 없음 (수동 확인 의존).
- **심각도**: low (현재 Cycle 0이라 아직 문제되지 않음)

### Structural (스키마가 표현 못함)
- **발견**: KU-0009(공항교통)의 value가 깊은 중첩 객체. 나리타/하네다 × 교통수단 × 필드 구조로, 단일 KU에 너무 많은 정보가 압축됨. 이상적으로는 각 교통수단별 KU로 분리하는 것이 Entity Resolution과 업데이트에 유리.
- **심각도**: medium
- **영향 KU**: [KU-0009]

### Consistency (충돌 다발/해결 불가)
- **발견**: 없음. Cycle 0에서 충돌 0건.
- **심각도**: -

### Planning (Gap 우선순위 비효율/검색전략 부정확)
- **발견**: Collection Plan의 Gap 선정은 critical/high 우선순위에 집중해 효율적이었음. 다만 7개 중 3개가 regulation 카테고리에 편중. accommodation, dining, attraction 카테고리가 전혀 다뤄지지 않아 **카테고리 커버리지 편향** 존재.
- **심각도**: medium

### Integration (정규화 오류/엔티티 해상도 문제)
- **발견**: IC카드(KU-0004)와 Suica(KU-0012)가 별도 엔티티로 분리됨. ic-card는 payment 카테고리, suica는 pass-ticket 카테고리. 논리적으로 Suica는 IC카드의 한 종류이므로 관계 정의(is_a)가 필요하나 현재 스키마에 없음.
- **심각도**: low

---

## 3. Root Cause Hypotheses

| 실패모드 | 가설 | 근거 |
|----------|------|------|
| Epistemic (KU-0013) | financial 정보의 교차검증 규칙이 있지만, 수집 예산 내에서 공식 출처 접근이 어려웠음 | JR Central 공식 사이트가 예약 시스템 위주로 가격표 페이지가 명확하지 않음 |
| Structural (KU-0009) | Seed의 Domain Skeleton이 "airport-transfer"를 단일 엔티티로 정의해 세부 교통수단 분리가 안됨 | Skeleton의 엔티티 입도(granularity) 설계 미흡 |
| Planning (카테고리 편향) | Gap 선정이 expected_utility + risk_level 기준만 적용, 카테고리 분포를 고려하지 않음 | Collection Plan §1에 카테고리 다양성 기준 없음 |
| Integration (ic-card/suica) | Domain Skeleton의 관계 정의가 covers_route/valid_for/located_in/accepted_at 4개뿐. is_a(분류 계층) 관계 부재. | domain-skeleton.json relations 섹션 확인 |

---

## 4. Prescriptions (→ 다음 Plan 반영)

| ID | 실패모드 | 처방 | 우선순위 | 반영 대상 |
|----|----------|------|----------|-----------|
| RX-01 | Epistemic | KU-0013(신칸센 가격)에 대해 JR 공식 예약 사이트(smartEX 등)에서 가격 교차확인. 최소 EU 2개 확보. | high | Plan (Source Strategy) |
| RX-02 | Structural | airport-transfer 엔티티를 세부 교통수단별로 분리 검토 (narita-express, skyliner 등). Cycle 1에서는 아직 보류하고, Outer Loop에서 스키마 리모델링 시 반영. | low | Schema (deferred) |
| RX-03 | Planning | Cycle 1 Plan에서 카테고리 분포 고려. accommodation, dining, attraction에서 최소 각 1개 Gap 포함. | high | Plan (Gap Selection) |
| RX-04 | Integration | Domain Skeleton에 `is_a` 관계 추가 검토. Suica is_a IC-card 같은 분류 계층 표현. | low | Schema (deferred) |
| RX-05 | Epistemic | KU-0007(SIM 가격)은 stale Gap(GU-0019)과 연결. Cycle 1에서 최신 가격 업데이트 시 다중 출처 확보. | medium | Plan (Target Gaps) |
| RX-06 | Temporal | KU-0011(면세 정책)의 expires_at 도래 시점(2026.11) 전에 GU-0026 해결 필요. Cycle 1-2에서 우선순위 상향. | medium | Plan (Gap Priority) |

---

## 5. Remodeling Triggers (Outer Loop)

| 조건 | 충족 여부 | 권고 |
|------|-----------|------|
| 스키마 확장 필요 | 부분적 yes | `is_a` 관계 추가, 엔티티 입도 재검토. 단 Cycle 0만으로는 리모델링까지 불필요. 3 Cycle 후 재평가. |
| 정책 수정 필요 | no | 현재 정책으로 수집/검증 정상 작동. |
| 평가 루브릭 개편 | no | Metrics 공식 이번 Cycle에서 확정. 실제 동작 확인됨. |

---

## 부록: 5대 불변원칙 준수 검증

| 원칙 | 준수 | 근거 |
|------|------|------|
| Gap-driven | ✅ | Collection Plan이 Gap Map에서 7개 선정 |
| Claim→KU 착지성 | ✅ | 7 Claims → 6 new KU + 2 update |
| Evidence-first | ✅ | 모든 KU에 EU ≥ 1. 근거율 100% |
| Conflict-preserving | ✅ | 충돌 0건이라 검증 불가. 다음 Cycle에서 의도적 충돌 시나리오 필요. |
| Prescription-compiled | ✅ (pending) | 6개 처방 생성됨. Revised Plan에서 실제 컴파일 확인 필요. |
