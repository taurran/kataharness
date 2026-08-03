---
date: 2026-07-26
purpose: the same queue as INGEST-EXECUTION-ORDER.md, written so it reads without decoding anything
---

# THE INGEST QUEUE — IN PLAIN ENGLISH

Every item is tagged **FIX** (something is broken or wrong), **FEATURE** (something doesn't exist
yet), **DECISION** (needs your call), or **CHORE** (bookkeeping). The short code in brackets is only
for cross-referencing the detailed docs.

---

## ALREADY DONE

**1. Catalogued everything that arrived.** `[INGEST-0]` — CHORE
The other team sent 8 code proposals, 5 "here's where we differ" notes, and their 26-item roadmap. I
listed every single one and where it's tracked, so nothing quietly falls off.

**2. Checked their package for leaks myself.** `[INGEST-1]` — CHORE
They're an AWS-internal team sending code to our public repo. I searched their package for AWS names,
internal URLs, account numbers, tokens, and hidden git history. Found none. I also re-ran their tests
and got exactly the number they claimed.

**3. Protected our own CloudFormation/Terraform skills from a future scan.** `[INGEST-2]` — CHORE
We ship IaC skills, so our code legitimately says "AWS" all over. Wrote that down before anyone runs
a leak-scan over our repo and mistakes our own product for a leak.

**4. Fixed the harness pointing at last generation's Opus.** `[T-11]` — FIX ✅
The harness had "opus" hard-wired to `claude-opus-4-8`. On Opus 5 it silently recognized nothing —
which meant **no cost-saving model downgrades and no Fable advisor**, with no error message. It now
identifies a model by reading the tier out of its name, so future versions work with no code change,
and it refuses to start if it sees a model tier it doesn't recognize. Two independent reviewers tore
it apart; both found real problems in my work, and both sets are fixed.

**5. Tested 18 things that were claimed to work.** `[TRACK-1]` — CHORE ✅
The other team's report said 14 of our subsystems were "the same on both sides." A claim isn't
evidence, so I checked each one against our actual code. Results are the bad news below.

---

## DO FIRST — nothing here needs code

**6. Rotate your GitHub token.** `[BL-M27]` — FIX 🔴 **you, not me**
Your GitHub personal access token is sitting in plain text in `~/.claude/settings.json`, readable by
anything, and handed to every program this tool starts. It's **not** in git, so nothing leaked. But
it should be rotated and moved somewhere protected.

**7. Ask them for the note they forgot to send.** `[T-00]` — ✅ **CLOSED 2026-08-02, accepted as withdrawn**
Their own paperwork says they held back two things as "too risky to send" and would explain both.
Only one explanation arrived. We were going to ask for the other — not because we wanted the code, but
because we couldn't see what they'd decided to withhold or why. **We're no longer working with them, so
we're not chasing it.** No code was ever sent for it, so nothing is missing from our side. `[D170]`

**8. Fix our own notes: MindBridge is not a branch of us.** `[T-09]` — FIX
Our records call it "a fork of KataHarness." It isn't. It's a hand-rebuilt copy with **no shared
history at all** — you cannot merge, rebase, or diff against a common ancestor. That's a genuinely
different risk picture than a branch, and our docs describe the wrong one.

**9. Do we care that bugs can travel backwards?** `[T-10]` — ✅ **CLOSED unbuilt 2026-08-02**

The two projects share no history at all — MindBridge is a hand-rebuilt copy, not a branch of us. So
code never moved between us by merging; it moved by **someone copying files across**. A copy captures
whatever version existed the day it was taken, which means **any fix made afterwards never follows** —
there's no merge to carry it. That's exactly how they ended up running five bugs we'd already fixed.
The question was whether to build something that checks, whenever code crosses between the two
projects in either direction, that already-fixed bugs aren't riding along.

**Decision: closed without building it.** We're not exchanging code with them anymore, so there's no
longer a route for this to happen. A guard on a road nobody drives protects nothing.

**What we're keeping, because it has nothing to do with MindBridge:** *copied code silently loses the
fixes made after the copy.* That's true of **any** hand-copy without a shared history — so it comes
back the first time we vendor or port code from anywhere. That's the trigger to re-open on, not this
item. `[D170]`

*Worth noting why this took three sessions: nobody ever wrote down what `T-10` meant, so each session
inherited a code with no content and passed it on. Closing it with the reasoning written down is the
fix; quietly deleting it would have repeated the mistake.*

---

## BROKEN — found by testing, confirmed with evidence

**10. Crash recovery would delete six of your working branches.** `[BL-M21]` — FIX 🔴
If a run dies and you recover it, the recovery code looks for a branch called `integration`. **We
don't have one** — we integrate on `master`. It treats "branch missing" as "nothing was finished,"
decides every task must be redone, and then deletes the task branches as stale. Six live ones would
go. It's never been run for real, which is why nobody noticed.

**11. The quality gate accepts month-old proof that the build passed.** `[T-04]` — FIX 🔴
Before declaring work done, the gate reads a results file. It checks the file exists and isn't
corrupt. **It never checks the results are from this run.** Ours right now claims a passing build
from 37 commits ago, and the gate would accept it today as proof. Their proposal fixes exactly this.

**12. The "don't lie about what you built" rules can be inverted and still pass.** `[T-07]` — FIX 🔴
We have two core honesty rules. The automated check confirms they're intact by looking for **seven
words**. I had a reviewer rewrite the rules to say the *opposite* — "stub it and move on,
present-but-dead counts as built" — keeping those seven words. **The check passed green.** Their
proposal replaces word-counting with something real.

**13. We never verify the code reviewer is actually independent.** `[T-05]` — FIX
Our rule is that work gets judged by a fresh reviewer who can't edit files. We do check it can't
edit. We **never** check it's actually fresh or independent — that's assumed from how it's launched.
Nothing records it either way.

---

## CHEAP AND SAFE

**14. Make our version-bump rule real.** `[T-01]` — FIX
Our standards say: edit a skill, you must bump its version, *and this is enforced*. **It isn't.** The
checker only confirms the version is well-formed — so `0.1.0` stays valid while you rewrite the whole
file. About 40 lines fixes it, and it can't break any of our 49 existing skills. This is the item
they'd pick if we only took one.

**15. Stop a log line from miscounting.** `[BL-M24]` — FIX
Every learning-log entry has said "1 item skipped" forever. I chased it: it's counting the
document's own title as an item. Harmless, nothing lost, one line to fix — but it's been quietly
lying for months.

**16. Read files back after writing them.** `[T-06]` — FEATURE
When we write an important file, we trust the write succeeded. They had file corruption from this
twice. Worth checking whether we actually have the same gap before adopting.

---

## BIG AND RISKY — real thought required

**17. A tool that automatically checks our reproducibility rules.** `[T-02]` — FEATURE
We have ten rules meaning "same input, same output, every time." Today a human has to notice
violations while reading code. They built a tool that checks nine of them automatically. **Run it in
report-only mode first** — it flags 101 things in our code and I estimate ~59 are false alarms,
because it doesn't know about an exception our own rules make. Turning it on as a hard gate on day
one would light the whole repo red.

**18. Six new rules for our reproducibility doctrine.** `[T-03]` — FEATURE ⚠️ highest risk
They want to add six rules to the document that every other quality rule defers to. **They admit the
rules were reviewed as a batch, never adversarially challenged, come from one codebase, and that
codebase is architecturally the opposite of ours.** They recommend two of the six transfer cleanly.
I'd take those two.

**Before we touch this**, one of their claims needs checking: they assert their additions *narrow*
where human judgment is allowed rather than widening it. Nobody has verified that, and it's the
crux of the whole item. `[D2-16]`

---

## ALREADY HALF-DONE ON OUR SIDE

**19. Their code-map fix — we already built it.** `[T-08]` — FIX, re-scoped
They offered to fix how our code map handles a common Python project layout. We shipped that fix on
July 2nd. The real remaining gap is much narrower: it only fails for that layout when it's nested
inside another folder. Don't merge a duplicate.

**20. Rebuild the code map.** `[BL-M26]` — CHORE
Ours is 35 days old and was built *before* the fix above, which is why it looks so sparse — 450
items with only 3 import connections. Rebuilding it is also the only way to check whether their
claimed improvement is real.

---

## THE BACKLOG — not scheduled, grouped by what they actually are

### Things that exist but nothing can reach
- **The "run the whole loop" component can't be started from any command.** `[BL-M20]`
- **An adaptive setting is validated, stored, and never read by anything.** `[BL-M25]`
- **Handoff notes have "why was this written" fields no real handoff has ever filled in.** `[BL-M23]`
- **The mid-build quality checker has never once produced machine-readable output** — 210 mentions in
  our history, zero actual results. `[BL-M16]`

### Things enforced by writing, not by code
- **Nothing in code reads the "how careful should this run be" setting** — it's a note for the AI to
  interpret. `[BL-M17]`
- **We say quality rules can't be weakened in cheaper modes. No test checks that.** `[BL-M18]`
- **7 places call git directly** instead of the shared wrapper that keeps output consistent. `[BL-M15]`

### Gaps in the safety net
- **Nothing forces a run to write a handoff before it ends.** If it dies, the context dies too — and
  that's exactly what happens when you hit a usage limit. `[BL-M22]`
- **The files proving a run happened are excluded from git**, so there's no permanent record. `[BL-M19]`

### Worth building eventually (their ideas, and they're good)
- **Trace one piece of data end-to-end and prove the same data came out the far side.** Nothing owns
  this today on either side. It's their top recommendation for us. `[BL-M01]`
- **Specialist agents get wired in one at a time, by hand.** Both teams hit this independently.
  Neither has built the general solution. `[BL-M02]`
- **We ship 49 skills and only check their formatting** — nothing tests whether they actually work.
  Their research says unevaluated skills can actively hurt. `[BL-M03]`
- **Does the "learn from mistakes" loop actually change anything?** The writing half is genuinely
  working — 269 pages. Whether anything *reads* them back has never been checked. `[BL-M04]`
- **Does the handoff system work on every path?** `[BL-M05]`
- **Our code map knows "defines" and "imports" but not "calls."** `[BL-M06]`
- **Turn code-understanding into something you can ask questions of**, not just a run summary. `[BL-M07]`
- **Review the agents that judge work** and give them explicit scoring standards. `[BL-M08]`
- **Measure how much reference material the orchestrator loads before doing any work.** Theirs was
  51% of the context window, before starting. Ours has never been measured. `[BL-M09]`
- **Nothing proves the model-picking logic actually ran.** `[BL-M10]`
- **Give the coding agent examples of good and bad code for this specific repo.** `[BL-M11]`
- **Add a non-Anthropic model family properly** — related to the Opus fix. `[BL-M28]`
- **Make "assess without changing anything" a repeatable run type** — it's what I did by hand this
  week. `[BL-M29]`
- **Our three mid-run mini-loops each grew their own trigger and were never tuned together.** `[BL-M30]`
- **Run the reproducibility checker over the whole codebase and triage it.** `[BL-M31]`
- **Build a checker that takes every promise in our docs and greps for the code behind it.** Neither
  team has this, and it's the direct answer to the pattern below. `[BL-M32]`

### Record-keeping
- **Note that our scripts-first architecture was externally validated** — they tried the opposite and
  recommend we don't follow. `[BL-M12]`
- **Check our repo for "conversion fossils"** — code that looks live but does nothing. `[BL-M13]`
- **Audit our checkers for a counting bug they found in theirs** (it silently checked only half its
  targets while reporting success). `[BL-M14]`
- **Two subsystem claims we never got round to testing.** `[D2-15, D2-16]`

---

## THE ONE PATTERN BEHIND MOST OF THIS

Nearly every broken thing above has the same shape:

> **The rule is written in a document for the AI to follow. Nothing in code enforces it.**

Every subsystem that *does* have real code behind it came back working. Every one that relies on an
instruction being read and obeyed came back either unverifiable or quietly broken.

We told the other team this exact thing about *their* architecture — that turning a mechanical rule
into prose is a regression. It turns out we have the same problem, just from the other direction:
they converted our code into prose, while we wrote prose we never got round to converting into code.
