"""kata_dispatch.py — cross-model worker dispatch (N1 brief + N2 adapters + N3 result).

The multi-model loop routes a ROLE to a platform/model (kata_roles) and dispatches a
worker on that platform over the shared filesystem (DESIGN multi-model-orchestration):

  build_brief()  ->  BRIEF.json   (N1, the cross-model task contract)
  dispatch()     ->  runs the platform's headless CLI in a worktree (N2)
  normalize()    ->  RESULT.json  (N3, per-role payload + envelope)

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
from pathlib import Path

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
    if any(part == ".." for part in Path(result_path).parts):
        raise ValueError(f"kata_dispatch: resultPath may not contain '..': {result_path!r}")
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


def _brief_prompt(brief: dict) -> str:
    """The prompt text handed to the worker: objective + acceptance + the result-file contract."""
    return (
        f"{brief['objective']}\n\n"
        f"Acceptance: {brief['acceptanceCriteria']}\n"
        f"Write your result as JSON for role '{brief['role']}' to: {brief['resultPath']}"
    )


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
        "--cd", str(worktree),
        "--sandbox", sandbox,
        "--model", brief["model"],
        "-o", brief["resultPath"],
        _brief_prompt(brief),
    ]


# adapter registry: platform -> command builder. Claude uses the in-process Agent path
# (no external CLI) and is handled by the orchestrator, not here.
_COMMAND_BUILDERS = {"codex": codex_command}


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


def _subprocess_runner(cmd: list[str], cwd: str, result_path: str, timeout: int):
    """Default real runner: shell out, then read the worker's result file. Gated on the CLI existing."""
    rp = _safe_result_path(result_path, cwd)
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)  # noqa: S603
    result_text = rp.read_text(encoding="utf-8") if rp.exists() else ""
    return proc.returncode, proc.stdout, result_text


def dispatch(brief: dict, worktree: str, runner=None, timeout: int = 600) -> dict:
    """Dispatch a worker for ``brief`` in ``worktree``; return a normalized RESULT envelope (N2→N3).

    ``runner(cmd, cwd, result_path, timeout) -> (exit_code, stdout, result_text)`` is injectable
    (a stub in tests; the real subprocess runner by default).
    """
    platform = brief["platform"]
    builder = _COMMAND_BUILDERS.get(platform)
    if builder is None:
        raise ValueError(f"kata_dispatch: no dispatch adapter for platform {platform!r}")
    cmd = builder(brief, worktree)
    runner = runner or _subprocess_runner

    try:
        exit_code, stdout, result_text = runner(cmd, worktree, brief["resultPath"], timeout)
    except subprocess.TimeoutExpired:
        return build_result(brief["taskId"], brief["role"], platform, brief["model"], "timeout", {}, raw="")

    if exit_code != 0:
        return build_result(
            brief["taskId"], brief["role"], platform, brief["model"], "failed",
            {"error": f"worker exited {exit_code}"}, raw=stdout,
        )
    try:
        payload = normalize(brief["role"], result_text)
    except (ValueError, TypeError, AttributeError, json.JSONDecodeError) as e:
        return build_result(
            brief["taskId"], brief["role"], platform, brief["model"], "failed",
            {"error": f"unparseable result: {e}"}, raw=result_text,
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
    data = json.loads(raw_text) if raw_text.strip() else {}
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
        return {"score": data.get("score"), "decision": decision, "reason": data.get("reason", "")}
    if role == "researcher":
        return {
            "claim": data.get("claim"), "source": data.get("source"),
            "confidence": data.get("confidence"), "groundsToPlan": data.get("groundsToPlan"),
        }
    # coder / orchestrator: pass through the worker's reported object
    return data
