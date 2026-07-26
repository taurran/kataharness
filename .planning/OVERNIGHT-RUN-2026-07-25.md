---
date: 2026-07-25
kind: delegated-overnight-run
branch: docs/mergeback-ingest-itemization
baseline: master `fcb0338` (v0.4.0) · branch tip `8dd648b`
status: PLAN — authorized, not yet executed
---

# OVERNIGHT RUN — plan + delegation record

## 0. The delegation grant (recorded IN-REPO, not only in transcript)

**Operator, 2026-07-25, before sleeping, verbatim in intent:**

> *"Go with your recommendations for selection. We can stick with offsets. But it should be future
> proofed for model upgrades such as today's move from 4.8 to 5. … I want you to be very thorough in
> this. Run determinism doctrine throughout, make sure everything is properly deterministic. Make sure
> all features are honestly finished and working. Run smoke tests. Go deep. I want this overnight run
> to really be thorough. Make sure to use the full power of the harness to implement it all with
> precision subagents."*

**This record exists because the 2026-07-21/22 overnight run's adval (F6) flagged that its
authorization quote lived in the session transcript rather than the repo.** Recording it here closes
that class. Any adval on this run can cite this file.

**Scope decisions carried by the grant:**
- *"stick with offsets"* ⇒ **layer 1 (an internal vendor-independent rung vocabulary) is OUT of scope.**
  Ladder arithmetic stays positional/offset-based on the existing rung names.
- *"future proofed for model upgrades such as today's move from 4.8 to 5"* ⇒ **semantic version
  recognition IS in scope** — a new generation of a known tier must resolve with no table edit.
- *"all features honestly finished and working"* ⇒ **`validate_anchor` gets WIRED** (PD-1:
  present-but-unwired is NOT built). This closes DEF-2 rather than opening it.

## 1. What triggered this: the T-11 adval found 2 MAJORs, both mine

Fresh-context read-only review of `8dd648b` returned **SHIP-WITH-FIXES**. Both MAJORs
operator-verified before acceptance (not taken on the reviewer's word):

| id | finding | verified |
|---|---|---|
| **M1** | `_normalize_anchor` is applied to `premium["offer"]` (`kata_models.py:777`), so the semantic fallback **widened the premium SPEND gate**. A config with `offer: "claude-opus-5"` + anchor `sonnet` previously NO-FIRED cost-free (`unknown-offer`); it now **fires and spends** — against the intent stated at `:1107` (*"EXPLICIT offer id — never inherit, never a ladder walk"*) | ✅ reproduced |
| **M2** | `fallback_chain` (`:1186-1193`) does its own reverse `ID_MAP` scan and is the **only** entry point that never calls `_normalize_anchor`. The emit-side bump therefore broke it: `fallback_chain("claude-opus-4-8")` → `[None]` (immediate degrade) instead of stepping down through sonnet→haiku | ✅ reproduced |

**Both directly refute claims in my own commit message** — "BC preserved byte-for-byte" and "makes
future emit-side bumps safe" are **false as written**. PD-2: recorded here, corrected in the fold.

Plus 5 MEDIUM and 3 LOW; full findings in the review returned this session.

## 2. Wave plan (precision subagents, disjoint file ownership)

### Wave A — T-11 completion · SEQUENTIAL (single owner: `tools/kata_models.py`)
File-ownership rule forbids parallel workers on one file, so A1–A5 are one worker in order.

| id | task | acceptance |
|---|---|---|
| A1 | **Fold M1** — revert normalization on `premium.offer` ONLY; keep it for the anchor. Operator-approved conservative arm: non-spend-increasing, preserves the `:1107` explicit-offer intent | test pins BOTH directions (exact id fires; semantically-recognized id does NOT) |
| A2 | **Fold M2** — `_normalize_anchor` at the top of `fallback_chain`; locate `start_idx` by short-name; fix the stale docstring example | `fallback_chain("claude-opus-4-8")` steps down again; test pins pre- and post-bump ids |
| A3 | **Fold D1** — the tier token is not always hyphen-field 2. `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, `claude-instant-1.2`, `claude-code`, `claude-agent-sdk` all currently mis-tokenize and would **false-RAISE**. Scan all hyphen fields for a rung match before declaring unknown. **PREREQUISITE for A5** | each listed id resolves or is silently ignored — never a false raise |
| A4 | **Fold D3/D4/D5** — D3: docstring claims a caller that does not exist. D4: scope the `claude-` regex to the **Anthropic** ladder, not the all-family union (else a populated gemini ladder routes `claude-pro-1` onto gemini). D5: test gaps — `premium.offer`, `fallback_chain` post-bump, `claude-3-*` shapes, case variants, error-message rung ORDER (deleting `sorted()` currently leaves all tests green), and the overclaiming test name `test_a_future_generation_resolves_with_no_id_map_edit` (proves recognition only; emit still needs the table edit) | law-3 order pinned by test; no test passes against a wrong implementation |
| A5 | **WIRE `validate_anchor`** into the `kata.config` load-guard (the `validate_advisor_block` house pattern, GB12). Closes DEF-2. **Gated on A3** | a vendor-shaped unknown-tier anchor fails LOUD at load; `session`/foreign/arbitrary anchors unaffected |
| A6 | **Fold D2** — retitle the `MERGEBACK-INGEST.md` T-11 heading (currently `✅ BUILT` with the NOT-WIRED qualifier 108 lines below); correct the two false BC claims in the record | heading matches reality |

### Wave B — Track 1 verification sweep · PARALLEL (read-only, independent)
The 13 remaining D2 probes from `MERGEBACK-INGEST.md` Part D. Read-only ⇒ no ownership conflict ⇒
genuine parallel fan-out. Each returns FIRED / WIRED-UNFIRED / BUILT-ONLY / BROKEN **with cited
evidence**, and every finding lands as a task or backlog item.

### Wave C — gates (after A and B)
| id | gate |
|---|---|
| C1 | `tools/scripts/gauntlet.py` — the authoritative gate, never `pytest \| tail` |
| C2 | **Determinism sweep** — run MC-01's ten-laws checker (from the merge-back, **used as an instrument, NOT merged**) over every changed file. Report-only. This is the operator's "run determinism doctrine throughout" |
| C3 | **Smoke tests** — `test_advisor_smoke.py` 6-seam + benchmark integration via `uv run` (NOT direct-venv: that hits the documented offline failure mode and produces a false red) |
| C4 | **Second fresh-context adval** on the folded result — no-write, must not be the same context that authored the fold |
| C5 | Snyk `snyk_code_scan` over `tools/` if configured; else a one-line deferred-security note |

## 3. Standing constraints for this run

- **PD-1 / PD-2 bind the conductor and every worker.** No silent defer/stub/skip; honesty labels
  travel with every claim.
- **Determinism doctrine is load-bearing on all new engine code** — the ten laws, checked at C2.
- **Conductor is the SOLE main-tree git writer.** Workers get worktrees or no-git.
- **Closeout tripwire:** stash empty + status reviewed.
- **NOTHING MERGES TO MASTER.** All work lands on `docs/mergeback-ingest-itemization`; the PR stays
  open for morning review.
- **T-01…T-08 are OUT of scope** — every one carries a grill tier, and grills are interactive
  (AskUserQuestion, one question at a time, D153/U1). An unattended run cannot answer them.
- **Park-and-tell on any judgment call** — plain operator message, no retry loop, no silent decision
  (the quota-resilience G-4 pattern).
- **ELEVATE:** any candidate is recorded and **defaults DECLINED** in absentia (D161 precedent).
  Two from the prior run are already owed; this run adds no unreviewed acceptances.

## 4. Explicitly NOT doing

Merging to master · T-01…T-08 · any grill · any policy/cost decision · layer-1 rung-vocabulary
decoupling (operator scoped it out: *"we can stick with offsets"*) · accepting any ELEVATE.
