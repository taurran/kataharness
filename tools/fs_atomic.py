"""fs_atomic.py — shared atomic text-file writer (D159).

A live race investigation (2026-07-12c) reproduced reader corruption — phantom
IndentationError, empty reads, partial reads — against the naive truncate-then-write
(``Path.write_text`` / ``open('w')``), and proved same-directory tmp + ``os.replace``
produces ZERO corruption across 12,606 rewrites.  This module is the ONE shared home
for that pattern, mirroring the two proven in-tree implementations
(``kata_statusline.write_bridge`` and ``kata_host_settings.write_host_settings_atomic``):

    mkstemp in the SAME directory  →  write via os.fdopen  →  os.replace over the
    final name  →  orphan-tmp cleanup on ANY failure.

A reader therefore only ever sees the complete old bytes or the complete new bytes —
never a truncated or half-written file.  The tmp lives beside the destination so the
rename never crosses a filesystem (a cross-device rename is not atomic).

Byte-compatibility note: the file handle is opened WITHOUT a ``newline`` override, so
platform newline translation matches ``Path.write_text`` exactly — converting a
``write_text`` call site to :func:`atomic_write_text` is byte-identical output-wise.

Zero repo-internal dependencies by design: the call sites (function_model,
debug_report, benchmark, iac_apply, intent_scaffold) are themselves low-dependency
leaf modules, and importing a heavier util module from them would invert the
dependency direction.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Atomically write *text* to *path* (same-dir tmp + ``os.replace``).

    Drop-in replacement for ``Path(path).write_text(text, encoding=...)`` with the
    same bytes on disk (including platform newline translation) but crash- and
    race-safe: a concurrent reader never observes a partial file, and the previous
    content survives intact if the write fails.

    Args:
        path:     Destination file path.  The parent directory must exist
                  (call sites ``mkdir`` first, exactly as they did for
                  ``write_text``).
        text:     Full text content to write.
        encoding: Text encoding (default ``"utf-8"``, the repo-wide pin).

    Raises:
        OSError: on any I/O failure; the orphan tmp file is removed first and the
            pre-existing destination (if any) is left untouched.
    """
    dest = Path(path)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(dest.parent), prefix=dest.name + ".", suffix=".kata-tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding) as fh:
            fh.write(text)
        os.replace(tmp_name, dest)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
