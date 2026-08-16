# templates/ — the pixel-exact UX references (preserved 2026-08-16)

**What these are.** The final approved mockups from the 2026-08-15/16 design sessions AND the
Python generators that produced them. **The generators are the real spec**: every box line is
width-asserted programmatically (64- or 72-column measure), the sea's frames are computed from the
locked waveform (UX-13), and a builder can re-derive any surface byte-exactly by running them.
The HTML files are the approved visual outputs for human reference (open in a browser; the sea
animates via CSS frame-cycling — content-fragment pages, self-contained styles).

| File | Surface | Ledger |
|---|---|---|
| `gen_runstart.py` → `run-start-v3.html` | run-start report (truth-serum outcome, waves + highlighted boundary chip, stops, config, zeroed vitals, sea, rail) | UX-16, BBM-11 |
| `gen_closeout5.py` → `closeout-v6.html` | closeout (divider-bound IN PLAIN WORDS, truth-serum items, git block, `[n]` mini-loop menu) — the four v4 stat boxes noted inline | UX-19/20 |
| `gen_remaining.py` → `remaining-surfaces.html` | guided interview (+/− trade lines) · help · settings (Kiban) · the wave-gate attention composite | UX-21/22/23 |
| `gen_board.py` → `nested-execution.html` | statusline depth chips · the /kata-status run-board tree · transcript lineage tags | UX-25/26 |
| `gen_errors.py` → `interrupts.html` | escalation · gate-rejected · breakthrough (weight ladder; §top waves box superseded by UX-23) | UX-18 |
| `wave-lab.html` | the sea selection round (open swell chosen; components recorded in UX-13) | UX-13 |
| `../launch-template.html` | the LOCKED launch screen (block KATA, starfield, seal, animated sea, parchment-border boxes) | UX-3 |
| `../doc-grammar.html` | the LOCKED document grammar + agent-orientation format | UX-15 |

**Iteration history** (what was tried and rejected, so it is not re-proposed) is recorded in
`../GRILL-LEDGER.md` per ruling. Earlier-round mockups live only in the gitignored
`.superpowers/brainstorm/` workspace — deliberately not preserved; the ledger's rejected-lists are
the durable record.

**Regenerating:** `uv run python <gen_*.py>` from `tools/` writes into the mockup workspace path
hard-coded at each file's bottom — repoint the output path when reusing. The `vw()` width function
(CJK = 2 columns) and the `box()`/`frame()` helpers in these files are the reference
implementations for the eventual grammar renderer (DESIGN §7).
