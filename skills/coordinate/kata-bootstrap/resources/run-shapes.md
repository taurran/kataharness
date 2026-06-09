# Run-shape presets (data — bootstrap pre-fills these, the user may then drill down)

| runShape | mode default | modules (default) | target.kind | notes |
|---|---|---|---|---|
| individual | standard | [] | greenfield | the D24c default→go floor; one one-shot |
| batch | standard | [bakeoff] | greenfield | best-of-N (Spec B); asks `bakeoff.n` |
| version-up | standard | [graph] | existing | feature-add to an existing repo; asks `target.path` + `baselineGate`. **Execution = A4** (kata-graph not built yet — bootstrap writes the config, flags execution as A4-pending) |
| advanced | advanced | [] | greenfield | top of the ladder; surfaces cross-tier picks + external ingest |

A preset only pre-fills capability that exists. `batch` (Spec B) and `version-up` (Spec A4) are
**configurable now, executable later** — readiness reports them as not-yet-wired; bootstrap still writes a
valid config so they light up when B/A4 land. (GB5)
