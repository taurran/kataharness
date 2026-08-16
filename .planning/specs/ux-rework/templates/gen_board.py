import re

W = 64
INNER = W - 2

def vw(s): return sum(2 if ord(c) > 0x2E80 else 1 for c in s)
def strip(html): return re.sub(r"<[^>]+>", "", html)
def s(c, t): return '<span class="%s">%s</span>' % (c, t)

def box(title, rows, bd="pb", ti="och"):
    dashes = INNER - len(title) - 3
    lines = ['<span class="%s">\u250c\u2500 </span><span class="%s">%s</span><span class="%s"> %s\u2510</span>' % (bd, ti, title, bd, "\u2500"*dashes)]
    for html_r in rows:
        if html_r == "":
            lines.append('<span class="%s">\u2502</span>%s<span class="%s">\u2502</span>' % (bd, " "*INNER, bd))
            continue
        pad = INNER - vw(strip(html_r))
        assert pad >= 0, (vw(strip(html_r)), strip(html_r))
        lines.append('<span class="%s">\u2502</span>%s%s<span class="%s">\u2502</span>' % (bd, html_r, " "*pad, bd))
    lines.append('<span class="%s">\u2514%s\u2518</span>' % (bd, "\u2500"*INNER))
    for ln in lines:
        assert vw(strip(ln)) == W, (vw(strip(ln)), strip(ln))
    return "\n".join(lines)

V, T, D, L, GD, WN, RS = "vl", "txt", "dim", "lb", "gd", "wn", "rs"

statusline = "\n".join([
 s(D,"tier 1 \u00b7 THE STATUSLINE \u2014 always visible, ~1s refresh, one line:"),
 "",
 s("sealbg","\u6539") + s(D,"\u2502") + s(T,"KataHarness ") + s(GD,"\u2593\u2593\u2593\u2593\u2593\u2593") + s("dimb","\u2591\u2591\u2591\u2591") + s(D," 61% \u2502 ") + s("och","fable") + s(D," \u2502 ") + s("wchip"," exec 3/6 ") + s(D," \u2502 crew ") + s(V,"W1") + s(WN,"\u25b82") + " " + s(V,"W2") + " " + s(V,"W3") + s(WN,"\u25b81"),
 "",
 s(D,"W1\u25b82 = worker W1 has 2 nested children cooking \u2014 depth at a glance"),
])

board = box("run board \u2014 backlog-burn-01 \u00b7 exec \u00b7 wave 2 of 3", [
 s(GD,"\u25cf") + " " + s(V,"W1  config validator") + s(D,"           building \u00b7 12m \u00b7 41k tok"),
 s(D,"    \u251c ") + s(GD,"\u25cf") + " " + s(V,"W1.1 test author") + s(D,"          red\u2192green \u00b7 4/9 cases"),
 s(D,"    \u2514 ") + s(WN,"\u25cf") + " " + s(V,"W1.2 docs sync") + s(D,"            waiting on W1.1"),
 s(GD,"\u25cf") + " " + s(V,"W2  /kata-loop command") + s(D,"         at the gate \u00b7 judge running"),
 s(D,"    \u2514 ") + s(GD,"\u25cf") + " " + s(V,"W2.1 judge (fresh ctx)") + s(D,"    verifying claims \u00b7 2m"),
 s("dimb","\u25cb") + " " + s(V,"W3  code-map measurement") + s(D,"       queued \u00b7 starts in wave 3"),
 "",
 s(D," agents 5 \u00b7 3 direct + 2 nested \u00b7 deepest branch 2 \u00b7 all owned"),
])

crumbs = "\n".join([
 s(D,"tier 3 \u00b7 IN THE TRANSCRIPT \u2014 every worker line carries its lineage:"),
 "",
 s("pru","\u258f") + s(D,"[W1.1]") + " " + s(T,"9 cases written \u00b7 4 green \u00b7 rerunning the red five"),
 s("pru","\u258f") + s(D,"[W2\u2192judge]") + " " + s(T,"claim 2 of 3 reproduced independently"),
])

page = """<h2>Nested execution — three tiers of legibility</h2>
<p class="subtitle">The answer to \u201chow do I follow subagents running subagents\u201d: the statusline shows depth at a glance, the run board shows the whole tree, and every transcript line names its lineage.</p>

<style>
  .term { background:#0e1218; color:#c9d1d9; padding:20px 22px; border-radius:8px; font-family:'Cascadia Code','Consolas',monospace; font-size:13px; line-height:1.42; overflow-x:auto; white-space:pre; }
  .foam { color:#F7F2E6; } .pale { color:#8fb3cc; } .blu { color:#4d87ae; } .pru { color:#2E6389; }
  .sealbg { color:#F7F2E6; background:#A6532B; font-weight:bold; }
  .chip { color:#0e1218; background:#d9a960; font-weight:bold; }
  .wchip { color:#0e1218; background:#e5c07b; font-weight:bold; }
  .och { color:#d9a960; } .pb { color:#CDBE9B; } .dimb { color:#44607a; }
  .gd { color:#5fd7a7; } .wn { color:#e5c07b; } .rs { color:#c2653a; }
  .txt { color:#a9b1c3; } .dim { color:#565f74; } .vl { color:#F7F2E6; } .lb { color:#4d87ae; }
</style>

<div class="term">
STATUSLINE

<span class="dim">tier 2 \u00b7 THE RUN BOARD \u2014 /kata-status, the full tree on demand:</span>

BOARD

CRUMBS
</div>

<p class="subtitle">Worker IDs are hierarchical (W1 \u2192 W1.1) so lineage is in the name itself; the board is depth-capped with rollup counts if a tree ever gets deeper than readable; \u201call owned\u201d = every branch traces to a dispatch record \u2014 no orphan agents.</p>
"""
page = page.replace("STATUSLINE", statusline).replace("BOARD", board).replace("CRUMBS", crumbs)
open(r"C:\dev\projects\KataHarness\.superpowers\brainstorm\40354-1786850132\content\nested-execution.html", "w", encoding="utf-8", newline="\n").write(page)
print("written, widths verified")
