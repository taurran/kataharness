---
spec: ux-rework
status: draft
opened: 2026-08-15
tier: pre-design operator rulings (launcher + UX rework, BL-N06/BL-N07; visual-companion session)
---

# GRILL LEDGER — launcher + UX rework (BL-N06 / BL-N07)

**What this is:** operator rulings from the 2026-08-15 visual design session (browser mockup
companion, ~10 iterations). The launch-screen TEMPLATE IS AGREED — see `LAUNCH-TEMPLATE.md` +
`launch-template.html` beside this file (the pixel-exact reference). Full grill + DESIGN still owed
before building.

## Operator rulings (2026-08-15)

- **UX-1 · Launcher mechanism — wrapper scripts by default, assessment-gated.** `kata-claude` /
  `kata-codex` / `kata-kiro` as PATH-installed wrapper executables (print the branded screen
  pre-model at zero token cost, verify the environment, exec the host). **Gated on a deep
  assessment**: is a PATH wrapper an available/standard pattern per host and per OS? **Fallback
  where the assessment finds a difference: shell aliases + host startup hooks.** The assessment is
  an explicit early task, not an assumption.

- **UX-2 · Launch screen content (all zero-token, knowable pre-model):** branded wordmark ·
  version + **update check against the GitHub repo** (rides the updater's ls-remote machinery;
  MUST be fail-soft — an offline launch never blocks or errors) · environment health line ·
  resumable-run status · second-brain/vault status · recent-activity line · command menu.

- **UX-3 · The agreed visual template** (iterated live; reference files beside this ledger):
  - **Wordmark:** block-slab KATA (the classic ANSI shadow letterforms — an Onari-style
    faux-Japanese alternative was rendered and REJECTED for readability; "not too bad" = revisit
    permitted, not planned) + mini-font HARNESS, colored **foam→deep**: crest-white at the top
    sinking through pale/mid blue to Prussian dark (Hokusai palette per
    `modules/closeout/resources/BRAND.md`).
  - **Seal:** 改善型 in a filled rust block (`#A6532B` bg, foam text) beside HARNESS. The mark is
    JAPANESE (kanji): 改善 kaizen + 型 kata — operator questioned Chinese-vs-Japanese 2026-08-15;
    resolved: kanji shared glyphs, the word is the brand's own. Kana variant (カイゼン) noted as the
    unmistakably-Japanese option, not adopted.
  - **Sky:** random starfield right of the wordmark, three magnitudes (foam ✦ / mid-blue ✧⋆ /
    faint ·˖). A stars-over-Fuji variant was rendered and passed over in favor of stars-only.
  - **Sea:** a full-width (64-col) rolling-swell line — trough Prussian, crest tips foam — sitting
    FLUSH against the boxes (no blank lines).
  - **Deck:** two fully-enclosed box-drawing boxes on the dark ground (parchment FILLS tried and
    REJECTED), borders in the **parchment line tone** (`#CDBE9B`, the BRAND border token) with
    **ochre box titles** (`#B5894B`) — amended from slate on 2026-08-15, operator: "lock A" —
    `status` (4 dense lines: version+update · env · resumable · brain/vault/last-run) and
    `commands` (8 lines, name + plain description columns).
  - Rejected along the way (do not re-propose): brush/katakana hand glyphs · full wave scene ·
    parchment page background · parchment box fills · hanko/cartouche ornaments beyond the one seal.

- **UX-4 · Command copy that survived a real confusion:** `/kata-loop` = *"full cycle: build →
  closeout → improve again"*; `/kata-start` = *"single run: plan and build once, then stop."* The
  operator could not tell them apart from the earlier copy — treat entry-command comprehension as a
  gate on any future command surface.

- **UX-5 · OPEN QUESTION (feed to the full grill):** should the LOOP be the only door — "single
  run" becoming a choice inside the guided flow — so users never face two entry commands? Interacts
  with BBM-5 (guided `/kata-start` is burn's primary path) and the /kata-settings future (BL-N05,
  already shown on the template as the intended state).

## Remaining UX agenda (operator-listed 2026-08-15, untouched this session)

statusline capabilities per host (kata segment exists on Claude; codex/kiro need assessment) ·
per-phase menu items · cursor/progress tracking components · run start/end reporting ·
copy/paste block formatting (agent orientation + command blocks as a first-class grammar) ·
CLI vs Claude Code app rendering (the app pane renders markdown, not ANSI — every template needs a
markdown skin).
