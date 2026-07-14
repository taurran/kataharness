"""adapters/claude/hooks/kata-gauge-check.py — UserPromptSubmit conductor gauge check (CG-L1).

Mechanizes the conductor's 0.70 context-gauge check on EVERY user turn (D152; fixes audit
C-1/C-2: the check was unenforced prose inside kata-orchestrate's wave loop). On each
UserPromptSubmit this hook reads the kata statusline bridge, evaluates the existing tested
gauge engine (:mod:`kata_gauge`), and — when the trigger fraction is crossed — injects a
one-line ``[KATA CONTEXT GAUGE]`` directive into the model context via
``hookSpecificOutput.additionalContext`` (GROUNDING-CLAUDE.md — same CONFIRMED mechanism as
kata-sessionstart.py, with ``hookEventName: "UserPromptSubmit"``).

Contract (DESIGN CG-L1, FROZEN 2026-07-12):
- Stdin: the UserPromptSubmit hook JSON; fields used are ``session_id`` and ``cwd``.
- **Kata-scope gate (freeze-gate F-3, mandatory):** inject ONLY when the cwd shows kata-run
  evidence — a ``.kata/`` dir or ``kata.config`` file at or above cwd, bounded upward walk
  (the shared ``kata_scope`` helper: cap ``kata_scope._SCOPE_WALK_CAP`` levels, stop at the
  filesystem root). The start path is resolved by ``kata_scope.resolve_start`` (cwd first,
  ``workspace.current_dir`` fallback) with this hook's ``os.getcwd()`` posture wrapping its
  None (D160/EV-1 — ONE definition, drift-test-pinned; the hook keeps NO local payload-cwd
  parsing of its own). A global hook must not push kata directives into non-kata sessions.
  Not found ⇒ print nothing, exit 0.
- Bridge: ``tempfile.gettempdir()/kata-ctx-<session_id>.json`` — the writer's EXACT
  resolution (kata_statusline.write_bridge / statusline_from_event; freeze-gate F-8 — never
  a raw ``%TEMP%`` env read). ``session_id`` is interpolated into filenames, so it is
  sanitized mirroring kata_statusline's ``_SAFE_SESSION_ID`` guard (CWE-22/CWE-23); an
  unsafe id ⇒ silent exit 0.
- Engine: ``kata_gauge.resolve_gauge`` (which walks ``read_bridge`` fail-closed) →
  ``trigger_crossed`` at the default :data:`kata_gauge.DEFAULT_TRIGGER_FRACTION` (0.70).
  Bridge absent / stale / corrupt (``source: "none"``) ⇒ silent exit 0.
- **Once-per-crossing dedupe (F-3):** sidecar ``kata-gauge-notified-<session_id>.json``
  (same temp dir) records the last-notified fraction. Notify on the first crossing;
  re-notify only when the current fraction has grown ≥ :data:`_RENOTIFY_GROWTH` (0.05)
  since the last notification. Sidecar writes are atomic (temp + ``os.replace``); a
  corrupt sidecar is treated as absent.
- FAIL-SOFT / NEVER EXIT 2 (F-8): a UserPromptSubmit exit 2 blocks AND erases the user's
  prompt, so this hook is structurally guaranteed never to do it — the entire body runs
  under one try/except that exits 0. Never raises, never exits nonzero, never blocks.

Usage:
    Invoked by Claude Code via the UserPromptSubmit hook entry in
    adapters/claude/settings.snippet.json. Also callable directly for testing:

        python adapters/claude/hooks/kata-gauge-check.py < event.json
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

#: session_id is interpolated into the bridge/sidecar filenames; accept only a safe
#: charset (UUIDs are `[0-9a-fA-F-]`). Combined with the explicit ".." reject below,
#: this blocks path traversal / separator injection (CWE-22/CWE-23). Mirrors
#: kata_statusline._SAFE_SESSION_ID (the bridge WRITER's guard) exactly.
_SAFE_SESSION_ID = re.compile(r"\A[A-Za-z0-9._-]+\Z")

#: Dedupe re-notify growth (F-3): re-inject only when the current fraction has grown
#: at least this much past the last-notified fraction.
_RENOTIFY_GROWTH = 0.05

#: Comparator slack for the growth check — floats only (0.75 + 0.05 style sums);
#: never widens the gate by a meaningful amount.
_FLOAT_EPS = 1e-9


def _read_last_notified(sidecar: Path) -> float | None:
    """Return the last-notified fraction from the dedupe sidecar, or None.

    Absent, unreadable, unparseable, wrong-shaped, non-numeric, or out-of-range
    (outside [0, 1], incl. NaN) ⇒ None — a corrupt sidecar is treated as absent
    (the protective direction: notify rather than silently never notify).
    """
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("last_notified_fraction")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    fraction = float(value)
    if not (0.0 <= fraction <= 1.0):  # False for NaN too
        return None
    return fraction


def _write_last_notified(temp_dir: Path, safe_session_id: str, fraction: float) -> None:
    """Atomically record *fraction* in the dedupe sidecar (temp + os.replace).

    Mirrors kata_statusline.write_bridge's atomic pattern: a sibling temp file in the
    SAME directory, then os.replace, so a reader never sees a partial file. Fail-soft:
    a write failure cleans up the orphan temp and returns (never raises).
    """
    final = temp_dir / f"kata-gauge-notified-{safe_session_id}.json"
    fd, tmp_name = tempfile.mkstemp(
        dir=str(temp_dir), prefix="kata-gauge-notified-", suffix=".json.tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump({"last_notified_fraction": fraction}, fh)
        os.replace(tmp_name, final)
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass


def _main() -> None:
    """Read the UserPromptSubmit event; inject the gauge directive iff crossed + deduped."""
    # Bytes-read + explicit UTF-8: Windows text-mode stdin defaults to the ANSI
    # codepage, so a non-ASCII cwd would UnicodeDecodeError into a silent no-op
    # (mirrors kata-sessionstart.py F7).
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    payload = json.loads(raw) if raw.strip() else {}
    if not isinstance(payload, dict):
        return

    # ------------------------------------------------------------------ #
    # Kata-scope gate (F-3, mandatory, FIRST): a global hook must stay
    # invisible outside kata runs — no bridge read, no output. The walk +
    # payload→start resolution live in the shared kata_scope helper (D160/
    # EV-1, ONE definition); this hook wraps its None with the getcwd
    # posture and keeps NO local payload-cwd parsing of its own (v2-F1).
    # ------------------------------------------------------------------ #
    scope_dir = Path(__file__).resolve().parents[3] / "tools"  # tools/kata_scope.py (U1 home)
    if str(scope_dir) not in sys.path:
        sys.path.insert(0, str(scope_dir))
    import kata_scope  # noqa: PLC0415  (deferred import — path must be set first)

    start = kata_scope.resolve_start(payload) or Path(os.getcwd())
    if not kata_scope.is_kata_scope(start):
        return

    # ------------------------------------------------------------------ #
    # session_id names the bridge + sidecar files: sanitize it mirroring
    # kata_statusline._SAFE_SESSION_ID (CWE-22/CWE-23). Unsafe ⇒ silent 0.
    # ------------------------------------------------------------------ #
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return
    if ".." in session_id or not _SAFE_SESSION_ID.match(session_id):
        return

    # ------------------------------------------------------------------ #
    # Add the HARNESS's tools/ to sys.path so kata_gauge imports without
    # install: this file lives at <harness>/adapters/claude/hooks/.
    # ------------------------------------------------------------------ #
    tools_dir = Path(__file__).resolve().parents[3] / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))

    import kata_gauge  # noqa: PLC0415  (deferred import — path must be set first)

    # Bridge path: the writer's exact convention (kata_statusline.py — F-8):
    # tempfile.gettempdir() / kata-ctx-<session_id>.json.
    temp_dir = Path(tempfile.gettempdir())
    bridge_path = temp_dir / f"kata-ctx-{session_id}.json"

    gauge = kata_gauge.resolve_gauge(
        bridge_path, None, now_utc=datetime.now(timezone.utc)
    )
    if gauge.get("source") == "none":
        return  # absent / stale / corrupt bridge ⇒ silent (fail-closed walk exhausted)

    sidecar = temp_dir / f"kata-gauge-notified-{session_id}.json"

    if not kata_gauge.trigger_crossed(gauge):  # DEFAULT_TRIGGER_FRACTION = 0.70
        # Below trigger with a READABLE gauge: clear the dedupe high-water mark so a
        # post-handoff/compaction context drop re-arms the notification for the next
        # crossing (adval G-1 — without this, a fresh climb past 0.70 stays suppressed
        # behind the pre-drop mark).
        try:
            sidecar.unlink()
        except OSError:
            pass  # absent or locked — nothing to re-arm / next readable sub-trigger turn retries
        return

    # ------------------------------------------------------------------ #
    # Once-per-crossing dedupe (F-3): notify on the first crossing; re-notify
    # only when the fraction has grown >= _RENOTIFY_GROWTH since last notice.
    # A sub-trigger turn clears the sidecar above, so each CROSSING re-fires.
    # ------------------------------------------------------------------ #
    used_pct = float(gauge["used_pct"])
    fraction = used_pct / 100.0
    last = _read_last_notified(sidecar)
    if last is not None and fraction < last + _RENOTIFY_GROWTH - _FLOAT_EPS:
        return

    trigger_pct = round(kata_gauge.DEFAULT_TRIGGER_FRACTION * 100)
    context = (
        f"[KATA CONTEXT GAUGE] context at {round(used_pct)}% of the effective window "
        f"(trigger {trigger_pct}%). Execute kata-selfhandoff at the next task boundary "
        "— refresh .planning/HANDOFF.md before continuing new work."
    )
    # Emit FIRST, then record the sidecar (adval G-2): a stdout failure must not
    # mark the crossing as notified-without-delivering.
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": context,
                }
            }
        )
    )
    _write_last_notified(temp_dir, session_id, fraction)


if __name__ == "__main__":
    # F-8 STRUCTURAL GUARANTEE: the entire body runs under this one try/except and
    # the process ALWAYS falls off main ⇒ exit 0. No explicit exit call exists
    # anywhere in this file — a UserPromptSubmit nonzero exit (worst case: 2)
    # would block and erase the user's prompt.
    try:
        _main()
    except Exception as exc:  # noqa: BLE001  (fail-soft: never touch the user's prompt)
        # One stderr breadcrumb so a broken install is distinguishable from a
        # clean no-op; still exit 0.
        try:
            print(f"[kata-gauge-check] fail-soft: {type(exc).__name__}: {exc}", file=sys.stderr)
        except Exception:  # noqa: BLE001
            pass
