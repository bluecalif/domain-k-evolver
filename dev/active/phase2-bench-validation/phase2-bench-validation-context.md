# Phase 2: Bench Integration & Real Self-Evolution — Context
> Last Updated: 2026-03-05 (Stage A'+B' 완료)
> Status: In Progress — Stage C' 진행 예정

## 1. 핵심 파일

### Stage A'+B' 완료 (254 tests 통과)
| 파일 | 내용 | 상태 |
|------|------|------|
| `src/config.py` | 환경 설정 (gpt-4.1-mini 확정) | ✅ |
| `src/adapters/llm_adapter.py` | LLMCallCounter 래퍼 + max_retries=3 + MockLLM | ✅ |
| `src/adapters/search_adapter.py` | Tavily 래퍼 + retry 백오프 + 호출 카운터 | ✅ |
| `src/utils/metrics_logger.py` | API calls/tokens 필드 추가 | ✅ |
| `src/utils/invariant_checker.py` | 5대 불변원칙 자동검증 (I1~I5) | ✅ 신규 |
| `src/utils/llm_parse.py` | LLM 응답 JSON 추출 (markdown fence 제거) | ✅ |
| `src/nodes/seed.py` | CORE_CATEGORIES 동적화 (skeleton 기반) | ✅ |
| `src/nodes/collect.py` | 프롬프트 정교화 + max_workers=5 | ✅ |
| `src/nodes/plan_modify.py` | 실제 plan/gap_map 수정 | ✅ |
| `src/nodes/critique.py` | C3 net_gap_changes 계산 + 전달 | ✅ |
| `src/nodes/mode.py` | jump target_count 상한 10 | ✅ |
| `src/state.py` | net_gap_changes 필드 추가 | ✅ |
| `scripts/run_one_cycle.py` | 1사이클 Real API 실행 + API 카운터 | ✅ 신규 |
| `scripts/run_bench.py` | N사이클 CLI 벤치 실행 + 불변원칙 + trajectory | ✅ 신규 |
| `bench/japan-travel/state/domain-skeleton.json` | core_categories 필드 추가 | ✅ |
| `tests/test_adapters.py` | retry + 카운터 테스트 추가 | ✅ |
| `tests/test_invariant_checker.py` | 불변원칙 8 tests | ✅ 신규 |

### 신규 생성 예정 (Stage C')
| 파일 | 내용 |
|------|------|
| `scripts/analyze_trajectory.py` | 실행 결과 분석 |

### 기존 참조
| 파일 | 용도 |
|------|------|
| `docs/design-v2.md` | 전체 설계 (Schema, Metrics, 불변원칙) |
| `bench/japan-travel/state/*.json` | 벤치 State 데이터 (원본 Cycle 2) |
| `bench/japan-travel-auto/state/*.json` | 자동 실행 결과 (Cycle 4) |
| `bench/japan-travel-auto/trajectory/` | 3 Cycle trajectory (JSON + CSV) |
| `schemas/*.json` | JSON Schema 4종 |

## 2. 기술 결정사항

| # | 결정 | 근거 |
|---|------|------|
| D-29 | OpenAI gpt-4.1-mini | 범용 API, 비용 효율 |
| D-30 | Tavily Search | 무료 1000 req/month, LangChain 통합 |
| D-31 | ~~25 tasks~~ → 16 tasks | 기존 Mock 위주 → Real API First 재설계 |
| D-32 | 외부 Orchestrator | 사이클 간 save/snapshot/check 필요 |
| D-33 | Stage별 세션 분리 | 컨텍스트 효율 |
| D-34 | Real API First 전략 | Mock 위주(Task 19에서야 Real) → 즉시 Real 검증 |
| D-35 | 25→16 tasks 축소 | Over-engineering 삭제 (녹화/재생, 시각화, Memory Guard 등) |
| D-36 | config fallback gpt-4.1-mini 확정 | from_env() fallback이 gpt-4o-mini → 수정 |
| D-37 | jump target_count 상한 10 | 과다 API 호출 방지 |
| D-38 | LLMCallCounter 래퍼 패턴 | ChatOpenAI 감싸고 call_count + token 추적 |

## 3. 한계점 (해결 완료)

| # | 한계점 | 해결 Task | 상태 |
|---|--------|-----------|------|
| 1 | Real SearchTool adapter 미테스트 | 2.1 | ✅ |
| 2 | Real LLM 통합 미테스트 | 2.1 | ✅ |
| 3 | LLM 응답 파싱 취약 | 2.2 | ✅ |
| 4 | collect 프롬프트 간결 | 2.3 | ✅ |
| 5 | critique C3 net_gap_changes 미전달 | 2.8 | ✅ |
| 6 | seed CORE_CATEGORIES 하드코딩 | 2.7 | ✅ |
| 7 | plan_modify Gap Map 실제 변경 안 함 | 2.8 | ✅ |
| 8 | Multi-cycle orchestrator 미검증 | 2.11 | ✅ |

## 4. 3 Cycle 실행 결과 (Stage B' Gate)

| Cycle | KU (active/disputed) | GU (open/resolved) | LLM calls | Search | Fetch |
|-------|---------------------|-------------------|-----------|--------|-------|
| 2 | 27/4 | 29/21 | 4 | 9 | 6 |
| 3 | 27/10 | 35/27 | 7 | 18 | 12 |
| 4 | 28/14 | 30/32 | 6 | 15 | 10 |
| **합계** | | | **17** | **42** | **28** |

- 총 LLM tokens: 84,736
- 불변원칙 위반: **0회**
- Jump Mode: 3/3 cycles

## 5. 의존성

### Python 패키지 (설치 완료)
| 패키지 | 용도 |
|--------|------|
| `langchain-openai` | ChatOpenAI (gpt-4.1-mini) |
| `tavily-python` | Tavily Search API |
| `python-dotenv` | .env 파일 로드 |

### 환경변수 (.env)
| 변수 | 용도 |
|------|------|
| `OPENAI_API_KEY` | OpenAI API 인증 (book-process 키) |
| `TAVILY_API_KEY` | Tavily Search 인증 |

## 6. 컨벤션 체크리스트

### 5대 불변원칙 (Task 2.9 자동검증 구현 완료)
- [x] Gap-driven: Plan.target_gaps ⊆ G (I1)
- [x] Claim→KU 착지성: claims 수 경고 (I2)
- [x] Evidence-first: active KU에 EU >= 1 (I3)
- [x] Conflict-preserving: disputed KU 존재 경고 (I4)
- [x] Prescription-compiled: RX ID 추적성 (I5)
