# AI Coding Fortress

A **reproducible lab** that secures an AI coding loop — an autonomous agent that writes
and ships code, wrapped in input/output guards, CI security gates, observability, and a
red-team harness. Every attack in this repo is run **against models and services I host
myself, in my own sandbox.** No third-party systems are touched.

The output is a verifiable findings report you can attach to anything you publish.

## Why this exists

AI coding assistants turn an LLM into a person with commit access. That gives a coding
loop **four attack surfaces**:

1. **Input** — prompt injection / jailbreak steering the agent.
2. **Output** — hallucinated or intentionally-malicious generated code, secrets, bad IaC.
3. **Supply chain** — the model and tools themselves (their own threats).
4. **Telemetry** — hidden PII/secret leakage on the way to observability backends.

This lab shows — with before/after evidence — what happens to each surface when you wrap
the loop in the right tools.

## Architecture

```
prompt ──> LLM Guard ──> local coding agent (Ollama)   # input: injection/PII/secrets
              ─────────────│
              Agentic loop: generate → judge → promote
              ─────────────│
           code diff    IaC output    LLM trace
              │              │            │
        LLM Guard        Checkov      Langfuse
        (output)         (gate)       → Grafana
              │              │
         SonarQube      DefectDojo
         (SAST)        (findings)
              │
        garak (red-team against the coding model)
```

## Stack

| Layer | Tool | Why |
|---|---|---|
| Input guard | LLM Guard API | prompt injection, PII, secret scanning on the way in |
| Agent | Ollama-hosted local model | fully sandboxed; pinned, reproducible |
| Loop | Agentic-Dev-Loop style orchestrator | generate → judge → promote |
| Output guard | LLM Guard | mask/block secrets & malicious code before commit |
| IaC gate | Checkov | fails agent-written Terraform/K8s/YAML in CI |
| SAST | SonarQube | code quality gate on generated diffs |
| Vuln mgmt | DefectDojo | aggregated finding ledger |
| Red team | garak | scans the coding model itself for injection vulnerabilities |
| Observability | Langfuse → Grafana | trace input-guard decisions + token spend |

## Quickstart

```bash
make up        # boot LLM Guard + garak worker
make demo      # run the secured loop against the local agent, emit findings
make report    # render reports/findings.md
make clean     # tear down
```

Each run pins its own identity (see Reproducible metrics) so every claim in the report
can be reproduced by anyone with the same manifest.

## Reproducible metrics (the honesty contract)

- **Model**: pinned tag + hash of the Ollama image (`MODEL` in `.env`).
- **Prompts**: every adversarial prompt is versioned under `prompts/` (not paste-in chat).
- **Guard configs**: LLM Guard scanners pinned to a commit.
- **Versions**: garak, Checkov, SonarQube, Langfuse versions recorded in the report manifest.
- **Seeds**: random seeds fixed for prompt generation.

## Findings

Featured before/after findings (filled from real runs):

- [ ] F1 — Secret in generated IaC: **blocked** by input Guard (diff evidence).
- [ ] F2 — Checkov gate on first agent commit: N findings, M auto-fixed in loop iteration 2.
- [ ] F3 — garak injection attempt success rate against the base model: X of Y succeeded.
- [ ] F4 — Langfuse trace: input-guard decision + tokens per loop iteration.

## Rules of the road

1. **No vendor claims** — everything is "my sandbox, my config, my model."
2. **No real credentials** — `.env.example` only; `.gitignore` protects yours.
3. **No working exploits at unknown risk** — any findings here are against my own host only.
4. **Verdicts, not vibes** — every claim links to a log line or screenshot.
5. See `SECURITY.md` for disclosure policy for this repo; report responsibly.

## License

MIT — see `LICENSE`.