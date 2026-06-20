# kata-plan — roadmap layer (incremental delivery)

The roadmap layer is the **net-new** surface sprint-cadence adds to the `kata-plan` family (D85). It runs
**before** the per-sprint plan whenever `delivery.shape == "incremental"` (`protocol/config.md`). Like
[`RUBRIC.md`](./RUBRIC.md) it is a shared method, not a tier — every `kata-plan-<tier>` obeys it; the chosen
tier still sets the *depth* of each individual sprint plan.

> One-shot runs never touch this file — they go straight to the tier method in `RUBRIC.md`. The roadmap layer is
> a no-op unless `delivery.shape == "incremental"`.

## What it does
Partition the **frozen project DESIGN's** dependency DAG at natural seams into **prime-frame-sized sprints**, emit
a single **roadmap artifact**, and then freeze each sprint's plan **just-in-time** (not all up front). The
roadmap is frozen but **boundary-amendable** ([[kata-sprint]] reshapes *remaining* sprints, never the active one).

## Step 1 — partition the DAG into sprints
- Start from the same DAG the tier method builds (vertical tracer-slices → disjoint ownership). **Cut at natural
  seams** — a seam is a place where a coherent, demonstrable increment ends and the next can start from a green
  baseline. Prefer a seam that yields a **demonstrable artifact** (something the human can see/run at the gate).
- **Size every sprint to the prime frame** (`protocol/config.md` *Prime-frame sizing*, D83 — do not redefine the
  number here; reference it). The prime frame is the model's recommended effective working band (adapter-resolved
  to real tokens).
  - **Floor:** if the *whole project* already fits within **one** prime frame ⇒ **refuse to sprint, recommend
    one-shot** (sprinting buys nothing; the boundary ceremony is pure overhead).
  - **Ceiling:** if a candidate sprint's context demand **exceeds** one prime frame ⇒ **split it** at the next
    seam. Max sprint count = `⌈project context demand ÷ prime frame⌉` — no arbitrary cap.
- Each sprint must be **independently gateable**: it ends at a runnable default-FAIL gate ([[kata-evaluate]]).

## Step 2 — emit the roadmap artifact (schema PINNED, D85/A1)
Write one roadmap doc (durable, git-committed = tier-2 trail) of exactly this shape:
```
{
  projectDesignRef,            # the frozen DESIGN this roadmap partitions
  frozenAt,                    # commit/timestamp of the freeze
  sprints: [
    {
      id,                      # stable sprint id (sprint-1, sprint-2, ...)
      goal,                    # the demonstrable increment this sprint delivers
      gateCommand,             # the runnable default-FAIL gate that closes the sprint
      demonstrableArtifactType,# what the human sees at the boundary (test run, screen, report, ...)
      dagSeamRationale,        # WHY the cut is here (the natural seam justification)
      dependsOn: []            # prior sprint ids this one builds on
    }
  ]
}
```

## Step 3 — just-in-time per-sprint freeze
- Do **not** freeze all sprint plans up front. At the start of each sprint, run the **tier method** (`RUBRIC.md`
  at the configured tier) over **only that sprint's** slice of the DAG, freeze that plan, hand to
  [[kata-orchestrate]]. This keeps each plan accurate against the latest green baseline (boundary amendments may
  have reshaped what is still ahead).
- **Sprint baseline = the most recent green gate** (D84): sprint 1 of a greenfield project is greenfield; every
  later sprint (and every sprint of an existing repo) is **version-up-shaped** — it reuses the shipped version-up
  machinery (footprint ownership + full-baseline-green regression, D50), protecting the prior sprint's result.

## Boundary amendability (handoff to [[kata-sprint]])
The roadmap layer only *produces* the roadmap and the active sprint plan. Steering the roadmap (add / drop /
reorder *remaining* sprints) happens **only at a boundary**, through [[kata-sprint]]'s G1–G4 protocol — a recorded
re-plan, never a silent rewrite. The **active** sprint plan is immutable within its sprint (D1, no-drift).
