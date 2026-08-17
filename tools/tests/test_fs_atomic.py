"""test_fs_atomic.py — D159: shared atomic text writer + every converted artifact writer.

A live race investigation (2026-07-12c) reproduced reader corruption (phantom
IndentationError / empty / partial reads) against non-atomic truncate-then-write and
proved same-dir tmp + ``os.replace`` produces ZERO corruption in 12,606 rewrites.

Covers:
1. ``fs_atomic.atomic_write_text`` — content lands, overwrite is whole, tmp is created in
   the SAME directory (cross-device rename can never happen), orphan tmp is cleaned on a
   simulated ``os.replace`` failure, prior content survives a failed write, encoding is
   honoured, and newline translation is byte-identical to ``Path.write_text``.
2. The five originally converted writer sites (function_model / debug_report / benchmark /
   iac_apply / intent_scaffold) now route through ``atomic_write_text`` — pinned both by
   source inspection (no residual ``.write_text(`` in the writer) and by a functional
   round-trip that also asserts no orphan tmp files remain.
3. BURN-A: the SIX gate-critical writers the original conversion stopped short of —
   ``run_result.write_result`` (RESULT.json), ``contract_gate.write_contract_gate``
   (contract-gate.json), ``gate_emit.emit_gate_artifacts`` (footprint.json + mutation.json,
   two sites in one function), ``grounding_gate.write_grounding`` (grounding.json),
   ``drift_gate.emit_deferrals`` + ``drift_gate.emit_drift_report``, and
   ``deviation.emit_findings``.  These are the artifacts the evaluator, the benchmark
   scorer and the closeout read WHILE a gate may still be emitting them, so the
   concurrent-partial-read window is exactly the D159 failure mode.  Each is pinned by
   the same two-part shape (source pin + functional round-trip) PLUS an explicit
   byte-identity assertion against the legacy ``Path.write_text`` form, because the
   conversion's stated contract is that no artifact byte changes.

   NOTE ON THE FIX CHOICE: atomicity, not readback.  ``fs_atomic.py:4-15`` records that the
   corruption actually reproduced here was a CONCURRENT READER seeing a partial file — the
   writer's own readback would succeed and see nothing.  Readback is deliberately not built.
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


# ---------------------------------------------------------------------------
# 3. BURN-A — the gate-critical writers the original conversion stopped short of
# ---------------------------------------------------------------------------

# (module, function, number of atomic writes the function must perform).
# gate_emit.emit_gate_artifacts owns THREE of the nine sites (footprint.json,
# mutation.json, and — since the W7 gate-preconditions wiring — preconditions.json)
# in one function body, so the per-function count is pinned rather
# than mere presence — a partial conversion inside that function would otherwise
# still satisfy an "atomic_write_text( in src" check.
_GATE_CRITICAL_SITES = [
    ("run_result", "write_result", 1),  # RESULT.json
    ("contract_gate", "write_contract_gate", 1),  # contract-gate.json
    ("gate_emit", "emit_gate_artifacts", 3),  # footprint.json + mutation.json + preconditions.json (W7)
    ("grounding_gate", "write_grounding", 1),  # grounding.json
    ("drift_gate", "emit_deferrals", 1),  # deviations/deferred.json
    ("drift_gate", "emit_drift_report", 1),  # drift/<finding_id>.json
    ("deviation", "emit_findings", 1),  # deviations/findings.json
]

# A non-ASCII payload with a tab: any accidental change of encoding, newline
# handling or ensure_ascii would move the bytes.
_U = "héllo — ünïcode\ttab"


def _legacy_bytes(tmp_path: Path, text: str) -> bytes:
    """Exact bytes the pre-conversion ``Path.write_text(text, encoding="utf-8")``
    would have put on disk, produced by actually calling it — so the reference is
    the real legacy behaviour (incl. platform newline translation), not a
    re-derivation of it."""
    ref = tmp_path / "_legacy_reference.bytes"
    ref.write_text(text, encoding="utf-8")
    data = ref.read_bytes()
    ref.unlink()
    return data


def test_burn_a_covers_exactly_the_nine_scoped_sites():
    """The frozen contract scoped EIGHT call sites; the ninth (preconditions.json,
    W7 gate-preconditions) joined at Loop-B integration — recorded there, so the
    count is nine and dropping one silently is a test failure rather than an
    invisible omission."""
    assert sum(n for _, _, n in _GATE_CRITICAL_SITES) == 9


@pytest.mark.parametrize(("modname", "funcname", "n_writes"), _GATE_CRITICAL_SITES)
def test_gate_critical_writer_routes_through_atomic_write(modname, funcname, n_writes):
    """Source-level pin: every write in the function is atomic and no residual
    non-atomic ``.write_text(`` survives anywhere in its body."""
    mod = importlib.import_module(modname)
    src = inspect.getsource(getattr(mod, funcname))
    assert src.count("atomic_write_text(") == n_writes, (
        f"{modname}.{funcname} must perform {n_writes} atomic write(s)"
    )
    assert ".write_text(" not in src, f"{modname}.{funcname} still has a non-atomic write"


def test_write_result_atomic_and_byte_identical(tmp_path):
    """run_result.write_result → RESULT.json (read by the evaluator and the
    benchmark scorer while a gate may still be emitting)."""
    import run_result

    payload = {"passed": 12, "failed": 0, "skipped": 1, "note": _U}
    dest = tmp_path / "RESULT.json"
    run_result.write_result(payload, dest)

    assert json.loads(dest.read_text(encoding="utf-8")) == payload
    assert dest.read_bytes() == _legacy_bytes(tmp_path, json.dumps(payload, indent=2))
    assert sorted(p.name for p in tmp_path.iterdir()) == ["RESULT.json"]


def test_write_contract_gate_atomic_and_byte_identical(tmp_path):
    """contract_gate.write_contract_gate → contract-gate.json (the evaluator's
    independence leg reads it; its ABSENCE is the skipped-gate signal)."""
    import contract_gate

    verdict = {
        "passed": True,
        "vacuous": False,
        "findings": [],
        "branch": "burn/a-atomic-writes",
        "surviving_stubs": [],
        "danglers": [],
        "note": _U,
    }
    out_dir = tmp_path / "kata"
    written = contract_gate.write_contract_gate(out_dir, verdict)

    on_disk = json.loads(written.read_text(encoding="utf-8"))
    assert {k: v for k, v in on_disk.items() if k != "utc"} == verdict
    # Reconstruct the legacy bytes independently, borrowing ONLY the wall-clock
    # stamp the writer generates.  The trailing "\n" and sort_keys are part of
    # this artifact's shape and are asserted here.
    expected = dict(verdict)
    expected["utc"] = on_disk["utc"]
    assert written.read_bytes() == _legacy_bytes(
        tmp_path, json.dumps(expected, indent=2, sort_keys=True) + "\n"
    )
    assert sorted(p.name for p in out_dir.iterdir()) == ["contract-gate.json"]


def test_emit_gate_artifacts_atomic_and_byte_identical(tmp_path, monkeypatch):
    """gate_emit.emit_gate_artifacts → footprint.json AND mutation.json (two of the
    eight sites) plus the RESULT.json it delegates to run_result for."""
    import gate_emit

    man = {"withinFootprint": True, "changed": ["tools/a.py"], "note": _U}
    monkeypatch.setattr(gate_emit._footprint, "changed_since", lambda sha: ["tools/a.py"])
    monkeypatch.setattr(gate_emit._footprint, "diff_stat", lambda sha: {})
    monkeypatch.setattr(gate_emit._footprint, "manifest", lambda changed, fp, ds: man)

    records = [{"nonVacuous": True, "id": "m1", "note": _U}]
    out_dir = tmp_path / "gate"
    summary = gate_emit.emit_gate_artifacts(
        gate_name="pytest",
        command="pytest -q",
        footprint=["tools/*"],
        baseline_sha="deadbeef",
        result_sha="cafef00d",
        out_dir=out_dir,
        mutation_records=records,
        runner=lambda cmd: ("2 passed, 0 failed", 0),
        utc="2026-08-04T00:00:00+00:00",
    )

    footprint_json = out_dir / "footprint.json"
    mutation_json = out_dir / "mutation.json"
    assert json.loads(footprint_json.read_text(encoding="utf-8")) == man
    assert footprint_json.read_bytes() == _legacy_bytes(tmp_path, json.dumps(man, indent=2))

    mutation_payload = {"records": records, "allNonVacuous": True}
    assert json.loads(mutation_json.read_text(encoding="utf-8")) == mutation_payload
    assert mutation_json.read_bytes() == _legacy_bytes(
        tmp_path, json.dumps(mutation_payload, indent=2)
    )

    assert summary["withinFootprint"] is True
    # No orphan *.kata-tmp litter beside any of the three artifacts.
    assert sorted(p.name for p in out_dir.iterdir()) == [
        "RESULT.json",
        "footprint.json",
        "mutation.json",
    ]


def test_write_grounding_atomic_and_byte_identical(tmp_path):
    """grounding_gate.write_grounding → grounding.json (the fold-authorization signal)."""
    import grounding_gate

    verdicts = [
        {"verdict": "GROUND", "claim": _U, "source": "docs/DESIGN.md"},
        {"verdict": "UNGROUND", "claim": "x", "source": None},
    ]
    out_dir = tmp_path / "kata"
    out_dir.mkdir()
    written = Path(grounding_gate.write_grounding(str(out_dir), verdicts))

    payload = {"verdicts": verdicts, "allGrounded": False}
    assert json.loads(written.read_text(encoding="utf-8")) == payload
    assert written.read_bytes() == _legacy_bytes(tmp_path, json.dumps(payload, indent=2))
    assert sorted(p.name for p in out_dir.iterdir()) == ["grounding.json"]


def test_emit_deferrals_atomic_and_byte_identical(tmp_path):
    """drift_gate.emit_deferrals → the LD12 closeout confidence input."""
    import drift_gate

    records = [{"id": "d1", "reason": _U, "owner": "conductor"}]
    dest = tmp_path / "deviations" / "deferred.json"
    drift_gate.emit_deferrals(records, dest)

    assert json.loads(dest.read_text(encoding="utf-8")) == records
    assert dest.read_bytes() == _legacy_bytes(tmp_path, json.dumps(records, indent=2))
    assert sorted(p.name for p in dest.parent.iterdir()) == ["deferred.json"]


def test_emit_drift_report_atomic_and_byte_identical(tmp_path):
    """drift_gate.emit_drift_report → the LD12 P3 regression proof."""
    import drift_gate

    report = {
        "finding_id": "f1",
        "behavioral": {"passed": True},
        "snapshot": {"a": 1},
        "verdict": "PASS",
        "utc": "2026-08-04T00:00:00+00:00",
        "note": _U,
    }
    dest = tmp_path / "drift" / "f1.json"
    drift_gate.emit_drift_report(report, dest)

    assert json.loads(dest.read_text(encoding="utf-8")) == report
    assert dest.read_bytes() == _legacy_bytes(tmp_path, json.dumps(report, indent=2))
    assert sorted(p.name for p in dest.parent.iterdir()) == ["f1.json"]


def test_emit_findings_atomic_and_byte_identical(tmp_path):
    """deviation.emit_findings → findings.json, rewritten as the funnel routes."""
    import deviation

    findings = [{"id": "dev1", "route": "fix", "detail": _U}]
    dest = tmp_path / "deviations" / "findings.json"
    deviation.emit_findings(findings, dest)

    assert json.loads(dest.read_text(encoding="utf-8")) == findings
    assert dest.read_bytes() == _legacy_bytes(tmp_path, json.dumps(findings, indent=2))
    assert sorted(p.name for p in dest.parent.iterdir()) == ["findings.json"]


@pytest.mark.parametrize(
    ("modname", "funcname"),
    [(m, f) for m, f, _ in _GATE_CRITICAL_SITES],
)
def test_gate_critical_writer_leaves_prior_artifact_intact_on_failure(
    modname, funcname, tmp_path, monkeypatch
):
    """The atomicity payoff, exercised end-to-end through each writer: when the
    rename fails mid-write the PREVIOUS artifact is still whole and no orphan tmp
    is left behind.  Under the old truncate-then-write the file would be gone."""
    mod = importlib.import_module(modname)

    def boom(src, dst):
        raise OSError("simulated replace failure")

    # The FIRST artifact each writer touches — pre-seeded so the assertion below is
    # about that writer's own destination, not an unrelated bystander file.
    targets = {
        "write_result": "RESULT.json",
        "write_contract_gate": "contract-gate.json",
        "emit_gate_artifacts": "RESULT.json",
        "write_grounding": "grounding.json",
        "emit_deferrals": "deferred.json",
        "emit_drift_report": "f1.json",
        "emit_findings": "findings.json",
    }
    dest = tmp_path / targets[funcname]
    dest.write_text("PRIOR-ARTIFACT", encoding="utf-8")

    calls = {
        "write_result": lambda: mod.write_result({"a": 1}, dest),
        "write_contract_gate": lambda: mod.write_contract_gate(
            tmp_path, {"passed": True, "findings": []}
        ),
        "emit_gate_artifacts": lambda: mod.emit_gate_artifacts(
            gate_name="g",
            command="c",
            footprint=[],
            baseline_sha="a",
            result_sha="b",
            out_dir=tmp_path,
            runner=lambda cmd: ("", 0),
            utc="2026-08-04T00:00:00+00:00",
        ),
        "write_grounding": lambda: mod.write_grounding(str(tmp_path), []),
        "emit_deferrals": lambda: mod.emit_deferrals([{"id": "d"}], dest),
        "emit_drift_report": lambda: mod.emit_drift_report({"finding_id": "f"}, dest),
        "emit_findings": lambda: mod.emit_findings([{"id": "x"}], dest),
    }
    monkeypatch.setattr(fs_atomic.os, "replace", boom)
    with pytest.raises(OSError, match="simulated replace failure"):
        calls[funcname]()

    assert dest.read_text(encoding="utf-8") == "PRIOR-ARTIFACT"
    assert not [p for p in tmp_path.iterdir() if p.name.endswith(".kata-tmp")], (
        "orphan tmp must be cleaned up on failure"
    )
