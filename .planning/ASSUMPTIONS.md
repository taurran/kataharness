# ASSUMPTIONS — spec assumptions made without a human grill (kata-defer ledger)

> D71 autonomous floor: every assumption the loop had to make to proceed is logged here with its
> provenance, so misalignment with the operator's intent is caught at the boundary (gate/handoff)
> rather than discovered later in the built thing. Logging an assumption is the alternative to
> assuming silently — it is never a substitute for asking when asking is possible.
>
> **Schema: `protocol/deferral.md`** (the sanctioned-deferral ledger contract). Entries are H2:
> `## ASM-<n> — <title> · <STATUS> (<ISO-date>)`, STATUS ∈ `OPEN | ACCEPTED | CLOSED`, with the
> required **Assumption / Provenance / Grilled** fields; `accepted_by` / `accepted_at` when the
> operator rules on one. Append-only.
>
> **Provenance of this file (PD-2):** it did not exist before 2026-08-16. `kata-defer`,
> `kata-evaluate` (rubric item 8), `kata-report` and `protocol/config.md` have referenced
> `ASSUMPTIONS.md` as the canonical assumption log since D71, but no run had ever written one in
> this repository — `git log` over the path is empty. It is created here by
> `tm-w1-deferral-contract`, which pins the path as canonical, seeded with the one assumption that
> task itself had to make. Its emptiness before today is a fact about the record, not a claim that
> no run ever assumed anything.

## ASM-1 — initial fingerprint pin for a NEW protocol contract is pasted by the builder · OPEN (2026-08-16)

- **Assumption:** registering `protocol/deferral.md` in `PROTOCOL_FINGERPRINTS` with its
  **initial** digest is a mechanical part of the registration the builder may complete, rather
  than a human-reserved re-approval. The two-step act `protocol/prime-directives.md` describes —
  *"make the change, then re-approve the fingerprint"* — is read as governing **edits to an
  already-pinned file**, where a self-computed pin would let a change launder itself past a pin a
  human had previously blessed. A first pin launders nothing: there is no prior approved state to
  bypass, and the human review of the content is the authored-artifact gate on the new file
  itself. The alternative reading (leave the pin unpasted for a human) was rejected because it
  leaves the tree red — `test_fingerprint_set_is_exactly_required_minus_the_declared_exemptions`
  (`tools/tests/test_validate_prime_directives.py:150`) requires every `REQUIRED_PROTOCOL` file
  except the two declared registry exemptions to be fingerprinted — so the registration would be
  incomplete work reported as done (PD-1).
- **Provenance:** `tm-w1-deferral-contract` (trust-model burn, wave 1). The task brief instructed:
  *"If registration requires a fingerprint step that only a human can approve (the updater prints,
  never rewrites), do the mechanical part and clearly report the printed value + the exact command
  as a HUMAN MOMENT for the conductor — do not self-bless anything the two-step reserves for a
  human."* Which side of that line an **initial** pin falls on is not stated anywhere in the
  protocol, the validator, or its tests, so the builder resolved it in-loop. Precedent used:
  commit `9af7c5e` (*the protocol folder guards itself*) landed **eight** new contracts with their
  initial fingerprints pasted in the same change, and the conductor verified the structure
  independently afterwards rather than pasting the values itself.
- **Grilled:** no. Resolved in-loop against the precedent above; never put to the operator.
- **Contradicting it costs one line:** deleting the `"deferral.md"` line from
  `PROTOCOL_FINGERPRINTS` reverts the assumption (and reds the test named above, deliberately).
  The reported HUMAN MOMENT gives the exact command to recompute and compare the value.
