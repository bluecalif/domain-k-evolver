# INDEX.md Row 템플릿

> `bench/silver/INDEX.md` 에 추가할 trial row 형식.
> masterplan v2 §12.4 verbatim.

## 신규 등록 (실행 전)

```markdown
| {trial_id} | {domain} | {phase} | {date} | {goal} | planned | - | - |
```

## 실행 중

```markdown
| {trial_id} | {domain} | {phase} | {date} | {goal} | running | - | - |
```

## 완료 (실행 후)

```markdown
| {trial_id} | {domain} | {phase} | {date} | {goal} | complete | VP1={x}/5 VP2={y}/6 | {짧은 노트} |
```

## 실패

```markdown
| {trial_id} | {domain} | {phase} | {date} | {goal} | failed | - | {실패 원인 요약} |
```

## 폐기

```markdown
| {trial_id} | {domain} | {phase} | {date} | {goal} | archived | - | {폐기 사유} |
```

## 규칙

- `status` 값: `planned` | `running` | `complete` | `failed` | `archived`
- 기존 row 절대 삭제 금지 (§12.3 규칙 6)
- `readiness` 컬럼: gate 판정 요약, 미판정 시 `-`
- `notes`: git dirty 시 `[dirty]` 표기, 그 외 짧은 메모
