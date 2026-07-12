"""test_kata_gauge_check.py — subprocess + unit tests for kata-gauge-check.py (CG-L1/CG-L7a).

The UserPromptSubmit conductor gauge check: crossed ⇒ `[KATA CONTEXT GAUGE]`
additionalContext; every other state ⇒ silent exit 0. Subprocess-invoked like
test_claude_hooks.py; the hook's `tempfile.gettempdir()` is redirected per-test via
TMPDIR/TEMP/TMP env so bridge + sidecar files are isolated in tmp_path.

Mutation proofs (CG-L7a):
- Kata-scope gate (F-3): ``test_non_kata_cwd_silent_even_when_crossed`` goes RED if the
  gate is mutated away; ``test_walk_cap_bounds_the_gate`` goes RED if the ~10-level bound
  is removed; ``test_kata_config_file_also_gates_in`` pins the second evidence form.
- Dedupe threshold (F-3): ``test_growth_below_threshold_stays_silent`` (0.75→0.79 silent)
  + ``test_growth_at_threshold_renotifies`` (0.75→0.80 notifies) pin the 0.05 constant
  from both sides; ``test_second_run_same_fraction_silent`` pins once-per-crossing.
- Never-exit-2 (F-8): ``test_source_is_never_exit_shaped`` goes RED on any exit(2)/
  block-decision mutation; every subprocess assertion requires returncode == 0.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]  # tools/
sys.path.insert(0, str(ROOT))

REPO_ROOT = ROOT.parent
GAUGE_CHECK = REPO_ROOT / "adapters" / "claude" / "hooks" / "kata-gauge-check.py"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _load(name: str = "kata_gauge_check_hook"):
    """Import the hyphen-named hook module by file path (no _main auto-run — guarded)."""
    spec = importlib.util.spec_from_file_location(name, GAUGE_CHECK)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(stdin_text: str, temp_dir: Path) -> subprocess.CompletedProcess[str]:
    """Run the hook as a subprocess with tempfile.gettempdir() redirected to *temp_dir*."""
    env = {
        **os.environ,
        "TMPDIR": str(temp_dir),
        "TEMP": str(temp_dir),
        "TMP": str(temp_dir),
    }
    return subprocess.run(
        [sys.executable, str(GAUGE_CHECK)],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


def _sid() -> str:
    """A unique, filename-safe session id per test."""
    return f"sess-{uuid.uuid4().hex}"


def _payload(session_id: str, cwd: Path | str) -> str:
    return json.dumps(
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": session_id,
            "cwd": str(cwd),
            "prompt": "continue",
        }
    )


def _write_bridge(
    temp_dir: Path,
    session_id: str,
    used_pct: float,
    *,
    total_tokens: int | None = 200_000,
    age_s: float = 0.0,
) -> Path:
    """Arrange a bridge file exactly as kata_statusline.write_bridge names/shapes it."""
    bridge = temp_dir / f"kata-ctx-{session_id}.json"
    bridge.write_text(
        json.dumps(
            {
                "session_id": session_id,
                "remaining_percentage": 100.0 - used_pct,
                "used_pct": used_pct,
                "timestamp": time.time() - age_s,
                "total_tokens": total_tokens,
            }
        ),
        encoding="utf-8",
    )
    return bridge


def _mk_kata_cwd(root: Path, *, evidence: str = ".kata") -> Path:
    """A kata-scoped cwd: *root* carries the evidence, cwd is *root* itself."""
    root.mkdir(parents=True, exist_ok=True)
    if evidence == ".kata":
        (root / ".kata").mkdir(exist_ok=True)
    else:
        (root / "kata.config").write_text("{}", encoding="utf-8")
    return root


def _ctx_of(cp: subprocess.CompletedProcess[str]) -> str:
    out = json.loads(cp.stdout)
    assert out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    return out["hookSpecificOutput"]["additionalContext"]


# --------------------------------------------------------------------------- #
# Crossed ⇒ notify
# --------------------------------------------------------------------------- #
class TestNotifies:
    def test_crossed_emits_additional_context_with_fraction(self, tmp_path: Path) -> None:
        sid = _sid()
        cwd = _mk_kata_cwd(tmp_path / "repo")
        _write_bridge(tmp_path, sid, 75.0)
        cp = _run(_payload(sid, cwd), tmp_path)
        assert cp.returncode == 0, cp.stderr
        ctx = _ctx_of(cp)
        assert "[KATA CONTEXT GAUGE]" in ctx
        assert "75%" in ctx  # the session's fraction
        assert "70%" in ctx  # the trigger
        assert "kata-selfhandoff" in ctx
        assert ".planning/HANDOFF.md" in ctx

    def test_kata_config_file_also_gates_in(self, tmp_path: Path) -> None:
        # MUTATION PROOF (scope gate, evidence form 2): kata.config alone suffices.
        sid = _sid()
        cwd = _mk_kata_cwd(tmp_path / "repo", evidence="kata.config")
        _write_bridge(tmp_path, sid, 80.0)
        cp = _run(_payload(sid, cwd), tmp_path)
        assert cp.returncode == 0
        assert "[KATA CONTEXT GAUGE]" in _ctx_of(cp)

    def test_kata_cwd_found_via_upward_walk(self, tmp_path: Path) -> None:
        sid = _sid()
        root = _mk_kata_cwd(tmp_path / "repo")
        deep = root / "src" / "pkg" / "mod"
        deep.mkdir(parents=True)
        _write_bridge(tmp_path, sid, 75.0)
        cp = _run(_payload(sid, deep), tmp_path)
        assert cp.returncode == 0
        assert "[KATA CONTEXT GAUGE]" in _ctx_of(cp)

    def test_percentage_only_bridge_triggers(self, tmp_path: Path) -> None:
        # CA-L2 degrade: total_tokens null ⇒ percentage-only triggering still fires.
        sid = _sid()
        cwd = _mk_kata_cwd(tmp_path / "repo")
        _write_bridge(tmp_path, sid, 90.0, total_tokens=None)
        cp = _run(_payload(sid, cwd), tmp_path)
        assert cp.returncode == 0
        assert "90%" in _ctx_of(cp)


# --------------------------------------------------------------------------- #
# Silent exits (all still exit 0 — never 2)
# --------------------------------------------------------------------------- #
class TestSilentPaths:
    def test_below_threshold_silent(self, tmp_path: Path) -> None:
        sid = _sid()
        cwd = _mk_kata_cwd(tmp_path / "repo")
        _write_bridge(tmp_path, sid, 50.0)
        cp = _run(_payload(sid, cwd), tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    def test_bridge_absent_silent(self, tmp_path: Path) -> None:
        sid = _sid()
        cwd = _mk_kata_cwd(tmp_path / "repo")
        cp = _run(_payload(sid, cwd), tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    def test_corrupt_bridge_silent(self, tmp_path: Path) -> None:
        sid = _sid()
        cwd = _mk_kata_cwd(tmp_path / "repo")
        (tmp_path / f"kata-ctx-{sid}.json").write_text("}{ not json", encoding="utf-8")
        cp = _run(_payload(sid, cwd), tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    def test_stale_bridge_silent(self, tmp_path: Path) -> None:
        sid = _sid()
        cwd = _mk_kata_cwd(tmp_path / "repo")
        _write_bridge(tmp_path, sid, 75.0, age_s=301.0)  # STALENESS_S = 300, strict >
        cp = _run(_payload(sid, cwd), tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    def test_non_kata_cwd_silent_even_when_crossed(self, tmp_path: Path) -> None:
        # MUTATION PROOF (F-3 scope gate): crossed bridge + no kata evidence ⇒ nothing.
        sid = _sid()
        plain = tmp_path / "plain"
        plain.mkdir()
        _write_bridge(tmp_path, sid, 90.0)
        cp = _run(_payload(sid, plain), tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    def test_walk_cap_bounds_the_gate(self, tmp_path: Path) -> None:
        # MUTATION PROOF (F-3 bounded walk): evidence 11 levels above cwd is out of
        # reach for the ~10-level cap ⇒ silent, even though the bridge is crossed.
        sid = _sid()
        root = _mk_kata_cwd(tmp_path / "repo")
        deep = root
        for i in range(11):
            deep = deep / f"d{i}"
        deep.mkdir(parents=True)
        _write_bridge(tmp_path, sid, 90.0)
        cp = _run(_payload(sid, deep), tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    @pytest.mark.parametrize("bad_sid", ["../evil", "a/b", "a\\b", "sp ace", "sess..1x/"])
    def test_unsafe_session_id_silent(self, tmp_path: Path, bad_sid: str) -> None:
        cwd = _mk_kata_cwd(tmp_path / "repo")
        cp = _run(_payload(bad_sid, cwd), tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    def test_missing_session_id_silent(self, tmp_path: Path) -> None:
        cwd = _mk_kata_cwd(tmp_path / "repo")
        cp = _run(json.dumps({"cwd": str(cwd)}), tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    def test_malformed_stdin_exit_zero(self, tmp_path: Path) -> None:
        cp = _run("}{ not json at all", tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    def test_empty_stdin_exit_zero(self, tmp_path: Path) -> None:
        cp = _run("", tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    def test_non_object_stdin_exit_zero(self, tmp_path: Path) -> None:
        cp = _run(json.dumps(["not", "a", "dict"]), tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""


# --------------------------------------------------------------------------- #
# Once-per-crossing dedupe (F-3)
# --------------------------------------------------------------------------- #
class TestDedupe:
    def test_second_run_same_fraction_silent(self, tmp_path: Path) -> None:
        # MUTATION PROOF (dedupe): removing the sidecar check re-notifies every turn.
        sid = _sid()
        cwd = _mk_kata_cwd(tmp_path / "repo")
        _write_bridge(tmp_path, sid, 75.0)
        first = _run(_payload(sid, cwd), tmp_path)
        assert first.returncode == 0
        assert "[KATA CONTEXT GAUGE]" in _ctx_of(first)
        second = _run(_payload(sid, cwd), tmp_path)
        assert second.returncode == 0
        assert second.stdout.strip() == ""

    def test_growth_below_threshold_stays_silent(self, tmp_path: Path) -> None:
        # MUTATION PROOF (0.05 constant, low side): 0.75 -> 0.79 is < +0.05 ⇒ silent.
        sid = _sid()
        cwd = _mk_kata_cwd(tmp_path / "repo")
        _write_bridge(tmp_path, sid, 75.0)
        assert "[KATA CONTEXT GAUGE]" in _ctx_of(_run(_payload(sid, cwd), tmp_path))
        _write_bridge(tmp_path, sid, 79.0)
        cp = _run(_payload(sid, cwd), tmp_path)
        assert cp.returncode == 0
        assert cp.stdout.strip() == ""

    def test_growth_at_threshold_renotifies(self, tmp_path: Path) -> None:
        # MUTATION PROOF (0.05 constant, high side): 0.75 -> 0.80 is ≥ +0.05 ⇒ notify.
        sid = _sid()
        cwd = _mk_kata_cwd(tmp_path / "repo")
        _write_bridge(tmp_path, sid, 75.0)
        assert "75%" in _ctx_of(_run(_payload(sid, cwd), tmp_path))
        _write_bridge(tmp_path, sid, 80.0)
        cp = _run(_payload(sid, cwd), tmp_path)
        assert cp.returncode == 0
        assert "80%" in _ctx_of(cp)

    def test_corrupt_sidecar_treated_as_absent(self, tmp_path: Path) -> None:
        sid = _sid()
        cwd = _mk_kata_cwd(tmp_path / "repo")
        _write_bridge(tmp_path, sid, 75.0)
        (tmp_path / f"kata-gauge-notified-{sid}.json").write_text(
            "}{ corrupt", encoding="utf-8"
        )
        cp = _run(_payload(sid, cwd), tmp_path)
        assert cp.returncode == 0
        assert "[KATA CONTEXT GAUGE]" in _ctx_of(cp)

    def test_sidecar_records_fraction_after_notify(self, tmp_path: Path) -> None:
        sid = _sid()
        cwd = _mk_kata_cwd(tmp_path / "repo")
        _write_bridge(tmp_path, sid, 75.0)
        assert _run(_payload(sid, cwd), tmp_path).returncode == 0
        sidecar = tmp_path / f"kata-gauge-notified-{sid}.json"
        data = json.loads(sidecar.read_text(encoding="utf-8"))
        assert data["last_notified_fraction"] == pytest.approx(0.75)
        # atomic temp+rename leaves no orphan temps behind on the happy path
        assert not list(tmp_path.glob("kata-gauge-notified-*.json.tmp"))


# --------------------------------------------------------------------------- #
# Never exit 2 (F-8) — structural + behavioral
# --------------------------------------------------------------------------- #
class TestNeverExit2:
    def test_source_is_never_exit_shaped(self) -> None:
        # MUTATION PROOF (never-block): an exit(2)/decision:block mutation -> RED.
        src = GAUGE_CHECK.read_text(encoding="utf-8")
        assert "sys.exit" not in src
        assert "exit(2)" not in src
        assert "os._exit" not in src
        assert '"decision"' not in src
        assert '"block"' not in src

    @pytest.mark.parametrize(
        "stdin_text",
        [
            "",
            "}{ garbage",
            json.dumps({"session_id": 42, "cwd": 17}),
            json.dumps({"session_id": "../..", "cwd": "Z:\\nope\\nowhere"}),
            json.dumps(None),
            "\x00\x01\x02",
        ],
    )
    def test_hostile_stdin_never_nonzero(self, tmp_path: Path, stdin_text: str) -> None:
        cp = _run(stdin_text, tmp_path)
        assert cp.returncode == 0  # exit 2 would block + erase the user's prompt
        assert cp.stdout.strip() == ""


# --------------------------------------------------------------------------- #
# Unit tests — scope-gate walk + sidecar parsing (imported module, no subprocess)
# --------------------------------------------------------------------------- #
class TestUnit:
    def setup_method(self) -> None:
        self.mod = _load()

    def test_scope_gate_finds_kata_dir_and_config(self, tmp_path: Path) -> None:
        kata = tmp_path / "a"
        (kata / ".kata").mkdir(parents=True)
        assert self.mod._is_kata_scope(kata) is True
        conf = tmp_path / "b"
        conf.mkdir()
        (conf / "kata.config").write_text("{}", encoding="utf-8")
        assert self.mod._is_kata_scope(conf) is True

    def test_scope_gate_stops_at_root_without_error(self) -> None:
        # A root path's parent is itself: the walk must terminate, not spin.
        root = Path(Path.cwd().anchor)
        assert self.mod._is_kata_scope(root) in (True, False)  # terminates

    def test_scope_gate_cap_is_exactly_bounded(self, tmp_path: Path) -> None:
        # MUTATION PROOF (cap boundary): evidence at exactly max_levels-1 ancestors
        # up is FOUND; one level deeper is NOT (cap ~10 — _SCOPE_WALK_CAP checks).
        cap = self.mod._SCOPE_WALK_CAP
        root = tmp_path / "repo"
        (root / ".kata").mkdir(parents=True)
        at_cap = root
        for i in range(cap - 1):
            at_cap = at_cap / f"d{i}"
        at_cap.mkdir(parents=True, exist_ok=True)
        assert self.mod._is_kata_scope(at_cap) is True
        beyond = at_cap / "one-more"
        beyond.mkdir()
        assert self.mod._is_kata_scope(beyond) is False

    def test_safe_session_id_mirrors_writer_guard(self) -> None:
        # Re-gate (LOW obligation): the charset mirrors kata_statusline._SAFE_SESSION_ID.
        import kata_statusline

        assert self.mod._SAFE_SESSION_ID.pattern == kata_statusline._SAFE_SESSION_ID.pattern

    @pytest.mark.parametrize(
        "content",
        ["", "}{", "[1,2]", '{"last_notified_fraction": "high"}',
         '{"last_notified_fraction": true}', '{"last_notified_fraction": 1.5}',
         '{"last_notified_fraction": -0.1}', '{"last_notified_fraction": NaN}'],
    )
    def test_read_last_notified_rejects_corrupt(self, tmp_path: Path, content: str) -> None:
        sidecar = tmp_path / "sidecar.json"
        sidecar.write_text(content, encoding="utf-8")
        assert self.mod._read_last_notified(sidecar) is None

    def test_read_last_notified_absent_is_none(self, tmp_path: Path) -> None:
        assert self.mod._read_last_notified(tmp_path / "nope.json") is None

    def test_read_last_notified_valid(self, tmp_path: Path) -> None:
        sidecar = tmp_path / "sidecar.json"
        sidecar.write_text('{"last_notified_fraction": 0.75}', encoding="utf-8")
        assert self.mod._read_last_notified(sidecar) == pytest.approx(0.75)

    def test_renotify_growth_constant_is_frozen(self) -> None:
        # MUTATION PROOF (constant pin): the DESIGN freezes the +0.05 growth step.
        assert self.mod._RENOTIFY_GROWTH == 0.05


# --------------------------------------------------------------------------- #
# settings.snippet.json — CG-L3 wiring
# --------------------------------------------------------------------------- #
class TestSnippetWiring:
    def test_snippet_has_userpromptsubmit_gauge_check(self) -> None:
        snippet = json.loads(
            (REPO_ROOT / "adapters" / "claude" / "settings.snippet.json").read_text(
                encoding="utf-8"
            )
        )
        entries = snippet["hooks"]["UserPromptSubmit"]
        commands = [h["command"] for e in entries for h in e["hooks"]]
        assert any("kata-gauge-check.py" in c for c in commands)
        # same <repo> templating + venv-python convention as the sibling hooks
        gauge_cmd = next(c for c in commands if "kata-gauge-check.py" in c)
        assert "<repo>" in gauge_cmd
        assert "tools/.venv/Scripts/python.exe" in gauge_cmd


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
