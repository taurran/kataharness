#!/usr/bin/env sh
# tools/scripts/sca.sh — dependency (SCA) scan for the kata-tools engine deps.
#
# Wired 2026-07-12 (health review M-1): the gauntlet ran SAST (Snyk Code) but no
# SCA. Snyk's SCA resolver can't read the uv-native manifest, so we export the
# locked deps to a requirements file and scan with pip-audit (via uvx — no global
# install needed).
#
# Usage (from repo root or tools/):  sh tools/scripts/sca.sh
# Exit 0 = clean; non-zero = a known vulnerability in a pinned dependency.
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TOOLS_DIR=$(CDPATH= cd -- "$HERE/.." && pwd)
REQ_FILE=$(mktemp 2>/dev/null || echo "${TMPDIR:-/tmp}/kata-sca-req.txt")

cleanup() { rm -f "$REQ_FILE"; }
trap cleanup EXIT

echo "kata-sca: exporting locked deps from $TOOLS_DIR ..."
( cd "$TOOLS_DIR" && uv export --format requirements-txt --no-emit-project --no-hashes ) \
    | grep -vE '^\s*#' | grep -vE '^\s*$' > "$REQ_FILE"

echo "kata-sca: auditing $(wc -l < "$REQ_FILE" | tr -d ' ') pinned packages with pip-audit ..."
uvx pip-audit --requirement "$REQ_FILE" --strict
echo "kata-sca: clean."
