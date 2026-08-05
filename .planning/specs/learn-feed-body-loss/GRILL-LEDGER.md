---
spec: learn-feed-body-loss
status: frozen
opened: 2026-08-04
baseline: master `af0be7d` · gauntlet 4/4 PASS · working tree clean
tier: short — the decision was settled by measurement, not by debate
---

# GRILL LEDGER — the publisher silently throws away most of what we write

**In plain terms:** the tool that publishes our decision ledgers to the second brain drops the body of
most entries. It renders the parsed fields *instead of* the body rather than *as well as* it, and our
house style puts the substance in the body. Pages publish as headings with the reasoning missing.

## Phase 0 — measured, not asserted (`af0be7d`, this session)

Ran the **shipped parser and the shipped render condition** over every ledger on disk:

| | |
|---|---|
| ledgers on disk | **22** (`DEF-2` said 19 — three were written today) |
| ledgers that lose content | **10** |
| entries whose body is dropped | **68 of 218** |
| characters lost | **46,427** |

Worst: `session-lifecycle` 25/37 (23,363 ch) · `ungated-protocol-files` 11/12 (8,515) ·
`bump-on-modify` 7/12 (3,948) · `evaluator-dispatch-record` 6/7 (3,545).

**`DEF-2` was right and is now worse than filed.** It measured 20 of 29 entries / 19,153 chars on
`session-lifecycle`; that ledger is now 25 of 37 / 23,363. Three of the ten affected ledgers were
authored today — every "why we rejected the alternative" paragraph in them would publish empty.

**Conductor error, recorded:** the first probe reported **zero** loss everywhere. It read the section
fields off the top level of the entry dict; `render_page:505` nests them under `entry["fields"]`, so
the condition could never fire. Caught by reading `render_page` rather than believing the output — the
same *assume-the-shape* mistake as `_run_git`, `git -M`, and `contract-gate.json` earlier today. **A
probe that returns a clean result is a claim, and claims get verified.**

### The defect, exactly — `tools/learn_feed.py:511-518`

```python
present = [k for k in _SECTION_ORDER if str(fields.get(k) or "").strip()]
if present:
    for k in present: ...render fields...
elif body_text:        # ONLY when NO field parsed
    ...render body...
```

`elif` is the bug. If **any** field parses, the body is discarded. The house style — a bold field
prefix followed by indented sub-bullets — reliably parses *some* field while leaving the substance in
the body, so the branch that drops everything is the one that fires.

## Resolved branches

### LFB-1 — Render the body IN ADDITION to the fields, never instead of · LOCKED

- **Decision:** when both parsed fields and a non-empty body exist, render the fields as today, then
  render the body under its own `## Detail` section. `elif body_text` becomes an independent `if`.
- **The field-less path is preserved unchanged:** when NO field parses, the body still renders under
  `## Decision` (the MM `· LOCKED` form, `learn_feed.py:516-518`). That path is load-bearing for other
  ledgers and must not regress.
- **Rejected — append the body to the Decision section:** conflates an operator's recorded decision
  with surrounding narrative; a reader could not tell which is which.
- **Rejected — change the house authoring style instead:** would require rewriting 22 existing ledgers
  and every future one to suit a renderer bug. The tool is wrong, not the writing.

### LFB-2 — Fix the heading miscount in the same change (`BL-M24`) · LOCKED

- `_HEADING_LINE_RE = re.compile(r"^#{1,6}\s+…")` (`learn_feed.py:123`) counts the ledger's **own H1**
  as an entry, which is why every emit has reported "1 item skipped" forever. Becomes `^#{2,6}`.
- **Same file, same run, one review.** Verified still present at `af0be7d`.

### LFB-3 — No block is needed once the renderer is correct · LOCKED

- **Decision:** the `DEF-2` interim block on grill-close emits is **lifted by the fix**, not carried.
  The block existed only because the blast radius was unmeasured; it is now measured and repaired at
  source.
- **`DEF-2`'s open question — "does the block extend to all 19 ledgers?" — is answered by removing the
  need for a block at all.** Recorded so the question is closed rather than left dangling.

### LFB-4 — Proof is re-measurement, not assertion · LOCKED

- The build must re-run the same measurement and show **68 → 0** dropped entries across the 22
  ledgers, plus a unit test per path: fields-only, body-only (the preserved `## Decision` path),
  fields+body (the new `## Detail` path), and the heading count.
