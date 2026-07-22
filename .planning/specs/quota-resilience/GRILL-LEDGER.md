# GRILL-LEDGER — quota-resilience Tier 1+2 (standard tier, 2026-07-21, overnight delegation)

> Subject: provider rate-limit / token-exhaustion graceful stop + resume, Tier 1+2 of
> `REQUIREMENT.md` (operator-reviewed 2026-07-20; Tier 3 EXCLUDED — its own future grill).
> **Authority for this run:** the operator's explicit overnight delegation (2026-07-21, verbatim:
> "Asses to see if any of them require grills or anything. If we are clear to go-ahead, run it
> using full kataharness. If not, pause when you need input.") — recorded as the dual-control
> grant + mirror confirmation; mirror values = the brief §5 framing the operator reviewed.
> Every §4 branch below resolves from RECORDED operator intent + load-bearing precedent; the
> assessment table was surfaced to the operator in-conversation before they left, with the
> resolutions shown. Research grounding: the brief's §2 ground truth (verified 2026-07-20)
> plus fresh grounding of every wiring surface this session (file:line cited per entry).
> Prerequisite landed: PR #42 (dispatch stderr fix) — the provider signal now reaches the
> RESULT envelope.

### G-1 (brief Q1) — handoff kind: REUSE + additive trigger field, no enum expansion · LOCKED
- **Question:** new 4th `kind: quota` in `protocol/handoff.md`, or reuse?
- **Provenance:** the L6 no-enum-change precedent (`protocol/escalation.md:42-55` — thrash
  routing reused `human-required` unchanged); `protocol/handoff.md` frontmatter rule: additive
  fields, "absent ⇒ unknown kind; never gates".
- **Decision:** **Reuse `kind: self` and add an ADDITIVE `trigger:` frontmatter field**
  (`trigger: quota` for this feature; absent ⇒ unknown, never gates — the exact CA-L21
  additive-provenance pattern `kind:` itself used). No enum expansion; BC byte-clean.
- **Edges:** a resumer reading an old handoff sees no `trigger:` — identical to today.

### G-2 (brief Q2) — lapse threshold: FIRST classified signal; N=2 generic · LOCKED
- **Question:** N=2 flat, or provider-signal-dependent?
- **Provenance:** the premium `premium-unavailable` posture fires on FIRST 401/403
  (`kata-orchestrate/SKILL.md:973-977`); generic failures have no clean signal.
- **Decision:** **Hybrid.** A CLASSIFIED provider signal (429/402/401/403/plan-limit text)
  lapses on the FIRST occurrence (the classifier makes it clean — matching the premium
  precedent). UNCLASSIFIED generic dispatch failures lapse at **2 consecutive** (the brief's
  Tier-1 N=2), counter reset on any success. Both flow into the existing rollup.
- **Edges:** the counter is run-scoped per subsystem/provider lane, tracked by the conductor
  with a board DECISION at lapse time (durable; the advisor spend-trail pattern).

### G-3 (brief Q3) — kill-switch: generic verb + argument over the EXISTING steering reader · LOCKED
- **Question:** generic `KATA_OFF <subsystem>` vs per-subsystem verbs; kata_steer grammar vs
  new file?
- **Provenance:** `tools/kata_steer.py:86-112` `read_active_directives` already parses the
  "## Active directives" section fail-soft; D151 = the engine exists and is polled at
  boundaries; per-subsystem verbs don't scale to providers.
- **Decision:** **Generic verb with argument — `KATA_OFF <subsystem>` as a directive line in
  the EXISTING Active-directives grammar.** `kata_steer.py` stays **byte-untouched**; the new
  pure parser (`kata_quota.parse_kill_switch`) consumes `read_active_directives` output.
  Recognized subsystems this run: `advisor`, `provider` (optionally `provider:<name>`).
  Unknown subsystem ⇒ returned in an `unknown` list the conductor surfaces LOUDLY (board NOTE)
  — never silently ignored, never run-fatal (steering's own additive-never-fatal posture;
  a typo must not kill a run, but it must not vanish either).
- **Edges:** `ADVISOR_OFF`-style bare verbs are NOT recognized (one grammar, not two).

### G-4 (brief Q4) — park-and-tell; NEVER poll/retry · LOCKED
- **Question:** auto-resume (poll/retry-after) vs park-and-tell?
- **Provenance:** the operator's VERBATIM ask ("tell them plainly they're out … save state …
  pick up exactly where they left off"); the load-bearing anti-retry rule
  (`specs/context-autonomy/GRILL-LEDGER.md:358` — "Retry-per-task would recreate the exact
  Fable-outage retry pattern R2 exists to prevent"); quota resets take wall-clock hours.
- **Decision:** **Park-and-tell.** On a classified quota/rate-limit signal on the PRIMARY
  dispatch path: human-required escalation + breakthrough alert + automatic handoff write →
  graceful stop at the boundary. **No retry loop, no polling, no retry-after scheduling.**
- **Edges:** `/kata-resume` is the re-entry; the handoff's NEXT-STEP section names the parked
  task set.

### G-5 (brief Q5) — registry freshness: OUT OF SCOPE · LOCKED
- **Decision:** Tier 3 by the operator's agreed scope. This run emits a **generic, always-true
  upgrade message** (provider named when known from the RESULT envelope's `platform` field;
  "add capacity with your provider / check your plan" + the classified evidence line). **No
  URLs, no slash-commands** — a wrong/stale URL is worse than none (PD-2); the registry with
  its freshness-ownership question is the Tier-3 grill's problem.

### G-6 (brief Q6) — non-Anthropic ladders STAY EMPTY; park, never downgrade · LOCKED
- **Provenance:** the operator's verbatim ask (told + parked, NOT silently downgraded);
  `kata_models.py:72-84` empty ladders are today's recorded posture (`CLAUDE.md:25`);
  populating ladders is adapter work outside this freeze.
- **Decision:** **Confirmed: leave the ladders empty. Quota exhaustion NEVER triggers a
  model downgrade** — the response is lapse (optional subsystem) or park (primary path).
  `kata_models.py` is **byte-untouched** this run.

### G-7 (brief Q7) — signal source: dispatch-result classification ONLY · LOCKED
- **Provenance:** ground truth — no host surfaces plan quota (`kata_gauge` bridge schema is
  context-window only, brief §2a); the gauge extension would be speculative schema for a
  signal that does not exist.
- **Decision:** **The classifier consumes dispatch RESULT envelopes only** (stderr tail +
  error/raw text + status, all present since PR #42). The gauge/bridge schema is untouched;
  a future host that reports plan quota re-opens this as its own additive branch.

### G-8 — classifier home: NEW pure engine `tools/kata_quota.py` · LOCKED
- **Question:** extend `kata_dispatch` or a new module?
- **Provenance:** the pure-engine pattern (`kata_advisor.py` — stdlib-only engine + orchestrate
  prose wiring, S-19 family); `kata_dispatch` owns transport, not policy.
- **Decision:** **New `tools/kata_quota.py`, pure stdlib, deterministic, fail-closed (D136):**
  `classify_dispatch_result(result) -> {classified, reason, evidence}` (reason ∈
  rate-limited | quota-exhausted | auth; deterministic ordered pattern table; malformed
  envelope RAISES; a signal-free envelope returns classified=False — that is a computed
  result, not an unread input) · `lapse_decision(consecutive_generic_failures,
  classified_reason) -> {lapse, reason}` · `parse_kill_switch(directives) -> {off, unknown}`.
  `kata_dispatch.py` stays **byte-untouched** this run.
- **Edges:** pattern table ordered most-specific-first; case-insensitive matching over the
  envelope's text fields; evidence = the first matched line (tail-capped input already).

### G-9 — lapse-vs-park by path criticality · LOCKED
- **Question:** does a classified quota signal always park the run?
- **Provenance:** the advisor's lapse-and-continue posture (budget lapse `SKILL.md:1128-1130` —
  the run finishes unadvised); a primary coding-path worker CANNOT be done without.
- **Decision:** **Optional subsystems (advisor consults) LAPSE-AND-CONTINUE** (loud, reported
  at closeout — the operator's original ask #1). **The primary dispatch path PARKS** (G-4
  sequence). The distinction is the dispatch's consumer, decided by the conductor at the
  wiring site, not by the pure classifier.

### G-10 — telemetry: `_validate_degraded` joins the fail-closed family · LOCKED
- **Provenance:** `kata_telemetry.build_ledger_row:1405` is an unvalidated passthrough
  (`row["degraded"] = list(...)`) beside fail-closed siblings `_validate_failure_kinds:1087`,
  `_validate_verdict_by_tier:1134` — the brief §2d names matching them "the consistent choice".
- **Decision:** **Add `_validate_degraded`:** each entry a dict with exactly `{scope, reason}`,
  both non-empty strings; absent/empty ⇒ `[]`; violation RAISES `TelemetryError` (producer
  bug, the `_validate_failure_kinds` posture). `scope` stays an open string (no enum — BC with
  existing `"premium"` producers). New reasons this run: scope `"provider"`, reasons
  `"quota-exhausted" | "rate-limited" | "auth"`.
- **Edges:** grep-verified before build that no existing producer emits extra keys.

### G-11 — prose wiring surfaces (kata-orchestrate 0.14.0 → 0.15.0) · LOCKED
- **Decision:** boundary step gains the kill-switch parse (over the existing directive read) +
  operator-directed lapse; the dispatch-failure step gains classify → (G-2 thresholds) →
  (G-9 lapse or park); the park sequence reuses: `human-required` escalation (enum UNCHANGED,
  decisionNeeded carries the quota distinction + G-5 message) + the breakthrough-alert rule
  (`protocol/narration.md:68-90` — trigger already covered by its existing rows; narration.md
  UNTOUCHED) + the handoff write (G-1 additive `trigger: quota`). `protocol/handoff.md` gains
  the additive `trigger:` field row. `protocol/steering.md` gains the `KATA_OFF` verb doc.
- **Edges:** all reporting rides the existing rollup (`SKILL.md:1194-1200`) + Final-gate step 8
  (`:1518-1526`) — zero new reporting machinery.

### G-12 — BC floor · LOCKED
- **Decision:** absent signals ⇒ byte-identical behavior: the classifier only runs on FAILED /
  TIMEOUT envelopes; a run with no dispatch failures, no `KATA_OFF` directive, and no quota
  signal produces today's artifacts byte-for-byte. `kata_dispatch.py`, `kata_models.py`,
  `kata_steer.py`, `kata_adaptive.py` all **byte-untouched** (diff-verified at gate).

### Convergence pass · PASS
G-1..G-12 cohere: the classifier (G-8) is the single signal source (G-7) feeding one decision
function (G-2) whose outcome routes by path criticality (G-9) into existing machinery only
(G-1/G-4/G-11), with honesty (G-5), no-downgrade (G-6), validated telemetry (G-10), and a
byte-clean BC floor (G-12). No branch contradicts another; the operator's two verbatim asks
(kill-switch; told+parked+resumable) are each owned by exactly one path. Overcomplication
audit (standing): four engines byte-untouched; one new pure module + one validator + prose;
the registry/watchdog temptations are fenced out (G-5, Tier 3).

### ADDENDUM — adval folds (2026-07-21 overnight, fresh-context review SHIP-WITH-FIXES)
- **F1 (MAJOR, confirmed) → folded:** traceback frames at status-number lines
  (`File "x.py", line 429, in f`) classified as provider signals — `(?<!line )` lookbehind
  added to every bare status number (401/402/403/429). Pinned (7 noise shapes + 5
  real-shape survivals).
- **F2 (MAJOR, confirmed) → folded:** bare-substring auth words matched test identifiers
  (`test_unauthorized_error_test`) and file-path prose (`permission denied: /var/data/api/`) —
  `\bunauthorized\b`/`\bforbidden\b` word-bounded; permission-denied binds to `api key`. Pinned.
- **F3 (MODERATE, confirmed) → RECORDED as a known precision limit, design call for the
  operator:** kata's own vocabulary (dogfood runs testing THIS feature — assertion output
  containing "quota-exhausted"/"usage limit") can still classify a failing worker's stderr.
  The F1/F2 folds remove the worst vectors; a structural fix (HTTP-ish anchor requirement, or
  two-field corroboration) is a G-8 amendment the operator may order. Consequence of a false
  positive: premature lane lapse + a false `degraded` ledger row — loud, recoverable, never a
  silent wrong answer; the park leg additionally requires no-fallback (F5).
- **F4 (MINOR, confirmed) → folded:** `+ ` bullet recognized; a MANGLED kill-switch line
  (verb present, parse failed — `-KATA_OFF advisor`) now surfaces in `unknown` instead of
  vanishing; scoped-name grammar tightened to `provider:[a-z0-9_-]+`. Pinned.
- **F5 (MINOR, plausible) → RECORDED honesty limit:** the park leg triggers only on
  ROUTED-lane envelopes — **host-session quota exhaustion produces no RESULT envelope to
  classify and remains uncovered by this trigger** (the manual playbook + restore path still
  owns it; a host-surfaced quota signal would be the gauge-side branch G-7 explicitly left
  closed until a host reports one). Stated in the CHANGELOG honesty section.
- **F6 (governance) → PASSED:** every G-entry provenance citation verified against its cited
  file:lines; no resolution exceeds recorded operator intent/precedent. The overnight-
  delegation quote itself lives in the conversation, not the repo — flagged for the
  operator's morning confirmation.

### ELEVATE — offered IN ABSENTIA (operator asleep; pending their morning review)
Candidate: **"Same-word hazard: `budget-exhausted` (kata's internal spend budget) vs provider
quota exhaustion — the brief had to carry an explicit do-NOT-conflate warning (§2d). Durable
insight: when two subsystems share a failure vocabulary, name the namespace in the enum value
itself (`provider:quota-exhausted`) or the confusion recurs in every future consumer."**
Default if unanswered: DECLINED (declines are signal, D153).
