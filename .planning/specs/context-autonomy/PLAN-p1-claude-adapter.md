---
spec: context-autonomy
phase: CA-P1
title: Claude adapter legs — bridge writer + chain wrapper, SessionStart(compact) re-anchor, PreCompact extension, settings snippet, gauge/trigger wiring, handoff kind + staleness rule, AGENTS.md standing line
status: frozen-candidate (pending plan gate)
created: 2026-07-04
branch: feat/context-autonomy
baseline: CA-P0 integrated (pytest grown-green, validator 48/0/0, Snyk medium+ 0)
tags: [kata/spine, context-autonomy, plan, CA-P1, adapter-claude, gauge, handoff]
---

# CA-P1 — the Claude adapter legs (the ONLY live platform in v0.2.1, CA-L38)

Wires the P0 engine to the live loop: the gauge gets a writer, the reset gets a re-anchor hook, the
trigger prose gets its long-missing wire (§0/SR-1: "this initiative wires a gauge to an existing
policy; no new threshold concept is invented"), and the handoff artifact gains its provenance +
staleness rules. Depends on CA-P0 (E1 `kata_gauge`, E7 config rows) being integrated on the branch.

Build mode: direct with dispatched workers, disjoint files, conductor integrates (D137-L8). **Dogfood
mandate:** run config `inlineEval: "telemetry"`; every worker brief carries the M4 checkpoint mandate.
Workers tier down per D131 (coding class); gates at anchor.

## Ownership (disjoint) + DAG

```yaml
ownership:
  A1: [tools/kata_statusline.py, tools/tests/test_kata_statusline.py]
  A3: [adapters/claude/hooks/kata-sessionstart.py, adapters/claude/hooks/kata-precompact.py, tools/tests/test_claude_hooks.py]
  A6: [skills/handoff/kata-handoff/SKILL.md, protocol/handoff.md]
  A7: [tools/kata_router.py, tools/tests/test_kata_router.py]
  A2: [adapters/claude/statusline.py, adapters/claude/statusline_chain.py, adapters/claude/settings.snippet.json, adapters/claude/README.md]
  A4: [skills/coordinate/kata-orchestrate/SKILL.md]
  A5: [skills/handoff/kata-selfhandoff/SKILL.md, skills/handoff/kata-orient/SKILL.md]
waves:
  wave1: [A1, A3, A6, A7]
  wave2: [A2, A4, A5]
depends_on:
  A2: [A1]
  A4: [A1, A6]
  A5: [A1, A6]
tasks:
  A1: { estimate: 35, class: code }
  A2: { estimate: 35, class: code }
  A3: { estimate: 35, class: code }
  A4: { estimate: 30, class: code }
  A5: { estimate: 25, class: code }
  A6: { estimate: 25, class: code }
  A7: { estimate: 15, class: code }
```

A8 (conductor closeout, after integration): full gauntlet; integration smoke of the statusline chain
(pipe a Claude-shaped stdin JSON through `adapters/claude/statusline.py` and through
`statusline_chain.py` with a stub child script; assert the bridge file lands atomic + schema-valid and
the child's stdout passes through byte-identical); commit. CHANGELOG/D-records stay in P2.

## A1 — the bridge superset writer in kata's OWN statusline (fresh-profile owner, CA-L1 fold #3)

read_first: DESIGN CA-L1/CA-L2 + §2 "Bridge file"; GROUNDING-CLAUDE.md G3 (stdin carries
`context_window.remaining_percentage` + `context_window.total_tokens`; the gsd bridge schema);
kata_statusline.py:153-200 (`statusline_from_event` — the entry point to extend).

1. **`write_bridge(temp_dir, payload_dict) -> Path | None`** — writes
   `%TEMP%/kata-ctx-<session_id>.json` with the CA-L2 superset schema verbatim: "`{session_id,
   remaining_percentage, used_pct, timestamp, total_tokens}`", `timestamp` = Unix seconds now,
   **atomic temp+rename** (CA-L1). Missing `context_window` in the stdin payload or missing
   `session_id` ⇒ returns None, writes nothing (a statusline event without gauge data is a legitimate
   host state — the READ side's absent-leg handles it; never a crash). Write errors are fail-soft
   (statusline contract: never crash the host statusline — kata_statusline.py's existing posture) —
   the observability-write exception to fail-closed, matching `write_task_telemetry`'s documented
   fail-soft class.
2. **`statusline_from_event` extension** — parse `session_id` + `context_window` from the SAME stdin
   JSON it already reads; call `write_bridge` BEFORE the render path (so a non-kata cwd still writes
   the gauge — the conductor session's cwd is the target repo, which has `.kata/`, but the bridge must
   not depend on it); rendering behavior byte-unchanged (existing tests green).
3. CA-L2 additive-BC note pinned in the docstring: the superset is "additive/BC with the gsd 4-field
   schema"; `total_tokens` is free because "the wrapper receives the same statusline stdin (GROUNDING
   G3 … confirmed)".

**Tests:** schema round-trip (all five fields, numeric types); atomicity (no partial file visible —
temp name ≠ final name, rename asserted via monkeypatched os.replace); absent `context_window` ⇒ no
file; absent `session_id` ⇒ no file; render output byte-identical to pre-change fixtures; a write
OSError does not break the rendered line. **Mutation proofs ≥2:** the atomic-rename step (mutate to
direct write → RED), the absent-field no-write guard.

## A2 — glue + the chaining wrapper + settings snippet + merge-discipline docs

read_first: DESIGN CA-L1 (chain-never-clobber, verbatim below), CA-L24 fold #5 (append-never-replace),
CA-A4; adapters/claude/statusline.py (the thin glue), adapters/claude/settings.snippet.json,
adapters/claude/README.md; GROUNDING G2/G3.

1. **`adapters/claude/statusline_chain.py` (NEW)** — CA-L1 verbatim: "kata offers a **chaining
   wrapper** (exec the user's script as child, pass stdin through unmodified, never touch the user's
   output or bridge file) … The chained wrapper writes its OWN sibling bridge
   `%TEMP%/kata-ctx-<session_id>.json` (atomic temp+rename); the user's file is untouched."
   Mechanics: read all stdin once; `subprocess.run(list-argv-of-the-user-command, input=stdin)` —
   NO `shell=True` (exec-safety registry row added is P2/C4's observability doc? No — registry rows
   live in `protocol/exec-safety.md`; A2 adds its row there is NOT owned here — instead the wrapper's
   child argv comes from its own argv tail (`statusline_chain.py -- <user-cmd> [args…]`), documented;
   the exec-safety registry row is added by A2 to adapters/claude/README.md §security and the
   protocol registry entry is deferred to P2/C10 closeout with a NOTE — single-owner discipline);
   print the child's stdout byte-identical; then call `kata_statusline.write_bridge` (A1's function)
   with the parsed stdin. Child failure/timeout ⇒ still emit child output if any, never hang (bounded
   timeout), exit 0 (fail-soft, the host-statusline contract).
2. **`adapters/claude/statusline.py`** — no behavior change needed beyond what A1's core provides
   (the glue already pipes stdin to `statusline_from_event`); confirm + comment only.
3. **`settings.snippet.json`** — add the SessionStart(compact) hook entry (A3's script) alongside the
   existing PreCompact entry; keep `statusLine` as the unchained kata command (the fresh-profile
   case). Document IN THE SNIPPET-adjacent README the CA-L24 merge discipline verbatim: "**hooks
   arrays are APPEND-NEVER-REPLACE; `statusLine` is only ever chained-or-skipped** — the CA-L1
   never-clobber guarantee generalizes to EVERY settings key kata touches", plus the CA-L1 offer
   logic: user statusline exists ⇒ offer chain (wrapper wrapping their command) or skip to fallback
   legs; "The operator's own statusline stays untouched (R-4: no operator action)". Reader priority
   (kata bridge → user bridge → deterministic fallback) cross-referenced to `kata_gauge`.
4. **README** — install/approval flow: the snippet is applied only via the CA-L24 bundle's
   host-settings write slot ("never an implied side effect"); `bridgeMode` recorded to
   `.kata-settings.json` `hostPosture` (E2) by the bootstrap prose (P2/C1) — README states the
   contract, writes nothing itself.

**Verify:** integration smoke (A8 harness): stub user script echoing a marker ⇒ chain output ==
marker byte-identical AND kata bridge file written AND stub's own bridge file (if it writes one)
untouched (CA-A4's mechanical core); snippet parses as JSON; README renders. **Acceptance:** CA-A4
leg — "user's statusLine + bridge file byte-unchanged; kata offers chain-or-skip".

## A3 — SessionStart(compact) re-anchor hook + PreCompact additive extension

read_first: DESIGN CA-L17/CA-L18; GROUNDING G2 (SessionStart matcher `compact` +
`hookSpecificOutput.additionalContext` CONFIRMED; PreCompact block = dangerous, observe-only);
adapters/claude/hooks/kata-precompact.py (the fail-soft pattern to copy — never raises, always exit
0); protocol/handoff.md:7 (`.planning/HANDOFF.md` — the canonical path).

1. **`kata-sessionstart.py` (NEW)** — on SessionStart with `source == "compact"` (also honor
   `resume` — a respawned session re-anchors identically; matcher set in the snippet is A2's), emit
   `{"hookSpecificOutput": {"additionalContext": …}}` — CA-L18: "the re-anchor instruction pointing
   at the newest **`.planning/HANDOFF.md`** (protocol/handoff.md:7 — NOT the brief's
   'SELFHANDOFF.md')". The instruction text: re-anchor via `.planning/HANDOFF.md` + apply the CA-L19
   staleness rule (A6's prose) + rebuild via kata-orient 3-tier; "Orientation tiers consume it 1:1."
   Absent HANDOFF.md ⇒ the context says so and points at kata-orient full rebuild (degradation §4
   row 8). Fail-soft: any exception ⇒ silent exit 0 (the kata-precompact.py pattern verbatim).
2. **`kata-precompact.py` extension** — CA-L17 verbatim: "extended ADDITIVELY to also surface
   HANDOFF.md existence/freshness. The hook **never blocks** compaction (G2: blocking near the limit
   is dangerous — no headroom left); observe-only + checkpoint guarantee." Mechanically: append
   HANDOFF.md existence + mtime/git-recency line into the existing `custom_instructions` nudge; the
   board-snapshot leg byte-unchanged; never emits `{"decision":"block"}`, never exit 2 (test-pinned).
   The README's sync-time-budget UNVERIFIED assumption stays flagged (live-proof item CA-A1 — do not
   delete the flag).
3. **`tools/tests/test_claude_hooks.py` (NEW)** — hooks are currently smoke-only; these are
   subprocess tests: pipe fixture stdin JSON, assert stdout JSON shape, assert exit 0 on garbage
   stdin (fail-soft), assert NO block-shaped output from precompact under any fixture.

**Mutation proofs ≥2:** the `source == "compact"` matcher guard; the never-block assertion (mutate to
emit decision:block → RED).

## A6 — handoff `kind:` frontmatter + the staleness rule (kata-handoff + protocol/handoff.md)

read_first: DESIGN CA-L19/CA-L21 (quote both verbatim into the prose); protocol/handoff.md (T1 rule
at the Boundary-handoff section; frontmatter list); protocol/board.md:9 (the line grammar the
comparator reads); skills/handoff/kata-handoff/SKILL.md (version 0.1.0).

1. **protocol/handoff.md:** frontmatter gains additive `kind: manual|self|boundary` (CA-L21(2));
   pre-existing handoffs without `kind:` "read as unknown kind; never gates" (§4 row 11). Taxonomy
   terminology paragraph (CA-L21(1) verbatim): "a handoff = the session-boundary durable artifact
   (`.planning/HANDOFF.md` family) ONLY; dispatch briefs, worker final reports, and escalation
   payloads are agent-exchange artifacts, never 'handoffs'." Refresh rule (CA-L21(4)): "an
   over-threshold refresh overwrites HANDOFF.md + commits (history lives in git); **T1 extended** —
   any coincident boundary handoff supersedes a same-boundary self-refresh". "(6) **NO new artifact
   formats**" — everything lands as additions to this file; no second schema.
2. **The staleness rule** (CA-L19, quoted verbatim including the clock-skew note): "STRICT: any board
   `DONE`/`DECISION` line **newer** than the HANDOFF.md git commit demotes the handoff from
   sole-anchor to context-input; the kata-orient 3-tier rebuild becomes authoritative. Comparator =
   newest board DONE/DECISION ISO-8601-UTC line timestamp (protocol/board.md:9 line grammar,
   verified) vs HANDOFF.md's git commit timestamp, strict `>`; same-second ties favor the handoff.
   N=1 semantics; **no tunable**. Trail-ref independent; no reliance on `@sha` presence." Plus the
   fold-#10 clock-skew paragraph (process clock vs committer clock; single-host acceptable;
   multi-machine revisit rides the board's own documented revisit item).
3. **kata-handoff SKILL.md** (0.1.0 → 0.2.0, MINOR — behavior-bearing frontmatter field): authoring
   rule for `kind:` (kata-handoff writes `manual`; the selfhandoff cycle writes `self`; the sprint
   boundary writes `boundary`); the refresh-overwrite + T1-extended rule at the write site; the
   staleness rule cross-referenced (the read side lives in protocol + kata-orient/A5).

**Verify:** validator green with the bump; `git diff protocol/handoff.md` additive-only (existing
required-sections list untouched); grep pins: `kind: manual|self|boundary` present, "strict" +
"ties favor the handoff" present verbatim.

## A7 — AGENTS.md standing line (router stanza, `kata_router.py`)

read_first: DESIGN CA-L20; tools/kata_router.py (`write_stanza` — upsert into the TARGET repo's
AGENTS.md, per kata-onboard SKILL.md:136-146); test_kata_router.py.

1. The stanza template gains ONE standing line (CA-L20 verbatim): "a resumed/compacted session
   re-anchors via `.planning/HANDOFF.md` + the staleness rule before doing anything else. (Universal
   fallback for platforms with no hook — §5.)"
2. Upsert semantics unchanged (marked-block replace — existing machinery); a target that already has
   the pre-v0.2.1 stanza gets the line at next `write_stanza` (the existing upsert path — no new
   mechanism).

**Tests:** stanza contains the line; upsert over an old stanza adds it exactly once; idempotent
double-write. **Mutation proof ≥1:** the line-present assertion (delete from template → RED).

## A4 — kata-orchestrate: gauge read + trigger + refresh-per-boundary + PRE-FLIGHT enforcement-only

read_first: DESIGN CA-L5/L7/L12/L14, CA-L24 sequencing, §4 rows 6-9; kata-orchestrate SKILL.md
(0.8.0): "Preconditions" (line 32), "The loop" (line 266), the frontier/wave recompute step, the
existing PRE-FLIGHT gating in preconditions; kata_gauge (P0/E1) function names — cite them exactly.

1. **Boundary evaluation** (CA-L12 verbatim): "The conductor evaluates the trigger at
   **wave/frontier-recompute boundaries only**; **never mid-task** (existing kata-selfhandoff
   mandate, unchanged)." At each boundary: resolve the gauge via `kata_gauge.resolve_gauge`
   (reader priority CA-L1), staleness per CA-L3; `trigger_crossed(gauge, contextTrigger-or-0.70)`
   with the CA-L5 denominator ("the gauge's `context_window.total_tokens` (post-cap): a capped
   session's real frame IS the cap"); no usable gauge ⇒ `fallback_waves` deterministic rotation
   (CA-L4/L6: "Degradation is always graceful rotation — never 'assume infinite context'").
2. **Post-trigger behavior** (CA-L12): "Post-trigger: **keep working**, refreshing the handoff at
   every subsequent boundary until the host reset arrives (option (a))." The refresh invokes
   kata-handoff with `kind: self` (A6); the T1-extended coincident-boundary supersede honored.
   Under-threshold ⇒ zero churn (CA-L13 / CA-A5 — state it as the graded NO-FIRE property).
3. **Reset ownership** (CA-L14): "Host compaction is the SOLE reset mechanism on Claude … Kata owns
   the **SCHEDULE + DURABILITY** …; the host owns the **MECHANISM**. … There is **no conductor
   self-compaction leg**." — stated where the loop describes the compact step.
4. **PRE-FLIGHT stays enforcement-only** (CA-L24 sequencing verbatim): "kata-orchestrate's existing
   PRE-FLIGHT gate stays **enforcement-only**: it verifies/provisions the approved set and NEVER
   prompts a second time." One sentence at the preconditions' preflight step; the bundle COLLECTION
   is bootstrap's (P2/C1).
5. **Scope guard:** the M4 scheduler, ladder, kill bindings, dispatch-time model selection, and final
   gate sections are byte-untouched in THIS task (P2/C3 owns the brief-template + premium-failure
   edits — sequenced in a later plan, no same-plan contention). Version 0.8.0 → 0.9.0 (MINOR,
   behavior-bearing).

**Verify:** validator green with 0.9.0; grep pins: "wave/frontier-recompute boundaries only",
"keep working", `kata_gauge.resolve_gauge`, "enforcement-only"; `git diff` shows zero hunks inside
the M4 scheduler/ladder/model-selection sections.

## A5 — kata-selfhandoff wiring + kata-orient resume side

read_first: DESIGN §0 (SR-1), CA-L6/L7/L8/L13/L14, CA-L32/L33 (rotation policy per shape);
kata-selfhandoff SKILL.md:29-45 (the existing trigger prose — this is the policy being WIRED, not
replaced); kata-orient SKILL.md + protocol/orientation.md (3-tier).

1. **kata-selfhandoff** (0.1.0 → 0.2.0): the "When to fire" section gains the WIRE — the trigger
   fraction source is now concrete (CA-L7 verbatim): "Trigger = **0.70 `[TUNABLE]` × host-reported
   effective window** (CA-L5). One key (`contextTrigger`, §2), shown in bootstrap's advanced drawer,
   **never interactively asked**", read via the gauge (`kata_gauge`), evaluated at boundaries by the
   conductor (A4). The smart-zone framing (CA-L7): operate "above the context floor (kata-orient
   3-tier load complete), below the rot ceiling"; the 1M-frame config-edit note. D83 pointer per
   CA-L8 (the 0.40 sprint fraction untouched — "Same primitive lineage, two policies").
   Generous-not-timid RESTATED, not weakened (CA-L13: "Early exit is a risk equal to rot" + the
   NO-FIRE acceptance). Rotation-mandatory degradation (CA-L6) + shape policy (CA-L32/L33): one-shot
   ⇒ unconditional (the key "is not consulted"; includes pre-v0.2.1 configs — the D147 departure,
   named); incremental ⇒ `contextAutonomy` governs intra-sprint refresh only. Reset ownership
   sentence (CA-L14) mirrored from A4.
2. **kata-orient** (0.2.0 → 0.2.1, PATCH — read-side note): a compacted/respawned session's tier
   input is the SessionStart-injected HANDOFF.md pointer, subject to the CA-L19 staleness rule —
   demoted handoff = context-input, 3-tier rebuild authoritative; resume quality bar (CA-L12):
   "Resume must reload FULL context quality — kata-orient 3-tier, budget-capped per
   protocol/orientation.md — seamless, no hangs, no degradation (graded at CA-A1, not just task
   continuity)."

**Verify:** validator green with both bumps; grep pins: "0.70", "contextTrigger", "generous, not
timid" retained (the D8 lineage line must survive), "unconditional" at the one-shot clause, staleness
cross-ref in kata-orient.

## Phase verification (default-FAIL)

- Full suite green (grown; includes test_claude_hooks.py, bridge-writer tests, router-line tests);
  validator 48/0/0 with bumps (kata-handoff 0.2.0, kata-orchestrate 0.9.0, kata-selfhandoff 0.2.0,
  kata-orient 0.2.1); Snyk medium+ 0 on changed/new Python (CA-A10).
- A8 chain smoke: child passthrough byte-identical + kata bridge written + user artifacts untouched
  (CA-A4 mechanical leg).
- Prose drift-magnet checks: D83 0.40 lines byte-unchanged; M4 scheduler/ladder sections
  byte-unchanged; kata-precompact board-snapshot leg byte-unchanged.
- Mutation-proof roster (≥5 across A1/A3/A7) listed for the D-record.

## Threat register

| Surface | Threat | Mitigation (task) |
|---|---|---|
| Chain wrapper executes the user's statusline command | Elevation/Tampering — arbitrary command runs per statusline tick | A2: the command is the USER'S OWN pre-existing statusline (no new privilege); list-argv, no `shell=True`; bounded timeout; installed only via the approved bundle write slot. |
| SessionStart additionalContext injection | Spoofing — a poisoned HANDOFF.md steers a fresh session | A3/A6: HANDOFF.md is a git-committed repo artifact (same trust domain as the plan); staleness rule demotes it under newer board evidence; redaction section required (protocol/handoff.md §7). |
| PreCompact hook | DoS — blocking compaction at the limit | A3: never-block test-pinned (no exit 2, no decision:block). |
| Bridge write in %TEMP% | Info disclosure — token counts in a world-temp file | A1: contents are context-usage numbers only (no code, no secrets); documented in README. |

## Out of scope

Bootstrap/preflight/readiness prose, report budgets + continuation contract, premium gate prose,
observability/platform docs, glossary, riders, D-records, CHANGELOG (P2); live proofs (P2/C11);
non-Claude legs (docs-only, §8).
