---
description: 대화 컴팩트 → 결과 파일 저장 → 클리어 → 컴팩트 파일 기반으로 다음 작업 이어서 진행
argument-hint: (optional) next action to continue after compaction
---

# Compact and Go

**Next Action:** $ARGUMENTS

## Overview

현재 대화를 컴팩트하고, 결과를 파일로 저장한 뒤, 대화를 클리어하고, 저장된 컴팩트 파일을 기반으로 다음 작업을 이어서 진행합니다.

```
/compact → Save to file → /clear → Continue from compact file
```

---

## Instructions

### Step 1: Compact the conversation

현재 대화의 전체 컨텍스트를 요약합니다. 다음 내용을 포함하여 정리하세요:

1. **작업 목표 (Goal)**: 이 대화에서 수행하려던 전체 목적
2. **완료된 작업 (Completed)**: 지금까지 완료한 모든 작업 목록 (파일 생성/수정 포함)
3. **현재 상태 (Current State)**: 프로젝트의 현재 상태, 변경된 파일들
4. **진행 중/남은 작업 (Remaining)**: 아직 완료하지 못한 작업이나 다음에 해야 할 일
5. **주요 결정사항 (Decisions)**: 대화 중 내린 중요한 기술적 결정들
6. **컨텍스트 (Context)**: 다음 세션에서 알아야 할 핵심 정보 (에러, 제약조건, 참조 파일 등)
7. **다음 액션 (Next Action)**: `$ARGUMENTS`가 있으면 해당 내용을, 없으면 대화 흐름에서 파악한 다음 단계를 명시

### Step 2: Save compaction result to file

위 요약 내용을 `docs/session-compact.md` 파일에 저장합니다. **기존 파일이 있으면 덮어씁니다.**

파일 형식:

```markdown
# Session Compact

> Generated: YYYY-MM-DD HH:MM
> Source: Conversation compaction via /compact-and-go

## Goal
[작업 목표]

## Completed
- [x] 완료 항목 1
- [x] 완료 항목 2

## Current State
[현재 상태 설명]

### Changed Files
- `path/to/file1` - 설명
- `path/to/file2` - 설명

## Remaining / TODO
- [ ] 남은 항목 1
- [ ] 남은 항목 2

## Key Decisions
- 결정 1: 이유
- 결정 2: 이유

## Context
다음 세션에서는 답변에 한국어를 사용하세요.
[다음 세션에서 필요한 핵심 정보]

## Next Action
[다음에 수행할 구체적 작업]
```

### Step 3: Instruct user to clear

파일 저장 완료 후, 사용자에게 다음 메시지를 표시합니다:

```
Compaction saved to: docs/session-compact.md

Now run: /clear

After clearing, start a new message and I will automatically
pick up from the compact file and continue with the next action.
```

### Step 4: (After /clear) Continue from compact file

**새 대화가 시작되면**, `docs/session-compact.md` 파일을 읽고:

1. 파일의 **Next Action** 섹션을 확인
2. **Context** 및 **Current State**를 파악
3. 해당 다음 액션을 즉시 실행
