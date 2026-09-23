# Findings Report — <run-id>

> Everything below is against **my own sandbox**: local model, local services, prompts I
> authored. It says nothing about any software vendor.

## Run manifest

| Field | Value |
|---|---|
| Date | YYYY-MM-DD |
| Model + tag | `ollama/<model>:<tag>` (digest) |
| LLM Guard version | `<ver>` |
| garak version | `<ver>` |
| Checkov version | `<ver>` |
| Prompts | `prompts/<run-id>.json` (versioned) |
| Seeds | `<list>` |

## Methodology

1. `make setup` once (venv + pinned deps).
2. Run baseline + guarded loop against the adversarial prompt set (`make demo` — this
   runs both arms in one pass, not two separate steps).
3. Render the report (`make report`), which regenerates it from the run JSON.
4. Run garak against the raw model separately, out-of-band (see `reports/garak-summary.md`).
5. Export the trace to Langfuse if configured (`make trace-export`); otherwise it stays local.

## Findings

### F1 — Input guard blocks secret emission
- **Prompt**: P1-07 (code snippet requesting IaC with embedded key)
- **Baseline output**: unguarded agent output contained `AKIA...`-style value
  [log link]()
- **Guarded output**: value masked `***MASKED***` [log link]()
- **Verdict**: guard works for this config; mask policy `REGEX_PII`/`SECRETS`

### F2 — Checkov gate on first agent commit
- **Findings on iteration 1**: N (L: X, H: Y, M: Z)
- **Auto-fixed by loop iteration 2**: M of N (list which)
- **Gate**: CI blocks merge until M=0 for `HIGH`/`CRITICAL`

### F3 — garak vs coding model
- **Probes run**: `dan`, `knownbadsignatures`, `promptinject`
- **Attempts**: Y — **succeeded**: X
- **Cadence**: model retained refusal in N cases
- **Caveat**: local base model, no safety-tuned post-config; numbers are config-specific

### F4 — Observability trace
- **Trace**: input-guard veto captured in Langfuse [link]()
- **Tokens/iteration**: mean ± std across loop
- **Guard latency p50/p95**: ms

## Limitations

- Single model config; results do not generalize to other models/services.
- No production data used. All prompts synthetic.
- Re-run with the manifest above to verify.

## Summary

One-sentence verdict + what a hiring manager should take away.