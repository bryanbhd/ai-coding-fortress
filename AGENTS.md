# AGENTS.md — ai-coding-fortress

Instructions for AI coding agents (Codex, Claude Code, Copilot, Cursor, Gemini CLI, opencode,
local agents) working on this repo. `AGENTS.md` is the open standard most of them read
([agents.md](https://agents.md/)); `CLAUDE.md` and `.gemini/settings.json` point the other two here.

This file is the lab's **policy layer**: the guards and gates in the README control what the
model says and ships, and these rules control what a coding agent is allowed to *do*. The project
facts are in this top part. The shared rules at the bottom are one baseline kept in sync across
all of the author's repos, and each comes from a real incident.

## Project
- **What it is:** a reproducible lab that secures an AI coding loop: llm-guard input/output
  guards, a Checkov IaC gate with one repair round, garak red-teaming, a findings report.
- **Setup:** `make setup` (venv + pinned deps from `requirements.txt`).
- **Run:** `make demo` (secured agent loop) → `make report` (findings + hardening re-run) →
  `make charts`. Optional: `make up` (hosted llm-guard), `make trace-export` (Langfuse, only if
  credentials are set in `.env`).
- **Before anything is published:** `make publish-check` (gitleaks / trufflehog) and the
  pre-publish checklist in `SECURITY.md`.

## Project-specific rules
- **Attacks run only against models and services the owner hosts.** Never point prompts in
  `prompts/`, garak probes or any red-team step at a third-party model, API or system.
- **Never weaken a guard or gate to make a run pass.** A blocked prompt or a failed Checkov run
  is a finding to record, not an error to work around. Don't auto-promote failed IaC.
- **Claims match evidence.** The README and `linkedin/` say only what a run in `reports/`
  shows. If a tool isn't actually integrated, it isn't claimed (see the README's scope note).
- **`.env` holds credentials and never leaves the machine.** It is gitignored; `.env.example`
  documents the variable names only. Read credentials from the environment, never print them.
- **Agent instruction files are reviewed like code.** `AGENTS.md`, `CLAUDE.md` and `.gemini/`
  steer every agent that works here, so an edit to them is a prompt-injection route. They're
  listed in `.github/CODEOWNERS`; never weaken or remove a rule here as a side effect of
  another change.
- **Reports are published artifacts.** Before committing anything under `reports/` or
  `linkedin/`, check it for hostnames, IPs, internal paths and secrets.

<!-- BEGIN agent-standards:baseline v=2ebff75804 - managed by agent-standards; edit baseline.md there and run `agentstd sync`, not this block -->
## Shared rules (all agents, all projects)

These rules come from real incidents: an agent once took a one-word reply as approval,
its backup attempt failed, and it wiped a secrets store anyway; a later sweep found live
passwords in unit files, `.env` files, container config and process arguments.

### Destructive actions — hard rules
1. **Explicit yes to the exact action.** Before deleting, wiping, re-initialising,
   force-pushing, dropping or overwriting anything stateful, state the exact command and
   what will be lost, then wait for an unambiguous "yes" to *that* command. A vague,
   one-word or frustrated reply is **not** approval — ask again.
2. **Safety net first, or stop.** Take a snapshot/backup before the destructive step. If it
   fails, **stop and report** — never proceed without it. Check that the snapshot actually
   covers the data (separate volumes are often not in a container snapshot).
3. **Move aside, don't delete.** Prefer `mv x x.bak-<date>` over `rm -rf`.
4. **Never wipe or re-initialise a secrets store or identity system.** Lost access means
   asking the owner to unseal / recover — not starting over.
5. **"Blocked" is an answer.** If you lack access or permission, say what is blocked and
   what the user can do. Don't find a workaround that destroys state or bypasses a control.

### Secrets
1. **Secrets live in the secret store** (e.g. Vault) and services read them at start. Never
   put a secret in a repo file, `.env`, unit file, compose file, container config, chat,
   log or command-line argument.
2. **Never display secret values**, even while debugging: print variable *names* only and
   compare secrets by hash or equality. Never ask the user to paste a secret into chat —
   have them run the command, or read it from a file inside the command.
3. **Pass secrets via stdin or files, never argv** — argv is readable by every process
   (`/proc/<pid>/cmdline`, `ps`). With curl:
   - body: `--data @<(printf '{"secret_id":"%s"}' "$SID")` or `--data @-`
   - headers: `-K <(printf 'header = "Authorization: Bearer %s"\n' "$TOKEN")`
   - CI secret variables: map them through the step's `env:`; never inline a secret
     variable macro (e.g. `$(SECRET)`) into script text.
4. **Rotating = change the store, restart the consumer.** If a rotation needs editing files
   on the consumer, wire the consumer to the store first.

### Git and publishing
- **Stage files by name.** Never `git add -A` / `git add .` — working trees hold private
  drafts. Never force-push or rewrite shared history without rule 1 of Destructive actions.
- **Public repos: every commit is publishing.** No internal hostnames, IPs, subnets,
  instance names, secret-store paths, employer-identifying details, or job-application
  material. Run the repo's pre-publish/security checks before pushing.
- Keep commits scoped to the request; never commit `.env` or credentials, even "temporarily".

### Working style
- Read only what the task needs; ignore `node_modules`, `dist`, `build`, `target`, `.git`,
  virtualenvs. Prefer the project's own scripts over new toolchains.
- Match existing style, layout and naming. Keep changes scoped; preserve public interfaces
  unless asked to break them.
- Validate external input; no SQL/command injection. Never disable auth, TLS verification
  or sandboxing for convenience — fix the trust chain instead.
- Report outcomes faithfully: say what was verified and how, and say plainly when something
  failed or was skipped.
- After changes, summarize the paths changed and how to verify them.
<!-- END agent-standards:baseline -->
