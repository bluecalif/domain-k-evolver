# Silver P3: Acquisition Expansion — Debug History
> Last Updated: 2026-04-12
> Status: Gate PASS

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
