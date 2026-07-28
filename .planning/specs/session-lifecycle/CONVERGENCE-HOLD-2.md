# CONVERGENCE GATE — PASS 2 · **HOLD** (2026-07-27)

> Fresh-context, no-write adversarial pass over the SL-19..SL-28 repairs. **VERDICT: HOLD — 13 HIGH
> remain open.** Pass 2 closed **2 of 9** HIGHs and the repairs introduced **12 new findings**.
> The grill is NOT converged and **must not** be compiled into a DESIGN.

## Closure of pass-1 HIGHs

| # | repair | status |
|---|---|---|
| H1 | SL-19 | **NOT CLOSED** — the live `GRILL-LEDGER.md` is **untracked** (18 of 19 ledgers tracked), so a "git-tracked source" rule cannot see it |
| H2 | SL-20 | ✅ **CLOSED** — retraction correct; drift 56/61 confirmed; cite-with-staleness answers SL-5 |
| H3 | SL-21 | PARTIAL — `READ-IN ORDER` restored, but the renumber breaks SL-4 and redefines the section's meaning |
| H4 | SL-22 | **NOT CLOSED** — barred by frozen decisions (below); no filename, no writer |
| H5 | SL-23 | PARTIAL — `≥2 initiatives` now operational, but `Targets:` repeats `Doc-baked`'s defect and SL-19..SL-28 carry none |
| H6 | SL-24 | PARTIAL — window concept sound, operands undefined for untracked/gitignored sources |
| H7 | SL-25 | ✅ **CLOSED** — cleanest repair in the set |
| H8 | SL-26 | PARTIAL — filename-unchanged migration verified sound; generator/trigger still unnamed |
| H9 | SL-27 | PARTIAL — core verified correct; "the pinned helper" is itself a phantom |

## 🔴 The four that matter most

**NEW-1 (HIGH) — SL-22's journal is barred by a FROZEN decision the ledger never cites.**
`DECISIONS.md:1952` **D135 — "board-is-the-trail; no separate continuous-replay journal — FROZEN"**:
*"we do NOT invent a continuous-replay journal subsystem… a second log creates two sources of truth
that can diverge."* **D133** carves the ref out *only* provided it *"commits **ONLY the board**"* and
is *"recovery-only and **self-pruning (squashed/dropped at task integration)**."* **D142(b)**:
*"D133's mechanical carve-out remains board→`refs/kata/trail` **ONLY**."* And
`restore-hardening/DESIGN.md:44` accepts as worst case that *"a `git gc` or a clone that omits
`refs/kata/*` loses the tail"* — confirmed: `remote.origin.fetch` does not fetch `refs/kata/*`.
**H4 was not closed; the loss was moved from tier-3 rebuild to clone/gc/integration, undisclosed** —
and it breaks SL-2's own binding test (*"the repo clone alone is sufficient"*).

**NEW-7 (HIGH) — the emit path was audited wrong, and the gate proved it by running the code.**
`learn_feed.py:511-518` renders `body` only when no recognized field is non-empty. This ledger's
house style (`- **Decision:**` + indented sub-bullets) yields an **empty** `decision` and orphans the
content into `body`. Measured: **20 of 29 entries lose body content on emit — 19,153 characters
dropped.** Six of ten repair entries parse with `decision=''`. **SL-19's rendered page contains no
Decision at all.** SL-28's adopted mitigation ("record supersession in the body") is defeated by the
same path.

**NEW-3 (HIGH) — SL-21 silently downgrades a fail-closed security gate.**
`D74` (FROZEN): *"**Redaction is a HARD pre-write gate** (`kata-handoff` §7, C3 — fail-closed)."*
Live at 8+ normative sites incl. `protocol/engram.md:87` (*"without it the LEARN path is a
data-exfiltration / IP-leak surface"*), `:154`, `:164`, `kata-improve/SKILL.md:116`. SL-21's
justification misapplies D151, which `engram.md:160-165` scopes to **the loop feed only** and which
explicitly keeps agent-authored pages fail-closed.

**NEW-5 (HIGH) — applied to this repo today, the repaired collector returns nothing.**
`git ls-files .planning/specs/session-lifecycle/` → empty. `DECISIONS.md` last commit
`2026-07-19T22:40`, `LESSONS-LEARNED.md` `22:44`, vs last `HANDOFF.md` commit `2026-07-26T20:23` —
**both named §5 sources are 7 days older than the handoff**, so they never demote and never collect.
**This grill's 28 decisions would be invisible to the handoff meant to carry them.**

## Remaining new findings

**NEW-2 (HIGH, SL-21)** the renumber never remaps SL-4, which still names `§3`/`§5`/`§7` in the old
scheme — so the anti-KH-T02 checks now bind to the wrong sections · **NEW-4 (HIGH, SL-19+SL-27)**
*"routed through the pinned helper"* is a **phantom reuse claim**: `log.follow=false` is inlined at
two call sites (`contract_gate.py:150`, `kata_restore.py:502`) and the Doctrine's named model
`kata_telemetry._run_git:139` **does not pin it** — committed twice, in the entry retracting a
phantom · **NEW-6 (HIGH, SL-19)** the left operand is the *file's* commit time, so a **floor-only**
write resets the freshness clock and SL-8 suppresses the rebuild at exactly the crossing the design
exists for — SL-10 said *"compare against the DEPTH write, not the file mtime"* and SL-19 collapsed
it by assertion · **NEW-8 (HIGH, SL-21+SL-25)** `§0` is FLOOR and checks *never* gate FLOOR, so
SL-4's first named check **can never fire** · **NEW-9 (MED)** the L10→L9 fix corrects the anchor but
**L9 still does not support the claim** (it reports a *classification* drift-magnet honored in a
zero-drift run; nothing about magnitude constants) — the PD-2 defect survives its own correction ·
**NEW-10 (MED, SL-22)** no filename, no reader, no module; the clean-tree claim holds only for a
plumbing shape SL-22 never pins · **NEW-11 (MED, SL-25)** the depth gate discards model-authored
depth at the one crossing where it cannot be re-authored; KH-T02 argues discard, never-no-handoff
argues marker, the ledger asserts both · **NEW-12 (LOW, SL-2)** *"the vault lives outside git"* is
**false** — `Vault\.git` exists, and SL-26 depends on it.

---

## Root cause (author's own assessment, recorded for the successor)

**Phase 0 never read `.planning/DECISIONS.md`.** It was measured *structurally* — line count, heading
count — and never *read*. D135, D133(c)(d), D142(b) and D74 are all frozen, all directly govern this
design, and none was cited. The 2734-line decision log is the single densest source of binding
constraint in the repo and this grill treated it as a parse target rather than as law.

**Second cause: the repairs were not re-verified against the code the way Phase 0 was.** Pass 2
closed NEW-7 by *running `learn_feed` over the ledger*. That was available to the author and was not
done.

**Signal to heed:** repairing 9 HIGHs produced 12 new findings. The design is more entangled with
frozen decisions than the grill accounted for; a third same-session repair pass is likely to
compound rather than converge.
