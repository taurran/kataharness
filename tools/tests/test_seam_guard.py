"""test_seam_guard.py — the W8 fail-closed seam guard (`adapters/claude/hooks/kata-seam-guard.py`).

This file is the **deny-tripwire's registered target**: `tools/probe_registry.json`'s
`deny-tripwire` entry runs
``uv run pytest tests/test_seam_guard.py::test_recordless_agent_call_denied -q`` from
``tools/``, and that probe's RESULT is what flips the Guardian enforcement declaration to
``Verified (intercepting)``. So the tests here are not documentation of intent — they are
the evidence the declaration derives from, and every enforcement assertion below runs the
hook **as a subprocess with a payload on stdin**, exactly as the Claude host runs it.

Mutation proofs (each goes RED on the named mutation):
- ``test_recordless_agent_call_denied`` — RED if the deny edge is weakened to a warn, if the
  scope gate is inverted, or if the JSON deny form stops being emitted.
- ``test_hook_asserting_a_single_tool_name_spelling_would_no_op`` — RED if the branch is
  narrowed to one spelling (the probe §2.4 silent-no-op trap).
- ``test_consumed_record_replay_is_denied`` — RED if validation degrades to file existence.
- ``test_stale_record_from_another_run_is_denied`` — RED if the semantic re-validation is
  skipped (T-04 staleness).
- ``test_non_kata_session_is_completely_untouched`` — RED if the hook denies outside a run.
- ``test_internal_error_denies_never_allows`` — RED if the fail-soft precedent is restored.
- ``test_digest_mismatch_reads_as_not_verified`` — RED if the fingerprint stops being
  jointly necessary with the tripwire.
- ``test_capture_is_appended_exactly_once_under_a_forced_race`` — RED if the capture guard
  stops being an exclusive election (G11: raced ``_RACE_ROUNDS`` times).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]  # tools/
sys.path.insert(0, str(ROOT))

import kata_board as kb  # noqa: E402
import kata_dispatch as kd  # noqa: E402
import kata_scope  # noqa: E402

REPO_ROOT = ROOT.parent
HOOK = REPO_ROOT / "adapters" / "claude" / "hooks" / "kata-seam-guard.py"
SNIPPET = REPO_ROOT / "adapters" / "claude" / "settings.snippet.json"
_FROZEN_PLAN = Path(__file__).parent / "fixtures" / "frozen_plan" / "PLAN.md"

#: G11 — a concurrency-bearing property is raced this many times per invocation. Matches
#: ``test_kata_dispatch._RACE_ROUNDS``: the claim-election defect it guards reproduced
#: ~1 run in 5, so a single round could pass while the property was broken.
_RACE_ROUNDS = 25


def _load_hook():
    """Import the hyphen-named hook by path (the ``test_claude_hooks._load`` precedent)."""
    spec = importlib.util.spec_from_file_location("kata_seam_guard_mod", HOOK)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


guard = _load_hook()


# --------------------------------------------------------------------------- helpers


def _run_hook(payload: dict, *, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run the hook exactly as the host does: a JSON event on stdin, nothing on argv."""
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _deny_reason(proc: subprocess.CompletedProcess) -> str | None:
    """The model-facing reason string, or None when the host would NOT have blocked."""
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        out = json.loads(proc.stdout)
    except ValueError:
        return None
    hook_out = out.get("hookSpecificOutput", {})
    if hook_out.get("permissionDecision") != "deny":
        return None
    return hook_out.get("permissionDecisionReason")


def _live_run(tmp_path: Path) -> Path:
    """A directory carrying a LIVE kata run — cursor + the seam-init run marker."""
    root = tmp_path / "project"
    root.mkdir(parents=True, exist_ok=True)
    kd.run_start(root / ".kata", repo_root=str(root))
    return root


def _agent_event(cwd: Path, prompt: str, *, tool_name: str = "Agent") -> dict:
    return {
        "session_id": "s-1",
        "cwd": str(cwd),
        "permission_mode": "bypassPermissions",
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {"description": "d", "prompt": prompt, "subagent_type": "general-purpose"},
        "tool_use_id": "toolu_x",
    }


def _mint(root: Path, **kw) -> dict:
    return kd.mint(
        governs="plan", role="coder", task_id=kw.pop("task_id", "t1"),
        kata_dir=root / ".kata", plan_path=_FROZEN_PLAN, brief={"objective": "build it"}, **kw,
    )


# --------------------------------------------------------------------------- THE TRIPWIRE


def test_recordless_agent_call_denied(tmp_path: Path) -> None:
    """**The registered `probe:deny-tripwire` node.** A record-less Agent launch is BLOCKED.

    Runs the real installed script as a subprocess against a real live run, and asserts
    the host would block: a clean ``exit 0`` carrying ``permissionDecision: "deny"``
    (probe §2.2's form — the model receives only the reason). The reason must NAME THE
    LEGAL PATH, which is DESIGN §1.8's requirement, not a nicety.
    """
    root = _live_run(tmp_path)
    proc = _run_hook(_agent_event(root, "launch a subagent with no record at all"))

    assert proc.returncode == 0, proc.stderr
    reason = _deny_reason(proc)
    assert reason is not None, f"NOT DENIED — stdout={proc.stdout!r} stderr={proc.stderr!r}"
    assert "NO dispatch-record id" in reason
    assert "legal path:" in reason and "kata_dispatch.mint(" in reason

    # The denial is also a cursor DENY event (DESIGN §1.8), not just a model-facing string.
    cursor = kb.read_cursor(root / ".kata")
    assert [ln for ln in cursor.lines if ln.type == "DENY"], "no DENY line on the cursor"


def test_the_tripwire_prober_returns_denied_true(tmp_path: Path) -> None:
    """``live_deny_tripwire`` is the shape ``kata_dispatch.deny_tripwire_probe`` consumes."""
    result = guard.live_deny_tripwire()
    assert result["denied"] is True, result
    assert kd.deny_tripwire_probe(guard.live_deny_tripwire) == {
        "result": "probed", "denied": True,
        "reason": "record-less dispatch denied in kata scope; non-kata session untouched",
    }


# --------------------------------------------------------------------------- deny edge


def test_valid_record_call_passes(tmp_path: Path) -> None:
    """A launch naming a freshly minted record is ALLOWED — silence is the allow."""
    root = _live_run(tmp_path)
    record = _mint(root)
    proc = _run_hook(_agent_event(root, f"SEAM DISPATCH RECORD: {record['recordId']}\nbuild it"))

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "", f"an allowed call must emit nothing, got {proc.stdout!r}"
    # ...and the hook CONSUMED it: the claim is the replay control, not a read.
    assert kd.record_path(root / ".kata", record["recordId"], consumed=True).is_file()
    assert not kd.record_path(root / ".kata", record["recordId"]).is_file()


def test_consumed_record_replay_is_denied(tmp_path: Path) -> None:
    """Replay: the SAME record twice. Second call denied, naming the re-mint path."""
    root = _live_run(tmp_path)
    record = _mint(root)
    event = _agent_event(root, f"record {record['recordId']}")

    first = _run_hook(event)
    assert first.stdout.strip() == "", first.stdout

    second = _run_hook(event)
    reason = _deny_reason(second)
    assert reason is not None, f"REPLAY NOT DENIED — {second.stdout!r}"
    assert "already CONSUMED" in reason
    assert "re-mint" in reason.lower()


def test_stale_record_from_another_run_is_denied(tmp_path: Path) -> None:
    """T-04 stays dead: validation is SEMANTIC, so a hand-copied record file is not enough.

    The record file is present and well-formed at the exact path the engine looks in — an
    existence check would pass it. Its ``runId`` belongs to a rotated-away run, so the
    engine's re-validation refuses.
    """
    root = _live_run(tmp_path)
    stale = _mint(root)
    stale_path = kd.record_path(root / ".kata", stale["recordId"])
    body = json.loads(stale_path.read_text(encoding="utf-8"))

    kd.run_start(root / ".kata", repo_root=str(root), force_new=True)  # rotate: new runId

    stale_path.parent.mkdir(parents=True, exist_ok=True)
    stale_path.write_text(json.dumps(body), encoding="utf-8")  # hand-restore the file
    assert stale_path.is_file()

    reason = _deny_reason(_run_hook(_agent_event(root, f"record {stale['recordId']}")))
    assert reason is not None, "a stale record was ACCEPTED — semantic re-validation is gone"
    assert "not the live run" in reason or "FAILED semantic re-validation" in reason


def test_a_fabricated_record_id_with_no_file_is_denied(tmp_path: Path) -> None:
    """A well-shaped id that was never minted is denied, not treated as absent-and-fine."""
    root = _live_run(tmp_path)
    fake = "run-20200101T000000Z-deadbeef-9"
    reason = _deny_reason(_run_hook(_agent_event(root, f"record {fake}")))
    assert reason is not None
    assert "no pending dispatch record" in reason or "not a dispatch-record id" in reason


def test_two_record_ids_is_an_ambiguous_launch_and_is_refused(tmp_path: Path) -> None:
    root = _live_run(tmp_path)
    a, b = _mint(root, task_id="t1"), _mint(root, task_id="t2")
    reason = _deny_reason(_run_hook(_agent_event(root, f"{a['recordId']} and {b['recordId']}")))
    assert reason is not None and "distinct dispatch-record ids" in reason
    # Neither record was consumed: an ambiguous call must not silently claim one.
    for rec in (a, b):
        assert kd.record_path(root / ".kata", rec["recordId"]).is_file()


def test_hook_asserting_a_single_tool_name_spelling_would_no_op(tmp_path: Path) -> None:
    """probe §2.4's trap: the payload says ``Agent``, the result envelope says ``Task``.

    BOTH spellings must reach the deny edge. A hook that matched ``Task`` in settings and
    then asserted ``tool_name == "Task"`` would silently allow every real call — an
    enforcement layer that looks installed and enforces nothing.
    """
    root = _live_run(tmp_path)
    for spelling in ("Agent", "Task"):
        reason = _deny_reason(_run_hook(_agent_event(root, "no record", tool_name=spelling)))
        assert reason is not None, f"tool_name={spelling!r} was NOT denied"
    assert guard._AGENT_TOOL_NAMES == frozenset({"Agent", "Task"})


# --------------------------------------------------------------------------- scope gate


def test_non_kata_session_is_completely_untouched(tmp_path: Path) -> None:
    """RS-L5: no run marker ⇒ no output, exit 0, whatever the tool. A global install is safe."""
    plain = tmp_path / "not-a-kata-project"
    plain.mkdir()
    for event in (
        _agent_event(plain, "launch with no record"),
        {"hook_event_name": "PreToolUse", "cwd": str(plain), "tool_name": "Bash",
         "tool_input": {"command": "codex exec \"do the thing\""}},
    ):
        proc = _run_hook(event)
        assert proc.returncode == 0
        assert proc.stdout == "", f"non-kata session got output: {proc.stdout!r}"


def test_a_kata_checkout_without_a_live_run_is_not_a_run_scope(tmp_path: Path) -> None:
    """``find_run_marker`` is deliberately NARROWER than ``is_kata_scope``.

    A checkout carrying ``kata.config`` / an empty ``.kata`` answers YES to "is this a kata
    project" and NO to "is a run live here" — so the deny edge stays silent until seam init
    writes the marker.
    """
    root = tmp_path / "checkout"
    (root / ".kata").mkdir(parents=True)
    (root / "kata.config").write_text("{}", encoding="utf-8")
    assert kata_scope.is_kata_scope(root) is True
    assert kata_scope.find_run_marker(root) is None

    proc = _run_hook(_agent_event(root, "no record"))
    assert proc.stdout == "" and proc.returncode == 0


def test_marker_loss_mid_run_reads_as_non_kata(tmp_path: Path) -> None:
    """The STATED marker-loss edge (RS-L5, pass-2 medium 5) — asserted, not assumed.

    A deleted marker reads as a non-kata session and the call proceeds. This is the hook's
    one fail-open window; its residual channel is the post-hoc cursor-lineage audit, which
    still sees the SPAWN line with no matching DENY/VERDICT.
    """
    root = _live_run(tmp_path)
    assert _deny_reason(_run_hook(_agent_event(root, "no record"))) is not None
    kd.run_marker_path(root / ".kata").unlink()
    after = _run_hook(_agent_event(root, "no record"))
    assert after.stdout == "", "marker-loss edge changed shape — update the DESIGN residual"


def test_kata_scope_marker_constants_match_the_engine() -> None:
    """``kata_scope`` mirrors two engine literals rather than importing the seam engine.

    The mirror is deliberate (the module is pure-stdlib and core-legal, and one consumer is
    a host-triggered hook), so the drift risk is closed HERE mechanically.
    """
    assert kata_scope.RUN_MARKER_FILENAME == kd.RUN_MARKER_FILENAME
    assert kata_scope._KATA_DIRNAME == ".kata"
    root = Path(kd.run_marker_path("/tmp/x/.kata")).parent.name
    assert root == kata_scope._KATA_DIRNAME


def test_find_run_marker_delegates_to_the_one_walk(tmp_path: Path) -> None:
    """One walk, two questions (D2 edge-(a)): the marker check ADDS no second loop.

    Pinned structurally as well as behaviourally — ``test_statusline_chain.TestScopeDrift``
    is the AST canary that requires the parent-loop to live in ``find_kata_root`` and
    nowhere else, so a future "just inline the walk here" edit is a RED test, not a review
    catch. Behaviourally: same cap, same root-stop, same fail-soft.
    """
    root = _live_run(tmp_path)
    deep = root / "a" / "b" / "c"
    deep.mkdir(parents=True)
    assert kata_scope.find_run_marker(deep) == kd.run_marker_path(root / ".kata")
    assert kata_scope.find_run_marker(deep, max_levels=1) is None  # cap honoured
    assert kata_scope.find_run_marker(tmp_path / "elsewhere") is None

    calls: list = []
    real = kata_scope.find_kata_root
    try:
        kata_scope.find_kata_root = lambda s, **kw: (calls.append((s, kw)), real(s, **kw))[1]
        assert kata_scope.find_run_marker(deep, max_levels=7) is not None
    finally:
        kata_scope.find_kata_root = real
    assert calls == [(deep, {"max_levels": 7})], "find_run_marker did not delegate the walk"


def test_a_nested_shadowing_scope_reads_as_non_kata(tmp_path: Path) -> None:
    """The STATED shadowing edge: an inner bare ``.kata`` hides an outer live run.

    The delegated walk stops at the FIRST ancestor carrying kata evidence, so an inner
    directory with a marker-less ``.kata`` resolves to "no live run" ⇒ allow. Asserted so
    the edge is a KNOWN residual with a test, not a surprise found in production.
    """
    root = _live_run(tmp_path)
    inner = root / "sub"
    (inner / ".kata").mkdir(parents=True)
    assert kata_scope.find_run_marker(root) is not None
    assert kata_scope.find_run_marker(inner) is None
    assert _run_hook(_agent_event(inner, "no record")).stdout == ""


# --------------------------------------------------------------------------- Bash leg


def test_bash_dispatch_shapes_are_matched_on_the_pre_expansion_literal(tmp_path: Path) -> None:
    """R-M7: ``codex exec`` / ``kiro-cli chat`` without a record are denied — best-effort."""
    root = _live_run(tmp_path)
    for command in (
        'codex exec --model o3 "implement task w1-foo per the frozen PLAN"',
        'kiro-cli chat --no-interactive --trust-all-tools "implement task w1-foo"',
        'PATH="/x/bin:$PATH" codex exec --model o3 "indirection check"',
    ):
        proc = _run_hook({
            "hook_event_name": "PreToolUse", "cwd": str(root), "tool_name": "Bash",
            "tool_input": {"command": command, "description": "d"},
        })
        assert _deny_reason(proc) is not None, f"not denied: {command!r}"


def test_an_ordinary_bash_command_is_never_touched(tmp_path: Path) -> None:
    root = _live_run(tmp_path)
    proc = _run_hook({
        "hook_event_name": "PreToolUse", "cwd": str(root), "tool_name": "Bash",
        "tool_input": {"command": "git status --porcelain"},
    })
    assert proc.stdout == "" and proc.returncode == 0


def test_the_bash_leg_is_evadable_by_indirection_and_says_so() -> None:
    """The honesty label is asserted, not just written: this leg is NOT interception.

    probe §4.1 observed that the hook sees the PRE-EXPANSION literal only. These three
    forms perform a dispatch and match nothing — which is exactly why the Guardian grade
    for this leg is ``Partially verified (bash-leg)`` and never ``Verified (intercepting)``.
    """
    for evasion in (
        'eval "$(printf \'\\x63odex exec "x"\')"',
        "./my-wrapper.sh 'implement task w1-foo'",
        "$DISPATCH_CMD 'implement task w1-foo'",
    ):
        assert guard.is_dispatch_shaped_command(evasion) is False
    assert kd.derive_enforcement(
        {"installed": True, "matches": True}, {"result": "probed", "denied": True},
        bash_leg=True,
    ) == kd.ENFORCEMENT_BASH_LEG


# --------------------------------------------------------------------------- fail CLOSED


def test_internal_error_denies_never_allows(tmp_path: Path, monkeypatch) -> None:
    """probe §5.2's inversion: an exception inside the guard is a DENY, in-process.

    The precedent it breaks is ``kata-gauge-check.py:34-36`` (all hooks fail soft), which is
    right there and wrong here. Asserted on the module's own outer handler so the failure
    can be injected deterministically.
    """
    mod = _load_hook()
    root = _live_run(tmp_path)
    mod._STATE.update({"in_scope": True, "event": "PreToolUse", "kata_dir": root / ".kata"})
    emitted: list[dict] = []
    monkeypatch.setattr(mod, "_emit", emitted.append)
    monkeypatch.setattr(mod, "_record_cursor_deny", lambda *a, **k: None)

    mod._fail_closed(RuntimeError("engine import exploded"))

    assert len(emitted) == 1
    decision = emitted[0]["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "failed internally and therefore DENIES" in decision["permissionDecisionReason"]


def test_internal_error_outside_kata_scope_still_allows(tmp_path: Path, monkeypatch) -> None:
    """The fail-closed inversion is SCOPE-GATED: it never leaks into a non-kata session."""
    mod = _load_hook()
    emitted: list[dict] = []
    monkeypatch.setattr(mod, "_emit", emitted.append)
    mod._STATE.update({"in_scope": False, "event": "PreToolUse", "kata_dir": None})
    mod._fail_closed(RuntimeError("boom"))
    assert emitted == []


def test_garbage_and_empty_stdin_do_not_crash_the_host(tmp_path: Path) -> None:
    """Unparseable input outside a run is a silent exit 0 (no scope ⇒ no standing)."""
    for raw in ("", "not json at all", "[1,2,3]"):
        proc = subprocess.run(
            [sys.executable, str(HOOK)], input=raw, capture_output=True, text=True, timeout=120,
            cwd=str(tmp_path),
        )
        assert proc.returncode == 0, proc.stderr


def test_oversized_payload_denies_with_a_reason(tmp_path: Path) -> None:
    """RS-M11: over the cap ⇒ deny WITH REASON, never a silent pass."""
    root = _live_run(tmp_path)
    event = _agent_event(root, "x" * (guard._MAX_PAYLOAD_BYTES + 4096))
    reason = _deny_reason(_run_hook(event))
    assert reason is not None and "over the" in reason and "cap" in reason


def test_internal_deadline_is_strictly_below_the_settings_timeout() -> None:
    """RS-M11: the host must never be the one that kills this hook.

    A host timeout was OBSERVED to fail OPEN (probe §5.1: ``exit_code: 1``,
    ``outcome: "cancelled"``, empty stdout/stderr, and the Agent call PROCEEDED). The
    internal deadline is therefore pinned strictly below the value recorded in settings.
    """
    entries = json.loads(SNIPPET.read_text(encoding="utf-8-sig"))["hooks"]
    timeouts = {
        h["timeout"]
        for event in ("PreToolUse", "PostToolUse", "SubagentStop")
        for entry in entries[event] for h in entry["hooks"] if "kata-seam-guard" in h["command"]
    }
    assert timeouts == {guard._HOST_TIMEOUT_S}
    assert guard._INTERNAL_DEADLINE_S < guard._HOST_TIMEOUT_S


# --------------------------------------------------------------------------- RS-M10 / RS-H4


def test_settings_entry_records_the_full_command_and_the_install_digest() -> None:
    """RS-M10: the entry records the FULL expected command string + the script digest.

    The digest is over the file's committed bytes. ``.gitattributes`` pins ``* text=auto
    eol=lf``, so the working tree is LF on every platform and the digest is stable — a
    CRLF checkout would otherwise make this a per-machine value.
    """
    digest = hashlib.sha256(HOOK.read_bytes()).hexdigest()
    raw = json.loads(SNIPPET.read_text(encoding="utf-8-sig"))["hooks"]

    found = 0
    for event, matcher in (("PreToolUse", "Agent|Task"), ("PreToolUse", "Bash"),
                           ("PostToolUse", "Agent|Task"), ("SubagentStop", None)):
        for entry in raw[event]:
            if entry.get("matcher") != matcher:
                continue
            for hook in entry["hooks"]:
                assert "kata-seam-guard.py" in hook["command"]
                assert hook["command"].startswith('"<repo>/tools/.venv/Scripts/python.exe"')
                assert hook["digest"] == digest, (
                    "settings digest is stale — update settings.snippet.json to "
                    f"{digest} (RS-M10: the install record must match the script)"
                )
                found += 1
    assert found == 4, f"expected all four seam-guard entries, found {found}"


def test_the_engine_consistency_check_sees_the_registered_entry() -> None:
    """TM-H2 settings-drift detection, wired against the REAL snippet + the REAL script."""
    settings = json.loads(SNIPPET.read_text(encoding="utf-8-sig"))
    fingerprint = kd.hook_fingerprint(REPO_ROOT)
    assert fingerprint["installed"] is True

    out = kd.config_settings_consistency({"hooks": {"seamGuard": True}}, settings,
                                         fingerprint=fingerprint)
    assert out["settingsRegistered"] is True and out["hookInstalled"] is True
    assert out["consistent"] is True, out["drift"]


def test_digest_mismatch_reads_as_not_verified() -> None:
    """RS-H4: tripwire and fingerprint are JOINTLY necessary — a green tripwire cannot
    rescue a script whose bytes are not the approved ones."""
    denied = {"result": "probed", "denied": True}
    good = kd.hook_fingerprint(REPO_ROOT, expected_digest=hashlib.sha256(HOOK.read_bytes()).hexdigest())
    bad = kd.hook_fingerprint(REPO_ROOT, expected_digest="0" * 64)

    assert good["matches"] is True
    assert bad["matches"] is False
    assert kd.derive_enforcement(bad, denied) == kd.ENFORCEMENT_DORMANT
    assert kd.derive_enforcement(good, denied) == kd.ENFORCEMENT_INTERCEPTING

    settings = json.loads(SNIPPET.read_text(encoding="utf-8-sig"))
    tampered = json.loads(json.dumps(settings))
    tampered["hooks"]["PreToolUse"][0]["hooks"][0]["digest"] = "0" * 64
    drift = kd.config_settings_consistency(None, tampered, fingerprint=good)
    assert "hook-digest-mismatch" in drift["drift"]


def test_run_start_declaration_flips_to_verified_intercepting(tmp_path: Path) -> None:
    """**The acceptance sentence, end to end.** The declaration DERIVES from the live probe.

    ``run_start`` is handed the real prober (:func:`live_deny_tripwire`, which spawns the
    real script) and the real expected digest; the declaration it renders is the one the
    run reports. Nothing here asserts enforcement — it reads the derivation's output.
    """
    digest = hashlib.sha256(HOOK.read_bytes()).hexdigest()
    out = kd.run_start(
        tmp_path / ".kata", repo_root=str(REPO_ROOT),
        expected_hook_digest=digest, tripwire_prober=guard.live_deny_tripwire,
    )
    assert out["hook"]["installed"] is True and out["hook"]["matches"] is True
    assert out["tripwire"]["result"] == "probed" and out["tripwire"]["denied"] is True
    assert out["enforcement"] == kd.ENFORCEMENT_INTERCEPTING
    assert out["declaration"].splitlines()[0] == "enforcement: Verified (intercepting)"


def test_no_result_tripwire_lands_on_dormant_never_inherits(tmp_path: Path) -> None:
    """RS-H4's load-bearing clause, asserted against THIS hook's presence.

    A broken hook is indistinguishable from an absent one from inside the session, so a
    tripwire that returns no result must land on Dormant even though the file is installed
    and its digest matches.
    """
    digest = hashlib.sha256(HOOK.read_bytes()).hexdigest()
    out = kd.run_start(tmp_path / ".kata", repo_root=str(REPO_ROOT),
                       expected_hook_digest=digest, tripwire_prober=None)
    assert out["hook"]["matches"] is True
    assert out["tripwire"]["result"] == "no-result"
    assert out["enforcement"] == kd.ENFORCEMENT_DORMANT


def test_a_neutered_hook_fails_the_tripwire(tmp_path: Path, monkeypatch) -> None:
    """The tripwire's own mutation proof: a hook that no-ops must NOT read as denied."""
    mod = _load_hook()
    monkeypatch.setattr(mod, "_handle_pre_tool_use", lambda payload: None)
    monkeypatch.setattr(mod, "_HANDLERS", {**mod._HANDLERS, "PreToolUse": lambda p: None})

    def _neutered_spawn(payload, timeout_s):  # noqa: ARG001
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(mod, "_spawn_self", _neutered_spawn)
    result = mod.live_deny_tripwire()
    assert result["denied"] is False
    assert kd.derive_enforcement(
        {"installed": True, "matches": True},
        kd.deny_tripwire_probe(mod.live_deny_tripwire),
    ) == kd.ENFORCEMENT_DORMANT


def test_a_blanket_denier_fails_the_scope_leg(tmp_path: Path, monkeypatch) -> None:
    """Leg 2's mutation proof: denying EVERYTHING must not read as Verified."""
    mod = _load_hook()

    def _always_deny(payload, timeout_s):  # noqa: ARG001
        return subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps(mod._deny_payload("PreToolUse", "blanket")), stderr="",
        )

    monkeypatch.setattr(mod, "_spawn_self", _always_deny)
    result = mod.live_deny_tripwire()
    assert result["denied"] is False
    assert "RS-L5 scope gate is broken" in result["reason"]


# --------------------------------------------------------------------------- capture edge


def _post_event(root: Path, rid: str, *, agent_id: str, content: str | None) -> dict:
    response: dict = {"agentId": agent_id, "agentType": "general-purpose",
                      "resolvedModel": "claude-haiku-4-5-20251001"}
    if content is None:
        response.update({"isAsync": True, "status": "async_launched"})
    else:
        response.update({"status": "completed", "content": [{"type": "text", "text": content}]})
    return {
        "hook_event_name": "PostToolUse", "cwd": str(root), "tool_name": "Agent",
        "tool_input": {"description": "d", "prompt": f"record {rid}"},
        "tool_response": response, "tool_use_id": "toolu_x",
    }


def _substop_event(root: Path, agent_id: str, message: str) -> dict:
    return {
        "hook_event_name": "SubagentStop", "cwd": str(root), "agent_id": agent_id,
        "agent_type": "general-purpose", "last_assistant_message": message,
        "stop_hook_active": False,
    }


def _verdict_lines(root: Path) -> list:
    return [ln for ln in kb.read_cursor(root / ".kata").lines if ln.type == "VERDICT"]


def test_sync_path_captures_from_the_post_edge(tmp_path: Path) -> None:
    """probe §3.2: ``tool_response.content[0].text`` is the complete return envelope."""
    root = _live_run(tmp_path)
    record = _mint(root)
    kd.claim_record(root / ".kata", record["recordId"])  # the deny edge would have claimed it

    proc = _run_hook(_post_event(root, record["recordId"], agent_id="ag1",
                                 content="VERDICT: PASS\nevidence: none."))
    assert proc.returncode == 0, proc.stderr
    lines = _verdict_lines(root)
    assert len(lines) == 1 and "verdict=PASS" in lines[0].msg
    assert "capture=post-edge" in lines[0].msg


def test_async_path_captures_from_subagent_stop(tmp_path: Path) -> None:
    """probe §3.3/§3.4: the async post edge carries a HANDLE, not content.

    ``status: async_launched``, no ``content`` key, and the advertised ``outputFile`` was
    empty when inspected — so the verdict has to come from ``SubagentStop``, and the
    ``agentId`` binding written here is the only thing that can correlate it (SubagentStop
    carries no ``tool_use_id``).
    """
    root = _live_run(tmp_path)
    record = _mint(root)
    kd.claim_record(root / ".kata", record["recordId"])

    _run_hook(_post_event(root, record["recordId"], agent_id="ag2", content=None))
    assert _verdict_lines(root) == []  # nothing to capture yet — and no fabricated verdict

    _run_hook(_substop_event(root, "ag2", "VERDICT: PASS_ASYNC"))
    lines = _verdict_lines(root)
    assert len(lines) == 1 and "verdict=PASS_ASYNC" in lines[0].msg


def test_subagent_stop_without_a_binding_captures_nothing(tmp_path: Path) -> None:
    """No binding ⇒ no correlation ⇒ no line. A capture is never guessed onto a record."""
    root = _live_run(tmp_path)
    _mint(root)
    proc = _run_hook(_substop_event(root, "unknown-agent", "VERDICT: PASS"))
    assert proc.returncode == 0
    assert _verdict_lines(root) == []


def test_capture_is_appended_exactly_once_across_both_edges(tmp_path: Path) -> None:
    """Both edges fire for the same record; exactly ONE VERDICT line results."""
    root = _live_run(tmp_path)
    record = _mint(root)
    kd.claim_record(root / ".kata", record["recordId"])

    _run_hook(_post_event(root, record["recordId"], agent_id="ag3", content="VERDICT: PASS"))
    _run_hook(_substop_event(root, "ag3", "VERDICT: PASS"))
    assert len(_verdict_lines(root)) == 1


@pytest.mark.parametrize("round_", range(3))
def test_capture_is_appended_exactly_once_under_a_forced_race(tmp_path: Path, round_) -> None:
    """G11: the capture guard is an ELECTION, raced in-process with forced interleaving.

    ``_capture_once`` is the concurrency-bearing property (two edges, one record). The
    guard is the same ``O_CREAT|O_EXCL`` primitive the engine's claim uses, for the reason
    ``kata_dispatch.claim_record`` measured on this host: a rename-to-self is a documented
    no-op success on Windows, so only exclusive-create is a genuine election on both
    platforms. Threads are released from a barrier so they collide at the guard, and the
    run is repeated ``_RACE_ROUNDS`` times per invocation.
    """
    mod = _load_hook()
    root = _live_run(tmp_path / f"r{round_}")
    kata = root / ".kata"

    for i in range(_RACE_ROUNDS):
        record = _mint(root, task_id=f"t{i}")
        kd.claim_record(kata, record["recordId"])
        rid = record["recordId"]
        barrier = threading.Barrier(4)
        results: list = []
        lock = threading.Lock()

        def contend() -> None:
            barrier.wait()
            out = mod._capture_once(kata, rid, "VERDICT: PASS")
            with lock:
                results.append(out)

        threads = [threading.Thread(target=contend) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)

        winners = [r for r in results if r is not None]
        assert len(winners) == 1, f"round {i}: {len(winners)} winners, expected exactly 1"
        assert winners[0] == "PASS"

    verdicts = _verdict_lines(root)
    assert len(verdicts) == _RACE_ROUNDS, f"{len(verdicts)} lines for {_RACE_ROUNDS} records"


def test_a_refused_capture_releases_the_guard_for_the_other_edge(tmp_path: Path) -> None:
    """A verdict-less envelope must not permanently suppress the record's real verdict.

    ``parse_verdict`` is strict by design (line 1 only, no body scan), so an envelope with
    no ``VERDICT:`` line is a refusal — and a refusal that kept the guard would silently
    lose the verdict the other edge is about to deliver.
    """
    root = _live_run(tmp_path)
    record = _mint(root)
    kd.claim_record(root / ".kata", record["recordId"])
    kata = root / ".kata"

    assert guard._capture_once(kata, record["recordId"], "no verdict here at all") is None
    assert not (kata / "hook-capture" / f"{record['recordId']}.captured").exists()
    assert guard._capture_once(kata, record["recordId"], "VERDICT: PASS") == "PASS"
    assert len(_verdict_lines(root)) == 1


def test_a_hostile_agent_id_never_reaches_the_filesystem(tmp_path: Path) -> None:
    """CWE-22/CWE-23: host-supplied ids are interpolated into filenames ⇒ closed charset."""
    for hostile in ("../../etc/passwd", "a/b", "a\\b", "", "x" * 200, None, 7):
        assert guard._safe_id(hostile) is None
    assert guard._safe_id("a794c33fb3386dec1") == "a794c33fb3386dec1"


# --------------------------------------------------------------------------- grammar pins


def test_record_grammar_matches_the_engine_guard() -> None:
    """The hook's extraction grammar and the engine's path guard accept the SAME ids."""
    good = "run-20260817T034343Z-e3b50e43-84"
    assert guard.extract_record_ids([f"prefix {good} suffix"]) == [good]
    assert kd._guard_record_id(good) == good
    for bad in ("run-2026-08-17-abc-1", "run-20260817T034343Z-XYZ-1", "notarecord"):
        assert guard.extract_record_ids([bad]) == []
        with pytest.raises(kd.RecordClaimRefused):
            kd._guard_record_id(bad)


def test_extract_record_ids_is_order_stable_and_deduplicating() -> None:
    a, b = "run-20260101T000000Z-aaaa-1", "run-20260101T000000Z-bbbb-2"
    assert guard.extract_record_ids([f"{a} {b} {a}", None, 7, f"{b}"]) == [a, b]
    assert guard.extract_record_ids([]) == []


def test_the_hook_never_shells_out_and_parses_input_structurally() -> None:
    """DESIGN §8 S2 + the exec-safety row: structured parse, no shell, no eval/exec."""
    source = HOOK.read_text(encoding="utf-8")
    assert "shell=True" not in source
    assert "shlex" not in source
    for forbidden in ("eval(", "exec(", "os.system", "os.popen"):
        assert forbidden not in source, f"{forbidden} in the seam guard"
    assert "kata-seam-guard" in (REPO_ROOT / "protocol" / "exec-safety.md").read_text(encoding="utf-8")


def test_the_registered_probe_argv_targets_this_file() -> None:
    """G29: ``probe:deny-tripwire`` must actually exercise the tripwire it names."""
    import evidence_grammar

    entry = evidence_grammar.load_probe_registry()["deny-tripwire"]
    assert entry.status == "active", "the W8 flip did not land"
    node = entry.argv[-2]
    path, name = node.split("::")
    assert (REPO_ROOT / entry.cwd / path) == Path(__file__).resolve()
    assert name == "test_recordless_agent_call_denied"
    assert name in globals(), "the registered node id does not exist in this module"


def test_the_deliberate_break_with_the_fail_soft_precedent_is_stated_in_both_files() -> None:
    """DESIGN §8 S6: "that difference is stated in both files" — asserted, not trusted."""
    guard_src = HOOK.read_text(encoding="utf-8")
    gauge_src = (REPO_ROOT / "adapters" / "claude" / "hooks" / "kata-gauge-check.py").read_text(
        encoding="utf-8")
    assert "kata-gauge-check.py:34-36" in guard_src
    assert "FAIL-SOFT / NEVER EXIT 2" in gauge_src
