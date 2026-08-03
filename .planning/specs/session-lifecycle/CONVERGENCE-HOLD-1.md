# CONVERGENCE GATE — PASS 1 · **HOLD** (2026-07-27)

> Fresh-context, no-write adversarial convergence pass over `GRILL-LEDGER.md` (SL-1..SL-18), run per
> the kata-grill RUBRIC's "don't grade your own convergence" backstop. Operator-authorized dispatch.
> **VERDICT: HOLD — 18 findings (9 HIGH · 7 MED · 2 LOW).** The grill is **NOT converged**; SL-1..SL-18
> are not safe to compile into a frozen DESIGN until the HIGHs are resolved.

## What the gate CONFIRMED (Phase-0 grounding held)

`recall.py` has no CLI and only a test importer; the five parsers + `_parse_bullets` + `_guard_path`
exist · `learn_feed.py:118 _FEED_SUBDIR` is a hardcoded constant · `.gitignore:9` ignores `.kata/`
and `git ls-files .kata` is empty · `kata_dash_model.py:211 _derive_phase` is run-scoped ·
`STATE.md` frontmatter is `2026-07-22` · `git log --follow HANDOFF.md` = 65 · the four wiki page
kinds really are siblings of `synthesis`, outside `engram.learnFeed.dir` · `handoff.md:53-64`
(CA-L19) is prose with no implementation · `_REENTRY_TEMPLATE:37-48` carries exactly five `->`
commands. **The measurement work was sound. The convergence bar is what failed.**

---

## 🔴 THREE CLAIMS I MADE THAT ARE FALSE (PD-2 — recorded plainly, author-owned)

1. **SL-9's "free T-04 fix" does not work.** I claimed the floor could verify `RESULT.json`'s
   `resultSha` is an ancestor of HEAD and that this *is* handoff finding #1. The gate **ran it**:
   `git merge-base --is-ancestor 159fc9b HEAD` → **yes**. The stale artifact **passes**. Ancestry is
   a *validity* test, not a *freshness* test. Two further errors in the same entry: the drift is
   **56** commits (`resultSha`) / **61** (`baselineSha`), not 37 (a figure I carried over from the
   handoff without measuring); and `.kata/RESULT.json` has `gateName: advisor-executor-integration`
   over three test files — **it is not the gauntlet**, so citing it as "the last gate run" would
   report `537 passed` where the operator's ground truth is `4/4 PASS`. **SL-5's gate-freshness edge
   is therefore still OPEN**, not resolved.
2. **The LESSONS-LEARNED L10 citation is wrong, and I used it twice as load-bearing rationale.**
   L10 is *"A/B VERDICT: TIE. The execution half is on-par with GSD, not better."* The
   "drift-magnet" phrase lives in **L9**. A real citation attached to a claim it does not support —
   **exactly the PD-2 violation class SL-4 itself defines.** It is the stated ground for rejecting
   token-overlap clustering in SL-12, so that rejection currently has no cited authority.
3. **SL-18(1)'s premise is false.** I wrote *"no real handoff has ever carried its provenance
   fields."* The current `.planning/HANDOFF.md:3-4` carries **both** `kind: manual` and `trigger:`,
   as do its last three commits. I inherited this from the handoff's prose while claiming the
   Phase-0 findings were "verified by reading the code — not inherited from the handoff."

**Also measured wrong:** `DECISIONS.md` is **2734 lines with 2 headings** (`:1` and `:596`), not
"2683 lines, one heading" — my own `^#{2,3}` regex excluded the level-1 heading and `-First 8`
hid the rest. 2 of its 171 bullets use non-`D{n}` anchors (`D-multisession`, `D-registry`). This was
the sole measured ground for SL-13(3).

---

## HIGH findings (all block FREEZE)

| # | entry | finding |
|---|---|---|
| H1 | **SL-10 / SL-8** | The comparator has an **undefined left operand** — nothing says where a "depth write" timestamp is stored or read — and is **not computable over two of its six sources**: `DECISIONS.md` has no frontmatter and no per-entry dates, and `GRILL-LEDGER.md` has none either, so both parse to `date=None`. Builders diverge to *opposite freshness verdicts on identical state*. |
| H2 | **SL-9** | The T-04 claim is false (above). SL-5's "cite-with-staleness **or** re-run" question is never answered — one builder re-runs the 146 s gauntlet on every write (blocking the auto-compact crossing SL-5 exists to survive), another ships a floor reporting a 2026-07-20 partial gate as current green. |
| H3 | **SL-3 / SL-8** | The FLOOR/DEPTH contract **silently deletes `Read-in order`** — required section 1 of the existing schema — yet **SL-8's entire rationale for demoting `kata-orient` depends on it**. `§4` (WHERE EVERYTHING IS) vanishes with no statement; "suggested next skills" is never explicitly deleted or made optional; numbering mixes ordinals and letters, skipping 4 and 8, with no stated order. |
| H4 | **SL-6 / SL-7 / SL-13(2)** | The depth journal — sole home for `§2` and `§7`, the two sections SL-3's own provenance credits with making the handoff work — has **no cadence, no format, no filename, no named writer**. SL-6 declared these open; SL-13(2) answered only location. So SL-7's stated purpose (not relying on the model remembering) is **unmet for exactly the sections it journals**. Worse: **D81 makes tier-3 `.kata/` a disposable cache rebuilt from the git trail** — a journal holding the only copy of model-authored narrative is either lost on rebuild or violates the tier model. |
| H5 | **SL-12** | Subject identity is called "mechanical" but derives from `Doc-baked`, a field **no parser reads** (`learn_feed._FIELD_PREFIXES` omits it; the code comment names this exact case), whose values are free prose, and which reads **"pending" in 8 of 18 entries**. Extracting an artifact from that is judgment, not a rule — and it fixes a *durable artifact's identity*, which the Determinism Doctrine requires be reproducible. **"≥2 distinct initiatives" is never defined operationally**; `DECISIONS.md` D-numbers belong to no spec dir at all. |
| H6 | **SL-7 / SL-10** | `GRILL-LEDGER.md` is named as a source **by bare filename** — there are **19** in `.planning/specs/`, and no state records which is current (SL-1's own premise). One builder globs all 19 and floods `§3` with hundreds of entries; another picks newest-mtime, non-deterministic on a fresh clone. Same ambiguity for board vs the **four** `board.*.archive.md` files. |
| H7 | **SL-3 / SL-4** | **No module is named as the floor's writer** — the central new build artifact is unowned, while every other decision names its file. And SL-4 defers "where the checks live (validator vs review vs gate)" while its edges assert "gate fails. Not a judgment call." **Gate-vs-advisory is the most consequential bit in SL-3/SL-4 and the ledger answers it both ways.** |
| H8 | **SL-11** | (a) The rollup `INDEX.md` has **no content contract at all** — no fields, ordering, generator or trigger — against SL-11's own determinism edge. (b) "Migration is optional" **contradicts the emitter's recorded precedent**: `learn_feed.py:44-49` documents that a prior relpath change ORPHANED old pages and that idempotency is per-filename, so re-emits write *beside*, not over. **This project already paid for this lesson.** |
| H9 | **SL-12 / SL-17** | Both make `git log --follow` load-bearing, but **DETERMINISM-DOCTRINE law 1 pins `log.follow=false`** in the shared helper, with two live enforcement sites (`contract_gate.py:150`, `kata_restore.py:502`) and a test asserting the pin. `--follow` appears **nowhere** in the codebase. It is also rename-heuristic dependent, so it is not reproducible — and SL-12 uses it to fix a durable identity. SL-17's "arc is already free" is an **uncited reuse claim**. |

## MED findings

`N` pinned to a private format-string constant with no extraction mechanism, and the `≥N lines`
check is a count orthogonal to content — five well-formed fabricated lines pass (**the KH-T02 defect
class SL-4 exists to prevent**) · the L10 mis-citation (above) · the `DECISIONS.md` mis-measurement
(above) · SL-18(1)'s false premise (above) · **`§7` now has two meanings** — "what I got wrong"
(SL-3) vs redaction (SL-16's edge, and normatively `protocol/engram.md:153-155`), in a grill whose
RUBRIC mandates glossary canonicalization · **SL-16 over-claims a gap**: `learn_feed.render_page`
already requires `scope`, hard-fails on unknown values, and emits the full contract — and SL-16's
redaction edge **contradicts D151** (`engram.md:160-165`: for the loop feed the scrub *never blocks
emit*) · **entries marked `· LOCKED` still carry OPEN edges** (SL-1 verbatim *"(OPEN — to be defined
in Phase 1 before this entry is complete)"* with no forward pointer to SL-13/SL-18 which do close
them; SL-3's `§R` *"(To confirm in Phase 1.)"* never confirmed — and its content is undefined at the
very crossing SL-3 exists for) · `DEFERRED.md`'s parseable date is the heading's **creation** date
(`DEF-1 · OPEN (2026-07-21)`) while the body records a **2026-07-25** re-assignment — the exact
blindness SL-10 exists to remove; and SL-13(2) never says **which** `.kata/` (integration root vs
per-task worktree), an ambiguity `protocol/board.md:13-14` found load-bearing enough to spell out.

## LOW findings

SL-2's Doc-baked cites `protocol/handoff.md:41-43` for a wiki boundary; those lines are CA-L21(1)
and concern dispatch briefs/worker reports/escalation payloads — they say nothing about the wiki
(SL-9 cites the same lines *correctly* for a different claim) · `learn_feed._parse_heading_entry`
truncates the title at the **first** status token, so `### SL-10 — … · LOCKED · supersedes CA-L19`
emits with **"supersedes CA-L19" silently discarded** — losing exactly the C5 lineage SL-10 exists
to preserve.

---

## Disposition

**The grill returns to Phase 1.** Per the RUBRIC, only a SHIP closes a grill; this HOLD names the
under-specified branches above. No entry here is compiled into a DESIGN until its finding is
resolved and a second convergence pass returns SHIP.

**Not re-litigated:** the gate's findings stand as written. Where a finding says a claim of mine is
false, it is false.
