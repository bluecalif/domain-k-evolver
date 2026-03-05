# Phase 2: Bench Integration & Real Self-Evolution — Plan
> Last Updated: 2026-03-05
> Status: Not Started

## 1. 목표

- Real LLM (OpenAI GPT) + Real Search (Tavily) 연동
- japan-travel 벤치에서 10+ 사이클 자동 실행
- 자기확장 품질 향상(KU 증가, GU 해소, Metrics 개선) 정량 검증
- 5대 불변원칙 매 사이클 자동 검증

## 2. 선행 조건

- [x] Phase 1 완료 (191 tests, 14-node StateGraph)
- [x] bench/japan-travel State 데이터 (Cycle 2 결과: KU 28, GU 39, EU 55)
- [ ] OPENAI_API_KEY 환경변수 설정
- [ ] TAVILY_API_KEY 환경변수 설정

## 3. Stage 구성

### Stage A: 실행 인프라 (6 tasks, 2.1~2.6)
- LLM/Search Adapter, Config, Orchestrator, State 전이 수정, Metrics Logger
- **Gate**: Orchestrator가 단일 사이클을 Mock LLM으로 완주할 수 있어야 함

### Stage B: 코드 수정 + 노드 강화 (8 tasks, 2.7~2.14)
- seed 일반화, critique 실패모드/T2·T5/C3, integrate LLM비교, plan_modify 실제효과, collect/plan 프롬프트
- **Gate**: 기존 191 tests + 신규 테스트 전체 통과

### Stage C: 10+ 사이클 검증 (7 tasks, 2.15~2.21)
- Realistic Mock, 불변원칙 자동검증, Metrics guard, 10-Cycle 테스트(Mock/Real), Trajectory Analyzer, Bench Run Script
- **Gate**: Mock 10사이클 불변원칙 전체 PASS + Real API 10사이클 실행 성공

### Stage D: 체크포인트 + 안정성 (4 tasks, 2.22~2.25)
- Gate D 강화, Plateau Detection, Snapshot Diff, Memory Guard
- **Gate**: 수렴 감지 시 자동 종료 + 메모리 사용량 모니터링

## 4. 진행 방식

- Stage별 세션 분리: A→commit→B→commit→C→commit→D→commit (D-33)
- 각 Stage 완료 시 dev-docs 갱신 + git commit
- Real API 테스트는 Stage C에서 집중 (비용 관리)

## 5. 위험 요소

| 리스크 | 완화 |
|--------|------|
| API 비용 | Tavily 무료 1000 req/month, GPT 사용량 모니터링 |
| LLM 응답 파싱 실패 | 구조화 프롬프트 + fallback 파서 |
| 10사이클 중 State 비대 | Memory Guard (2.25) + Snapshot 크기 모니터링 |
| Mock/Real 결과 괴리 | Realistic Mock (2.15)으로 녹화/재생 |
