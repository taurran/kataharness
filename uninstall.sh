#!/bin/sh
# uninstall.sh — KataHarness uninstaller (thin POSIX wrapper)
#
# USAGE
#   sh uninstall.sh --platform claude --target-dir /path/to/project [--yes]
#   # with explicit harness home:
#   KATA_HOME=/path/to/kataharness sh uninstall.sh --platform claude \
#     --target-dir /path/to/project --yes
#
# ENVIRONMENT VARIABLES
#   KATA_HOME    path to the KataHarness home (default: ~/.kata-home)
#   KATA_SRC     local path override (same semantics as install.sh)
#
# REVERSAL SCOPE
#   Removes flat-linked skills from the host, the settings file, and the
#   router stanza from the SUPPLIED --target-dir only.  The harness keeps
#   no registry of every project where a stanza was written, so other
#   projects' AGENTS.md files are not crawled.  For each additional project:
#     sh uninstall.sh --platform claude --target-dir /path/to/other-project
#
# Re-running on an already-uninstalled target exits 0 (no-op).

set -eu

_KATA_DEFAULT_HOME="${HOME}/.kata-home"

# --------------------------------------------------------------------------
# Resolve harness home (no cloning — harness must already be present)
# --------------------------------------------------------------------------
if [ -n "${KATA_SRC:-}" ]; then
    _kata_home="${KATA_SRC}"
elif [ -n "${KATA_HOME:-}" ] && [ -f "${KATA_HOME}/tools/kata_install.py" ]; then
    _kata_home="${KATA_HOME}"
elif [ -f "${_KATA_DEFAULT_HOME}/tools/kata_install.py" ]; then
    _kata_home="${_KATA_DEFAULT_HOME}"
else
    printf 'kata-uninstall: error: KataHarness home not found.\n' >&2
    printf 'Set KATA_HOME to your KataHarness install path, or KATA_SRC for a local path.\n' >&2
    exit 1
fi

if [ ! -f "${_kata_home}/tools/kata_install.py" ]; then
    printf 'kata-uninstall: error: tools/kata_install.py not found in %s\n' "${_kata_home}" >&2
    exit 1
fi

# --------------------------------------------------------------------------
# Default --platform to 'claude' when not supplied
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
# Invoke the engine's --uninstall verb; propagate its exit code via exec.
# --------------------------------------------------------------------------
cd "${_kata_home}"
if command -v uv > /dev/null 2>&1; then
    exec uv run python tools/kata_install.py --uninstall "$@"
elif command -v python3 > /dev/null 2>&1; then
    exec python3 tools/kata_install.py --uninstall "$@"
elif command -v python > /dev/null 2>&1; then
    exec python tools/kata_install.py --uninstall "$@"
else
    printf 'kata-uninstall: error: Python not found.\n' >&2
    printf 'Install uv (https://docs.astral.sh/uv/) or Python 3.12+.\n' >&2
    exit 1
fi
