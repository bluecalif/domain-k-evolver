# Silver P1: Entity Resolution & State Safety — Context
> Last Updated: 2026-04-12
> Status: Complete (12/12, 544 tests)

---

## 1. 핵심 파일

### 읽어야 할 기존 코드
| 파일 | 내용 | 참조 이유 |
|------|------|-----------|
| `src/nodes/integrate.py` | Claims → KU/GU 통합 노드 | `_find_matching_ku` 수정 대상 (L28~L37) |
| `src/nodes/dispute_resolver.py` | Evidence-weighted dispute 해결 | ledger entry 업데이트 연동 |
| `src/state.py` | EvolverState + 보조 타입 | `conflict_ledger: list[dict]` 이미 선언 (L223) |
| `src/utils/state_io.py` | State JSON I/O | `conflict_ledger.json` save/load 추가 |
| `src/utils/schema_validator.py` | JSON Schema 검증 | skeleton validator 확장 |
| `bench/silver/japan-travel/p0-20260412-baseline/` | P0 baseline trial | 중복 KU 감소 비교 기준 |

### 신규 작성 파일
| 파일 | 내용 |
|------|------|
| `src/utils/entity_resolver.py` | alias/is_a/canonicalize 함수 3개 |
| `tests/test_utils/test_entity_resolver.py` | resolver 단위 테스트 ≥ 8건 |
| `tests/integration/test_japan_travel_rerun.py` | 중복 KU 15% 감소 통합 테스트 |

### 수정 파일
| 파일 | 수정 내용 |
|------|-----------|
| `src/nodes/integrate.py` | `_find_matching_ku` → resolver 경유 |
| `src/nodes/dispute_resolver.py` | resolve 시 `conflict_ledger` status=resolved 업데이트 |
| `src/utils/state_io.py` | `conflict_ledger.json` save/load |
| `src/utils/schema_validator.py` | skeleton aliases/is_a optional validation |
| `bench/japan-travel/state/domain_skeleton.json` | alias/is_a 예시 추가 |
| `tests/test_nodes/test_integrate.py` | S4/S5/S6 scenario 추가 |

---

## 2. 데이터 인터페이스

### 입력
| 데이터 | 소스 | 형식 |
|--------|------|------|
| skeleton.aliases | `domain_skeleton.json` | `{canonical_key: [alias1, alias2, ...]}` |
| skeleton.is_a | `domain_skeleton.json` | `{child_key: parent_key}` |
| Claims (current_claims) | collect_node 출력 | `list[dict]` (P0-X2 동결) |
| conflict_ledger | `state/conflict_ledger.json` | `list[dict]` (P1-B1 포맷) |

### 출력
| 데이터 | 대상 | 형식 |
|--------|------|------|
| resolved entity_key | integrate_node 내부 | canonical `str` |
| is_a parent chain | integrate_node 내부 | `list[str]` |
| conflict_ledger entries | `state/conflict_ledger.json` | append-only, 삭제 금지 |
| updated KUs | EvolverState.knowledge_units | P0-X1 동결 shape |

### conflict_ledger entry 포맷 (P1-B1)
```json
{
  "ledger_id": "cl-001",
  "ku_id": "KU-0042",
  "created_at": "2026-04-12T14:30:00",
  "status": "open",
  "conflicting_evidence": ["EU-0012", "EU-0034"],
  "resolution": null
}
```

resolved 상태:
```json
{
  "ledger_id": "cl-001",
  "ku_id": "KU-0042",
  "created_at": "2026-04-12T14:30:00",
  "status": "resolved",
  "conflicting_evidence": ["EU-0012", "EU-0034"],
  "resolution": {
    "method": "evidence_weighted",
    "resolved_at": "2026-04-12T15:00:00",
    "chosen_ku": "KU-0042"
  }
}
```

---

## 3. 주요 결정사항

| # | 결정 | 근거 |
|---|------|------|
| D-96 (예정) | alias map 은 skeleton 에 정적 선언 (LLM 동적 생성 아님) | 결정론적 매칭 보장, LLM 호출 비용 절감. 후속 Phase 에서 audit 기반 alias 자동 제안 가능 |
| D-97 (예정) | is_a depth limit = 5 | 순환 방지 + japan-travel 계층 최대 3단 |
| D-98 (예정) | conflict_ledger 는 append-only (삭제/수정 불가, status 변경만) | 감사 추적성 보장 (5대 원칙: conflict-preserving) |
| D-99 (예정) | dispute_queue = 휘발성 큐, conflict_ledger = 영속 감사 로그 — 독립 구조 | P0-C7 에서 추가된 dispute_queue 와의 관계 명확화 |

---

## 4. 컨벤션 체크리스트

### 5대 불변원칙
- [ ] **Gap-driven**: Plan.target_gaps ⊆ G.open — P1 변경 없음 (영향 없음)
- [ ] **Claim→KU 착지성**: resolver 경유 후에도 모든 claim 이 add/update/reject 중 하나로 착지
- [ ] **Evidence-first**: resolver 가 KU merge 시 evidence_links 합집합 유지
- [ ] **Conflict-preserving**: conflict_ledger 영속 보존 (삭제 금지) — **P1 핵심**
- [ ] **Prescription-compiled**: P1 변경 없음 (critique/plan_modify 미수정)

### Metrics 영향
- 중복 KU 감소 → `evidence_rate` 개선 예상 (같은 entity 의 evidence 가 하나의 KU 에 집중)
- `conflict_rate` 는 정확한 감지이므로 변동 가능 (FP 감소 + 실질 conflict 유지)

### Blocking Scenarios
- **S4**: 동의어 2개 (JR-Pass / 재팬레일패스) → `test_alias_equivalence`
- **S5**: is_a (shinkansen → train) → `test_is_a_inheritance`
- **S6**: conflict 보존 후 resolve → `test_conflict_ledger_persistence`

### 인코딩
- `conflict_ledger.json` read/write: `encoding='utf-8'` 명시
- skeleton JSON: `encoding='utf-8'` 명시
