# The 4 Attack Surfaces of an AI Coding Loop

An AI coding assistant is an LLM with commit access. Securing it means treating each of
the four surfaces below as a separate threat model.

## 1. Input — the prompt is untrusted

Adversarial prompts arrive from anywhere: a README the agent reads, an issue a user
files, a package that got scraped. Injection can steer the agent past its instructions.

**Control:** LLM Guard at the boundary — reject or mask prompt-injection, PII, secrets.

## 2. Output — the code is untrusted

Generated code is indistinguishable from human-written unless you gate it. Secrets leak
in IaC, shell commands escalate, dependencies get typosquatted by the model itself.

**Control:** output guard + CI gates (SAST, IaC scan) with **auto-fix in the loop**, so
the agent repairs what it broke.

## 3. Supply chain — the model and tools are untrusted surfaces too

The assistant is a remoting dependency. Its own instruction-following can be exploited
(retrieval, RAG poisoning, memory injection). Red-team it — a coding model that folds on
`dan`-style probes shouldn't be given a merge button.

**Control:** garak red-team cadence on the model; pin versions; scan the toolchain.

## 4. Telemetry — the hard-won data can leak

Every guard decision, every trace, every token log is data about your code. Unencrypted
traces or PII in prompts can leak to observability backends.

**Control:** mask at the source, encrypt traces, keep observability in the sandbox.

## Takeaway

Guardrails do the work; gates verify the work; red-teaming validates the model; traces
prove it all happened. Skip one surface and the "secure" loop still has a hole.

*This is the framing behind the `ai-coding-fortress` lab.*