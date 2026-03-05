# Phase 2: Bench Integration & Real Self-Evolution — Plan
> Last Updated: 2026-03-05 (Stage A'+B' 완료)
> Status: In Progress — Stage C' 진행 예정

## 1. Summary (개요)

Real LLM (OpenAI gpt-4.1-mini) + Real Search (Tavily)를 연동하여
japan-travel 벤치에서 10+ 사이클 자동 실행, 지식 자기확장 품질 검증.

**재설계 원칙**: "먼저 1사이클을 Real API로 돌려보고, 거기서 발견된 문제를 해결하는 순서"
기존 25-task 4-Stage Mock 위주 설계 → **16-task 3-Stage Real API First 설계**로 변경.

## 2. Current State (현재 상태)

- **Stage A' 완료**: Real API 1 Cycle 성공 (KU +6), 254 tests
- **Stage B' 완료**: 3 Cycle 연속 성공, 불변원칙 위반 0회
  - KU 28→42 (active 28, disputed 14)
  - GU resolved 21→32
  - LLM 17 calls (84K tokens), Search 42, Fetch 28
- **Stage C' 진행 예정**: 10+ Cycle 자동화

## 3. Target State (목표 상태)

- Real API로 10+ 사이클 자동 실행 성공
- 사이클마다 KU 증가, GU 해소, 5대 불변원칙 위반 0건
- 비용/토큰 추적 + Plateau 감지 자동 종료
- 원커맨드 벤치 실행 CLI

## 4. Implementation Stages

### Stage A': Smoke Test → Real 1 Cycle (5 tasks, 2.1~2.5) ✅
- API 키 검증, LLM 파싱 강화, 프롬프트 정교화, Orchestrator 정합성, **Real 1 Cycle 실행**
- **Gate**: japan-travel Real API 1사이클 완주 + KU 1개 이상 추가 → **PASSED**

### Stage B': 안정화 + 3 Cycle (6 tasks, 2.6~2.11) ✅
- 에러 핸들링, seed 일반화, plan_modify 실효성, 불변원칙 자동검증, 비용 로깅, **Real 3 Cycle 실행**
- **Gate**: 3사이클 연속 에러 없이 완주 + 불변원칙 위반 0건 → **PASSED**

### Stage C': 10+ Cycle 자동화 (5 tasks, 2.12~2.16)
- Plateau Detection, Metrics Guard, **Real 10 Cycle 실행**, CLI 정비, 결과 분석
- **Gate**: 10사이클 완주 (또는 plateau 조기 종료) + 결과 분석 리포트

## 5. Task Breakdown

| Stage | Total | S | M | L | Done |
|-------|-------|---|---|---|----|
| A': Smoke + 1 Cycle | 5 | 1 | 3 | 1 | 5/5 ✅ |
| B': 안정화 + 3 Cycle | 6 | 2 | 3 | 1 | 6/6 ✅ |
| C': 10+ Cycle | 5 | 2 | 2 | 1 | 0/5 |
| **합계** | **16** | **5** | **8** | **3** | **11/16** |

## 6. Risks & Mitigation

| 리스크 | 완화 |
|--------|------|
| API 비용 | gpt-4.1-mini ~$0.06/10cycles, Tavily 무료 1000/month |
| LLM 응답 파싱 실패 | extract_json() + fallback to deterministic |
| Rate Limit (429) | 지수 백오프 retry (1s→2s→4s) ✅ 구현 |
| 10사이클 중 State 비대 | Plateau Detection으로 조기 종료 (2.12) |

## 7. Dependencies

### Python 패키지 (설치 완료)
| 패키지 | 용도 |
|--------|------|
| `langchain-openai` | ChatOpenAI (gpt-4.1-mini) |
| `tavily-python` | Tavily Search API |
| `python-dotenv` | .env 파일 로드 |

## 8. 비용 추정

| API | 3사이클 실측 | 10사이클 예상 | 비용 |
|-----|-------------|-------------|------|
| Tavily Search | 42 calls | ~140 calls | 무료 |
| Tavily Fetch | 28 calls | ~93 calls | 무료 |
| OpenAI gpt-4.1-mini | 17 calls, 85K tokens | ~57 calls, ~280K tokens | ~$0.08 |
| **총 실행 시간** | **~2.5분** | **~8분** | |
