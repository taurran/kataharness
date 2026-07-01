# KataHarness — NEXT-SESSION ORIENTATION (restore-hardening SHIPPED · pick the next initiative)

## 0. WHO / WHERE
- **Project:** KataHarness — a tool-agnostic, skills-based agent harness ("the Kata Loop") that one-shots complex
  coding tasks behind frozen plans + a fresh-context default-FAIL evaluator. Dir `C:\Dev\Projects\KataHarness`.
- **Git:** private remote `github.com/taurran/kataharness`. Branch **`master`**, tip **`16007f7`**. Tag `v0.1.0`
  at `365c7f1`. **Everything is committed, pushed, and the working tree is CLEAN.**
- **You are the conductor:** you own the plan, the gates, and the merge. Drive real build work through subagents
  (Sonnet for build/encode, Opus for judgment/grill/gate). The fresh-context adversarial sweep is non-negotiable.
- ⚠️ **IGNORE `C:\Dev\CLAUDE.md`** (it describes "Mise", an unrelated meal-planning app). Follow `AGENTS.md` +
  the repo's own `CLAUDE.md` only.

## 1. WHERE WE ARE — restore-hardening SHIPPED; nothing in flight
Last session designed, built, and **MERGED to master** the D132 Option-2 **restore-hardening** initiative, plus a
recurrence-hardening guard and a README refresh. Three PRs/commits landed on master:
- **PR #1 (`0bc2a0e`)** — restore-hardening (lean scope): (A) six pointer-only `/kata` slash-commands +
  additive installer; (B) durable board → orphan ref `refs/kata/trail`, integration-cadence checkpoint +
  `Kata-Task:<id>` trailer, **task-granular lost-run restore**, and a PreCompact auto-checkpoint hook. Decisions
  **D133** (recovery-ref git carve-out), **D134** (task-granular re-dispatch), **D135** (board-is-the-trail —
  supersedes D132's continuous-replay-SPINE scope; the journal subsystem was CUT).
- **`70542a0`** — **D136** silent-permissive-default guard (default-FAIL generalized to built decision-code;
  D33 never-tiered family; prose guards in `kata-tdd` 0.1.1 + `kata-review`).
- **PR #2 (`16007f7`)** — salesy README landing-page refresh (honest maturity preserved).

**Green:** `pytest 2170 passed / 3 skip / 0 fail` (run with `-m "not integration"`) · `validate 47/0` ·
`Snyk medium+ 0`. **The loop caught + fixed 4 silent-under-dispatch bugs during the build** that the passing
tests had blessed — every one via a fresh-context adversarial sweep. That is the load-bearing discipline here.

## 2. ★ FIRST ACTION — re-anchor, confirm green, pick the next initiative WITH the operator
**There is NO forced next build.** Do NOT assume the next task. Instead:
1. Confirm green: `tools/.venv/Scripts/python.exe -m pytest tools/tests -q -m "not integration"` → expect
   ~2170 passed, 0 fail; `... -m validate_skills` → 47/0.
2. Read `.planning/HANDOFF.md` (§4/§6) + `.planning/BACKLOG.md` for the candidate work.
3. **Ask the operator which initiative to start.** Strongest candidates (their call):
   - **(a) live-proof #2** — confirm Claude's PreCompact hook actually fires synchronously with a usable budget
     in a real session (the ONE unproven seam of the shipped restore feature). Only confirmable live. If it does
     not fire as assumed, restore still works via the integration-cadence checkpoint — it degrades safely.
   - **(b) restore follow-ups #14–#16** — small, safe-direction polish.
   - **(c) a v0.1.x deferral (#6–#13)** — e.g. Debug Mode live run, benchmark→improve hook.
   - **(d) a scheduled larger build** — wiring-completeness gate, or the second-brain-learning spec (D99).
4. Only once an initiative is chosen: run the full loop (§5).

## 3. KEY FILES
- `.planning/HANDOFF.md` — the full 7-section handoff (read first).
- `.planning/BACKLOG.md` — the next-work menu (#6–#16 + scheduled builds).
- `.planning/DECISIONS.md` — decision ledger; skim the tail (D131 → **D136**).
- `.planning/specs/restore-hardening/{DESIGN,PLAN}.md` — the frozen spec (if touching restore code).
- `tools/kata_trail.py` · `tools/kata_restore.py` — the shipped durability + restore engines.
- `tools/kata_install.py` — the installer; the **5 frozen engine fns** (`_flat_link_skills`, `_link_or_copy`,
  `install`, `copy_project`, `confirm_platform`) must stay BYTE-UNCHANGED.
- `AGENTS.md` — the vision + spine + conventions (canonical). `README.md` — the just-refreshed landing page.

## 4. HARD RULES (no exceptions)
- **★ D136 (new, load-bearing):** any decision-bearing computation you BUILD that reads/parses an external
  artifact to drive a dispatch set / resolver output / gate verdict must **hard-fail on absent/unparseable input**
  — never a silent permissive default (empty set, None-inherit, vacuous-pass). Governs INPUTS, not empty OUTPUTS;
  designed fail-safe fallbacks are exempt. `kata-tdd` now requires one absent/malformed-input test for such fns.
- **bump-on-modify ACTIVE:** every SKILL.md edit → semver bump (minor = new capability, patch = fix). A shared
  `RUBRIC.md` edit needs NO peer bump. Run `validate_skills --write` to regen the README index after a bump.
- **5 frozen `kata_install.py` engine fns stay byte-identical** (MD5/`git diff`-verify after any installer work).
- **STDLIB-only on the install/materialize path** — never import `yaml` or `validate_skills` there. (Runtime
  tools like `kata_restore.py` MAY use `yaml`; the install path may not.)
- **Commit only on explicit operator approval** — re-ask each session; it does NOT carry across contexts. Follow
  GitHub-flow: branch per feature/phase → PR → merge → delete branch. Never commit straight to master.
- **Final fresh-context adversarial sweep before every commit** (standing operator rule). It caught 4 bugs this
  session the tests missed — do not skip it; do not self-certify correctness-critical work.
- **Supersede-never-rewrite** for decisions (new D-numbers ≥ D137; never edit a prior D-entry).
- **Model routing:** judgment/plan/grill/eval/gate = **Opus** (anchor); build/encode/workers = **Sonnet**
  (economy). Never hard-bake a model ID in a skill.
- **Tests:** run via the repo venv and exclude integration offline (`-m "not integration"`) — 2 benchmark
  integration tests need `uv run pytest` over a temp clone, which fails offline. They are NOT a regression.

## 5. THE RECIPE (the build loop — once an initiative is chosen)
grill → freeze `DESIGN.md` → **adversarial freeze-gate** (`kata-review`, fresh context, HOLD→SHIP) → `PLAN.md`
(wave DAG + disjoint file ownership) → orchestrated subagent build (TDD, mutation-proof, disjoint ownership) →
integration gate (pytest + validate 47/0 + Snyk med+ 0) → **LIVE PROOF** (real artifacts, not asserted) →
fresh-context `kata-evaluate` (PART A, default-FAIL) + standing adversarial sweep (PART B) → operator merge gate →
commit on approval. **Load-bearing (D124/D136, confirmed live): unit tests + PART A cannot see cross-seam gaps or
silent-permissive defaults — the fresh-context sweep is the real catch.**

## 6. THE ONE THING THAT'S STILL UNPROVEN
Everything shipped is tested/gated EXCEPT whether Claude's **PreCompact hook fires synchronously with a usable
time budget** in a live session (live-proof #2). It's implemented + wired + documented as an assumption. If it
holds, the compaction-window auto-checkpoint works; if not, restore still works via the integration-cadence
checkpoint. This is the natural first thing to verify in a real Claude Code window — but it's the operator's call.
