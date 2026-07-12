"""kata_host_settings.py — render + merge kata's Claude Code host-settings snippet (CG-L2).

The conductor-gauge chain (DESIGN ``.planning/specs/conductor-gauge-wiring/DESIGN.md``,
freeze-gate F-7) is deployed by merging ``adapters/claude/settings.snippet.json`` into the
operator's GLOBAL ``~/.claude/settings.json``.  This module owns that merge:

Pure core (no I/O — independently testable)
-------------------------------------------
``render_snippet(snippet, repo, venv_exists=None) -> dict``
    Resolve every ``<repo>`` placeholder to the absolute repo path and pick the python
    executable (the repo venv's ``python.exe`` when present, else bare ``python``).  The
    snippet is treated as GENERIC data — statusLine plus every hooks event present in the
    file is rendered; no event list is hard-coded here.
``merge_host_settings(existing, rendered) -> (merged, report)``
    Hook entries APPEND (never remove/reorder the user's own entries); idempotent (kata
    entries already present ⇒ no change); a stale kata entry (same event, kata-identified,
    different content — e.g. the venv moved) is updated in place.  statusLine: absent ⇒ set
    kata's; present + chain-eligible ⇒ wrap via the CA-L1 chain
    (``… statusline_chain.py" -- <original>``, the original preserved VERBATIM after
    ``--``); present + ineligible ⇒ untouched, reported ``skipped-ineligible``.
``unmerge_host_settings(existing, rendered) -> (cleaned, report)``
    Remove exactly kata's hook entries; unwrap the chain back to the user's original
    command; a kata-set statusLine (no prior user one) is removed outright.

Kata entries are identified STRUCTURALLY: any string inside the entry contains the
rendered ``<repo>/adapters/claude/`` path (never by event name or position).

I/O shell (thin)
----------------
Strict fail-closed read of ``~/.claude/settings.json`` with ``encoding="utf-8-sig"``
(lossless BOM handling); unparseable ⇒ :class:`HostSettingsError` whose message
distinguishes "BOM was handled, the JSON itself is corrupt" from plain corruption —
NEVER guess (D136).  A timestamped backup ``settings.json.kata-backup-<UTC ts>`` is
written BEFORE any change; the write is atomic (temp + ``os.replace``); key order is
preserved (``sort_keys`` is NOT applied).  Consent/diff/confirmation live in
``kata_install.main`` — this module never prompts.

``is_chain_eligible`` is a FAITHFUL PORT of the CA-L1 pin in
``adapters/claude/statusline_chain.py`` (a cross-tree import from ``tools/`` would need
importlib file-loading machinery inside a pure core, so the port + a parity test on a
shared vector set is the sanctioned leg).  Any change to the pin must land in BOTH
places — the parity test in ``tests/test_kata_host_settings.py`` goes RED on divergence.

Hard rule: never invokes git; stdlib-only.
"""

from __future__ import annotations

import copy
import difflib
import json
import os
import re
import shlex
import tempfile
from datetime import UTC, datetime
from pathlib import Path

#: Repo-relative path of the venv python the snippet commands prefer when it exists.
VENV_PYTHON_REL = "tools/.venv/Scripts/python.exe"

#: The snippet's quoted-venv-python placeholder token (replaced as ONE unit so the
#: quotes collapse correctly when falling back to bare ``python``).
_VENV_TOKEN = f'"<repo>/{VENV_PYTHON_REL}"'

#: Marker suffix used to identify kata-owned entries structurally: every command in the
#: snippet references a script under ``<repo>/adapters/claude/``.
_ADAPTER_SEGMENT = "/adapters/claude/"

#: Unwrap separator — the chain script's quoted path followed by the ``--`` tail marker.
#: Everything AFTER this separator is the user's original command, verbatim.
_CHAIN_SEP = 'statusline_chain.py" -- '


class HostSettingsError(ValueError):
    """Fail-closed host-settings failure (unparseable/ambiguous file — never guess)."""


# --------------------------------------------------------------------------- #
# Chain-eligibility — faithful port of the CA-L1 pin (statusline_chain.py)
# --------------------------------------------------------------------------- #

#: PORT of ``statusline_chain._SHELL_METACHARS`` — keep byte-identical to the pin.
_SHELL_METACHARS = frozenset("|&;<>()$`\\*?[]{}~!#%^\n\r\t")

#: PORT of ``statusline_chain._BATCH_EXTENSIONS`` — keep byte-identical to the pin.
_BATCH_EXTENSIONS = frozenset({".bat", ".cmd", ".com"})


def is_chain_eligible(command_str: str) -> bool:
    """Decision gate (CA-L1 pin, ported): is *command_str* safe to chain as list-argv?

    Chain-eligible IFF the command is a non-empty string that (1) contains no shell
    metacharacter from :data:`_SHELL_METACHARS`, (2) ``shlex.split``-parses to at least
    one token, and (3) the argv[0] target is not a Windows batch file
    (:data:`_BATCH_EXTENSIONS`, case-insensitive).  Anything else ⇒ ``False`` ⇒ the
    SKIP leg.  Faithful port of ``adapters/claude/statusline_chain.is_chain_eligible``;
    the parity test pins equivalence on a shared vector set.
    """
    if not isinstance(command_str, str) or not command_str.strip():
        return False
    if any(ch in _SHELL_METACHARS for ch in command_str):
        return False
    try:
        tokens = shlex.split(command_str)
    except ValueError:
        # unbalanced quote / dangling escape — never guess, SKIP.
        return False
    if not tokens:
        return False
    if Path(tokens[0]).suffix.lower() in _BATCH_EXTENSIONS:
        return False
    return True


# --------------------------------------------------------------------------- #
# Pure core — render
# --------------------------------------------------------------------------- #


def render_snippet(
    snippet: dict,
    repo: Path,
    venv_exists: bool | None = None,
) -> dict:
    """Resolve every ``<repo>`` placeholder in *snippet* against the absolute *repo* path.

    Python-executable rule (CG-L2): commands use ``<repo>/tools/.venv/Scripts/python.exe``
    when it is present, else bare ``python``.  ``venv_exists`` parameterizes the existence
    check for testability; ``None`` (the default) probes the real filesystem once.

    Paths are emitted with forward slashes (the snippet convention — valid on Windows and
    chain-eligibility-safe: backslash is a rejected metacharacter).  The snippet structure
    is walked generically — every hooks event present in the file is rendered; nothing is
    hard-coded to an event list.  Pure aside from the optional default probe.
    """
    if not isinstance(snippet, dict):
        raise ValueError("kata_host_settings: snippet must be a JSON object")
    repo_posix = _safe_abs(repo).as_posix()
    if venv_exists is None:
        venv_exists = (Path(repo_posix) / VENV_PYTHON_REL).exists()
    py_token = f'"{repo_posix}/{VENV_PYTHON_REL}"' if venv_exists else "python"

    def render_str(s: str) -> str:
        # 1. The quoted venv-python token collapses to the chosen interpreter.
        s = s.replace(_VENV_TOKEN, py_token)
        # 2. A bare leading `python ` interpreter upgrades to the venv when present.
        if venv_exists and s.startswith("python "):
            s = py_token + s[len("python"):]
        # 3. Every remaining `<repo>` placeholder resolves to the absolute repo path.
        return s.replace("<repo>", repo_posix)

    def walk(node):
        if isinstance(node, str):
            return render_str(node)
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(snippet)


def _safe_abs(raw: str | Path) -> Path:
    """Reject ``..`` traversal (CWE-23) then resolve to absolute (repo guard style)."""
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"kata_host_settings: refusing path with '..' traversal: {raw!r}")
    return p.resolve()


# --------------------------------------------------------------------------- #
# Pure core — kata-entry identification
# --------------------------------------------------------------------------- #

_MARKER_RE = re.compile(r'"?([^"\s]+)/adapters/claude/')


def _iter_strings(node):
    """Yield every string anywhere inside a JSON-shaped structure."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from _iter_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _iter_strings(v)


def _kata_marker(rendered: dict) -> str:
    """The rendered repo's ``…/adapters/claude/`` path — kata's structural identity.

    Extracted from the rendered snippet itself (every command references a script under
    that directory).  Fail-closed: a rendered snippet with no such command cannot support
    idempotent merge/unmerge, so raise rather than guess.
    """
    for s in _iter_strings(rendered):
        m = _MARKER_RE.search(s)
        if m:
            return m.group(1) + _ADAPTER_SEGMENT
    raise ValueError(
        "kata_host_settings: rendered snippet contains no <repo>/adapters/claude/ command — "
        "cannot identify kata entries structurally"
    )


def _is_kata_entry(entry, marker: str) -> bool:
    """A hook entry is kata's iff any string inside it contains the kata adapter path."""
    return any(marker in s for s in _iter_strings(entry))


# --------------------------------------------------------------------------- #
# Pure core — merge / unmerge
# --------------------------------------------------------------------------- #


def merge_host_settings(existing: dict, rendered: dict) -> tuple[dict, dict]:
    """Merge kata's *rendered* snippet into the user's *existing* settings (pure).

    Returns ``(merged, report)``.  *existing* is never mutated.  Hook entries APPEND
    (user entries are never removed or reordered); an identical kata entry already
    present is a no-op; a kata-identified entry with different content (stale render)
    is updated in place.  statusLine follows the CG-L2 decision table (set / chain /
    skipped-ineligible).  Fail-closed on structurally unusable user data (a non-dict
    ``hooks`` or non-list event) — never guess (D136).
    """
    if not isinstance(existing, dict):
        raise HostSettingsError("kata_host_settings: existing settings must be a JSON object")
    marker = _kata_marker(rendered)
    merged = copy.deepcopy(existing)
    report: dict = {"hooks": {}, "statusline": None}

    rendered_hooks = rendered.get("hooks") or {}
    if rendered_hooks:
        if "hooks" in merged and not isinstance(merged["hooks"], dict):
            raise HostSettingsError(
                "kata_host_settings: existing settings 'hooks' is not an object — refusing to guess"
            )
        hooks = merged.setdefault("hooks", {})
        for event, entries in rendered_hooks.items():
            if event in hooks and not isinstance(hooks[event], list):
                raise HostSettingsError(
                    f"kata_host_settings: existing hooks[{event!r}] is not a list — refusing to guess"
                )
            tgt = hooks.setdefault(event, [])
            # kata-owned slots available for in-place update (stale renders), FIFO.
            kata_slots = [i for i, e in enumerate(tgt) if _is_kata_entry(e, marker)]
            actions: list[str] = []
            for entry in entries:
                if entry in tgt:
                    actions.append("noop")
                    if tgt.index(entry) in kata_slots:
                        kata_slots.remove(tgt.index(entry))
                    continue
                if kata_slots:
                    tgt[kata_slots.pop(0)] = copy.deepcopy(entry)
                    actions.append("updated")
                else:
                    tgt.append(copy.deepcopy(entry))
                    actions.append("appended")
            report["hooks"][event] = actions

    rendered_sl = rendered.get("statusLine")
    if rendered_sl is not None:
        existing_sl = merged.get("statusLine")
        if existing_sl is None:
            merged["statusLine"] = copy.deepcopy(rendered_sl)
            report["statusline"] = "set"
        else:
            cmd = existing_sl.get("command", "") if isinstance(existing_sl, dict) else ""
            if marker in cmd:
                # already kata's (plain or chain-wrapped) — idempotent no-op.
                report["statusline"] = "noop"
            elif is_chain_eligible(cmd):
                wrapper = _chain_wrapper_command(rendered_sl.get("command", ""), cmd)
                new_sl = copy.deepcopy(existing_sl)
                new_sl["command"] = wrapper
                merged["statusLine"] = new_sl
                report["statusline"] = "chained"
            else:
                # CA-L1 never-clobber: leave the user's statusLine untouched.
                report["statusline"] = "skipped-ineligible"

    return merged, report


def _chain_wrapper_command(rendered_statusline_cmd: str, original: str) -> str:
    """Build the chain-wrapper command: ``… statusline_chain.py" -- <original verbatim>``.

    Derived from kata's own rendered statusline command (same interpreter token, same
    resolved repo path) by retargeting ``statusline.py`` → ``statusline_chain.py``.
    """
    chain_cmd = rendered_statusline_cmd.replace(
        f"{_ADAPTER_SEGMENT}statusline.py", f"{_ADAPTER_SEGMENT}statusline_chain.py"
    )
    return f"{chain_cmd} -- {original}"


def unmerge_host_settings(existing: dict, rendered: dict) -> tuple[dict, dict]:
    """Remove exactly kata's entries from *existing* (pure); returns ``(cleaned, report)``.

    - Hook entries structurally identified as kata's are removed; user entries are
      untouched.  An event list (and the ``hooks`` dict) emptied BY this removal is
      dropped so a merge→unmerge round-trip returns the original dict exactly; a
      pre-existing empty container the removal never touched is preserved.
    - A chain-wrapped statusLine is unwrapped back to the user's original command
      (verbatim tail after ``statusline_chain.py" -- ``).
    - A kata-set statusLine (kata's own command, no chain) is removed outright.
    """
    if not isinstance(existing, dict):
        raise HostSettingsError("kata_host_settings: existing settings must be a JSON object")
    marker = _kata_marker(rendered)
    cleaned = copy.deepcopy(existing)
    report: dict = {"hooks": {}, "statusline": None}

    hooks = cleaned.get("hooks")
    if isinstance(hooks, dict):
        removed_any = False
        for event in list(hooks.keys()):
            entries = hooks[event]
            if not isinstance(entries, list):
                continue
            kept = [e for e in entries if not _is_kata_entry(e, marker)]
            removed = len(entries) - len(kept)
            if removed:
                removed_any = True
                report["hooks"][event] = removed
                if kept:
                    hooks[event] = kept
                else:
                    del hooks[event]
        if removed_any and not hooks:
            del cleaned["hooks"]

    sl = cleaned.get("statusLine")
    if isinstance(sl, dict):
        cmd = sl.get("command", "")
        if marker in cmd:
            idx = cmd.find(_CHAIN_SEP)
            if idx != -1:
                # chain-wrapped user command — restore the verbatim original tail.
                new_sl = copy.deepcopy(sl)
                new_sl["command"] = cmd[idx + len(_CHAIN_SEP):]
                cleaned["statusLine"] = new_sl
                report["statusline"] = "unwrapped"
            else:
                # kata-set statusLine (no prior user command) — remove the key.
                del cleaned["statusLine"]
                report["statusline"] = "removed"

    return cleaned, report


# --------------------------------------------------------------------------- #
# I/O shell (thin)
# --------------------------------------------------------------------------- #


def host_settings_path(host_dir: str | Path | None = None) -> Path:
    """``<host_dir>/settings.json`` (default host_dir: ``~/.claude``)."""
    base = _safe_abs(host_dir) if host_dir is not None else (Path.home() / ".claude")
    return base / "settings.json"


def read_host_settings(path: Path) -> dict:
    """Strict fail-closed read: ``utf-8-sig`` (lossless BOM strip) + strict ``json.loads``.

    File absent ⇒ ``{}`` (a fresh install target).  Unparseable ⇒
    :class:`HostSettingsError` whose message distinguishes "a BOM was present and WAS
    handled — the JSON itself is corrupt" from plain no-BOM corruption (D136: never
    guess, never lossy-recover someone's live settings).
    """
    if not path.exists():
        return {}
    raw = path.read_bytes()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig")
        data = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        bom_note = (
            "a UTF-8 BOM was present and was handled (utf-8-sig) — the JSON content itself is corrupt"
            if had_bom
            else "no BOM present — the JSON content is corrupt"
        )
        raise HostSettingsError(
            f"kata_host_settings: refusing to touch unparseable host settings file {path} "
            f"({bom_note}): {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise HostSettingsError(
            f"kata_host_settings: host settings file {path} is not a JSON object — refusing to guess"
        )
    return data


def backup_host_settings(path: Path) -> Path | None:
    """Byte-exact timestamped backup ``settings.json.kata-backup-<UTC ts>`` (pre-change).

    Returns the backup path, or ``None`` when the settings file does not exist yet
    (nothing to lose).  Never compared afterwards (law-6-legal).
    """
    if not path.exists():
        return None
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    backup = path.with_name(f"{path.name}.kata-backup-{ts}")
    backup.write_bytes(path.read_bytes())
    return backup


def write_host_settings_atomic(path: Path, data: dict) -> None:
    """Atomic write: temp file in the same dir + ``os.replace``; no ``sort_keys``.

    ``indent=2`` standard dump (the file is never byte-compared); user key ORDER is
    preserved because the merge core mutates deep copies in place and ``json.dumps``
    keeps insertion order.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=path.name + ".", suffix=".kata-tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(data, indent=2) + "\n")
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def settings_diff(before: dict, after: dict, path: Path) -> str:
    """Unified diff of the settings change (what consent shows the operator)."""
    a = json.dumps(before, indent=2).splitlines(keepends=True)
    b = json.dumps(after, indent=2).splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(a, b, fromfile=f"{path} (current)", tofile=f"{path} (proposed)")
    )


def default_snippet_path(repo: str | Path) -> Path:
    """``<repo>/adapters/claude/settings.snippet.json`` — the adapter's snippet."""
    return _safe_abs(repo) / "adapters" / "claude" / "settings.snippet.json"


def apply_hooks_change(
    repo: str | Path,
    host_dir: str | Path | None = None,
    uninstall: bool = False,
    dry_run: bool = False,
    venv_exists: bool | None = None,
    snippet_path: str | Path | None = None,
) -> dict:
    """Render + merge (or unmerge) kata's snippet into the host settings file.

    The one I/O orchestration entry point ``kata_install.main`` calls.  Sequence:
    strict read → pure merge/unmerge → diff; then (unless ``dry_run`` or no change)
    timestamped backup BEFORE any change, then atomic write.  Consent/prompting is the
    CALLER's job — this function never prompts.

    Returns ``{ok, changed, dryRun, uninstall, path, backup, report, diff}``.
    Raises :class:`HostSettingsError` (fail-closed, D136) on an unparseable host file.
    """
    repo_abs = _safe_abs(repo)
    sp = _safe_abs(snippet_path) if snippet_path is not None else default_snippet_path(repo_abs)
    snippet = json.loads(sp.read_text(encoding="utf-8-sig"))
    rendered = render_snippet(snippet, repo_abs, venv_exists=venv_exists)

    path = host_settings_path(host_dir)
    existing = read_host_settings(path)  # fail-closed on corruption
    if uninstall:
        new, report = unmerge_host_settings(existing, rendered)
    else:
        new, report = merge_host_settings(existing, rendered)

    changed = new != existing
    result: dict = {
        "ok": True,
        "changed": changed,
        "dryRun": dry_run,
        "uninstall": uninstall,
        "path": str(path),
        "backup": None,
        "report": report,
        "diff": settings_diff(existing, new, path),
    }
    if dry_run or not changed:
        return result

    backup = backup_host_settings(path)  # BEFORE any change; None on fresh install
    result["backup"] = str(backup) if backup is not None else None
    write_host_settings_atomic(path, new)
    return result
