"""test_kata_supersede.py — TDD for C1: supersedes / fork precedence resolver.

Task C1 of install-update-polish/PLAN.md.
DESIGN §7 (supersede precedence, validate_shadows, toolkit/agentSkills.dir).

Coverage:
- resolve_shadows: promoted fork with supersedes: resolves to {upstream: fork_dir}
- resolve_shadows: candidate in candidates/ dir is IGNORED (only skills/ shadows)
- resolve_shadows: fork with no supersedes field → not in result
- resolve_shadows: fork with empty supersedes (supersedes: []) → not in result
- resolve_shadows: absent/None agentskills_dir → {} (no-op, BC)
- resolve_shadows: missing directory path → {} (no-op)
- resolve_shadows: multiple forks each with different supersedes → all resolve
- resolve_shadows: two forks same upstream → _CONFLICT_PATH sentinel
- resolve_shadows: inline list form (supersedes: [kata-x]) → resolves
- resolve_shadows: multiline list form (- kata-x on next line) → resolves
- resolve_shadows: path with '..' traversal → {} (guarded, fail-closed)
- validate_shadows: valid single shadow → []
- validate_shadows: unknown upstream (not in base_names) → ERROR
- validate_shadows: conflict sentinel (two forks same upstream) → ERROR
- validate_shadows: empty shadows → []
- validate_shadows: multiple errors reported (one per problem)
- validate_shadows: conflict entry skips unknown-upstream check (no double-error)
- No subprocess / git import in kata_supersede.py (DESIGN Invariant 3)
- No yaml import in kata_supersede.py (stdlib-only invariant)
- Clean-interpreter subprocess guard: importing kata_supersede loads NO yaml
"""

from __future__ import annotations

from pathlib import Path

import pytest

import kata_supersede as ks
from kata_supersede import _CONFLICT_PATH, resolve_shadows, validate_shadows

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_skill(parent: Path, *, supersedes: str | None = None, extra: str = "") -> Path:
    """Write a minimal SKILL.md under *parent* and return *parent*.

    ``supersedes`` is written as-is (raw YAML value string) when provided.
    Pass ``extra`` to include additional raw frontmatter lines.
    """
    fm_lines = ["---", "name: test-skill", "version: 0.1.0"]
    if supersedes is not None:
        fm_lines.append(f"supersedes: {supersedes}")
    if extra:
        fm_lines.append(extra)
    fm_lines += ["---", "", "Skill body.", ""]
    skill_text = "\n".join(fm_lines)
    parent.mkdir(parents=True, exist_ok=True)
    (parent / "SKILL.md").write_text(skill_text, encoding="utf-8")
    return parent


def _make_skill_multiline_supersedes(parent: Path, upstream: str) -> Path:
    """Write a SKILL.md with a multi-line YAML list for supersedes."""
    skill_text = (
        "---\n"
        "name: test-skill\n"
        "version: 0.1.0\n"
        "supersedes:\n"
        f"- {upstream}\n"
        "---\n"
        "\n"
        "Skill body.\n"
    )
    parent.mkdir(parents=True, exist_ok=True)
    (parent / "SKILL.md").write_text(skill_text, encoding="utf-8")
    return parent


# ---------------------------------------------------------------------------
# TestResolveShadows
# ---------------------------------------------------------------------------


class TestResolveShadows:
    """resolve_shadows(agentskills_dir) -> dict[str, Path]

    Scans <agentskills_dir>/skills/**/SKILL.md (NOT candidates/).
    Returns {upstream_name: fork_dir} for every promoted skill with a non-empty
    supersedes field.
    """

    # --- None / absent dir cases -------------------------------------------

    def test_none_agentskills_dir_returns_empty(self) -> None:
        """None agentskills_dir → {} (no-op, BC — common case for an un-configured toolkit)."""
        assert resolve_shadows(None) == {}

    def test_missing_directory_returns_empty(self, tmp_path: Path) -> None:
        """Path to a non-existent directory → {} (no-op)."""
        missing = tmp_path / "nonexistent_toolkit"
        assert resolve_shadows(missing) == {}

    def test_directory_with_no_skills_subdir_returns_empty(self, tmp_path: Path) -> None:
        """agentskills_dir exists but has no skills/ subdir → {}."""
        (tmp_path / "candidates").mkdir()
        assert resolve_shadows(tmp_path) == {}

    # --- Core: promoted fork with supersedes --------------------------------

    def test_promoted_fork_with_supersedes_resolves(self, tmp_path: Path) -> None:
        """A promoted skill in skills/ with supersedes: kata-review → {kata-review: dir}."""
        fork_dir = tmp_path / "skills" / "meta" / "my-fork"
        _make_skill(fork_dir, supersedes="kata-review")

        result = resolve_shadows(tmp_path)

        assert "kata-review" in result
        assert result["kata-review"] == fork_dir

    def test_fork_dir_path_is_absolute(self, tmp_path: Path) -> None:
        """The fork_dir path in the result is absolute (resolved by _safe_abs)."""
        fork_dir = tmp_path / "skills" / "meta" / "my-fork"
        _make_skill(fork_dir, supersedes="kata-target")

        result = resolve_shadows(tmp_path)

        assert result["kata-target"].is_absolute()

    def test_fork_dir_points_to_parent_of_skill_md(self, tmp_path: Path) -> None:
        """fork_dir is the directory containing SKILL.md, not the SKILL.md file itself."""
        fork_dir = tmp_path / "skills" / "execute" / "my-fork"
        _make_skill(fork_dir, supersedes="kata-target")

        result = resolve_shadows(tmp_path)

        assert result["kata-target"] == fork_dir
        assert (result["kata-target"] / "SKILL.md").exists()

    # --- Candidates directory is IGNORED ------------------------------------

    def test_candidate_fork_is_ignored(self, tmp_path: Path) -> None:
        """A fork under candidates/ is sandboxed and NEVER shadows upstream skills."""
        cand_dir = tmp_path / "candidates" / "my-fork"
        _make_skill(cand_dir, supersedes="kata-review")

        result = resolve_shadows(tmp_path)

        assert result == {}

    def test_candidates_ignored_even_with_skills_dir_present(self, tmp_path: Path) -> None:
        """When both candidates/ and skills/ exist, only skills/ forks shadow."""
        # Candidate: should be ignored.
        cand_dir = tmp_path / "candidates" / "cand-fork"
        _make_skill(cand_dir, supersedes="kata-cand-target")

        # Promoted skill: should shadow.
        prom_dir = tmp_path / "skills" / "meta" / "prom-fork"
        _make_skill(prom_dir, supersedes="kata-plan")

        result = resolve_shadows(tmp_path)

        assert "kata-cand-target" not in result
        assert "kata-plan" in result
        assert result["kata-plan"] == prom_dir

    # --- No / empty supersedes → no shadow ----------------------------------

    def test_fork_without_supersedes_does_not_shadow(self, tmp_path: Path) -> None:
        """A promoted fork with no supersedes field at all → not in shadow map."""
        fork_dir = tmp_path / "skills" / "meta" / "brand-new"
        _make_skill(fork_dir)  # no supersedes argument

        result = resolve_shadows(tmp_path)

        assert result == {}

    def test_fork_with_empty_list_supersedes_does_not_shadow(self, tmp_path: Path) -> None:
        """supersedes: [] → empty list → not in shadow map."""
        fork_dir = tmp_path / "skills" / "meta" / "my-skill"
        _make_skill(fork_dir, supersedes="[]")

        result = resolve_shadows(tmp_path)

        assert result == {}

    def test_fork_with_blank_supersedes_does_not_shadow(self, tmp_path: Path) -> None:
        """supersedes: (blank inline value, no list continuation) → not in shadow map."""
        # Write a SKILL.md with a blank supersedes line and no continuation.
        skill_text = "---\nname: test\nsupersedes:\n---\n\nBody.\n"
        fork_dir = tmp_path / "skills" / "meta" / "blank-super"
        fork_dir.mkdir(parents=True)
        (fork_dir / "SKILL.md").write_text(skill_text, encoding="utf-8")

        result = resolve_shadows(tmp_path)

        assert result == {}

    # --- Inline list form ---------------------------------------------------

    def test_inline_list_supersedes_resolves(self, tmp_path: Path) -> None:
        """supersedes: [kata-review] (inline list) → resolves."""
        fork_dir = tmp_path / "skills" / "meta" / "list-fork"
        _make_skill(fork_dir, supersedes="[kata-review]")

        result = resolve_shadows(tmp_path)

        assert "kata-review" in result
        assert result["kata-review"] == fork_dir

    # --- Multi-line list form -----------------------------------------------

    def test_multiline_list_supersedes_resolves(self, tmp_path: Path) -> None:
        """supersedes:\\n- kata-review (multi-line YAML list) → resolves."""
        fork_dir = tmp_path / "skills" / "meta" / "multiline-fork"
        _make_skill_multiline_supersedes(fork_dir, "kata-review")

        result = resolve_shadows(tmp_path)

        assert "kata-review" in result
        assert result["kata-review"] == fork_dir

    # --- Multiple forks, different upstreams --------------------------------

    def test_multiple_forks_different_upstreams_all_resolve(self, tmp_path: Path) -> None:
        """Multiple promoted forks each targeting a different upstream → all appear."""
        pairs = [
            ("fork-a", "kata-plan"),
            ("fork-b", "kata-review"),
            ("fork-c", "kata-evaluate"),
        ]
        expected: dict[str, Path] = {}
        for dir_name, upstream in pairs:
            fork_dir = tmp_path / "skills" / "meta" / dir_name
            _make_skill(fork_dir, supersedes=upstream)
            expected[upstream] = fork_dir

        result = resolve_shadows(tmp_path)

        assert result == expected

    def test_nested_skills_dir_structure_resolved(self, tmp_path: Path) -> None:
        """Skills nested more than one level deep under skills/ are still found."""
        fork_dir = tmp_path / "skills" / "execute" / "level2" / "deep-fork"
        _make_skill(fork_dir, supersedes="kata-deep-target")

        result = resolve_shadows(tmp_path)

        assert "kata-deep-target" in result
        assert result["kata-deep-target"] == fork_dir

    # --- Conflict: two forks same upstream ----------------------------------

    def test_two_forks_same_upstream_returns_conflict_sentinel(
        self, tmp_path: Path
    ) -> None:
        """Two promoted forks both with supersedes: kata-review → _CONFLICT_PATH sentinel."""
        for name in ("fork-alpha", "fork-beta"):
            fork_dir = tmp_path / "skills" / "meta" / name
            _make_skill(fork_dir, supersedes="kata-review")

        result = resolve_shadows(tmp_path)

        assert "kata-review" in result
        assert result["kata-review"] == _CONFLICT_PATH

    def test_two_forks_same_upstream_validated_as_error(self, tmp_path: Path) -> None:
        """Full pipeline: two forks same upstream → validate_shadows returns an ERROR."""
        for name in ("fork-one", "fork-two"):
            fork_dir = tmp_path / "skills" / "meta" / name
            _make_skill(fork_dir, supersedes="kata-review")

        shadows = resolve_shadows(tmp_path)
        errors = validate_shadows(shadows, {"kata-review"})

        assert len(errors) >= 1
        assert any("kata-review" in e for e in errors)

    # --- Path safety --------------------------------------------------------

    def test_path_with_dotdot_traversal_returns_empty(self) -> None:
        """A path with '..' traversal is rejected (CWE-23 guard) → {}."""
        assert resolve_shadows(Path("..") / "some" / "dir") == {}

    # --- Unreadable SKILL.md ----------------------------------------------------------------

    def test_skills_dir_with_no_skill_md_ignored(self, tmp_path: Path) -> None:
        """A skills/ dir containing no SKILL.md files → {}."""
        (tmp_path / "skills" / "meta").mkdir(parents=True)
        # No SKILL.md files written.
        assert resolve_shadows(tmp_path) == {}


# ---------------------------------------------------------------------------
# TestValidateShadows
# ---------------------------------------------------------------------------


class TestValidateShadows:
    """validate_shadows(shadows, base_names) -> list[str]

    Fail-closed structural check.  Empty list = all shadows valid.
    (a) Unknown upstream (not in base_names) → ERROR.
    (b) Conflict sentinel (_CONFLICT_PATH) → ERROR.
    """

    def test_empty_shadows_returns_no_errors(self) -> None:
        """Empty shadows dict → [] (nothing to validate)."""
        assert validate_shadows({}, {"kata-review", "kata-plan"}) == []

    def test_valid_single_shadow_returns_no_errors(self, tmp_path: Path) -> None:
        """A single valid shadow (upstream in base_names, no conflict) → []."""
        fork_dir = tmp_path / "fork"
        fork_dir.mkdir()
        shadows = {"kata-review": fork_dir}
        base_names = {"kata-review", "kata-plan", "kata-evaluate"}

        errors = validate_shadows(shadows, base_names)

        assert errors == []

    def test_valid_multiple_shadows_returns_no_errors(self, tmp_path: Path) -> None:
        """Multiple valid shadows → []."""
        fork_a = tmp_path / "fork-a"
        fork_b = tmp_path / "fork-b"
        fork_a.mkdir()
        fork_b.mkdir()
        shadows = {"kata-plan": fork_a, "kata-review": fork_b}
        base_names = {"kata-plan", "kata-review", "kata-evaluate"}

        assert validate_shadows(shadows, base_names) == []

    # --- Case (a): unknown upstream ----------------------------------------

    def test_unknown_upstream_returns_error(self, tmp_path: Path) -> None:
        """supersedes target not in base_names → ERROR with the unknown name."""
        fork_dir = tmp_path / "fork"
        fork_dir.mkdir()
        shadows = {"kata-nonexistent": fork_dir}
        base_names = {"kata-review", "kata-plan"}

        errors = validate_shadows(shadows, base_names)

        assert len(errors) == 1
        assert "kata-nonexistent" in errors[0]

    def test_multiple_unknown_upstreams_all_reported(self, tmp_path: Path) -> None:
        """Each unknown upstream produces a separate ERROR string."""
        fork_a = tmp_path / "fork-a"
        fork_b = tmp_path / "fork-b"
        fork_a.mkdir()
        fork_b.mkdir()
        shadows = {"kata-ghost-a": fork_a, "kata-ghost-b": fork_b}
        base_names = {"kata-review"}

        errors = validate_shadows(shadows, base_names)

        assert len(errors) == 2
        unknown_names = {e for e in errors}
        assert any("kata-ghost-a" in e for e in errors)
        assert any("kata-ghost-b" in e for e in errors)
        del unknown_names  # suppress unused warning

    def test_known_upstream_not_an_error(self, tmp_path: Path) -> None:
        """A shadow whose upstream IS in base_names → no error for that entry."""
        fork_dir = tmp_path / "fork"
        fork_dir.mkdir()
        shadows = {"kata-review": fork_dir}
        base_names = {"kata-review"}

        assert validate_shadows(shadows, base_names) == []

    # --- Case (b): conflict sentinel ----------------------------------------

    def test_conflict_sentinel_returns_error(self) -> None:
        """_CONFLICT_PATH sentinel in shadows → ERROR for ambiguous double-supersede."""
        shadows = {"kata-review": _CONFLICT_PATH}
        base_names = {"kata-review"}

        errors = validate_shadows(shadows, base_names)

        assert len(errors) == 1
        assert "kata-review" in errors[0]

    def test_conflict_sentinel_error_mentions_conflict(self) -> None:
        """The ERROR string for a conflict is informative (contains 'conflict' or 'multiple')."""
        shadows = {"kata-target": _CONFLICT_PATH}
        errors = validate_shadows(shadows, {"kata-target"})

        assert any(
            word in errors[0].lower() for word in ("conflict", "multiple", "ambiguous")
        )

    def test_conflict_sentinel_skips_unknown_upstream_check(self) -> None:
        """A conflicting entry whose upstream is also unknown → only ONE error (conflict wins)."""
        # The upstream is NOT in base_names, AND the entry has the conflict sentinel.
        # We should get exactly one error (the conflict), not two (conflict + unknown).
        shadows = {"kata-ghost": _CONFLICT_PATH}
        base_names = {"kata-review"}  # kata-ghost NOT present

        errors = validate_shadows(shadows, base_names)

        # Only the conflict error — the 'continue' in validate_shadows skips the unknown check.
        assert len(errors) == 1
        assert "kata-ghost" in errors[0]

    def test_mixed_valid_conflict_unknown_all_reported(self, tmp_path: Path) -> None:
        """Mix of valid, unknown, and conflicting entries → each problem reported."""
        fork_ok = tmp_path / "fork-ok"
        fork_ok.mkdir()
        shadows = {
            "kata-ok": fork_ok,            # valid
            "kata-unknown": fork_ok,       # unknown upstream
            "kata-conflict": _CONFLICT_PATH,  # conflict
        }
        base_names = {"kata-ok"}  # kata-unknown NOT in base_names

        errors = validate_shadows(shadows, base_names)

        # Should have errors for kata-unknown and kata-conflict.
        assert len(errors) == 2
        assert any("kata-unknown" in e for e in errors)
        assert any("kata-conflict" in e for e in errors)

    # --- base_names as various iterables -----------------------------------

    def test_base_names_as_list(self, tmp_path: Path) -> None:
        """base_names can be a list (not just a set)."""
        fork_dir = tmp_path / "fork"
        fork_dir.mkdir()
        shadows = {"kata-review": fork_dir}

        assert validate_shadows(shadows, ["kata-review", "kata-plan"]) == []

    def test_base_names_as_empty_set_reports_all_unknown(self, tmp_path: Path) -> None:
        """Empty base_names → every shadow is unknown → one error per entry."""
        fork_dir = tmp_path / "fork"
        fork_dir.mkdir()
        shadows = {"kata-review": fork_dir, "kata-plan": fork_dir}

        errors = validate_shadows(shadows, set())

        assert len(errors) == 2


# ---------------------------------------------------------------------------
# TestNoGitNoSubprocess
# ---------------------------------------------------------------------------


class TestNoGitNoSubprocess:
    """kata_supersede must not import subprocess or git (DESIGN Invariant 3)."""

    def test_module_source_does_not_import_subprocess(self) -> None:
        source = Path(ks.__file__).read_text(encoding="utf-8")
        # The implementation should never import subprocess.
        # (Tests use subprocess, but the module under test must not.)
        assert "import subprocess" not in source

    def test_module_source_does_not_import_git(self) -> None:
        source = Path(ks.__file__).read_text(encoding="utf-8")
        assert "import git" not in source


# ---------------------------------------------------------------------------
# TestNoYaml — stdlib-only invariant (install/materialize path has no pyyaml)
# ---------------------------------------------------------------------------


class TestNoYaml:
    """kata_supersede MUST be stdlib-only.

    The install/update path runs under a plain ``python`` with NO pyyaml
    installed.  Importing yaml (directly or transitively via validate_skills,
    which imports yaml at module top) would make kata_install's
    import-guarded _materialize_pass silently no-op in a real install —
    fork bodies would never be installed.
    """

    def test_module_source_has_no_yaml_import(self) -> None:
        source = Path(ks.__file__).read_text(encoding="utf-8")
        assert "import yaml" not in source, "kata_supersede must never import yaml"

    def test_module_source_does_not_import_validate_skills(self) -> None:
        """validate_skills imports yaml at module top — kata_supersede must never
        import it (even indirectly), or yaml would be pulled in transitively."""
        source = Path(ks.__file__).read_text(encoding="utf-8")
        assert "import validate_skills" not in source
        assert "from validate_skills" not in source

    def test_importing_kata_supersede_does_not_load_yaml(self) -> None:
        """In a CLEAN interpreter, importing kata_supersede must not pull yaml into
        sys.modules.  Run in a subprocess because this test process may already have
        imported yaml (via validate_skills or other test fixtures)."""
        import subprocess
        import sys

        tools_dir = Path(ks.__file__).resolve().parent
        code = (
            "import sys; "
            "import kata_supersede; "
            "assert 'yaml' not in sys.modules, "
            "'kata_supersede import pulled yaml into sys.modules'"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(tools_dir),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"clean import of kata_supersede loaded yaml or failed:\n"
            f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
        )
