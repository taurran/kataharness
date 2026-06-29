---
title: kata-validate — PLAN (FROZEN, disjoint-file-ownership slices)
status: FROZEN
spec: kata-validate
tags: [kata/evaluate, validation, plan]
---

# PLAN — kata-validate

Ordered, disjoint-file-ownership slices. Each is TDD + mutation-proof and independently testable. No slice
touches another's files (build-in-isolation, AGENTS.md:71). `kata-orchestrate` is NEVER edited. The standing
quality bar runs at the end (Integration gate + PART A/PART B).

---

## Slice 1 — `tools/validation_report.py` engine (PURE) + tests + tripwire fixtures

**Owns:** `tools/validation_report.py`, `tools/tests/test_validation_report.py`,
`tools/tests/fixtures/validation_tripwire/**`.

**TDD (write tests first):**
1. `findings_schema()` — the `Finding` shape (`finding_id`, `severity ∈ {error,warning,info}`, `leg`,
   `location`, `message`, `behavior_changing: bool`) and the `Report{passed, findings[]}` shape.
2. `finding_id(finding)` — stable, deterministic join key (`id` → `location`-hash → `"unknown"`), matching the
   `debug_report.finding_id` precedent (`skills/evaluate/kata-debrief/SKILL.md:64-65`).
3. `severity_of(finding)` — SARIF band by the rule **"behavior_changing ⇒ error"**; maps the existing
   BLOCKER/MAJOR/MINOR + slop critical/major/minor bands → error/warning/info.
4. `render_table(report)` — markdown, **severity-first** ordering, one row per finding (severity · finding_id ·
   location · one-line message). **No HTML.** Deterministic byte-output (sorted by severity then finding_id).
   **R4 render guard (test it):** a leg that did not run (above all `score` with no plan) renders an **explicit
   N/A `info` row** ("N/A — no plan to conform to" / "N/A — leg not selected") — `render_table` NEVER silently
   omits a leg. Test: a report with a skipped `score` leg yields a visible N/A row, so it can never read as a
   clean PASS (DESIGN §4d/§6).
5. `emit_findings(report, path)` / `load_findings(path)` — JSON round-trip to `.kata/validation/findings.json`;
   `..`-guarded writer (the `tools/grounding_gate.py:36-54` `_safe_path` precedent).
6. `tripwire_corpus()` — returns the known-bad fixtures; `assert_tripwire_flagged(findings)` — raises when the
   corpus is NOT flagged (the leniency guard, DESIGN §7-i).
7. `default_passed()` invariant — `Report.passed` defaults `False`; `compute_passed(findings, tripwire_ok)`
   returns `True` only when no `error`/HOLD finding AND `tripwire_ok` (default-FAIL, DESIGN §10-2).

**Mutation-proof:** each test must go RED if its target logic is removed (e.g. flip the severity rule → table
row order changes; drop the tripwire assertion → `assert_tripwire_flagged` no longer raises). No exec/subprocess
sink anywhere in the module (`protocol/exec-safety.md`).

**Done when:** `uv run pytest tools/tests/test_validation_report.py` green; module is stdlib-only.

---

## Slice 2 — `tools/kata_banner.py` : add `render_validation_banner()`

**Owns:** `tools/kata_banner.py` (one additive function), `tools/tests/test_kata_banner.py` (additive test).

**TDD:**
1. `render_validation_banner(*, color=False) -> str` renders the deterministic
   **"Running KataHarness validation loop…"** marker using the existing `_PALETTE`/`_paint` (DESIGN §8) —
   byte-identical output, honors `color=False` (no ANSI). Add a `--validation` CLI branch in `main`.
2. Test: plain output is exact/byte-stable; colored output wraps the brand mark in the ochre code; no regression
   to `render_banner` (existing banner tests stay green).

**Mutation-proof:** removing the palette wrap or changing the marker string flips the assertion RED.

**Done when:** `uv run pytest tools/tests/test_kata_banner.py` green; existing banner behavior unchanged.

---

## Slice 3 — `skills/evaluate/kata-validate/SKILL.md` (the conductor + writer)

**Owns:** `skills/evaluate/kata-validate/SKILL.md` (new dir).

**Content (per DESIGN §1–§11):**
- Frontmatter exactly per DESIGN §1 (tag `kata/spine`; `cost-weight: 3`; writer holds Write/Edit; NOT in the
  no-write set).
- The typed contract (§2) + the isolation invariant (payload-as-data) stated prominently.
- The own-conductor justification (§3) — explicit "does NOT route through `[[kata-orchestrate]]`, does NOT
  modify its EVALUATE wiring."
- The 4 legs as **METHOD-by-reference, NOT skill/module dispatch** (§4, freeze-gate MAJOR 1): the skill applies
  the `kata-evaluate` / `kata-review` / `kata-slop-check` / `kata-research` **methods** to its own fresh-context
  critics. State explicitly that the `kata/module/*` activation guard does NOT gate this conductor (a literal
  `[[kata-slop-check]]`/`[[kata-research]]` dispatch would self-no-op and leave the tripwire unflagged). Cross-ref
  wikilinks may appear in prose for resolution (`tools/validate_skills.py:370-377`) but MUST read as
  "apply the method of …", never "dispatch …". Include the deterministic-first cascade and the conditional
  `score` leg with its explicit N/A render (§4d/§6).
- Mini-loop (§5), writer/fix-gate (§6, human-gated, drives `validation_report`), safety rails (§7), banner (§8),
  telemetry (§9), invariants (§10), trigger story (§11).
- Voice via `protocol/persona.md`; breakthrough-alert for the approval gate / broken tripwire / injection
  (`protocol/narration.md:69-92`). No internal stage names.
- A reuse map (cite-by-name, `protocol/reuse-claims.md`) labeling NEW vs REUSED.

**Mutation-proof / structural:** `validate_skills.py` checks enforce frontmatter, tags, wikilink resolution,
cost-weight, allowed-tools shape — all must pass for this skill (Slice covered by the Integration gate).

**Done when:** the skill parses; all `validate_skills` checks pass for it (verified in the Integration gate).

---

## Slice 4 — README skill-index regen (mechanical, generated)

**Owns:** `README.md` (generated SKILL-INDEX block only).

**Steps:** run `uv run python tools/validate_skills.py --write` to regenerate the mechanical columns from
frontmatter; hand-author the one "Use" cell for `kata-validate` (`tools/validate_skills.py:235-248` preserves
hand-authored Use). No other README prose changes.

**Done when:** `check_readme_sync` (`tools/validate_skills.py:286-297`) is green (index in sync).

---

## Integration gate (run after all slices)

1. **pytest:** `uv run pytest tools/tests/` — all green (new engine + banner tests + the full existing suite).
2. **validate_skills:** `uv run python tools/validate_skills.py` — **0 ERRORS**. (Skill count rises by 1 to
   **47**; see Residual Risk R1 on the locked "46/0" phrasing — the invariant is **0 errors**, not the absolute
   count.)
3. **Snyk:** `mcp__Snyk__snyk_code_scan` on the new/modified Python (`validation_report.py`, `kata_banner.py`)
   — **0 medium-or-above**; fix-and-rescan until clean (global security instruction).
4. **End-to-end WIRING step (COMMITTED gate — freeze-gate MAJOR 2; closes the D124 built-but-unwired class).**
   Unit tests on `validation_report.py` prove the pure engine, **not** that the conductor's legs are actually
   wired to it. So **invoke `kata-validate` once for real** on each of two inputs and assert the live behavior:
   - **(a) a clean fixture** (a small known-good payload) — assert: **report-only mode writes ZERO changes to
     the payload** (byte-identical before/after — the report-only-default invariant, DESIGN §5/§6); and
     `.kata/validation/findings.json` **is produced** (real artifact on disk, `validation_report.load_findings`
     round-trips it).
   - **(b) the tripwire corpus** (`tools/tests/fixtures/validation_tripwire/`) — assert the tripwire is **flagged
     by the REAL legs end-to-end** (the live conductor run produces flagging findings), **not merely** by the
     pure-function `assert_tripwire_flagged` unit. A clean tripwire here ⇒ the wiring is broken ⇒ gate FAIL +
     breakthrough-alert (DESIGN §7-i).

   This is a **committed gate step, not PART A / PART B discretion** — it must run and pass on every build of this
   spec. (n=1 live by nature; record it honestly as exercised end-to-end, not "proven", CONTEXT.md:256-260.)

## Standing quality bar (end, on the final post-build artifact)

- **PART A — `kata-evaluate`** (default-FAIL conformance): fresh-context, no-write subagent grades this spec's
  build against this frozen DESIGN/PLAN; mutation proof present for the code-bearing slices (1, 2). PASS required
  (`skills/evaluate/kata-evaluate/SKILL.md:37-77`).
- **PART B — D98 `kata-review`** (adversarial, after PART A settles): fresh-context 5-surface red-team on the
  final artifact (`skills/evaluate/kata-review/RUBRIC.md:20-41`); any conformance-escape it catches is flagged
  and recorded by the orchestrator to `.planning/validation-misses.jsonl`
  (`protocol/validation-misses.md:62-77`). SHIP required.

---

## Slice dependency order

```
Slice 1 (engine)  ─┐
Slice 2 (banner)  ─┼─▶ Slice 3 (skill) ─▶ Slice 4 (README regen) ─▶ Integration gate ─▶ PART A ─▶ PART B
                   │     (skill cites engine + banner by path/name)
(1 and 2 are independent — buildable in parallel; both are disjoint files)
```

---

## Residual risk (for the freeze-gate reviewer to scrutinize)

- **R1 — locked "46/0" count.** The integration gate was LOCKED as "validate_skills 46/0," but the tree already
  holds 46 SKILL.md files; adding `kata-validate` makes **47**. The load-bearing invariant is **0 ERRORS**, not
  the absolute number. Flagged honestly rather than silently writing "46". Reviewer: confirm 47/0 is acceptable.
- **R2 — cross-family judge fallback.** When `kata.config.roles` is unconfigured, the critics fall back to
  fresh-context same-host (same model family as the writer) — the anti-collusion guarantee is then weaker and
  must be stated as such (DESIGN §7-ii). Reviewer: confirm the honest-fallback wording is not an overclaim.
- **R3 — `kata/spine` tag on an always-available-but-not-spine skill.** The tag taxonomy has only
  spine|module; `kata/spine` is the least-wrong required tag (the `kata-onboard` precedent). Reviewer: confirm
  this divergence is acceptable and recorded (it is, in DESIGN §1).
- **R4 — `score` leg N/A on arbitrary content.** When no spec/plan is supplied, the conformance leg is skipped
  (N/A, not failed). Reviewer: confirm a profile that *requests* `score` on plan-less content surfaces an honest
  "N/A — no plan to conform to," never a false PASS.
