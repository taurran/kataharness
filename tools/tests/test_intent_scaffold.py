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
"""

from __future__ import annotations

import yaml
import pytest


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
    from intent_scaffold import write_intent, build_intent
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
