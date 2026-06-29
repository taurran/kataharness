# protocol/intent.md — the `INTENT.md` artifact schema

The **front-half hand-off**. Written and **frozen by `kata-initiate`** at the end of initiation; read by the
harness as the authoritative goal record for the current run. This schema is **PINNED** (D88/DESIGN §2) — slices
may not fork it.

> **Additive amendment (Slice D, 2026-06-29):** `acceptanceCriteria` added as an OPTIONAL field.  This is an
> additive amendment to the PINNED schema, not a fork — the required set is unchanged and existing `INTENT.md`
> files that omit this field remain fully valid.

> **BC:** `INTENT.md` absent ⇒ the harness reads the frozen DESIGN as today. Initiation is additive; the
> greater loop remains fully optional.

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
| `acceptanceCriteria` | `string[]` **(OPTIONAL)** | Checkable success criteria captured in the Phase-2 mirror (step 2g) — "how we'll know it's done."  Framed as outcomes, not implementation.  **Absent or empty is valid** (e.g. `research` runs or when the human explicitly confirms no checkable criteria for this run).  `build_intent` emits this field only when non-empty; absent ⇒ byte-identical output to pre-field builds (BC). |

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
- **Validator.** `protocol/intent.md` is in `REQUIRED_PROTOCOL`; `check_protocol_schemas` enforces that
  every required term is documented here (`kind`, `goal`, `fixes`, `features`, `changeSummary`, `target`,
  `grillDepth`, `readiness`).  `acceptanceCriteria` is documented as an **optional** term — it is not in
  the required set and existing `INTENT.md` files that omit it remain fully valid.
