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

    monkeypatch.setattr(pathlib.Path, "read_bytes", _boom)
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


# --- Adval fold (2026-07-02): P0-F1..F5, F8, F12 ------------------------------

def test_surviving_stubs_catches_non_py_files(tmp_path):
    # P0-F2: the sentinel scan is extension-blind — a .pyi/.ts/.md stub must not
    # survive invisibly ("zero contracts/ files may still bear the sentinel").
    d = tmp_path / "contracts" / "c1"
    d.mkdir(parents=True)
    (d / "iface.pyi").write_text("def foo() -> int: ...  # KATA-CONTRACT-STUB\n", encoding="utf-8")
    (d / "api.md").write_text("# KATA-CONTRACT-STUB\ncontract notes\n", encoding="utf-8")
    got = ce.surviving_stubs(tmp_path)
    assert got == ["contracts/c1/api.md", "contracts/c1/iface.pyi"]


def test_surviving_stubs_catches_utf16_sentinel(tmp_path):
    # P0-F8: a UTF-16-encoded contracts/ file must not mask the sentinel.
    d = tmp_path / "contracts" / "c1"
    d.mkdir(parents=True)
    (d / "stub.py").write_bytes("# KATA-CONTRACT-STUB\n".encode("utf-16-le"))
    assert ce.surviving_stubs(tmp_path) == ["contracts/c1/stub.py"]


def test_surface_hash_raises_on_dir_without_py(tmp_path):
    # P0-F4: a contract dir with no .py file is an absent input to a decision
    # hash — hard-fail (D136/M1-L9), never a vacuous empty pin.
    empty = tmp_path / "contracts" / "empty"
    empty.mkdir(parents=True)
    with pytest.raises(ValueError):
        ce.surface_hash(empty)
    pyi_only = tmp_path / "contracts" / "pyi"
    pyi_only.mkdir(parents=True)
    (pyi_only / "iface.pyi").write_text("def foo() -> int: ...\n", encoding="utf-8")
    with pytest.raises(ValueError):
        ce.surface_hash(pyi_only)


def test_surface_hash_hash_in_string_default_does_not_mask_edits(tmp_path):
    # P0-F3: a '#' inside a string default is CONTENT — a later param edit in the
    # same signature must still flip the pin (quote-aware comment strip).
    a = _contract(tmp_path, 'def foo(x="#", y=2):\n    ...\n', "a")
    b = _contract(tmp_path, 'def foo(x="#", y=3):\n    ...\n', "b")
    c = _contract(tmp_path, 'def foo(x="#", z=9, *, q=None):\n    ...\n', "c")
    assert ce.surface_hash(a) != ce.surface_hash(b)
    assert ce.surface_hash(a) != ce.surface_hash(c)
    # real comments in a multiline signature are still stripped (no flip)
    d = _contract(tmp_path, "def bar(\n    x: int,  # the x\n    y: str,\n) -> int:\n    ...\n", "d")
    e = _contract(tmp_path, "def bar(x: int, y: str) -> int:\n    ...\n", "e")
    assert ce.surface_hash(d) == ce.surface_hash(e)


def test_surface_hash_stable_across_black_trailing_comma(tmp_path):
    # P0-F5: a black-style multiline explode with magic trailing comma is a
    # cosmetic reformat — must NOT flip the pin (M1-L8 autoformatter no-op)...
    a = _contract(tmp_path, "def foo(x, y):\n    ...\n", "a")
    b = _contract(tmp_path, "def foo(\n    x,\n    y,\n):\n    ...\n", "b")
    assert ce.surface_hash(a) == ce.surface_hash(b)
    # ...while an inner tuple default's comma is SEMANTIC and still pins.
    c = _contract(tmp_path, "def bar(x=(1,)):\n    ...\n", "c")
    d = _contract(tmp_path, "def bar(x=(1)):\n    ...\n", "d")
    assert ce.surface_hash(c) != ce.surface_hash(d)


def test_surface_hash_changes_on_default_value_edit(tmp_path):
    # F12: pin the de-facto answer — a default VALUE is part of the pinned surface.
    a = _contract(tmp_path, "def foo(x=1):\n    ...\n", "a")
    b = _contract(tmp_path, "def foo(x=2):\n    ...\n", "b")
    assert ce.surface_hash(a) != ce.surface_hash(b)


def test_surface_hash_changes_on_top_level_decorator(tmp_path):
    a = _contract(tmp_path, "def foo():\n    ...\n", "a")
    b = _contract(tmp_path, "@functools.cache\ndef foo():\n    ...\n", "b")
    assert ce.surface_hash(a) != ce.surface_hash(b)


def test_surface_hash_rel_path_attribution_pins_file_identity(tmp_path):
    # F12: two dirs whose files SWAP surfaces must hash differently — pins the
    # f"{rel}::" attribution (dropping it would make these collide).
    d1 = tmp_path / "contracts" / "d1"
    d1.mkdir(parents=True)
    (d1 / "a.py").write_text("def f():\n    ...\n", encoding="utf-8")
    (d1 / "b.py").write_text("def g():\n    ...\n", encoding="utf-8")
    d2 = tmp_path / "contracts" / "d2"
    d2.mkdir(parents=True)
    (d2 / "a.py").write_text("def g():\n    ...\n", encoding="utf-8")
    (d2 / "b.py").write_text("def f():\n    ...\n", encoding="utf-8")
    assert ce.surface_hash(d1) != ce.surface_hash(d2)


def test_edge_grammar_rejects_uppercase_hex():
    # F12: the edge pin is lowercase-hex by grammar; an uppercase hash RAISES
    # (writers normalize; a silent accept would desync the kata_restore join).
    with pytest.raises(ValueError):
        ce.invert({"T1": ["C1@ABCDEF12"]})


def test_edge_honesty_catches_relative_import(tmp_path):
    # P0-F1: `from .provider import foo` — the natural test-next-to-impl style —
    # must be a violation, not silently resolve to nothing.
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "provider.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    (pkg / "test_dep.py").write_text("from .provider import foo\n\ndef test_x():\n    foo()\n", encoding="utf-8")
    v = ce.edge_honesty(["pkg/test_dep.py"], ["pkg/provider.py"], tmp_path)
    assert v == [{"file": "pkg/test_dep.py", "imported": "pkg/provider.py"}]
    # bare `from . import provider` resolves the submodule too
    (pkg / "test_dep.py").write_text("from . import provider\n", encoding="utf-8")
    v2 = ce.edge_honesty(["pkg/test_dep.py"], ["pkg/provider.py"], tmp_path)
    assert v2 == [{"file": "pkg/test_dep.py", "imported": "pkg/provider.py"}]


def test_edge_honesty_catches_local_deferred_import(tmp_path):
    # Pin the (pre-existing) local-import coverage: an import inside a function
    # body is still a violation.
    _honesty_repo(tmp_path, "def test_x():\n    import provider\n    assert provider.foo()\n")
    v = ce.edge_honesty(["test_dep.py"], ["provider.py"], tmp_path)
    assert v == [{"file": "test_dep.py", "imported": "provider.py"}]
