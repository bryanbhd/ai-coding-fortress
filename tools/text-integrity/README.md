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

## Run in an ephemeral Incus OCI container

This option scans tracked text files in the current checkout using an
ephemeral Python OCI app container. The runner copies tracked files into the
container, so it also works when the Incus daemon is remote and cannot mount
the client's local checkout. No package installation or container network
access is needed at runtime. The host needs Incus, Git, Python 3, and a Docker
Hub OCI remote. The runner defaults to remote `docker`; set
`TEXT_INTEGRITY_OCI_REMOTE` to use another configured OCI remote.

Add the OCI remote once if it is not already configured:

```bash
incus remote add docker https://docker.io --protocol=oci
```

```bash
tools/text-integrity/run-incus.sh
tools/text-integrity/run-incus.sh --output /tmp/text-integrity-report.json
```

The script creates a uniquely named temporary instance and removes only that
instance. A HIGH-risk finding still returns a failing status; with `--output`,
the JSON report is copied to the requested host path even when the gate fails.
For routine CI use, prefer the existing GitHub Actions workflow, which runs
directly on the runner.

## CI gate

The GitHub Actions workflow runs the scanner directly with Python; it does not
need Docker. HIGH-risk Unicode tag characters and bidirectional controls fail
the check. MEDIUM/LOW signals are reported but do not fail it.

The report explicitly marks keyed model-level watermarks as
`UNVERIFIABLE_WITHOUT_PROVIDER_KEYS`. An absence of detected signals is not
evidence of human authorship.
