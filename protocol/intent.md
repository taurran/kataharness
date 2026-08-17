# protocol/intent.md — the `INTENT.md` artifact schema

The **front-half hand-off**. Written and **frozen by `kata-initiate`** at the end of initiation; read by the
harness as the authoritative goal record for the current run. This schema is **PINNED** (D88/DESIGN §2) — slices
may not fork it.

> **Additive amendment (Slice D, 2026-06-29):** `acceptanceCriteria` added as an OPTIONAL field.  This is an
> additive amendment to the PINNED schema, not a fork — the required set is unchanged and existing `INTENT.md`
> files that omit this field remain fully valid.

> **Additive amendment (Trust Model W2, 2026-08-16):** `status` added — a closed two-value enum
> `draft | frozen`, always emitted by `intent_scaffold` on every new `INTENT.md`.  This is an additive
> amendment to the PINNED schema, not a fork — the required set is unchanged, no existing field was removed
> or reordered, and existing `INTENT.md` files that omit `status` remain fully valid (they read as `absent`,
> which is never coerced to `frozen`).

> **BC:** `INTENT.md` absent ⇒ the harness reads the frozen DESIGN as today. Initiation is additive; the
> greater loop remains fully optional.

> **BC (freeze field, R3-H2):** a **direct one-shot harness run** — no initiation — governs under `plan`
> exactly as today; `intent: frozen` binds ONLY runs that entered via initiation / the kata-loop.  The freeze
> field adds a governor rung for initiation-entered runs; it takes nothing away from the one-shot path, and no
> previously-legal run becomes a denied run because of it.

## Location
`INTENT.md` (Markdown with YAML frontmatter) at the working-branch root. Written once by `kata-initiate`,
frozen at the end of the initiation session, never mutated mid-run.

## Schema

| Field | Type | Meaning |
|---|---|---|
| `kind` | `"project" \| "research" \| "version-up"` | The classified intent kind. `project` = net-new build; `research` = inquiry-first, no code committed; `version-up` = iterating on an existing codebase (evaluate what the *actual* goal of the version-up is — the captured gap, D88). |
| `goal` | `string` | One-paragraph north star. The single most important thing this run must achieve. Immutable once frozen. |
| `fixes` | `string[]` | What is being **repaired** (version-up: bugs, regressions, tech-debt items). Empty list for `project`/`research`. |
| `features` | `string[]` | What is being **added** — new capabilities, skills, modules, or user-visible behaviors. |
| `modulesAdded` | `string[]` | New modules or skills introduced by this run (e.g. `["modules/initiation"]`). Used by closeout to build the understand-map and by the validator to confirm discovery. |
| `changeSummary` | `string` | One-sentence summary of what changes in this version — the diff in plain language. Surfaced by `kata-report`. |
| `target` | `object` | WHERE/ON WHAT the run executes — see *target sub-schema* below. |
| `grillDepth` | `"skip" \| "light" \| "standard" \| "full"` | The grill tier chosen during initiation (maps to `config.tiers["kata-grill"]`). Frozen here so closeout + kata-loop can reconstruct the run's rigor level. |
| `readiness` | `string` | The agent's "enough-to-execute" verdict + rationale — one paragraph stating which decision branches are resolved and what, if anything, remains to be discovered mid-run. Honest: if readiness is conditional, say so. |
| `acceptanceCriteria` | `string[]` **(OPTIONAL)** | Checkable success criteria captured in the Phase-2 mirror (step 2g) — "how we'll know it's done."  Framed as outcomes, not implementation.  **Absent or empty is valid** (e.g. `research` runs or when the human explicitly confirms no checkable criteria for this run).  `build_intent` emits this field only when non-empty; absent ⇒ output identical to a build that omits the field (BC). |
| `status` | `"draft" \| "frozen"` | The machine-checkable freeze state of this artifact (Trust Model W2, R2-H1/R3-L2). `draft` = written but not yet sealed; `frozen` = sealed by `kata-initiate` at its Phase-6 freeze act. `intent_scaffold.build_intent` / `write_intent` emit `frozen` **only** when the caller passes the keyword-only `freeze=True` argument by name — never inferred from the answers dict, never a call-site default. Read back by `intent_scaffold.intent_status` under the **first-word parse rule** (BL-F01): the value is split on whitespace and the first word case-folded, so `status: frozen — sealed at the Phase-6 gate` parses as `frozen`; absent/empty ⇒ `absent` (never coerced to `frozen`); any other first word ⇒ raises. |

### `target` sub-schema

| Field | Type | Meaning |
|---|---|---|
| `kind` | `"self" \| "existing" \| "greenfield"` | `self` = the harness dogfoods itself; `existing` = version-up on an existing repo (path required); `greenfield` = new repo, no prior baseline. |
| `path` | `string?` | Filesystem path to the target repo. Required when `kind == "existing"`. |
| `vault` | `string?` | PokeVault binding — one of: `"linked"` (existing PokeVault), `"scaffolded"` (kata-initiate set one up), `"own:<path>"` (user-supplied vault), or `"per-folder:<path>"` (aim-each-folder mode). Absent ⇒ no vault configured for this run. |
| `platform` | `"claude" \| "codex" \| "kiro" \| "quick" \| "other"` | The agent platform driving this run. Set during the interactive config session (GL-R3c). Governs which adapter `AGENTS.md`/installer is activated. **`claude` + `codex` are the v0.1 public targets**; **`kiro`** is the planned v0.3 adapter; **`quick`** is the **ACP desktop-host target — the integration seam for an external/work ACP host** (that host brings its own installer); **`other`** is the catch-all. |

## Notes

- **Frozen at end of initiation.** `kata-initiate` writes and freezes `INTENT.md`; no downstream skill mutates
  it. If a mid-run discovery invalidates the goal, that is an escalation event (`protocol/escalation.md`),
  not a silent rewrite.
- **The grill hand-off.** `grillDepth` written here is authoritative — it overrides any config default for
  this run. `kata-bootstrap` reads it to set `config.tiers["kata-grill"]` consistently.
- **Dual-control freeze.** Either the user says "execute" (hard bail from grill) OR the grill self-judges
  readiness and proposes execute (user confirms) — both paths write and freeze this file.
- **version-up gap capture (D88).** For `kind: version-up`, `goal` must capture the *actual* objective of
  the upgrade, not just "improve the thing". The `fixes[]` / `features[]` split makes it auditable.
- **The freeze is a named act, not an inference.** `status: frozen` is written by exactly one code path —
  a caller naming `freeze=True` on `intent_scaffold.write_intent` (`kata-initiate`'s Phase-6 freeze).
  Every other write, including every interview-in-progress save, omits the argument and writes `draft`.
  A freeze reachable by inference — a heuristic over the answers, a defaulted argument, a "looks complete"
  guess — would be a silent-permissive default of the D136 class, which is the failure this rung exists to
  eliminate.  Writer and reader (`intent_status`) live together in `tools/intent_scaffold.py` so the two
  halves of one schema row cannot drift apart; the dispatch seam is a **consumer** of `intent_status`, not
  its owner.
- **Fail-closed reading.** `intent_status` mirrors `kata_restore.plan_status` in posture verbatim: same
  first-word parse rule, same three-way return (`draft` / `frozen` / `absent`), same refusal to coerce an
  unrecognized value in either direction.  Two governor rungs that read a `status:` field must not disagree
  about what that field means.
- **Validator.** `protocol/intent.md` is in `REQUIRED_PROTOCOL`; `check_protocol_schemas` enforces that
  every required term is documented here (`kind`, `goal`, `fixes`, `features`, `changeSummary`, `target`,
  `grillDepth`, `readiness`).  `acceptanceCriteria` is documented as an **optional** term — it is not in
  the required set and existing `INTENT.md` files that omit it remain fully valid.  `status` is likewise
  documented but not in the validator's required-term set: adding it there would fail every pre-amendment
  `INTENT.md` in the wild, and the BC law above is precisely that those artifacts stay legal.  This file is
  fingerprinted, so this amendment carries its own two-step — the digest is re-approved by hand after the
  diff is reviewed (the `acceptanceCriteria` precedent).
