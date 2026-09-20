#!/usr/bin/env python3
"""Export the latest run's trace.json to Langfuse.

Runs fully offline when no credentials are configured: the trace JSON is already a
faithful record and stays in the run's artifact dir for later import.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_demo import ROOT  # noqa: E402

REPORTS_DIR = ROOT / "reports"


def load_env_if_present() -> dict:
    env = {}
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"')
    return env


def main() -> None:
    runs = sorted((REPORTS_DIR / "artifacts").glob("*/trace.json"))
    if not runs:
        raise SystemExit("no run traces found — run `make demo` first")
    trace_path = runs[-1]
    run_id = trace_path.parent.name
    nodes = json.loads(trace_path.read_text()).get("nodes", [])
    print(f"trace: {trace_path.relative_to(ROOT)} ({len(nodes)} nodes)")

    cfg = {**load_env_if_present(), **os.environ}
    host = cfg.get("LANGFUSE_HOST") or cfg.get("LANGFUSE_BASEURL")
    pk = cfg.get("LANGFUSE_PUBLIC_KEY")
    sk = cfg.get("LANGFUSE_SECRET_KEY")
    if not (host and pk and sk):
        print("no Langfuse credentials (LANGFUSE_HOST/PUBLIC_KEY/SECRET_KEY); "
              "keeping local trace JSON — nothing sent")
        return

    from langfuse import Langfuse

    langfuse = Langfuse(public_key=pk, secret_key=sk, host=host)
    trace = langfuse.trace(name=f"ai-coding-fortress {run_id}")
    for n in nodes:
        output = {k: v for k, v in n.items() if k not in ("id", "stage")}
        trace.span(name=f"{n['id']}:{n['stage']}", output=output)
    langfuse.flush()
    print(f"exported {len(nodes)} spans for {run_id} to {host}")


if __name__ == "__main__":
    main()