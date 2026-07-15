"""kata_settings.py — the central-install settings file for KataHarness.

KataHarness lives in one central place ("harness home") and remembers **two
settings** so each run can find the project to work on:

- ``parentDir`` — the default parent project folder (overridable per run).
- ``vaultDir``  — where the vault / second brain sits (optional). Seeds the
  second-brain learn-feed paths top-down via ``default_learn_feed_dir``
  (``<vaultDir>/second-brain/wiki/pages/synthesis``) and
  ``default_learn_log_path`` (``<vaultDir>/second-brain/wiki/log.md``) —
  the values kata-bootstrap writes into ``engram.learnFeed.dir`` / the emit
  log path at config-write (SB-L7). Absent ⇒ both helpers return ``None``
  and the learn feed is a no-op (BC1).
- ``telemetryLedger`` — absolute path to the harness repo's committed M4
  telemetry ledger (``.planning/telemetry-ledger.md``); the locator target-repo
  runs use to READ (slack class-medians) and APPEND (closeout row) — identical
  resolution both directions (M4-P0 T4, gate v2 F4). Absent ⇒ the ledger source
  is absent: medians fall through per A1-Q3 and closeout rows land in
  ``.kata/telemetry/ledger-row.pending.json``, surfaced (never silent).

The settings file is ``<harness_home>/.kata-settings.json`` (git-ignored). These
values SEED the per-run ``kata.config`` path-fields (``target.path``,
``engram.learnFeed.dir``, ``agentSkills.dir`` — protocol/config.md:22/25/26); a
run may override them. Absent settings ⇒ the harness runs in-repo unchanged (BC1).

Public API
----------
harness_home() -> Path
    Resolve the install root: ``$KATA_HOME`` env → self-locate (this file lives
    at ``<home>/tools/``). No machine registry, no multi-level chain (kept simple).
settings_path(home=None) -> Path
build_settings(parent_dir, vault_dir=None) -> dict   # pure; validates + resolves
read_settings(home=None) -> dict                      # {} when absent
write_settings(parent_dir, vault_dir=None, home=None) -> Path
default_learn_feed_dir(settings) -> str | None        # SB-L7 seeding helper (pure)
default_learn_log_path(settings) -> str | None        # SB-L7 seeding helper (pure)

Security: operator-supplied paths are ``..``-guarded (CWE-23) then resolved to
absolute before storage, mirroring gate_emit._safe_path.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import kata_version

SETTINGS_FILENAME = ".kata-settings.json"
SETTINGS_VERSION = 1

# Allowed bridgeMode values for the audit-only hostPosture block (CA-L37 / §2).
_BRIDGE_MODES = ("chained", "user-only", "none")


def _safe_abs(raw: str | Path) -> Path:
    """Reject ``..`` traversal (CWE-23) then resolve to an absolute path."""
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"kata_settings: refusing path with '..' traversal: {raw!r}")
    return p.resolve()


def harness_home() -> Path:
    """The KataHarness install root.

    Precedence: ``$KATA_HOME`` (explicit override / CI) → self-locate. This file
    is ``<home>/tools/kata_settings.py``, so the home is two parents up.
    """
    env = os.environ.get("KATA_HOME")
    if env:
        return _safe_abs(env)
    return Path(__file__).resolve().parent.parent


def settings_path(home: str | Path | None = None) -> Path:
    base = _safe_abs(home) if home is not None else harness_home()
    return base / SETTINGS_FILENAME


def build_settings(parent_dir: str | Path, vault_dir: str | Path | None = None) -> dict:
    """Pure builder: validate + resolve the two settings into a dict.

    Raises ``ValueError`` (fail-closed) when ``parent_dir`` is missing/blank.
    """
    if parent_dir is None or not str(parent_dir).strip():
        raise ValueError("kata_settings: parentDir is required")
    out: dict = {
        "settingsVersion": SETTINGS_VERSION,
        "parentDir": str(_safe_abs(parent_dir)),
        "vaultDir": str(_safe_abs(vault_dir)) if vault_dir not in (None, "") else None,
    }
    return out


def read_settings(home: str | Path | None = None) -> dict:
    """Read the settings file; return ``{}`` when it is absent OR unreadable/corrupt (degrade to BC1)."""
    p = settings_path(home)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}  # corrupt/unreadable ⇒ treat as absent, fall back to in-repo defaults


# ---------------------------------------------------------------------------
# SB-L7 — second-brain loop config seeding (pure helpers; freeze-gate F-2)
#
# BOTH paths are computed TOP-DOWN from vaultDir — the log path is NEVER
# derived from the feed dir via `..` (F-2: each consumer receives its path as
# supplied, guarded independently). vaultDir is already `..`-guarded at the
# write boundary (build_settings), but each helper RE-GUARDS defensively —
# a settings dict is attacker-influenceable on-disk input to decision code.
# ---------------------------------------------------------------------------


def default_learn_feed_dir(settings: dict) -> str | None:
    """The default second-brain learn-feed dir seeded from ``vaultDir`` (SB-L7).

    ``<vaultDir>/second-brain/wiki/pages/synthesis`` as an absolute resolved
    string when ``vaultDir`` is set; ``None`` when absent/blank (the learn feed
    is then a no-op — BC1). ``..`` in ``vaultDir`` ⇒ ``ValueError`` (CWE-23
    re-guard). Pure: no filesystem writes, no existence requirement.
    """
    vault = settings.get("vaultDir")
    if vault in (None, ""):
        return None
    base = _safe_abs(vault)  # defensive re-guard + resolve to absolute
    return str(base / "second-brain" / "wiki" / "pages" / "synthesis")


def default_learn_log_path(settings: dict) -> str | None:
    """The default second-brain emit-log path seeded from ``vaultDir`` (SB-L7).

    ``<vaultDir>/second-brain/wiki/log.md`` as an absolute resolved string when
    ``vaultDir`` is set; ``None`` when absent/blank. Computed top-down from
    ``vaultDir`` — NEVER via ``..`` from the feed dir (freeze-gate F-2).
    ``..`` in ``vaultDir`` ⇒ ``ValueError`` (CWE-23 re-guard). Pure.
    """
    vault = settings.get("vaultDir")
    if vault in (None, ""):
        return None
    base = _safe_abs(vault)  # defensive re-guard + resolve to absolute
    return str(base / "second-brain" / "wiki" / "log.md")


def add_confirmed_platform(platform: str, home: str | Path | None = None) -> list[str]:
    """Append ``platform`` to the settings' ``confirmedPlatforms`` list (idempotent); return the list.

    Written by the install confirm-probe (N5); read by the multi-model roles resolver to gate
    routing a role to a non-host platform.
    """
    if not platform or not platform.strip():
        raise ValueError("kata_settings: platform is required")
    p = settings_path(home)
    data = read_settings(home)
    confirmed = list(data.get("confirmedPlatforms", []))
    if platform not in confirmed:
        confirmed.append(platform)
    data["confirmedPlatforms"] = confirmed
    data.setdefault("settingsVersion", SETTINGS_VERSION)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return confirmed


def confirmed_platforms(home: str | Path | None = None) -> list[str]:
    """The platforms confirmed on this machine (empty if none)."""
    return list(read_settings(home).get("confirmedPlatforms", []))


def _load_existing(path: Path) -> dict:
    """Strict raw-load of the settings file for merge use.

    Returns ``{}`` when the file is absent. Raises ``ValueError`` when the file
    is present but unparseable JSON **or** contains valid JSON that is not a dict
    (e.g. ``[]``, ``null``, ``42``). OSError is NOT caught — the CLI maps it to
    exit-4 and the operator should not silently lose state they cannot read.

    Deliberately does NOT reuse ``read_settings``: that function leniently returns
    ``{}`` on corruption (BC1 degrade for the *run* path). A *writer* about to
    overwrite must not destroy data it cannot understand — fail-closed is required.
    """
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise ValueError(
            f"kata_settings: refusing to overwrite unparseable settings file: {path}"
        )
    if not isinstance(data, dict):
        raise ValueError(
            f"kata_settings: refusing to overwrite unparseable settings file: {path}"
        )
    return data


def write_settings(
    parent_dir: str | Path,
    vault_dir: str | Path | None = None,
    home: str | Path | None = None,
) -> Path:
    """Write the settings file at ``<home>/.kata-settings.json`` and return its path.

    Validates at the persistence boundary (DESIGN §4): ``parentDir`` must be an
    existing directory; ``vaultDir``, when given, likewise. (``build_settings``
    stays pure for previews; existence checks need IO so they live here.)

    Merge semantics (load-existing → overlay owned keys → write):
    - File absent: behaves exactly like today (``existing == {}``).
    - File present but corrupt / non-dict: **fail-closed** (``ValueError``; file
      untouched). Do NOT silently clobber.
    - Owned keys (``settingsVersion``, ``parentDir``): always replaced.
    - ``vaultDir``: replaced when ``vault_dir`` is supplied; otherwise the prior
      on-disk value is preserved (falls back to ``None`` only when no prior exists).
    - Every other key (e.g. ``confirmedPlatforms``, future keys): preserved verbatim.
    """
    # 1. Validate FIRST — same ValueErrors, same order, before any file read.
    if not Path(parent_dir).is_dir():
        raise ValueError(f"kata_settings: parentDir is not an existing directory: {parent_dir!r}")
    if vault_dir not in (None, "") and not Path(vault_dir).is_dir():
        raise ValueError(f"kata_settings: vaultDir is not an existing directory: {vault_dir!r}")
    # 2. Strict-load existing (fail-closed on corrupt / non-dict).
    p = settings_path(home)
    existing = _load_existing(p)
    # 3. Overlay owned keys on top of existing (owned wins on collision).
    owned = build_settings(parent_dir, vault_dir)
    merged = {**existing, **owned}
    # 4. Vault-preserve rule: when vault_dir was NOT supplied, restore the prior
    #    on-disk vaultDir so a --parent-dir-only reconfigure does not drop it.
    #    Falls back to None only when no prior exists — byte-identical to today.
    if vault_dir in (None, ""):
        merged["vaultDir"] = existing.get("vaultDir")
    # 5. Write (same serialization as today: indent=2 + trailing newline).
    p.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# CA-P0 / E2 — context-autonomy per-install keys (CA-L35..L37, §2 settings table)
#
# Four additive keys, all AUDIT-ONLY except ``firstRunCompletedAt`` (the only
# do-once suppression in the file, CA-L37):
#   firstRunCompletedAt  — ISO-8601 UTC, the force-run marker (CA-L36).
#   firstRunVersion      — the .kata-version stamp ``gitSha`` the forced run
#                          completed for (CA-L36 / R-43; NOT ``suiteSemver``).
#   hostPosture          — {autoCompactChecked, recommendedWindowTokens,
#                          bridgeMode}; last-write-wins, never consulted for
#                          suppression (CA-L37/R-42).
#   acceptedDefaults     — {"<bundleItemId>": {value, v, at}}; C-1 schema,
#                          audit-only, per-item last-write-wins (CA-L37).
#
# WRITER DISCIPLINE (C-4, gate v6): every writer below copies the fail-closed
# ``_load_existing`` pattern (a corrupt file RAISES ``ValueError``, the file is
# left byte-unchanged), NEVER the lenient ``add_confirmed_platform``
# read-before-write which silently clobbers a corrupt file — that would
# contradict the C-3 corrupt-settings contract.
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    """Current instant as an ISO-8601 UTC string (matches kata_version stamps)."""
    return datetime.now(UTC).isoformat()


def _merge_write(updates: dict, home: str | Path | None) -> Path:
    """Fail-closed overlay-write: strict-load existing, overlay ``updates``, write.

    Copies the ``write_settings`` merge discipline (C-4): ``_load_existing``
    RAISES ``ValueError`` on a corrupt / non-dict file and the file is left
    untouched. Never the lenient ``add_confirmed_platform`` clobber.
    """
    p = settings_path(home)
    existing = _load_existing(p)  # fail-closed on corrupt / non-dict
    merged = {**existing, **updates}
    merged.setdefault("settingsVersion", SETTINGS_VERSION)
    p.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return p


def record_first_run(git_sha: str, home: str | Path | None = None) -> Path:
    """Stamp the force-run marker: ``firstRunCompletedAt`` + ``firstRunVersion``.

    ``git_sha`` is the current ``.kata-version`` stamp's ``gitSha`` (CA-L36/R-43
    — the marker records a ``gitSha``, never ``suiteSemver``). ``"unknown"`` is a
    valid value (the plain-install path); only ``None``/blank is rejected.

    Fail-closed (C-4): a corrupt ``.kata-settings.json`` RAISES ``ValueError``
    and is left byte-unchanged. CALLER CONTRACT (CA-L37/C-3): bootstrap MUST
    detect this write failure, surface LOUDLY pointing at the corrupt file path,
    and stop — **never loop**.
    """
    if git_sha is None or not str(git_sha).strip():
        raise ValueError("kata_settings: git_sha is required for the first-run marker")
    return _merge_write(
        {"firstRunCompletedAt": _utc_now_iso(), "firstRunVersion": str(git_sha)},
        home,
    )


def record_host_posture(posture: dict, home: str | Path | None = None) -> Path:
    """Write the AUDIT-ONLY ``hostPosture`` block (last-write-wins; CA-L37/R-42).

    ``posture`` schema (§2): ``{autoCompactChecked: bool, recommendedWindowTokens:
    int|None, bridgeMode: "chained"|"user-only"|"none"}``. NEVER consulted for
    suppression — the compact-window recommendation is RECOMPUTED at every run's
    preflight (OP-4). Malformed posture ⇒ ``ValueError`` (fail-closed, D136).

    Fail-closed on a corrupt settings file (C-4), same as ``record_first_run``.
    """
    if not isinstance(posture, dict):
        raise ValueError("kata_settings: hostPosture must be a dict")
    if not isinstance(posture.get("autoCompactChecked"), bool):
        raise ValueError("kata_settings: hostPosture.autoCompactChecked must be a bool")
    rwt = posture.get("recommendedWindowTokens")
    if not (rwt is None or (isinstance(rwt, int) and not isinstance(rwt, bool))):
        raise ValueError(
            "kata_settings: hostPosture.recommendedWindowTokens must be int or null"
        )
    if posture.get("bridgeMode") not in _BRIDGE_MODES:
        raise ValueError(
            f"kata_settings: hostPosture.bridgeMode must be one of {_BRIDGE_MODES}"
        )
    block = {
        "autoCompactChecked": posture["autoCompactChecked"],
        "recommendedWindowTokens": rwt,
        "bridgeMode": posture["bridgeMode"],
    }
    return _merge_write({"hostPosture": block}, home)


def record_accepted_defaults(entries: dict, home: str | Path | None = None) -> Path:
    """Merge AUDIT-ONLY ``acceptedDefaults`` entries (per-item last-write-wins).

    ``entries`` schema (C-1, §2): ``{"<bundleItemId>": {"value": <json>, "v":
    "<harness semver>", "at": "<ISO-8601 UTC>"}}`` — one entry per bundle item
    the operator accepted at CA-L24. Each item's latest value wins; existing
    items not in ``entries`` are preserved. Audit-only, never consulted for
    suppression (CA-L37). Malformed entries ⇒ ``ValueError`` (fail-closed).

    Fail-closed on a corrupt settings file (C-4).
    """
    if not isinstance(entries, dict):
        raise ValueError("kata_settings: acceptedDefaults entries must be a dict")
    for item_id, entry in entries.items():
        if not isinstance(entry, dict):
            raise ValueError(
                f"kata_settings: acceptedDefaults[{item_id!r}] must be a dict"
            )
        for req in ("value", "v", "at"):
            if req not in entry:
                raise ValueError(
                    f"kata_settings: acceptedDefaults[{item_id!r}] missing key {req!r}"
                )
        if not isinstance(entry["v"], str) or not isinstance(entry["at"], str):
            raise ValueError(
                f"kata_settings: acceptedDefaults[{item_id!r}] 'v'/'at' must be strings"
            )
    p = settings_path(home)
    existing = _load_existing(p)  # fail-closed
    merged_defaults = {**existing.get("acceptedDefaults", {}), **entries}
    return _merge_write({"acceptedDefaults": merged_defaults}, home)


def delete_settings_key(key: str, home: str | Path | None = None) -> bool:
    """Remove ``key`` from the settings file; return whether a delete happened.

    The CA-L36 named build item: ``write_settings`` cannot delete a key
    (``{**existing, **owned}`` preserves every key), so the factory-reset marker
    clear needs this small fail-closed helper.

    - File absent OR key not present ⇒ return ``False``, no write.
    - Key present ⇒ removed, file rewritten, return ``True``.
    - Corrupt / non-dict file ⇒ ``_load_existing`` RAISES ``ValueError``; the
      file is left byte-unchanged (fail-closed, C-4).
    """
    if not key or not str(key).strip():
        raise ValueError("kata_settings: key is required")
    p = settings_path(home)
    data = _load_existing(p)  # fail-closed on corrupt / non-dict
    if key not in data:
        return False
    del data[key]
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def first_run_required(home: str | Path | None = None) -> dict:
    """The CA-L36 force-first-run comparator.

    Bootstrap force-executes the FULL first run when the marker is **absent OR
    ``firstRunVersion`` differs from the ``.kata-version`` stamp's ``gitSha``**
    (R-43: the stamp has no ``version`` field; ``suiteSemver`` is rejected).
    ``Stamp absent OR gitSha == "unknown"`` ⇒ the version clause is SKIPPED and
    marker absence alone forces (dev in-repo homes are not force-every-run).

    Returns ``{required: bool, reason: "marker-absent"|"sha-mismatch"|None,
    clause_skipped: bool}``.

    **C-3 surface:** the marker READ here is LENIENT — a corrupt settings file
    reads as absent (``read_settings`` degrades to ``{}``) ⇒ the run is forced.
    The paired ``record_first_run`` on that same corrupt file fail-closes, so a
    forced run that cannot persist its marker MUST be surfaced LOUDLY by the
    caller pointing at the corrupt file path, then stop — **never loop**.
    """
    settings = read_settings(home)  # LENIENT (corrupt ⇒ {} ⇒ force)
    marker = settings.get("firstRunCompletedAt")
    recorded_sha = settings.get("firstRunVersion")

    stamp = kata_version.read_stamp(home if home is not None else harness_home())
    stamp_sha = stamp.get("gitSha") if isinstance(stamp, dict) else None
    clause_skipped = stamp_sha in (None, "", "unknown")

    if marker is None:
        return {"required": True, "reason": "marker-absent", "clause_skipped": clause_skipped}
    if clause_skipped:
        # Marker present + no comparable stamp ⇒ marker governs ⇒ not required.
        return {"required": False, "reason": None, "clause_skipped": True}
    if recorded_sha != stamp_sha:
        return {"required": True, "reason": "sha-mismatch", "clause_skipped": False}
    return {"required": False, "reason": None, "clause_skipped": False}


# ---------------------------------------------------------------------------
# second-brain-target / S1 — the PokeVault recommendation engine (EV-1)
#
# Second brain is an OPTIONAL, user-definable TARGET (D2), never required. The
# NEW build is the recommendation flow (D3) with the remembered-decline leg
# (EV-1): recommend a starter vault when none is configured, remember an explicit
# decline in the EXISTING acceptedDefaults store (no new store), and re-arm the
# recommendation on the next upgrade — mirroring first_run_required's version
# clause, INVERTED for a decline record.
# ---------------------------------------------------------------------------

POKEVAULT_LINK = "https://github.com/taurran/pokevault"
_VAULT_REC_ITEM = "vault-recommendation"  # the acceptedDefaults key (existing C-1 schema)


def _current_git_sha(home: str | Path | None) -> str | None:
    """The current ``.kata-version`` stamp's ``gitSha`` (``None`` when no comparable stamp).

    Mirrors ``first_run_required``'s stamp read exactly: an absent stamp or a
    non-dict read yields ``None``; ``"unknown"`` is returned verbatim (the caller
    decides whether that value skips the version clause).
    """
    stamp = kata_version.read_stamp(home if home is not None else harness_home())
    return stamp.get("gitSha") if isinstance(stamp, dict) else None


def vault_recommendation(settings: dict, home: str | Path | None = None) -> dict:
    """The PokeVault second-brain recommendation decision (S1; pure w.r.t. ``settings``).

    Returns ``{"recommend": bool, "reason": str, "link": <POKEVAULT_LINK>}``.
    ``recommend=True`` IFF ``vaultDir`` is unset/empty **AND** no *un-lapsed*
    remembered decline exists. The decline lives in
    ``acceptedDefaults["vault-recommendation"]`` — the existing C-1 schema, no new
    store — as ``{value: "declined", v: <gitSha-or-"unknown">, at: <ISO>}``.

    **Re-arm (EV-1) — mirrors ``first_run_required``'s version clause, INVERTED for
    a decline record:** a recorded decline whose ``v`` ≠ the current
    ``.kata-version`` ``gitSha`` has LAPSED ⇒ recommend again (``reason``
    ``"decline-lapsed"``). ``Stamp absent OR gitSha == "unknown"`` ⇒ the version
    clause is SKIPPED and the decline HOLDS (dev in-repo posture — a dev tree must
    not nag).

    ``settings`` is the (lenient) ``read_settings`` output: a corrupt/absent file
    degrades to ``{}`` upstream ⇒ "no decline recorded" ⇒ recommend when
    ``vaultDir`` is also unset. A non-dict ``settings`` is treated the same way.
    This function never writes — the WRITE stays fail-closed in
    ``record_vault_decline``.
    """
    if not isinstance(settings, dict):
        settings = {}
    # A configured vault ⇒ nothing to recommend.
    if settings.get("vaultDir") not in (None, ""):
        return {"recommend": False, "reason": "vault-configured", "link": POKEVAULT_LINK}
    # No remembered decline ⇒ recommend.
    accepted = settings.get("acceptedDefaults")
    entry = accepted.get(_VAULT_REC_ITEM) if isinstance(accepted, dict) else None
    if not isinstance(entry, dict):
        return {"recommend": True, "reason": "no-vault", "link": POKEVAULT_LINK}
    # A decline exists — apply the (inverted) version clause to decide lapse.
    recorded_v = entry.get("v")
    stamp_sha = _current_git_sha(home)
    clause_skipped = stamp_sha in (None, "", "unknown")
    if clause_skipped:
        # No comparable stamp ⇒ clause skipped ⇒ decline governs ⇒ hold.
        return {"recommend": False, "reason": "declined", "link": POKEVAULT_LINK}
    if recorded_v != stamp_sha:
        return {"recommend": True, "reason": "decline-lapsed", "link": POKEVAULT_LINK}
    return {"recommend": False, "reason": "declined", "link": POKEVAULT_LINK}


def record_vault_decline(home: str | Path | None = None) -> None:
    """Remember the operator's PokeVault decline (EV-1) — thin ``record_accepted_defaults`` wrapper.

    Writes ``acceptedDefaults["vault-recommendation"] = {value: "declined", v:
    <current stamp gitSha or "unknown">, at: <ISO-8601 UTC>}`` — the existing C-1
    schema, no new store. ``v`` stamps the current ``.kata-version`` ``gitSha`` so
    ``vault_recommendation`` can re-arm on the next upgrade (a ``gitSha`` change);
    a stamp that is absent/blank/``"unknown"`` records ``"unknown"`` and the decline
    then HOLDS until a comparable stamp appears (dev in-repo posture).

    Fail-closed inherited from ``record_accepted_defaults`` (C-4): a corrupt
    ``.kata-settings.json`` RAISES ``ValueError`` and is left byte-unchanged.
    """
    stamp_sha = _current_git_sha(home)
    v = stamp_sha if stamp_sha else "unknown"  # None/"" ⇒ "unknown"; "unknown" preserved
    record_accepted_defaults(
        {_VAULT_REC_ITEM: {"value": "declined", "v": v, "at": _utc_now_iso()}},
        home,
    )
