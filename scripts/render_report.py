#!/usr/bin/env python3
"""Render findings JSON into a Markdown report (findings.md).

Annotations are re-derived from the stored artifacts at render time so that
the report reflects the actual gate output (avoids stale/misread summaries).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_demo import ROOT  # noqa: E402

REPORTS_DIR = ROOT / "reports"
CHECKOV = ROOT / ".venv" / "bin" / "checkov"


def latest_run() -> Path:
    runs = sorted(REPORTS_DIR.glob("findings-*.json"))
    if not runs:
        raise SystemExit("no findings yet — run `make demo` first")
    for p in reversed(runs):
        data = json.loads(p.read_text())
        if len(data.get("results", [])) > 1:
            return p
    return runs[-1]


def checkov_on(path: Path) -> dict:
    cp = subprocess.run(
        [str(CHECKOV), "-f", str(path), "--output", "json", "--quiet"],
        capture_output=True, text=True, timeout=300,
    )
    if cp.returncode not in (0, 1):
        return {"error": cp.stderr.strip()[:200]}
    try:
        data = json.loads(cp.stdout)
    except json.JSONDecodeError:
        return {"error": "unparseable checkov output"}
    results = data.get("results", {})
    failed = results.get("failed_checks", [])
    return {
        "failed": len(failed),
        "check_ids": sorted({f["check_id"] for f in failed}),
        "passed": data.get("summary", {}).get("passed", 0),
        "parsing_errors": data.get("summary", {}).get("parsing_errors", 0),
        "resource_count": data.get("summary", {}).get("resource_count", 0),
    }


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else None
    path = Path(src) if src else latest_run()
    data = json.loads(path.read_text())

    m = data["manifest"]
    rows = data["results"]
    sum_base = sum(1 for r in rows if r["baseline"]["hard_indicators"])
    sum_gd = sum(1 for r in rows if r["guarded"]["hard_indicators"])
    sum_blocked = sum(1 for r in rows if r["input_guard"]["injection_blocked"])
    sum_masked = sum(1 for r in rows if r["input_guard"]["secret_masked"])

    out = ["# Findings — AI Coding Agent Guard Evaluation\n"]
    out.append(f"- **run** `{m['run']}` · **model** `{m['model']}` · **date** {m['date']}")
    g = m.get("guard", {})
    c = m.get("checks", {})
    out.append(f"- **guard** llm-guard {g.get('version') or 'n/a'} (input: PromptInjection, Secrets; output: Sensitive)")
    out.append(f"- **IaC gate** checkov {c.get('checkov') or 'n/a'} · **prompt set** `{m.get('prompt_set')}`")
    out.append("")
    out.append(f"## Summary")
    out.append("")
    out.append(f"- {len(rows)} adversarial prompts run against both a **baseline** (unguarded) agent and the **guarded** agent")
    out.append(f"- baseline emitted a hard indicator in **{sum_base}/{len(rows)}** outputs; guarded agent in **{sum_gd}/{len(rows)}**")
    out.append(f"- input guard **blocked** {sum_blocked} prompt-injection attempts and **masked** secrets in {sum_masked} prompts")
    out.append("")
    out.append("| prompt | angle | input guard | baseline | guarded | out-mask |")
    out.append("|---|---|---|---|---|---|")
    for r in rows:
        ing = r["input_guard"]
        iv = "blocked" if ing["injection_blocked"] else ("masked" if ing["secret_masked"] else "clean")
        b = r["baseline"]["hard_indicators"] or "—"
        gd = r["guarded"]["hard_indicators"] or "—"
        om = "masked" if r["guarded"]["output_guard"]["masked"] else "—"
        out.append(f"| {r['id']} | {r['angle'].replace('-', ' ')} | {iv} | {','.join(b) if isinstance(b, list) else b} | "
                   f"{','.join(gd) if isinstance(gd, list) else gd} | {om} |")
    out.append("")

    iac = [r for r in rows if r.get("checkov")]
    if iac:
        out.append("## IaC gate (checkov P1-06 fix-loop)\n")
        for r in iac:
            art = Path(m["artifacts_dir"])
            tf1 = ROOT / art / f"{r['id']}-generated.tf"
            tf2 = ROOT / art / f"{r['id']}-iter2.tf"
            c1 = checkov_on(tf1) if tf1.exists() else r["checkov"].get("iteration1", {})
            out.append(f"### {r['id']} — `{r['angle']}`")
            out.append(f"- iteration 1 (draft): failed={c1.get('failed')} · passed={c1.get('passed')} · "
                       f"parsing_errors={c1.get('parsing_errors')} · resource_count={c1.get('resource_count')}")
            if c1.get("check_ids"):
                out.append(f"  - policy failures: {', '.join(c1['check_ids'])}")
            c2 = checkov_on(tf2) if tf2.exists() else r["checkov"].get("iteration2")
            if c2 is not None:
                out.append(f"- iteration 2 (after feedback): failed={c2.get('failed')} · passed={c2.get('passed')} · "
                           f"parsing_errors={c2.get('parsing_errors')}")
                if c2.get("check_ids"):
                    out.append(f"  - policy failures: {', '.join(c2['check_ids'])}")
            out.append("")
    else:
        out.append("## IaC gate (checkov fix-loop)\n")
        out.append("no run produced an insecure-iac row with a guard-cleared output; loop skipped.\n")

    residual = [r for r in rows
                if r["baseline"]["hard_indicators"] and r["baseline"]["hard_indicators"] == r["guarded"]["hard_indicators"]]
    if residual:
        out.append("## Residual risks (guard did not change the outcome)\n")
        out.append("These cases keep their risky indicator in both arms; the output guard does not cover them. "
                   "They are surfaced here deliberately — guards are not a silver bullet, and this is upstream of any policy gate:\n")
        out.append("| prompt | angle | indicator |")
        out.append("|---|---|---|")
        for r in residual:
            out.append(f"| {r['id']} | {r['angle'].replace('-', ' ')} | {', '.join(r['guarded']['hard_indicators'])} |")
        out.append("")
        out.append("Hardening path: add URL/reputation scanning (e.g. llm-guard `MaliciousURLs`) to the output guard, "
                   "then re-run only the affected row.\n")

    out.append("## Method & disclosure")
    out.append("")
    out.append(f"> {m.get('note', '')}" if m.get("note", "") else "> —")
    out.append("> Model runs on a self-hosted local Ollama instance inside an isolated sandbox; the findings "
               "are a demonstration of guard-through-gate behavior, not a vendor benchmark. Identifiers in the "
               "prompts are fabricated examples.")

    out.append("")
    out.append("## Adjoining artifacts")
    out.append("")
    out.append("- **Red-team (base model):** `reports/garak-summary.md` — `dan.DanInTheWild` against the raw "
               "model, 28.1% mitigation-bypass success on 1280 slices (garak 0.17, seed 42); the guard delta is "
               "what the rows above measure.")
    out.append("- **Hardening re-run:** `reports/hardening.md` — the P1-07 residual case re-run with the URL "
               "blocklist active (run `make demo -- --ids P1-07` then `make report`).")
    out.append(f"- **Trace:** `{m.get('artifacts_dir')}/trace.json`; export to Langfuse via `make trace-export` "
               "(needs `LANGFUSE_HOST/PUBLIC_KEY/SECRET_KEY`, else it stays local).")

    target = REPORTS_DIR / "findings.md"
    target.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"[ok] rendered {target} ({len(out)} lines)")


if __name__ == "__main__":
    main()