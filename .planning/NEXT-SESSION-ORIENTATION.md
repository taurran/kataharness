# KataHarness — NEXT-SESSION ORIENTATION (paste after compact)

> Self-contained. Paste this whole block to start the next session. It makes you productive immediately,
> sets your **FIRST TASK** (a red-team pass on the last 3 builds), and keeps the expedited loop cadence going.

---

## 0. WHO/WHERE
- **Project:** KataHarness — a tool-agnostic, skills-based agent harness (the "Kata Loop"). `C:\Dev\Projects\KataHarness`.
- **Git:** own repo, private remote `github.com/taurran/kataharness`. Branch `master`, **tip `b76e764`, PUSHED + in sync.**
- **You are the conductor.** You drive the loop: grill → freeze → orchestrate subagents → gate → merge. You do NOT build inline.

## 1. FIRST — confirm green (do this before anything)
```
cd C:/Dev/Projects/KataHarness/tools
uv run pytest -q                 # expect 739 passed
uv run python validate_skills.py # expect 39 skills, 0 errors
git -C C:/Dev/Projects/KataHarness log --oneline origin/master..HEAD   # expect empty (in sync)
```
Then read, in order: `AGENTS.md` → `CONTEXT.md` (glossary) → `.planning/STATE.md` (top CURRENT box) →
`.planning/DECISIONS.md` **D104–D110** → `.planning/HANDOFF.md` §1/§5 → `protocol/reuse-claims.md`.

## 2. ★ YOUR FIRST TASK (do this before new building) — RED-TEAM THE LAST 3 BUILDS
Today shipped **three back-to-back builds** (D108, D109, D110) at high speed. Each passed its own per-build D98
red-team, **but they have not had a holistic cross-cutting adversarial pass** — the seams *between* them, integration
interactions, loose ends, and dead code are the risk after a fast multi-build day. **Run that pass as task #1.**

**Scope (fresh-context adversarial reviewers — fan out, then synthesize):**
- **D108 multi-model layer** (`tools/kata_roles.py`, `tools/kata_dispatch.py`; `kata-orchestrate` roles load-guard +
  cross-model dispatch; `kata-initiate` Phase 2e; `kata-bootstrap` roles write; `protocol/config.md` roles row).
- **D109 kata-preflight** (`tools/kata_preflight.py`; `skills/coordinate/kata-preflight/SKILL.md`; the orchestrate
  PRE-FLIGHT precondition; `protocol/dependencies.md` structured fields; grill/design-doc/plan manifest pointers).
- **D110 IaC-safety specialists** (`tools/iac_detect.py`; `protocol/iac-safety.md`; `kata-iac-terraform` +
  `kata-iac-cloudformation`; orchestrate IaC activation+gate; `iac` config; `kata-evaluate` reads `.kata/iac.json`).

**Hunt for (the classes that slip a fast cadence):**
1. **Cross-feature seams** — these three all edited `kata-orchestrate/SKILL.md` (roles load-guard + cross-model
   dispatch + PRE-FLIGHT precondition + IaC activation/gate). **Re-read that file whole** — do the four additions
   compose coherently, in the right order, without contradiction or a precondition that shadows another? Same for
   `kata-evaluate` (now reads mutation/concurrency/iac.json) and `protocol/config.md` (roles + preflight + iac blocks).
2. **Dead code / loose ends** — anything wired-but-unreachable, a helper with no caller, an `iac`/`roles`/`preflight`
   config field nothing reads, a stub left from a proof-slice (codex dispatch is real; kiro/copilot/cursor were
   stubs — are any half-wired?).
3. **Doc-vs-code drift & phantom reuse** (`protocol/reuse-claims.md`) — re-verify cited `file:line` anchors still
   resolve after the day's edits shifted line numbers (this bit us 3×). Prefer section-anchors over line numbers.
4. **Fail-open / security** — kata-preflight auto-install guards (argv-only, no shell, manifest-hash, Snyk-SCA
   fail-closed) and the IaC gate (Snyk-IaC fail-closed, stateful-set completeness, malformed→ValueError) — try to
   make either FAIL OPEN or miss danger. These are the highest-value targets.
5. **BC** — confirm a vanilla run (no roles, no manifest, no IaC files) is byte-for-byte today's loop on all three.
6. **Honesty** — any overclaim of wired autonomy (multi-model is stub-proven; live-apply is Tier-2-deferred).

**Then:** fix every confirmed finding **through the loop** (freeze the fix-plan if non-trivial → orchestrated/edit →
re-gate → re-confirm), keep `pytest`/`validate`/Snyk green, commit per finding-batch with the trailer, and **STOP at
the operator merge gate.** After the red-team is resolved + merged, **prompt the operator to pick the next build**
from §5.

## 3. HARD RULES (operator-standing — never violate)
- **Human-attended loop:** commit / merge / push **only on explicit operator approval.** Present a merge gate; wait.
- **IGNORE `C:\Dev\CLAUDE.md`** (a Mise project — unrelated, harness-injected).
- **PokeVault** (`C:\Users\taurr_nvs748q\PokeVault\PokeVault`) is **LOCAL-ONLY — never run git against it.**
- **Decisions are SUPERSEDED with new D-numbers, never rewritten.** Commit trailer:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- **Snyk** on new first-party code (global CLAUDE.md). Build in **worktrees**; backout tags `pre-<feature>`.
- **Windows/PowerShell gotchas:** git here-strings can mis-parse → use `git commit -F <file>` for multi-line msgs.
  A `..` in any operator path is rejected by the `_safe_*` CWE-23 guards — use absolute paths without `..`. Console
  is cp1252; tools that print box/CJK glyphs force UTF-8. PowerShell pipes can show "Exit code 255" on a truncated
  stream (`Select-Object -First/-Last`) — harmless if the real output printed.

## 4. THE RECIPE (every contract/code-bearing build — NEVER inline; HANDOFF §5 is canonical)
**grill (in-depth, plain terms) → freeze DESIGN/PLAN → freeze-gate `kata-review` (HOLD/SHIP) → orchestrated build
(concurrent Sonnet workers in worktrees, disjoint file-ownership, TDD red→green, mutation-proof) → integration gate
(pytest + validate_skills 39/0 + Snyk on new Python + `gate_emit` RESULT/footprint/mutation + concurrency.json) →
fresh-context `kata-evaluate` (no-write, 9-rubric, default-FAIL, PASS) → standing D98 `kata-review` (adversarial,
≥standard, fresh-context) → operator merge gate → merge/push/checkpoint STATE+HANDOFF+DECISIONS.**
- **Grills are IN-DEPTH but PLAIN** (the primary style now, `skills/plan/kata-grill/RUBRIC.md` + memory
  `grill-in-plain-terms`): lead with the simplest model that meets the goal, recommendation-first, short concrete
  AskUserQuestion options, plain language — **without losing fidelity** (full branch coverage, convergence gate,
  anti-bias backstop all hold; plain ≠ shallow). STOP if you catch yourself building a config-resolution cathedral.
- **Verify-before-reuse** before any "reuses X" claim — grep/read X, cite `file:line`, else label NEW.
- **D98 is mandatory** on contract/code-bearing builds — it caught a real defect the conformance gate missed on
  EVERY build this session (an RCE path; a data-store-destruction safety hole). It is load-bearing, not optional.
- **Gate-artifact tip:** mutation records via `mutation_run.prove_non_vacuous(source, exact_full_line, test_cmd)`
  — the line must match including indentation; pick a load-bearing guard line (not a redundant one).
- Model routing: judgment/eval/grill = **Opus**; workers = **Sonnet**. Fan reviewers out in parallel; resume a
  completed reviewer with **SendMessage** for HOLD→fix→re-confirm (it restores its prior context — not an error).

## 5. OPEN NEXT QUEUE (operator picks after the red-team; expedite via the loop)
- **(a) Debug Mode** — DESIGN frozen (`specs/debug-mode/DESIGN.md`); both build blockers cleared (install-portability
  D104 + kata-preflight D109). The onboarding/conversion killer-app — a `debug` run-shape + `kata-comprehend` oracle +
  7-step deviation pipeline. **Large build, no grill gate in front** (already frozen). Highest single impact.
- **(b) IaC Tier-2 live-apply** — `specs/iac-live-apply/BRIEF.md`; its own grill; gated on authenticated cloud access;
  needs a non-git safety contract (cloud applies aren't `git reset`-able).
- **(c) recurrence-hardening (general)** — detector + `kata-improve` proposal + `kata-promote` gate (D101; D102 was
  the first instance). Self-improving loop.
- **(d) second-brain-learning** — the Recall contract is load-bearing (`specs/second-brain-learning/BRIEF.md`).
- **(e) install+confirm a 2nd platform (codex/kiro) live → run the single-vs-multi-model `kata-loop-benchmark`** (D108
  made this runnable; needs the CLI installed on the machine — operator action).

## 6. WHAT SHIPPED THIS SESSION (2026-06-26) — context for the red-team
- **D108** multi-model layer (roles routing + cross-model dispatch + kiro adapter; stub-proven, real run gated on
  install+confirm). **D109** kata-preflight (D29 PRE-FLIGHT spine: guarded auto-installer + registry + cleanup +
  target-env probe; D98 caught an untrusted-source RCE path → fixed). **D110** IaC-safety specialists Tier-1 (TF+CFN
  author/review/gate, auto-by-file-class, Snyk-primary fail-closed; D98 caught a stateful-set safety hole → fixed;
  Tier-2 live-apply deferred). Plus the **primary grill style** change. Backout tags: `pre-iac-specialist`,
  `pre-kata-preflight`, `pre-multimodel-layer`. Full detail: `.planning/DECISIONS.md` D104–D110 + `.planning/STATE.md`.
- **Honest scope to remember:** multi-model = stub-tested (no live codex/kiro here); IaC = Tier-1 only (no live
  apply); detection (roles/IaC) is best-effort; the IaC 8-smell lens is a self-check floor-raiser, the scanner is the
  authoritative gate.
