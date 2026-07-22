"""Tests for tools/kata_quota.py — the quota-resilience Tier 1+2 pure engine.

Grill contract under pin: `.planning/specs/quota-resilience/GRILL-LEDGER.md` G-2/G-3/G-5/
G-7/G-8. Real-world provider error shapes are exercised through classify_dispatch_result
via REAL kata_dispatch envelopes (build_result / dispatch with a stub runner) so the
integration seam — envelope field names — is pinned, not assumed.
"""

from __future__ import annotations

import pytest

import kata_dispatch as kd
import kata_quota as kq


def _envelope(status="failed", stderr=None, error=None, raw="", platform="codex"):
    """A RESULT envelope the way dispatch() builds them (payload keys optional)."""
    payload = {}
    if error is not None:
        payload["error"] = error
    if stderr is not None:
        payload["stderr"] = stderr
    return kd.build_result("t1", "coder", platform, "m", status, payload, raw=raw)


# ---------------------------------------------------------------------------
# classify_dispatch_result — the pattern table over real-world shapes (G-8)
# ---------------------------------------------------------------------------

class TestClassify:
    @pytest.mark.parametrize("stderr,expected", [
        # OpenAI-style 429 JSON
        ('{"error": {"message": "Rate limit reached for gpt-5 (429)", "type": "requests"}}',
         "rate-limited"),
        # Anthropic overloaded
        ("Error: overloaded_error: the API is temporarily overloaded", "rate-limited"),
        ("HTTP 429 Too Many Requests; Retry-After: 60", "rate-limited"),
        # codex 402 / credit class (docs/platforms/codex-cli.md)
        ("error: insufficient credit (HTTP 402); visit your billing page", "quota-exhausted"),
        ("You have reached your usage limit. Upgrade your plan to continue.", "quota-exhausted"),
        ("Your credit balance is too low to complete this request.", "quota-exhausted"),
        ("plan limit exceeded: out of tokens for this billing period", "quota-exhausted"),
        # auth class
        ("401 Unauthorized: invalid x-api-key", "auth"),
        ("authentication_error: API key is invalid or expired", "auth"),
        ("HTTP 403 Forbidden", "auth"),
    ])
    def test_real_world_shapes(self, stderr, expected):
        got = kq.classify_dispatch_result(_envelope(stderr=stderr))
        assert got["classified"] is True
        assert got["reason"] == expected
        assert got["evidence"]  # a non-empty matched line
        assert got["platform"] == "codex"

    def test_unclassifiable_failure_stays_generic(self):
        got = kq.classify_dispatch_result(_envelope(stderr="Traceback: KeyError 'x'",
                                                    error="worker exited 1"))
        assert got == {"classified": False, "reason": None, "evidence": "", "platform": "codex"}

    def test_success_envelope_never_classifies(self):
        # even with quota-looking noise in raw: success needs no quota routing
        got = kq.classify_dispatch_result(_envelope(status="completed", raw="429 mentioned in logs"))
        assert got["classified"] is False

    def test_timeout_envelope_is_classifiable(self):
        # the codex hang-on-402 class can surface as timeout with captured stderr
        got = kq.classify_dispatch_result(_envelope(status="timeout",
                                                    stderr="insufficient quota; request aborted"))
        assert got["classified"] is True and got["reason"] == "quota-exhausted"

    def test_scan_order_payload_stderr_wins_over_raw(self):
        # fixed field order: stderr's auth signal beats raw's rate-limit noise
        got = kq.classify_dispatch_result(_envelope(stderr="401 Unauthorized",
                                                    raw="429 too many requests"))
        assert got["reason"] == "auth"

    def test_evidence_is_the_matching_line(self):
        stderr = "starting worker\nHTTP 429 Too Many Requests\ndone"
        got = kq.classify_dispatch_result(_envelope(stderr=stderr))
        assert got["evidence"] == "HTTP 429 Too Many Requests"

    def test_through_real_dispatch_failure(self):
        """Integration seam: a real dispatch() failure envelope classifies (PR #42 field names)."""
        b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R")

        def limited_runner(cmd, cwd, result_path, timeout):
            return 1, "", "429 Too Many Requests: rate limit exceeded", ""
        res = kd.dispatch(b, "/wt", runner=limited_runner)
        got = kq.classify_dispatch_result(res)
        assert got["classified"] is True and got["reason"] == "rate-limited"

    @pytest.mark.parametrize("noise", [
        # adval F1: traceback frames at status-number lines must NOT classify
        'Traceback:\n  File "worker.py", line 429, in run_task\nKeyError',
        '  File "app.py", line 403, in main',
        '  File "b.py", line 402, in f',
        '  File "c.py", line 401, in auth_helper',
        # adval F2: test identifiers / prose containing auth words must NOT classify
        "FAILED tests/test_forbidden_route.py - assertion error",
        "FAILED test_unauthorized_error_test - assert x == y",
        "PermissionError: permission denied: /var/data/api/cache",
    ])
    def test_false_positive_noise_stays_generic(self, noise):
        got = kq.classify_dispatch_result(_envelope(stderr=noise))
        assert got["classified"] is False, f"noise misclassified as {got['reason']}: {noise!r}"

    @pytest.mark.parametrize("real,expected", [
        # the F1/F2 tightenings must NOT break the real shapes
        ("HTTP 429 Too Many Requests", "rate-limited"),
        ("error 402: insufficient credit", "quota-exhausted"),
        ("401 Unauthorized: bad key", "auth"),
        ("403 Forbidden", "auth"),
        ("permission denied: invalid api key", "auth"),
    ])
    def test_real_shapes_survive_the_tightening(self, real, expected):
        got = kq.classify_dispatch_result(_envelope(stderr=real))
        assert got["classified"] is True and got["reason"] == expected

    @pytest.mark.parametrize("bad", [None, [], "failed", 42])
    def test_malformed_envelope_raises(self, bad):
        with pytest.raises(kq.QuotaError):
            kq.classify_dispatch_result(bad)

    def test_missing_status_raises(self):
        with pytest.raises(kq.QuotaError, match="status"):
            kq.classify_dispatch_result({"payload": {}})

    def test_deterministic(self):
        env = _envelope(stderr="429 and also 402 in one line")
        assert kq.classify_dispatch_result(env) == kq.classify_dispatch_result(env)


# ---------------------------------------------------------------------------
# lapse_decision — the G-2 hybrid threshold
# ---------------------------------------------------------------------------

class TestLapseDecision:
    def test_classified_fires_on_first(self):
        assert kq.lapse_decision(0, "quota-exhausted") == {"lapse": True, "reason": "quota-exhausted"}

    def test_generic_boundary_1_no_2_yes(self):
        assert kq.lapse_decision(1, None) == {"lapse": False, "reason": None}
        assert kq.lapse_decision(2, None) == {"lapse": True, "reason": "provider-unavailable"}

    def test_zero_and_none_no_lapse(self):
        assert kq.lapse_decision(0, None)["lapse"] is False

    @pytest.mark.parametrize("bad_count", [-1, 1.5, True, "2"])
    def test_bad_count_raises(self, bad_count):
        with pytest.raises(kq.QuotaError):
            kq.lapse_decision(bad_count, None)

    def test_unknown_reason_raises(self):
        with pytest.raises(kq.QuotaError, match="unknown classified reason"):
            kq.lapse_decision(0, "budget-exhausted")  # the do-NOT-conflate word (brief §2d)


# ---------------------------------------------------------------------------
# parse_kill_switch — G-3 over the existing steering grammar
# ---------------------------------------------------------------------------

class TestKillSwitch:
    def test_recognized_subsystems(self):
        got = kq.parse_kill_switch(["- KATA_OFF advisor", "KATA_OFF provider"])
        assert got == {"off": ["advisor", "provider"], "unknown": []}

    def test_provider_scoped_form(self):
        got = kq.parse_kill_switch(["* KATA_OFF provider:codex"])
        assert got == {"off": ["provider:codex"], "unknown": []}

    def test_unknown_subsystem_surfaced_not_dropped(self):
        got = kq.parse_kill_switch(["KATA_OFF advsor", "KATA_OFF", "KATA_OFF advisor now"])
        assert got["off"] == []
        assert len(got["unknown"]) == 3  # every malformed use surfaces for a loud NOTE

    def test_scoped_nonprovider_and_trailing_colon_are_unknown(self):
        got = kq.parse_kill_switch(["KATA_OFF advisor:x", "KATA_OFF provider:"])
        assert got["off"] == [] and len(got["unknown"]) == 2

    def test_other_directives_ignored(self):
        got = kq.parse_kill_switch(["- prefer smaller diffs", "focus on tests"])
        assert got == {"off": [], "unknown": []}

    def test_case_sensitive_verb(self):
        # steering verbs are shouted (AGENT_STOP precedent) — lowercase is not the verb
        got = kq.parse_kill_switch(["kata_off advisor"])
        assert got == {"off": [], "unknown": []}

    def test_dedupe_first_wins(self):
        got = kq.parse_kill_switch(["KATA_OFF advisor", "- KATA_OFF advisor"])
        assert got["off"] == ["advisor"]

    def test_plus_bullet_recognized(self):
        # adval F4: + is a valid markdown bullet marker too
        got = kq.parse_kill_switch(["+ KATA_OFF advisor"])
        assert got == {"off": ["advisor"], "unknown": []}

    def test_mangled_kill_switch_never_vanishes(self):
        # adval F4: a line CONTAINING the verb that fails to parse surfaces in unknown
        got = kq.parse_kill_switch(["-KATA_OFF advisor", "see KATA_OFF docs"])
        assert got["off"] == []
        assert len(got["unknown"]) == 2

    @pytest.mark.parametrize("bad", ["provider:CODEX", "provider:name:extra", "provider:a b"])
    def test_scoped_name_grammar_tightened(self, bad):
        # adval F4: lowercase single-segment provider names only
        got = kq.parse_kill_switch([f"KATA_OFF {bad}"])
        assert got["off"] == [] and len(got["unknown"]) == 1

    def test_non_list_raises(self):
        with pytest.raises(kq.QuotaError):
            kq.parse_kill_switch("KATA_OFF advisor")


# ---------------------------------------------------------------------------
# park_message — G-4/G-5: plain, deterministic, NO URLs
# ---------------------------------------------------------------------------

class TestParkMessage:
    def test_quota_message_shape(self):
        msg = kq.park_message("quota-exhausted", "HTTP 402 insufficient credit", "codex")
        assert "out of codex tokens" in msg
        assert "HTTP 402 insufficient credit" in msg
        assert "PARKED" in msg and "/kata-resume" in msg
        assert "http" not in msg.lower().replace("http 402", "")  # no URLs (G-5, Tier 3)

    def test_generic_provider_unavailable(self):
        msg = kq.park_message("provider-unavailable", "", "")
        assert "failing repeatedly" in msg and "no clean provider signal" in msg

    def test_unknown_reason_raises(self):
        with pytest.raises(kq.QuotaError):
            kq.park_message("banana", "", "")

    def test_deterministic(self):
        assert kq.park_message("auth", "401", "kiro") == kq.park_message("auth", "401", "kiro")
