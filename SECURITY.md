# Security Policy

## Scope

This repository is an educational sandbox lab. It intentionally contains adversarial
prompts and code that is harmful **only against models and services hosted by the owner
inside this sandbox.** Nothing here should be pointed at systems you do not control.

## Reporting a vulnerability

If you find a flaw in this lab itself (a config that would leak secrets, a bad gate, an
unsafe default), please report it **privately** first:

- Open a security advisory on GitHub (do not file a public issue).
- Include the affected file, a minimal repro, and impact.

Timeline expectation: acknowledgement within 5 business days; coordinated disclosure
after a fix or 30 days, whichever is first.

## Safe use

- Run only against your own host (or authorized targets).
- Do not use adversarial prompts on models that host third-party data.
- Redact anything that looks like a real credential immediately.

## Pre-publish checklist

Applied to **anything** that leaves this sandbox (repo, posts, published reports). Originals
stay in the sandbox; only scrubbed copies get published.

1. Keep original artifacts (garak runs, findings JSON, trace.json) intact locally for
   reproduction — never destroy them.
2. Redact before publishing:
   - Keys/tokens: AWS-style IDs, JWTs, bearer tokens, `pk-`/`sk-` prefixes, passwords
   - Infrastructure: IPs, MACs, internal hostnames, `/home/<user>` paths
   - Identifiers: real usernames, client names, contact details
3. Preserve the evidence that matters: verdicts, counts, timings, versions.
4. Run a secret scan over the final tree: `make publish-check` (gitleaks or trufflehog).
5. Note in each report manifest: *"Identifiers redacted; verdicts/metrics unchanged."*

## README badges / citation

If you reuse findings from this lab, cite the run manifest (model, versions, prompts,
seeds) so results remain reproducible.