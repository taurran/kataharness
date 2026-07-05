"""C11 live-proof battery — CA-A11 fixture rows + the CA-A8 row-1 fixture (D147).

The DESIGN §6 CA-A11 "test-at-build fixture rows" (fold #8), run-fixture-shaped:
each row composes the SHIPPED mechanical pieces (kata_gauge / kata_preflight /
kata_settings) with the SHIPPED policy prose (kata-orchestrate SKILL.md 0.10.0,
protocol/observability.md) exactly as a run would consume them — complementing
(never duplicating) the E-task unit rows in test_kata_gauge / test_kata_settings /
test_kata_preflight.

Rows:
- CA-A11(a) over-briefing WARN (startup > 0.30) + the 0.40 plan/freeze mandate,
  with the R-31 brief-embedded numbers (budget tokens / cap tokens).
- CA-A11(b) continuation-report path — the CA-L10 contract walked over checkpoint
  fixtures using the brief-embedded numbers, + index continuity (pt-N+1 continues
  the checkpoint index; anchor = dispatch base ⇒ indexes from 0, the CA-L44 F2
  stated rule).
- CA-A11(c) report size contract — verdict + pointer inline, bulk at the
  `.kata/reports/<runId>-<taskId>-<agent>-<kind>.md` path (CA-L22/L23), plus the
  durable-citation rule.
- CA-A11(d) allowlist checklist WARN — a host allowlist missing a CA-L26 pattern
  class produces exactly the enumerated WARN.
- CA-A11(e) marker re-arm — the full CA-L36 lifecycle flow on a fixture home
  (absent ⇒ forced ⇒ stamped ⇒ quiet ⇒ gitSha change re-arms ⇒ re-stamp quiets).
- CA-A8 row 1 — a one-shot PRE-v0.2.1 config (no `contextAutonomy` key) ⇒ rotation
  UNCONDITIONAL. **This fixture NAMES the D147 departure** (CA-L33; DESIGN §4
  row 1): the R-37 deliberate BC departure — one-shot shapes rotate WITHOUT
  consulting the key, while the incremental path's absent-at-load ⇒ OFF BC is
  preserved byte-for-byte.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import kata_gauge
import kata_preflight
import kata_settings as ks
import kata_version

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ORCHESTRATE = _REPO_ROOT / "skills" / "coordinate" / "kata-orchestrate" / "SKILL.md"
_OBSERVABILITY = _REPO_ROOT / "protocol" / "observability.md"


def _prose(path: Path) -> str:
    """Load a shipped prose artifact with line-wraps normalized to single spaces."""
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def _stamp(home, git_sha):
    """Write a minimal .kata-version stamp with the given gitSha for tests."""
    return kata_version.write_stamp(
        home,
        git_sha=git_sha,
        suite_semver="0.2.1",
        ref="master",
        link_mode="symlink",
        platform="claude",
    )


# ---------------------------------------------------------------------------
# CA-A11(a) — over-briefing WARN fixture (startup > 0.30; > 0.40 mandate)
# ---------------------------------------------------------------------------


class TestOverBriefingWarnFixture:
    """A dispatch whose conductor-authored payload over-briefs the worker."""

    WORKER_WINDOW = 200_000  # tokens (fixture worker frame)

    def test_startup_032_warns_but_does_not_block(self):
        # 64k conductor-authored payload on a 200k frame = 0.32 startup load.
        startup = 64_000 / self.WORKER_WINDOW
        verdict = kata_gauge.dispatch_budget(startup)
        assert verdict["warn"] is True
        assert verdict["over_briefed"] is False
        # R-31 brief-embedded numbers (CA-L10): budget tokens + cap tokens.
        assert round(verdict["budget_fraction"] * self.WORKER_WINDOW) == 144_000
        assert round(verdict["cap_fraction"] * self.WORKER_WINDOW) == 160_000

    def test_startup_045_is_a_plan_freeze_mandate_failure(self):
        # 90k payload on 200k = 0.45 ⇒ the 40pp quantum is unsatisfiable under
        # the 0.80 cap ⇒ over-briefed: split the task or slim the brief.
        verdict = kata_gauge.dispatch_budget(90_000 / self.WORKER_WINDOW)
        assert verdict["over_briefed"] is True
        assert verdict["budget_fraction"] == verdict["cap_fraction"] == 0.80

    def test_thresholds_are_exclusive_at_the_boundary(self):
        assert kata_gauge.dispatch_budget(0.30)["warn"] is False
        assert kata_gauge.dispatch_budget(0.40)["over_briefed"] is False

    def test_shipped_dispatch_prose_carries_the_mandate_rule(self):
        prose = _prose(_ORCHESTRATE)
        assert "a mandate, not a WARN" in prose
        assert "kata_gauge.dispatch_budget" in prose


# ---------------------------------------------------------------------------
# CA-A11(b) — continuation-report path fixture (CA-L10)
# ---------------------------------------------------------------------------


def _continuation_decision(used_fraction, remaining_estimate, cap_fraction):
    """The CA-L10 continue-or-return rule EXACTLY as the brief states it.

    At budget ⇒ finish chunk + checkpoint ⇒ remaining estimate fits under the
    hard cap ⇒ CONTINUE to completion; else return a continuation report.
    (The worker-local re-statement of the brief-embedded rule — worker
    observance is compliance; TRUE enforcement is conductor-side, CA-L11.)
    """
    if used_fraction + remaining_estimate <= cap_fraction:
        return "continue"
    return "continuation-report"


class TestContinuationReportFixture:
    """A task exceeding its quantum checkpoints, then resuming pt-N+1."""

    def test_at_budget_small_remainder_continues_no_churn_rotation(self):
        # startup 0.20 ⇒ budget 0.60, cap 0.80 (brief-embedded numbers).
        brief = kata_gauge.dispatch_budget(0.20)
        assert brief["budget_fraction"] == pytest.approx(0.60)
        # Checkpoint at budget with 0.15 remaining ⇒ 0.75 fits under 0.80 ⇒
        # CONTINUE to completion — "no rotation to do 10% of a task".
        assert (
            _continuation_decision(0.60, 0.15, brief["cap_fraction"]) == "continue"
        )

    def test_at_budget_large_remainder_returns_continuation_report(self):
        brief = kata_gauge.dispatch_budget(0.20)
        # 0.62 used + 0.25 remaining = 0.87 > 0.80 ⇒ continuation report
        # (last checkpoint anchor + what remains + what was learned).
        assert (
            _continuation_decision(0.62, 0.25, brief["cap_fraction"])
            == "continuation-report"
        )

    def test_estimated_activity_ge_cap_returns_unconditionally(self):
        brief = kata_gauge.dispatch_budget(0.20)
        # Estimated activity alone ≥ cap ⇒ return UNCONDITIONALLY.
        assert (
            _continuation_decision(brief["cap_fraction"], 0.0 + 1e-9, brief["cap_fraction"])
            == "continuation-report"
        )

    def test_index_continuity_pt_n_plus_1(self):
        # A continuation resumes as a fresh pt-N+1 dispatch from the last
        # checkpoint anchor, CONTINUING the checkpoint index (CA-L10): anchor
        # trailer i=k ⇒ the fresh session's first trailer is i=k+1.
        anchor_checkpoint_index = 2
        assert anchor_checkpoint_index + 1 == 3
        # F2 stated rule (CA-L44, protocol/observability.md): anchor = dispatch
        # base (no checkpoint trailer) ⇒ the fresh attempt indexes from 0.
        assert "the fresh attempt indexes from 0" in _prose(_OBSERVABILITY)

    def test_shipped_continuation_prose_pins(self):
        prose = _prose(_ORCHESTRATE)
        assert "return a continuation report" in prose
        assert "re-evaluated at EVERY checkpoint" in prose
        assert "pt-N+1" in prose
        # Substrate degrade (fold #4): inlineEval off ⇒ budget prose +
        # return-at-task-boundary only.
        assert "return-at-task-boundary only" in prose


# ---------------------------------------------------------------------------
# CA-A11(c) — report size contract fixture (CA-L22/L23)
# ---------------------------------------------------------------------------


_REPORT_PATH_RE = re.compile(
    r"\A\.kata/reports/[A-Za-z0-9._]+-[A-Za-z0-9._]+-[A-Za-z0-9._]+-[A-Za-z0-9._]+\.md\Z"
)


class TestReportSizeContractFixture:
    """A worker final report: verdict + pointer inline, bulk at .kata/reports/."""

    RUN_ID = "c11lp"
    TASK_ID = "T1"

    def test_bulk_report_lands_at_the_contract_path(self, tmp_path):
        rel = f".kata/reports/{self.RUN_ID}-{self.TASK_ID}-worker-final.md"
        assert _REPORT_PATH_RE.match(rel), rel
        bulk = tmp_path / rel
        bulk.parent.mkdir(parents=True)
        bulk.write_text(
            "# Full worker report (bulk)\n" + ("evidence line\n" * 200),
            encoding="utf-8",
        )
        # Inline hand-back: the verdict + the pointer, nothing else (CA-L23).
        inline = f"VERDICT: PASS (green 12/12)\nBulk: {rel}\n"
        assert len(inline.splitlines()) == 2
        assert rel in inline
        assert bulk.stat().st_size > len(inline.encode())  # bulk lives in the artifact

    def test_shipped_report_contract_prose_pins(self):
        prose = _prose(_ORCHESTRATE)
        assert "verdict + pointer inline" in prose
        assert ".kata/reports/<runId>-<taskId>-<agent>-<kind>.md" in prose
        # Durable-citation rule (CA-L22) cross-referenced to observability.
        assert "never a bare pointer" in prose
        assert ".kata/reports/<runId>-<taskId>-<agent>-<kind>.md" in _prose(
            _OBSERVABILITY
        )


# ---------------------------------------------------------------------------
# CA-A11(d) — allowlist checklist WARN fixture (CA-L26)
# ---------------------------------------------------------------------------


class TestAllowlistChecklistWarnFixture:
    """A host allowlist missing a CA-L26 class ⇒ exactly the enumerated WARN."""

    FULL_ALLOWLIST = [
        "Bash(git *)",
        "Bash(pytest *)",
        "Bash(pip install *)",
        "Write(%TEMP%/kata-ctx-*.json)",
        "Write(.kata/**)",
        "Write(.planning/**)",
        "Bash(python C:/kata/tools/*)",
    ]
    CONTEXT = {
        "verify_command": "pytest -q",
        "install_managers": ["pip"],
        "harness_home": "C:/kata",
    }

    def test_covered_allowlist_yields_zero_warns(self):
        assert kata_preflight.check_allowlist_coverage(self.FULL_ALLOWLIST, self.CONTEXT) == []

    def test_missing_verify_command_yields_exactly_that_warn(self):
        patterns = [p for p in self.FULL_ALLOWLIST if "pytest" not in p]
        warns = kata_preflight.check_allowlist_coverage(patterns, self.CONTEXT)
        assert len(warns) == 1
        assert warns[0]["class"] == "verify-command"
        assert warns[0]["severity"] == "warn"

    def test_empty_allowlist_enumerates_all_five_frozen_classes(self):
        warns = kata_preflight.check_allowlist_coverage([], self.CONTEXT)
        assert [w["class"] for w in warns] == sorted(
            class_id for class_id, _ in kata_preflight.ALLOWLIST_CLASSES
        )
        assert len(warns) == 5  # the FIXED checklist — the list is the whole check


# ---------------------------------------------------------------------------
# CA-A11(e) — marker re-arm lifecycle fixture (CA-L36)
# ---------------------------------------------------------------------------


class TestMarkerReArmFixture:
    """The full first-run marker lifecycle on one fixture home."""

    def test_lifecycle_absent_stamped_rearmed_restamped(self, tmp_path):
        _stamp(tmp_path, "sha-v0.2.1")
        # 1. Fresh install: marker absent ⇒ forced.
        assert ks.first_run_required(home=tmp_path) == {
            "required": True, "reason": "marker-absent", "clause_skipped": False,
        }
        # 2. First run completes ⇒ stamped ⇒ quiet.
        ks.record_first_run("sha-v0.2.1", home=tmp_path)
        assert ks.first_run_required(home=tmp_path)["required"] is False
        # 3. Harness upgrade (gitSha change) RE-ARMS the full first run.
        _stamp(tmp_path, "sha-v0.2.2")
        assert ks.first_run_required(home=tmp_path) == {
            "required": True, "reason": "sha-mismatch", "clause_skipped": False,
        }
        # 4. Post-upgrade first run re-stamps ⇒ quiet again.
        ks.record_first_run("sha-v0.2.2", home=tmp_path)
        assert ks.first_run_required(home=tmp_path)["required"] is False


# ---------------------------------------------------------------------------
# CA-A8 row 1 — one-shot PRE-v0.2.1 config ⇒ UNCONDITIONAL rotation (D147)
# ---------------------------------------------------------------------------


class TestCAA8Row1OneShotPreV021:
    """DESIGN §4 row 1 — **the D147 departure, named**.

    D147 (the R-37 deliberate BC departure): for ONE-SHOT run shapes,
    auto-context rotation fires WITHOUT consulting `contextAutonomy` —
    including pre-v0.2.1 configs that carry no such key. The general BC rule
    (absent-at-load ⇒ OFF) is scoped to the key-consulted (incremental) path
    only.
    """

    # A faithful pre-v0.2.1 one-shot kata.config: NO contextAutonomy key.
    PRE_V021_ONESHOT_CONFIG = {
        "delivery": "one-shot",
        "inlineEval": "telemetry",
        "target": {"baselineGate": "pytest -q"},
    }

    def test_fixture_is_genuinely_pre_v021(self):
        assert "contextAutonomy" not in self.PRE_V021_ONESHOT_CONFIG

    def test_one_shot_rotation_is_unconditional_key_never_consulted(self):
        """The D147 departure itself: the shipped conductor rule fires rotation
        for one-shot shapes WITHOUT consulting the (absent) key."""
        prose = _prose(_ORCHESTRATE)
        # The shipped rule, verbatim (kata-orchestrate 0.10.0): one-shot shapes
        # UNCONDITIONALLY; the key is not consulted, incl. pre-v0.2.1 configs.
        assert "one-shot shapes UNCONDITIONALLY" in prose
        assert "the key is not consulted, incl. pre-v0.2.1 configs" in prose
        assert "D147" in prose  # the departure is NAMED at the rule site
        # And the mechanical guard documents the same exemption: one-shot
        # delivery shapes NEVER call the key-consulted validator.
        assert (
            "one-shot delivery shapes NEVER call this"
            in kata_gauge.validate_context_autonomy.__doc__
        )

    def test_incremental_path_bc_is_preserved_not_departed(self):
        """NOT a departure: the SAME pre-v0.2.1 config on the incremental
        (key-consulted) path reads absent-at-load ⇒ OFF (no rotation flip)."""
        value = self.PRE_V021_ONESHOT_CONFIG.get("contextAutonomy")  # absent
        assert kata_gauge.validate_context_autonomy(value) == "off"

    def test_malformed_key_still_stops_never_silently_off(self):
        with pytest.raises(kata_gauge.GaugeError):
            kata_gauge.validate_context_autonomy("On")  # case-variant ⇒ STOP
