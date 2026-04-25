# Session Compact

> Generated: 2026-04-25
> Source: Conversation compaction via /compact-and-go

## Goal

SI-P7 rebuild Stage B 진입. Option B 재순서 적용 (P2+P3 패턴) + Pre-Stage B (S4-T1) + Stage B-1/B-2 (S3-T1/T2) 완료.

---

## Completed

### Stage B 재구성 + Pre-Stage B

- [x] **Option B 채택**: tasks.md Stage B 섹션 재구성
  - Pre-B (S4-T1) → B-1/B-2 (S3-T1~T8) → B-3 (S2-T3~T8) → B-4 (S4-T2~T4)
  - P3 측정 오염원 먼저 제거, P2 root cause 먼저

- [x] **Pre-Stage B / S4-T1**: virtual `balance-N` entity 완전 제거 (commit `56e4649`)
  - `src/nodes/critique.py`: `_generate_balance_gus` 함수 + `MIN_KU_PER_CAT` 삭제, 호출 블록 삭제
  - `tests/test_nodes/test_critique.py`: `TestGenerateBalanceGus` → `TestBalanceGuRegression` (3 cases)
  - L1: 835 passed ✓ | L2: `p7-s4-t1-smoke` (1c) — balance-* 0건, KU 13→24 ✓

### Stage B-1/B-2 (S3-T1, S3-T2)

- [x] **S3-T1**: D-56 suppress 완전 제거 (commit `2fa51e0`)
  - 결정: 1.5→2.0 변경 대신 suppress 자체 제거 — "field 풍부한 쪽이 좋다"
  - `src/nodes/integrate.py`: `_generate_dynamic_gus` 에서 suppressed_fields 블록 삭제, `kus` 파라미터 제거
  - `tests/test_nodes/test_integrate.py`: `TestFieldDiversitySuppression` → `TestSuppressRemovalRegression` (3 cases)
  - 효과: adj GU 0→6건, price field 생성 허용, adj_gen=0 root cause 제거

- [x] **S3-T2**: `recent_conflict_fields` blocklist N=2 구현 (commit `2fa51e0`)
  - `src/state.py`: `recent_conflict_fields: list[dict]` 필드 추가
  - `src/nodes/integrate.py`: conflict 감지 시 field 기록, 2c window 트리밍, adj GU 차단 로직
  - `tests/test_nodes/test_integrate.py`: `TestRecentConflictFieldsBlocklist` (3 cases)
  - L1: 838 passed ✓ | L2: `p7-s3-t1t2-smoke` (1c) — adj=6, KU 13→32, balance-* 0 ✓

---

## Current State

- **브랜치**: `feature/si-p7-rebuild`
- **최신 commit**: `d9dad76` ([si-p7] S3-T3/T4: field_adjacency rule engine seed + 참조 구현)
- **테스트**: 841 passed, 3 skipped
- **Stage A**: 완료 (S1 5c + S2-T1/T2 1c Gate PASS)
- **Pre-Stage B**: S4-T1 완료 (1c Gate PASS)
- **Stage B-1/B-2**: S3-T1/T2 완료 (L1 + L2 1c PASS), S3-T3/T4 완료 (L1 + L2 1c PASS)

### Changed Files (this session)

| 파일 | 변경 |
|---|---|
| `dev/active/phase-si-p7-structural-redesign/si-p7-tasks.md` | Stage B Option B 재구성, S4-T1/S3-T1/T2 완료 마킹 |
| `src/nodes/critique.py` | `_generate_balance_gus` + `MIN_KU_PER_CAT` 제거, balance_gus 호출 블록 제거 |
| `src/nodes/integrate.py` | D-56 suppress 블록 제거, `recent_conflict_fields` blocklist N=2 추가 |
| `src/state.py` | `recent_conflict_fields: list[dict]` 필드 추가 |
| `tests/test_nodes/test_critique.py` | `TestGenerateBalanceGus` → `TestBalanceGuRegression` |
| `tests/test_nodes/test_integrate.py` | `TestFieldDiversitySuppression` → `TestSuppressRemovalRegression` + `TestRecentConflictFieldsBlocklist` |
| `bench/silver/japan-travel/p7-s4-t1-smoke/` | Pre-B S4-T1 1c smoke 결과 |
| `bench/silver/japan-travel/p7-s3-t1t2-smoke/` | S3-T1/T2 1c smoke 결과 |

---

## Remaining / TODO

### Stage B-2 (S3-T3~T8) — rule engine 본체

- [ ] **S3-T3**: `domain-skeleton.json` 에 `field_adjacency` rule engine seed 추가
  - 형식: `field_adjacency: {source_field: [next_fields]}` — skeleton level에 정의
  - 참조: `bench/japan-travel/state/domain-skeleton.json` (현재 skeleton 확인 필요)
- [ ] **S3-T4**: `_generate_dynamic_gus` 가 rule engine 참조 (L2: `si-p7-s3-t4-smoke` 1c)
- [ ] **S3-T5**: `fields[].default_risk`, `default_utility` skeleton 추가
- [ ] **S3-T6**: dynamic GU 가 skeleton default 사용
- [ ] **S3-T7**: rule yield tracker — 약화 임계 5c 평균 < 0.05 (L2: `si-p7-s3-t7-smoke` 5c)
- [ ] **S3-T8**: blocklist N cycle 동안 source/next 양쪽 배제 (현재 S3-T2는 next만 차단)
- [ ] **S3 Axis Gate** (5c smoke): GU_open c3+ ≥ 5, target c5 ≥ 3, KU c5 ≥ 70

### Stage B-3 (S2-T3~T8) — condition_split

- [ ] **S2-T3** F2 = α + β 확정 (design only)
- [ ] **S2-T4~T8** F2 구현 + condition_split 4 rules
- [ ] **S2 Axis Gate** (5c): c1 ΔKU ≤ +35, KU c5 ≥ 90

### Stage B-4 (S4-T2~T4) — balance 대체

- [ ] **S4-T2~T4** deficit_score, field_adjacency 통일, S5a entity 한정

### Stage C / D

- [ ] S5a (entity discovery), S5a 5c gate
- [ ] Stage D: 15c L3 통합 trial + readiness-report

---

## Key Decisions

### 이번 세션 확정

- **Option B 채택**: Pre-B(S4-T1) 분리 + S3↔S2 역전. Full option A는 과잉. Minimal C는 부족.
- **S4-T1**: balance-N virtual entity 완전 제거. S1 5c re-smoke KU=104 초과 단일 원인.
- **S3-T1 — suppress 완전 제거** (1.5→2.0 변경 대신): "field 풍부한 쪽이 좋다". suppress는 합법적 adj GU를 차단하고 adj_gen=0 root cause. S3-T3 rule engine이 올바른 대체제.
- **S3-T2 — N=2** (original spec N=3): 보수화. 더 짧은 window가 conflict field를 더 빠르게 해제.

### Stage A에서 확정 유지

- **F1**: budget 완전 제거. `gu_queries[:3]` hard-cap (D-129 guard 보호)
- **S1 Gate 조건부 PASS**: KU=104 초과는 balance-N 원인 → S4-T1로 해결 완료
- **S2-T2 reason code**: `integration_added_low`, `adjacent_yield_low` 2개

---

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### S3-T3 설계 사전 정보

- **현재 skeleton**: `bench/japan-travel/state/domain-skeleton.json` (seed 스테이트) 또는 `bench/silver/japan-travel/p7-s3-t1t2-smoke/state/domain-skeleton.json` (최신 run 결과)
- **field_adjacency 형식** (SKILL.md 기준): `{source_field: [next_fields]}`
  - 예: `"price": ["tips", "how_to_use"]`, `"location": ["access", "hours"]`
- **S3-T4 영향 범위**: `_generate_dynamic_gus` — 현재 `applicable_fields`를 skeleton fields로 계산. rule engine 참조 시 `field_adjacency[field]` 우선, fallback은 기존 방식.
- **S3-T5**: `fields[].default_risk` ("low"/"medium"/"high"), `default_utility` ("high"/"medium"/"low")
- **S3-T6**: dynamic GU의 `expected_utility`/`risk_level` 가 skeleton default 참조 (현재 "medium"/"convenience" 하드코딩)

### L2 1c smoke 결과 비교

| trial | KU | adj GU | balance-* |
|---|---|---|---|
| p7-s4-t1-smoke (Pre-B) | 24 | 0 (suppress 있음) | 0 ✓ |
| p7-s3-t1t2-smoke (S3-T1/T2) | 32 | 6 | 0 ✓ |

suppress 제거 후 KU +8 (+33%) — adj GU 생성이 KU 성장에 직접 기여 확인.

### 제약

- **D-129**: target_count cap 재도입 금지 (S1-T7 guard 보호)
- **D-34**: real API 필수
- **D-200**: per-axis 5c gate 통과 전 다음 axis 진입 금지
- **F1 (확정)**: budget 재도입 금지

### 최근 commits

- `2fa51e0` [si-p7] S3-T1/T2: D-56 suppress 제거 + conflict blocklist N=2
- `56e4649` [si-p7] Pre-B / S4-T1: virtual balance-N entity 완전 제거
- `40a5dfa` [si-p7] S2 Gate: PASS (Stage A 최종)

---

## Next Action

**S3-T3 착수**: `domain-skeleton.json`에 `field_adjacency` rule engine seed 추가

1. `bench/japan-travel/state/domain-skeleton.json` 읽어 현재 fields 목록 확인
2. field 간 인접 관계 설계 (japan-travel 도메인 기반)
3. skeleton에 `field_adjacency` 키 추가
4. S3-T4: `_generate_dynamic_gus`가 `field_adjacency` 참조하도록 수정
   - `field_adjacency[claim.field]` → adj_field list
   - fallback: 기존 `applicable_fields` (skeleton.fields 전체)
5. L1 + L2 `si-p7-s3-t4-smoke` (1c) — adj GU field가 seed 맵 내 확인
