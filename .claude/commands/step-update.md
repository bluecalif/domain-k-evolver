---
description: Step 완료 → Phase docs 업데이트 → Git commit (project-overall은 명시 요청 시만)
argument-hint: phase-name step-number [--sync-overall] (예: "phase1 1.3" 또는 "phase1 1.3 --sync-overall")
---

# 단계 업데이트 (Step Update)

**Task:** $ARGUMENTS

## Overview

개발 단계(step) 완료 시 실행. Phase 문서를 업데이트한 뒤 커밋.

> **Note:** `project-overall` 동기화는 `--sync-overall` 플래그가 있거나 사용자가 명시적으로 요청할 때만 수행.

```
Phase docs 업데이트 → Git Commit (+ project-overall 동기화는 선택적)
```

---

## Instructions

### 1. 인자 파싱 (Parse Arguments)

입력 형식: `[phase-name] [step-id]`

예시:
- `phase1 1.3` → Phase 1, Step 3
- `phase2 2.1` → Phase 2, Step 1

### 2. 현재 상태 확인 (Check Current State)

읽어야 할 파일:
```
dev/active/[phase-name]/[phase-name]-tasks.md
dev/active/[phase-name]/[phase-name]-context.md
dev/active/[phase-name]/[phase-name]-plan.md
dev/active/[phase-name]/debug-history.md
docs/session-compact.md
```

`--sync-overall` 플래그 있을 때 추가로 읽기:
```
dev/active/project-overall/project-overall-tasks.md
dev/active/project-overall/project-overall-plan.md
dev/active/project-overall/project-overall-context.md
```

확인 사항:
- [ ] Phase dev-docs 파일 존재 여부 (없으면 `/dev-docs` 먼저 실행 안내)
- [ ] 현재 브랜치, 커밋되지 않은 변경사항
- [ ] 완료된 step의 실제 코드 변경 내역 (`git diff --stat`)

### 3. Phase Dev-Docs 업데이트

#### 3.1 `[phase-name]-tasks.md`
- 완료된 step 체크: `- [ ]` → `- [x]` + commit hash
- Progress 카운터 갱신 (예: `3/14 (21%)`)

#### 3.2 `[phase-name]-context.md`
- 변경/생성된 파일 목록 추가
- 새 결정사항 추가 (있을 경우)

#### 3.3 `debug-history.md`
- 해당 step에서 발생한 버그/디버깅 이력 추가
- 버그/디버깅 없는 step이면 이 섹션 스킵

#### 3.4 `[phase-name]-plan.md`
- Last Updated 날짜 갱신
- Status / Current Step 갱신
- Current State 섹션에 완료 항목 추가

### 4. project-overall 동기화 (--sync-overall 시에만)

> **SKIP** 이 섹션은 `--sync-overall` 플래그가 없고 사용자가 요청하지 않았으면 건너뛴다.

### 5. session-compact.md 업데이트

- Remaining/TODO 해당 항목 진행 상태 반영
- Phase 마지막 step 완료 시: Phase 자체를 `[x]` 완료 처리

### 6. 정합성 검증 (Consistency Check)

업데이트 후 아래를 검증:
- [ ] session-compact.md의 TODO가 실제 진행률과 일치

### 7. Git Commit

#### 7.1 Staging
```bash
git add src/                            # 해당 Phase 코드
git add dev/active/[phase-name]/        # Phase dev-docs
git add docs/session-compact.md         # session-compact (변경 시)
```

#### 7.2 Commit Message 형식
```
[phase-name] Step X.Y: 간단한 설명

- 주요 변경 1
- 주요 변경 2

Refs: dev/active/[phase-name]/[phase-name]-tasks.md
```

### 8. Git Push & Remote 정합성 확인

```bash
git push origin [branch-name]
git fetch origin
git log --oneline HEAD..origin/[branch-name]
git log --oneline origin/[branch-name]..HEAD
```

---

## Output Format

```
Step Update 완료

Task: [phase-name]
Step: X.Y — [Step Name]

Phase docs 업데이트:
- tasks.md: Step X.Y 완료 체크 (N/M, P%)
- context.md: N개 파일/결정사항 추가
- plan.md: 상태 업데이트
- debug-history.md: N개 버그/디버깅 이력 추가 (없으면 스킵)

Git:
- Commit: [hash] [message]
- Push: origin/[branch] ← [hash]
- Remote 정합: local == remote
```
