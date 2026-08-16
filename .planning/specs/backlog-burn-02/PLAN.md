---
spec: backlog-burn-02
status: draft
opened: 2026-08-16
kind: small burn — burn-mode prototype round 2 (evidence-tracked per the burn-mode vision)
scope: BL-X01 · BL-X02 · BL-X03 · BL-X07 (wave 1) · BL-X05 (wave 2) — operator-ruled D171
branch: burn/backlog-burn-02 (stacked on burn/backlog-burn-01 @ eed995c; PR #54 open on the parent)
waveBoundaries: autonomous
baseSHA: PINNED AT DISPATCH — recorded below at freeze; every worktree provisioned manually at it (BBM-9)
evidence-out: OBSERVATIONS.md beside this file (mode evidence round 2)
---

# PLAN — backlog-burn-02 (the five ≤1-file fixes, two waves)

**Triage happened before this plan was written (BBM-7).** All five filings were re-verified live on
2026-08-16 by the conductor: X01 (grep re-proved only `quality` has provider tags), X02 (read
`kata_install.py:1303-1313`), X03 (read `SKILL.md:47`, `--root ..` still present), X07 (read the
kata-promote frontmatter + body), X05 (survey grep — most literals are fixtures/test-local; the
living-file pin class is the target and may be near-empty).

## Standing rules — every builder, every item (the shared half; convergence-gate attack target)

1. **Step 0 — verify your ground (BBM-9/H6×2):** `git rev-parse HEAD` in your worktree MUST equal
   the pinned base SHA in your brief, and `git status --porcelain` MUST be empty. Report both
   values in your report. If either mismatches: STOP and escalate — do not "fix" it.
2. **Push back (BBM-10/H7):** if your brief is wrong, internally unsatisfiable, or the filed claim
   does not reproduce, SAY SO AND STOP at the exact collision point. A precise escalation with
   file:line beats a guessed fix.
3. **Verify a primitive before reusing it (H3):** never assert a function/flag/behavior exists
   without reading it in this tree.
4. **Ownership is exact:** touch ONLY the files in your owner set. Anything else you believe needs
   an edit → flag it in your report, do not edit it. Exception (H5 rule): **regenerated** shared
   artifacts — the README skill-index mechanical columns are regenerable; if your version bump
   requires it for a green gauntlet, regenerate freely (`uv run python validate_skills.py --fix`
   style path per the repo's regeneration route — verify the actual command by reading
   `tools/validate_skills.py --help` first, rule 3). The conductor re-derives once at integration,
   so index merge conflicts are resolved by regeneration, never by hand.
5. **Gauntlet green in your worktree before you report** (`cd tools && uv run python
   scripts/gauntlet.py` — MUST use `uv run`; the bare venv python false-reds 2 integration tests
   offline). 4/4 or an escalation explaining exactly which gate reds and why it is not yours.
6. **Mechanical self-gates (BBM-1):** ship at least one assertion/check that proves YOUR fix
   specifically (named per item below). The conductor re-runs it; a judge reproduces it fresh.
7. **Commit style:** conventional commits, specific files staged (never `-A`), trailer
   `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
8. **Report contract:** base-SHA check result · what changed (files + why) · self-gate command +
   output · gauntlet numbers · anything flagged-not-fixed · truthful status per PD-2
   (built / built-with-caveat / escalated / not done).

## Wave 1 — four concurrent builders, disjoint owner sets

### Item 1 · BL-X01 — protocol/config.md's own example fails the new load-guard
- **Owner set:** `protocol/config.md` ONLY.
- **The defect:** the `modules` row's example (`config.md:14`) names `["quality","design","bakeoff",
  "improve"]`; `tools/kata_config.py:validate_core_config` requires each module to have a provider
  skill carrying tag `kata/module/<name>`, and only `quality` has any (verified twice).
- **The fix:** make the example pass its own validator. First DISCOVER the honest set: grep
  `skills/` for all `kata/module/*` tags; use real provider-backed module names in the example
  (keep `quality`; add others only if providers exist). Keep the example illustrative — if only
  `quality` qualifies, the example becomes `["quality"]` and that is fine.
- **Clause-pin constraint:** `protocol/config.md` is CLAUSE-PINNED (fingerprint-EXEMPT). Before
  editing, read the pinned clauses for config.md in `tools/validate_skills.py`
  (`check_protocol_integrity` / the pinned-clause table) and confirm your edit does not touch a
  pinned sentence. If the example line IS inside a pinned clause: STOP and escalate (rule 2).
- **Self-gate:** a one-shot probe — load the edited example's module list through
  `validate_core_config` with the real skills tree and show it passes (a `uv run python -c` probe
  with the command + output in your report is sufficient; a durable test is welcome but NOT
  required for a doc example).
- **Acceptance:** example validates · pinned clauses untouched (validator green proves it) ·
  gauntlet 4/4.

### Item 2 · BL-X02 — the installer's "next steps" banner names commands that do not exist
- **Owner set:** `tools/kata_install.py` + any test file that pins the banner's step2 text
  (discover by grepping `tools/tests` for `kata-initiate`/`kata-bootstrap`/step2 fragments; if a
  pinning test exists it is YOURS for exactly those assertions).
- **The defect:** the claude branch (`kata_install.py:1306-1313`) tells first-run users to run
  `/kata-initiate` and `/kata-bootstrap`; neither exists. The real command set:
  `/kata` · `/kata-loop` · `/kata-start` · `/kata-onboard` · `/kata-resume` · `/kata-status` ·
  `/kata-validate` (verify against `adapters/claude/commands/` before writing, rule 3).
- **The fix:** step2 names only real commands with the settled comprehension-gated copy (UX-4):
  `/kata-start` = "single run: plan and build once, then stop" · `/kata-loop` = "full cycle:
  build → closeout → improve again" · `/kata-onboard` = guided tour on an existing repo. The
  codex/kiro and generic branches reference SKILLS (kata-initiate exists as a skill) — verify and
  leave correct references alone.
- **Self-gate:** a test (new or amended) asserting the claude step2 block's command tokens are a
  subset of the real command files in `adapters/claude/commands/` — a structural guard, not a
  string pin, so it cannot rot the way the banner did.
- **Acceptance:** no phantom commands anywhere in `_next_steps` output · self-gate test green ·
  gauntlet 4/4.

### Item 3 · BL-X03 — kata-understand documents a graph-rebuild command the tool refuses
- **Owner set:** `modules/closeout/kata-understand/SKILL.md` ONLY.
- **The defect:** Step 1 (`SKILL.md:46-48`) says `uv run python graph_gen.py --root .. --out
  ../kata.graph.json`; `graph_gen._safe_path` raises on ANY path containing `..` (verified live
  2026-08-15 by BURN-F). Every literal follower crashes.
- **The fix:** read `graph_gen._safe_path` first (rule 3) and document an invocation it actually
  accepts — the absolute-path form BURN-F used is the known-good shape; a portable phrasing
  (e.g. compute the absolute repo root into the flags) is preferred over a hardcoded path.
- **PROOF obligation:** RUN the documented command once against this repo from a fresh shell,
  exactly as written, and include the invocation + resulting node/file counts in your report. A
  doc fix for a doc-vs-mechanism collision is only done when the doc has been literally executed.
  Write the graph output to a scratch path (NOT the repo root) so the worktree stays clean.
- **Version bump:** `version:` PATCH bump in the SKILL.md frontmatter (bump-on-modify is
  validator-enforced); regenerate the README index if `check_readme_sync` demands it (rule 4).
- **Acceptance:** documented command executed verbatim with output shown · version bumped ·
  gauntlet 4/4.

### Item 4 · BL-X07 — kata-promote's frontmatter mischaracterizes Hermes
- **Owner set:** `skills/meta/kata-promote/SKILL.md` ONLY.
- **The defect:** `source:` frontmatter and the body call Hermes a "no-gate instant-universal
  model". The 2026 Hermes docs show an opt-in staging gate exists (`write_approval`, pending
  queue, unified diffs) — the ungated behavior is the DEFAULT config only. Our comparison must
  stay truthful (PD-2 honesty-labels discipline applied to our own docs).
- **The fix:** tighten both sites to say "Hermes' DEFAULT config applies learning ungated and
  instantly-universal; an opt-in staging gate (write_approval / pending queue / unified diffs)
  exists" — the design contrast (our always-on human gate vs their default-off gate) survives,
  stated accurately. Reference: `.planning/specs/learning-graph/RESEARCH-HERMES-PI.md` (read it,
  rule 3 — match its evidence labels, do not overclaim in the other direction).
- **Version bump:** 0.1.0 → 0.1.1 (PATCH); regenerate the README index if required (rule 4).
- **Acceptance:** both sites truthful and consistent with the research file · bump + index in
  sync · gauntlet 4/4.

### Wave-1 integration (conductor)
Merge order x01 → x02 → x03 → x07 (arbitrary, sets disjoint); on README-index conflicts,
REGENERATE (never hand-merge); re-run the index regeneration once after all merges; integrated
gauntlet 4/4; hybrid gate (below) per item; record per-item wall-clock/tokens/gate outcome +
surprises in OBSERVATIONS.md.

## Wave 2 — one builder, after wave-1 integration

### Item 5 · BL-X05 — sweep the exact-pin class from the test suite
- **Owner set:** `tools/tests/**` — MINUS any assertion a wave-1 item just authored (they are
  fresh, not rot; flag, don't edit, if one looks wrong).
- **The defect class:** an exact pin (version string, count, literal) asserted against a LIVING
  repo file reds on every legitimate future change and trains editing-tests-under-pressure. The
  proven instance: `test_validate_prime_directives.py`'s `version: 0.17.0` pin (already fixed to
  a semver floor — that fix is the model).
- **The fix:** audit the suite for the class — pins against living files ONLY (fixtures,
  test-local data, and generated-in-test values are all LEGITIMATE and out of scope). Convert real
  instances to floors or regenerable assertions, one commit per file. **"Audited N candidate
  sites, found zero real instances" is an acceptable outcome** — with the audit trail (what was
  checked, why each was legitimate) in the report; do not manufacture work (PD-2).
- **Self-gate:** for each conversion, show the assertion still fails on a genuinely-wrong value
  (non-vacuity — the BURN-D 16/33 discipline, spot-check level: one neutralization probe per
  converted file is enough at this scale).
- **Acceptance:** audit trail complete · conversions non-vacuous · gauntlet 4/4.

## Gating — hybrid (BBM-1)

Per item: (a) the conductor RE-RUNS the builder's named self-gate; (b) a fresh-context NO-WRITE
judge agent per item, running concurrently with other items' judges, checks diff-vs-brief (scope
exact, nothing beyond the owner set) and independently reproduces the central claim; (c) the
conductor spot-audits ONE wave-1 item end-to-end (chosen after reports arrive, not announced in
advance); (d) integrated gauntlet 4/4 closes the wave. Default-FAIL: an unverifiable claim is a
NEEDS_WORK, not a benefit of the doubt.

## What is NOT in this burn (truth serum)

BL-X04 (graph_gen worktree exclusion — next round; BBM-2 prerequisite of the burn engine) ·
BL-X06 (host-issue tracking, not code) · the six platform probes (operator-in-the-loop,
interleaved with the UX grill, not builder work) · anything from the BL-N feature batch (D169:
every feature builds only after its spec freezes).
