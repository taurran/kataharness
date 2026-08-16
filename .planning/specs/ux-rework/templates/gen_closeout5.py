import math, re

W, F, STEP = 72, 48, 0.135
DUR, TAU = F*STEP, 2*math.pi
G = " \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
BASE = [(2.6, 0.10, -2, 0.0), (1.2, 0.145, -3, 1.1), (0.5, 0.06, +1, 2.4)]
INNER = W - 2

def vw(s): return sum(2 if ord(c) > 0x2E80 else 1 for c in s)
def cls(h):
    return "foam" if h>=7 else "pale" if h>=5.5 else "blu" if h>=4 else "pru" if h>=2.5 else "pruk"

def frame(fi):
    u = fi / F
    cells = []
    for x in range(W):
        h = 4.2
        for A, sf, k, ph in BASE:
            h += A * math.sin(sf*x + TAU*k*u + ph)
        h = max(0.6, min(8.0, h))
        cells.append((cls(h), G[max(1, min(8, int(h)))]))
    out, cur, buf = [], "S", []
    for c, ch in cells + [("E","")]:
        if c != cur and buf:
            out.append('<span class="%s">%s</span>' % (cur, "".join(buf))); buf=[]
        cur = c; buf.append(ch)
    return "".join(out)

SEA = '<div class="oceanc">' + "".join(
    '<div class="ofr" style="animation-delay:%.3fs">%s</div>' % (-(F-i)*STEP, frame(i)) for i in range(F)) + "</div>"

def strip(html): return re.sub(r"<[^>]+>", "", html)
def s(c, t): return '<span class="%s">%s</span>' % (c, t)

def box(title, rows, bd="pb", ti="och", dbl=False):
    if dbl:
        tl, tr, bl, br, hz, vt = "\u2554", "\u2557", "\u255a", "\u255d", "\u2550", "\u2551"
    else:
        tl, tr, bl, br, hz, vt = "\u250c", "\u2510", "\u2514", "\u2518", "\u2500", "\u2502"
    dashes = INNER - len(title) - 3
    lines = ['<span class="%s">%s%s </span><span class="%s">%s</span><span class="%s"> %s%s</span>' % (bd, tl, hz, ti, title, bd, hz*dashes, tr)]
    for html_r in rows:
        if html_r == "":
            lines.append('<span class="%s">%s</span>%s<span class="%s">%s</span>' % (bd, vt, " "*INNER, bd, vt))
            continue
        pad = INNER - vw(strip(html_r))
        assert pad >= 0, (vw(strip(html_r)), strip(html_r))
        lines.append('<span class="%s">%s</span>%s%s<span class="%s">%s</span>' % (bd, vt, html_r, " "*pad, bd, vt))
    lines.append('<span class="%s">%s%s%s</span>' % (bd, bl, hz*INNER, br))
    for ln in lines:
        assert vw(strip(ln)) == W, (vw(strip(ln)), strip(ln))
    return "\n".join(lines)

V, T, D, L, GD, WN, RS = "vl", "txt", "dim", "lb", "gd", "wn", "rs"

title = "IN PLAIN WORDS — what this run did"
tdash = W - len(title) - 4
plain = "\n".join([
 '<span class="pb">━━ </span><span class="och">' + title + '</span><span class="pb"> ' + "━"*tdash + "</span>",
 s(T,"This run burned six stale backlog items in three waves, and all six"),
 s(T,"shipped. The files your gates depend on can no longer tear mid-write,"),
 s(T,"install failures finally say WHY they failed, and the code map now"),
 s(T,"sees project layouts it had been blind to."),
 "",
 s(T,"Two of the six turned out to be filed WRONG — triage caught it before"),
 s(T,"any code was written, and the right fixes were built instead. One item"),
 s(T,"was a measurement that closed a 55-day-old question: the map fixes"),
 s(T,"worked — coverage went from 25 files seen to 157."),
 "",
 s(T,"Three new problems were found along the way and FILED, not fixed"),
 s(T,"silently. For every number and diff, open the report ") + s(WN,"[2]") + s(T,"; to walk the"),
 s(T,"changes themselves, take the tour ") + s(WN,"[1]") + s(T,"."),
 '<span class="dimb">' + "─"*W + "</span>",
])

items = box("THE ITEMS \u2014 each one, truthfully", [
 s(GD,"\u25cf") + " " + s(V,"atomic gate writes") + s(D,"        done \u00b7 8 writers converted \u00b7 637a8d5"),
 s(GD,"\u25cf") + " " + s(V,"install errors surfaced") + s(D,"   done \u00b7 closed a deferred debt \u00b7 63bd65f"),
 s(GD,"\u25cf") + " " + s(V,"nested source roots") + s(D,"       done \u00b7 repro test first \u00b7 595078f"),
 s(GD,"\u25cf") + " " + s(V,"config load-guard") + s(D,"         done \u00b7 33 tests, 16 non-vacuous \u00b7 5550d35"),
 s(GD,"\u25cf") + " " + s(V,"/kata-loop entry point") + s(D,"    done \u00b7 routes \u00b7 b08f79e"),
 s(WN,"\u25cf") + " " + s(V,"code-map rebuild") + s(D,"          done, with a finding \u2014 the documented"),
 s(D,"                            rebuild command is broken; filed"),
])

gitbox = box("GIT \u2014 where everything stands", [
 s(L,"branch") + "  " + s(V,"burn/backlog-burn-01") + s(D,"  \u00b7 14 commits ahead of master"),
 "",
 s(GD,"\u25cf") + " " + s(V,"committed") + s(D,"   14/14 \u00b7 working tree clean \u00b7 stash empty"),
 s("dimb","\u25cb") + " " + s(V,"pushed") + s(D,"      not yet \u2192 ") + s(WN,"[6]"),
 s("dimb","\u25cb") + " " + s(V,"pull request") + s(D,"  none open \u2192 ") + s(WN,"[7]"),
 s("dimb","\u25cb") + " " + s(V,"merged") + s(D,"      awaits the PR \u2192 ") + s(WN,"[8]"),
 s("dimb","\u25cb") + " " + s(V,"tagged") + s(D,"      optional at ship time"),
])

decide = box("WHAT NOW? \u2014 type a number \u00b7 this menu returns after every step", [
 s(D," LOOK DEEPER"),
 " " + s(WN,"[1]") + " " + s(V,"tour the changes") + s(D," \u2014 a guided map of what was built"),
 " " + s(WN,"[2]") + " " + s(V,"open the full report") + s(D," \u2014 printable \u2192 PDF"),
 "",
 s(D," GIT"),
 " " + s(WN,"[3]") + " " + s(V,"push the branch"),
 " " + s(WN,"[4]") + " " + s(V,"open the pull request"),
 " " + s(WN,"[5]") + " " + s(V,"merge") + s(D," \u2014 after the PR exists"),
 "",
 s(D," GO AGAIN"),
 " " + s(WN,"[6]") + " " + s(V,"another pass on this repo") + s(D," \u2014 keeps everything learned"),
 s(D,"      re-plan depth: full \u00b7 standard \u00b7 light \u00b7 skip (fastest)"),
 " " + s(WN,"[7]") + " " + s(V,"a different kind of run on this repo"),
 " " + s(WN,"[8]") + " " + s(V,"move to a new repo") + s(D," \u2014 ") + s(WN,"handoff first (recommended)"),
 "",
 s(D," WRAP UP"),
 " " + s(WN,"[9]") + " " + s(RS,"undo everything") + s(D," \u2014 clean backout, one branch delete"),
 " " + s(WN,"[0]") + " " + s(V,"finish") + s(D," \u2014 recycle this session for a new run, or exit"),
], bd="wn", ti="wchip", dbl=True)

loopdemo = "\n".join([
 s(D,"\u2500\u2500 how the loop feels \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"),
 s(D,"you") + " " + s(V,"3"),
 s(GD,"\u2713") + " " + s(T,"pushed \u2014 14 commits \u2192 origin/burn/backlog-burn-01"),
 s(D,"you") + " " + s(V,"4"),
 s(GD,"\u2713") + " " + s(T,"PR #54 opened \u2014 \u201cbacklog burn: six items, three waves\u201d"),
 s(D,"the menu returns in short form after each step \u2014 until [0] or a new run"),
])

rail = ('<span class="sealbg">\u6539</span> '
 + s(GD,"\u2713") + s("foamd","init") + ' <span class="pb">\u2501</span> '
 + s(GD,"\u2713") + s("foamd","grill") + ' <span class="pb">\u2501</span> '
 + s(GD,"\u2713") + s("foamd","freeze") + ' <span class="pb">\u2501</span> '
 + s(GD,"\u2713") + s("foamd","plan") + ' <span class="pb">\u2501</span> '
 + s(GD,"\u2713") + s("foamd","exec") + ' <span class="pb">\u2501</span> '
 + s(GD,"\u2713") + s("foamd","gate") + ' <span class="pb">\u2501\u2501</span> '
 + '<span class="chip"> close </span>')

heavy = "\u2501"*W
page = """<h2>Closeout v6 — prose unboxed</h2>
<p class="subtitle">The plain-words narrative now sits between dividers instead of inside a box — full-width text, less scroll. Boxes are for data; dividers are for prose.</p>

<style>
  .term { background:#0e1218; color:#c9d1d9; padding:22px 24px; border-radius:8px; font-family:'Cascadia Code','Consolas',monospace; font-size:13px; line-height:1.40; overflow-x:auto; white-space:pre; }
  .foam { color:#F7F2E6; } .foamd { color:#cfd8d3; } .pale { color:#8fb3cc; }
  .blu { color:#4d87ae; } .pru { color:#2E6389; } .pruk { color:#163A57; }
  .sealbg { color:#F7F2E6; background:#A6532B; font-weight:bold; }
  .chip { color:#0e1218; background:#d9a960; font-weight:bold; }
  .wchip { color:#0e1218; background:#e5c07b; font-weight:bold; }
  .och { color:#d9a960; } .pb { color:#CDBE9B; } .dimb { color:#44607a; }
  .gd { color:#5fd7a7; } .wn { color:#e5c07b; } .rs { color:#c2653a; }
  .txt { color:#a9b1c3; } .dim { color:#565f74; } .vl { color:#F7F2E6; } .lb { color:#4d87ae; }
  .oceanc { position:relative; height:1.38em; overflow:hidden; }
  .ofr { position:absolute; left:0; top:0; visibility:hidden; animation: ofrshow DURs steps(1) infinite; }
  @keyframes ofrshow { 0%, ONP% { visibility:visible; } OFFP%, 100% { visibility:hidden; } }
</style>

<div class="term">
<span class="pb">HEAVY</span>
<span class="sealbg">\u6539</span> <span class="foam">KATAHARNESS \u00b7 RUN CLOSE</span>
<span class="dim">run</span> <span class="txt">backlog-burn-01</span> <span class="dim">\u00b7 shape</span> <span class="txt">burn</span> <span class="dim">\u00b7 closed</span> <span class="txt">2026-08-15 23:16</span>
<span class="pb">HEAVY</span>

PLAINBOX

ITEMSBOX

GITBOX

<span class="dim">(the four stat boxes \u2014 WHAT GOT DONE \u00b7 WHO DID THE WORK \u00b7 QUALITY AND
COST \u00b7 WHAT WE LEARNED \u2014 sit here unchanged from v4)</span>

DECIDEBOX

LOOPDEMO
SEA
RAIL
</div>

<p class="subtitle">Truth-serum discipline holds in the item list: the one item with a finding says so in its own row. The git block's open circles point at the exact menu numbers that close them.</p>
"""
page = (page.replace("DURs", "%.2fs" % DUR).replace("ONP", "%.2f" % (100.0/F-0.01))
        .replace("OFFP", "%.2f" % (100.0/F)).replace("HEAVY", heavy)
        .replace("PLAINBOX", plain).replace("ITEMSBOX", items).replace("GITBOX", gitbox)
        .replace("DECIDEBOX", decide).replace("LOOPDEMO", loopdemo)
        .replace("SEA", SEA).replace("RAIL", rail))
open(r"C:\dev\projects\KataHarness\.superpowers\brainstorm\40354-1786850132\content\closeout-v6.html", "w", encoding="utf-8", newline="\n").write(page)
print("written, widths verified")
