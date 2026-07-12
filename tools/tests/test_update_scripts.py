"""test_update_scripts.py — D157: updater stale-lock robustness (update.ps1 + update.sh).

Observed failure (2026-07-12b): update.ps1 ran while a stale
``refs/remotes/origin/master.lock`` (left by an interrupted fetch) existed; the fetch
SILENTLY failed to advance the remote-tracking ref, ``git rev-parse origin/master``
returned the STALE sha, ``git reset --hard`` "advanced" to the OLD sha, and the engine
re-stamped it — a silent-stale-install.

The updater bootstraps are shell scripts with no python seam, so these are content/
regex pins over both scripts, symmetrically:

a. PRE-FETCH stale-lock detection (``.git/refs/remotes/**/*.lock`` +
   ``.git/packed-refs.lock``) — abort with path + age, ``--clear-stale-locks`` opt-in
   deletion that prints every removed path (never silent).
b. POST-FETCH truth check — ``git ls-remote origin <ref>`` verified against the local
   remote-tracking target BEFORE any reset; distinct loud failures for a stale ref and
   for a suspicious ls-remote failure right after a successful fetch.
c. The "advanced to" message prints only after HEAD is confirmed against the verified
   sha.

Order is asserted by match POSITIONS inside each script's update-path segment.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SH = (REPO_ROOT / "update.sh").read_text(encoding="utf-8")
PS1 = (REPO_ROOT / "update.ps1").read_text(encoding="utf-8")

# Update-path segments (the factory-reset path precedes these markers in both scripts).
SH_UPDATE_MARKER = "# Update path"
PS1_UPDATE_MARKER = "# UPDATE path"


def _segment_from(text: str, marker: str) -> str:
    idx = text.find(marker)
    assert idx != -1, f"marker {marker!r} missing — script structure changed"
    return text[idx:]


SH_UPDATE = _segment_from(SH, SH_UPDATE_MARKER)
PS1_UPDATE = _segment_from(PS1, PS1_UPDATE_MARKER)
SH_FACTORY = SH[SH.find("--factory-reset path") : SH.find(SH_UPDATE_MARKER)]
PS1_FACTORY = PS1[PS1.find("FACTORY-RESET path") : PS1.find(PS1_UPDATE_MARKER)]


# ---------------------------------------------------------------------------
# (flag) --clear-stale-locks is parsed in both scripts and NOT forwarded to engine
# ---------------------------------------------------------------------------


def test_sh_parses_clear_stale_locks_flag():
    m = re.search(r"--clear-stale-locks\)(.*?);;", SH, re.DOTALL)
    assert m, "update.sh must parse a --clear-stale-locks case arm"
    body = m.group(1)
    assert "_clear_stale_locks=1" in body
    assert "set --" not in body, "--clear-stale-locks is bootstrap-only, never forwarded"


def test_ps1_parses_clear_stale_locks_flag():
    m = re.search(r"elseif \(\$a -eq '--clear-stale-locks'\) \{ (.*?) \}", PS1)
    assert m, "update.ps1 must parse --clear-stale-locks"
    body = m.group(1)
    assert "$_clearStaleLocks = $true" in body
    assert "_engineArgs" not in body, "--clear-stale-locks is bootstrap-only, never forwarded"


# ---------------------------------------------------------------------------
# (a) PRE-FETCH stale-lock scan: locations, age print, opt-in deletion, guidance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("script", "remotes_path"),
    [(SH, ".git/refs/remotes"), (PS1, ".git\\refs\\remotes")],
    ids=["sh", "ps1"],
)
def test_scan_covers_remote_ref_locks_and_packed_refs_lock(script, remotes_path):
    assert remotes_path in script, "scan must cover .git/refs/remotes/**"
    assert "packed-refs.lock" in script, "scan must cover .git/packed-refs.lock"
    assert "*.lock" in script or ".lock" in script


@pytest.mark.parametrize("script", [SH, PS1], ids=["sh", "ps1"])
def test_abort_prints_age_and_clear_guidance(script):
    assert "(age:" in script, "abort must print each lock path + age"
    assert "re-run with --clear-stale-locks" in script
    assert "no other git process" in script


def test_sh_deletion_prints_each_path_never_silent():
    m = re.search(r"printf '  removing %s\\n' \"\$\{_lk\}\"\s*\n\s*rm -f \"\$\{_lk\}\"", SH)
    assert m, "update.sh must print each lock path immediately before deleting it"


def test_ps1_deletion_prints_each_path_never_silent():
    m = re.search(r'Write-Host "  removing \$_lk"\s*\r?\n\s*Remove-Item', PS1)
    assert m, "update.ps1 must print each lock path immediately before deleting it"


# ---------------------------------------------------------------------------
# (b) POST-FETCH truth check — ls-remote verified, distinct loud failures
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("script", [SH, PS1], ids=["sh", "ps1"])
def test_truth_check_uses_ls_remote_and_fails_loud(script):
    assert "ls-remote origin" in script
    assert "fetch did not advance the remote-tracking ref" in script
    # ls-remote failure right after a successful fetch is its own distinct abort
    assert "immediately after a successful fetch" in script


@pytest.mark.parametrize("script", [SH, PS1], ids=["sh", "ps1"])
def test_reset_landing_verified_before_advanced_message(script):
    assert "did not land on the verified sha" in script


# ---------------------------------------------------------------------------
# ORDER pins — scan < fetch < ls-remote check < reset < landing check < "advanced to"
# ---------------------------------------------------------------------------


def _ordered(segment: str, *needles: str) -> list[int]:
    positions = []
    for needle in needles:
        pos = segment.find(needle)
        assert pos != -1, f"{needle!r} missing from update-path segment"
        positions.append(pos)
    return positions


def test_sh_update_path_order():
    pos = _ordered(
        SH_UPDATE,
        "guard_stale_locks",
        "git fetch origin",
        "verify_remote_truth",
        "git reset --hard",
        "did not land on the verified sha",
        "advanced to",
    )
    assert pos == sorted(pos), f"update.sh update-path guard order broken: {pos}"


def test_ps1_update_path_order():
    pos = _ordered(
        PS1_UPDATE,
        "Assert-NoStaleGitLocks",
        "git fetch origin",
        "Assert-RemoteTruth",
        "git reset --hard",
        "did not land on the verified sha",
        "advanced to",
    )
    assert pos == sorted(pos), f"update.ps1 update-path guard order broken: {pos}"


def test_sh_factory_reset_fetch_is_lock_guarded():
    fetch = SH_FACTORY.find("git fetch origin")
    guard = SH_FACTORY.find("guard_stale_locks")
    assert fetch != -1, "factory-reset fetch missing"
    assert guard != -1, "factory-reset path must scan stale locks before its fetch"
    assert guard < fetch


def test_ps1_factory_reset_fetch_is_lock_guarded():
    fetch = PS1_FACTORY.find("git fetch origin")
    guard = PS1_FACTORY.find("Assert-NoStaleGitLocks")
    assert fetch != -1, "factory-reset fetch missing"
    assert guard != -1, "factory-reset path must scan stale locks before its fetch"
    assert guard < fetch


# ---------------------------------------------------------------------------
# Symmetry + structural sanity
# ---------------------------------------------------------------------------


def test_both_scripts_still_have_single_update_fetch():
    """Exactly one fetch in each update-path segment (the guarded one)."""
    assert SH_UPDATE.count("git fetch origin") == 1
    assert PS1_UPDATE.count("git fetch origin") == 1


def test_sh_documents_clear_stale_locks_in_usage():
    assert "--clear-stale-locks" in SH.split("set -eu")[0], (
        "update.sh usage header must document --clear-stale-locks"
    )


def test_ps1_documents_clear_stale_locks_in_usage():
    header = PS1.split("$ErrorActionPreference")[0]
    assert "--clear-stale-locks" in header, (
        "update.ps1 usage header must document --clear-stale-locks"
    )
