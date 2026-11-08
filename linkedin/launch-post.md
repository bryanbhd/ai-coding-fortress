# Launch Post Draft

> Target: ~200 words + a screenshot of the dashboard + repo link. Replace brackets.

I tested a guarded AI coding-agent generation loop, then red-teamed the underlying model —
all inside my own sandbox. The harness checks generated responses; it does not run an
autonomous agent with terminal or commit access.

What that loop looks like now:

→ Input guard (prompt injection / PII / secrets) at the boundary
→ The model generates responses; a Checkov gate checks Terraform output and requests one repair pass
→ Seen through, and fixed, in the same loop
→ Every decision recorded in a per-run trace — because "it's fine" isn't a security finding; evidence is

Eight adversarial prompts, baseline vs guarded, self-hosted model; saved reports document
this run, but reruns may produce different model output:

→ Three of 8 baseline outputs tripped a raw detector (a key shape, an attacker-controlled
  URL, and one known false-positive keyword hit) → 1 of 8 guarded outputs; excluding the
  false positive, the baseline had 2 substantive indicators
→ The input guard blocked 2 prompt-injection attempts outright and masked a seed key in 1
→ The URL case slipped through both arms in run one — so I added a URL blocklist and re-ran
  the prompt: blocked. The gap, the fix, and the re-run are all in the report
→ Pre-launch red-team: garak's DanInTheWild probe hit the raw model under a
  mitigation-bypass detector — 28.1% of 1280 judged output slices got through, which is
  why the guard sits before model responses reach downstream steps

I also had the model generate Terraform and ran it through Checkov: the gate refused to
evaluate the first draft (parse error on the model output) and still rejected it after one
repair round — no generated Terraform passed the gate.

Honest numbers, honest failures, local model, local config — nothing against any system but
this one. `make demo` reruns the harness, but the model tag is not an immutable digest and
the output is not guaranteed to match this report.

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