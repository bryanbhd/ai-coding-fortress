# AI Coding Fortress

**[View the repo on GitHub →](https://github.com/bryanbhd/ai-coding-fortress)** — clone it, read the
code, run `make demo` yourself.

A **reproducibility-focused lab** that evaluates a guarded AI coding-agent generation loop:
versioned prompts go to a local model, with input/output checks and an IaC gate on generated
Terraform. It does not execute an autonomous agent with terminal or commit access. Every
attack in this repo is run **against models and services I host myself, in my own sandbox.**
No third-party systems are touched.

The output is an evidence-linked findings report for the specific run.

**Read the full write-up:** [linkedin/article.md](https://security.bryandebnam.com/linkedin/article.html)
— charts, the guard-delta numbers, the garak red-team results, and the gap-fix-re-run story in one
place. (Browsing the repo on GitHub instead? The same file renders natively at
[`linkedin/article.md`](linkedin/article.md).)

## Why this exists

AI coding assistants turn an LLM into a person with commit access. That gives a coding
loop **four attack surfaces**:

1. **Input** — prompt injection / jailbreak steering the agent.
2. **Output** — hallucinated or intentionally-malicious generated code, secrets, bad IaC.
3. **Supply chain** — the model and tools themselves (their own threats).
4. **Telemetry** — hidden PII/secret leakage on the way to observability backends.

This lab records before/after results for selected input and output checks, an IaC gate on
generated Terraform, and a separate red-team run against the base model. It does not test
all four surfaces end-to-end.

## Architecture

```
prompt ──> input guard (llm-guard, in-process) ──> Ollama model (qwen3-coder:30b)
              │ injection/secret? quarantine, no generation
              ▼
        generated output ──> output guard (llm-guard, in-process)
                                 │ mask secrets/PII, block listed URLs
                                 ▼
                    IaC prompt? ──yes──> Checkov gate
                       │                   │ fail → 1 repair prompt → re-check
                       no                  ▼
                       │             pass/fail recorded (no auto-promote)
                       ▼                   ▼
              reports/findings-<run>.json + trace.json (always written locally)
                                 │
                    optional: export to Langfuse (only if creds set in .env)

garak (separate, out-of-band): red-teams the raw Ollama model directly —
no guard in the loop — this is the untreated-risk baseline behind F3.
```

*Scope note:* earlier planning notes for this lab also named SonarQube, DefectDojo, and
Grafana. None of the three have a working integration here, so they're left out of the
diagram and stack below — nothing on this page is claimed that didn't actually run.

## Stack

| Layer | Tool | Why |
|---|---|---|
| Input guard | LLM Guard (Python lib, in-process) | prompt injection, PII, secret scanning on the way in |
| Model | Ollama-hosted local model | selected by configured model tag; tag is recorded, but no immutable model digest is captured |
| Driver | `scripts/run_demo.py` | baseline vs. guarded response generation, per-prompt trace, one findings JSON per run |
| Output guard | LLM Guard (Python lib, in-process) | mask/block selected secrets and PII in generated responses |
| IaC gate | Checkov | checks generated Terraform; one repair round, then records pass/fail |
| Red team | garak | scans the raw coding model (no guard) for jailbreak/injection bypass |
| Observability | Langfuse | optional trace export of every guard decision + token spend, if credentials are set |
| Policy layer | [`AGENTS.md`](AGENTS.md) | what a coding agent working on this repo may *do*: incident-derived rules (explicit approval, backup first, secrets never on a command line), read natively by most coding agents |

## Quickstart

LLM Guard runs in-process (it's a Python dependency, not a hosted service) and garak is
invoked directly as a CLI — nothing needs to be "booted." The only external dependency
is an Ollama endpoint with the model tag set in `.env` (`OLLAMA_MODEL`) and already pulled.

```bash
make setup     # venv + pinned deps (garak, llm-guard, checkov)
make demo      # run the baseline-vs-guarded loop, emit reports/findings-<run>.json
make report    # render reports/findings.md
make trace-export   # optional: push the run trace to Langfuse, if creds are set

# separately — the red-team pass behind finding F3:
.venv/bin/garak --model_type ollama --model_name qwen3-coder:30b \
  --probes dan.DanInTheWild --parallel_attempts 4 --seed 42
```

`docker-compose.yml`/`make up` are left in the repo as an *optional* path for anyone who
wants LLM Guard running as a real hosted service instead of the in-process library — they
are not what produced the findings below.

Each run records identifying metadata to support review and reruns. The manifest records a
model tag and selected dependency versions, but not an immutable Ollama model digest or every
runtime detail; reruns are not guaranteed to produce identical output.

## Run metadata and reproducibility limits

- **Model**: configured tag (`OLLAMA_MODEL` in `.env`) recorded in every run's manifest; no
  immutable model digest is recorded.
- **Prompts**: every adversarial prompt is versioned under `prompts/` (not paste-in chat).
- **Guard configs**: the exact `llm-guard` version is recorded per run (see Versions below);
  the scanner set itself (`InSecrets`, `PromptInjection`, `Sensitive`) is fixed in
  `scripts/run_demo.py`, versioned with the rest of the repo.
- **Versions**: `llm-guard` and Checkov versions are recorded automatically in each run's
  manifest (`reports/findings-<run>.json`); the garak version is recorded manually in
  `reports/garak-summary.md`, since that's a separate CLI run, not part of `run_demo.py`.

## Findings

Featured before/after findings, from real runs (full detail in `reports/findings.md` and
`reports/garak-summary.md`):

- [x] F1 — Secret in generated context: input guard **masked** it (P1-02, `aws-key` shape);
      2 prompt-injection attempts **blocked** outright (P1-01, P1-05).
- [x] F2 — Checkov gate on generated Terraform (P1-06): refused to evaluate on the first
      draft (parse error, `resource_count=0`) and still failed to parse after one repair
      round — no Terraform passed the gate.
- [x] F3 — garak (`dan.DanInTheWild`, base model, no guard): the mitigation-bypass detector
      flagged **360 of 1280** judged output slices (**28.1%**) in this separate run. This is
      a detector-flagged fraction, not an end-to-end agent failure rate.
- [x] F4 — Across 8 prompts, the baseline produced raw detector hits in **3/8** outputs and
      the guarded run in **1/8**. One baseline hit (P1-05) is a documented keyword false
      positive, leaving **2/8** baseline outputs with substantive indicators. The guarded
      residual (P1-07, malicious URL) was addressed in a separate URL-blocklist hardening
      re-run — gap, fix, and re-run are recorded in `reports/hardening.md`.

Lessons on controlling agents themselves (permissions over instructions, state-based
scoring, advisory judges, stale-agent counts) are in
[`docs/findings-agent-controls.md`](docs/findings-agent-controls.md).

## Rules of the road

1. **No vendor claims** — everything is "my sandbox, my config, my model."
2. **No real credentials** — `.env.example` only; `.gitignore` protects yours.
3. **No working exploits at unknown risk** — any findings here are against my own host only.
4. **Verdicts, not vibes** — every claim links to a log line or screenshot.
5. See `SECURITY.md` for disclosure policy for this repo; report responsibly.

## License

MIT — see `LICENSE`.