# Phase 0C Context — GU 전략 재검토
> Last Updated: 2026-03-04
> Status: Not Started

## 1. 핵심 파일

### 직접 참조
| 파일 | 내용 | 용도 |
|------|------|------|
| `docs/gu-bootstrap-expansion-policy.md` | GU 확장 정책 v0.1 (Axis Coverage, Quantum Jump, Guardrail) | 검증 대상 정책 |
| `docs/gu-bootstrap-spec.md` | 현행 GU Bootstrap 명세 (v1.0) | 통합 대상 |
| `bench/japan-travel/state/gap-map.json` | 현재 31 GU (16 open / 15 resolved) | Matrix 입력 |
| `bench/japan-travel/state/domain-skeleton.json` | 카테고리/필드/관계 (축 보완 대상) | 수정 대상 |
| `bench/japan-travel/state/knowledge-units.json` | KU 21개 (active 19 + disputed 2) | 축 태그 참조 |
| `bench/japan-travel/cycle-1/revised-plan-c2.md` | Cycle 2 Collection Plan | Cycle 2 실행 입력 |
| `docs/design-v2.md` | 전체 설계 문서 | 통합 반영 대상 |

### 간접 참조
| 파일 | 내용 |
|------|------|
| `bench/japan-travel/cycle-1/critique-c1.md` | Cycle 1 Critique (RX-07~11, 구조적 한계 언급) |
| `schemas/gap-unit.json` | GU JSON Schema (선택 필드 추가 대상) |
| `templates/critique-report.md` | Critique 템플릿 (Structural Deficit Analysis 추가) |
| `templates/revised-plan.md` | Revised Plan 템플릿 (explore/exploit budget 추가) |

---

## 2. 문제 분석 요약

### expansion-policy v0.1의 3대 진단

| # | 문제 | 현재 증거 (japan-travel) |
|---|------|--------------------------|
| 1 | 국소 최적화 편향 | 동적 GU 3개만 생성 (base mode), 기존 open GU 주변만 탐색 |
| 2 | 스켈레톤 불완전성 | category 축만 관리, geography/condition/risk 미추적. 오사카/교토/지방 GU = 0 |
| 3 | 상한 경직성 | 20% 고정 상한으로 Cycle당 최대 4개 — 구조 결손 회복 느림 |

### Phase 0C로 검증할 제안 요소

| 요소 | 정의 상태 | Phase 0C 검증 목표 |
|------|-----------|-------------------|
| Axis Coverage Matrix | 개념만 제안 | 계산 로직 구체화 + 첫 실측 |
| Quantum Jump Mode | trigger 5가지 열거, 임계치 미정 | Cycle 2 수동 테스트로 trigger 검증 |
| explore/exploit budget | 단위 불명확 | GU 개수 기반으로 구체화 |
| Guardrail 4종 | 규칙 서술 | Cycle 2에서 작동 여부 확인 |
| Base Mode cap 공식 | `min(max(4, ceil(open * 0.2)), 12)` | 기존 20% 대비 차이 확인 |
| Jump Mode cap 공식 | `min(max(10, ceil(open * 0.6)), 30)` | 실전 적정성 검증 |

---

## 3. 축(Axis) 정의 초안

japan-travel 도메인 기준, Phase 0C에서 확정할 축:

| 축 | 설명 | Anchor 후보 |
|----|------|-------------|
| category | 정보 카테고리 (기존) | transport, accommodation, attraction, dining, regulation, pass-ticket, connectivity, payment |
| geography | 지역성 | tokyo, osaka, kyoto, rural, nationwide |
| condition | 조건/시즌/채널 | peak-season, off-season, weekday, weekend, online, in-person |
| risk | 리스크 유형 | safety, financial, policy, convenience, informational |

> **주의**: condition 축은 일부 GU에만 해당. 모든 GU에 강제 태깅하지 않음.

---

## 4. 데이터 인터페이스

### Axis Coverage Matrix 구조 (제안)

```json
{
  "axis_name": "geography",
  "values": {
    "tokyo": {"open": 5, "resolved": 3, "critical_open": 1, "evidence_density": 2.1},
    "osaka": {"open": 0, "resolved": 0, "critical_open": 0, "evidence_density": 0},
    "kyoto": {"open": 0, "resolved": 0, "critical_open": 0, "evidence_density": 0},
    "rural": {"open": 0, "resolved": 0, "critical_open": 0, "evidence_density": 0},
    "nationwide": {"open": 11, "resolved": 12, "critical_open": 0, "evidence_density": 1.8}
  },
  "deficit_ratio": 0.6
}
```

### Jump Mode Trigger 판정 입력

```
trigger_input = {
  axis_coverage_matrix,
  current_gap_map,
  critique_prescriptions,
  collect_spillover_count,
  high_risk_blindspot_count
}
```

---

## 5. 주요 결정사항 (Phase 0C 내)

| # | 결정 예정 사항 | 대안 | 판단 기준 |
|---|---------------|------|-----------|
| D-0C.1 | axes를 skeleton에 포함 vs 별도 파일 | 별도 axis-map.json | skeleton 일체가 참조 단순 |
| D-0C.2 | Jump Mode trigger 임계치 (axis under-coverage) | 0%, 20%, 30% | Cycle 2 실측 기반 |
| D-0C.3 | explore/exploit 비율 초기값 | 50:50, 60:40, 70:30 | Cycle 2 실측 기반 |
| D-0C.4 | condition 축 강제 vs 선택 태깅 | 강제 | GU 특성상 일부만 해당 → 선택 유력 |
| D-0C.5 | design-v2 업데이트 vs design-v3 신규 | — | 변경 범위에 따라 판단 |

---

## 6. 컨벤션 체크리스트 (Phase 0C 추가)

### Axis Coverage 검증
- [ ] 모든 선언된 축에 최소 1개 anchor가 정의되어 있다
- [ ] 각 GU에 적용 가능한 축 태그가 할당되어 있다
- [ ] deficit_ratio 계산이 정확하다 (값 0인 anchor / 전체 anchor)

### Jump Mode 검증
- [ ] Trigger 판정이 명시적이다 (어떤 trigger가 발동했는지 기록)
- [ ] jump_cap 이내로 GU가 생성되었다
- [ ] 신규 GU 중 high/critical ≥ 40%
- [ ] Guardrail 4종 위반 없음

### explore/exploit 검증
- [ ] budget 배분이 명시되어 있다 (단위: GU 개수)
- [ ] explore GU가 실제로 신규 축 영역을 커버한다
- [ ] exploit GU가 기존 open GU 해결에 기여한다
