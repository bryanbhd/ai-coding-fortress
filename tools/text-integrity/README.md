# Text integrity and provenance scan

This tool packages the upstream `detect-text-watermark` skill to scan tracked
text/source files for hidden Unicode channels and C2PA text-manifest indicators.
It does **not** establish whether content was AI-generated or detect a keyed
model watermark.

The upstream detector scripts are vendored from
[`neeeophytee/ai-watermarks-reality-check`](https://github.com/neeeophytee/ai-watermarks-reality-check)
at commit `0e8eb630b20f2b03ced0e77f3d650012a4ae48a1`. They are licensed under
AGPL-3.0; see `upstream/LICENSE`. The report contains paths and signal metadata
only, never matched text or the hidden character itself.

## Run locally

With Python 3.11+:

```bash
python3 tools/text-integrity/scan.py --root . --fail-high
python3 -m unittest discover -s tools/text-integrity/tests -v
```

Or build and run the isolated container from the repository root:

```bash
docker build -f tools/text-integrity/Dockerfile -t text-integrity .
docker run --rm --read-only --user "$(id -u):$(id -g)" \
  -v "$PWD:/workspace:ro" text-integrity --root /workspace --fail-high
```

The container runs as an unprivileged user, needs no network access at runtime,
and mounts the checkout read-only. Add `--output /path/report.json` to save a
JSON report. Scan errors always return a nonzero status.

## CI gate

The GitHub Actions workflow runs the scanner directly with Python; it does not
need Docker. HIGH-risk Unicode tag characters and bidirectional controls fail
the check. MEDIUM/LOW signals are reported but do not fail it.

The report explicitly marks keyed model-level watermarks as
`UNVERIFIABLE_WITHOUT_PROVIDER_KEYS`. An absence of detected signals is not
evidence of human authorship.
