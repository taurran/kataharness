"""kata_preflight.py — guarded PRE-FLIGHT engine (Spec D / N1).

Implements the deterministic PRE-FLIGHT spine phase: read + verify the frozen
manifest, run guarded installs (argv built from structured fields ONLY), re-verify,
record to the machine-global D-registry, probe the target env, emit a cleanup report,
and write ``.kata/preflight.json``.

Public API
----------
run_preflight(repo_root, *, runner, snyk_check, sandbox_check, ...) -> dict
    The deterministic engine.  Returns a dict matching N3 (preflight.json schema).

preflight_required(repo_root) -> bool
    True iff ``kata.dependencies.json`` is present at ``repo_root``.

gate_status(repo_root) -> "ready" | "blocked" | "degraded" | "absent"
    Read ``.kata/preflight.json`` status field; "absent" if missing / malformed.

_build_argv(dep, registry_url) -> list[str]
    Build install argv from structured manifest fields (manager allowlist → forced
    registry, H1 guards).  Exported so the skill layer and tests can verify it
    directly.

_validate_field_value(value, field_name) -> None
    H1 guard: reject leading ``-`` and invalid charsets.  Raises ValueError.

ALLOWED_MANAGERS : frozenset[str]
    The hard global allowlist of install managers.

Security model
--------------
- The freeform ``install`` field is **documentation-only — NEVER read or executed**
  (LD2/LD3).  Only structured fields (``manager``, ``package``, ``version``) are used
  to build argv.
- ``shell=True`` is **never** used anywhere in this module (mirrors
  ``tools/kata_dispatch.py:171``).
- **H1 (flag-injection):** ``_validate_field_value`` rejects any field value starting
  with ``-``; ``_build_argv`` inserts ``--`` before positional package args.
- **H2 (approval-hash):** ``run_preflight`` computes the SHA-256 of
  ``kata.dependencies.json`` and compares it to the approved hash in the distinct
  freeze artifact (not beside the manifest).  Mismatch → ``blocked`` + escalate.
- **CWE-23:** every operator-supplied path is ``..``-guarded by ``_safe_abs``
  (mirrors ``tools/kata_settings.py:39-44``).

Reuse citations (verify-before-reuse — ``protocol/reuse-claims.md``)
----------------------------------------------------------------------
- ``_COMMAND_BUILDERS``-style fixed table:  tools/kata_dispatch.py:150
- injectable runner pattern:               tools/kata_dispatch.py:168-173
- ``_safe_abs`` ``..``-guard:              tools/kata_settings.py:39-44
- gate artifact emit path:                 tools/gate_emit.py:94-150
- ``preflight`` config block:              protocol/config.md:29-36
- ``target.baselineGate``:                 protocol/config.md:22
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

#: Hard global allowlist of install managers (LD3).
#: A ``manager`` value not in this set is always rejected, regardless of config.
ALLOWED_MANAGERS: frozenset[str] = frozenset({"pip", "uv", "npm", "cargo"})

# Forced registry URLs per manager — the manifest CANNOT override these (LD3).
# Mirrors the ``_COMMAND_BUILDERS`` registry-force pattern (kata_dispatch.py:150).
_MANAGER_REGISTRY_URLS: dict[str, str] = {
    "pip": "https://pypi.org/simple",
    "uv": "https://pypi.org/simple",
    "npm": "https://registry.npmjs.org",
    "cargo": "sparse+https://index.crates.io/",
}

# H1: safe charset for ``package`` and ``version`` field values.
# Allows alnum + . - _ / @ : + (covers PEP-508, npm, semver, crates.io).
_SAFE_CHARS_RE = re.compile(r"^[A-Za-z0-9.\-_/@:+]+$")

_REGISTRY_VERSION = 1
_DEFAULT_FREEZE_APPROVAL_FILENAME = "kata.freeze-approval.json"

# Type aliases (Python 3.12+; kept for clarity even at 3.12 minimum)
RunnerType = Callable[[list[str]], tuple[int, str]]
SnykCheckType = Callable[[str, str], bool]  # (package, version) -> True=safe/False=blocked


# ---------------------------------------------------------------------------
# CWE-23 path guard — mirrors kata_settings._safe_abs (tools/kata_settings.py:39-44)
# ---------------------------------------------------------------------------

def _safe_abs(raw: str | Path) -> Path:
    """Reject ``..`` traversal (CWE-23) then resolve to an absolute path.

    Mirrors ``kata_settings._safe_abs`` (``tools/kata_settings.py:39-44``).
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"kata_preflight: refusing path with '..' traversal: {raw!r}"
        )
    return p.resolve()


# ---------------------------------------------------------------------------
# H1: field-value guard
# ---------------------------------------------------------------------------

def _validate_field_value(value: str, field_name: str) -> None:
    """H1 flag-injection guard: reject leading ``-`` and unsafe charsets.

    Raises ``ValueError`` on violation.  Called by ``_build_argv`` before any
    field value is placed into an argv list (DESIGN §8 H1).
    """
    if not value:
        raise ValueError(f"Field {field_name!r} is empty")
    if value.startswith("-"):
        raise ValueError(
            f"Field {field_name!r} starts with '-' (flag injection risk): {value!r}"
        )
    if not _SAFE_CHARS_RE.match(value):
        raise ValueError(
            f"Field {field_name!r} contains invalid characters: {value!r}"
        )


# ---------------------------------------------------------------------------
# Argv builder — mirrors ``_COMMAND_BUILDERS`` (tools/kata_dispatch.py:150)
# ---------------------------------------------------------------------------

def _build_argv(dep: dict, registry_url: str | None) -> list[str]:
    """Build install argv from structured manifest fields ONLY.

    Never reads or uses the freeform ``install`` field (LD2/LD3).
    Mirrors the ``_COMMAND_BUILDERS``-style table at ``tools/kata_dispatch.py:150``.

    H1 guards applied:
    - ``manager`` must be in ``ALLOWED_MANAGERS``.
    - ``package`` and ``version`` must pass ``_validate_field_value``.
    - ``--`` end-of-options separator inserted before positional package args.

    Args:
        dep:          A dependency dict from the manifest.
        registry_url: The forced registry/index URL (from ``preflight.allowed_registries``).
                      ``None`` omits the flag (tests / offline use).

    Returns:
        A ``list[str]`` argv suitable for ``subprocess.run(argv, shell=False)``.

    Raises:
        ValueError: if ``manager`` ∉ ``ALLOWED_MANAGERS``, or ``package``/``version``
                    is missing or fails validation.
    """
    manager = dep.get("manager")
    if manager not in ALLOWED_MANAGERS:
        raise ValueError(
            f"manager {manager!r} not in allowlist {sorted(ALLOWED_MANAGERS)!r}"
        )

    package: str | None = dep.get("package")
    version: str | None = dep.get("version")

    if not package:
        raise ValueError("Missing required structured field 'package'")
    if not version:
        raise ValueError("Missing required structured field 'version'")

    # H1: validate before placing into argv
    _validate_field_value(package, "package")
    _validate_field_value(version, "version")

    # Builder table — each path inserts ``--`` before positional package args (H1)
    if manager == "pip":
        argv: list[str] = ["pip", "install"]
        if registry_url:
            argv += ["--index-url", registry_url]
        argv += ["--", f"{package}=={version}"]

    elif manager == "uv":
        argv = ["uv", "pip", "install"]
        if registry_url:
            argv += ["--index-url", registry_url]
        argv += ["--", f"{package}=={version}"]

    elif manager == "npm":
        argv = ["npm", "install"]
        if registry_url:
            argv += ["--registry", registry_url]
        argv += ["--", f"{package}@{version}"]

    elif manager == "cargo":
        argv = ["cargo", "install"]
        if registry_url:
            argv += ["--registry", registry_url]
        # cargo: --version flag carries the pinned version; ``--`` separates the crate name
        argv += ["--version", version, "--", package]

    else:  # pragma: no cover — ALLOWED_MANAGERS check above is the gate
        raise ValueError(f"No argv builder for manager {manager!r}")

    return argv


# ---------------------------------------------------------------------------
# Manifest hash (H2 / LD8)
# ---------------------------------------------------------------------------

def _compute_manifest_hash(manifest_path: Path) -> str:
    """Compute the SHA-256 hex digest of the manifest file bytes."""
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _load_approved_hash(approved_hash_path: Path) -> str | None:
    """Load the approved manifest hash from the distinct freeze artifact.

    Returns ``None`` if the artifact is missing, unreadable, or malformed.
    The freeze artifact is **not** co-located with ``kata.dependencies.json``
    (H2 tamper-resistance: they live at different paths, committed separately).
    """
    if not approved_hash_path.exists():
        return None
    try:
        data = json.loads(approved_hash_path.read_text(encoding="utf-8"))
        return data.get("manifestHash") or None
    except (json.JSONDecodeError, OSError):
        return None


# ---------------------------------------------------------------------------
# Default subprocess runner (no shell=True) — mirrors kata_dispatch.py:168-173
# ---------------------------------------------------------------------------

def _default_runner(argv: list[str]) -> tuple[int, str]:
    """Default real runner: ``subprocess.run(argv)`` with ``shell=False``.

    Mirrors ``_subprocess_runner`` at ``tools/kata_dispatch.py:168-173``.
    ``shell=True`` is **never** used — this is the structural guard that kills
    the ``curl|bash`` / untrusted-index injection class (LD2/LD3).
    """
    import subprocess  # noqa: PLC0415  (lazy to keep import light for pure-unit tests)

    result = subprocess.run(argv, capture_output=True, text=True)  # noqa: S603
    return result.returncode, result.stdout


# ---------------------------------------------------------------------------
# Default Snyk SCA check seam
# ---------------------------------------------------------------------------

def _default_snyk_check(package: str, version: str) -> bool:
    """Seam for the Snyk SCA pre-install gate (DESIGN LD3).

    Returns ``True`` (safe) when no scanner is wired in.  The skill layer
    (Slice B) injects the real ``mcp__Snyk__snyk_sca_scan`` call.
    """
    return True


# ---------------------------------------------------------------------------
# D-registry read/write (N4 — ~/.kata/installed-registry.json)
# ---------------------------------------------------------------------------

def _registry_path(home_dir: Path) -> Path:
    return home_dir / ".kata" / "installed-registry.json"


def _read_registry(registry_p: Path) -> dict:
    """Read the D-registry; return an empty registry if missing / corrupt."""
    if not registry_p.exists():
        return {"registryVersion": _REGISTRY_VERSION, "installs": []}
    try:
        return json.loads(registry_p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"registryVersion": _REGISTRY_VERSION, "installs": []}


def _write_registry(registry_p: Path, registry: dict) -> None:
    registry_p.parent.mkdir(parents=True, exist_ok=True)
    registry_p.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _record_install(
    dep: dict,
    project_path: str | None,
    branch: str | None,
    home_dir: Path,
) -> None:
    """Append an install record to the machine-global D-registry (N4 schema)."""
    reg_p = _registry_path(home_dir)
    registry = _read_registry(reg_p)
    registry["installs"].append(
        {
            "package": dep.get("package", ""),
            "version": dep.get("version", ""),
            "source": dep.get("source", ""),
            "scope": dep.get("scope", "global"),
            "classification": dep.get("classification", "build-time"),
            "project": project_path or "",
            "branch": branch or "",
            "installedAt": datetime.now(timezone.utc).isoformat(),
            "used": True,
        }
    )
    _write_registry(reg_p, registry)


# ---------------------------------------------------------------------------
# Cleanup report (PF-2, LD6) — reference-count across projects
# ---------------------------------------------------------------------------

def _compute_cleanup_report(registry: dict) -> list[dict]:
    """Reference-count each package across all recorded projects' manifests.

    Conservative rule (DESIGN §4 N4): a recorded project path that no longer
    exists or whose manifest is unreadable ⇒ treat the package as **still needed**
    (skip-and-note) — never recommend removal on incomplete evidence.
    ``used`` defaults ``True``; it is only ever set ``False`` by an explicit human
    cleanup action, never inferred here.

    Returns a list of ``{"package": str, "safe_to_remove": bool}`` dicts.
    """
    installs: list[dict] = registry.get("installs", [])

    # Group install records by package name
    pkg_to_projects: dict[str, set[str]] = {}
    for rec in installs:
        pkg = rec.get("package", "")
        if not pkg:
            continue
        project = rec.get("project", "")
        if pkg not in pkg_to_projects:
            pkg_to_projects[pkg] = set()
        pkg_to_projects[pkg].add(project)

    recommendations: list[dict] = []
    for pkg, projects in pkg_to_projects.items():
        still_needed = False
        for project in projects:
            if not project:
                # Unknown project path → conservative
                still_needed = True
                break
            try:
                manifest_p = Path(project) / "kata.dependencies.json"
                if not manifest_p.exists():
                    # Project path missing → conservative (never recommend removal)
                    still_needed = True
                    break
                manifest = json.loads(manifest_p.read_text(encoding="utf-8"))
                if any(
                    d.get("package") == pkg for d in manifest.get("dependencies", [])
                ):
                    still_needed = True
                    break
            except Exception:  # noqa: BLE001 — any I/O or parse error → conservative
                still_needed = True
                break

        recommendations.append(
            {"package": pkg, "safe_to_remove": not still_needed}
        )

    return recommendations


# ---------------------------------------------------------------------------
# preflight.json writer
# ---------------------------------------------------------------------------

def _write_preflight(repo_root: Path, result: dict) -> None:
    """Write ``result`` to ``.kata/preflight.json``."""
    out_dir = repo_root / ".kata"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "preflight.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def preflight_required(repo_root: str | Path) -> bool:
    """Return ``True`` iff a ``kata.dependencies.json`` manifest is present.

    Used by the ``kata-orchestrate`` N5 precondition (Slice B) to determine whether
    the BC path (no deps declared) applies.
    """
    return (_safe_abs(repo_root) / "kata.dependencies.json").exists()


def gate_status(repo_root: str | Path) -> str:
    """Return the status from ``.kata/preflight.json``, or ``"absent"``.

    Called by ``kata-orchestrate`` Preconditions §0 (Slice B) — the orchestrate
    precondition stays thin; the decision logic lives here (tested).

    Returns:
        ``"ready"`` | ``"blocked"`` | ``"degraded"`` | ``"absent"``
    """
    pf_path = _safe_abs(repo_root) / ".kata" / "preflight.json"
    if not pf_path.exists():
        return "absent"
    try:
        data = json.loads(pf_path.read_text(encoding="utf-8"))
        status = data.get("status", "")
        if status in {"ready", "blocked", "degraded"}:
            return status
        return "absent"
    except (json.JSONDecodeError, OSError):
        return "absent"


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

def run_preflight(
    repo_root: str | Path,
    *,
    kata_config: dict | None = None,
    runner: RunnerType | None = None,
    snyk_check: SnykCheckType | None = None,
    sandbox_check: Callable[[], bool] | None = None,
    home_dir: str | Path | None = None,
    approved_hash_path: str | Path | None = None,
    project_path: str | None = None,
    branch: str | None = None,
) -> dict:
    """Run the PRE-FLIGHT engine.

    Returns a dict matching the N3 ``preflight.json`` schema (DESIGN §4 N3).

    All parameters except ``repo_root`` are keyword-only for safe, explicit
    call sites (no positional-arg surprises in the skill layer).

    Args:
        repo_root:
            Working-branch root where ``kata.dependencies.json`` lives.
            ``..``-guarded (CWE-23).
        kata_config:
            Full ``kata.config`` dict.  The engine reads the ``preflight`` block
            (``protocol/config.md:29-36``) and ``target.baselineGate``
            (``protocol/config.md:22``).  Safe defaults when absent.
        runner:
            Injectable ``(argv: list[str]) -> (exit_code: int, stdout: str)``.
            Used for both ``verify`` and ``install`` calls.  Default: real
            ``subprocess.run(argv, shell=False)`` (no ``shell=True`` — LD2).
        snyk_check:
            Injectable ``(package: str, version: str) -> bool`` (True = safe).
            Default: always safe (no-op seam; the skill layer wires the real call).
        sandbox_check:
            Injectable ``() -> bool`` (True = a sandbox/container is available).
            Default: always available.
        home_dir:
            Override for the D-registry home directory.  Injectable in tests so
            the real ``~/.kata/`` is never touched.
        approved_hash_path:
            Override path to the freeze approval artifact (H2).  Default:
            ``<repo_root>/.kata/kata.freeze-approval.json``.
        project_path:
            Recorded in D-registry install entries (for cleanup reference-counting).
        branch:
            Recorded in D-registry install entries.

    Returns:
        N3 schema dict with keys:
            ``status``    — ``"ready"`` | ``"blocked"`` | ``"degraded"``
            ``deps``      — per-dep result list
            ``installed`` — ``["<name@version>"]`` installed this run
            ``targetEnv`` — ``{gate, runnable}`` or ``None``
            ``warnings``  — list of operator-facing warnings
            ``blockers``  — list of block reasons (non-empty ⇒ ``blocked``)
            ``sandbox``   — ``"isolated"`` | ``"host"``
            ``cleanup``   — cleanup recommendation list

    Security:
        - The freeform ``dep["install"]`` field is **never read or executed**.
        - ``shell=True`` is never used.
        - All paths are ``..``-guarded.
    """
    # --- Resolve + validate paths (CWE-23 gate at the boundary) ---
    repo_root_p: Path = _safe_abs(repo_root)
    real_home: Path = _safe_abs(home_dir) if home_dir is not None else Path.home()

    # --- Resolve approved-hash path (H2) ---
    if approved_hash_path is not None:
        real_approved_hash_p: Path = _safe_abs(approved_hash_path)
    else:
        real_approved_hash_p = (
            repo_root_p / ".kata" / _DEFAULT_FREEZE_APPROVAL_FILENAME
        )

    # --- Wire injectable defaults ---
    real_runner: RunnerType = runner or _default_runner
    real_snyk_check: SnykCheckType = snyk_check or _default_snyk_check
    real_sandbox_check: Callable[[], bool] = sandbox_check or (lambda: True)

    # --- Extract preflight config (protocol/config.md:29-36) ---
    kata_cfg: dict = kata_config or {}
    preflight_cfg: dict = kata_cfg.get("preflight", {})
    allowed_registries: set[str] = set(
        preflight_cfg.get("allowed_registries", list(ALLOWED_MANAGERS))
    )
    scan_required: bool = bool(preflight_cfg.get("scan_required", True))
    sandbox_required: bool = bool(preflight_cfg.get("sandbox_required", False))

    # --- Extract target config (protocol/config.md:22) ---
    target_cfg: dict = kata_cfg.get("target", {})
    target_baseline_gate: str | None = target_cfg.get("baselineGate") or None

    # =========================================================================
    # BC: no manifest → PRE-FLIGHT not required → ready immediately (DESIGN §5)
    # =========================================================================
    manifest_path: Path = repo_root_p / "kata.dependencies.json"
    if not manifest_path.exists():
        result: dict = {
            "status": "ready",
            "deps": [],
            "installed": [],
            "targetEnv": None,
            "warnings": [],
            "blockers": [],
            "sandbox": "isolated",
            "cleanup": [],
        }
        _write_preflight(repo_root_p, result)
        return result

    # =========================================================================
    # H2 / LD8: manifest-hash check (tamper-detect post-freeze edits)
    # =========================================================================
    manifest_hash: str = _compute_manifest_hash(manifest_path)
    approved_hash: str | None = _load_approved_hash(real_approved_hash_p)

    if approved_hash is None:
        result = {
            "status": "blocked",
            "deps": [],
            "installed": [],
            "targetEnv": None,
            "warnings": [],
            "blockers": [
                "missing freeze approval artifact — run kata-freeze to record the "
                "approved manifest hash before kata-preflight can auto-install (LD8/H2)"
            ],
            "sandbox": "isolated",
            "cleanup": [],
        }
        _write_preflight(repo_root_p, result)
        return result

    if approved_hash != manifest_hash:
        result = {
            "status": "blocked",
            "deps": [],
            "installed": [],
            "targetEnv": None,
            "warnings": [],
            "blockers": [
                f"manifest hash mismatch — manifest was changed after freeze approval "
                f"(approved={approved_hash[:12]}…, actual={manifest_hash[:12]}…). "
                "Re-freeze required before auto-install proceeds (LD8/H2)."
            ],
            "sandbox": "isolated",
            "cleanup": [],
        }
        _write_preflight(repo_root_p, result)
        return result

    # =========================================================================
    # LD4: sandbox check — sandbox_required:true + no sandbox → blocked
    # =========================================================================
    sandbox_ok: bool = real_sandbox_check()

    if sandbox_required and not sandbox_ok:
        result = {
            "status": "blocked",
            "deps": [],
            "installed": [],
            "targetEnv": None,
            "warnings": [],
            "blockers": [
                "sandbox_required:true but no sandbox/container is available (LD4). "
                "Provide an isolated environment or set sandbox_required:false to allow "
                "host installation with a degraded warning."
            ],
            "sandbox": "host",
            "cleanup": [],
        }
        _write_preflight(repo_root_p, result)
        return result

    sandbox_status: str = "isolated" if sandbox_ok else "host"

    # =========================================================================
    # Read manifest
    # =========================================================================
    try:
        manifest_data: dict = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        result = {
            "status": "blocked",
            "deps": [],
            "installed": [],
            "targetEnv": None,
            "warnings": [],
            "blockers": [f"manifest unreadable: {exc}"],
            "sandbox": sandbox_status,
            "cleanup": [],
        }
        _write_preflight(repo_root_p, result)
        return result

    deps: list[dict] = manifest_data.get("dependencies", [])

    # =========================================================================
    # Process each dependency
    # =========================================================================
    installed_this_run: list[str] = []
    dep_results: list[dict] = []
    blockers: list[str] = []
    warnings: list[str] = []
    overall_status: str = "ready"

    for dep in deps:
        name: str = dep.get("name", "<unknown>")
        manager: str | None = dep.get("manager")

        # ---- Guard 1: manager must be in BOTH the global allowlist AND the config's allowed_registries
        if manager not in ALLOWED_MANAGERS or manager not in allowed_registries:
            blockers.append(
                f"dep {name!r}: manager {manager!r} not in allowlist "
                f"(ALLOWED_MANAGERS={sorted(ALLOWED_MANAGERS)!r}, "
                f"config.allowed_registries={sorted(allowed_registries)!r})"
            )
            dep_results.append(
                {
                    "name": name, "verify": "failed", "action": "skipped",
                    "source": dep.get("source", ""), "scope": dep.get("scope", ""),
                    "classification": dep.get("classification", ""),
                }
            )
            overall_status = "blocked"
            continue

        # ---- Guard 2: required structured fields
        package: str | None = dep.get("package")
        version: str | None = dep.get("version")

        missing_fields = [f for f, v in [("package", package), ("version", version)] if not v]
        if missing_fields:
            blockers.append(
                f"dep {name!r}: missing required structured fields: {missing_fields} "
                "(the freeform 'install' string is docs-only and is never executed)"
            )
            dep_results.append(
                {
                    "name": name, "verify": "failed", "action": "skipped",
                    "source": dep.get("source", ""), "scope": dep.get("scope", ""),
                    "classification": dep.get("classification", ""),
                }
            )
            overall_status = "blocked"
            continue

        # ---- Guard 3: H1 field-value validation (called here; also inside _build_argv)
        try:
            _validate_field_value(package, "package")  # type: ignore[arg-type]
            _validate_field_value(version, "version")   # type: ignore[arg-type]
        except ValueError as exc:
            blockers.append(f"dep {name!r}: {exc}")
            dep_results.append(
                {
                    "name": name, "verify": "failed", "action": "skipped",
                    "source": dep.get("source", ""), "scope": dep.get("scope", ""),
                    "classification": dep.get("classification", ""),
                }
            )
            overall_status = "blocked"
            continue

        # ---- Verify presence (run the dep's `verify` command)
        verify_cmd: str = dep.get("verify", "")
        dep_present: bool = False
        if verify_cmd:
            try:
                verify_argv = shlex.split(verify_cmd)
                exit_code, _ = real_runner(verify_argv)
                dep_present = exit_code == 0
            except Exception:  # noqa: BLE001
                dep_present = False

        if dep_present:
            dep_results.append(
                {
                    "name": name, "verify": "ok", "action": "present",
                    "source": dep.get("source", ""), "scope": dep.get("scope", ""),
                    "classification": dep.get("classification", ""),
                }
            )
            continue

        # ---- Dep is missing → Snyk SCA pre-install gate (LD3)
        if scan_required:
            is_safe: bool = real_snyk_check(package, version)  # type: ignore[arg-type]
            if not is_safe:
                blockers.append(
                    f"dep {name!r}: Snyk SCA scan blocked install of "
                    f"{package}@{version} (preflight.scan_required:true, LD3)"
                )
                dep_results.append(
                    {
                        "name": name, "verify": "failed", "action": "skipped",
                        "source": dep.get("source", ""), "scope": dep.get("scope", ""),
                        "classification": dep.get("classification", ""),
                    }
                )
                overall_status = "blocked"
                continue

        # ---- Build argv from structured fields (NEVER from freeform `install` string)
        # NOTE: dep.get("install") — the freeform install string — is intentionally
        # NEVER read or executed anywhere in this engine (LD2/LD3).
        registry_url: str | None = _MANAGER_REGISTRY_URLS.get(manager)  # type: ignore[arg-type]
        try:
            install_argv = _build_argv(dep, registry_url)
        except ValueError as exc:
            blockers.append(f"dep {name!r}: argv build failed — {exc}")
            dep_results.append(
                {
                    "name": name, "verify": "failed", "action": "skipped",
                    "source": dep.get("source", ""), "scope": dep.get("scope", ""),
                    "classification": dep.get("classification", ""),
                }
            )
            overall_status = "blocked"
            continue

        # ---- Run install (injectable runner, no shell=True — LD2)
        install_exit, _ = real_runner(install_argv)
        if install_exit != 0:
            blockers.append(
                f"dep {name!r}: install command exited {install_exit} (non-zero = failed)"
            )
            dep_results.append(
                {
                    "name": name, "verify": "failed", "action": "installed",
                    "source": dep.get("source", ""), "scope": dep.get("scope", ""),
                    "classification": dep.get("classification", ""),
                }
            )
            overall_status = "blocked"
            continue

        # ---- Re-verify after install (default-FAIL / LD7)
        re_verify_ok: bool
        if verify_cmd:
            try:
                re_verify_argv = shlex.split(verify_cmd)
                rv_exit, _ = real_runner(re_verify_argv)
                re_verify_ok = rv_exit == 0
            except Exception:  # noqa: BLE001
                re_verify_ok = False
        else:
            # No verify command supplied: accept install at face value
            re_verify_ok = True

        if not re_verify_ok:
            blockers.append(
                f"dep {name!r}: re-verify failed after install — default-FAIL (LD7). "
                "The package installed but its verify command returned non-zero."
            )
            dep_results.append(
                {
                    "name": name, "verify": "failed", "action": "installed",
                    "source": dep.get("source", ""), "scope": dep.get("scope", ""),
                    "classification": dep.get("classification", ""),
                }
            )
            overall_status = "blocked"
            continue

        # ---- Record successful install to D-registry (N4)
        _record_install(dep, project_path, branch, real_home)
        installed_this_run.append(f"{package}@{version}")
        dep_results.append(
            {
                "name": name, "verify": "ok", "action": "installed",
                "source": dep.get("source", ""), "scope": dep.get("scope", ""),
                "classification": dep.get("classification", ""),
            }
        )

    # =========================================================================
    # PF-3 / LD5: target-env probe (protocol/config.md:22 — target.baselineGate)
    # =========================================================================
    targetEnv: dict | None = None
    if target_baseline_gate:
        try:
            gate_argv = shlex.split(target_baseline_gate)
            gate_exit, _ = real_runner(gate_argv)
            gate_runnable = gate_exit == 0
        except Exception:  # noqa: BLE001
            gate_runnable = False

        targetEnv = {"gate": target_baseline_gate, "runnable": gate_runnable}
        if not gate_runnable:
            if overall_status == "ready":
                overall_status = "degraded"
            warnings.append(
                f"target baseline gate {target_baseline_gate!r} failed → "
                "targetEnv.runnable=false → degraded (PF-3/LD5)"
            )

    # =========================================================================
    # LD4: sandbox-degraded path (sandbox_required:false + no sandbox)
    # =========================================================================
    if not sandbox_ok and overall_status != "blocked":
        overall_status = "degraded"
        warnings.append(
            "no sandbox available — installed on host (sandbox_required:false, LD4). "
            "Operator must explicitly accept this degraded run before the loop dispatches."
        )

    # =========================================================================
    # PF-2 / LD6: cleanup report (reference-counted across all recorded projects)
    # =========================================================================
    reg_p = _registry_path(real_home)
    registry = _read_registry(reg_p)
    cleanup = _compute_cleanup_report(registry)

    # =========================================================================
    # Assemble and emit the N3 preflight.json artifact
    # =========================================================================
    result = {
        "status": overall_status,
        "deps": dep_results,
        "installed": installed_this_run,
        "targetEnv": targetEnv,
        "warnings": warnings,
        "blockers": blockers,
        "sandbox": sandbox_status,
        "cleanup": cleanup,
    }
    _write_preflight(repo_root_p, result)
    return result
