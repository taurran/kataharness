"""test_fs_atomic.py — D159: shared atomic text writer + the five converted artifact writers.

A live race investigation (2026-07-12c) reproduced reader corruption (phantom
IndentationError / empty / partial reads) against non-atomic truncate-then-write and
proved same-dir tmp + ``os.replace`` produces ZERO corruption in 12,606 rewrites.

Covers:
1. ``fs_atomic.atomic_write_text`` — content lands, overwrite is whole, tmp is created in
   the SAME directory (cross-device rename can never happen), orphan tmp is cleaned on a
   simulated ``os.replace`` failure, prior content survives a failed write, encoding is
   honoured, and newline translation is byte-identical to ``Path.write_text``.
2. The five proven-corruptible writer sites (function_model / debug_report / benchmark /
   iac_apply / intent_scaffold) now route through ``atomic_write_text`` — pinned both by
   source inspection (no residual ``.write_text(`` in the writer) and by a functional
   round-trip that also asserts no orphan tmp files remain.
"""

from __future__ import annotations

import importlib
import inspect
import json
import os
from pathlib import Path

import pytest

import fs_atomic
from fs_atomic import atomic_write_text

# ---------------------------------------------------------------------------
# 1. Helper unit tests
# ---------------------------------------------------------------------------


def test_content_lands(tmp_path):
    dest = tmp_path / "out.json"
    atomic_write_text(dest, '{"a": 1}')
    assert dest.read_text(encoding="utf-8") == '{"a": 1}'


def test_non_ascii_content_utf8(tmp_path):
    dest = tmp_path / "out.txt"
    atomic_write_text(dest, "héllo — ünïcode")
    assert dest.read_text(encoding="utf-8") == "héllo — ünïcode"


def test_encoding_parameter_honoured(tmp_path):
    dest = tmp_path / "out16.txt"
    atomic_write_text(dest, "héllo", encoding="utf-16")
    assert dest.read_text(encoding="utf-16") == "héllo"


def test_overwrite_replaces_whole_content(tmp_path):
    """New content fully replaces old — no truncate-then-write tail residue."""
    dest = tmp_path / "out.txt"
    dest.write_text("OLD-CONTENT-MUCH-LONGER-THAN-THE-NEW-ONE", encoding="utf-8")
    atomic_write_text(dest, "new")
    assert dest.read_text(encoding="utf-8") == "new"


def test_no_tmp_left_behind_on_success(tmp_path):
    dest = tmp_path / "out.txt"
    atomic_write_text(dest, "x")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["out.txt"]


def test_tmp_created_in_same_directory(tmp_path, monkeypatch):
    """The tmp file must be a SIBLING of the destination so os.replace never
    crosses a filesystem (cross-device rename is not atomic)."""
    seen: list[tuple[str, str]] = []
    real_replace = os.replace

    def recording_replace(src, dst):
        seen.append((str(src), str(dst)))
        return real_replace(src, dst)

    monkeypatch.setattr(fs_atomic.os, "replace", recording_replace)
    dest = tmp_path / "sub" / "out.txt"
    dest.parent.mkdir()
    atomic_write_text(dest, "x")
    assert len(seen) == 1
    src, dst = seen[0]
    assert Path(src).parent == dest.parent, "tmp must live in the destination directory"
    assert Path(dst) == dest


def test_orphan_tmp_cleaned_on_replace_failure(tmp_path, monkeypatch):
    """Simulated os.replace failure: the exception propagates AND the orphan tmp
    is removed — the directory holds no *.kata-tmp litter."""

    def boom(src, dst):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(fs_atomic.os, "replace", boom)
    dest = tmp_path / "out.txt"
    with pytest.raises(OSError, match="simulated replace failure"):
        atomic_write_text(dest, "x")
    assert list(tmp_path.iterdir()) == [], "orphan tmp must be cleaned up on failure"


def test_prior_content_survives_failed_write(tmp_path, monkeypatch):
    """A failed rewrite never destroys the existing artifact (the atomicity point)."""
    dest = tmp_path / "out.txt"
    dest.write_text("intact", encoding="utf-8")

    def boom(src, dst):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(fs_atomic.os, "replace", boom)
    with pytest.raises(OSError):
        atomic_write_text(dest, "torn")
    assert dest.read_text(encoding="utf-8") == "intact"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["out.txt"]


def test_newline_translation_matches_write_text(tmp_path):
    """Byte-identical LF handling vs the Path.write_text default (platform newline
    translation unchanged) — the D159 BC requirement."""
    text = "line1\nline2\n"
    via_helper = tmp_path / "helper.txt"
    via_write_text = tmp_path / "legacy.txt"
    atomic_write_text(via_helper, text)
    via_write_text.write_text(text, encoding="utf-8")
    assert via_helper.read_bytes() == via_write_text.read_bytes()


# ---------------------------------------------------------------------------
# 2. The five converted writer sites
# ---------------------------------------------------------------------------

_SITES = [
    ("function_model", "emit_function_model"),
    ("debug_report", "emit_debug_report"),
    ("benchmark", "emit_scorecard"),
    ("iac_apply", "emit_iac_apply"),
    ("intent_scaffold", "write_intent"),
]


@pytest.mark.parametrize(("modname", "funcname"), _SITES)
def test_writer_site_routes_through_atomic_write(modname, funcname):
    """Each proven-corruptible writer calls atomic_write_text and has no residual
    non-atomic .write_text( in its body (source-level pin)."""
    mod = importlib.import_module(modname)
    src = inspect.getsource(getattr(mod, funcname))
    assert "atomic_write_text(" in src, f"{modname}.{funcname} must use atomic_write_text"
    assert ".write_text(" not in src, f"{modname}.{funcname} still has a non-atomic write"


def test_emit_function_model_roundtrip_no_orphans(tmp_path):
    import function_model

    dest = tmp_path / "nested" / "fm.json"
    payload = {"name": "f", "confidence": 0.5}
    function_model.emit_function_model(payload, dest)
    assert json.loads(dest.read_text(encoding="utf-8")) == payload
    assert sorted(p.name for p in dest.parent.iterdir()) == ["fm.json"]


def test_emit_function_model_bytes_identical_to_legacy(tmp_path):
    """Output bytes equal the old write_text(json.dumps(..., indent=2,
    ensure_ascii=False)) form exactly (incl. platform newline translation)."""
    import function_model

    payload = {"name": "fé", "n": 1}
    dest = tmp_path / "fm.json"
    function_model.emit_function_model(payload, dest)
    expected = json.dumps(payload, indent=2, ensure_ascii=False).replace("\n", os.linesep)
    assert dest.read_bytes() == expected.encode("utf-8")


def test_emit_debug_report_roundtrip_no_orphans(tmp_path):
    import debug_report

    dest = tmp_path / "debug" / "closeout.json"
    payload = {"schemaVersion": 1, "utc": "2026-07-12T00:00:00+00:00"}
    debug_report.emit_debug_report(payload, dest)
    assert json.loads(dest.read_text(encoding="utf-8")) == payload
    assert sorted(p.name for p in dest.parent.iterdir()) == ["closeout.json"]


def test_emit_scorecard_roundtrip_no_orphans(tmp_path):
    import benchmark

    dest = tmp_path / "benchmark" / "run-1.json"
    payload = {"arms": [], "runId": "run-1"}
    benchmark.emit_scorecard(dest, payload)
    assert json.loads(dest.read_text(encoding="utf-8")) == payload
    assert sorted(p.name for p in dest.parent.iterdir()) == ["run-1.json"]


def test_emit_iac_apply_roundtrip_no_orphans(tmp_path):
    import iac_apply

    dest = tmp_path / "iac" / "apply.json"
    payload = {"schemaVersion": 1, "kind": "terraform", "state": "applied"}
    iac_apply.emit_iac_apply(payload, dest)
    assert json.loads(dest.read_text(encoding="utf-8")) == payload
    assert sorted(p.name for p in dest.parent.iterdir()) == ["apply.json"]


def test_write_intent_roundtrip_no_orphans(tmp_path):
    import intent_scaffold

    answers = {
        "kind": "version-up",
        "goal": "atomic-write regression coverage",
        "fixes": [],
        "features": [],
        "modulesAdded": [],
        "changeSummary": "n/a",
        "target": {"kind": "self", "path": "", "vault": "linked", "platform": "claude"},
        "grillDepth": "standard",
        "readiness": "ready",
    }
    dest = tmp_path / "INTENT.md"
    intent_scaffold.write_intent(str(dest), answers)
    assert dest.read_text(encoding="utf-8") == intent_scaffold.build_intent(answers)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["INTENT.md"]
