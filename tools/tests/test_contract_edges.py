"""Tests for contract_edges.py — Freeze/Float M1 engine (M1-P0).

Slice A: invert + invalidation_set (pure, fail-closed). Every malformed shape must
RAISE (M1-L9 / F7 discipline) — a silent empty set would under-invalidate.
"""

from __future__ import annotations

import pytest

import contract_edges as ce

_H = "deadbeefcafe1234"  # a valid 16-hex surface hash


def _ba() -> dict:
    """A well-formed builds_against: T2,T3 build against C1; T3 also against C2."""
    return {
        "T2": [f"C1@{_H}"],
        "T3": [f"C1@{_H}", f"C2@{_H}"],
    }


# --- invert -------------------------------------------------------------------

def test_invert_happy_path():
    inv = ce.invert(_ba())
    assert inv == {"C1": ["T2", "T3"], "C2": ["T3"]}


def test_invert_empty_is_vacuous():
    assert ce.invert({}) == {}


def test_invert_dedupes_and_sorts():
    # A task listing the same contract twice collapses; tasks come out sorted.
    ba = {"T9": [f"C1@{_H}"], "T1": [f"C1@{_H}", f"C1@{_H}"]}
    assert ce.invert(ba) == {"C1": ["T1", "T9"]}


# --- invert: fail-closed on malformed (M1-L9) ---------------------------------

def test_invert_raises_not_a_dict():
    with pytest.raises(ValueError):
        ce.invert(["T2", "C1"])


def test_invert_raises_non_string_task_key():
    with pytest.raises(ValueError):
        ce.invert({1: [f"C1@{_H}"]})


def test_invert_raises_value_not_a_list():
    with pytest.raises(ValueError):
        ce.invert({"T2": f"C1@{_H}"})


def test_invert_raises_entry_not_a_string():
    with pytest.raises(ValueError):
        ce.invert({"T2": [123]})


def test_invert_raises_missing_at_separator():
    with pytest.raises(ValueError):
        ce.invert({"T2": ["C1_no_hash"]})


def test_invert_raises_bad_hash_charset():
    with pytest.raises(ValueError):
        ce.invert({"T2": ["C1@NOTHEX!!"]})


def test_invert_raises_hash_too_short():
    with pytest.raises(ValueError):
        ce.invert({"T2": ["C1@dead"]})  # < 8 hex


def test_invert_raises_on_trailing_newline():
    # \Z (not $) anchor: a trailing newline is malformed, not silently accepted.
    with pytest.raises(ValueError):
        ce.invert({"T2": [f"C1@{_H}\n"]})


# --- invalidation_set ---------------------------------------------------------

def test_invalidation_set_returns_bound_tasks():
    assert ce.invalidation_set(_ba(), "C1") == ["T2", "T3"]
    assert ce.invalidation_set(_ba(), "C2") == ["T3"]


def test_invalidation_set_unknown_contract_is_empty():
    assert ce.invalidation_set(_ba(), "C_missing") == []


def test_invalidation_set_empty_map_is_empty():
    assert ce.invalidation_set({}, "C1") == []


def test_invalidation_set_raises_on_malformed():
    # A malformed map must RAISE, never silently return [] (would under-invalidate).
    with pytest.raises(ValueError):
        ce.invalidation_set({"T2": "C1@" + _H}, "C1")


def test_invalidation_set_raises_on_bad_changed_id():
    with pytest.raises(ValueError):
        ce.invalidation_set(_ba(), "")


# --- Slice B: surface_hash ----------------------------------------------------

def _contract(tmp_path, body: str, name: str = "c1") -> str:
    d = tmp_path / "contracts" / name
    d.mkdir(parents=True)
    (d / "__init__.py").write_text(body, encoding="utf-8")
    return str(d)


def test_surface_hash_stable_across_body_fill(tmp_path):
    """Filling a stub body must NOT change the pin (bodies excluded — M1-L8)."""
    stub = _contract(tmp_path, "def foo(x: int) -> str:\n    ...  # KATA-CONTRACT-STUB\n", "a")
    filled = _contract(tmp_path, "def foo(x: int) -> str:\n    return str(x)\n", "b")
    assert ce.surface_hash(stub) == ce.surface_hash(filled)


def test_surface_hash_changes_on_return_annotation(tmp_path):
    a = _contract(tmp_path, "def foo(x):\n    ...\n", "a")
    b = _contract(tmp_path, "def foo(x) -> int:\n    ...\n", "b")
    assert ce.surface_hash(a) != ce.surface_hash(b)


def test_surface_hash_changes_on_decorator(tmp_path):
    a = _contract(tmp_path, "class C:\n    def m(self):\n        ...\n", "a")
    b = _contract(tmp_path, "class C:\n    @property\n    def m(self):\n        ...\n", "b")
    assert ce.surface_hash(a) != ce.surface_hash(b)


def test_surface_hash_changes_on_param(tmp_path):
    a = _contract(tmp_path, "def foo(x):\n    ...\n", "a")
    b = _contract(tmp_path, "def foo(x, y):\n    ...\n", "b")
    assert ce.surface_hash(a) != ce.surface_hash(b)


def test_surface_hash_changes_on_rename(tmp_path):
    a = _contract(tmp_path, "def foo(x):\n    ...\n", "a")
    b = _contract(tmp_path, "def bar(x):\n    ...\n", "b")
    assert ce.surface_hash(a) != ce.surface_hash(b)


def test_surface_hash_changes_on_class_header(tmp_path):
    a = _contract(tmp_path, "class C:\n    ...\n", "a")
    b = _contract(tmp_path, "class C(Base):\n    ...\n", "b")
    assert ce.surface_hash(a) != ce.surface_hash(b)


def test_surface_hash_raises_on_unparseable(tmp_path):
    bad = _contract(tmp_path, "def foo(:\n    this is not python\n", "a")
    with pytest.raises(ValueError):
        ce.surface_hash(bad)


def test_surface_hash_raises_on_missing_dir(tmp_path):
    with pytest.raises(ValueError):
        ce.surface_hash(str(tmp_path / "nope"))


def test_surface_hash_deferred_residual_constant(tmp_path):
    """DOCUMENTED RESIDUAL (M1-L1, not a bug): a module-constant change does NOT
    change the surface hash — constants are deferred to the review backstop, not
    machine-pinned. This test pins the known gap so it is visible, not silent."""
    a = _contract(tmp_path, "MAX = 5\ndef foo(x):\n    ...\n", "a")
    b = _contract(tmp_path, "MAX = 10\ndef foo(x):\n    ...\n", "b")
    assert ce.surface_hash(a) == ce.surface_hash(b)  # residual: constants unseen


def test_surface_hash_distinguishes_async(tmp_path):
    # async is an interface change (callers must await) — must move the pin (#1).
    a = _contract(tmp_path, "def foo(x):\n    ...\n", "a")
    b = _contract(tmp_path, "async def foo(x):\n    ...\n", "b")
    assert ce.surface_hash(a) != ce.surface_hash(b)


def test_surface_hash_format_invariant_whitespace(tmp_path):
    # Autoformatter whitespace must NOT flip the pin (#2 — M1-L8 no-op guarantee).
    a = _contract(tmp_path, "def foo(x,y):\n    ...\n", "a")
    b = _contract(tmp_path, "def foo(x,  y):\n    ...\n", "b")
    c = _contract(tmp_path, "def foo( x , y ):\n    ...\n", "c")
    assert ce.surface_hash(a) == ce.surface_hash(b) == ce.surface_hash(c)


def test_surface_hash_format_invariant_comment(tmp_path):
    a = _contract(tmp_path, "def foo(x, y):\n    ...\n", "a")
    b = _contract(tmp_path, "def foo(x,  # note\n        y):\n    ...\n", "b")
    assert ce.surface_hash(a) == ce.surface_hash(b)


def test_surface_hash_excludes_nested_defs(tmp_path):
    # A nested def/class inside a body is implementation, not surface (M1-L8 core).
    a = _contract(tmp_path, "def foo(x):\n    ...\n", "a")
    b = _contract(
        tmp_path,
        "def foo(x):\n    def helper():\n        return 1\n"
        "    class Inner:\n        pass\n    return helper\n",
        "b",
    )
    assert ce.surface_hash(a) == ce.surface_hash(b)


def test_surface_hash_distinguishes_keyword_only(tmp_path):
    a = _contract(tmp_path, "def foo(x, y):\n    ...\n", "a")
    b = _contract(tmp_path, "def foo(x, *, y):\n    ...\n", "b")
    assert ce.surface_hash(a) != ce.surface_hash(b)


def test_surface_hash_is_valid_edge_hash(tmp_path):
    # Internal consistency: a real surface_hash satisfies the builds_against grammar.
    d = _contract(tmp_path, "def foo(x):\n    ...\n", "a")
    h = ce.surface_hash(d)
    ce.invert({"T1": [f"C1@{h}"]})  # must not raise


# --- Slice C: surviving_stubs -------------------------------------------------

def test_surviving_stubs_flags_sentinel(tmp_path):
    d = tmp_path / "contracts" / "c1"
    d.mkdir(parents=True)
    (d / "__init__.py").write_text("def foo():\n    ...  # KATA-CONTRACT-STUB\n", encoding="utf-8")
    assert ce.surviving_stubs(tmp_path) == ["contracts/c1/__init__.py"]


def test_surviving_stubs_clean_when_retired(tmp_path):
    d = tmp_path / "contracts" / "c1"
    d.mkdir(parents=True)
    (d / "__init__.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    assert ce.surviving_stubs(tmp_path) == []


def test_surviving_stubs_ignores_non_contract_files(tmp_path):
    # A sentinel outside a contracts/ dir is not a contract stub — not flagged.
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "x.py").write_text("# KATA-CONTRACT-STUB\n", encoding="utf-8")
    assert ce.surviving_stubs(tmp_path) == []


def test_surviving_stubs_raises_on_unreadable(tmp_path, monkeypatch):
    # Fail-closed (M1-L9): a contracts/ file the gate cannot read must RAISE, never be
    # silently skipped (that would let a surviving sentinel pass the final gate).
    import pathlib

    d = tmp_path / "contracts" / "c1"
    d.mkdir(parents=True)
    (d / "__init__.py").write_text("def foo():\n    ...\n", encoding="utf-8")

    def _boom(self, *a, **k):
        raise OSError("unreadable contract file")

    monkeypatch.setattr(pathlib.Path, "read_text", _boom)
    with pytest.raises(OSError):
        ce.surviving_stubs(tmp_path)


# --- Slice C: edge_honesty ----------------------------------------------------

def _honesty_repo(tmp_path, test_body: str) -> None:
    (tmp_path / "provider.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    cdir = tmp_path / "contracts" / "c1"
    cdir.mkdir(parents=True)
    (cdir / "__init__.py").write_text("def foo():\n    ...  # KATA-CONTRACT-STUB\n", encoding="utf-8")
    (tmp_path / "test_dep.py").write_text(test_body, encoding="utf-8")


def test_edge_honesty_flags_provider_import(tmp_path):
    _honesty_repo(tmp_path, "import provider\n\ndef test_x():\n    assert provider.foo()\n")
    v = ce.edge_honesty(["test_dep.py"], ["provider.py"], tmp_path)
    assert v == [{"file": "test_dep.py", "imported": "provider.py"}]


def test_edge_honesty_clean_when_contract_only(tmp_path):
    _honesty_repo(tmp_path, "from contracts.c1 import foo\n\ndef test_x():\n    foo()\n")
    v = ce.edge_honesty(["test_dep.py"], ["provider.py"], tmp_path)
    assert v == []


def test_edge_honesty_raises_on_unreadable_dependent(tmp_path):
    # Fail-closed (M1-L9): an absent/unreadable dependent file cannot be certified
    # honest — RAISE, never silently deem it a non-violation.
    _honesty_repo(tmp_path, "from contracts.c1 import foo\n")
    with pytest.raises(OSError):
        ce.edge_honesty(["does_not_exist.py"], ["provider.py"], tmp_path)
