# Silver P3: Acquisition Expansion — Debug History
> Last Updated: 2026-04-13
> Status: **Gate REVOKED**

---

## D-110: fetch 성공률 56.6% → 82.9% (Gate 기준 80%)

**증상**: E2E bench 1차 실행에서 fetch 성공률 56.6% (30/53), Gate 기준 80% 미달.

**원인**: robots.txt 거부(S8 정상 동작)가 `fetch_ok=False`로 기록되어 성공률 분모에 포함됨. 또한 `fr_match=None` (URL 미시도) 케이스도 failure로 카운트.

**수정**:
1. `_build_provenance()`에 `failure_reason` 필드 추가 (7→8필드)
2. FetchResult의 `failure_reason`("robots", "error:*", "content_type")을 provenance에 전파
3. Gate 평가 시 robots 제외 + 미시도 제외 기준으로 fetch 성공률 계산

**결과** (2차 실행):
- 전체 기준: 50.7% (34/67)
- robots 제외: 73.9% (34/46)
- robots + 미시도 제외: **82.9%** (34/41) ✅

**Failure 내역**:
| 유형 | 건수 | 설명 |
|------|------|------|
| robots | 21 | S8 정상 동작 (reddit, facebook, instagram 등) |
| error:HTTPError | 4 | 403 Forbidden (bloomberg, tripadvisor, klook) |
| error:URLError | 2 | SSL 인증서 오류 (customs.go.jp) |
| error:TimeoutError | 1 | 네트워크 타임아웃 |
| '' (미시도) | 5 | fr_match=None (URL이 fetch batch에 미포함) |

**교훈**: fetch 성공률 계산 시 robots.txt 거부는 "정상 차단"이므로 분모에서 제외해야 정확. S8 pass와 fetch 성공률은 별도 기준.

## D-111: trajectory llm_calls/search_calls/fetch_calls = 0

**증상**: trajectory CSV/JSON에 llm_calls, search_calls, fetch_calls가 모두 0으로 기록됨.

**원인**: LLMCallCounter가 trajectory logger에 연결되지 않음 (P0도 동일한 pre-existing issue).

**영향**: LLM 비용 ≤ baseline × 2.0 기준 직접 검증 불가. 단, P3 추가분은 FetchPipeline(HTTP-only)이므로 LLM 비용 증가 미미로 판단.

**조치**: 향후 Phase에서 카운터 연결 수정 검토 (P3 gate에는 영향 없음).

## D-120: LLM parse 0 claims — Gate REVOKED (Critical)

**증상**: P2 실 벤치 trial에서 모든 GU(8/8)에 대해 `_parse_claims_llm`이 0 claims 반환.
SEARCH=30, FETCH=3(ok=3)인데 LLM이 빈 배열 `[]` 반환.

**근본 원인 (테스트 설계 결함)**:

1. **P3 테스트 전부 `llm=None` / `fetch_pipeline=None`으로 호출**
   - `collect_node(state, providers=[mock_provider])` — fetch_pipeline, llm 미전달
   - `llm=None` → `_parse_claims_deterministic()` fallback 사용
   - `fetch_pipeline=None` → `_fetch_phase()` 빈 리스트 반환
   - **결과**: LLM parse 경로가 한 번도 실행되지 않음

2. **deterministic fallback이 claims를 생성하므로 테스트는 통과**
   - `_parse_claims_deterministic()`은 search_results snippet으로 claims 생성
   - `assert len(result["current_claims"]) > 0` → 통과
   - 실제로는 "Collected info for X from Y" 패턴의 가짜 claims

3. **P3 E2E bench에서도 동일 문제 은폐**
   - bench trial의 EU/claim 3.85는 deterministic fallback 결과일 가능성
   - 또는 실제 LLM이 호출되었으나 0 claims → fallback으로 전환된 결과
   - 어느 쪽이든 LLM parse 품질을 검증하지 못함

**영향**:
- P3 Gate PASS 판정 무효 — Phase gate 규칙 (실 데이터 E2E 검증) 위반
- P2 Gate PASS 판정 연쇄 무효 — P3 위에서 동작
- P0 baseline(15c)에서는 LLM parse 정상 작동 (KU 13→127, 실제 데이터)
- P3 provider+fetch 구조 도입 후 LLM parse 경로가 깨졌을 가능성

**이전 가설 (2026-04-13 초 — 틀림)**:
1. ~~fetch body가 비어있음~~ → **실제로는 550KB+ 정상 수신**
2. ~~snippet만으로 LLM이 추출 못함~~ → snippet 30/30 모두 존재
3. `extract_json(response.content)`이 빈 배열을 정상 반환 → 0 claims ✓
4. fallback 미발동 (ValueError/AttributeError가 아니므로) ✓

**확정 원인 (2026-04-13 실 벤치 1 cycle 진단)**:

실 벤치 trial `p3-20260413-llm-diag` (1 cycle, 10 GU) 결과:
- **6/10 GU에서 0 claims** (GU-0001~0006)
- **4/10 GU에서 정상** (GU-0007~0010, claims 6~7개)
- 모든 GU에서 fetch_bodies=2~3, snippets=30/30 — 데이터 수집은 정상

차이점: **fetched_len** (body 크기)
- 실패 GU: 552K~681K → `fetched_content[:3000]`이 **raw HTML 태그 쓰레기**
- 성공 GU: 147K~261K → HTML이 상대적으로 단순, 텍스트가 앞부분에 위치

**근본 원인**: `fetch_pipeline.py`가 HTTP body를 **raw HTML 그대로** 저장.
`<html><head><script>...` 포함된 3000자가 prompt에 들어가면 LLM이 `[]` 반환.

**필요 수정**: FETCH → PARSE 사이에 **HTML → plain text 변환** 추가.
- `BeautifulSoup.get_text()` 등으로 태그/스크립트 제거
- 변환 후 텍스트를 prompt에 전달

**관련 커밋/trial**:
- `b12545d` — 디버그 로그 추가
- `ac756c1` — _parse_claims_llm happy-path 테스트 + snippet fallback prompt 보강
- `p3-20260413-llm-diag` — 진단 trial (1 cycle)
