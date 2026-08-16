---
spec: ux-rework
status: DRAFT — awaiting full grill + convergence gate before freeze
opened: 2026-08-16
sources: GRILL-LEDGER.md (UX-1..UX-20, the ruling record) · launch-template.html · doc-grammar.html · PLATFORM-MATRIX.md
---

# DESIGN (draft) — the KataHarness UX system

**What this is:** the consolidated design for BL-N06 (launcher) + BL-N07 (UX rework), compiled
from the 2026-08-15/16 operator design sessions (browser mockup companion, ~20 iterations). The
per-ruling record with rejected alternatives is `GRILL-LEDGER.md`; the pixel-exact references sit
beside this file. **This draft is NOT frozen** — it still owes the full grill, the convergence
gate, and the open sections at the bottom.

## 1. Identity

- **Palette:** the Hokusai brand (`modules/closeout/resources/BRAND.md`) — Prussian deep `#163A57`
  / mid `#2E6389`, ochre `#B5894B`, rust `#A6532B`, parchment line `#CDBE9B`, foam `#F7F2E6`, on
  the terminal's dark ground. Dark-terminal working tones: pale `#8fb3cc`, blu `#4d87ae`, warn
  `#e5c07b`, ok `#5fd7a7`.
- **The seal:** 改善型 (kaizen-kata — Japanese, kanji) in a filled rust chip. The one Japanese
  mark; kana variants noted, not adopted.
- **The sea (UX-13):** ONE waveform everywhere — open swell, three summed sines
  (2.6/0.10/−2 · 1.2/0.145/−3 · 0.5/0.06/+1, base 4.2, clamp 0.6..8), 48 frames × 135 ms =
  6.48 s seamless loop (integer cycles per component). Frame 0 is the canonical static form.
- **Widths:** generator-asserted, never eyeballed. Launch banner = **64**; dense report pages may
  use **72**; always uniform within a page.

## 2. The grammar (how anything is framed)

> **Boxes are for data · dividers are for prose · scissors are for copy.** Three framings, three
> meanings, no overlap (UX-7, UX-15, UX-20).

- **Breaker hierarchy:** phase transition = the full phase-break block (below) · major topic =
  heavy parchment breaker + ochre title · minor = light dim breaker + pale title.
- **Copy blocks:** ✂-line above and below, label names the destination ("copy below · paste into
  new session"); content lines flush-left, ZERO decoration or leading/trailing whitespace.
- **Stream output:** every harness line carries the Prussian `▏` tick; severity is color only
  (green pass · ochre caution · rust fail).
- **Status dots (UX-17):** ● green done/healthy · ● ochre attention/partial · ● rust
  blocked/failed · ○ dim not-started.
- **Weight discipline:** rust background chips appear ONLY on interruption surfaces; the double
  border (╔═╗) appears ONLY on a human decision gate.
- **Options:** standard CLI `[n]` tokens the user types into the reply, grouped under dim
  mini-headers.
- **Plain language everywhere:** section headers say what they mean (WHAT GOT DONE, not "vitals ·
  the work"); items always named in plain English beside any code.

## 3. The components (locked)

| Component | Reference | Ledger |
|---|---|---|
| **Launch screen** — block KATA foam-to-deep, starfield, seal, animated sea, parchment-border status + commands boxes | `launch-template.html` | UX-2/3 |
| **Phase rail (A2)** — seal chip · ✓done · ochre current chip w/ counts · dim future · detail subline | in break block | UX-9/12 |
| **Phase-break block** — rail → vitals box → animated sea, flush | `gen_*` generators | UX-12 |
| **Vitals** — cumulative-for-run figures (BL-N14 semantics; counters are run STATE, never config) | — | UX-12/16 |
| **Document grammar + agent orientation** — MISSION → GUARDRAILS → CONTEXT → REPORT CONTRACT → YOUR BRIEF (✂ last) | `doc-grammar.html` | UX-15 |
| **Run-start report** — truth-serum: WHAT WILL BE TRUE (incl. explicit NOT-in-this-run) → waves w/ boundary chip → WHAT WILL STOP THIS RUN → config → zeroed vitals → sea → rail | mockups | UX-16, BBM-11 |
| **Interruption surfaces** — escalation (ochre) → gate-rejected (rust verdict) → breakthrough (only full rust frame) | mockups | UX-18 |
| **Closeout** — IN PLAIN WORDS (divider-bound prose) → truth-serum item list → git block wired to menu numbers → four plain-header stat boxes → double-border decision menu as a mini-LOOP ([n] steps repeat until [0] finish) → sea | mockups | UX-19/20 |

## 4. Platform constraints (from PLATFORM-MATRIX.md)

1. **Theme lives in KataHarness-printed frames, never host customization** — Codex/Kiro have zero
   brandable chrome but our dispatch captures their workers entirely.
2. **Animation only where we own the TTY** (wrapper launch, waits, phase breaks we print); the one
   host live region (Claude statusline) refreshes at ≥1 s — static frame-0 sea is load-bearing.
3. **ANSI-in-transcript is unproven on every host** — the grammar must degrade glyph-only (all
   structure is plain UTF-8); probe #1 in the matrix settles it in minutes.
4. Markdown skin is mandatory for desktop/IDE panes and reports.

## 5. Governance

- Launcher mechanism: wrapper scripts default, **gated on a standardness assessment**, alias+hook
  fallback (UX-1). Wrapper obligations: VT enable, UTF-8, color fallback (UX-14).
- "**Wave**" is the official term; never "sprint" (UX-16). Wave-boundary posture is a run-config
  key with per-shape defaults, declared highlighted in run-start (BBM-11).
- Run personas (register per audience) are a future item; all layouts stay persona-neutral
  skeletons (UX-16). Closeout learning options align with the learning graph (BL-N16).

## 6. OPEN — designed nowhere yet (owed before freeze)

launcher secondary screens (help · settings · new-project/run-existing flows) · the guided-start
interview rendering (run-shape, economy, multi-model, fan-out, brain/vault, grill-with-docs,
goal/system-prompt optimization — BBM-5) · per-phase menus · statusline integration spec (the A1
rail string; kata-launched theme variant; 2-line option probe) · the markdown skins · the six
platform probes (matrix §4) · Human Prose / persona integration (BL-N02).

## 7. Build path (indicative, for the eventual PLAN)

The design freezes only after the full grill + convergence gate. Build order candidate: the
grammar renderer (boxes/dividers/rail/sea as a small pure engine — widths asserted like the
mockup generators) → run-start + closeout composition → launcher wrapper (post-assessment) →
statusline integration → interruption surfaces wiring. Every gate/score artifact obeys the
Determinism Doctrine; renderers are pure functions over run state.
