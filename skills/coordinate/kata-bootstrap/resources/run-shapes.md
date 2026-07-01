# Run-shape presets (data — bootstrap pre-fills these, the user may then drill down)

| runShape | mode default | modules (default) | target.kind | notes |
|---|---|---|---|---|
| individual | standard | [] | greenfield | the D24c default→go floor; one one-shot |
| batch | standard | [bakeoff] | greenfield | best-of-N (Spec B); asks `bakeoff.n` |
| version-up | standard | [graph] | existing | feature-add to an existing repo; asks `target.path` + `baselineGate`. **Built + wired** — execution via `kata-graph` ingestion. |
| debug | standard | [graph, kata/module/debug] | existing | systematic whole-codebase debug (peer of version-up); asks `target.path` + `baselineGate`. **Built + wired (P1–P3)** — comprehension (`kata-comprehend`) → deviation pipeline (`kata-deviate`) → characterization + drift gate (`kata-characterize`) → debrief (`kata-debrief`), gated on module `kata/module/debug`. |
| advanced | advanced | [] | greenfield | top of the ladder; surfaces cross-tier picks + external ingest |

A preset only pre-fills capability that exists. `version-up` and `debug` are **built and wired** (P1–P3 for debug).
`batch` (Spec B) writes a valid config now, but its **concurrent** best-of-N arms remain execution-pending
(sequential + k-repeat is built) — it lights up fully when the concurrent-arm capability lands. (GB5)
