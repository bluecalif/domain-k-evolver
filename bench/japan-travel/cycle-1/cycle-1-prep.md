# Cycle 1 준비 문서

> **생성일**: 2026-03-03
> **Phase**: 0B — Cycle 1 수동 검증

---

## 1. revised-plan-c1.md 최종 리뷰 체크

| 항목 | 확인 | 비고 |
|------|------|------|
| 8개 Target Gap 명시 | OK | GU-0001,0003,0007,0008,0010,0013,0019,0026 |
| Source Strategy 명시 | OK | financial 2출처 필수, 카테고리 분포 5개+ |
| Acceptance Tests 명시 | OK | GU별 해결 조건, 최소 EU, 신선도 기준 |
| Budget & Stop Rules | OK | 15회 검색 상한, 동일출처 3회 제한 |
| 처방 추적성 (RX-01~06) | OK | 6개 처방 모두 반영 방법/위치 기록 |

---

## 2. Cycle 0 State 스냅샷 요약

| 항목 | 값 |
|------|----|
| KU 수 | 13 (active 13, disputed 0) |
| EU 수 | 18 |
| GU open | 21 |
| GU resolved | 7 |
| 근거율 | 1.0 |
| 다중근거율 | 0.538 |
| Gap 해소율 | 0.28 |
| 평균 confidence | 0.888 |

---

## 3. 충돌 시나리오 계획

Cycle 1에서 의도적으로 충돌을 탐지/보존할 3개 시나리오:

### 시나리오 1: GU-0019 SIM 가격 (높은 확률)
- **기존**: KU-0007 — 7일 3GB 약 1500-3000 JPY, 15일 무제한 약 3000-5000 JPY
- **기존 신뢰도**: confidence 0.70, 단일출처 (EU-0006)
- **예상 충돌**: 2026년 eSIM 보급 확대로 가격 구조 변화, 물리 SIM vs eSIM 가격 차이
- **처리 계획**: 2개 독립출처 확보 (RX-05) → 기존 KU-0007 값과 비교 → 가격 범위 불일치 시 `disputed` 설정, `condition_split` (물리SIM vs eSIM) 시도

### 시나리오 2: GU-0001 JR Pass Nozomi 대안 (중간 확률)
- **기존**: KU-0005 — "Nozomi/Mizuho 제외" 명시, 시간 비교 없음
- **예상 충돌**: Hikari/Kodama 소요시간 출처 간 차이 (운행 변경, 정차역 차이)
- **처리 계획**: 신규 KU 생성 (nozomi-alternative 필드) → KU-0005와 시간 관련 수치 불일치 시 `condition_split` (열차 종류별)

### 시나리오 3: GU-0026 면세 신제도 절차 (낮은 확률)
- **기존**: KU-0011 — 2026.11 신제도 "환급형" 기재, 세부 절차 미확정
- **예상 충돌**: 신제도 세부 절차가 기존 기재와 다를 수 있음 (최소금액 유/무, 환급 방법)
- **처리 계획**: 공식 출처 확보 → KU-0011 update 또는 신규 KU → 기존 값과 상충 시 `hold` (시행 전이므로)

### 충돌 처리 원칙 (design-v2.md §6 + policies.json)
1. 충돌 발견 즉시 `status: "disputed"` 설정
2. `disputes[]`에 충돌 정보 (상대 KU, 출처, 차이점) 기록
3. 판정: `hold` (추가 출처 필요) / `condition_split` (조건 분리 가능) / `coexist` (양립 가능)
4. **삭제 금지** — Conflict-preserving 불변원칙

---

## 4. 동적 GU 발견 대비 (gu-bootstrap-spec §2)

| 트리거 | 조건 | 예상 시나리오 |
|--------|------|---------------|
| A: 인접 Gap | 새 KU가 미지 슬롯 참조 | metro 이용법 → 노선별 가격 Gap 발생 가능 |
| B: Epistemic | 단일출처 + safety/financial | credit-card acceptance 단일출처 시 uncertain GU |
| C: 새 엔티티 | Skeleton에 없는 entity_key | eSIM 별도 엔티티 발견 시 핵심 필드 GU 배치 |
| **상한** | 신규 GU ≤ 4개 (open 21의 20%) | safety 예외 적용 가능 |
