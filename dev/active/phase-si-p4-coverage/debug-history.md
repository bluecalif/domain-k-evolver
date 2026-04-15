# Silver P4: Coverage Intelligence — Debug History
> Last Updated: 2026-04-15
> Status: **Stage A~D Complete · Stage E Planning**

---

## Stage A~D 진행 중 발견 이슈 (2026-04-15)

### ISSUE-P4-01 (설계): novelty 자기참조 측정
- 증상: 15c bench novelty avg 0.127 (< gate 0.25). Stage A~D 구현은 계획대로 완료됐으나 Gate FAIL.
- 원인: `novelty.py` 가 cycle-diff (prev vs curr) 만 측정 → 시스템이 자기 collected set 에 수렴할수록 자연 감소. 우주 대비 측정 아님.
- 분석 문서: `mission-alignment-critique.md`, `mission-alignment-opinion.md`
- 결론: **구현 결함 아님, 측정 정의가 미션과 어긋남**. Stage E external_novelty (history-aware) 도입으로 해결.

### ISSUE-P4-02 (설계): coverage_map 이 skeleton 에 갇힘
- 증상: `deficit = 1 - min(1, ku_count / target_per_category)` 가 skeleton 내부만 측정.
- 원인: `target_per_category` 는 seed 시점 skeleton 에 하드코딩. skeleton 밖 영역 존재는 비가시.
- 결론: Stage E universe_probe + tiered skeleton (candidate_categories) 로 해결.

### ISSUE-P4-03 (해석): category_addition 15c 내 0회 발동
- 증상: Stage C 의 smart category_addition 이 japan-travel 15c 내내 발동 안 함.
- 1차 해석(기각): "보수성 과증명".
- 2차 해석(채택): 반응형 트리거 (≥5 KU 패턴) 는 이미 수집한 데이터에서만 튀어나옴 → skeleton 밖 영역은 구조적으로 발동 불가.
- 결론: Stage E L4b universe_probe 로 **선제적** category 후보 발굴. 기존 L4a 경로와 병행.

---

## Stage E 진행 시 여기에 새 항목 추가
