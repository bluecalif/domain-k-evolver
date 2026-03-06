# Phase 3: Cycle Quality Remodeling — Context
> Created: 2026-03-06
> Status: Planning

## 변경 대상 파일

| 파일 | 변경 내용 |
|------|-----------|
| `src/nodes/integrate.py` | `_detect_conflict()` 리팩터 (LLM semantic) |
| `src/nodes/critique.py` | dispute resolution workflow + C6 수렴 조건 |
| `src/nodes/plan_modify.py` | dispute 해소 처방 반영 |
| `src/utils/plateau_detector.py` | early stopping 복합 조건 확장 |
| `src/config.py` | conflict detection 설정 추가 |
| `tests/` | 신규 테스트 추가 |

## Phase 2 Baseline (비교 기준)

| 지표 | 값 |
|------|------|
| Active KU | 31 (Cycle 11) |
| Disputed KU | 54 |
| Active 성장률 | 0.4/cycle |
| conflict_rate | 0.64 |
| Disputed FP rate | 100% (54/54) |
| Health Grade | D (0.7/2.0) |
| Total entities (active) | 18 |
| Total entities (disputed unique) | 20 (11 신규) |

## 핵심 분석 결과 (Phase 2 보고서 요약)

1. **탐색 품질 우수**: disputed KU가 11개 신규 entity 발견, 지리적 다양성 더 높음
2. **통합 병목**: `_detect_conflict()` 문자열 비교 → 모든 업데이트가 conflict 판정
3. **FP 수정 효과**: active KU 성장률 0.4→4.6/cycle (11.5x) 추정
4. **카테고리 커버**: disputed에서 8/8 카테고리 커버

## 기술 결정 로그

| ID | 결정 | 근거 | 날짜 |
|----|------|------|------|
| D-40 | Phase 3 = Cycle Quality Remodeling | Phase 2 분석 결과 FP가 유일 병목 | 2026-03-06 |
| D-41 | TBD: conflict detection 방식 | pure LLM vs hybrid | — |
| D-42 | TBD: dispute resolution 전략 | 다수결 vs 최신우선 vs 출처신뢰도 | — |
| D-43 | TBD: C6 임계치 | 0.15 vs 0.20 | — |
