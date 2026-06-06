# STEERING — KataHarness

Operator → agent steering channel (mid-run direction without a restart). The harness reads this on a
cadence; entries are consumed and cleared. Empty = no active steering.

> Convention (from Anthropic's `STEER.md`): write a directive here; the running loop surfaces it,
> acts, and clears it. `AGENT_STOP` (presence of the file) is the kill-switch.

## Active directives
_(none)_
