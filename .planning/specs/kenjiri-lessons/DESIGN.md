---
spec: kenjiri-lessons
title: Release Hardening — Milestone 1 (Kenjiri one-shot lessons)
status: frozen
created: 2026-07-02
baseline:
  sha: 653f501
  pytest: 2177 passed / 3 skipped
  validate: 47 skills / 0 err / 0 warn
tags:
  - kata/hardening
  - kata/spine
  - release
---

# Release Hardening — Milestone 1

## Origin

Field lessons from the **Kenjiri v1.0.0 one-shot** (corgi-Tetris clone; kata-evaluate PASS 14/14,
kata-review SHIP, drift 0, 1 fix-cycle). The run surfaced six concrete harness defects (F1–F6) and a
separate efficiency doctrine (Freeze/Float, M1–M4). All six F-findings were **independently verified
against the code** by fresh-context investigators before this freeze — three required reshaping the
run's proposed fix (see LOCKED decisions).

## Scope boundary (what this milestone is and is NOT)

**IN — Milestone 1 (this freeze):** the six verified harness fixes, reshaped, delivered as six
workstreams built **directly and sequentially** (not dogfooded — see L8). Plus the tool-agnostic
security-gate posture (Lever 2 + F6).

**OUT — routed elsewhere:**
- **Freeze/Float doctrine (M1–M4)** → **Milestone 2**, staged in the doctrine's own ship order
  (M1 → M4 → M2 → M3; M3 behind dedicated adversarial review). NOT in this freeze (L9). Milestone 1
  is deliberately built as its *substrate*: WS-D exposes file-hash footprint stamping and WS-E exposes
  a structured progress heartbeat, both of which M4 consumes.
- **Lever 1** (soften the operator's global `~/.claude/CLAUDE.md` Snyk mandate) — **DONE** 2026-07-02,
  outside the harness repo (external config; reversible).
- **Kenjiri Part-3 backlog** (level-up SFX gate, numpy dev-group move, `.gitattributes`, play-polish)
  → the `kenjiri` repo's v1.1 loop-back. Out of scope (L10).

## Principle

Every fix either (a) closes a **silent-pass hole** in a spine gate (F1, F5), (b) restores **degraded
signal** the loop relies on (F2 blast-radius, F3 liveness), or (c) makes a gate **honest about a
terminal state it cannot reach by fixing** (F6 documented-acceptance) or **tool-agnostic** (Lever 2).
No fix relaxes default-FAIL. Where a fix adds an "accept and proceed" path, that path is **graded for
soundness by a fresh-context evaluator**, never rubber-stamped, and is always **surfaced**, never
silently taken.

## LOCKED decisions (drift-gate anchors — verbatim)

- **L1 — Lever 1 done, external.** Global mandate softened to conditional + toolchain-aware +
  acceptance-path. Not a harness change; recorded for provenance only.
- **L2 — F1 fix is key-presence + type validation, NOT block-on-empty.** Block only when the
  top-level `dependencies` key is **absent / misspelled / wrong-type**. A **present-but-empty `[]`
  stays `ready`** (it is a first-class, heavily-tested legit state — `.get("dependencies", [])`
  currently collapses all three cases, `kata_preflight.py:788`). The no-manifest BC short-circuit
  (`preflight_required` False) is untouched.
- **L3 — F2 fix is additive candidate generation in `_module_to_path`.** Append source-root-prefixed
  candidates **after** the existing import-relative + repo-root candidates (first-match-wins preserves
  flat-layout order → no false edges). Source roots derived from directories containing `__init__.py`
  (fallback `src/`). **Import edges only** — the "0 ref edges" symptom is a separate name-match
  heuristic and is out of scope.
- **L4 — F5 lane-check is commit/merge-base-scoped.** The per-task drift check names an explicit
  commit-scoped method (merge-base against the task's own commits), not a branch-range diff.
  `footprint.py` gains a merge-base-scoped changed-files helper AND **per-file content-hash stamping**
  (the M4 evidence-validity substrate). `changed_since(ref)` single-ref behavior is retained (BC).
- **L5 — F3 is structured heartbeat + liveness monitor + bounded intervention; NO blind auto-kill.**
  Worker dispatch template mandates a periodic `PROGRESS` board line carrying
  `modulesDone/modulesOwned` (structured — the M4 slack-timing signal). Orchestrator gains a liveness
  monitor that detects staleness past a deadline and routes a dark worker through the **existing
  escalation / kata-diagnose machinery** (nudge → escalate → human-gated re-dispatch). No SIGKILL,
  no automatic re-dispatch without the existing gate. `PROGRESS` stays excluded from concurrency
  evidence.
- **L6 — Security gate is tool-agnostic + posture-configurable + honest terminal state.**
  `kata.config` gains `securityScan: required | when-available | off` (default `when-available`;
  **absent field ⇒ today's behavior byte-for-byte**, BC). Gate prose says "the security scan" tool-
  agnostically (never "Snyk" by name in the *generic* gate; the debug-mode and IaC Snyk wirings are
  unchanged). Terminal states: `required` → fail-closed (unchanged spine); `when-available` → run if a
  scanner is wired AND toolchain supported, else `degraded` + surfaced (never silent skip); a finding
  that cannot be driven to zero → **harden → document acceptance in-repo (`.snyk` reason + expiry) →
  board DECISION → evaluator grades acceptance SOUNDNESS (not raw count)**. `off` → operator opt-out,
  surfaced at handoff.
- **L7 — F4 seeding lives in the language overlay, not the agnostic core.** The Python src-layout
  seeding checklist (`uv init` + `[build-system]` + `[tool.setuptools.packages.find] where=["src"]` +
  verify `import <pkg>`) goes in `kata-lang-profile/resources/python.md`. The agnostic core gains only
  a **generic precondition**: "the project's own package is importable before wave-1 dispatch,"
  delegating language specifics to the overlay.
- **L8 — Direct build, not dogfood.** This pass repairs the harness's own safety instruments; self-
  certifying that repair with the same (pre-fix) gates violates the fresh-context adversarial
  discipline. Build directly; **mandatory fresh-context adversarial review (kata-review) on WS-A
  (security posture) and WS-D (lane-check)** before closeout. The next feature milestone dogfoods the
  hardened harness.
- **L9 — Freeze/Float is Milestone 2, staged, out of this freeze.**
- **L10 — Kenjiri Part-3 backlog is out of scope.**

## Acceptance criteria (checkable end-state)

1. `validate_skills.py` → **0 errors / 0 warnings**; README skill-index regenerated (`--write`) and in
   sync; every edited SKILL semver-bumped (bump-on-modify).
2. `pytest` → **≥ 2177 passed, 0 failed, 0 unexpected skips**, PLUS new tests:
   - F1: malformed/renamed/absent-key manifest ⇒ `blocked`; present-empty `[]` ⇒ `ready` (regression
     guard on the legit state).
   - F2: src-layout `from pkg.mod import x` resolves an import edge to `src/pkg/mod.py`; flat-layout
     resolution byte-unchanged.
   - F5: commit/merge-base-scoped lane check reports only the task's own changed files when the task
     forked from an earlier integration head; per-file hash stamping round-trips.
3. `securityScan` absent ⇒ orchestrate/evaluate/report behavior **byte-for-byte unchanged** (BC test).
4. Snyk medium+ **0** on every changed Python file (`kata_preflight.py`, `graph_gen.py`, `footprint.py`,
   any board/heartbeat engine change) OR documented-acceptance per L6.
5. Fresh-context **kata-review = SHIP** on WS-A and WS-D (L8).
6. Baseline suite still green (BC): empty-deps manifest ⇒ ready; absent `kata/module/debug` unchanged;
   absent `securityScan` unchanged; flat-layout graph unchanged.

## Files touched (ownership map — see PLAN for per-phase partition)

| Area | Files |
|---|---|
| Preflight (F1) | `tools/kata_preflight.py`, `tools/tests/test_kata_preflight.py`, `skills/coordinate/kata-preflight/SKILL.md` |
| Graph (F2) | `tools/graph_gen.py`, `tools/tests/test_graph_gen.py` |
| Lane-check (F5) | `tools/footprint.py`, `tools/tests/test_footprint.py`, `skills/coordinate/kata-orchestrate/SKILL.md` (gate step), `skills/evaluate/kata-evaluate/SKILL.md` (item 4 note) |
| Liveness (F3) | `skills/coordinate/kata-orchestrate/SKILL.md` (dispatch+monitor), `protocol/board.md`, `tools/kata_board.py` (+test) if PROGRESS needs engine support |
| Security posture (WS-A: Lever2+F6) | `protocol/config.md`, `skills/evaluate/kata-evaluate/SKILL.md`, `skills/coordinate/kata-orchestrate/SKILL.md` (security gate prose), `skills/evaluate/kata-report/SKILL.md`, `skills/coordinate/kata-bootstrap/SKILL.md` |
| Seeding (F4) | `skills/execute/kata-lang-profile/resources/python.md`, `skills/coordinate/kata-orchestrate/SKILL.md` (generic precondition) |
| Closeout | `README.md` (index), `CHANGELOG.md`, `.planning/DECISIONS.md`, `.planning/LESSONS-LEARNED.md` |

**Shared-file note:** `kata-orchestrate/SKILL.md` (WS-D/E/A/F) and `kata-evaluate/SKILL.md` (WS-D/A)
are edited across phases in the PLAN's order; each phase touches a distinct section. Because the build
is sequential-direct, this is ordered editing, not concurrent merge.
