"""test_benchmark_control.py — TDD suite for tools/benchmark_control.py (S4).

Strategy: default-FAIL (tests written before implementation; green only after
benchmark_control.py is present and correct).  Mutation-proof tests use
mutation_run.prove_non_vacuous and spawn a real subprocess.  All other tests
are pure (no I/O except tmp_path writes).

Coverage map
------------
sibling_name:
    TestSiblingName::test_sibling_name_basic
    TestSiblingName::test_sibling_name_n_zero
    TestSiblingName::test_sibling_name_large_n
    TestSiblingName::test_sibling_name_with_hyphens

next_index:
    TestNextIndex::test_next_index_empty_dir
    TestNextIndex::test_next_index_existing_siblings
    TestNextIndex::test_next_index_gap_uses_max_plus_one
    TestNextIndex::test_next_index_only_unrelated_dirs

content_hash:
    TestContentHash::test_content_hash_stable
    TestContentHash::test_content_hash_different_content
    TestContentHash::test_content_hash_path_included_in_digest
    TestContentHash::test_content_hash_file_order_invariant
    TestContentHash::test_content_hash_no_path_content_collision

detect_drift:
    TestDetectDrift::test_detect_drift_no_drift
    TestDetectDrift::test_detect_drift_with_drift
    TestDetectDrift::test_detect_drift_returns_typed_result
    TestDetectDrift::test_detect_drift_current_hash_in_result

clone_control:
    TestCloneControl::test_clone_control_copies_files
    TestCloneControl::test_clone_control_ref_untouched
    TestCloneControl::test_clone_control_refuses_source_overlap_dest_inside_src
    TestCloneControl::test_clone_control_refuses_source_overlap_src_inside_dest
    TestCloneControl::test_clone_control_refuses_equal_paths
    TestCloneControl::test_clone_control_refuses_dotdot_in_ref
    TestCloneControl::test_clone_control_refuses_dotdot_in_dest
    TestCloneControl::test_clone_control_injectable_copy_fn_called

prune:
    TestPrune::test_prune_removes_benchmark_copy
    TestPrune::test_prune_refuses_non_benchmark_name
    TestPrune::test_prune_refuses_non_digit_suffix
    TestPrune::test_prune_refuses_dotdot
    TestPrune::test_prune_refuses_nonexistent_dir
    TestPrune::test_prune_injectable_rm_fn_called

exec-safety:
    TestExecSafety::test_no_subprocess_in_benchmark_control
    TestExecSafety::test_no_eval_in_benchmark_control
    TestExecSafety::test_no_shell_true_in_benchmark_control
    TestExecSafety::test_benchmark_control_is_ast_parseable

Mutation proofs (spawn real subprocess via prove_non_vacuous):
    TestMutationProof::test_mutation_proof_ref_never_written_overlap_guard
    TestMutationProof::test_mutation_proof_detect_drift_comparison
    TestMutationProof::test_mutation_proof_content_hash_collision_fix
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Resolve the tools directory (parent of tests/) — used for imports and paths
_TESTS = Path(__file__).resolve().parent
_TOOLS = _TESTS.parent

# Add tools/ to sys.path so benchmark_control is importable without installation
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import benchmark_control  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ref(tmp_path: Path, files: dict[str, bytes]) -> Path:
    """Create a synthetic reference directory with the given file contents."""
    ref = tmp_path / "myproject"
    ref.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        dest = ref / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
    return ref


# ---------------------------------------------------------------------------
# sibling_name
# ---------------------------------------------------------------------------


class TestSiblingName:
    """Unit tests for sibling_name(base, n) → '<base>-katabenchmark<N>'."""

    def test_sibling_name_basic(self):
        assert benchmark_control.sibling_name("foo", 1) == "foo-katabenchmark1"

    def test_sibling_name_n_zero(self):
        assert benchmark_control.sibling_name("foo", 0) == "foo-katabenchmark0"

    def test_sibling_name_large_n(self):
        assert benchmark_control.sibling_name("my-proj", 42) == "my-proj-katabenchmark42"

    def test_sibling_name_with_hyphens(self):
        """A base with hyphens must not confuse the suffix."""
        result = benchmark_control.sibling_name("my-proj-name", 3)
        assert result == "my-proj-name-katabenchmark3"
        # Verify suffix is appended once, at the end
        assert result.endswith("-katabenchmark3")


# ---------------------------------------------------------------------------
# next_index
# ---------------------------------------------------------------------------


class TestNextIndex:
    """Tests for next_index(parent_dir, base) → next free N."""

    def test_next_index_empty_dir(self, tmp_path):
        """No siblings → returns 1 (first available index)."""
        result = benchmark_control.next_index(tmp_path, "myproject")
        assert result == 1

    def test_next_index_existing_siblings(self, tmp_path):
        """Siblings 1 and 2 present → returns 3."""
        (tmp_path / "myproject-katabenchmark1").mkdir()
        (tmp_path / "myproject-katabenchmark2").mkdir()
        result = benchmark_control.next_index(tmp_path, "myproject")
        assert result == 3

    def test_next_index_gap_uses_max_plus_one(self, tmp_path):
        """Siblings 1 and 3 (gap at 2) → returns 4 (max + 1, not first gap)."""
        (tmp_path / "myproject-katabenchmark1").mkdir()
        (tmp_path / "myproject-katabenchmark3").mkdir()
        result = benchmark_control.next_index(tmp_path, "myproject")
        assert result == 4

    def test_next_index_only_unrelated_dirs(self, tmp_path):
        """Unrelated dirs don't affect the count → returns 1."""
        (tmp_path / "myproject").mkdir()
        (tmp_path / "other-katabenchmark1").mkdir()  # different base
        (tmp_path / "myproject-notbenchmark").mkdir()  # wrong suffix
        result = benchmark_control.next_index(tmp_path, "myproject")
        assert result == 1

    def test_next_index_non_digit_suffix_ignored(self, tmp_path):
        """A dir matching '<base>-katabenchmark<non-digit>' is ignored."""
        (tmp_path / "myproject-katabenchmarkfoo").mkdir()
        result = benchmark_control.next_index(tmp_path, "myproject")
        assert result == 1


# ---------------------------------------------------------------------------
# content_hash
# ---------------------------------------------------------------------------


class TestContentHash:
    """Tests for content_hash(ref_dir) — stable SHA-256 over sorted file set."""

    def test_content_hash_stable(self, tmp_path):
        """Same directory, same content → same hash on two calls."""
        ref = _make_ref(tmp_path, {"a.txt": b"hello", "b.txt": b"world"})
        h1 = benchmark_control.content_hash(ref)
        h2 = benchmark_control.content_hash(ref)
        assert h1 == h2

    def test_content_hash_different_content(self, tmp_path):
        """Different file content → different hash."""
        ref1 = _make_ref(tmp_path / "r1", {"a.txt": b"hello"})
        ref2 = _make_ref(tmp_path / "r2", {"a.txt": b"HELLO"})
        assert benchmark_control.content_hash(ref1) != benchmark_control.content_hash(ref2)

    def test_content_hash_path_included_in_digest(self, tmp_path):
        """Same bytes under a different filename → different hash (path is part of the digest)."""
        ref1 = _make_ref(tmp_path / "r1", {"alpha.txt": b"data"})
        ref2 = _make_ref(tmp_path / "r2", {"beta.txt": b"data"})
        assert benchmark_control.content_hash(ref1) != benchmark_control.content_hash(ref2)

    def test_content_hash_file_order_invariant(self, tmp_path):
        """Adding files in a different order produces the same hash (sort-based)."""
        ref = _make_ref(tmp_path, {"z.txt": b"zzz", "a.txt": b"aaa", "m.txt": b"mmm"})
        h = benchmark_control.content_hash(ref)
        # A second dir with the same final content (regardless of creation order)
        ref2 = _make_ref(tmp_path / "copy", {"a.txt": b"aaa", "m.txt": b"mmm", "z.txt": b"zzz"})
        assert benchmark_control.content_hash(ref2) == h

    def test_content_hash_returns_hex_string(self, tmp_path):
        """Returns a 64-char lowercase hex string (SHA-256)."""
        ref = _make_ref(tmp_path, {"f.py": b"print('x')"})
        h = benchmark_control.content_hash(ref)
        assert isinstance(h, str)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_content_hash_nested_files_included(self, tmp_path):
        """Files in subdirectories are included; hash changes if a nested file changes."""
        ref = _make_ref(tmp_path, {"src/main.py": b"def foo(): pass", "README": b"doc"})
        h_before = benchmark_control.content_hash(ref)
        (ref / "src" / "main.py").write_bytes(b"def foo(): return 1")
        h_after = benchmark_control.content_hash(ref)
        assert h_before != h_after

    def test_content_hash_no_path_content_collision(self, tmp_path):
        """Regression D98: two distinct adversarial collision patterns must be rejected.

        Case 1 — naive concatenation (D98 original, requires BOTH prefixes):
          ref A: file named 'ab' containing b'c'  → naive stream b'ab'+b'c'  = b'abc'
          ref B: file named 'a'  containing b'bc' → naive stream b'a' +b'bc' = b'abc'
          Without any length-prefix, SHA-256 sees the same bytes for both trees.

        Case 2 — same-length path, same data, different name (requires path bytes):
          ref C: file named 'ab' containing b'c'
          ref D: file named 'ac' containing b'c'
          Without hashing the path bytes (h.update(rel_bytes)), both trees produce
          the stream '<len>:<datalen>:<data>' which is identical for any two files
          of the same path-byte-count and same content — defeating rename detection.

        Both patterns must produce distinct hashes under the full fix.
        """
        # Case 1: D98 naive-concat collision
        ref_a = tmp_path / "ref_a"
        ref_a.mkdir()
        (ref_a / "ab").write_bytes(b"c")

        ref_b = tmp_path / "ref_b"
        ref_b.mkdir()
        (ref_b / "a").write_bytes(b"bc")

        assert benchmark_control.content_hash(ref_a) != benchmark_control.content_hash(ref_b), (
            "D98 case 1: content_hash({'ab': b'c'}) == content_hash({'a': b'bc'}) — "
            "length-prefix fix was not applied (both trees naive-stream b'abc')"
        )

        # Case 2: same-length-path same-content rename collision
        ref_c = tmp_path / "ref_c"
        ref_c.mkdir()
        (ref_c / "ab").write_bytes(b"c")

        ref_d = tmp_path / "ref_d"
        ref_d.mkdir()
        (ref_d / "ac").write_bytes(b"c")  # same length as 'ab', same data

        assert benchmark_control.content_hash(ref_c) != benchmark_control.content_hash(ref_d), (
            "D98 case 2: content_hash({'ab': b'c'}) == content_hash({'ac': b'c'}) — "
            "path bytes (h.update(rel_bytes)) are not contributing to the digest"
        )


# ---------------------------------------------------------------------------
# detect_drift
# ---------------------------------------------------------------------------


class TestDetectDrift:
    """Tests for detect_drift(ref_dir, pinned_hash) → typed result dict."""

    def test_detect_drift_no_drift(self, tmp_path):
        """No change since pin → drifted=False."""
        ref = _make_ref(tmp_path, {"a.py": b"x = 1"})
        pinned = benchmark_control.content_hash(ref)
        result = benchmark_control.detect_drift(ref, pinned)
        assert result["drifted"] is False

    def test_detect_drift_with_drift(self, tmp_path):
        """File changed after pin → drifted=True."""
        ref = _make_ref(tmp_path, {"a.py": b"x = 1"})
        pinned = benchmark_control.content_hash(ref)
        # Mutate the reference (simulate reference tampering)
        (ref / "a.py").write_bytes(b"x = 99")
        result = benchmark_control.detect_drift(ref, pinned)
        assert result["drifted"] is True

    def test_detect_drift_returns_typed_result(self, tmp_path):
        """Result dict must have keys: drifted, current_hash, pinned_hash."""
        ref = _make_ref(tmp_path, {"f.txt": b"data"})
        pinned = benchmark_control.content_hash(ref)
        result = benchmark_control.detect_drift(ref, pinned)
        assert "drifted" in result
        assert "current_hash" in result
        assert "pinned_hash" in result

    def test_detect_drift_current_hash_in_result(self, tmp_path):
        """current_hash in result matches the live hash of ref_dir."""
        ref = _make_ref(tmp_path, {"f.txt": b"data"})
        pinned = "deadbeef" * 8  # deliberately wrong
        result = benchmark_control.detect_drift(ref, pinned)
        assert result["current_hash"] == benchmark_control.content_hash(ref)
        assert result["pinned_hash"] == pinned

    def test_detect_drift_wrong_pinned_hash(self, tmp_path):
        """A pinned hash that was never the real hash → drifted=True."""
        ref = _make_ref(tmp_path, {"f.txt": b"data"})
        result = benchmark_control.detect_drift(ref, "aabbccdd" * 8)
        assert result["drifted"] is True


# ---------------------------------------------------------------------------
# clone_control
# ---------------------------------------------------------------------------


class TestCloneControl:
    """Tests for clone_control(ref_dir, dest, *, copy_fn=None) → Path."""

    def test_clone_control_copies_files(self, tmp_path):
        """All files from ref appear under dest."""
        ref = _make_ref(tmp_path, {
            "src/main.py": b"print('hello')",
            "README.md": b"# project",
        })
        dest = tmp_path / "myproject-katabenchmark1"
        benchmark_control.clone_control(ref, dest)
        assert (dest / "src" / "main.py").read_bytes() == b"print('hello')"
        assert (dest / "README.md").read_bytes() == b"# project"

    def test_clone_control_ref_untouched(self, tmp_path):
        """Cloning does not mutate the reference directory (core invariant)."""
        ref = _make_ref(tmp_path, {"a.py": b"original"})
        hash_before = benchmark_control.content_hash(ref)
        dest = tmp_path / "myproject-katabenchmark1"
        benchmark_control.clone_control(ref, dest)
        hash_after = benchmark_control.content_hash(ref)
        assert hash_before == hash_after, "Reference was mutated by clone_control!"

    def test_clone_control_refuses_source_overlap_dest_inside_src(self, tmp_path):
        """dest is a subdirectory of ref_dir → raises ValueError (overlap guard)."""
        ref = _make_ref(tmp_path, {"f.py": b"x"})
        dest_inside = ref / "subdir"
        with pytest.raises(ValueError, match="overlap"):
            benchmark_control.clone_control(ref, dest_inside)

    def test_clone_control_refuses_source_overlap_src_inside_dest(self, tmp_path):
        """ref_dir is a subdirectory of dest → raises ValueError (overlap guard)."""
        outer = tmp_path / "outer"
        outer.mkdir()
        ref = outer / "inner"
        ref.mkdir()
        (ref / "f.py").write_bytes(b"x")
        with pytest.raises(ValueError, match="overlap"):
            benchmark_control.clone_control(ref, outer)

    def test_clone_control_refuses_equal_paths(self, tmp_path):
        """ref_dir == dest → raises ValueError (equal-path overlap guard)."""
        ref = _make_ref(tmp_path, {"f.py": b"x"})
        with pytest.raises(ValueError, match="overlap"):
            benchmark_control.clone_control(ref, ref)

    def test_clone_control_refuses_dotdot_in_ref(self, tmp_path):
        """``..`` in ref_dir path → raises ValueError (CWE-23)."""
        dest = tmp_path / "dest"
        with pytest.raises(ValueError, match=r"'\.\.'|traversal"):
            benchmark_control.clone_control(tmp_path / ".." / "somewhere", dest)

    def test_clone_control_refuses_dotdot_in_dest(self, tmp_path):
        """``..`` in dest path → raises ValueError (CWE-23)."""
        ref = _make_ref(tmp_path, {"f.py": b"x"})
        with pytest.raises(ValueError, match=r"'\.\.'|traversal"):
            benchmark_control.clone_control(ref, tmp_path / ".." / "dest")

    def test_clone_control_injectable_copy_fn_called(self, tmp_path):
        """Custom copy_fn is called with (src, dst) instead of shutil.copytree."""
        ref = _make_ref(tmp_path, {"f.py": b"x"})
        dest = tmp_path / "myproject-katabenchmark1"
        calls: list[tuple[Path, Path]] = []

        def spy_copy(src: Path, dst: Path) -> None:
            calls.append((src, dst))

        result = benchmark_control.clone_control(ref, dest, copy_fn=spy_copy)
        assert len(calls) == 1
        assert calls[0][0] == ref.resolve()
        assert calls[0][1] == dest.resolve()
        assert result == dest.resolve()


# ---------------------------------------------------------------------------
# prune
# ---------------------------------------------------------------------------


class TestPrune:
    """Tests for prune(copy_dir, *, rm_fn=None)."""

    def test_prune_removes_benchmark_copy(self, tmp_path):
        """A valid ``*-katabenchmark<N>`` directory is removed."""
        copy_dir = tmp_path / "myproject-katabenchmark1"
        copy_dir.mkdir()
        (copy_dir / "f.py").write_bytes(b"x")
        assert copy_dir.exists()
        benchmark_control.prune(copy_dir)
        assert not copy_dir.exists()

    def test_prune_refuses_non_benchmark_name(self, tmp_path):
        """Directory without ``-katabenchmark`` in its name → raises ValueError."""
        bad = tmp_path / "myproject"
        bad.mkdir()
        with pytest.raises(ValueError, match="-katabenchmark"):
            benchmark_control.prune(bad)

    def test_prune_refuses_non_digit_suffix(self, tmp_path):
        """``<base>-katabenchmarkfoo`` (non-digit suffix) → raises ValueError."""
        bad = tmp_path / "myproject-katabenchmarkfoo"
        bad.mkdir()
        with pytest.raises(ValueError, match="decimal integer|not a benchmark"):
            benchmark_control.prune(bad)

    def test_prune_refuses_dotdot(self, tmp_path):
        """``..`` in path → raises ValueError (CWE-23 guard)."""
        with pytest.raises(ValueError, match=r"'\.\.'|traversal"):
            benchmark_control.prune(tmp_path / ".." / "myproject-katabenchmark1")

    def test_prune_refuses_nonexistent_dir(self, tmp_path):
        """Valid name but non-existent directory → raises ValueError."""
        ghost = tmp_path / "myproject-katabenchmark99"
        assert not ghost.exists()
        with pytest.raises(ValueError, match="not an existing directory"):
            benchmark_control.prune(ghost)

    def test_prune_injectable_rm_fn_called(self, tmp_path):
        """Custom rm_fn is called with the resolved Path."""
        copy_dir = tmp_path / "myproject-katabenchmark1"
        copy_dir.mkdir()
        removed: list[Path] = []

        def spy_rm(p: Path) -> None:
            removed.append(p)

        benchmark_control.prune(copy_dir, rm_fn=spy_rm)
        assert len(removed) == 1
        assert removed[0] == copy_dir.resolve()


# ---------------------------------------------------------------------------
# exec-safety (mirrors TestExecSafety in test_debug_report.py)
# ---------------------------------------------------------------------------


class TestExecSafety:
    """Verify benchmark_control.py introduces zero new exec sinks (exec-safety.md)."""

    def _source(self) -> str:
        return (str(_TOOLS / "benchmark_control.py"))

    def _source_text(self) -> str:
        return Path(self._source()).read_text(encoding="utf-8")

    def test_no_subprocess_in_benchmark_control(self):
        """benchmark_control.py must not import subprocess (import statement check)."""
        import re
        hits = [
            m.group()
            for m in re.finditer(
                r"^\s*(?:import|from)\s+subprocess\b", self._source_text(), re.MULTILINE
            )
        ]
        assert not hits, (
            f"subprocess import found in benchmark_control.py: {hits} — "
            "zero new exec sink is a frozen invariant (exec-safety.md)"
        )

    def test_no_eval_in_benchmark_control(self):
        """benchmark_control.py must not use eval()."""
        import re
        # Allow the string 'eval' as part of another word, but not as a standalone call
        matches = re.findall(r'\beval\s*\(', self._source_text())
        assert not matches, (
            f"benchmark_control.py must not use eval() — found: {matches}"
        )

    def test_no_shell_true_in_benchmark_control(self):
        """benchmark_control.py must not use shell=True."""
        assert "shell=True" not in self._source_text(), (
            "benchmark_control.py must not use shell=True (exec-safety.md)"
        )

    def test_benchmark_control_is_ast_parseable(self):
        """benchmark_control.py must be valid Python (parseable by ast)."""
        import ast
        src = self._source_text()
        # Should not raise SyntaxError
        ast.parse(src)


# ---------------------------------------------------------------------------
# Mutation proofs (spawn real subprocess via prove_non_vacuous)
# ---------------------------------------------------------------------------


class TestMutationProof:
    """Mutation-proof tests for two load-bearing lines in benchmark_control.py.

    Targets:
      (1) The overlap guard in clone_control — removing it allows cloning into
          the reference directory itself (destroying the immutable-reference
          invariant).
      (2) The drift comparison in detect_drift — removing it means drift is
          never correctly detected.

    mutation_run.prove_non_vacuous always restores the source file afterward
    (try/finally guarantee), so these tests are self-healing even on failure.
    """

    def _src(self) -> str:
        return str(_TOOLS / "benchmark_control.py")

    def _cmd(self, test_spec: str) -> str:
        """Build a pytest command targeting a specific test in test_benchmark_control.py."""
        return (
            f'cd /d "{_TOOLS}" && '
            f"{sys.executable} -m pytest "
            f'"tests/test_benchmark_control.py::{test_spec}" -q --tb=no'
        )

    def test_mutation_proof_ref_never_written_overlap_guard(self):
        """Prove the clone_control overlap guard is load-bearing (ref-never-written invariant).

        Target line (exact, in clone_control):
            ``    if s == d or d in s.parents or s in d.parents:``

        When removed: the overlap check is skipped entirely, so cloning into
        a subdirectory of the reference (or into the reference itself) would
        proceed silently.  The test that expects ValueError stops getting it →
        testWentRed=True.
        """
        import mutation_run

        asserted_line = "    if s == d or d in s.parents or s in d.parents:"
        test_cmd = self._cmd(
            "TestCloneControl::test_clone_control_refuses_source_overlap_dest_inside_src"
        )
        verdict = mutation_run.prove_non_vacuous(self._src(), asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make the overlap-guard test go red — "
            "the 'if s == d or d in s.parents or s in d.parents' line is not load-bearing"
        )
        assert verdict["nonVacuous"], (
            "test_clone_control_refuses_source_overlap_dest_inside_src must catch "
            "removal of the overlap guard"
        )

    def test_mutation_proof_detect_drift_comparison(self):
        """Prove the drift-detection comparison line is load-bearing.

        Target line (exact, in detect_drift):
            ``    drifted = current != pinned_hash``

        When removed: ``drifted`` is undefined, causing a NameError in the return
        statement → the test that asserts drifted=True goes red.
        """
        import mutation_run

        asserted_line = "    drifted = current != pinned_hash"
        test_cmd = self._cmd(
            "TestDetectDrift::test_detect_drift_with_drift"
        )
        verdict = mutation_run.prove_non_vacuous(self._src(), asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make the drift-detection test go red — "
            "the 'drifted = current != pinned_hash' line is not load-bearing"
        )
        assert verdict["nonVacuous"], (
            "test_detect_drift_with_drift must catch removal of the "
            "drifted = current != pinned_hash comparison"
        )

    def test_mutation_proof_content_hash_collision_fix(self):
        """Prove the path-bytes contribution to content_hash is load-bearing (D98 case 2).

        Target line (exact, in content_hash):
            ``        h.update(rel_bytes)``

        When removed: the path bytes are absent from the digest, so two files with
        the same path-byte-length and the same content (e.g. 'ab'/b'c' vs 'ac'/b'c')
        produce an identical stream '<pathlen>:<datalen>:<data>' → identical digest →
        test_content_hash_no_path_content_collision case 2 goes red.
        """
        import mutation_run

        asserted_line = "        h.update(rel_bytes)"
        test_cmd = self._cmd(
            "TestContentHash::test_content_hash_no_path_content_collision"
        )
        verdict = mutation_run.prove_non_vacuous(self._src(), asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make the collision test go red — "
            "h.update(rel_bytes) is not load-bearing (path bytes not in digest)"
        )
        assert verdict["nonVacuous"], (
            "test_content_hash_no_path_content_collision must catch "
            "removal of h.update(rel_bytes) (D98 case 2)"
        )
