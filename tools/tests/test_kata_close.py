"""Tests for kata_close.py — the plan-grounding, fail-closed close (DESIGN §5).

The two DECLARED evidence nodes for the `close-machinery` task (frozen PLAN frontmatter):

    test:tools/tests/test_kata_close.py::test_close_refuses_absent_records
    test:tools/tests/test_kata_close.py::test_provenance_drift_fails_close

Both are marked in place below and are runnable standalone.

Concurrency discipline (G11, the D-25 lesson): every concurrency property here is proved
TWICE — an in-process race run N times (so a 1-in-5 defect cannot survive one pytest
invocation) AND a deterministic forced-interleaving test through the module's race hooks.
Platform divergence is the known trap: an election must be `O_CREAT|O_EXCL`, never a
rename (a rename onto an occupied path is a documented no-op SUCCESS on Windows and a
silent clobber on POSIX), and both properties below are asserted the same way on both.

Every fixture repo is a real git repo: the `Kata-Task:` trailer leg of the three-way join
is tier-2 git history by contract (D134), so faking it would test nothing.
"""

from __future__ import annotations

import collections
import concurrent.futures
import json
import subprocess
import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest

import kata_board as kb
import kata_close as kc
import kata_config
import kata_dispatch as kd
import kata_settings

_NOW = datetime(2026, 8, 17, 12, 0, 0, tzinfo=UTC)

#: Rounds each in-process race runs.  The D-25 defect reproduced ~1 run in 5, so a single
#: round could pass while the property was broken; 25 rounds makes one invocation decisive.
_RACE_ROUNDS = 25


# --------------------------------------------------------------------------- fixtures


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True, check=True,
    )
    return proc.stdout.strip()


def _init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "kata@example.invalid")
    _git(root, "config", "user.name", "kata")
    _git(root, "config", "commit.gpgsign", "false")


_PLAN_TEMPLATE = """---
status: frozen (D169 freeze act)
ownership:
{ownership}
waves:
  wave1: [{tasks}]
depends_on:
{depends}
evidence:
{evidence}
---

# PLAN — fixture
"""


def _write_plan(root: Path, tasks: dict[str, list[str]]) -> Path:
    """A frozen PLAN whose frontmatter carries ownership/waves/depends_on/evidence."""
    plan = root / ".planning" / "PLAN.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    ownership = "\n".join(f"  {t}:\n    - src/{t}.py" for t in tasks)
    depends = "\n".join(f"  {t}: []" for t in tasks)
    evidence = "\n".join(
        f"  {t}:\n" + "\n".join(f'    - "{d}"' for d in decls) for t, decls in tasks.items()
    )
    plan.write_text(
        _PLAN_TEMPLATE.format(
            ownership=ownership, tasks=", ".join(sorted(tasks)),
            depends=depends, evidence=evidence,
        ),
        encoding="utf-8",
    )
    return plan


_CONFIG = {"mode": "standard", "modules": [], "runShape": "individual"}
_INTENT = "---\nstatus: frozen\n---\n\n# INTENT — fixture\n"


def _repo(tmp_path: Path, tasks: dict[str, list[str]] | None = None,
          *, config: dict | None = None) -> dict:
    """A committed fixture repo: frozen PLAN + kata.config + INTENT.md at the fork point."""
    root = tmp_path / "repo"
    _init_repo(root)
    tasks = tasks if tasks is not None else {"t1": ["artifact:src/t1.py"]}
    plan = _write_plan(root, tasks)
    (root / "kata.config").write_text(
        json.dumps(config if config is not None else _CONFIG, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (root / "INTENT.md").write_text(_INTENT, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "freeze: PLAN + provenance")
    return {"root": root, "plan": plan, "tasks": tasks}


def _integrate(root: Path, task_id: str, *, files: dict[str, str] | None = None) -> str:
    """An integration commit carrying the tier-2 `Kata-Task:` trailer for *task_id*."""
    for rel, body in (files or {f"src/{task_id}.py": f"# {task_id}\n"}).items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"feat: {task_id}\n\nKata-Task: {task_id}")
    return _git(root, "rev-parse", "HEAD")


def _kata(root: Path, *, entropy: str = "abcd1234", phases: tuple[str, ...] = ("open EXECUTION wave=1",)) -> Path:
    """A `.kata/` inside *root* carrying one live run with recorded phase events."""
    kata = root / ".kata"
    kb.start_run(kata, now=_NOW, entropy=entropy)
    for msg in phases:
        kd.phase(kata, msg, repo_root=str(root), now=_NOW)
    return kata


def _home(tmp_path: Path, *, consent_for: Path | None = None) -> Path:
    """A machine-local settings home, optionally with consent already recorded."""
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    if consent_for is not None:
        kata_settings.record_target_consent(
            kc.consent_key(consent_for),
            {"granted": True, "by": "operator", "at": "2026-08-17T00:00:00+00:00"},
            home=home,
        )
    return home


def _green_runner(argv, cwd):
    """An injected evidence runner that reports exit 0 — used where the JOIN is under test."""
    return 0


def _red_runner(argv, cwd):
    return 1


def _close(fx: dict, kata: Path, home: Path, **kw):
    defaults = dict(
        plan_path=fx["plan"], repo_root=fx["root"], settings_home=home,
        evidence_runner=_green_runner, now=_NOW,
    )
    return kc.close_run(kata, **{**defaults, **kw})


# --------------------------------------------------------------------------- §5.3 records


# ----- DECLARED EVIDENCE NODE (PLAN frontmatter `evidence:` for close-machinery) -----
def test_close_refuses_absent_records(tmp_path):
    """§5.3 — the close REFUSES without required records, per fact class (D134).

    Three absences, each bound to a DIFFERENT system of record, each refused:

    1. no cursor at all — there is nothing to close and nothing to close it against;
    2. a cursor with NO phase events — a run with no recorded position cannot be graded;
    3. an UNCOMMITTED kata.config — committed run provenance is the record the drift
       check compares against, and it does not exist.

    The refusal is an ARTIFACT, not a message: every refusal that gets far enough to
    grade emits the close verdict artifact, so a report cites a path that exists rather
    than quoting the refusal's own narration.
    """
    fx = _repo(tmp_path)
    home = _home(tmp_path, consent_for=fx["root"])
    _integrate(fx["root"], "t1")

    # 1. No cursor at all.
    empty = fx["root"] / ".kata"
    empty.mkdir(parents=True, exist_ok=True)
    with pytest.raises(kc.CloseRefused, match="no readable cursor") as first:
        _close(fx, empty, home)
    assert first.value.fact_class == "phase"

    # 2. A live run with NO phase events recorded.
    kb.start_run(empty, now=_NOW, entropy="beef0001")
    with pytest.raises(kc.CloseRefused, match="required records are ABSENT") as second:
        _close(fx, empty, home)
    assert second.value.fact_class == "phase"
    assert "NO phase events" in str(second.value)
    # The refusal left an artifact behind — cite the path, never the message.
    verdict_path = Path(second.value.verdict_path)
    assert verdict_path.is_file()
    payload = json.loads(Path(str(verdict_path).replace("-close.md", "-close.json")).read_text("utf-8"))
    assert payload["verdict"] == kc.VERDICT_NEEDS_WORK
    assert [m["class"] for m in payload["missingRecords"]] == ["phase"]
    assert payload["missingRecords"][0]["systemOfRecord"] == kc.SYSTEM_OF_RECORD["phase"]

    # 3. Provenance that was never committed.
    bare = _repo(tmp_path / "bare")
    _integrate(bare["root"], "t1")
    (bare["root"] / "kata.config").unlink()
    _git(bare["root"], "rm", "-q", "--cached", "kata.config")
    _git(bare["root"], "commit", "-q", "-m", "chore: drop config")
    kata2 = _kata(bare["root"], entropy="beef0002")
    with pytest.raises(kc.CloseRefused, match="required records are ABSENT") as third:
        kc.close_run(
            kata2, plan_path=bare["plan"], repo_root=bare["root"],
            settings_home=_home(tmp_path / "bare", consent_for=bare["root"]),
            evidence_runner=_green_runner, now=_NOW,
        )
    classes = {m["class"] for m in json.loads(
        Path(str(third.value.verdict_path).replace("-close.md", "-close.json")).read_text("utf-8")
    )["missingRecords"]}
    assert "provenance" in classes


def test_absent_records_refusal_binds_each_class_to_its_system_of_record(tmp_path):
    """D134 as DATA: every required class names the authority it is graded from."""
    for fact_class in kc.REQUIRED_RECORD_CLASSES:
        assert fact_class in kc.SYSTEM_OF_RECORD
    # DONE is bound to tier-2 trailers, never to the cursor — the D134 line itself.
    assert "Kata-Task" in kc.SYSTEM_OF_RECORD["task-done"]
    assert "AUTHORITATIVE for DONE" in kc.SYSTEM_OF_RECORD["task-done"]
    assert "cursor" in kc.SYSTEM_OF_RECORD["phase"]
    assert "accepted_by" in kc.SYSTEM_OF_RECORD["deferral-approval"]


def test_degraded_integration_scan_is_never_credited_as_zero(tmp_path):
    """Anti-vacuity (TM-D3): an unreadable history is not 'no tasks done'."""
    fx = _repo(tmp_path)
    kata = _kata(fx["root"])
    provenance = kc.provenance_drift(repo_root=fx["root"])
    join = {"degraded": True, "reasons": ["integration-history-unreadable"], "taskCount": 1}
    missing = kc.missing_required_records(
        kb.read_cursor(kata), kata_dir=kata, provenance=provenance, join=join
    )
    assert [m["class"] for m in missing] == ["task-done"]
    assert "anti-vacuity" in missing[0]["reason"]


def test_empty_plan_task_set_is_reported_not_certified(tmp_path):
    """A join over zero items certifies nothing and must say so."""
    fx = _repo(tmp_path)
    kata = _kata(fx["root"])
    provenance = kc.provenance_drift(repo_root=fx["root"])
    missing = kc.missing_required_records(
        kb.read_cursor(kata), kata_dir=kata,
        provenance=provenance, join={"degraded": False, "reasons": [], "taskCount": 0},
    )
    assert any("ran over nothing" in m["reason"] for m in missing)


# --------------------------------------------------------------------------- §5.4 provenance


# ----- DECLARED EVIDENCE NODE (PLAN frontmatter `evidence:` for close-machinery) -----
def test_provenance_drift_fails_close(tmp_path):
    """TM-A2 / §5.4 — committed provenance ≠ what the run executed ⇒ the close FAILS.

    The check reads the COMMITTED blob from git (never the working tree — that is the
    whole point) and compares it with what the run actually executed.  Three properties
    are pinned here:

    * a clean run has NO drift and closes;
    * an edited-but-uncommitted `kata.config` is `config-drift` and FAILS the close, which
      then routes per §5.3 (the two legal paths are named in the emitted artifact);
    * a MACHINE-LOCAL value moving between machines is NOT drift — that is what the
      machine-local split buys, and without it the check would cry wolf on every machine.
    """
    fx = _repo(tmp_path)
    home = _home(tmp_path, consent_for=fx["root"])
    _integrate(fx["root"], "t1")
    kata = _kata(fx["root"])

    clean = kc.provenance_drift(repo_root=fx["root"])
    assert clean["drift"] is False and clean["classes"] == []
    assert clean["source"] == "working-tree"   # the honest label travels with the claim

    # The run executed against a config that was never committed in this shape.
    (fx["root"] / "kata.config").write_text(
        json.dumps({**_CONFIG, "mode": "advanced"}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    drifted = kc.provenance_drift(repo_root=fx["root"])
    assert drifted["drift"] is True
    assert drifted["classes"] == ["config-drift"]

    with pytest.raises(kc.CloseRefused, match="REFUSING to close run") as exc:
        _close(fx, kata, home)
    payload = json.loads(
        Path(str(exc.value.verdict_path).replace("-close.md", "-close.json")).read_text("utf-8")
    )
    assert payload["verdict"] == kc.VERDICT_NEEDS_WORK
    assert payload["provenance"]["classes"] == ["config-drift"]
    assert "ANOTHER LOOP PASS" in payload["legalPaths"]
    assert "RECORDED OPERATOR ACCEPTANCE" in payload["legalPaths"]
    # Nothing was closed: the terminal line is NOT on the cursor.
    assert kd.is_run_closed(kb.read_cursor(kata)) is False

    # A machine-local value differing from the committed config is NOT drift.
    (fx["root"] / "kata.config").write_text(
        json.dumps({**_CONFIG, "agentSkills": {"dir": "/some/other/machine/skills"}},
                   indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    assert kc.provenance_drift(repo_root=fx["root"])["classes"] == []


def test_provenance_recorded_map_is_authoritative_over_the_working_tree(tmp_path):
    """The recorded-execution leg outranks the working-tree fallback, and says which ran."""
    fx = _repo(tmp_path)
    live = kc.provenance_drift(repo_root=fx["root"])
    recorded = kc.provenance_drift(
        repo_root=fx["root"], executed={"config": "deadbeef", "intent": "cafebabe"},
    )
    assert live["source"] == "working-tree" and recorded["source"] == "recorded"
    assert recorded["classes"] == ["config-drift", "intent-drift"]


def test_provenance_tree_semantics_check_each_arm(tmp_path):
    """TM-A2 rider / R-M8: committed config + arm registry vs EACH arm's execution."""
    fx = _repo(tmp_path)
    good = kc.provenance_drift(repo_root=fx["root"])["executed"]
    result = kc.provenance_drift(
        repo_root=fx["root"],
        arms=[
            {"label": "arm-b", "executed": {"config": "0" * 64, "intent": good["intent"]}},
            {"label": "arm-a", "executed": good},
        ],
    )
    assert [a["label"] for a in result["arms"]] == ["arm-a", "arm-b"]   # explicit total order
    assert result["arms"][0]["drift"] is False
    assert result["arms"][1]["classes"] == ["config-drift"]
    assert "arm:arm-b:config-drift" in result["classes"]


def test_provenance_digest_is_length_prefixed(tmp_path):
    """Doctrine law 4 — a multi-item digest length-prefixes every frame (D98)."""
    assert kc._netstring_digest([("ab", b"c")]) != kc._netstring_digest([("a", b"bc")])
    assert kc._netstring_digest([("a", b"x"), ("b", b"y")]) == \
        kc._netstring_digest([("b", b"y"), ("a", b"x")])   # sorted, order-independent


def test_absent_committed_blob_is_uncommitted_never_unchanged(tmp_path):
    """`None` at a ref means ABSENT and must never read as 'unchanged'."""
    fx = _repo(tmp_path)
    result = kc.provenance_drift(repo_root=fx["root"], intent_path="NOT-THERE.md")
    assert "intent-absent" in result["classes"]


# --------------------------------------------------------------------------- machine-local


def test_machine_local_split_and_merge_round_trip():
    """The migration is lossless and non-mutating; empty blocks do not survive."""
    config = {
        "mode": "standard",
        "agentSkills": {"dir": "C:/Users/someone/skills"},
        "engram": {"learnFeed": {"dir": "C:/vault/pages"}, "autonomy": "always-human"},
        "target": {"kind": "existing", "path": "C:/dev/thing"},
    }
    original = json.loads(json.dumps(config))
    clean, moved = kata_config.split_machine_local(config)
    assert config == original, "split must not mutate its input"
    assert moved == {
        "agentSkills.dir": "C:/Users/someone/skills",
        "engram.learnFeed.dir": "C:/vault/pages",
        "target.path": "C:/dev/thing",
    }
    assert "agentSkills" not in clean            # the block was emptied and dropped
    assert clean["engram"] == {"autonomy": "always-human"}
    assert clean["target"] == {"kind": "existing"}
    assert kata_config.merge_machine_local(clean, moved) == json.loads(
        json.dumps(config, sort_keys=True)
    )


def test_machine_local_split_is_idempotent_and_refuses_non_dict():
    clean, moved = kata_config.split_machine_local({"mode": "standard"})
    assert moved == {} and clean == {"mode": "standard"}
    again, moved2 = kata_config.split_machine_local(clean)
    assert again == clean and moved2 == {}
    with pytest.raises(ValueError, match="must be a dict"):
        kata_config.split_machine_local(["nope"])


def test_migrate_machine_local_writes_both_files(tmp_path):
    fx = _repo(tmp_path, config={**_CONFIG, "agentSkills": {"dir": "C:/personal/skills"}})
    home = _home(tmp_path)
    result = kc.migrate_machine_local(fx["root"] / "kata.config", home=home)
    assert result["moved"] == {"agentSkills.dir": "C:/personal/skills"}
    assert "agentSkills" not in json.loads((fx["root"] / "kata.config").read_text("utf-8"))
    assert kata_settings.machine_local(home) == {"agentSkills.dir": "C:/personal/skills"}
    # Idempotent: a second migration moves nothing and leaves both files alone.
    assert kc.migrate_machine_local(fx["root"] / "kata.config", home=home)["moved"] == {}


# --------------------------------------------------------------------------- §5.2 the join


def test_three_way_join_is_total_over_the_plan_task_set(tmp_path):
    """Every plan item lands in exactly one of the three resolutions — no fourth bucket."""
    fx = _repo(tmp_path, tasks={
        "t1": ["artifact:src/t1.py"],
        "t2": ["artifact:src/t2.py"],
        "t3": ["artifact:src/t3.py"],
    })
    _integrate(fx["root"], "t1")
    (fx["root"] / ".planning" / "DEFERRED.md").write_text(
        "# DEFERRED\n\n"
        "## DEF-1 — t2 is parked pending the upstream fix · OPEN (2026-08-17)\n"
        "- **What:** t2's encoder, `src/t2.py`\n"
        "- **Why:** the upstream contract is unfrozen; building now would be a guess\n"
        "- **Provenance:** run-20260817T120000Z-abcd1234, task t2\n"
        "- **Owed-to:** the next wave\n",
        encoding="utf-8",
    )
    join = kc.three_way_join(
        plan_path=fx["plan"], repo_root=fx["root"], evidence_runner=_green_runner
    )
    assert join["taskCount"] == 3
    assert join["built"] == ["t1"]
    assert join["deferred"] == ["t2"]
    assert join["drift"] == ["t3"]
    assert sorted(join["items"]) == ["t1", "t2", "t3"]
    assert {i["resolution"] for i in join["items"].values()} <= set(kc.RESOLUTIONS)
    assert join["items"]["t3"]["why"] == "no integration trailer and no bound deferral entry"


def test_trailer_without_resolving_evidence_is_drift_not_done(tmp_path):
    """Both halves are required: a trailer over dead evidence is NOT built-and-exercised."""
    fx = _repo(tmp_path, tasks={"t1": ["artifact:src/never-written.py"]})
    _integrate(fx["root"], "t1")
    join = kc.three_way_join(
        plan_path=fx["plan"], repo_root=fx["root"], evidence_runner=_green_runner
    )
    assert join["drift"] == ["t1"]
    assert "did NOT resolve" in join["items"]["t1"]["why"]


def test_behavioral_evidence_is_executed_not_file_touched(tmp_path):
    """§5.2: a `test:` item resolves by RUNNING, never by a file-touch heuristic."""
    fx = _repo(tmp_path, tasks={"t1": ["test:tests/test_thing.py::test_it"]})
    _integrate(fx["root"], "t1", files={"tests/test_thing.py": "def test_it():\n    pass\n"})
    seen: list[tuple] = []

    def runner(argv, cwd):
        seen.append((tuple(argv), str(cwd)))
        return 0

    join = kc.three_way_join(plan_path=fx["plan"], repo_root=fx["root"], evidence_runner=runner)
    assert join["built"] == ["t1"]
    assert seen and "pytest" in seen[0][0] and "tests/test_thing.py::test_it" in seen[0][0]
    assert seen[0][0][:2] == ("uv", "run")     # the explicit execution-boundary wrap

    # The SAME file exists whether the test passes or fails — only the run decides.
    red = kc.three_way_join(plan_path=fx["plan"], repo_root=fx["root"], evidence_runner=_red_runner)
    assert red["drift"] == ["t1"]
    assert red["items"]["t1"]["evidence"][0]["exitCode"] == 1


def test_join_calls_parse_plan_tasks_with_the_evidence_check_on(tmp_path):
    """This function is `parse_plan_tasks(check_evidence=True)`'s production caller (D-22)."""
    fx = _repo(tmp_path)
    plan_text = (fx["plan"]).read_text("utf-8").replace('    - "artifact:src/t1.py"', "    - \"rm -rf /\"")
    (fx["plan"]).write_text(plan_text, encoding="utf-8")
    with pytest.raises(ValueError, match="not one of the three legal evidence forms"):
        kc.three_way_join(plan_path=fx["plan"], repo_root=fx["root"], evidence_runner=_green_runner)


def test_artifact_evidence_is_never_executed(tmp_path):
    """The `artifact` form's `argv is None` is the contract, not an omission."""
    fx = _repo(tmp_path)
    _integrate(fx["root"], "t1")
    calls: list = []
    kc.three_way_join(
        plan_path=fx["plan"], repo_root=fx["root"],
        evidence_runner=lambda argv, cwd: calls.append(argv) or 0,
    )
    assert calls == []


# --------------------------------------------------------------------------- the ledger


def _ledger(root: Path, body: str) -> Path:
    path = root / ".planning" / "DEFERRED.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_ledger_parses_the_deferral_grammar(tmp_path):
    path = _ledger(tmp_path, (
        "# DEFERRED\n\n"
        "## DEF-3 — a thing · **CLOSED (2026-08-04)**\n"
        "- **What:** the thing\n- **Why:** reasons\n- **Provenance:** run-x\n"
        "- **Owed-to:** wave 9\n- **closing_commit:** abc1234 (feat: the thing)\n\n"
        "### Closure record\n"
        "- **What:** this sub-heading content is RECORD, never a second field block\n"
    ))
    entries = kc.parse_deferral_ledger(path)
    assert [e["id"] for e in entries] == ["DEF-3"]
    assert entries[0]["status"] == "CLOSED"           # emphasis markers flattened
    assert entries[0]["fields"]["closing_commit"].startswith("abc1234")
    assert "Owed-to" in entries[0]["fields"]


def test_ledger_keeps_the_underscore_in_snake_case_fields(tmp_path):
    """The one deliberate difference from the protocol normaliser (deferral.md says so)."""
    path = _ledger(tmp_path, (
        "## DEF-4 — x · ACCEPTED (2026-08-17)\n"
        "- **What:** x\n- **Why:** y\n- **Provenance:** z\n- **Owed-to:** w\n"
        "- **accepted_by:** Taur\n- **accepted_at:** 2026-08-17T00:00:00Z\n"
    ))
    entry = kc.parse_deferral_ledger(path)[0]
    assert entry["fields"]["accepted_by"] == "Taur"
    assert entry["fields"]["accepted_at"] == "2026-08-17T00:00:00Z"


@pytest.mark.parametrize("body,match", [
    ("## DEF-9 — broken heading with no status\n", "malformed ledger entry heading"),
    ("## DEF-9 — x · OPEN (2026-08-17)\n- **What:** x\n", "missing required field"),
    ("## DEF-9 — x · CLOSED (2026-08-17)\n- **What:** x\n- **Why:** y\n"
     "- **Provenance:** z\n- **Owed-to:** w\n", "captured is not closed"),
    ("## DEF-9 — x · ACCEPTED (2026-08-17)\n- **What:** x\n- **Why:** y\n"
     "- **Provenance:** z\n- **Owed-to:** w\n", "ONLY from those fields"),
])
def test_ledger_parse_failure_is_a_refusal_never_a_skip(tmp_path, body, match):
    path = _ledger(tmp_path, body)
    with pytest.raises(kc.DeferralLedgerError, match=match):
        kc.parse_deferral_ledger(path)


def test_absent_ledger_is_a_legal_zero_but_unreadable_is_not(tmp_path):
    """A zero is reported as zero; a ledger that could not be READ is never a zero."""
    fx = _repo(tmp_path)
    _integrate(fx["root"], "t1")
    join = kc.three_way_join(
        plan_path=fx["plan"], repo_root=fx["root"], evidence_runner=_green_runner
    )
    assert join["ledger"] == {
        "path": str(fx["root"] / ".planning" / "DEFERRED.md"),
        "present": False, "entries": 0, "bound": {},
    }
    unreadable = fx["root"] / ".planning" / "DEFERRED.md"
    unreadable.mkdir()          # a directory where a file is expected: present, unreadable
    with pytest.raises(kc.DeferralLedgerError, match="UNREADABLE"):
        kc.three_way_join(
            plan_path=fx["plan"], repo_root=fx["root"], evidence_runner=_green_runner
        )


def _entry(eid, status, title, **fields):
    return {"id": eid, "status": status, "title": title, "fields": fields, "text": ""}


def test_deferral_binding_is_whole_token_and_excludes_closed(tmp_path):
    """`t1` must never claim `t12`'s entry, and a CLOSED entry never covers unbuilt work."""
    entries = [
        _entry("DEF-1", "OPEN", "about t12", What="t12's encoder"),
        _entry("DEF-2", "CLOSED", "about t1", What="t1's encoder"),
        _entry("DEF-3", "ACCEPTED", "about t3", What="t3's encoder"),
    ]
    bound = kc.bind_deferrals(entries, {"t1", "t12", "t3"})
    assert "t1" not in bound                    # DEF-1 is t12's; DEF-2 is CLOSED
    assert [e["id"] for e in bound["t12"]] == ["DEF-1"]
    assert [e["id"] for e in bound["t3"]] == ["DEF-3"]


def test_deferral_binding_ignores_why_provenance_and_owed_to(tmp_path):
    """The silent-deferral hole, closed: an ADJACENCY mention never resolves a plan item.

    Measured on the live ledger: DEF-6 and DEF-12 both say "W7 close-machinery adjacency"
    in `Why`/`Owed-to` while their `What` names an entirely different surface.  A
    whole-entry binding rule would have resolved a DRIFTED `close-machinery` as a recorded
    deferral on the strength of those sentences.
    """
    adjacency = _entry(
        "DEF-6", "OPEN", "phase boundaries are instructed, not mechanically checked",
        What="kata-orchestrate pins four phase boundaries, but no check asserts them",
        Why="the natural home is close-machinery (W7) or a validator check",
        Provenance="tm-w4-orchestrate builder deferral 3",
        **{"Owed-to": "W7 close-machinery adjacency, else the backlog"},
    )
    bound = kc.bind_deferrals([adjacency], {"close-machinery", "kata-orchestrate"})
    assert "close-machinery" not in bound, "a Why/Owed-to adjacency must never bind"
    # The same entry DOES bind once `What` names the task — the field that says what
    # was not done is the only one the binding reads.
    real = {**adjacency, "fields": {**adjacency["fields"], "What": "close-machinery's join"}}
    assert "close-machinery" in kc.bind_deferrals([real], {"close-machinery"})
    assert kc.BINDING_FIELDS == ("What",)
    # The documented residual, DEMONSTRATED rather than only prosed (PD-2): `What` is
    # prose, so an entry whose `What` merely MENTIONS a task-id over-binds.  DEF-6's
    # `What` names kata-orchestrate while the entry defers a check, not that task.
    assert "kata-orchestrate" in bound, "the stated residual must be pinned, not hidden"


def test_deferral_binding_on_the_live_ledger_binds_no_plan_task(tmp_path):
    """Dogfood on live BYTES, not a fixture of the same shape (the D-23 lesson).

    The repo's own ledger and frozen PLAN: 13 entries, 28 tasks, and — correctly — ZERO
    plan-item bindings, because no entry's `What` names a plan task.  If this ever starts
    binding, the entry that did it is worth reading.
    """
    repo = Path(__file__).resolve().parents[2]
    ledger = repo / ".planning" / "DEFERRED.md"
    plan = repo / ".planning" / "specs" / "trust-model" / "PLAN.md"
    if not (ledger.is_file() and plan.is_file()):
        pytest.skip("not running inside the harness repo")
    import kata_restore
    entries = kc.parse_deferral_ledger(ledger)
    assert len(entries) >= 13, "the live ledger must parse in full, not partially"
    bound = kc.bind_deferrals(entries, kata_restore.parse_plan_tasks(plan))
    assert bound == {}, f"unexpected live binding(s): {bound}"


# --------------------------------------------------------------------------- RS-M7 redaction


def test_secret_class_fixture_fails_the_commit_act(tmp_path):
    """RS-M7 / §8 S4 — a detected class fails the commit act CLOSED, at branch close."""
    with pytest.raises(kc.RedactionRefused, match="REFUSING the commit act") as exc:
        kc.redact_at_commit_act({"config": '{"token": "AKIAABCDEFGHIJKLMNOP"}'})
    assert "aws-key" in str(exc.value)
    assert "Redaction is detection, not prevention" in str(exc.value)
    assert kc.redact_at_commit_act({"config": '{"mode": "standard"}'})["clean"] is True


def test_close_run_fails_the_commit_act_on_a_secret_class(tmp_path):
    """The whole close refuses, and the refusal leaves an artifact to cite."""
    fx = _repo(tmp_path)
    home = _home(tmp_path, consent_for=fx["root"])
    _integrate(fx["root"], "t1")
    kata = _kata(fx["root"])
    (fx["root"] / "INTENT.md").write_text(
        _INTENT + "\nthe deploy uses github_pat_11ABCDEFGHIJ_secretvalue here\n", encoding="utf-8",
    )
    _git(fx["root"], "add", "-A")
    _git(fx["root"], "commit", "-q", "-m", "chore: intent")
    with pytest.raises(kc.RedactionRefused) as exc:
        _close(fx, kata, home)
    assert Path(exc.value.verdict_path).is_file()
    assert kd.is_run_closed(kb.read_cursor(kata)) is False


def test_the_two_named_points_share_ONE_scrub(tmp_path):
    """RS-M7: one scrub, two points — neither point owns a pattern of its own."""
    import learn_feed
    text = "api_key = ABCDEFGHIJ"
    scrubbed, counts = kc.redact_at_snapshot_edge(text)
    assert scrubbed == learn_feed.redact(text)[0] and counts == learn_feed.redact(text)[1]
    with pytest.raises(kc.RedactionRefused):
        kc.redact_at_commit_act({"cursor": text})
    # The snapshot edge SCRUBS where the commit act REFUSES — different policy, one table.
    assert "[REDACTED:api-key]" in scrubbed


# --------------------------------------------------------------------------- RS-M6 consent


def test_consent_prompt_fires_exactly_once_per_target(tmp_path):
    """RS-M6 — per-target, remembered machine-local, asked once and only once."""
    home = _home(tmp_path)
    target_a, target_b = tmp_path / "target-a", tmp_path / "target-b"
    target_a.mkdir(); target_b.mkdir()
    prompts: list[str] = []

    def prompter(target):
        prompts.append(target)
        return True

    first = kc.target_consent(target_a, prompter=prompter, home=home, now=_NOW)
    assert first["granted"] is True and first["source"] == "prompted"
    for _ in range(5):
        again = kc.target_consent(target_a, prompter=prompter, home=home, now=_NOW)
        assert again["source"] == "remembered" and again["granted"] is True
    assert len(prompts) == 1, "the prompt must fire EXACTLY once per target"

    # A DIFFERENT target gets its own single prompt — per-target, not per-machine.
    kc.target_consent(target_b, prompter=prompter, home=home, now=_NOW)
    assert len(prompts) == 2
    assert sorted(kata_settings.read_settings(home)["targetConsent"]) == sorted(
        [kc.consent_key(target_a), kc.consent_key(target_b)]
    )


def test_unattended_consent_parks_and_never_proceeds(tmp_path):
    """TM-B5 — an unattended run PARKS the consent moment; the park is PERFORMED."""
    fx = _repo(tmp_path)
    home = _home(tmp_path)
    kata = _kata(fx["root"])
    with pytest.raises(kc.ConsentRequired, match="PARKED") as exc:
        kc.target_consent(fx["root"], prompter=None, home=home, kata_dir=kata, now=_NOW)
    park = kata / "escalations" / "close-consent.json"
    assert park.is_file(), "the park artifact must EXIST, not merely be named"
    assert json.loads(park.read_text("utf-8"))["kind"] == "human-required"
    assert str(park) in str(exc.value)
    assert kata_settings.target_consent(kc.consent_key(fx["root"]), home=home) is None


def test_declined_consent_refuses_the_close(tmp_path):
    fx = _repo(tmp_path)
    home = _home(tmp_path)
    kata_settings.record_target_consent(
        kc.consent_key(fx["root"]),
        {"granted": False, "by": "operator", "at": "2026-08-17T00:00:00+00:00"}, home=home,
    )
    _integrate(fx["root"], "t1")
    kata = _kata(fx["root"])
    with pytest.raises(kc.CloseRefused, match="recorded as DECLINED"):
        _close(fx, kata, home)


def test_unrecorded_consent_is_neither_granted_nor_declined(tmp_path):
    """`None` means UNASKED; both coercions are wrong in opposite directions."""
    home = _home(tmp_path)
    assert kata_settings.target_consent("C:/nowhere", home=home) is None
    kata_settings.record_target_consent(
        "C:/nowhere", {"granted": False, "by": "op", "at": "2026-08-17T00:00:00+00:00"}, home=home
    )
    assert kata_settings.target_consent("C:/nowhere", home=home)["granted"] is False


def test_consent_record_refuses_an_unattributable_decision(tmp_path):
    home = _home(tmp_path)
    with pytest.raises(ValueError, match="must be a bool"):
        kata_settings.record_target_consent("t", {"granted": "yes", "by": "o", "at": "x"}, home=home)
    with pytest.raises(ValueError, match="'by'"):
        kata_settings.record_target_consent("t", {"granted": True, "by": "", "at": "x"}, home=home)


# --------------------------------------------------------------------------- G11 concurrency


def test_run_closed_is_written_exactly_once_under_race(tmp_path):
    """§2.6 / R4 residual 3 — the terminal record is written EXACTLY once, under a race.

    The race runs `_RACE_ROUNDS` times IN-PROCESS (a single round can pass while the
    property is broken — the D-25 lesson).  The election is `O_CREAT|O_EXCL`, never a
    rename: on Windows a rename onto an occupied path is a documented no-op success, so a
    rename-election degrades to everyone-wins, and on POSIX it silently clobbers.  The
    deterministic proof is the forced-interleaving test below.
    """
    closers = 6
    tally = collections.Counter()
    for round_no in range(_RACE_ROUNDS):
        fx = _repo(tmp_path / f"r{round_no}")
        home = _home(tmp_path / f"r{round_no}", consent_for=fx["root"])
        _integrate(fx["root"], "t1")
        kata = _kata(fx["root"], entropy=f"{round_no:08x}")
        barrier = threading.Barrier(closers)

        def attempt(_fx=fx, _kata=kata, _home=home, _barrier=barrier):
            _barrier.wait()
            try:
                return ("won", _close(_fx, _kata, _home))
            except kc.CloseRefused as exc:
                return ("refused", str(exc))

        with concurrent.futures.ThreadPoolExecutor(max_workers=closers) as pool:
            outcomes = [f.result() for f in [pool.submit(attempt) for _ in range(closers)]]

        winners = [o for o in outcomes if o[0] == "won"]
        tally[len(winners)] += 1
        assert len(winners) == 1, (
            f"round {round_no}: exactly one closer may win, got {len(winners)}"
        )
        cursor = kb.read_cursor(kata)
        terminal = [
            ln for ln in cursor.lines
            if ln.type == "PHASE" and ln.msg.startswith("run-closed")
        ]
        assert len(terminal) == 1, f"round {round_no}: {len(terminal)} terminal lines"
        assert kd.is_run_closed(cursor) is True
    assert tally == collections.Counter({1: _RACE_ROUNDS}), f"winner tally: {dict(tally)}"


def test_close_election_is_exclusive_under_a_forced_interleaving(tmp_path, monkeypatch):
    """The deterministic pin: the second closer enters at the EXACT race point and loses."""
    fx = _repo(tmp_path)
    home = _home(tmp_path, consent_for=fx["root"])
    _integrate(fx["root"], "t1")
    kata = _kata(fx["root"])
    second: list = []

    def at_the_race_point(run_id):
        monkeypatch.setattr(kc, "_CLOSE_RACE_HOOK", None)
        try:
            _close(fx, kata, home)
            second.append("won")
        except kc.CloseRefused as exc:
            second.append(str(exc))

    monkeypatch.setattr(kc, "_CLOSE_RACE_HOOK", at_the_race_point)
    result = _close(fx, kata, home)
    assert result["verdict"] == kc.VERDICT_CLOSED
    assert len(second) == 1 and "already being closed" in second[0]
    assert sum(
        1 for ln in kb.read_cursor(kata).lines
        if ln.type == "PHASE" and ln.msg.startswith("run-closed")
    ) == 1


def test_consent_prompt_is_elected_exactly_once_under_race(tmp_path):
    """RS-M6 exactly-once, raced: N callers, ONE prompt, no caller proceeds unasked."""
    callers = 6
    tally = collections.Counter()
    for round_no in range(_RACE_ROUNDS):
        home = tmp_path / f"h{round_no}"
        home.mkdir(parents=True, exist_ok=True)
        target = tmp_path / f"t{round_no}"
        target.mkdir(parents=True, exist_ok=True)
        prompts: list[str] = []
        lock = threading.Lock()
        barrier = threading.Barrier(callers)

        def prompter(t, _prompts=prompts, _lock=lock):
            with _lock:
                _prompts.append(t)
            return True

        def attempt(_home=home, _target=target, _barrier=barrier, _prompter=prompter):
            _barrier.wait()
            try:
                return ("ok", kc.target_consent(
                    _target, prompter=_prompter, home=_home, now=_NOW))
            except kc.ConsentRequired as exc:
                return ("refused", str(exc))

        with concurrent.futures.ThreadPoolExecutor(max_workers=callers) as pool:
            outcomes = [f.result() for f in [pool.submit(attempt) for _ in range(callers)]]

        assert len(prompts) == 1, f"round {round_no}: {len(prompts)} prompts fired"
        tally[len(prompts)] += 1
        for status, value in outcomes:
            if status == "ok":
                assert value["granted"] is True
            else:
                assert "EXACTLY once per target" in value
    assert tally == collections.Counter({1: _RACE_ROUNDS})


def test_consent_election_loser_refuses_under_a_forced_interleaving(tmp_path, monkeypatch):
    """A loser never prompts and never assumes — it refuses, deterministically."""
    home = _home(tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    prompts: list[str] = []
    loser: list[str] = []

    def at_the_race_point(_target):
        monkeypatch.setattr(kc, "_CONSENT_RACE_HOOK", None)
        try:
            kc.target_consent(target, prompter=lambda t: prompts.append(t) or True, home=home)
        except kc.ConsentRequired as exc:
            loser.append(str(exc))

    monkeypatch.setattr(kc, "_CONSENT_RACE_HOOK", at_the_race_point)
    granted = kc.target_consent(
        target, prompter=lambda t: prompts.append(t) or True, home=home, now=_NOW
    )
    assert granted["granted"] is True
    assert len(prompts) == 1
    assert len(loser) == 1 and "EXACTLY once per target" in loser[0]


# --------------------------------------------------------------------------- the close itself


def test_a_passing_close_emits_the_verdict_artifact_and_run_closed(tmp_path):
    """Acceptance: a passing close emits the verdict artifact + the terminal record."""
    fx = _repo(tmp_path)
    home = _home(tmp_path, consent_for=fx["root"])
    _integrate(fx["root"], "t1")
    kata = _kata(fx["root"])
    result = _close(fx, kata, home)

    assert result["verdict"] == kc.VERDICT_CLOSED
    verdict = Path(result["verdictPath"])
    assert verdict.read_text("utf-8").splitlines()[0] == "VERDICT: CLOSED"
    payload = json.loads(Path(result["payloadPath"]).read_text("utf-8"))
    assert payload["verdict"] == "CLOSED" and payload["runId"] == result["runId"]
    assert payload["metrics"]["itemsResolved"]["built-and-exercised"] == 1
    assert payload["systemOfRecord"] == kc.SYSTEM_OF_RECORD
    assert json.dumps(payload, sort_keys=True) == json.dumps(payload)   # law 5, as written

    cursor = kb.read_cursor(kata)
    assert kd.is_run_closed(cursor) is True
    assert result["terminalLine"]["msg"] == "run-closed verdict=CLOSED"
    assert result["phasesClosed"] == ["EXECUTION(wave=1)"]


def test_nothing_appends_after_run_closed(tmp_path):
    """§2.6 terminality — the cursor is sealed, and a second close is refused."""
    fx = _repo(tmp_path)
    home = _home(tmp_path, consent_for=fx["root"])
    _integrate(fx["root"], "t1")
    kata = _kata(fx["root"])
    _close(fx, kata, home)

    with pytest.raises(kd.PhaseRefused, match="is CLOSED"):
        kd.phase(kata, "open CLOSEOUT", repo_root=str(fx["root"]), now=_NOW)
    with pytest.raises(kd.SeamError, match="is CLOSED"):
        kd.deny(kata, "late", legal_path="none", now=_NOW)
    with pytest.raises(kc.CloseRefused, match="ALREADY CLOSED"):
        _close(fx, kata, home)


def test_drift_fixture_fails_close_and_routes_to_the_two_legal_paths(tmp_path):
    """Acceptance: unresolved plan items fail the close; both legal paths are named."""
    fx = _repo(tmp_path, tasks={"t1": ["artifact:src/t1.py"], "t2": ["artifact:src/t2.py"]})
    home = _home(tmp_path, consent_for=fx["root"])
    _integrate(fx["root"], "t1")          # t2 is neither integrated nor deferred ⇒ drift
    kata = _kata(fx["root"])

    with pytest.raises(kc.CloseRefused, match="TM-A1 routing") as exc:
        _close(fx, kata, home)
    message = str(exc.value)
    assert "if anything is false or facade it should be another loop pass" in message
    assert "ANOTHER LOOP PASS" in message and "RECORDED OPERATOR ACCEPTANCE" in message
    assert kd.is_run_closed(kb.read_cursor(kata)) is False
    payload = json.loads(
        Path(str(exc.value.verdict_path).replace("-close.md", "-close.json")).read_text("utf-8")
    )
    assert payload["metrics"]["routing"] == "re-loop"
    assert payload["metrics"]["driftNamed"] == ["t2"]
    assert payload["metrics"]["leftovers"] == {"items": ["t2"], "runAgain": True}

    # Legal path 2: a recorded operator acceptance (the TM-D1 shape) closes it.
    accepted = _close(
        fx, kata, home, accepted_by="Taur", accepted_at="2026-08-17T12:30:00+00:00",
    )
    assert accepted["verdict"] == kc.VERDICT_ACCEPTED
    assert accepted["acceptance"] == {
        "accepted_by": "Taur", "accepted_at": "2026-08-17T12:30:00+00:00"
    }
    assert kd.is_run_closed(kb.read_cursor(kata)) is True


def test_half_recorded_acceptance_is_never_credited(tmp_path):
    """A gate credits an approval ONLY from BOTH fields (protocol/deferral.md)."""
    fx = _repo(tmp_path, tasks={"t1": ["artifact:src/t1.py"], "t2": ["artifact:src/t2.py"]})
    home = _home(tmp_path, consent_for=fx["root"])
    _integrate(fx["root"], "t1")
    kata = _kata(fx["root"])
    with pytest.raises(kc.CloseRefused, match="BOTH accepted_by and accepted_at") as exc:
        _close(fx, kata, home, accepted_by="Taur")
    assert exc.value.fact_class == "deferral-approval"


def test_tm_a1_routes_a_claim_stronger_than_its_derivation_to_needs_work(tmp_path):
    """TM-A1 — Dormant-claimed-as-Verified is the facade class and re-loops."""
    fx = _repo(tmp_path)
    home = _home(tmp_path, consent_for=fx["root"])
    _integrate(fx["root"], "t1")
    kata = _kata(fx["root"])
    with pytest.raises(kc.CloseRefused, match="guardian findings") as exc:
        _close(
            fx, kata, home,
            declared={"enforcement": kd.ENFORCEMENT_INTERCEPTING},
            derived={"enforcement": kd.ENFORCEMENT_DORMANT},
        )
    payload = json.loads(
        Path(str(exc.value.verdict_path).replace("-close.md", "-close.json")).read_text("utf-8")
    )
    findings = payload["metrics"]["guardian"]["findings"]
    assert [f["class"] for f in findings] == ["claimed-stronger-than-derived"]
    assert payload["metrics"]["routing"] == "re-loop"


def test_an_honest_declaration_matching_its_derivation_passes(tmp_path):
    fx = _repo(tmp_path)
    home = _home(tmp_path, consent_for=fx["root"])
    _integrate(fx["root"], "t1")
    kata = _kata(fx["root"])
    result = _close(
        fx, kata, home,
        declared={"enforcement": kd.ENFORCEMENT_DORMANT},
        derived={"enforcement": kd.ENFORCEMENT_DORMANT},
    )
    assert result["verdict"] == kc.VERDICT_CLOSED
    assert result["metrics"]["guardian"]["findings"] == []


# --------------------------------------------------------------------------- the loop-back ruling


def test_close_run_closes_open_phases_lifo_including_loop_back(tmp_path):
    """The G20/R3 ruling: LOOP-BACK over an open predecessor, reconciled AT the close.

    kata-loop's Path A opens LOOP-BACK while the run still holds phases open.  The seam
    refuses `run-closed` while ANY phase is open, so the close must close them — LIFO, so
    LOOP-BACK (opened last) closes FIRST — and only then write the terminal line.  The
    terminal line records `loopBack=1`, so the successor's `prev-run:` chain is
    corroborated by the predecessor's own terminal record.
    """
    fx = _repo(tmp_path)
    home = _home(tmp_path, consent_for=fx["root"])
    _integrate(fx["root"], "t1")
    kata = _kata(fx["root"], phases=(
        "open EXECUTION wave=1", "open CLOSEOUT", "open LOOP-BACK",
    ))
    result = _close(fx, kata, home)

    assert result["phasesClosed"] == ["LOOP-BACK", "CLOSEOUT", "EXECUTION(wave=1)"]
    assert result["loopBack"] is True
    assert result["terminalLine"]["msg"] == "run-closed verdict=CLOSED loopBack=1"

    closes = [
        ln.msg for ln in sorted(kb.read_cursor(kata).lines, key=lambda x: (x.seq, x.pos))
        if ln.type == "PHASE" and ln.msg.startswith("close ")
    ]
    assert closes == ["close LOOP-BACK", "close CLOSEOUT", "close EXECUTION wave=1"]
    assert kd.phase_state(kb.read_cursor(kata))["open"] == []


def test_close_run_refuses_with_the_instruction_when_told_not_to_close_phases(tmp_path):
    """The other half of the ruling: refuse, and NAME the instruction."""
    fx = _repo(tmp_path)
    home = _home(tmp_path, consent_for=fx["root"])
    _integrate(fx["root"], "t1")
    kata = _kata(fx["root"], phases=("open EXECUTION wave=1", "open LOOP-BACK"))
    with pytest.raises(kc.CloseRefused, match="INSTRUCTION") as exc:
        _close(fx, kata, home, close_open_phases=False)
    assert "LOOP-BACK" in str(exc.value)
    assert exc.value.fact_class == "phase"
    assert kd.is_run_closed(kb.read_cursor(kata)) is False
    payload = json.loads(
        Path(str(exc.value.verdict_path).replace("-close.md", "-close.json")).read_text("utf-8")
    )
    assert payload["openPhases"] == ["EXECUTION(wave=1)", "LOOP-BACK"]


def test_parameterized_execution_phase_round_trips_through_the_seam_grammar(tmp_path):
    """A close msg is rendered back through the seam's own grammar, never hand-built."""
    assert kc._phase_close_msg("EXECUTION(wave=12)") == "EXECUTION wave=12"
    assert kc._phase_close_msg("CLOSEOUT") == "CLOSEOUT"
    assert kd.parse_phase_msg("close " + kc._phase_close_msg("EXECUTION(wave=12)"))["key"] == \
        "EXECUTION(wave=12)"


# --------------------------------------------------------------------------- misc


def test_verdict_enum_is_closed():
    with pytest.raises(ValueError, match="not in the closed enum"):
        kc.emit_close_verdict(".kata", "run-20260817T120000Z-abcd1234", "GREEN", {})


def test_path_guard_rejects_traversal():
    with pytest.raises(ValueError, match="traversal"):
        kc._safe_path("../evil/x")
    assert kc._safe_path(".kata/sub/thing") == Path(".kata/sub/thing")


def test_default_evidence_runner_returns_a_raw_exit_code(tmp_path):
    """D-6a: the RAW code, never a boolean; a missing program is non-zero, never 0."""
    assert kc.default_evidence_runner(("this-program-does-not-exist-kata",), tmp_path) == 127


def test_close_resilience_is_a_fold_over_recorded_fact(tmp_path):
    """`full` needs a push RECEIPT on the cursor — the config flag can never raise it."""
    fx = _repo(tmp_path)
    kata = _kata(fx["root"])
    level = kc.close_resilience(kata, {"cursor": {"pushTrail": True}})
    assert level["level"] != "full"
    assert level["basis"]["pushConfigured"] is True
    assert level["basis"]["pushReceipts"] == 0
