"""Tests for _link_or_copy_file and _flat_link_commands (commands install, A1-b).

All tests use tmp dirs + fixtures — no real ~/.claude or adapters/ files touched.
The real adapters/claude/commands/ directory is deliberately NOT used; fixture files
in tmp dirs substitute so the tests are fully isolated.

Coverage
--------
- _link_or_copy_file: links (or copies) a file; idempotent on re-run
- _link_or_copy_file: policy (b) — skips a pre-existing non-kata file with NOTE
- _link_or_copy_file: replaces an owned symlink pointing into the harness home
- _link_or_copy_file: replaces a file recorded in the manifest (managed_names)
- _link_or_copy_file: falls back to shutil.copy2 when os.symlink is denied
- manifest round-trip: install writes manifest; second install is idempotent; uninstall removes exactly ours
- _flat_link_commands: links all *.md from fixture adapters/claude/commands/ into host/commands/
- _flat_link_commands: returns expected shape (commandsDir, linked, method)
- _flat_link_commands: no-op (empty linked) when adapters/claude/commands/ is absent
- _flat_link_commands: skips pre-existing non-kata files with NOTE; user file intact
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import kata_install as ki


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_home_with_commands(tmp_path):
    """A minimal harness home with adapters/claude/commands/*.md fixture files.

    Creates three fixture command files so _flat_link_commands has something to link.
    Deliberately does NOT depend on the real adapters/claude/commands/ directory.
    """
    home = tmp_path / "KataHarness"
    cmds_dir = home / "adapters" / "claude" / "commands"
    cmds_dir.mkdir(parents=True)
    for name in ("kata-alpha", "kata-beta", "kata-gamma"):
        (cmds_dir / f"{name}.md").write_text(
            f"---\ndescription: {name} fixture command\n---\n# {name}\ncontent\n",
            encoding="utf-8",
        )
    return home


@pytest.fixture()
def host_dir(tmp_path):
    """Simulates ~/.claude (an existing host config directory)."""
    h = tmp_path / "dot-claude"
    h.mkdir()
    return h


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_src_in_home(home: Path, name: str = "kata-test.md", content: str = "# test\n") -> Path:
    """Create a fixture command file inside home/adapters/claude/commands/."""
    src = home / "adapters" / "claude" / "commands" / name
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(content, encoding="utf-8")
    return src


# ---------------------------------------------------------------------------
# Tests: _link_or_copy_file
# ---------------------------------------------------------------------------


class TestLinkOrCopyFile:

    def test_links_or_copies_file_into_dest(self, tmp_path):
        """_link_or_copy_file creates a link (or copy) of the source at the destination."""
        home = tmp_path / "home"
        home.mkdir()
        src = _make_src_in_home(home, "kata-foo.md")
        dst = tmp_path / "commands" / "kata-foo.md"
        dst.parent.mkdir(parents=True, exist_ok=True)

        method = ki._link_or_copy_file(src, dst, home, set())

        assert method in ("symlink", "copy"), f"unexpected method: {method!r}"
        assert dst.exists()
        assert dst.read_text(encoding="utf-8") == "# test\n"

    def test_idempotent_on_rerun(self, tmp_path):
        """Second call with the same src/dst succeeds without error (idempotent)."""
        home = tmp_path / "home"
        home.mkdir()
        src = _make_src_in_home(home, "kata-foo.md", "v1")
        dst = tmp_path / "commands" / "kata-foo.md"
        dst.parent.mkdir(parents=True, exist_ok=True)

        m1 = ki._link_or_copy_file(src, dst, home, set())
        assert m1 in ("symlink", "copy")

        # Second call: dst now exists (symlink → owned by home; copy → in managed_names)
        m2 = ki._link_or_copy_file(src, dst, home, {"kata-foo.md"})
        assert m2 in ("symlink", "copy"), "second call must succeed (idempotent)"
        assert dst.read_text(encoding="utf-8") == "v1"

    def test_policy_b_skips_non_kata_file(self, tmp_path, capsys):
        """Policy (b): pre-existing file not in managed_names is NOT overwritten; NOTE emitted."""
        home = tmp_path / "home"
        home.mkdir()
        src = _make_src_in_home(home, "kata-foo.md", "NEW CONTENT")
        dst = tmp_path / "commands" / "kata-foo.md"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text("USER CONTENT", encoding="utf-8")  # user's own file

        result = ki._link_or_copy_file(src, dst, home, set())  # not in managed_names

        assert result is None, "non-kata file must be skipped (return None)"
        assert dst.read_text(encoding="utf-8") == "USER CONTENT", "user file must be intact"
        captured = capsys.readouterr()
        assert "NOTE" in captured.out, "a NOTE must be printed when skipping"

    def test_replaces_owned_symlink_into_home(self, tmp_path):
        """A symlink whose resolved target is under harness_home is replaced (policy a)."""
        home = tmp_path / "home"
        home.mkdir()
        src = _make_src_in_home(home, "kata-foo.md", "v1")
        dst = tmp_path / "commands" / "kata-foo.md"
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Manually create the symlink so the test controls the initial state.
        try:
            os.symlink(src, dst)
        except OSError:
            pytest.skip("symlinks not supported on this platform — skipping symlink-ownership test")

        # Update source content; re-call should replace the symlink without error.
        src.write_text("v2", encoding="utf-8")
        method = ki._link_or_copy_file(src, dst, home, set())

        assert method in ("symlink", "copy"), "should succeed when replacing an owned symlink"
        assert dst.read_text(encoding="utf-8") == "v2"

    def test_replaces_file_recorded_in_managed_names(self, tmp_path):
        """A file whose name is in managed_names is replaced (policy a) even if it is a plain file."""
        home = tmp_path / "home"
        home.mkdir()
        src = _make_src_in_home(home, "kata-foo.md", "NEW")
        dst = tmp_path / "commands" / "kata-foo.md"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text("OLD", encoding="utf-8")

        method = ki._link_or_copy_file(src, dst, home, {"kata-foo.md"})

        assert method in ("symlink", "copy")
        assert dst.read_text(encoding="utf-8") == "NEW"

    def test_copy_fallback_when_symlink_denied(self, tmp_path, monkeypatch):
        """Falls back to shutil.copy2 when os.symlink raises OSError (e.g. Windows without dev mode)."""
        home = tmp_path / "home"
        home.mkdir()
        src = _make_src_in_home(home, "kata-foo.md", "content")
        dst = tmp_path / "commands" / "kata-foo.md"
        dst.parent.mkdir(parents=True, exist_ok=True)

        def _deny(*args, **kwargs):
            raise OSError("symlinks denied on this platform")

        monkeypatch.setattr(ki.os, "symlink", _deny)
        method = ki._link_or_copy_file(src, dst, home, set())

        assert method == "copy", "must fall back to copy when symlink raises OSError"
        assert dst.read_text(encoding="utf-8") == "content"


# ---------------------------------------------------------------------------
# Tests: manifest round-trip
# ---------------------------------------------------------------------------


class TestManifestRoundTrip:
    """Install writes manifest; second install is idempotent; manifest-driven removal
    removes exactly what KataHarness placed and nothing else."""

    def test_install_writes_manifest(self, fake_home_with_commands, host_dir):
        """After _flat_link_commands, the manifest records all linked command filenames."""
        ki._flat_link_commands(fake_home_with_commands, host_dir)

        manifest_path = host_dir / ki._COMMANDS_MANIFEST
        assert manifest_path.exists(), "manifest must be written after install"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert "managed" in data
        assert set(data["managed"]) == {
            "kata-alpha.md",
            "kata-beta.md",
            "kata-gamma.md",
        }, f"unexpected manifest contents: {data['managed']}"

    def test_second_install_is_idempotent(self, fake_home_with_commands, host_dir):
        """Running _flat_link_commands twice yields the same manifest (idempotent)."""
        ki._flat_link_commands(fake_home_with_commands, host_dir)
        manifest_path = host_dir / ki._COMMANDS_MANIFEST
        data1 = json.loads(manifest_path.read_text(encoding="utf-8"))

        ki._flat_link_commands(fake_home_with_commands, host_dir)
        data2 = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert set(data1["managed"]) == set(data2["managed"]), (
            "manifest must be identical after a second install"
        )

    def test_manifest_driven_removal_removes_only_kata_files(
        self, fake_home_with_commands, host_dir
    ):
        """Manifest-driven removal removes exactly the files KataHarness placed, nothing else."""
        ki._flat_link_commands(fake_home_with_commands, host_dir)
        commands_dir = host_dir / "commands"

        # Simulate a user file installed by a different tool — must NOT be touched.
        user_file = commands_dir / "user-own-command.md"
        user_file.write_text("user content — must survive", encoding="utf-8")

        # Perform manifest-driven removal (simulates what an uninstall would do).
        manifest_path = host_dir / ki._COMMANDS_MANIFEST
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        removed = []
        for fname in data["managed"]:
            target = commands_dir / fname
            if target.exists() or target.is_symlink():
                target.unlink()
                removed.append(fname)
        manifest_path.write_text(
            json.dumps({"managed": []}, indent=2) + "\n", encoding="utf-8"
        )

        # All kata-placed files are gone.
        assert not (commands_dir / "kata-alpha.md").exists()
        assert not (commands_dir / "kata-beta.md").exists()
        assert not (commands_dir / "kata-gamma.md").exists()
        assert len(removed) == 3, f"expected 3 removed, got {removed}"

        # User file is intact.
        assert user_file.read_text(encoding="utf-8") == "user content — must survive"


# ---------------------------------------------------------------------------
# Tests: _flat_link_commands
# ---------------------------------------------------------------------------


class TestFlatLinkCommands:

    def test_links_all_fixture_commands_into_host_commands_dir(
        self, fake_home_with_commands, host_dir
    ):
        """_flat_link_commands links every *.md from adapters/claude/commands/ into host/commands/."""
        res = ki._flat_link_commands(fake_home_with_commands, host_dir)

        commands_dir = host_dir / "commands"
        for name in ("kata-alpha.md", "kata-beta.md", "kata-gamma.md"):
            assert (commands_dir / name).exists(), f"expected command file missing: {name}"

        assert sorted(res["linked"]) == ["kata-alpha.md", "kata-beta.md", "kata-gamma.md"]

    def test_returns_expected_result_shape(self, fake_home_with_commands, host_dir):
        """_flat_link_commands returns a dict with commandsDir, linked, and method keys."""
        res = ki._flat_link_commands(fake_home_with_commands, host_dir)

        assert "commandsDir" in res, "missing 'commandsDir' key"
        assert "linked" in res, "missing 'linked' key"
        assert "method" in res, "missing 'method' key"
        assert isinstance(res["linked"], list)
        assert isinstance(res["method"], list)
        assert len(res["method"]) >= 1, "method list must be non-empty when files are linked"

    def test_no_commands_dir_returns_empty_linked(self, tmp_path, host_dir):
        """When adapters/claude/commands/ is absent, _flat_link_commands returns empty linked list."""
        home = tmp_path / "EmptyHome"
        home.mkdir()

        res = ki._flat_link_commands(home, host_dir)

        assert res["linked"] == [], "linked must be empty when source commands dir is absent"

    def test_skips_preexisting_user_file_with_note(
        self, fake_home_with_commands, host_dir, capsys
    ):
        """A pre-existing non-kata file at a command slot is not overwritten; NOTE is printed."""
        commands_dir = host_dir / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)
        victim = commands_dir / "kata-alpha.md"
        victim.write_text("USER DATA — must survive", encoding="utf-8")

        ki._flat_link_commands(fake_home_with_commands, host_dir)

        # User file must be intact.
        assert victim.read_text(encoding="utf-8") == "USER DATA — must survive"
        # A NOTE must have been printed.
        captured = capsys.readouterr()
        assert "NOTE" in captured.out, "expected a NOTE about the skipped file"
        # Other (non-conflicting) commands were still linked.
        assert (commands_dir / "kata-beta.md").exists()
        assert (commands_dir / "kata-gamma.md").exists()
