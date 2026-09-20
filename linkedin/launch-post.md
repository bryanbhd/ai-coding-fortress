# Launch Post Draft

> Target: ~200 words + a screenshot of the dashboard + repo link. Replace brackets.

I gave an AI coding agent *commit access*. Then I hardened the pipeline it ships through,
and red-teamed the agent itself — all inside my own sandbox.

What that loop looks like now:

→ Input guard (prompt injection / PII / secrets) at the boundary
→ The agent generates, a judge reviews, a CI gate (Checkov + SonarQube) rejects bad output
→ Seen through, and fixed, in the same loop
→ Every decision traced in Langfuse — because "it's fine" isn't a security finding; evidence is

Eight adversarial prompts, baseline vs guarded, self-hosted model, all reproducible:

→ Three of 8 unsafe outputs from the unguarded agent (a leaked key shape, a committed .env
  secret, an attacker-controlled URL) → 1 of 8 behind the guard
→ The input guard blocked 2 prompt-injection attempts outright and masked a seed key in 1
→ The URL case slipped through both arms in run one — so I added a URL blocklist and re-ran
  the prompt: blocked. The gap, the fix, and the re-run are all in the report
→ Pre-launch red-team: garak threw 256 jailbreak prompts at the raw model under a
  mitigation-bypass detector and 28.1% of slices got through — which is why the guard
  sits before the agent, not after the damage

I also let the agent write Terraform and ran it through Checkov: the gate refused to
evaluate the first draft (parse error on the model output) and still rejected it after one
repair round — no plan got approved without passing the gate.

Honest numbers, honest failures, local model, local config — nothing against any system but
this one, and `make demo` reproduces the whole report from a pinned manifest.

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