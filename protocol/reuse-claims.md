# protocol/reuse-claims.md — the verify-before-reuse contract

A cross-skill contract enforcing **verify-before-reuse** — the guard that blocks phantom-machinery claims from
entering any frozen artifact. This is the canonical source of truth (LD2); responsible skills reference it by
path (`protocol/reuse-claims.md`), never by `[[wikilink]]`.

## Purpose

A "reuses X" sentence is an architectural assertion about existing code. When it enters a frozen artifact
unchecked, it creates a **documentation-only seam** — a design that describes machinery that does not expose the
surface it assumes. This is the project's signature failure mode. This contract makes the check explicit,
mandatory, and auditable at every site where reuse claims are authored.

## The guard (LD3 — verbatim contract text)

> Before writing **"reuses / composes / via the existing X"** (or "the orchestrator already writes Y", "this
> already exists/has Z"), **grep/read X and confirm it exposes the exact field / event / output / path the
> design assumes — cite the concrete `file:line`.** Treat "this already exists" as a **claim to verify, not an
> assumption**. If the surface is not there, label it a **NEW capability** and scope it. A reuse claim with no
> cited surface is a documentation-only seam (the project's signature failure mode) — do not freeze it.

## Verified vs phantom reuse claims

| Kind | Definition | What to do |
|---|---|---|
| **Verified** | The claim cites a concrete `file:line` that exposes the exact field / event / output / path the design assumes. The surface is present and accessible. | Freeze the claim as written. |
| **Phantom** | The claim uses "reuses / composes / via the existing X" (or equivalent) with no cited `file:line`. The surface may or may not exist — it has not been confirmed. | Do NOT freeze. Apply the guard: grep/read, then either cite the surface or label it NEW. |

A cited path alone is insufficient — the specific field, event, output, or path the design relies on must be
visible at the cited line, not merely inferred from the file's existence.

## NEW-capability fallback

When the surface is not there — the module exists but does not expose the assumed interface, or the module does
not exist at all — the claim becomes a **NEW capability** and must be:
1. Labeled explicitly as NEW (not "reuses" or "composes existing").
2. Scoped: ownership, acceptance criteria, and any downstream dependency updated accordingly.
3. Re-reviewed before freeze, since a new capability changes the cost and risk profile of the design.

Do not soft-label ("could reuse", "may compose") — the distinction is binary: verified surface present, or NEW
capability required.

## Structural invariant — never tiered (LD1)

This guard is a **structural invariant** in the sense of D33: it applies identically at Essential, Standard, and
Advanced depth. Tiers vary the depth of exploration and coverage; this guard is integrity — like
no-self-certification — and never relaxes. A skill operating in Essential mode does not skip the `file:line`
check.

## Producer skills (LD4)

The guard applies at three sites, each of which references this file by path:

| Site | Skill / artifact | Role |
|---|---|---|
| **Design freeze** | `kata-design-doc` | Primary authoring site — DESIGN §2 "grounded in the code" and §5 backward-compat. Every reuse claim entering a frozen DESIGN must be verified here. |
| **Plan re-assert** | `kata-plan` / `RUBRIC.md` | Quality-bar re-assertion — the RUBRIC's invariant list. Inherited by all three tier plan files (essential / standard / advanced). |
| **Worker pre-flight** | `kata-tdd` | Worker check before implementing — when reading the closest existing code analogs, verify that any "reuses X" in the assigned task has a cited surface. Escalate if not. |

`kata-grill` is explicitly **not** a site — it resolves decisions with the human; it does not author
code-grounded reuse claims.
