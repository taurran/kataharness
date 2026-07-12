#!/bin/sh
# update.sh — KataHarness update / factory-reset POSIX bootstrap
#
# USAGE
#   sh update.sh                          # fast-forward to latest on KATA_REF
#   sh update.sh --check                  # report current vs available (no mutation)
#   sh update.sh --discard-local          # proceed even if tracked base files are dirty
#   sh update.sh --clear-stale-locks      # delete stale .git ref locks (printed), then update
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
#   Bootstrap-only (NOT forwarded to engine): --check, --discard-local,
#                                             --clear-stale-locks
#   Forwarded to engine AND acted on here:    --factory-reset, --hard,
#                                             --yes / --non-interactive
#   Forwarded unchanged:                      everything else
#                                             (--platform, --json, --dry-run …)
#
#   Engine args are rebuilt into the positional parameters ("$@") via
#   `set -- "$@" …` so values with spaces (e.g. --target-dir "/a b/x")
#   survive and nothing glob-expands (SC2086). Each pass shifts one ORIGINAL
#   arg off the front and appends its translation to the back; after $_argc
#   passes, "$@" holds exactly the engine pass-through args. The engine
#   invocations below quote "$@".
# --------------------------------------------------------------------------
_check=0
_discard_local=0
_clear_stale_locks=0
_factory_reset=0
_hard=0
_yes=0

_argc=$#
_i=0
while [ "${_i}" -lt "${_argc}" ]; do
    _arg=$1
    shift
    case "${_arg}" in
        --check)
            _check=1
            ;;
        --discard-local)
            _discard_local=1
            ;;
        --clear-stale-locks)
            _clear_stale_locks=1
            ;;
        --factory-reset|--reinstall)
            _factory_reset=1
            set -- "$@" --factory-reset
            ;;
        --hard)
            _hard=1
            set -- "$@" --hard
            ;;
        --yes|--non-interactive)
            _yes=1
            set -- "$@" --non-interactive
            ;;
        *)
            set -- "$@" "${_arg}"
            ;;
    esac
    _i=$((_i + 1))
done

# Default --platform to 'claude' when not supplied (mirror install.sh)
case " $* " in
    *" --platform "*) ;;
    *) set -- --platform claude "$@" ;;
esac

# Pass the git ref through so the engine stamps the ACTUAL ref (not hardcoded
# "master") into .kata-version — stamp-ref honesty (DESIGN B2 --ref).
set -- "$@" --ref "${KATA_REF}"

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
# D157 — stale ref-lock guard + post-fetch remote-truth verification
#
# Observed failure (2026-07-12b): a stale .git/refs/remotes/origin/master.lock
# (left by an interrupted fetch) made `git fetch` SILENTLY fail to advance the
# remote-tracking ref; `git rev-parse origin/master` returned the STALE sha and
# `git reset --hard` "advanced" to the OLD sha — a silent-stale-install.
# Two guards close the class:
#   (a) guard_stale_locks   — PRE-FETCH: abort on any stale lock (path + age);
#                             delete only with the explicit --clear-stale-locks
#                             flag, printing every removed path (never silent).
#   (b) verify_remote_truth — POST-FETCH: one `git ls-remote origin <ref>` call
#                             confirms the local remote-tracking target equals
#                             the REAL remote sha BEFORE any reset.
# --------------------------------------------------------------------------

# Print one lock path + its age in seconds (falls back to ls -ld when no
# usable stat is available).
print_lock_age() {
    _pl_now=$(date +%s)
    _pl_mtime=$(stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || printf '')
    if [ -n "${_pl_mtime}" ]; then
        printf '  %s (age: %ss)\n' "$1" "$((_pl_now - _pl_mtime))"
    else
        printf '  %s (age: unknown; %s)\n' "$1" "$(ls -ld "$1" 2>/dev/null || printf '?')"
    fi
}

guard_stale_locks() {
    _locks=""
    if [ -d .git/refs/remotes ]; then
        _locks=$(find .git/refs/remotes -type f -name '*.lock' 2>/dev/null || true)
    fi
    if [ -f .git/packed-refs.lock ]; then
        if [ -n "${_locks}" ]; then
            _locks="${_locks}
.git/packed-refs.lock"
        else
            _locks=".git/packed-refs.lock"
        fi
    fi
    if [ -z "${_locks}" ]; then
        return 0
    fi
    if [ "${_clear_stale_locks}" = "1" ]; then
        if [ "${_check}" = "1" ]; then
            printf 'kata-update: ABORT — --check is a no-mutation path; stale lock(s) present but NOT deleted:\n' >&2
            printf '%s\n' "${_locks}" | while IFS= read -r _lk; do
                [ -n "${_lk}" ] || continue
                print_lock_age "${_lk}" >&2
            done
            printf 'Re-run --clear-stale-locks WITHOUT --check to delete them.\n' >&2
            exit 1
        fi
        printf 'kata-update: --clear-stale-locks — removing stale git lock file(s):\n'
        printf '%s\n' "${_locks}" | while IFS= read -r _lk; do
            [ -n "${_lk}" ] || continue
            printf '  removing %s\n' "${_lk}"
            rm -f "${_lk}"
        done
        return 0
    fi
    printf 'kata-update: ABORT — stale git lock file(s) detected before fetch:\n' >&2
    printf '%s\n' "${_locks}" | while IFS= read -r _lk; do
        [ -n "${_lk}" ] || continue
        print_lock_age "${_lk}" >&2
    done
    printf '\nAn interrupted fetch can leave these behind; fetching over them SILENTLY\n' >&2
    printf 'fails to advance the remote-tracking ref (silent-stale-install, D157).\n' >&2
    printf 'Confirm no other git process is running, then re-run with --clear-stale-locks.\n' >&2
    exit 1
}

# verify_remote_truth <local-target-ref> <exact-remote-ref | ''>
# '' means the target is a pinned sha — immutable, so ls-remote does not apply.
verify_remote_truth() {
    _vt_target=$1
    _vt_lsref=$2
    if ! _vt_local=$(git rev-parse --verify --quiet "${_vt_target}"); then
        printf 'kata-update: ABORT — could not resolve local target %s after fetch.\n' \
            "${_vt_target}" >&2
        exit 1
    fi
    if [ -z "${_vt_lsref}" ]; then
        printf 'kata-update: NOTE — target %s is a pinned sha; ls-remote verification not applicable.\n' \
            "${_vt_target}"
        return 0
    fi
    if ! _vt_out=$(git ls-remote origin "${_vt_lsref}"); then
        printf 'kata-update: ABORT — git ls-remote origin failed immediately after a successful fetch.\n' >&2
        printf 'That is suspicious (the network was just reachable); refusing to proceed.\n' >&2
        exit 1
    fi
    _vt_remote=$(printf '%s\n' "${_vt_out}" | awk -v ref="${_vt_lsref}" '$2 == ref { print $1; exit }')
    if [ -z "${_vt_remote}" ]; then
        printf 'kata-update: ABORT — ls-remote returned no sha for %s on origin.\n' "${_vt_lsref}" >&2
        exit 1
    fi
    if [ "${_vt_local}" != "${_vt_remote}" ]; then
        printf 'kata-update: ABORT — fetch did not advance the remote-tracking ref — likely a stale ref lock; re-run with --clear-stale-locks.\n' >&2
        printf '  local  %s = %s\n' "${_vt_target}" "${_vt_local}" >&2
        printf '  remote %s = %s\n' "${_vt_lsref}" "${_vt_remote}" >&2
        exit 1
    fi
}

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
            guard_stale_locks
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
    if command -v uv > /dev/null 2>&1; then
        exec uv run python tools/kata_install.py --git-sha "${_git_sha}" "$@"
    elif command -v python3 > /dev/null 2>&1; then
        exec python3 tools/kata_install.py --git-sha "${_git_sha}" "$@"
    elif command -v python > /dev/null 2>&1; then
        exec python tools/kata_install.py --git-sha "${_git_sha}" "$@"
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

# Step 2 — fetch origin (D157: stale-lock guard runs BEFORE the fetch)
guard_stale_locks
printf 'kata-update: fetching origin ...\n'
git fetch origin

# Step 3 — resolve the reset target + local/remote SHAs for the target ref.
# Resolution chain mirrors update.ps1's Get-ResetTarget: origin/<ref>, else
# refs/tags/<ref>, else <ref> (pinned sha). _ls_ref is the EXACT remote ref
# name used by verify_remote_truth ('' for a pinned sha — not applicable).
_local_sha=$(git rev-parse HEAD)
if git rev-parse --verify --quiet "origin/${KATA_REF}" > /dev/null 2>&1; then
    _target="origin/${KATA_REF}"
    _ls_ref="refs/heads/${KATA_REF}"
elif git rev-parse --verify --quiet "refs/tags/${KATA_REF}" > /dev/null 2>&1; then
    _target="refs/tags/${KATA_REF}"
    _ls_ref="refs/tags/${KATA_REF}"
elif git rev-parse --verify --quiet "${KATA_REF}" > /dev/null 2>&1; then
    _target="${KATA_REF}"
    _ls_ref=""
else
    printf 'kata-update: error: ref %s not found (tried origin/%s, refs/tags/%s, %s)\n' \
        "${KATA_REF}" "${KATA_REF}" "${KATA_REF}" "${KATA_REF}" >&2
    exit 1
fi
_remote_sha=$(git rev-parse --verify --quiet "${_target}")
# Peel annotated tags to their COMMIT for HEAD comparisons: `reset --hard` lands
# HEAD on the peeled commit, so comparing HEAD against a tag-OBJECT sha would
# false-abort every annotated-tag update (adval env-hardening finding 1).
# verify_remote_truth still compares UNPEELED shas (tag object vs ls-remote tag
# object — internally consistent).
_remote_commit=$(git rev-parse --verify --quiet "${_target}^{commit}") || _remote_commit="${_remote_sha}"

# --------------------------------------------------------------------------
# --check: report current vs available, then exit without mutating (DESIGN §4.1)
# --------------------------------------------------------------------------
if [ "${_check}" = "1" ]; then
    if [ "${_local_sha}" = "${_remote_commit}" ]; then
        printf 'kata-update --check: already current at %.12s (ref: %s)\n' \
            "${_local_sha}" "${KATA_REF}"
    else
        printf 'kata-update --check: update available\n'
        printf '  current:   %.12s\n' "${_local_sha}"
        printf '  available: %.12s (ref: %s)\n' "${_remote_commit}" "${KATA_REF}"
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
# checkout + hard-reset to the resolved target (spike Recommendation,
# DESIGN §4.1).  D157: verify_remote_truth runs BEFORE any checkout/reset —
# a stale remote-tracking ref must never reach the reset or the engine.
# --------------------------------------------------------------------------
verify_remote_truth "${_target}" "${_ls_ref}"

git checkout "${KATA_REF}" 2>/dev/null \
    || git checkout --detach "origin/${KATA_REF}" 2>/dev/null \
    || git checkout --detach "${KATA_REF}"
git reset --hard "${_target}"
_new_sha=$(git rev-parse HEAD)

# D157(c) — the advancement message prints ONLY on true advancement: HEAD must
# equal the verified target sha (pinned to the ls-remote truth above).
if [ "${_new_sha}" != "${_remote_commit}" ]; then
    printf 'kata-update: ABORT — reset did not land on the verified sha (HEAD %.12s != %.12s).\n' \
        "${_new_sha}" "${_remote_commit}" >&2
    exit 1
fi
printf 'kata-update: advanced to %.12s (ref: %s)\n' "${_new_sha}" "${KATA_REF}"

# --------------------------------------------------------------------------
# Step 6 — invoke engine --update --git-sha <sha>; propagate exit via exec.
# ALL git is done above; the engine stays git-free (DESIGN Invariant 3).
# --------------------------------------------------------------------------
if command -v uv > /dev/null 2>&1; then
    exec uv run python tools/kata_install.py --update --git-sha "${_new_sha}" "$@"
elif command -v python3 > /dev/null 2>&1; then
    exec python3 tools/kata_install.py --update --git-sha "${_new_sha}" "$@"
elif command -v python > /dev/null 2>&1; then
    exec python tools/kata_install.py --update --git-sha "${_new_sha}" "$@"
else
    printf 'kata-update: error: Python not found.\n' >&2
    printf 'Install uv (https://docs.astral.sh/uv/) or Python 3.12+.\n' >&2
    exit 1
fi
