#!/bin/sh
# update.sh — KataHarness update / factory-reset POSIX bootstrap
#
# USAGE
#   sh update.sh                          # fast-forward to latest on KATA_REF
#   sh update.sh --check                  # report current vs available (no mutation)
#   sh update.sh --discard-local          # proceed even if tracked base files are dirty
#   sh update.sh --factory-reset          # restore pristine links, keep overlay store
#   sh update.sh --factory-reset --hard   # + clear overlay store; confirm-gated
#   sh update.sh --factory-reset --hard --yes   # skip confirmation prompt
#
#   With curl (same honesty posture as install.sh):
#     curl -fsSL https://raw.githubusercontent.com/taurran/kataharness/master/update.sh | sh
#     curl -fsSL .../update.sh | sh -s -- --check
#     curl -fsSL .../update.sh | sh -s -- --factory-reset --hard --yes
#
# ENVIRONMENT VARIABLES
#   KATA_HOME    path to an existing KataHarness home (default: ~/.kata-home)
#   KATA_SRC     local path override — skips all network fetches (offline testing)
#   KATA_REF     git ref / branch / tag to update to (default: master)
#
# SECURITY — curl | sh tradeoff (plain statement, no overclaim)
#   The piped form executes bytes as they stream — nothing to hash first.
#   A checksum protects the download-THEN-run path (fetch the script to a
#   file, verify its SHA, then execute); it does NOT protect the piped form.
#   Mitigations shipped here:
#     • stable URL (raw.githubusercontent.com/taurran/kataharness/master/…)
#     • short, readable script
#     • KATA_REF env var for version-pinning to a specific tag or commit
#   Audit-friendly alternatives:
#     • inspect before running: curl -fsSL .../update.sh | less
#     • curl -fsSL .../update.sh -o update.sh && sh update.sh
#   See docs/SETUP.md for the full tradeoff discussion.
#
# ALL git operations live in this script.  tools/kata_install.py NEVER
# invokes git; the resolved SHA is forwarded via --git-sha so the engine
# stays git-free (DESIGN Invariant 3).

set -eu

# --------------------------------------------------------------------------
# Defaults
# --------------------------------------------------------------------------
_KATA_DEFAULT_HOME="${HOME}/.kata-home"
: "${KATA_REF:=master}"

# --------------------------------------------------------------------------
# Parse own flags; collect engine pass-through args
#
#   Bootstrap-only (NOT forwarded to engine): --check, --discard-local
#   Forwarded to engine AND acted on here:    --factory-reset, --hard,
#                                             --yes / --non-interactive
#   Forwarded unchanged:                      everything else
#                                             (--platform, --json, --dry-run …)
# --------------------------------------------------------------------------
_check=0
_discard_local=0
_factory_reset=0
_hard=0
_yes=0
_engine_args=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --check)
            _check=1
            ;;
        --discard-local)
            _discard_local=1
            ;;
        --factory-reset|--reinstall)
            _factory_reset=1
            _engine_args="${_engine_args} --factory-reset"
            ;;
        --hard)
            _hard=1
            _engine_args="${_engine_args} --hard"
            ;;
        --yes|--non-interactive)
            _yes=1
            _engine_args="${_engine_args} --non-interactive"
            ;;
        *)
            _engine_args="${_engine_args} $1"
            ;;
    esac
    shift
done

# Default --platform to 'claude' when not supplied (mirror install.sh)
case " ${_engine_args} " in
    *" --platform "*) ;;
    *) _engine_args="--platform claude${_engine_args:+ }${_engine_args}" ;;
esac

# --------------------------------------------------------------------------
# Step 1 — resolve the harness home (no cloning — must already be present)
# --------------------------------------------------------------------------
if [ -n "${KATA_SRC:-}" ]; then
    _kata_home="${KATA_SRC}"
elif [ -n "${KATA_HOME:-}" ] && [ -f "${KATA_HOME}/tools/kata_install.py" ]; then
    _kata_home="${KATA_HOME}"
elif [ -f "${_KATA_DEFAULT_HOME}/tools/kata_install.py" ]; then
    _kata_home="${_KATA_DEFAULT_HOME}"
else
    printf 'kata-update: error: KataHarness home not found.\n' >&2
    printf 'Set KATA_HOME to your install path, or KATA_SRC for a local path.\n' >&2
    exit 1
fi

if [ ! -f "${_kata_home}/tools/kata_install.py" ]; then
    printf 'kata-update: error: tools/kata_install.py not found in %s\n' "${_kata_home}" >&2
    exit 1
fi

cd "${_kata_home}"

# --------------------------------------------------------------------------
# --factory-reset path
# The engine handles the re-link; the bootstrap handles the optional --hard
# git reset (the bootstrap's sole git responsibility for factory-reset).
# --------------------------------------------------------------------------
if [ "${_factory_reset}" = "1" ]; then
    # Capture current SHA for the version stamp (best-effort; "unknown" if no .git)
    _git_sha="unknown"
    if [ -d ".git" ] && git remote get-url origin > /dev/null 2>&1; then
        _git_sha=$(git rev-parse HEAD 2>/dev/null || printf 'unknown')
    fi

    # --hard: confirm-gated (DESIGN §9) + optional bootstrap git reset --hard
    if [ "${_hard}" = "1" ]; then
        if [ "${_yes}" != "1" ]; then
            # Refuse to block if stdin is not a TTY (piped / non-interactive)
            if [ ! -t 0 ]; then
                printf 'kata-update: error: --factory-reset --hard requires --yes in non-interactive mode.\n' >&2
                exit 1
            fi
            printf 'kata-update: --factory-reset --hard will CLEAR the overlay store'
            printf ' and reset the base tree.\n'
            printf 'Type YES to continue, anything else to abort: '
            read -r _confirm
            if [ "${_confirm}" != "YES" ]; then
                printf 'kata-update: aborted.\n' >&2
                exit 1
            fi
        fi

        # The bootstrap's git reset --hard is OPTIONAL: only when the home is
        # a git clone with a fetchable origin.  Non-clone homes skip this step
        # (the engine still clears the overlay store via --hard).
        if [ -d ".git" ] && git remote get-url origin > /dev/null 2>&1; then
            printf 'kata-update: fetching and resetting to origin/%s ...\n' "${KATA_REF}"
            git fetch origin
            git checkout "${KATA_REF}" 2>/dev/null \
                || git checkout --detach "origin/${KATA_REF}" 2>/dev/null \
                || git checkout --detach "${KATA_REF}"
            git reset --hard "origin/${KATA_REF}" 2>/dev/null \
                || git reset --hard "refs/tags/${KATA_REF}" 2>/dev/null \
                || git reset --hard "${KATA_REF}"
            _git_sha=$(git rev-parse HEAD)
        fi
    fi

    # Invoke engine: --factory-reset [--hard] --git-sha <sha> [engine-args]
    # shellcheck disable=SC2086
    if command -v uv > /dev/null 2>&1; then
        exec uv run python tools/kata_install.py --git-sha "${_git_sha}" ${_engine_args}
    elif command -v python3 > /dev/null 2>&1; then
        exec python3 tools/kata_install.py --git-sha "${_git_sha}" ${_engine_args}
    elif command -v python > /dev/null 2>&1; then
        exec python tools/kata_install.py --git-sha "${_git_sha}" ${_engine_args}
    else
        printf 'kata-update: error: Python not found.\n' >&2
        printf 'Install uv (https://docs.astral.sh/uv/) or Python 3.12+.\n' >&2
        exit 1
    fi
fi

# --------------------------------------------------------------------------
# Update path — home must be a git clone with a fetchable origin
# --------------------------------------------------------------------------

# minor-c: detect a non-git-clone home (copy / "Use this template" home)
if ! [ -d ".git" ]; then
    printf 'kata-update: this home is not a git clone — re-install to update\n' >&2
    exit 1
fi
if ! git remote get-url origin > /dev/null 2>&1; then
    printf 'kata-update: this home is not a git clone — re-install to update\n' >&2
    exit 1
fi

# Step 2 — fetch origin
printf 'kata-update: fetching origin ...\n'
git fetch origin

# Step 3 — determine local and remote SHAs for the target ref
_local_sha=$(git rev-parse HEAD)
_remote_sha=$(git rev-parse "origin/${KATA_REF}" 2>/dev/null \
    || git rev-parse "refs/tags/${KATA_REF}" 2>/dev/null \
    || git rev-parse "${KATA_REF}")

# --------------------------------------------------------------------------
# --check: report current vs available, then exit without mutating (DESIGN §4.1)
# --------------------------------------------------------------------------
if [ "${_check}" = "1" ]; then
    if [ "${_local_sha}" = "${_remote_sha}" ]; then
        printf 'kata-update --check: already current at %.12s (ref: %s)\n' \
            "${_local_sha}" "${KATA_REF}"
    else
        printf 'kata-update --check: update available\n'
        printf '  current:   %.12s\n' "${_local_sha}"
        printf '  available: %.12s (ref: %s)\n' "${_remote_sha}" "${KATA_REF}"
    fi
    exit 0
fi

# --------------------------------------------------------------------------
# M2 — dirty-tree guard: runs BEFORE any checkout/reset (DESIGN §4.1 + Invariant 7)
# Only TRACKED file changes can be clobbered by git checkout/reset --hard.
# Untracked files (??) and git-ignored files are untouched by the reset.
# Filter out untracked (??) lines so the guard is scoped to tracked base files only.
# --------------------------------------------------------------------------
_dirty=$(git status --porcelain 2>/dev/null | grep -v '^??' || true)
if [ -n "${_dirty}" ]; then
    if [ "${_discard_local}" != "1" ]; then
        printf 'kata-update: ABORT — tracked base files have local modifications:\n' >&2
        printf '%s\n' "${_dirty}" >&2
        printf '\nRe-run with --discard-local to overwrite them, or commit/stash first.\n' >&2
        exit 1
    fi
    printf 'kata-update: WARNING — --discard-local: discarding modifications to tracked base files:\n'
    printf '%s\n' "${_dirty}"
fi

# Step 4 — already current? Still re-run engine (idempotent re-link + stamp refresh)
if [ "${_local_sha}" = "${_remote_sha}" ]; then
    printf 'kata-update: already at %.12s (ref: %s) — re-running engine for idempotent re-link.\n' \
        "${_local_sha}" "${KATA_REF}"
fi

# --------------------------------------------------------------------------
# Step 5 — fast-forward the tracked tree to the target ref
# The base is immutable-by-contract so no 3-way merge is needed — clean
# checkout + reset --hard to origin (spike Recommendation, DESIGN §4.1).
# --------------------------------------------------------------------------
git checkout "${KATA_REF}" 2>/dev/null \
    || git checkout --detach "origin/${KATA_REF}" 2>/dev/null \
    || git checkout --detach "${KATA_REF}"
git reset --hard "origin/${KATA_REF}" 2>/dev/null \
    || git reset --hard "refs/tags/${KATA_REF}" 2>/dev/null \
    || git reset --hard "${KATA_REF}"
_new_sha=$(git rev-parse HEAD)

printf 'kata-update: advanced to %.12s (ref: %s)\n' "${_new_sha}" "${KATA_REF}"

# --------------------------------------------------------------------------
# Step 6 — invoke engine --update --git-sha <sha>; propagate exit via exec.
# ALL git is done above; the engine stays git-free (DESIGN Invariant 3).
# --------------------------------------------------------------------------
# shellcheck disable=SC2086
if command -v uv > /dev/null 2>&1; then
    exec uv run python tools/kata_install.py --update --git-sha "${_new_sha}" ${_engine_args}
elif command -v python3 > /dev/null 2>&1; then
    exec python3 tools/kata_install.py --update --git-sha "${_new_sha}" ${_engine_args}
elif command -v python > /dev/null 2>&1; then
    exec python tools/kata_install.py --update --git-sha "${_new_sha}" ${_engine_args}
else
    printf 'kata-update: error: Python not found.\n' >&2
    printf 'Install uv (https://docs.astral.sh/uv/) or Python 3.12+.\n' >&2
    exit 1
fi
