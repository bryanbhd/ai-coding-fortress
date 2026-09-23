# The 4 Attack Surfaces of an AI Coding Loop

An AI coding assistant is an LLM with commit access. Securing it means treating each of
the four surfaces below as a separate threat model.

## 1. Input — the prompt is untrusted

Adversarial prompts arrive from anywhere: a README the agent reads, an issue a user
files, a package that got scraped. Injection can steer the agent past its instructions.

**Control:** LLM Guard at the boundary — reject prompt-injection, mask secrets. (PII/
sensitive-data detection sits on the *output* side in this lab, not here — see #2.)

## 2. Output — the code is untrusted

Generated code is indistinguishable from human-written unless you gate it. Secrets leak
in IaC, shell commands escalate, dependencies get typosquatted by the model itself.

**Control:** output guard + an IaC policy gate (Checkov), with one repair attempt when a
plan fails. Not SAST — that isn't part of this lab. And "repair attempt" is the honest
phrase, not "auto-fix": in this lab's own run, the repair round still didn't produce a
passing plan (finding F2) — the gate refusing a bad "fix" instead of rubber-stamping it
is the actual point, not a defect.

## 3. Supply chain — the model and tools are untrusted surfaces too

The assistant is a remoting dependency. Its own instruction-following can be exploited
(retrieval, RAG poisoning, memory injection). Red-team it — a coding model that folds on
`dan`-style probes shouldn't be given a merge button.

**Control:** red-team the model with garak (this lab ran one pass; a real deployment
would repeat it on every model swap) and pin versions.

## 4. Telemetry — the hard-won data can leak

Every guard decision, every trace, every token log is data about your code. Unencrypted
traces or PII in prompts can leak to observability backends.

**Control:** mask at the source, and keep observability in your own sandbox rather than
a third-party backend.

## Takeaway

Guardrails do the work; gates verify the work; red-teaming validates the model; traces
prove it all happened. Skip one surface and the "secure" loop still has a hole.

*This is the framing behind the `ai-coding-fortress` lab.*