#!/usr/bin/env python3
"""AI Coding Fortress demo driver.

Runs the secured agent loop entirely against sandbox services and emits a findings
report into reports/. Skeleton: service wiring is marked TODO and filled as the lab
services are brought up.

Everything here runs against self-hosted services only.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


@dataclass
class RunManifest:
    model: str = os.getenv("OLLAMA_MODEL", "<pin-model-tag-here>")
    run_id: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
    guard_url: str = os.getenv("LLM_GUARD_URL", "http://localhost:8000")
    versions: dict = field(default_factory=dict)


def check_guard_up(url: str) -> tuple[bool, int]:
    """TODO: probe LLM Guard health endpoint once services are pinned."""
    return False, 0


def scan_prompt(prompt: str) -> dict:
    """TODO: POST /analyze to LLM Guard; return verdict JSON from the sandbox."""
    return {"sampled": prompt, "verdict": None, "masked_output": None}


def run_guard_loop(manifest: RunManifest, count: int = 12) -> list[dict]:
    """Run the protected loop against synthetic adversarial prompts."""
    results = []
    for i in range(count):
        results.append(
            {
                "iter": i,
                "prompt_id": f"P1-{i:02d}",
                "input_verdict": None,  # TODO from scan_prompt()
                "output_masked": False,  # TODO from agent + output guard
                "checkov_findings": {"critical": 0, "high": 0},  # TODO from CI gate
                "tokens": None,  # TODO from Langfuse trace
            }
        )
    return results


def write_report(manifest: RunManifest, results: list[dict]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"findings-{manifest.run_id}.json"
    payload = {
        "manifest": {
            "model": manifest.model,
            "guard_url": manifest.guard_url,
            "versions": manifest.versions,
            "run_id": manifest.run_id,
            "date": datetime.now(timezone.utc).isoformat(),
        },
        "results": results,
        "note": "See reports/FINDINGS_TEMPLATE.md for the human-readable shape.",
    }
    out.write_text(json.dumps(payload, indent=2))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the AI coding fortress demo loop.")
    ap.add_argument("--it", type=int, default=12, help="number of loop iterations")
    args = ap.parse_args()

    manifest = RunManifest()
    up, code = check_guard_up(manifest.guard_url)
    if not up:
        print(f"[warn] LLM Guard not reachable at {manifest.guard_url} (last code={code}); "
              "results will be placeholders. Run `make up` first.")

    results = run_guard_loop(manifest, args.it)
    out = write_report(manifest, results)
    print(f"[ok] run {manifest.run_id} -> {out}")


if __name__ == "__main__":
    main()