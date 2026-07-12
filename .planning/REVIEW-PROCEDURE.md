# FULL-PROJECT HEALTH REVIEW — PROCEDURE

> Portable procedure for a full, adversarial, claims-vs-reality health review of any project.
> First executed against KataHarness (2026-07-12, Fable 5). Copy this file into any project's
> planning dir and follow it verbatim. **The reviewer must be a fresh context that did not build
> the code under review** (no self-certification — KataHarness D33 generalized).

## Standing rules for the reviewer

- **Trust no claimed number.** Re-run every gate (tests, validators, security scans) yourself
  before using its result. A claimed "N tests green" is a claim until reproduced.
- **The review does NOT run inside the project's own automation** when that automation is itself
  under review. Review the loop from outside the loop.
- **Default-FAIL posture:** every "shipped" claim is unproven until the code, its wiring, and its
  tests are located and read.
- **Distinguish honest deferral from facade.** A named, documented deferral ("X is deferred, here
  is why, here is the tracking record") is healthy. An **unlabeled** gap — prose that implies a
  behavior with no engine, an engine with no wiring, a flag with no consumer, a claim of "built"
  over a stub — is a finding. Severity scales with how load-bearing the claim is.
- **Record findings as you go** in a findings ledger (see §8), never only at the end.

## Phase 0 — Independent baseline

1. `git status` / `git log` / tags — confirm ground truth of what is merged where; note any
   uncommitted or untracked files.
2. Re-run the project's full gate suite from a clean shell (tests, skill/schema validators,
   security scan). Record actual numbers next to the claimed numbers.
3. Any mismatch between claimed and reproduced gate numbers is an automatic HIGH finding.

## Phase 1 — Claims inventory (what SHOULD exist)

Build one table: **Claim | Source | Claimed status | Verified?**

Sources to sweep, in order:
1. README (the public promise — every feature bullet, every number, every "shipped in vX").
2. CHANGELOG (per-version shipped lists).
3. Design docs / specs (everything the design said WILL be built; each design's deferral list).
4. Decision log (each D-record's "built/locked" assertions).
5. State/handoff docs (the "CURRENT" blocks' shipped claims).
6. Git history (`git log --oneline` full sweep — every `feat:` commit is a claim).
7. Public surface (GitHub README if it can diverge from local; install docs).

Claimed-status vocabulary: `shipped` · `shipped-off-by-default` · `deferred-named` ·
`queued` · `abandoned`. Anything that can't be classified from the docs is already a finding
(status ambiguity).

## Phase 2 — Facade audit (what ACTUALLY exists)  ⟵ the core pass

For every `shipped` claim, verify **all three legs**; a claim passes only if all three hold:
1. **Engine leg:** the implementing code exists and is non-trivial (not a stub returning a
   constant, not `pass`, not raise-NotImplemented, not a facade delegating to nothing).
2. **Wiring leg:** something actually invokes it in the real flow (prose/skill references it,
   CLI exposes it, config key is read). Grep from both directions: engine→callers and
   claim→engine. The two orphan classes:
   - *prose-orphaned engine*: built code nothing invokes;
   - *engine-orphaned prose*: instructions referencing code that doesn't exist or can't do
     what the prose says.
3. **Test leg:** tests exercise the real path (not only mocks of it); spot-check that deleting
   the behavior would fail a test (mutation thinking, applied by reading).

Mechanical sweeps to run across the whole tree (findings only where unlabeled):
- `TODO|FIXME|XXX|HACK|stub|placeholder|not implemented|NotImplementedError|for now|in a real`
- functions whose body is only `pass`/`...`/`return None`/`return []`
- config keys defined in schema docs vs actually read in code (both directions)
- CLI flags/subcommands parsed but with empty or trivial handlers
- prose "call X with Y" where X lacks Y (signature mismatch between skill prose and engine)
- dead files: modules imported by nothing and referenced by no prose/doc

## Phase 3 — Code quality + loose ends

- Fail-open hunting: `except: pass/continue`, broad `except Exception` that swallows, silent
  permissive defaults on absent/unparseable input to decision-code (hard-fail is the standard).
- Error paths that return success-shaped values.
- Duplication that has drifted (two copies, one fixed).
- Dead/vestigial code and flags left from superseded designs.
- Doc-truth drift: version strings, counts, statuses in docs vs reality.

## Phase 4 — Determinism audit

Hunt nondeterminism in anything that gates, scores, orders, or hashes:
- time (`now()`, timestamps in hashed/compared content), randomness, dict/set iteration order
  reaching output, filesystem listing order, locale/encoding, env/cwd dependence, float
  formatting, subprocess output ordering, LLM judgment used where a deterministic rule could
  decide (deterministic-first is the doctrine).
- Output: a **Determinism Doctrine** doc for the project — what MUST be deterministic, what is
  allowed to be judgment, and the rule for choosing.

## Phase 5 — Behavioral contract (Prime Directives)

Verify the project ships a behavioral contract injected into every agent run, containing at
minimum: never silently stub/defer/skip designed work; express operator permission before any
bypass; absolute truthfulness about built-vs-not; misrepresenting built-ness = drift. If absent,
author it AND wire it into the actual context-injection path (not just drop the file).

## Phase 6 — Synthesis

- Findings ledger → severity-ranked report (BLOCKER / HIGH / MED / LOW), each finding with
  file:line evidence and a proposed fix.
- Fix only operator-approved classes; every fix re-gated.
- Update this procedure with anything the review taught.

## §7 Execution notes (lessons from the first run, KataHarness 2026-07-12)

- **Fan-out worked:** five parallel READ-ONLY audit agents (claims 3-leg / engine stubs /
  wiring both-directions / determinism / fail-open quality), each returning a structured
  ledger. The lead reviewer synthesizes; agents never write.
- **Fix wave:** parallel fix agents with STRICT disjoint file ownership (engine files vs
  skill prose), tests alongside, no commits — the lead runs the consolidated gauntlet and
  owns the commit series. Re-run the project's index/codegen (`validate_skills --write`
  here) after any frontmatter change, or the sync test fails.
- **The claims agents should receive the known-deferral list up front** so they audit the
  labels, not re-report honest deferrals.
- **Look for the INVERSE facade too:** built-and-tested capability missing from the public
  feature list (the KataHarness dashboard). Under-claiming distorts a health picture the
  same way over-claiming does.
- **Sweep operator-facing convention files** (STEERING/kill-switch class): claims about
  harness *behavior* in planning files are claims like any other — grep for the implementing
  code.
- **Baseline gotcha:** run gates from the directory that owns the manifest (tools/ here),
  or the baseline itself lies.
- **Findings not fixed in-session go into the project's named-deferral system** (BACKLOG
  here) before the review closes — an unrecorded finding is itself the facade pattern.

## §8 Findings ledger format

`| ID | Sev | Class | Claim/File | Evidence | Proposed fix |`
Classes: `facade` · `built-unwired` · `prose-orphan` · `doc-drift` · `fail-open` ·
`nondeterminism` · `loose-end` · `quality`.
