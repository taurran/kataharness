---
title: "Multi-Model Layer — FROZEN PLAN (full-layer build over the proof-slice)"
status: FROZEN (2026-06-26) — pending freeze-gate kata-review (HOLD/SHIP), then orchestrated build.
spec: multi-model-orchestration
compiled-from: DESIGN.md (§4 N1–N5, §8 build sequence) + the proof-slice (kata_roles.py, kata_dispatch.py)
recipe: HANDOFF §5 (freeze → freeze-gate review → orchestrated build → kata-evaluate → D98 review → operator merge gate)
ownership-disjoint: true
waves:
  - wave-1: [A, B, C]
  - wave-2: [D]   # depends_on C (the probe⊆dispatch invariant test imports kata_dispatch)
---

# Multi-Model Layer — FROZEN PLAN

> Turn the frozen DESIGN's PARKED full layer into wired machinery. The proof-slice already proved
> **validator→codex** end-to-end against a stub runner (`kata_roles` resolver + `kata_dispatch`
> brief/normalize/codex-adapter + N5 confirm probe + the `roles` config block). This build wires that
> chain into the live loop and generalizes it to a **second real adapter (kiro=researcher)** — the
> operator's stated vision (Claude=coder · Codex=validator · Kiro=researcher).
>
> Plain story (per [[grill-in-plain-terms]]): *when you set up a run you can say which model does which
> job; the orchestrator checks those assignments are real (installed + confirmed) and, when a job is
> assigned off-host, shells out over the shared filesystem via a brief/result file instead of spawning a
> Claude subagent; if the off-host model fails, it falls back to Claude and tells you.* No new
> orchestrator — a thin routing layer over existing machinery.

## LOCKED decisions (this PLAN; trace to DESIGN unless marked MP)

- **L-A — `roles` load-guard in `kata-orchestrate` Preconditions §0** (DESIGN N4; flips the
  `config.md:27` DESIGN-STAGED status). The orchestrator reads `confirmedPlatforms` via
  `kata_settings.confirmed_platforms()` (`tools/kata_settings.py:109`) + resolves `kata.config.roles` via
  `kata_roles.resolve_roles(roles_block, confirmed, host_platform)` (`tools/kata_roles.py:28`). **`host_platform`
  = the orchestrator's own runtime adapter identity** — `"claude"` in v1 (the only shipped dispatch adapter,
  `kata-orchestrate/SKILL.md:14`), which is also the resolver's default (`kata_roles.py:31`). The orchestrator
  *is* the host, so the host is its adapter identity, **not** a `kata.config` field (there is no
  `target.platform`); a **non-Claude orchestrator host is DEFERRED (LD11)**, so v1 hard-codes the Claude
  identity rather than inventing a config surface. A `ValueError` (unknown role / platform ∉
  confirmed) ⇒ **STOP + escalate at preflight** (same fail-closed posture as the existing
  mode/effort/tiers/modules guard, `kata-orchestrate/SKILL.md:34-50`). Absent `roles` ⇒ resolver returns
  all-on-host ⇒ today's loop byte-for-byte (BC1, DESIGN R5/LD3). **Slice A also flips `config.md:27`** from
  "DESIGN-STAGED / NOT yet wired / PARKED" to "wired: validated fail-closed at preflight via
  `kata_roles.resolve_roles`" (MAJOR-2 — else the live contract under-claims wired machinery).
- **L-B — cross-model dispatch path** (DESIGN LD4/LD5/LD6/LD7). At each **role-group dispatch site**, if
  the resolved role's platform ≠ host: build a BRIEF (`kata_dispatch.build_brief`, `kata_dispatch.py:42`)
  → `kata_dispatch.dispatch(brief, worktree)` (`kata_dispatch.py:149`) → read the normalized RESULT
  envelope → fold the role's `payload`. **LD6:** off-host dispatches run as concurrent background
  subprocesses reconciled with the rolling frontier + `.kata/concurrency.json`. **LD7:** RESULT
  `status ∈ {failed, timeout, fallback}` ⇒ **host fallback** (the existing Agent path) **+ log + surface**;
  a routed platform failing repeatedly is flagged unconfirmed for the run.
- **L-MP5 — role-group → dispatch-site map.** **validator** → the D98 red-team (`SKILL.md:248`) + the
  grounding-gate review (`SKILL.md:126-130`); **researcher** → `kata-research` on a research-needed
  escalation (`SKILL.md:122-137`); **coder** → the per-task worker dispatch (`SKILL.md:72`, sandbox=write);
  **evaluator** → host (the accept/send-back/reroll *mechanism* is DEFERRED, DESIGN §8.5); **orchestrator**
  → host only in v1 (LD11). **Proven v1 paths = the read-only roles (validator→codex, researcher→kiro);**
  coder-routing (write sandbox) is described and supported by `build_brief(sandbox="write")` but is **not**
  the proven path this build ships (honest scope).
- **L-C — multi-modal preflight question** (DESIGN LD3). `kata-initiate` gains a **Phase 2e** "Make this
  run multi-modal?" surfaced **only when** `confirmed_platforms()` lists a non-host platform; per-role
  assignment is chosen from `confirmedPlatforms`, surfaced in the Phase-2 mirror as a load-bearing value,
  and checked in the infer-then-confirm gate. Absent confirmation / no confirmed off-host platforms ⇒
  all-on-host (BC1).
- **L-MP4 — `roles` lives in `kata.config` only, written by `kata-bootstrap`.** It is executable routing
  (*how*), not intent (*what*), so it is NOT added to `INTENT.md`/`protocol/intent.md`. `kata-bootstrap`
  Phase 3 (`kata-bootstrap/SKILL.md:137-139`) gains `roles` in its written-fields list + a short body
  paragraph (write the confirmed assignment; omit when single-host — BC1). Config authority unchanged
  (INTENT wins on `target`; `roles` has no INTENT counterpart).
- **L-D — second dispatch adapter = kiro (researcher); install `.agents/skills/` targeting** (DESIGN N2
  step 4 + N5). `kata_dispatch._COMMAND_BUILDERS` (`kata_dispatch.py:123`) gains `"kiro"`;
  `kata_install._flat_link_skills` (`kata_install.py:137`) generalizes its skills-root so non-claude
  best-effort installs target the cross-tool **`.agents/skills/`** standard (claude keeps `<host>/skills/`);
  `kata_install._PROBE_COMMANDS` (`kata_install.py:262`) gains `"kiro"`.
- **L-MP2 — invariant: `_PROBE_COMMANDS ⊆ _COMMAND_BUILDERS`.** A platform is routable only if it has
  **both** a dispatch adapter and a confirm probe (else a confirmed platform would be undispatchable, or a
  dispatchable platform unconfirmable). Enforced by a test (`test_kata_install.py`, imports `kata_dispatch`).
- **L-MP1 — copilot/cursor DEFERRED.** This build ships **kiro** as the second adapter. copilot/cursor
  command/probe builders are speculative (point-in-time flags, unverifiable here) → deferred to a
  fast-follow, recorded in DESIGN §8 step 4, not shipped as phantom machinery.

## Slices (disjoint file ownership)

### Slice A — orchestrator roles wiring  *(contract-bearing, `.md`)*
- **owns:** `skills/coordinate/kata-orchestrate/SKILL.md`, `protocol/config.md`
- **read_first:** `tools/kata_roles.py`, `tools/kata_dispatch.py`, `tools/kata_settings.py`,
  `.planning/specs/multi-model-orchestration/DESIGN.md` §3/§4, `protocol/reuse-claims.md`
- **action:**
  1. Preconditions §0 — add the **`roles` load-guard** (L-A): read `confirmed_platforms()`, resolve
     `config.roles` via `kata_roles.resolve_roles` with **`host_platform` = the orchestrator's runtime
     adapter identity (`"claude"` in v1, `SKILL.md:14`; non-Claude host deferred per LD11)**, fail-closed
     STOP+escalate on `ValueError`; state BC1 (absent ⇒ all-host).
  2. Add a **"Cross-model dispatch (multi-model routing)"** subsection (L-B + L-MP5): the
     build_brief→dispatch→read-RESULT→fold procedure, the role-group→site map, LD6 concurrency, LD7
     host-fallback (+ surface), and the honest note that read-only roles are the proven v1 paths.
  3. **Flip `protocol/config.md:27`** (MAJOR-2): the `roles` row changes from "DESIGN-STAGED, proof-slice
     only; NOT yet read by the load-guard … PARKED … a hand-edited `roles` block is NOT validated at
     preflight" → "**wired**: resolved + validated **fail-closed at preflight** via
     `kata_roles.resolve_roles` (unknown role / unconfirmed platform → STOP)." Keep the BC1 sentence.
  4. Keep dispatch/frontier/gate logic otherwise unchanged; the routing check is **additive** (host path
     is the default branch).
- **acceptance (REVIEW-gated content + default-FAIL validate; MINOR-3):**
  - The load-guard names `kata_settings.confirmed_platforms()` + `kata_roles.resolve_roles` +
    `host_platform`=runtime-adapter-identity (`"claude"` v1, LD11) + fail-closed STOP-on-ValueError; the cross-model subsection names
    `build_brief`/`dispatch` + LD6 + LD7 host-fallback; `config.md:27` flipped to "wired"; BC1 stated.
    **Every reuse claim cites a `file:line`** (`protocol/reuse-claims.md`) — no phantom seam.
  - `validate_skills.py` → 36/0 (frontmatter + wikilinks intact; SKILL parses). **Note:** `validate_skills`
    does **not** verify prose presence/citations — the content acceptance above is **review-gated** (the
    integration-gate `kata-evaluate` + D98 review), not provable by the `verify` command alone.
- **verify:** `cd tools && uv run python validate_skills.py`  *(content acceptance = review-gated)*

### Slice B — multi-modal preflight + config write  *(contract-bearing, `.md`)*
- **owns:** `modules/initiation/kata-initiate/SKILL.md`, `skills/coordinate/kata-bootstrap/SKILL.md`
- **read_first:** `protocol/config.md` (`roles` row, line 27), `tools/kata_settings.py:109`, DESIGN LD3
- **action:**
  1. `kata-initiate` — add **Phase 2e "Make this run multi-modal?"** (L-C): gate on
     `confirmed_platforms()` having a non-host entry; per-role pick from `confirmedPlatforms`; add
     **load-bearing value #8 (multi-model routing)** to the Phase-2 mirror + the infer-then-confirm gate
     checklist; absent/decline ⇒ omit `roles` (BC1).
  2. `kata-bootstrap` — Phase 3 (`SKILL.md:137-139`): add `roles` to the written-fields list + a short
     body paragraph (write the confirmed assignment from the mirror; omit when single-host).
- **acceptance (REVIEW-gated content + default-FAIL validate; MINOR-3):**
  - Phase 2e exists, conditioned on confirmed off-host platforms; mirror + gate gain the multi-model value;
    bootstrap Phase 3 lists `roles` with the omit-when-single-host (BC1) note. Reuse claims cite `file:line`.
  - `validate_skills.py` → 36/0. (Content/citation acceptance is **review-gated**, as in Slice A.)
- **verify:** `cd tools && uv run python validate_skills.py`  *(content acceptance = review-gated)*

### Slice C — kiro dispatch adapter  *(code-bearing, `.py`)*
- **owns:** `tools/kata_dispatch.py`, `tools/tests/test_kata_dispatch.py`
- **read_first:** `kata_dispatch.py` (`_brief_prompt`:82, `codex_command`:102, `_COMMAND_BUILDERS`:123,
  `dispatch`:149, `_subprocess_runner`:141), DESIGN N2 (`DESIGN.md:98-102`)
- **action:**
  1. **Capture-model branch in `_brief_prompt` (MAJOR-1 — the stub-proven/real-broken seam).** Today
     `_brief_prompt` (`kata_dispatch.py:97`) hardcodes *"emit as FINAL message … do not write files"* — correct
     for codex (`-o` captures the final message) but **wrong for kiro**, which has **no `-o` capture** (DESIGN
     `:100`): the kiro worker must **write `resultPath` itself**. Add a capture model
     (`emit` vs `write`): `codex_command` calls `_brief_prompt(brief, capture="emit")` (unchanged wording);
     `kiro_command` calls `_brief_prompt(brief, capture="write")` → prompt says *"Write that JSON object to
     the file `<resultPath>`."* (`_subprocess_runner` already reads `resultPath` after the run, so both models
     converge.)
  2. Add `kiro_command(brief, worktree)` (the `kiro-cli` headless invocation per DESIGN N2) + register in
     `_COMMAND_BUILDERS`. Flags are a point-in-time snapshot (RESEARCH §0/§6) — documented; the confirm probe
     is the standing guard.
  3. Refresh the module docstring `:13` (NIT-5) — the `"fallback"`/PARKED note is updated once dispatch is
     wired (Slice A) into kata-orchestrate.
  4. TDD red→green.
- **acceptance (default-FAIL):**
  - `kiro_command` returns the documented command-line shape (asserted in a test).
  - **The kiro brief prompt CONTAINS the write-to-`resultPath` instruction and does NOT contain "do not
    write files"** (MAJOR-1 regression test); the codex brief prompt is unchanged (still "do not write files").
  - `dispatch(researcher-brief, platform="kiro", runner=stub)` returns a `completed` envelope whose
    `payload` is the normalized **researcher** shape `{claim, source, confidence, groundsToPlan}`.
  - Mutation: `prove_non_vacuous` on a new line is non-vacuous (`.kata/mutation.json` at integration).
- **verify:** `cd tools && uv run pytest tests/test_kata_dispatch.py -q`

### Slice D — install `.agents/skills` targeting + kiro probe  *(code-bearing, `.py`; depends_on C)*
- **owns:** `tools/kata_install.py`, `tools/tests/test_kata_install.py`
- **read_first:** `kata_install.py` (`_flat_link_skills`:137, `_install_besteffort`:168,
  `_PROBE_COMMANDS`:262), DESIGN N5
- **action:**
  1. Generalize `_flat_link_skills` to take a skills-root subdir; non-claude best-effort installs
     (`_install_besteffort`) target **`.agents/skills/`** (cross-tool standard); claude unchanged
     (`<host>/skills/`).
  2. Add `"kiro"` to `_PROBE_COMMANDS` (the `kiro-cli` headless probe); update the codex-only comment.
  3. Add the **probe⊆dispatch invariant test** (L-MP2): `set(kata_install._PROBE_COMMANDS) ⊆
     set(kata_dispatch._COMMAND_BUILDERS)`.
- **acceptance (default-FAIL):**
  - A best-effort install (codex/kiro) links into `.agents/skills/`; claude still links into
    `<host>/skills/` (existing tests stay green).
  - `confirm_platform("kiro", runner=stub)` confirms on a token-returning stub; the invariant test passes.
  - Mutation: `prove_non_vacuous` non-vacuous.
- **verify:** `cd tools && uv run pytest tests/test_kata_install.py -q`

## Integration gate (after the frontier drains)
1. `cd tools && uv run pytest -q` (full suite green; ≥ 542 + new tests) + `uv run python validate_skills.py` (36/0).
2. `mcp__Snyk__snyk_code_scan` on the changed Python (`kata_dispatch.py`, `kata_install.py`) — CWE-23
   CLI/stdin-path FPs are documented (`..`-guarded).
3. `gate_emit.emit_gate_artifacts(..., mutation_records=<union of C+D prove_non_vacuous>)` → `.kata/{RESULT,footprint,mutation}.json`
   (`allNonVacuous:true` for the code-bearing slices). Emit `.kata/concurrency.json` per `protocol/board.md`.
4. **Fresh-context `kata-evaluate`** (no-write, 9-rubric, default-FAIL) — point at `.kata/` + the diff.
5. **Standing D98 `kata-review`** (≥ standard tier, fresh-context, no-write, adversarial) before merge.
6. Operator merge gate → merge/push/checkpoint STATE+HANDOFF.

## Scope boundaries / deferred
- **DEFERRED (DESIGN §8.5):** the evaluator injection-points + score-threshold mechanism (its result
  *shape* is frozen; *thresholds* are not); a live ACP control channel; the orchestrator-location config
  (LD11, Quick→Kiro/Codex); true cross-host async. **copilot/cursor adapters** (L-MP1).
- **Honest scope:** kiro (like codex) is **not installed here** → proven against the stub runner; a real
  multi-model run is gated on install + confirm. Coder-routing (write sandbox) is supported by the brief
  schema but is not the proven v1 path. The `.agents/skills` location + the per-platform CLI flags are
  June-2026 snapshots — the confirm probe is the standing guard.

## BC / invariants held
- `roles` absent ⇒ `resolve_roles` returns all-host ⇒ the single-host Claude loop byte-for-byte (R5/BC1).
- Fail-closed routing (unknown role / unconfirmed platform → STOP); `_PROBE_COMMANDS ⊆ _COMMAND_BUILDERS`;
  no command injection (command builders take structured fields); CWE-23 `..`-guards on all paths.
- verify-before-reuse: every "reuses X" in the `.md` slices cites a `file:line` (`protocol/reuse-claims.md`).
