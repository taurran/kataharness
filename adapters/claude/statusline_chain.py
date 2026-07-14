"""adapters/claude/statusline_chain.py — the chain-never-clobber statusLine wrapper.

CA-L1 (DESIGN §1, Leg A) verbatim intent: when a user ALREADY has a Claude Code
``statusLine`` command (e.g. the operator's ``gsd-statusline.js``), kata **never
clobbers** it.  Kata offers a **chaining wrapper**: exec the user's script as a child,
pass stdin through UNMODIFIED, print the child's stdout **byte-identical**, and never
touch the user's own output or bridge file.  The wrapper then writes kata's OWN sibling
bridge ``%TEMP%/kata-ctx-<session_id>.json`` (via ``kata_statusline.write_bridge`` — A1)
with the CA-L2 superset schema, atomic temp+rename.  Two files, zero contention (R-32).

**Kata-leg carve-out (D160 replace-in-kata-scopes — the ONE exception to the
byte-identical passthrough above).** When the payload cwd is inside a kata scope
(``kata_scope.find_kata_root`` returns a root — a ``.kata/`` dir or ``kata.config`` file
at/above cwd), the wrapper renders kata's OWN one-line segment to stdout and **does NOT run
the child** — kata renders kata state in kata scopes, the operator's statusline owns
everywhere else.  Outside kata scope (and on unparseable / cwd-less / non-kata stdin) the
CHAIN and SKIP legs stay byte-identical.  ``_write_kata_bridge`` still runs on every leg,
kata scope or not.

Reader priority (documented in README §statusLine chaining / cross-ref ``kata_gauge``):
    (1) kata bridge  →  (2) user bridge (4-field, %-only)  →  (3) deterministic fallback.

Security posture (this is the highest-scrutiny surface in CA-P1 — a subprocess sink that
runs the operator's own statusline command every statusline tick):

  * **list-argv only, NEVER a shell** — the child command is executed as a validated
    ``list[str]`` with ``shell`` left False.  The user's command string is NEVER
    string-interpolated into a shell.
  * **Chain-eligibility gate (the pin):** kata chains ONLY when the user's
    ``statusLine.command`` shlex-parses to plain argv with **NO shell metacharacters**.
    Any metacharacter (``| & ; < > ( ) $ `` ``` ` ``` ``\\ * ? [ ] { } ~ ! #`` /
    newline/tab, plus the cmd.exe-only ``%`` and ``^``), an unbalanced quote, or an
    empty command ⇒ the **SKIP leg**: run no child, emit nothing, still write kata's
    bridge.  A Windows batch target (``.bat``/``.cmd``/``.com`` argv[0], case-insensitive)
    is likewise NEVER chained: CreateProcess runs it via an implicit cmd.exe even under
    ``shell=False``, re-introducing shell evaluation — skip-not-chain.  Re-introducing
    shell evaluation is never an option; the never-clobber guarantee is preserved at
    install time (kata does not wrap an ineligible command — it leaves the user's
    statusline untouched).
  * **Bounded child** — the child runs under a hard timeout (``_CHILD_TIMEOUT_S`` seconds,
    ``[TUNABLE]``).  Child failure / nonzero exit / timeout ⇒ still emit whatever stdout
    the child produced, never hang, exit 0 (the host-statusline fail-soft contract — kata
    must never break the operator's statusline under any failure).

  The ``protocol/exec-safety.md`` sink-registry row for this subprocess is NOT authored
  here (it lands at P2/C10 closeout); this task documents the sink in
  ``adapters/claude/README.md`` §security and rides a NOTE on its commit.  stdlib-only.

Usage (wired by kata's approved settings write slot, CA-L24 — never an implied side
effect):

    "statusLine": {
      "type": "command",
      "command": "python \"<repo>/adapters/claude/statusline_chain.py\" -- <user-command>"
    }

Everything after ``--`` is the user's original ``statusLine.command`` (passed as a single
quoted argument, or as already-split argv).  The wrapper shlex-parses it, checks
eligibility, and runs it as the child.
"""

from __future__ import annotations

import json
import math
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

#: Child timeout in seconds. [TUNABLE] — a statusline tick is sub-second in practice; 5 s
#: is a generous ceiling that still guarantees the wrapper never hangs Claude's status bar.
_CHILD_TIMEOUT_S = 5

#: Shell metacharacters whose presence means the user's command relies on shell semantics
#: (operators, expansions, substitution) that a plain list-argv exec cannot faithfully
#: reproduce.  Any occurrence ⇒ NOT chain-eligible ⇒ the SKIP leg.  Quotes (`"` / `'`) are
#: intentionally NOT here: they are resolved by ``shlex`` (that is what "shlex-parses to
#: plain argv" means).  Backslash IS rejected — it is a shell escape and, under POSIX
#: shlex, would mangle Windows paths; forward slashes keep a command chain-eligible.
#: ``%`` and ``^`` are cmd.exe-only metacharacters (env expansion / escape) — rejected
#: because a Windows batch child re-enters cmd.exe semantics (see the batch gate below).
_SHELL_METACHARS = frozenset("|&;<>()$`\\*?[]{}~!#%^\n\r\t")

#: Windows batch-file vector (live-proven): a ``.bat``/``.cmd``/``.com`` child target is
#: executed via an IMPLICIT cmd.exe even under ``shell=False`` — the argument line is
#: re-parsed with cmd.exe shell semantics, defeating the list-argv guarantee.  Batch
#: targets are therefore skip-not-chain: NEVER eligible.  Checked case-insensitively on
#: the literal argv[0] token (no PATHEXT resolution is performed anywhere in this module).
_BATCH_EXTENSIONS = frozenset({".bat", ".cmd", ".com"})

# --------------------------------------------------------------------------- #
# Kata-native segment (D160 replace-in-kata-scopes) — rendering constants.
# --------------------------------------------------------------------------- #
#: ANSI SGR codes. ``kata`` marker + dirname + run-hint are DIM so the operator can tell at
#: a glance which renderer owns the line; the meter carries the band colour.
_ANSI_DIM = "\x1b[2m"
_ANSI_RESET = "\x1b[0m"
_ANSI_RED = "\x1b[31m"
_ANSI_YELLOW = "\x1b[33m"
_ANSI_GREEN = "\x1b[32m"

#: Segment field separator (U+2502 BOX DRAWINGS LIGHT VERTICAL, spaced) — matches the kata
#: statusline family (`kata_statusline._SEP`).
_SEG_SEP = " │ "

#: Meter width in segments (10-segment bar, DESIGN S2).
_METER_SEGMENTS = 10

#: Meter yellow pre-warning band start, in displayed-percent. A NEW display-only [TUNABLE]
#: introduced HERE (G4 fold): 55 is NOT a kata semantic — the RED boundary alone is derived
#: from kata_gauge (DEFAULT_TRIGGER_FRACTION); yellow is a cosmetic early smell for the bar.
_METER_YELLOW_PCT = 55  # [TUNABLE]


def is_chain_eligible(command_str: str) -> bool:
    """Decision gate (CA-L1 pin): is *command_str* safe to chain as plain list-argv?

    Chain-eligible IFF the command is a non-empty string that (1) contains **no** shell
    metacharacter from :data:`_SHELL_METACHARS`, (2) ``shlex.split``-parses to at least
    one token, and (3) the argv[0] target is NOT a Windows batch file
    (:data:`_BATCH_EXTENSIONS`, case-insensitive — a batch child runs via an implicit
    cmd.exe despite ``shell=False``, re-introducing shell evaluation).  Anything else ⇒
    ``False`` ⇒ the SKIP leg (never a shell eval).

    This is pure decision code — no I/O, no side effects — so it is mutation-provable in
    isolation.
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
    # Windows batch-file gate: .bat/.cmd/.com argv[0] ⇒ implicit cmd.exe ⇒ NOT eligible.
    if Path(tokens[0]).suffix.lower() in _BATCH_EXTENSIONS:
        return False
    return True


def parse_tail(argv: List[str]) -> Optional[List[str]]:
    """Return the argv tail after the first ``--`` separator, or ``None`` if absent/empty.

    ``argv`` is the process argv (``argv[0]`` is this script).  Everything after ``--`` is
    the user's original ``statusLine`` command.
    """
    try:
        idx = argv.index("--", 1)
    except ValueError:
        return None
    tail = argv[idx + 1:]
    return tail if tail else None


def child_argv(tail: Optional[List[str]]) -> Optional[List[str]]:
    """Normalize the argv tail to a validated child argv, or ``None`` for the SKIP leg.

    The tail is either a single element (the user's command STRING, shlex-parsed here — the
    CA-L1 pin) or already-split argv (re-joined with ``shlex.join`` so the ONE eligibility
    path applies).  Returns the child ``list[str]`` when chain-eligible, else ``None``.
    """
    if not tail:
        return None
    command_str = tail[0] if len(tail) == 1 else shlex.join(tail)
    if not is_chain_eligible(command_str):
        return None
    try:
        argv = shlex.split(command_str)
    except ValueError:
        return None
    return argv or None


def run_child(argv: List[str], stdin_bytes: bytes, timeout: int = _CHILD_TIMEOUT_S) -> bytes:
    """Run the child statusline command as list-argv (``shell=False``); return its stdout.

    stdin is passed through **unmodified**.  The return value is the child's stdout **bytes**
    (byte-identical passthrough).  Fail-soft: a nonzero exit still returns the captured
    stdout; a timeout returns whatever partial stdout was buffered; a missing program /
    invalid argv returns ``b""``.  NEVER raises, NEVER hangs (bounded by *timeout*).
    """
    try:
        result = subprocess.run(  # noqa: S603 — list-argv, shell=False, validated child
            argv,
            input=stdin_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            shell=False,
        )
        return result.stdout or b""
    except subprocess.TimeoutExpired as exc:
        # emit any partial stdout the child produced before the deadline; never hang.
        return exc.stdout or b""
    except (OSError, ValueError):
        # missing program, empty argv, etc. — SKIP silently (fail-soft).
        return b""


def _import_kata_scope():
    """Import ``kata_scope`` from tools/ (its core home since U1 — the SAME sys.path pattern
    ``_import_kata_gauge`` uses), mirroring the bridge-import path insert. Returns the module.
    Raising is the caller's cue to take the existing legs (it cannot confirm kata scope)."""
    tools_dir = Path(__file__).resolve().parents[2] / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    import kata_scope  # noqa: PLC0415 — deferred import (path set first)

    return kata_scope


def _import_kata_gauge():
    """Import ``kata_gauge`` from tools/ (the SAME sys.path pattern ``_write_kata_bridge``
    uses) so the meter's RED boundary is DERIVED from ``DEFAULT_TRIGGER_FRACTION`` — never a
    literal 70 (structural agreement with the D152 gauge)."""
    tools_dir = Path(__file__).resolve().parents[2] / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    import kata_gauge  # noqa: PLC0415 — deferred import (path set first)

    return kata_gauge


def _strip_control(text: str) -> str:
    """Strip C0 (U+0000–U+001F), DEL (U+007F), and C1 (U+0080–U+009F) control characters.

    Terminal-escape injection via a hostile directory name (an ESC/CSI in a dir basename)
    is the vector (G7d fold): a directory named ``\\x1b[31mowned`` would recolour the whole
    status bar. The ESC that drives every such attack lives in the C0 range, so stripping
    C0/C1/DEL neutralizes the class while leaving printable names intact.
    """
    return "".join(ch for ch in text if not (ord(ch) < 0x20 or 0x7F <= ord(ch) <= 0x9F))


def _bar10(used_pct: float) -> str:
    """Return a 10-segment ``▰``/``▱`` bar for *used_pct* (0..100), clamped."""
    filled = max(0, min(_METER_SEGMENTS, round(used_pct / 100 * _METER_SEGMENTS)))
    return "▰" * filled + "▱" * (_METER_SEGMENTS - filled)


def _render_meter(payload: dict, kata_gauge) -> str:  # noqa: ANN001
    """Return the ` {bar} {used}%` meter, or "" when there is no numeric gauge to show.

    ``used_pct`` = raw ``100 − remaining_percentage`` (kata's own semantics — exactly what
    ``write_bridge`` records; NO GSD-style buffer normalization). The colour band and the
    printed percent both key off the ROUNDED displayed value so they always agree: RED at/above
    the kata trigger (``DEFAULT_TRIGGER_FRACTION × 100``, imported — never a literal 70),
    YELLOW at/above the display-only pre-warning band, GREEN below.

    ``remaining_percentage`` absent OR non-numeric (mirroring ``write_bridge``'s ``_is_number``)
    ⇒ the meter is OMITTED (return "") — never blank the whole segment for a malformed meter
    field (v2-F6).
    """
    context_window = payload.get("context_window")
    remaining = context_window.get("remaining_percentage") if isinstance(context_window, dict) else None
    # NaN/Infinity pass _is_number but blow up round() — a malformed meter field must
    # omit ONLY the meter, never blank the whole segment (v2-F6; sweep finding 3).
    if not kata_gauge._is_number(remaining) or not math.isfinite(remaining):
        return ""

    used_pct = 100 - remaining
    displayed = round(used_pct)
    red_boundary = kata_gauge.DEFAULT_TRIGGER_FRACTION * 100  # DERIVED, never a literal 70
    if displayed >= red_boundary:
        colour = _ANSI_RED
    elif displayed >= _METER_YELLOW_PCT:
        colour = _ANSI_YELLOW
    else:
        colour = _ANSI_GREEN
    return f" {colour}{_bar10(used_pct)} {displayed}%{_ANSI_RESET}"


def _render_run_hint(root: Path) -> str:
    """Return ` │ run` (dim) when ``<root>/.kata/board.md`` exists non-empty, else "".

    ``root`` is the value the ONE ``find_kata_root`` call in the kata leg already returned
    (v2-F6: reuse its result — no second walk). Cheap existence+size check only; the board
    is never parsed. A probe OSError ⇒ omit the hint (never blank the whole segment)."""
    board = root / ".kata" / "board.md"
    try:
        if board.is_file() and board.stat().st_size > 0:
            return f"{_SEG_SEP}{_ANSI_DIM}run{_ANSI_RESET}"
    except OSError:
        return ""
    return ""


def _render_segment(payload: dict, start: Path, root: Path) -> str:
    """Render the pinned kata segment: ``kata │ {dirname}{meter}{run}`` (DESIGN S2).

    ``{dirname}`` is the basename of the payload cwd (``start``), dim, with control chars
    stripped; ``{meter}`` keys off ``context_window.remaining_percentage``; ``{run}`` keys off
    the board at ``root`` (the ancestor the ONE walk returned)."""
    kata_gauge = _import_kata_gauge()
    marker = f"{_ANSI_DIM}kata{_ANSI_RESET}"
    dirname = f"{_ANSI_DIM}{_strip_control(start.name)}{_ANSI_RESET}"
    meter = _render_meter(payload, kata_gauge)
    run = _render_run_hint(root)
    return f"{marker}{_SEG_SEP}{dirname}{meter}{run}"


def _kata_leg(payload: dict) -> Optional[str]:
    """Return the kata segment (or "") when the cwd is kata-scoped, else None.

    - ``None`` ⇒ NOT a kata scope (cwd-less / non-kata / scope undeterminable) ⇒ the caller
      takes the existing byte-identical CHAIN/SKIP legs.
    - ``""`` ⇒ kata scope confirmed but an error occurred INSIDE rendering ⇒ emit nothing,
      still DO NOT run the child (fail-soft, exit 0).
    - a non-empty string ⇒ the rendered segment to emit (child not run).
    """
    try:
        kata_scope = _import_kata_scope()
        start = kata_scope.resolve_start(payload)
        if start is None:
            return None
        root = kata_scope.find_kata_root(start)
        if root is None:
            return None
    except Exception:  # noqa: BLE001 — scope undeterminable ⇒ existing legs (never guess)
        return None
    try:
        return _render_segment(payload, start, root)
    except Exception:  # noqa: BLE001 — in-scope render error ⇒ emit nothing, never run child
        return ""


def _parse_payload(stdin_bytes: bytes) -> Optional[dict]:
    """Parse stdin to a JSON object, or None (non-JSON / non-object). Never raises."""
    try:
        data = json.loads(stdin_bytes.decode("utf-8", errors="replace"))
    except (ValueError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def _write_kata_bridge(stdin_bytes: bytes) -> None:
    """Write kata's OWN superset bridge from the SAME stdin (A1's ``write_bridge``).

    Never touches the user's bridge file.  Fail-soft: any error is swallowed (the
    observability-write exception to fail-closed — must never break the host statusline).
    """
    try:
        tools_dir = Path(__file__).resolve().parents[2] / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        import kata_statusline  # noqa: PLC0415 — deferred import (path set first)

        data = json.loads(stdin_bytes.decode("utf-8", errors="replace"))
        if isinstance(data, dict):
            kata_statusline.write_bridge(tempfile.gettempdir(), data)
    except Exception:  # noqa: BLE001 — fail-soft observability write; never raise to host
        pass


def _main() -> None:
    """Kata-leg-or-chain-or-skip: render kata's segment in kata scopes (child NOT run),
    otherwise run the user's child (byte-identical passthrough); write kata's bridge always."""
    stdin_bytes = sys.stdin.buffer.read()

    payload = _parse_payload(stdin_bytes)
    segment = _kata_leg(payload) if payload is not None else None
    if segment is not None:
        # KATA leg (D160 replace-in-kata-scopes): emit kata's OWN segment ("" on an in-scope
        # render error), NEVER run the child. The bridge below still writes on this leg too.
        if segment:
            sys.stdout.buffer.write(segment.encode("utf-8"))
            sys.stdout.buffer.flush()
        _write_kata_bridge(stdin_bytes)
        return

    argv = child_argv(parse_tail(sys.argv))
    if argv is not None:
        # CHAIN leg: exec the user's command, pass stdin through, emit stdout byte-identical.
        out = run_child(argv, stdin_bytes)
        sys.stdout.buffer.write(out)
        sys.stdout.buffer.flush()
    # else SKIP leg: no eligible child — emit nothing (never break the user's statusline;
    # kata's own bridge below still feeds the gauge / deterministic fallback).

    # Kata's sibling bridge — the user's file is untouched either way (R-32, two files).
    _write_kata_bridge(stdin_bytes)


if __name__ == "__main__":
    try:
        _main()
    except Exception:  # noqa: BLE001 — fail-soft: never crash or hang Claude's statusline
        pass
