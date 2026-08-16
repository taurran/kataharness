import math, re

W, F, STEP = 64, 48, 0.135
DUR, TAU = F*STEP, 2*math.pi
G = " \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
BASE = [(2.6, 0.10, -2, 0.0), (1.2, 0.145, -3, 1.1), (0.5, 0.06, +1, 2.4)]

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

def box(title, rows):
    dashes = 62 - len(title) - 3
    lines = ['<span class="pb">\u250c\u2500 </span><span class="och">' + title + '</span><span class="pb"> ' + "\u2500"*dashes + "\u2510</span>"]
    for html_r in rows:
        if html_r == "":
            lines.append('<span class="pb">\u2502</span>' + " "*62 + '<span class="pb">\u2502</span>')
            continue
        pad = 62 - vw(strip(html_r))
        assert pad >= 0, (vw(strip(html_r)), strip(html_r))
        lines.append('<span class="pb">\u2502</span>' + html_r + " "*pad + '<span class="pb">\u2502</span>')
    lines.append('<span class="pb">\u2514' + "\u2500"*62 + "\u2518</span>")
    for ln in lines:
        assert vw(strip(ln)) == 64, (vw(strip(ln)), strip(ln))
    return "\n".join(lines)

def s(c, t): return '<span class="%s">%s</span>' % (c, t)
V, T, D, L, GD, WN, RS = "vl", "txt", "dim", "lb", "gd", "wn", "rs"

outcome = box("WHEN THIS RUN ENDS \u2014 what will be TRUE", [
 s(GD,"\u2713") + " " + s(V,"gate files can no longer be read half-written") + s(D," (8 writers)"),
 s(GD,"\u2713") + " " + s(V,"a failed install will tell you WHY") + s(D," (stderr surfaced)"),
 s(GD,"\u2713") + " " + s(V,"the code map will see nested src layouts"),
 s(GD,"\u2713") + " " + s(V,"a broken config will STOP the run, never be guessed at"),
 s(GD,"\u2713") + " " + s(V,"the improvement cycle gains its front door: /kata-loop"),
 s(GD,"\u2713") + " " + s(V,"the code map rebuilt + the July fixes finally MEASURED"),
 "",
 s(RS,"\u2717 NOT in this run") + s(T," \u2014 said now so nothing is implied:"),
 s(T,"  write-then-readback verification ") + s(D,"(rejected by design, D159)"),
 s(T,"  deleting the dormant adaptive keys ") + s(D,"(kept by deferral)"),
])

waves = box("THE WAVES \u2014 what finishes when", [
 s(L,"wave 1") + "  " + s(V,"atomic writes \u00b7 stderr fix \u00b7 nested roots") + s(D," \u00b7 3 builders"),
 s(D,"        at wave end: all merged, integrated gauntlet green"),
 s(L,"wave 2") + "  " + s(V,"config validator \u00b7 /kata-loop command") + s(D," \u00b7 2 builders"),
 s(D,"        at wave end: guard real, command routes, docs aligned"),
 s(L,"wave 3") + "  " + s(V,"code-map rebuild \u2014 a measurement, not a build"),
 s(D,"        at wave end: before/after numbers on the record"),
 "",
 s(L,"boundaries") + "  " + s("wn","approve \u2014 the run WAITS for you at each wave end"),
])

stops = box("WHAT WILL STOP THIS RUN \u2014 fail-closed, by design", [
 s(WN,"\u25a0") + " " + s(V,"a builder's gauntlet is red") + s(T," \u2192 that item does not merge"),
 s(WN,"\u25a0") + " " + s(V,"a judge returns NEEDS_WORK") + s(T," \u2192 targeted fix, same plan"),
 s(RS,"\u25a0") + " " + s(V,"anything conflicts with the frozen contract") + s(T," \u2192 wave"),
 s(T,"   halts; the operator decides \u2014 never a silent re-plan"),
 s(RS,"\u25a0") + " " + s(V,"a builder says the brief is wrong") + s(T," \u2192 item pauses for"),
 s(T,"   a conductor ruling \u2014 push-back is designed, not failure"),
 s(WN,"\u25a0") + " " + s(V,"provider quota runs out") + s(T," \u2192 run parks; /kata-resume"),
 s(RS,"\u25a0") + " " + s(V,"you say stop, or a breakthrough alert fires") + s(T," \u2192 hold"),
])

config = box("CONFIGURATION", [
 s(L,"mode") + " " + s(V,"standard") + "   " + s(L,"anchor") + " " + s(V,"fable") + s(D," \u00b7 builders opus \u00b7 judges fable"),
 s(L,"modules") + " " + s(V,"quality \u00b7 slop") + "    " + s(L,"brain") + " " + s(V,"PokeVault") + "  " + s(L,"vault") + " " + s(V,"linked"),
 s(L,"contract") + " " + s(V,"frozen 3e10ce4") + s(D," \u00b7 gated \u00b7 6 items / 3 waves"),
 s(L,"baseline") + " " + s(V,"d4650fc") + s(D," \u00b7 gauntlet 4/4 \u00b7 clean \u00b7 stash empty"),
])

vitals = box("run vitals \u2014 everything accrues from here", [
 s(L,"agents") + " " + s(V,"0") + "      " + s(L,"waves") + " " + s(V,"0/3") + "      " + s(L,"miniloops") + " " + s(V,"0") + "      " + s(L,"conf") + " " + s(D,"\u2014"),
 s(L,"tokens") + " " + s(V,"0") + " " + s(D,"(in 0 \u00b7 out 0)") + "              " + s(L,"time") + " " + s(V,"0m"),
 s(L,"flagged") + " " + s(V,"0") + " " + s(D,"\u2192") + " " + s(L,"remediated") + " " + s(V,"0") + "          " + s(L,"gate streak") + " " + s(D,"\u2014"),
])

rail = ('<span class="sealbg">\u6539</span> <span class="chip"> init </span> '
        '<span class="dimb">\u2500 grill \u2500 freeze \u2500 plan \u2500 exec \u2500 gate \u2500 close</span>')

heavy = "\u2501"*64
show_on = 100.0/F - 0.01
show_off = 100.0/F

page = """<h2>Run-start v2 — the truth-serum bookend</h2>
<p class="subtitle">Outcome first, stops explicit, every block 64 wide, the sea alive. "Wave" is the official term. Top-to-bottom: what will be TRUE when it ends → what finishes when → what can stop it → configuration → zeroed vitals into the water.</p>

<style>
  .term { background:#0e1218; color:#c9d1d9; padding:22px 24px; border-radius:8px; font-family:'Cascadia Code','Consolas',monospace; font-size:13px; line-height:1.40; overflow-x:auto; white-space:pre; }
  .foam { color:#F7F2E6; } .foamd { color:#cfd8d3; } .pale { color:#8fb3cc; }
  .blu { color:#4d87ae; } .pru { color:#2E6389; } .pruk { color:#163A57; }
  .sealbg { color:#F7F2E6; background:#A6532B; font-weight:bold; }
  .chip { color:#0e1218; background:#d9a960; font-weight:bold; }
  .och { color:#d9a960; } .ochd { color:#B5894B; } .pb { color:#CDBE9B; } .dimb { color:#44607a; }
  .gd { color:#5fd7a7; } .wn { color:#e5c07b; } .rs { color:#c2653a; }
  .txt { color:#a9b1c3; } .dim { color:#565f74; } .vl { color:#F7F2E6; } .lb { color:#4d87ae; }
  .oceanc { position:relative; height:1.38em; overflow:hidden; }
  .ofr { position:absolute; left:0; top:0; visibility:hidden; animation: ofrshow DURs steps(1) infinite; }
  @keyframes ofrshow { 0%, ONPCT% { visibility:visible; } OFFPCT%, 100% { visibility:hidden; } }
</style>

<div class="term">
<span class="pb">HEAVY</span>
<span class="sealbg">\u6539</span> <span class="foam">KATAHARNESS \u00b7 RUN START</span>
<span class="dim">run</span> <span class="txt">backlog-burn-01</span> <span class="dim">\u00b7 shape</span> <span class="txt">burn</span> <span class="dim">\u00b7 opened</span> <span class="txt">2026-08-15 21:04</span>
<span class="pb">HEAVY</span>

OUTCOME

WAVES

STOPS

CONFIG

VITALS
SEA
RAIL
</div>

<p class="subtitle">Every box asserted at exactly 64 columns. Run personas (how the harness speaks per audience) noted for a future backlog item — this layout is the persona-neutral skeleton.</p>
"""
page = (page.replace("DURs", "%.2fs" % DUR).replace("ONPCT", "%.2f" % show_on)
            .replace("OFFPCT", "%.2f" % show_off).replace("HEAVY", heavy)
            .replace("OUTCOME", outcome).replace("WAVES", waves).replace("STOPS", stops)
            .replace("CONFIG", config).replace("VITALS", vitals).replace("SEA", SEA).replace("RAIL", rail))

open(r"C:\dev\projects\KataHarness\.superpowers\brainstorm\40354-1786850132\content\run-start-v2.html", "w", encoding="utf-8", newline="\n").write(page)
print("written, all boxes 64-verified")
