"""End-to-end stub-runner proof for the dispatch-authoring roles (KH-T13, T4).

Proves the whole chain round-trips using the injectable stub runner
(``tools/kata_dispatch.py``'s ``dispatch(runner=...)`` seam — the same seam already proven for
validator->codex, ``.planning/DECISIONS.md`` D-record 1032-1033) for the two new
``design-author``/``plan-author`` roles: resolve_roles -> build_brief -> dispatch(stub) ->
normalized payload. No live CLI/network call is made anywhere in this file.

Kept separate from ``test_kata_roles.py``/``test_kata_dispatch.py`` (T1's owned files) to avoid a
file-ownership collision between T1 and T4 (PLAN.md T4 action).
"""

from __future__ import annotations

import json

import kata_dispatch as kd
import kata_roles as kr


def test_design_author_round_trip_on_codex(tmp_path):
    """resolve_roles -> build_brief -> dispatch(stub) yields a completed envelope with designPath."""
    resolved = kr.resolve_roles({"design-author": {"platform": "codex"}}, ["codex"])
    assert resolved["design-author"]["platform"] == "codex"

    assign = resolved["design-author"]
    brief = kd.build_brief(
        "t-design-1", "design-author", assign["platform"], model="m",
        objective="Compile the grill ledger into DESIGN.md.",
        result_path="RESULT.json", sandbox="write",
        acceptance="Return designPath + verdict.",
    )

    def stub_runner(cmd, cwd, result_path, timeout):
        return 0, "design-author done", "", json.dumps({"designPath": "DESIGN.md", "verdict": "ready"})

    result = kd.dispatch(brief, str(tmp_path), runner=stub_runner)
    assert result["status"] == "completed"
    assert result["payload"]["designPath"] == "DESIGN.md"
    assert result["payload"]["verdict"] == "ready"
    assert result["payload"]["deviations"] == []


def test_plan_author_round_trip_on_codex(tmp_path):
    """The same round trip for plan-author/planPath."""
    resolved = kr.resolve_roles({"plan-author": {"platform": "codex"}}, ["codex"])
    assert resolved["plan-author"]["platform"] == "codex"

    assign = resolved["plan-author"]
    brief = kd.build_brief(
        "t-plan-1", "plan-author", assign["platform"], model="m",
        objective="Turn the frozen DESIGN.md into a task-level PLAN.md.",
        result_path="RESULT.json", sandbox="write",
        acceptance="Return planPath + verdict.",
    )

    def stub_runner(cmd, cwd, result_path, timeout):
        return 0, "plan-author done", "", json.dumps({"planPath": "PLAN.md", "verdict": "needs-rework",
                                                        "deviations": ["ambiguous ownership for T3"]})

    result = kd.dispatch(brief, str(tmp_path), runner=stub_runner)
    assert result["status"] == "completed"
    assert result["payload"]["planPath"] == "PLAN.md"
    assert result["payload"]["verdict"] == "needs-rework"
    assert result["payload"]["deviations"] == ["ambiguous ownership for T3"]


def test_design_author_malformed_result_fails_via_existing_catch(tmp_path):
    """A stub returning malformed JSON (missing designPath) fails via dispatch()'s EXISTING catch
    (kata_dispatch.py's normalize-error handling) — no new code path is exercised, proving T1 added
    no special-casing that bypasses the existing failure handling."""
    resolved = kr.resolve_roles({"design-author": {"platform": "codex"}}, ["codex"])
    assign = resolved["design-author"]
    brief = kd.build_brief(
        "t-design-2", "design-author", assign["platform"], model="m",
        objective="Compile the grill ledger into DESIGN.md.",
        result_path="RESULT.json", sandbox="write",
        acceptance="Return designPath + verdict.",
    )

    def bad_stub_runner(cmd, cwd, result_path, timeout):
        # missing designPath entirely — normalize() must raise, dispatch() must catch it
        return 0, "ok", "", json.dumps({"verdict": "ready"})

    result = kd.dispatch(brief, str(tmp_path), runner=bad_stub_runner)
    assert result["status"] == "failed"
    assert "designPath" in result["payload"]["error"]
