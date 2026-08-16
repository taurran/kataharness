import math, re

W = 64
INNER = W - 2
F, STEP = 48, 0.135
DUR, TAU = F*STEP, 2*math.pi
G = " ▁▂▃▄▅▆▇█"
BASE = [(2.6, 0.10, -2, 0.0), (1.2, 0.145, -3, 1.1), (0.5, 0.06, +1, 2.4)]

def wavecls(h):
    return "foam" if h>=7 else "pale" if h>=5.5 else "blu" if h>=4 else "pru" if h>=2.5 else "pruk"

def frame(fi):
    u = fi / F
    cells = []
    for x in range(W):
        h = 4.2
        for A, sf, k, ph in BASE:
            h += A * math.sin(sf*x + TAU*k*u + ph)
        h = max(0.6, min(8.0, h))
        cells.append((wavecls(h), G[max(1, min(8, int(h)))]))
    out, cur, buf = [], "S", []
    for c, ch in cells + [("E","")]:
        if c != cur and buf:
            out.append('<span class="%s">%s</span>' % (cur, "".join(buf))); buf=[]
        cur = c; buf.append(ch)
    return "".join(out)

SEA = '<div class="oceanc">' + "".join(
    '<div class="ofr" style="animation-delay:%.3fs">%s</div>' % (-(F-i)*STEP, frame(i)) for i in range(F)) + "</div>"

def vw(s): return sum(2 if ord(c) > 0x2E80 else 1 for c in s)
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

# ---------- 1. GUIDED-START INTERVIEW ----------
irail = ('<span class="sealbg">\u6539</span> '
 + s(GD,"\u2713") + s("foamd","shape") + ' <span class="pb">\u2501</span> '
 + s(GD,"\u2713") + s("foamd","careful") + ' <span class="pb">\u2501\u2501</span> '
 + '<span class="chip"> fan-out </span> '
 + '<span class="dimb">\u2500 models \u2500 brain \u2500 vault \u2500 docs \u2500 goal</span>')

istep = box("STEP 3 of 8 \u2014 fan-out", [
 s(T," How wide may this run go? Independent work can run in"),
 s(T," parallel; this dial caps how many branches cook at once."),
 "",
 " " + s(WN,"[1]") + " " + s(V,"focused") + s(D,"   \u2014 one thing at a time"),
 s(GD,"      + every step visible as it happens") + s(WN,"  \u2212 slowest overall"),
 " " + s(WN,"[2]") + " " + s(V,"balanced") + s(D,"  \u2014 sized to the work ") + s(GD,"(recommended)"),
 s(GD,"      + real time savings in parallel") + s(WN,"  \u2212 oversight by summary"),
 " " + s(WN,"[3]") + " " + s(V,"full sail") + s(D,"  \u2014 KataHarness sizes the ceiling"),
 s(GD,"      + fastest finish") + s(WN,"  \u2212 least visibility; the gates watch"),
 "",
 s(D," your config already sets: shape burn \u00b7 careful standard \u2014"),
 s(D," those steps were skipped, ") + s(WN,"[b]") + s(D," goes back to change one"),
])

iconfirm = "\n".join([
 s(D,"you") + " " + s(V,"2"),
 s(GD,"\u2713") + " " + s(T,"fan-out: balanced \u2014 the interview moves on \u00b7 5 steps left"),
])

# ---------- 2. HELP SCREEN ----------
helpbox = box("HELP \u2014 the five-minute version", [
 s(T," A RUN takes your goal through: plan deeply \u2192 freeze \u2192"),
 s(T," build in parallel WAVES \u2192 gate everything \u2192 close with"),
 s(T," receipts. You decide at gates; the harness proves its work."),
 "",
 " " + s("cm","/kata-loop") + "      " + s(D,"the full improvement cycle \u2014 start here"),
 " " + s("cm","/kata-start") + "     " + s(D,"one guided run"),
 " " + s("cm","/kata-onboard") + "   " + s(D,"bring an existing repo in"),
 " " + s("cm","/kata-status") + "    " + s(D,"what is happening right now"),
 " " + s("cm","/kata-resume") + "    " + s(D,"pick up where you left off"),
 " " + s("cm","/kata-settings") + "  " + s(D,"system settings"),
 "",
 s(D," deeper: README \u00b7 every closeout report explains its run"),
])

# ---------- 3. SETTINGS SCREEN ----------
settings = box("SETTINGS \u2014 type a number to change", [
 " " + s(WN,"[1]") + " " + s(L,"platforms") + "   " + s(V,"claude \u2713") + s(D," \u00b7 codex \u2014 \u00b7 kiro \u2014"),
 " " + s(WN,"[2]") + " " + s(L,"vault") + "       " + s(V,"~/Kiban/Vault") + s(D," \u00b7 linked"),
 " " + s(WN,"[3]") + " " + s(L,"brain") + "       " + s(V,"Kiban/kataharness") + s(D," \u00b7 learning feed on"),
 " " + s(WN,"[4]") + " " + s(L,"defaults") + "    " + s(V,"mode standard \u00b7 boundaries by shape"),
 " " + s(WN,"[5]") + " " + s(L,"models") + "      " + s(V,"anchor = session \u00b7 tiers relative"),
 " " + s(WN,"[6]") + " " + s(L,"update") + "      " + s(V,"v0.4.0") + s(WN," \u25b2 v0.5.0 available"),
 "",
 s(D," settings persist in the vault \u2014 reinstalls keep them (BL-N16)"),
])

# ---------- 4. PHASE MENU (wave boundary, approve posture) ----------
wavesum = "\n".join([
 s(D,"\u2500\u2500 wave 1 of 3 ended \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"),
 s(GD,"\u2713") + " " + s(T,"3 items merged \u00b7 integrated gauntlet green \u00b7 0 escalations open"),
])

wrule = '<span class="wn">' + "\u2501"*W + "</span>"
banner = "\n".join([
 wrule,
 '<span class="sealbg">\u6539</span> ' + s("wchip"," \u23f8 WAVE GATE \u2014 YOUR CALL ") + "  "
   + s(T,"wave 1 is done; wave 2 waits"),
 wrule,
])

wavemap = box("the run so far", [
 s(GD,"\u25cf") + " " + s(L,"wave 1") + "  " + s(V,"atomic writes \u00b7 stderr fix \u00b7 roots") + s(D,"   done \u00b7 green"),
 s("wn","\u25cf") + " " + s(L,"wave 2") + "  " + s(V,"config validator \u00b7 /kata-loop") + s("wn","   \u27f5 waits on you"),
 s("dimb","\u25cb") + " " + s(L,"wave 3") + "  " + s(V,"code-map measurement") + s(D,"            queued"),
])

phasemenu = box("WHAT NOW? \u2014 reply with a number", [
 " " + s(WN,"[1]") + " " + s(V,"continue \u2014 launch wave 2"),
 " " + s(WN,"[2]") + " " + s(V,"read the wave report first"),
 " " + s(WN,"[3]") + " " + s(V,"adjust before continuing") + s(D," \u2014 a deliberate re-plan event"),
 " " + s(WN,"[4]") + " " + s(V,"park the run") + s(D," \u2014 handoff written; /kata-resume returns"),
 " " + s(WN,"[5]") + " " + s(RS,"stop here") + s(D," \u2014 close out with what wave 1 delivered"),
], bd="wn", ti="wchip", dbl=True)

page = """<h2>The remaining surfaces — interview · help · settings · wave gate</h2>
<p class="subtitle">All four in the locked grammar. The interview gets its own progress rail; help leads with a plain five-minute explanation; settings is the numbered loop; the wave gate is a double-border decision.</p>

<style>
  .term { background:#0e1218; color:#c9d1d9; padding:20px 22px; border-radius:8px; font-family:'Cascadia Code','Consolas',monospace; font-size:13px; line-height:1.40; overflow-x:auto; white-space:pre; }
  .foam { color:#F7F2E6; } .foamd { color:#cfd8d3; } .pale { color:#8fb3cc; }
  .blu { color:#4d87ae; } .pru { color:#2E6389; } .pruk { color:#163A57; }
  .sealbg { color:#F7F2E6; background:#A6532B; font-weight:bold; }
  .chip { color:#0e1218; background:#d9a960; font-weight:bold; }
  .wchip { color:#0e1218; background:#e5c07b; font-weight:bold; }
  .och { color:#d9a960; } .pb { color:#CDBE9B; } .dimb { color:#44607a; }
  .gd { color:#5fd7a7; } .wn { color:#e5c07b; } .rs { color:#c2653a; }
  .txt { color:#a9b1c3; } .dim { color:#565f74; } .vl { color:#F7F2E6; } .lb { color:#4d87ae; }
  .cm { color:#61afef; }
</style>

<div class="term">
<span class="dim">\u256c\u256c 1 \u00b7 THE GUIDED-START INTERVIEW \u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c</span>

IRAIL

ISTEP
ICONFIRM

<span class="dim">one question per step \u00b7 config-answered steps auto-skip (shown \u2713)
on Claude the host question UI renders the choices; this frame is
the context around it \u00b7 [b] back works at every step</span>

<span class="dim">\u256c\u256c 2 \u00b7 HELP \u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c</span>

HELPBOX

<span class="dim">\u256c\u256c 3 \u00b7 SETTINGS \u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c</span>

SETTINGS

<span class="dim">\u256c\u256c 4 \u00b7 THE WAVE GATE (approve posture) \u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c</span>

GATEBANNER

WAVEMAP
SEAWATER
PHASEMENU
</div>

<p class="subtitle">Notes: settings values persist in the vault (BL-N16) \u00b7 the wave gate exists only when the boundary posture says approve \u2014 autonomous/notify runs never see it \u00b7 [3] adjust is the sanctioned deliberate-re-plan door, not a silent edit. React to any of the four.</p>
"""
page = page.replace("</style>", """  .oceanc { position:relative; height:1.38em; overflow:hidden; }
  .ofr { position:absolute; left:0; top:0; visibility:hidden; animation: ofrshow %.2fs steps(1) infinite; }
  @keyframes ofrshow { 0%%, %.2f%% { visibility:visible; } %.2f%%, 100%% { visibility:hidden; } }
</style>""" % (DUR, 100.0/F-0.01, 100.0/F))
page = (page.replace("IRAIL", irail).replace("ISTEP", istep).replace("ICONFIRM", iconfirm)
        .replace("HELPBOX", helpbox).replace("SETTINGS", settings)
        .replace("GATEBANNER", banner).replace("WAVEMAP", wavemap)
        .replace("SEAWATER", SEA).replace("PHASEMENU", phasemenu))
open(r"C:\dev\projects\KataHarness\.superpowers\brainstorm\40354-1786850132\content\remaining-surfaces.html", "w", encoding="utf-8", newline="\n").write(page)
print("written, widths verified")
