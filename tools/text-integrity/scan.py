#!/usr/bin/env python3
"""Scan tracked text files for hidden Unicode channels and C2PA text manifests."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from typing import Any


HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "upstream"))

import detect_text_watermark as detector  # noqa: E402
import provenance_core as core  # noqa: E402


TEXT_SUFFIXES = {
    ".bicep",
    ".c",
    ".cc",
    ".cfg",
    ".conf",
    ".cpp",
    ".cs",
    ".css",
    ".csv",
    ".dart",
    ".ex",
    ".exs",
    ".go",
    ".gql",
    ".graphql",
    ".h",
    ".hcl",
    ".hrl",
    ".htm",
    ".html",
    ".ini",
    ".ipynb",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".kts",
    ".less",
    ".lua",
    ".md",
    ".markdown",
    ".mdx",
    ".mjs",
    ".cjs",
    ".php",
    ".pl",
    ".proto",
    ".properties",
    ".ps1",
    ".psm1",
    ".py",
    ".pyi",
    ".r",
    ".rb",
    ".rst",
    ".rs",
    ".sass",
    ".scala",
    ".scss",
    ".sh",
    ".sql",
    ".svelte",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
    ".zsh",
}
TEXT_FILENAMES = {"dockerfile", "jenkinsfile", "makefile"}
DETECTORS = {"unicode-covert-channel", "c2pa-text-manifest"}


def _tracked_paths(
    root: pathlib.Path, tracked_list: pathlib.Path | None = None
) -> list[pathlib.Path]:
    if tracked_list is not None:
        paths = []
        for raw in tracked_list.read_bytes().split(b"\0"):
            if not raw:
                continue
            relative = pathlib.PurePosixPath(os.fsdecode(raw))
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError("tracked-path manifest contains an invalid path")
            paths.append(root.joinpath(*relative.parts))
        return paths

    result = subprocess.run(
        ["git", "-c", f"safe.directory={root}", "-C", str(root), "ls-files", "-z"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode:
        raise RuntimeError("could not enumerate tracked files with git ls-files")
    return [root / os.fsdecode(raw) for raw in result.stdout.split(b"\0") if raw]


def _is_text_candidate(path: pathlib.Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name.lower() in TEXT_FILENAMES


def _file_result(path: pathlib.Path, root: pathlib.Path) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        if path.is_symlink() or not resolved.is_file():
            return {"skipped": True}

        head = core.read_head(resolved)
        if not core.is_text_asset(resolved, head):
            return {"skipped": True}

        stream = core.read_text_stream(resolved)
        if not stream["scan_complete"]:
            return {"error": "file exceeds the detector's complete-scan limit"}

        channel_scan = core.scan_covert_channels(stream["text"])
        c2pa = detector.detector_c2pa_text(
            stream["text"], {"asset_path": str(resolved)}
        )
        return {
            "path": relative,
            "risk": channel_scan["risk"],
            "channels": [
                {
                    "channel": finding["channel"],
                    "codepoint": finding["codepoint"],
                    "severity": finding["severity"],
                    "count": finding["count"],
                }
                for finding in channel_scan["findings"]
            ],
            "c2pa_manifest": c2pa["state"] == detector.STATE_DETECTED,
        }
    except (OSError, ValueError, RuntimeError) as error:
        return {"path": relative, "error": type(error).__name__}


def scan_repository(
    root: pathlib.Path, tracked_list: pathlib.Path | None = None
) -> dict[str, Any]:
    root = root.resolve(strict=True)
    findings: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    scanned = 0
    skipped = 0

    for path in _tracked_paths(root, tracked_list):
        if not _is_text_candidate(path):
            skipped += 1
            continue
        result = _file_result(path, root)
        if result.get("skipped"):
            skipped += 1
        elif "error" in result:
            errors.append({"path": result["path"], "error": result["error"]})
        else:
            scanned += 1
            if result["channels"] or result["c2pa_manifest"]:
                findings.append(result)

    high_count = sum(
        1
        for item in findings
        for channel in item["channels"]
        if channel["severity"] == "HIGH"
    )
    return {
        "scanner": "detect-text-watermark",
        "source_commit": "0e8eb630b20f2b03ced0e77f3d650012a4ae48a1",
        "files_scanned": scanned,
        "files_skipped": skipped,
        "files_with_signals": findings,
        "high_risk_signal_count": high_count,
        "errors": errors,
        "keyed_model_watermarks": "UNVERIFIABLE_WITHOUT_PROVIDER_KEYS",
        "authorship_conclusion": "NOT_ASSESSED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument(
        "--tracked-list",
        type=pathlib.Path,
        help="NUL-separated tracked paths, for scans without a Git checkout",
    )
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--fail-high", action="store_true")
    args = parser.parse_args()

    try:
        report = scan_repository(args.root, args.tracked_list)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Watermark and Integrity Scanner failed: {type(error).__name__}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    print(
        "Watermark and Integrity Scanner: "
        f"{report['files_scanned']} tracked text files scanned, "
        f"{len(report['files_with_signals'])} file(s) with signals, "
        f"{report['high_risk_signal_count']} high-risk signal(s), "
        f"{len(report['errors'])} scan error(s)"
    )
    if report["errors"]:
        print("scan incomplete; see the JSON report for affected paths", file=sys.stderr)
        return 2
    if args.fail_high and report["high_risk_signal_count"]:
        print("text integrity gate failed on high-risk Unicode channels", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
