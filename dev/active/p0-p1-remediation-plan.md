# P0/P1 Remediation Plan

> Phase 6 착수 전 필수 해결 항목. 2026-04-10 분석 기준.

---

## P0: Critical (Phase 6 진입 차단)

### P0-1. collect_node 예외처리 강화
- **위치**: `src/nodes/collect.py` L79-97
- **현재**: bare `except Exception` → 에러 무시, 로그 없음. fetch 실패도 `except: pass`
- **위험**: 데이터 유실 + 감사 추적 불가
- **수정 방향**:
  - retry 실패 시 `logger.warning`으로 query/에러 기록
  - fetch 실패도 URL/에러 로깅
  - 최종 실패 시 gu_id별 실패 카운터 반환 → metrics에 `collect_failure_rate` 추가
- **작업량**: ~30줄 수정

### P0-2. API 타임아웃 추가
- **위치**: `src/config.py` + `src/adapters/llm_adapter.py` + `src/adapters/search_adapter.py`
- **현재**: LLM `max_retries=3` 고정(L74), Search 타임아웃 없음, ThreadPoolExecutor 무제한 대기
- **위험**: API 장애 시 그래프 hang
- **수정 방향**:
  1. `config.py`에 추가:
     - `LLMConfig.request_timeout: int = 60` (초)
     - `SearchConfig.request_timeout: int = 30` (초)
  2. `llm_adapter.py` L69: `ChatOpenAI(timeout=config.request_timeout)`
  3. `search_adapter.py`: `_retry_with_backoff`에 timeout 파라미터 전달
  4. `collect.py` L169: `ThreadPoolExecutor`에 timeout 설정
- **작업량**: config 4줄 + adapter 각 3줄

### P0-3. search_adapter 재시도 버그 수정
- **위치**: `src/adapters/search_adapter.py` L39
- **현재**: `"5" in exc_str[:1]` → 문자열 첫 글자만 체크하므로 504 등 5xx 에러 대부분 누락
- **수정 방향**: 
  ```python
  is_retryable = (
      "429" in exc_str
      or "rate" in exc_str
      or any(c in exc_str for c in ("500", "502", "503", "504"))
  )
  ```
- **작업량**: 3줄

### P0-4. remodeling_node 구현
- **위치**: 신규 `src/nodes/remodel.py` + `src/graph.py` 수정
- **현재**: design-v2 §10에 설계만 존재, 코드 전무. `remodel.py` 파일 없음
- **수정 방향**:
  1. `remodel.py`: entity 구조 분석 → 중복 감지 → 병합/분리 제안
  2. `graph.py` L103: `cycle % 10 == 0` 분기에 remodel 경로 추가
  3. 테스트: entity 병합, entity 분리 시나리오
- **작업량**: 새 파일 ~150줄 + graph 수정 ~20줄 + 테스트 ~100줄

---

## P1: High (Gate 통과 필수)

### P1-1. integrate_node 충돌 evidence 보존
- **위치**: `src/nodes/integrate.py` L270-288
- **현재**: `ValueError` catch → `pass` (ID 파싱 실패 시 무시)
- **위험**: 불변원칙 4번(Conflict-preserving) 위반
- **수정 방향**:
  - `except ValueError as e: logger.warning("KU/GU ID parse: %s", e)`
- **작업량**: 4줄

### P1-2. Entity alias/is_a 적용
- **위치**: `src/nodes/integrate.py` + 신규 `src/utils/entity_resolver.py`
- **현재**: design-v2 §6에 alias/is_a 설계, 코드는 exact match만 (`integrate.py` L28-37)
- **수정 방향**:
  1. `src/utils/entity_resolver.py` 신규:
     - `resolve_alias(entity_key, skeleton)` → canonical_key
     - `resolve_is_a(entity_key, skeleton)` → parent chain
  2. `integrate.py` `_find_existing_ku()`에 alias 해상도 추가
  3. skeleton에 `aliases` 필드가 있으면 자동 변환
- **작업량**: 새 파일 ~80줄 + integrate 수정 ~15줄 + 테스트 ~60줄

### P1-3. collect_node 테스트 보강
- **위치**: `tests/test_nodes/test_collect.py`
- **현재**: ~40% 커버리지
- **누락 시나리오**:
  1. mock search timeout → graceful 처리 확인
  2. malformed LLM JSON → deterministic fallback 확인
  3. 빈 검색 결과 → 빈 claims 반환 확인
  4. 병렬 GU 수집 시 claim 중복 제거 확인
- **작업량**: 테스트 ~120줄

### P1-4. State I/O 검증 로직
- **위치**: `src/utils/state_io.py` L54-56
- **현재**: JSON 읽기 실패 시 빈 리스트/딕트로 대체 (무검증)
- **수정 방향**:
  - JSON decode 실패 시 `logger.error` + 백업 파일에서 복구 시도
  - 필수 필드(`ku_id`, `entity_key` 등) 누락 시 경고
- **작업량**: ~25줄

---

## 실행 순서 (권장)

| 순서 | 항목 | 근거 |
|------|------|------|
| 1 | P0-3 | 버그 수정, 최소 변경 |
| 2 | P0-1 | 데이터 안전성 확보 |
| 3 | P0-2 | 런타임 안정성 확보 |
| 4 | P1-1 | 불변원칙 위반 해소 |
| 5 | P1-3 | 테스트 커버리지 확보 |
| 6 | P1-4 | State 견고성 확보 |
| 7 | P1-2 | Entity 해상도 기능 추가 |
| 8 | P0-4 | 신규 노드 구현 (가장 큰 작업) |

---

## 총 규모

- **P0**: 4건 (~210줄 신규/수정 + ~100줄 테스트)
- **P1**: 4건 (~125줄 신규/수정 + ~180줄 테스트)
- **합계**: 8건, 약 615줄
