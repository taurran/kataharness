---
spec: kenjiri-lessons
title: Release Hardening — Milestone 1 — frozen PLAN
status: frozen
created: 2026-07-02
baseline_sha: 653f501
branch: hardening/kenjiri-lessons
delivery: incremental, always-stop
tags:
  - kata/hardening
  - plan
---

# Frozen PLAN — Release Hardening (Milestone 1)

Seven phases, built **sequentially-direct** (L8). Each phase: implement → per-phase verify green →
mutation proof where code-bearing → **conventional commit** (co-author trailer). No phase begins until
the prior phase's verify is green. The full green gate + adversarial review run at closeout (Phase 7).

**Ordering rationale (perceived order):** isolated tool fixes that close safety holes first (P1–P2),
then the two M4-substrate pieces (P3 footprint hashing, P4 heartbeat) so they land before the posture
work, then the careful spine-gate posture change (P5) with adversarial review, then the language-scoped
seeding (P6), then closeout (P7).

---

## Phase 1 · F1 — Preflight manifest shape-validation  (WS-B)

- **Owns:** `tools/kata_preflight.py`, `tools/tests/test_kata_preflight.py`,
  `skills/coordinate/kata-preflight/SKILL.md`.
- **Change:** in `run_preflight`, **after** the JSON parse (~line 773) and **before**
  `.get("dependencies", [])` (line 788), validate manifest shape: the top-level `dependencies` key
  MUST be present AND a `list`. Absent / misspelled key / non-list ⇒ `status: blocked` with a
  `manifest-shape` blocker (fail-closed, escalate). **Present-but-empty `[]` proceeds to `ready`**
  (L2 — do NOT block empty). No change to the no-manifest BC short-circuit.
- **SKILL prose:** add a line to Procedure step 2 / schema note that manifest shape is validated
  (key present + list) before dependency extraction; bump `version` (0.1.0 → 0.1.1).
- **Verify:** `uv run pytest tools/tests/test_kata_preflight.py -q` green.
- **New tests:** (a) manifest `{"deps":[...]}` (misspelled) ⇒ `blocked`; (b) `{}` (absent key) ⇒
  `blocked`; (c) `{"dependencies": "x"}` (wrong type) ⇒ `blocked`; (d) `{"dependencies": []}` ⇒
  `ready` (regression guard — legit state stays green); (e) no-manifest ⇒ `ready` (BC unchanged).
- **Mutation:** flip the shape guard (accept absent key) ⇒ test (a) or (b) must go red.
- **Commit:** `fix(preflight): fail-closed on malformed dependency manifest shape (F1)`.

## Phase 2 · F2 — graph_gen src-layout import resolution  (WS-C)

- **Owns:** `tools/graph_gen.py`, `tools/tests/test_graph_gen.py`.
- **Change:** in `_module_to_path` (`:230-246`), after the existing import-relative and repo-root
  candidates, **append** source-root-prefixed candidates: for each discovered source root `R`, try
  `R/<parts>.py` and `R/<parts>/__init__.py`. Discover roots from `all_rel_paths` (top-level dirs that
  contain an `__init__.py`; if none, fall back to a literal `src/` prefix). First-match-wins order is
  preserved so flat-layout resolution is byte-identical (L3). Import edges only.
- **Verify:** `uv run pytest tools/tests/test_graph_gen.py -q` green.
- **New tests:** (a) src-layout fixture (`src/pkg/__init__.py`, `src/pkg/mod.py`,
  `src/pkg/other.py` with `from pkg.mod import x`) ⇒ import edge resolves to `src/pkg/mod.py`;
  (b) existing flat-layout import-edge test unchanged (BC); (c) no phantom edge when the target file
  does not exist.
- **Mutation:** remove the appended src-root candidates ⇒ test (a) goes red; flat-layout test stays
  green.
- **Commit:** `fix(graph): resolve src-layout package imports into blast-radius edges (F2)`.

## Phase 3 · F5 — Commit-scoped lane-check + file-hash footprint  (WS-D)

- **Owns:** `tools/footprint.py`, `tools/tests/test_footprint.py`,
  `skills/coordinate/kata-orchestrate/SKILL.md` (per-task drift-check gate step only),
  `skills/evaluate/kata-evaluate/SKILL.md` (rubric item 4 note only).
- **Change (engine):** add `changed_in_task(base_ref, task_commits)` (or merge-base-scoped variant)
  that returns files changed by the task's *own* commits, NOT a branch-range diff against a possibly-
  stale integration head. Retain `changed_since(ref)` (BC). Add `file_content_hashes(paths) -> {path:
  sha}` — the **M4 evidence-validity substrate** (per-file byte-hash for later staleness checks).
- **Change (orchestrate gate step, `:261-263`):** replace the unspecified "read the diff / confirm it
  touched only owned files" with the explicit commit/merge-base-scoped method (name the helper). State
  the branch-range-diff hazard and why merge-base scoping is required.
- **Change (evaluate item 4):** note that ownership is checked commit-scoped, not branch-range.
- **Versions:** bump `kata-orchestrate`, `kata-evaluate` semver.
- **Verify:** `uv run pytest tools/tests/test_footprint.py -q` green.
- **New tests:** (a) task forked from an earlier integration head ⇒ `changed_in_task` returns only the
  task's files (foreign files excluded); (b) `changed_since` single-ref behavior unchanged (BC);
  (c) `file_content_hashes` round-trips + detects a byte change.
- **Mutation:** revert the lane-check to a branch-range diff ⇒ test (a) goes red.
- **Adversarial:** WS-D flagged for fresh-context kata-review at closeout (L8).
- **Commit:** `fix(orchestrate,footprint): commit-scoped lane-check + file-hash stamping (F5, M4 subst.)`.

## Phase 4 · F3 — Worker liveness: structured heartbeat + monitor  (WS-E)

- **Owns:** `skills/coordinate/kata-orchestrate/SKILL.md` (dispatch template + a new monitoring
  section), `protocol/board.md` (PROGRESS semantics), `tools/kata_board.py` + test IF PROGRESS needs
  structured-field engine support.
- **Change (board):** define the structured `PROGRESS` line to carry `modulesDone/modulesOwned`
  (the M4 slack-timing signal). PROGRESS stays **excluded from concurrency evidence** and
  coordination-ignored for gating (L5) — it is a *liveness/progress* signal only.
- **Change (dispatch template, `:254-259`):** worker MUST emit a periodic `PROGRESS` line (e.g. per
  owned-module completed), in addition to `CLAIM`/`DONE`.
- **Change (monitoring section — new):** orchestrator liveness monitor detects a worker stale past a
  configurable deadline and routes it through the **existing escalation / kata-diagnose machinery**
  (nudge → escalate → human-gated re-dispatch). **No blind SIGKILL, no auto re-dispatch without the
  existing gate** (L5).
- **Versions:** bump `kata-orchestrate` semver.
- **Verify:** if `kata_board.py` changed: `uv run pytest tools/tests/test_kata_board.py -q` green +
  mutation on the new field. If prose-only: `validate_skills.py` green + explicit no-code-bearing note.
- **Commit:** `feat(orchestrate,board): structured PROGRESS heartbeat + liveness monitor (F3, M4 subst.)`.

## Phase 5 · WS-A — Tool-agnostic security-gate posture + documented-acceptance  (Lever 2 + F6)

- **Owns:** `protocol/config.md`, `skills/evaluate/kata-evaluate/SKILL.md` (rubric item 2 +
  acceptance-soundness), `skills/coordinate/kata-orchestrate/SKILL.md` (generic security-gate prose),
  `skills/evaluate/kata-report/SKILL.md`, `skills/coordinate/kata-bootstrap/SKILL.md`.
- **Change (config):** add `securityScan: required | when-available | off` to the preflight/config
  block; default `when-available`; **absent field ⇒ today's behavior byte-for-byte** (BC, documented).
- **Change (evaluate item 2):** "the security scan clean" → tool-agnostic; add the terminal-state
  ladder (required→fail-closed; when-available→run-or-`degraded`+surface; documented-acceptance graded
  for **soundness** — reason + expiry + board DECISION — not raw count). Add a rubric line grading
  acceptance soundness (L6).
- **Change (orchestrate generic gate `:261-262`):** tool-agnostic "security scan" + the documented-
  acceptance terminal state. **Do NOT touch** the debug-mode `snyk_code_scan` (`:138`) or IaC
  `snyk_iac_scan` (`:269`) wirings — those are intentional named integrations.
- **Change (report):** grade acceptance state, not only raw Snyk count.
- **Change (bootstrap):** write the `securityScan` posture into `kata.config` (default when-available;
  surface `off` at handoff).
- **Versions:** bump the four edited skills; `check_protocol_schemas` green for `config.md`.
- **Verify:** `validate_skills.py` green; `uv run pytest -q` green; **BC test**: absent `securityScan`
  ⇒ behavior byte-for-byte unchanged.
- **Adversarial:** WS-A flagged for fresh-context kata-review at closeout (L8) — the spine-gate change.
- **Commit:** `feat(security-gate): tool-agnostic + securityScan posture + documented-acceptance (Lever2/F6)`.

## Phase 6 · F4 — Greenfield seeding checklist (overlay-scoped)  (WS-F)

- **Owns:** `skills/execute/kata-lang-profile/resources/python.md`,
  `skills/coordinate/kata-orchestrate/SKILL.md` (generic precondition only).
- **Change (overlay):** add a Python src-layout seeding checklist — `uv init` + `[build-system]` +
  `[tool.setuptools.packages.find] where=["src"]` + verify `uv run python -c "import <pkg>"` BEFORE
  wave-1 dispatch.
- **Change (orchestrate precondition — generic):** add a wave-1 precondition "the project's own
  package is importable," delegating language specifics to the overlay (agnostic core stays language-
  free, L7).
- **Versions:** bump `kata-lang-profile`, `kata-orchestrate` semver.
- **Verify:** `validate_skills.py` green (prose-only ⇒ explicit no-code-bearing note).
- **Commit:** `feat(lang-profile,orchestrate): greenfield src-layout seeding precondition (F4)`.

## Phase 7 · Closeout — index, gate, adversarial review

- **Regenerate index:** `uv run python validate_skills.py --write` → README skill-index in sync; all
  version bumps reflected.
- **Full green gate:** `uv run pytest -q` (≥ 2177 + new tests, 0 fail) + `validate_skills.py` 0/0.
- **Snyk:** medium+ 0 on changed Python (`kata_preflight.py`, `graph_gen.py`, `footprint.py`,
  `kata_board.py` if touched) — or documented-acceptance per L6.
- **Adversarial review (L8):** fresh-context `kata-review` on **WS-A** (security posture) and **WS-D**
  (lane-check). Any material finding → fix-in-loop against this frozen plan, re-gate. SHIP required.
- **Records:** `CHANGELOG.md` entry; `.planning/DECISIONS.md` (L1–L10 as a dated decision);
  `.planning/LESSONS-LEARNED.md` (verified-before-fix discipline + the three reshaped fixes).
- **Commit:** `chore(release): closeout Milestone 1 hardening — index, records, gate green`.
- **Handoff:** PR `hardening/kenjiri-lessons` → `master`; Milestone 2 (Freeze/Float) opens as its own
  spec on the hardened baseline.

---

## Verify conservation

The final gate (P7) re-runs the entire suite + validator + Snyk against the integration head — no
phase's local green substitutes for the full gate. Baseline `653f501` is the drift-gate reference:
baseline-green must stay green (BC criteria in DESIGN §Acceptance).
