"""adapters/claude/hooks/kata-seam-guard.py — the FAIL-CLOSED seam guard (PLAN W8).

The last switch of the Trust Model burn. Three edges in one script, dispatched on
``hook_event_name``:

* **deny edge** (``PreToolUse`` on ``Agent``/``Task``) — an agent launch that carries no
  VALID dispatch record is DENIED, with a message naming the legal path (DESIGN §1.8).
  "Valid" is decided by the engine's SEMANTIC re-validation
  (:func:`kata_dispatch.claim_and_validate` = atomic single-use claim + re-run of every
  mint predicate), **never by file existence** — a stale, replayed, or hand-copied record
  fails exactly there, which is what keeps the T-04 staleness class dead (TM-B4).
* **Bash leg** (``PreToolUse`` on ``Bash``) — the same rule applied to ``codex exec`` /
  ``kiro-cli chat`` dispatch shapes on the pre-expansion command literal. **Best-effort,
  declared `Partially verified (bash-leg)`, NEVER "intercepting"** (R-M7): see LIMITS.
* **capture edge** (``PostToolUse`` on ``Agent``/``Task`` + ``SubagentStop``) — appends the
  seam-authored VERDICT line mechanically via :func:`kata_dispatch.capture`, correlated
  through the dispatch record. Both events are wired because **neither alone closes the
  loop** (probe §3.4).

Activation order is TM-H1's binding law: this hook lands only after every sanctioned
dispatch path is migrated to the seam, because a hook activated early denies legitimate
un-migrated sites and the soft "warn-only" interim is the REJECTED shape.

------------------------------------------------------------------------------------
BUILT TO WHAT THE W1 PROBE OBSERVED — .planning/specs/trust-model/evidence/hook-probe.md
------------------------------------------------------------------------------------
1. **Fail-open is the governing limit (probe §5.1/§5.2/§5.3).** A hook that times out or
   crashes lets the call THROUGH; the host reports `exit_code: 1` and moves on. Only a
   clean ``exit 2`` or a clean ``exit 0`` carrying ``permissionDecision: "deny"`` blocks.
   Consequences, all implemented below:
   - **Internal error ⇒ DENY** (:func:`_main`'s outer handler), the deliberate INVERSION
     of the all-hooks-fail-soft precedent at ``kata-gauge-check.py:34-36``. That precedent
     is correct THERE (a ``UserPromptSubmit`` exit 2 erases the user's prompt) and wrong
     here. The inversion is scope-gated: it applies only inside a live kata run.
   - **An internal deadline strictly below the host's** (:data:`_INTERNAL_DEADLINE_S` =
     10s vs the settings entry's ``"timeout": 20``), enforced by a watchdog that emits the
     deny and exits 0 rather than letting the host kill us into an ambiguous state (RS-M11).
   - **Post-hoc verification is MANDATORY, not belt-and-braces.** A hook that silently died
     is indistinguishable from an absent one from inside the session, which is why
     :func:`live_deny_tripwire` exists and why a no-result tripwire lands on
     ``Dormant (pre-activation)`` and NEVER inherits a prior declaration (RS-H4).
2. **The matcher-naming trap (probe §2.4).** The hook payload always says
   ``tool_name: "Agent"``; the RESULT envelope says ``"Task"``. A hook that matches ``Task``
   and then asserts ``tool_name == "Task"`` silently no-ops on every call — an enforcement
   layer that looks installed and enforces nothing. This file matches ``Agent|Task`` in
   settings and branches on :data:`_AGENT_TOOL_NAMES` (both spellings), never on one.
3. **Capture needs BOTH edges (probe §3.2-§3.4).** ``PostToolUse.tool_response.content``
   exists ONLY on the synchronous path; the async path returns a handle and an
   empty ``outputFile``. ``SubagentStop.last_assistant_message`` carries the verdict text
   on BOTH paths but has no ``tool_use_id``. So: PostToolUse captures when it has content
   and always records the ``agentId`` binding; SubagentStop captures from the binding.
   Whichever edge gets there first wins an atomic exclusive guard, so the two edges can
   never double-append (order-independence achieved by the guard, not assumed).
4. **Deny survives ``--dangerously-skip-permissions``** (probe §2.3) — every probe ran
   under ``bypassPermissions`` and the deny held. Load-bearing for unattended shapes.
5. **The Bash leg sees the PRE-EXPANSION literal** (probe §4/§4.1) — untruncated to at
   least 1468 chars, but shell expansion is invisible and indirection defeats
   shape-matching. Hence best-effort, never "intercepting".

UNPROBED / NOT PROBED — scopes this file makes NO claim about (probe §5.4, §7):
interactive (non-headless) sessions · the Kiro host · the Codex host · a nested
Agent-denies-Agent launch (nested Bash deny WAS observed; nested Agent is an inference) ·
POSIX hosts · Claude Code versions other than 2.1.233 · user/local settings scope (the
probes loaded PROJECT scope only — the run-marker gate below is what makes a global
install safe, and it is exercised by :func:`live_deny_tripwire`'s second leg).

Contract:
- Stdin: the hook event JSON. Parsed STRUCTURED, never string-eval'd (DESIGN §8 S2, and
  this file is registered in ``protocol/exec-safety.md``'s sink registry for its one
  subprocess sink — the tripwire's self-spawn).
- **Scope gate FIRST (RS-L5):** the seam-init RUN MARKER (``kata_scope.find_run_marker``).
  Marker present ⇒ a kata run is live ⇒ fail closed on every error from here on. Marker
  absent ⇒ **emit nothing, exit 0** — a non-kata session is untouched, whatever the tool.
  The marker read is the hook's ONE fail-open window and is a stated residual; a marker
  deleted mid-run reads as non-kata and its residual channel is the post-hoc
  cursor-lineage audit at the next gate.
- Deny form: the JSON ``permissionDecision`` (probe §2.2) — the model receives ONLY the
  reason string, so DESIGN §1.8's "name the legal path" sentence arrives verbatim instead
  of buried behind the ``exit 2`` form's interpreter-path noise.
- Every denial is also a cursor DENY event (DESIGN §1.8), best-effort: a cursor that
  cannot be written is NEVER allowed to swallow the refusal itself.

Usage:
    Wired by the ``PreToolUse`` / ``PostToolUse`` / ``SubagentStop`` entries in
    adapters/claude/settings.snippet.json. Also runnable directly:

        python adapters/claude/hooks/kata-seam-guard.py < event.json
        python adapters/claude/hooks/kata-seam-guard.py --tripwire
"""

from __future__ import annotations

import json
import os
import re
import subprocess  # the tripwire's ONE registered sink — see _spawn_self / protocol/exec-safety.md
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Optional

# --------------------------------------------------------------------------- constants

#: The subagent tool's TWO spellings (probe §2.4). Branching on one of them is the
#: silent-no-op trap; this set is the guard against it.
_AGENT_TOOL_NAMES: frozenset[str] = frozenset({"Agent", "Task"})

#: A dispatch-record id, mirroring ``kata_dispatch._guard_record_id``'s grammar
#: (``run-<utc>-<hex>-<seq>``). Pinned against the engine by
#: ``test_seam_guard.py::test_record_grammar_matches_the_engine_guard``.
_RECORD_RE = re.compile(r"run-\d{8}T\d{6}Z-[0-9a-f]+-\d+")

#: Off-host dispatch shapes the Bash leg recognises on the PRE-EXPANSION literal
#: (probe §4). Word-boundary anchored; whitespace-tolerant between the two tokens.
_BASH_DISPATCH_RE = re.compile(r"\b(codex\s+exec|kiro-cli\s+chat)\b")

#: Payload cap (RS-M11). A payload larger than this is not parsed for validation — in
#: kata scope that is a DENY WITH REASON, never a silent pass.
_MAX_PAYLOAD_BYTES = 1_048_576

#: The hook's internal deadline, seconds. **Strictly below the host timeout** recorded in
#: settings.snippet.json (20s) — RS-M11's "the host can never kill the hook into an
#: ambiguous state". Pinned as a pair by
#: ``test_seam_guard.py::test_internal_deadline_is_strictly_below_the_settings_timeout``.
_INTERNAL_DEADLINE_S = 10.0

#: The settings-recorded host timeout this file is pinned against (see above).
_HOST_TIMEOUT_S = 20

#: Bound on the tripwire's self-spawn. Generous: it is a seam-init act, not a per-call one.
_TRIPWIRE_TIMEOUT_S = 90

#: Correlation + idempotency artifacts live here, under the run's own kata dir.
_CAPTURE_DIRNAME = "hook-capture"

#: Host-supplied ids are interpolated into filenames ⇒ closed charset (CWE-22/CWE-23),
#: mirroring the ``kata-gauge-check._SAFE_SESSION_ID`` precedent.
_SAFE_ID_RE = re.compile(r"\A[A-Za-z0-9._-]{1,128}\Z")

#: The legal path a record-less launch is told to take (DESIGN §1.8 — never a bare refusal).
_LEGAL_PATH = (
    "mint a dispatch record first — kata_dispatch.mint(governs=..., role=..., task_id=..., "
    "kata_dir=..., brief=...) — and name its recordId in the launched brief; never launch "
    "an agent without one, and never reuse a consumed record"
)

#: Mutable per-process state the watchdog consults. A watchdog that fired a deny outside
#: kata scope would break RS-L5, so the scope decision is recorded here the moment it is made.
_STATE: dict[str, Any] = {"in_scope": False, "event": None, "kata_dir": None}


# --------------------------------------------------------------------------- emit


def _emit(obj: dict) -> None:
    """Write one JSON object to stdout (the host's structured channel)."""
    sys.stdout.write(json.dumps(obj))
    sys.stdout.flush()


def _deny_payload(event: str, reason: str) -> dict:
    """The probe-§2.2 deny form: the model receives ONLY ``permissionDecisionReason``."""
    return {
        "hookSpecificOutput": {
            "hookEventName": event,
            "permissionDecision": "deny",
            "permissionDecisionReason": f"{reason} ;; legal path: {_LEGAL_PATH}",
        }
    }


def _record_cursor_deny(reason: str, *, task: str = "run") -> None:
    """Append the cursor DENY event (DESIGN §1.8). Best-effort, NEVER load-bearing.

    A cursor that cannot be written must not swallow the refusal — the deny has already
    been emitted to the host by the time this runs.
    """
    kata_dir = _STATE.get("kata_dir")
    if not kata_dir:
        return
    try:
        engine = _import_engine()
        engine.deny(kata_dir, reason, legal_path=_LEGAL_PATH, task=task, agent="hook")
    except Exception as exc:  # noqa: BLE001 — breadcrumb only
        _breadcrumb(f"cursor DENY not recorded: {type(exc).__name__}: {exc}")


def _deny(event: str, reason: str, *, task: str = "run") -> None:
    """Emit the deny, then record it. Emission FIRST — the block is the load-bearing act."""
    _emit(_deny_payload(event, reason))
    _record_cursor_deny(reason, task=task)


def _breadcrumb(text: str) -> None:
    """One stderr line so a broken install is distinguishable from a clean no-op."""
    try:
        sys.stderr.write(f"[kata-seam-guard] {text}\n")
    except Exception:  # noqa: BLE001
        pass


# --------------------------------------------------------------------------- engine


def _tools_dir() -> Path:
    """``<harness>/tools`` — this file lives at ``<harness>/adapters/claude/hooks/``."""
    return Path(__file__).resolve().parents[3] / "tools"


def _import_scope():
    """Import the shared kata-scope helper (pure stdlib; safe before the scope decision)."""
    tools = str(_tools_dir())
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import kata_scope  # noqa: PLC0415 — deferred: sys.path must be set first

    return kata_scope


def _import_engine():
    """Import the seam engine. Only ever called AFTER the scope gate has passed."""
    tools = str(_tools_dir())
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import kata_dispatch  # noqa: PLC0415 — deferred: sys.path must be set first

    return kata_dispatch


# --------------------------------------------------------------------------- pure helpers


def extract_record_ids(payload_texts) -> list[str]:
    """Every DISTINCT dispatch-record id appearing in *payload_texts*, in first-seen order.

    The dispatch payload is fully visible to the hook (probe §2.5: ``tool_input`` carries
    the entire ``prompt`` string, ``description`` and ``subagent_type``), so the record
    token travels in the brief itself and needs no side channel.

    Returns a LIST, not a single value, deliberately: zero ids and two-or-more ids are
    different refusals, and collapsing them would let an ambiguous launch pick a record.
    """
    seen: list[str] = []
    for text in payload_texts:
        if not isinstance(text, str):
            continue
        for match in _RECORD_RE.findall(text):
            if match not in seen:
                seen.append(match)
    return seen


def _agent_texts(tool_input: Any) -> list[str]:
    """The Agent-call fields a record token may legally travel in."""
    if not isinstance(tool_input, dict):
        return []
    return [tool_input.get("prompt"), tool_input.get("description")]


def is_dispatch_shaped_command(command: Any) -> bool:
    """True when the pre-expansion Bash literal looks like an off-host dispatch (R-M7).

    **Best-effort by construction, and the honesty label travels with it.** The probe
    established as OBSERVED FACT (§4.1) that this leg cannot see shell expansion and is
    evadable by indirection — a wrapper script, an alias, or ``eval "$(printf ...)"``
    performs the same dispatch behind a literal that matches nothing here. Therefore this
    leg's Guardian grade is ``Partially verified (bash-leg)`` and **only the Agent-tool leg
    may ever read as "intercepting"**.
    """
    return isinstance(command, str) and _BASH_DISPATCH_RE.search(command) is not None


def _safe_id(raw: Any) -> Optional[str]:
    """A host-supplied id that is safe to interpolate into a filename, or None."""
    if not isinstance(raw, str) or ".." in raw or not _SAFE_ID_RE.match(raw):
        return None
    return raw


# --------------------------------------------------------------------------- scope gate


def _scope_gate(payload: dict) -> Optional[Path]:
    """Resolve the kata dir of the LIVE run this call belongs to, or None (RS-L5).

    None means: not a kata run ⇒ the caller emits nothing and exits 0. This is the ONLY
    place the hook is permitted to be permissive.
    """
    scope = _import_scope()
    start = scope.resolve_start(payload) or Path(os.getcwd())
    marker = scope.find_run_marker(start)
    if marker is None:
        return None
    return marker.parent


# --------------------------------------------------------------------------- deny edge


def _validate_or_deny(event: str, texts: list, *, what: str, task: str) -> None:
    """The shared deny-edge body: find the record, then re-validate it SEMANTICALLY.

    Emits a deny and returns on any refusal; returns silently (no output = allow) on a
    clean claim+validation. Never raises — an unexpected exception is the caller's
    fail-CLOSED path, and this function's own engine errors are converted here.
    """
    kata_dir = _STATE["kata_dir"]
    ids = extract_record_ids(texts)

    if not ids:
        _deny(event, f"{what} carries NO dispatch-record id — a record-less launch is "
                     "denied (DESIGN §1.8)", task=task)
        return
    if len(ids) > 1:
        _deny(event, f"{what} names {len(ids)} distinct dispatch-record ids ({', '.join(ids)}) "
                     "— an ambiguous launch is refused rather than resolved by guesswork", task=task)
        return

    rid = ids[0]
    engine = _import_engine()
    try:
        engine.claim_and_validate(kata_dir, rid)
    except engine.RecordClaimRefused as exc:
        # Consumed / lost-the-race / never-minted. A legitimate retry racing its OWN
        # consumed record is told to re-mint, in the engine's own words (pass-2 low 11).
        _emit(_deny_payload(
            event,
            f"{exc} ;; if this is a legitimate retry: {engine.RETRY_RACE_LEGAL_PATH}",
        ))
        _record_cursor_deny(engine.retry_race_deny_message(rid), task=task)
        return
    except engine.SeamError as exc:
        # Semantic re-validation failed: wrong run, no cursor lineage, governor no longer
        # met, role mismatch, brief-hash mismatch. This is the T-04 staleness class dying.
        _deny(event, f"dispatch record {rid} FAILED semantic re-validation: {exc}", task=task)
        return
    # Valid record, now consumed. Emit nothing — silence is the allow.


def _handle_pre_tool_use(payload: dict) -> None:
    """PreToolUse: the deny edge (Agent/Task) and the best-effort Bash leg."""
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    task = _safe_id(payload.get("session_id")) or "run"

    if tool_name in _AGENT_TOOL_NAMES:
        _validate_or_deny(
            "PreToolUse", _agent_texts(tool_input),
            what="this Agent launch", task=task,
        )
        return

    if tool_name == "Bash":
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        if not is_dispatch_shaped_command(command):
            return  # not a dispatch shape — allow, untouched
        _validate_or_deny(
            "PreToolUse", [command],
            what="this off-host dispatch command", task=task,
        )
        return

    # Any other tool: not this hook's business. (The settings entries only register
    # Agent|Task and Bash; this branch is the belt for a hand-widened matcher.)
    return


# --------------------------------------------------------------------------- capture edge


def _capture_dir(kata_dir: Path) -> Path:
    return Path(kata_dir) / _CAPTURE_DIRNAME


def _write_binding(kata_dir: Path, agent_id: str, rid: str) -> None:
    """Record ``agentId -> recordId`` so SubagentStop can correlate (probe §3.4's gap)."""
    target = _capture_dir(kata_dir) / f"agent-{agent_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump({"agentId": agent_id, "recordId": rid}, fh, sort_keys=True)
        os.replace(tmp_name, target)
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass


def _read_binding(kata_dir: Path, agent_id: str) -> Optional[str]:
    try:
        data = json.loads((_capture_dir(kata_dir) / f"agent-{agent_id}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    rid = data.get("recordId") if isinstance(data, dict) else None
    return rid if isinstance(rid, str) and _RECORD_RE.fullmatch(rid) else None


def _capture_once(kata_dir: Path, rid: str, envelope: Any) -> Optional[str]:
    """Append the VERDICT line for *rid* AT MOST ONCE across both capture edges.

    The guard is an ``O_CREAT|O_EXCL`` token — the same primitive the engine's claim uses,
    and for the same measured reason (:func:`kata_dispatch.claim_record`'s docstring: on
    Windows a rename-to-self is a documented no-op success, so only exclusive-create is a
    genuine election on both platforms). PostToolUse (sync path, has content) and
    SubagentStop (both paths) race here by design; exactly one wins.

    A capture that then FAILS releases the token, so a lost verdict is retryable by the
    other edge rather than permanently suppressed.
    """
    guard = _capture_dir(kata_dir) / f"{rid}.captured"
    guard.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(guard, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return None  # the other edge already captured this record
    except OSError as exc:
        _breadcrumb(f"capture guard unavailable for {rid}: {exc}")
        return None
    os.close(fd)

    engine = _import_engine()
    try:
        result = engine.capture(envelope, rid, kata_dir=kata_dir, kind="verdict", source="post-edge")
    except Exception as exc:  # noqa: BLE001 — CaptureRefused and anything else
        try:
            os.unlink(guard)
        except OSError:
            pass
        _breadcrumb(f"capture refused for {rid}: {type(exc).__name__}: {exc}")
        return None
    return result.get("verdict")


def _handle_post_tool_use(payload: dict) -> None:
    """PostToolUse(Agent): bind identity ALWAYS; capture when this path carried content.

    Probe §3.2/§3.3: ``tool_response.content[0].text`` is the complete return envelope on
    the SYNCHRONOUS path only. On the async path ``status`` is ``async_launched``, there is
    no ``content`` key at all, and the advertised ``outputFile`` was empty (0 bytes) — so
    "read the outputFile here" is NOT a working substitute. The binding is therefore
    written unconditionally and the verdict is taken wherever it actually exists.
    """
    kata_dir = _STATE["kata_dir"]
    ids = extract_record_ids(_agent_texts(payload.get("tool_input")))
    if len(ids) != 1:
        return  # nothing to correlate to; the deny edge already refused any such launch
    rid = ids[0]

    response = payload.get("tool_response")
    response = response if isinstance(response, dict) else {}
    agent_id = _safe_id(response.get("agentId"))
    if agent_id:
        _write_binding(kata_dir, agent_id, rid)

    content = response.get("content")
    if isinstance(content, list) and content:
        _capture_once(kata_dir, rid, content[0])


def _handle_subagent_stop(payload: dict) -> None:
    """SubagentStop: the capture edge that works on BOTH paths (probe §3.4).

    ``last_assistant_message`` carries the verdict text, first line included, on the sync
    AND async paths. What it lacks is ``tool_use_id`` — hence the PostToolUse binding.
    """
    kata_dir = _STATE["kata_dir"]
    agent_id = _safe_id(payload.get("agent_id"))
    if not agent_id:
        return
    rid = _read_binding(kata_dir, agent_id)
    if not rid:
        return  # no binding: the async post edge has not run, or this is not our subagent
    message = payload.get("last_assistant_message")
    if not isinstance(message, str) or not message:
        return
    _capture_once(kata_dir, rid, message)


# --------------------------------------------------------------------------- watchdog


def _arm_watchdog() -> threading.Timer:
    """Deny-and-exit at :data:`_INTERNAL_DEADLINE_S`, strictly before the host's timeout.

    Probe §5.1 observed that a host timeout kills the hook and the call PROCEEDS, with
    ``output``/``stdout``/``stderr`` all empty — a silent fail-open. This watchdog converts
    that into a clean, reasoned deny while the process is still ours (RS-M11).

    Outside kata scope, and on the non-blocking capture edges, it exits 0 silently: the
    scope gate's posture is not negotiable by a timer.
    """
    def fire() -> None:
        if _STATE.get("in_scope") and _STATE.get("event") == "PreToolUse":
            try:
                _emit(_deny_payload(
                    "PreToolUse",
                    f"kata-seam-guard exceeded its internal deadline of "
                    f"{_INTERNAL_DEADLINE_S:g}s (host timeout {_HOST_TIMEOUT_S}s) — a guard that "
                    "cannot finish DENIES rather than letting the host kill it into a "
                    "silent fail-open (DESIGN §8 RS-M11)",
                ))
            except Exception:  # noqa: BLE001
                pass
        os._exit(0)

    timer = threading.Timer(_INTERNAL_DEADLINE_S, fire)
    timer.daemon = True
    timer.start()
    return timer


# --------------------------------------------------------------------------- main


_HANDLERS = {
    "PreToolUse": _handle_pre_tool_use,
    "PostToolUse": _handle_post_tool_use,
    "SubagentStop": _handle_subagent_stop,
}


def _main() -> None:
    """Read the event, gate on scope, dispatch to the edge handler."""
    raw = sys.stdin.buffer.read()
    oversized = len(raw) > _MAX_PAYLOAD_BYTES
    text = raw.decode("utf-8", errors="replace")

    try:
        payload = json.loads(text) if text.strip() else {}
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    # ---- scope gate FIRST (RS-L5). Everything above this line is stdlib-only and
    # cannot touch the seam engine, so a non-kata session pays nothing and sees nothing.
    kata_dir = _scope_gate(payload)
    if kata_dir is None:
        return
    _STATE["in_scope"] = True
    _STATE["kata_dir"] = kata_dir

    event = payload.get("hook_event_name")
    _STATE["event"] = event

    if oversized:
        # RS-M11: oversized ⇒ deny WITH REASON, recorded. On a capture edge there is
        # nothing to deny, so it is recorded and dropped.
        reason = (
            f"hook payload is {len(raw)} bytes, over the {_MAX_PAYLOAD_BYTES}-byte cap — "
            "refusing to validate an unbounded payload"
        )
        if event == "PreToolUse":
            _deny("PreToolUse", reason)
        else:
            _record_cursor_deny(reason)
        return

    handler = _HANDLERS.get(event)
    if handler is None:
        return
    handler(payload)


def _fail_closed(exc: BaseException) -> None:
    """The INVERSION of the fail-soft precedent: an internal error DENIES (probe §5.3).

    Only inside a live kata run, and only on the blocking edge — a capture-edge crash has
    no call to block, and outside kata scope the hook has no standing to deny anything.
    """
    detail = f"{type(exc).__name__}: {exc}"
    _breadcrumb(f"internal error: {detail}")
    if not _STATE.get("in_scope"):
        return
    if _STATE.get("event") != "PreToolUse":
        _record_cursor_deny(f"seam guard internal error on the capture edge: {detail}")
        return
    _deny(
        "PreToolUse",
        "kata-seam-guard failed internally and therefore DENIES: a guard that cannot "
        f"decide must not let the call through ({detail})",
    )


# --------------------------------------------------------------------------- tripwire


def _spawn_self(payload: dict, timeout_s: int) -> subprocess.CompletedProcess:
    """Run THIS hook exactly as the host runs it. **The registered subprocess sink.**

    Structured argv, ``shell=False``, fixed program (``sys.executable``) and a fixed
    script path (this file, resolved) — no element originates from any payload field.
    Registered by name in ``protocol/exec-safety.md``.
    """
    return subprocess.run(  # noqa: S603 — fixed argv, shell=False, exec-safety-registered
        [sys.executable, str(Path(__file__).resolve())],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        shell=False,
    )


def _tripwire_payload(cwd: str, *, tool_name: str = "Agent") -> dict:
    """A synthetic RECORD-LESS PreToolUse Agent dispatch — the self-test that MUST be denied."""
    return {
        "session_id": "kata-seam-guard-tripwire",
        "cwd": cwd,
        "permission_mode": "bypassPermissions",
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {
            "description": "seam-guard deny tripwire",
            "prompt": "TRIPWIRE: this dispatch deliberately carries no dispatch record.",
            "subagent_type": "general-purpose",
        },
        "tool_use_id": "toolu_katatripwire",
    }


def _is_deny(proc: subprocess.CompletedProcess) -> bool:
    """True iff the host would BLOCK on this hook run (probe §5.3's rule, applied)."""
    if proc.returncode == 2:
        return True  # the exit-2 deny form
    if proc.returncode != 0:
        return False  # timeout / crash / anything else FAILS OPEN — never read as a deny
    try:
        out = json.loads(proc.stdout)
    except ValueError:
        return False
    hook_out = out.get("hookSpecificOutput") if isinstance(out, dict) else None
    return isinstance(hook_out, dict) and hook_out.get("permissionDecision") == "deny"


def live_deny_tripwire() -> dict:
    """The LIVE deny-tripwire (RS-H4). Shape: ``kata_dispatch.deny_tripwire_probe``'s prober.

    Two legs, because one would be forgeable in opposite directions:

    1. **in a live kata run, a record-less Agent dispatch MUST be denied** — the
       enforcement claim itself;
    2. **outside any kata run, the SAME dispatch must produce NO output at all** — without
       this, a hook that denies everything unconditionally would pass leg 1 and read as
       "Verified (intercepting)" while breaking every non-kata session (RS-L5).

    Both legs spawn THIS file as a subprocess with a synthetic payload on stdin, so what is
    probed is the real installed script end to end — not an in-process shortcut that could
    stay green while the installed entry point is broken. File presence proves nothing: a
    mid-session install reads present-but-inactive and a neutered hook reads
    present-and-green, which is exactly why the tripwire and the fingerprint are jointly
    necessary.

    Returns ``{"denied": bool, "reason": str | None}``. Any failure to complete returns
    ``denied: False``, which ``derive_enforcement`` maps to ``Dormant (pre-activation)`` —
    **no result NEVER inherits a prior declaration.**
    """
    engine = _import_engine()
    with tempfile.TemporaryDirectory(prefix="kata-seam-tripwire-") as tmp:
        root = Path(tmp).resolve()
        scoped = root / "scoped"
        unscoped = root / "unscoped"
        scoped.mkdir()
        unscoped.mkdir()

        # Leg 1 — a genuine live run: run_start writes the cursor AND the run marker.
        engine.run_start(scoped / ".kata", repo_root=str(scoped))
        try:
            denied_proc = _spawn_self(_tripwire_payload(str(scoped)), _TRIPWIRE_TIMEOUT_S)
        except (OSError, subprocess.SubprocessError) as exc:
            return {"denied": False, "reason": f"tripwire could not run the hook: {exc}"}
        if not _is_deny(denied_proc):
            return {
                "denied": False,
                "reason": (
                    f"record-less Agent dispatch was NOT denied in a live kata run "
                    f"(exit {denied_proc.returncode}, stdout {denied_proc.stdout[:200]!r})"
                ),
            }

        # Leg 2 — no run marker anywhere above: the hook must be invisible.
        try:
            quiet_proc = _spawn_self(_tripwire_payload(str(unscoped)), _TRIPWIRE_TIMEOUT_S)
        except (OSError, subprocess.SubprocessError) as exc:
            return {"denied": False, "reason": f"tripwire could not run the scope leg: {exc}"}
        if quiet_proc.returncode != 0 or quiet_proc.stdout.strip():
            return {
                "denied": False,
                "reason": (
                    f"non-kata session was NOT left untouched (exit {quiet_proc.returncode}, "
                    f"stdout {quiet_proc.stdout[:200]!r}) — RS-L5 scope gate is broken"
                ),
            }

    return {
        "denied": True,
        "reason": "record-less dispatch denied in kata scope; non-kata session untouched",
    }


# --------------------------------------------------------------------------- entry point


if __name__ == "__main__":
    if "--tripwire" in sys.argv[1:]:
        _result = live_deny_tripwire()
        _emit(_result)
        sys.stdout.write("\n")
        raise SystemExit(0 if _result["denied"] else 3)

    _watchdog = _arm_watchdog()
    try:
        _main()
    except BaseException as exc:  # noqa: BLE001 — fail CLOSED, deliberately (probe §5.3)
        _fail_closed(exc)
    finally:
        _watchdog.cancel()
