# Silver P2: Outer-Loop Remodel — Debug History
> Last Updated: 2026-04-15
> Status: **Gate PASS**

---

## D-P2-1: P3 연쇄 무효화로 Gate REVOKED

**증상**: P2 실 벤치 trial 준비 중 collect LLM parse가 모든 GU에서 0 claims 반환 발견.

**원인**: P3 D-120 참조. P3의 SEARCH→FETCH→PARSE(LLM) 통합 경로 미검증.
P2의 remodel 구현은 정상이지만, 그 위에서 동작하는 collect 파이프라인이 실제 claims를 생산하지 못하므로 실 벤치 trial 결과를 신뢰할 수 없음.

**영향**: P2 Gate PASS 무효 → P3 수정 후 순차 재판정 필요.

**조치**: P3R (snippet-first refactor) 완료 → Gap-Res Investigation (target_count cap 제거) → P2 재판정.

**해결**: P3R Gate PASS (D-125) + Gap-Res PASS (D-129) → P2 재판정 가능 (D-131).

---

## D-P2-2: Remodel 15c 실 벤치에서 미발동

**증상**: gap-res-fix-trial (15c)에서 remodel=0.0s 전 cycle. remodel이 한 번도 발동하지 않음.

**원인**: remodel 트리거 조건 = `audit.has_critical` (카테고리 KU 0개일 때만 critical).
15c면 모든 카테고리에 KU가 채워져서 항상 warning → remodel 항상 스킵.

**조치**: Smart Remodel Criteria 구현 (D-132).
- ① Growth Stagnation: KU 순증 < 5/cycle (3c 평균)
- ② Exploration Drought: 신규 GU < 30/5c 누적
- ③ 기존 audit critical
→ 3-way OR 조건으로 확장. commit `4b91521`.

**결과**: p2-smart-remodel-trial (15c)에서 cycle 10, 15에 자연 발동 (exploration_drought).

---

## D-P2-3: Merge 67개 과다 발동

**증상**: cycle 10에서 remodel 발동 시 67개 merge proposal 생성. 대부분 attraction 카테고리.

**원인**: KU 1개짜리 entity끼리 같은 (field, value) 공유 시 overlap 과대평가.
- attraction 27개 entity 중 12개가 (location, "Japan") 동일
- overlap = 1/1 = 100% → C(12,2) = 66쌍 전부 merge 판정

**조치**: `_MERGE_MIN_OVERLAP_COUNT = 2` 추가 (D-133).
overlap field-value 수가 2개 이상일 때만 merge 제안. commit `83b94ee`.

**결과**: 67 → 실질 중복만 잡히도록 수정. 613 tests PASS.
