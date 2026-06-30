"""kata_version.py — version stamp and content-hash manifest for KataHarness installs.

Provides the version surface defined in the install-update-polish DESIGN §5.
This module is PURE: NO git, NO subprocess, stdlib + hashlib only.

The git SHA is always passed IN by the caller; this module never shells out.
``gitSha: "unknown"`` is a valid schema value for plain installs that run without
the bootstrap (bootstrap computes the real SHA and passes ``--git-sha <sha>``).

Public API
----------
stamp_path(home) -> Path
manifest_path(home) -> Path
write_stamp(home, *, git_sha, suite_semver, ref, link_mode, platform) -> Path
read_stamp(home) -> dict
compute_manifest(home) -> dict
write_manifest(home, *, git_sha) -> Path
read_manifest(home) -> dict
is_pristine(home, name) -> bool
suite_semver(home) -> str

Stamp schema (.kata-version):
    {
      "schema": 1,
      "gitSha": "<40-hex>|unknown",
      "suiteSemver": "0.1.0",
      "ref": "master",
      "installedAt": "<ISO-8601 UTC>",
      "linkMode": "symlink|copy|mixed",
      "platform": "claude"
    }

Manifest schema (.kata-manifest.json):
    {
      "schema": 1,
      "generatedAt": "<ISO-8601 UTC>",
      "gitSha": "<sha>|unknown",
      "skills": {
        "<name>": { "path": "skills/<cat>/<name>", "sha256": "<sha256 of SKILL.md>" }
      }
    }

Security: all operator-supplied paths are ``..``-guarded (CWE-23) before use.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

STAMP_FILENAME = ".kata-version"
MANIFEST_FILENAME = ".kata-manifest.json"
_SCHEMA = 1


# ---------------------------------------------------------------------------
# Path safety — mirror kata_settings._safe_abs convention exactly
# ---------------------------------------------------------------------------


def _safe_abs(raw: str | Path) -> Path:
    """Reject ``..`` traversal (CWE-23) then resolve to an absolute path."""
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"kata_version: refusing path with '..' traversal: {raw!r}")
    return p.resolve()


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def stamp_path(home: str | Path) -> Path:
    """Absolute path to the version stamp: ``<home>/.kata-version``."""
    return _safe_abs(home) / STAMP_FILENAME


def manifest_path(home: str | Path) -> Path:
    """Absolute path to the content-hash manifest: ``<home>/.kata-manifest.json``."""
    return _safe_abs(home) / MANIFEST_FILENAME


# ---------------------------------------------------------------------------
# Stamp write / read
# ---------------------------------------------------------------------------


def write_stamp(
    home: str | Path,
    *,
    git_sha: str,
    suite_semver: str,
    ref: str,
    link_mode: str,
    platform: str,
) -> Path:
    """Write ``.kata-version`` stamp and return its path.

    The caller is responsible for supplying ``git_sha`` (computed by the bootstrap
    shell, not this module).  ``git_sha`` may be ``"unknown"`` when the bootstrap is
    not involved (a plain install via ``install.sh`` without ``--git-sha``).

    Never shells out — no subprocess, no git.
    """
    p = stamp_path(home)
    data: dict = {
        "schema": _SCHEMA,
        "gitSha": git_sha,
        "suiteSemver": suite_semver,
        "ref": ref,
        "installedAt": datetime.now(timezone.utc).isoformat(),
        "linkMode": link_mode,
        "platform": platform,
    }
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return p


def read_stamp(home: str | Path) -> dict:
    """Read the stamp file; return ``{}`` when absent or corrupt (degrade gracefully).

    Mirrors the fail-closed-but-lenient read pattern from ``kata_settings.read_settings``.
    """
    p = stamp_path(home)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return data
    except (json.JSONDecodeError, OSError):
        return {}


# ---------------------------------------------------------------------------
# Skill enumeration (mirrors iter_skill_dirs semantics — re-implemented to
# keep kata_version independent of kata_install's internals)
# ---------------------------------------------------------------------------


def _iter_skill_dirs(home: Path) -> list[Path]:
    """Every directory containing a ``SKILL.md`` under ``skills/`` and ``modules/``.

    Exact semantics as ``kata_install.iter_skill_dirs`` — re-implemented here so
    ``kata_version`` is a standalone pure module with no engine dependency.
    """
    out: list[Path] = []
    for root in ("skills", "modules"):
        base = home / root
        if not base.is_dir():
            continue
        out.extend(sorted(p.parent for p in base.rglob("SKILL.md")))
    return out


# ---------------------------------------------------------------------------
# Manifest compute / write / read
# ---------------------------------------------------------------------------


def compute_manifest(home: str | Path) -> dict:
    """Compute the content-hash manifest for the skill tree.

    Hashes ``SKILL.md`` for every skill directory (``skills/**/SKILL.md`` +
    ``modules/**/SKILL.md``) using sha256.  Returns a manifest dict with
    ``schema``, ``generatedAt``, ``gitSha`` (empty string placeholder — the
    caller sets it via ``write_manifest``), and ``skills``.

    This function is PURE with respect to the filesystem (read-only) and
    never invokes git or any subprocess.
    """
    h = _safe_abs(home)
    skills: dict[str, dict] = {}
    for skill_dir in _iter_skill_dirs(h):
        skill_md = skill_dir / "SKILL.md"
        sha256 = hashlib.sha256(skill_md.read_bytes()).hexdigest()
        # Store path relative to home, forward-slash separated (cross-platform).
        rel = skill_dir.relative_to(h)
        skills[skill_dir.name] = {
            "path": rel.as_posix(),
            "sha256": sha256,
        }
    return {
        "schema": _SCHEMA,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "gitSha": "",  # placeholder; write_manifest injects the real value
        "skills": skills,
    }


def write_manifest(home: str | Path, *, git_sha: str) -> Path:
    """Compute + persist the content-hash manifest; return its path.

    ``git_sha`` is passed in by the caller (bootstrap or ``"unknown"`` for
    plain installs) — never computed here.
    """
    p = manifest_path(home)
    data = compute_manifest(home)
    data["gitSha"] = git_sha
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return p


def read_manifest(home: str | Path) -> dict:
    """Read the manifest; return ``{}`` when absent or corrupt (degrade gracefully)."""
    p = manifest_path(home)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return data
    except (json.JSONDecodeError, OSError):
        return {}


# ---------------------------------------------------------------------------
# is_pristine — drift / overlay-detection check
# ---------------------------------------------------------------------------


def is_pristine(home: str | Path, name: str) -> bool:
    """True iff the base ``SKILL.md`` for ``name`` matches the recorded manifest hash.

    Returns ``False`` when:
    - the manifest is absent or corrupt (fail-closed: can't confirm pristine)
    - ``name`` is not in the manifest
    - the current ``SKILL.md`` hash differs from the recorded hash (drifted)
    - the ``SKILL.md`` file no longer exists

    This is the "drift / pristine slot" check consumed by ``--update``'s minor-a
    NOTE path (DESIGN §5): call it before the engine re-link to surface any
    hand-edited tracked base files.
    """
    manifest = read_manifest(home)
    skills = manifest.get("skills", {})
    entry = skills.get(name)
    if entry is None:
        return False
    h = _safe_abs(home)
    # The manifest stores the relative path to the skill DIRECTORY; SKILL.md is inside it.
    skill_md = h / entry["path"] / "SKILL.md"
    if not skill_md.exists():
        return False
    current_sha = hashlib.sha256(skill_md.read_bytes()).hexdigest()
    return current_sha == entry["sha256"]


# ---------------------------------------------------------------------------
# suite_semver — README heuristic (mirrors kata_install._suite_version)
# ---------------------------------------------------------------------------


def suite_semver(home: str | Path) -> str:
    """Best-effort suite semver read from ``README.md``; defaults to ``"0.1.0"``.

    Re-implements the ``_suite_version`` heuristic from ``kata_install.py`` so that
    ``kata_version`` remains an independent, git-free module with no dependency on
    the engine's private helpers.  The extracted token is the first token in the
    first version-bearing README line that looks numeric (with a dot), after
    stripping a leading ``v``.
    """
    h = _safe_abs(home)
    readme = h / "README.md"
    if readme.exists():
        for line in readme.read_text(encoding="utf-8", errors="ignore").splitlines():
            low = line.lower()
            if "v0." in low or "version" in low:
                for tok in line.replace("`", " ").split():
                    t = tok.lstrip("v")
                    if t[:2].isdigit() or (t[:1].isdigit() and "." in t):
                        return t
                break
    return "0.1.0"
