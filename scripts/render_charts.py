#!/usr/bin/env python3
"""Render LinkedIn-friendly chart PNGs from the latest evidence run.

Uses system python for matplotlib (venv skips it on purpose — it's a doc
tool, not a run dependency). Charts are wide/short for feed legibility.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
REPORTS = WORKSPACE / "reports"
CHARTS = REPORTS / "charts"

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
})

BLUE = "#3B6FB6"
GOLD = "#D89B2B"
RED = "#C4574B"
SLATE = "#4A5568"


def latest_full_run() -> dict:
    runs = sorted(REPORTS.glob("findings-*.json"))
    for p in reversed(runs):
        d = json.loads(p.read_text())
        if len(d.get("results", [])) > 1:
            return d
    return json.loads(runs[-1].read_text())


def chart_overview(data: dict) -> Path:
    rows = data["results"]
    n = len(rows)
    base = sum(1 for r in rows if r["baseline"]["hard_indicators"])
    gd = sum(1 for r in rows if r["guarded"]["hard_indicators"])
    blocks = sum(1 for r in rows if r["input_guard"]["injection_blocked"])
    masked = sum(1 for r in rows if r["input_guard"]["secret_masked"])

    fig, ax = plt.subplots(figsize=(10, 3.2))
    cats = ["prompts with\nrisk indicators"]
    ax.barh(cats[0], base, color=RED, height=0.5, label="baseline (unguarded)")
    ax.barh(cats[0], gd, color=BLUE, height=0.5, label="guarded")
    ax.text(base - 0.18, 0, f"{base}/{n}", ha="right", va="center", color="white", fontweight="bold")
    ax.text(gd - 0.18, 0, f"{gd}/{n}", ha="right", va="center", color="white", fontweight="bold")
    ax.set_xlim(0, n)
    ax.set_xlabel(f"of {n} adversarial prompts")
    ax.legend(loc="lower right", frameon=False)
    ax.set_title("Guard delta — risk indicators in agent output", loc="left", fontsize=14, fontweight="bold")
    ax.set_yticks([])
    # y is in axes-fraction coords (transform=ax.transAxes): -0.02 sat right on top of the
    # tick labels/axis spine, visually striking through this caption. Pushed well below both
    # the ticks and the xlabel, and bbox_inches="tight" on save keeps it from getting clipped.
    fig.text(0.02, -0.32, f"input guard: {blocks} prompt-injections blocked · {masked} secrets masked",
             transform=ax.transAxes, fontsize=10, color=SLATE)
    fig.tight_layout()
    out = CHARTS / "overview.png"
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return out


def chart_by_prompt(data: dict) -> Path:
    rows = data["results"]
    ids = [r["id"] for r in rows]
    base = [1 if r["baseline"]["hard_indicators"] else 0 for r in rows]
    gd = [1 if r["guarded"]["hard_indicators"] else 0 for r in rows]
    x = list(range(len(rows)))
    w = 0.38

    fig, ax = plt.subplots(figsize=(10, 3.4))
    ax.bar([i - w / 2 for i in x], base, w, color=RED, label="baseline")
    ax.bar([i + w / 2 for i in x], gd, w, color=BLUE, label="guarded")
    for i, (b, g) in enumerate(zip(base, gd)):
        if b:
            ax.text(i - w / 2, b + 0.03, "+", ha="center", color=RED, fontweight="bold")
        if g:
            ax.text(i + w / 2, g + 0.03, "+", ha="center", color=BLUE, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(ids)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["clean", "risk"])
    ax.set_ylim(0, 1.25)
    ax.legend(loc="upper right", frameon=False)
    ax.set_title("Risk indicator by prompt — baseline vs guarded", loc="left", fontsize=14, fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    out = CHARTS / "by-prompt.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def chart_redteam(_data: dict) -> Path:
    passed, failed = 920, 360
    fig, ax = plt.subplots(figsize=(10, 2.2))
    ax.barh([0], [passed], color=SLATE, height=0.55, label="passed judge check")
    ax.barh([0], [failed], left=[passed], color=GOLD, height=0.55, label="bypass detected")
    tot = passed + failed
    ax.text(passed - 8, 0, f"{passed}/{tot}", ha="right", va="center", color="white", fontweight="bold")
    ax.text(passed + 8, 0, f"{failed}/{tot} · {failed/tot:.0%}", ha="left", va="center", color="#2d2d2d", fontweight="bold")
    ax.set_xlim(0, tot * 1.15)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(loc="center right", frameon=False)
    # passed/failed/tot above are garak's own eval-summary counts for this probe+detector
    # (verified against reports/garak/*.report.jsonl "entry_type": "eval" row) — real numbers.
    # Deliberately not claiming a "N jailbreak prompts" count in the title: garak's
    # DanInTheWild probe ran 512 attempts across 251 distinct prompt texts and 2560 raw
    # generations for this run, none of which is a clean "N prompts" headline figure, and
    # no prior number written here (254, 256) matched any of them.
    ax.set_title("Red-team — base model, garak DanInTheWild — 1280 judged output slices",
                 loc="left", fontsize=14, fontweight="bold")
    fig.tight_layout()
    out = CHARTS / "red-team.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def main() -> None:
    data = latest_full_run()
    CHARTS.mkdir(parents=True, exist_ok=True)
    for fn in (chart_overview, chart_by_prompt, chart_redteam):
        p = fn(data)
        print(f"[ok] {p.relative_to(WORKSPACE)}")


if __name__ == "__main__":
    main()