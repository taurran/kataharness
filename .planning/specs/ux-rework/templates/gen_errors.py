import re

def vw(s): return sum(2 if ord(c) > 0x2E80 else 1 for c in s)
def strip(html): return re.sub(r"<[^>]+>", "", html)
def s(c, t): return '<span class="%s">%s</span>' % (c, t)

def box(title, rows, bd="pb", ti="och"):
    dashes = 62 - len(title) - 3
    lines = ['<span class="%s">\u250c\u2500 </span><span class="%s">%s</span><span class="%s"> %s\u2510</span>' % (bd, ti, title, bd, "\u2500"*dashes)]
    for html_r in rows:
        if html_r == "":
            lines.append('<span class="%s">\u2502</span>%s<span class="%s">\u2502</span>' % (bd, " "*62, bd))
            continue
        pad = 62 - vw(strip(html_r))
        assert pad >= 0, (vw(strip(html_r)), strip(html_r))
        lines.append('<span class="%s">\u2502</span>%s%s<span class="%s">\u2502</span>' % (bd, html_r, " "*pad, bd))
    lines.append('<span class="%s">\u2514%s\u2518</span>' % (bd, "\u2500"*62))
    for ln in lines:
        assert vw(strip(ln)) == 64, (vw(strip(ln)), strip(ln))
    return "\n".join(lines)

V, T, D, L, GD, WN, RS = "vl", "txt", "dim", "lb", "gd", "wn", "rs"

# --- 1. the updated WAVES box with the highlighted boundary chip ---
waves = box("THE WAVES \u2014 what finishes when", [
 s(L,"wave 1") + "  " + s(V,"atomic writes \u00b7 stderr fix \u00b7 nested roots") + s(D," \u00b7 3 builders"),
 s(D,"        at wave end: all merged, integrated gauntlet green"),
 s(L,"wave 2") + "  " + s(V,"config validator \u00b7 /kata-loop command") + s(D," \u00b7 2 builders"),
 s(D,"        at wave end: guard real, command routes, docs aligned"),
 s(L,"wave 3") + "  " + s(V,"code-map rebuild \u2014 a measurement, not a build"),
 s(D,"        at wave end: before/after numbers on the record"),
 "",
 s(L,"boundaries") + "  " + s("wchip"," AUTONOMOUS \u2014 a burn never asks between waves ") ,
 s(D,"            set by run shape \u00b7 change at start or by steering"),
])

# --- 2. breakthrough alert (rust, maximum weight) ---
btop = '<span class="rs">' + "\u2501"*64 + "</span>"
breakthrough = "\n".join([
 btop,
 s("rschip"," \u26a0 BREAKTHROUGH ") + " " + s("foam","you are needed \u2014 the run is HOLDING"),
 btop,
 "",
 s(L,"what   ") + " " + s(V,"worker W2 hit a conflict with the frozen contract"),
 s(D,"         the brief requires editing graph_gen's private symbol \u2014"),
 s(D,"         Amendment 1 forbids exactly that"),
 s(L,"held   ") + " " + s(V,"nothing merges while you decide") + s(D," \u00b7 other branches keep") ,
 s(D,"         cooking \u2014 only this item is stopped"),
 s(L,"needed ") + " " + s(V,"one decision: keep the contract, or accept the deviation"),
 s(L,"respond") + " " + s(V,"answer here") + s(D," \u00b7 /kata-status shows the full board"),
 "",
 btop,
])

# --- 3. gate rejected (standard box, rust verdict) ---
rejected = box("GATE \u2014 item \u00abconfig validator\u00bb", [
 s(L,"verdict ") + " " + s("rschip"," REJECTED ") + "  " + s(D,"fresh-context judge \u00b7 default-FAIL"),
 s(L,"because ") + " " + s(V,"12 test assertions removed while claiming green"),
 s(D,"          finding class: test-weakening \u00b7 PD-2"),
 s(L,"evidence") + " " + s(V,"tools/tests/test_kata_config.py:41-88 \u00b7 33\u219221 asserts"),
 s(L,"next    ") + " " + s(V,"targeted fix against the SAME plan \u2192 re-gate"),
 s(D,"          the plan does not change because a build failed"),
])

# --- 4. escalation prompt (ochre) ---
escalation = box("ESCALATION \u2014 W3 \u00abatomic writes\u00bb stopped and is waiting", [
 s(L,"question") + " " + s(V,"\u201cfs_atomic.py:21 docstring is stale, but that file is"),
 s(V,"          outside my owner set \u2014 fix it or flag it?\u201d"),
 "",
 s(WN,"a") + " " + s(V,"conductor fixes it at integration") + s(D," (recommended \u2014 wave-1"),
 s(D,"   precedent)"),
 s(WN,"b") + " " + s(V,"extend W3's owner set to include it"),
 s(WN,"c") + " " + s(V,"leave it \u00b7 record as an item"),
 "",
 s(D,"the worker stays paused until you (or the conductor) choose"),
])

page = """<h2>Boundary highlight + the interruption surfaces</h2>
<p class="subtitle">Top: the WAVES box with the boundary declaration as a highlighted chip (burn shown — autonomous). Below: the three moments the harness interrupts a human, in escalating weight — escalation (ochre, one worker paused) → gate rejection (rust verdict, one item stopped) → breakthrough (full rust frame, the run holds).</p>

<style>
  .term { background:#0e1218; color:#c9d1d9; padding:22px 24px; border-radius:8px; font-family:'Cascadia Code','Consolas',monospace; font-size:13px; line-height:1.40; overflow-x:auto; white-space:pre; }
  .foam { color:#F7F2E6; } .pale { color:#8fb3cc; } .blu { color:#4d87ae; } .pru { color:#2E6389; }
  .sealbg { color:#F7F2E6; background:#A6532B; font-weight:bold; }
  .chip { color:#0e1218; background:#d9a960; font-weight:bold; }
  .wchip { color:#0e1218; background:#e5c07b; font-weight:bold; }
  .rschip { color:#F7F2E6; background:#A6532B; font-weight:bold; }
  .och { color:#d9a960; } .pb { color:#CDBE9B; } .dimb { color:#44607a; }
  .gd { color:#5fd7a7; } .wn { color:#e5c07b; } .rs { color:#c2653a; }
  .txt { color:#a9b1c3; } .dim { color:#565f74; } .vl { color:#F7F2E6; } .lb { color:#4d87ae; }
</style>

<div class="term">
<span class="dim">\u256c\u256c the updated WAVES box \u2014 boundary as a chip \u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c</span>

WAVESBOX

<span class="dim">\u256c\u256c 1 \u00b7 ESCALATION \u2014 lightest: one worker paused \u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c\u256c</span>

ESCBOX

<span class="dim">\u256c\u256c 2 \u00b7 GATE REJECTED \u2014 one item stopped, run continues \u256c\u256c\u256c\u256c</span>

REJBOX

<span class="dim">\u256c\u256c 3 \u00b7 BREAKTHROUGH \u2014 heaviest: the run holds for you \u256c\u256c\u256c\u256c\u256c</span>

BREAKBOX
</div>

<p class="subtitle">Weight discipline: rust background chips appear ONLY on interruption surfaces \u2014 nowhere else in the system \u2014 so their meaning stays unmistakable. React to any of the three.</p>
"""
page = (page.replace("WAVESBOX", waves).replace("ESCBOX", escalation)
            .replace("REJBOX", rejected).replace("BREAKBOX", breakthrough))
open(r"C:\dev\projects\KataHarness\.superpowers\brainstorm\40354-1786850132\content\interrupts.html", "w", encoding="utf-8", newline="\n").write(page)
print("written, widths verified")
