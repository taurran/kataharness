"""kata_settings.py — the central-install settings file for KataHarness.

KataHarness lives in one central place ("harness home") and remembers **two
settings** so each run can find the project to work on:

- ``parentDir`` — the default parent project folder (overridable per run).
- ``vaultDir``  — where the vault / second brain sits (optional; the learning
  component reads/writes here). Absent ⇒ learning is a no-op (BC1).

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

Security: operator-supplied paths are ``..``-guarded (CWE-23) then resolved to
absolute before storage, mirroring gate_emit._safe_path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

SETTINGS_FILENAME = ".kata-settings.json"
SETTINGS_VERSION = 1


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
