# Project Overall Debug History
> Last Updated: 2026-04-27

## 기록 규칙
- Phase별로 발생한 버그/디버깅 이력을 시간순 기록
- 각 항목: 날짜, Phase/Step, 증상, 원인, 수정, 교훈

---

## Preparation (Claude Code 인프라 구축)

### 2026-03-03 | Hook PS1 BOM 문제
- **증상**: Write 도구로 생성한 `.ps1` 파일이 PowerShell 문법 검증 실패
- **원인**: Write 도구가 UTF-8 BOM을 삽입 → PowerShell 5.1 파서가 BOM 이후 첫 토큰을 인식 못함
- **수정**: Bash heredoc (`cat > file << 'EOF'`)으로 작성하여 BOM 없는 UTF-8 파일 생성
- **교훈**: Windows에서 PS1 파일은 Bash heredoc으로 작성. Write 도구의 BOM 동작 주의.

---

## 2026-03-03 ~ 2026-04-27 | Silver 전 Phase 갭 (50일)

> 이 기간의 디버깅 이력은 각 Phase dev-docs 의 debug-history.md 에 개별 기록됨.
> 아래는 project-overall 수준의 주요 판단 지점만 요약.

### 2026-04-25~27 | SI-P7 attempt 1 종결 + attempt 2 rebuild CLOSED

**attempt 1** (main `a33dfdb`, tag `si-p7-attempt-1`):
- Step A/B 구현 완료 후 c3+ 고착 발견. V1~V5 audit (~$2.0, 3 ablation trials).
- D-194/195/196: Primary Introducer=S2, T5~T8 subtask, S1 adj oscillation 메커니즘 확정.

**attempt 2 rebuild** (`feature/si-p7-rebuild` from `2ebd435`):
- Axis-gated 재구현. S1/S2/S3/S4 gate PASS. GU 확장 6종 fix (D-203~D-208).
- S3 Diagnosis Trial 1/2/3 (5c each, ~$2.5 총비용): KU 79→120 (+52%). M-Gate V/O 4/6 + M 9/13 PASS.
- **CLOSED (2026-04-27)**: 잔여 FAIL (O1/O2/M5/M6/M7) = plan-side budget 한계. merge 후 P6 에서 동반 처리.
- V-T11 cherry-pick 완료 (commit `176d2c0`), D-202 예외 적용.
- **교훈**: per-axis 5c smoke gate 가 c3+ 고착 조기 발견에 효과적. GU pool 고갈 → plan budget 제약이 dominant blocker.

---

## Phase 1: LangGraph Core Pipeline

(아직 시작 전)

---

## Phase 2: Bench Integration & Validation

(아직 시작 전)

---

## Phase 3: Multi-Domain & Robustness

(아직 시작 전)
