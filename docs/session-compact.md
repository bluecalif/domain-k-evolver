# Session Compact

> Generated: 2026-04-14
> Source: D-121 — Provider/Fetch/Parse 3단계 전면 폐기, Snippet-First Refactor(SI-P3R) 수립

## 2026-04-14 Pivot Summary

D-121: Silver P3 3단계 구조를 폐기하고 Tavily snippet → LLM 파싱의 2단계로 복원한다.

- **근거**: D-120 진단(2026-04-13) — snippet-only 경로로 단일 GU 4 claims 성공. 3단계 복잡도가 품질·비용·지연 모두 악화 요인
- **신규 Phase**: `dev/active/phase-si-p3r-snippet-refactor/` (plan/tasks/context/debug-history)
- **project-overall 반영**: Phase 실행 순서 재정의 — `SI-P3R → P2 재판정 → P4 → P5 → P6`
- **Bench alignment**: Bronze read-only 유지, silver `p3-*` historical trial 보존, 신규 `p3r-*` namespace
- **Gate 체인**: SI-P3R Gate PASS 시 → Silver P2 실 벤치 재판정 → REVOKED 해제

아래는 2026-04-13 세션 기록 (D-120 근본 원인 확정 + 부분 수정). SI-P3R T1에서 해당 수정본(html_to_text, URL 정렬)도 폐기 예정.

---

> Generated: 2026-04-13 22:35
> Source: D-120 근본 원인 확정 + HTML→text 변환 구현

## Goal

P3 Gate 무효화(D-120) → 근본 원인 특정 → 코드 수정 → P3/P2 Gate 재판정

## Completed

### 이전 세션
- [x] P3/P2 Gate REVOKED 공식 반영
- [x] Scripts Policy 수립 (run_readiness.py 단일 진입점)
- [x] run_one_cycle.py, run_bench.py deprecated 처리

### 이번 세션: 테스트 + 진단
- [x] `_parse_claims_llm` happy-path 테스트 10개 추가 — `ac756c1`
- [x] collect_node LLM 통합 테스트 (llm+providers+fetch_pipeline)
- [x] snippet fallback prompt 보강 ("use the snippets" 안내)
- [x] 이전 세션 디버그 로그 커밋 — `b12545d`

### 이번 세션: D-120 근본 원인 확정
- [x] **실 벤치 1 cycle 진단 실행** (p3-20260413-llm-diag) — 3가지 가설 검증
- [x] **가설 1 기각**: "fetch body 없음" → 실제로는 550KB+ 정상 수신
- [x] **가설 2 기각**: "코드 버그" → mock 테스트 전부 통과
- [x] **근본 원인 확정 (2단계)**:
  1. fetch body가 **raw HTML** 그대로 prompt에 전달 → `<script>/<style>` 노이즈
  2. **CuratedProvider가 홈페이지 URL 반환** (japan-guide.com 루트) → fetch body가 GU와 무관한 콘텐츠
  3. `search_results[:5]`가 전부 curated → Tavily의 좋은 snippet이 prompt에서 제외

### 이번 세션: D-120 수정 구현
- [x] `src/utils/html_strip.py` 생성 — BeautifulSoup 기반 HTML→text
- [x] `collect.py`에 `html_to_text()` 적용 (PARSE 직전)
- [x] `_fetch_phase` URL 정렬 — 구체적 URL(path 길이순) 우선 fetch
- [x] `_build_parse_prompt` snippet 정렬 — 실질 snippet 우선 (curated 메타 후순위)
- [x] `pyproject.toml` beautifulsoup4 의존성 추가
- [x] 단위 테스트 11개 (test_html_strip.py)
- [x] **단일 GU 검증 성공**: GU-0001 — 0 claims → **4 claims** (timeout=1초)
- [x] 694 tests passed, 3 skipped
- [x] 커밋: `9985c98`, `d66434b`

## Current State

- **Git**: branch `main`, latest commit `d66434b`
- **Tests**: 694 passed, 3 skipped
- **P3 Status**: **REVOKED** — 코드 수정 완료, full bench trial 미실행
- **P2 Status**: **REVOKED** — P3 연쇄 무효

### 파이프라인 데이터 흐름 (현재, 4단계)
```
Gap("JR Pass 가격 빈칸")
    │
    ▼ STEP 1: SEARCH — Tavily/DDG API 쿼리
    │ 반환: url + title + snippet (보통 10~30건)
    │ snippet = 검색엔진이 뽑아준 짧은 요약 (1~2문장)
    │ LLM 사용: ✗
    │
    ▼ STEP 2: FETCH — 상위 N개 URL에 HTTP GET
    │ 반환: raw HTML body (최대 500KB)
    │ robots.txt 체크 + rate-limit (1초/도메인)
    │ LLM 사용: ✗
    │
    ▼ STEP 3: TEXT — html_to_text() 변환
    │ BeautifulSoup: script/style/nav/header/footer 제거
    │ <main> 또는 <article> 태그 우선 추출
    │ 반환: clean plain text
    │ LLM 사용: ✗
    │
    ▼ STEP 4: PARSE — LLM에 prompt 전달
    │ 입력: snippet(상위5개) + plain text([:3000])
    │ 출력: 구조화된 Claim JSON array
    │ LLM 사용: ✓ (유일한 LLM 호출)
    │
    ▼ integrate_node → KU 생성
```

## Remaining / TODO — 단계별 이슈 매트릭스

> **1 cycle 성숙이 최우선**. 아래 모든 이슈를 단계별로 해결해야 함.

### STEP 1 (SEARCH) 이슈

| # | 이슈 | 상태 | 상세 |
|---|------|------|------|
| S1 | **CuratedProvider가 홈페이지 URL 반환** | **미해결** | `japan-guide.com`, `jnto.go.jp/en/` 등 도메인 루트. GU와 무관한 content를 fetch하는 원인. **제거하거나 구체적 서브페이지 URL로 교체 필요** |
| S2 | Curated snippet이 메타데이터만 포함 | **미해결** | `"Curated source: transport, accommodation"` — 사실적 정보 없음. prompt에 들어가면 LLM에 무의미 |
| S3 | Curated 결과가 search_results 상위 독점 | 부분 수정 | prompt snippet 정렬은 적용됨. 하지만 **curated 자체를 정리하는 것이 근본 해법** |

**해결 방향**: `bench/japan-travel/.../domain-skeleton.json`의 `preferred_sources`를 점검하여:
- 홈페이지 URL → 구체적 서브페이지로 교체 (예: `japan-guide.com` → `japan-guide.com/e/e2025.html`)
- 또는 fetch 대상에서 curated 홈페이지 제외

### STEP 2 (FETCH) 이슈

| # | 이슈 | 상태 | 상세 |
|---|------|------|------|
| F1 | **fetch timeout 15초 → 병렬 실행 극심한 지연** | **미해결** | 10 GU × 3 URL × rate-limit → collect 단계에서 수분 소요. `run_readiness.py --cycles 1`이 hang처럼 보임 |
| F2 | 일부 사이트 429/timeout | 관찰됨 | URL 정렬로 구체적 페이지 우선 fetch → 느린/차단 사이트에 집중됨 |
| F3 | URL 정렬(path 길이순) 적용됨 | 완료 | 홈페이지 후순위, 구체적 URL 우선 |

**해결 방향**: fetch timeout 단축 (15초→5초), 또는 `fetch_top_n` 축소 (3→2)

### STEP 3 (TEXT) 이슈

| # | 이슈 | 상태 | 상세 |
|---|------|------|------|
| T1 | html_to_text() 구현 완료 | **완료** | 11개 테스트 통과 |
| T2 | **홈페이지 URL의 텍스트는 변환해도 무의미** | **미해결** | japan-guide.com 홈 → "Top Travel Stories, Tokyo, Kyoto..." 나열. GU와 무관. **STEP 1(S1)에서 해결해야 함** |
| T3 | 일반 URL의 텍스트 품질 검증 필요 | **미검증** | 구체적 URL(예: `worldtrips.com/resources/japan/visa-requirements`) → `html_to_text()` → 실제 유용한 텍스트인지 **확인 필요** |

### STEP 4 (PARSE) 이슈

| # | 이슈 | 상태 | 상세 |
|---|------|------|------|
| P1 | **fetched text vs snippet — LLM 파싱 성공률 비교 미수행** | **미검증** | prompt에 snippet(상위5개)과 text([:3000]) 둘 다 들어감. LLM이 어느 쪽에서 claims를 뽑는지, 각각의 기여도를 알 수 없음 |
| P2 | prompt에 `search_results[:5]` → snippet 정렬 적용됨 | 완료 | 실질 snippet 우선 (curated 메타 후순위) |
| P3 | `fetched_content[:3000]` 절단 | 확인 필요 | text 변환 후 3000자면 충분한지, 늘려야 하는지 검증 필요 |

**검증 방법**: 단일 GU에서:
1. text만 있고 snippet 없을 때 → claims?
2. snippet만 있고 text 없을 때 → claims?
3. 둘 다 있을 때 → claims 수/품질 차이?

### 전체 파이프라인 (E2E) 이슈

| # | 이슈 | 상태 | 상세 |
|---|------|------|------|
| E1 | **1 cycle full 실행 미완료** | **미해결** | 10 GU 병렬에서 hang 발생. F1(timeout)과 S1(curated 홈페이지) 해결 후 재시도 필요 |
| E2 | P3 Gate 재판정 | **대기** | 5 cycle full trial 필요 |
| E3 | P2 Gate 재판정 | **대기** | P3 선행 |

## Key Decisions

- D-120 근본 원인 확정 (2026-04-13): raw HTML + curated 홈페이지 URL 조합이 원인
- HTML→text: **beautifulsoup4** 채택
- 변환 삽입 위치: **collect.py 사용 직전** (fetch_pipeline은 raw HTML 보존)
- fetch URL 정렬: **path 길이순** (구체적 URL 우선)
- prompt snippet 정렬: 실질 snippet 우선
- **완료 요약 규칙** (CLAUDE.md): what + so what(효과) 필수

## Context

다음 세션에서는 답변에 **한국어** 사용.

### 핵심 제약
- **Bash 절대경로 필수** (CLAUDE.md) — `cd` 금지
- **Bronze 보호**: `bench/japan-travel/` read-only
- **커밋 prefix**: `[si-p3]` (P3 수정 시), `[si-p2]` (P2 수정 시)
- **인코딩**: `PYTHONUTF8=1`, `encoding='utf-8'` 명시
- **Phase Gate 규칙**: 실 API로 E2E 검증 필수. 합성 E2E만으로 gate 불가
- **API 비용 주의**: 실행 전 기존 결과 확인 + 유저 확인 필수
- **완료 요약**: what + so what(효과) 필수, 나열만 금지

### 핵심 파일
- `src/utils/html_strip.py` — HTML→text 변환
- `src/nodes/collect.py` — 4단계 파이프라인 (SEARCH→FETCH→TEXT→PARSE)
- `src/adapters/fetch_pipeline.py` — HTTP fetch (raw HTML body, timeout=15초)
- `src/adapters/providers/curated_provider.py` — CuratedProvider (preferred_sources 기반)
- `bench/japan-travel/state-snapshots/cycle-0-snapshot/domain-skeleton.json` — preferred_sources 정의
- `tests/test_collect_p3.py` — P3 collect 테스트 25개
- `tests/test_html_strip.py` — html_to_text 테스트 11개
- `dev/active/phase-si-p3-acquisition/phase-si-p3-acquisition-context.md` — 파이프라인 문서

### 진단 trial 결과
| Trial | 수정 적용 | 결과 |
|-------|----------|------|
| p3-20260413-llm-diag | 없음 (raw HTML) | 6/10 GU 실패 |
| p3-20260413-llm-verify | html_to_text만 | 6/10 GU 실패 (curated URL 문제) |
| 단일 GU 인라인 | html_to_text + URL 정렬 + timeout=1초 | **GU-0001: 4 claims 성공** |

## Next Action

**1 cycle 성숙을 위한 단계별 점검 + 수정 후 1 cycle 실행.**

모든 단계를 하나씩 확인하고, 각 단계가 합리적인 출력을 내는지 검증한 뒤 1 cycle을 돌린다.

### Step-by-step 작업 순서

1. **S1 해결: curated 홈페이지 URL 정리**
   - `domain-skeleton.json`의 `preferred_sources` 확인
   - 홈페이지 URL → 제거 또는 구체적 서브페이지로 교체
   - CuratedProvider 동작 확인

2. **F1 해결: fetch timeout 단축**
   - `fetch_pipeline.py` DEFAULT_TIMEOUT 15초 → 5초 (또는 config 경유)
   - 병렬 실행 시간이 합리적인지 확인

3. **T3 검증: 일반 URL의 html_to_text 품질 확인**
   - 구체적 URL 2~3개를 fetch → html_to_text → 텍스트가 GU와 관련 있는지 직접 확인

4. **P1 검증: fetched text vs snippet 기여도 분석**
   - 단일 GU에서 3가지 조합 테스트:
     - text만 (snippet 제거) → claims?
     - snippet만 (text 제거) → claims?
     - 둘 다 → claims?
   - LLM이 어느 소스에서 claims를 뽑는지 파악

5. **E1: 1 cycle 전체 실행**
   - `run_readiness.py --cycles 1 --bench-root ... --audit-interval 0`
   - **10/10 GU에서 claims > 0** 확인
   - 실행 시간이 2분 이내인지 확인

6. **결과 분석 + 커밋**
