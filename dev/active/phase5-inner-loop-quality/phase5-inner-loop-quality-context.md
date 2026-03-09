# Phase 5: Inner Loop Quality — Context
> Last Updated: 2026-03-09
> Status: In Progress — Stage E-2 (VP2 잔여 FAIL 해결)

## 1. 핵심 파일

### 수정 대상
| 파일 | 변경 내용 | Stage |
|------|-----------|-------|
| `src/utils/readiness_gate.py` | VP1-R1 Shannon→Gini, VP1-R2 blind_spot KU 기반 | 선행, A |
| `src/state.py` | KnowledgeUnit에 `axis_tags: dict` 추가 | A |
| `src/nodes/integrate.py` | GU→KU axis_tags 전파, geography 추론, refresh 통합, field 다양성 억제 | A, B, C |
| `src/nodes/critique.py` | Refresh GU 자동생성, category balance GU 생성 | B, C |
| `src/nodes/plan.py` | 소수 카테고리 GU 우선 선택 (필요시) | C |
| `src/nodes/mode.py` | target_count/cap 하드캡 제거 — 비례 스케일링 | D |
| `scripts/run_readiness.py` | 더블 서픽스 버그 수정 (L104, L162) | D |

### 참조 파일
| 파일 | 참조 이유 |
|------|-----------|
| `docs/phase4-readiness-report.md` | Gate FAIL 상세 분석 |
| `bench/japan-travel-readiness/readiness-report.json` | Gate 수치 데이터 |
| `bench/japan-travel-readiness/state/*.json` | 벤치 최종 State |
| `src/utils/metrics.py` | staleness_risk 계산 로직, 건강 임계치 |
| `src/nodes/audit.py` | axis_coverage 계산, audit findings |
| `src/config.py` | OrchestratorConfig 파라미터 |
| `schemas/gap-unit.json` | GU axis_tags 스키마 |
| `schemas/knowledge-unit.json` | KU 스키마 (axis_tags 추가 필요) |

## 2. 데이터 인터페이스

### axis_tags 흐름 (Phase 5 신규)
```
[GU.axis_tags] ──(Integrate)──> [KU.axis_tags]
     ↑                                ↓
[동적 GU 생성]                  [Readiness Gate VP1-R2]
  entity_key에서                 KU 기반 blind_spot 계산
  geography 추론
```

### Refresh GU 흐름 (Phase 5 신규)
```
[Critique] ──> stale KU 감지 ──> Refresh GU 생성 (gap_type="stale")
                                      ↓
[Plan] ──> Refresh GU 선택 ──> [Collect] ──> [Integrate]
                                                ↓
                                        기존 KU 업데이트
                                        (observed_at 갱신)
```

### Category Balance GU 흐름 (Phase 5 신규)
```
[Critique] ──> min_ku < 5 감지 ──> Balance GU 생성 (trigger="E:category_balance")
                                         ↓
[Plan] ──> Balance GU 선택 ──> [Collect] ──> [Integrate] ──> 신규 KU 생성
```

## 3. 주요 결정사항

| # | 결정 | 근거 | Phase |
|---|------|------|-------|
| D-53 | VP1-R1 Shannon Entropy → Gini Coefficient | Shannon은 분포 균등성 미측정 (8.7x 차이도 PASS) | 5 |
| D-54 | Geography 추론 = 규칙 기반 (entity_key 패턴 매칭) | LLM 호출 불필요, 도메인 skeleton anchors로 충분 | 5 |
| D-55 | Refresh GU cycle당 상한 설정 | 59개 동시 생성 방지, 점진적 갱신 | 5 |
| D-56 | Field 다양성 = count > mean×1.5 억제 | category-specific 필드 우선, `*` 필드 편중 해소 | 5 |
| D-57 | Readiness Gate seed state(cycle-0) fresh start | Phase 5 코드 효과 독립 측정 | 5 |
| D-58 | Orchestrator plateau_window=0 비활성화 | Gate 벤치 시 plateau 간섭 방지 | 5 |
| D-59 | run_readiness.py japan-travel-readiness 분리 저장 | 원본 bench 데이터 보호 | 5 |
| D-60 | target_count/cap 하드캡 제거 — 비례 스케일링 | GU 생성(~72/cycle) >> 해결(~8/cycle) 구조적 불균형 해소. dynamic_gu_cap은 유지. | 5 |
| D-61 | bench/ 더블 서픽스 버그 수정 + 아티팩트 정리 | run_readiness.py에서 `-readiness` 이중 적용 → `japan-travel-readiness-readiness` 생성 버그 | 5 |
| D-62 | stale refresh observed_at = today 고정 | evidence의 오래된 observed_at 사용 시 refresh 후에도 stale 유지 버그 | 5 |
| D-63 | stale refresh confidence 가중 평균 (0.3:0.7) | 최신 evidence가 더 신뢰할 수 있으므로 0.7 가중 | 5 |
| D-64 | Adaptive REFRESH_GU_CAP (staleness 비례) | 고정 cap=10으로 93 stale KU 소화 불가, 적응형 스케일링 | 5 |
| D-65 | T7 Staleness Trigger → Jump Mode | staleness_risk > 20 시 Jump Mode로 수집량 확대 | 5 |
| D-66 | Closed Loop 세분화 — category별 findings 감소 인정 | 전체 findings 수 비교만으로는 closed_loop 판정 불충분 | 5 |
| D-67 | 신규/condition_split KU observed_at = today 고정 | KU의 observed_at은 "시스템 확인 시점"이지 "원본 출처 작성일"이 아님. 생성 즉시 stale 방지 | 5 |
| D-68 | 일반 업데이트 observed_at = today 갱신 | 새 evidence로 KU 확인 시점 = today. stale refresh(D-62)와 일관성 확보 | 5 |
| D-69 | evidence-count 가중 평균 confidence | `(old*N+new)/(N+1)` — N개 evidence 누적 결과를 1:1 단순 평균으로 파괴 방지 | 5 |
| D-70 | multi-evidence confidence boost (삼각측량) | 독립 출처 N개 확인 → 단일 출처보다 높은 신뢰도. ≥2→+0.03, ≥3→+0.05, ≥4→+0.07 | 5 |

## 4. 컨벤션 체크리스트

### 5대 불변원칙 영향
- **Gap-driven**: Refresh GU, Balance GU 모두 Gap Map에 추가 → Plan이 선택 ✅
- **Claim→KU 착지성**: Refresh 통합 시 기존 KU 업데이트 (신규 KU 아님) → 별도 처리 필요
- **Evidence-first**: Refresh 통합 시 새 EU 추가 필수 ✅
- **Conflict-preserving**: 변경 없음 ✅
- **Prescription-compiled**: Refresh GU는 Critique prescription의 실체화 ✅

### Metrics 임계치
- staleness_risk: 건강=0, 주의=1~3, 위험=>3 (변경 없음)
- Gini threshold: ≤0.45 (category/field 동일 기준)

### Gate 기준 변경
| 기준 | 변경 전 | 변경 후 |
|------|---------|---------|
| VP1-R1 | Shannon Entropy ≥ 0.75 | Gini Coefficient ≤ 0.45 |
| VP1-R2 | resolved GU axis_tags 기반 | KU axis_tags 기반 (+ GU fallback) |
