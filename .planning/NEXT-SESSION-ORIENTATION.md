# KataHarness — NEXT-SESSION ORIENTATION (2026-07-02e · Freeze/Float M1 COMPLETE + MERGED · next: the TEST-PATH decision, then M4)

> Paste-ready, self-contained. You are a fresh coding-agent window resuming KataHarness. Read this top to
> bottom before touching anything. **Freeze/Float M1 is DONE and MERGED to master** (P0 engine + P1 substrate
> + the D139 integrated adval + P2 THE FLOAT — D137–D140, PR #5). Nothing is broken; nothing is mid-flight.
> **This session does NOT start with a build — it starts with an OPERATOR BRAINSTORM on the test path** (§4).
> ⚠️ IGNORE `C:\Dev\CLAUDE.md` (describes "Mise", unrelated). Follow `AGENTS.md` + the repo `CLAUDE.md` only.

## 0. WHO / WHERE
- **Project:** KataHarness — tool-agnostic, skills-based agent harness ("the Kata Loop") that one-shots
  complex tasks behind frozen plans + fresh-context default-FAIL gates. Dir `C:\Dev\Projects\KataHarness`.
- **Git:** private remote `github.com/taurran/kataharness`. Branch **`master`**, tip `0c82bc4`
  (merge of PR #5), clean. No open PRs, no feature branches.
- **You are the conductor:** you own the plan, the gates, and the merge. Build work runs through subagents;
  the fresh-context adversarial sweep is non-negotiable (it caught real unsoundness SEVEN times last session).

## 1. GREEN (verify first, from `tools/`)
- `uv run pytest tests -q -m "not integration"` → **2306 passed / 3 skip** (2 benchmark integration tests
  need network; run them separately with `-m integration` as an end-to-end smoke — they passed last session).
- `uv run python validate_skills.py` → **47 / 0 / 0** (add `--write` after any SKILL.md bump).
- Snyk medium+ **0** on `tools/`. 21 decision guards mutation-proven across the M1 unit.

## 2. WHAT SHIPPED LAST SESSION (the context you inherit)
- **D139 — integrated adval** of everything Milestone-1→P1: 9 fresh-context reviewers, 9× SHIP-WITH-FIXES;
  5 HIGHs + ~15 MEDs folded and mutation-proven. **L19:** unit-reviewed ≠ integration-reviewed — cross-seam
  holes live where no unit review looks; reviewer prompts must name ADJACENT seams.
- **D140 — M1-P2 THE FLOAT:** a `builds_against` dependent now dispatches at freeze, in parallel with its
  provider, under fail-closed machine-checked companions. Pieces: `tools/contract_gate.py` (final-gate
  re-derivation: supersede-id cross-check, pin/newest-supersede surface drift, commit-granular temporal
  invalidation coverage, base-module dangler scan, `.kata/contract-gate.json` artifact); `contract_edges`
  + `kata_restore` (P0/P1, hardened by the adval); `kata-plan/RUBRIC.md` `builds_against:` schema +
  authoring rules; `kata-orchestrate` **0.5.0** (dispatchable-at-freeze, freeze-time companion checks,
  route-time durable trailers `Kata-Supersede:`/`Kata-Invalidated:` on the superseding commit, contract
  final-gate step, fix-loop re-verification); `kata-evaluate` **0.3.0** (artifact-presence independence
  rule); `kata-review` RUBRIC surface 7 (contract-edge honesty backstop).
- **BC:** every float surface no-ops when no plan declares `builds_against` — **zero live runs exist.**
- Process record: PLAN-p2 survived three freeze-gates (HOLD 18 → HOLD 10 → SHIP-WITH-FIXES 7); two
  built-work sweeps folded. Full history in `.planning/specs/freeze-float-m1/PLAN-p2-float.md` §Gate history
  + `DECISIONS.md` D139/D140.

## 3. CONTEXT LOADING ORDER (stay lean)
1. This file + `.planning/HANDOFF.md` (frontmatter + the ★2026-07-02e block).
2. `AGENTS.md` (the spine) — `CLAUDE.md` is a pointer to it.
3. `.planning/DECISIONS.md` **D137–D140** (the whole M1 arc) + `LESSONS-LEARNED.md` **L18/L19**.
4. Only if the session touches the float: `.planning/specs/freeze-float-m1/{DESIGN,PLAN-p2-float}.md` +
   `tools/contract_gate.py` + the `kata-plan/RUBRIC.md` contract-edges section.
5. The doctrine (operator holds it): Freeze/Float validated draft v2 — ship order **M1 ✅ → M4 → M2 → M3**.

## 4. ★ THE SESSION OPENER — the TEST-PATH brainstorm (operator decision, NOT a build)
The operator directed: open by brainstorming the test path together, conversational prose (no popup menus).
The three candidate paths, with what each proves:

- **(a) NEW-project one-shot** (`/kata-start` → the full loop on a fresh small project). **The natural
  FIRST LIVE PROOF OF THE FLOAT:** plan it with a genuine provider/dependent split (e.g. a core engine
  module + a consumer UI/CLI task that only needs the engine's interface) so the plan declares a real
  `builds_against` edge — the planner authors `contracts/<id>/`, the pin is computed at freeze, the
  dependent dispatches in wave 1 alongside its provider, and the final gate's contract checks run live for
  the first time. Everything is currently proven only by fixtures. Candidate scale: Kenjiri-sized or smaller.
  Project location per operator settings: `~\PokeVault\PokeVault\projects\`.
- **(b) VERSION-UP an existing project.** **Kenjiri is PAUSED mid-run** (2026-07-01: T1/T2/T4 integrated,
  T3/T5 were in-flight; resume steps in the operator's memory file) — resuming it also live-tests
  `kata_restore`'s hardened restore path (the adval-fixed trailer parsing) on a real interrupted run.
  Other candidates in the operator's portfolio: CPP, kiban, kagami, PokeVault (each has its own repo state;
  ask the operator which, if any).
- **(c) BUG-FIX / DEBUG-MODE review run** on an existing repo (`/kata-onboard` → Debug Mode): exercises
  the comprehension pass + diagnose/fix loop + the M1-hardened gates on real defects. Debug Mode has had
  no live run since it was built (BACKLOG deferral: "Debug Mode live run n=0→1").
- Combinations are legitimate (e.g. (a) now for the float proof, (b) Kenjiri resume after).
- **After the test path: M4 (inline evaluator/reroll)** — consumes the M1 edges + the F5 file-hash and F3
  heartbeat substrate that Milestone 1 laid down for it. M4 gets its own grill → freeze → gate cycle.

## 5. HARD RULES (no exceptions — unchanged, plus one new)
- **Freeze-gate discipline:** grill → freeze DESIGN/PLAN → fresh-context adversarial gate (HOLD→SHIP) →
  build (TDD, mutation-proof, disjoint ownership) → integration gate → fresh-context sweep → operator merge
  gate. Never self-certify. Seven gates caught real unsoundness last session — the discipline is load-bearing.
- **M1-L9 / D136 fail-closed:** decision-code reading external artifacts hard-fails on absent/malformed
  input; never a silent permissive default.
- **NEW — L19 sweep rule:** any multi-piece body of work gets ONE integrated cross-seam adval before
  anything builds on top of it; reviewer prompts name the adjacent seams (what consumes this? what does
  this reuse?).
- **bump-on-modify** (SKILL.md edits; shared RUBRIC needs no peer bump; `validate_skills --write` regens
  the README index). **5 frozen `kata_install.py` engine fns byte-identical; stdlib-only install path.**
- **Commit only on explicit operator approval** (re-ask each session). GitHub-flow: branch → PR → merge →
  delete; never straight to master. Complex commit messages via `git commit -F <file>` (PowerShell mangles
  here-strings).
- **Supersede-never-rewrite** decisions; new D# ≥ **D141**. **Model routing:** judgment/plan/grill/gate at
  the session anchor; build/encode workers tier down.
- If a run declares `builds_against`: the P2 obligations live in the DESIGN Phasing (supersede-id
  cross-check, contracts/ scan anchoring, raise-consumption, ownership-dir expansion) and are implemented
  in `contract_gate` — do not re-derive them ad hoc.

## 6. OPEN ITEMS (tracked, none blocking)
- BACKLOG **#17** RESULT.json security-state carrier · **#18** `.snyk` vendor-specific acceptance artifact
  (L6 amendment) · **#19** sprint-blind guard config-namespace coverage · **#20** preflight cleanup-helper
  raw manifest read — all adval deferrals, all small.
- Whole-dir contract retirement (DESIGN Amendment #2 — needs a retirement-record design, later milestone).
- Known-stale by append-only convention: the D98 record's "step 6" anchor (now step 7) — do not edit.
- PreCompact-hook live-proof + benchmark-D5 real fixture remain deferred (pre-existing).
