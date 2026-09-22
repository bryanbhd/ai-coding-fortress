# AI Coding Fortress

A **reproducible lab** that secures an AI coding loop — an autonomous agent that writes
and ships code, wrapped in input/output guards, CI security gates, observability, and a
red-team harness. Every attack in this repo is run **against models and services I host
myself, in my own sandbox.** No third-party systems are touched.

The output is a verifiable findings report you can attach to anything you publish.

**Read the full write-up:** [linkedin/article.md](linkedin/article.md) — charts, the guard-delta
numbers, the garak red-team results, and the gap-fix-re-run story in one place.

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

Featured before/after findings, from real runs (full detail in `reports/findings.md` and
`reports/garak-summary.md`):

- [x] F1 — Secret in generated context: input guard **masked** it (P1-02, `aws-key` shape);
      2 prompt-injection attempts **blocked** outright (P1-01, P1-05).
- [x] F2 — Checkov gate on agent-written Terraform (P1-06): refused to evaluate on the first
      draft (parse error, `resource_count=0`) and still failed to parse after one repair
      round — no plan was ever approved.
- [x] F3 — garak (`dan.DanInTheWild`, base model, no guard): **360 of 1280** judged slices
      bypassed the mitigation-bypass detector — **28.1%** attack success rate on the untreated
      model. This is why the guard sits upstream of the agent, not after it.
- [x] F4 — Guard delta across all 8 prompts: baseline agent showed a hard risk indicator in
      **3/8** outputs; guarded agent in **1/8**. The one residual case (P1-07, malicious URL)
      was closed with a URL-blocklist hardening pass and a targeted re-run — gap, fix, and
      re-run are all recorded in `reports/hardening.md`.

## Rules of the road

1. **No vendor claims** — everything is "my sandbox, my config, my model."
2. **No real credentials** — `.env.example` only; `.gitignore` protects yours.
3. **No working exploits at unknown risk** — any findings here are against my own host only.
4. **Verdicts, not vibes** — every claim links to a log line or screenshot.
5. See `SECURITY.md` for disclosure policy for this repo; report responsibly.

## License

MIT — see `LICENSE`.