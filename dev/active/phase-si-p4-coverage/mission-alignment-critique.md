# P4 Mission-Alignment Critique

> Generated: 2026-04-15
> Source: 사용자 지적 후 self-review (semi-front 진입 직전 백엔드 로직 재점검)
> Status: **미션 재정렬 필요** — P4 Gate 판정 재권고 포함

## 0. 배경

P4 구현 완료 + 15c Gate Trial 후 session-compact 리뷰 중, 사용자가 미션을 재강조:

> - 도메인 지식 **우주 전체**(예: 웹에 존재하는 일본여행 관련 모든 지식)를 염두에 둘 것
> - 현재 수집한 KU를 그 우주와 비교할 것
> - 매 step의 **new KU** + **wide distribution** 강조 → 진정한 knowledge evolution
> - 이 관점에서 P4의 기준이 뭘 놓쳤는지, 어디서 distract됐는지 비판적으로 볼 것

이 문서는 그 self-critique를 보존한다.

## 1. Novelty 측정 자체가 미션과 어긋남

```python
# 현재 구현 (src/utils/novelty.py)
novelty = jaccard(prev_cycle_claims, curr_cycle_claims)
```

**자기참조 측정.**

- 현재 기준: "지난 cycle의 우리 수집물 vs 이번 cycle의 우리 수집물"
- 미션 기준: "일본여행 지식 우주 vs 지금까지 우리 수집물(누적)"

Cycle이 쌓일수록 우리 데이터가 서로 비슷해지는 건 당연 → novelty → 0. 이걸 "자연스러운 수렴"이라 변호했으나, **무엇에 대한 수렴인가?** 우주가 아니라 우리 tiny set에 대한 수렴. 우주의 0.1%만 긁고 "포화"라 말하는 꼴.

실측 0.127이 "정상"이라는 판정은 **미션 관점에서 오히려 경보**.

## 2. Coverage_map이 skeleton에 갇혀있음

```python
deficit = 1 - min(1, ku_count / target_per_category)
```

- `target_per_category`는 skeleton에 **우리가 미리 박아놓은 것**.
- skeleton은 seed 시점의 상상력 한계.
- 일본여행 우주에는 skeleton에 없는 축(계절 축제 세부, 동물카페, 은퇴자 장기체류, 장애인 접근성, 철도 마니아 루트, 재해 대비 정보 등)이 무한.

**coverage_map은 "내 지도 안의 빈칸"만 측정. 지도 밖은 안 보임.**

## 3. Gini 해석 오류

리뷰에서 "cat_gini 0.37→0.20 양호, 건강한 수렴"이라 썼던 것 — **틀림**.

- Gini 0.20 = 현재 카테고리들 사이의 균형 = "내 지도 안에서 고르게 칠함"
- 미션: 절대 커버리지 × 다양성. 좁은 5개를 균등하게 < 30개를 약간 불균등하게.

**낮은 Gini = 긍정** 해석은 mission-blind.

## 4. category_addition이 반응형(reactive)

계획 트리거:
- 조건: "기존 카테고리에 잘 안 맞는 KU ≥ 5개 패턴"

**이미 수집한 데이터에서 튀어나온 것만 본다.** 미션은 반대여야:

- 미션형: "LLM에게 '일본여행 우주에서 우리 skeleton에 **없는** 주요 카테고리는?' 물어서 **선제적** 확장"
- 현재 구조는 "이미 수집한 것 안에서만" 카테고리 성장 가능 → **우주 방향 성장 구조적 불가**

15c 내내 category_addition 0회 발동을 "보수성 과증명"이라 포장했으나, 실제로는 **구조상 터질 수 없음**.

## 5. plateau_detector action이 내향적

- trigger: novelty < 0.1 × 5c → OK
- action: audit → remodel (기존 지식 **재배열**)
- **미션 action**: 수집 전략 변경 — 다른 축, 다른 provider, 다른 시간대, 다른 언어, long-tail 쿼리. **hard pivot to unexplored territory**.

현재는 정체 시 **있는 것을 재정리**. 미션은 **없는 곳으로 나가기**.

## 6. 외부 우주 anchor 부재

| 미션 요구 | 현재 P4 | 격차 |
|---|---|---|
| 우주 크기 추정 | — | 없음 |
| 누적 외부 novelty (첫 발견 entity) | — | cycle-diff만 존재 |
| reach diversity (distinct domains 누적) | — | domain_entropy는 per-cycle |
| long-tail 포착률 | — | 없음 |
| 시간/언어/저자 다양성 | — | 없음 |
| unexplored axes 탐지 | coverage_map이 skeleton 밖 못 봄 | 구조적 불가 |
| 외부 대비 커버리지 비율 | — | 없음 |

## 7. 내가 distract된 지점 정리

1. **테스트 669개 PASS → 품질 신호로 착각.** 테스트는 코드 정확성이지 미션 달성 아님.
2. **"계획 9/9 달성"을 성공 서사로 구성.** 계획 자체가 미션과 어긋났으면 100% 달성해도 미션 실패.
3. **novelty threshold 완화를 Option A로 권고.** 가장 큰 실수. threshold는 미션을 강제하려던 유일한 수치 안전장치. "도메인 포화 특성상 비현실적"이라며 완화 추천은 **미션 포기 방향**.
4. **내부 지표의 "건강한" 움직임을 진보 신호로 해석.** Gini 수렴, conflict 0, confidence 상승 — 전부 **좁은 우물 안의 정돈**일 수 있다는 의심 결여.
5. **category_addition 미발동을 보수성 증거로 포장.** 실제로는 구조적으로 봉인된 기능.

## 8. Semi-front 진입 전 재설계해야 할 백엔드 로직 (우선순위 순)

1. **External Novelty Metric** — cycle-diff 아닌 `|new_entities_this_cycle ∩ never_seen_in_history|` / targets. 누적 발견율.
2. **Universe Probe** — 광역 탐색 쿼리(LLM survey, broad Tavily, Wikipedia category enumeration)로 "모르는 주요 카테고리/축" 목록 생성 → skeleton 선제 확장 신호.
3. **Reach Diversity Ledger** — 누적 distinct domain, author/publisher, 언어, 시간대. 매 cycle 증가율 추적.
4. **Long-Tail Capture Rate** — top-K 인기 쿼리 외 쿼리로 얻은 KU 비율. 낮으면 hard-pivot.
5. **Proactive Category Addition** — 반응형 ≥5 KU 패턴 아닌, LLM universe survey 기반 선제 제안.
6. **Plateau Action Re-route** — plateau → remodel이 아니라 `exploration_pivot` 노드(새 축/provider/쿼리 전략).
7. **Coverage Ratio vs Estimated Universe** — 정확하지 않아도 좋음. "추정 우주 대비 몇 %" 지표가 수렴 판단 전제.
8. **Novelty threshold는 완화가 아니라 정의 교체** — 새 정의(external novelty) 하에 0.25 유지 또는 상향.

## 9. P4 Gate 판정 재권고

이전 Option A (완화 PASS) **철회**.

- **철회 사유**: 미션 포기 방향.
- **수정안**:
  - (a) P4는 내부 지표 체계 구축까지 완료로 간주, external novelty/universe anchor는 P5 이전에 **Stage E (External Anchor)** 추가 후 재-Gate
  - (b) 또는 P4를 열어둔 채 위 §8의 1~3번만 P4 확장으로 흡수, 4~8은 P5 재설계로 이관
- **원칙**: semi-front 진입 전 반드시 미션-정렬 수치 체계 확보. 지금 상태로 UI가 "수렴"을 표시하면 **사용자 기만**.

## 10. 결정 필요 사항

- [ ] P4를 "현 상태 문서화 PASS"로 닫고 **새 Phase (External Anchor)** 신설 vs P4 재개
- [ ] Universe probe 의 비용 budget (broad queries × cycle 수)
- [ ] Reference corpus 선정 (Wikipedia ja/en, sitemap, Tavily broad)
- [ ] External novelty 정의 구체화 (entity_key 기준 vs claim-hash 기준 vs token 기준)
- [ ] 기존 novelty.py / coverage_map.py 를 internal 지표로 유지하되 external 신규 추가 vs 교체

## 참조

- session-compact: `docs/session-compact.md`
- P4 plan: `dev/active/phase-si-p4-coverage/si-p4-coverage-plan.md`
- P4 tasks: `dev/active/phase-si-p4-coverage/si-p4-coverage-tasks.md`
- readiness-report: `bench/japan-travel-readiness/readiness-report.json`
- silver masterplan: `docs/silver-masterplan-v2.md`
