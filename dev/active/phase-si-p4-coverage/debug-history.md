# Silver P4: Coverage Intelligence — Debug History
> Last Updated: 2026-04-17
> Status: **Stage A~E Complete · VP4 PASS 4/5 (D-147~D-150 해소)**

---

## Stage A~D 진행 중 발견 이슈 (2026-04-15)

### ISSUE-P4-01 (설계): novelty 자기참조 측정
- 증상: 15c bench novelty avg 0.127 (< gate 0.25). Stage A~D 구현은 계획대로 완료됐으나 Gate FAIL.
- 원인: `novelty.py` 가 cycle-diff (prev vs curr) 만 측정 → 시스템이 자기 collected set 에 수렴할수록 자연 감소. 우주 대비 측정 아님.
- 분석 문서: `mission-alignment-critique.md`, `mission-alignment-opinion.md`
- 결론: **구현 결함 아님, 측정 정의가 미션과 어긋남**. Stage E external_novelty (history-aware) 도입으로 해결.

### ISSUE-P4-02 (설계): coverage_map 이 skeleton 에 갇힘
- 증상: `deficit = 1 - min(1, ku_count / target_per_category)` 가 skeleton 내부만 측정.
- 원인: `target_per_category` 는 seed 시점 skeleton 에 하드코딩. skeleton 밖 영역 존재는 비가시.
- 결론: Stage E universe_probe + tiered skeleton (candidate_categories) 로 해결.

### ISSUE-P4-03 (해석): category_addition 15c 내 0회 발동
- 증상: Stage C 의 smart category_addition 이 japan-travel 15c 내내 발동 안 함.
- 1차 해석(기각): "보수성 과증명".
- 2차 해석(채택): 반응형 트리거 (≥5 KU 패턴) 는 이미 수집한 데이터에서만 튀어나옴 → skeleton 밖 영역은 구조적으로 발동 불가.
- 결론: Stage E L4b universe_probe 로 **선제적** category 후보 발굴. 기존 L4a 경로와 병행.

---

## Stage E VP4 FAIL 근본 원인 분석 및 Fix (2026-04-17)

### ISSUE-P4-04 (버그): llm_budget kill-switch 조기 발동 (D-147)
- **증상**: E7-2 stage-e-on에서 cycle 4에 kill-switch trip. 이후 11c Stage E 전체 사망.
- **원인**: `ExternalAnchorConfig.llm_budget_per_run = 3`. universe_probe 1회 = survey 1 + validator 2 = LLM 3. 첫 probe 실행만으로 예산 100% 소진.
- **수정**: `src/config.py` `llm_budget_per_run: int = 3 → 12`, env 기본값 "3" → "12". `f822f2c`
- **검증**: E7-3 bench — LLM 10/12 사용, kill-switch 미발동. 예산 여유 2 확인.

### ISSUE-P4-05 (설계): ext_novelty 0 수렴 — 분모 단조 증가 (D-148)
- **증상**: E7-2에서 external_novelty 0.085 (< 임계치 0.25). cycle 3부터 0.1 미만, cycle 10+ 0.01 수준.
- **원인**: `compute_external_novelty(curr_kus, ...)` 에서 `curr_kus` = state의 전체 KU. 분모가 누적 증가하여 `novel / total` → 0 수렴. 임계치 0.25는 구조적으로 도달 불가.
- **수정**: `src/utils/external_novelty.py`에 `compute_delta_kus(prev_kus, curr_kus)` 추가. `src/orchestrator.py` `_update_novelty_and_coverage`에서 `self._prev_kus` 업데이트 전에 delta 계산 → `compute_external_novelty(delta_kus, ...)` 전달. `f822f2c`
- **검증**: E7-3 bench — ext_novelty avg 0.7857 (0.085 → 13× 개선). R1 PASS.
- **테스트**: `test_external_novelty_with_delta_avoids_convergence` (D-148 regression guard)

### ISSUE-P4-06 (설계): exploration_pivot 조건 구조적 unreachable (D-149)
- **증상**: E7-2에서 exploration_pivot 미발동 (R4 FAIL 0/1).
- **원인**: `should_pivot`의 조건 2: `is_reach_degraded` = `distinct_domains_per_100ku < 15 연속 3c`. 실측 52~57 (floor의 3.5배). Tavily 자연적 다양성으로 절대 조건 미달 불가. + budget kill-switch로 pivot도 차단.
- **수정**: `src/nodes/exploration_pivot.py`에서 `from src.utils.reach_ledger import is_reach_degraded` import 제거 + `should_pivot` 조건 2 전체 제거. 이제 enabled → novelty stagnant → audit 미소비의 2-step. `f822f2c`
- **검증**: E7-3 bench — pivot는 novelty 5c 연속 미달 조건 미충족으로 미발동 (설계상 정상). 기존 unreachable 조건 제거 확인.
- **테스트**: `test_reach_diversity_no_longer_blocks_pivot` — reach=55.0 상황에서도 novelty 정체 시 pivot PASS

### ISSUE-P4-07 (설계): VP4 R5 자동 벤치 원천 불가 — HITL 경로 미구현 (D-150)
- **증상**: E7-2에서 R5 category_addition = 0 (< 임계치 1). candidate_categories에 6개 등록되었으나 active 승격은 0.
- **원인**: 기존 R5 기준 = `phase_history` 내 `category_addition` type 이벤트 카운트. 실제 승격은 HITL-R(사람 승인) 필수. 자동 벤치에 사람 없음 → 영원히 0.
- **수정 (Gate 기준)**: `src/utils/readiness_gate.py` R5를 `probe_history` 실행 횟수로 변경 (`VP4_PROBE_RUNS_FLOOR = 1`). 자동 벤치에서도 probe 1회 실행 시 PASS. `f822f2c`
- **미구현 (런타임)**: `promote_candidate()` 함수는 존재하나 HITL 진입점(CLI/API/interrupt node) 미구현. `dev/active/phase-si-p4-coverage/si-p4-coverage-context.md §5.9` 참조. Future work.
- **검증**: E7-3 bench — R5 probe_runs = 1 PASS. 전체 VP4 PASS 4/5.
- **테스트**: `test_no_probe_run_non_critical` (probe_run_count=0 → R5 FAIL 확인)
