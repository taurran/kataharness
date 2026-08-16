---
spec: backlog-burn-02
status: frozen
opened: 2026-08-16
kind: small burn — burn-mode prototype round 2 (evidence-tracked per the burn-mode vision)
scope: BL-X01 · BL-X02 · BL-X03 · BL-X07 (wave 1) · BL-X05 (wave 2) — operator-ruled D171
branch: burn/backlog-burn-02 (stacked on burn/backlog-burn-01 @ eed995c; PR #54 open on the parent)
waveBoundaries: autonomous
baseSHA: resolved at dispatch as `git rev-parse HEAD` of the commit that froze this plan; the
  resolved value is RECORDED in OBSERVATIONS.md's dispatch row (the durable audit record — MED-5)
convergence: reviewed 2026-08-16 (fresh-context no-write judge) — CONVERGE-HOLD, 4 HIGH / 5 MED /
  4 LOW; ALL findings resolved in this revision (each resolution tagged [Hn]/[Mn]/[Ln] inline)
evidence-out: OBSERVATIONS.md beside this file (mode evidence round 2)
---

# PLAN — backlog-burn-02 (the five ≤1-file fixes, two waves)

**Triage happened before this plan was written (BBM-7), and the convergence review corrected it
(H3-class catch):** the conductor's "only `quality` has provider tags, verified twice" claim was
WRONG — machine-checked, **twelve** `kata/module/*` provider tags exist across `skills/` AND
`modules/` (`benchmark closeout debug defer graph iac initiation meta quality report research
slop`). The X01 defect still reproduces (`design`/`bakeoff`/`improve` have no providers), but
discovery instructions below are machine-probes, never greps [HIGH-4a].

## Worktree provisioning (conductor, before dispatch)

Worktrees are provisioned **OUTSIDE the repo root** at sibling paths —
`C:\dev\projects\kh-burn02-<item>` — via manual `git worktree add <path> -b task/burn02-<item>
<baseSHA>` (BBM-9). Outside-the-root placement is load-bearing, not cosmetic: `graph_gen` has no
worktree exclusion (BL-X04, deferred), so any embedded worktree poisons X03's proof-run counts —
the measured ~7× BURN-F contamination class [HIGH-2].

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
   artifacts — the README skill-index mechanical columns are regenerable via
   `uv run python validate_skills.py --write` (the flag is `--write`, NOT `--fix` [MED-1]); note
   that `--write` REFUSES while any non-README skill ERROR exists (`validate_skills.py:1155-1160`)
   — if you hit that refusal, fix YOUR skill error first; it is not an H5 collision [MED-1]. The
   conductor re-derives the index once at integration, so index merge conflicts are resolved by
   regeneration, never by hand.
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
  skill carrying frontmatter tag `kata/module/<name>`, and `design`/`bakeoff`/`improve` have no
  provider (machine-verified at review).
- **The fix — PRE-DECIDED end state [HIGH-4b]:** the example becomes **`["slop","debug",
  "benchmark"]`** — exactly the three modules the SAME FILE's "Optional modules" registry table
  (`config.md:176-180`) documents, all three provider-backed (in the twelve-tag list). This keeps
  the owner file internally consistent: the example, the registry table, and the load-guard all
  agree. `quality` leaves the example because it is mode-bundle machinery, not an à-la-carte
  optional module per that registry. Do NOT re-derive the set by grep — verify it with the
  machine probe below.
- **Clause-pin — PRE-DECIDED, no escalation branch [LOW-3]:** verified at review: `config.md`'s
  pinned clauses (`validate_skills.py:738-742`) are the D33 grounding-gate sentence (line 26), the
  scanner-agnostic sentence (line 30), and the toolkit-external sentence (line 27) — line 14 is in
  NONE of them; `config.md` is fingerprint-exempt (`validate_skills.py:914-916`); the
  REQUIRED_PROTOCOL term `"bakeoff"` is carried independently by line 19, so removing it from
  line 14 is safe. Your only obligation: the validator stays green (which mechanically proves all
  of the above held).
- **Self-gate:** the machine probe —
  `uv run python -c "import validate_skills, kata_config; skills=validate_skills.load_skills();
  import re,pathlib; ex=re.search(r'\[\"[a-z\",]+\"\]', pathlib.Path('../protocol/config.md')
  .read_text(encoding='utf-8').splitlines()[13]); print(kata_config.validate_core_config(...))"` —
  shape it however is cleanest, but it MUST load the REAL skills tree via
  `kata_config.available_from_skills(validate_skills.load_skills())` and show the edited example's
  module list passing `validate_core_config`. Command + output in your report.
- **Acceptance:** example = the registry-consistent provider-backed set · probe passes against the
  live tree · gauntlet 4/4.

### Item 2 · BL-X02 — the installer's "next steps" banner names commands that do not exist
- **Owner set [MED-2]:** `tools/kata_install.py` + `tools/tests/test_install_cli_headless.py`
  (its `expected_banner` check is tautological — it byte-compares stdout against a call to the
  same function; touch it only if your edit breaks it) + **one NEW test file you create:**
  `tools/tests/test_install_banner_commands.py` (named here so rule 4 and rule 6 can both hold —
  discovery at review found NO existing test pins the banner, so the self-gate needs a home).
- **The defect:** the claude branch (`kata_install.py:1306-1313`, function `_next_steps_banner`
  [LOW-1]) tells first-run users to run `/kata-initiate` and `/kata-bootstrap`; neither exists.
  The real command set (verified at review — exactly these seven files in
  `adapters/claude/commands/`): `/kata` · `/kata-loop` · `/kata-start` · `/kata-onboard` ·
  `/kata-resume` · `/kata-status` · `/kata-validate`.
- **The fix:** step2 names only real commands with the settled comprehension-gated copy (UX-4):
  `/kata-start` = "single run: plan and build once, then stop" · `/kata-loop` = "full cycle:
  build → closeout → improve again" · `/kata-onboard` = guided tour on an existing repo. The
  codex/kiro and generic branches reference SKILLS (kata-initiate exists as a skill) — verify and
  leave correct references alone.
- **Self-gate:** the new test asserts every `/kata[-a-z]*` token regex-extracted from the claude
  branch's `_next_steps_banner` output is a subset of the `*.md` basenames in the real
  `adapters/claude/commands/` — structural, so it cannot rot the way the banner did.
  **Stated convention crossing [LOW-2]:** `test_install_commands.py:4` deliberately avoids the
  real commands dir (fixtures only). Your new test knowingly crosses that convention — that is
  SANCTIONED here (this guard's entire purpose is coupling the banner to the real command set);
  say so in a comment citing this plan, so the X05 sweep and future readers see it is deliberate.
- **Acceptance:** no phantom commands in `_next_steps_banner` output · new structural test green ·
  gauntlet 4/4.

### Item 3 · BL-X03 — kata-understand documents a graph-rebuild command the tool refuses
- **Owner set:** `modules/closeout/kata-understand/SKILL.md` ONLY.
- **The defect:** Step 1 (`SKILL.md:46-48`) says `uv run python graph_gen.py --root .. --out
  ../kata.graph.json`; `graph_gen._safe_path` (`graph_gen.py:766-777`) raises on ANY `..` path
  component. Verified at review: absolute paths PASS `_safe_path` (they are `.resolve()`d, no
  root-confinement on `--out` — `graph_gen.py:800` creates parent dirs), so the absolute-path
  form is mechanically sound.
- **The fix — parameterized form [HIGH-1]:** rewrite Step 1's command with EXPLICIT placeholders —
  `--root <absolute-repo-root> --out <absolute-out-path>` (with a one-line note that relative
  `..` paths are refused by design) — and harmonize Step 2 (`SKILL.md:53-55`), which currently
  reads the repo-root `kata.graph.json`, to read "the `--out` path you chose". Placeholders are
  the doc's own contract, so a proof run that substitutes them IS running the doc as written —
  this dissolves the run-exactly vs. keep-clean collision: substitute `<absolute-out-path>` with
  a scratch location outside the repo.
- **PROOF obligation [HIGH-1/HIGH-2]:** RUN the rewritten Step 1 once from a fresh shell with
  placeholders substituted (`--root` = your worktree's absolute root, `--out` = a scratch path
  outside any repo). Include invocation + node/file counts in your report, AND sanity-check the
  counts against the honest baseline (~157 files / ~5,560 nodes / ~6,629 edges at BURN-F's clean
  measure — your worktree contains no embedded worktrees, so wildly higher numbers mean
  contamination and are themselves an escalation, not a pass).
- **Version bump:** `version:` PATCH bump in the SKILL.md frontmatter (bump-on-modify is
  validator-enforced); regenerate the README index if `check_readme_sync` demands it (rule 4).
- **Acceptance:** rewritten command literally executed with sane counts shown · Step 2
  harmonized · version bumped · gauntlet 4/4.

### Item 4 · BL-X07 — kata-promote's frontmatter mischaracterizes Hermes
- **Owner set:** `skills/meta/kata-promote/SKILL.md` ONLY (+ README index regeneration, which the
  `source:` edit MANDATES — the index renders `source:` frontmatter (`validate_skills.py:483-484`),
  so skipping the regen reds gate 4; conversely, editing only the body and not `source:` leaves
  the derived `README.md:352` false with the gate still green — edit BOTH sites [MED-4]).
- **The defect:** `source:` frontmatter and the body (`SKILL.md:16-17`, `:29-31`) call Hermes a
  "no-gate instant-universal model". The research (`.planning/specs/learning-graph/
  RESEARCH-HERMES-PI.md:29-36`) shows Hermes' SKILLS pipeline has an opt-in staging gate. Our
  comparison must stay truthful (PD-2 applied to our own docs).
- **The fix — corrected primitives [HIGH-3]:** tighten both sites to: "Hermes' DEFAULT config
  applies skill learning ungated and instantly-universal; an opt-in staging gate exists (staged
  writes in `~/.hermes/pending/skills/`, `/skills pending`, `/skills diff <id>` unified-diff
  review, approve/reject)". Do NOT name `write_approval` — that is Hermes' MEMORY gate
  (RESEARCH:15-25), not the skills gate; the review caught the conductor's first draft making
  exactly that error. Match the research file's evidence labels; do not overclaim either way.
- **Historical references — PRE-DECIDED, out of scope [MED-4]:** the same claim appears in five
  historical planning records (`DECISIONS.md:444/471/585`, `specs/loop-cognition/DESIGN.md:86`,
  `ARCHITECTURE-CORRECTION-2026-07-26.md:123`, `STATE.md:1526`). Those are point-in-time records
  and are deliberately NOT swept (decisions are superseded, never rewritten); the research file +
  the fixed skill are the authoritative current statements. Flag, don't touch.
- **Version bump:** 0.1.0 → 0.1.1 (PATCH) + README index regen (rule 4).
- **Acceptance:** `source:` AND body corrected with the skills-gate primitives · consistent with
  RESEARCH-HERMES-PI.md · bump + index in sync · gauntlet 4/4.

### Wave-1 integration (conductor)
Merge order x01 → x02 → x03 → x07 (arbitrary, sets disjoint — disjointness + import closure
re-verified CLEAN at review); on README-index conflicts, first restore a syntactically VALID
table (take either side wholesale), THEN regenerate with `--write` — `_parse_existing_use`
(`validate_skills.py:460-473`) reads the hand-authored Use column back from the current README,
so regenerating over a conflict-markered table silently loses Use cells [LOW-4]; a README
conflict is CERTAIN (X03 and X07 both bump). Then integrated gauntlet 4/4; hybrid gate (below)
per item; record per-item wall-clock/tokens/gate outcome + surprises in OBSERVATIONS.md.

## Wave 2 — one builder, after wave-1 integration

### Item 5 · BL-X05 — sweep the exact-pin class from the test suite
- **Owner set:** `tools/tests/**` — MINUS any assertion a wave-1 item just authored (they are
  fresh, not rot; flag, don't edit, if one looks wrong — X02's new structural test is a
  deliberately-sanctioned living-file dependency, marked by its comment).
- **The defect class — SCOPE PRE-DECIDED [MED-3]:** an exact pin against a LIVING repo file that
  rots on legitimate change. **In scope: version strings, counts, and generated values ONLY.
  Explicitly OUT of scope: doctrine-phrase presence checks** (`assert "Grill-depth dial" in text`
  and kin — those are semantic floors per `prime-directives.md:79-81`, a protection feature;
  loosening one is a silent protection removal the gauntlet CANNOT catch, so the judge reviews
  every conversion individually). Fixtures, test-local data, and generated-in-test values are all
  legitimate and out of scope. The proven model fix: `test_validate_prime_directives.py:477-487`
  (semver floor + doctrine text).
- **The fix:** audit the ~12 test files that touch real repo files via `REPO_ROOT`; convert real
  in-scope instances to floors or regenerable assertions, one commit per file. **"Audited N
  candidate sites, found zero real instances" is an acceptable outcome** — with the audit trail
  (what was checked, why each was legitimate) in the report; do not manufacture work (PD-2).
- **Self-gate:** for each conversion, show the assertion still fails on a genuinely-wrong value
  (non-vacuity — one neutralization probe per converted file).
- **Acceptance:** audit trail complete · conversions non-vacuous · zero doctrine-phrase checks
  touched · gauntlet 4/4.

## Gating — hybrid (BBM-1)

Per item: (a) the conductor RE-RUNS the builder's named self-gate; (b) a fresh-context NO-WRITE
judge agent per item, running concurrently with other items' judges, checks diff-vs-brief (scope
exact, nothing beyond the owner set) and independently reproduces the central claim; (c) the
conductor spot-audits ONE wave-1 item end-to-end (chosen after reports arrive, not announced in
advance); (d) integrated gauntlet 4/4 closes the wave. Default-FAIL: an unverifiable claim is a
NEEDS_WORK, not a benefit of the doubt. For X05 the judge ADDITIONALLY reviews every conversion
for scope-creep into the doctrine-phrase class [MED-3].

## What is NOT in this burn (truth serum)

BL-X04 (graph_gen worktree exclusion — next round; BBM-2 prerequisite of the burn engine;
mitigated here by outside-the-root worktree placement) · BL-X06 (host-issue tracking, not code) ·
the six platform probes (operator-in-the-loop, interleaved with the UX grill, not builder work;
probe 1 already RESOLVED 2026-08-16) · the five historical Hermes references (MED-4 ruling
above) · anything from the BL-N feature batch (D169: every feature builds only after its spec
freezes).
