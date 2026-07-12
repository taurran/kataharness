"""Tests for kata_version.py — version stamp + content-hash manifest (DESIGN §5, A1 TDD gate).

TDD targets (from PLAN.md §A1):
- stamp write→read round-trips (including gitSha:"unknown")
- manifest hashes stable across two computes on unchanged tree
- manifest covered set matches iter_skill_dirs semantics (no skill missing/extra)
- is_pristine returns True on verbatim base, False after a single content change
- write_stamp/whole module never shells out: no subprocess import, no git import
- corrupt stamp/manifest → lenient {} on read, not a crash
- ..–guard: stamp_path/manifest_path reject paths containing ".."
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import kata_version as kv

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_home(tmp_path):
    """Minimal harness home with two nested skills + one module skill."""
    home = tmp_path / "KataHarness"
    # skills/coordinate/kata-bootstrap
    s1 = home / "skills" / "coordinate" / "kata-bootstrap"
    s1.mkdir(parents=True)
    (s1 / "SKILL.md").write_text(
        "---\nname: kata-bootstrap\ntags: [meta]\n---\nbody line 1\n",
        encoding="utf-8",
    )
    # skills/plan/kata-grill-standard
    s2 = home / "skills" / "plan" / "kata-grill-standard"
    s2.mkdir(parents=True)
    (s2 / "SKILL.md").write_text(
        "---\nname: kata-grill-standard\ntags: [plan]\n---\nbody line 2\n",
        encoding="utf-8",
    )
    # modules/closeout/kata-closeout
    m1 = home / "modules" / "closeout" / "kata-closeout"
    m1.mkdir(parents=True)
    (m1 / "SKILL.md").write_text(
        "---\nname: kata-closeout\ntags: [module]\n---\nmodule body\n",
        encoding="utf-8",
    )
    # README with an extractable version token
    (home / "README.md").write_text(
        "# KataHarness v0.1.0-alpha.3\n\nSome description.\n",
        encoding="utf-8",
    )
    return home


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


class TestPathHelpers:
    def test_stamp_path_location(self, fake_home):
        assert kv.stamp_path(fake_home) == fake_home / ".kata-version"

    def test_manifest_path_location(self, fake_home):
        assert kv.manifest_path(fake_home) == fake_home / ".kata-manifest.json"

    def test_stamp_path_rejects_dotdot(self, tmp_path):
        """Paths containing '..' must be refused (CWE-23 guard)."""
        with pytest.raises(ValueError, match=r"\.\."):
            kv.stamp_path(str(tmp_path) + "/../evil")

    def test_manifest_path_rejects_dotdot(self, tmp_path):
        with pytest.raises(ValueError, match=r"\.\."):
            kv.manifest_path(str(tmp_path) + "/../evil")


# ---------------------------------------------------------------------------
# Stamp round-trips
# ---------------------------------------------------------------------------


class TestStampRoundTrip:
    _SHA = "a" * 40  # 40-hex placeholder

    def test_write_stamp_basic(self, fake_home):
        kv.write_stamp(
            fake_home,
            git_sha=self._SHA,
            suite_semver="0.1.0",
            ref="master",
            link_mode="symlink",
            platform="claude",
        )
        stamp = kv.read_stamp(fake_home)
        assert stamp["schema"] == 1
        assert stamp["gitSha"] == self._SHA
        assert stamp["suiteSemver"] == "0.1.0"
        assert stamp["ref"] == "master"
        assert stamp["linkMode"] == "symlink"
        assert stamp["platform"] == "claude"
        assert "installedAt" in stamp

    def test_write_stamp_unknown_sha(self, fake_home):
        """gitSha='unknown' is a valid schema value for plain installs (no bootstrap)."""
        kv.write_stamp(
            fake_home,
            git_sha="unknown",
            suite_semver="0.1.0",
            ref="master",
            link_mode="copy",
            platform="claude",
        )
        stamp = kv.read_stamp(fake_home)
        assert stamp["gitSha"] == "unknown"
        assert stamp["linkMode"] == "copy"

    def test_write_stamp_mixed_link_mode(self, fake_home):
        kv.write_stamp(
            fake_home,
            git_sha="unknown",
            suite_semver="0.1.0",
            ref="master",
            link_mode="mixed",
            platform="kiro",
        )
        assert kv.read_stamp(fake_home)["linkMode"] == "mixed"
        assert kv.read_stamp(fake_home)["platform"] == "kiro"

    def test_write_stamp_returns_path(self, fake_home):
        p = kv.write_stamp(
            fake_home,
            git_sha="unknown",
            suite_semver="0.1.0",
            ref="master",
            link_mode="symlink",
            platform="claude",
        )
        assert p == kv.stamp_path(fake_home)
        assert p.exists()

    def test_write_stamp_file_is_valid_json(self, fake_home):
        kv.write_stamp(
            fake_home,
            git_sha="unknown",
            suite_semver="0.1.0",
            ref="master",
            link_mode="symlink",
            platform="claude",
        )
        raw = kv.stamp_path(fake_home).read_text(encoding="utf-8")
        data = json.loads(raw)  # must not raise
        assert isinstance(data, dict)

    def test_read_stamp_absent_returns_empty(self, fake_home):
        assert kv.read_stamp(fake_home) == {}

    def test_read_stamp_corrupt_returns_empty(self, fake_home):
        """Corrupt JSON → {} (lenient / fail-closed-but-degrade, DESIGN §5)."""
        kv.stamp_path(fake_home).write_text("not valid json!!", encoding="utf-8")
        assert kv.read_stamp(fake_home) == {}

    def test_read_stamp_truncated_returns_empty(self, fake_home):
        kv.stamp_path(fake_home).write_text("{truncated", encoding="utf-8")
        assert kv.read_stamp(fake_home) == {}

    def test_write_stamp_overwrites_existing(self, fake_home):
        kv.write_stamp(
            fake_home,
            git_sha="unknown",
            suite_semver="0.1.0",
            ref="master",
            link_mode="symlink",
            platform="claude",
        )
        kv.write_stamp(
            fake_home,
            git_sha=self._SHA,
            suite_semver="0.1.1",
            ref="v0.1.1",
            link_mode="copy",
            platform="codex",
        )
        stamp = kv.read_stamp(fake_home)
        assert stamp["gitSha"] == self._SHA
        assert stamp["suiteSemver"] == "0.1.1"


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


class TestManifest:
    def test_compute_manifest_schema(self, fake_home):
        m = kv.compute_manifest(fake_home)
        assert m["schema"] == 1
        assert "skills" in m
        assert "generatedAt" in m

    def test_compute_manifest_stable(self, fake_home):
        """Two computes on unchanged tree → identical skill hashes."""
        m1 = kv.compute_manifest(fake_home)
        m2 = kv.compute_manifest(fake_home)
        assert m1["skills"] == m2["skills"]

    def test_compute_manifest_covers_all_skills(self, fake_home):
        """Every skill (skills/ + modules/) appears — no missing, no extra."""
        m = kv.compute_manifest(fake_home)
        names = set(m["skills"].keys())
        assert names == {"kata-bootstrap", "kata-grill-standard", "kata-closeout"}

    def test_compute_manifest_sha256_matches_file(self, fake_home):
        """Stored hash == sha256(SKILL.md bytes) for each skill."""
        m = kv.compute_manifest(fake_home)
        for name, entry in m["skills"].items():
            skill_md = fake_home / entry["path"] / "SKILL.md"
            expected = hashlib.sha256(skill_md.read_bytes()).hexdigest()
            assert entry["sha256"] == expected, f"hash mismatch for {name}"

    def test_compute_manifest_path_is_relative(self, fake_home):
        """Stored path is relative (from home), not absolute."""
        m = kv.compute_manifest(fake_home)
        for name, entry in m["skills"].items():
            assert not Path(entry["path"]).is_absolute(), f"path should be relative for {name}"

    def test_compute_manifest_empty_tree(self, tmp_path):
        """A home with no skills → empty skills dict (no crash)."""
        home = tmp_path / "empty_home"
        home.mkdir()
        m = kv.compute_manifest(home)
        assert m["skills"] == {}

    def test_write_manifest_returns_path(self, fake_home):
        p = kv.write_manifest(fake_home, git_sha="unknown")
        assert p == kv.manifest_path(fake_home)
        assert p.exists()

    def test_write_read_manifest_round_trip(self, fake_home):
        kv.write_manifest(fake_home, git_sha="abc" + "0" * 37)
        manifest = kv.read_manifest(fake_home)
        assert manifest["schema"] == 1
        assert manifest["gitSha"] == "abc" + "0" * 37
        assert "skills" in manifest
        assert "generatedAt" in manifest
        assert "kata-bootstrap" in manifest["skills"]

    def test_write_manifest_unknown_git_sha(self, fake_home):
        kv.write_manifest(fake_home, git_sha="unknown")
        manifest = kv.read_manifest(fake_home)
        assert manifest["gitSha"] == "unknown"

    def test_write_manifest_file_is_valid_json(self, fake_home):
        kv.write_manifest(fake_home, git_sha="unknown")
        raw = kv.manifest_path(fake_home).read_text(encoding="utf-8")
        data = json.loads(raw)  # must not raise
        assert isinstance(data, dict)

    def test_read_manifest_absent_returns_empty(self, fake_home):
        assert kv.read_manifest(fake_home) == {}

    def test_read_manifest_corrupt_returns_empty(self, fake_home):
        kv.manifest_path(fake_home).write_text("{broken json", encoding="utf-8")
        assert kv.read_manifest(fake_home) == {}

    def test_read_manifest_truncated_returns_empty(self, fake_home):
        kv.manifest_path(fake_home).write_text("null", encoding="utf-8")
        # valid JSON but not a dict — degrade gracefully
        result = kv.read_manifest(fake_home)
        # either {} or null → caller-safe; we accept both
        assert result == {} or result is None

    def test_write_manifest_skill_coverage_matches_iter_semantics(self, fake_home):
        """Manifest coverage matches the same enumeration as iter_skill_dirs."""
        # iter_skill_dirs is the reference implementation in kata_install;
        # kata_version uses the same semantics (skills/ + modules/, rglob SKILL.md).
        # We verify by constructing expected names from the fixture tree directly.
        expected_names = set()
        for root in ("skills", "modules"):
            base = fake_home / root
            if base.is_dir():
                for skill_md in base.rglob("SKILL.md"):
                    expected_names.add(skill_md.parent.name)

        kv.write_manifest(fake_home, git_sha="unknown")
        manifest = kv.read_manifest(fake_home)
        assert set(manifest["skills"].keys()) == expected_names


# ---------------------------------------------------------------------------
# is_pristine
# ---------------------------------------------------------------------------


class TestIsPristine:
    def test_pristine_true_on_verbatim_base(self, fake_home):
        """Manifest written, file unchanged → pristine."""
        kv.write_manifest(fake_home, git_sha="unknown")
        assert kv.is_pristine(fake_home, "kata-bootstrap") is True

    def test_pristine_true_for_all_skills(self, fake_home):
        """All skills in a freshly written manifest are pristine."""
        kv.write_manifest(fake_home, git_sha="unknown")
        for name in ("kata-bootstrap", "kata-grill-standard", "kata-closeout"):
            assert kv.is_pristine(fake_home, name) is True, f"{name} should be pristine"

    def test_pristine_false_after_content_change(self, fake_home):
        """A single content change to one skill file makes it non-pristine."""
        kv.write_manifest(fake_home, git_sha="unknown")
        skill_md = fake_home / "skills" / "coordinate" / "kata-bootstrap" / "SKILL.md"
        skill_md.write_text(
            "---\nname: kata-bootstrap\ntags: [meta]\n---\nMODIFIED CONTENT\n",
            encoding="utf-8",
        )
        assert kv.is_pristine(fake_home, "kata-bootstrap") is False

    def test_pristine_false_after_change_leaves_others_true(self, fake_home):
        """Changing one skill doesn't affect the pristine status of others."""
        kv.write_manifest(fake_home, git_sha="unknown")
        skill_md = fake_home / "skills" / "coordinate" / "kata-bootstrap" / "SKILL.md"
        skill_md.write_text("---\nname: kata-bootstrap\n---\nCHANGED\n", encoding="utf-8")

        assert kv.is_pristine(fake_home, "kata-bootstrap") is False
        assert kv.is_pristine(fake_home, "kata-grill-standard") is True
        assert kv.is_pristine(fake_home, "kata-closeout") is True

    def test_pristine_false_when_no_manifest(self, fake_home):
        """No manifest file → False (fail-closed; can't confirm pristine)."""
        assert kv.is_pristine(fake_home, "kata-bootstrap") is False

    def test_pristine_false_for_unknown_name(self, fake_home):
        """A name not in the manifest → False."""
        kv.write_manifest(fake_home, git_sha="unknown")
        assert kv.is_pristine(fake_home, "nonexistent-skill") is False

    def test_pristine_false_corrupt_manifest(self, fake_home):
        """Corrupt manifest → False (degrade to safe)."""
        kv.manifest_path(fake_home).write_text("corrupted!", encoding="utf-8")
        assert kv.is_pristine(fake_home, "kata-bootstrap") is False


# ---------------------------------------------------------------------------
# suite_semver
# ---------------------------------------------------------------------------


class TestSuiteSemver:
    def test_reads_version_from_readme(self, fake_home):
        sv = kv.suite_semver(fake_home)
        # README: "# KataHarness v0.1.0-alpha.3" → token "v0.1.0-alpha.3" → strip "v" → "0.1.0-alpha.3"
        assert sv == "0.1.0-alpha.3"

    def test_default_when_no_readme(self, tmp_path):
        """No README → default '0.1.0'."""
        home = tmp_path / "no_readme"
        home.mkdir()
        assert kv.suite_semver(home) == "0.1.0"

    def test_default_when_readme_has_no_version(self, tmp_path):
        """README without a version line → default '0.1.0'."""
        home = tmp_path / "no_ver"
        home.mkdir()
        (home / "README.md").write_text("# Some title\n\nNo version here.\n", encoding="utf-8")
        assert kv.suite_semver(home) == "0.1.0"


# ---------------------------------------------------------------------------
# No-git / no-subprocess invariant (DESIGN Invariant 3 + PLAN A1 gate)
# ---------------------------------------------------------------------------


class TestNoGitNoSubprocess:
    def test_module_source_contains_no_subprocess(self):
        """kata_version must not import subprocess — it's purely git-free."""
        source = Path(kv.__file__).read_text(encoding="utf-8")
        # Check for an actual import statement, not just the word in docstrings/comments.
        assert "import subprocess" not in source, (
            "kata_version.py must never import subprocess (DESIGN Invariant 3)"
        )

    def test_module_source_contains_no_git_import(self):
        """kata_version must not import any git library."""
        source = Path(kv.__file__).read_text(encoding="utf-8")
        assert "import git" not in source, (
            "kata_version.py must never import a git library (DESIGN Invariant 3)"
        )

    def test_write_stamp_does_not_trigger_subprocess_import(self, fake_home, monkeypatch):
        """write_stamp must not cause subprocess to be imported at call time."""
        import builtins
        import sys

        # Use monkeypatch.delitem so the fixture restores sys.modules["subprocess"]
        # when the test ends — prevents cross-test pollution.
        monkeypatch.delitem(sys.modules, "subprocess", raising=False)

        triggered: list[str] = []
        original = builtins.__import__

        def spy_import(name, *args, **kwargs):
            if name == "subprocess":
                triggered.append(name)
            return original(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", spy_import)

        kv.write_stamp(
            fake_home,
            git_sha="unknown",
            suite_semver="0.1.0",
            ref="master",
            link_mode="symlink",
            platform="claude",
        )

        assert not triggered, (
            f"write_stamp imported subprocess — violates the never-git invariant: {triggered}"
        )

    def test_write_manifest_does_not_trigger_subprocess_import(self, fake_home, monkeypatch):
        """write_manifest must not cause subprocess to be imported."""
        import builtins
        import sys

        # Use monkeypatch.delitem so the fixture restores sys.modules["subprocess"]
        # when the test ends — prevents cross-test pollution.
        monkeypatch.delitem(sys.modules, "subprocess", raising=False)
        triggered: list[str] = []
        original = builtins.__import__

        def spy_import(name, *args, **kwargs):
            if name == "subprocess":
                triggered.append(name)
            return original(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", spy_import)
        kv.write_manifest(fake_home, git_sha="unknown")
        assert not triggered, f"write_manifest imported subprocess: {triggered}"
