#!/bin/sh
set -eu

usage() {
    printf 'Usage: %s [--output REPORT.json]\n' "$0" >&2
}

report_output=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --output)
            [ "$#" -ge 2 ] || { usage; exit 2; }
            report_output=$2
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage
            exit 2
            ;;
    esac
done

command -v incus >/dev/null 2>&1 || {
    printf 'Incus CLI is required\n' >&2
    exit 2
}
command -v git >/dev/null 2>&1 || {
    printf 'Git is required on the host\n' >&2
    exit 2
}

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
instance="text-integrity-$$-$(date +%s)"
container_report=/tmp/text-integrity-report.json
instance_created=0

cleanup() {
    status=$?
    trap - EXIT
    if [ "$instance_created" -eq 1 ] && incus info "$instance" >/dev/null 2>&1; then
        if ! incus delete --force "$instance"; then
            printf 'Failed to remove temporary Incus instance: %s\n' "$instance" >&2
            status=1
        fi
    fi
    exit "$status"
}
trap cleanup EXIT

incus init images:debian/12 "$instance" --ephemeral
instance_created=1
incus config device add "$instance" checkout disk \
    source="$repo_root" path=/workspace readonly=true
incus start "$instance"

incus exec "$instance" -- sh -ec '
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 git ca-certificates
' </dev/null

set +e
if [ -n "$report_output" ]; then
    incus exec "$instance" -- python3 /workspace/tools/text-integrity/scan.py \
        --root /workspace --fail-high --output "$container_report" </dev/null
    scan_status=$?
    report_dir=$(dirname -- "$report_output")
    mkdir -p "$report_dir"
    incus file pull "$instance$container_report" "$report_output"
    pull_status=$?
    if [ "$pull_status" -ne 0 ]; then
        exit "$pull_status"
    fi
else
    incus exec "$instance" -- python3 /workspace/tools/text-integrity/scan.py \
        --root /workspace --fail-high </dev/null
    scan_status=$?
fi
set -e

exit "$scan_status"
