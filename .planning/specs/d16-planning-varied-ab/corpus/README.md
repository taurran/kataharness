# D16 test corpus — pre-registered

Three small greenfield projects, all **Python**, distinct shapes (CLI · REST API · parser). They are the
**fixed stimuli** for the planning-varied A/B (DESIGN.md). Frozen with the protocol — **do not edit after the
first run** (post-hoc edits invalidate pre-registration).

## What lives here vs. where runs happen
- **Here (repo, durable):** each project's `SPEC` (the natural-language feature request given *identically* to
  both arms) + `GATE` (the experimenter's acceptance criteria) + `METRIC-SHEET.md`.
- **Arm output (throwaway, outside repo):** each run builds into
  `C:\Dev\_kata_d16\<project>\<arm>\run-<n>\` — generated code is **not** committed to this repo.

## Run model (one run)
1. Give the arm **only the SPEC** (never the gate test code) + a fresh throwaway dir.
2. **Arm A** plans via `kata-grill`→`kata-design-doc`→`kata-plan` then executes (`kata-orchestrate`/`worktree`/
   `tdd`); **Arm B** plans via local GSD (`~/.claude/get-shit-done`) then executes. Both on **Sonnet**, fresh
   context, then both run `kata-review`.
3. Run the **GATE** against the arm's output: `pytest -q` (experimenter suite, written from the enumerated
   acceptance cases) **and** `ruff check .`. **First-pass green** = both pass on the arm's first delivered build.
4. Record the 7 metrics + covariates into `METRIC-SHEET.md` for that run.

## Gate authoring note (pre-run sub-step)
The enumerated acceptance cases in each project's `GATE` are the pre-registered truth. Before the first run,
turn each into an executable `pytest` suite stored at `C:\Dev\_kata_d16\_gates\<project>/` (held out — arms
never see it). The lint gate is `ruff check .` (clean = 0 findings) for every project.

## Projects
| # | File | Shape | Acceptance |
|---|---|---|---|
| 1 | `01-cli-wordfreq.md` | CLI tool | pytest + ruff |
| 2 | `02-rest-notes-api.md` | REST API (FastAPI, in-memory) | pytest (TestClient) + ruff |
| 3 | `03-parser-expr-eval.md` | parser/evaluator | pytest + ruff |
