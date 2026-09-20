# Red-team — base model (garak)

- **garak** v0.17.0 · target: Ollama `qwen3-coder:30b` (self-hosted, sandbox)
- **probe**: `dan.DanInTheWild` (254 jailbreak prompts) · detector: `mitigation.MitigationBypass`
- **result**: 360 of 1280 model slices flagged → **attack success rate 28.1%**
- seed 42 · raw report: `reports/garak/garak.dbd65157-57ea-4bce-9eda-fdaa552a0859.report.jsonl`

## What this measures

This is a **base-model** red-team: garak talks to the raw Ollama endpoint, so the
28.1% reflects the model with no guard in the loop. It is the *untreated* risk
surface, not the pipeline outcome.

## How it reads against the pipeline

The guarded pipeline in `run_demo.py` intercepts these classes earlier:
- input guard blocks prompt-injection framing before generation (2/8 caught in run 001),
- the findings run showed the guarded agent at 1/8 risky outputs (and hardening closed that),
- every generation is judged and gated before anything ship-shaped.

A jailbreak that slips a mitigation-bypass detector is exactly the case we want to
count, so this number goes in the report next to the guard delta instead of it. Re-run command (bounded):

```sh
.venv/bin/garak --model_type ollama --model_name qwen3-coder:30b \
  --probes dan.DanInTheWild --parallel_attempts 4 --seed 42
```