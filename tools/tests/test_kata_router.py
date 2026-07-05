"""Tests for kata_router.py — AGENTS.md marker-stanza manager.

TDD discipline: written FIRST (red→green).  All tests use tmp_path; pure stdlib;
no real kata run required.

Coverage
--------
- render_stanza has begin/end markers in the correct order
- stanza body is within the 15-line budget (between markers)
- stanza names the required entrypoints (kata-bootstrap, kata-validate)
- stanza names the required state paths (.kata/, .planning/, INTENT.md, kata.config)
- render_stanza is deterministic (byte-stable for identical inputs)
- render_stanza body contains no HTML tags
- write_stanza creates AGENTS.md with exactly one marked block when file is absent
- write_stanza appends block when file exists without a block (preserves user content byte-for-byte)
- write_stanza idempotent: second call yields exactly ONE block; surrounding content unchanged
- remove_stanza removes exactly the marked block; surrounding content byte-identical
- remove_stanza is a no-op when the file has no marked block (no crash, file unchanged)
- remove_stanza is a no-op when the file is absent (no crash, no spurious file)
- _safe_path rejects paths containing '..' (raises ValueError)

Mutation-proof targets
----------------------
- marker-match: swapping BEGIN/END would break presence/count assertions
- replace-in-place vs append: always-appending ⇒ idempotency tests see 2 blocks
- no-op-on-absent guard: crashing on absent ⇒ noop tests fail
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import kata_router

# ---------------------------------------------------------------------------
# Marker constants (must match what the module exposes)
# ---------------------------------------------------------------------------

BEGIN = "<!-- kata:begin -->"
END = "<!-- kata:end -->"

# CA-L20 standing line — distinctive substrings the resume/re-anchor line must carry.
RESUME_PHRASE = "re-anchors via `.planning/HANDOFF.md`"
RESUME_STALENESS = "staleness rule before doing anything else"
RESUME_FALLBACK = "Universal fallback for platforms with no hook"


def _body_lines(stanza: str) -> list[str]:
    """Return the lines strictly between the BEGIN and END markers."""
    lines = stanza.splitlines()
    begin_idx = next(i for i, ln in enumerate(lines) if ln == BEGIN)
    end_idx = next(i for i, ln in enumerate(lines) if ln == END)
    return lines[begin_idx + 1 : end_idx]


# ---------------------------------------------------------------------------
# Import smoke
# ---------------------------------------------------------------------------


def test_import():
    """Importing the module must not raise."""
    import kata_router as kr  # noqa: F401

    assert kr is not None


# ---------------------------------------------------------------------------
# render_stanza — structural
# ---------------------------------------------------------------------------


def test_render_stanza_returns_str():
    assert isinstance(kata_router.render_stanza(), str)


def test_render_stanza_has_begin_marker():
    assert BEGIN in kata_router.render_stanza()


def test_render_stanza_has_end_marker():
    assert END in kata_router.render_stanza()


def test_render_stanza_markers_in_order():
    """begin marker must precede end marker."""
    stanza = kata_router.render_stanza()
    assert stanza.index(BEGIN) < stanza.index(END)


def test_render_stanza_line_budget():
    """Content between markers must be <= 15 lines (instruction-budget contract)."""
    stanza = kata_router.render_stanza()
    lines = stanza.splitlines()
    try:
        begin_idx = lines.index(BEGIN)
        end_idx = lines.index(END)
    except ValueError:
        pytest.fail("BEGIN or END marker was not found as a standalone line")
    content_lines = lines[begin_idx + 1 : end_idx]
    assert len(content_lines) <= 17, (
        f"Stanza body has {len(content_lines)} lines (budget: ≤17); "
        f"body:\n" + "\n".join(content_lines)
    )


# ---------------------------------------------------------------------------
# render_stanza — required content
# ---------------------------------------------------------------------------


def test_render_stanza_contains_kata_bootstrap():
    assert "kata-bootstrap" in kata_router.render_stanza()


def test_render_stanza_contains_kata_validate():
    assert "kata-validate" in kata_router.render_stanza()


def test_render_stanza_kata_validate_gloss_reflects_validation():
    """kata-validate line must describe adversarial validation, not run-state inspection.

    Mutation-proof: reverting the gloss to 'check current run state' → assertion fails.
    """
    stanza = kata_router.render_stanza()
    lines = stanza.splitlines()
    begin_idx = next(i for i, ln in enumerate(lines) if ln == BEGIN)
    end_idx = next(i for i, ln in enumerate(lines) if ln == END)
    body_lines = lines[begin_idx + 1 : end_idx]
    validate_line = next(
        (ln for ln in body_lines if "kata-validate" in ln), None
    )
    assert validate_line is not None, "No line containing 'kata-validate' found in stanza body"
    assert "run state" not in validate_line, (
        "kata-validate gloss still says 'run state' — update _STANZA_BODY in kata_router.py"
    )
    assert any(word in validate_line for word in ("validate", "adversarial", "payload")), (
        f"kata-validate gloss does not reflect validation purpose: {validate_line!r}"
    )


def test_render_stanza_contains_kata_dir():
    assert ".kata/" in kata_router.render_stanza()


def test_render_stanza_contains_planning_dir():
    assert ".planning/" in kata_router.render_stanza()


def test_render_stanza_contains_intent_md():
    assert "INTENT.md" in kata_router.render_stanza()


def test_render_stanza_contains_kata_config():
    assert "kata.config" in kata_router.render_stanza()


def test_render_stanza_no_html_in_body():
    """Body between markers must contain no HTML tags (Markdown only)."""
    stanza = kata_router.render_stanza()
    lines = stanza.splitlines()
    begin_idx = next(i for i, ln in enumerate(lines) if ln == BEGIN)
    end_idx = next(i for i, ln in enumerate(lines) if ln == END)
    body = "\n".join(lines[begin_idx + 1 : end_idx])
    assert not re.search(r"<[a-zA-Z][^>]*>", body), (
        "HTML tags found in stanza body — use Markdown only"
    )


# ---------------------------------------------------------------------------
# CA-L20 — the resume/compact re-anchor standing line (A7)
# ---------------------------------------------------------------------------


def test_render_stanza_contains_resume_reanchor_line():
    """Stanza body carries the CA-L20 standing line verbatim (re-anchor via HANDOFF.md).

    Mutation-proof: deleting the standing line from _STANZA_BODY → this fails (RED).
    """
    body = "\n".join(_body_lines(kata_router.render_stanza()))
    assert RESUME_PHRASE in body, (
        f"CA-L20 re-anchor phrase missing from stanza body:\n{body}"
    )
    assert RESUME_STALENESS in body, (
        f"CA-L20 staleness-rule clause missing from stanza body:\n{body}"
    )
    assert RESUME_FALLBACK in body, (
        f"CA-L20 universal-fallback clause missing from stanza body:\n{body}"
    )


def test_render_stanza_resume_line_appears_once():
    """The standing line's distinctive phrase appears exactly once in the body."""
    body = "\n".join(_body_lines(kata_router.render_stanza()))
    assert body.count(RESUME_PHRASE) == 1


def test_write_stanza_upsert_over_old_stanza_adds_line_exactly_once(tmp_path):
    """Upserting over a pre-v0.2.1 stanza (no standing line) adds the line exactly once.

    Simulates a target that already carries an OLD marked block; the existing
    marked-block-replace machinery must swap in the new body containing the line.
    """
    agents_md = tmp_path / "AGENTS.md"
    old_block = (
        "# My Project\n\n"
        f"{BEGIN}\n"
        "## KataHarness\n\n"
        "KataHarness is installed in this project.\n\n"
        "_Managed by KataHarness._\n"
        f"{END}\n"
    )
    agents_md.write_text(old_block, encoding="utf-8")
    assert RESUME_PHRASE not in old_block  # precondition: old stanza lacks the line

    kata_router.write_stanza(str(agents_md))

    content = agents_md.read_text(encoding="utf-8")
    assert content.count(BEGIN) == 1, "upsert must leave exactly one block"
    assert content.count(END) == 1
    assert content.count(RESUME_PHRASE) == 1, "standing line must appear exactly once"
    assert "# My Project" in content, "surrounding content must be preserved"


def test_write_stanza_idempotent_double_write_line_once(tmp_path):
    """Two write_stanza calls leave the standing line present exactly once (idempotent)."""
    agents_md = tmp_path / "AGENTS.md"
    kata_router.write_stanza(str(agents_md))
    kata_router.write_stanza(str(agents_md))

    content = agents_md.read_text(encoding="utf-8")
    assert content.count(RESUME_PHRASE) == 1


# ---------------------------------------------------------------------------
# render_stanza — determinism
# ---------------------------------------------------------------------------


def test_render_stanza_deterministic_no_args():
    """Repeated calls with identical args produce byte-identical output."""
    assert kata_router.render_stanza() == kata_router.render_stanza()


def test_render_stanza_deterministic_with_summary():
    assert kata_router.render_stanza("v1.2") == kata_router.render_stanza("v1.2")


# ---------------------------------------------------------------------------
# write_stanza — create if absent
# ---------------------------------------------------------------------------


def test_write_stanza_creates_file_if_absent(tmp_path):
    """write_stanza on a missing AGENTS.md creates it with exactly one marked block."""
    agents_md = tmp_path / "AGENTS.md"
    assert not agents_md.exists()

    kata_router.write_stanza(str(agents_md))

    assert agents_md.exists()
    content = agents_md.read_text(encoding="utf-8")
    assert content.count(BEGIN) == 1
    assert content.count(END) == 1


def test_write_stanza_created_file_has_required_content(tmp_path):
    """Newly created AGENTS.md contains entrypoints and state paths."""
    agents_md = tmp_path / "AGENTS.md"
    kata_router.write_stanza(str(agents_md))
    content = agents_md.read_text(encoding="utf-8")
    assert "kata-bootstrap" in content
    assert "kata-validate" in content
    assert ".kata/" in content
    assert "INTENT.md" in content


# ---------------------------------------------------------------------------
# write_stanza — append if present without block
# ---------------------------------------------------------------------------


def test_write_stanza_appends_when_no_block(tmp_path):
    """Block is appended when AGENTS.md exists but has no marked block."""
    agents_md = tmp_path / "AGENTS.md"
    user_content = "# My Project\n\nExisting instructions here.\n"
    agents_md.write_text(user_content, encoding="utf-8")

    kata_router.write_stanza(str(agents_md))

    content = agents_md.read_text(encoding="utf-8")
    assert content.count(BEGIN) == 1
    assert content.count(END) == 1


def test_write_stanza_preserves_existing_content_byte_for_byte(tmp_path):
    """Existing user content is present byte-for-byte after append."""
    agents_md = tmp_path / "AGENTS.md"
    user_content = "# My Project\n\nExisting instructions here.\n"
    agents_md.write_text(user_content, encoding="utf-8")

    kata_router.write_stanza(str(agents_md))

    content = agents_md.read_text(encoding="utf-8")
    assert user_content in content


def test_write_stanza_block_appended_after_existing_content(tmp_path):
    """Stanza is appended (not prepended) when a non-block file exists."""
    agents_md = tmp_path / "AGENTS.md"
    user_content = "# My Project\n\nExisting instructions here.\n"
    agents_md.write_text(user_content, encoding="utf-8")

    kata_router.write_stanza(str(agents_md))

    content = agents_md.read_text(encoding="utf-8")
    # Block comes after user content
    assert content.index(user_content) < content.index(BEGIN)


# ---------------------------------------------------------------------------
# write_stanza — idempotent replace (mutation-proof: swapping to always-append fails here)
# ---------------------------------------------------------------------------


def test_write_stanza_idempotent_exactly_one_block(tmp_path):
    """Calling write_stanza twice yields exactly ONE marked block — never two."""
    agents_md = tmp_path / "AGENTS.md"
    kata_router.write_stanza(str(agents_md))
    kata_router.write_stanza(str(agents_md))

    content = agents_md.read_text(encoding="utf-8")
    assert content.count(BEGIN) == 1, "Idempotency violated: more than one begin marker"
    assert content.count(END) == 1, "Idempotency violated: more than one end marker"


def test_write_stanza_idempotent_surrounding_content_unchanged(tmp_path):
    """After two write_stanza calls, content outside the markers is unchanged."""
    agents_md = tmp_path / "AGENTS.md"
    before = "# Project Header\n"
    after = "\n# Appendix Section\n"
    agents_md.write_text(before + after, encoding="utf-8")

    kata_router.write_stanza(str(agents_md))
    kata_router.write_stanza(str(agents_md))

    content = agents_md.read_text(encoding="utf-8")
    assert content.startswith(before), "Content before the block was altered"
    assert after in content, "Content after the block was altered"
    assert content.count(BEGIN) == 1


def test_write_stanza_idempotent_on_new_file(tmp_path):
    """write_stanza on a brand-new file followed by a second call: still one block."""
    agents_md = tmp_path / "AGENTS.md"
    assert not agents_md.exists()
    kata_router.write_stanza(str(agents_md))
    kata_router.write_stanza(str(agents_md))

    content = agents_md.read_text(encoding="utf-8")
    assert content.count(BEGIN) == 1
    assert content.count(END) == 1


# ---------------------------------------------------------------------------
# remove_stanza — removes exactly the block
# ---------------------------------------------------------------------------


def test_remove_stanza_removes_block(tmp_path):
    """After remove_stanza, zero begin/end markers remain."""
    agents_md = tmp_path / "AGENTS.md"
    kata_router.write_stanza(str(agents_md))

    kata_router.remove_stanza(str(agents_md))

    content = agents_md.read_text(encoding="utf-8")
    assert BEGIN not in content
    assert END not in content


def test_remove_stanza_preserves_surrounding_content(tmp_path):
    """Surrounding user content is byte-identical after remove_stanza."""
    agents_md = tmp_path / "AGENTS.md"
    user_content = "# My Project\n\nSome instructions.\n"
    agents_md.write_text(user_content, encoding="utf-8")
    kata_router.write_stanza(str(agents_md))

    kata_router.remove_stanza(str(agents_md))

    result = agents_md.read_text(encoding="utf-8")
    # Strip trailing whitespace differences (newline after stanza removal)
    assert result.strip() == user_content.strip()
    # No markers remain
    assert BEGIN not in result
    assert END not in result


def test_remove_stanza_exact_removal_multiblock_context(tmp_path):
    """Only the kata block is removed; other content at both sides is intact."""
    agents_md = tmp_path / "AGENTS.md"
    header = "# Header\n\nSome preamble.\n"
    footer = "\n## Footer\n\nEnd of file.\n"
    agents_md.write_text(header + footer, encoding="utf-8")
    kata_router.write_stanza(str(agents_md))

    kata_router.remove_stanza(str(agents_md))

    content = agents_md.read_text(encoding="utf-8")
    assert header in content, "Header content was altered"
    assert footer.strip() in content, "Footer content was altered"
    assert BEGIN not in content
    assert END not in content


# ---------------------------------------------------------------------------
# remove_stanza — no-op paths (mutation-proof: removing no-op guard causes crash)
# ---------------------------------------------------------------------------


def test_remove_stanza_noop_when_no_block(tmp_path):
    """remove_stanza must not crash and must leave the file unchanged when no block exists."""
    agents_md = tmp_path / "AGENTS.md"
    original = "# My Project\n\nSome instructions.\n"
    agents_md.write_text(original, encoding="utf-8")

    kata_router.remove_stanza(str(agents_md))  # must not raise

    assert agents_md.read_text(encoding="utf-8") == original


def test_remove_stanza_noop_when_file_absent(tmp_path):
    """remove_stanza must not crash and must not create a file when none exists."""
    agents_md = tmp_path / "AGENTS.md"
    assert not agents_md.exists()

    kata_router.remove_stanza(str(agents_md))  # must not raise

    assert not agents_md.exists()


# ---------------------------------------------------------------------------
# Path-traversal guard (mutation-proof: removing the guard causes these to pass silently)
# ---------------------------------------------------------------------------


def test_safe_path_rejects_dotdot_in_write_stanza(tmp_path):
    """write_stanza must raise ValueError for a path containing '..'."""
    malicious = str(tmp_path) + "/../../../escape/AGENTS.md"
    with pytest.raises(ValueError):
        kata_router.write_stanza(malicious)


def test_safe_path_rejects_dotdot_in_remove_stanza(tmp_path):
    """remove_stanza must raise ValueError for a path containing '..'."""
    malicious = str(tmp_path) + "/../../../escape/AGENTS.md"
    with pytest.raises(ValueError):
        kata_router.remove_stanza(malicious)


def test_safe_path_accepts_normal_path_write(tmp_path):
    """A path without '..' must not be blocked."""
    agents_md = tmp_path / "subdir" / "AGENTS.md"
    kata_router.write_stanza(str(agents_md))  # must not raise
    assert agents_md.exists()


# ---------------------------------------------------------------------------
# Finding 1: Orphan begin-marker guard (data-loss prevention)
# ---------------------------------------------------------------------------


def test_write_stanza_raises_on_orphan_begin_marker(tmp_path):
    """write_stanza RAISES ValueError when the file has <!-- kata:begin --> with no end.

    Mutation-proof: changing to 'never raise' → this test fails.
    """
    agents_md = tmp_path / "AGENTS.md"
    orphan_content = "# My Project\n\n<!-- kata:begin -->\n\nSome user content.\n"
    agents_md.write_text(orphan_content, encoding="utf-8")

    with pytest.raises(ValueError, match="malformed"):
        kata_router.write_stanza(str(agents_md))


def test_write_stanza_orphan_begin_file_byte_identical(tmp_path):
    """File is byte-identical after the ValueError raise — zero data loss.

    Mutation-proof: changing to 'write then raise' → read_bytes differ.
    """
    agents_md = tmp_path / "AGENTS.md"
    orphan_content = "# Header\n<!-- kata:begin -->\norphan line\n"
    agents_md.write_text(orphan_content, encoding="utf-8")
    original_bytes = agents_md.read_bytes()

    try:
        kata_router.write_stanza(str(agents_md))
    except ValueError:
        pass

    assert agents_md.read_bytes() == original_bytes, (
        "File was mutated before the ValueError — data-loss path is open"
    )


def test_write_stanza_complete_block_still_upserts(tmp_path):
    """A complete begin..end pair still upserts in place (no regression)."""
    agents_md = tmp_path / "AGENTS.md"
    kata_router.write_stanza(str(agents_md))            # create
    kata_router.write_stanza(str(agents_md))            # upsert (must not raise)
    content = agents_md.read_text(encoding="utf-8")
    assert content.count(BEGIN) == 1
    assert content.count(END) == 1


def test_write_stanza_no_marker_still_appends(tmp_path):
    """A file with no marker at all still gets the block appended (no regression)."""
    agents_md = tmp_path / "AGENTS.md"
    agents_md.write_text("# Clean project\n", encoding="utf-8")
    kata_router.write_stanza(str(agents_md))            # must not raise
    content = agents_md.read_text(encoding="utf-8")
    assert content.count(BEGIN) == 1
    assert content.count(END) == 1


# ---------------------------------------------------------------------------
# Finding 4: render_stanza summary correctness
# ---------------------------------------------------------------------------


def test_render_stanza_with_summary_includes_text_in_body():
    """render_stanza(summary='hello marker') embeds summary text in the body.

    Mutation-proof: removing the summary-insert branch → 'hello marker' absent → fail.
    """
    stanza = kata_router.render_stanza(summary="hello marker")
    lines = stanza.splitlines()
    begin_idx = next(i for i, ln in enumerate(lines) if ln == BEGIN)
    end_idx = next(i for i, ln in enumerate(lines) if ln == END)
    body = "\n".join(lines[begin_idx + 1 : end_idx])

    assert "hello marker" in body, (
        f"Summary text 'hello marker' not found in body:\n{body}"
    )
    # Base body is 17 lines; one summary line is inserted → ≤18 (the ~15 budget)
    assert len(lines[begin_idx + 1 : end_idx]) <= 18, (
        f"Body exceeds budget with summary: {len(lines[begin_idx + 1 : end_idx])} lines"
    )
