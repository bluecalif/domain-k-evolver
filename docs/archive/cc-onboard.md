---
description: claude code에서 프로젝트 온보딩 절차 — 사전 준비(Preparation)와 실제 구현(Implementation) 두 단계로 구성
argument-hint: 프로젝트 온보딩 (예: "project start", "scratch")
---

## Part 1. Preparation (사전 준비)

### 1. 마스터플랜 읽기

- `docs/` 아래 마스터플랜 파일들 읽기: `masterplan-*.md`, `context-*.md`, `plan-*.md`, `detail-*.md`, `guide-*.md`
- 프로젝트 전체 목표, 범위, 기술 스택 파악

### 2. CLAUDE.md 생성

- Reference 확인: `@Projects-2026\archive\REF-CLAUDE.md`
- 마스터플랜을 바탕으로 project-specific instruction 작성
- general instruction은 reference 내용 확인 후 필요시 수정

### 3. commands 생성

- Reference 확인: `@Projects-2026\archive\REF-commands\*`
- reference 파일 복사 → 프로젝트에 맞게 수정 → `.claude\commands\` 저장

### 4. hooks 생성

- Reference 확인: `@Projects-2026\archive\REF-hooks\*`
- reference 파일 복사 → 프로젝트에 맞게 수정 → `.claude\hooks\` 저장

### 5. skills 생성

- Reference 확인: `@Projects-2026\archive\REF-skills\*`
- reference 파일 복사 → **프로젝트 context를 반영하여** 수정 → `.claude\skills\` 저장

### 6. commands / skills 동작 테스트

- 생성한 commands와 skills가 정상 동작하는지 테스트
- 오류 발생 시 즉시 수정

### 7. `dev-docs` command 구현 — project-overall

- `dev-docs` command로 `project-overall` dev-docs 먼저 생성
- project-overall은 rough한 상태이므로, 실제 구현(Phase 1) 전에 모든 설계/설정/계약 사항을 확인하는 Phase 0 역할

### 8. `dev-docs` command 구현 — Phase 1

- `project-overall`과 Phase 1 context를 기반으로 Phase 1 dev-docs 생성
- Phase 1 구현에 필요한 상세 스펙, 인터페이스, 의존성 정의

### 9. Phase 1 실제 구현 시작

- Phase 0(Preparation) 완료 확인
- Phase 1 plan 및 context 존재 여부 확인 후 구현 착수

---

## Part 2. Actual Implementation (실제 구현)

### 1. `session-compact` command — sub step 완료 시

- sub step 완료 시 (또는 context가 가득 찰 때) `session-compact` 실행
- 현재 진행 상태를 compact하여 저장 → clear 후 이어서 작업 가능하도록 함

### 2. `step-update` command — 3~5 sub step마다

- 3~5개 sub step 완료 시 `step-update` 실행
- git commit + dev-docs 업데이트를 함께 수행

### 3. Phase 완료 시 프로젝트 상태 점검

- Phase 완료 전 audit: `re-consider this phase original goal in terms of total project context. Are there any missing parts? If not satisfactory, show me the better plan`
- 부족한 부분에 대한 개선 plan 생성 및 실행
- Phase 내 **자기완결성** 반드시 확보

---

## 주의 사항

- **Clear**: 매 과제 실시 완료(step 완료가 아님) 시 반드시 **Clear** 실시
- **Compact**: 과제가 길어지면 반드시 **Compact** 실시
- **자기완결성**: Phase 안에서 Phase 자기완결성을 반드시 확보할 것
- **Rate limit 대비**: CC 작업 중 rate limit 초과 시 마지막 상태를 compact하여 `temp_compact.md`에 기록
