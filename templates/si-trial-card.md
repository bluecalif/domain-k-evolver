# Trial Card — {trial_id}

> Created: {YYYY-MM-DD}
> Phase: {phase}
> Domain: {domain}
> Status: planned

## Goal
{한 줄. INDEX.md 에 그대로 들어감}

## Config Diff
이전 trial 대비 변경된 config / code 항목. 없으면 "baseline (no diff)".

- `{config.key}`: {old} -> {new}
- commit: `{git short sha}` (vs baseline `{baseline sha}`)

## 가설
이 trial 이 통과해야 할 가설을 1~3 개 bullet 로. Phase gate 항목과 매핑되어야 한다.

- H1: {가설 1}
- H2: {가설 2}

## 측정 대상
- {metric_1}
- {metric_2}

## 실행 명령

```bash
PYTHONUTF8=1 python scripts/run_readiness.py \
  --bench-root bench/silver/{domain}/{trial_id} \
  --cycles {N}
```

## 상태
- [ ] config.snapshot.json 기록됨
- [ ] 실행 완료
- [ ] readiness-report.md 작성됨
- [ ] INDEX.md row 갱신
