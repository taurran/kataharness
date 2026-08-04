---
spec: bump-on-modify
status: frozen
opened: 2026-08-03
baseline: master `20faf0e` · gauntlet 4/4 PASS · working tree clean
tier: kata-grill-standard (short — the change is ~40 lines)
---

# GRILL LEDGER — make the version-bump rule real

**In plain terms:** the standards say *"edit a skill, you must bump its version, and this is
enforced."* It is not enforced. The checker only confirms the number is well-formed, so `0.1.0` stays
valid while the whole file is rewritten.

## Phase 0 — grounding (read, not measured)

### The gap, exactly

- `docs/STANDARDS.md:111-112`: *"Every modification to an existing skill MUST increment the appropriate
  version component before merge. The frontmatter `version` field is REQUIRED and
  **validator-enforced**."*
- `tools/validate_skills.py:123-124`: the **only** version check is
  `if not SEMVER.match(str(fm.get("version", "")))` → `"version '…' is not semver"`.

So "validator-enforced" is **true for presence and format, false for bump-on-modify**. The claim in
STANDARDS.md is the thing that is wrong, and either the code must become true or the sentence must be
reworded. This is the same shape as `KH-T02`: a documented invariant with nothing enforcing it.

### Measured facts (verified this session at `20faf0e`)

| fact | value | how |
|---|---|---|
| skills discovered by the validator | **49** | two roots: `SKILLS_DIR` + `MODULES_DIR` (`validate_skills.py:80`) |
| `SKILL.md` under `skills/` | **46** | `skills/*/*/SKILL.md` — matches the validator's own glob (`:85`) |
| the other 3 | `modules/` | not a discrepancy; two roots by design |
| companion files inside skill dirs | `RUBRIC.md` ×4 (shared), plus per-skill `ROADMAP.md`, `DECISION-LEDGER.md`, language files | `Get-ChildItem skills -Recurse` |
| pinned git helper already exists | `kata_telemetry._run_git` | Determinism Doctrine law 1 — **reuse it, never re-derive the pin set** |

### Prior art to obey

- **Determinism law 1** — every git call whose stdout is parsed goes through the shared pinned helper.
  A new git call site here MUST use `_run_git`, not a fresh `subprocess` call.
- **Determinism law 2** — sorted at every filesystem boundary.
- **D136** — decision code that reads an external artifact must **hard-fail** on absent/unparseable
  input, never fall through to a permissive default. Directly relevant to "what if there is no git
  history?" — see B3.
- **`config.md` / `exec-safety.md` precedent (shipped today)** — a whole-file digest is the wrong tool
  for something that changes constantly; it trains blind re-approval. 49 skills change far more often
  than 23 protocol files, so **fingerprinting skills is the wrong mechanism** and is ruled out at
  Phase 0 rather than carried as a live option.

### Known prior statement that needs re-checking, not inheriting

The 2026-07-01 handoff states: *"Editing a shared `RUBRIC.md` needs NO peer bump (verified: the
validator does not flag it)."* That records the **absence of a check**, not a policy ruling — the
validator flags nothing today, so "does not flag it" is trivially true of everything. **It must not be
cited as an existing decision.** Whether a RUBRIC edit obliges its consumers to bump is B1, open.

## The decision tree

| # | branch | status |
|---|---|---|
| **B1** | What counts as "the skill changed" — `SKILL.md` only, or its whole folder (incl. shared `RUBRIC.md`)? | **OPEN — asked first** |
| B2 | Baseline to compare against — the branch's fork point from `master`, or the previous commit | OPEN |
| B3 | Behavior when there is no git history (tarball / fresh clone / CI shallow checkout) — fail, or skip with a surfaced note | OPEN |
| B4 | Which component must change — any bump counts, or must MAJOR/MINOR/PATCH match the kind of edit | OPEN |
| B5 | New skills (no baseline) and deleted skills | OPEN |
| B6 | Does `STANDARDS.md:111-112` get reworded, or does the code make it true | OPEN |

## Resolved branches

### BOM-1 — "Changed" means `SKILL.md` changed. Nothing else. · LOCKED

- **Decision:** the check compares each discovered `SKILL.md` against its baseline. Companion files —
  shared `RUBRIC.md`, `ROADMAP.md`, `DECISION-LEDGER.md`, language notes — do **not** trigger a bump
  for anyone.
- **Rejected — whole skill folder / RUBRIC cascades:** a shared `RUBRIC.md` edit would oblige all four
  grill skills to bump for a change none of them made. Bumps would stop meaning "this skill changed"
  and start meaning "something near this skill changed", which makes the version less informative, not
  more. *(Operator initially chose the folder scope, then reversed to the recommendation.)*
- **Rationale:** the `version` field lives in `SKILL.md` and describes `SKILL.md`. One file, one
  version, no cascade rules to explain.
- **Explicitly NOT inherited:** the 2026-07-01 handoff's *"editing a shared RUBRIC needs no peer bump
  (verified)"* recorded the **absence of any check** — trivially true of every file — not a ruling.
  This entry is the first actual decision on the question.
- **Known residual, stated not hidden:** a `RUBRIC.md` edit genuinely does change how its four
  consumers behave, and after this change that still requires no bump. Accepted deliberately; revisit
  only if RUBRIC churn becomes a real source of untracked behavior change.

### BOM-2 — Baseline is the branch's fork point from `master` · LOCKED

- **Decision:** compare each `SKILL.md` at the working tree against its content at
  `git merge-base HEAD master`. If the file differs and `version:` does not, that is an ERROR naming
  the skill. When `HEAD` has **not diverged** from `master` (i.e. the merge-base *is* `HEAD`), there is
  nothing under review and the check is a **no-op**.
- **Rejected — compare against the previous commit:** would demand a version bump on *every commit*,
  which directly contradicts the repo's own "commit as you go, not one giant commit at the end"
  convention. The rule is a **pre-merge** gate, not a per-commit tax.
- **Resolved without asking** — the fork-point framing is the only one compatible with the existing
  commit convention; `STANDARDS.md:111` already says *"before merge"*, which names the boundary.
- **Determinism:** the git call MUST go through the existing pinned helper (`kata_telemetry._run_git`),
  never a fresh `subprocess` call — Determinism Doctrine law 1, *"never re-derive the pin set per
  call-site."*

### BOM-3 — Any increment satisfies the rule; the component is not machine-judged · LOCKED

- **Decision:** the check requires only that `version` **differs from and is greater than** its
  baseline value. It does **not** attempt to decide whether an edit "deserved" MAJOR vs MINOR vs PATCH.
- **Rationale:** whether a wording change is really a contract change is a semantic judgment, not a
  statically detectable property. A checker that guessed would produce false HOLDs and train people to
  work around it — the same reasoning `D136` uses to keep the silent-permissive-default guard as prose
  rather than a static check. `STANDARDS.md:106-111` keeps the MAJOR/MINOR/PATCH guidance as
  human-applied guidance; review remains its enforcement.
- **Also required:** the new version must be **greater** than the baseline, not merely different —
  otherwise lowering a version would pass.

### BOM-4 — New skills need no bump; deleted skills are not checked · LOCKED

- **Decision:** a `SKILL.md` that does not exist at the baseline is **new** — there is nothing to bump
  from, so it is exempt (it enters at `0.1.0` per `STANDARDS.md`). A `SKILL.md` deleted on the branch
  is simply absent from the discovery walk and is not checked.
- **Resolved without asking:** both follow mechanically from "compare against the baseline"; neither
  has a second reasonable reading.

### BOM-6 — The code becomes true; the sentence gets sharpened, not deleted · LOCKED

- **Decision:** `STANDARDS.md:111-112`'s *"validator-enforced"* claim stays, because this change makes
  it true — but the sentence is tightened to state the scope decided in BOM-1 (it is `SKILL.md` that
  must bump, measured against the fork point from `master`), so it does not over-claim a folder-wide
  rule that was explicitly rejected.
- **Rationale:** the failure mode here was a document asserting enforcement that did not exist.
  Replacing it with a document asserting *slightly different* enforcement than what was built would
  repeat the fault at smaller scale.

### BOM-5 — No git baseline ⇒ SKIP the check and SAY SO · LOCKED

- **Decision:** when the baseline cannot be resolved (no `.git`, no `master` ref, shallow clone with no
  merge-base), the bump check emits a **visible skip notice** — e.g. `bump-on-modify: SKIPPED (no git
  baseline)` — and the remaining checks run normally. It does **not** fail, and it does **not** stay
  silent.
- **Rejected — hard-fail:** would make the validator unusable outside a full git checkout, including
  for the skill suite installed as a bundle in another repo, which is a shipped use case.
- **Rejected — skip silently:** a check that quietly does nothing is indistinguishable from a check
  that passed. That is the exact silent-permissive-default `D136` exists to forbid, and it is the
  disease this whole spec is treating.
- **Why this is not a `D136` violation:** `D136` targets **accidental** silent-permissive defaults and
  exempts *"designed, documented fail-safe fallbacks"* by name. An announced skip is the documented
  kind — the operator can see the guard did not run, which is the property `D136` actually protects.
- **Binding on the build:** the skip notice must be **visible in normal validator output**, not
  buried behind a verbose flag. If it cannot be seen, it is a silent skip wearing a label.

## Tree status — ALL BRANCHES CLOSED

| # | branch | resolution |
|---|---|---|
| B1 | what counts as changed | BOM-1 — `SKILL.md` only, no cascades |
| B2 | baseline | BOM-2 — fork point from `master`; no-op when undiverged |
| B3 | no git history | BOM-5 — announced skip, never silent, never fatal |
| B4 | which component | BOM-3 — any *increase*; component not machine-judged |
| B5 | new / deleted skills | BOM-4 — new is exempt, deleted is not checked |
| B6 | the STANDARDS sentence | BOM-6 — code makes it true; sentence sharpened to match |

## Convergence pass 1 — HOLD. It caught a design that would have shipped broken.

A fresh-context no-write reviewer returned **HOLD** with 10 findings. Every decisive claim was
re-verified by the conductor before folding. **All verified true.** The corrections below **supersede**
the entries they name.

Had this shipped as originally grilled it would have been **red on Windows on day one** and **would
never have fired in CI** — i.e. it would have replaced an unenforced rule with a differently-unenforced
rule, which is the disease, not the cure.

### ⚠️ CORRECTION to BOM-5 — the conductor asserted a fact that was false (second time this session)

BOM-5 justified skip-don't-fail on the grounds that the validator "ships as a bundle in another repo,
which is a shipped use case." **`tools/validate_skills.py:2` says the opposite, verbatim:** *"KataHarness
skill-conformance validator (maintainer tooling — **NOT shipped with the suite**, D27)."*
`tools/pyproject.toml:4` repeats it.

**The decision stands; the reason is replaced.** The real no-git conditions are: a **source zip/tarball
download with no `.git`**, and a **shallow CI checkout with no base ref**. Both are real, and both are
the "designed, documented fail-safe fallback" `D136` exempts by name.

### ⚠️ CORRECTION to BOM-2 — mandating `_run_git` was wrong on two counts

**(a) It cannot do the job.** `kata_telemetry._run_git` calls `subprocess.run(..., text=True)` with
**no `encoding=`**, so git stdout is decoded with the process locale. **All 49 `SKILL.md` files contain
non-ASCII** (`≤`, `—`, `⇒`, `…`). On Windows (the primary dev box, and `windows-latest` in the CI
matrix) `git show <ref>:<path>` would return mojibake that can never equal
`Path.read_text(encoding="utf-8")` → **every skill reads as changed** → the gate fires on all 49.

**(b) I did not check for prior art, and it already exists.** `tools/footprint.py:171`
`changed_in_task(base_ref, task_ref)` does exactly this comparison, and carries guards this ledger had
not thought of: `--no-renames` pinned (Doctrine law 1 requires it "where file sets are compared", and
`_run_git` does **not** pin it), and **`>1 merge-base RAISES`** (`footprint.py:199`, `check=True` at
`:216`) — a criss-cross branch topology fails closed instead of silently picking one ancestor.

**This is a named, recurring blind spot** — *verify a primitive exposes the needed surface before
mandating its reuse* — and it was walked into anyway. Recording it rather than quietly fixing it.

**Superseding decision:** change detection **reuses `footprint.changed_in_task`** against the resolved
base ref. No new git call site. No raw `subprocess`. Path comparison is on the repo-relative POSIX
paths that helper already emits.

### BOM-7 — Ref resolution, scope, and the CI change that makes the claim true · LOCKED

- **Base ref resolution order:** `origin/master` → `master` → the default branch via
  `refs/remotes/origin/HEAD` → **no baseline found ⇒ the BOM-5 skip**. Bare `master` alone was wrong:
  a contributor's local `master` can be months stale, while `origin/master` is what the work actually
  merges into.
- **Scope is COMMITTED work only** (operator ruling). Uncommitted edits do not trip the gate. This
  matches `footprint.py:200-203` for the sibling check verbatim — *"only COMMITTED work is visible …
  the gate runs after the task commits"* — and it keeps the gauntlet green during ordinary mid-edit
  runs. **Stated consequence:** an uncommitted un-bumped edit passes; the rule is a pre-merge gate, not
  a save-time linter.
- **The CI must change or the rule is decorative** (operator ruling). Verified at `20faf0e`:
  `.github/workflows/ci.yml` uses `actions/checkout@v4` with **no `fetch-depth`** (defaults to a
  shallow depth-1 clone) and triggers on `push: [master]` + `pull_request`. On push, `git merge-base
  HEAD master` returns `HEAD` itself (both `20faf0e` — measured) ⇒ no-op. On PR, no base ref ⇒ skip.
  **Net: the gate never fires in automation.** Fix: `fetch-depth: 0` and ensure the base ref is
  fetched. Without this, `BOM-6` must not claim enforcement "before merge", because nothing enforces it
  there.

### BOM-8 — Version comparison is tuple-based; a bad baseline is an ERROR · LOCKED

- **Compare `tuple(int(p) for p in version.split("."))`, never strings.** Measured: `"0.10.0" > "0.9.0"`
  is **False** in Python, so a correct `0.9.0 → 0.10.0` MINOR bump would be rejected as a decrease.
  Skills already sit at `0.2.x`/`0.4.x`, so double digits are reachable, not hypothetical.
- **Baseline version absent, non-semver, or unparseable frontmatter ⇒ ERROR naming the skill**, never a
  permissive pass (`D136`: unreadable decision input hard-fails).

### BOM-9 — A renamed skill must not launder itself into "new" · LOCKED

- **The bypass:** under a path-keyed lookup, `git mv` a skill and rewrite it freely — at the baseline
  path nothing exists, `BOM-4` calls it new, and new is exempt. Since `docs/STANDARDS.md:98` encodes the
  category in the path and `:125` mandates moving deprecated skills, renames are a *normal* operation.
- **Decision:** rename detection is on. `footprint.changed_in_task` pins `--no-renames`, so a move
  surfaces as delete+add; the check resolves the old path via `git diff -M --name-status` against the
  base and compares against it. A genuinely new skill (no predecessor) stays exempt per `BOM-4`.
- **Precedent:** `footprint.py:186-190` records the mirror-image lesson — `git mv` invisibly defeating a
  path-keyed check — as adversarial finding F5-1. The same trap, caught twice.

### BOM-10 — The skip notice is a `WARN` finding; the mechanism is named · LOCKED

- **Decision:** the no-baseline notice is emitted as `Finding("WARN", "bump-on-modify", …)`. Verified
  mechanics: findings print to **stderr** at `validate_skills.py:946-947`, the summary counts
  `len(findings) - len(errors)` as warnings at `:950`, and **exit code is `1 if errors else 0`** at
  `:951` — so a WARN is **visible in normal output and does not break the gauntlet**.
- **Why this does not permanently change the "N/0" green convention:** the WARN is emitted **only when
  no baseline can be resolved.** With git present — every normal dev run and, after the `BOM-7` CI
  change, every CI run — the check runs and emits nothing. `0 warning(s)` remains the steady state.
- **Honest residual:** `--only <skill>` filters findings by `f.where` (`:944-945`), so the notice is
  dropped under `--only`. That is **pre-existing behavior for every global finding** (the protocol
  checks included), not something this change introduces, and `--only` is documented at `:940-942` as a
  reporting aid and "never a narrower gate."

### BOM-11 — Named tests are required, including the paths the gauntlet cannot reach · LOCKED

- **The problem the reviewer surfaced:** on `master` the check is a permanent no-op (merge-base ==
  HEAD, measured), so `uv run python validate_skills.py` in the gauntlet **never exercises the
  comparison logic**. Shipping it without tests would ship it unexercised.
- **Required tests:** (1) changed-without-bump ⇒ ERROR naming the skill · (2) changed-with-bump ⇒ pass ·
  (3) no baseline ⇒ WARN + exit 0 · (4) undiverged HEAD ⇒ no-op · (5) `0.9.0 → 0.10.0` ⇒ pass (the
  string-compare trap) · (6) renamed-and-rewritten ⇒ ERROR, not exempt · (7) baseline with a
  non-semver version ⇒ ERROR.
- **Also required:** the existing fixture tests monkeypatch `SKILLS_DIR`/`MODULES_DIR` to `tmp_path`
  (`tools/tests/test_validate_skills.py:509-511`), which is **outside the git repo** —
  `Path.relative_to(REPO_ROOT)` would raise. The build must handle skill dirs outside the repo without
  crashing, and a test must pin that.

### BOM-12 — "Differs" means any textual difference · LOCKED

- Any byte difference in `SKILL.md` counts, with no normalization beyond git's newline handling
  (`.gitattributes` pins LF). **A whitespace-only or reflow-only edit does require a bump** — stated
  explicitly so no builder invents a "meaningful change" heuristic, and so the rule stays mechanical.

## Tree status — ALL BRANCHES CLOSED (post-HOLD)

| # | resolution |
|---|---|
| B1 | BOM-1 — `SKILL.md` only |
| B2 | BOM-2 **as corrected** + BOM-7 — reuse `footprint.changed_in_task`; `origin/master` first; committed-only |
| B3 | BOM-5 **as corrected** + BOM-10 — `WARN` finding, exit 0, real no-git reasons |
| B4 | BOM-3 + BOM-8 — any *increase*, tuple-compared |
| B5 | BOM-4 + BOM-9 — new exempt, renames closed |
| B6 | BOM-6 + BOM-7 — sentence true only if the CI change lands |
| new | BOM-11 tests · BOM-12 any-textual-difference |

## Status — CONTRACT FROZEN 2026-08-04

Deliberate deviation, recorded: for a change this size this ledger **is** the frozen contract and
serves as the builder's brief; DESIGN/PLAN are not separately dispatched. Operator-directed pace. The
conductor does not author the change and gates it default-FAIL.

## Blocked at close — do not forget

The grill-close `learn_feed.py` emit stays **BLOCKED** by `DEF-2` (the emitter silently drops entry
bodies for this ledger style). Same posture as the `ungated-protocol-files` grill.
