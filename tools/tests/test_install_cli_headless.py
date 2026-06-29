"""test_install_cli_headless.py — TDD for Slices B + C headless surface.

Tests the NEW additive CLI flags (--non-interactive/--yes, --answers-json, --json,
--uninstall/--target-dir), semantic exit codes, and the uninstall verb.

File ownership: Slices B + C ONLY.  Does NOT import or call the engine functions
directly (_flat_link_skills, _link_or_copy, install, copy_project, confirm_platform)
except where needed to set up state for CLI-level assertions.

Coverage (PLAN §Slice B + C):
B-1  New flags parse without error
B-2  Non-TTY stdin auto-enables non-interactive mode
B-3  --answers-json loads + writes settings; malformed → 2; bad dir → 3
B-4  Env-var fallbacks KATA_PARENT_DIR / KATA_VAULT_DIR
B-5  _exit_code_for mapper: ok→0; ok:False→3; OSError→4; non-kata ValueError→5; generic→1
B-6  --json: machine JSON to stdout; human notes to stderr
B-7  BC regression / stdout golden: no-flag main() format unchanged
C-1  uninstall removes kata symlinks
C-2  uninstall removes .kata-managed copy dirs
C-3  CLI --uninstall removes settings file + calls remove_stanza on AGENTS.md
C-4  Re-run --uninstall is a no-op (exit 0, no raise)
C-5  Plugin-manifest removal is flag-gated (default keep)
C-6  Non-kata-dir guard: uninstall leaves non-kata dirs intact
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import kata_install as ki


# ---------------------------------------------------------------------------
# Shared fixture (mirrors fake_home in test_kata_install.py; local copy so
# this file has zero cross-file fixture dependencies)
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_home(tmp_path):
    """A minimal harness home: two category-nested skills + one module skill."""
    home = tmp_path / "KataHarness"
    (home / "skills" / "coordinate" / "kata-bootstrap").mkdir(parents=True)
    (home / "skills" / "coordinate" / "kata-bootstrap" / "SKILL.md").write_text(
        "---\nname: kata-bootstrap\n---\n", encoding="utf-8"
    )
    (home / "skills" / "plan" / "kata-grill-standard").mkdir(parents=True)
    (home / "skills" / "plan" / "kata-grill-standard" / "SKILL.md").write_text(
        "---\nname: kata-grill-standard\n---\n", encoding="utf-8"
    )
    (home / "modules" / "closeout" / "kata-closeout").mkdir(parents=True)
    (home / "modules" / "closeout" / "kata-closeout" / "SKILL.md").write_text(
        "---\nname: kata-closeout\n---\n", encoding="utf-8"
    )
    (home / "README.md").write_text("# KataHarness v0.1.0-alpha.3\n", encoding="utf-8")
    return home


# ---------------------------------------------------------------------------
# Helper: parse JSON from the front of a mixed stdout string
# ---------------------------------------------------------------------------


def _parse_result_json(stdout: str) -> dict:
    """Extract the first JSON object from a mixed stdout (JSON + note lines)."""
    decoder = json.JSONDecoder()
    result, _ = decoder.raw_decode(stdout.lstrip())
    return result


# ---------------------------------------------------------------------------
# B-7 BC regression / stdout golden (must PASS before and after changes)
# ---------------------------------------------------------------------------


def test_no_flag_stdout_golden(fake_home, tmp_path, capsys):
    """Without any new flag, stdout is pretty-JSON + note lines only; stderr is empty.

    This is the BC regression anchor (PLAN §Slice B test 7 + BUILD NIT 1).
    Verifies the default mixed-stdout path (:360-362) is byte-for-byte preserved
    after the Slice B refactor.
    """
    host = tmp_path / "dot-claude"
    rc = ki.main(
        ["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)]
    )
    assert rc == 0
    out, err = capsys.readouterr()

    # stdout must begin with the pretty-printed JSON result
    result = _parse_result_json(out)
    assert result["ok"] is True
    assert result["platform"] == "claude"
    assert "linked" in result
    assert "method" in result

    # Reconstruct expected stdout using the SAME format as install() -> print pipeline
    reinstall_result = ki.install("claude", harness_home=fake_home, host_dir=host)
    expected_json = json.dumps(reinstall_result, indent=2)
    expected_notes = "".join(
        f"  - {n}\n" for n in reinstall_result.get("notes", [])
    )
    expected_stdout = expected_json + "\n" + expected_notes
    assert out == expected_stdout  # byte-identical to the current format

    # Nothing on stderr in non-json mode
    assert err == ""


# ---------------------------------------------------------------------------
# B-1 New flags parse
# ---------------------------------------------------------------------------


def test_new_flags_non_interactive_parse(fake_home, tmp_path):
    """--non-interactive flag must be accepted by argparse without error."""
    host = tmp_path / "dot-claude"
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--non-interactive",
        ]
    )
    assert rc == 0


def test_new_flags_yes_parse(fake_home, tmp_path):
    """--yes flag (alias for --non-interactive) must be accepted by argparse."""
    host = tmp_path / "dot-claude"
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--yes",
        ]
    )
    assert rc == 0


def test_uninstall_flag_parses(fake_home, tmp_path):
    """--uninstall flag must be recognised by argparse (Slice C wiring)."""
    host = tmp_path / "dot-claude"
    # Install first so uninstall has something to remove
    ki.install("claude", harness_home=fake_home, host_dir=host)
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--uninstall",
        ]
    )
    assert rc == 0  # uninstall exits 0


def test_json_flag_parses(fake_home, tmp_path, capsys):
    """--json flag must be accepted by argparse."""
    host = tmp_path / "dot-claude"
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--json",
        ]
    )
    assert rc == 0
    capsys.readouterr()  # consume output


# ---------------------------------------------------------------------------
# B-2 Non-TTY auto non-interactive
# ---------------------------------------------------------------------------


def test_non_tty_stdin_does_not_block(fake_home, tmp_path, monkeypatch):
    """When stdin is not a TTY, the install must complete without hanging."""
    host = tmp_path / "dot-claude"
    monkeypatch.setattr(
        "sys.stdin", type("_FakeStdin", (), {"isatty": lambda self: False})()
    )
    rc = ki.main(
        ["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)]
    )
    assert rc == 0
    assert (host / "skills" / "kata-bootstrap" / "SKILL.md").exists()


# ---------------------------------------------------------------------------
# B-6 --json channel split
# ---------------------------------------------------------------------------


def test_json_flag_machine_output_on_stdout(fake_home, tmp_path, capsys):
    """--json -> pure machine JSON on stdout; human notes on stderr; stdout parseable."""
    host = tmp_path / "dot-claude"
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--json",
        ]
    )
    assert rc == 0
    out, err = capsys.readouterr()

    # stdout must be valid JSON (and ONLY JSON - no trailing note lines)
    result = json.loads(out)  # raises if stdout is not pure JSON
    assert result["ok"] is True
    assert result["platform"] == "claude"

    # Human-formatted note lines ("  - ...") must be on stderr, NOT on stdout
    # (Note: the JSON result itself contains "notes": [...] — that's expected on stdout)
    assert "  - " in err  # human-formatted note line appears on stderr
    assert "  - " not in out  # no human note lines on stdout with --json


def test_json_flag_stdout_has_no_note_lines(fake_home, tmp_path, capsys):
    """With --json, stdout contains ONLY the JSON object (no '  - ...' lines)."""
    host = tmp_path / "dot-claude"
    ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--json",
        ]
    )
    out, _ = capsys.readouterr()
    # Must be parseable as JSON with nothing extra
    parsed = json.loads(out)
    assert isinstance(parsed, dict)
    # Verify there are no human-note lines embedded
    assert "  - " not in out


# ---------------------------------------------------------------------------
# B-3 Exit codes
# ---------------------------------------------------------------------------


def test_exit_code_not_confirmed_stays_one(fake_home, tmp_path):
    """confirm-probe not confirmed -> exit 1 (preserved from today's :357)."""
    # codex not in PATH in CI - the probe will fail -> rc == 1
    rc = ki.main(["--platform", "codex", "--home", str(fake_home), "--confirm"])
    assert rc == 1


def test_exit_code_malformed_answers_json(fake_home, tmp_path):
    """Malformed JSON in --answers-json -> exit 2 USAGE."""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not { valid } json !!!", encoding="utf-8")

    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--answers-json", str(bad_file),
        ]
    )
    assert rc == 2


def test_exit_code_missing_required_key_answers_json(fake_home, tmp_path):
    """Missing required key in --answers-json -> exit 2 USAGE."""
    bad_file = tmp_path / "missing.json"
    bad_file.write_text(json.dumps({"vaultDir": "/some/path"}), encoding="utf-8")

    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--answers-json", str(bad_file),
        ]
    )
    assert rc == 2


def test_exit_code_missing_answers_json_path(fake_home, tmp_path):
    """--answers-json path that does not exist -> exit 3 NOT_FOUND."""
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--answers-json", str(tmp_path / "nonexistent.json"),
        ]
    )
    assert rc == 3


def test_exit_code_bad_vault_dir_via_answers_json(fake_home, tmp_path):
    """Non-existent vaultDir in --answers-json -> write_settings ValueError -> exit 3 NOT_FOUND."""
    parent = tmp_path / "projects"
    parent.mkdir()

    answers_file = tmp_path / "answers.json"
    answers_file.write_text(
        json.dumps(
            {
                "parentDir": str(parent),
                "vaultDir": str(tmp_path / "nonexistent-vault"),
            }
        ),
        encoding="utf-8",
    )

    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--answers-json", str(answers_file),
        ]
    )
    assert rc == 3


def test_exit_code_bad_parent_dir_via_answers_json(fake_home, tmp_path):
    """Non-existent parentDir in --answers-json -> write_settings ValueError -> exit 3 NOT_FOUND."""
    answers_file = tmp_path / "answers.json"
    answers_file.write_text(
        json.dumps({"parentDir": str(tmp_path / "no-such-dir")}),
        encoding="utf-8",
    )

    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--answers-json", str(answers_file),
        ]
    )
    assert rc == 3


def test_exit_code_non_kata_clobber_is_five(fake_home, tmp_path, capsys):
    """Non-kata dir collision -> exit 5 CONFLICT (not an uncaught traceback)."""
    host = tmp_path / "dot-claude"
    victim = host / "skills" / "kata-bootstrap"
    victim.mkdir(parents=True)
    (victim / "USER_DATA.txt").write_text("precious", encoding="utf-8")

    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
        ]
    )
    assert rc == 5
    # User data must survive
    assert (victim / "USER_DATA.txt").read_text(encoding="utf-8") == "precious"
    # No Python traceback on stdout or stderr
    out, err = capsys.readouterr()
    assert "Traceback" not in out
    assert "Traceback" not in err


def test_exit_code_reinstall_is_zero_noop(fake_home, tmp_path, capsys):
    """Re-installing over kata-managed dirs exits 0; no traceback; valid links present;
    result dict has NO 'changed' key (MAJOR-1: engine result dict not extended)."""
    host = tmp_path / "dot-claude"
    ki.main(
        ["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)]
    )
    capsys.readouterr()  # clear first-run output

    rc = ki.main(
        ["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)]
    )
    out, err = capsys.readouterr()

    assert rc == 0
    # Valid links still present
    assert (host / "skills" / "kata-bootstrap" / "SKILL.md").exists()
    assert (host / "skills" / "kata-closeout" / "SKILL.md").exists()

    # No traceback in either stream
    assert "Traceback" not in out
    assert "Traceback" not in err

    # Parse result -- must NOT contain 'changed' key (MAJOR-1)
    result = _parse_result_json(out)
    assert "changed" not in result


def test_exit_code_unknown_platform_is_three(fake_home):
    """Unknown platform -> install_generic ok:False -> exit 3 NOT_FOUND."""
    rc = ki.main(["--platform", "banana", "--home", str(fake_home)])
    assert rc == 3


# ---------------------------------------------------------------------------
# B-3 / B-4 --answers-json happy path + env-var fallbacks
# ---------------------------------------------------------------------------


def test_answers_json_happy_path_no_tty(fake_home, tmp_path, monkeypatch):
    """--answers-json happy path: writes settings without any TTY interaction."""
    import kata_settings as ks

    parent = tmp_path / "projects"
    parent.mkdir()
    host = tmp_path / "dot-claude"

    answers_file = tmp_path / "answers.json"
    answers_file.write_text(
        json.dumps({"parentDir": str(parent)}),
        encoding="utf-8",
    )

    # Simulate non-TTY stdin
    monkeypatch.setattr(
        "sys.stdin", type("_Fake", (), {"isatty": lambda self: False})()
    )

    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--answers-json", str(answers_file),
        ]
    )
    assert rc == 0
    saved = ks.read_settings(home=fake_home)
    assert Path(saved["parentDir"]) == parent.resolve()


def test_answers_json_with_vault_dir(fake_home, tmp_path):
    """--answers-json with vaultDir writes both parentDir and vaultDir."""
    import kata_settings as ks

    parent = tmp_path / "projects"
    parent.mkdir()
    vault = tmp_path / "vault"
    vault.mkdir()
    host = tmp_path / "dot-claude"

    answers_file = tmp_path / "answers.json"
    answers_file.write_text(
        json.dumps({"parentDir": str(parent), "vaultDir": str(vault)}),
        encoding="utf-8",
    )

    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--answers-json", str(answers_file),
        ]
    )
    assert rc == 0
    saved = ks.read_settings(home=fake_home)
    assert Path(saved["parentDir"]) == parent.resolve()
    assert Path(saved["vaultDir"]) == vault.resolve()


def test_env_var_fallback_kata_parent_dir(fake_home, tmp_path, monkeypatch):
    """KATA_PARENT_DIR env var is used when --parent-dir flag is absent."""
    import kata_settings as ks

    parent = tmp_path / "env-projects"
    parent.mkdir()
    host = tmp_path / "dot-claude"

    monkeypatch.setenv("KATA_PARENT_DIR", str(parent))

    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
        ]
    )
    assert rc == 0
    saved = ks.read_settings(home=fake_home)
    assert Path(saved["parentDir"]) == parent.resolve()


def test_explicit_flag_wins_over_env_var(fake_home, tmp_path, monkeypatch):
    """Explicit --parent-dir wins over KATA_PARENT_DIR env var."""
    import kata_settings as ks

    env_parent = tmp_path / "env-projects"
    env_parent.mkdir()
    flag_parent = tmp_path / "flag-projects"
    flag_parent.mkdir()
    host = tmp_path / "dot-claude"

    monkeypatch.setenv("KATA_PARENT_DIR", str(env_parent))

    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--parent-dir", str(flag_parent),
        ]
    )
    assert rc == 0
    saved = ks.read_settings(home=fake_home)
    # Flag value wins
    assert Path(saved["parentDir"]) == flag_parent.resolve()


def test_answers_json_dot_dot_guard(fake_home, tmp_path):
    """--answers-json with a '..' path component is rejected (CWE-23 guard -> exit 2 or 3)."""
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--answers-json", "../traversal.json",
        ]
    )
    # CWE-23 guard raises ValueError from _safe_abs -> USAGE (2) or NOT_FOUND (3)
    assert rc in (2, 3)


# ---------------------------------------------------------------------------
# B-5 _exit_code_for mapper (unit-level)
# ---------------------------------------------------------------------------


def test_exit_code_for_ok_result():
    """_exit_code_for with ok:True result -> 0 (OK)."""
    assert ki._exit_code_for({"ok": True}) == 0


def test_exit_code_for_not_ok_result():
    """_exit_code_for with ok:False result (unknown platform) -> 3 NOT_FOUND."""
    assert ki._exit_code_for({"ok": False}) == 3


def test_exit_code_for_oserror():
    """_exit_code_for with OSError -> 4 PERMISSION."""
    assert ki._exit_code_for({}, exc=OSError("permission denied")) == 4


def test_exit_code_for_non_kata_valueerror():
    """_exit_code_for with non-kata ValueError -> 5 CONFLICT."""
    err = ValueError("refusing to overwrite non-kata directory: /foo")
    assert ki._exit_code_for({}, exc=err) == 5


def test_exit_code_for_other_valueerror():
    """_exit_code_for with other ValueError -> 3 NOT_FOUND."""
    err = ValueError("parentDir is not an existing directory")
    assert ki._exit_code_for({}, exc=err) == 3


def test_exit_code_for_generic_exception():
    """_exit_code_for with a generic exception -> 1 ERROR."""
    err = RuntimeError("something unexpected")
    assert ki._exit_code_for({}, exc=err) == 1


# ---------------------------------------------------------------------------
# _load_answers_json unit tests
# ---------------------------------------------------------------------------


def test_load_answers_json_happy_path(tmp_path):
    """_load_answers_json returns the dict for a valid file with parentDir."""
    f = tmp_path / "answers.json"
    f.write_text(
        json.dumps({"parentDir": "/some/dir", "vaultDir": "/vault"}),
        encoding="utf-8",
    )
    result = ki._load_answers_json(str(f))
    assert result["parentDir"] == "/some/dir"
    assert result["vaultDir"] == "/vault"


def test_load_answers_json_missing_file(tmp_path):
    """_load_answers_json raises FileNotFoundError when path does not exist."""
    with pytest.raises(FileNotFoundError):
        ki._load_answers_json(str(tmp_path / "no-such.json"))


def test_load_answers_json_malformed_json(tmp_path):
    """_load_answers_json raises ValueError for malformed JSON."""
    f = tmp_path / "bad.json"
    f.write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed"):
        ki._load_answers_json(str(f))


def test_load_answers_json_missing_parent_dir_key(tmp_path):
    """_load_answers_json raises ValueError when required 'parentDir' key is absent."""
    f = tmp_path / "missing_key.json"
    f.write_text(json.dumps({"vaultDir": "/vault"}), encoding="utf-8")
    with pytest.raises(ValueError, match="parentDir"):
        ki._load_answers_json(str(f))


def test_load_answers_json_not_an_object(tmp_path):
    """_load_answers_json raises ValueError when JSON is not a dict."""
    f = tmp_path / "array.json"
    f.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ValueError):
        ki._load_answers_json(str(f))


def test_load_answers_json_dot_dot_guard(tmp_path):
    """_load_answers_json rejects paths with '..' traversal."""
    with pytest.raises((ValueError, SystemExit)):
        ki._load_answers_json("../outside.json")


# ---------------------------------------------------------------------------
# C-1 / C-2 uninstall verb: removes kata-managed skills
# ---------------------------------------------------------------------------


def test_uninstall_removes_kata_symlink(fake_home, tmp_path):
    """uninstall() removes a symlink whose resolved target is under harness home (C-1)."""
    host = tmp_path / "dot-claude"
    ki.install("claude", harness_home=fake_home, host_dir=host)

    skill_link = host / "skills" / "kata-bootstrap"
    assert skill_link.is_symlink() or skill_link.is_dir()  # installed

    result = ki.uninstall("claude", harness_home=fake_home, host_dir=host)
    assert result["ok"] is True
    assert "kata-bootstrap" in result["removed"]
    assert not skill_link.exists()


def test_uninstall_removes_kata_managed_copy(fake_home, tmp_path, monkeypatch):
    """uninstall() removes a .kata-managed copy dir (C-2)."""

    def _deny(*a, **k):
        raise OSError("no symlinks in this test")

    monkeypatch.setattr(ki.os, "symlink", _deny)
    host = tmp_path / "dot-claude"
    ki.install("claude", harness_home=fake_home, host_dir=host)

    copy_dir = host / "skills" / "kata-bootstrap"
    assert (copy_dir / ki._MARKER).exists()  # copy marker present

    result = ki.uninstall("claude", harness_home=fake_home, host_dir=host)
    assert result["ok"] is True
    assert "kata-bootstrap" in result["removed"]
    assert not copy_dir.exists()


def test_uninstall_leaves_non_kata_dir_intact(fake_home, tmp_path):
    """uninstall() does NOT delete non-kata dirs; reports them in leftIntact (C-6)."""
    host = tmp_path / "dot-claude"
    victim = host / "skills" / "kata-bootstrap"
    victim.mkdir(parents=True)
    (victim / "USER_DATA.txt").write_text("precious", encoding="utf-8")

    result = ki.uninstall("claude", harness_home=fake_home, host_dir=host)
    assert result["ok"] is True
    # non-kata dir must be reported, not removed
    assert "kata-bootstrap" not in result.get("removed", [])
    assert any("kata-bootstrap" in s for s in result.get("leftIntact", []))
    # data preserved
    assert (victim / "USER_DATA.txt").read_text(encoding="utf-8") == "precious"


# ---------------------------------------------------------------------------
# C-3 CLI --uninstall removes settings + calls remove_stanza on AGENTS.md
# ---------------------------------------------------------------------------


def test_cli_uninstall_removes_settings_and_stanza(fake_home, tmp_path):
    """CLI --uninstall unlinks .kata-settings.json and strips router stanza from AGENTS.md."""
    import kata_settings as ks
    from kata_router import BEGIN_MARKER, END_MARKER, write_stanza

    host = tmp_path / "dot-claude"
    parent = tmp_path / "projects"
    parent.mkdir()
    target_project = tmp_path / "myproject"
    target_project.mkdir()
    agents_md = target_project / "AGENTS.md"

    # Install + write settings + seed AGENTS.md with a stanza
    ki.install("claude", harness_home=fake_home, host_dir=host)
    ks.write_settings(str(parent), home=fake_home)
    preamble = "# My Project\n\nExisting content.\n"
    agents_md.write_text(preamble, encoding="utf-8")
    write_stanza(agents_md)

    # Verify stanza is present
    content = agents_md.read_text(encoding="utf-8")
    assert BEGIN_MARKER in content
    assert END_MARKER in content

    # Run --uninstall
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--uninstall",
            "--target-dir", str(target_project),
        ]
    )
    assert rc == 0

    # Settings file must be gone
    settings_path = ks.settings_path(home=fake_home)
    assert not settings_path.exists()

    # Router stanza must be removed; preamble preserved
    updated = agents_md.read_text(encoding="utf-8")
    assert BEGIN_MARKER not in updated
    assert END_MARKER not in updated
    assert "Existing content." in updated  # surrounding content intact


def test_cli_uninstall_removes_skill_links(fake_home, tmp_path):
    """CLI --uninstall removes installed skill links from the host skills dir."""
    host = tmp_path / "dot-claude"
    ki.install("claude", harness_home=fake_home, host_dir=host)

    assert (host / "skills" / "kata-bootstrap" / "SKILL.md").exists()

    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--uninstall",
        ]
    )
    assert rc == 0
    assert not (host / "skills" / "kata-bootstrap").exists()
    assert not (host / "skills" / "kata-closeout").exists()
    assert not (host / "skills" / "kata-grill-standard").exists()


# ---------------------------------------------------------------------------
# C-4 Idempotency: second uninstall is a clean no-op
# ---------------------------------------------------------------------------


def test_uninstall_is_idempotent_exit_zero(fake_home, tmp_path, capsys):
    """Re-running --uninstall exits 0 and produces no traceback (C-4)."""
    host = tmp_path / "dot-claude"
    ki.install("claude", harness_home=fake_home, host_dir=host)

    rc1 = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--uninstall",
        ]
    )
    assert rc1 == 0
    capsys.readouterr()

    # Second run -- everything already absent
    rc2 = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--uninstall",
        ]
    )
    out, err = capsys.readouterr()
    assert rc2 == 0
    assert "Traceback" not in out
    assert "Traceback" not in err


def test_uninstall_no_op_when_nothing_installed(fake_home, tmp_path):
    """uninstall() on a clean host (nothing installed) returns ok:True (C-4)."""
    host = tmp_path / "dot-claude"
    result = ki.uninstall("claude", harness_home=fake_home, host_dir=host)
    assert result["ok"] is True
    assert result["removed"] == []


# ---------------------------------------------------------------------------
# C-5 Plugin-manifest removal is flag-gated (default keep)
# ---------------------------------------------------------------------------


def test_uninstall_keeps_plugin_manifest_by_default(fake_home, tmp_path):
    """By default, --uninstall keeps the plugin manifest (it lives in harness home, not host)."""
    ki.ensure_plugin_manifest(fake_home)
    manifest = fake_home / ".claude-plugin" / "plugin.json"
    assert manifest.exists()

    host = tmp_path / "dot-claude"
    ki.install("claude", harness_home=fake_home, host_dir=host)
    ki.uninstall("claude", harness_home=fake_home, host_dir=host)

    # Manifest must still be present (default keep)
    assert manifest.exists()


# ---------------------------------------------------------------------------
# Finding 2: settings-write OSError → exit code 4 PERMISSION
# ---------------------------------------------------------------------------


def test_settings_write_oserror_returns_permission_code(fake_home, tmp_path, monkeypatch, capsys):
    """OSError from write_settings (disk full / unwritable) → exit 4 PERMISSION, no traceback.

    Mutation-proof: removing the except OSError clause → OSError propagates as traceback.
    """
    import kata_settings

    parent = tmp_path / "projects"
    parent.mkdir()
    host = tmp_path / "dot-claude"

    def _raise_oserror(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(kata_settings, "write_settings", _raise_oserror)

    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--parent-dir", str(parent),
        ]
    )

    out, err = capsys.readouterr()
    assert rc == 4, f"Expected exit 4 (PERMISSION) for OSError; got {rc}"
    assert "Traceback" not in out
    assert "Traceback" not in err
