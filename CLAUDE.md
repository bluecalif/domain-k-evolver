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
# /step-update after each step | /dev-docs to generate planning docs
# /compact-and-go to compact session and continue
python -m pytest                    # Run all tests
```

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
