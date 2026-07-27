---
date: 2026-07-26
kind: assessment — answers "should grill/design/plan run as subagents?"
verdict: SPLIT. One of them structurally cannot. The rest should, and it is a bigger win than model control.
---

# SHOULD PHASE-1 WORK RUN AS SUBAGENTS?

## The proposal

> *"Since the plan/grill/elevate/design/etc is important to be executed in the appropriate loop
> profile — should we also execute these as subagents to control the quality of them? … With asking
> the user to `/model`, combined with this, it gives us maximum control over the allocation of models
> across the entire lifecycle, and we can also use things like advisor and assessor agents within
> them."*

## Verdict: SPLIT — and the split falls on one hard structural line

**The dividing question is not "is this important?" It is "does this activity need to talk to the
human?"** Subagents cannot. `AskUserQuestion` is withheld from them structurally — confirmed in the
orchestrator research, and consistent with Claude Code's documented subagent contract (one prompt in,
one summary out; teammate prompts bubble up to the lead).

| phase-1 activity | needs the human mid-flight? | dispatch? |
|---|---|---|
| **Grill** | **YES — this IS the mechanism** | ❌ **NO — structurally impossible** |
| **`kata-context` term pinning** | partly — resolves terms *as decisions are made* | 🟡 rides the grill |
| **ELEVATE** | proposes *to* the human, but generates autonomously | 🟡 **hybrid** — generate dispatched, present in main |
| **Design doc authoring** | no — synthesizes an already-frozen grill output | ✅ **YES** |
| **Plan authoring** | no — decomposes an already-frozen design | ✅ **YES** |
| **Freeze-gate review** | no — adversarial, must be fresh-context | ✅ **ALREADY IS** |

## Why the grill cannot be dispatched — this is decisive

**Our own `D70` already settled the underlying point**, from a real experiment:

> *"The grill's engine is **interrogating the human**, which is OFF in autonomous mode (Arm A: 'no
> ambiguities required human resolution')."*

D70 retired the grill-vs-baseline A/B precisely because a grill with no human to interrogate **is not
a grill** — it degenerates into an autonomous planning pass, which D70 showed a capable agent does
about equally well either way. Dispatching the grill to a subagent recreates exactly the condition
that made the experiment invalid.

Two more blockers, both structural:
- **The infer-then-confirm gate** requires each load-bearing value to be *individually named in the
  mirror and explicitly confirmed or corrected by the human.* A subagent cannot hold that conversation.
- **Dual control** — the operator can type "execute" at any point to end the grill. That is a live
  human channel into a running process, which the subagent contract does not provide.

**So the grill stays in the main session. That is not a limitation to engineer around — it is what the
grill is.**

## Why design + plan SHOULD be dispatched — and the win is bigger than model control

The operator's stated motivation is model allocation. That is real, but it is the **third**-largest
benefit here.

**1. It removes the largest context load from the main session — the actual prize.**
Today the main window absorbs the grill conversation **plus** the full generative authoring of the
design doc **plus** the plan, and only *then* becomes the orchestrator. Design and plan authoring are
long, token-heavy, generative work. Dispatching them means the main session holds **the grill
conversation and the resulting artifacts** — not the drafting. This is the single biggest available
reduction in phase-1 context, and it directly attacks the exhaustion problem behind `KH-T01`.

It is also precisely Anthropic's stated rationale for Workflows — *"the script holds the loop … so
Claude's context holds only the final answer."* Same move, applied one phase earlier.

**2. It makes the doctrine consistent.** *"A well-behaved orchestrator does not do the work itself."*
**Authoring a design document is doing the work.** The conductor should coordinate its authoring and
gate the result — exactly as it already does for build tasks. Phase 1 is currently the inconsistency:
we dispatch building, evaluating and reviewing, but the conductor personally writes the two most
load-bearing documents in the run.

**3. Then model control** — the operator's point, and it holds. A dispatched design/plan author takes
an explicit model override, so their quality stops depending on whatever the session launched with.

**4. It gives `KH-T10` somewhere to land.** A dispatched design-author and plan-author are *roles*,
which can carry real specifications, rubrics, and per-role behavior. Today they are "whatever the main
session does next." This is how phase 1 stops being a prompt convention.

**5. Advisor and assessor consults become natural** — as the operator noted. A dispatched plan-author
can raise an advice-request the same way a build worker does, through machinery that already exists.

## What this costs, honestly

1. **The conductor must now VALIDATE artifacts it did not author.** That needs a real gate, not a
   glance. Precedent exists — we already gate returned build work default-FAIL — but a returned
   design doc is judged differently from a returned diff, and that rubric does not exist yet.
2. **A dispatch level.** Research warning stands: Claude Code's depth default has swung **5 → 1 → 3
   across four releases.** Spending a level on phase 1 is a real cost on an unstable number.
3. **A lossy return boundary.** A subagent returns a summary. A design doc's value is its *full*
   reasoning. **Mitigation is straightforward and we already use it: return the artifact as a FILE, not
   as a summary.** The conductor reads the file. The return payload is just a path plus a verdict.
4. **Who writes `INTENT.md`.** `intent_scaffold.write_intent` is the sole authorized writer and the
   conductor is sole main-tree git writer. A dispatched author must return content for the conductor to
   write, or write into a worktree. **Not a blocker — but it must be explicit, or we breach
   single-writer discipline the moment we build this.**

## Recommended shape

```
MAIN SESSION (conductor — needs the right model, hence the /model check)
├── grill ......................... IN-SESSION. Interrogates the human. Non-negotiable.
├── kata-context .................. in-session, rides the grill
├── ELEVATE ....................... generate dispatched → present in-session
├── freeze INTENT.md .............. in-session (sole writer)
│
├── design-doc author ............. DISPATCHED · own model · own spec · returns a FILE
├── freeze-gate review ............ DISPATCHED (already is) · fresh-context, adversarial
├── plan author ................... DISPATCHED · own model · own spec · returns a FILE
├── plan check .................... DISPATCHED (already is)
│
└── ORCHESTRATION ................. thin. Coordinates; does not do the work.
```

**The main session keeps exactly two things: the human conversation, and the authority to freeze.**
Everything generative moves out.

## What this does to the `/model` requirement

**Narrows it, does not remove it.** The grill still runs in the main session, and the grill is the
highest-judgment activity in the loop. So the anchor still matters — but it matters for *one* activity
instead of four, and the run's *artifacts* become model-controllable independent of the session.

That makes the readiness `/model` check **more** worth building, not less: it now guards a small,
precisely-identified surface rather than a vague "the whole run might be degraded."

## Open questions for the grill

1. **What gate does a returned design doc face?** Default-FAIL like build work, or something else? The
   rubric does not exist.
2. **Is ELEVATE's split real or over-engineering?** Generating candidates in a subagent and presenting
   in-session may be more machinery than value for a single recommendation.
3. **Does the grill hand the design-author its full ledger, or a distilled brief?** Full ledger is
   faithful but expensive; a brief risks losing the resolution that made a decision what it is.
4. **Depth budget.** If design/plan take a level, what does that leave for workers, and do we hit the
   host default?
