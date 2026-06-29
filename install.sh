#!/bin/sh
# install.sh — KataHarness one-command POSIX bootstrap
#
# QUICK START
#   curl -fsSL https://raw.githubusercontent.com/taurran/kataharness/master/install.sh | sh
#   # pass extra args via  sh -s --:
#   curl -fsSL .../install.sh | sh -s -- --platform codex --host-dir ~/.codex
#
# ENVIRONMENT VARIABLES
#   KATA_HOME        reuse an existing harness home (skip the clone)
#   KATA_REF         git tag / branch / SHA to pin  (default: master)
#   KATA_SRC         local filesystem path to use as harness home — skips all
#                    network fetches (for offline smoke-testing or CI that
#                    already has a checkout):
#                      KATA_SRC=/path/to/KataHarness sh install.sh
#   KATA_PARENT_DIR  default parent project folder (forwarded to engine)
#   KATA_VAULT_DIR   vault location (forwarded to engine)
#
# SECURITY  — curl | sh tradeoff (plain statement, no overclaim)
#   The piped form executes bytes as they stream — nothing to hash first.
#   A checksum protects the download-THEN-run path (fetch the script to a
#   file, verify its SHA, then execute); it does NOT protect the piped form.
#   Mitigations shipped here:
#     • stable URL (raw.githubusercontent.com/taurran/kataharness/master/…)
#     • short, readable script (< 80 lines of logic)
#     • KATA_REF env var for version-pinning to a specific tag or commit
#   Audit-friendly alternatives:
#     • git clone https://github.com/taurran/kataharness.git (inspect first)
#     • curl -fsSL .../install.sh -o install.sh && sh install.sh ...
#     • GitHub "Use this template" button (no remote script involved)
#   See docs/SETUP.md for the full tradeoff discussion.
#
# All arguments (after --) are forwarded unchanged to tools/kata_install.py.
# Defaults --platform to 'claude' when no --platform arg is supplied.

set -eu

# --------------------------------------------------------------------------
# Defaults
# --------------------------------------------------------------------------
_KATA_REPO_URL="https://github.com/taurran/kataharness.git"
_KATA_DEFAULT_HOME="${HOME}/.kata-home"
: "${KATA_REF:=master}"

# --------------------------------------------------------------------------
# Step 1 — resolve the harness home (priority order)
# --------------------------------------------------------------------------
if [ -n "${KATA_SRC:-}" ]; then
    # Offline / local-source override — use this path directly, no network.
    _kata_home="${KATA_SRC}"
elif [ -n "${KATA_HOME:-}" ] && [ -f "${KATA_HOME}/tools/kata_install.py" ]; then
    # KATA_HOME already contains a valid harness — idempotent, no re-clone.
    _kata_home="${KATA_HOME}"
elif [ -f "${_KATA_DEFAULT_HOME}/tools/kata_install.py" ]; then
    # Default home present — idempotent, no re-clone.
    _kata_home="${_KATA_DEFAULT_HOME}"
else
    # Clone to the default home.  The .git inside is legitimate repo metadata
    # (enables future `git pull` updates); it is not cruft.
    _kata_home="${_KATA_DEFAULT_HOME}"
    printf 'kata-install: cloning KataHarness (ref=%s) to %s ...\n' "${KATA_REF}" "${_kata_home}"
    git clone --branch "${KATA_REF}" --depth 1 "${_KATA_REPO_URL}" "${_kata_home}"
    printf 'kata-install: clone complete.\n'
fi

# --------------------------------------------------------------------------
# Step 2 — sanity check
# --------------------------------------------------------------------------
if [ ! -f "${_kata_home}/tools/kata_install.py" ]; then
    printf 'kata-install: error: tools/kata_install.py not found in %s\n' "${_kata_home}" >&2
    exit 1
fi

# --------------------------------------------------------------------------
# Step 3 — default --platform to 'claude' when not supplied
# --------------------------------------------------------------------------
_has_platform=0
for _arg in "$@"; do
    if [ "${_arg}" = "--platform" ]; then
        _has_platform=1
        break
    fi
done
if [ "${_has_platform}" = "0" ]; then
    set -- --platform claude "$@"
fi

# --------------------------------------------------------------------------
# Steps 4–5 — locate Python → invoke engine → propagate exit code (exec)
# All install logic lives in the engine; this script adds none of its own.
# --------------------------------------------------------------------------
cd "${_kata_home}"
if command -v uv > /dev/null 2>&1; then
    exec uv run python tools/kata_install.py "$@"
elif command -v python3 > /dev/null 2>&1; then
    exec python3 tools/kata_install.py "$@"
elif command -v python > /dev/null 2>&1; then
    exec python tools/kata_install.py "$@"
else
    printf 'kata-install: error: Python not found.\n' >&2
    printf 'Install uv (https://docs.astral.sh/uv/) or Python 3.12+.\n' >&2
    exit 1
fi
