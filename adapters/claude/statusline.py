"""adapters/claude/statusline.py — Claude Code statusLine adapter for KataHarness.

This is the thin glue layer that wires the Claude Code 'statusLine' command hook
into the agnostic core (tools/kata_statusline.py).  It is NOT unit-tested; it is
integration-smoked by piping a Claude-shaped JSON through it.

What it does:
    1. Adds the repo's tools/ directory to sys.path (lazy, resolved from __file__).
    2. Reads all of stdin (the Claude statusLine JSON payload).
    3. Calls kata_statusline.statusline_from_event(text) — which is already fail-soft.
    4. Prints the result WITHOUT a trailing newline (Claude renders the bare string).

Fail-soft contract: any exception in this glue layer prints nothing and exits 0.
Claude ignores non-zero exits and empty stdout alike; never crashing is the priority.

Bridge writing (CA-L1/CA-L2 — no change needed here): the superset context-usage
bridge (%TEMP%/kata-ctx-<session_id>.json) is written by the CORE
(kata_statusline.statusline_from_event → write_bridge, A1), BEFORE the render path and
independent of a kata cwd.  This is the FRESH-PROFILE owner (no user statusline exists);
when a user statusline DOES exist, kata never clobbers it and instead offers the
chaining wrapper (adapters/claude/statusline_chain.py, A2).  This glue therefore needs
no bridge logic of its own — confirm-and-delegate only.

See also: adapters/claude/README.md for installation, the chaining wrapper, and rationale.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _main() -> None:
    # --- add repo tools/ to sys.path (relative to this file: adapters/claude/ -> ../../tools/) ---
    tools_dir = Path(__file__).resolve().parents[2] / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))

    # --- UTF-8 reconfigure: handle Unicode glyphs (改善型, ▰▱) on Windows consoles ---
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError, OSError):
        pass

    # --- read stdin and delegate to the agnostic core ---
    import kata_statusline  # noqa: PLC0415  (import inside function for path safety)

    stdin_text = sys.stdin.read()
    result = kata_statusline.statusline_from_event(stdin_text)
    # statusline_from_event is already fail-soft; print with no trailing newline
    print(result, end="")


try:
    _main()
except Exception:  # noqa: BLE001  (fail-soft: never crash or hang Claude's statusline)
    pass
