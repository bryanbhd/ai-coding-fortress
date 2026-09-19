# Launch Post Draft

> Target: ~200 words + a screenshot of the dashboard + repo link. Replace brackets.

I gave an AI coding agent *commit access*. Then I hardened the pipeline it ships through,
and red-teamed the agent itself — all inside my own sandbox.

What that loop looks like now:

→ Input guard (prompt injection / PII / secrets) at the boundary
→ The agent generates, a judge reviews, a CI gate (Checkov + SonarQube) rejects bad output
→ Seen through, and fixed, in the same loop
→ The model red-teamed with garak before it gets a merge button
→ Every decision traced in Langfuse — because "it's fine" isn't a security finding; evidence is

The results so far: [insert F1–F3 numbers, e.g. "a prompt that made the unguarded agent
emit a secret-shaped key is masked by the guard; the agent's first commit was rejected by
Checkov and repaired in the next iteration; garak found X of Y injection attempts
succeeded against my base model"].

None of this is against any company's systems. It's my machine, my model, my config — and
it's all reproducible from a pinned manifest.

This is exactly the kind of "show, don't tell" footing AI-coding security needs.

Repo: [link] — `make demo` reproduces the whole report.
Open to feedback and challenges from the security crowd.

#<hashtags>

---

### Draft 2 (Alternative hook — threat-model focus)
[Optional shorter version if Draft 1 feels long.]

---

### Follow-up article plan (ANCHORED repo docs)
1. *Four attack surfaces of an AI coding loop* → `docs/attack-surfaces.md`
2. *What garak actually found on my own agent* → findings F3 + garak report
3. *Gates that fix, not just detect* → findings F2 + Checkov log