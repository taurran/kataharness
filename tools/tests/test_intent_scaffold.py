"""Tests for intent_scaffold.py — deterministic INTENT.md builder.

TDD discipline: written FIRST before intent_scaffold.py existed.
All tests are PURE — no real filesystem operations except via tmp_path.

Coverage:
- build_intent returns text with YAML frontmatter containing every required
  protocol/intent.md key and the chosen values (including nested target sub-keys)
- missing 'kind' raises ValueError
- invalid 'kind' value raises ValueError
- missing 'target.kind' raises ValueError
- invalid 'target.kind' value raises ValueError
- invalid 'grillDepth' raises ValueError
- write_intent writes a file whose frontmatter round-trips as valid YAML
- the '..' traversal guard in write_intent rejects escape paths
- the additive `status: draft|frozen` freeze field (R2-H1/R3-L2): explicit
  keyword-only `freeze=True` is the ONLY writer of `frozen`
- the fail-closed `intent_status` reader (first-word parse, BL-F01), including
  the statusless-legacy-INTENT backward-compatibility path
"""

from __future__ import annotations

import pytest
import yaml

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

FULL_ANSWERS = {
    "kind": "version-up",
    "goal": "Close the interactive-initiation gap so the harness always prompts the human.",
    "fixes": ["G4: initiation never prompted"],
    "features": ["deterministic INTENT.md writer", "hard interview gate in kata-initiate"],
    "modulesAdded": [],
    "changeSummary": "Add intent_scaffold + tighten kata-initiate interview to structural stop.",
    "target": {
        "kind": "self",
        "path": "",
        "vault": "linked",
        "platform": "claude",
    },
    "grillDepth": "standard",
    "readiness": "All load-bearing branches resolved; executor may proceed.",
}


# ---------------------------------------------------------------------------
# Import guard — module must exist first (TDD: will fail initially)
# ---------------------------------------------------------------------------

def test_import():
    """Importing the module should not raise."""
    import intent_scaffold  # noqa: F401


# ---------------------------------------------------------------------------
# build_intent — frontmatter content
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> dict:
    """Extract and parse the YAML frontmatter block from INTENT.md text."""
    lines = text.splitlines()
    # frontmatter delimiters are lines that are exactly '---'
    if not lines or lines[0].strip() != "---":
        raise ValueError("No opening frontmatter delimiter found")
    closing = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing = i
            break
    if closing is None:
        raise ValueError("No closing frontmatter delimiter found")
    fm_text = "\n".join(lines[1:closing])
    return yaml.safe_load(fm_text)


def test_build_intent_returns_string():
    from intent_scaffold import build_intent
    result = build_intent(FULL_ANSWERS)
    assert isinstance(result, str)


def test_build_intent_has_frontmatter_delimiters():
    from intent_scaffold import build_intent
    text = build_intent(FULL_ANSWERS)
    lines = text.splitlines()
    assert lines[0].strip() == "---", "First line must be '---'"
    assert any(l.strip() == "---" for l in lines[1:]), "Closing '---' must be present"


def test_build_intent_frontmatter_top_level_keys():
    """Every required top-level key from protocol/intent.md must be present."""
    from intent_scaffold import build_intent
    fm = _parse_frontmatter(build_intent(FULL_ANSWERS))
    required = {"kind", "goal", "fixes", "features", "modulesAdded",
                "changeSummary", "target", "grillDepth", "readiness"}
    missing = required - fm.keys()
    assert not missing, f"Frontmatter missing required keys: {missing}"


def test_build_intent_kind_value():
    from intent_scaffold import build_intent
    fm = _parse_frontmatter(build_intent(FULL_ANSWERS))
    assert fm["kind"] == "version-up"


def test_build_intent_grillDepth_value():
    from intent_scaffold import build_intent
    fm = _parse_frontmatter(build_intent(FULL_ANSWERS))
    assert fm["grillDepth"] == "standard"


def test_build_intent_target_sub_schema():
    """target must contain kind, path, vault, platform with correct values."""
    from intent_scaffold import build_intent
    fm = _parse_frontmatter(build_intent(FULL_ANSWERS))
    target = fm["target"]
    assert target["kind"] == "self"
    assert target["vault"] == "linked"
    assert target["platform"] == "claude"


def test_build_intent_fixes_as_list():
    from intent_scaffold import build_intent
    fm = _parse_frontmatter(build_intent(FULL_ANSWERS))
    assert isinstance(fm["fixes"], list)
    assert fm["fixes"] == FULL_ANSWERS["fixes"]


def test_build_intent_features_as_list():
    from intent_scaffold import build_intent
    fm = _parse_frontmatter(build_intent(FULL_ANSWERS))
    assert isinstance(fm["features"], list)
    assert fm["features"] == FULL_ANSWERS["features"]


def test_build_intent_modulesAdded_as_list():
    from intent_scaffold import build_intent
    fm = _parse_frontmatter(build_intent(FULL_ANSWERS))
    assert isinstance(fm["modulesAdded"], list)


def test_build_intent_has_body_after_frontmatter():
    """There should be non-empty body text after the closing '---'."""
    from intent_scaffold import build_intent
    text = build_intent(FULL_ANSWERS)
    lines = text.splitlines()
    # Find the closing '---'
    closing = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing = i
            break
    body = "\n".join(lines[closing + 1:]).strip()
    assert body, "Body (north-star narrative) must be non-empty"


def test_build_intent_all_kind_values():
    """All three valid kind values must be accepted."""
    from intent_scaffold import build_intent
    for kind in ("project", "research", "version-up"):
        answers = {**FULL_ANSWERS, "kind": kind}
        fm = _parse_frontmatter(build_intent(answers))
        assert fm["kind"] == kind


def test_build_intent_all_grillDepth_values():
    """All four valid grillDepth values must be accepted."""
    from intent_scaffold import build_intent
    for depth in ("skip", "light", "standard", "full"):
        answers = {**FULL_ANSWERS, "grillDepth": depth}
        fm = _parse_frontmatter(build_intent(answers))
        assert fm["grillDepth"] == depth


def test_build_intent_all_target_kind_values():
    """All three valid target.kind values must be accepted."""
    from intent_scaffold import build_intent
    for tk in ("self", "existing", "greenfield"):
        answers = {**FULL_ANSWERS, "target": {**FULL_ANSWERS["target"], "kind": tk}}
        fm = _parse_frontmatter(build_intent(answers))
        assert fm["target"]["kind"] == tk


# ---------------------------------------------------------------------------
# build_intent — validation / fail-closed
# ---------------------------------------------------------------------------

def test_build_intent_missing_kind_raises():
    from intent_scaffold import build_intent
    answers = {k: v for k, v in FULL_ANSWERS.items() if k != "kind"}
    with pytest.raises(ValueError, match="kind"):
        build_intent(answers)


def test_build_intent_invalid_kind_raises():
    from intent_scaffold import build_intent
    answers = {**FULL_ANSWERS, "kind": "unknown-kind"}
    with pytest.raises(ValueError, match="kind"):
        build_intent(answers)


def test_build_intent_missing_target_key_raises():
    from intent_scaffold import build_intent
    answers = {k: v for k, v in FULL_ANSWERS.items() if k != "target"}
    with pytest.raises((ValueError, KeyError)):
        build_intent(answers)


def test_build_intent_invalid_target_kind_raises():
    from intent_scaffold import build_intent
    answers = {**FULL_ANSWERS, "target": {**FULL_ANSWERS["target"], "kind": "bogus"}}
    with pytest.raises(ValueError, match="target"):
        build_intent(answers)


def test_build_intent_missing_grillDepth_raises():
    from intent_scaffold import build_intent
    answers = {k: v for k, v in FULL_ANSWERS.items() if k != "grillDepth"}
    with pytest.raises(ValueError, match="grillDepth"):
        build_intent(answers)


def test_build_intent_invalid_grillDepth_raises():
    from intent_scaffold import build_intent
    answers = {**FULL_ANSWERS, "grillDepth": "extreme"}
    with pytest.raises(ValueError, match="grillDepth"):
        build_intent(answers)


# ---------------------------------------------------------------------------
# write_intent — file write + round-trip
# ---------------------------------------------------------------------------

def test_write_intent_creates_file(tmp_path):
    from intent_scaffold import write_intent
    target = tmp_path / "INTENT.md"
    write_intent(str(target), FULL_ANSWERS)
    assert target.exists(), "write_intent must create the target file"


def test_write_intent_roundtrips_frontmatter(tmp_path):
    from intent_scaffold import write_intent
    target = tmp_path / "INTENT.md"
    write_intent(str(target), FULL_ANSWERS)
    text = target.read_text(encoding="utf-8")
    fm = _parse_frontmatter(text)
    # Spot-check key fields survive the round-trip
    assert fm["kind"] == FULL_ANSWERS["kind"]
    assert fm["grillDepth"] == FULL_ANSWERS["grillDepth"]
    assert fm["target"]["kind"] == FULL_ANSWERS["target"]["kind"]
    assert fm["target"]["platform"] == FULL_ANSWERS["target"]["platform"]


def test_write_intent_utf8_encoding(tmp_path):
    """File must be valid UTF-8."""
    from intent_scaffold import write_intent
    target = tmp_path / "INTENT.md"
    write_intent(str(target), FULL_ANSWERS)
    # read_bytes then decode — would raise if not valid UTF-8
    raw = target.read_bytes()
    raw.decode("utf-8")


def test_write_intent_content_matches_build_intent(tmp_path):
    """write_intent must write exactly what build_intent returns."""
    from intent_scaffold import build_intent, write_intent
    target = tmp_path / "INTENT.md"
    write_intent(str(target), FULL_ANSWERS)
    expected = build_intent(FULL_ANSWERS)
    actual = target.read_text(encoding="utf-8")
    assert actual == expected


# ---------------------------------------------------------------------------
# write_intent — '..' traversal guard (CWE-23)
# ---------------------------------------------------------------------------

def test_write_intent_rejects_parent_traversal(tmp_path):
    """A path containing '..' must be rejected with ValueError."""
    from intent_scaffold import write_intent
    # Build a traversal path using the tmp_path anchor so the absolute prefix
    # is valid but the '..' segment is the attack vector.
    traversal = str(tmp_path / ".." / "escape.md")
    with pytest.raises(ValueError, match=r"\.\."):
        write_intent(traversal, FULL_ANSWERS)


def test_write_intent_rejects_literal_dotdot_segment():
    """A raw path with '..' anywhere must be rejected."""
    from intent_scaffold import write_intent
    with pytest.raises(ValueError, match=r"\.\."):
        write_intent("some/../../etc/passwd", FULL_ANSWERS)


# ---------------------------------------------------------------------------
# Slice D — OPTIONAL acceptanceCriteria field (additive, BC)
# ---------------------------------------------------------------------------

def test_build_intent_acceptance_criteria_when_supplied():
    """When acceptanceCriteria is non-empty it appears in the frontmatter as a list."""
    from intent_scaffold import build_intent
    criteria = ["CLI exits 0 on clean install", "no orphan symlinks after uninstall"]
    answers = {**FULL_ANSWERS, "acceptanceCriteria": criteria}
    fm = _parse_frontmatter(build_intent(answers))
    assert "acceptanceCriteria" in fm, "acceptanceCriteria must appear when non-empty"
    assert isinstance(fm["acceptanceCriteria"], list)
    assert fm["acceptanceCriteria"] == criteria


def test_build_intent_no_acceptance_criteria_byte_identical():
    """BC golden: absent or empty acceptanceCriteria yields byte-identical output.

    Mutation-proof: if the 'if acceptance_criteria:' guard is removed and the
    field is always emitted, the absent-key case would include
    'acceptanceCriteria: []\\n' in YAML, failing the 'not in fm' assertion.
    """
    from intent_scaffold import build_intent

    # Absent key — the baseline (FULL_ANSWERS has no acceptanceCriteria key)
    out_absent = build_intent(FULL_ANSWERS)

    # Explicit empty list — must be treated identically to absent
    out_empty = build_intent({**FULL_ANSWERS, "acceptanceCriteria": []})

    assert out_absent == out_empty, (
        "Empty acceptanceCriteria must produce byte-identical output to absent key"
    )

    # The field must NOT appear in the frontmatter in either case
    fm = _parse_frontmatter(out_absent)
    assert "acceptanceCriteria" not in fm, (
        "acceptanceCriteria must be omitted from frontmatter when absent/empty"
    )


def test_build_intent_acceptance_criteria_not_required():
    """acceptanceCriteria is OPTIONAL — omitting it never triggers validation error."""
    from intent_scaffold import build_intent
    # FULL_ANSWERS has no acceptanceCriteria key; must build without raising
    result = build_intent(FULL_ANSWERS)
    assert isinstance(result, str)
    fm = _parse_frontmatter(result)
    # Required keys still present
    required = {"kind", "goal", "fixes", "features", "modulesAdded",
                "changeSummary", "target", "grillDepth", "readiness"}
    assert required <= fm.keys()


def test_build_intent_acceptance_criteria_conditional_guard():
    """Mutation-proof: non-empty → field present; absent/empty → field absent."""
    from intent_scaffold import build_intent

    # Non-empty: field must appear
    answers_with = {**FULL_ANSWERS, "acceptanceCriteria": ["exits 0", "no cruft"]}
    fm_with = _parse_frontmatter(build_intent(answers_with))
    assert "acceptanceCriteria" in fm_with

    # Absent: field must NOT appear; output must differ from the non-empty case
    fm_absent = _parse_frontmatter(build_intent(FULL_ANSWERS))
    assert "acceptanceCriteria" not in fm_absent

    # The two outputs must differ (the conditional inserts content)
    assert build_intent(answers_with) != build_intent(FULL_ANSWERS)


def test_write_intent_roundtrips_acceptance_criteria(tmp_path):
    """write_intent round-trips acceptanceCriteria through YAML correctly."""
    from intent_scaffold import write_intent
    criteria = ["all tests green", "validate_skills 0 errors", "Snyk medium+ 0"]
    answers = {**FULL_ANSWERS, "acceptanceCriteria": criteria}
    target = tmp_path / "INTENT.md"
    write_intent(str(target), answers)
    text = target.read_text(encoding="utf-8")
    fm = _parse_frontmatter(text)
    assert fm["acceptanceCriteria"] == criteria


# ---------------------------------------------------------------------------
# R2-H1 / R3-L2 — the additive `status: draft|frozen` freeze field
#
# The whole point of the field is that `frozen` is UNREACHABLE except by a
# caller naming `freeze=True`. These tests attack that from both sides: the
# default must be draft everywhere, and the argument must not be settable by
# accident (positionally) or by inference from the answers dict.
# ---------------------------------------------------------------------------

def test_build_intent_emits_status_field():
    """The frontmatter always carries a `status:` key (additive amendment)."""
    from intent_scaffold import build_intent
    fm = _parse_frontmatter(build_intent(FULL_ANSWERS))
    assert "status" in fm, "status must always be emitted"


def test_build_intent_default_status_is_draft():
    """Omitted freeze argument ⇒ `draft`. Never a defaulted freeze."""
    from intent_scaffold import build_intent
    fm = _parse_frontmatter(build_intent(FULL_ANSWERS))
    assert fm["status"] == "draft"


def test_build_intent_freeze_true_writes_frozen():
    from intent_scaffold import build_intent
    fm = _parse_frontmatter(build_intent(FULL_ANSWERS, freeze=True))
    assert fm["status"] == "frozen"


def test_build_intent_freeze_false_writes_draft():
    """Explicit freeze=False is the same as omitting it."""
    from intent_scaffold import build_intent
    fm = _parse_frontmatter(build_intent(FULL_ANSWERS, freeze=False))
    assert fm["status"] == "draft"
    assert build_intent(FULL_ANSWERS, freeze=False) == build_intent(FULL_ANSWERS)


def test_build_intent_freeze_is_keyword_only():
    """A positional second argument must be a TypeError, not a silent freeze.

    Mutation-proof: if the `*` marker is dropped from the signature, a caller
    passing a truthy positional would silently freeze the artifact.
    """
    from intent_scaffold import build_intent
    with pytest.raises(TypeError):
        build_intent(FULL_ANSWERS, True)  # noqa: FBT003 — that is the point


def test_build_intent_freeze_not_inferred_from_answers():
    """A `status`/`freeze`/`frozen` key in the answers dict must NOT freeze it.

    The freeze is a named argument, never inferred from the payload — a dict
    key that could flip the governor rung would be exactly the silent-permissive
    default (D136 class) the explicit argument exists to eliminate.
    """
    from intent_scaffold import build_intent
    for smuggled in ("status", "freeze", "frozen"):
        answers = {**FULL_ANSWERS, smuggled: "frozen"}
        fm = _parse_frontmatter(build_intent(answers))
        assert fm["status"] == "draft", (
            f"answers[{smuggled!r}] must not be able to freeze the artifact"
        )


def test_build_intent_status_differs_between_modes():
    """The two modes must produce different text (the field is load-bearing)."""
    from intent_scaffold import build_intent
    assert build_intent(FULL_ANSWERS, freeze=True) != build_intent(FULL_ANSWERS)


def test_write_intent_default_status_is_draft(tmp_path):
    from intent_scaffold import write_intent
    target = tmp_path / "INTENT.md"
    write_intent(str(target), FULL_ANSWERS)
    fm = _parse_frontmatter(target.read_text(encoding="utf-8"))
    assert fm["status"] == "draft"


def test_freeze_true_writes_frozen_status(tmp_path):
    """The write-path freeze, end-to-end: freeze=True ⇒ `status: frozen` on disk.

    NAME IS LOAD-BEARING — do not rename. The frozen PLAN declares this exact
    node as this task's evidence:
        test:tools/tests/test_intent_scaffold.py::test_freeze_true_writes_frozen_status
    (.planning/specs/trust-model/PLAN.md:261). The declaration was frozen before
    the build; a differently-named test does not discharge it.
    """
    from intent_scaffold import write_intent
    target = tmp_path / "INTENT.md"
    write_intent(str(target), FULL_ANSWERS, freeze=True)
    text = target.read_text(encoding="utf-8")
    # Parsed form: the field carries the frozen token.
    assert _parse_frontmatter(text)["status"] == "frozen"
    # Raw form too — the literal line a reader/grep would see in the artifact.
    assert "status: frozen" in text


def test_write_intent_freeze_is_keyword_only(tmp_path):
    from intent_scaffold import write_intent
    target = tmp_path / "INTENT.md"
    with pytest.raises(TypeError):
        write_intent(str(target), FULL_ANSWERS, True)  # noqa: FBT003


def test_write_intent_freeze_matches_build_intent(tmp_path):
    """write_intent(freeze=True) must write exactly build_intent(freeze=True)."""
    from intent_scaffold import build_intent, write_intent
    target = tmp_path / "INTENT.md"
    write_intent(str(target), FULL_ANSWERS, freeze=True)
    assert target.read_text(encoding="utf-8") == build_intent(FULL_ANSWERS, freeze=True)


# ---------------------------------------------------------------------------
# intent_status — the fail-closed reader (mirrors kata_restore.plan_status,
# kata_restore.py:347-377). Writer and reader are round-tripped against each
# other so the two halves of the schema row cannot drift apart.
# ---------------------------------------------------------------------------

def _write_raw(tmp_path, body: str, name: str = "INTENT.md"):
    """Write a raw INTENT.md and return its path (bypasses the builder)."""
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_intent_status_roundtrips_draft(tmp_path):
    from intent_scaffold import intent_status, write_intent
    target = tmp_path / "INTENT.md"
    write_intent(str(target), FULL_ANSWERS)
    assert intent_status(target) == "draft"


def test_intent_status_roundtrips_frozen(tmp_path):
    from intent_scaffold import intent_status, write_intent
    target = tmp_path / "INTENT.md"
    write_intent(str(target), FULL_ANSWERS, freeze=True)
    assert intent_status(target) == "frozen"


def test_intent_status_accepts_str_path(tmp_path):
    from intent_scaffold import intent_status, write_intent
    target = tmp_path / "INTENT.md"
    write_intent(str(target), FULL_ANSWERS, freeze=True)
    assert intent_status(str(target)) == "frozen"


def test_intent_status_absent_when_no_status_key(tmp_path):
    """BC: a legacy INTENT.md written before the amendment has no `status:`.

    It must read as "absent" — not frozen (silent-permissive), not an error
    (which would break every pre-amendment artifact).
    """
    from intent_scaffold import intent_status
    legacy = _write_raw(tmp_path, LEGACY_STATUSLESS_INTENT)
    assert intent_status(legacy) == "absent"


def test_intent_status_absent_is_not_frozen(tmp_path):
    """The load-bearing half of the BC path: absent must never equal frozen."""
    from intent_scaffold import intent_status
    legacy = _write_raw(tmp_path, LEGACY_STATUSLESS_INTENT)
    assert intent_status(legacy) != "frozen"


def test_intent_status_absent_when_empty_value(tmp_path):
    from intent_scaffold import intent_status
    p = _write_raw(tmp_path, "---\nkind: project\nstatus:\n---\n\nbody\n")
    assert intent_status(p) == "absent"


def test_intent_status_absent_when_whitespace_value(tmp_path):
    from intent_scaffold import intent_status
    p = _write_raw(tmp_path, '---\nkind: project\nstatus: "   "\n---\n\nbody\n')
    assert intent_status(p) == "absent"


def test_intent_status_first_word_parse_with_trailing_prose(tmp_path):
    """BL-F01 first-word rule: trailing prose after the token is ignored."""
    from intent_scaffold import intent_status
    p = _write_raw(
        tmp_path,
        "---\nkind: project\n"
        "status: frozen — sealed at the Phase-6 gate (operator confirmed)\n"
        "---\n\nbody\n",
    )
    assert intent_status(p) == "frozen"


def test_intent_status_first_word_parse_draft_with_prose(tmp_path):
    from intent_scaffold import intent_status
    p = _write_raw(
        tmp_path,
        "---\nkind: project\nstatus: draft — interview still open\n---\n\nbody\n",
    )
    assert intent_status(p) == "draft"


def test_intent_status_case_folded(tmp_path):
    from intent_scaffold import intent_status
    p = _write_raw(tmp_path, "---\nkind: project\nstatus: FROZEN\n---\n\nbody\n")
    assert intent_status(p) == "frozen"


def test_intent_status_unrecognized_raises(tmp_path):
    """Fail-closed: an unknown token is never coerced in either direction."""
    from intent_scaffold import intent_status
    p = _write_raw(tmp_path, "---\nkind: project\nstatus: sealed\n---\n\nbody\n")
    with pytest.raises(ValueError, match="unrecognized status"):
        intent_status(p)


def test_intent_status_typo_raises(tmp_path):
    """A near-miss typo must raise, not silently read as its neighbour."""
    from intent_scaffold import intent_status
    p = _write_raw(tmp_path, "---\nkind: project\nstatus: frozzen\n---\n\nbody\n")
    with pytest.raises(ValueError, match="unrecognized status"):
        intent_status(p)


def test_intent_status_missing_file_raises(tmp_path):
    from intent_scaffold import intent_status
    with pytest.raises(ValueError, match="cannot read INTENT"):
        intent_status(tmp_path / "nope" / "INTENT.md")


def test_intent_status_no_frontmatter_raises(tmp_path):
    from intent_scaffold import intent_status
    p = _write_raw(tmp_path, "# North-Star Intent\n\nno frontmatter here\n")
    with pytest.raises(ValueError, match="no YAML frontmatter"):
        intent_status(p)


def test_intent_status_invalid_yaml_raises(tmp_path):
    from intent_scaffold import intent_status
    p = _write_raw(tmp_path, "---\nkind: [unclosed\n---\n\nbody\n")
    with pytest.raises(ValueError, match="not valid YAML"):
        intent_status(p)


def test_intent_status_non_mapping_frontmatter_raises(tmp_path):
    from intent_scaffold import intent_status
    p = _write_raw(tmp_path, "---\n- just\n- a\n- list\n---\n\nbody\n")
    with pytest.raises(ValueError, match="not a mapping"):
        intent_status(p)


def test_intent_status_returns_only_enum_values(tmp_path):
    """Every non-raising return is one of exactly three tokens."""
    from intent_scaffold import intent_status, write_intent
    draft = tmp_path / "d.md"
    frozen = tmp_path / "f.md"
    write_intent(str(draft), FULL_ANSWERS)
    write_intent(str(frozen), FULL_ANSWERS, freeze=True)
    legacy = _write_raw(tmp_path, LEGACY_STATUSLESS_INTENT, name="legacy.md")
    got = {intent_status(draft), intent_status(frozen), intent_status(legacy)}
    assert got == {"draft", "frozen", "absent"}


# ---------------------------------------------------------------------------
# BC — statusless legacy INTENT.md files must not break any existing path
# ---------------------------------------------------------------------------

LEGACY_STATUSLESS_INTENT = """---
kind: version-up
goal: A pre-amendment INTENT.md, written before the status field existed.
fixes: []
features:
- something
modulesAdded: []
changeSummary: Legacy artifact.
target:
  kind: self
  path: ''
  vault: ''
  platform: claude
grillDepth: standard
readiness: Ready.
---

# North-Star Intent
"""


def test_legacy_statusless_intent_frontmatter_still_parses(tmp_path):
    """The legacy artifact remains a schema-valid, readable INTENT.md."""
    legacy = _write_raw(tmp_path, LEGACY_STATUSLESS_INTENT)
    fm = _parse_frontmatter(legacy.read_text(encoding="utf-8"))
    required = {"kind", "goal", "fixes", "features", "modulesAdded",
                "changeSummary", "target", "grillDepth", "readiness"}
    assert required <= fm.keys()
    assert "status" not in fm


def test_legacy_answers_without_status_still_build():
    """An answers dict from a pre-amendment caller still builds without raising."""
    from intent_scaffold import build_intent
    result = build_intent(FULL_ANSWERS)
    assert isinstance(result, str)


def test_legacy_positional_call_signature_unchanged(tmp_path):
    """Pre-amendment call sites (path, answers) / (answers) keep working."""
    from intent_scaffold import build_intent, write_intent
    build_intent(FULL_ANSWERS)
    target = tmp_path / "INTENT.md"
    write_intent(str(target), FULL_ANSWERS)
    assert target.exists()


# ---------------------------------------------------------------------------
# The "appended LAST, never reordered" invariant — pinned STRUCTURALLY.
#
# yaml.safe_load is order-insensitive, so every parsed-form assertion above is
# blind to key ORDER. The additive-amendment claim in protocol/intent.md ("no
# existing field was removed or reordered") is therefore unpinned by them: an
# edit that inserted `status` in the middle would keep all of them green. These
# tests read the RAW frontmatter text instead.
# ---------------------------------------------------------------------------

def _frontmatter_text(text: str) -> str:
    """Return the raw YAML frontmatter block, un-parsed, order preserved."""
    lines = text.splitlines()
    assert lines[0].strip() == "---"
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:i])
    raise ValueError("No closing frontmatter delimiter found")


def _top_level_key_order(text: str) -> list[str]:
    """Top-level frontmatter keys in EMITTED order (nested keys are indented)."""
    keys = []
    for line in _frontmatter_text(text).splitlines():
        if line[:1].isalpha() and ":" in line:
            keys.append(line.split(":", 1)[0])
    return keys


PRE_FIELD_KEY_ORDER = ["kind", "goal", "fixes", "features", "modulesAdded",
                       "changeSummary", "target", "grillDepth", "readiness"]


def test_status_is_the_final_top_level_key():
    from intent_scaffold import build_intent
    assert _top_level_key_order(build_intent(FULL_ANSWERS))[-1] == "status"
    assert _top_level_key_order(build_intent(FULL_ANSWERS, freeze=True))[-1] == "status"


def test_status_is_appended_not_inserted():
    """Every pre-existing key keeps its exact position; status is added at the end."""
    from intent_scaffold import build_intent
    assert _top_level_key_order(build_intent(FULL_ANSWERS)) == [*PRE_FIELD_KEY_ORDER, "status"]


def test_status_appended_after_optional_acceptance_criteria():
    """With the optional field present, status is still last."""
    from intent_scaffold import build_intent
    text = build_intent({**FULL_ANSWERS, "acceptanceCriteria": ["a", "b"]})
    assert _top_level_key_order(text) == [
        *PRE_FIELD_KEY_ORDER, "acceptanceCriteria", "status",
    ]


def test_output_minus_status_line_is_byte_identical_to_pre_field_build():
    """Golden: dropping the emitted `status:` line reproduces the pre-field bytes.

    This is the amendment's whole BC claim as a byte assertion — the new field
    costs exactly one appended line and perturbs nothing else in the artifact.
    Mutation-proof: reordering the frontmatter dict, or re-rendering any other
    value, breaks this even though every parsed-form test stays green.
    """
    from intent_scaffold import build_intent

    text = build_intent(FULL_ANSWERS)
    stripped = text.replace("status: draft\n", "", 1)

    # The pre-field bytes, reconstructed independently of the builder: the same
    # YAML dump of the same ordered mapping, minus the appended row.
    import yaml as _yaml
    pre_field_fm = _yaml.dump(
        {
            "kind": FULL_ANSWERS["kind"],
            "goal": FULL_ANSWERS["goal"],
            "fixes": FULL_ANSWERS["fixes"],
            "features": FULL_ANSWERS["features"],
            "modulesAdded": FULL_ANSWERS["modulesAdded"],
            "changeSummary": FULL_ANSWERS["changeSummary"],
            "target": {
                "kind": FULL_ANSWERS["target"]["kind"],
                "path": FULL_ANSWERS["target"]["path"],
                "vault": FULL_ANSWERS["target"]["vault"],
                "platform": FULL_ANSWERS["target"]["platform"],
            },
            "grillDepth": FULL_ANSWERS["grillDepth"],
            "readiness": FULL_ANSWERS["readiness"],
        },
        default_flow_style=False, allow_unicode=True, sort_keys=False,
    )
    assert _frontmatter_text(stripped) + "\n" == pre_field_fm


def test_draft_and_frozen_differ_only_in_the_status_line():
    """The freeze changes exactly one line — nothing else in the artifact moves."""
    from intent_scaffold import build_intent
    draft = build_intent(FULL_ANSWERS).replace("status: draft\n", "", 1)
    frozen = build_intent(FULL_ANSWERS, freeze=True).replace("status: frozen\n", "", 1)
    assert draft == frozen


# ---------------------------------------------------------------------------
# The two-rungs-must-agree law, pinned.
#
# protocol/intent.md states: "Two governor rungs that read a `status:` field
# must not disagree about what that field means." That law lives in prose and
# in a deliberate copy of kata_restore's posture — nothing mechanical held the
# copy in sync, so a later edit to either side could silently fork the seam's
# `plan` and `intent` rungs. These tests are that mechanism.
#
# Importing kata_restore here is safe: its module level is imports, constants
# and compiled regexes only — every subprocess.run call sits inside a function
# body (kata_restore.py:94, :128), so no git/subprocess work happens at import.
# ---------------------------------------------------------------------------

def test_frontmatter_regex_matches_kata_restore():
    """intent_scaffold's frontmatter matcher must equal kata_restore's."""
    import intent_scaffold
    import kata_restore
    assert intent_scaffold._FM_RE.pattern == kata_restore._FM_RE.pattern
    assert intent_scaffold._FM_RE.flags == kata_restore._FM_RE.flags


def test_known_status_sets_align_with_kata_restore():
    """Both rungs read the same two-value vocabulary, per the schema."""
    import intent_scaffold
    import kata_restore
    assert (
        intent_scaffold._KNOWN_INTENT_STATUSES == kata_restore._KNOWN_PLAN_STATUSES
    ), "the `intent` and `plan` rungs must not disagree about `status:`"
    assert intent_scaffold._KNOWN_INTENT_STATUSES == frozenset({"draft", "frozen"})


def test_readers_agree_on_the_same_file(tmp_path):
    """Behavioural half of the law: both readers, one file, same verdict.

    Stronger than comparing constants — it pins that the two rungs actually
    return the same token for identical input, across all three outcomes.
    """
    import intent_scaffold
    import kata_restore

    cases = [
        ("---\nstatus: frozen\n---\n\nbody\n", "frozen"),
        ("---\nstatus: draft\n---\n\nbody\n", "draft"),
        ("---\nstatus: FROZEN — sealed at the gate\n---\n\nbody\n", "frozen"),
        ("---\nkind: project\n---\n\nbody\n", "absent"),
        ("---\nstatus:\n---\n\nbody\n", "absent"),
    ]
    for i, (body, expected) in enumerate(cases):
        p = tmp_path / f"case{i}.md"
        p.write_text(body, encoding="utf-8")
        assert intent_scaffold.intent_status(p) == expected
        assert kata_restore.plan_status(p) == expected

    # And they agree on REFUSING the same unrecognized value.
    bad = tmp_path / "bad.md"
    bad.write_text("---\nstatus: sealed\n---\n\nbody\n", encoding="utf-8")
    with pytest.raises(ValueError):
        intent_scaffold.intent_status(bad)
    with pytest.raises(ValueError):
        kata_restore.plan_status(bad)
