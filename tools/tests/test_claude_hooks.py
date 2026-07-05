"""test_claude_hooks.py — subprocess + unit tests for the Claude adapter hooks (A3, CA-P1).

Covers:
- kata-sessionstart.py: SessionStart(compact|resume) re-anchor injection via
  ``hookSpecificOutput.additionalContext`` (CA-L18); matcher guard; fail-soft.
- kata-precompact.py: the CA-L17 ADDITIVE HANDOFF-surfacing suffix; the never-block
  guarantee (G2 — blocking compaction near the limit is dangerous); fail-soft exit 0.

The hooks are stdlib-only fail-soft scripts (mirror the kata-precompact posture: never
raise to the host, always exit 0).  These are the first non-smoke tests for the hooks.

Mutation proofs (>=2 for A3):
- ``source == "compact"`` matcher guard: ``test_startup_source_emits_nothing`` goes RED
  if the guard is mutated to emit unconditionally.
- never-block: ``test_precompact_source_never_block_shaped`` goes RED if the hook is
  mutated to emit ``{"decision": "block"}`` / ``exit(2)``.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]  # tools/
sys.path.insert(0, str(ROOT))

REPO_ROOT = ROOT.parent
HOOKS_DIR = REPO_ROOT / "adapters" / "claude" / "hooks"
SESSIONSTART = HOOKS_DIR / "kata-sessionstart.py"
PRECOMPACT = HOOKS_DIR / "kata-precompact.py"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _load(path: Path, name: str):
    """Import a hyphen-named hook module by file path (no _main auto-run — guarded)."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(script: Path, stdin_text: str) -> subprocess.CompletedProcess[str]:
    """Run a hook script as a subprocess, piping ``stdin_text``."""
    return subprocess.run(
        [sys.executable, str(script)],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _mk_handoff(tmp_path: Path) -> Path:
    planning = tmp_path / ".planning"
    planning.mkdir(parents=True, exist_ok=True)
    hf = planning / "HANDOFF.md"
    hf.write_text("# HANDOFF\n", encoding="utf-8")
    return hf


# --------------------------------------------------------------------------- #
# kata-sessionstart.py — unit tests
# --------------------------------------------------------------------------- #
class TestSessionStartUnit:
    def setup_method(self) -> None:
        self.mod = _load(SESSIONSTART, "kata_sessionstart_hook")

    def test_should_anchor_compact_and_resume(self) -> None:
        assert self.mod._should_anchor("compact") is True
        assert self.mod._should_anchor("resume") is True

    def test_should_not_anchor_startup_clear_or_missing(self) -> None:
        assert self.mod._should_anchor("startup") is False
        assert self.mod._should_anchor("clear") is False
        assert self.mod._should_anchor(None) is False
        assert self.mod._should_anchor("") is False

    def test_build_context_present_cites_handoff_and_orient(self) -> None:
        txt = self.mod._build_context(handoff_exists=True)
        assert ".planning/HANDOFF.md" in txt
        assert "kata-orient" in txt
        assert "Orientation tiers consume it 1:1." in txt
        # staleness rule is referenced (owned/defined in protocol + A6)
        assert "staleness" in txt

    def test_build_context_absent_points_at_full_rebuild(self) -> None:
        txt = self.mod._build_context(handoff_exists=False)
        assert "kata-orient" in txt
        assert "full" in txt.lower()
        # honest about absence
        assert "no" in txt.lower()


# --------------------------------------------------------------------------- #
# kata-sessionstart.py — subprocess tests
# --------------------------------------------------------------------------- #
class TestSessionStartSubprocess:
    def _emit(self, source: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        payload = {
            "hook_event_name": "SessionStart",
            "source": source,
            "cwd": str(cwd),
            "session_id": "sess-abc",
        }
        return _run(SESSIONSTART, json.dumps(payload))

    def test_compact_with_handoff_injects_additional_context(self, tmp_path: Path) -> None:
        _mk_handoff(tmp_path)
        cp = self._emit("compact", tmp_path)
        assert cp.returncode == 0
        out = json.loads(cp.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert ".planning/HANDOFF.md" in ctx

    def test_compact_without_handoff_points_at_rebuild(self, tmp_path: Path) -> None:
        cp = self._emit("compact", tmp_path)  # no HANDOFF.md written
        assert cp.returncode == 0
        ctx = json.loads(cp.stdout)["hookSpecificOutput"]["additionalContext"]
        assert "kata-orient" in ctx

    def test_resume_source_also_anchors(self, tmp_path: Path) -> None:
        _mk_handoff(tmp_path)
        cp = self._emit("resume", tmp_path)
        assert cp.returncode == 0
        assert "additionalContext" in json.loads(cp.stdout)["hookSpecificOutput"]

    def test_startup_source_emits_nothing(self, tmp_path: Path) -> None:
        # MUTATION PROOF (source guard): unconditional emit -> RED here.
        cp = self._emit("startup", tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    def test_clear_source_emits_nothing(self, tmp_path: Path) -> None:
        cp = self._emit("clear", tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    def test_garbage_stdin_fail_soft(self) -> None:
        cp = _run(SESSIONSTART, "}{ not json at all")
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    def test_empty_stdin_fail_soft(self) -> None:
        cp = _run(SESSIONSTART, "")
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""


# --------------------------------------------------------------------------- #
# kata-precompact.py — unit tests for the CA-L17 HANDOFF suffix
# --------------------------------------------------------------------------- #
class TestPrecompactHandoffSuffix:
    def setup_method(self) -> None:
        self.mod = _load(PRECOMPACT, "kata_precompact_hook")

    def test_suffix_present_surfaces_existence_and_staleness(self, tmp_path: Path) -> None:
        _mk_handoff(tmp_path)
        suffix = self.mod._handoff_status_suffix(tmp_path)
        assert "HANDOFF.md" in suffix
        assert "staleness" in suffix
        # observe-only: never a block-shaped decision JSON (prose "DONE/DECISION" is fine)
        assert '"decision"' not in suffix
        assert '"block"' not in suffix

    def test_suffix_absent_points_at_rebuild(self, tmp_path: Path) -> None:
        suffix = self.mod._handoff_status_suffix(tmp_path)  # no HANDOFF.md
        assert "kata-orient" in suffix
        assert "block" not in suffix.lower()

    def test_suffix_is_leading_space_appendable(self, tmp_path: Path) -> None:
        _mk_handoff(tmp_path)
        suffix = self.mod._handoff_status_suffix(tmp_path)
        # additive to an existing nudge string: must start with a separator space
        assert suffix.startswith(" ")


# --------------------------------------------------------------------------- #
# kata-precompact.py — never-block + fail-soft
# --------------------------------------------------------------------------- #
class TestPrecompactNeverBlock:
    def test_source_never_block_shaped(self) -> None:
        # MUTATION PROOF (never-block): a decision:block / exit(2) mutation -> RED.
        src = PRECOMPACT.read_text(encoding="utf-8")
        assert '"decision"' not in src
        assert "decision:block" not in src
        assert "'block'" not in src
        assert '"block"' not in src
        assert "sys.exit(2)" not in src
        assert "exit(2)" not in src

    def test_garbage_stdin_exits_zero_no_block(self) -> None:
        cp = _run(PRECOMPACT, "}{ not json")
        assert cp.returncode == 0
        if cp.stdout.strip():
            assert "block" not in cp.stdout.lower()

    def test_empty_stdin_exits_zero(self) -> None:
        cp = _run(PRECOMPACT, "")
        assert cp.returncode == 0

    def test_committed_nudge_never_block_shaped_any_fixture(self, tmp_path: Path) -> None:
        # Exercise the committed-branch nudge assembly directly (present + absent HANDOFF).
        _mk_handoff(tmp_path)
        with_hf = self.mod_suffix(tmp_path)
        without = self.mod_suffix(tmp_path / "nope")
        for s in (with_hf, without):
            assert '"block"' not in s
            assert '"decision"' not in s

    def mod_suffix(self, root: Path) -> str:
        mod = _load(PRECOMPACT, "kata_precompact_hook_x")
        return mod._handoff_status_suffix(root)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
