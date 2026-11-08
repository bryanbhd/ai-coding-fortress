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
command -v python3 >/dev/null 2>&1 || {
    printf 'Python 3 is required on the host to prepare the tracked-path manifest\n' >&2
    exit 2
}

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
oci_remote=${TEXT_INTEGRITY_OCI_REMOTE:-docker}
instance="text-integrity-$$-$(date +%s)"
container_report=/tmp/text-integrity-report.json
tracked_paths=$(mktemp "${TMPDIR:-/tmp}/text-integrity-paths.XXXXXX")
source_archive=$(mktemp "${TMPDIR:-/tmp}/text-integrity-source.XXXXXX.tar")
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
    rm -f "$tracked_paths" "$source_archive"
    exit "$status"
}
trap cleanup EXIT

git -C "$repo_root" ls-files -z >"$tracked_paths"
tar -C "$repo_root" -cf "$source_archive" --null -T "$tracked_paths"

incus init "$oci_remote:python:3.11-slim" "$instance" --ephemeral
instance_created=1
incus config set "$instance" "oci.entrypoint=/bin/sh -c 'sleep infinity'"
incus start "$instance"

incus file push "$source_archive" "$instance/tmp/text-integrity-source.tar"
incus file push "$tracked_paths" "$instance/tmp/text-integrity-tracked-paths"
incus exec "$instance" -- sh -ec '
    mkdir -p /workspace
    tar -xf /tmp/text-integrity-source.tar -C /workspace
' </dev/null

set +e
if [ -n "$report_output" ]; then
    incus exec "$instance" -- python3 /workspace/tools/text-integrity/scan.py \
        --root /workspace --tracked-list /tmp/text-integrity-tracked-paths \
        --fail-high --output "$container_report" </dev/null
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
        --root /workspace --tracked-list /tmp/text-integrity-tracked-paths \
        --fail-high </dev/null
    scan_status=$?
fi
set -e

exit "$scan_status"
