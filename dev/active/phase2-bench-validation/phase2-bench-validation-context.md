# Phase 2: Bench Integration & Real Self-Evolution — Context
> Last Updated: 2026-03-05
> Status: Not Started

## 1. 핵심 파일

### 신규 생성 예정
| 파일 | 내용 |
|------|------|
| `src/adapters/llm_adapter.py` | OpenAI GPT LLM Adapter |
| `src/adapters/search_adapter.py` | Tavily Search Adapter |
| `src/config.py` | 환경 설정 (API 키, 모델명 등) |
| `src/orchestrator.py` | 사이클 관리 Orchestrator |
| `src/utils/metrics_logger.py` | 사이클별 Metrics 기록 |
| `src/utils/invariant_checker.py` | 5대 불변원칙 자동검증 |
| `scripts/bench_run.py` | 벤치 실행 스크립트 |

### 수정 예정
| 파일 | 수정 내용 |
|------|-----------|
| `src/nodes/seed.py` | CORE_CATEGORIES 하드코딩 제거 |
| `src/nodes/critique.py` | 실패모드 5/6, T2/T5, C3 수정 |
| `src/nodes/integrate.py` | LLM 기반 충돌 감지 |
| `src/nodes/plan_modify.py` | Gap Map 실제 변경 |
| `src/nodes/collect.py` | Real Search + LLM Claim 추출 |
| `src/nodes/plan.py` | LLM 기반 Plan 생성 |
| `src/graph.py` | State 전이 + Orchestrator 연동 |

### 기존 참조
| 파일 | 용도 |
|------|------|
| `docs/design-v2.md` | 전체 설계 (Schema, Metrics, 불변원칙) |
| `bench/japan-travel/state/*.json` | 벤치 State 데이터 (Cycle 2) |
| `schemas/*.json` | JSON Schema 4종 |

## 2. 기술 결정사항

| # | 결정 | 근거 |
|---|------|------|
| D-29 | OpenAI GPT | 범용 API, 비용 효율 |
| D-30 | Tavily Search | 무료 1000 req/month, LangChain 통합 |
| D-31 | 25 tasks 확대 | 10+ 사이클 검증 필수 |
| D-32 | 외부 Orchestrator | 사이클 간 save/snapshot/check 필요 |
| D-33 | Stage별 세션 분리 | 컨텍스트 효율 |

## 3. 한계점 (Phase 1에서 이관)

1. Real SearchTool adapter 없음 — MockSearchTool만 존재
2. Real LLM 통합 미테스트 — llm=None fallback만 사용
3. critique: Structural(5)/Integration(6) 실패모드 미구현
4. critique: T2 spillover_count, T5 domain_shift_detected 미설정
5. critique: C3 net_gap_changes 미전달 → 항상 True
6. integrate: 충돌 감지가 단순 str() 비교
7. seed: CORE_CATEGORIES japan-travel 하드코딩
8. plan_modify: Gap Map 실제 변경 안 함
9. Multi-cycle orchestrator 없음

## 4. 의존성

### Python 패키지 (신규)
| 패키지 | 용도 |
|--------|------|
| `langchain-openai` | ChatOpenAI |
| `tavily-python` | TavilySearchResults |

### 환경변수
| 변수 | 용도 |
|------|------|
| `OPENAI_API_KEY` | OpenAI API 인증 |
| `TAVILY_API_KEY` | Tavily Search 인증 |
