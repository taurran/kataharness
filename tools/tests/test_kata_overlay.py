"""test_kata_overlay.py — TDD for B1: overlay store + materializer core.

Task B1 of install-update-polish/PLAN.md.
DESIGN §2 (overlay store, M4 compose semantics) / §3 (materialized.json) / §6 (adaptation_context).

Coverage:
- overlay_dir: correct path; rejects '..'
- read_overlay: absent → empty-equivalent; corrupt → empty-equivalent; valid → parsed
- validate_overlay: valid passes ([] errors); structural violations reported
- has_overlay: True when entry present; False when absent
- apply_overlay — frontmatter overrides:
    scalar key replaced; list key (tags) replaced WHOLESALE (M4, never element-merged)
    other frontmatter keys survive; multiple overrides in one pass
- apply_overlay — prepend at named heading: content immediately after heading line
- apply_overlay — append at named heading: content just before next equal-or-higher heading
- apply_overlay — null anchor prepend: content at start of body (before first heading)
- apply_overlay — null anchor append: content at end of body (after all headings)
- apply_overlay — multiple same-anchor prepend/append blocks in array order
- apply_overlay — unresolvable anchor on present base → ValueError (fail-closed)
- apply_overlay — composed output is valid SKILL.md (parse_frontmatter round-trip)
- write_overlay_entry: creates dir; preserves other entries (D127 lesson); updates existing
- drop_overlay_entry: removes named; returns False when absent; preserves others
- adaptation_context: "install" iff .kata-version present; "dev-repo" otherwise
- corrupt overlay.json → read_overlay degrades to empty (no crash)
- read_materialized / write_materialized / record_slot / drop_slot I/O
- No subprocess / git import in kata_overlay.py (DESIGN Invariant 3)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import kata_overlay as ko
from validate_skills import parse_frontmatter

# ---------------------------------------------------------------------------
# Shared SKILL.md fixtures (module-level constants; not written to disk)
# ---------------------------------------------------------------------------

# Body has a leading blank line then two level-2 headings — the canonical test shape.
SKILL_TEXT = """\
---
name: kata-test
version: 0.1.0
model: sonnet
tags:
- kata/meta
- kata/spine
---

## Output
Original output content.

## Guidance
Guidance content.
"""

# Skill with a nested (level-3) heading inside ## Output — for testing append scope.
SKILL_NESTED = """\
---
name: kata-nested
version: 0.1.0
---

## Output
Output intro.

### Sub-output
Sub content.

## Guidance
Guidance content.
"""

# A SKILL.md that starts the body with a level-2 heading directly (no blank line).
SKILL_NO_GAP = """\
---
name: kata-nogap
version: 0.1.0
---
## Output
Content here.
## Guidance
Guidance here.
"""


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_home(tmp_path: Path) -> Path:
    """A minimal home directory (no skills needed for overlay store tests)."""
    home = tmp_path / "KataHarness"
    home.mkdir()
    return home


# ---------------------------------------------------------------------------
# TestOverlayDir
# ---------------------------------------------------------------------------


class TestOverlayDir:
    def test_path_under_home(self, fake_home: Path) -> None:
        d = ko.overlay_dir(fake_home)
        assert d == fake_home / ".kata-overlay"

    def test_rejects_dotdot(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match=r"\.\."):
            ko.overlay_dir(str(tmp_path) + "/../evil")


# ---------------------------------------------------------------------------
# TestReadOverlay
# ---------------------------------------------------------------------------


class TestReadOverlay:
    def test_absent_returns_empty_equivalent(self, fake_home: Path) -> None:
        result = ko.read_overlay(fake_home)
        assert result == {"schema": 1, "skills": {}}

    def test_corrupt_json_returns_empty_equivalent(self, fake_home: Path) -> None:
        ko.overlay_dir(fake_home).mkdir(parents=True)
        (ko.overlay_dir(fake_home) / "overlay.json").write_text(
            "not valid json!!", encoding="utf-8"
        )
        assert ko.read_overlay(fake_home) == {"schema": 1, "skills": {}}

    def test_valid_json_non_dict_returns_empty_equivalent(self, fake_home: Path) -> None:
        ko.overlay_dir(fake_home).mkdir(parents=True)
        (ko.overlay_dir(fake_home) / "overlay.json").write_text(
            "[1, 2, 3]", encoding="utf-8"
        )
        assert ko.read_overlay(fake_home) == {"schema": 1, "skills": {}}

    def test_valid_overlay_returns_parsed(self, fake_home: Path) -> None:
        data = {
            "schema": 1,
            "skills": {
                "kata-test": {
                    "frontmatterOverrides": {"model": "haiku"},
                    "prepend": [],
                    "append": [],
                    "pin": None,
                }
            },
        }
        ko.overlay_dir(fake_home).mkdir(parents=True)
        (ko.overlay_dir(fake_home) / "overlay.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        result = ko.read_overlay(fake_home)
        assert result["skills"]["kata-test"]["frontmatterOverrides"]["model"] == "haiku"

    def test_missing_skills_key_returns_empty_equivalent(self, fake_home: Path) -> None:
        ko.overlay_dir(fake_home).mkdir(parents=True)
        (ko.overlay_dir(fake_home) / "overlay.json").write_text(
            json.dumps({"schema": 1}), encoding="utf-8"
        )
        assert ko.read_overlay(fake_home) == {"schema": 1, "skills": {}}


# ---------------------------------------------------------------------------
# TestValidateOverlay
# ---------------------------------------------------------------------------


class TestValidateOverlay:
    def _valid(self) -> dict:
        return {
            "schema": 1,
            "skills": {
                "kata-test": {
                    "frontmatterOverrides": {"model": "haiku"},
                    "prepend": [{"anchor": "## Output", "markdown": "BLOCK"}],
                    "append": [],
                    "pin": "0.1.0",
                }
            },
        }

    def test_valid_overlay_returns_no_errors(self) -> None:
        assert ko.validate_overlay(self._valid()) == []

    def test_non_dict_top_level_errors(self) -> None:
        errors = ko.validate_overlay([])  # type: ignore[arg-type]
        assert len(errors) > 0

    def test_missing_schema_errors(self) -> None:
        data = {"skills": {}}
        errors = ko.validate_overlay(data)
        assert any("schema" in e for e in errors)

    def test_skills_not_dict_errors(self) -> None:
        data = {"schema": 1, "skills": "oops"}
        errors = ko.validate_overlay(data)
        assert any("skills" in e for e in errors)

    def test_entry_not_dict_errors(self) -> None:
        data = {"schema": 1, "skills": {"kata-test": "bad"}}
        errors = ko.validate_overlay(data)
        assert any("kata-test" in e for e in errors)

    def test_prepend_not_list_errors(self) -> None:
        data = {
            "schema": 1,
            "skills": {"kata-test": {"frontmatterOverrides": {}, "prepend": "bad", "append": []}},
        }
        errors = ko.validate_overlay(data)
        assert any("prepend" in e for e in errors)

    def test_block_missing_markdown_errors(self) -> None:
        data = {
            "schema": 1,
            "skills": {
                "kata-test": {
                    "frontmatterOverrides": {},
                    "prepend": [{"anchor": "## X"}],  # no markdown
                    "append": [],
                }
            },
        }
        errors = ko.validate_overlay(data)
        assert any("markdown" in e for e in errors)

    def test_empty_skills_is_valid(self) -> None:
        assert ko.validate_overlay({"schema": 1, "skills": {}}) == []


# ---------------------------------------------------------------------------
# TestHasOverlay
# ---------------------------------------------------------------------------


class TestHasOverlay:
    def test_true_when_entry_present(self, fake_home: Path) -> None:
        ko.write_overlay_entry(
            fake_home,
            "kata-test",
            {"frontmatterOverrides": {}, "prepend": [], "append": [], "pin": None},
        )
        assert ko.has_overlay(fake_home, "kata-test") is True

    def test_false_when_entry_absent(self, fake_home: Path) -> None:
        assert ko.has_overlay(fake_home, "kata-test") is False

    def test_false_after_drop(self, fake_home: Path) -> None:
        ko.write_overlay_entry(
            fake_home,
            "kata-test",
            {"frontmatterOverrides": {}, "prepend": [], "append": [], "pin": None},
        )
        ko.drop_overlay_entry(fake_home, "kata-test")
        assert ko.has_overlay(fake_home, "kata-test") is False


# ---------------------------------------------------------------------------
# TestApplyOverlayFrontmatter
# ---------------------------------------------------------------------------


class TestApplyOverlayFrontmatter:
    def _entry(self, overrides: dict) -> dict:
        return {"frontmatterOverrides": overrides, "prepend": [], "append": [], "pin": None}

    def test_scalar_override_replaces_value(self) -> None:
        entry = self._entry({"model": "haiku"})
        result = ko.apply_overlay(SKILL_TEXT, entry)
        fm, _ = parse_frontmatter(result)
        assert fm["model"] == "haiku"

    def test_scalar_override_leaves_other_keys(self) -> None:
        entry = self._entry({"model": "haiku"})
        result = ko.apply_overlay(SKILL_TEXT, entry)
        fm, _ = parse_frontmatter(result)
        assert fm["name"] == "kata-test"
        assert fm["version"] == "0.1.0"

    def test_list_key_replaced_wholesale_not_merged(self) -> None:
        """M4: list-valued keys replaced WHOLESALE — base list is not element-merged."""
        entry = self._entry({"tags": ["kata/meta", "kata/custom"]})
        result = ko.apply_overlay(SKILL_TEXT, entry)
        fm, _ = parse_frontmatter(result)
        # Should be EXACTLY the override list, not base list + override list.
        assert fm["tags"] == ["kata/meta", "kata/custom"]
        # Specifically: "kata/spine" from the base must NOT appear.
        assert "kata/spine" not in fm["tags"]

    def test_list_and_scalar_overrides_together(self) -> None:
        """Both a scalar and a list key can be overridden in one entry."""
        entry = self._entry({"model": "opus", "tags": ["kata/custom"]})
        result = ko.apply_overlay(SKILL_TEXT, entry)
        fm, _ = parse_frontmatter(result)
        assert fm["model"] == "opus"
        assert fm["tags"] == ["kata/custom"]
        # Non-overridden keys survive.
        assert fm["name"] == "kata-test"
        assert fm["version"] == "0.1.0"

    def test_empty_overrides_leaves_frontmatter_unchanged(self) -> None:
        entry = self._entry({})
        result = ko.apply_overlay(SKILL_TEXT, entry)
        fm, _ = parse_frontmatter(result)
        assert fm["name"] == "kata-test"
        assert fm["model"] == "sonnet"
        assert fm["tags"] == ["kata/meta", "kata/spine"]

    # F4: a non-indented block-list item `- k: v` must NOT be misread as a
    # top-level key (which truncated the owning key's value-block).
    _SKILL_BLOCK_LIST = (
        "---\n"
        "name: kata-list\n"
        "steps:\n"
        "- run: build\n"
        "- run: test\n"
        "model: sonnet\n"
        "---\n"
        "\n"
        "## Output\n"
        "body\n"
    )

    def test_override_block_list_of_mappings_reconstructs(self) -> None:
        """Overriding a key whose value is a `- k: v` block list replaces it
        wholesale — no stray list items strand after the new flow line (F4)."""
        entry = self._entry({"steps": ["lint", "ship"]})
        result = ko.apply_overlay(self._SKILL_BLOCK_LIST, entry)
        fm, _ = parse_frontmatter(result)  # would raise on stranded list items
        assert fm["steps"] == ["lint", "ship"]
        # Non-overridden keys survive; the mapping-list did not truncate them.
        assert fm["name"] == "kata-list"
        assert fm["model"] == "sonnet"

    def test_scalar_override_preserves_block_list_of_mappings(self) -> None:
        """Overriding a scalar next to a `- k: v` block list leaves the list intact (F4)."""
        entry = self._entry({"model": "haiku"})
        result = ko.apply_overlay(self._SKILL_BLOCK_LIST, entry)
        fm, _ = parse_frontmatter(result)
        assert fm["model"] == "haiku"
        assert fm["steps"] == [{"run": "build"}, {"run": "test"}]


# ---------------------------------------------------------------------------
# TestApplyOverlayPrepend
# ---------------------------------------------------------------------------


class TestApplyOverlayPrepend:
    def _entry_prepend(self, blocks: list[dict]) -> dict:
        return {"frontmatterOverrides": {}, "prepend": blocks, "append": [], "pin": None}

    def test_prepend_named_heading_immediately_after_heading(self) -> None:
        """prepend block lands as the FIRST content after the anchor heading line."""
        entry = self._entry_prepend([{"anchor": "## Output", "markdown": "PREPENDED_CONTENT"}])
        result = ko.apply_overlay(SKILL_TEXT, entry)
        # The prepended block appears right after the heading.
        assert "## Output\nPREPENDED_CONTENT" in result

    def test_prepend_named_heading_before_original_content(self) -> None:
        entry = self._entry_prepend([{"anchor": "## Output", "markdown": "PREPENDED_CONTENT"}])
        result = ko.apply_overlay(SKILL_TEXT, entry)
        idx_p = result.index("PREPENDED_CONTENT")
        idx_orig = result.index("Original output content.")
        assert idx_p < idx_orig

    def test_prepend_null_anchor_before_first_heading(self) -> None:
        """null anchor prepend → content appears before the first heading in the body."""
        entry = self._entry_prepend([{"anchor": None, "markdown": "NULL_PREPEND"}])
        result = ko.apply_overlay(SKILL_TEXT, entry)
        assert "NULL_PREPEND" in result
        idx_p = result.index("NULL_PREPEND")
        idx_h = result.index("## Output")
        assert idx_p < idx_h

    def test_prepend_null_anchor_after_frontmatter(self) -> None:
        """null anchor prepend appears after the closing '---' of the frontmatter block."""
        entry = self._entry_prepend([{"anchor": None, "markdown": "NULL_PREPEND"}])
        result = ko.apply_overlay(SKILL_TEXT, entry)
        # The frontmatter ends with '---'; content should come after it.
        fm_end = result.index("---", result.index("---") + 3)  # second ---
        idx_p = result.index("NULL_PREPEND")
        assert idx_p > fm_end

    def test_prepend_multiple_same_anchor_array_order(self) -> None:
        """Multiple same-anchor prepend blocks appear in array order (B1 gate)."""
        entry = self._entry_prepend([
            {"anchor": "## Output", "markdown": "BLOCK_A"},
            {"anchor": "## Output", "markdown": "BLOCK_B"},
        ])
        result = ko.apply_overlay(SKILL_TEXT, entry)
        assert "BLOCK_A" in result
        assert "BLOCK_B" in result
        assert result.index("BLOCK_A") < result.index("BLOCK_B")

    def test_prepend_multiple_same_anchor_both_after_heading(self) -> None:
        entry = self._entry_prepend([
            {"anchor": "## Output", "markdown": "BLOCK_A"},
            {"anchor": "## Output", "markdown": "BLOCK_B"},
        ])
        result = ko.apply_overlay(SKILL_TEXT, entry)
        heading_idx = result.index("## Output")
        assert result.index("BLOCK_A") > heading_idx
        assert result.index("BLOCK_B") > heading_idx

    def test_prepend_different_anchors_each_placed_correctly(self) -> None:
        """Two prepend blocks for different anchors each land at their own anchor."""
        entry = self._entry_prepend([
            {"anchor": "## Output", "markdown": "OUTPUT_PREPEND"},
            {"anchor": "## Guidance", "markdown": "GUIDANCE_PREPEND"},
        ])
        result = ko.apply_overlay(SKILL_TEXT, entry)
        assert "## Output\nOUTPUT_PREPEND" in result
        assert "## Guidance\nGUIDANCE_PREPEND" in result


# ---------------------------------------------------------------------------
# TestApplyOverlayAppend
# ---------------------------------------------------------------------------


class TestApplyOverlayAppend:
    def _entry_append(self, blocks: list[dict]) -> dict:
        return {"frontmatterOverrides": {}, "prepend": [], "append": blocks, "pin": None}

    def test_append_named_heading_before_next_same_level_heading(self) -> None:
        """append block lands just before the next equal-or-higher heading."""
        entry = self._entry_append([{"anchor": "## Output", "markdown": "APPENDED_CONTENT"}])
        result = ko.apply_overlay(SKILL_TEXT, entry)
        # Content appears before ## Guidance.
        idx_a = result.index("APPENDED_CONTENT")
        idx_g = result.index("## Guidance")
        assert idx_a < idx_g

    def test_append_named_heading_after_original_content(self) -> None:
        entry = self._entry_append([{"anchor": "## Output", "markdown": "APPENDED_CONTENT"}])
        result = ko.apply_overlay(SKILL_TEXT, entry)
        idx_orig = result.index("Original output content.")
        idx_a = result.index("APPENDED_CONTENT")
        assert idx_orig < idx_a

    def test_append_stops_before_same_level_not_higher_level(self) -> None:
        """A level-3 heading inside the section does NOT stop the append search."""
        # In SKILL_NESTED, ## Output contains ### Sub-output.
        # Append to ## Output should place content before ## Guidance (level-2), not before ### Sub-output.
        entry = self._entry_append([{"anchor": "## Output", "markdown": "APPENDED"}])
        result = ko.apply_overlay(SKILL_NESTED, entry)
        idx_a = result.index("APPENDED")
        idx_g = result.index("## Guidance")
        idx_sub = result.index("### Sub-output")
        # APPENDED appears after ### Sub-output (level-3 doesn't stop it)
        assert idx_a > idx_sub
        # APPENDED appears before ## Guidance (level-2 stops it)
        assert idx_a < idx_g

    def test_append_null_anchor_at_end_of_body(self) -> None:
        """null anchor append → content at end of body, after all headings."""
        entry = self._entry_append([{"anchor": None, "markdown": "NULL_APPEND"}])
        result = ko.apply_overlay(SKILL_TEXT, entry)
        assert "NULL_APPEND" in result
        # Must appear after all body headings.
        idx_a = result.rindex("NULL_APPEND")
        idx_last_heading = result.rindex("## Guidance")
        assert idx_a > idx_last_heading

    def test_append_multiple_same_anchor_array_order(self) -> None:
        """Multiple same-anchor append blocks appear in array order."""
        entry = self._entry_append([
            {"anchor": "## Output", "markdown": "BLOCK_A"},
            {"anchor": "## Output", "markdown": "BLOCK_B"},
        ])
        result = ko.apply_overlay(SKILL_TEXT, entry)
        assert result.index("BLOCK_A") < result.index("BLOCK_B")

    def test_append_multiple_same_anchor_both_before_next_heading(self) -> None:
        entry = self._entry_append([
            {"anchor": "## Output", "markdown": "BLOCK_A"},
            {"anchor": "## Output", "markdown": "BLOCK_B"},
        ])
        result = ko.apply_overlay(SKILL_TEXT, entry)
        idx_g = result.index("## Guidance")
        assert result.index("BLOCK_A") < idx_g
        assert result.index("BLOCK_B") < idx_g

    def test_append_to_last_section_goes_to_end(self) -> None:
        """Appending to the last heading (no next heading) places content at end."""
        entry = self._entry_append([{"anchor": "## Guidance", "markdown": "END_BLOCK"}])
        result = ko.apply_overlay(SKILL_TEXT, entry)
        idx_a = result.index("END_BLOCK")
        idx_g = result.index("## Guidance")
        # END_BLOCK is after ## Guidance content.
        assert idx_a > idx_g


# ---------------------------------------------------------------------------
# TestApplyOverlayFailClosed
# ---------------------------------------------------------------------------


class TestApplyOverlayFailClosed:
    def test_unresolvable_prepend_anchor_raises_value_error(self) -> None:
        """Unresolvable anchor on a present base raises ValueError (fail-closed)."""
        entry = {
            "frontmatterOverrides": {},
            "prepend": [{"anchor": "## NonExistent", "markdown": "X"}],
            "append": [],
            "pin": None,
        }
        with pytest.raises(ValueError, match="anchor"):
            ko.apply_overlay(SKILL_TEXT, entry)

    def test_unresolvable_append_anchor_raises_value_error(self) -> None:
        entry = {
            "frontmatterOverrides": {},
            "prepend": [],
            "append": [{"anchor": "## Missing", "markdown": "X"}],
            "pin": None,
        }
        with pytest.raises(ValueError, match="anchor"):
            ko.apply_overlay(SKILL_TEXT, entry)

    def test_valid_anchor_does_not_raise(self) -> None:
        entry = {
            "frontmatterOverrides": {},
            "prepend": [{"anchor": "## Output", "markdown": "X"}],
            "append": [],
            "pin": None,
        }
        result = ko.apply_overlay(SKILL_TEXT, entry)
        assert "## Output" in result  # no exception raised


# ---------------------------------------------------------------------------
# TestApplyOverlayRoundTrip
# ---------------------------------------------------------------------------


class TestApplyOverlayRoundTrip:
    def test_composed_output_parses_cleanly(self) -> None:
        """The composed result is a valid SKILL.md: parse_frontmatter round-trips it."""
        entry = {
            "frontmatterOverrides": {"model": "haiku"},
            "prepend": [{"anchor": "## Output", "markdown": "GUARD NOTE"}],
            "append": [{"anchor": "## Guidance", "markdown": "APPENDED NOTE"}],
            "pin": None,
        }
        result = ko.apply_overlay(SKILL_TEXT, entry)
        fm, body = parse_frontmatter(result)
        # Frontmatter round-trips.
        assert isinstance(fm, dict)
        assert fm.get("name") == "kata-test"
        assert fm.get("model") == "haiku"
        # Body still contains the headings.
        assert "## Output" in body
        assert "## Guidance" in body

    def test_composed_output_starts_with_frontmatter_block(self) -> None:
        entry = {"frontmatterOverrides": {}, "prepend": [], "append": [], "pin": None}
        result = ko.apply_overlay(SKILL_TEXT, entry)
        assert result.startswith("---\n")

    def test_prepend_and_frontmatter_override_together(self) -> None:
        """Frontmatter override + prepend block in one entry both apply."""
        entry = {
            "frontmatterOverrides": {"model": "opus"},
            "prepend": [{"anchor": "## Output", "markdown": "PREPENDED"}],
            "append": [],
            "pin": None,
        }
        result = ko.apply_overlay(SKILL_TEXT, entry)
        fm, body = parse_frontmatter(result)
        assert fm["model"] == "opus"
        assert "PREPENDED" in body


# ---------------------------------------------------------------------------
# TestWriteOverlayEntry
# ---------------------------------------------------------------------------


class TestWriteOverlayEntry:
    _ENTRY_A = {"frontmatterOverrides": {"model": "haiku"}, "prepend": [], "append": [], "pin": None}
    _ENTRY_B = {"frontmatterOverrides": {"version": "2.0.0"}, "prepend": [], "append": [], "pin": None}

    def test_creates_overlay_json(self, fake_home: Path) -> None:
        path = ko.write_overlay_entry(fake_home, "kata-test", self._ENTRY_A)
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "kata-test" in data["skills"]

    def test_creates_overlay_dir_if_absent(self, fake_home: Path) -> None:
        assert not ko.overlay_dir(fake_home).exists()
        ko.write_overlay_entry(fake_home, "kata-test", self._ENTRY_A)
        assert ko.overlay_dir(fake_home).exists()

    def test_returns_overlay_json_path(self, fake_home: Path) -> None:
        path = ko.write_overlay_entry(fake_home, "kata-test", self._ENTRY_A)
        assert path == ko.overlay_dir(fake_home) / "overlay.json"

    def test_preserves_other_entries_d127(self, fake_home: Path) -> None:
        """D127 / item-3 lesson: write_overlay_entry NEVER wholesale-overwrites; other entries survive."""
        ko.write_overlay_entry(fake_home, "kata-a", self._ENTRY_A)
        ko.write_overlay_entry(fake_home, "kata-b", self._ENTRY_B)
        # Update kata-a; kata-b must survive unchanged.
        new_a = {"frontmatterOverrides": {"model": "sonnet"}, "prepend": [], "append": [], "pin": None}
        ko.write_overlay_entry(fake_home, "kata-a", new_a)
        overlay = ko.read_overlay(fake_home)
        assert "kata-b" in overlay["skills"]
        assert overlay["skills"]["kata-b"] == self._ENTRY_B
        assert overlay["skills"]["kata-a"]["frontmatterOverrides"]["model"] == "sonnet"

    def test_three_entries_all_preserved(self, fake_home: Path) -> None:
        for name in ("skill-x", "skill-y", "skill-z"):
            ko.write_overlay_entry(
                fake_home, name, {"frontmatterOverrides": {"tag": name}, "prepend": [], "append": [], "pin": None}
            )
        overlay = ko.read_overlay(fake_home)
        for name in ("skill-x", "skill-y", "skill-z"):
            assert name in overlay["skills"]

    def test_updates_existing_entry(self, fake_home: Path) -> None:
        ko.write_overlay_entry(fake_home, "kata-test", self._ENTRY_A)
        updated = {"frontmatterOverrides": {"model": "opus"}, "prepend": [], "append": [], "pin": "0.1.0"}
        ko.write_overlay_entry(fake_home, "kata-test", updated)
        overlay = ko.read_overlay(fake_home)
        assert overlay["skills"]["kata-test"]["frontmatterOverrides"]["model"] == "opus"
        assert overlay["skills"]["kata-test"]["pin"] == "0.1.0"

    def test_written_file_is_valid_json(self, fake_home: Path) -> None:
        path = ko.write_overlay_entry(fake_home, "kata-test", self._ENTRY_A)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# TestDropOverlayEntry
# ---------------------------------------------------------------------------


class TestDropOverlayEntry:
    _ENTRY = {"frontmatterOverrides": {}, "prepend": [], "append": [], "pin": None}

    def test_removes_named_entry(self, fake_home: Path) -> None:
        ko.write_overlay_entry(fake_home, "kata-test", self._ENTRY)
        result = ko.drop_overlay_entry(fake_home, "kata-test")
        assert result is True
        assert not ko.has_overlay(fake_home, "kata-test")

    def test_returns_false_when_not_present(self, fake_home: Path) -> None:
        assert ko.drop_overlay_entry(fake_home, "nonexistent") is False

    def test_preserves_other_entries(self, fake_home: Path) -> None:
        ko.write_overlay_entry(fake_home, "kata-a", self._ENTRY)
        ko.write_overlay_entry(fake_home, "kata-b", self._ENTRY)
        ko.drop_overlay_entry(fake_home, "kata-a")
        assert not ko.has_overlay(fake_home, "kata-a")
        assert ko.has_overlay(fake_home, "kata-b")

    def test_idempotent_double_drop(self, fake_home: Path) -> None:
        ko.write_overlay_entry(fake_home, "kata-test", self._ENTRY)
        ko.drop_overlay_entry(fake_home, "kata-test")
        # Second drop: False (not found), no crash.
        assert ko.drop_overlay_entry(fake_home, "kata-test") is False


# ---------------------------------------------------------------------------
# TestAdaptationContext
# ---------------------------------------------------------------------------


class TestAdaptationContext:
    def test_install_when_stamp_present(self, fake_home: Path) -> None:
        import kata_version as kv
        kv.write_stamp(
            fake_home,
            git_sha="unknown",
            suite_semver="0.1.0",
            ref="master",
            link_mode="symlink",
            platform="claude",
        )
        assert ko.adaptation_context(fake_home) == "install"

    def test_dev_repo_when_stamp_absent(self, fake_home: Path) -> None:
        assert ko.adaptation_context(fake_home) == "dev-repo"

    def test_dev_repo_after_stamp_deleted(self, fake_home: Path) -> None:
        import kata_version as kv
        kv.write_stamp(
            fake_home,
            git_sha="unknown",
            suite_semver="0.1.0",
            ref="master",
            link_mode="symlink",
            platform="claude",
        )
        assert ko.adaptation_context(fake_home) == "install"
        kv.stamp_path(fake_home).unlink()
        assert ko.adaptation_context(fake_home) == "dev-repo"


# ---------------------------------------------------------------------------
# TestReadMaterialized
# ---------------------------------------------------------------------------


class TestReadMaterialized:
    def test_absent_returns_empty_equivalent(self, fake_home: Path) -> None:
        result = ko.read_materialized(fake_home)
        assert result == {"schema": 1, "slots": {}}

    def test_corrupt_returns_empty_equivalent(self, fake_home: Path) -> None:
        ko.overlay_dir(fake_home).mkdir(parents=True)
        (ko.overlay_dir(fake_home) / "materialized.json").write_text(
            "not json", encoding="utf-8"
        )
        assert ko.read_materialized(fake_home) == {"schema": 1, "slots": {}}

    def test_valid_returns_parsed(self, fake_home: Path) -> None:
        data = {
            "schema": 1,
            "slots": {
                "kata-test": {
                    "hostPath": "/home/.claude/skills/kata-test",
                    "baseMode": "symlink",
                    "source": "overlay",
                    "appliedSha": "abc123",
                }
            },
        }
        ko.overlay_dir(fake_home).mkdir(parents=True)
        (ko.overlay_dir(fake_home) / "materialized.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        result = ko.read_materialized(fake_home)
        assert result["slots"]["kata-test"]["baseMode"] == "symlink"


# ---------------------------------------------------------------------------
# TestWriteMaterialized
# ---------------------------------------------------------------------------


class TestWriteMaterialized:
    def test_write_round_trip(self, fake_home: Path) -> None:
        data = {
            "schema": 1,
            "slots": {
                "kata-test": {
                    "hostPath": "/some/path",
                    "baseMode": "copy",
                    "source": "overlay",
                    "appliedSha": "deadbeef",
                }
            },
        }
        path = ko.write_materialized(fake_home, data)
        assert path.exists()
        result = ko.read_materialized(fake_home)
        assert result["slots"]["kata-test"]["baseMode"] == "copy"

    def test_creates_overlay_dir(self, fake_home: Path) -> None:
        assert not ko.overlay_dir(fake_home).exists()
        ko.write_materialized(fake_home, {"schema": 1, "slots": {}})
        assert ko.overlay_dir(fake_home).exists()

    def test_returns_materialized_path(self, fake_home: Path) -> None:
        path = ko.write_materialized(fake_home, {"schema": 1, "slots": {}})
        assert path == ko.overlay_dir(fake_home) / "materialized.json"


# ---------------------------------------------------------------------------
# TestRecordSlot
# ---------------------------------------------------------------------------


class TestRecordSlot:
    _SLOT_A = {"hostPath": "/a", "baseMode": "symlink", "source": "overlay", "appliedSha": "aaa"}
    _SLOT_B = {"hostPath": "/b", "baseMode": "copy", "source": "overlay", "appliedSha": "bbb"}

    def test_creates_slot(self, fake_home: Path) -> None:
        ko.record_slot(fake_home, "kata-a", self._SLOT_A)
        result = ko.read_materialized(fake_home)
        assert "kata-a" in result["slots"]
        assert result["slots"]["kata-a"]["baseMode"] == "symlink"

    def test_preserves_other_slots(self, fake_home: Path) -> None:
        ko.record_slot(fake_home, "kata-a", self._SLOT_A)
        ko.record_slot(fake_home, "kata-b", self._SLOT_B)
        ko.record_slot(fake_home, "kata-a", {**self._SLOT_A, "appliedSha": "new"})
        result = ko.read_materialized(fake_home)
        # kata-b must survive.
        assert result["slots"]["kata-b"] == self._SLOT_B
        assert result["slots"]["kata-a"]["appliedSha"] == "new"

    def test_returns_path(self, fake_home: Path) -> None:
        path = ko.record_slot(fake_home, "kata-a", self._SLOT_A)
        assert path == ko.overlay_dir(fake_home) / "materialized.json"


# ---------------------------------------------------------------------------
# TestDropSlot
# ---------------------------------------------------------------------------


class TestDropSlot:
    _SLOT = {"hostPath": "/x", "baseMode": "symlink", "source": "overlay", "appliedSha": "xxx"}

    def test_removes_slot_returns_true(self, fake_home: Path) -> None:
        ko.record_slot(fake_home, "kata-test", self._SLOT)
        assert ko.drop_slot(fake_home, "kata-test") is True
        assert "kata-test" not in ko.read_materialized(fake_home)["slots"]

    def test_returns_false_when_absent(self, fake_home: Path) -> None:
        assert ko.drop_slot(fake_home, "nonexistent") is False

    def test_preserves_other_slots(self, fake_home: Path) -> None:
        ko.record_slot(fake_home, "kata-a", self._SLOT)
        ko.record_slot(fake_home, "kata-b", {**self._SLOT, "appliedSha": "bbb"})
        ko.drop_slot(fake_home, "kata-a")
        result = ko.read_materialized(fake_home)
        assert "kata-a" not in result["slots"]
        assert "kata-b" in result["slots"]


# ---------------------------------------------------------------------------
# TestNoGitNoSubprocess (DESIGN Invariant 3)
# ---------------------------------------------------------------------------


class TestNoGitNoSubprocess:
    def test_module_does_not_import_subprocess(self) -> None:
        source = Path(ko.__file__).read_text(encoding="utf-8")
        assert "import subprocess" not in source

    def test_module_does_not_import_git(self) -> None:
        source = Path(ko.__file__).read_text(encoding="utf-8")
        assert "import git" not in source


# ---------------------------------------------------------------------------
# TestNoYaml — stdlib-only invariant (install/materialize path has no pyyaml)
# ---------------------------------------------------------------------------


class TestNoYaml:
    """kata_overlay MUST be stdlib-only — the install/materialize path runs under a
    plain ``python`` with NO pyyaml installed.  Importing yaml (directly or via
    validate_skills) would make kata_install's import-guarded _materialize_pass
    silently no-op in a real install (overlays would never materialize)."""

    def test_module_source_has_no_yaml_import(self) -> None:
        source = Path(ko.__file__).read_text(encoding="utf-8")
        assert "import yaml" not in source, "kata_overlay must never import yaml"

    def test_module_source_does_not_import_validate_skills(self) -> None:
        """validate_skills imports yaml at module top, so importing it transitively
        pulls yaml — kata_overlay must do its own stdlib frontmatter split instead."""
        source = Path(ko.__file__).read_text(encoding="utf-8")
        assert "import validate_skills" not in source
        assert "from validate_skills" not in source

    def test_importing_kata_overlay_does_not_load_yaml(self) -> None:
        """In a CLEAN interpreter, importing kata_overlay must not pull yaml into
        sys.modules.  Run in a subprocess because this test process already imported
        yaml (via validate_skills.parse_frontmatter for round-trip assertions)."""
        import subprocess
        import sys

        tools_dir = Path(ko.__file__).resolve().parent
        code = (
            "import sys; import kata_overlay; "
            "assert 'yaml' not in sys.modules, "
            "'kata_overlay import pulled yaml into sys.modules'"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(tools_dir),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"clean import of kata_overlay loaded yaml or failed:\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
