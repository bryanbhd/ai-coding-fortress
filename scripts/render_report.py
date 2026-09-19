#!/usr/bin/env python3
"""Render findings JSON into a Markdown report (report target)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_demo import REPORTS_DIR  # noqa: E402


def latest_run() -> Path:
    runs = sorted(REPORTS_DIR.glob("findings-*.json"))
    if not runs:
        raise SystemExit("no findings yet — run `make demo` first")
    return runs[-1]


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else None
    path = Path(src) if src else latest_run()
    data = json.loads(path.read_text())

    m = data["manifest"]
    print(f"# Findings — {m['run_id']}\n")
    print(f"- model: `{m['model']}`")
    print(f"- date: {m['date']}\n")
    print(f"| iter | prompt | input_verdict | output_masked | checkov C/H | tokens |")
    print("|---|---|---|---|---|---|")
    for r in data["results"]:
        lvl = r["checkov_findings"]
        print(
            f"| {r['iter']} | {r['prompt_id']} | {r['input_verdict']} "
            f"| {r['output_masked']} | {lvl['critical']}/{lvl['high']} | {r['tokens']} |"
        )
    print(f"\n> Manifest note: `{data['note']}`")


if __name__ == "__main__":
    main()