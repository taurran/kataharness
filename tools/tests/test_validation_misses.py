"""Tests for validation_misses.py — TDD first (red → green).

Coverage:
- schema round-trips; a valid entry passes validate_miss (empty errors)
- validate_miss returns errors for: missing required field, bad severity,
  bad what_caught_it, extra key, wrong type on nullable field
- append_miss is append-only (two appends → two lines, first line preserved) + creates file
- append_miss raises ValueError on '..' path and on a malformed entry
- append_miss returns False (does NOT raise) on an I/O failure (e.g. directory path)
- read_misses tolerates a malformed line (returns valid ones) and returns [] for absent path
- count_by_class aggregates by string key (not tuple)
- recurrences surfaces a class with 3 entries at threshold=3, NOT at threshold=4
- Mutation proof via mutation_run.prove_non_vacuous on:
    (a) the >= threshold comparison in recurrences
    (b) the '..' guard in _guard_path
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helper: canonical valid entry
# ---------------------------------------------------------------------------

def _valid_entry(**overrides) -> dict:
    """Return a valid miss entry dict; keyword args override individual fields."""
    base = {
        "ts": "2026-06-27T12:00:00Z",
        "mode": "debug",
        "failure_class": "rce-unchecked",
        "responsible_skill": "kata-evaluate",
        "severity": "BLOCKER",
        "what_conformance_missed": "eval passed an unchecked exec call",
        "what_caught_it": "d98",
        "guard_ref": None,
        "decision_ref": "D109",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def test_schema_round_trips():
    """miss_schema returns a dict containing all 10 schema fields (incl. run_id).

    T2 §Enum-BC: adding the nullable ``run_id`` makes this a 10-field schema. The
    published schema must not lie about its field set, so this expected set is
    bumped 9→10 — the single intentional existing-test edit (an additive schema
    extension, not a regression).
    """
    import validation_misses as vm

    schema = vm.miss_schema()
    expected_fields = {
        "ts", "mode", "failure_class", "responsible_skill", "severity",
        "what_conformance_missed", "what_caught_it", "guard_ref", "decision_ref",
        "run_id",
    }
    assert set(schema.keys()) == expected_fields, (
        f"Schema fields mismatch. Got: {set(schema.keys())}"
    )


# ---------------------------------------------------------------------------
# validate_miss — valid entry
# ---------------------------------------------------------------------------

def test_valid_entry_passes_validate_miss():
    """A fully valid entry returns an empty error list."""
    import validation_misses as vm

    errors = vm.validate_miss(_valid_entry())
    assert errors == [], f"Expected no errors, got: {errors}"


def test_valid_entry_with_guard_ref_string():
    """guard_ref as a string is valid."""
    import validation_misses as vm

    errors = vm.validate_miss(_valid_entry(guard_ref="protocol/exec-safety.md"))
    assert errors == [], f"Expected no errors with str guard_ref, got: {errors}"


def test_valid_entry_with_null_decision_ref():
    """decision_ref=None is valid."""
    import validation_misses as vm

    errors = vm.validate_miss(_valid_entry(decision_ref=None))
    assert errors == [], f"Expected no errors with None decision_ref, got: {errors}"


def test_all_severity_values_valid():
    """All three severity enum values are accepted."""
    import validation_misses as vm

    for sev in ("BLOCKER", "MAJOR", "MINOR"):
        errors = vm.validate_miss(_valid_entry(severity=sev))
        assert errors == [], f"severity={sev!r} unexpectedly invalid: {errors}"


def test_all_caught_by_values_valid():
    """All three what_caught_it enum values are accepted."""
    import validation_misses as vm

    for caught in ("d98", "re-confirm", "human"):
        errors = vm.validate_miss(_valid_entry(what_caught_it=caught))
        assert errors == [], f"what_caught_it={caught!r} unexpectedly invalid: {errors}"


# ---------------------------------------------------------------------------
# validate_miss — error paths
# ---------------------------------------------------------------------------

def test_validate_missing_required_field():
    """A missing required field produces an error mentioning that field."""
    import validation_misses as vm

    entry = _valid_entry()
    del entry["severity"]
    errors = vm.validate_miss(entry)
    assert errors, "Expected errors for missing field"
    assert any("severity" in e for e in errors), (
        f"Expected 'severity' in errors, got: {errors}"
    )


def test_validate_bad_severity():
    """An invalid severity value produces an enum error."""
    import validation_misses as vm

    errors = vm.validate_miss(_valid_entry(severity="CRITICAL"))
    assert errors, "Expected errors for bad severity"
    assert any("severity" in e for e in errors), (
        f"Expected severity error, got: {errors}"
    )


def test_validate_bad_what_caught_it():
    """An invalid what_caught_it value produces an enum error."""
    import validation_misses as vm

    errors = vm.validate_miss(_valid_entry(what_caught_it="gpt4"))
    assert errors, "Expected errors for bad what_caught_it"
    assert any("what_caught_it" in e for e in errors), (
        f"Expected what_caught_it error, got: {errors}"
    )


def test_validate_extra_key_rejected():
    """Extra keys are rejected (additionalProperties: false)."""
    import validation_misses as vm

    entry = _valid_entry()
    entry["extra_field"] = "not allowed"
    errors = vm.validate_miss(entry)
    assert errors, "Expected errors for extra key"
    assert any("extra" in e for e in errors), (
        f"Expected extra-key error, got: {errors}"
    )


def test_validate_guard_ref_wrong_type():
    """guard_ref must be str or None; an int is rejected."""
    import validation_misses as vm

    errors = vm.validate_miss(_valid_entry(guard_ref=42))
    assert errors, "Expected errors for wrong guard_ref type"
    assert any("guard_ref" in e for e in errors), (
        f"Expected guard_ref error, got: {errors}"
    )


def test_validate_decision_ref_wrong_type():
    """decision_ref must be str or None; a dict is rejected."""
    import validation_misses as vm

    errors = vm.validate_miss(_valid_entry(decision_ref={"nested": "dict"}))
    assert errors, "Expected errors for wrong decision_ref type"
    assert any("decision_ref" in e for e in errors), (
        f"Expected decision_ref error, got: {errors}"
    )


def test_validate_required_field_wrong_type():
    """A required str field that is an int produces a type error."""
    import validation_misses as vm

    errors = vm.validate_miss(_valid_entry(ts=12345))
    assert errors, "Expected errors for wrong ts type"
    assert any("ts" in e for e in errors), (
        f"Expected ts type error, got: {errors}"
    )


# ---------------------------------------------------------------------------
# append_miss — happy path: creates file and is append-only
# ---------------------------------------------------------------------------

def test_append_miss_creates_file(tmp_path):
    """append_miss creates the file (and parent dirs) and returns True."""
    import validation_misses as vm

    target = tmp_path / "sub" / "misses.jsonl"
    assert not target.exists()
    result = vm.append_miss(_valid_entry(), target)
    assert result is True
    assert target.exists()


def test_append_miss_is_append_only(tmp_path):
    """Two appends produce exactly two lines; the first line is preserved intact."""
    import validation_misses as vm

    target = tmp_path / "misses.jsonl"
    entry1 = _valid_entry(ts="2026-01-01T00:00:00Z", failure_class="rce-first")
    entry2 = _valid_entry(ts="2026-01-02T00:00:00Z", failure_class="rce-second")

    vm.append_miss(entry1, target)
    vm.append_miss(entry2, target)

    lines = target.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2, f"Expected 2 lines after two appends, got {len(lines)}"
    first = json.loads(lines[0])
    assert first["failure_class"] == "rce-first", (
        f"First line was overwritten or lost. Got: {first}"
    )
    second = json.loads(lines[1])
    assert second["failure_class"] == "rce-second"


def test_append_miss_returns_true(tmp_path):
    """append_miss returns True on a successful write."""
    import validation_misses as vm

    result = vm.append_miss(_valid_entry(), tmp_path / "ok.jsonl")
    assert result is True


# ---------------------------------------------------------------------------
# append_miss — error contract (ValueError raises + I/O False)
# ---------------------------------------------------------------------------

def test_append_miss_raises_on_dotdot_path(tmp_path):
    """append_miss raises ValueError for a '..' path segment (CWE-23)."""
    import validation_misses as vm

    traversal = tmp_path / ".." / "evil.jsonl"
    with pytest.raises(ValueError, match=r"\.\."):
        vm.append_miss(_valid_entry(), traversal)


def test_append_miss_raises_on_malformed_entry(tmp_path):
    """append_miss raises ValueError when the entry fails validation."""
    import validation_misses as vm

    bad_entry = _valid_entry(severity="NOT_VALID")
    with pytest.raises(ValueError):
        vm.append_miss(bad_entry, tmp_path / "misses.jsonl")


def test_append_miss_raises_on_extra_key(tmp_path):
    """append_miss raises ValueError for an entry with an extra key."""
    import validation_misses as vm

    entry = _valid_entry()
    entry["sneaky"] = "extra"
    with pytest.raises(ValueError):
        vm.append_miss(entry, tmp_path / "misses.jsonl")


def test_append_miss_returns_false_on_io_failure(tmp_path):
    """append_miss returns False (does NOT raise) when the write target is a directory."""
    import validation_misses as vm

    # Point at an existing directory — opening a dir as a file raises PermissionError
    # (an OSError subclass) on Windows and IsADirectoryError on POSIX.
    dir_path = tmp_path / "a_directory"
    dir_path.mkdir()
    result = vm.append_miss(_valid_entry(), dir_path)
    assert result is False, (
        f"Expected False on I/O failure (directory path), got {result!r}"
    )


def test_append_miss_does_not_raise_on_io_failure(tmp_path):
    """append_miss must not propagate OSError — logging is a pure side-effect."""
    import validation_misses as vm

    dir_path = tmp_path / "another_dir"
    dir_path.mkdir()
    # Must not raise anything
    try:
        vm.append_miss(_valid_entry(), dir_path)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(
            f"append_miss raised {type(exc).__name__} on I/O failure; "
            f"it must return False instead. Error: {exc}"
        )


def test_append_miss_nul_byte_path_returns_false_not_raise():
    """D98-B1: a pathological path (embedded NUL) is a non-fatal write failure,
    not a raise — the BC guarantee must be self-contained in code, not reliant
    on a caller's try/except. (`..` and malformed-entry still raise; this does not.)"""
    import validation_misses as vm

    result = vm.append_miss(_valid_entry(), "bad\x00path.jsonl")
    assert result is False  # returned, did not raise


# ---------------------------------------------------------------------------
# read_misses
# ---------------------------------------------------------------------------

def test_read_misses_absent_file(tmp_path):
    """read_misses returns [] for a non-existent file."""
    import validation_misses as vm

    result = vm.read_misses(tmp_path / "nonexistent.jsonl")
    assert result == []


def test_read_misses_tolerates_malformed_line(tmp_path):
    """A malformed JSON line is silently skipped; valid entries are returned."""
    import validation_misses as vm

    target = tmp_path / "misses.jsonl"
    valid = _valid_entry(ts="2026-01-01T00:00:00Z")
    target.write_text(
        "not valid json {{{\n" + json.dumps(valid) + "\n",
        encoding="utf-8",
    )
    results = vm.read_misses(target)
    assert len(results) == 1, f"Expected 1 valid entry, got {len(results)}"
    assert results[0]["ts"] == "2026-01-01T00:00:00Z"


def test_read_misses_round_trips_appended(tmp_path):
    """Entries written by append_miss are faithfully read back by read_misses."""
    import validation_misses as vm

    target = tmp_path / "misses.jsonl"
    entry = _valid_entry()
    vm.append_miss(entry, target)
    read_back = vm.read_misses(target)
    assert len(read_back) == 1
    assert read_back[0] == entry


def test_read_misses_multiple_entries(tmp_path):
    """read_misses returns all valid entries in order."""
    import validation_misses as vm

    target = tmp_path / "misses.jsonl"
    entries = [
        _valid_entry(ts=f"2026-01-0{i}T00:00:00Z", failure_class=f"class-{i}")
        for i in range(1, 4)
    ]
    for e in entries:
        vm.append_miss(e, target)
    result = vm.read_misses(target)
    assert len(result) == 3
    for i, e in enumerate(entries):
        assert result[i] == e


def test_read_misses_skips_all_malformed(tmp_path):
    """A file of all-malformed lines returns []."""
    import validation_misses as vm

    target = tmp_path / "bad.jsonl"
    target.write_text("bad\nnot json\n[1,2,3]\n", encoding="utf-8")
    result = vm.read_misses(target)
    assert result == []


# ---------------------------------------------------------------------------
# count_by_class
# ---------------------------------------------------------------------------

def test_count_by_class_aggregates_correctly():
    """count_by_class produces correct string-keyed counts."""
    import validation_misses as vm

    misses = [
        _valid_entry(responsible_skill="kata-evaluate", failure_class="rce"),
        _valid_entry(responsible_skill="kata-evaluate", failure_class="rce"),
        _valid_entry(responsible_skill="kata-evaluate", failure_class="dos"),
        _valid_entry(responsible_skill="kata-review", failure_class="rce"),
    ]
    counts = vm.count_by_class(misses)
    assert counts["kata-evaluate::rce"] == 2
    assert counts["kata-evaluate::dos"] == 1
    assert counts["kata-review::rce"] == 1


def test_count_by_class_keys_are_strings():
    """All keys in count_by_class output are strings (JSON-serializable, not tuples)."""
    import validation_misses as vm

    misses = [_valid_entry(responsible_skill="s", failure_class="c")]
    counts = vm.count_by_class(misses)
    for k in counts:
        assert isinstance(k, str), f"Key {k!r} is not a string"


def test_count_by_class_empty():
    """count_by_class on an empty list returns an empty dict."""
    import validation_misses as vm

    assert vm.count_by_class([]) == {}


def test_count_by_class_skips_missing_fields():
    """Entries missing responsible_skill or failure_class are skipped."""
    import validation_misses as vm

    misses = [
        {"responsible_skill": "s"},           # missing failure_class
        {"failure_class": "c"},               # missing responsible_skill
        _valid_entry(responsible_skill="s", failure_class="c"),
    ]
    counts = vm.count_by_class(misses)
    assert counts == {"s::c": 1}


def test_count_by_class_tolerates_non_dict_element():
    """D98-B3: a non-dict element in the list must be skipped, not crash."""
    import validation_misses as vm

    misses = [
        "not-a-dict",
        None,
        _valid_entry(responsible_skill="s", failure_class="c"),
    ]
    counts = vm.count_by_class(misses)  # must not raise
    assert counts == {"s::c": 1}


# ---------------------------------------------------------------------------
# recurrences
# ---------------------------------------------------------------------------

def test_recurrences_surfaces_at_threshold():
    """A class with 3 entries is surfaced at threshold=3 (>= semantics)."""
    import validation_misses as vm

    misses = [
        _valid_entry(responsible_skill="kata-evaluate", failure_class="rce"),
        _valid_entry(responsible_skill="kata-evaluate", failure_class="rce"),
        _valid_entry(responsible_skill="kata-evaluate", failure_class="rce"),
    ]
    result = vm.recurrences(misses, threshold=3)
    assert len(result) == 1, f"Expected 1 recurrence, got {len(result)}: {result}"
    r = result[0]
    assert r["key"] == "kata-evaluate::rce"
    assert r["responsible_skill"] == "kata-evaluate"
    assert r["failure_class"] == "rce"
    assert r["count"] == 3


def test_recurrences_not_surfaced_below_threshold():
    """A class with 3 entries is NOT surfaced at threshold=4 (count 3 < 4)."""
    import validation_misses as vm

    misses = [
        _valid_entry(responsible_skill="kata-evaluate", failure_class="rce"),
        _valid_entry(responsible_skill="kata-evaluate", failure_class="rce"),
        _valid_entry(responsible_skill="kata-evaluate", failure_class="rce"),
    ]
    result = vm.recurrences(misses, threshold=4)
    assert result == [], (
        f"Expected empty list at threshold=4 (count 3 < 4), got: {result}"
    )


def test_recurrences_surfaces_exactly_at_threshold():
    """count == threshold is surfaced (>= is inclusive on the lower bound)."""
    import validation_misses as vm

    misses = [
        _valid_entry(responsible_skill="s", failure_class="c"),
        _valid_entry(responsible_skill="s", failure_class="c"),
    ]
    result = vm.recurrences(misses, threshold=2)
    assert len(result) == 1
    assert result[0]["count"] == 2


def test_recurrences_empty_misses():
    """recurrences with no misses returns []."""
    import validation_misses as vm

    assert vm.recurrences([], threshold=3) == []


def test_recurrences_result_shape():
    """Each result dict has the four required keys."""
    import validation_misses as vm

    misses = [_valid_entry(responsible_skill="s", failure_class="c")] * 3
    result = vm.recurrences(misses, threshold=3)
    assert len(result) == 1
    r = result[0]
    assert set(r.keys()) == {"key", "responsible_skill", "failure_class", "count"}


def test_recurrences_multiple_classes(tmp_path):
    """Only classes at/over threshold are returned; below-threshold classes excluded."""
    import validation_misses as vm

    misses = (
        [_valid_entry(responsible_skill="s1", failure_class="c1")] * 3  # count=3
        + [_valid_entry(responsible_skill="s2", failure_class="c2")] * 2  # count=2
    )
    result = vm.recurrences(misses, threshold=3)
    keys = {r["key"] for r in result}
    assert "s1::c1" in keys
    assert "s2::c2" not in keys


# ---------------------------------------------------------------------------
# T2 — curated failure_class SOFT enum (BC: validate_miss unchanged)
# ---------------------------------------------------------------------------

_LOCKED_FAILURE_CLASSES = {
    "honesty-fail-open", "over-claim-fail-open", "exec-injection",
    "phantom-reuse", "dos-vector", "stateful-hole", "fail-open", "over-claim",
}


def test_failure_class_values_contains_locked_members():
    """_FAILURE_CLASS_VALUES is a frozenset containing the 8 LOCKED members."""
    import validation_misses as vm

    assert isinstance(vm._FAILURE_CLASS_VALUES, frozenset)
    assert _LOCKED_FAILURE_CLASSES <= vm._FAILURE_CLASS_VALUES, (
        f"Missing LOCKED members: {_LOCKED_FAILURE_CLASSES - vm._FAILURE_CLASS_VALUES}"
    )


def test_failure_class_enum_published_in_schema():
    """miss_schema()['failure_class']['enum'] lists the curated vocabulary (sorted)."""
    import validation_misses as vm

    enum = vm.miss_schema()["failure_class"]["enum"]
    assert set(enum) == set(vm._FAILURE_CLASS_VALUES)
    assert enum == sorted(vm._FAILURE_CLASS_VALUES), "enum should be published sorted"


def test_is_known_class_membership():
    """is_known_class is True for a curated member, False for an off-vocab slug."""
    import validation_misses as vm

    assert vm.is_known_class("honesty-fail-open") is True
    assert vm.is_known_class("over-claim-fail-open") is True
    assert vm.is_known_class("rce-unchecked") is False
    assert vm.is_known_class("totally-made-up") is False


def test_soft_enum_off_vocab_failure_class_still_validates():
    """BC: an off-enum failure_class (default 'rce-unchecked') still validates.

    The enum is SOFT — validate_miss is UNCHANGED for failure_class (any non-None
    str). A non-fatal append must never drop a real miss over a vocab typo.
    """
    import validation_misses as vm

    assert vm.validate_miss(_valid_entry()) == []  # failure_class='rce-unchecked'
    assert vm.validate_miss(_valid_entry(failure_class="some-new-slug")) == []


# ---------------------------------------------------------------------------
# T2 — nullable run_id field (BC: existing run_id-less misses stay valid)
# ---------------------------------------------------------------------------

def test_run_id_in_nullable_fields_and_schema():
    """run_id joins _NULLABLE_STR_FIELDS and the published 10-field schema."""
    import validation_misses as vm

    assert "run_id" in vm._NULLABLE_STR_FIELDS
    assert "run_id" in vm._ALL_FIELDS
    assert "run_id" in vm.miss_schema()
    assert vm.miss_schema()["run_id"]["type"] == "str|null"


def test_miss_without_run_id_validates():
    """A miss with NO run_id key validates (missing-key allowed, like guard_ref)."""
    import validation_misses as vm

    entry = _valid_entry()
    assert "run_id" not in entry
    assert vm.validate_miss(entry) == []


def test_run_id_none_validates():
    """run_id=None validates (nullable)."""
    import validation_misses as vm

    assert vm.validate_miss(_valid_entry(run_id=None)) == []


def test_run_id_string_validates():
    """run_id as a string validates."""
    import validation_misses as vm

    assert vm.validate_miss(_valid_entry(run_id="run-2026-06-27-abc")) == []


def test_run_id_non_str_rejected():
    """run_id as a non-str (int) is rejected (mirrors guard_ref)."""
    import validation_misses as vm

    errors = vm.validate_miss(_valid_entry(run_id=42))
    assert errors, "Expected errors for non-str run_id"
    assert any("run_id" in e for e in errors), f"Expected run_id error, got: {errors}"


# ---------------------------------------------------------------------------
# T2 — data BC: the two REAL logged misses stay valid + are known classes
# ---------------------------------------------------------------------------

def test_logged_misses_stay_valid_and_known(tmp_path):
    """The two real .planning/validation-misses.jsonl entries (no run_id,
    enum-member failure_class) still validate and ARE is_known_class True."""
    import validation_misses as vm

    manifest = (
        Path(__file__).resolve().parents[2] / ".planning" / "validation-misses.jsonl"
    )
    entries = vm.read_misses(manifest)
    assert len(entries) >= 2, f"Expected >=2 logged misses, got {len(entries)}"
    for e in entries:
        assert "run_id" not in e, "the two logged misses are run_id-less (legacy)"
        assert vm.validate_miss(e) == [], f"logged miss must still validate: {e}"
        assert vm.is_known_class(e["failure_class"]) is True, (
            f"logged failure_class must be a curated member: {e['failure_class']}"
        )


# ---------------------------------------------------------------------------
# Mutation proof — non-vacuity proofs for load-bearing lines
# ---------------------------------------------------------------------------

def test_mutation_proof_threshold_comparison():
    """Mutation proof (a): removing >= threshold breaks a recurrences test.

    Asserted line (exact, 8-space indent):
        '        if count >= threshold:'
    If this line is removed, Python raises IndentationError (orphaned body)
    → module import fails → recurrences tests go red → nonVacuous=True.
    """
    import mutation_run

    source = str((Path(__file__).parent.parent / "validation_misses.py").resolve())
    asserted_line = "        if count >= threshold:"
    tools_dir = str(Path(__file__).parent.parent.resolve())
    test_cmd = (
        f'cd /d "{tools_dir}" && uv run pytest '
        f"tests/test_validation_misses.py::test_recurrences_surfaces_at_threshold "
        f"tests/test_validation_misses.py::test_recurrences_not_surfaced_below_threshold -q"
    )

    verdict = mutation_run.prove_non_vacuous(source, asserted_line, test_cmd)
    assert verdict["nonVacuous"] is True, (
        f"Mutation proof FAILED for threshold comparison (line: {asserted_line!r}): {verdict}"
    )


def test_mutation_proof_dotdot_guard():
    """Mutation proof (b): removing the '..' guard breaks the dotdot path test.

    Asserted line (exact, 4-space indent):
        '    if any(part == ".." for part in p.parts):'
    If this line is removed, Python raises IndentationError (orphaned raise)
    → module import fails → dotdot test goes red → nonVacuous=True.
    """
    import mutation_run

    source = str((Path(__file__).parent.parent / "validation_misses.py").resolve())
    asserted_line = '    if any(part == ".." for part in p.parts):'
    tools_dir = str(Path(__file__).parent.parent.resolve())
    test_cmd = (
        f'cd /d "{tools_dir}" && uv run pytest '
        f"tests/test_validation_misses.py::test_append_miss_raises_on_dotdot_path -q"
    )

    verdict = mutation_run.prove_non_vacuous(source, asserted_line, test_cmd)
    assert verdict["nonVacuous"] is True, (
        f"Mutation proof FAILED for '..' guard (line: {asserted_line!r}): {verdict}"
    )
