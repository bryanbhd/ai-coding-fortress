#!/usr/bin/env python3
"""Render the hardening re-run (URL block) into reports/hardening.md."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_demo import ROOT  # noqa: E402


def main() -> None:
    runs = sorted((ROOT / "reports").glob("findings-*.json"))
    data = json.loads(runs[-1].read_text())
    if len(data["results"]) != 1:
        raise SystemExit("last run is not a single-prompt hardening run; pass run file explicitly")
    m = data["manifest"]
    r = data["results"][0]

    base = r["baseline"]["hard_indicators"]
    gd = r["guarded"]["hard_indicators"]
    lines = [
        "# Hardening re-run — URL blocking\n",
        f"- **run** `{m['run']}` · **model** `{m['model']}` · **prompts**: `{r['id']}` ({r['angle']})",
        f"- **hardening**: output guard gained a sandbox-local URL blocklist: {', '.join(m.get('hardening', []) or [])}",
        "",
        f"`{r['id']}` baseline emitted `{', '.join(base) or '—'}`; guarded output: "
        f"**{', '.join(gd) or 'blocked'}** (`url_blocked={r['guarded']['output_guard']['url_blocked']}`).\n",
        "| prompt | baseline | guarded (hardened) | url_blocked |",
        "|---|---|---|---|",
        f"| {r['id']} | {', '.join(base) or '—'} | {', '.join(gd) or 'blocked'} | "
        f"{r['guarded']['output_guard']['url_blocked']} |",
        "",
        "> Note: llm-guard's `MaliciousURLs` output scanner needs a HuggingFace model download"
        " (and `aURL` for character-class checks) that is unreachable from this air-gapped run"
        " host, so this hardening is implemented as a local blocklist rule in the same guard"
        " position. Swapping it for `MaliciousURLs` at a connected site is a configuration "
        "change, not a code change.",
        "",
        f"> Manifest note: `{m['note']}`\n",
    ]
    target = ROOT / "reports" / "hardening.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[ok] rendered {target}")


if __name__ == "__main__":
    main()