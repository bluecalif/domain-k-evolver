# Phase 3: Cycle Quality Remodeling — Plan
> Created: 2026-03-06
> Status: Planning

## 1. 목적

Phase 2 심층 분석(docs/phase2-analysis.md)에서 도출된 6대 권고(R1~R6)를 구현하여
Cycle 품질을 근본적으로 개선한다.

**핵심 문제**: integrate 노드의 `_detect_conflict()` 문자열 비교가 FP 100% (54/54)를 유발.
- active KU 성장률: 0.4/cycle (현재) → 4.6/cycle (FP 수정 시 추정, 11.5x)
- disputed KU에 11개 신규 entity + 8/8 카테고리 커버 → 탐색 품질 자체는 우수

## 2. 입력 조건

- Phase 2 완료 (272 tests, 16/16 tasks)
- 10 Cycle 실행 데이터: `bench/japan-travel-auto/`
- 심층 분석 보고서: `docs/phase2-analysis.md`
- R1~R6 권고 사항 확정

## 3. Stage 구성

### Stage A: Semantic Conflict Detection (R1)
> **Gate**: _detect_conflict FP rate < 30%

- **3.1** `_detect_conflict()` → LLM semantic conflict detection
  - 기존: `str(existing_value) != str(new_value)` → 모든 업데이트가 conflict
  - 개선: LLM에게 "실제 의미적 충돌인지" 판단 요청
  - 고려사항: LLM 호출 비용 vs 정확도 트레이드오프
- **3.2** 충돌 판정 테스트 + FP rate 측정
  - disputed KU 54개 중 실제 conflict 분류
  - 단위 테스트 작성
- **3.3** 10 Cycle 재실행으로 FP 감소 확인
  - Phase 2 결과 대비 active KU 성장률 비교

### Stage B: Dispute Resolution (R2~R4)
> **Gate**: disputed→active 전환 경로 작동 확인

- **3.4** dispute resolution mechanism 설계 + 구현
  - 다수결, 최신 우선, 출처 신뢰도 기반 등 전략 선택
- **3.5** disputed→active 전환 경로
  - 자동 해소 조건 정의 + 구현
- **3.6** critique 노드에 dispute resolution workflow 추가
  - critique 시 disputed KU 목록 평가 + 해소 권고

### Stage C: 수렴 개선 + 재검증 (R5~R6)
> **Gate**: 10 Cycle 완주 시 Health Grade B 이상

- **3.7** 수렴 조건 C6: conflict_rate < 0.15 상한
- **3.8** early stopping 개선 (plateau + conflict_rate 복합)
- **3.9** 최종 10 Cycle 실행 + 개선 효과 보고
  - Phase 2 baseline 대비 정량 비교

## 4. 성공 기준

| 지표 | Phase 2 (baseline) | Phase 3 목표 |
|------|-------------------|-------------|
| Active KU 성장률 | 0.4/cycle | ≥ 3.0/cycle |
| Disputed FP rate | 100% | < 30% |
| conflict_rate | 0.64 (최종) | < 0.15 |
| Health Grade | D (0.7/2.0) | B (≥ 1.4/2.0) |

## 5. 리스크

| 리스크 | 심각도 | 완화 |
|--------|--------|------|
| LLM conflict 판정 비용 증가 | Medium | 배치 처리, 캐시, 간단한 경우 rule-based 선처리 |
| dispute resolution 전략 선택 불확실 | Medium | 복수 전략 비교 실험 |
| 기존 테스트 호환성 | Low | Mock LLM 기반 테스트 유지 |

## 6. 기술 결정 필요

- D-41: conflict detection 방식 — pure LLM vs hybrid (rule + LLM)
- D-42: dispute resolution 전략 — 다수결 vs 최신우선 vs 출처신뢰도
- D-43: conflict_rate 상한 C6의 정확한 임계치 (0.15 vs 0.20)
