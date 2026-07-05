"""test_statusline_chain.py — tests for the CA-L1 chain-never-clobber wrapper (A2, CA-P1).

Covers the decision gate (chain-eligibility), the `--` tail parse, byte-identical child
passthrough, kata's sibling bridge write, the untouched user bridge (CA-A4), and the
fail-soft legs (timeout, nonzero exit, missing program, SKIP).

Security posture under test: list-argv only, NEVER shell=True; on ANY doubt (metacharacter,
parse failure, timeout, nonzero) the wrapper takes the SKIP/fail-soft leg and never breaks
the user's statusline.

Mutation proofs (decision code):
- eligibility metachar reject: ``test_metachars_rejected`` goes RED if a metacharacter is
  dropped from ``_SHELL_METACHARS`` (e.g. removing ``|``).
- eligibility shlex-failure reject: ``test_unbalanced_quote_rejected`` goes RED if the
  ``ValueError`` guard is removed.
- SKIP-vs-CHAIN branch: ``test_child_argv_skips_ineligible`` goes RED if ``child_argv``
  returns argv for an ineligible command.
- never shell=True: ``test_source_has_no_shell_true`` pins the source.
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
CHAIN = REPO_ROOT / "adapters" / "claude" / "statusline_chain.py"


def _load():
    spec = importlib.util.spec_from_file_location("statusline_chain_mod", CHAIN)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load()


def _fwd(p: Path) -> str:
    """Forward-slash a path so it stays chain-eligible (backslash is a rejected metachar)."""
    return str(p).replace("\\", "/")


def _stdin(session_id: str = "sess-1", remaining: int = 42, total: int = 200_000) -> str:
    return json.dumps(
        {
            "session_id": session_id,
            "cwd": "/tmp/whatever",
            "context_window": {"remaining_percentage": remaining, "total_tokens": total},
        }
    )


# --------------------------------------------------------------------------- #
# is_chain_eligible — the decision gate
# --------------------------------------------------------------------------- #
class TestEligibility:
    def test_plain_command_eligible(self) -> None:
        assert mod.is_chain_eligible("python /path/gsd-statusline.js") is True

    def test_quoted_spaces_eligible(self) -> None:
        # shlex resolves quotes → still plain argv.
        assert mod.is_chain_eligible('python "/path with space/gsd.js"') is True

    @pytest.mark.parametrize(
        "cmd",
        [
            "a | b",
            "a && b",
            "a; b",
            "a > out",
            "a < in",
            "cat $(x)",
            "echo `x`",
            "node ~/gsd.js",
            "ls *.js",
            "run [a]",
            "run {a,b}",
            "a & b",
            "a # c",
            "run !x",
            r"python C:\gsd.js",
        ],
    )
    def test_metachars_rejected(self, cmd: str) -> None:
        # MUTATION PROOF: dropping any char from _SHELL_METACHARS makes one case RED.
        assert mod.is_chain_eligible(cmd) is False

    def test_unbalanced_quote_rejected(self) -> None:
        # MUTATION PROOF: removing the shlex ValueError guard makes this RED.
        assert mod.is_chain_eligible('python "unterminated') is False

    def test_empty_and_blank_rejected(self) -> None:
        assert mod.is_chain_eligible("") is False
        assert mod.is_chain_eligible("   ") is False

    def test_non_string_rejected(self) -> None:
        assert mod.is_chain_eligible(None) is False  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# parse_tail + child_argv
# --------------------------------------------------------------------------- #
class TestArgvParsing:
    def test_parse_tail_after_separator(self) -> None:
        assert mod.parse_tail(["chain.py", "--", "python", "x.js"]) == ["python", "x.js"]

    def test_parse_tail_absent_separator(self) -> None:
        assert mod.parse_tail(["chain.py"]) is None

    def test_parse_tail_empty_after_separator(self) -> None:
        assert mod.parse_tail(["chain.py", "--"]) is None

    def test_child_argv_single_string_shlex_split(self) -> None:
        assert mod.child_argv(['python "/a b/x.js"']) == ["python", "/a b/x.js"]

    def test_child_argv_presplit_tokens(self) -> None:
        assert mod.child_argv(["python", "/path/x.js"]) == ["python", "/path/x.js"]

    def test_child_argv_skips_ineligible(self) -> None:
        # MUTATION PROOF: if child_argv ignored eligibility, this returns argv → RED.
        assert mod.child_argv(["python x.js | rm -rf /"]) is None

    def test_child_argv_none_tail(self) -> None:
        assert mod.child_argv(None) is None


# --------------------------------------------------------------------------- #
# run_child — byte-identical passthrough + fail-soft
# --------------------------------------------------------------------------- #
class TestRunChild:
    def test_byte_identical_stdout(self, tmp_path: Path) -> None:
        stub = tmp_path / "echo_marker.py"
        stub.write_text(
            "import sys\nsys.stdout.buffer.write(b'MARKER-\\xe6\\x94\\xb9')\n",
            encoding="utf-8",
        )
        out = mod.run_child([sys.executable, str(stub)], b"anything")
        assert out == b"MARKER-\xe6\x94\xb9"

    def test_stdin_passed_through_unmodified(self, tmp_path: Path) -> None:
        stub = tmp_path / "echo_stdin.py"
        stub.write_text(
            "import sys\nsys.stdout.buffer.write(sys.stdin.buffer.read())\n",
            encoding="utf-8",
        )
        payload = b'{"session_id":"s","x":1}'
        assert mod.run_child([sys.executable, str(stub)], payload) == payload

    def test_nonzero_exit_still_returns_stdout(self, tmp_path: Path) -> None:
        stub = tmp_path / "fail.py"
        stub.write_text(
            "import sys\nsys.stdout.write('partial')\nsys.exit(3)\n", encoding="utf-8"
        )
        assert mod.run_child([sys.executable, str(stub)], b"") == b"partial"

    def test_timeout_fail_soft(self, tmp_path: Path) -> None:
        stub = tmp_path / "hang.py"
        stub.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
        # bounded — returns quickly, never hangs.
        out = mod.run_child([sys.executable, str(stub)], b"", timeout=1)
        assert out == b""

    def test_missing_program_fail_soft(self) -> None:
        assert mod.run_child(["definitely-not-a-real-binary-xyz"], b"") == b""

    def test_empty_argv_fail_soft(self) -> None:
        assert mod.run_child([], b"") == b""


# --------------------------------------------------------------------------- #
# _main end-to-end (subprocess) — CHAIN + SKIP legs, bridge, untouched user file
# --------------------------------------------------------------------------- #
def _run_main(tail_args, stdin_text: str, tmp_temp: Path) -> subprocess.CompletedProcess:
    env = {
        **_base_env(),
        "TMPDIR": str(tmp_temp),
        "TEMP": str(tmp_temp),
        "TMP": str(tmp_temp),
    }
    return subprocess.run(
        [sys.executable, str(CHAIN), "--", *tail_args],
        input=stdin_text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        env=env,
    )


def _base_env() -> dict:
    import os

    return dict(os.environ)


class TestMainEndToEnd:
    def test_chain_passthrough_and_kata_bridge(self, tmp_path: Path) -> None:
        temp = tmp_path / "t"
        temp.mkdir()
        stub = tmp_path / "user_status.py"
        stub.write_text(
            "import sys\nsys.stdout.buffer.write(b'USER-LINE')\n", encoding="utf-8"
        )
        exe = _fwd(Path(sys.executable))
        cmd = f'"{exe}" "{_fwd(stub)}"'
        cp = _run_main([cmd], _stdin(session_id="sess-abc"), temp)
        assert cp.returncode == 0
        # child stdout passed through byte-identical
        assert cp.stdout == b"USER-LINE"
        # kata's OWN bridge written to the sibling path
        bridge = temp / "kata-ctx-sess-abc.json"
        assert bridge.is_file()
        data = json.loads(bridge.read_text(encoding="utf-8"))
        assert data["session_id"] == "sess-abc"
        assert data["remaining_percentage"] == 42
        assert data["total_tokens"] == 200_000

    def test_user_bridge_untouched(self, tmp_path: Path) -> None:
        # CA-A4: the user's own bridge file is byte-unchanged after chaining.
        temp = tmp_path / "t"
        temp.mkdir()
        user_bridge = temp / "claude-ctx-sess-abc.json"
        original = '{"user":"owned","untouched":true}'
        user_bridge.write_text(original, encoding="utf-8")
        stub = tmp_path / "user_status.py"
        # the child writes ITS bridge only if absent; here it just echoes (never touches it)
        stub.write_text("import sys\nsys.stdout.write('X')\n", encoding="utf-8")
        exe = _fwd(Path(sys.executable))
        cp = _run_main([f'"{exe}" "{_fwd(stub)}"'], _stdin(session_id="sess-abc"), temp)
        assert cp.returncode == 0
        assert user_bridge.read_text(encoding="utf-8") == original
        # and kata's sibling exists alongside it (two files, zero contention)
        assert (temp / "kata-ctx-sess-abc.json").is_file()

    def test_skip_leg_ineligible_emits_nothing_but_writes_bridge(self, tmp_path: Path) -> None:
        temp = tmp_path / "t"
        temp.mkdir()
        # a metacharacter command → SKIP: no child runs, nothing emitted, exit 0
        cp = _run_main(["echo hi | rm"], _stdin(session_id="sess-skip"), temp)
        assert cp.returncode == 0
        assert cp.stdout == b""
        # kata bridge still written (SKIP leg falls back to kata's own gauge)
        assert (temp / "kata-ctx-sess-skip.json").is_file()

    def test_garbage_stdin_fail_soft(self, tmp_path: Path) -> None:
        temp = tmp_path / "t"
        temp.mkdir()
        cp = _run_main(["echo hi | rm"], "}{ not json", temp)
        assert cp.returncode == 0
        assert cp.stdout == b""


# --------------------------------------------------------------------------- #
# Source-level security pins
# --------------------------------------------------------------------------- #
class TestSecurityPins:
    def test_source_has_no_shell_true(self) -> None:
        src = CHAIN.read_text(encoding="utf-8")
        assert "shell=True" not in src
        assert "shell=False" in src

    def test_no_os_system_or_popen_shell(self) -> None:
        src = CHAIN.read_text(encoding="utf-8")
        assert "os.system" not in src
        assert "os.popen" not in src


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
