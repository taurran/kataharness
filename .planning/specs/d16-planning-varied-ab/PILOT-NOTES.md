# D16 pilot notes (2026-06-18) — project 1, run-1, Arm A vs Arm B

**Purpose of the pilot:** shake out method before the full 18. It did its job — it found the experiment, as
first-registered, would not discriminate. Both arms ran fully autonomously on Sonnet and both passed the
held-out gate; the value here is the **method learnings**, not the (tied) result.

## Raw result
| | Arm A (KataHarness) | Arm B (GSD) |
|---|---|---|
| held-out gate (8 cases) | **8/8 pass** | **8/8 pass** |
| ruff | clean | clean |
| drift / replans / escalations / interventions / eval_defects / rework | 0/0/0/0/0/0 | 1/0/0/0/0/0 |
| self `first_pass_green` | "no" (strict) | "yes" (lenient) |
| tokens · tool-uses · wall | 56.9K · 45 · 350s | 50.3K · 28 · 229s |
| files · self-tests | 6 · 29 | 6 · 35 |

## Learnings (→ re-spec, DESIGN v2)
1. **Corpus too easy → zero discrimination.** A crisp, unambiguous spec lets both methods sail; every
   discriminating metric reads ~0. The grill's thesis is value *under ambiguity/complexity* — `wordfreq` had
   neither. (Echoes L10.) **Fix:** harden the 3 projects to be *planning*-hard (interacting rules, subtle
   edges, order-of-operations, underspecified-but-determinable points) while staying small/one-shottable (D57).
2. **`first_pass_green` is not objectively measurable post-hoc.** Identical situation (both needed one ruff
   fix on first lint), opposite self-reports (A strict "no", B lenient "yes"). The held-out gate measures
   *final* correctness, not first-attempt. **Fix:** drop self-judged `first_pass_green`; use objective
   **`gate_pass`** (held-out gate ∧ ruff on the delivered build) + **`fix_iterations`** (failing→fix cycles to
   green, precise definition, both arms count identically). A lint auto-fix is **not** drift.
3. **Grill overhead is real on trivial tasks** (A: +6.6K tokens, +121s, +17 tool-uses for the same outcome).
   Expected and fine — the grill should pay off on *hard* tasks; this just confirms the corpus must be hard
   enough that the overhead buys something measurable.

## Integrity note
This adjustment is **instrument-driven on a tied result** — there is no "winning arm" to bias toward, so it is
not p-hacking. The pilot is explicitly a pre-run shakeout (DESIGN §6/corpus README); the hardened protocol is
**re-registered (DESIGN v2)** before any counted run. v1 pilot data is retained here as history.
