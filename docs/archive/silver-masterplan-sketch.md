# domain-k-evolver Gen-Silver Masterplan Sketch

---

## 1. 비전 및 개요

### 1.1 핵심 목표

- **지식 무결성**: Source 탐색 신뢰도 확보. Domain 최적화 카테고리별 충분한 지식 Quantity 확보
- **Self Improvement**: Cycle별 지식 Expansion 및 Super-Cycle별 지식 수집 Logic Audit & Remodel
- **Observability**: Web Dashboard를 통한 Bottleneck 가시화 및 사용자 피드백 기반 마련

### 1.2 프로젝트 철학

- 도메인 지식은  
- LLM은 도구이며, **구조 + 인간 선택(Human-in-the-Loop)**이 품질을 결정한다

---

## 2. Product Generations 개요

| Generation | 코드명 | 핵심 방향 | 상태 |
|------------|--------|-----------|------|
| **1st** | Bronze (BZ) | 기초 지식 수집 및 구조화 Logic 구현 | ✅ 완료 |
| **2nd** | Silver (SI) | 지식 수집 및 모니터링 고도화 | 🔜 현재 |
| **3rd** | Gold (GD) | 수직적 깊이 + Quality + Business | 📋 비전 |


## 3. Silver Core Mission (Before /After)

### 3.1 지식 소스 확장

- 현재: Tavily 검색에 의존
- 개선: Tavily 검색의 웹페이지를 추가 Crawling하여 정보의 풍부성 강화. Duck-Duck-Go 활용 검토

### 3.2 지식 무결성 Flow

- 현재: 현 Cycle의 지식 검색이 이전 Cycle의 지식 검색과 얼마나 Non-Overlap인지 판단이 없음
- 개선: 매 Cycle에서 Non-Overlap (source, 분야, 카테고리, entity등) 정도를 판단하여, 다음 cycle의 검색 방향을 지정할 것 

### 3.3 Self Improvement

- 현재: 매 cycle별로 검색 기준을 판단하여 진행됨으로, Local Optimum에 매몰될 수 있음
- 개선: Global Audit을 신설 (예를 들면 10 cycle 단위) 현재까지 수집된 지식 전체를 llm으로 통합적으로 정리 -> 이것을 Domain 전체의 이상적인 지식 모습과 비교하여 혁신적으로 지식을 확장 및 고도화할 방법을 검토 by llm -> 이것을 revolutionary path로 지정 -> 이를 위해서 할일을 정리 (카테고리 및 entity, source, 판정 기준 변경) -> 새로운 Cycle (Phase를 다르게 붙이는 것이 좋을듯. 기존에는 Phase0- cycle 1, 2..., audit 이후 Phase 1 cycle 1, 2, 3,...)

### 3.4 Visuallization & Monitoring

- 현재: 진행 과정 외부로 표현 안됨. 모니터링 불가
- 개선: 웹 대시보드 작성. cycle/phase별 진행상황 모니터링 (KU, GU, 검색 parameter, policy등). 사용자 Feedback에 의한 수정도 용이하도록 가이드가 제시되는 대시보드로 작성
