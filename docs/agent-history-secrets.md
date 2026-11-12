# I went into the sandbox blind. My AI agents were keeping my secrets.

By Bryan Debnam · [LinkedIn](https://www.linkedin.com/in/bryanhd)

I went into the sandbox blind, the way I believe many people start off their AI journey.

This comes from my home R&D fleet, a set of self-hosted machines where I test AI tooling before trusting it
anywhere else. The numbers are from one machine in it. No hostnames, paths or secret values appear here.

This IBM Technology video helped me understand what was going on. It covers the four types of memory AI agents
use: working, semantic, procedural and episodic [7]. Episodic memory, the record of what happened, is the one
this post is about.

Agents keep transcripts, tool output, chat databases and memory notes: a record of every command and every file
printed. A token shown once while debugging stays in that record. It is cleartext storage [1] and a
secrets-in-logs problem [2] in a new place.

## Two places to catch it

| | In the IDE | At deployment |
|---|---|---|
| Where | The machine where the agent runs | Where code ships |
| Stops the leak | At its source | At the gate |
| Flow | Agent runs a command that prints a token → transcript and chat database store it on local disk → history scanner flags it (counts only, never values) → a scrubbed copy replaces the original, backup first | Commit leaves the IDE through a pre-commit hook → SecDevOps pipeline gate (secret scan, SAST, IaC and image scans, argv-secret check) → any finding fails the build → deploy reads secrets from the vault at start |

The IDE side covers what an agent remembers. SecDevOps covers what a repo ships. Neither replaces the other.

## What I found

| 284 | 61 | 22 | 119 |
|---|---|---|---|
| history files scanned | file/pattern pairs flagged | testable values, all dead | memory notes, all clean |

The scan covered five tools: Claude Code, OpenCode, Codex, VS Code chat and Ollama. It prints counts only, because
an early version that printed matches copied the secrets into the transcript. The notes an agent writes on purpose
were clean. The raw transcripts were not. The counts are from before the cleanup.

Vault tokens (`lookup-self` [3]) and GitHub tokens (`GET /user`) can be tested safely. All 22 were dead, and a
control with a known-valid token showed the check works.

Other kinds of secret, such as cloud key IDs and passwords inside URLs, can't be tested this way. For those the fix is rotation, not testing.

**Update:** I then looked at the other kinds. The one cloud key ID was the vendor's own documentation example, not a real credential. The two AppRole secret IDs were already gone when I checked them against Vault. Passwords inside URLs are still untested: most were placeholders, and the rest sit on my own internal hosts.

## Cleaning it safely

1. **Stage scrubbed copies.** Each secret becomes `[REDACTED:<fingerprint>]`, a keyed hash. Originals are untouched.
2. **Back up, verify hashes, then swap** one file at a time. Nothing is deleted.
3. **Skip live files** until the session ends.
4. **Databases:** edit through SQLite, then `VACUUM` with `secure_delete` on [4][5].

I made mistakes on the way: a pattern that broke JSON files, a redaction marker the scanner flagged as a secret,
and calling 18 values "real by shape" before testing them. Shape tells you what to test, not what is live.

A scrub does not recall anything already sent to a model provider. Rotate what is live.

## Takeaways

- Treat agent history as a store that holds secrets.
- Print names and counts, never values.
- Test liveness first, and say what you could not test.
- Scrub copies, verify, back up, then swap.

The scanner and the history tools are open source [6].

## Sources

1. CWE-312: Cleartext Storage of Sensitive Information. <https://cwe.mitre.org/data/definitions/312.html>
2. CWE-532: Insertion of Sensitive Information into Log File. <https://cwe.mitre.org/data/definitions/532.html>
3. HashiCorp Vault, Token auth method API. <https://developer.hashicorp.com/vault/api-docs/auth/token>
4. SQLite VACUUM. <https://www.sqlite.org/lang_vacuum.html>
5. SQLite PRAGMA statements (`secure_delete`). <https://www.sqlite.org/pragma.html>
6. check-argv-secrets. <https://github.com/bryanbhd/check-argv-secrets>
7. IBM Technology (Martin Keen), The Four Types of Memory Every AI Agent Needs. <https://www.youtube.com/watch?v=BacJ6sEhqMo>. More on agents: <https://www.ibm.com/think/topics/ai-agents>
