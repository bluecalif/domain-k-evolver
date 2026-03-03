# Project Overall Debug History
> Last Updated: 2026-03-03

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

## Phase 1: LangGraph Core Pipeline

(아직 시작 전)

---

## Phase 2: Bench Integration & Validation

(아직 시작 전)

---

## Phase 3: Multi-Domain & Robustness

(아직 시작 전)
