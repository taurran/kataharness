"""Tests for project_find.py — per-run project-folder search.

PURE tests — only real filesystem use is the pytest tmp_path fixture, on which a
small project tree is materialized.

Coverage:
- exact name match ranks above prefix/substring matches
- a unique match returns a single candidate
- N matches all returned, exact-first
- no match returns []
- non-existent parent returns []
- empty/blank name returns []
- rough_location boosts a candidate in that subtree above a better name elsewhere
- isRepo flags a directory containing .git
- noise dirs (node_modules/.git) are never returned as candidates
"""

from __future__ import annotations

import pytest

from project_find import find_projects


@pytest.fixture()
def tree(tmp_path):
    """A small parent with several project-ish folders."""
    (tmp_path / "MyApp").mkdir()
    (tmp_path / "MyApp" / ".git").mkdir()  # a real repo
    (tmp_path / "myapp-helper").mkdir()  # prefix match
    (tmp_path / "legacy-myapp").mkdir()  # substring match
    (tmp_path / "Unrelated").mkdir()
    (tmp_path / "node_modules").mkdir()  # noise
    # a nested project two levels down
    (tmp_path / "work" / "Widget").mkdir(parents=True)
    return tmp_path


def test_exact_match_ranks_first(tree):
    results = find_projects("MyApp", tree)
    assert results, "expected at least one candidate"
    assert results[0]["name"] == "MyApp"
    assert results[0]["score"] >= results[-1]["score"]


def test_unique_match_single_candidate(tree):
    results = find_projects("Widget", tree)
    names = [r["name"] for r in results]
    assert names == ["Widget"]


def test_n_matches_exact_first(tree):
    results = find_projects("myapp", tree)
    names = [r["name"] for r in results]
    # all three myapp-ish dirs found; exact (case-insensitive) first
    assert "MyApp" in names and "myapp-helper" in names and "legacy-myapp" in names
    assert names[0] == "MyApp"


def test_no_match_returns_empty(tree):
    assert find_projects("nonexistent", tree) == []


def test_missing_parent_returns_empty(tmp_path):
    assert find_projects("x", tmp_path / "does-not-exist") == []


def test_blank_name_returns_empty(tree):
    assert find_projects("   ", tree) == []
    assert find_projects("", tree) == []


def test_rough_location_boosts_subtree(tmp_path):
    # two same-named projects; the rough location points at one subtree
    (tmp_path / "alpha" / "Service").mkdir(parents=True)
    (tmp_path / "beta" / "Service").mkdir(parents=True)
    results = find_projects("Service", tmp_path, rough_location="beta")
    assert results[0]["path"].casefold().find("beta") != -1


def test_isrepo_flag(tree):
    results = find_projects("MyApp", tree)
    top = results[0]
    assert top["name"] == "MyApp"
    assert top["isRepo"] is True


def test_noise_dirs_not_returned(tree):
    results = find_projects("node_modules", tree)
    assert results == []
