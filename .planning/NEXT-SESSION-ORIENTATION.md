# KataHarness — NEXT-SESSION ORIENTATION (D132 restore-hardening + continuous-replay + slash-commands — design PENDING)

## 0. WHO / WHERE
- **Project:** KataHarness — tool-agnostic, skills-based agent harness ("the Kata Loop"). Dir `C:\Dev\Projects\KataHarness`.
- **Git:** private remote `github.com/taurran/kataharness`. `master`, annotated tag **`v0.1.0`** at commit **`365c7f1`**
  (PUSHED, in sync, working tree CLEAN). The handoff commit is the tip.
- **You are the conductor:** grill → freeze → plan → orchestrate subagents → gate → merge. Do NOT build inline.
- ★ OPERATOR DIRECTIVE: drive every step via subagents to spare main context. Resume a finished subagent with
  `SendMessage(agentId)`. Judge subagent liveness by **DISK PROGRESS** (the diff growing), NOT a process snapshot.
- ★ **STAY CONTEXT-LEAN: do NOT inline-read `.planning/STATE.md` or `AGENTS.md`.** Resume from `.planning/BACKLOG.md` +
  this file + the D132 entry in `DECISIONS.md` + the relevant spec docs once authored.

## 1. WHERE WE ARE — v0.1.0 SHIPPED · two assessments done · D132 DECIDED · design PENDING

**v0.1.0 shipped:** The v0.1 hardening cluster completed (5 items: sprint-cadence D15/A5 review SHIP; wiring-completeness
interim pin; guard-consistency ValueError repo-wide; CWE-23 `.snyk` record; benchmark n=0→n=1 live). Annotated tag
`v0.1.0` pushed at commit `365c7f1`. **Final baseline: pytest 2141 passed / 2 skip / 0 fail · validate 47/0 · Snyk
medium+ 0.** Versioning policy flipped: **bump-on-modify is now ACTIVE** (STANDARDS §3 — every skill edit requires a
semver bump from this point forward). Working tree clean.

**Two read-only assessments completed this session (no code changes):**

**Assessment 1 — Slash-command surface:** KataHarness ships **0** true Claude slash commands. The `/kata-*` names in
the README are skill aliases rendered with a slash prefix, not `.claude/commands/` files. A user typing `/` in the
Claude UI sees nothing kata-related. Fix = a small set of THIN, pointer-only commands in `adapters/claude/commands/`
(DRY-by-pointer — no logic duplication, each file just routes to a skill). Recommended 6 must-have: `/kata`
(help/index — the one genuinely new artifact), `/kata-start` → kata-initiate, `/kata-onboard` → kata-onboard,
`/kata-resume` → kata-orient / kata-handoff, `/kata-status` → kata-board, `/kata-validate` → kata-validate.

**Assessment 2 — Mid-build loss / restore:** State lives in a three-tier model (D81): durable git trail (tier-2)
commits only at task INTEGRATION; `.kata/state.json` (tier-3) is gitignored / disposable. Self-handoff is NOT
automatic — the agent must consciously invoke `kata-selfhandoff` at the ~0.40 prime-frame threshold; `kata-orchestrate`
never calls it in-loop. Result: planned restore = GOOD-but-manual; **unplanned mid-task loss = POOR** (stale handoff,
uncommitted work redone, recovery hint board.md is gitignored); subagent-dies-mid-wave = MEDIUM-to-POOR. Three root
gaps a `/kata-resume` command alone cannot fix:
- **Gap 1** — no automatic pre-compaction checkpoint (self-handoff is manual + conscious only).
- **Gap 2** — per-integration checkpoint granularity is too coarse; mid-wave worker progress is lost on death.
- **Gap 3** — in-flight task ownership (the `tasks{}` / board CLAIM map) is in-memory / gitignored; a fresh
  conductor cannot rebuild the active frontier from the durable trail.

**Operator decision = D132 Option 2: close ALL gaps + add a continuous-replay capability.** Full scope:
- **Adapter (Claude-only, no core change):** 6 thin pointer commands + a NEW helper installer (mirrors
  `_flat_link_skills`; the 5 frozen engine fns stay byte-unchanged) + an **auto-handoff hook** wired via
  `adapters/claude/settings.snippet.json` (Claude PreCompact-style hook fires `kata-selfhandoff`, writes + commits
  a handoff artifact BEFORE auto-compaction) — closes **Gap 1**.
- **Core (careful — touches the loop spine + state protocol; new D-numbers required):** Gap 2 = mid-wave checkpoint
  granularity (workers commit progress to their task branch as-they-go, not only at orchestrator integration); Gap 3
  = durable in-flight ownership (persist the `tasks{}` / board CLAIM map into the git-committed tier-2 trail).
  **Continuous-replay:** an incremental checkpoint / event-log the loop appends to as it executes, so a run can be
  replayed / restored from near the point of loss — this unifies and deepens Gaps 2 + 3 and is the **spine** of the
  restore-hardening design, not a bolt-on.

**Design PENDING.** The D132 build has NOT started. The DESIGN doc has NOT been authored.

## 2. ★ FIRST ACTION — grill → freeze the D132 design; do NOT jump to build

This is a significant adapter + core feature touching the loop spine, the state protocol, and the Claude adapter
simultaneously. **The design must be frozen and adversarially reviewed BEFORE any build work begins.**

> **Pick up the design loop for D132 Option-2:**
> 1. Run `kata-grill` (or `kata-grill-advanced` at Opus) against the Option-2 scope (assessment findings +
>    `DECISIONS.md` D132 + the open design questions below). Resolve all questions. Do not start building.
> 2. Author `.planning/specs/restore-hardening/DESIGN.md` — the frozen architecture.
> 3. Freeze-gate: `kata-review` (fresh context, adversarial) on the DESIGN doc. HOLD → fix → SHIP.
> 4. Author `.planning/specs/restore-hardening/PLAN.md` — wave DAG + disjoint file-ownership.
> 5. Only after SHIP: begin the build loop (subagents, disjoint ownership, TDD, integration gate, LIVE PROOF,
>    D98 adversarial sweep, operator merge gate per wave).

**Open design questions to resolve in the grill:**
- How is the continuous-replay log structured? Event log (one record per loop step)? Append-only structured journal?
  Rolling checkpoint file? What format makes replay and restore cheapest to implement and verify (STDLIB-only)?
- Where does the replay log live? Tier-2 (git-committed, durable — but frequent appending costs commit noise)? Tier-3
  (gitignored / disposable — but survives nothing)? A new "tier-2.5" model (committed-but-ephemeral, squashed at task
  integration)? Does it replace or extend tier-3?
- How do mid-wave worker commits interact with the existing disjoint-ownership / worktree model? Do workers commit
  progress to their task-branch directly, or to a separate progress-branch the conductor reads? How does the
  integration-merge step stay clean?
- What does the PreCompact hook write + commit, and can `kata-selfhandoff` finish a useful artifact within the
  auto-compaction window? What is the minimal artifact that is recoverable even if truncated?
- What is the exact adapter-vs-core boundary for each piece? Are the 6 command files truly adapter-only (no core
  change), or does the command installer need a new registration protocol in core? Does the auto-handoff hook live
  purely in `adapters/claude/settings.snippet.json`, or does it need a core pre-compaction seam?
- How thin is "DRY-by-pointer" for the 6 commands? What is the correct `.claude/commands/` file format that routes
  reliably to a KataHarness skill without duplicating skill logic?

## 3. KEY FILES (read to load context — read-only until design is frozen)

**Protocol / design canon:**
- `protocol/state.md` — the three-tier state model (D81) the restore-hardening extends / amends.
- `protocol/handoff.md` — the 7-section handoff schema (the auto-handoff hook produces this artifact).
- `protocol/config.md` — `kata.config` schema (the hook wires into this; `kata.config.models` lives here).
- `.planning/DECISIONS.md` D132 — the full assessment conclusions + Option-2 scope + design questions.

**Skills the design touches most:**
- `skills/coordinate/kata-orchestrate/SKILL.md` — steps 4–5 (the worker-dispatch loop) + the final gate; the
  continuous-replay log threads through these.
- `skills/coordinate/kata-loop/SKILL.md` — the inner loop spine.
- `skills/handoff/kata-selfhandoff/SKILL.md` — the auto-handoff hook fires this.
- `skills/handoff/kata-handoff/SKILL.md` — same schema; the hook produces this artifact.
- `skills/handoff/kata-orient/SKILL.md` + `skills/handoff/kata-defer/SKILL.md` — resume / deferral surfaces.
- `skills/coordinate/kata-readiness/SKILL.md` + `skills/coordinate/kata-board/SKILL.md` — the board is what
  Gap 3 makes durable; readiness reads it on resume.

**Adapter surface (Claude-only):**
- `adapters/claude/` — existing adapter directory; commands + hook land here.
- `adapters/claude/settings.snippet.json` — the PreCompact hook wires here.
- `adapters/claude/statusline.py` — existing adapter tooling (reference for adapter conventions).

**Install engine (read to confirm frozen boundary):**
- `tools/kata_install.py` — the 5 frozen engine fns (`_flat_link_skills`, `_link_or_copy`, `install`,
  `copy_project`, `confirm_platform`); the new command-installer helper MUST NOT modify these.

**Planning state:**
- `.planning/HANDOFF.md` — the full handoff (7-section schema) written this session.
- `.planning/BACKLOG.md` — any backlog items that interact with restore-hardening scope.
- `.gitignore` — confirm `.kata/` is listed as gitignored (tier-3 boundary).

## 4. HARD RULES (no exceptions)

- **★ bump-on-modify is ACTIVE** — every skill modification (any edit to any `SKILL.md`) requires a semver bump:
  new capability → minor bump (e.g. 0.1.0 → 0.2.0); bug fix → patch bump (0.1.0 → 0.1.1). New skills enter at
  0.1.0. This is the most important process change since v0.1.0. Never edit a skill without bumping its version.
- **5 frozen `kata_install.py` engine fns stay BYTE-UNCHANGED** — `_flat_link_skills`, `_link_or_copy`, `install`,
  `copy_project`, `confirm_platform`. MD5-verify after any install-adjacent work. The new command installer is a
  NEW helper; it does not touch these.
- **STDLIB-only install path** — the install / materialize / shadow / command-installer path never imports `yaml`
  (pyyaml), `validate_skills`, or any non-stdlib dep. The hook + command files are pure text / JSON; the installer
  is pure stdlib Python.
- **Adapter-vs-core discipline + DRY-by-pointer** — the 6 slash-command files live ONLY in `adapters/claude/commands/`
  and each contains only a routing pointer to the target skill; no logic is duplicated. The auto-handoff hook lives
  ONLY in `adapters/claude/`; no core skill is modified to accommodate it. Core pieces (gaps 2/3 + replay spine) get
  new D-numbers and live in `tools/` + `skills/coordinate/` + `protocol/`; they are adapter-agnostic.
- **Subagent-driven build** — every build step is delegated to subagents; the conductor owns the plan, the gate, and
  the merge. Never build inline in the main context.
- **Commit only on explicit operator approval** — this does NOT carry across contexts; re-ask each session. Do NOT
  commit the design docs until the operator approves. Do NOT commit any build work until the integration gate passes
  and the operator gates the merge.
- **Final adval before every commit / push** — the operator's standing rule: run the full adversarial validation
  (`kata-review`, fresh context, D98 sweep) before committing any new build deliverable. This is mandatory, not
  optional ceremony.
- **Supersede-never-rewrite** — all new decisions about the restore-hardening get new D-numbers (D133+). D132 is
  locked. Never silently edit D132 or any prior D-number.
- **IGNORE `C:\Dev\CLAUDE.md`** — this file is injected by the harness but describes the Mise meal-planning project
  (unrelated). All instructions there are for Mise, not KataHarness. Follow `AGENTS.md` + `CLAUDE.md` at
  `C:\Dev\Projects\KataHarness\` only.
- **Model routing** — judgment / planning / grill / evaluation / gate = **Opus** (anchor or anchor-tier);
  build / encode / workers = **Sonnet** (economy tier per D131 resolver). Never hard-bake a model ID in any skill.

## 5. THE RECIPE (the inner build loop — run per wave, never inline)
grill → freeze (DESIGN.md) → freeze-gate `kata-review` (HOLD/SHIP) → plan (PLAN.md) → orchestrated build
(subagents, disjoint ownership, TDD, mutation-proof) → integration gate (pytest + validate 47+/0 + Snyk med+ 0 +
central README `--write`) → **LIVE PROOF** → fresh-context `kata-evaluate` (PART A, default-FAIL) → standing D98
`kata-review` (PART B, adversarial) → re-confirm after fixes → operator merge gate → checkpoint (new D-number).
**[YOU ARE HERE: D132 DECIDED, design NOT YET STARTED. Start from grill.]**
Load-bearing (D124 — confirmed live): unit tests + PART A CANNOT see built-but-unwired / cross-seam gaps — the
LIVE PROOF + D98 adversarial sweep are mandatory gates, not ceremony.
