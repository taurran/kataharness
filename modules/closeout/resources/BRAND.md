# BRAND.md — KataHarness 改善型 Closeout Report Brand Reference

Durable record of the brand decisions in `closeout-report.template.html`.
Single source: inline `<style>` + the inline `<svg>` logo in that file. Update the template; update this doc.

A calm, **editorial print** look on a **Hokusai-derived palette** (aged paper · Prussian-blue ink · ochre ·
rust). Readability first: serif section titles, generous spacing, callout **tiles** to break the report up.
No decorative wave motif (tried, dropped) and no loop-phase ribbon (read as broken tabs — removed).

---

## Logo

A subtle **KataHarness mark** (inline SVG, ~26px): three **ascending bars** (deep → mid → deep Prussian) with a
thin **ochre arrow rising** over them — the *Improvement Kata / kaizen "continuous improvement"* idea (each loop
raises the bar). Sits in the brand splash next to the name; never large or loud. This is the project's first
logo — defined here, reusable elsewhere (favicon, docs, statusline glyph).

## Palette (Hokusai-derived)

| Role | Hex | Usage |
|---|---|---|
| Paper (ground) | `#E9DFC8` | Page background |
| Card surface | `#F5EEDD` | Report card |
| Border | `#CDBE9B` | Card border, dividers |
| Ink (text) | `#1A2C3B` | Primary body text |
| Muted | `#756A52` | Metadata, taglines |
| Deep (Prussian) | `#163A57` | Titles, logo, footer, accents, PASS badge |
| Blue (mid) | `#2E6389` | Section left-borders, aspect headings, links, bullets |
| Foam | `#F7F2E6` | Footer text |
| Ochre | `#B5894B` / ink `#856231` | Logo arrow, link underline, **WARNING** tile, PARTIAL badge |
| Rust | `#A6532B` | **ERROR** tile, backout, NEEDS WORK badge |

## Typography (readability-first)

- **Titles & section headings** — serif: `Georgia, "Iowan Old Style", "Palatino Linotype", Palatino,
  "Book Antiqua", serif`. Section headings are **Title Case, ~1.18rem** (not tiny mono-uppercase) — the key
  readability fix. Report title ~1.6rem.
- **Body / aspect headings** — sans: `"Inter", system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial,
  sans-serif`. Aspect headings ~0.95rem semibold, mid-blue.
- **Labels / badge / footer / code** — `ui-monospace, "Cascadia Code", "JetBrains Mono", Consolas, monospace`.
- Base `15.5px` · line-height `1.72`. All fonts are system/offline-safe (no web fetch; `"Inter"`/`"Iowan"` are
  optional first-choices that fall back cleanly).

## Callout tiles (the scannability system)

Severity tiles break content into legible blocks. Each: rounded, `4px` left accent border, a small mono label.
- `.tile--warning` (ochre) — risks / cautions. Risks render as one warning tile each (`Watch`).
- `.tile--error` (rust) — critical errors / NEEDS_WORK, and the **backout** block (`Clean undo · L9 backout`).
- `.tile--note` (blue) — informational asides.
- `.tile--ok` (deep) — positive confirmations (e.g. "Goal hit").

## Layout

- Single column, **`~700px`** card; soft shadow; `8px` corners.
- Structure: **brand splash** (logo · `KataHarness` · `改善型` · "closeout report") → header (serif title +
  pill verdict badge) → body sections → deep-Prussian footer (gate · SHAs · UTC, mono).
- Section headings: serif, mid-blue `3px` left-border.

## Tone

Calm craftsperson, editorial, composed. The report is a durable print the owner can open, keep, and trust.
