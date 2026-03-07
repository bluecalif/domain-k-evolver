# Phase 4: Self-Governing Evolver — Context
> Created: 2026-03-07
> Status: Planning

## 변경 대상 파일 (예상)

| 파일 | 변경 내용 |
|------|-----------|
| `src/nodes/audit.py` | **신규** — Executive Audit 노드 |
| `src/utils/metrics.py` | 다축 교차 매트릭스, KU yield/cost 계산 추가 |
| `src/utils/coverage_matrix.py` | **신규** — category × geography × condition × risk 교차 분석 |
| `src/orchestrator.py` | audit 주기 실행, policy rollback 로직 |
| `src/config.py` | audit_interval, budget 설정 추가 |
| `src/state.py` | AuditReport 타입, policy version 필드 |
| `src/nodes/mode.py` | explore/exploit 비율 동적 조정 |
| `src/nodes/critique.py` | threshold 적응 반영 |
| `src/utils/metrics_guard.py` | 적응형 threshold |
| `src/utils/policy_manager.py` | **신규** — policy 수정/롤백/버전 관리 |
| `schemas/policy.json` | **신규** — Policy JSON Schema |
| `bench/japan-travel/state/policies.json` | version 필드 + change_history 추가 |
| `tests/` | 신규 테스트 (예상 30~40개) |
| `scripts/run_bench.py` | audit 주기 + budget 옵션 |

## Phase 3 → Phase 4 갭 분석

| 영역 | 현재 (Phase 3) | 목표 (Phase 4) |
|------|---------------|---------------|
| Audit | Metrics 관찰만 (passive) | N-cycle 자동 진단 + 권고 (active) |
| Policy | 정적 JSON (전 cycle 불변) | Audit 결과 → 자동 수정 + 롤백 |
| Threshold | 하드코딩 (D-43 등) | 실적 기반 이동 평균 적응 |
| Explore/Exploit | stage별 고정 (60/40→40/60) | yield 기반 동적 조정 |
| Cost | 추적만 (metrics_logger) | Budget 설정 + graceful degradation |
| 커버리지 진단 | axis_coverage (단축) | 다축 교차 매트릭스 (category×geo×cond×risk) |
| Readiness | 없음 | 3-Viewpoint Gate (필수) |

## Phase 번호 체계 결정

| ID | 결정 | 근거 | 날짜 |
|----|------|------|------|
| D-44 | Phase 4 = Self-Governing Evolver | 단일 도메인 자기 진화 보장이 multi-domain 전제 | 2026-03-07 |
| D-45 | Multi-Domain = Phase X (잠정) | Readiness Gate 통과 후 번호 확정 | 2026-03-07 |
| D-46 | 3-Viewpoint Readiness Gate 필수 | Variability + Completeness + Self-Governance | 2026-03-07 |
| D-47 | Gate FAIL 시 Phase N+1 삽입 | 보완 Phase 후 Gate 재실행 | 2026-03-07 |

## 참조 문서

| 문서 | 용도 |
|------|------|
| `docs/phase3-analysis.md` | Phase 3 결과 baseline |
| `docs/design-v2.md` §9 | Outer Loop / Executive Audit 원안 |
| `bench/japan-travel-auto/trajectory/` | 10 Cycle trajectory 데이터 |
| `src/utils/metrics.py` | 현재 metrics 계산 로직 |
| `src/nodes/mode.py` | 현재 mode switching 로직 |
| `bench/japan-travel/state/policies.json` | 현재 정적 정책 |
