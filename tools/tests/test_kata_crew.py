"""Tests for kata_crew.py — the pure, agnostic crew/roster renderer (subagent-monitor S1/S4).

TDD contract (PLAN T1): the LAYOUT GOLDENS are byte-pinned FIRST, authored from the frozen
D5 layout (DESIGN §Frame) with a FIXED injected ``now`` and REAL ANSI bytes — no environment
dependence (Determinism laws 2/3/7/10). Then the roster API (atomic write/close, fail-soft
read, fail-closed corrupt write) and the ``liveness`` never-raise / boundary / board-corroboration
behaviour.

The D5 chip layout (byte-pin reference):

    ⚒ C·opus·H▰ C·opus·H▰ V·son·M▱          (marker · role·model·effort·liveness, 3 chips)
    ⚒ C·opus·H▰ C·opus·H▰ V·son·M▰ +2       (truncate at 3 chips + " +N")
    ""                                       (empty roster ⇒ crew slot vanishes)

``render_crew`` renders each entry's ``model`` field through the DISPLAY-ONLY abbreviation map
(``sonnet``→``son``, ``mythos``→``myth`` — adval fold A); every other string renders verbatim.
Role/model/effort are control-stripped (the G7d ANSI-injection class — adval fold B).
``render_model_chip`` lowercases the payload display_name's first token.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import kata_crew as kc

# --- Real ANSI theme bytes (mirror statusline_chain._ANSI_DIM/_ANSI_RESET) -------------
DIM = "\x1b[2m"
RESET = "\x1b[0m"

# --- Fixed injected clock (Determinism law 7 — the composition golden byte-pins) -------
NOW = datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC)
LIVE_1 = "2026-07-14T11:58:00+00:00"  # 2 min ago  → fresh (deadline 10)
LIVE_2 = "2026-07-14T11:58:10+00:00"
LIVE_3 = "2026-07-14T11:58:20+00:00"
LIVE_4 = "2026-07-14T11:58:30+00:00"
LIVE_5 = "2026-07-14T11:58:40+00:00"
STALE = "2026-07-14T11:45:00+00:00"  # 15 min ago → stale


def _entry(role: str, model: str, effort: str, dispatched: str, closed=None) -> dict:
    return {
        "role": role,
        "model": model,
        "effort": effort,
        "dispatchedAt": dispatched,
        "closedAt": closed,
    }


def _roster(workers: dict) -> dict:
    return {"v": 1, "workers": workers}


# ======================================================================================
# S4 — LAYOUT GOLDENS (byte-pinned, fixed now, real ANSI)
# ======================================================================================


def test_golden_empty_roster_vanishes():
    # empty roster ⇒ "" (the crew slot vanishes entirely — DESIGN idle render)
    assert kc.render_crew(_roster({}), "", now=NOW, deadline_minutes=10) == ""


def test_golden_one_live_worker():
    roster = _roster({"t1": _entry("coder", "opus", "H", LIVE_1)})
    assert kc.render_crew(roster, "", now=NOW, deadline_minutes=10) == f"{DIM}⚒ C·opus·H▰{RESET}"


def test_golden_three_workers_sorted():
    # Inserted SCRAMBLED — render must sort by dispatchedAt then taskId (law 10) ⇒ t1,t2,t3.
    roster = _roster(
        {
            "t3": _entry("validator", "son", "M", LIVE_3),
            "t1": _entry("coder", "opus", "H", LIVE_1),
            "t2": _entry("coder", "opus", "H", LIVE_2),
        }
    )
    assert (
        kc.render_crew(roster, "", now=NOW, deadline_minutes=10)
        == f"{DIM}⚒ C·opus·H▰ C·opus·H▰ V·son·M▰{RESET}"
    )


def test_golden_many_workers_truncate_plus_n():
    roster = _roster(
        {
            "t3": _entry("validator", "son", "M", LIVE_3),
            "t1": _entry("coder", "opus", "H", LIVE_1),
            "t5": _entry("coder", "opus", "H", LIVE_5),
            "t2": _entry("coder", "opus", "H", LIVE_2),
            "t4": _entry("coder", "opus", "H", LIVE_4),
        }
    )
    assert (
        kc.render_crew(roster, "", now=NOW, deadline_minutes=10)
        == f"{DIM}⚒ C·opus·H▰ C·opus·H▰ V·son·M▰ +2{RESET}"
    )


def test_golden_stale_chip_hollow():
    roster = _roster({"t1": _entry("coder", "opus", "H", STALE)})
    assert kc.render_crew(roster, "", now=NOW, deadline_minutes=10) == f"{DIM}⚒ C·opus·H▱{RESET}"


# ======================================================================================
# EV-1 — DEGRADE GOLDEN FAMILY (never blank/crash from bad crew data)
# ======================================================================================


def test_degrade_roster_absent(tmp_path: Path):
    # roster file absent ⇒ read_roster {} ⇒ render_crew "" (gauge+model only upstream)
    assert kc.read_roster(tmp_path) == {}
    assert kc.render_crew(kc.read_roster(tmp_path), "", now=NOW, deadline_minutes=10) == ""


def test_degrade_roster_corrupt(tmp_path: Path):
    # corrupt JSON ⇒ read_roster {} (fail-soft, never an error render)
    (tmp_path / "dispatch.json").write_text("{not json", encoding="utf-8")
    assert kc.read_roster(tmp_path) == {}
    assert kc.render_crew(kc.read_roster(tmp_path), "", now=NOW, deadline_minutes=10) == ""


def test_degrade_roster_non_dict(tmp_path: Path):
    (tmp_path / "dispatch.json").write_text("[1, 2, 3]", encoding="utf-8")
    assert kc.read_roster(tmp_path) == {}


def test_degrade_all_stale_hollow_never_dropped():
    # all-stale roster ⇒ hollow chips, NEVER dropped (EV-1)
    roster = _roster(
        {
            "t1": _entry("coder", "opus", "H", STALE),
            "t2": _entry("coder", "opus", "H", "2026-07-14T11:44:00+00:00"),
        }
    )
    assert (
        kc.render_crew(roster, "", now=NOW, deadline_minutes=10)
        == f"{DIM}⚒ C·opus·H▱ C·opus·H▱{RESET}"
    )


def test_degrade_render_crew_on_non_dict_roster():
    # a non-dict roster (defensive) ⇒ "" never raise
    assert kc.render_crew(None, "", now=NOW, deadline_minutes=10) == ""
    assert kc.render_crew([], "", now=NOW, deadline_minutes=10) == ""
    assert kc.render_crew({"v": 1}, "", now=NOW, deadline_minutes=10) == ""


def test_degrade_closed_entries_excluded():
    roster = _roster(
        {
            "t1": _entry("coder", "opus", "H", LIVE_1, closed="2026-07-14T11:59:00+00:00"),
            "t2": _entry("validator", "son", "M", LIVE_2),
        }
    )
    # t1 is closed ⇒ only t2 renders
    assert kc.render_crew(roster, "", now=NOW, deadline_minutes=10) == f"{DIM}⚒ V·son·M▰{RESET}"


# ======================================================================================
# Fold A — display-only model abbreviation map (adval finding 2)
# ======================================================================================


def test_abbrev_sonnet_renders_son():
    # a REAL conductor write of the ladder short-name "sonnet" renders the pinned `V·son·M` chip
    roster = _roster({"t1": _entry("validator", "sonnet", "M", LIVE_1)})
    assert kc.render_crew(roster, "", now=NOW, deadline_minutes=10) == f"{DIM}⚒ V·son·M▰{RESET}"


def test_abbrev_mythos_renders_myth():
    roster = _roster({"t1": _entry("coder", "mythos", "H", LIVE_1)})
    assert kc.render_crew(roster, "", now=NOW, deadline_minutes=10) == f"{DIM}⚒ C·myth·H▰{RESET}"


def test_abbrev_opus_fable_haiku_verbatim():
    # ladder names within the one-line budget pass through unchanged
    for model in ("opus", "fable", "haiku"):
        roster = _roster({"t1": _entry("coder", model, "H", LIVE_1)})
        assert (
            kc.render_crew(roster, "", now=NOW, deadline_minutes=10)
            == f"{DIM}⚒ C·{model}·H▰{RESET}"
        )


def test_abbrev_unknown_model_verbatim():
    roster = _roster({"t1": _entry("coder", "gpt-5-codex", "H", LIVE_1)})
    assert kc.render_crew(roster, "", now=NOW, deadline_minutes=10) == f"{DIM}⚒ C·gpt-5-codex·H▰{RESET}"


# ======================================================================================
# Fold B — ANSI-injection guard on roster content (adval finding 3, G7d class)
# ======================================================================================


def test_roster_ansi_injection_stripped():
    # a hostile/corrupt dispatch.json with control bytes in role/model/effort renders STRIPPED,
    # never raw: ESC (C0), CSI (C1 \x9b), and BEL vanish (byte-pinned)
    roster = _roster({"t1": _entry("\x07coder", "op\x1bus\x9b", "H\x07", LIVE_1)})
    rendered = kc.render_crew(roster, "", now=NOW, deadline_minutes=10)
    assert rendered == f"{DIM}⚒ C·opus·H▰{RESET}"
    assert rendered.count("\x1b") == 2  # only kata's own _ANSI_DIM + _ANSI_RESET remain


def test_roster_full_csi_sequence_defanged():
    # a full ESC[31m injection: the ESC is stripped, the printable remnant "[31m" stays INERT
    # text (the same semantics as statusline_chain._strip_control on a hostile dirname) — the
    # terminal never sees a live escape from roster content
    roster = _roster({"t1": _entry("coder", "opus\x1b[31m", "H", LIVE_1)})
    rendered = kc.render_crew(roster, "", now=NOW, deadline_minutes=10)
    assert rendered == f"{DIM}⚒ C·opus[31m·H▰{RESET}"
    assert rendered.count("\x1b") == 2  # no injected ESC survives


def test_roster_control_only_role_renders_placeholder():
    # a role that is ONLY control bytes degrades to the "?" placeholder, never raw escapes
    roster = _roster({"t1": _entry("\x1b\x9b", "opus", "H", LIVE_1)})
    assert kc.render_crew(roster, "", now=NOW, deadline_minutes=10) == f"{DIM}⚒ ?·opus·H▰{RESET}"


# ======================================================================================
# render_model_chip — EV-1 (main-session model chip)
# ======================================================================================


def test_model_chip_happy():
    assert kc.render_model_chip({"model": {"display_name": "Fable 5"}}) == f"{DIM}fable{RESET}"


def test_model_chip_lowercases_first_token():
    assert kc.render_model_chip({"model": {"display_name": "Claude Opus 4.8"}}) == f"{DIM}claude{RESET}"


def test_model_chip_absent_field_empty():
    assert kc.render_model_chip({}) == ""
    assert kc.render_model_chip({"model": {}}) == ""
    assert kc.render_model_chip({"model": {"display_name": ""}}) == ""
    assert kc.render_model_chip({"model": {"display_name": "   "}}) == ""


def test_model_chip_malformed_payload_empty():
    assert kc.render_model_chip(None) == ""
    assert kc.render_model_chip("nope") == ""
    assert kc.render_model_chip({"model": "not-a-dict"}) == ""
    assert kc.render_model_chip({"model": {"display_name": 42}}) == ""


# ======================================================================================
# Roster API — atomic write/close round-trip, fail-closed write, fail-soft read
# ======================================================================================


def test_write_close_round_trip(tmp_path: Path):
    kata_dir = tmp_path / ".kata"
    kc.write_roster_entry(kata_dir, "t1", role="coder", model="opus", effort="H", now=NOW)
    roster = kc.read_roster(kata_dir)
    assert roster["v"] == 1
    entry = roster["workers"]["t1"]
    assert entry["role"] == "coder"
    assert entry["model"] == "opus"
    assert entry["effort"] == "H"
    assert entry["dispatchedAt"] == NOW.isoformat()
    assert entry["closedAt"] is None

    later = NOW + timedelta(minutes=5)
    kc.close_roster_entry(kata_dir, "t1", now=later)
    entry2 = kc.read_roster(kata_dir)["workers"]["t1"]
    assert entry2["closedAt"] == later.isoformat()
    # dispatchedAt unchanged by close
    assert entry2["dispatchedAt"] == NOW.isoformat()


def test_write_second_entry_preserves_first(tmp_path: Path):
    kata_dir = tmp_path / ".kata"
    kc.write_roster_entry(kata_dir, "t1", role="coder", model="opus", effort="H", now=NOW)
    kc.write_roster_entry(kata_dir, "t2", role="validator", model="son", effort="M", now=NOW)
    workers = kc.read_roster(kata_dir)["workers"]
    assert set(workers) == {"t1", "t2"}


def test_write_is_sorted_keys_deterministic(tmp_path: Path):
    kata_dir = tmp_path / ".kata"
    p = kc.write_roster_entry(kata_dir, "t1", role="coder", model="opus", effort="H", now=NOW)
    text = Path(p).read_text(encoding="utf-8")
    # sort_keys=True (law 5) + trailing newline; top-level keys "v" before "workers"
    assert text.endswith("\n")
    assert json.loads(text) == {
        "v": 1,
        "workers": {
            "t1": {
                "closedAt": None,
                "dispatchedAt": NOW.isoformat(),
                "effort": "H",
                "model": "opus",
                "role": "coder",
            }
        },
    }
    # deterministic bytes: re-serialize matches
    assert json.dumps(json.loads(text), indent=2, sort_keys=True) + "\n" == text


def test_write_rejects_bad_effort(tmp_path: Path):
    kata_dir = tmp_path / ".kata"
    with pytest.raises(ValueError, match="effort"):
        kc.write_roster_entry(kata_dir, "t1", role="coder", model="opus", effort="X", now=NOW)


def test_write_rejects_blank_task_id(tmp_path: Path):
    kata_dir = tmp_path / ".kata"
    with pytest.raises(ValueError, match="task_id"):
        kc.write_roster_entry(kata_dir, "  ", role="coder", model="opus", effort="H", now=NOW)


def test_write_fail_closed_on_corrupt_existing(tmp_path: Path):
    # a corrupt existing roster ⇒ fail-closed write (ValueError), file byte-UNCHANGED
    kata_dir = tmp_path / ".kata"
    kata_dir.mkdir()
    corrupt = kata_dir / "dispatch.json"
    corrupt.write_text("{ this is not json", encoding="utf-8")
    before = corrupt.read_bytes()
    with pytest.raises(ValueError, match="refusing to overwrite"):
        kc.write_roster_entry(kata_dir, "t1", role="coder", model="opus", effort="H", now=NOW)
    assert corrupt.read_bytes() == before  # never clobbered


def test_write_fail_closed_on_non_dict_existing(tmp_path: Path):
    kata_dir = tmp_path / ".kata"
    kata_dir.mkdir()
    corrupt = kata_dir / "dispatch.json"
    corrupt.write_text("[1, 2, 3]", encoding="utf-8")
    before = corrupt.read_bytes()
    with pytest.raises(ValueError, match="refusing to overwrite"):
        kc.write_roster_entry(kata_dir, "t1", role="coder", model="opus", effort="H", now=NOW)
    assert corrupt.read_bytes() == before


def test_close_fail_closed_on_corrupt_existing(tmp_path: Path):
    kata_dir = tmp_path / ".kata"
    kata_dir.mkdir()
    corrupt = kata_dir / "dispatch.json"
    corrupt.write_text("{bad", encoding="utf-8")
    before = corrupt.read_bytes()
    with pytest.raises(ValueError, match="refusing to overwrite"):
        kc.close_roster_entry(kata_dir, "t1", now=NOW)
    assert corrupt.read_bytes() == before


def test_close_missing_entry_is_noop(tmp_path: Path):
    kata_dir = tmp_path / ".kata"
    kc.write_roster_entry(kata_dir, "t1", role="coder", model="opus", effort="H", now=NOW)
    # closing an unknown task is a no-op (does not raise, does not add an entry)
    kc.close_roster_entry(kata_dir, "nope", now=NOW)
    assert set(kc.read_roster(kata_dir)["workers"]) == {"t1"}


def test_close_on_absent_file_is_noop(tmp_path: Path):
    kata_dir = tmp_path / ".kata"
    # no file yet — close is a harmless no-op
    kc.close_roster_entry(kata_dir, "t1", now=NOW)
    assert kc.read_roster(kata_dir) == {}


def test_read_roster_fail_soft(tmp_path: Path):
    # absent
    assert kc.read_roster(tmp_path / ".kata") == {}
    # corrupt
    d = tmp_path / ".kata"
    d.mkdir()
    (d / "dispatch.json").write_text("nonsense", encoding="utf-8")
    assert kc.read_roster(d) == {}


def test_write_defaults_now_when_absent(tmp_path: Path):
    # now=None ⇒ a real UTC stamp is written (parseable ISO); never raises
    kata_dir = tmp_path / ".kata"
    kc.write_roster_entry(kata_dir, "t1", role="coder", model="opus", effort="H")
    stamp = kc.read_roster(kata_dir)["workers"]["t1"]["dispatchedAt"]
    parsed = datetime.fromisoformat(stamp)
    assert parsed.tzinfo is not None


# ======================================================================================
# liveness() — never-raise, boundary (±ε), board corroboration beats dispatchedAt
# ======================================================================================


def test_liveness_fresh_from_dispatched():
    entry = _entry("coder", "opus", "H", LIVE_1)
    assert kc.liveness(entry, "", "t1", now=NOW, deadline_minutes=10) is True


def test_liveness_stale_from_dispatched():
    entry = _entry("coder", "opus", "H", STALE)
    assert kc.liveness(entry, "", "t1", now=NOW, deadline_minutes=10) is False


def test_liveness_boundary_fresh_at_deadline_minus_epsilon():
    # dispatched at now - (deadline - ε) ⇒ fresh
    dispatched = (NOW - timedelta(minutes=10) + timedelta(seconds=1)).isoformat()
    entry = _entry("coder", "opus", "H", dispatched)
    assert kc.liveness(entry, "", "t1", now=NOW, deadline_minutes=10) is True


def test_liveness_boundary_stale_at_deadline_plus_epsilon():
    # dispatched at now - (deadline + ε) ⇒ stale
    dispatched = (NOW - timedelta(minutes=10) - timedelta(seconds=1)).isoformat()
    entry = _entry("coder", "opus", "H", dispatched)
    assert kc.liveness(entry, "", "t1", now=NOW, deadline_minutes=10) is False


def test_liveness_board_corroboration_beats_dispatched():
    # dispatchedAt is STALE, but a recent board PROGRESS heartbeat for the task ⇒ FRESH
    entry = _entry("coder", "opus", "H", STALE)
    board = (
        "2026-07-14T11:00:00+00:00 | worker-t1 | CLAIM | t1 | starting\n"
        "2026-07-14T11:59:00+00:00 | worker-t1 | PROGRESS | t1 | 3/5 writing tests\n"
    )
    assert kc.liveness(entry, board, "t1", now=NOW, deadline_minutes=10) is True


def test_liveness_board_only_matches_own_task():
    # a fresh heartbeat for a DIFFERENT task must not rescue this stale entry
    entry = _entry("coder", "opus", "H", STALE)
    board = "2026-07-14T11:59:00+00:00 | worker-t2 | PROGRESS | t2 | 1/2 building\n"
    assert kc.liveness(entry, board, "t1", now=NOW, deadline_minutes=10) is False


def test_liveness_board_ignores_non_heartbeat_types():
    # DONE/NOTE/BLOCK are not CLAIM/PROGRESS ⇒ do not corroborate liveness
    entry = _entry("coder", "opus", "H", STALE)
    board = "2026-07-14T11:59:00+00:00 | worker-t1 | DONE | t1 | finished\n"
    assert kc.liveness(entry, board, "t1", now=NOW, deadline_minutes=10) is False


def test_liveness_never_raises_on_garbage_board():
    entry = _entry("coder", "opus", "H", LIVE_1)
    for garbage in (
        "not a board at all",
        "|||||",
        "a | b | c",  # too few fields
        "\x00\x01\x02 | x | CLAIM | t1 | msg",  # bad ts
        "2026-13-99T99:99 | x | PROGRESS | t1 | msg",  # unparseable ts
        "",
        "\n\n\n",
    ):
        result = kc.liveness(entry, garbage, "t1", now=NOW, deadline_minutes=10)
        assert isinstance(result, bool)


def test_liveness_never_raises_on_non_string_board():
    entry = _entry("coder", "opus", "H", LIVE_1)
    assert isinstance(kc.liveness(entry, None, "t1", now=NOW, deadline_minutes=10), bool)


def test_liveness_no_anchor_is_stale():
    # entry with no parseable dispatchedAt AND no board stamp ⇒ stale (cannot confirm)
    entry = {"role": "coder", "model": "opus", "effort": "H", "dispatchedAt": "garbage"}
    assert kc.liveness(entry, "", "t1", now=NOW, deadline_minutes=10) is False


def test_liveness_naive_now_normalized():
    # a naive now (no tzinfo) is normalized to UTC — never raises comparing to tz-aware stamps
    naive_now = datetime(2026, 7, 14, 12, 0, 0)
    entry = _entry("coder", "opus", "H", LIVE_1)
    assert kc.liveness(entry, "", "t1", now=naive_now, deadline_minutes=10) is True
