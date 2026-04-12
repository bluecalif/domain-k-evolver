# Silver P2: Outer-Loop Remodel — Context
> Last Updated: 2026-04-12
> Status: Stage A+B 완료 (8/14)

## 1. 핵심 파일

### 읽어야 할 기존 코드
| 파일 | 내용 | 이유 |
|------|------|------|
| `src/nodes/audit.py` | 4 분석함수 (cross_axis_coverage, yield_cost, quality_trends) + run_audit | remodel 입력 = audit 출력 |
| `src/nodes/hitl_gate.py` | HITL-R stub (gate="R", line 32~36) | stub → 실구현 승격 |
| `src/graph.py` | StateGraph 빌드, hitl_r 노드 등록 (line 167) | remodel 경로 엣지 추가 |
| `src/orchestrator.py` | Outer Loop — metrics log → rollback → audit → save | phase transition 핸들러 삽입 위치 |
| `src/state.py` | EvolverState TypedDict (phase_history: line 224) | phase_number 필드 추가 |
| `src/utils/state_io.py` | State JSON I/O | phase 스냅샷 저장 로직 |
| `src/utils/entity_resolver.py` | alias/is_a/canonicalize (P1) | merge/reclassify 제안 시 호출 |
| `src/utils/schema_validator.py` | JSON Schema 검증 | remodel_report 검증 연동 |
| `schemas/*.json` | 기존 5종 스키마 | remodel_report 스키마 참조 |

### 설계 문서
| 파일 | 참조 섹션 |
|------|-----------|
| `docs/silver-masterplan-v2.md` | §4 P2, §14 HITL-R |
| `docs/silver-implementation-tasks.md` | §6 Phase P2 (14 tasks 상세) |

---

## 2. 데이터 인터페이스

### 입력 (어디서 읽는가)
| 데이터 | 소스 | 형태 |
|--------|------|------|
| audit findings | `audit.py:run_audit()` 반환값 | `list[dict]` — `{type, severity, message, details}` |
| 현재 state | `EvolverState` | TypedDict (KU, GU, skeleton 등) |
| entity_resolver | `entity_resolver.py` | alias map, is_a hierarchy |

### 출력 (어디에 쓰는가)
| 데이터 | 대상 | 형태 |
|--------|------|------|
| RemodelReport | `state["remodel_report"]` (임시) → HITL-R | JSON (schema: `remodel_report.schema.json`) |
| phase snapshot | `bench/{domain}/state/phase_{N}/` | 현 state 전체 복사 |
| skeleton 변경 | `state["domain_skeleton"]` | merge/split/reclassify 적용 |
| phase_number | `state["phase_number"]` | int, bump +1 |

### RemodelReport 스키마 (핵심 필드)
```json
{
  "report_id": "RM-0001",
  "created_at": "2026-04-12T...",
  "source_audit_id": "...",
  "proposals": [
    {
      "type": "merge | split | reclassify | alias_canonicalize | source_policy | gap_rule",
      "rationale": "...",
      "target_entities": ["japan-travel:transport:jr-pass", "..."],
      "params": {},
      "expected_delta": {"metric": "...", "before": 0.0, "after": 0.0}
    }
  ],
  "rollback_payload": {},
  "approval": {"status": "pending | approved | rejected", "actor": "...", "at": "..."}
}
```

---

## 3. 주요 결정사항

| # | 결정 | 근거 |
|---|------|------|
| (기존) D-48 | Orchestrator 순서 = metrics log → rollback → audit → save | Phase 4 |
| (기존) D-72 | HITL 축소 — HITL-S/R/D/E 4세트 | P0 |
| (신규) | remodel은 audit 4 분석함수 결과를 **소비만**, 중복 분석 금지 | masterplan §6 P2-A1 verbatim |
| (신규) | remodel 경로 조건: `cycle > 0 and cycle % 10 == 0 and audit.has_critical` | masterplan §6 P2-B1 |
| (신규) | HITL-R rejected → state 변경 없음, rollback_payload 검증만 | masterplan §6 P2-B4 |
| (신규) | phase_number bump = +1 per approved remodel | P2-A3 |

---

## 4. 컨벤션 체크리스트

### 5대 불변원칙
- [x] **Gap-driven**: remodel은 gap rule 제안 가능 → Plan에 반영
- [x] **Claim→KU 착지성**: remodel은 KU 자체를 생성/삭제하지 않음 (merge/split은 entity_key 변경만)
- [x] **Evidence-first**: remodel은 기존 EU를 보존, 재연결만
- [x] **Conflict-preserving**: merge 시 disputed KU는 보존, entity_key만 통합
- [x] **Prescription-compiled**: audit→remodel→plan 경로로 처방 전달

### Metrics 임계치 (P2 직접 관련)
| 지표 | 건강 | 비고 |
|------|------|------|
| rollback state diff | = ∅ | P2 Gate 필수 |
| 중복률 탐지 | ≥ 30% threshold | P2 Gate 필수 |

### Schema 정합성
- `remodel_report.schema.json` — JSON Schema Draft 2020-12
- `state.py` EvolverState — phase_number: int, phase_history: list[dict]

### 인코딩
- JSON read/write: `encoding='utf-8'` explicit
- 커밋: `[si-p2] Step X.Y: 설명`
