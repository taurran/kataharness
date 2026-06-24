# BRAND.md — 改善型 Closeout Report Brand Reference

Durable record of the brand decisions implemented in `closeout-report.template.html`.
Single source: inline `<style>` in that file. Update the template; update this doc.

---

## Palette

| Role | Hex | Usage |
|---|---|---|
| Ground | `#14141B` | Page background |
| Card surface | `#1C1C26` | Report card background |
| Border | `#2E2E3C` | Card border, dividers, section separators |
| Text | `#EAEAF2` | Primary body text |
| Muted | `#9AA0B4` | Metadata, labels, secondary text |
| Accent (kaizen green) | `#5BD6A6` | Section heading left-borders, badge (PASS), list bullets, links |
| Warm highlight (gold) | `#D4A843` | Wordmark dot, PARTIAL badge — sparingly |
| Alert (terracotta) | `#E0764A` | NEEDS WORK badge, backout block border |

---

## Typography

- **Display / headers** — `ui-monospace, "Cascadia Code", "JetBrains Mono", Consolas, monospace`
  Used for: wordmark, report title, section headings, ribbon band, badge text, footer labels.
  No web-font fetch — offline-safe.

- **Body / prose** — `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`
  Used for: paragraph text, list items, aspect descriptions.

- Base font-size: `15px` · line-height: `1.65` · generous spacing throughout.

---

## Identity

- **Wordmark:** `改善型 · KATAHARNESS` — monospace, small-caps style, gold `·` separator.
  Always in the card header; the kanji reads as the system's own identity, not a mascot name.

- **Loop ribbon band:** `GRILL ▸ FREEZE ▸ EXECUTE ▸ EVALUATE ▸ HANDOFF ▸ IMPROVE`
  Rendered as a thin dark band (`#14141B`) below the header. Muted text — ambient context,
  not the focus. Matches the `改善型` kata loop vocabulary exactly.

- **Verdict badge:** three states, same shape, different palette:
  - `GOAL HIT` / `badge--pass` → kaizen green
  - `PARTIAL` / `badge--partial` → gold/amber
  - `NEEDS WORK` / `badge--needs-work` → terracotta/alert

---

## Layout

- **Single column, `~720px` max-width** centered card.
- Dark editorial feel: calm, technical, not busy. Matches the `kata_web.py` web viewer spirit.
- **Section headings:** accent left-border (`3px solid #5BD6A6`), monospace, uppercase, small.
- **Card structure:** header → ribbon band → body sections → footer.
- Footer: gate numbers · baseline→result SHAs · UTC timestamp — all in monospace, muted.
- Rounded corners (`8px`), subtle surface/border separation.
- Generous padding (`2rem`) — legible at a glance for non-expert readers.

---

## Tone

Calm craftsperson. Editorial-but-technical. Never gaudy, never chatty. The report is
a durable artifact the owner can open, keep, and trust.
