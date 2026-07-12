"""test_kata_host_settings.py — CG-L2 host-settings render/merge/unmerge engine tests.

Covers (DESIGN .planning/specs/conductor-gauge-wiring/DESIGN.md, freeze-gate F-7):
- render: <repo> placeholder resolution, venv-present/absent interpreter rule, generic
  event handling (no hard-coded hook-event list).
- merge: empty settings; the REAL shape of a GSD-style settings file; append-never-
  remove/reorder; idempotent re-merge; stale-kata-entry in-place update; the statusLine
  decision table (set / chained with byte-identical original after ``--`` /
  skipped-ineligible); fail-closed on structurally unusable user data.
- eligibility PIN for the GSD-style command: the forward-slash pattern
  ``"C:/Program Files/nodejs/node.exe" "C:/Users/x/.claude/hooks/gsd-statusline.js"``
  is ELIGIBLE (quotes resolve via shlex; no metacharacters) ⇒ chain-wrapped; the
  backslash variant is INELIGIBLE (backslash is a rejected metachar) ⇒ skipped.
- parity: kata_host_settings.is_chain_eligible is a faithful port of the CA-L1 pin in
  adapters/claude/statusline_chain.py — asserted on a shared vector set AND on the
  metachar/batch constant sets themselves.
- unmerge: exact round-trip back to the original dict; chain unwrap verbatim; kata-set
  statusLine removed.
- I/O shell: BOM'd file reads OK; corrupt JSON fail-closed (BOM-vs-corruption
  distinguishing message, file untouched); timestamped backup BEFORE change; atomic
  write leaves no temp file; re-run idempotency proven.
- kata_install wiring: --install-hooks / --uninstall-hooks / --dry-run / consent
  refusal without --yes; frozen-five existence + unchanged signatures.
"""

from __future__ import annotations

import copy
import importlib.util
import inspect
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]  # tools/
sys.path.insert(0, str(ROOT))

import kata_host_settings as khs  # noqa: E402
import kata_install  # noqa: E402

REPO_ROOT = ROOT.parent
CHAIN = REPO_ROOT / "adapters" / "claude" / "statusline_chain.py"
REAL_SNIPPET = REPO_ROOT / "adapters" / "claude" / "settings.snippet.json"


def _load_chain_module():
    spec = importlib.util.spec_from_file_location("statusline_chain_mod", CHAIN)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# Fixtures — snippet + GSD-style settings shapes
# --------------------------------------------------------------------------- #

#: Hermetic snippet mirroring the real file's SHAPE (statusLine + hooks events with the
#: <repo> placeholder convention) plus a MADE-UP extra event to prove the renderer and
#: merge engine treat the event list as generic data (another worker adds
#: UserPromptSubmit to the real snippet — nothing here may hard-code the event list).
def _snippet() -> dict:
    return {
        "statusLine": {
            "type": "command",
            "command": 'python "<repo>/adapters/claude/statusline.py"',
            "padding": 1,
            "refreshInterval": 1,
        },
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "compact|resume",
                    "hooks": [
                        {
                            "type": "command",
                            "command": '"<repo>/tools/.venv/Scripts/python.exe" "<repo>/adapters/claude/hooks/kata-sessionstart.py"',
                        }
                    ],
                }
            ],
            "PreCompact": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": '"<repo>/tools/.venv/Scripts/python.exe" "<repo>/adapters/claude/hooks/kata-precompact.py"',
                        }
                    ]
                }
            ],
            "MadeUpFutureEvent": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": '"<repo>/tools/.venv/Scripts/python.exe" "<repo>/adapters/claude/hooks/kata-future.py"',
                        }
                    ]
                }
            ],
        },
    }


FAKE_REPO = Path("C:/fake/KataHarness") if sys.platform == "win32" else Path("/fake/KataHarness")
REPO_POSIX = FAKE_REPO.resolve().as_posix()

#: The GSD-style statusLine command pattern from the task pin — QUOTED, forward slashes.
GSD_CMD = '"C:/Program Files/nodejs/node.exe" "C:/Users/x/.claude/hooks/gsd-statusline.js"'
#: The same command as Windows-native backslash paths.
GSD_CMD_BACKSLASH = (
    '"C:\\Program Files\\nodejs\\node.exe" "C:\\Users\\x\\.claude\\hooks\\gsd-statusline.js"'
)


def _gsd_settings(cmd: str = GSD_CMD) -> dict:
    """The REAL shape of a GSD-style ~/.claude/settings.json (statusLine + own hooks)."""
    return {
        "$schema": "https://json.schemastore.org/claude-code-settings.json",
        "statusLine": {"type": "command", "command": cmd, "padding": 0},
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "Write|Edit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'node "C:/Users/x/.claude/hooks/gsd-check.js"',
                        }
                    ],
                }
            ],
            "SessionStart": [
                {
                    "matcher": "startup",
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'node "C:/Users/x/.claude/hooks/gsd-session.js"',
                        }
                    ],
                }
            ],
        },
        "env": {"GSD_MODE": "1"},
    }


def _rendered(venv: bool = True) -> dict:
    return khs.render_snippet(_snippet(), FAKE_REPO, venv_exists=venv)


# --------------------------------------------------------------------------- #
# render_snippet
# --------------------------------------------------------------------------- #
class TestRender:
    def test_venv_present_uses_venv_python(self) -> None:
        r = _rendered(venv=True)
        cmd = r["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        assert cmd == (
            f'"{REPO_POSIX}/tools/.venv/Scripts/python.exe" '
            f'"{REPO_POSIX}/adapters/claude/hooks/kata-sessionstart.py"'
        )

    def test_venv_absent_falls_back_to_bare_python(self) -> None:
        r = _rendered(venv=False)
        cmd = r["hooks"]["PreCompact"][0]["hooks"][0]["command"]
        assert cmd == f'python "{REPO_POSIX}/adapters/claude/hooks/kata-precompact.py"'

    def test_bare_python_upgraded_when_venv_present(self) -> None:
        r = _rendered(venv=True)
        assert r["statusLine"]["command"] == (
            f'"{REPO_POSIX}/tools/.venv/Scripts/python.exe" '
            f'"{REPO_POSIX}/adapters/claude/statusline.py"'
        )

    def test_bare_python_kept_when_venv_absent(self) -> None:
        r = _rendered(venv=False)
        assert r["statusLine"]["command"] == f'python "{REPO_POSIX}/adapters/claude/statusline.py"'

    def test_no_placeholder_remains_and_events_generic(self) -> None:
        for venv in (True, False):
            r = _rendered(venv=venv)
            assert "<repo>" not in json.dumps(r)
            # EVERY event present in the snippet is rendered — incl. the made-up one
            # (no hard-coded event list anywhere in the renderer).
            assert set(r["hooks"].keys()) == set(_snippet()["hooks"].keys())

    def test_real_snippet_renders_clean(self) -> None:
        snippet = json.loads(REAL_SNIPPET.read_text(encoding="utf-8-sig"))
        for venv in (True, False):
            r = khs.render_snippet(snippet, REPO_ROOT, venv_exists=venv)
            assert "<repo>" not in json.dumps(r)
            assert set(r["hooks"].keys()) == set(snippet["hooks"].keys())

    def test_default_probe_uses_filesystem(self) -> None:
        # venv_exists=None probes the real repo — the tools venv exists in this checkout,
        # so commands must reference it; regardless, no placeholder may survive.
        snippet = json.loads(REAL_SNIPPET.read_text(encoding="utf-8-sig"))
        r = khs.render_snippet(snippet, REPO_ROOT)
        assert "<repo>" not in json.dumps(r)

    def test_non_string_scalars_preserved(self) -> None:
        r = _rendered(venv=True)
        assert r["statusLine"]["padding"] == 1
        assert r["statusLine"]["refreshInterval"] == 1


# --------------------------------------------------------------------------- #
# is_chain_eligible — GSD pin + parity with the statusline_chain CA-L1 pin
# --------------------------------------------------------------------------- #

#: Shared parity vector set — every class the pin decides on.
PARITY_VECTORS = [
    GSD_CMD,  # the operator's GSD-style command (forward slashes, quoted) — ELIGIBLE
    GSD_CMD_BACKSLASH,  # backslash variant — INELIGIBLE (metachar)
    "python /path/gsd-statusline.js",
    'python "/path with space/gsd.js"',
    "a | b",
    "a && b",
    "a; b",
    "a > out",
    "cat $(x)",
    "echo `x`",
    "node ~/gsd.js",
    "ls *.js",
    "run [a]",
    "run {a,b}",
    "a # c",
    "run !x",
    r"python C:\gsd.js",
    "echo %PATH%",
    "run ^escape",
    "/path/user-status.bat",
    "C:/scripts/STATUS.CMD",
    "legacy.com --flag",
    "python /path/reader.py input.bat",
    'python "unterminated',
    "",
    "   ",
]


class TestEligibility:
    def test_gsd_forward_slash_command_is_ELIGIBLE_pin(self) -> None:
        # THE FIXTURE VERDICT PIN: the GSD-style command with QUOTED FORWARD-SLASH paths
        # contains no shell metacharacter and shlex-parses cleanly ⇒ chain-ELIGIBLE.
        assert khs.is_chain_eligible(GSD_CMD) is True

    def test_gsd_backslash_command_is_INELIGIBLE_pin(self) -> None:
        # The Windows-native backslash form IS a rejected metachar ⇒ INELIGIBLE ⇒ the
        # merge takes the skipped-ineligible leg (statusLine untouched).
        assert khs.is_chain_eligible(GSD_CMD_BACKSLASH) is False

    def test_parity_with_statusline_chain_pin(self) -> None:
        # The faithful-port cross-check (sanctioned leg): identical verdicts on the
        # shared vector set. Divergence in EITHER copy goes RED here.
        chain = _load_chain_module()
        for vec in PARITY_VECTORS:
            assert khs.is_chain_eligible(vec) == chain.is_chain_eligible(vec), vec
        assert khs.is_chain_eligible(None) == chain.is_chain_eligible(None)  # type: ignore[arg-type]

    def test_parity_of_constant_sets(self) -> None:
        chain = _load_chain_module()
        assert khs._SHELL_METACHARS == chain._SHELL_METACHARS
        assert khs._BATCH_EXTENSIONS == chain._BATCH_EXTENSIONS


# --------------------------------------------------------------------------- #
# merge_host_settings
# --------------------------------------------------------------------------- #
class TestMerge:
    def test_merge_into_empty(self) -> None:
        rendered = _rendered()
        merged, report = khs.merge_host_settings({}, rendered)
        assert merged["statusLine"] == rendered["statusLine"]
        for event, entries in rendered["hooks"].items():
            assert merged["hooks"][event] == entries
            assert report["hooks"][event] == ["appended"] * len(entries)
        assert report["statusline"] == "set"

    def test_existing_never_mutated(self) -> None:
        original = _gsd_settings()
        snapshot = copy.deepcopy(original)
        khs.merge_host_settings(original, _rendered())
        assert original == snapshot

    def test_gsd_eligible_statusline_chain_wrapped(self) -> None:
        rendered = _rendered(venv=False)
        merged, report = khs.merge_host_settings(_gsd_settings(GSD_CMD), rendered)
        assert report["statusline"] == "chained"
        # The DESIGN-pinned wrapper shape (venv absent ⇒ bare python interpreter):
        assert merged["statusLine"]["command"] == (
            f'python "{REPO_POSIX}/adapters/claude/statusline_chain.py" -- {GSD_CMD}'
        )
        # user's other statusLine keys preserved
        assert merged["statusLine"]["padding"] == 0
        assert merged["statusLine"]["type"] == "command"

    def test_chain_original_byte_identical_after_separator(self) -> None:
        merged, _ = khs.merge_host_settings(_gsd_settings(GSD_CMD), _rendered(venv=True))
        cmd = merged["statusLine"]["command"]
        sep = 'statusline_chain.py" -- '
        idx = cmd.find(sep)
        assert idx != -1
        tail = cmd[idx + len(sep):]
        assert tail == GSD_CMD  # VERBATIM — byte-identical original after `--`

    def test_gsd_backslash_ineligible_skipped_statusline_untouched(self) -> None:
        original = _gsd_settings(GSD_CMD_BACKSLASH)
        merged, report = khs.merge_host_settings(original, _rendered())
        assert report["statusline"] == "skipped-ineligible"
        assert merged["statusLine"] == original["statusLine"]  # untouched
        # hooks are STILL installed on the skip leg (DESIGN: skip statusline, report,
        # still install hooks)
        for event in _rendered()["hooks"]:
            assert any(
                khs._is_kata_entry(e, f"{REPO_POSIX}/adapters/claude/")
                for e in merged["hooks"][event]
            )

    def test_hooks_append_never_remove_or_reorder_user_entries(self) -> None:
        original = _gsd_settings()
        merged, report = khs.merge_host_settings(original, _rendered())
        # user's SessionStart entry keeps index 0; kata's entry appended AFTER it
        assert merged["hooks"]["SessionStart"][0] == original["hooks"]["SessionStart"][0]
        assert len(merged["hooks"]["SessionStart"]) == 2
        assert report["hooks"]["SessionStart"] == ["appended"]
        # user's PostToolUse (an event kata does not own) is byte-untouched
        assert merged["hooks"]["PostToolUse"] == original["hooks"]["PostToolUse"]
        # unrelated top-level keys preserved verbatim
        assert merged["env"] == {"GSD_MODE": "1"}
        assert merged["$schema"] == original["$schema"]

    def test_idempotent_remerge_is_noop(self) -> None:
        rendered = _rendered()
        merged1, _ = khs.merge_host_settings(_gsd_settings(), rendered)
        merged2, report2 = khs.merge_host_settings(merged1, rendered)
        assert merged2 == merged1
        for event in rendered["hooks"]:
            assert set(report2["hooks"][event]) == {"noop"}
        assert report2["statusline"] == "noop"

    def test_stale_kata_entry_updated_in_place_not_duplicated(self) -> None:
        # First merge with the venv interpreter, then the venv disappears (re-render
        # with bare python): the kata entry is UPDATED in place, never duplicated.
        merged1, _ = khs.merge_host_settings(_gsd_settings(), _rendered(venv=True))
        merged2, report2 = khs.merge_host_settings(merged1, _rendered(venv=False))
        assert len(merged2["hooks"]["SessionStart"]) == 2  # user + ONE kata entry
        assert report2["hooks"]["SessionStart"] == ["updated"]
        kata_cmd = merged2["hooks"]["SessionStart"][1]["hooks"][0]["command"]
        assert kata_cmd.startswith("python ")

    def test_statusline_absent_gets_kata_default(self) -> None:
        settings = {"hooks": {}}
        merged, report = khs.merge_host_settings(settings, _rendered())
        assert report["statusline"] == "set"
        assert merged["statusLine"] == _rendered()["statusLine"]

    def test_fail_closed_on_non_dict_hooks(self) -> None:
        with pytest.raises(khs.HostSettingsError):
            khs.merge_host_settings({"hooks": []}, _rendered())

    def test_fail_closed_on_non_list_event(self) -> None:
        with pytest.raises(khs.HostSettingsError):
            khs.merge_host_settings({"hooks": {"SessionStart": {}}}, _rendered())


# --------------------------------------------------------------------------- #
# unmerge_host_settings — exact round-trips
# --------------------------------------------------------------------------- #
class TestUnmerge:
    @pytest.mark.parametrize(
        "original",
        [
            {},
            _gsd_settings(GSD_CMD),
            _gsd_settings(GSD_CMD_BACKSLASH),
        ],
        ids=["empty", "gsd-eligible", "gsd-ineligible"],
    )
    def test_roundtrip_returns_original_exactly(self, original: dict) -> None:
        rendered = _rendered()
        merged, _ = khs.merge_host_settings(original, rendered)
        cleaned, _ = khs.unmerge_host_settings(merged, rendered)
        assert cleaned == original

    def test_kata_set_statusline_removed(self) -> None:
        rendered = _rendered()
        merged, _ = khs.merge_host_settings({}, rendered)
        cleaned, report = khs.unmerge_host_settings(merged, rendered)
        assert "statusLine" not in cleaned
        assert report["statusline"] == "removed"

    def test_chain_unwrapped_verbatim(self) -> None:
        rendered = _rendered()
        merged, _ = khs.merge_host_settings(_gsd_settings(GSD_CMD), rendered)
        cleaned, report = khs.unmerge_host_settings(merged, rendered)
        assert report["statusline"] == "unwrapped"
        assert cleaned["statusLine"]["command"] == GSD_CMD  # verbatim original

    def test_user_hooks_preserved(self) -> None:
        original = _gsd_settings()
        rendered = _rendered()
        merged, _ = khs.merge_host_settings(original, rendered)
        cleaned, _ = khs.unmerge_host_settings(merged, rendered)
        assert cleaned["hooks"] == original["hooks"]

    def test_unmerge_on_untouched_settings_is_noop(self) -> None:
        original = _gsd_settings()
        cleaned, report = khs.unmerge_host_settings(original, _rendered())
        assert cleaned == original
        assert report["hooks"] == {}
        assert report["statusline"] is None


# --------------------------------------------------------------------------- #
# I/O shell — strict read, backup, atomic write, idempotent re-run
# --------------------------------------------------------------------------- #
class TestIOShell:
    def _host(self, tmp_path: Path) -> Path:
        host = tmp_path / "claude-host"
        host.mkdir()
        return host

    def _snippet_file(self, tmp_path: Path) -> Path:
        p = tmp_path / "settings.snippet.json"
        p.write_text(json.dumps(_snippet(), indent=2), encoding="utf-8")
        return p

    def _apply(self, tmp_path: Path, host: Path, **kw) -> dict:
        return khs.apply_hooks_change(
            FAKE_REPO,
            host_dir=host,
            snippet_path=self._snippet_file(tmp_path),
            venv_exists=True,
            **kw,
        )

    def test_read_absent_returns_empty(self, tmp_path: Path) -> None:
        assert khs.read_host_settings(tmp_path / "nope.json") == {}

    def test_read_bom_file_ok(self, tmp_path: Path) -> None:
        p = tmp_path / "settings.json"
        p.write_bytes(b"\xef\xbb\xbf" + json.dumps(_gsd_settings()).encode("utf-8"))
        assert khs.read_host_settings(p) == _gsd_settings()

    def test_read_corrupt_no_bom_fail_closed(self, tmp_path: Path) -> None:
        p = tmp_path / "settings.json"
        p.write_bytes(b'{"broken": ')
        with pytest.raises(khs.HostSettingsError) as ei:
            khs.read_host_settings(p)
        assert "no BOM present" in str(ei.value)
        assert p.read_bytes() == b'{"broken": '  # file untouched

    def test_read_corrupt_with_bom_distinguished(self, tmp_path: Path) -> None:
        p = tmp_path / "settings.json"
        p.write_bytes(b"\xef\xbb\xbf" + b'{"broken": ')
        with pytest.raises(khs.HostSettingsError) as ei:
            khs.read_host_settings(p)
        # the error DISTINGUISHES: the BOM was handled — the JSON itself is corrupt
        assert "BOM was present and was handled" in str(ei.value)

    def test_read_non_dict_fail_closed(self, tmp_path: Path) -> None:
        p = tmp_path / "settings.json"
        p.write_text("[1, 2]", encoding="utf-8")
        with pytest.raises(khs.HostSettingsError):
            khs.read_host_settings(p)

    def test_apply_creates_settings_and_result_shape(self, tmp_path: Path) -> None:
        host = self._host(tmp_path)
        result = self._apply(tmp_path, host)
        assert result["ok"] is True and result["changed"] is True
        data = json.loads((host / "settings.json").read_text(encoding="utf-8"))
        assert "statusLine" in data
        for event in _snippet()["hooks"]:
            assert event in data["hooks"]
        assert result["backup"] is None  # fresh file — nothing to back up

    def test_backup_written_before_change_byte_exact(self, tmp_path: Path) -> None:
        host = self._host(tmp_path)
        original_bytes = json.dumps(_gsd_settings(), indent=4).encode("utf-8")
        (host / "settings.json").write_bytes(original_bytes)
        result = self._apply(tmp_path, host)
        backups = list(host.glob("settings.json.kata-backup-*"))
        assert len(backups) == 1
        assert result["backup"] == str(backups[0])
        assert backups[0].read_bytes() == original_bytes  # byte-exact pre-change copy

    def test_atomic_write_no_temp_left(self, tmp_path: Path) -> None:
        host = self._host(tmp_path)
        self._apply(tmp_path, host)
        assert list(host.glob("*.kata-tmp")) == []

    def test_rerun_idempotent(self, tmp_path: Path) -> None:
        host = self._host(tmp_path)
        (host / "settings.json").write_text(json.dumps(_gsd_settings()), encoding="utf-8")
        r1 = self._apply(tmp_path, host)
        after_first = (host / "settings.json").read_bytes()
        r2 = self._apply(tmp_path, host)
        assert r1["changed"] is True
        assert r2["changed"] is False  # no-op reported
        assert (host / "settings.json").read_bytes() == after_first
        # no second backup for a no-op
        assert len(list(host.glob("settings.json.kata-backup-*"))) == 1

    def test_dry_run_writes_nothing(self, tmp_path: Path) -> None:
        host = self._host(tmp_path)
        original = json.dumps(_gsd_settings()).encode("utf-8")
        (host / "settings.json").write_bytes(original)
        result = self._apply(tmp_path, host, dry_run=True)
        assert result["changed"] is True
        assert result["diff"]  # a real diff is produced for consent
        assert (host / "settings.json").read_bytes() == original
        assert list(host.glob("settings.json.kata-backup-*")) == []

    def test_uninstall_roundtrip_on_disk(self, tmp_path: Path) -> None:
        host = self._host(tmp_path)
        original = _gsd_settings()
        (host / "settings.json").write_text(json.dumps(original), encoding="utf-8")
        self._apply(tmp_path, host)
        self._apply(tmp_path, host, uninstall=True)
        data = json.loads((host / "settings.json").read_text(encoding="utf-8"))
        assert data == original

    def test_apply_fail_closed_on_corrupt_host_file(self, tmp_path: Path) -> None:
        host = self._host(tmp_path)
        (host / "settings.json").write_bytes(b"not json at all {")
        with pytest.raises(khs.HostSettingsError):
            self._apply(tmp_path, host)
        assert (host / "settings.json").read_bytes() == b"not json at all {"


# --------------------------------------------------------------------------- #
# kata_install CLI wiring — flags + consent + exit codes (real snippet, real repo)
# --------------------------------------------------------------------------- #
class TestInstallCliWiring:
    def _run(self, tmp_path: Path, *extra: str) -> int:
        return kata_install.main(
            [
                "--platform",
                "claude",
                "--home",
                str(REPO_ROOT),
                "--host-dir",
                str(tmp_path),
                *extra,
            ]
        )

    def test_install_hooks_headless_json(self, tmp_path: Path, capsys) -> None:
        rc = self._run(tmp_path, "--install-hooks", "--yes", "--json")
        assert rc == 0
        out = capsys.readouterr()
        result = json.loads(out.out.strip().splitlines()[-1])  # JSON report on stdout
        assert result["ok"] is True and result["changed"] is True
        data = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
        real_events = json.loads(REAL_SNIPPET.read_text(encoding="utf-8-sig"))["hooks"]
        for event in real_events:
            assert event in data["hooks"]
        assert "statusLine" in data
        assert "<repo>" not in json.dumps(data)
        # GLOBAL-hooks disclosure went to stderr (human notes) in --json mode
        assert "GLOBAL" in out.err

    def test_install_hooks_dry_run_writes_nothing(self, tmp_path: Path, capsys) -> None:
        rc = self._run(tmp_path, "--install-hooks", "--dry-run", "--yes", "--json")
        assert rc == 0
        assert not (tmp_path / "settings.json").exists()
        result = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
        assert result["dryRun"] is True

    def test_install_hooks_headless_without_yes_refused(self, tmp_path: Path, capsys) -> None:
        # pytest's stdin is not a TTY and --yes is absent ⇒ consent REFUSED, exit 2 USAGE
        rc = self._run(tmp_path, "--install-hooks")
        assert rc == 2
        assert not (tmp_path / "settings.json").exists()
        assert "consent" in capsys.readouterr().err

    def test_install_then_uninstall_roundtrip(self, tmp_path: Path) -> None:
        assert self._run(tmp_path, "--install-hooks", "--yes", "--json") == 0
        assert self._run(tmp_path, "--uninstall-hooks", "--yes", "--json") == 0
        data = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
        assert data == {}  # everything kata added was removed exactly

    def test_install_hooks_idempotent_rerun(self, tmp_path: Path, capsys) -> None:
        assert self._run(tmp_path, "--install-hooks", "--yes", "--json") == 0
        first = (tmp_path / "settings.json").read_bytes()
        capsys.readouterr()
        assert self._run(tmp_path, "--install-hooks", "--yes", "--json") == 0
        result = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
        assert result["changed"] is False
        assert (tmp_path / "settings.json").read_bytes() == first

    def test_mutually_exclusive_flags_usage_error(self, tmp_path: Path) -> None:
        rc = self._run(tmp_path, "--install-hooks", "--uninstall-hooks", "--yes")
        assert rc == 2

    def test_non_claude_platform_rejected(self, tmp_path: Path) -> None:
        rc = kata_install.main(
            [
                "--platform",
                "codex",
                "--home",
                str(REPO_ROOT),
                "--host-dir",
                str(tmp_path),
                "--install-hooks",
                "--yes",
            ]
        )
        assert rc == 3

    def test_corrupt_host_settings_exit_5(self, tmp_path: Path, capsys) -> None:
        (tmp_path / "settings.json").write_bytes(b"corrupt {{{")
        rc = self._run(tmp_path, "--install-hooks", "--yes", "--json")
        assert rc == 5  # fail-closed: never guess, never write
        assert (tmp_path / "settings.json").read_bytes() == b"corrupt {{{"
        assert "unparseable" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# Frozen-five pin — the engine functions exist with unchanged signatures
# --------------------------------------------------------------------------- #
class TestFrozenFivePin:
    #: parameter-name/default pins for the five BYTE-FROZEN kata_install engine fns
    EXPECTED_PARAMS = {
        "_flat_link_skills": ["home", "host_dir", "skills_subdir"],
        "_link_or_copy": ["src_dir", "dst_dir"],
        "install": ["platform", "harness_home", "host_dir"],
        "copy_project": ["src", "dest", "overwrite"],
        "confirm_platform": ["platform", "runner", "home"],
    }
    EXPECTED_DEFAULTS = {
        "_flat_link_skills": {"skills_subdir": "skills"},
        "install": {"harness_home": None, "host_dir": None},
        "copy_project": {"overwrite": False},
        "confirm_platform": {"runner": None, "home": None},
    }

    @pytest.mark.parametrize("name", sorted(EXPECTED_PARAMS))
    def test_function_exists_with_unchanged_signature(self, name: str) -> None:
        fn = getattr(kata_install, name)
        sig = inspect.signature(fn)
        assert list(sig.parameters) == self.EXPECTED_PARAMS[name]
        for pname, default in self.EXPECTED_DEFAULTS.get(name, {}).items():
            assert sig.parameters[pname].default == default


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
