# CLAUDE.md

> **Rule: This file must stay under 100 lines.** Move details to skills or `dev/` docs.

## Project Overview

Domain-K-Evolver — 도메인 불문 자기확장 지식 Evolver 프레임워크.
부분적으로 알려진 지식에서 시작해 Gap-driven 계획 → 수집 → 통합 → 비평 → 계획수정 루프를 반복하며 지식을 자동 확장.
Docs: `docs/draft.md` (원본 설계), `docs/design-v2.md` (Cycle 0 검증 반영 정교화 설계).

## Tech Stack

- **Language**: Python (anaconda3)
- **Framework**: LangGraph (자동화 파이프라인)
- **Data**: JSON 파일 기반 상태 관리 (추후 SQLite/PostgreSQL 전환 가능)
- **Tools**: WebSearch, WebFetch (collect_node)
- **Bench**: `bench/japan-travel/` (일본 여행 벤치 도메인)

## Core Concepts

```
State = (K, G, P, M, D)
  K: Knowledge Units (KU) — 정규화된 주장
  G: Gap Map (GU) — 결손/불확실/충돌/노후화
  P: Policies — 출처신뢰/TTL/교차검증/충돌해결 규칙
  M: Metrics — 근거율/충돌률/커버리지 등
  D: Domain Skeleton — 카테고리/필드/관계/키규칙
```

## Inner Loop (6단계)

```
Seed → Plan → Collect → Integrate → Critique → Plan Modify → Next Cycle
```

## 5대 불변원칙

1. **Gap-driven**: Plan은 Gap이 구동
2. **Claim→KU 착지성**: 모든 Claim은 KU로 변환
3. **Evidence-first**: KU는 EU 없이 미완성
4. **Conflict-preserving**: 충돌은 구조적 보존
5. **Prescription-compiled**: Critique 처방은 Plan에 반영

## Project Structure

```
docs/           — 설계 문서 (draft, design-v2, session-compact)
schemas/        — JSON Schema (KU, EU, GU, PU)
templates/      — 6대 Deliverable MD 템플릿
bench/          — 벤치 도메인 (japan-travel: cycle-0, state/)
dev/active/     — Phase별 dev-docs (plan, context, tasks, debug-history)
src/            — LangGraph 자동화 코드 (구현 예정)
```

## Common Commands

```bash
python -m pytest                    # Run all tests
python scripts/run_readiness.py     # 실 벤치 (유일한 실행 진입점)
python scripts/analyze_trajectory.py # 결과 분석
```

## Scripts Policy

- **실행 스크립트는 `run_readiness.py` 단일 진입점.** 새 실행 스크립트 금지 — 옵션/플래그로 확장.
- 비교·분석 스크립트(예: `run_p2_bench.py`, `analyze_trajectory.py`)는 허용 (API 미호출).
- 새 스크립트 추가 시: 기존 스크립트로 불가능한 이유를 커밋 메시지에 명시.
- `run_one_cycle.py`, `run_bench.py`는 **deprecated** — `run_readiness.py --cycles 1`로 대체.

## Bash Tool Rules

- **항상 절대경로 사용** — 특히 git 명령어. `cd` 대신 절대경로로 실행.

## Encoding (Windows + Korean)

| Context | Rule |
|---------|------|
| CSV read | `encoding='utf-8-sig'` (BOM) |
| File write | `encoding='utf-8'` explicit |
| JSON read/write | `encoding='utf-8'` explicit |
| Python stdout | `PYTHONUTF8=1` env var |

**Never rely on system default encoding.** Always specify explicitly.

## Workflow Conventions

- **Dev docs**: `dev/active/[phase-name]/` with `-plan.md`, `-context.md`, `-tasks.md`, `debug-history.md`
- **Commits**: `[phase-name] Step X.Y: description`
- **Branches**: `feature/[phase-name]`
- **entity_key 형식**: `{domain}:{category}:{slug}` (예: japan-travel:transport:jr-pass)
- **Convention checks**: 5대 불변원칙 준수, Metrics 임계치 확인, Schema 정합성
- **Phase Gate**: 합성 E2E만으로 gate 불가. 실 벤치 trial (real API, before/after metrics 비교) 필수
