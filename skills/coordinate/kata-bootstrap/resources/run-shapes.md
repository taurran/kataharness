# Run-shape presets (data — bootstrap pre-fills these, the user may then drill down)

| runShape | mode default | modules (default) | target.kind | notes |
|---|---|---|---|---|
| individual | standard | [] | greenfield | the D24c default→go floor; one one-shot |
| batch | standard | [bakeoff] | greenfield | best-of-N (Spec B); asks `bakeoff.n` |
| version-up | standard | [graph] | existing | feature-add to an existing repo; asks `target.path` + `baselineGate`. **Execution = A4** (kata-graph not built yet — bootstrap writes the config, flags execution as A4-pending) |
| debug | standard | [graph, kata/module/debug] | existing | systematic whole-codebase debug (peer of version-up); asks `target.path` + `baselineGate`. **Execution-pending (P1 foundation only)** — readiness flags this execution-pending; bootstrap writes a valid config so it lights up when the full debug pipeline (P2: deviation pipeline + drift gate) lands. |
| advanced | advanced | [] | greenfield | top of the ladder; surfaces cross-tier picks + external ingest |

A preset only pre-fills capability that exists. `batch` (Spec B), `version-up` (Spec A4), and `debug` (P1
foundation only — P2 wires the full deviation pipeline + drift gate) are **configurable now, executable later**
— readiness reports them as not-yet-wired; bootstrap still writes a valid config so they light up when the
respective capabilities land. (GB5)
