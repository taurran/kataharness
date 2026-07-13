"""test_kata_scope.py — the ONE shared kata-scope helper (D160/EV-1).

Ports the gauge hook's former ``_is_kata_scope`` walk tests as the base (they moved here
when the walk was extracted to ``adapters/claude/kata_scope.py``), and adds the
``resolve_start`` precedence contract (cwd wins over workspace.current_dir; non-string/empty
⇒ None; NO os.getcwd fallback here).

Mutation proofs:
- walk found-at-cwd / N-up / cap-stops / root-stop / OSError-None pin ``find_kata_root``.
- ``test_cap_boundary_exact`` goes RED if the ~10 bound is dropped or off-by-one.
- ``test_resolve_start_cwd_wins`` goes RED if precedence flips to workspace-first.
- ``test_resolve_start_no_getcwd_fallback`` goes RED if a getcwd fallback is added here.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]  # tools/
sys.path.insert(0, str(ROOT))

REPO_ROOT = ROOT.parent
KATA_SCOPE = REPO_ROOT / "adapters" / "claude" / "kata_scope.py"


def _load():
    spec = importlib.util.spec_from_file_location("kata_scope_mod", KATA_SCOPE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load()


# --------------------------------------------------------------------------- #
# find_kata_root / is_kata_scope — the ONE bounded upward walk
# --------------------------------------------------------------------------- #
class TestWalk:
    def test_found_at_start_kata_dir(self, tmp_path: Path) -> None:
        (tmp_path / ".kata").mkdir()
        assert mod.find_kata_root(tmp_path) == tmp_path
        assert mod.is_kata_scope(tmp_path) is True

    def test_found_at_start_kata_config(self, tmp_path: Path) -> None:
        # MUTATION PROOF (evidence form 2): kata.config alone suffices.
        (tmp_path / "kata.config").write_text("{}", encoding="utf-8")
        assert mod.find_kata_root(tmp_path) == tmp_path
        assert mod.is_kata_scope(tmp_path) is True

    def test_found_n_levels_up_returns_root_not_start(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        (root / ".kata").mkdir(parents=True)
        deep = root / "src" / "pkg" / "mod"
        deep.mkdir(parents=True)
        # the returned root is the ANCESTOR carrying evidence, not the deep start.
        assert mod.find_kata_root(deep) == root
        assert mod.is_kata_scope(deep) is True

    def test_absent_evidence_is_none(self, tmp_path: Path) -> None:
        plain = tmp_path / "plain"
        plain.mkdir()
        assert mod.find_kata_root(plain) is None
        assert mod.is_kata_scope(plain) is False

    def test_cap_boundary_exact(self, tmp_path: Path) -> None:
        # MUTATION PROOF (cap boundary): evidence exactly at max_levels-1 ancestors up is
        # FOUND; one level deeper is NOT (default cap = _SCOPE_WALK_CAP).
        cap = mod._SCOPE_WALK_CAP
        root = tmp_path / "repo"
        (root / ".kata").mkdir(parents=True)
        at_cap = root
        for i in range(cap - 1):
            at_cap = at_cap / f"d{i}"
        at_cap.mkdir(parents=True, exist_ok=True)
        assert mod.is_kata_scope(at_cap) is True
        beyond = at_cap / "one-more"
        beyond.mkdir()
        assert mod.is_kata_scope(beyond) is False

    def test_max_levels_kwarg_forwarded(self, tmp_path: Path) -> None:
        # v2-F5: the kwarg is forwarded from is_kata_scope to find_kata_root (one signature).
        root = tmp_path / "repo"
        (root / ".kata").mkdir(parents=True)
        child = root / "child"
        child.mkdir()
        assert mod.is_kata_scope(child, max_levels=1) is False  # cap=1 can't reach the parent
        assert mod.is_kata_scope(child, max_levels=2) is True

    def test_root_stop_terminates(self) -> None:
        # A root path's parent is itself: the walk must terminate, not spin.
        root = Path(Path.cwd().anchor)
        assert mod.find_kata_root(root) in (None, root) or isinstance(
            mod.find_kata_root(root), Path
        )  # terminates either way

    def test_oserror_probing_returns_none(self, tmp_path: Path, monkeypatch) -> None:
        # MUTATION PROOF (fail-soft): an OSError while probing ⇒ None, never a raise.
        def _boom(self):  # noqa: ANN001
            raise OSError("simulated probe failure")

        monkeypatch.setattr(Path, "is_dir", _boom)
        assert mod.find_kata_root(tmp_path) is None
        assert mod.is_kata_scope(tmp_path) is False


# --------------------------------------------------------------------------- #
# resolve_start — the ONE payload→start resolution
# --------------------------------------------------------------------------- #
class TestResolveStart:
    def test_cwd_used(self, tmp_path: Path) -> None:
        payload = {"cwd": str(tmp_path)}
        assert mod.resolve_start(payload) == tmp_path.resolve()

    def test_workspace_fallback(self, tmp_path: Path) -> None:
        payload = {"workspace": {"current_dir": str(tmp_path)}}
        assert mod.resolve_start(payload) == tmp_path.resolve()

    def test_cwd_wins_over_workspace(self, tmp_path: Path) -> None:
        # MUTATION PROOF: precedence is cwd-first (pins the repo-wide "cwd wins").
        win = tmp_path / "win"
        win.mkdir()
        payload = {"cwd": str(win), "workspace": {"current_dir": str(tmp_path)}}
        assert mod.resolve_start(payload) == win.resolve()

    def test_empty_cwd_falls_to_workspace(self, tmp_path: Path) -> None:
        payload = {"cwd": "", "workspace": {"current_dir": str(tmp_path)}}
        assert mod.resolve_start(payload) == tmp_path.resolve()

    @pytest.mark.parametrize("bad", [None, "", 17, 3.5, True, ["x"], {"a": 1}])
    def test_non_string_or_empty_is_none(self, bad) -> None:
        # A non-string/empty cwd with no usable workspace slot ⇒ None (no getcwd here).
        assert mod.resolve_start({"cwd": bad}) is None

    def test_non_string_cwd_falls_to_workspace(self, tmp_path: Path) -> None:
        payload = {"cwd": 42, "workspace": {"current_dir": str(tmp_path)}}
        assert mod.resolve_start(payload) == tmp_path.resolve()

    def test_no_getcwd_fallback(self, tmp_path: Path, monkeypatch) -> None:
        # MUTATION PROOF (S3 posture): resolve_start NEVER adopts the process cwd — an
        # absent cwd is None here; the getcwd posture belongs to the hook caller only.
        monkeypatch.chdir(tmp_path)
        assert mod.resolve_start({}) is None
        assert mod.resolve_start({"session_id": "s"}) is None

    def test_non_dict_payload_is_none(self) -> None:
        assert mod.resolve_start(None) is None
        assert mod.resolve_start("nope") is None
        assert mod.resolve_start(["a"]) is None

    def test_workspace_not_a_dict_is_none(self) -> None:
        assert mod.resolve_start({"workspace": "not-a-dict"}) is None
        assert mod.resolve_start({"workspace": ["x"]}) is None

    def test_returned_path_is_resolved(self, tmp_path: Path) -> None:
        # v2-F2: the returned path is .resolve()d (absolute, normalized).
        sub = tmp_path / "a" / ".." / "b"
        (tmp_path / "b").mkdir(parents=True)
        got = mod.resolve_start({"cwd": str(sub)})
        assert got == (tmp_path / "b").resolve()
        assert got.is_absolute()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
