# Red-team — base model (garak)

- **garak** v0.17.0 · target: Ollama `qwen3-coder:30b` (self-hosted, sandbox)
- **probe**: `dan.DanInTheWild` · detector: `mitigation.MitigationBypass`
  (512 attempts, 251 distinct prompt texts, 2560 raw generations — 1280 of them judged by this
  detector; see the raw report's `entry_type: eval` row for the authoritative counts)
- **result**: detector flagged 360 of 1280 judged output slices → **28.1% flagged fraction**
- seed 42 · raw report: `reports/garak/garak.dbd65157-57ea-4bce-9eda-fdaa552a0859.report.jsonl`

## What this measures

This is a **base-model** red-team: garak talks to the raw Ollama endpoint, so the
28.1% is the mitigation-bypass detector's flagged fraction for the judged slices in this
run, with no guard in the loop. It is not an end-to-end agent failure rate or the pipeline
outcome.

## How it reads against the pipeline

The separate harness in `run_demo.py` measures a small set of baseline and guarded
response-generation prompts:
- input guard blocked 2 of 8 prompts in run 001,
- the guarded response had a raw detector hit in 1 of 8 prompts; the baseline count includes
  one documented false positive,
- a separate P1-07 hardening re-run verified that the local URL blocklist blocked that case.

These are different tests with different measures; the garak flagged fraction is reported
alongside, not compared with, the eight-prompt guard evaluation. Re-run command:

```sh
.venv/bin/garak --model_type ollama --model_name qwen3-coder:30b \
  --probes dan.DanInTheWild --parallel_attempts 4 --seed 42
```