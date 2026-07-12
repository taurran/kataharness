"""kata_web.py — KataHarness localhost web viewer (S1.5b).

Stdlib-only: http.server, json, argparse, pathlib.
NO third-party deps, NO rich.

Routes:
    GET /          → PAGE_HTML (text/html; charset=utf-8)
    GET /api/view  → JSON ViewModel (application/json)
    else           → 404

Security:
    - Binds 127.0.0.1 ONLY (never 0.0.0.0).
    - --kata-dir is _safe_path-guarded (CWE-23, consistent with kata_dash).
    - HTML is embedded (no disk file-serving over HTTP, no HTTP path-traversal).

Architecture:
    view_to_dict(view_model) -> dict   — pure, duck-typed, no I/O
    build_web_view(kata_dir) -> dict   — reads .kata/ files, builds ViewModel, serialises
    PAGE_HTML                          — self-contained HTML+CSS+JS string
    Handler(BaseHTTPRequestHandler)    — two-route request handler
    main(argv=None)                    — argparse CLI entry-point (not unit-tested)
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# ---------------------------------------------------------------------------
# Security: path-traversal guard (CWE-23, mirrored from kata_dash._safe_path)
# ---------------------------------------------------------------------------


def _safe_path(raw: str) -> Path:
    """Reject path-traversal (CWE-23) in an operator-supplied path, then resolve.

    Blocks any '..' segment — the traversal-escape primitive — so a crafted
    argument cannot climb out of the intended tree.  Consistent with kata_dash
    and gate_emit.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"kata_web: refusing path with '..' traversal: {raw!r}")
    return p.resolve()


# ---------------------------------------------------------------------------
# Pure serialisation — no I/O
# ---------------------------------------------------------------------------


def view_to_dict(view_model) -> dict:
    """Serialise a ViewModel (duck-typed) to a JSON-ready dict.

    Keys produced:
        spec, wave, phase, gate, waiting, updatedUtc,
        driftEscalations  — list [d, e]  (NOT a tuple)
        events            — list[str]
        tasks             — list of {id, label, status, percent, active,
                                     blocked, done, progressLabel}

    Duck-typed: works with the real ViewModel dataclass and SimpleNamespace
    stand-ins alike.
    """
    d, e = view_model.driftEscalations  # unpack tuple → list for JSON

    tasks = [
        {
            "id": t.id,
            "label": t.label,
            "status": t.status,
            "percent": t.percent,
            "active": t.active,
            "blocked": t.blocked,
            "done": t.done,
            "progressLabel": getattr(t, "progressLabel", ""),
        }
        for t in view_model.tasks
    ]

    return {
        "spec": view_model.spec,
        "wave": view_model.wave,
        "phase": view_model.phase,
        "gate": view_model.gate,
        "waiting": view_model.waiting,
        "updatedUtc": view_model.updatedUtc,
        "driftEscalations": [d, e],
        "events": list(view_model.events),
        "tasks": tasks,
    }


# ---------------------------------------------------------------------------
# I/O reader — mirrors kata_dash main()._read_sources()
# ---------------------------------------------------------------------------


def _error_view(detail: str = "internal") -> dict:
    """Fail-soft /api/view payload for a corrupt/unreadable board.

    S-6: a corrupt board must be operator-VISIBLE, not disguised as the idle
    "waiting for a run" state.  ``status="error"`` (distinct from ``waiting``)
    drives a visible error panel in the page.  ``waiting`` is explicitly False so
    no consumer mistakes this for idle.  Fail-soft: the caller still returns 200
    on this localhost-only dev surface — the error is in the rendered state, not
    a hidden key.
    """
    return {"status": "error", "waiting": False, "error": detail}


def build_web_view(kata_dir: str) -> dict:
    """Read .kata/board.md + .kata/state.json and return a serialised ViewModel.

    _safe_path guards kata_dir against .. traversal (CWE-23).
    If board.md is absent → board_text = "".
    If state.json is absent or contains bad JSON → state = None.
    Lazy-imports kata_dash_model so this module is importable even when the
    model module is not yet on sys.path (test isolation).
    """
    resolved = _safe_path(kata_dir)

    board_text = ""
    state = None

    board_file = resolved / "board.md"
    state_file = resolved / "state.json"

    if board_file.exists():
        try:
            board_text = board_file.read_text(encoding="utf-8")
        except OSError:
            pass

    if state_file.exists():
        try:
            raw = state_file.read_text(encoding="utf-8")
            state = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            pass

    # Lazy import — consistent with kata_dash pattern
    import kata_dash_model  # type: ignore[import]

    vm = kata_dash_model.build_view_model(board_text, state)
    return view_to_dict(vm)


# ---------------------------------------------------------------------------
# Self-contained HTML page — no CDN, no framework, inline CSS + vanilla JS
# ---------------------------------------------------------------------------

PAGE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>KATAHARNESS 改善型</title>
  <style>
    /* ── Reset & base ───────────────────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:      #0d1117;
      --surface: #161b22;
      --border:  #30363d;
      --text:    #e6edf3;
      --muted:   #8b949e;
      --active:  #58a6ff;
      --done:    #3fb950;
      --blocked: #f85149;
      --idle:    #d29922;
      --phase-hl:#58a6ff;
      --bar-fill:#58a6ff;
      --bar-empty:#30363d;
      font-family: ui-monospace, "SFMono-Regular", "Cascadia Code", Menlo, monospace;
      font-size: 14px;
    }

    body {
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 1.5rem;
    }

    /* ── Header ─────────────────────────────────────────────────────── */
    header {
      display: flex;
      align-items: baseline;
      gap: 1rem;
      margin-bottom: 1.5rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--border);
    }
    header h1 {
      font-size: 1.25rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      color: var(--text);
    }
    header .meta {
      font-size: 0.8rem;
      color: var(--muted);
    }
    header .dot {
      width: 8px; height: 8px;
      border-radius: 50%;
      background: var(--done);
      display: inline-block;
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50%       { opacity: 0.4; }
    }

    /* ── Cards ──────────────────────────────────────────────────────── */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1rem;
      margin-bottom: 1rem;
    }
    .card-title {
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 0.75rem;
    }

    /* ── Idle state ─────────────────────────────────────────────────── */
    .idle {
      text-align: center;
      padding: 3rem 1rem;
      color: var(--idle);
    }
    .idle .icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
    .idle p { color: var(--muted); font-size: 0.85rem; margin-top: 0.25rem; }
    /* Error state — distinct from idle so a corrupt board is not read as "waiting". */
    .idle.error { color: var(--blocked); }

    /* ── Task list ──────────────────────────────────────────────────── */
    .task-row {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.35rem 0;
      border-bottom: 1px solid var(--border);
    }
    .task-row:last-child { border-bottom: none; }
    .task-label {
      min-width: 8rem;
      max-width: 14rem;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-weight: 500;
    }
    .bar {
      font-family: inherit;
      letter-spacing: -0.02em;
      white-space: nowrap;
    }
    .bar-fill   { color: var(--bar-fill); }
    .bar-empty  { color: var(--bar-empty); }
    .pct        { min-width: 3rem; text-align: right; color: var(--muted); font-size: 0.85rem; }
    .status-chip {
      font-size: 0.75rem;
      padding: 0.1rem 0.45rem;
      border-radius: 999px;
      font-weight: 500;
      white-space: nowrap;
    }
    .chip-active   { background: rgba(88,166,255,0.15); color: var(--active); }
    .chip-done     { background: rgba(63,185,80,0.15);  color: var(--done); }
    .chip-blocked  { background: rgba(248,81,73,0.15);  color: var(--blocked); }
    .chip-default  { background: rgba(139,148,158,0.15); color: var(--muted); }
    .progress-label { font-size: 0.75rem; color: var(--muted); margin-left: 0.25rem; }

    /* ── Phase ribbon ───────────────────────────────────────────────── */
    .ribbon {
      display: flex;
      flex-wrap: wrap;
      gap: 0.25rem;
      align-items: center;
      justify-content: center;
    }
    .ribbon-phase {
      padding: 0.2rem 0.6rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      color: var(--muted);
      background: transparent;
    }
    .ribbon-phase.active {
      color: var(--phase-hl);
      background: rgba(88,166,255,0.12);
      border: 1px solid rgba(88,166,255,0.4);
    }
    .ribbon-arrow { color: var(--muted); font-size: 0.7rem; }

    /* ── Board events ───────────────────────────────────────────────── */
    .events-list { list-style: none; }
    .events-list li {
      font-size: 0.78rem;
      color: var(--muted);
      padding: 0.2rem 0;
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .events-list li:last-child { border-bottom: none; }
    .events-empty { color: var(--muted); font-size: 0.8rem; }

    /* ── Gate + drift row ───────────────────────────────────────────── */
    .status-row {
      display: flex;
      gap: 1.5rem;
      flex-wrap: wrap;
    }
    .status-item { font-size: 0.82rem; }
    .status-label { color: var(--muted); margin-right: 0.3rem; }
    .status-value { color: var(--text); font-weight: 500; }

    /* ── Footer ─────────────────────────────────────────────────────── */
    footer {
      margin-top: 1.5rem;
      font-size: 0.72rem;
      color: var(--muted);
      text-align: center;
      border-top: 1px solid var(--border);
      padding-top: 0.75rem;
    }
  </style>
</head>
<body>

  <header>
    <h1>KATAHARNESS 改善型</h1>
    <span class="meta" id="meta-spec"></span>
    <span class="dot" id="live-dot" title="polling /api/view every 1000 ms"></span>
  </header>

  <div id="root">
    <div class="idle">
      <div class="icon">⏳</div>
      <strong>Loading…</strong>
      <p>Connecting to /api/view</p>
    </div>
  </div>

  <footer>polling /api/view every 1000 ms · bind 127.0.0.1 · KATAHARNESS 改善型</footer>

  <script>
    // ── Render helpers ────────────────────────────────────────────────
    const PHASES = ["GRILL", "FREEZE", "EXECUTE", "EVALUATE", "HANDOFF", "IMPROVE"];

    function renderBar(percent, width) {
      width = width || 16;
      var filled = Math.round(percent / 100 * width);
      filled = Math.max(0, Math.min(width, filled));
      var empty  = width - filled;
      var s = "";
      for (var i = 0; i < filled; i++) s += "▰";
      for (var i = 0; i < empty;  i++) s += "▱";
      return s;
    }

    function chipClass(status, active, blocked, done) {
      if (done)    return "chip-done";
      if (blocked) return "chip-blocked";
      if (active)  return "chip-active";
      return "chip-default";
    }

    function el(tag, attrs, ...children) {
      var e = document.createElement(tag);
      for (var k in (attrs || {})) {
        if (k === "className") e.className = attrs[k];
        else if (k === "textContent") e.textContent = attrs[k];
        else e.setAttribute(k, attrs[k]);
      }
      children.forEach(function(c) {
        if (c == null) return;
        // Coerce primitives (string AND number) to text nodes — a numeric child
        // like driftEscalations[0]=0 must not reach appendChild(0) (TypeError).
        if (typeof c === "string" || typeof c === "number") {
          e.appendChild(document.createTextNode(String(c)));
        } else {
          e.appendChild(c);
        }
      });
      return e;
    }

    function renderIdle() {
      return el("div", {className: "idle"},
        el("div", {className: "icon"}, "⏳"),
        el("strong", {textContent: "idle — no active run"}),
        el("p", {textContent: "Waiting for an orchestrated kata run…"})
      );
    }

    function renderError(detail) {
      return el("div", {className: "idle error"},
        el("div", {className: "icon"}, "⚠"),
        el("strong", {textContent: "error — board could not be read"}),
        el("p", {textContent: "The kata board is corrupt or unreadable" +
          (detail ? " (" + detail + ")" : "") + " — this is not an idle run."})
      );
    }

    function renderTaskRow(task) {
      var bar   = renderBar(task.percent, 16);
      var filled = Math.round(task.percent / 100 * 16);
      var barFill  = bar.slice(0, filled);
      var barEmpty = bar.slice(filled);

      var barSpan = el("span", {className: "bar"},
        el("span", {className: "bar-fill", textContent: barFill}),
        el("span", {className: "bar-empty", textContent: barEmpty})
      );
      var pctSpan   = el("span", {className: "pct", textContent: task.percent + "%"});
      var chip      = el("span", {
        className: "status-chip " + chipClass(task.status, task.active, task.blocked, task.done),
        textContent: task.status
      });

      var row = el("div", {className: "task-row"},
        el("span", {className: "task-label", textContent: task.label}),
        barSpan,
        pctSpan,
        chip
      );
      if (task.progressLabel) {
        row.appendChild(el("span", {className: "progress-label", textContent: task.progressLabel}));
      }
      return row;
    }

    function renderRibbon(activePhase) {
      var ribbon = el("div", {className: "ribbon"});
      PHASES.forEach(function(p, i) {
        if (i > 0) ribbon.appendChild(el("span", {className: "ribbon-arrow"}, "▸"));
        var cls = "ribbon-phase" + (p === activePhase ? " active" : "");
        ribbon.appendChild(el("span", {className: cls, textContent: p}));
      });
      return ribbon;
    }

    function renderView(data) {
      var root = document.getElementById("root");

      // ---- header meta ----
      var metaEl = document.getElementById("meta-spec");
      if (data.spec) {
        metaEl.textContent = data.spec +
          (data.wave ? "  ·  wave " + data.wave : "") +
          (data.updatedUtc ? "  ·  " + data.updatedUtc : "");
      } else {
        metaEl.textContent = data.updatedUtc || "";
      }

      // ---- error path (corrupt / unreadable board) ----
      // Distinct from idle: a corrupt board must NOT render as "waiting for a run".
      if (data.status === "error") {
        root.innerHTML = "";
        root.appendChild(renderError(data.error));
        return;
      }

      // ---- waiting / idle path ----
      if (data.waiting) {
        root.innerHTML = "";
        root.appendChild(renderIdle());
        return;
      }

      // ---- build DOM ----
      var frag = document.createDocumentFragment();

      // Tasks card
      var taskCard = el("div", {className: "card"});
      taskCard.appendChild(el("div", {className: "card-title"}, "Tasks"));
      if (data.tasks && data.tasks.length > 0) {
        data.tasks.forEach(function(t) {
          taskCard.appendChild(renderTaskRow(t));
        });
      } else {
        taskCard.appendChild(el("p", {className: "events-empty"}, "No tasks"));
      }
      frag.appendChild(taskCard);

      // Loop ribbon card
      var ribbonCard = el("div", {className: "card"});
      ribbonCard.appendChild(el("div", {className: "card-title"}, "Loop Phase"));
      ribbonCard.appendChild(renderRibbon(data.phase));
      frag.appendChild(ribbonCard);

      // Board events card
      var eventsCard = el("div", {className: "card"});
      eventsCard.appendChild(el("div", {className: "card-title"}, "Board Events"));
      if (data.events && data.events.length > 0) {
        var ul = el("ul", {className: "events-list"});
        // show last 5 events
        var slice = data.events.slice(-5);
        slice.forEach(function(ev) {
          ul.appendChild(el("li", {textContent: ev}));
        });
        eventsCard.appendChild(ul);
      } else {
        eventsCard.appendChild(el("span", {className: "events-empty"}, "No events yet"));
      }
      frag.appendChild(eventsCard);

      // Gate + drift card
      var statusCard = el("div", {className: "card"});
      statusCard.appendChild(el("div", {className: "card-title"}, "Gate & Drift"));
      var statusRow = el("div", {className: "status-row"});
      statusRow.appendChild(el("span", {className: "status-item"},
        el("span", {className: "status-label"}, "gate"),
        el("span", {className: "status-value"}, data.gate || "—")
      ));
      var de = data.driftEscalations || [0, 0];
      statusRow.appendChild(el("span", {className: "status-item"},
        el("span", {className: "status-label"}, "drift"),
        el("span", {className: "status-value"}, de[0])
      ));
      statusRow.appendChild(el("span", {className: "status-item"},
        el("span", {className: "status-label"}, "escalations"),
        el("span", {className: "status-value"}, de[1])
      ));
      statusCard.appendChild(statusRow);
      frag.appendChild(statusCard);

      // Swap out root content
      root.innerHTML = "";
      root.appendChild(frag);
    }

    // ── Poll loop — fetch /api/view every 1000 ms ─────────────────────
    function poll() {
      fetch("/api/view")
        .then(function(r) { return r.json(); })
        .then(function(data) { renderView(data); })
        .catch(function(err) { console.error("kata_web poll error:", err); });
    }

    poll();  // immediate first fetch
    setInterval(poll, 1000);
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# HTTP handler — two routes only; no disk file-serving
# ---------------------------------------------------------------------------


class Handler(BaseHTTPRequestHandler):
    """Minimal two-route handler.

    Routes:
        GET /          → 200 text/html  PAGE_HTML
        GET /api/view  → 200 application/json  build_web_view(self.server.kata_dir)
        *              → 404

    Security: no disk file-serving; kata_dir is set on the server instance
    and is already _safe_path-validated before the server starts.
    """

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]  # strip query string

        if path == "/":
            body = PAGE_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path == "/api/view":
            try:
                data = build_web_view(self.server.kata_dir)
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            except Exception:
                # S-6: surface a DISTINCT error state — a corrupt/unreadable board
                # must not masquerade as the idle "waiting for a run" state (which
                # hid the failure in a key the page never rendered).  Fail-soft:
                # still 200 on this localhost-only dev surface; the page renders a
                # visible error panel (status="error"), never an idle spinner.
                body = json.dumps(_error_view()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

    def log_message(self, fmt: str, *args) -> None:  # type: ignore[override]
        """Silence the default stderr request logging."""
        pass


# ---------------------------------------------------------------------------
# CLI entry-point (thin glue — NOT unit-tested)
# ---------------------------------------------------------------------------


def main(argv: list | None = None) -> None:
    """CLI: serve the web viewer for a .kata directory.

    Security: binds 127.0.0.1 ONLY — never 0.0.0.0.
    """
    parser = argparse.ArgumentParser(
        prog="kata_web",
        description="KataHarness localhost web viewer — serve a live HTML dashboard for .kata/.",
    )
    parser.add_argument(
        "--kata-dir",
        default=".kata",
        metavar="DIR",
        help="Path to the .kata/ directory (default: .kata)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        metavar="PORT",
        help="Port to bind on 127.0.0.1 (default: 8765)",
    )
    args = parser.parse_args(argv)

    # Validate kata_dir before we start serving
    kata_dir_path = _safe_path(args.kata_dir)

    # Reconfigure stdout for UTF-8 (handles Windows console encoding edge-cases)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError, OSError):
        pass

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.kata_dir = str(kata_dir_path)  # type: ignore[attr-defined]

    print(f"http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
