# E7-3 Stage E On/Off 비교 리포트

> Generated: 2026-04-17
> Bench: `bench/japan-travel-external-anchor/` — 15c, japan-travel domain
> Commits: stage-e-off `b2aafc5` / stage-e-on `10bc58a` (VP4 fix D-147~D-150 적용)

---

## 1. 종합 게이트 판정

| Viewpoint | stage-e-off | stage-e-on |
|-----------|:-----------:|:----------:|
| VP1 expansion_variability | ✅ PASS 5/5 | ✅ PASS 5/5 |
| VP2 completeness | ❌ FAIL 4/6 | ❌ FAIL 4/6 |
| VP3 self_governance | ✅ PASS 5/6 | ✅ PASS 5/6 |
| VP4 exploration_reach | N/A | ✅ **PASS 4/5** |
| **Overall** | **FAIL** | **FAIL** |

Stage E on/off 모두 VP2 completeness (gap_resolution < 0.85) 로 gate FAIL.
VP4는 Stage E on 에서 **PASS** 달성.

---

## 2. 핵심 지표 비교

### 2.1 KU / GU 성장

| Cycle | off KU | on KU | off gap_res | on gap_res |
|------:|-------:|------:|------------:|-----------:|
| 1 | 27 | 35 | 0.343 | 0.343 |
| 5 | 71 | 73 | 0.637 | 0.607 |
| 10 | 97 | 104 | 0.750 | 0.792 |
| 15 | **116** | **106** | **0.789** | **0.813** |

- Stage E on: KU 최종 10개 적음 (probe overhead + 정체 후 재탐색 구조)
- gap_resolution: on이 소폭 높음 (0.789 → 0.813) — Stage E 탐색 전략이 GU 해소에 일부 기여

### 2.2 완성도 지표 (cycle 15)

| 지표 | stage-e-off | stage-e-on | 변화 |
|------|------------:|-----------:|:----:|
| gap_resolution | 0.789 | **0.813** | +0.024 |
| avg_confidence | **0.879** | 0.858 | -0.021 |
| multi_evidence_rate | **0.765** | 0.676 | -0.089 |
| conflict_rate | 0.009 | 0.009 | — |
| staleness_risk | 0 | 0 | — |

- avg_confidence 소폭 하락: Stage E가 probe 기반 신규 KU 도입 → 초기 confidence 낮음
- multi_evidence 하락: 신규 카테고리(safety-security 등) KU는 단일 증거로 시작

---

## 3. VP4 상세 (stage-e-on)

| 기준 | 값 | 임계치 | 판정 |
|------|---:|-------:|:----:|
| R1 external_novelty avg | 0.7857 | ≥ 0.25 | ✅ |
| R2 distinct_domains/100ku | 49.06 | ≥ 15 | ✅ |
| R3 validated_proposals | 6 | ≥ 2 | ✅ |
| R4 exploration_pivot | 0 | ≥ 1 | ❌ |
| R5 universe_probe_runs | 1 | ≥ 1 | ✅ |

**R4 미발동 원인**: ext_novelty 패턴이 `1.0×10 → 0.0×3 → 1.0×2`로 5cycle 연속 < 0.1 조건 미달.
cycle 14에서 KU 1개 추가(→ ext_novelty 1.0 복귀)로 연속 window 리셋됨. 비설계적 동작 아님.

---

## 4. Stage E 실행 이력 (stage-e-on)

### Universe Probe (3회 실행)

| 사이클 | 트리거 | accepted | registered | LLM 누적 |
|-------:|--------|:--------:|:----------:|---------:|
| 9 | periodic (10%5==0) | 0 | 0 | 7/12 |
| 13 | novelty_stagnation (last_3<0.15) | 0 | 0 | 8/12 |
| 15 | periodic (15%5==0) | 1 | 1 | 10/12 |

- Cycle 9/13: 제안 5건 모두 `collision_active` (기존 skeleton 카테고리와 중복)
- Cycle 15: `safety-security` 카테고리 accepted → Tavily 5 snippets → LLM validation PASS → 등록

### Exploration Pivot

- **미발동** (D-149 fix 적용됨, reach_degraded 조건 제거)
- ext_novelty 연속 5cycle < 0.1 조건이 cycle 11-13(3cycle)만 충족 → 트리거 불가

### Cost Guard

| 예산 | 사용 | 잔여 |
|------|-----:|-----:|
| LLM 12 | 10 | 2 |
| Tavily 9 | 6 | 3 |

D-147 fix(3→12)로 kill-switch 미발동. 예산 여유 확인.

### 등록된 Candidate Categories (누적 6개)

| slug | name | 출처 |
|------|------|------|
| accessibility | Accessibility | 이전 run |
| budget-travel | Budget Travel | 이전 run |
| long-term-stay | Long-Term Stay | 이전 run |
| cultural-experience | Cultural Experience | 이전 run |
| health-safety | Health & Safety | 이전 run |
| safety-security | Safety & Security | 이번 run (cycle 15) |

---

## 5. VP4 FAIL 근본 원인 해소 현황 (D-147~D-150)

| # | 결정 | Fix | 이번 벤치 검증 |
|---|------|-----|---------------|
| D-147 | llm_budget kill-switch | 3→12 | ✅ LLM 10/12 사용, kill-switch 미발동 |
| D-148 | ext_novelty 0 수렴 | delta_kus 분모 | ✅ avg 0.085→**0.7857** |
| D-149 | pivot 조건 unreachable | reach_degraded 제거 | ✅ 조건 제거 확인 (pivot은 novelty pattern으로 미발동) |
| D-150 | category_addition HITL 불가 | probe_history 기준 | ✅ R5 PASS (probe 1회 실행) |

---

## 6. 잔존 이슈

### VP2 gap_resolution (Stage E 무관)

두 모드 모두 VP2 FAIL (off: 0.789, on: 0.813). Stage E는 외부 탐색 레이어이며 core loop의 GU 해소 성능에 직접 영향 없음. 별도 Phase(P4~P6 범위)에서 해결 필요.

### Universe Probe collision_active 반복

Cycle 9/13에서 LLM이 기존 skeleton 카테고리(transport, accommodation 등)와 동일한 slug 제안 반복. 프롬프트에 기존 카테고리 목록이 전달되나 LLM이 변형명(예: "transportation" vs "transport")으로 우회 제안. **D-151 후보**: 프롬프트에 slug 정규화 + 유사도 필터 추가.

### Exploration Pivot 미발동

15c 내에서 novelty 연속 저하 5cycle 조건 미달. 더 긴 run이나 KU 수렴 후 plateau 구간에서 발동 가능. 설계상 정상 동작.
