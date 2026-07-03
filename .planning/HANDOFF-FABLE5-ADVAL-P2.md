# DETAILED HANDOFF — fable5 session: adval all Milestone-1→P1 changes, then build M1-P2 (the float)

> **Paste-ready, self-contained.** You are a fresh coding-agent window (model: **Fable 5**) resuming KataHarness
> at `C:\Dev\Projects\KataHarness`. This handoff carries (1) the **logic behind the float assessment** — why
> Freeze/Float is sound and how its pieces fit; (2) the **enumerated set of every change** from Milestone 1
> through M1-P1 — the exact adval target; and (3) the **execution plan**: load context → comprehensive
> fresh-context adval of all those changes → fix any issues → then build **M1-P2 (the float)** under its own
> freeze-gate. Nothing is broken. Do NOT start P2 until the adval is clean and the operator says go.

---

## 0. THE PLAN (this session, in order)
1. **Load all end-to-end context** (§4 order). Confirm green (§3).
2. **Run a comprehensive fresh-context adval** over **every code-bearing change from Milestone 1 → M1-P1**
   (§6 enumerates them exactly). Each piece was individually reviewed as it was built; this is the
   **integrated, cross-seam sweep before the risky P2** — catch anything that slipped, any interaction
   between the six M1 fixes + the P0 engine + the P1 substrate, any residual fail-open, any BC break.
3. **Address every issue** the adval surfaces (fix → re-prove → re-scan). Keep green.
4. **Only then build M1-P2 (the float)** via the full freeze-gate recipe (§7). P2 is the behavior change to
   the dispatch core — it earns its own adversarial DESIGN freeze-gate (HOLD→SHIP) before any code.

⚠️ **IGNORE `C:\Dev\CLAUDE.md`** (describes "Mise", unrelated). Follow `AGENTS.md` + repo `CLAUDE.md` only.
⚠️ **Freeze/Float is the OPERATOR-DIRECTED Milestone 2 (D138) — do NOT re-question its legitimacy.** It is
recorded in ROADMAP/BACKLOG/STATE. The operator ingested the doctrine into the M1 pass and directed every step.

---

## 1. THE LOGIC BEHIND THE FLOAT ASSESSMENT (why this is sound)

**The doctrine (one sentence):** *Control governs WHAT gets built; efficiency governs WHEN and BY WHOM; drift
lives entirely in the WHAT.* The whole safety argument rests on this split: you can reorder/parallelize *when
and by whom* work happens (layer C — scheduling) **without** risking plan-drift, because drift can only enter
through the *WHAT* (intent = layer A, contracts = layer B), and those stay **frozen + human-gated**. So the
harness floats **only layer C**, under machine-checked fail-closed invariants.

**The mechanism — `builds_against` contract edges.** Today a dependent task waits for its provider task to
*integrate* before it can dispatch (`depends_on`). But if the dependent only needs the provider's **contract**
(its interface surface), not its implementation, it can dispatch **at freeze, in parallel** — the contract is
pinned and known, so there is nothing to wait for. That is the float: **free wall-clock, same tokens.** A
`builds_against` edge is `{ "<dependent-task>": [ "<contractId>@<surfaceHash>" ] }`, treated as *satisfied at
freeze*.

**Why the float is unsound WITHOUT its 3 companions (this is the crux of the assessment):**
- **Companion 1 — contract pin + invalidation.** If a dependent builds against a contract, that contract must
  be **immutable between freeze and supersede**, or the dependent is building against a moving target. Enforced
  by the **surface-hash pin** (`contract_edges.surface_hash` — pins signatures/return-annotations/decorators/
  class-headers, NOT bodies, so a provider filling in stub *bodies* does not trip it, but an *interface* edit
  does). If a contract genuinely must change, that is **never a re-decomposition** — it is a **human-gated
  supersede** that mechanically **invalidates every dependent bound to it** (`invalidation_set`), aborting
  in-flight consumers and re-opening integrated ones. Without this, a silent contract change strands consumers.
- **Companion 2 — stub lifecycle (provider-owned `contracts/<id>/`).** For the dependent to import the contract
  at freeze, the contract must *exist* at freeze. The **provider** authors a stub carrying `# KATA-CONTRACT-STUB`
  at freeze, then fills real behavior in its own task (deleting the sentinel). The **provider owns the contract
  dir** (one writer — this preserves disjoint-ownership; the dependent only *imports* it). The final gate proves
  **no stub sentinel survived** — else a dependent built against a hollow contract and the run is vacuously green.
- **Companion 3 — edge honesty.** A `builds_against` dependent's tests must import **ONLY the contract surface**,
  never the provider's implementation paths (`edge_honesty`). If they import impl, the edge is really a
  `depends_on` and dispatching it early is unsound — the dependent would run against code that does not exist yet.

**Why fail-closed everywhere (D136 / M1-L9).** Every predicate that drives invalidation or dispatch **hard-fails
on malformed/absent input**, never returns a silent permissive default. Rationale: a silent empty invalidation
set would *under-invalidate* — leave a dependent bound to a stale contract — which is the exact failure the
companions exist to prevent. `surface_hash` raises on a parse error; `invalidation_set` raises on malformed
`builds_against`; the (P2) final gate treats an absent/partial invalidation record as NEEDS_WORK.

**Why durability is git-commit-trailers, not `.kata/` (the v2 freeze-gate's headline catch).** `.kata/` is
gitignored and **rebuilt from `refs/kata/trail`, which snapshots only `board.md`** — so any recovery state in
`.kata/` is **lost on the canonical lost-run** (crash + `.kata/` wipe). Invalidation/supersede records MUST
therefore be **git-durable commit trailers** (`Kata-Invalidated:`, `Kata-Supersede:`) that survive the wipe.

**Why over-dispatch-safe (P1 restore subtract, D138).** On a crash, the restore subtract errs toward
**re-dispatching** an invalidated-then-re-integrated task (redundant work) rather than skipping it. Over-dispatch
wastes tokens; **under-dispatch loses work** (ships stale/wrong output). D134/D135: tier-2 authoritative, board
corroborates-never-gates, always err toward redoing.

**Why phased P0/P1/P2 (the assessment's process outcome).** The DESIGN went through **two fresh-context
adversarial freeze-gates, both HOLD** — the headline win: they stopped an unsound architecture **before any
code**. v1 HOLD caught 7 holes (ownership collision, unenforced BLOCK, un-superseded drift, silent-permissive
set, whole-dir hash, stub-scan-tested-location-not-content). v2 HOLD caught that the v1 durability fix **leaked
into disposable `.kata/`** and the surface extractor was over-scoped. Folding those converged on "M1 is a
multi-milestone program," so it was split so the **behavior change lands LAST**: **P0** (pure engine, zero
wiring, zero risk) → **P1** (durable substrate, additive/BC, still no float) → **P2** (wiring + the actual
float, re-gated on its own). This is why P0 and P1 are safe to have already built and merged-in-spirit while P2
waits.

---

## 2. BRANCH TOPOLOGY + STATE
```
master  8653faf  (Milestone 1 "Release Hardening" MERGED — PR #4, merge commit)
   └── freeze-float/m1-contract-edges   tip d26a0ba   (P0 + reconcile + P1 + doc-sync; PUSHED, tracking origin)
```
- **Milestone 1 (Release Hardening): MERGED** (D137, L18). F1–F6 + tool-agnostic security gate.
- **Freeze/Float M1 P0 + P1: DONE, reviewed SHIP, committed + pushed.** No PR yet (deliberately holding so the
  float ships reviewed-as-a-unit with P2).
- Everything committed + pushed; working tree clean.

## 3. GREEN (verify first)
- `pytest 2236 passed / 3 skip` — run from `tools/`: `uv run pytest tests -q -m "not integration"` (2 benchmark
  integration tests need `uv run pytest` over a temp clone → fail offline; NOT a regression).
- `uv run python validate_skills.py` → **47 / 0 / 0**. Snyk medium+ **0** on the changed tool modules.

## 4. CONTEXT LOADING ORDER (stay lean)
1. **This file.** + `.planning/NEXT-SESSION-ORIENTATION.md` + `.planning/HANDOFF.md` (frontmatter + ★2026-07-02c).
2. `AGENTS.md` — the spine (plan-no-drift · default-FAIL · agnostic-via-adapters · two-way handoff · versioned).
3. **`.planning/DECISIONS.md`** — **D137** (Milestone 1, L1–L10) + **D138** (Freeze/Float sanction + M1 DESIGN
   reconciliation + over-dispatch-safe + fail-open closures). Skim D131–D136 for the restore/model context.
4. **`.planning/specs/freeze-float-m1/`** — `DESIGN.md` (LOCKED **M1-L1…L9**, the two freeze-gate histories, the
   **D138 amendment**, the **Phasing** section) + `PLAN-p0-engine.md` + `PLAN-p1-substrate.md`.
5. **`.planning/specs/kenjiri-lessons/`** — `DESIGN.md` (LOCKED L1–L10) + `PLAN.md` (the Milestone-1 fixes).
6. **The built code** (the adval targets — §6): `tools/contract_edges.py`, `tools/kata_restore.py`,
   `tools/footprint.py`, `tools/graph_gen.py`, `tools/kata_preflight.py` + their test files.
7. The doctrine (north star, operator holds it): **Freeze/Float validated draft v2**. Ship order M1→M4→M2→M3.

---

## 5. HARD RULES (no exceptions)
- **Freeze-gate discipline** (proved its worth on 2 DESIGN HOLDs + several built-code catches): grill → freeze
  `DESIGN.md` → **fresh-context adversarial `kata-review` (HOLD→SHIP)** → `PLAN.md` → build (TDD, mutation-proof,
  disjoint ownership) → integration gate → **fresh-context adversarial sweep of built code** → operator merge
  gate. Never self-certify correctness-critical work. **P2 MUST be freeze-gated before the float lands.**
- **M1-L9 / D136 fail-closed:** decision-code that reads an external artifact to drive a dispatch set / verdict
  hard-fails on absent/malformed input — never a silent permissive default.
- **Durability = git-durable commit trailers, not `.kata/`** (gitignored, rebuilt from `refs/kata/trail`).
- **bump-on-modify:** every `SKILL.md` edit → semver bump (minor=capability, patch=fix); shared `RUBRIC.md` needs
  no peer bump; run `validate_skills --write` to regen the README index. **P0/P1 touched NO skills; P2 WILL**
  (kata-plan RUBRIC, kata-orchestrate, kata-review) — bump them.
- **5 frozen `kata_install.py` engine fns byte-identical; stdlib-only on the install path.**
- **Commit only on explicit operator approval** (re-ask each session). GitHub-flow; never straight to master.
- **Supersede-never-rewrite** decisions (new D# ≥ **D139**; never edit a prior D-entry).
- **Model routing:** judgment/plan/grill/gate = anchor (this session = Fable 5); build/encode workers tier down.
- **Complex commit messages via `git commit -F <file>`** — PowerShell mangles here-strings with `|`,`>`,`->`,`=>`,quotes.

---

## 6. ★ THE ADVAL TARGET SET — every change from Milestone 1 → M1-P1 (enumerate + attack)

Full body of work = `git diff 653f501..d26a0ba` (34 files, +2469/−132). Grouped below by initiative. Each piece
had its own review as built; the adval is the **integrated cross-seam sweep**. **Attack focus per item is noted.**

### A. Milestone 1 — Release Hardening (merged, D137). Code-bearing fixes:
| Fix | Files | What it does | Attack |
|---|---|---|---|
| **F1** preflight | `tools/kata_preflight.py` (+30), `test_kata_preflight.py` (+45) | fail-closed on a malformed manifest (absent/misspelled/wrong-typed top-level `dependencies`); a present-but-**empty** `[]` stays `ready` | Is the empty-vs-malformed boundary exactly right? Any manifest shape that still passes vacuously? |
| **F2** graph | `tools/graph_gen.py` (+81), `test_graph_gen.py` (+72) | `_discover_source_roots` + src-layout import resolution; src candidates appended **last** (flat layout byte-identical) | Does flat-layout resolution stay byte-identical? Any phantom edge? Nested-package / namespace-package edge cases? |
| **F5** lane-check | `tools/footprint.py` (+65), `test_footprint.py` (+87) | `changed_in_task` (three-dot merge-base diff), `file_content_hashes` (sha256, missing→None) | Three-dot vs two-dot correctness on odd fork topologies; missing→None handling; the M4 evidence-substrate contract |
| **F3** liveness | `kata-orchestrate/SKILL.md`, `protocol/board.md`, `protocol/config.md` | mandated PROGRESS heartbeat + liveness monitor (nudge→escalate→human-gated re-dispatch, **NO blind kill**); top-level `livenessDeadline` | Does orchestrate stay **sprint-blind** (no `delivery.` coupling)? Is PROGRESS truly excluded from coordination/concurrency? |
| **F6+Lever2** security | `kata-evaluate/SKILL.md`, `kata-orchestrate`, `kata-report`, `kata-bootstrap`, `protocol/config.md` | tool-agnostic `securityScan: required\|when-available\|off` (absent⇒when-available, BC); documented-acceptance graded for soundness | Does `required` fail closed on scanner-absence? Can the `when-available` carve-out leak into `required`? Is acceptance graded, never rubber-stamped? |
| **F4** seeding | `kata-lang-profile/SKILL.md` + `resources/python.md`, `kata-orchestrate` | greenfield "own package importable before wave-1"; Python specifics in the overlay | Is the precondition version-up-safe (BC for existing repos)? Overlay vs core split honest? |

### B. Freeze/Float M1-P0 — the pure engine (contract_edges):
- `tools/contract_edges.py` (+293) + `test_contract_edges.py` (+289, 38 tests). `invert`, `invalidation_set`
  (raise-on-malformed), `surface_hash` (narrowed, fail-closed, format-invariant, async-aware, bodies excluded),
  `surviving_stubs` (sentinel content scan; dangling-import half deferred to P2), `edge_honesty`. **Zero wiring ⇒ BC.**
  **Attack:** the fail-closed spine (does any predicate silently under-invalidate?); surface_hash residual
  (constants/aliases/`__all__` NOT machine-pinned — honestly documented?); the two `OSError` paths now closed
  (D138); zero-wiring claim (grep the tree — nothing imports it outside its test).

### C. Freeze/Float M1-P1 — durable substrate (kata_restore):
- `tools/kata_restore.py` (+111) + `test_kata_restore.py` (+204, +10 tests). `parse_plan_tasks` unions
  `builds_against` keys (M1-L2); `collect_integrated_tasks` subtracts `Kata-Invalidated:` (set-based,
  over-dispatch-safe) via the extracted `_scan_integration_commit_bodies`; `parse_supersede_trailers` (hash
  lowercased to match `_EDGE_RE`, for the P2 gate). **Attack:** BC of the scan extraction (None-vs-set error
  path, unbounded-NOTE parity); can the subtract ever UNDER-dispatch (the data-loss direction)?; regex symmetry
  with `contract_edges._EDGE_RE`; the malformed-`Kata-Invalidated:` surfaced-not-swallowed path.

### D. Docs/specs (consistency-checkable, lower priority):
DESIGN/PLAN specs (kenjiri-lessons, freeze-float-m1), DECISIONS (D137, D138), STATE/HANDOFF/ORIENTATION/CONTEXT/
ROADMAP/BACKLOG, CHANGELOG (+ the corrected benchmark honesty line), README, LESSONS-LEARNED (L18). **Attack:**
any remaining internal contradiction; any over-claim; DESIGN↔code drift (esp. `edge_honesty` signature, the
`.kata/invalidated.json` residue — should be fully gone).

**How to run the adval:** fresh-context reviewers (one per code module, or grouped), each told to try to BREAK
the change against its spec — default to finding holes. Prioritize B and C (Freeze/Float, unreviewed as an
integrated pair) and F6/F3 (spine-gate + sprint-blindness). Report SHIP / SHIP-WITH-FIXES / HOLD per item.
Fold every real finding, re-prove (mutation), re-scan (Snyk), keep green. Do NOT proceed to P2 with an open HOLD.

---

## 7. M1-P2 — what you build AFTER the adval is clean (re-gated)
The wiring + the actual float. Scope (DESIGN Phasing + change-map): `builds_against` schema in
`kata-plan/RUBRIC.md` (provider-owned `contracts/<id>/` + sentinel + retirement obligation); the
dispatchable-at-freeze clause (`kata-orchestrate:211,481`); the supersede enumerate+trailer+route (`:507-509`);
the **final-gate independent re-derivation** (`:525-540` — consumes `parse_supersede_trailers` +
`contract_edges.invalidation_set` + `Kata-Invalidated:` coverage; treats absent/partial as NEEDS_WORK) + the
**surviving-stub scan incl. the dangling-import half** (moved here from P0) + surface-drift checks; a
`kata-review` edge-honesty attack surface. **This is the ONLY place a contract-only dependent actually dispatches
early.** Run the FULL recipe (§5): grill → freeze `PLAN-p2` → **fresh-context adversarial freeze-gate on the
DESIGN/PLAN (HOLD→SHIP)** → build (bump every edited SKILL) → integration gate → fresh-context adversarial sweep
→ operator merge gate. The P1 substrate it consumes is ready and proven.

## 8. THREE THINGS MOST LIKELY TO BITE (in P2)
- **`surface_hash` residual:** constants/type-aliases/`__all__`/re-exports are NOT machine-pinned (M1-L1) — a P2
  contract leaning on a pinned constant MUST route to the `kata-review` backstop, not be assumed covered.
- **Provider-owns-contract:** `contracts/<id>/` is PROVIDER-owned only (M1-L4) — the disjoint-ownership invariant
  depends on it; the dependent never writes the contract.
- **Restore subtract is best-effort; the P2 final gate is the fail-closed authority** for malformed/partial
  invalidation records (M1-L9). Wire that re-derivation as the real gate, not the restore subtract.
