# Reach Axes 실측 조사 (Task #3 / E0-2)

> 2026-04-15 · Stage E External Anchor — `reach_ledger` 축 결정 근거

## 조사 목적

External Anchor 의 `reach_ledger` 에 기록할 축(axis) 후보를 선별.
현재 Tavily snippet-first 파이프라인에서 **실제로 추출 가능한 축**과
**각 축의 coverage/cardinality** 를 확인하여 채택 여부를 결정.

## 조사 대상 데이터

- `bench/japan-travel-readiness/` (SI-P2 Gate PASS 15c 결과)
  - `state-snapshots/cycle-{1..15}-snapshot/` — KU/GU/metrics only
  - `trajectory/trajectory.json` — 집계 metrics only (search_calls=0, URL 원문 없음)
- Raw search snippet / EU 개별 객체는 **현 파이프라인상 persisted 안 됨**
  (claim.evidence 는 KU 통합 후 `evidence_links=["EU-xxxx"]` 로만 남음)

결과: 과거 bench 디렉토리에서 publisher/author/language 분포를 **사후 측정할 수 없음**.
따라서 조사는 "코드상 현재 무엇이 capture 가능한가" + "Tavily API 가 무엇을 반환하는가"
관점으로 수행.

## 현행 capture 경로

1. `src/adapters/search_adapter.py:63-80` — `TavilySearchAdapter.search()`
   - Tavily `client.search(query)` 응답의 각 item 에서
     `{url, title, content(=snippet)}` 3개만 유지. 나머지 필드 drop.
2. `src/nodes/collect.py:64-72` — `_build_provenance(source_url)`
   - `{provider:"tavily", domain:urlparse(url).netloc, retrieved_at, trust_tier}` 생성.
   - **domain(=publisher_domain) 은 이미 100% 보존** (claim.provenance).
3. `src/nodes/collect.py:86-102` — 결정론 / LLM Parse 모두 `evidence.url` 을 claim 에 첨부.

## 축별 추출 가능성

| 축 | 추출 경로 | 성공률 예상 | 카디널리티 | 채택 |
|----|-----------|-------------|------------|------|
| **publisher_domain** | `urlparse(url).netloc` — 이미 provenance.domain | **100%** | 높음 (수십~수백) | ✅ Primary |
| **tld** | domain rsplit('.', 1)[-1] | **100%** | 낮음 (.jp/.com/.kr/.go.jp 등) | ✅ Secondary (language/region proxy) |
| **published_date** | Tavily item["published_date"] — 현재 drop 중. adapter 확장 필요 | 중간 (Tavily 플랜/쿼리별 sparse) | 연속값 → bucket 필요 | ⚠️ Tentative (E3 단계 실측 후 결정) |
| **language** | snippet 에 대한 heuristic 또는 `langdetect` lib | 높음 (90%+) | 매우 낮음 (ko/en/ja 3-4개) | ❌ Defer — 신규 dep + 축 자체 diversity 낮음 |
| **author** | Tavily 응답 미포함. HTML fetch 필요 | 낮음 (fetch 재도입은 D-121 위반) | - | ❌ 제외 |
| **url_section** | urlparse(url).path 의 first segment | 높음 | 중간 | ⚠️ Tentative (noise 가능, E3 실측 후) |

## 결정

**Stage E `reach_ledger` 초기 축(axes) 확정:**

1. `publisher_domain` — 단일 primary 축. distinct count / 100 KU 가 VP4 지표.
2. `tld` — 지역/언어 대용 secondary 축. 별도 distinct count 지표는 두지 않고,
   publisher_domain 이 같은 tld 로 과집중되는지 모니터링용으로만 사용.

**확장 여지 (E3 후속):**

- `published_date` 는 `TavilySearchAdapter` 에 item["published_date"] 보존 옵션 추가 후,
  실제 bench trial 에서 coverage 측정 → ≥ 60% 이상일 때 ledger 에 bucket 축으로 추가.
- `url_section` 은 domain diversity 가 정체될 때 보조 축으로 도입 검토.

**기각:**

- `language` — langdetect 신규 의존성 대비 diversity 낮음. ROI 부족.
- `author` — fetch 재도입 불가 (D-121 snippet-first 원칙).

## 구현 영향 (E1/E3 으로 이월)

- `src/utils/external_novelty.py` (E1-1): `(entity_key, field, publisher_domain)` 튜플 단위로 novelty 집계.
- `src/utils/reach_ledger.py` (E3): `{publisher_domain: count, tld: count}` 누적. `distinct_domains_per_100ku` 계산 API 제공.
- `TavilySearchAdapter` 확장은 E3 시점에 필요 시 별도 task 로 (현재는 미확장).

## 관련 결정

- D-138: external_novelty granularity = entity_key+field 튜플 (본 조사로 `publisher_domain` 보조축 추가 확정).
- VP4 기준 중 `distinct_domains_per_100ku ≥ 15` 는 **publisher_domain** 축을 전제.
