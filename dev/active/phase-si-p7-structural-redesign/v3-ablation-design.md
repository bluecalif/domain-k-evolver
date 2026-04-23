# SI-P7 Step V — V3 Ablation Design (V-T7)

> 작성: 2026-04-23
> 목표: V1/V2 후에도 **축별 기여도 분리가 안 되는 항목** (특히 H5c S2-T4 β) 을 ablation 으로 isolate.
> 근거: D-191 (cycle=8, baseline 재사용, 의심 축 1~2 개 한정)

## 배경

- V1 (재파싱): ✓11 / ✗2 / ~6 / N/A 2. S2-T4 β 는 ✗ 확정이나 root cause 까지 확정 못함 (H5c: S5a coupled dead code 가설)
- V2 (계측): si-p7-signals.json + telemetry si_p7 + event logger 완료. 이제 축별 signal 이 재파싱 가능
- V-T6 smoke: c1 에서 stagnation 자연 미발동 → H5c 확정은 c5+ trial 필요

**V3 목적**: p7-ab-on/off baseline 과 대비하여 **특정 축을 off 한 상태** 로 8c trial 수행. 축별 효과 isolate.

## 원칙 (D-191)

1. **Cycle = 8** (GU 고갈 재현 충분선. p7-ab-on 에서 c2 에 이미 KU 82 고정 관찰 → 8c 면 stagnation trigger 조건도 수차례 검증 가능)
2. **Baseline 재사용**: `p7-ab-on` (상한) + `p7-ab-off` (하한) 이미 존재. 재실행 금지 (비용 + 재현성)
3. **Ablation 방식**: `p7-ab-minus-{axis}` — 해당 축 off, 나머지 on (Step A/B 전체가 on 인 `p7-ab-on` 과 1 축 차이)
4. **의심 축 1~2 개 한정** — 전수 ablation 금지 (비용 최적)
5. **real API 필수** (D-34) / mock 금지 (D-187)

---

## 축별 후보 평가

| 축 | 범위 | H5c 관련성 | 우선순위 | 비고 |
|---|---|---|---|---|
| **S1** (defer/queue) | Target 자유화, deferred_targets | 낮음 | 낮음 | 이미 c1 에서 defer=20, c2 소진 확인. 기능 자체는 작동. |
| **S2** (condition_split + β aggressive) | integration_result, condition_split 재정의, β mode | **매우 높음** | **최우선** | H5c 직접 검증. condition_split 은 c1 에서 5건 확인, β 는 5c+ 에서 stagnation 후 확인 가능 |
| **S3** (adjacent rule engine + suppress + blocklist) | field_adjacency, rule yield tracker, recent_conflict_fields | 중간 | 두번째 | c1 에서 adj_gen, suppress 3건 확인. 8c 동안 rule yield 약화 패턴 관찰 필요 |
| **S4** (virtual entity 제거 + coverage_map.deficit_score) | balance-* 제거, deficit_score | 낮음 | 낮음 | S4-T1 이 `balance-*` 제거라 "단독 원인" 의심 대상이었으나 D-190 으로 기각 방향. 우선순위 하락 |

### 권장: 1~2 trial

- **권장 1개 (비용 절감)**: `p7-ab-minus-s2` — S2-T1~T8 + β aggressive mode off, 나머지 on
- **권장 2개 (완전 검증)**: 추가로 `p7-ab-minus-s3` — S3 adjacent rule engine off
- **3 개 이상은 거절** — D-191 "1~2 개 한정" 원칙 준수

---

## Trial 설계

### Trial #1: `p7-ab-minus-s2`

**가설**: S2 (condition_split 재정의 + β aggressive mode) 를 off 하면:
- H5c 참 (β 가 dead code): p7-ab-minus-s2 ≈ p7-ab-on (차이 미미) → β 자체가 효과 없음 재확인
- H5c 거짓 (β 가 실제 기능): p7-ab-minus-s2 < p7-ab-on (후퇴) 또는 ≠ (다른 패턴)

**off 범위** (config + feature flag):
- `integration_result` plan 주입 비활성 (S2-T1)
- `ku_stagnation` trigger 비활성 (S2-T2)
- `query_rewrite` α 비활성 (S2-T4α) — `_rewrite_query_stagnation` 호출 억제
- β aggressive mode set 비활성 (S2-T4β) — `aggressive_mode_remaining=3` 설정 skip
- condition_split 재정의 비활성 (S2-T5~T8) — 기존 conditions-only rule 로 회귀
- 기타 (S1, S3, S4) 는 on 유지

**구현 방식**: 기존 코드를 건드리지 않고 `OrchestratorConfig` 또는 env flag 추가 (예: `SI_P7_S2_ENABLED=false`). 각 emit/trigger 지점에서 check → no-op

**8c 관찰 지표**:
| 지표 | p7-ab-on (baseline 상한) | p7-ab-minus-s2 (예상) | p7-ab-off (baseline 하한) |
|---|---|---|---|
| KU 성장 (c1→c8) | 26→82 (c2 에 완전 고착) | ? (유사 or 더 낮음) | 31→109 |
| GU open (c8) | 0 | ? | 35 |
| `growth_stagnation` 로그 | 3회 (c5~c15) | 0회 (S2-T2 off) | 0회 |
| `aggressive_mode_history` | 0회 (dead code 의심) | 0회 (S2-T4 off) | 0회 |
| `query_rewrite_rx_log` | 0회 (검증 불가) | 0회 (S2-T4α off) | 0회 |
| `condition_split_events` | ~5건/cycle (V-T6 기준) | 기존 rule 로 축소 | ~5건/cycle |
| 최종 gap_resolution | 1.00 (GU 고갈) | ? | 0.66 (c8 기준) |

**H5c 판정**:
- p7-ab-on 의 `aggressive_mode_history=0` + p7-ab-minus-s2 의 동일 패턴 = β 자체의 기능 부재 (dead code) 확정
- p7-ab-on 에서 `growth_stagnation` 3회 발동 + `aggressive_mode_history=0` = "trigger 는 있으나 action 경로 단절" 정량 증거

### Trial #2 (optional): `p7-ab-minus-s3`

S3 adjacent rule engine 전체 off → GU 발견 메커니즘 복구 여부 확인. **비용 이슈로 Trial #1 결과 후 판단**.

---

## 비용 추정

### 기반 데이터 (run.log 기반 HTTP request count)

| Trial | Cycles | LLM calls (from run.log) | Avg/cycle | 비고 |
|---|---|---|---|---|
| `p7-ab-on` | 15 | 176 | 11.7 | c1-2 집중 (176 중 대부분), c3+ GU 고갈로 0 |
| `p7-ab-off` | 15 | 452 | 30.1 | 건전 성장 시 cycle 당 ~30 |
| `p7-v2-smoke` | 1 | ~55 (추정) | 55 | c1 은 활발 claims 처리 |

### `p7-ab-minus-s2` 8c 예상

- S2 off → condition_split 처리 경로 축소 → LLM 호출 약간 감소
- 다른 축 정상 → 건전 성장 시나리오 (p7-ab-off 패턴과 유사) 가정
- **예상 8c LLM**: ~200-250 calls (p7-ab-off 8c 구간 ≈ 240 calls 기준)
- **예상 8c search**: ~100-150 calls
- **예상 비용**: ~$0.60-0.80 (LLM $0.003/call 기준)

### 2 trial 합계 (최대 시나리오)

- 2 × 240 = ~480 LLM calls, ~200-300 search calls
- **예상 총 비용**: ~$1.20-1.60

---

## 구현 설계 (착수 전)

### Feature flag 시스템

`src/config.py` 에 `OrchestratorConfig.si_p7_axis_toggles: dict[str, bool]` 추가:

```python
@dataclass
class OrchestratorConfig:
    ...
    si_p7_axis_toggles: dict[str, bool] = field(default_factory=lambda: {
        "s1_defer_queue": True,
        "s2_condition_split": True,
        "s2_aggressive_mode": True,
        "s2_query_rewrite": True,
        "s2_integration_injection": True,
        "s2_ku_stagnation_trigger": True,
        "s3_adjacent_rule": True,
        "s3_suppress": True,
        "s3_blocklist": True,
        "s3_yield_tracker": True,
        "s4_balance_removed": True,
        "s4_deficit_score": True,
    })
```

각 emit / trigger 지점에 `if not config.si_p7_axis_toggles.get(...)` check 추가.

### Trial runner 확장

`run_readiness.py --bench-root bench/silver/japan-travel/p7-ab-minus-s2 --cycles 8 --si-p7-axis-off s2`

또는 `config.snapshot.json` 에 축 toggle 기록 → orchestrator 가 로드.

### 검증

- 축 off 시 관련 emit 이 0건 (si-p7-signals.json 에서 빈 필드)
- 다른 축 on 시 정상 동작 (기존 테스트 944 pass)
- L1 테스트: axis toggle 파라미터 전달 + no-op 경로 (mock 금지 — flag 설정 후 production 함수 직접 호출)

---

## V3 실행 전 리스크

| Risk | 완화 |
|---|---|
| 축 toggle 구현 자체가 로직 변경 → 기존 테스트 영향 | 기본값 전부 True (기존 동작). off 시만 check |
| 8c 로 stagnation trigger 미발동 | p7-ab-on 에서 c2 에 이미 KU 82 정체 → 8c 충분. 부족 시 12c 로 조정 |
| `p7-ab-on` baseline 재사용 타당성 | 코드 변경 후 재실행 필요할 수 있음 — V3 실행 전 `p7-ab-on` config 와 min-s2 config diff 가 **축 toggle 만**인지 확인 |
| LLM 응답 가변성 (같은 config 도 결과 다름) | 통계 표본 1 로는 noise 포함. H5c 는 **정성적 패턴** (aggressive_mode_history 0 vs 양) 으로 판정 → noise 영향 적음 |

---

## 승인 요청 (Next Step)

### 옵션 1 — 권장: Trial #1 만 실행 (`p7-ab-minus-s2` 8c)
- 비용: ~$0.60-0.80
- 시간: ~30분 real API (V-T6 기준 c1 4분 × 8 ≈ 32분, 고갈 후 빠름)
- H5c 1차 확정 가능
- Trial #2 는 결과 보고 결정

### 옵션 2 — Trial #1 + #2 묶음 실행 (`p7-ab-minus-s2` + `p7-ab-minus-s3` 8c × 2)
- 비용: ~$1.20-1.60
- 시간: ~60분
- S2/S3 기여도 독립 isolate 완성

### 착수 순서 (옵션 1 기준)

1. **V-T7a** (본 문서) — 설계 + 사용자 승인
2. **V-T7b** — axis toggle 구현 (config + check 지점) + L1 테스트
3. **V-T8** — `p7-ab-minus-s2` 8c trial 실행 (real API)
4. **V-T9** — `v3-isolation-report.md` 작성 (축별 signal diff + H5c 판정)
5. **V-T10** — D-192 root cause 확정

### 승인 필요 사항

- [ ] Trial #1 만 또는 #1+#2
- [ ] Cycle=8 유지 (또는 12로 조정)
- [ ] Axis toggle 구현 방식 (config flag vs env var)
- [ ] 예산 상한 (예: LLM calls 500 이하 / 총 비용 $1 이하)
