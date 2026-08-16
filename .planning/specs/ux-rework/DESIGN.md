---
spec: ux-rework
status: DRAFT — freeze-candidate, awaiting convergence gate
opened: 2026-08-16
compiled: 2026-08-16
revision: 2 (post CONVERGE-HOLD; conductor-ruled interims labeled inline)
sources: GRILL-LEDGER.md (UX-1..UX-32, the ruling record) · PLATFORM-MATRIX.md (UX-11; probe 1 RESOLVED §3.1) · templates/README.md + the gen_* generators and committed HTML outputs (the pixel-exact spec) · launch-template.html · doc-grammar.html · modules/closeout/resources/BRAND.md · .planning/BACKLOG.md (BL-N04/N05/N06/N07/N14/N16)
---

# DESIGN (freeze-candidate) — the KataHarness UX system

**What this is:** the consolidated design for BL-N06 (launcher) + BL-N07 (UX rework), compiled
from the 2026-08-15/16 operator design sessions (browser mockup companion, ~20 iterations) and the
2026-08-16 freeze-grill rulings (UX-28..32). The per-ruling record with rejected alternatives is
`GRILL-LEDGER.md`; the pixel-exact references sit beside this file (`templates/` — the committed
HTML outputs plus their width-asserted generators). **This draft is NOT frozen** — it owes the
convergence gate (§8). Claims cite their ruling (UX-n / BBM-n); anything the ledger did not rule
is labeled **[author-proposed]**; interim calls the conductor made during convergence are labeled
**[author-proposed, conductor-ruled interim — operator confirms at freeze]**.

## 1. Identity

- **Palette:** the Hokusai brand (`modules/closeout/resources/BRAND.md`) — Prussian deep `#163A57`
  / mid `#2E6389`, ochre `#B5894B`, rust `#A6532B`, parchment line `#CDBE9B`, foam `#F7F2E6`, on
  the terminal's dark ground. The full role table, compiled from the approved templates' locked
  CSS, is §2.3.
- **The seal:** 改善型 (kaizen-kata — Japanese, kanji) in a filled rust chip (`#A6532B` background,
  foam text). The one Japanese mark; kana variants noted, not adopted (UX-3).
- **The sky:** random starfield right of the wordmark, three magnitudes (UX-3). Rendering is
  **seeded-RNG** — fixed seed, same bytes every launch, per Determinism law 9 **[author-proposed]**.
- **The sea (UX-13):** ONE waveform everywhere — open swell, three summed sines
  (2.6/0.10/−2 · 1.2/0.145/−3 · 0.5/0.06/+1, base 4.2, phases 0/1.1/2.4, clamp 0.6..8), 48 frames
  × 135 ms = 6.48 s seamless loop (integer cycles per component). Frame 0 is the canonical static
  form (UX-13) — and the form most surfaces actually show, since animation exists only where
  KataHarness owns the TTY (UX-14; matrix §3.2).
- **Widths:** generator-asserted, never eyeballed (UX-12/19). Launch banner = **64**; dense report
  pages may use **72**; always uniform within a page. The engine (§5) asserts widths at runtime,
  with the data-overflow policy of §5.

## 2. The grammar (how anything is framed) — ONE theme, GLYPH-FIRST

The locked launch template's language — Hokusai palette, parchment borders, block grammar —
carries across EVERY surface: clearly visible blocks throughout, never walls of undifferentiated
text (UX-6).

> **Boxes are for data · dividers are for prose · scissors are for copy.** Three framings, three
> meanings, no overlap (UX-7, UX-15, UX-20).

### 2.1 The primary form is glyphs, not color (UX-30)

Probe 1 proved ANSI color is STRIPPED in the Claude Code transcript while UTF-8 glyphs render
clean (PLATFORM-MATRIX §3.1, LP 2026-08-16 n=1). The ruling: **every transcript surface is
glyph-first** — all meaning is carried by structure and glyph, with color as a progressive
enhancement applied ONLY where KataHarness owns the rendering (§2.3). The glyph form is not a
degradation of a color design; it IS the design. Concretely:

- **All structure is plain UTF-8** — box-drawing frames, rails, breakers, the ▏ tick, the static
  sea — rendering clean on every monospace surface tested so far (the n=1 transcript probe plus
  the UTF-8 glyphs already live in the statusline) (UX-30, UX-27; matrix §2).
- **Severity/status is carried by the full glyph set — ✓ ⚠ ✗ ● ○** (UX-17, UX-27, UX-30), with a
  stated role split: **✓/⚠/✗ carry OUTCOME states · ● carries live/in-progress status · ○
  not-started.** On glyph-only surfaces a bare colored-status ● is ambiguous, so where UX-17
  dot-grammar surfaces render glyph-only, outcome disambiguation uses the ✓/⚠/✗ prefix beside the
  dot. **[author-proposed, conductor-ruled interim — operator confirms at freeze]**
- **Breaker hierarchy (UX-15):** phase transition = the full phase-break block (UX-12) · major
  topic = heavy breaker + title · minor = light breaker + title. The hierarchy is legible from
  glyph weight alone; color (parchment/ochre/pale) layers on owned surfaces.
- **Block spacing:** blocks within a composite sit FLUSH — no blank line — as the phase-break
  block's rail/box/sea and the launch screen's sea-against-boxes already lock (UX-12, UX-3); ONE
  blank line separates sibling top-level blocks. Generalized rule **[author-proposed]**.
- **Stream output:** every harness line carries the `▏` tick (UX-15); worker lines add the lineage
  tag `[W1.1]` (UX-26). Line order: **▏ · lineage tag · severity glyph · content** — e.g.
  `▏[W1.1] ✓ …` **[author-proposed]**. On owned surfaces severity is additionally color (UX-15).
- **Copy blocks (UX-7):** ✂-line above and below, label names the destination ("copy below ·
  paste into new session", UX-15); content lines flush-left, ZERO decoration or leading/trailing
  whitespace. Paste fidelity beats border aesthetics.
- **Weight discipline:** rust chips/fills appear ONLY on interruption surfaces (UX-18; the 改 seal
  is the standing exception — a brand mark, not a severity); the double border (╔═╗) appears ONLY
  on a human decision gate (UX-19); paired warn rules appear ONLY on the wave-gate composite
  (UX-23).
- **Options:** standard CLI `[n]` tokens the user types into the reply, grouped under dim
  mini-headers (UX-20 — superseding UX-19's numbered filled chips).
- **Plain language everywhere:** section headers say what they mean (WHAT GOT DONE, not "vitals ·
  the work"); items always named in plain English beside any code (UX-19, UX-24).

### 2.2 The markdown skin (UX-27)

For markdown-only surfaces (desktop/IDE panes, PR bodies, reports): structure survives verbatim
inside fenced code blocks (box-drawing, glyphs, the static sea frame); color degrades to the same
glyph prefixes; chips become **bold** tokens. One skin, defined once; per-component mappings
enumerated at build time. Since UX-30, the skin and the transcript form are the SAME grammar —
the skin is no longer a special case, just the fenced-block carrier of the primary form.

### 2.3 The color-role tokens (UX-8, fixed here) — owned-rendering surfaces ONLY

Color applies on exactly three surface classes: **wrapper-owned TTY screens, captured worker
consoles, and the Claude Code statusline** (UX-30, matrix §3.1/§3.3). One table, one system — no
per-surface improvisation (UX-8). The hexes below are **compiled from the locked CSS the operator
approved — identical across all five generators/templates** (gen_runstart / gen_closeout5 /
gen_remaining / gen_board / gen_errors and their committed HTML). The role naming and assignment
as a whole remain **[author-proposed]** for the operator at the gate.

| Role | Dark-ground hex (locked template CSS) | Usage (on owned surfaces) | Glyph-first degradation |
|---|---|---|---|
| `structure` | `#CDBE9B` parchment | box borders, rails, breakers, dividers, table rules (the BRAND border token, unchanged on dark) | the box-drawing characters themselves — structure is already glyph |
| `title` | `#d9a960` ochre (chip fill likewise); brand `#B5894B` on light surfaces | box titles, major-topic breaker titles, current-phase chip fill (UX-12) | UPPERCASE title text; **bold** in the markdown skin |
| `action` | `#4d87ae` blu | command names, `[n]` option tokens, paths/links | the `[n]` bracket token itself; backtick spans in markdown |
| `value` | `#F7F2E6` | figures, values, item identifiers | plain text — position in the grammar carries the meaning |
| `text` | `#a9b1c3` | prose/body lines on the dark ground | plain text |
| `header` | `#8fb3cc` pale | headers, secondary labels, minor-breaker titles | plain text |
| `ok` | `#5fd7a7` green | pass/done lines and dots, benefit sub-lines (UX-21) | ✓ prefix (beside the ● where a dot surface goes glyph-only, §2.1) |
| `warn` | `#e5c07b` (also the wave-gate ⏸ chip fill, UX-23) | attention/partial dots, wave-gate warn rules, tradeoff sub-lines (UX-21), caution stream lines | ⚠ prefix (same dot rule) |
| `fail` | `#c2653a` as TEXT; `#A6532B` as chip/seal BACKGROUND only | blocked/failed dots and text, gate-rejected verdict chip, the breakthrough frame, backout — chips/fills interruption-only (UX-18) | ✗ prefix (same dot rule) |
| `deep` | `#163A57` / `#2E6389` | wordmark depth gradient, sea trough, the ▏ tick, statusline bands (UX-25) | the ▏ tick glyph itself |
| `dim` | `#565f74`, plus the `#44607a` dim-blue variant | de-emphasis: metadata, mini-headers, future phases; dim-blue: ○ not-started, dim rules | ○ dot; trailing/parenthesized placement |

Supporting tints from the same locked CSS: `foam #F7F2E6` (primary/crest — shares the value hex)
and `#cfd8d3` (the rail's done-phase label tint).

Notes for the gate: (a) **On the dark terminal ground all three earth tones LIGHTEN for
legibility** — ochre `#B5894B → #d9a960`, rust `#A6532B → #c2653a` (as text; `#A6532B` retained
as background fill), with `#e5c07b` the yellow member of the family; light surfaces (the BRAND.md
report) keep the brand hexes **[author-proposed reconciliation, from the approved templates]**.
(b) 24-bit → 256-color fallback per hex is a wrapper obligation (UX-14); the fallback table lives
in the engine (§5) so every renderer shares it **[author-proposed placement]**.

## 3. The components (locked)

| Component | Reference | Ledger |
|---|---|---|
| **Launch screen** — block KATA foam-to-deep, starfield, seal, animated sea, parchment-border status + commands boxes | `launch-template.html` | UX-2/3 |
| **Phase rail (A2)** — replaces the old top status-bar block (recorded WRONG — a bar-plus-input-field surface, removed); carries the named phase sequence initiate → grill → freeze → plan → execute → gate → close: seal chip · ✓done · ochre current chip w/ counts · dim future · detail subline | in break block | UX-9/12 |
| **Phase-break block** — rail → vitals box → animated sea, flush, 64 cols | `templates/gen_*` | UX-12 |
| **Vitals** — cumulative-for-run figures (BL-N14 semantics; counters are run STATE, never config); split **direct + nested** under fan-out | — | UX-12/16/26 |
| **Document grammar + agent orientation** — MISSION → GUARDRAILS → CONTEXT → REPORT CONTRACT → YOUR BRIEF (✂ last) | `doc-grammar.html` | UX-15 |
| **Run-start report** — truth-serum: WHAT WILL BE TRUE (incl. explicit NOT-in-this-run) → waves w/ boundary chip → WHAT WILL STOP THIS RUN → config → zeroed vitals → sea → rail | `run-start-v3.html` (see §5 generator-drift note) | UX-16, BBM-11 |
| **Branded execution output** — worker/dispatch/gate output carries the theme (▏ tick, lineage tags, breakers, phase markers, color roles on captured consoles), never raw tool spew | engine-rendered (§5) | UX-10, UX-26 |
| **Interruption surfaces** — escalation (ochre) → gate-rejected (rust verdict) → breakthrough (only full rust frame) | `templates/gen_errors.py` → `interrupts.html` | UX-18 |
| **Guided-start interview** — progress rail · one-question context boxes · auto-skip · one +/− trade line per option. Platform honesty: on Claude the host question UI renders the choices; our frame is the context around it | `templates/gen_remaining.py` | UX-21 |
| **Help + settings** — plain-explanation-first help; numbered-loop settings; vault (Kiban) persistence stated | `templates/gen_remaining.py` | UX-22, UX-24 |
| **Wave gate** — attention composite: paired warn rules + ⏸ chip → wave map → animated sea → double-border menu | `templates/gen_remaining.py` | UX-23, BBM-11 |
| **Run board** — /kata-status tree: hierarchical IDs, depth rollups, lineage tags, ownership line ("all owned"); statusline depth chips | `templates/gen_board.py` | UX-25/26 |
| **Closeout** — IN PLAIN WORDS (divider-bound prose) → truth-serum item list → git block wired to menu numbers → four plain-header stat boxes → double-border decision menu as a mini-LOOP ([n] steps repeat until [0] finish) → sea. **Stat boxes: layout locked by UX-19 prose (WHAT GOT DONE · WHO DID THE WORK · QUALITY AND COST · WHAT WE LEARNED); pixel reference LOST** — the v4 rendering lived in gitignored scratch and `gen_closeout5.py` carries only a placeholder comment; reconstruction owed, operator re-approval required (§8) | `templates/gen_closeout5.py` → `closeout-v6.html` | UX-19/20 |

### 3.1 The closeout decision menu — the full option set (UX-19/20)

Every entry is real machinery; groups are **LOOK DEEPER / GIT / GO AGAIN / WRAP UP** (UX-20):

- **Understand-map** (`kata-understand`; its broken graph command is BL-X03 — the fix rides this
  batch and is being built in burn-02 right now).
- **Full report** — `.kata/closeout.html`, print-ready → PDF; a dedicated PDF export is a
  candidate item, not promised.
- **Go again on THIS repo** — the loop-back re-enters `kata-initiate` carrying context, with the
  grill dial inline (full / standard / light / **skip = fast reiterate**, the existing D71 rung —
  ONE door, ONE dial, no third onramp).
- **Different shape on this repo.**
- **New repo — end here, `kata-handoff` first (recommended).**
- **Ship** — push / open PR / merge-after-PR as menu items, so shipping is part of the same loop,
  not a side quest (UX-20).
- **Clean backout** (rust).
- **Satisfied / end** — `[0]` finish, directing the user to recycle the session or exit (UX-20).

Loop behavior: pick a number → the action executes → a SHORT status line prints → the menu
returns (short form) → repeat, until a new run launches or `[0]` (UX-20). Learning options align
with BL-N16: the WHAT WE LEARNED box and the learning-session menu options (apply learning
guidance · review all learning applied this run) are one surface (UX-20 addendum).

## 4. The launcher — wrappers as the preferred door (UX-28/31/32)

### 4.1 Entry hierarchy (UX-28)

Both in-session commands stay — `/kata-loop` ("full cycle: build → closeout → improve again") and
`/kata-start` ("single run: plan and build once, then stop"), the UX-4 copy that survived a real
confusion; entry-command comprehension is a standing gate on any future command surface (UX-4).
But the **preferred door is the wrapper shell commands** — `kata-claude` / `kata-codex` /
`kata-kiro` — because only the wrapper can act BEFORE the host starts. The guided flow stays
reachable from every door; no door is removed (UX-28, closing the UX-5 open question).

### 4.2 What the wrapper does (four jobs, in order)

1. **Branded launch screen at zero token cost** (UX-2/3): wordmark · version + GitHub update
   check (rides the updater's ls-remote machinery, MUST be fail-soft — an offline launch never
   blocks or errors) · environment health line · resumable-run status · vault (Kiban) status ·
   recent-activity line · command menu. Rendered by the engine (§5).
2. **Terminal obligations** (UX-14): enable VT processing on legacy conhost (SetConsoleMode),
   force UTF-8 out (chcp 65001 / Console.OutputEncoding), detect 24-bit color and fall back to
   256-color approximations.
3. **Environment provisioning** (UX-28): load the launch-time preload set — MCP servers, skill
   packs, agentic files — through the preload seam (§4.3), per host, before exec.
4. **Exec the host**, setting a wrapper env marker our own statusline script reads
   ("kata-launched session" theming, UX-25) — the mechanism is our code on both sides and rated
   trivially available, but is **UA (unverified assumption)** per the matrix until built.

### 4.3 The preload seam — open, config-driven, third-party-independent (UX-32)

Which packs load is **configuration, never hard-wired** — the seam is a pluggable ingestion
point. Near term it ingests the CURRENT third-party superpowers pack **as a placeholder only**.
The standing direction is the independence doctrine (BL-N04 ruling, 2026-08-16): **KataHarness
divests from ALL third-party module components — superpowers and GSD included**; third-party
packs are reference/placeholder material, never load-bearing harness components; the kata-native
superpowers set (the BL-N04 "KataHarness Superpowers" vehicle) replaces the placeholder over
time, and **the swap must be a config change at the seam, not a rework**. Seam config shape
(keys, per-host pack lists, where it lives relative to `kata.config`) is **[author-proposed to
be settled at the eventual PLAN, within the UX-32 constraint]**.

### 4.4 The gating pre-task: the standardness assessment (UX-1, widened by UX-28/31)

The wrapper build is **gated on a deep assessment**, an explicit early task, not an assumption
(UX-1): per host AND per OS — (a) is a PATH-installed wrapper an available/standard pattern; (b)
what are the per-host **environment-injection mechanisms** (Claude: settings/`--mcp-config`-class
surfaces; Codex/Kiro equivalents — **assess, do not assume**) (UX-28). **All three hosts are
assessed and built together in one pass** — the assessment is a single deliverable covering
`kata-claude`/`kata-codex`/`kata-kiro` before any wrapper builds (UX-31). **Fallback where the
assessment finds a difference: shell aliases + host startup hooks** (UX-1). The user-facing
surface for what the wrapper provisions belongs with BL-N05's settings screen
**[author-proposed routing]**.

## 5. The grammar-renderer engine — one small committed module (UX-29)

The only new **engine module** this spec adds; the wrappers additionally carry a thin Python
entrypoint shim (§4.2) — that split honors UX-29's "only new Python" intent by scope: rendering
logic lives in ONE module, everything above it is skill-prose calling it.

**What the generators actually are (verified on disk):** the five `templates/gen_*.py` emit
HTML `<span>` runs, in five divergent copies with incompatible signatures (W=64 vs 72; `box()`
arities differ per file). Literal promotion of that code cannot produce a terminal renderer.
**Shape (preserving the operator's UX-29 intent — one small engine, widths asserted):** the
engine implements the SAME `box()`/`frame()`/`vw()` (CJK = 2 columns)/sea SEMANTICS fresh, with
**multi-form output — glyph-first text · ANSI · markdown fence · html** — specified from the
ledger + templates; the generators become **GOLDEN FIXTURES**: their committed HTML outputs are
conformance targets the engine's html form must reproduce, not import sites.
**[author-proposed, conductor-ruled interim — operator confirms at freeze]**

- **Pure render, impure caller.** Renderers are pure functions over run state — no I/O, no clock,
  no environment reads inside them; same input, same bytes (Determinism Doctrine; the starfield
  is seeded-RNG, §1). All data gathering is the CALLER's job — skills, the conductor, and the
  wrapper shim (which gathers version/env/vault data, then calls the engine) sit on the impure
  side of the line.
- **Width policy — authored vs. data** **[author-proposed, conductor-ruled interim — operator
  confirms at freeze]**: AUTHORED/structural strings (titles, labels, borders, fixed copy) are
  width-ASSERTED — a violation RAISES, because it is a bug; VARIABLE data fields (worker names,
  SHAs, paths, item titles) declare a per-field truncation and the engine TRUNCATES with a
  trailing `…` at the measure — it never raises on data. The engine never ships a crooked frame
  either way (UX-29).
- **Everything above the engine is skill-prose calling it** — which surface, what content, when,
  stays in skills; the engine only renders (UX-29). In-context rendering and a boxes-only hybrid
  were considered and REJECTED (drift-certain; two-author artifacts) — do not re-propose.
- The 256-color fallback table (§2.3 note b) lives here. Module name (e.g. `tools/kata_grammar.py`)
  settled at PLAN **[author-proposed]**.
- **Generator drift, disclosed:** all five generators write to gitignored scratch paths
  (`.superpowers/brainstorm/…`), and `gen_runstart.py` produces **v2** while the approved
  committed artifact is `run-start-v3.html` — the committed HTML, not the generator, is the
  approved reference where they diverge. "Repoint the output paths + regenerate the committed
  outputs" is a build-path step (§9.1) so the golden fixtures are reproducible.
- **Erratum (not edited here):** `templates/README.md` points at "DESIGN §7" for the eventual
  grammar renderer; after this revision the engine section is §5.

## 6. Platform constraints (PLATFORM-MATRIX.md; probe 1 RESOLVED)

1. **Theme lives in KataHarness-printed frames, never host customization** — Codex/Kiro have zero
   brandable chrome, but our dispatch captures their workers entirely, so 100% of the worker
   execution view is conductor/wrapper-rendered (matrix §3.3).
2. **ANSI color in the host transcript is SETTLED: stripped** on the primary host (probe 1, LP
   2026-08-16 n=1, Windows Terminal — both assistant text and tool output; glyphs render clean).
   Hence glyph-first (§2.1) is the floor everywhere; color only where we own the rendering
   (UX-30, matrix §3.1). The Codex TUI ANSI-passthrough probe (3) remains open but no longer
   gates the design; there is NO Kiro transcript probe — the Kiro-transcript question is covered
   by the glyph-first floor, not by a probe. A Mac Claude Code cross-check is a cheap
   non-blocking follow-up.
3. **Animation only where we own the TTY** (wrapper launch, waits, phase breaks we print); the one
   host live region (Claude statusline) refreshes at ≥1 s — the 135 ms sea can never run there;
   static frame-0 sea is the load-bearing artifact (UX-14, matrix §3.2).
4. **Markdown skin is mandatory for desktop/IDE panes** regardless of probe 2's outcome (matrix
   §2 — panes render markdown, not a terminal), and for PR bodies and reports on every host.
5. **Statusline is single-line until probe 6 passes** — the 2-line variant (double real estate for
   the phase rail) rides the multi-line/`refreshInterval` probe (UX-25, matrix §4.6).
6. **No kata hooks registered on Kiro until probe 4** re-verifies Kiro hook stdout
   user-visibility and the #5527 auto-compact hard-fail on a live install (matrix §4.4; the repo
   already mandates the re-verify). **Kiro headless dispatch flags re-verified before the wrapper
   build** (probe 5, the standing confirm-probe).

## 7. Governance

- Launcher: wrapper scripts preferred door, **gated on the §4.4 standardness assessment**,
  alias + hook fallback (UX-1/28). Wrapper obligations per UX-14. All three hosts one pass (UX-31).
- "**Wave**" is the official term; never "sprint" (UX-16). Wave-boundary posture is a run-config
  key with per-shape defaults, declared highlighted in run-start (BBM-11).
- **Naming discipline (UX-24):** internal codenames NEVER appear on user surfaces — plain terms
  ("KataHarness", "the harness") only. **The vault is Kiban.**
- Run personas (register per audience) are a future item (BL-N02); all layouts stay
  persona-neutral skeletons + swappable prose (UX-16).
- Closeout learning options align with the learning graph (BL-N16), per §3.1.
- Vitals semantics are BL-N14's: cumulative-for-run at print time; counters are run STATE
  (`.kata/`), never config; direct + nested split (UX-26). Metric NAMES and the confidence-chip
  derivation are BL-N14 grill candidates, not frozen here (UX-19).
- Every gate/score artifact obeys the Determinism Doctrine; renderers are pure functions (§5).

## 8. OPEN — owed before freeze

Honestly still open — nothing else:

1. **The convergence gate itself (D169)** — this document is its input, including every
   [author-proposed] and [conductor-ruled interim] label above (§2.1 dot role-split · §5 engine
   shape and width policy · §2.3 role table + earth-tone note · §1 seeded starfield · §2.1
   spacing + stream-line order · §4.3 seam-config deferral · §4.4 settings routing).
2. **The four closeout stat boxes — pixel reference LOST** (§3): layout locked by UX-19 prose;
   the v4 rendering is gone with the gitignored scratch; reconstruction owed, **operator
   re-approval required**.
3. **Platform probes 2–6** (matrix §4) — **non-blocking**, each with its conservative default
   already designed in: probe 2 (pane statusline/hook visibility) → markdown skin mandatory, no
   ANSI, no live region assumed (§6.4); probe 3 (Codex TUI ANSI passthrough) → glyph-first floor
   covers both outcomes (§6.2); probe 4 (Kiro hook stdout visibility + #5527) → no Kiro hooks
   until probed (§6.6); probe 5 (Kiro headless flags) → re-verify before the wrapper build
   (§6.6); probe 6 (multi-line statusline) → single-line until it passes (§6.5). Plus the
   non-blocking Mac Claude Code transcript cross-check (§6.2).
4. **Deferred-to-PLAN details:** preload-seam config shape (§4.3) · engine module name (§5) ·
   per-component markdown-skin mappings (§2.2, enumerated at build time).
5. **Run personas / Human Prose integration** — out of scope, lives at BL-N02 (UX-16).
6. **BL-N14 metric names + confidence derivation** — grilled at BL-N14, not here (§7).

All SURFACES are designed as of 2026-08-16 (ledger closing note), with the §8.2 stat-box caveat.
Naming discipline UX-24 binds every one.

## 9. Build path (indicative, for the eventual PLAN)

The design freezes only after the convergence gate. Order:

1. **The engine first (UX-29)** — implement the box/frame/vw/sea semantics fresh with the four
   output forms (§5), width assertions raising on authored strings, per-field truncation on data,
   pure, tested; **repoint the generators' output paths and regenerate the committed HTML** so
   the golden fixtures are reproducible, resolving the run-start v2/v3 drift (§5); conformance-
   test the engine's html form against them.
2. **The standardness assessment (UX-1/28/31)** — one deliverable, all three hosts × OSes,
   wrapper pattern + environment-injection mechanisms. **Gates step 4.** Can run in parallel with
   step 3.
3. **Surface composition via the engine** — run-start + closeout first (the truth-serum
   bookends, incl. the §3.1 menu loop), then the phase-break block + rail (UX-12/9), the document
   grammar + agent orientation (UX-15), **branded execution output on captured consoles and the
   transcript (UX-10)**, guided interview, help/settings, wave gate, run board, interruption
   surfaces — each a skill-prose composition over engine calls (UX-29), glyph-first with
   owned-surface color (§2). The closeout stat boxes wait on the §8.2 reconstruction +
   re-approval.
4. **The wrappers — all three in one pass (UX-31)**, post-assessment: launch screen (engine-
   rendered) · UX-14 obligations · the preload seam as config with the placeholder pack (UX-32) ·
   host exec + env marker (UA until built, §4.2) — the thin shim being the wrappers' only Python
   (§5). Fallback path (aliases + hooks) wherever the assessment ruled the wrapper non-standard
   (UX-1).
5. **Statusline theming** — single-line (§6.5): seal lead chip, Prussian/ochre bands, A1 rail
   string, depth chips (UX-25/26); the 2-line variant only after probe 6.
6. **Probes 2–6 opportunistically** alongside the above — each resolution upgrades a conservative
   default, none blocks a step.
