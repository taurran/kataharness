import subprocess

import footprint


def test_partition_prefix_match():
    result = footprint.partition(
        ["tools/x.py", "skills/y/SKILL.md"],
        ["tools/"],
    )
    assert result["in_footprint"] == ["tools/x.py"]
    assert result["out_of_footprint"] == ["skills/y/SKILL.md"]


def test_partition_exact_match():
    result = footprint.partition(
        ["tools/footprint.py", "docs/README.md"],
        ["tools/footprint.py"],
    )
    assert result["in_footprint"] == ["tools/footprint.py"]
    assert result["out_of_footprint"] == ["docs/README.md"]


def test_partition_multiple_footprint_entries():
    result = footprint.partition(
        ["tools/footprint.py", "skills/y/SKILL.md", "docs/README.md"],
        ["tools/", "skills/y/"],
    )
    assert result["in_footprint"] == ["skills/y/SKILL.md", "tools/footprint.py"]
    assert result["out_of_footprint"] == ["docs/README.md"]


def test_partition_backslash_normalized():
    result = footprint.partition(
        ["tools\\footprint.py", "docs\\README.md"],
        ["tools/"],
    )
    assert result["in_footprint"] == ["tools/footprint.py"]
    assert result["out_of_footprint"] == ["docs/README.md"]


def test_partition_output_is_sorted():
    result = footprint.partition(
        ["tools/z.py", "tools/a.py", "skills/x.md"],
        ["tools/"],
    )
    assert result["in_footprint"] == sorted(result["in_footprint"])
    assert result["out_of_footprint"] == sorted(result["out_of_footprint"])


def test_partition_empty_inputs():
    result = footprint.partition([], [])
    assert result["in_footprint"] == []
    assert result["out_of_footprint"] == []


def test_is_within_footprint_true():
    assert footprint.is_within_footprint(
        ["tools/footprint.py"],
        ["tools/"],
    ) is True


def test_is_within_footprint_false():
    assert footprint.is_within_footprint(
        ["tools/footprint.py", "skills/y/SKILL.md"],
        ["tools/"],
    ) is False


def test_is_within_footprint_empty():
    assert footprint.is_within_footprint([], ["tools/"]) is True


def test_manifest_keys_and_values():
    changed = ["tools/footprint.py", "skills/y/SKILL.md"]
    fp = ["tools/"]
    stat = "1 file changed"
    result = footprint.manifest(changed, fp, stat)

    assert "footprint" in result
    assert "changed" in result
    assert "inFootprint" in result
    assert "outOfFootprint" in result
    assert "withinFootprint" in result
    assert "diffstat" in result

    assert result["footprint"] == fp
    assert result["changed"] == changed
    assert result["inFootprint"] == ["tools/footprint.py"]
    assert result["outOfFootprint"] == ["skills/y/SKILL.md"]
    assert result["withinFootprint"] is False
    assert result["diffstat"] == stat


def test_manifest_within_footprint_true():
    result = footprint.manifest(["tools/footprint.py"], ["tools/"])
    assert result["withinFootprint"] is True


def test_manifest_default_diffstat_empty():
    result = footprint.manifest([], [])
    assert result["diffstat"] == ""


# ---------------------------------------------------------------------------
# code_bearing — new pure function (MAJOR-3)
# ---------------------------------------------------------------------------

def test_code_bearing_py_file():
    assert footprint.code_bearing(["tools/x.py"]) is True


def test_code_bearing_js_file():
    assert footprint.code_bearing(["src/app.js"]) is True


def test_code_bearing_ts_file():
    assert footprint.code_bearing(["src/index.ts"]) is True


def test_code_bearing_tsx_file():
    assert footprint.code_bearing(["components/App.tsx"]) is True


def test_code_bearing_jsx_file():
    assert footprint.code_bearing(["components/Button.jsx"]) is True


def test_code_bearing_go_file():
    assert footprint.code_bearing(["cmd/main.go"]) is True


def test_code_bearing_rs_file():
    assert footprint.code_bearing(["src/lib.rs"]) is True


def test_code_bearing_java_file():
    assert footprint.code_bearing(["Main.java"]) is True


def test_code_bearing_md_only_false():
    assert footprint.code_bearing(["docs/x.md"]) is False


def test_code_bearing_json_only_false():
    assert footprint.code_bearing(["config.json"]) is False


def test_code_bearing_mixed_docs_only_false():
    assert footprint.code_bearing(["docs/x.md", "a.json"]) is False


def test_code_bearing_empty_false():
    assert footprint.code_bearing([]) is False


def test_code_bearing_mixed_code_and_docs_true():
    # A mix of code and docs is still code-bearing
    assert footprint.code_bearing(["docs/README.md", "tools/footprint.py"]) is True


def test_code_bearing_case_insensitive():
    # Extensions are matched case-insensitively
    assert footprint.code_bearing(["tools/X.PY"]) is True


def test_code_bearing_txt_only_false():
    assert footprint.code_bearing(["notes.txt"]) is False


def test_code_bearing_yml_only_false():
    assert footprint.code_bearing([".github/ci.yml"]) is False


def test_code_bearing_backslash_path():
    # Windows-style separators are handled via _normalize
    assert footprint.code_bearing(["tools\\footprint.py"]) is True


# ---------------------------------------------------------------------------
# manifest — codeBearing field (MAJOR-3)
# ---------------------------------------------------------------------------

def test_manifest_code_bearing_true_for_py_change():
    result = footprint.manifest(["tools/footprint.py"], ["tools/"])
    assert "codeBearing" in result
    assert result["codeBearing"] is True


def test_manifest_code_bearing_false_for_docs_only():
    result = footprint.manifest(["docs/README.md", "config.json"], ["docs/"])
    assert "codeBearing" in result
    assert result["codeBearing"] is False


def test_manifest_code_bearing_false_for_empty():
    result = footprint.manifest([], [])
    assert "codeBearing" in result
    assert result["codeBearing"] is False


# ---------------------------------------------------------------------------
# F5 — commit-scoped lane-check (changed_in_task) + file-hash stamping
# ---------------------------------------------------------------------------

def _git(args: list[str], cwd) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def test_changed_in_task_excludes_foreign_fork(tmp_path, monkeypatch):
    """A task forked from an EARLIER integration head must report only its own
    changed files — the three-dot (merge-base) diff excludes files integration
    changed after the fork. Contrast: the two-dot diff would list them (the
    exact F5 hazard)."""
    repo = tmp_path
    _git(["init"], repo)
    _git(["checkout", "-b", "integration"], repo)
    _git(["config", "user.email", "t@t"], repo)
    _git(["config", "user.name", "t"], repo)
    (repo / "base.txt").write_text("base", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "base"], repo)

    # Fork the task branch at the base commit.
    _git(["checkout", "-b", "task/T5"], repo)

    # Integration advances with a FOREIGN file (after the task forked).
    _git(["checkout", "integration"], repo)
    (repo / "foreign.txt").write_text("foreign", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "foreign"], repo)

    # The task commits its OWN file, still forked from the earlier head.
    _git(["checkout", "task/T5"], repo)
    (repo / "task_owned.txt").write_text("owned", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "task"], repo)

    monkeypatch.chdir(repo)

    # Commit-scoped (three-dot) lane check → ONLY the task's own file.
    assert footprint.changed_in_task("integration", "task/T5") == ["task_owned.txt"]

    # Demonstrate the hazard the fix avoids: the two-dot diff lists foreign.txt.
    two_dot = footprint.changed_since("integration")
    assert "foreign.txt" in two_dot


def test_file_content_hashes_roundtrip_and_change(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("y = 2\n", encoding="utf-8")
    h1 = footprint.file_content_hashes(["a.py", "b.py"], str(tmp_path))
    assert set(h1) == {"a.py", "b.py"}
    assert all(v for v in h1.values())

    # A byte change is detected; the untouched file's hash is stable.
    (tmp_path / "a.py").write_text("x = 2\n", encoding="utf-8")
    h2 = footprint.file_content_hashes(["a.py", "b.py"], str(tmp_path))
    assert h2["a.py"] != h1["a.py"]
    assert h2["b.py"] == h1["b.py"]


def test_file_content_hashes_missing_is_none(tmp_path):
    h = footprint.file_content_hashes(["gone.py"], str(tmp_path))
    assert h["gone.py"] is None


def test_changed_since_single_ref_unchanged(tmp_path, monkeypatch):
    """BC guard: changed_since keeps its single-ref (two-dot) semantics — diff
    HEAD against the given ref. Untouched by the F5 changed_in_task addition."""
    repo = tmp_path
    _git(["init"], repo)
    _git(["checkout", "-b", "main"], repo)
    _git(["config", "user.email", "t@t"], repo)
    _git(["config", "user.name", "t"], repo)
    (repo / "base.txt").write_text("base", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "base"], repo)
    (repo / "second.txt").write_text("second", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "second"], repo)

    monkeypatch.chdir(repo)
    assert footprint.changed_since("HEAD~1") == ["second.txt"]


import pytest

# --- Adval fold (2026-07-02): F5-1..F5-3 -----------------------------------------

def _seed_repo(repo) -> None:
    _git(["init"], repo)
    _git(["checkout", "-b", "integration"], repo)
    _git(["config", "user.email", "t@t"], repo)
    _git(["config", "user.name", "t"], repo)
    (repo / "base.txt").write_text("base", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "base"], repo)


def test_changed_in_task_sees_renames_as_add_plus_delete(tmp_path, monkeypatch):
    """F5-1 (HIGH): a `git mv foreign -> owned/` must report BOTH paths — with
    rename detection on (the git default) only the destination appears, hiding
    the cross-lane deletion AND making the gate depend on operator git config."""
    repo = tmp_path
    _seed_repo(repo)
    (repo / "foreign_orig.txt").write_text("foreign content that is long enough\n", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "foreign file"], repo)

    _git(["checkout", "-b", "task/T7"], repo)
    _git(["mv", "foreign_orig.txt", "owned_moved.txt"], repo)
    _git(["commit", "-m", "task: steal a foreign file into own lane"], repo)

    monkeypatch.chdir(repo)
    got = footprint.changed_in_task("integration", "task/T7")
    assert got == ["foreign_orig.txt", "owned_moved.txt"], (
        "rename must surface as add+delete; destination-only hides the lane violation"
    )


def test_changed_in_task_raises_on_criss_cross(tmp_path, monkeypatch):
    """F5-2: multiple merge-bases make the three-dot base timestamp-dependent —
    ambiguous evidence must RAISE (D136 fail-closed), never drive the lane check."""
    repo = tmp_path
    _seed_repo(repo)
    # Build a criss-cross: two branches, each merges the other's tip once.
    _git(["checkout", "-b", "task/T8"], repo)
    (repo / "t8_a.txt").write_text("a", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "t8 a"], repo)

    _git(["checkout", "integration"], repo)
    (repo / "int_b.txt").write_text("b", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "int b"], repo)

    # cross-merge both ways (no-ff so both parents survive)
    _git(["merge", "--no-ff", "-m", "int merges t8", "task/T8"], repo)
    _git(["checkout", "task/T8"], repo)
    _git(["merge", "--no-ff", "-m", "t8 merges old int", "integration~1"], repo)

    # advance both again so the criss-cross bases are distinct
    (repo / "t8_c.txt").write_text("c", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "t8 c"], repo)
    _git(["checkout", "integration"], repo)
    (repo / "int_d.txt").write_text("d", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "int d"], repo)
    _git(["checkout", "task/T8"], repo)

    monkeypatch.chdir(repo)
    import subprocess as sp
    bases = sp.run(
        ["git", "merge-base", "--all", "integration", "task/T8"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    if len(bases) > 1:
        with pytest.raises(ValueError, match="merge-bases"):
            footprint.changed_in_task("integration", "task/T8")
    else:
        pytest.skip("topology did not produce multiple merge-bases on this git")


def test_changed_in_task_raises_on_no_common_ancestor(tmp_path, monkeypatch):
    """F5-3: an orphan branch (no merge base) must RAISE — a silent empty list
    would read as 'no drift' (the D136 silent-permissive default)."""
    repo = tmp_path
    _seed_repo(repo)
    _git(["checkout", "--orphan", "task/T9"], repo)
    (repo / "orphan.txt").write_text("o", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "orphan"], repo)

    monkeypatch.chdir(repo)
    import subprocess as sp
    with pytest.raises((sp.CalledProcessError, ValueError)):
        footprint.changed_in_task("integration", "task/T9")
