"""kata_dispatch.py — cross-model worker dispatch (N1 brief + N2 adapters + N3 result).

The multi-model loop routes a ROLE to a platform/model (kata_roles) and dispatches a
worker on that platform over the shared filesystem (DESIGN multi-model-orchestration):

  build_brief()  ->  the cross-model task-contract dict (N1; persisted as BRIEF.json by the caller)
  dispatch()     ->  runs the platform's headless CLI in a worktree (N2)
  normalize()    ->  the per-role result payload (N3); build_result() wraps it in the envelope
                     a caller persists as RESULT.json

These functions RETURN dicts; they do not themselves write BRIEF.json / RESULT.json (the
orchestrator owns persistence). `"fallback"` status covers the LD7 host-fallback path;
dispatch is wired into kata-orchestrate (Slice A of the multi-model layer build).

The CLI launch is behind an **injectable runner** so the whole chain is testable with a
stub CLI (no live host). The default runner shells out for real (gated on the CLI being
installed + confirmed). Per-platform CLI flags are point-in-time (RESEARCH §0/§6) — the
install confirm-probe is the standing guard; pin/verify at build.

Public API
----------
build_brief(task_id, role, platform, *, model, objective, result_path, ...) -> dict   # N1
codex_command(brief, worktree) -> list[str]                                            # N2 (codex adapter)
dispatch(brief, worktree, runner=None, timeout=600) -> dict                            # N2 -> N3
normalize(role, raw_text) -> dict                                                      # N3 per-role payload
build_result(task_id, role, platform, model, status, payload, raw="") -> dict          # N3 envelope
"""

from __future__ import annotations

import json
import subprocess  # noqa: S404 — used only by the default real runner; tests inject a stub
from pathlib import Path, PurePosixPath, PureWindowsPath

from kata_roles import ROLE_GROUPS

_SANDBOX = frozenset({"read-only", "write"})
_STATUS = frozenset({"completed", "failed", "timeout", "fallback"})


# --------------------------------------------------------------------------- N1
def build_brief(
    task_id: str,
    role: str,
    platform: str,
    *,
    model: str,
    objective: str,
    result_path: str,
    inputs: list[str] | None = None,
    owned_files: list[str] | None = None,
    sandbox: str = "read-only",
    acceptance: str = "",
    output_contract: str | None = None,
) -> dict:
    """Build the cross-model task-brief (N1). Pure; validates role + sandbox."""
    if role not in ROLE_GROUPS:
        raise ValueError(f"kata_dispatch: unknown role {role!r}")
    if sandbox not in _SANDBOX:
        raise ValueError(f"kata_dispatch: sandbox must be one of {sorted(_SANDBOX)}, got {sandbox!r}")
    if not objective or not result_path:
        raise ValueError("kata_dispatch: objective and result_path are required")
    # Absolute under EITHER OS convention (Windows treats a leading "/" as drive-relative, not absolute),
    # or containing "..", is rejected — resultPath must stay inside the worktree.
    if (PurePosixPath(result_path).is_absolute() or PureWindowsPath(result_path).is_absolute()
            or any(part == ".." for part in Path(result_path).parts)):
        raise ValueError(f"kata_dispatch: resultPath must be worktree-relative, no '..': {result_path!r}")
    return {
        "taskId": task_id,
        "role": role,
        "platform": platform,
        "model": model,
        "objective": objective,
        "inputs": inputs or [],
        "boundaries": {"ownedFiles": owned_files or [], "sandbox": sandbox},
        "outputContract": output_contract or role,
        "resultPath": result_path,
        "acceptanceCriteria": acceptance,
    }


def _brief_prompt(brief: dict, capture: str = "emit") -> str:
    """The prompt handed to the worker: objective + inputs + boundaries + the result contract.

    ``capture="emit"`` (codex/default): the result is captured by the adapter's ``-o`` flag from
    the worker's FINAL message — the worker emits and does NOT write the result file itself.
    ``capture="write"`` (kiro): kiro has no ``-o`` capture (DESIGN §4 N2); the prompt instructs
    the worker to write the result JSON to ``resultPath`` directly.  ``_subprocess_runner`` reads
    ``resultPath`` after the run in both cases, so both paths converge at the same read point.
    """
    parts = [brief["objective"]]
    if brief.get("inputs"):
        parts.append("Inputs: " + ", ".join(brief["inputs"]))
    owned = brief.get("boundaries", {}).get("ownedFiles") or []
    if owned:
        parts.append("You may only modify: " + ", ".join(owned))
    parts.append(f"Acceptance: {brief['acceptanceCriteria']}")
    parts.append(f"Output contract: a single JSON object for role '{brief['role']}' ({brief['outputContract']}).")
    if capture == "write":
        parts.append(f"Write that JSON object to the file `{brief['resultPath']}`.")
    else:
        parts.append("Emit that JSON object as your FINAL message — it is captured automatically; do not write files.")
    return "\n".join(parts)


# --------------------------------------------------------------------------- N2
def codex_command(brief: dict, worktree: str) -> list[str]:
    """Build the `codex exec` command for a brief (the codex dispatch adapter).

    Uses ``-o <resultPath>`` to capture the worker's final JSON message to the result file;
    the prompt instructs the worker to emit JSON for its role. (A real per-role JSON-Schema
    file could later be passed to ``--output-schema`` for hard constraint — NOT the result
    path itself; passing the output path as the schema was a latent bug, fixed here.)
    """
    sandbox = "workspace-write" if brief["boundaries"]["sandbox"] == "write" else "read-only"
    return [
        "codex", "exec",
        "--skip-git-repo-check",
        "--cd", str(worktree),
        "--sandbox", sandbox,
        "--model", brief["model"],
        "-o", brief["resultPath"],
        _brief_prompt(brief, capture="emit"),
    ]


def kiro_command(brief: dict, worktree: str) -> list[str]:
    """Build the ``kiro-cli chat`` command for a brief (the kiro dispatch adapter).

    Launches kiro in headless mode with the assigned role as the agent.  Because kiro has no
    ``-o`` capture flag (DESIGN §4 N2), ``_brief_prompt`` is called with ``capture="write"``
    so the prompt instructs the worker to write the result JSON to ``resultPath`` itself.
    ``_subprocess_runner`` then reads ``resultPath`` after the run — the same read point as
    the codex path, so both adapters converge at N3 normalize.

    Command shape (DESIGN §4 N2, June-2026 point-in-time snapshot — RESEARCH §0/§6):
        kiro-cli chat --no-interactive --agent <role> <prompt>
    ⚠ Pin/verify these flags at build; the N5 confirm-probe is the standing guard against
    stale flag names between kiro-cli releases.
    """
    return [
        "kiro-cli", "chat",
        "--no-interactive",
        "--agent", brief["role"],
        _brief_prompt(brief, capture="write"),
    ]


# adapter registry: platform -> command builder. Claude uses the in-process Agent path
# (no external CLI) and is handled by the orchestrator, not here.
_COMMAND_BUILDERS = {"codex": codex_command, "kiro": kiro_command}


def _safe_result_path(result_path: str, cwd: str) -> Path:
    """Resolve ``result_path`` strictly UNDER ``cwd`` (CWE-23). Reject ``..`` and any escape.

    Mirrors the ``_safe_abs`` ``..``-guard the rest of the codebase applies (kata_install /
    kata_settings) — the result file must live inside the worker's worktree, never outside it.
    """
    if any(part == ".." for part in Path(result_path).parts):
        raise ValueError(f"kata_dispatch: refusing resultPath with '..' traversal: {result_path!r}")
    base = Path(cwd).resolve()
    rp = (base / result_path).resolve()
    if base != rp and base not in rp.parents:
        raise ValueError(f"kata_dispatch: resultPath escapes the worktree: {result_path!r}")
    return rp


_STDERR_TAIL_CHARS = 4000
_STDERR_TRUNCATION_MARKER = f"[stderr truncated to last {_STDERR_TAIL_CHARS} chars]\n"


def _stderr_tail(stderr) -> str:
    """Deterministic tail cap for worker stderr carried into RESULT envelopes.

    The ONE dispatch-side choke point (injected runners cannot bypass it): keeps the LAST
    ``_STDERR_TAIL_CHARS`` chars — provider error text (rate-limit/quota/auth) arrives at the
    END of stderr — prepending a literal marker only when clipped. Accepts ``bytes``
    (``TimeoutExpired.stderr`` is bytes on some platforms) and decodes tolerantly.
    Pure function of its input (Determinism Doctrine).
    """
    if stderr is None:
        return ""
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    if len(stderr) > _STDERR_TAIL_CHARS:
        return _STDERR_TRUNCATION_MARKER + stderr[-_STDERR_TAIL_CHARS:]
    return stderr


def _subprocess_runner(cmd: list[str], cwd: str, result_path: str, timeout: int):
    """Default real runner: shell out, then read the worker's result file. Gated on the CLI existing."""
    rp = _safe_result_path(result_path, cwd)
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)  # noqa: S603
    result_text = rp.read_text(encoding="utf-8") if rp.exists() else ""
    return proc.returncode, proc.stdout, proc.stderr, result_text


def dispatch(brief: dict, worktree: str, runner=None, timeout: int = 600) -> dict:
    """Dispatch a worker for ``brief`` in ``worktree``; return a normalized RESULT envelope (N2→N3).

    ``runner(cmd, cwd, result_path, timeout) -> (exit_code, stdout, stderr, result_text)`` is
    injectable (a stub in tests; the real subprocess runner by default). The worker's stderr is
    carried — tail-capped via ``_stderr_tail`` — into the payload of every FAILURE envelope
    (exit≠0 / timeout / unparseable result) so the provider error signal survives dispatch;
    the ``completed`` envelope is byte-unchanged and ``raw`` keeps stdout-only semantics.
    """
    platform = brief["platform"]
    builder = _COMMAND_BUILDERS.get(platform)
    if builder is None:
        # No adapter for this platform → fail gracefully (LD7 surfaces it / host-fallback),
        # never crash the loop. (A confirmed-but-undispatchable platform must not raise.)
        return build_result(
            brief["taskId"], brief["role"], platform, brief.get("model"), "failed",
            {"error": f"no dispatch adapter for platform {platform!r}"}, raw="",
        )
    cmd = builder(brief, worktree)
    runner = runner or _subprocess_runner

    try:
        exit_code, stdout, stderr, result_text = runner(cmd, worktree, brief["resultPath"], timeout)
    except subprocess.TimeoutExpired as exc:
        # Captured-so-far stderr rides the timeout envelope — a quota-hung worker's last words.
        payload: dict = {}
        tail = _stderr_tail(getattr(exc, "stderr", None))
        if tail:
            payload["stderr"] = tail
        return build_result(brief["taskId"], brief["role"], platform, brief["model"], "timeout", payload, raw="")

    stderr_tail = _stderr_tail(stderr)
    if exit_code != 0:
        payload = {"error": f"worker exited {exit_code}"}
        if stderr_tail:
            payload["stderr"] = stderr_tail
        return build_result(
            brief["taskId"], brief["role"], platform, brief["model"], "failed",
            payload, raw=stdout,
        )
    try:
        payload = normalize(brief["role"], result_text)
    except (ValueError, TypeError, AttributeError, json.JSONDecodeError) as e:
        payload = {"error": f"unparseable result: {e}"}
        if stderr_tail:
            payload["stderr"] = stderr_tail
        return build_result(
            brief["taskId"], brief["role"], platform, brief["model"], "failed",
            payload, raw=result_text,
        )
    return build_result(brief["taskId"], brief["role"], platform, brief["model"], "completed", payload, raw=stdout)


# --------------------------------------------------------------------------- N3
def build_result(task_id, role, platform, model, status: str, payload: dict, raw: str = "") -> dict:
    """Build the RESULT envelope (N3). ``status`` = the DISPATCH OUTCOME (not the verdict)."""
    if status not in _STATUS:
        raise ValueError(f"kata_dispatch: status must be one of {sorted(_STATUS)}, got {status!r}")
    return {
        "taskId": task_id, "role": role, "platform": platform, "model": model,
        "status": status, "payload": payload, "raw": raw,
    }


def normalize(role: str, raw_text: str) -> dict:
    """Map a worker's raw JSON output to the ROLE's payload shape (N3). Raises on a missing verdict.

    The verdict lives in the payload (distinct from the envelope ``status``):
    - validator  -> {verdict: "ship"|"hold", findings: [...]}
    - evaluator  -> {score: 0.0-1.0, decision: "accept"|"send-back"|"reroll", reason}
    - researcher -> {claim, source, confidence, groundsToPlan}
    - coder      -> {resultJson?, diffPath?}  (the gate RESULT.json is produced separately)
    """
    if not raw_text.strip():
        raise ValueError(f"empty worker result for role {role!r} (default-FAIL)")
    data = json.loads(raw_text)
    if not isinstance(data, dict):
        raise ValueError(f"worker result must be a JSON object, got {type(data).__name__}")
    if role == "validator":
        verdict = data.get("verdict")
        if verdict not in {"ship", "hold"}:
            raise ValueError(f"validator result missing verdict ship|hold (got {verdict!r})")
        return {"verdict": verdict, "findings": data.get("findings", [])}
    if role == "evaluator":
        decision = data.get("decision")
        if decision not in {"accept", "send-back", "reroll"}:
            raise ValueError(f"evaluator result missing decision accept|send-back|reroll (got {decision!r})")
        score = data.get("score")
        if score is not None and (isinstance(score, bool) or not isinstance(score, (int, float)) or not 0.0 <= score <= 1.0):
            raise ValueError(f"evaluator score must be a number in [0.0, 1.0] (got {score!r})")
        return {"score": score, "decision": decision, "reason": data.get("reason", "")}
    if role == "researcher":
        if not (data.get("claim") or data.get("groundsToPlan")):
            raise ValueError("researcher result missing both claim and groundsToPlan (default-FAIL)")
        claim = data.get("claim")
        source = data.get("source")
        # Q-13: an ungrounded claim is not a finding.  Mirror escalation.build_finding's
        # source-required rule (D136 fail-closed): when a claim is asserted, its citation
        # is mandatory and must be a non-empty string.  Without this a cross-model
        # researcher result with a claim but no source silently flowed in as completed.
        # (The confidence/groundsToPlan enum from build_finding is NOT replicated here:
        # this role's schema uses a numeric confidence and free-text groundsToPlan.)
        if claim and not (isinstance(source, str) and source.strip()):
            raise ValueError(
                "researcher result has an ungrounded claim: 'source' citation is required "
                "and must be a non-empty string (default-FAIL)"
            )
        return {
            "claim": claim, "source": source,
            "confidence": data.get("confidence"), "groundsToPlan": data.get("groundsToPlan"),
        }
    # coder / orchestrator: pass through the worker's reported object, but reject an empty one
    if not data:
        raise ValueError(f"empty payload for role {role!r} (default-FAIL)")
    return data
