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
import shutil
from pathlib import Path

PLUGIN_NAME = "kata"


def _safe_abs(raw: str | Path) -> Path:
    """Reject ``..`` traversal (CWE-23) then resolve to absolute."""
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


def _flat_link_skills(home: Path, host_dir: Path) -> dict:
    """Flat-link every skill dir into ``<host_dir>/skills/<name>`` (symlink, copy fallback)."""
    skills_dst = host_dir / "skills"
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


def _install_claude(home: Path, host_dir: Path) -> dict:
    manifest = ensure_plugin_manifest(home)
    res = _flat_link_skills(home, host_dir)
    return {
        "platform": "claude",
        "ok": True,
        "manifest": str(manifest),
        **res,
        "notes": [f"{len(res['linked'])} skills linked into {res['skillsDir']}"],
    }


def _install_besteffort(platform: str, home: Path, host_dir: Path | None) -> dict:
    """Codex/Kiro: same flat-link idea; documented best-effort (host not verifiable here)."""
    result: dict = {"platform": platform, "ok": True, "bestEffort": True}
    if host_dir is not None:
        result.update(_flat_link_skills(home, host_dir))
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
# for routing — confirming a platform we can't dispatch to would mislead the router. codex only for now.
# Point-in-time flags (RESEARCH §0/§6) — pin/verify at build.
_PROBE_COMMANDS = {
    "codex": lambda: ["codex", "exec", "--sandbox", "read-only", _PROBE_PROMPT],
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

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)  # noqa: S603
    return proc.returncode, proc.stdout


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Install KataHarness into a platform; optionally record the two settings."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="kata_install",
        description="Install KataHarness into a host platform from its central home.",
    )
    parser.add_argument("--platform", required=True, help="claude | codex | kiro | quick | other")
    parser.add_argument("--home", default=None, help="harness home (default: $KATA_HOME or self-locate)")
    parser.add_argument("--host-dir", default=None, help="host config root (default: ~/.claude for claude)")
    parser.add_argument("--parent-dir", default=None, help="default parent project folder (also writes settings)")
    parser.add_argument("--vault-dir", default=None, help="vault / second-brain location (optional)")
    parser.add_argument("--confirm", action="store_true",
                        help="run the headless confirm-probe for --platform and record it in confirmedPlatforms")
    args = parser.parse_args(argv)

    if args.parent_dir:
        import kata_settings

        sp = kata_settings.write_settings(args.parent_dir, args.vault_dir, home=args.home)
        print(f"settings: wrote {sp}")

    if args.confirm:
        probe = confirm_platform(args.platform, home=args.home)
        print(json.dumps(probe, indent=2))
        return 0 if probe.get("confirmed") else 1

    result = install(args.platform, harness_home=args.home, host_dir=args.host_dir)
    print(json.dumps(result, indent=2))
    for note in result.get("notes", []):
        print(f"  - {note}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
