"""kata_install.py — install KataHarness into a host platform from its central home.

KataHarness lives in one central place ("harness home"). This installer makes its
skills discoverable to a host agent and ensures the central settings file exists.
Multi-platform by a simple convention — one small routine per platform — not an
installer-interface taxonomy:

- ``claude`` — REAL, verified here. Flat-links every skill dir into the host skills
  folder (``~/.claude/skills/<name>``), the mechanism Claude Code discovers
  reliably regardless of the repo's category nesting; also writes the
  ``.claude-plugin/plugin.json`` manifest so the suite is plugin-distributable later.
- ``codex`` / ``kiro`` — BEST-EFFORT (documented). Same flat-link idea into that
  host's skills location; not fully verifiable without the host, so they also
  return manual steps. (Honest scope, DESIGN §IP-D testability caveat.)
- ``quick`` — NO-OP. The work/ACP host brings its own installer (core defines only
  the contract, AGENTS.md:42-46).
- unknown — generic manual-steps fallback.

Public API
----------
install(platform, harness_home=None, host_dir=None) -> dict
iter_skill_dirs(harness_home) -> list[Path]
ensure_plugin_manifest(harness_home) -> Path
copy_project(src, dest, overwrite=False) -> Path   # copy-mode (Debug Mode import)

Hard rule: this installer NEVER invokes git, so it can never run git against a
vault (PokeVault is LOCAL-ONLY). ``copy_project`` uses ``shutil`` only.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

PLUGIN_NAME = "kata"


def _safe_abs(raw: str | Path) -> Path:
    """Reject ``..`` traversal (CWE-23) then resolve to absolute."""
    # CWE-23 guard: rejects any path containing a '..' component before resolving.
    # Snyk rule python/PT on downstream path ops is suppressed in .snyk — this idiom is not recognised as a sanitizer.
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"kata_install: refusing path with '..' traversal: {raw!r}")
    return p.resolve()


def _default_home() -> Path:
    env = os.environ.get("KATA_HOME")
    if env:
        return _safe_abs(env)
    return Path(__file__).resolve().parent.parent


def iter_skill_dirs(harness_home: str | Path) -> list[Path]:
    """Every directory containing a ``SKILL.md`` under ``skills/`` and ``modules/``."""
    home = _safe_abs(harness_home)
    out: list[Path] = []
    for root in ("skills", "modules"):
        base = home / root
        if not base.is_dir():
            continue
        out.extend(sorted(p.parent for p in base.rglob("SKILL.md")))
    return out


# Reference form ``../<name>/`` inside a tier skill's SKILL.md — a single path
# segment (no slashes), so it can never escape the skill's category dir.
_REL_REF = re.compile(r"\.\./([^/\s)\]]+)/")


def iter_shared_base_dirs(harness_home: str | Path) -> list[Path]:
    """Shared tier-family base dirs: payload-only dirs referenced by sibling tier skills.

    CA-L42 fix. ``iter_skill_dirs`` returns only dirs directly containing a
    ``SKILL.md``, so a tier-family **base** dir (``kata-grill/`` holding
    ``RUBRIC.md`` + ``resources/`` but no ``SKILL.md``, likewise ``kata-plan`` /
    ``kata-review`` / ``kata-diagnose``) is never flat-linked — and a copy-mode
    install dangles the tier variants' ``../kata-grill/RUBRIC.md`` relative
    reference (the SMOKE-observed real defect). This **ADDITIVE** enumerator is a
    SEPARATE function: ``iter_skill_dirs`` keeps its exact current return contract
    (CA-L42). The Claude install path links what this returns alongside the skills.

    Detection — a dir under ``skills/`` that (the *no-SKILL.md-but-payload*
    discriminator):

    1. is **referenced** by a sibling tier skill's ``../<name>/`` relative path, and
    2. is a directory that contains **NO ``SKILL.md``** (else it is itself a real
       skill, already owned by ``iter_skill_dirs``), and
    3. **carries payload** (is non-empty).

    Everything else is dropped — "referenced by sibling tier skills' relative
    paths" is the whole rule. Stdlib-only; never invokes git.
    """
    home = _safe_abs(harness_home)
    skills_root = (home / "skills").resolve()
    skill_dirs = iter_skill_dirs(home)

    candidates: set[Path] = set()
    for sk in skill_dirs:
        skill_md = sk / "SKILL.md"
        try:
            text = skill_md.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for name in _REL_REF.findall(text):
            if name in ("", ".", ".."):
                continue  # never a bare traversal segment
            candidates.add((sk.parent / name).resolve())

    out: list[Path] = []
    for cand in candidates:
        # Structurally can't escape skills/ (single segment, '..' filtered), but
        # pin the invariant explicitly ("a dir under skills/").
        if not cand.is_relative_to(skills_root):
            continue
        if not cand.is_dir():
            continue
        if (cand / "SKILL.md").exists():  # a real skill dir — iter_skill_dirs owns it
            continue
        if not any(cand.iterdir()):  # no payload — nothing to link
            continue
        out.append(cand)
    return sorted(set(out))


def _suite_version(home: Path) -> str:
    """Best-effort suite version (README line or a default); never fails the install."""
    readme = home / "README.md"
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


def ensure_plugin_manifest(harness_home: str | Path) -> Path:
    """Create ``<home>/.claude-plugin/plugin.json`` if absent; return its path."""
    home = _safe_abs(harness_home)
    manifest_dir = home / ".claude-plugin"
    manifest = manifest_dir / "plugin.json"
    if not manifest.exists():
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps(
                {
                    "name": PLUGIN_NAME,
                    "description": "KataHarness - a tool-agnostic, skills-based agent harness (the Kata Loop).",
                    "version": _suite_version(home),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return manifest


_MARKER = ".kata-managed"
_OVERLAY_MATERIALIZED_MARKER = ".kata-overlay-materialized"
_COMMANDS_MANIFEST = ".kata-commands.json"


def _link_or_copy(src_dir: Path, dst_dir: Path) -> str:
    """Link ``src_dir`` at ``dst_dir`` (idempotent); fall back to copy. Returns the method.

    Idempotency NEVER clobbers a directory KataHarness did not create: a prior
    symlink (ours) is unlinked; a prior copy is replaced ONLY if it carries the
    ``.kata-managed`` marker; any other pre-existing directory raises rather than
    being silently ``rmtree``'d (prevents data loss on a name collision).
    """
    if dst_dir.is_symlink():
        dst_dir.unlink()
    elif dst_dir.exists():
        if not (dst_dir / _MARKER).exists():
            raise ValueError(
                f"kata_install: refusing to overwrite non-kata directory: {dst_dir} "
                f"(no {_MARKER} marker — remove it manually if you intend to replace it)"
            )
        shutil.rmtree(dst_dir)
    dst_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(src_dir, dst_dir, target_is_directory=True)
        return "symlink"
    except (OSError, NotImplementedError):
        # Windows without Developer Mode/admin, or an unsupported FS → copy.
        shutil.copytree(src_dir, dst_dir)
        (dst_dir / _MARKER).write_text(
            "kata-managed copy — safe to delete on uninstall.\n", encoding="utf-8"
        )
        return "copy"


def _link_or_copy_file(
    src_file: Path,
    dst_file: Path,
    harness_home: Path,
    managed_names: set[str],
) -> str | None:
    """Link (or copy) a single command file to dst_file; apply the file-collision policy.

    Unlike ``_link_or_copy`` (directory-only), this primitive operates on individual
    files so it can install into a SHARED directory (e.g. ``~/.claude/commands/``) one
    file at a time without touching other tools' files that live alongside ours.

    Collision policy (DESIGN §A2 — FROZEN)
    ----------------------------------------
    (a) **Replace only files we own** — a symlink whose resolved target is under
        ``harness_home``, or a name already recorded in ``managed_names``.
    (b) **Skip (print NOTE) any real pre-existing file we did NOT write** — never
        clobber a user's own ``~/.claude/commands/<name>.md``.

    Parameters
    ----------
    src_file:
        Source ``.md`` file inside the harness home.
    dst_file:
        Destination path (typically inside the host's ``commands/`` dir).
    harness_home:
        Resolved harness home; used to determine whether an existing symlink is ours.
    managed_names:
        Set of filenames (with ``.md`` extension) recorded in the kata commands
        manifest — names KataHarness placed on a prior install.

    Returns
    -------
    ``'symlink'``, ``'copy'``, or ``None`` (skipped — non-kata file in the way).
    """
    name = dst_file.name
    home_resolved = harness_home.resolve()

    if dst_file.is_symlink():
        # Determine ownership by resolving the symlink target.
        try:
            resolved = dst_file.resolve()
        except (OSError, RuntimeError):
            print(
                f"NOTE: {name}: cannot resolve existing symlink — "
                f"skipping to avoid data loss"
            )
            return None
        if resolved.is_relative_to(home_resolved):
            dst_file.unlink()  # ours — safe to replace
        else:
            print(
                f"NOTE: {name}: existing symlink points outside KataHarness — "
                f"skipping to avoid data loss"
            )
            return None
    elif dst_file.exists():
        # Real file — check manifest ownership.
        if name in managed_names:
            dst_file.unlink()  # we placed it — safe to replace
        else:
            print(
                f"NOTE: {name}: pre-existing file not managed by KataHarness — "
                f"skipping to avoid data loss"
            )
            return None

    dst_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(src_file, dst_file)
        return "symlink"
    except (OSError, NotImplementedError):
        # Windows without Developer Mode / unsupported FS → copy.
        shutil.copy2(src_file, dst_file)
        return "copy"


def _flat_link_commands(home: Path, host_dir: Path) -> dict:
    """Flat-link every command file from ``adapters/claude/commands/`` into ``<host_dir>/commands/``.

    Links **per-FILE** (never the whole directory) into the shared ``~/.claude/commands/``
    so other tools' command files already present are left untouched.  Tracks managed
    command filenames in ``<host_dir>/<_COMMANDS_MANIFEST>`` for idempotent re-install
    and clean uninstall.

    Mirrors ``_flat_link_skills`` in shape but operates on individual ``.md`` files
    rather than skill directories.
    """
    src_commands_dir = home / "adapters" / "claude" / "commands"
    commands_dst = host_dir / "commands"
    manifest_path = host_dir / _COMMANDS_MANIFEST

    # Load existing manifest so re-install can recognise its own prior copies.
    managed_names: set[str] = set()
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            managed_names = set(data.get("managed", []))
        except (json.JSONDecodeError, OSError):
            pass  # corrupt manifest — treat as empty; will be overwritten below

    if not src_commands_dir.is_dir():
        return {"commandsDir": str(commands_dst), "linked": [], "method": []}

    commands_dst.mkdir(parents=True, exist_ok=True)
    linked: list[str] = []
    methods: set[str] = set()
    newly_managed: set[str] = set()

    for src_file in sorted(src_commands_dir.glob("*.md")):
        dst_file = commands_dst / src_file.name
        method = _link_or_copy_file(src_file, dst_file, home, managed_names)
        if method is not None:
            linked.append(src_file.name)
            methods.add(method)
            newly_managed.add(src_file.name)

    # Write manifest with exactly the names successfully placed in this run.
    # Prior entries that were skipped (non-kata collision) are intentionally dropped
    # so the manifest stays accurate and the uninstall list stays safe.
    manifest_path.write_text(
        json.dumps({"managed": sorted(newly_managed)}, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "commandsDir": str(commands_dst),
        "linked": linked,
        "method": sorted(methods),
    }


def _flat_link_skills(home: Path, host_dir: Path, skills_subdir: str = "skills") -> dict:
    """Flat-link every skill dir into ``<host_dir>/<skills_subdir>/<name>`` (symlink, copy fallback).

    ``skills_subdir`` defaults to ``"skills"`` (the Claude-native location ``<host>/skills/``).
    Best-effort installers (codex/kiro) pass ``".agents/skills"`` — the cross-tool shared skills
    location (June-2026 snapshot; the N5 confirm probe is the standing guard against stale
    discovery paths between releases).
    """
    skills_dst = host_dir / skills_subdir
    skills_dst.mkdir(parents=True, exist_ok=True)
    skill_dirs = iter_skill_dirs(home)
    # Flat-linking keys on the dir basename — two same-named skills in different categories would
    # collide (the second silently clobbering the first). Refuse rather than lose a skill.
    names = [d.name for d in skill_dirs]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise ValueError(f"kata_install: duplicate skill names collide on flat-link: {dupes}")
    linked, methods = [], set()
    for skill_dir in skill_dirs:
        method = _link_or_copy(skill_dir, skills_dst / skill_dir.name)
        linked.append(skill_dir.name)
        methods.add(method)
    return {"skillsDir": str(skills_dst), "linked": linked, "method": sorted(methods)}


def _flat_link_shared_base_dirs(home: Path, host_dir: Path, skills_subdir: str = "skills") -> dict:
    """Flat-link shared tier-family base dirs into ``<host_dir>/<skills_subdir>/<name>``.

    CA-L42 additive companion to ``_flat_link_skills`` (the D104 install-portability
    pattern, SR-13): the payload-only base dirs from ``iter_shared_base_dirs`` are
    linked (symlink, copy fallback) so the tier variants' ``../<family>/RUBRIC.md``
    references resolve. Uses the FROZEN ``_link_or_copy`` unchanged — the frozen
    five stay byte-identical (CA-L43). Never invokes git; stdlib-only.
    """
    skills_dst = host_dir / skills_subdir
    base_dirs = iter_shared_base_dirs(home)
    if not base_dirs:
        return {"baseDirsDir": str(skills_dst), "baseDirsLinked": [], "baseDirMethod": []}
    # A base-dir basename that collides with a real skill name would clobber it on
    # flat-link. Refuse rather than lose a skill (mirrors _flat_link_skills's guard).
    skill_names = {d.name for d in iter_skill_dirs(home)}
    collisions = sorted(b.name for b in base_dirs if b.name in skill_names)
    if collisions:
        raise ValueError(
            f"kata_install: tier-family base dir names collide with skills on flat-link: {collisions}"
        )
    skills_dst.mkdir(parents=True, exist_ok=True)
    linked, methods = [], set()
    for base_dir in base_dirs:
        method = _link_or_copy(base_dir, skills_dst / base_dir.name)
        linked.append(base_dir.name)
        methods.add(method)
    return {"baseDirsDir": str(skills_dst), "baseDirsLinked": linked, "baseDirMethod": sorted(methods)}


def _install_claude(home: Path, host_dir: Path) -> dict:
    manifest = ensure_plugin_manifest(home)
    res = _flat_link_skills(home, host_dir)
    base = _flat_link_shared_base_dirs(home, host_dir)  # CA-L42 (additive, Claude-only)
    cmds = _flat_link_commands(home, host_dir)
    notes = [
        f"{len(res['linked'])} skills linked into {res['skillsDir']}",
        f"{len(cmds['linked'])} commands linked into {cmds['commandsDir']}",
    ]
    if base["baseDirsLinked"]:
        notes.append(
            f"{len(base['baseDirsLinked'])} shared tier-family base dirs linked into {base['baseDirsDir']}"
        )
    return {
        "platform": "claude",
        "ok": True,
        "manifest": str(manifest),
        **res,
        "baseDirsLinked": base["baseDirsLinked"],
        "commandsDir": cmds["commandsDir"],
        "commandsLinked": cmds["linked"],
        "notes": notes,
    }


def _install_besteffort(platform: str, home: Path, host_dir: Path | None) -> dict:
    """Codex/Kiro: flat-link into .agents/skills/ (cross-tool shared location); documented best-effort.

    ``.agents/skills/`` is the cross-tool standard skills location (June-2026 snapshot; the N5
    confirm probe is the standing guard against stale discovery paths between releases).
    The host is not fully verifiable here, so the install is flagged best-effort and returns
    manual steps for the operator to verify in-host.
    """
    result: dict = {"platform": platform, "ok": True, "bestEffort": True}
    if host_dir is not None:
        # Target .agents/skills/ — the shared cross-tool skills location (June-2026 snapshot).
        # Claude uses <host>/skills/; codex/kiro use <host>/.agents/skills/ (cross-tool standard).
        result.update(_flat_link_skills(home, host_dir, ".agents/skills"))
    result["notes"] = [
        f"{platform}: best-effort install — verify the skills folder location for {platform} "
        f"and confirm discovery in-host. See docs/SETUP.md.",
    ]
    return result


def _install_quick(home: Path, host_dir: Path | None) -> dict:
    return {
        "platform": "quick",
        "ok": True,
        "noop": True,
        "notes": ["quick/ACP brings its own installer; core defines only the contract (AGENTS.md)."],
    }


def _install_generic(platform: str, home: Path, host_dir: Path | None) -> dict:
    return {
        "platform": platform,
        "ok": False,
        "notes": [
            f"unknown platform {platform!r}: copy each skills/*/<name>/SKILL.md (and modules/*/<name>/) "
            f"into your host's skills directory. See docs/SETUP.md.",
        ],
    }


_REAL = {"claude": _install_claude}
_BEST_EFFORT = {"codex", "kiro"}


def install(
    platform: str,
    harness_home: str | Path | None = None,
    host_dir: str | Path | None = None,
) -> dict:
    """Install KataHarness into ``platform`` from ``harness_home``.

    ``host_dir`` is the host's config root (default ``~/.claude`` for claude);
    injectable so the install is testable against a tmp dir.
    """
    home = _safe_abs(harness_home) if harness_home is not None else _default_home()
    p = (platform or "").strip().casefold()

    if p == "claude":
        hd = _safe_abs(host_dir) if host_dir is not None else (Path.home() / ".claude")
        return _install_claude(home, hd)
    if p in _BEST_EFFORT:
        hd = _safe_abs(host_dir) if host_dir is not None else None
        return _install_besteffort(p, home, hd)
    if p == "quick":
        return _install_quick(home, None)
    return _install_generic(platform, home, None)


def copy_project(src: str | Path, dest: str | Path, overwrite: bool = False) -> Path:
    """Copy a project folder for copy-mode (Debug Mode import); operate on the copy.

    Uses ``shutil`` only — NEVER invokes git, so a vault source is never git-touched.
    """
    s = _safe_abs(src)
    d = _safe_abs(dest)
    if not s.is_dir():
        raise ValueError(f"kata_install.copy_project: source is not a directory: {s}")
    # Reject ANY overlap: equal, dest-is-ancestor-of-source (rmtree would delete the source!),
    # or source-is-ancestor-of-dest (copy into itself). Copy mode's whole promise is "original untouched".
    if s == d or d in s.parents or s in d.parents:
        raise ValueError(
            f"kata_install.copy_project: source and destination overlap (ancestor/descendant): {s} <-> {d}"
        )
    if d.exists():
        if not overwrite:
            raise ValueError(f"kata_install.copy_project: destination exists: {d} (pass overwrite=True)")
        shutil.rmtree(d)
    shutil.copytree(s, d)
    return d


# ---------------------------------------------------------------------------
# Confirm probe (N5) — verify a platform can run the harness headlessly
# ---------------------------------------------------------------------------

# The probe asks the model to GENERATE a transformed token (not present verbatim in the prompt),
# so a CLI that merely echoes the prompt to stdout cannot false-positive the substring check.
_PROBE_TOKEN = "SSENRAHATAK"  # "KATAHARNESS" reversed — must be produced, not echoed
_PROBE_PROMPT = "Reply with ONLY the single word KATAHARNESS spelled backwards, and nothing else."
# Only platforms with a real DISPATCH adapter (kata_dispatch._COMMAND_BUILDERS) may be confirmed
# for routing — confirming a platform we can't dispatch to would mislead the router.
# Both codex and kiro now have dispatch adapters (Slice C added kiro to _COMMAND_BUILDERS).
# The invariant _PROBE_COMMANDS ⊆ _COMMAND_BUILDERS is enforced by test (L-MP2).
# Point-in-time flags (RESEARCH §0/§6) — pin/verify at build; the confirm probe is the standing guard.
_PROBE_COMMANDS = {
    "codex": lambda: ["codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only", _PROBE_PROMPT],
    "kiro": lambda: ["kiro-cli", "chat", "--no-interactive", _PROBE_PROMPT],
}


def confirm_platform(platform: str, runner=None, home: str | Path | None = None) -> dict:
    """Confirm a platform can run the harness headlessly; record it on success (N5).

    ``runner(cmd) -> (exit_code, stdout)`` is injectable (a stub in tests; a real subprocess
    by default). The host platform ``claude`` is trivially confirmed (it's where we run).
    On success the platform is appended to ``confirmedPlatforms`` in the settings file.
    """
    p = (platform or "").strip().casefold()
    if p == "claude":
        confirmed = _record(p, home)
        return {"platform": p, "confirmed": True, "detail": "host", "confirmedPlatforms": confirmed}

    builder = _PROBE_COMMANDS.get(p)
    if builder is None:
        return {"platform": p, "confirmed": False, "detail": f"no probe command for {p!r}"}

    runner = runner or _real_probe_runner
    try:
        exit_code, stdout = runner(builder())
    except Exception as e:  # CLI absent / any launch error  # noqa: BLE001
        return {"platform": p, "confirmed": False, "detail": f"probe failed to launch: {e}"}

    ok = exit_code == 0 and _PROBE_TOKEN in (stdout or "")
    if ok:
        confirmed = _record(p, home)
        return {"platform": p, "confirmed": True, "detail": "probe ok", "confirmedPlatforms": confirmed}
    return {"platform": p, "confirmed": False, "detail": f"probe did not return {_PROBE_TOKEN} (exit {exit_code})"}


def _record(platform: str, home) -> list[str]:
    import kata_settings

    return kata_settings.add_confirmed_platform(platform, home=home)


def _real_probe_runner(cmd: list[str]):
    import subprocess  # noqa: S404 — default real runner; tests inject a stub

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL)  # noqa: S603
    return proc.returncode, proc.stdout


# ---------------------------------------------------------------------------
# Headless-surface helpers (Slice B — NEW, ADDITIVE)
# ---------------------------------------------------------------------------


def _emit(msg: str, as_json: bool = False) -> None:
    """Print a human-readable message to stdout (default) or stderr (``--json`` mode).

    Without ``--json`` the output is byte-for-byte identical to the old
    ``print()`` call, preserving the BC guarantee.
    """
    if as_json:
        print(msg, file=sys.stderr)
    else:
        print(msg)


def _exit_code_for(result: dict, exc: BaseException | None = None) -> int:
    """Map an install/uninstall result dict or exception to a semantic exit code.

    Codes
    -----
    0  OK        — ``result["ok"] is True`` (idempotent re-install, confirm ok, uninstall ok)
    1  ERROR     — generic / confirm-probe not confirmed (preserved from today)
    2  USAGE     — bad/missing args (argparse default; not mapped here)
    3  NOT_FOUND — ``ok:False`` (unknown platform); bad path; settings-write ``ValueError``
    4  PERMISSION — ``OSError`` from the link/copy fallback
    5  CONFLICT  — non-kata dir collision (the ``":118-122"`` ``ValueError``)
    """
    if exc is not None:
        if isinstance(exc, OSError):
            return 4  # PERMISSION
        if isinstance(exc, ValueError) and "non-kata" in str(exc):
            return 5  # CONFLICT
        if isinstance(exc, ValueError):
            return 3  # NOT_FOUND (bad path / settings write failure)
        return 1  # generic
    return 0 if result.get("ok") else 3  # NOT_FOUND for ok:False


def _load_answers_json(path: str | Path) -> dict:
    """Load and validate a ``--answers-json`` setup file.

    Returns the parsed dict on success.

    Raises
    ------
    FileNotFoundError
        When the path does not exist (maps to exit ``3 NOT_FOUND`` in ``main()``).
    ValueError
        For a traversal-containing path, malformed JSON, non-dict JSON, or a
        missing required key.  Maps to exit ``2 USAGE`` in ``main()``.
    """
    p = _safe_abs(path)  # raises ValueError for '..' traversal
    if not p.exists():
        raise FileNotFoundError(f"--answers-json path not found: {path!r}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"malformed --answers-json ({path!r}): {e}") from e
    if not isinstance(data, dict):
        raise ValueError(
            f"--answers-json must contain a JSON object, got {type(data).__name__!r}: {path!r}"
        )
    required = {"parentDir"}
    missing = required - data.keys()
    if missing:
        raise ValueError(
            f"--answers-json missing required key(s): {sorted(missing)} — in {path!r}"
        )
    return data


# ---------------------------------------------------------------------------
# Uninstall verb (Slice C — NEW, ADDITIVE)
# ---------------------------------------------------------------------------


def uninstall(
    platform: str,
    harness_home: str | Path | None = None,
    host_dir: str | Path | None = None,
    target_dir: str | Path | None = None,
    dry_run: bool = False,
) -> dict:
    """Reverse a KataHarness install: remove flat-linked skills, settings, and router stanza.

    Removes **only** what KataHarness created:

    - Symlinks whose resolved target is under ``harness_home`` → unlinked.
    - Directories carrying the ``.kata-managed`` marker → ``rmtree``'d.
    - Anything else → reported in ``leftIntact`` and **left intact** (never deleted).

    Also unlinks ``<harness_home>/.kata-settings.json`` and, when ``target_dir``
    is supplied, calls ``kata_router.remove_stanza(<target_dir>/AGENTS.md)``.

    This function **never invokes git** (hard rule, mirrors ``install()``).
    """
    import kata_router
    import kata_settings

    home = _safe_abs(harness_home) if harness_home is not None else _default_home()
    p = (platform or "").strip().casefold()

    removed: list[str] = []
    left_intact: list[str] = []

    # Determine skills host dir + subdir (mirrors install routing)
    skills_subdir = ".agents/skills" if p in _BEST_EFFORT else "skills"

    if host_dir is not None or p == "claude":
        hd = _safe_abs(host_dir) if host_dir is not None else (Path.home() / ".claude")
        skills_dst = hd / skills_subdir
        if skills_dst.is_dir():
            for skill_dir in iter_skill_dirs(home):
                dst = skills_dst / skill_dir.name
                if not dst.exists() and not dst.is_symlink():
                    continue  # already gone — no-op
                if dst.is_symlink():
                    try:
                        resolved = dst.resolve()
                    except (OSError, RuntimeError):
                        left_intact.append(str(dst))
                        continue
                    if resolved.is_relative_to(home.resolve()):
                        dst.unlink()
                        removed.append(skill_dir.name)
                    else:
                        left_intact.append(str(dst))
                elif dst.is_dir() and (dst / _MARKER).exists():
                    shutil.rmtree(dst)
                    removed.append(skill_dir.name)
                else:
                    # Non-kata dir occupying the slot — leave intact, report
                    left_intact.append(str(dst))

            # Sweep ALL host slots for orphaned kata-managed entries (A2: rename-orphan
            # cleanup).  The basename loop above handles current skills; this pass catches
            # any entry whose source skill was renamed or removed since the last install.
            swept_removed, swept_intact = _sweep_managed_slots(
                skills_dst, home, dry_run=dry_run
            )
            for name in swept_removed:
                if name not in removed:
                    removed.append(name)
            for path in swept_intact:
                if path not in left_intact:
                    left_intact.append(path)

        # Remove flat-linked command files + the commands manifest (2026-07-12
        # health review F3: install links adapters/claude/commands/*.md into
        # <host>/commands/ and records them in .kata-commands.json, but uninstall
        # previously left both behind as orphans). Same ownership test as skills:
        # a symlink resolving under harness_home, OR a file named in the manifest.
        commands_dst = hd / "commands"
        manifest_path = hd / _COMMANDS_MANIFEST
        managed_cmds: set[str] = set()
        if manifest_path.exists():
            try:
                managed_cmds = set(
                    json.loads(manifest_path.read_text(encoding="utf-8")).get("managed", [])
                )
            except (json.JSONDecodeError, OSError):
                managed_cmds = set()
        if commands_dst.is_dir():
            src_commands_dir = home / "adapters" / "claude" / "commands"
            candidate_names = managed_cmds | {
                f.name for f in src_commands_dir.glob("*.md")
            } if src_commands_dir.is_dir() else managed_cmds
            for name in sorted(candidate_names):
                cmd = commands_dst / name
                if not cmd.exists() and not cmd.is_symlink():
                    continue
                if cmd.is_symlink():
                    try:
                        resolved = cmd.resolve()
                    except (OSError, RuntimeError):
                        left_intact.append(str(cmd))
                        continue
                    if resolved.is_relative_to(home.resolve()):
                        cmd.unlink()
                        removed.append(f"commands/{name}")
                    else:
                        left_intact.append(str(cmd))
                elif name in managed_cmds:
                    # copy-mode install (no symlink); manifest attests ownership
                    cmd.unlink()
                    removed.append(f"commands/{name}")
                else:
                    left_intact.append(str(cmd))
        if manifest_path.exists():
            manifest_path.unlink()

    # Unlink settings file (idempotent: absent -> no-op)
    sp = kata_settings.settings_path(home)
    if sp.exists():
        sp.unlink()

    # Remove router stanza from the supplied target dir's AGENTS.md
    if target_dir is not None:
        agents_md = _safe_abs(target_dir) / "AGENTS.md"
        kata_router.remove_stanza(agents_md)

    notes: list[str] = [f"uninstalled {len(removed)} skills"]
    if left_intact:
        notes.append(f"left intact (not kata-managed): {left_intact}")

    return {
        "ok": True,
        "removed": removed,
        "leftIntact": left_intact,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Post-link hooks (A2 — NEW, ADDITIVE; Phase B/C will flesh these out)
# ---------------------------------------------------------------------------


def _materialize_pass(home: Path, host_skills_dir: Path, link_mode: str) -> None:
    """Post-link materialize pass — applies fork shadows and overlay entries (Phase B/C2).

    Runs AFTER ``_flat_link_skills`` (which laid pristine symlinks/copies for every
    skill).

    **C2 — Fork shadow precedence (fork > overlay > pristine):**

    1. Read ``agentSkills.dir`` from ``.kata-settings.json``; absent → no shadows (BC).
    2. ``kata_supersede.resolve_shadows(agentskills_dir)`` → map of upstream skill name
       to promoted fork dir.
    3. ``kata_supersede.validate_shadows(shadows, base_names)`` → STOP with
       ``ValueError("shadow validation failed: …")`` on any structural error
       (unknown upstream, double-supersede) BEFORE any slot is materialised.
    4. For each shadowed upstream skill: ``shutil.copytree`` the fork dir into the slot,
       write both ``.kata-managed`` and ``.kata-overlay-materialized`` markers, and record
       the slot in ``materialized.json`` with ``source: "fork"``.
    5. If an overlay entry also exists for a fork-shadowed skill, emit a dormant-overlay
       NOTE and skip overlay application (the overlay entry is preserved so it
       re-activates if the fork is later removed).

    **Phase B — Overlay materialization (unchanged; skips fork-shadowed skills):**

    For each skill that has an overlay entry (and no winning fork shadow) this pass
    replaces the verbatim host slot with a concrete materialized directory:

    1. Read the base SKILL.md from the home tree.
    2. Call ``kata_overlay.apply_overlay(base_text, entry)`` to compose the overlay.
    3. Remove the verbatim slot (symlink → unlink; ``.kata-managed`` copy → rmtree).
    4. ``shutil.copytree`` the base skill dir into the slot.
    5. Overwrite ``SKILL.md`` with the composed text.
    6. Write ``.kata-managed`` and ``.kata-overlay-materialized`` markers.
    7. Record the slot in ``materialized.json`` with ``source: "overlay"``.

    Skills without a fork shadow or overlay remain as pristine symlinks/copies.

    **M3 (fail-soft):** an overlay entry whose base skill no longer exists → NOTE + skip.

    **Per-skill failures** emit a NOTE and continue (fail-soft at skill granularity).

    **Structural integrity:** this function does NOT swallow structural exceptions.
    ``ValueError`` from shadow validation propagates to the caller (no partial shadow).
    The caller places this call OUTSIDE any stamp-write ``except Exception`` guard.

    Import-guarded: when ``kata_overlay`` is absent (Phase A fallback), exits as no-op.
    Never invokes git.  Never touches the 5 frozen engine fns.
    """
    try:
        import kata_overlay as _ko
    except ImportError:
        return  # kata_overlay not present — safe no-op (Phase A fallback)

    import hashlib

    # C2: Resolve fork shadows from agentSkills.dir.
    # Import-guarded separately so ImportError only suppresses the shadow path,
    # not overlay processing.  ValueError from validate_shadows propagates (no catch).
    shadows: dict[str, Path] = {}
    try:
        import kata_settings as _ks
        import kata_supersede as _kss
    except ImportError:
        _ks = None  # type: ignore[assignment]
        _kss = None  # type: ignore[assignment]

    if _ks is not None and _kss is not None:
        _settings = _ks.read_settings(home)
        _agentskills_dir = _settings.get("agentSkills", {}).get("dir")
        if _agentskills_dir:
            shadows = _kss.resolve_shadows(_agentskills_dir)
            # Validate BEFORE any materialization — fail-closed on structural errors.
            # Raises ValueError("shadow validation failed: …") if any error found.
            _base_names: set[str] = {d.name for d in iter_skill_dirs(home)}
            _errors = _kss.validate_shadows(shadows, _base_names)
            if _errors:
                raise ValueError("shadow validation failed: " + "; ".join(_errors))

    # Build a map of skill-name → base skill dir from the home tree.
    base_skill_dirs: dict[str, Path] = {d.name: d for d in iter_skill_dirs(home)}

    # Read overlay store; empty store → fast path when no shadows either.
    overlay_data = _ko.read_overlay(home)
    overlay_skills: dict = overlay_data.get("skills", {})
    if not overlay_skills and not shadows:
        return  # no overlays and no shadows — no-op

    # --- C2: Fork shadow materialization (fork > overlay > pristine) ----------------
    for upstream_name, fork_dir in shadows.items():
        slot = host_skills_dir / upstream_name

        # Determine baseMode from the current slot (as laid by _flat_link_skills).
        if slot.is_symlink():
            base_mode = "symlink"
        elif slot.is_dir() and (slot / _MARKER).exists():
            base_mode = "copy"
        else:
            base_mode = link_mode

        # Remove the verbatim slot.
        try:
            if slot.is_symlink():
                slot.unlink()
            elif slot.is_dir() and (slot / _MARKER).exists():
                shutil.rmtree(slot)
            elif slot.exists():
                print(
                    f"NOTE: fork shadow for '{upstream_name}': host slot exists but is not "
                    f"kata-managed — skipped to avoid data loss"
                )
                continue
        except OSError as exc:
            print(
                f"NOTE: fork shadow for '{upstream_name}': failed to remove verbatim slot:"
                f" {exc} — skipped"
            )
            continue

        # Copytree the fork dir into the slot.
        try:
            shutil.copytree(fork_dir, slot)
        except OSError as exc:
            print(
                f"NOTE: fork shadow for '{upstream_name}': failed to materialize fork slot:"
                f" {exc} — skipped"
            )
            continue

        # Write both markers.
        (slot / _MARKER).write_text(
            "kata-managed materialized fork shadow — safe to delete on uninstall.\n",
            encoding="utf-8",
        )
        (slot / _OVERLAY_MATERIALIZED_MARKER).write_text(
            "kata fork materialization marker — factory-reset restores pristine link.\n",
            encoding="utf-8",
        )

        # If an overlay entry also exists for this skill → emit dormant NOTE.
        # The overlay entry is preserved (not dropped) so it re-activates if the fork is removed.
        if upstream_name in overlay_skills:
            print(
                f"NOTE: overlay for '{upstream_name}' is dormant"
                f" — a superseding fork shadows it"
            )

        # Compute SHA256 of the fork's SKILL.md and record the slot.
        fork_skill_md = slot / "SKILL.md"
        applied_sha = ""
        if fork_skill_md.exists():
            fork_text = fork_skill_md.read_text(encoding="utf-8")
            applied_sha = hashlib.sha256(fork_text.encode("utf-8")).hexdigest()

        _ko.record_slot(
            home,
            upstream_name,
            {
                "hostPath": str(slot),
                "baseMode": base_mode,
                "source": "fork",
                "appliedSha": applied_sha,
            },
        )

    # --- Phase B: Overlay materialization (unchanged; skips fork-shadowed skills) ---
    for name, entry in overlay_skills.items():
        # Fork wins — skip overlay application; entry preserved in overlay.json.
        if name in shadows:
            continue

        slot = host_skills_dir / name

        # M3 fail-soft: base skill no longer in the home tree.
        base_dir = base_skill_dirs.get(name)
        if base_dir is None:
            print(
                f"NOTE: overlay for '{name}': base skill no longer exists — skipped"
            )
            continue

        base_skill_md = base_dir / "SKILL.md"
        if not base_skill_md.exists():
            print(
                f"NOTE: overlay for '{name}': base SKILL.md not found — skipped"
            )
            continue

        base_text = base_skill_md.read_text(encoding="utf-8")

        # Per-skill fail-soft: apply_overlay errors (e.g. bad anchor) → NOTE + continue.
        try:
            composed_text = _ko.apply_overlay(base_text, entry)
        except Exception as exc:  # noqa: BLE001
            print(
                f"NOTE: overlay for '{name}': apply_overlay failed: {exc} — skipped"
            )
            continue

        # Determine baseMode from the current slot (as laid by _flat_link_skills).
        if slot.is_symlink():
            base_mode = "symlink"
        elif slot.is_dir() and (slot / _MARKER).exists():
            base_mode = "copy"
        else:
            # Slot absent or unrecognized — fall back to the install's link_mode.
            base_mode = link_mode

        # Remove the verbatim slot (mirrors _link_or_copy's own idempotency signal).
        try:
            if slot.is_symlink():
                slot.unlink()
            elif slot.is_dir() and (slot / _MARKER).exists():
                shutil.rmtree(slot)
            elif slot.exists():
                # Non-kata dir — skip to avoid data loss (fail-closed on ambiguity).
                print(
                    f"NOTE: overlay for '{name}': host slot exists but is not "
                    f"kata-managed — skipped to avoid data loss"
                )
                continue
        except OSError as exc:
            print(
                f"NOTE: overlay for '{name}': failed to remove verbatim slot: {exc} — skipped"
            )
            continue

        # Copy the base skill dir into the slot, then overwrite SKILL.md.
        try:
            shutil.copytree(base_dir, slot)
            (slot / "SKILL.md").write_text(composed_text, encoding="utf-8")
        except OSError as exc:
            print(
                f"NOTE: overlay for '{name}': failed to materialize slot: {exc} — skipped"
            )
            continue

        # Write both markers.
        (slot / _MARKER).write_text(
            "kata-managed materialized overlay — safe to delete on uninstall.\n",
            encoding="utf-8",
        )
        (slot / _OVERLAY_MATERIALIZED_MARKER).write_text(
            "kata overlay materialization marker — factory-reset restores pristine link.\n",
            encoding="utf-8",
        )

        # Compute SHA256 of the composed SKILL.md and record the slot.
        applied_sha = hashlib.sha256(composed_text.encode("utf-8")).hexdigest()
        _ko.record_slot(
            home,
            name,
            {
                "hostPath": str(slot),
                "baseMode": base_mode,
                "source": "overlay",
                "appliedSha": applied_sha,
            },
        )


def _sweep_managed_slots(
    skills_dst: Path,
    home: Path,
    *,
    dry_run: bool = False,
) -> tuple[list[str], list[str]]:
    """Sweep ALL entries in ``skills_dst`` and remove kata-managed ones.

    Unlike the ``uninstall()`` basename loop (which only iterates *current*
    skill names), this sweep enumerates every filesystem entry in the host
    skills directory.  It removes an entry **iff**:

    - it is a **symlink whose resolved target is under ``home``** (an orphaned
      kata link — e.g. left behind by a skill rename/remove in the home), OR
    - it is a **directory carrying ``.kata-managed``** (a kata copy or a
      materialized slot written by ``_materialize_pass``).

    **Fail-closed:** anything else — a non-kata dir, a symlink pointing
    outside the home, an unreadable entry — is reported in ``left_intact``
    and **never removed**.  This reuses the same signal the engine already
    trusts (``_link_or_copy:115–123``).

    Parameters
    ----------
    skills_dst:
        The host skills directory to sweep (e.g. ``~/.claude/skills``).
    home:
        The resolved harness home; used to determine whether a symlink
        target is kata-owned.
    dry_run:
        When ``True``, classify entries and return the lists **without
        performing any filesystem mutation**.

    Returns
    -------
    tuple[list[str], list[str]]
        ``(removed, left_intact)`` — basenames (not full paths) that were
        removed or left intact, respectively.  Full paths are used for
        ``left_intact`` to aid diagnosis, matching the existing ``uninstall``
        convention.
    """
    removed: list[str] = []
    left_intact: list[str] = []

    if not skills_dst.is_dir():
        return removed, left_intact

    home_resolved = home.resolve()

    for entry in sorted(skills_dst.iterdir()):
        if entry.is_symlink():
            try:
                resolved = entry.resolve()
            except (OSError, RuntimeError):
                left_intact.append(str(entry))
                continue
            if resolved.is_relative_to(home_resolved):
                if not dry_run:
                    entry.unlink()
                removed.append(entry.name)
            else:
                left_intact.append(str(entry))
        elif entry.is_dir():
            if (entry / _MARKER).exists():
                if not dry_run:
                    shutil.rmtree(entry)
                removed.append(entry.name)
            else:
                left_intact.append(str(entry))
        else:
            # Files or other non-dir entries — leave intact, report
            left_intact.append(str(entry))

    return removed, left_intact


# ---------------------------------------------------------------------------
# Hooks verb (CG-L2 — NEW, ADDITIVE; engine lives in kata_host_settings)
# ---------------------------------------------------------------------------


def _hooks_verb(args, use_json: bool, auto_compact_window: int | None = None) -> int:
    """Dispatch ``--install-hooks`` / ``--uninstall-hooks`` into ``kata_host_settings``.

    Consent flow (CG-L2, FROZEN): print the unified settings diff + the explicit
    disclosure that these are GLOBAL hooks affecting every Claude Code session on the
    machine (containment = each hook's F-3 kata-scope gate), then require interactive
    confirmation or ``--yes``.  ``--dry-run`` prints the diff and writes nothing.
    Headless ``--json``: machine JSON report to stdout, human notes to stderr.

    D154 (additive): *auto_compact_window* (already parsed + bounds-checked by
    ``main``) rides the same consent flow.  The disclosure names the key state
    (absent→N / old→N / already-N) and — when the CLAUDE_CODE_AUTO_COMPACT_WINDOW
    env var is set — notes that the env var takes precedence (G1); never blocks.
    On uninstall a present key is never removed; one honest note names its
    possible kata origin and the timestamped backup as the restore path.

    Exit codes reuse the semantic table: 0 OK / 1 no-consent / 2 USAGE (flag conflict,
    headless without --yes) / 3 NOT_FOUND (non-claude platform, bad path) /
    4 PERMISSION (OSError) / 5 CONFLICT-class (unparseable host settings — fail-closed,
    never guess, D136).
    """
    import kata_host_settings

    if args.install_hooks and args.uninstall_hooks:
        print(
            "error: --install-hooks and --uninstall-hooks are mutually exclusive",
            file=sys.stderr,
        )
        return 2  # USAGE
    p = (args.platform or "").strip().casefold()
    if p != "claude":
        print(
            f"error: --install-hooks/--uninstall-hooks support only --platform claude "
            f"(got {args.platform!r}) — host settings are Claude Code's",
            file=sys.stderr,
        )
        return 3  # NOT_FOUND
    uninstall: bool = args.uninstall_hooks
    verb = "uninstall-hooks" if uninstall else "install-hooks"
    home = args.home if args.home is not None else _default_home()

    def _apply(dry: bool) -> tuple[dict | None, int]:
        try:
            return (
                kata_host_settings.apply_hooks_change(
                    home,
                    host_dir=args.host_dir,
                    uninstall=uninstall,
                    dry_run=dry,
                    auto_compact_window=auto_compact_window,
                ),
                0,
            )
        except kata_host_settings.HostSettingsError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return None, 5  # CONFLICT-class: unparseable host settings — fail closed
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return None, 4  # PERMISSION
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return None, 3  # NOT_FOUND (bad path / traversal)

    # Plan pass (never writes) — the diff shown for consent.
    plan, code = _apply(dry=True)
    if plan is None:
        return code

    _emit(f"kata {verb}: proposed change to {plan['path']}", as_json=use_json)
    _emit(
        plan["diff"] if plan["changed"] else "(no change — already in the desired state)",
        as_json=use_json,
    )
    # D154 disclosure: name the autoCompactWindow key state so the consent is informed.
    acw_report = plan["report"].get("autoCompactWindow")
    if auto_compact_window is not None and isinstance(acw_report, dict):
        action = acw_report.get("action")
        if action == "set":
            _emit(
                f"autoCompactWindow: absent -> {auto_compact_window}", as_json=use_json
            )
        elif action == "updated":
            _emit(
                f"autoCompactWindow: {acw_report.get('old')} -> {auto_compact_window} "
                f"(a different value exists — it will be overwritten under this consent gate)",
                as_json=use_json,
            )
        else:  # noop
            _emit(
                f"autoCompactWindow: already {auto_compact_window} (no change)",
                as_json=use_json,
            )
        if "CLAUDE_CODE_AUTO_COMPACT_WINDOW" in os.environ:
            _emit(
                "note: CLAUDE_CODE_AUTO_COMPACT_WINDOW="
                f"{os.environ['CLAUDE_CODE_AUTO_COMPACT_WINDOW']} is set in this "
                "environment and takes precedence over the settings key (G1) — the "
                "written autoCompactWindow will not take effect until it is unset.",
                as_json=use_json,
            )
    # D154 uninstall note: a present autoCompactWindow is NEVER removed (a scalar
    # carries no kata marker) — one honest note, never silent.
    if uninstall and isinstance(acw_report, dict) and acw_report.get("action") == "left-in-place":
        _emit(
            f"note: autoCompactWindow={acw_report.get('value')} remains in the settings — "
            "it may have been set by kata --install-hooks --auto-compact-window; kata does "
            "not remove it (a scalar carries no kata marker). To revert it, restore from a "
            "timestamped settings.json.kata-backup-* backup.",
            as_json=use_json,
        )
    _emit(
        "DISCLOSURE: these are GLOBAL Claude Code hooks — once installed they run in "
        "EVERY Claude Code session on this machine, not only kata runs. Containment: "
        "each hook's kata-scope gate exits silently unless the session's cwd shows "
        "kata-run evidence (a .kata/ dir or kata.config file).",
        as_json=use_json,
    )

    if args.dry_run:
        if use_json:
            print(json.dumps(plan))
        _emit("dry-run: nothing written", as_json=use_json)
        return 0
    if not plan["changed"]:
        if use_json:
            print(json.dumps(plan))
        return 0

    # Consent: --yes (--non-interactive) OR an interactive y/N prompt. A headless run
    # without --yes is REFUSED (never silently edit the operator's global settings).
    if not args.non_interactive:
        if sys.stdin.isatty():
            answer = input("Apply this GLOBAL settings change? [y/N] ").strip().casefold()
            if answer not in ("y", "yes"):
                _emit("aborted: no consent — nothing written", as_json=use_json)
                return 1
        else:
            print(
                f"error: --{verb} edits your GLOBAL Claude Code settings and requires "
                f"explicit consent: re-run with --yes (headless) or from an interactive "
                f"terminal",
                file=sys.stderr,
            )
            return 2  # USAGE

    result, code = _apply(dry=False)
    if result is None:
        return code
    if use_json:
        print(json.dumps(result))
    else:
        print(json.dumps({k: v for k, v in result.items() if k != "diff"}, indent=2))
    if result.get("backup"):
        _emit(f"backup written: {result['backup']}", as_json=use_json)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _next_steps_banner(
    platform: str, home: str | Path, link_mode: str, skill_count: int
) -> str:
    """Compose the post-install human guidance shown after a successful install.

    ASCII-only (Windows legacy-console safe — no box-drawing or emoji), and
    platform-aware. Returned as a plain string so ``main`` owns routing; this is
    NEVER emitted in ``--json`` mode (the JSON stdout contract stays clean).
    Lives in the engine (not the shell bootstraps) so install.sh, install.ps1,
    and the download-then-run path all inherit one tested copy.
    """
    p = (platform or "").strip().casefold()
    home_disp = str(home)
    bar = "=" * 60
    if p == "claude":
        skills_path = "~/.claude/skills"
        restart = "Claude Code: exit and reopen (start a fresh session)."
        step2 = [
            '  2) Start a run. In Claude Code, either just ask:',
            '        "Start a KataHarness run on <your project>"',
            "     or invoke a skill directly:",
            "        /kata-initiate    start a run (the front door)",
            "        /kata-onboard     guided tour on an existing repo",
            "        /kata-bootstrap   configure and launch a run",
        ]
    elif p in _BEST_EFFORT:  # codex / kiro
        skills_path = "<host>/.agents/skills"
        restart = f"Restart {platform} so it rescans its skills directory."
        step2 = [
            "  2) Start a run. Ask your agent to begin a KataHarness run, or",
            "     invoke the kata-initiate / kata-onboard skill if your tool",
            "     exposes installed skills as commands.",
        ]
    else:
        skills_path = "your host's skills directory"
        restart = "Restart your tool so it loads the new skills."
        step2 = [
            "  2) Start a run. Ask your agent to begin a KataHarness run",
            "     (the kata-initiate skill is the front door).",
        ]

    head = (
        f"  KataHarness installed   [{platform} * {skill_count} skills"
        f" * mode: {link_mode}]"
        if skill_count
        else f"  KataHarness installed   [{platform} * mode: {link_mode}]"
    )
    lines = [
        "",
        bar,
        head,
        bar,
        "",
        "NEXT STEPS",
        "",
        "  1) Restart your tool so it loads the new skills.",
        f"     {restart}",
        f"     Skills live in {skills_path} and load at startup.",
        "",
        *step2,
        "",
        "  3) Your first run helps you bind a project folder + vault.",
        "",
        "LEARN MORE",
        f"  Quickstart & modes .... {home_disp}/docs/SETUP.md",
        f"  What each skill does .. {home_disp}/README.md",
        "  Update later .......... update.ps1 | update.sh  (--check to preview)",
        "",
        f"Home: {home_disp}",
        bar,
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Install (or uninstall) KataHarness into a platform; optionally record settings.

    Exit codes (Slice B semantic table)
    ------------------------------------
    0  OK         — install ok, idempotent re-install, confirm ok, uninstall ok
    1  ERROR      — generic / confirm-probe not confirmed
    2  USAGE      — bad/missing args (argparse default; also malformed --answers-json)
    3  NOT_FOUND  — unknown platform, missing path, bad parentDir/vaultDir
    4  PERMISSION — host dir not writable / symlink + copy both denied (OSError)
    5  CONFLICT   — non-kata dir occupies a skill slot (refuse to clobber)
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="kata_install",
        description="Install KataHarness into a host platform from its central home.",
        epilog=(
            "Examples:\n"
            "  kata_install --platform claude\n"
            "  kata_install --platform claude --answers-json setup.json --json\n"
            "  kata_install --platform claude --uninstall --target-dir /path/to/project\n"
            "  kata_install --platform codex --confirm\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--platform", required=True, help="claude | codex | kiro | quick | other")
    parser.add_argument("--home", default=None, help="harness home (default: $KATA_HOME or self-locate)")
    parser.add_argument("--host-dir", default=None, help="host config root (default: ~/.claude for claude)")
    parser.add_argument("--parent-dir", default=None, help="default parent project folder (also writes settings)")
    parser.add_argument("--vault-dir", default=None, help="vault / second-brain location (optional)")
    parser.add_argument("--confirm", action="store_true",
                        help="run the headless confirm-probe for --platform and record it in confirmedPlatforms")
    # NEW flags (Slice B)
    parser.add_argument(
        "--non-interactive", "--yes",
        dest="non_interactive",
        action="store_true",
        help=(
            "non-interactive mode: suppress all prompts "
            "(reserved; no interactive prompts today; "
            "also auto-enabled when stdin is not a TTY)"
        ),
    )
    parser.add_argument(
        "--answers-json",
        dest="answers_json",
        default=None,
        metavar="PATH",
        help="JSON file supplying setup values {parentDir, vaultDir} for headless runs",
    )
    parser.add_argument(
        "--json",
        dest="use_json",
        action="store_true",
        help="machine-readable JSON to stdout; human notes to stderr",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="reverse the install: remove linked skills, settings, and the router stanza",
    )
    parser.add_argument(
        "--target-dir",
        dest="target_dir",
        default=None,
        metavar="DIR",
        help="target project directory (used by --uninstall to remove the router stanza)",
    )
    # NEW flags (A2 — update / factory-reset / dry-run / git-sha)
    parser.add_argument(
        "--update",
        action="store_true",
        help=(
            "re-link / re-copy skills from the home, then re-stamp (idempotent; "
            "use after `git pull` in the home or via `update.sh`)"
        ),
    )
    parser.add_argument(
        "--factory-reset",
        "--reinstall",
        dest="factory_reset",
        action="store_true",
        help=(
            "restore pristine links + re-stamp (Phase-A form: re-link/re-copy pristine; "
            "Phase B will also drop overlay materializations)"
        ),
    )
    parser.add_argument(
        "--hard",
        action="store_true",
        help=(
            "--factory-reset --hard: additionally clear the overlay store (Phase B+). "
            "In Phase A this is a no-op passthrough (overlay does not exist yet)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help=(
            "print what would happen without mutating any files "
            "(for --update, --factory-reset, --uninstall)"
        ),
    )
    parser.add_argument(
        "--git-sha",
        dest="git_sha",
        default=None,
        metavar="SHA",
        help=(
            "40-hex git SHA passed in by the bootstrap shell (update.sh / update.ps1); "
            "recorded in .kata-version. Omit for plain installs → gitSha:'unknown'."
        ),
    )
    parser.add_argument(
        "--ref",
        default="master",
        metavar="REF",
        help=(
            "git ref the bootstrap resolved to (e.g. 'master', 'v0.2.0'); "
            "recorded in .kata-version stamp. Passed by the bootstraps via $KATA_REF. "
            "Default: 'master'."
        ),
    )
    # NEW flags (CG-L2 — conductor-gauge chain deployment; engine in kata_host_settings)
    parser.add_argument(
        "--install-hooks",
        dest="install_hooks",
        action="store_true",
        help=(
            "merge kata's rendered Claude Code statusLine + hooks "
            "(adapters/claude/settings.snippet.json) into your GLOBAL ~/.claude/settings.json. "
            "Consent-gated: prints the settings diff and requires confirmation or --yes; "
            "combine with --dry-run to preview without writing"
        ),
    )
    parser.add_argument(
        "--uninstall-hooks",
        dest="uninstall_hooks",
        action="store_true",
        help=(
            "remove exactly kata's hook entries from ~/.claude/settings.json and unwrap the "
            "statusLine chain back to your original command (consent-gated like --install-hooks). "
            "Never removes autoCompactWindow (a scalar carries no kata marker); the timestamped "
            "backup is the restore path"
        ),
    )
    # NEW flag (D154 — opt-in autoCompactWindow write; valid ONLY with --install-hooks)
    parser.add_argument(
        "--auto-compact-window",
        dest="auto_compact_window",
        default=None,
        metavar="N",
        help=(
            "with --install-hooks only: also merge the top-level \"autoCompactWindow\": N "
            "into the GLOBAL settings (Claude schema bounds: 100000-1000000, G1). Same "
            "consent gate, diff disclosure, timestamped backup, and atomic write as the "
            "hooks merge. Note: a set CLAUDE_CODE_AUTO_COMPACT_WINDOW env var takes "
            "precedence over the settings key"
        ),
    )
    args = parser.parse_args(argv)

    use_json: bool = args.use_json
    # Non-interactive auto-engages when stdin is not a TTY (forward-compat assertion)
    _non_interactive: bool = args.non_interactive or not sys.stdin.isatty()  # noqa: F841

    # Env-var fallbacks (additive; explicit flags win)
    parent_dir: str | None = args.parent_dir or os.environ.get("KATA_PARENT_DIR")
    vault_dir: str | None = args.vault_dir or os.environ.get("KATA_VAULT_DIR")

    # --answers-json: load all setup values up-front for headless runs
    if args.answers_json:
        try:
            answers = _load_answers_json(args.answers_json)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 3  # NOT_FOUND
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2  # USAGE
        # Answers override flag / env values
        parent_dir = answers.get("parentDir", parent_dir)
        vault_dir = answers.get("vaultDir", vault_dir)

    # D154: --auto-compact-window is valid ONLY together with --install-hooks; parse +
    # bounds-check up-front (G1 schema) so a bad value is a USAGE error, exit 2.
    auto_compact_window: int | None = None
    if args.auto_compact_window is not None:
        if not args.install_hooks:
            print(
                "error: --auto-compact-window is only valid together with --install-hooks",
                file=sys.stderr,
            )
            return 2  # USAGE
        import kata_host_settings as _khs_acw

        try:
            auto_compact_window = _khs_acw.parse_auto_compact_window(args.auto_compact_window)
        except ValueError as exc:
            print(f"error: --auto-compact-window: {exc}", file=sys.stderr)
            return 2  # USAGE

    # CG-L2 dispatch: consent-gated GLOBAL host-settings merge (engine: kata_host_settings)
    if args.install_hooks or args.uninstall_hooks:
        return _hooks_verb(args, use_json, auto_compact_window=auto_compact_window)

    # Write settings when parentDir is known (--parent-dir, KATA_PARENT_DIR, or --answers-json)
    if parent_dir:
        import kata_settings

        try:
            sp = kata_settings.write_settings(parent_dir, vault_dir, home=args.home)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 3  # NOT_FOUND (non-existent dir)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 4  # PERMISSION (disk full / unwritable settings file)
        _emit(f"settings: wrote {sp}", as_json=use_json)

    # --confirm probe (existing path, unchanged)
    if args.confirm:
        probe = confirm_platform(args.platform, home=args.home)
        print(json.dumps(probe, indent=2))
        return 0 if probe.get("confirmed") else 1

    # --uninstall verb (Slice C; extended A2: dry_run passthrough)
    if args.uninstall:
        if args.dry_run:
            # Dry-run: classify what the sweep would remove without mutating
            _home_dr = _safe_abs(args.home) if args.home is not None else _default_home()
            _p_dr = (args.platform or "").strip().casefold()
            _subdir_dr = ".agents/skills" if _p_dr in _BEST_EFFORT else "skills"
            _hd_raw_dr = args.host_dir
            if _hd_raw_dr is not None or _p_dr == "claude":
                _hd_dr = (
                    _safe_abs(_hd_raw_dr)
                    if _hd_raw_dr is not None
                    else (Path.home() / ".claude")
                )
                _would_rm, _would_keep = _sweep_managed_slots(
                    _hd_dr / _subdir_dr, _home_dr, dry_run=True
                )
                plan = {
                    "dryRun": True,
                    "wouldRemove": _would_rm,
                    "wouldKeepIntact": _would_keep,
                }
            else:
                plan = {"dryRun": True, "wouldRemove": [], "wouldKeepIntact": []}
            if use_json:
                print(json.dumps(plan))
            else:
                print(json.dumps(plan, indent=2))
            return 0

        try:
            result = uninstall(
                args.platform,
                harness_home=args.home,
                host_dir=args.host_dir,
                target_dir=args.target_dir,
                dry_run=args.dry_run,
            )
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return _exit_code_for({}, exc=exc)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return _exit_code_for({}, exc=exc)
        if use_json:
            print(json.dumps(result))
        else:
            print(json.dumps(result, indent=2))
        for note in result.get("notes", []):
            _emit(f"  - {note}", as_json=use_json)
        return 0 if result.get("ok") else 1

    # --update: re-link / re-materialize / re-stamp (A2 NEW branch; NO git)
    if args.update:
        if args.dry_run:
            _emit("dry-run: would re-link all skills and re-write the version stamp", as_json=use_json)
            return 0

        # minor-a: check is_pristine for each tracked skill against the PREVIOUS manifest;
        # surface a drift NOTE for any hand-edited tracked base file before the re-link.
        import kata_version as _kv_upd

        _home_upd = _safe_abs(args.home) if args.home is not None else _default_home()
        _prev_manifest = _kv_upd.read_manifest(_home_upd)
        if _prev_manifest.get("skills"):
            for _skill_name in _prev_manifest["skills"]:
                if not _kv_upd.is_pristine(_home_upd, _skill_name):
                    _emit(
                        f"NOTE: drift detected in base skill '{_skill_name}' — "
                        f"tracked base file has been hand-edited (minor-a). "
                        f"Use the overlay (kata-improve) rather than editing the base directly.",
                        as_json=use_json,
                    )

        # Re-link (composing the frozen engine fns unchanged)
        try:
            result = install(args.platform, harness_home=args.home, host_dir=args.host_dir)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return _exit_code_for({}, exc=exc)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return _exit_code_for({}, exc=exc)

        # Derive link_mode from result
        _methods_upd = result.get("method", [])
        _link_mode_upd = (
            _methods_upd[0]
            if len(_methods_upd) == 1
            else ("mixed" if len(_methods_upd) > 1 else "unknown")
        )

        # Post-link materialize pass (applies fork shadows + overlay entries; Phase B/C2)
        _p_upd = (args.platform or "").strip().casefold()
        _hd_raw_upd = args.host_dir
        if _p_upd == "claude":
            _hd_upd = (
                _safe_abs(_hd_raw_upd)
                if _hd_raw_upd is not None
                else (Path.home() / ".claude")
            )
            _materialize_pass(_home_upd, _hd_upd / "skills", _link_mode_upd)
        elif _p_upd in _BEST_EFFORT and _hd_raw_upd is not None:
            _hd_upd = _safe_abs(_hd_raw_upd)
            _materialize_pass(_home_upd, _hd_upd / ".agents" / "skills", _link_mode_upd)

        # Write stamp + manifest (consuming --git-sha; "unknown" when absent)
        _git_sha_upd = args.git_sha or "unknown"
        try:
            _kv_upd.write_stamp(
                _home_upd,
                git_sha=_git_sha_upd,
                suite_semver=_kv_upd.suite_semver(_home_upd),
                ref=args.ref,
                link_mode=_link_mode_upd,
                platform=args.platform or "",
            )
            _kv_upd.write_manifest(_home_upd, git_sha=_git_sha_upd)
        except Exception:  # noqa: BLE001 — stamp write failure non-fatal for update
            pass

        if use_json:
            print(json.dumps(result))
        else:
            print(json.dumps(result, indent=2))
        for note in result.get("notes", []):
            _emit(f"  - {note}", as_json=use_json)
        return _exit_code_for(result)

    # --factory-reset / --reinstall: re-link pristine + re-stamp (A2 NEW branch; NO git)
    # Phase A form: no overlay materializations yet; --hard is a no-op passthrough on overlay.
    if args.factory_reset:
        if args.dry_run:
            _emit(
                "dry-run: would re-link all skills to pristine and re-write the version stamp",
                as_json=use_json,
            )
            if args.hard:
                _emit("dry-run: --hard would clear the overlay store", as_json=use_json)
            return 0

        import kata_version as _kv_fr

        _home_fr = _safe_abs(args.home) if args.home is not None else _default_home()

        # Re-link pristine (composing the frozen engine fns unchanged)
        try:
            result = install(args.platform, harness_home=args.home, host_dir=args.host_dir)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return _exit_code_for({}, exc=exc)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return _exit_code_for({}, exc=exc)

        # Derive link_mode
        _methods_fr = result.get("method", [])
        _link_mode_fr = (
            _methods_fr[0]
            if len(_methods_fr) == 1
            else ("mixed" if len(_methods_fr) > 1 else "unknown")
        )

        # Factory-reset: drop materializations (Phase B).
        # install() above already restored pristine links (it rmtree'd any .kata-managed
        # materialized slot via _link_or_copy's existing .kata-managed guard).
        # We still need to clear materialized.json so the record isn't stale, and
        # --hard additionally clears the overlay store itself.
        # DO NOT call _materialize_pass here — factory-reset drops materializations
        # back to pristine links; a later --update will re-apply the preserved overlay.
        try:
            import kata_overlay as _ko_fr_drop
            _ko_fr_drop.write_materialized(_home_fr, {"schema": 1, "slots": {}})
            if args.hard:
                # --hard: clear overlay store (write an empty store).
                _od_fr = _ko_fr_drop.overlay_dir(_home_fr)
                _od_fr.mkdir(parents=True, exist_ok=True)
                (_od_fr / "overlay.json").write_text(
                    json.dumps({"schema": 1, "skills": {}}, indent=2) + "\n",
                    encoding="utf-8",
                )
                _emit("NOTE: --hard: overlay store cleared", as_json=use_json)
        except ImportError:
            # kata_overlay not present (Phase A behavior — nothing to clear)
            if args.hard:
                _emit(
                    "NOTE: --hard: no overlay store present — no-op",
                    as_json=use_json,
                )

        # Re-stamp + re-manifest
        _git_sha_fr = args.git_sha or "unknown"
        try:
            _kv_fr.write_stamp(
                _home_fr,
                git_sha=_git_sha_fr,
                suite_semver=_kv_fr.suite_semver(_home_fr),
                ref=args.ref,
                link_mode=_link_mode_fr,
                platform=args.platform or "",
            )
            _kv_fr.write_manifest(_home_fr, git_sha=_git_sha_fr)
        except Exception:  # noqa: BLE001 — stamp write failure non-fatal
            pass

        # CA-L36: factory-reset wipes install state, so it additionally CLEARS the
        # force-first-run marker (firstRunCompletedAt + firstRunVersion) — one forced
        # first-run pass after a reset is correct. The re-link + re-stamp above have
        # already completed ("reset otherwise proceeds"); a corrupt settings file makes
        # the fail-closed delete helper RAISE, which we surface LOUDLY via the existing
        # factory-reset error path (never silent) without aborting the reset (CA-L36/C-3).
        import kata_settings as _ks_fr

        try:
            _ks_fr.delete_settings_key("firstRunCompletedAt", home=_home_fr)
            _ks_fr.delete_settings_key("firstRunVersion", home=_home_fr)
        except ValueError as _clear_exc:
            print(
                f"error: factory-reset could not clear the first-run marker — "
                f"corrupt settings file {_ks_fr.settings_path(_home_fr)}: {_clear_exc} "
                f"(reset otherwise completed; fix the file, then the next run forces one "
                f"first-run pass — it will NOT loop)",
                file=sys.stderr,
            )

        if use_json:
            print(json.dumps(result))
        else:
            print(json.dumps(result, indent=2))
        for note in result.get("notes", []):
            _emit(f"  - {note}", as_json=use_json)
        return _exit_code_for(result)

    # second-brain-target / S2 — PokeVault recommendation decision (plain-install path
    # only). Computed HERE, immediately before the plain-install install() call and AFTER
    # every verb branch (--install-hooks/--uninstall-hooks, --confirm, --uninstall,
    # --update, --factory-reset) has already returned — so NO verb ever emits it
    # (freeze-gate HIGH-2). Recommend IFF the effective vault_dir is unset AND
    # kata_settings.vault_recommendation() says recommend (vaultDir unset in settings AND no
    # un-lapsed remembered decline). NEVER a prompt — a note cannot hang a headless run, so
    # the _non_interactive "no interactive prompts today" contract holds (AC2's never-hang
    # leg). The note RECORDS NOTHING: a note the user never answered is not a decline (only
    # the interactive skill-surface decline writes one, S3). The field/note are EMITTED
    # below in the plain-install print section (so a clobber/ValueError early-return never
    # emits a half-note), riding the completed result together or not at all.
    _vault_rec: dict | None = None
    if not vault_dir:  # effective vault_dir (--vault-dir / KATA_VAULT_DIR / --answers-json) unset
        import kata_settings as _ks_vrec

        _rec = _ks_vrec.vault_recommendation(
            _ks_vrec.read_settings(home=args.home), home=args.home
        )
        if _rec.get("recommend"):
            _vault_rec = _rec

    # Install (existing path, now wrapped in try/except for semantic exit codes)
    try:
        result = install(args.platform, harness_home=args.home, host_dir=args.host_dir)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return _exit_code_for({}, exc=exc)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return _exit_code_for({}, exc=exc)

    # M1 (load-bearing): write stamp + manifest on every successful install so that
    # adaptation_context (DESIGN §6.2) returns "install" on a real install, and the
    # §12 Phase-A live-proof step 1 passes.  gitSha is "unknown" when --git-sha is
    # absent (plain install.sh path — the engine never computes a SHA).  Stays additive
    # and git-free: the stamp write is appended post-install, never inside the 5 frozen fns.
    #
    # Fold-in #2: _materialize_pass is called OUTSIDE the stamp's except block so a
    # structural materialize failure surfaces instead of being silently discarded.
    # Per-skill failures are handled fail-soft (NOTE + continue) inside _materialize_pass.
    if result.get("ok"):
        import kata_version as _kv_inst

        _home_inst = _safe_abs(args.home) if args.home is not None else _default_home()
        _methods_inst = result.get("method", [])
        _link_mode_inst = (
            _methods_inst[0]
            if len(_methods_inst) == 1
            else ("mixed" if len(_methods_inst) > 1 else "unknown")
        )
        _git_sha_inst = args.git_sha or "unknown"
        try:
            _kv_inst.write_stamp(
                _home_inst,
                git_sha=_git_sha_inst,
                suite_semver=_kv_inst.suite_semver(_home_inst),
                ref=args.ref,
                link_mode=_link_mode_inst,
                platform=args.platform or "",
            )
            _kv_inst.write_manifest(_home_inst, git_sha=_git_sha_inst)
        except Exception:  # noqa: BLE001 — stamp write failure is non-fatal for install
            pass
        # Post-link materialize pass — OUTSIDE the stamp except (fold-in #2).
        # Structural errors from _materialize_pass propagate; per-skill errors are
        # caught inside _materialize_pass itself (fail-soft NOTE + continue).
        _p_inst = (args.platform or "").strip().casefold()
        _hd_raw_inst = args.host_dir
        if _p_inst == "claude":
            _hd_inst = (
                _safe_abs(_hd_raw_inst)
                if _hd_raw_inst is not None
                else (Path.home() / ".claude")
            )
            _materialize_pass(_home_inst, _hd_inst / "skills", _link_mode_inst)
        elif _p_inst in _BEST_EFFORT and _hd_raw_inst is not None:
            _hd_inst = _safe_abs(_hd_raw_inst)
            _materialize_pass(_home_inst, _hd_inst / ".agents" / "skills", _link_mode_inst)

    # S2: the recommendation rides the completed plain-install result — attach the
    # `vault_recommendation` field to the result dict (surfaced under --json) and print the
    # one-line note to stderr. Both together or neither; stderr keeps the --json stdout
    # contract clean. Absent entirely when a vault is configured or a live decline holds.
    if _vault_rec is not None:
        result["vault_recommendation"] = _vault_rec
        print(
            "note: a second brain is optional (never required) — add one later by pointing "
            f"--vault-dir at any vault, or start with PokeVault → {_vault_rec['link']}",
            file=sys.stderr,
        )

    if use_json:
        print(json.dumps(result))
    else:
        print(json.dumps(result, indent=2))
    for note in result.get("notes", []):
        _emit(f"  - {note}", as_json=use_json)
    # Professional post-install next-steps guidance (human mode only; suppressed
    # under --json so the machine contract stays clean). Only on a successful
    # install — _home_inst / _link_mode_inst are in scope iff result.get("ok").
    if result.get("ok") and not use_json:
        print(
            _next_steps_banner(
                args.platform or "",
                _home_inst,
                _link_mode_inst,
                len(result.get("linked", [])),
            )
        )
    return _exit_code_for(result)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
