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

import ast
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
KATA_SCOPE = REPO_ROOT / "adapters" / "claude" / "kata_scope.py"
GAUGE_CHECK = REPO_ROOT / "adapters" / "claude" / "hooks" / "kata-gauge-check.py"


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


def _stdin(
    session_id: str = "sess-1",
    remaining: float = 42,
    total: int = 200_000,
    cwd: str = "/tmp/whatever",
) -> str:
    # NOTE (v2-F3 hermeticity): callers that exercise the CHAIN/SKIP legs MUST pass a
    # guaranteed-non-kata *cwd* (a pytest tmp_path) so a stray `.kata` on the machine's
    # `/tmp` cannot flip the wrapper onto the kata leg and break byte-identical passthrough.
    return json.dumps(
        {
            "session_id": session_id,
            "cwd": cwd,
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
            "echo %PATH%",
            "run ^escape",
        ],
    )
    def test_metachars_rejected(self, cmd: str) -> None:
        # MUTATION PROOF: dropping any char from _SHELL_METACHARS makes one case RED
        # (includes the cmd.exe-only % and ^ — the implicit-cmd.exe hardening fold).
        assert mod.is_chain_eligible(cmd) is False

    @pytest.mark.parametrize(
        "cmd",
        [
            "/path/user-status.bat",
            "/path/user-status.BAT arg1",
            "C:/scripts/status.cmd",
            "C:/scripts/STATUS.CMD",
            "legacy.com",
            "LEGACY.COM --flag",
        ],
    )
    def test_batch_targets_rejected(self, cmd: str) -> None:
        # MUTATION PROOF (extension gate): removing the _BATCH_EXTENSIONS argv[0]
        # check makes every case here RED — a .bat/.cmd/.com child runs via an
        # IMPLICIT cmd.exe despite shell=False (live-proven): skip-not-chain.
        assert mod.is_chain_eligible(cmd) is False

    def test_batch_gate_is_argv0_only_not_arguments(self) -> None:
        # a .bat mentioned as an ARGUMENT does not poison an eligible interpreter target
        assert mod.is_chain_eligible("python /path/reader.py input.bat") is True

    def test_child_argv_skips_batch(self) -> None:
        assert mod.child_argv(["/path/user-status.bat"]) is None

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
        nonkata = tmp_path / "nonkata"
        nonkata.mkdir()
        cp = _run_main([cmd], _stdin(session_id="sess-abc", cwd=str(nonkata)), temp)
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
        nonkata = tmp_path / "nonkata"
        nonkata.mkdir()
        cp = _run_main(
            [f'"{exe}" "{_fwd(stub)}"'], _stdin(session_id="sess-abc", cwd=str(nonkata)), temp
        )
        assert cp.returncode == 0
        assert user_bridge.read_text(encoding="utf-8") == original
        # and kata's sibling exists alongside it (two files, zero contention)
        assert (temp / "kata-ctx-sess-abc.json").is_file()

    def test_skip_leg_ineligible_emits_nothing_but_writes_bridge(self, tmp_path: Path) -> None:
        temp = tmp_path / "t"
        temp.mkdir()
        nonkata = tmp_path / "nonkata"
        nonkata.mkdir()
        # a metacharacter command → SKIP: no child runs, nothing emitted, exit 0
        cp = _run_main(
            ["echo hi | rm"], _stdin(session_id="sess-skip", cwd=str(nonkata)), temp
        )
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

    def test_garbage_stdin_eligible_child_still_runs(self, tmp_path: Path) -> None:
        # DESIGN S2 pinned clause (sweep finding 7): byte-identical passthrough
        # does NOT depend on payload validity — an ELIGIBLE child still runs on
        # unparseable stdin (garbage can never reach the kata leg either).
        temp = tmp_path / "t"
        temp.mkdir()
        stub = tmp_path / "user_status.py"
        stub.write_text(
            "import sys\nsys.stdout.buffer.write(b'ELIGIBLE-RAN')\n", encoding="utf-8"
        )
        cmd = f'"{_fwd(Path(sys.executable))}" "{_fwd(stub)}"'
        cp = _run_main([cmd], "}{ not json", temp)
        assert cp.returncode == 0
        assert cp.stdout == b"ELIGIBLE-RAN"


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


# --------------------------------------------------------------------------- #
# Kata segment rendering (D160 replace-in-kata-scopes) — unit
# --------------------------------------------------------------------------- #
_ABSENT = object()


def _render(
    tmp_path: Path,
    *,
    remaining=_ABSENT,
    start_name: str = "repo",
    board=None,
) -> str:
    """Render the kata segment for a synthetic payload. *start* only contributes its
    ``.name`` (never touched on disk, so control-char names are safe); *root* is a real
    on-disk kata dir so the board run-hint check can run."""
    root = tmp_path / "root"
    (root / ".kata").mkdir(parents=True, exist_ok=True)
    if board is not None:
        (root / ".kata" / "board.md").write_text(board, encoding="utf-8")
    start = tmp_path / start_name  # NOT created — _render_segment reads only .name
    cw = {} if remaining is _ABSENT else {"remaining_percentage": remaining}
    payload = {"context_window": cw}
    return mod._render_segment(payload, start, root)


class TestKataSegmentRender:
    def test_marker_and_dirname_are_dim(self, tmp_path: Path) -> None:
        seg = _render(tmp_path, remaining=42, start_name="myproj")
        assert mod._ANSI_DIM + "kata" + mod._ANSI_RESET in seg
        assert mod._ANSI_DIM + "myproj" + mod._ANSI_RESET in seg

    def test_meter_ten_segments(self, tmp_path: Path) -> None:
        seg = _render(tmp_path, remaining=42)  # used 58
        assert seg.count("▰") + seg.count("▱") == 10
        assert "58%" in seg

    def test_band_red_at_trigger_boundary(self, tmp_path: Path) -> None:
        # MUTATION PROOF (red boundary DERIVED from DEFAULT_TRIGGER_FRACTION=0.70): used 70
        # is RED (>=), used 69 is not.
        import kata_gauge

        assert kata_gauge.DEFAULT_TRIGGER_FRACTION * 100 == 70
        assert mod._ANSI_RED in _render(tmp_path, remaining=30)  # used 70
        assert mod._ANSI_RED not in _render(tmp_path, remaining=31)  # used 69

    def test_band_yellow_at_pre_warn_boundary(self, tmp_path: Path) -> None:
        # MUTATION PROOF (yellow display-only band = 55): used 55 YELLOW, used 54 GREEN.
        assert mod._METER_YELLOW_PCT == 55
        assert mod._ANSI_YELLOW in _render(tmp_path, remaining=45)  # used 55
        assert mod._ANSI_GREEN in _render(tmp_path, remaining=46)  # used 54

    def test_band_and_text_key_off_rounded_value(self, tmp_path: Path) -> None:
        # MUTATION PROOF (bands evaluate the ROUNDED displayed value so colour and printed %
        # agree): used 69.6 rounds to 70 ⇒ RED + "70%"; used 69.4 rounds to 69 ⇒ not-red + "69%".
        hot = _render(tmp_path, remaining=30.4)  # used 69.6 -> 70
        assert mod._ANSI_RED in hot and "70%" in hot
        warm = _render(tmp_path, remaining=30.6)  # used 69.4 -> 69
        assert mod._ANSI_RED not in warm and "69%" in warm

    def test_meter_omitted_when_remaining_absent(self, tmp_path: Path) -> None:
        seg = _render(tmp_path, remaining=_ABSENT)
        # meter omitted, but the segment (marker + dirname) still renders (v2-F6).
        assert "▰" not in seg and "▱" not in seg and "%" not in seg
        assert mod._ANSI_DIM + "kata" + mod._ANSI_RESET in seg

    @pytest.mark.parametrize("bad", [None, "high", True, [1], {"a": 1}])
    def test_meter_omitted_when_remaining_non_numeric(self, tmp_path: Path, bad) -> None:
        # mirrors write_bridge's _is_number (bool rejected).
        seg = _render(tmp_path, remaining=bad)
        assert "%" not in seg
        assert "kata" in seg  # never blank the whole segment (v2-F6)

    def test_run_hint_present_for_nonempty_board(self, tmp_path: Path) -> None:
        seg = _render(tmp_path, remaining=42, board="## phase\nrows")
        assert mod._SEG_SEP + mod._ANSI_DIM + "run" + mod._ANSI_RESET in seg

    def test_run_hint_absent_for_empty_board(self, tmp_path: Path) -> None:
        seg = _render(tmp_path, remaining=42, board="")
        assert mod._ANSI_DIM + "run" + mod._ANSI_RESET not in seg

    def test_run_hint_absent_when_no_board(self, tmp_path: Path) -> None:
        seg = _render(tmp_path, remaining=42, board=None)
        assert mod._ANSI_DIM + "run" + mod._ANSI_RESET not in seg

    def test_dirname_control_chars_stripped(self, tmp_path: Path) -> None:
        # MUTATION PROOF (G7d terminal-escape injection): C0 (0x07 BEL, 0x1b ESC) and C1
        # (0x9b CSI) control chars in a hostile dir name are stripped from the output.
        seg = _render(tmp_path, remaining=42, start_name="re\x07po\x1b\x9bX")
        assert "\x07" not in seg
        assert "\x9b" not in seg
        assert "repoX" in seg


# --------------------------------------------------------------------------- #
# _kata_leg — scope decision + fail-soft posture
# --------------------------------------------------------------------------- #
class TestKataLeg:
    def test_non_kata_payload_returns_none(self, tmp_path: Path) -> None:
        plain = tmp_path / "plain"
        plain.mkdir()
        assert mod._kata_leg({"cwd": str(plain)}) is None

    def test_cwdless_payload_returns_none(self) -> None:
        # no cwd / workspace ⇒ resolve_start None ⇒ NOT the kata leg (no getcwd here).
        assert mod._kata_leg({"session_id": "s"}) is None

    def test_kata_scope_returns_segment(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        (root / ".kata").mkdir(parents=True)
        seg = mod._kata_leg({"cwd": str(root), "context_window": {"remaining_percentage": 42}})
        assert seg is not None and "kata" in seg

    def test_in_scope_render_error_returns_empty_not_none(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        # MUTATION PROOF (fail-soft): in-scope render error ⇒ "" (emit nothing, still do NOT
        # run the child), never None (which would fall through to the child).
        root = tmp_path / "repo"
        (root / ".kata").mkdir(parents=True)

        def _boom(*a, **k):  # noqa: ANN002, ANN003
            raise RuntimeError("render blew up")

        monkeypatch.setattr(mod, "_render_segment", _boom)
        assert mod._kata_leg({"cwd": str(root)}) == ""


# --------------------------------------------------------------------------- #
# Kata leg end-to-end (subprocess) — child NOT run, bridge still written
# --------------------------------------------------------------------------- #
class TestKataLegEndToEnd:
    def test_kata_scope_renders_segment_and_never_runs_child(self, tmp_path: Path) -> None:
        temp = tmp_path / "t"
        temp.mkdir()
        katadir = tmp_path / "repo"
        (katadir / ".kata").mkdir(parents=True)
        stub = tmp_path / "child.py"
        stub.write_text(
            "import sys\nsys.stdout.buffer.write(b'CHILD-SHOULD-NOT-RUN')\n", encoding="utf-8"
        )
        exe = _fwd(Path(sys.executable))
        cmd = f'"{exe}" "{_fwd(stub)}"'
        cp = _run_main([cmd], _stdin(session_id="sess-kata", cwd=str(katadir)), temp)
        assert cp.returncode == 0
        # child NOT invoked — its marker must be absent
        assert b"CHILD-SHOULD-NOT-RUN" not in cp.stdout
        # kata segment rendered (dim marker + meter for used 58%)
        assert b"kata" in cp.stdout
        assert b"58%" in cp.stdout
        # bridge still written on the kata leg
        assert (temp / "kata-ctx-sess-kata.json").is_file()

    def test_kata_scope_found_via_upward_walk(self, tmp_path: Path) -> None:
        temp = tmp_path / "t"
        temp.mkdir()
        root = tmp_path / "repo"
        (root / ".kata").mkdir(parents=True)
        deep = root / "src" / "pkg"
        deep.mkdir(parents=True)
        stub = tmp_path / "child.py"
        stub.write_text("import sys\nsys.stdout.buffer.write(b'NOPE')\n", encoding="utf-8")
        exe = _fwd(Path(sys.executable))
        cp = _run_main(
            [f'"{exe}" "{_fwd(stub)}"'], _stdin(session_id="deep", cwd=str(deep)), temp
        )
        assert cp.returncode == 0
        assert b"NOPE" not in cp.stdout
        assert b"kata" in cp.stdout


# --------------------------------------------------------------------------- #
# Golden fixtures (G6 fold) — byte-identical passthrough, committed expected bytes
# --------------------------------------------------------------------------- #
#: The stub IGNORES stdin and emits these FIXED bytes, so the golden stdout stays
#: byte-fixed regardless of the (hermetic tmp_path) cwd injected into the payload (v2-F3).
_GOLDEN_CHILD_STDOUT = b"GOLDEN-STATUSLINE-\xe6\x94\xb9-v1"


class TestGoldenPassthrough:
    def test_chain_leg_golden_bytes(self, tmp_path: Path) -> None:
        temp = tmp_path / "t"
        temp.mkdir()
        nonkata = tmp_path / "nonkata"
        nonkata.mkdir()
        stub = tmp_path / "golden_child.py"
        stub.write_text(
            "import sys\nsys.stdin.buffer.read()\n"
            "sys.stdout.buffer.write(b'GOLDEN-STATUSLINE-\\xe6\\x94\\xb9-v1')\n",
            encoding="utf-8",
        )
        exe = _fwd(Path(sys.executable))
        cmd = f'"{exe}" "{_fwd(stub)}"'
        cp = _run_main([cmd], _stdin(session_id="gold", cwd=str(nonkata)), temp)
        assert cp.returncode == 0
        assert cp.stdout == _GOLDEN_CHILD_STDOUT  # committed expected bytes (CHAIN leg)

    def test_skip_leg_golden_bytes(self, tmp_path: Path) -> None:
        temp = tmp_path / "t"
        temp.mkdir()
        nonkata = tmp_path / "nonkata"
        nonkata.mkdir()
        # ineligible (metachar) command ⇒ SKIP leg golden: nothing emitted.
        cp = _run_main(["echo hi | rm"], _stdin(session_id="gold2", cwd=str(nonkata)), temp)
        assert cp.returncode == 0
        assert cp.stdout == b""


# --------------------------------------------------------------------------- #
# Drift test (G2-sharpened, v2-F4 conjunctive) — the ONE walk lives only in kata_scope
# --------------------------------------------------------------------------- #
def _funcs_with_parent_walk(src_path: Path) -> list[str]:
    """Return the names of functions that carry the upward-walk logic, defined conjunctively
    as: a loop (For/While) AND a ``.parent`` reference AND BOTH evidence literals
    (``.kata`` and ``kata.config``) in the SAME function body. A bare ``.kata`` literal
    elsewhere (e.g. the run-hint's path join) does NOT match."""
    src = src_path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            seg = ast.get_source_segment(src, node) or ""
            has_loop = any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(node))
            has_parent = ".parent" in seg
            has_both_literals = ".kata" in seg and "kata.config" in seg
            if has_loop and has_parent and has_both_literals:
                hits.append(node.name)
    return hits


class TestScopeDrift:
    def test_upward_walk_defined_only_in_kata_scope(self) -> None:
        # MUTATION PROOF (drift): the parent-loop + evidence-literal walk exists in
        # kata_scope.py and NOWHERE else. Copy it back into a consumer ⇒ RED.
        assert _funcs_with_parent_walk(KATA_SCOPE)  # find_kata_root carries it
        assert _funcs_with_parent_walk(CHAIN) == []
        assert _funcs_with_parent_walk(GAUGE_CHECK) == []

    def test_run_hint_bare_kata_literal_is_not_a_false_positive(self) -> None:
        # The chain wrapper DOES contain a bare ".kata" literal (the run-hint board path);
        # the conjunctive rule must NOT flag it as the walk.
        assert ".kata" in CHAIN.read_text(encoding="utf-8")
        assert _funcs_with_parent_walk(CHAIN) == []

    def test_both_consumers_import_the_shared_helper(self) -> None:
        assert "import kata_scope" in CHAIN.read_text(encoding="utf-8")
        assert "import kata_scope" in GAUGE_CHECK.read_text(encoding="utf-8")

    def test_neither_consumer_parses_payload_cwd_locally(self) -> None:
        # v2-F1: neither consumer carries local payload-cwd parsing — cwd resolution is the
        # shared helper's job. The hook's start line IS the resolve_start-or-getcwd wrap.
        chain_src = CHAIN.read_text(encoding="utf-8")
        gauge_src = GAUGE_CHECK.read_text(encoding="utf-8")
        assert '.get("cwd")' not in chain_src
        assert '.get("cwd")' not in gauge_src
        assert "kata_scope.resolve_start(payload) or Path(os.getcwd())" in gauge_src


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
