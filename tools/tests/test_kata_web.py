"""test_kata_web.py — TDD tests for kata_web.py (S1.5b localhost web viewer).

TDD discipline: tests written FIRST, before kata_web.py existed.
All tests are hermetic (tmp_path only, no external network).

Coverage:
- PAGE_HTML contains required substrings (改善型, /api/view, 1000)
- view_to_dict: shape for a populated ViewModel (tasks list of dicts + driftEscalations as [d,e])
- build_web_view: over a tmp .kata dir with board+state → expected phase/tasks
- build_web_view: over empty/absent dir → waiting: True
- _safe_path / build_web_view rejects .. traversal kata_dir
- Optional: server on port 0 does a round-trip /api/view request
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

# ---------------------------------------------------------------------------
# Resolve the tools/ directory so we can import kata_web regardless of cwd.
# ---------------------------------------------------------------------------
_TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))


# ---------------------------------------------------------------------------
# Import gate
# ---------------------------------------------------------------------------


def test_kata_web_importable():
    """Module must be importable without side-effects."""
    import kata_web  # noqa: F401


def test_no_third_party_imports():
    """kata_web must NOT import rich or any non-stdlib third-party library."""
    import importlib
    import inspect

    if "kata_web" in sys.modules:
        del sys.modules["kata_web"]

    import kata_web as m

    source = inspect.getsource(m)
    assert "import rich" not in source, "kata_web must not import rich"
    assert "import flask" not in source, "kata_web must not import flask"
    assert "import fastapi" not in source.lower(), "kata_web must not import fastapi"


# ---------------------------------------------------------------------------
# PAGE_HTML required substrings
# ---------------------------------------------------------------------------


class TestPageHTML:
    def test_contains_kanji_title(self):
        import kata_web
        assert "改善型" in kata_web.PAGE_HTML, "PAGE_HTML must contain 改善型"

    def test_contains_api_view_route(self):
        import kata_web
        assert "/api/view" in kata_web.PAGE_HTML, "PAGE_HTML must contain /api/view"

    def test_contains_poll_interval_1000(self):
        import kata_web
        assert "1000" in kata_web.PAGE_HTML, "PAGE_HTML must contain 1000 (poll interval)"

    def test_is_html_string(self):
        import kata_web
        html = kata_web.PAGE_HTML
        assert isinstance(html, str)
        assert "<html" in html.lower() or "<!doctype" in html.lower()


# ---------------------------------------------------------------------------
# view_to_dict — pure serialisation
# ---------------------------------------------------------------------------


def _make_populated_vm():
    """Build a real ViewModel via kata_dash_model.build_view_model from minimal fixtures."""
    import kata_dash_model

    board_text = (
        "2026-06-21T10:00:00Z | agent-A | CLAIM | T1 | starting\n"
        "2026-06-21T10:01:00Z | agent-B | CLAIM | T2 | starting render\n"
    )
    state = {
        "tasks": {"T1": "in-progress", "T2": "done"},
        "gate": None,
        "driftLedger": {"unauthorizedDeviations": 2, "escalations": 1},
        "wavesDone": ["wave-0"],
        "plan": "test-spec",
        "updatedUtc": "2026-06-21T10:05:00Z",
    }
    return kata_dash_model.build_view_model(board_text, state)


class TestViewToDict:
    def test_returns_dict(self):
        import kata_web
        vm = _make_populated_vm()
        result = kata_web.view_to_dict(vm)
        assert isinstance(result, dict)

    def test_top_level_keys_present(self):
        import kata_web
        vm = _make_populated_vm()
        result = kata_web.view_to_dict(vm)
        required = {"spec", "wave", "phase", "gate", "waiting", "updatedUtc",
                    "driftEscalations", "events", "tasks"}
        assert required <= result.keys(), f"Missing keys: {required - result.keys()}"

    def test_drift_escalations_is_list_of_two(self):
        import kata_web
        vm = _make_populated_vm()
        result = kata_web.view_to_dict(vm)
        de = result["driftEscalations"]
        assert isinstance(de, list), "driftEscalations must be a list"
        assert len(de) == 2, "driftEscalations must be [d, e] (len 2)"
        assert de[0] == 2, "driftEscalations[0] = unauthorizedDeviations"
        assert de[1] == 1, "driftEscalations[1] = escalations"

    def test_tasks_is_list_of_dicts(self):
        import kata_web
        vm = _make_populated_vm()
        result = kata_web.view_to_dict(vm)
        tasks = result["tasks"]
        assert isinstance(tasks, list), "tasks must be a list"
        assert len(tasks) == 2

    def test_each_task_dict_has_required_keys(self):
        import kata_web
        vm = _make_populated_vm()
        result = kata_web.view_to_dict(vm)
        required = {"id", "label", "status", "percent", "active", "blocked", "done", "progressLabel"}
        for t in result["tasks"]:
            assert isinstance(t, dict), "each task must be a dict"
            assert required <= t.keys(), f"Task missing keys: {required - t.keys()}"

    def test_events_is_list_of_strings(self):
        import kata_web
        vm = _make_populated_vm()
        result = kata_web.view_to_dict(vm)
        events = result["events"]
        assert isinstance(events, list)
        for e in events:
            assert isinstance(e, str)

    def test_phase_is_string(self):
        import kata_web
        vm = _make_populated_vm()
        result = kata_web.view_to_dict(vm)
        assert isinstance(result["phase"], str)
        assert result["phase"] in ("GRILL", "FREEZE", "EXECUTE", "EVALUATE", "HANDOFF", "IMPROVE")

    def test_waiting_false_for_populated_vm(self):
        import kata_web
        vm = _make_populated_vm()
        result = kata_web.view_to_dict(vm)
        assert result["waiting"] is False

    def test_task_T1_in_progress(self):
        import kata_web
        vm = _make_populated_vm()
        result = kata_web.view_to_dict(vm)
        t1 = next(t for t in result["tasks"] if t["id"] == "T1")
        assert t1["status"] == "in-progress"
        assert t1["active"] is True
        assert t1["done"] is False

    def test_task_T2_done(self):
        import kata_web
        vm = _make_populated_vm()
        result = kata_web.view_to_dict(vm)
        t2 = next(t for t in result["tasks"] if t["id"] == "T2")
        assert t2["status"] == "done"
        assert t2["done"] is True
        assert t2["active"] is False


# ---------------------------------------------------------------------------
# build_web_view — integration over tmp_path
# ---------------------------------------------------------------------------


class TestBuildWebView:
    def test_populated_kata_dir_returns_expected_phase(self, tmp_path):
        import kata_web

        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()

        board_text = (
            "2026-06-21T10:00:00Z | agent-A | CLAIM | T1 | starting\n"
        )
        state = {
            "tasks": {"T1": "in-progress", "T2": "assigned"},
            "gate": None,
            "driftLedger": {},
            "wavesDone": [],
            "plan": "loop-hardening",
            "updatedUtc": "2026-06-21T10:01:00Z",
        }
        (kata_dir / "board.md").write_text(board_text, encoding="utf-8")
        (kata_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        result = kata_web.build_web_view(str(kata_dir))
        assert isinstance(result, dict)
        assert result["phase"] in ("GRILL", "FREEZE", "EXECUTE", "EVALUATE", "HANDOFF", "IMPROVE")
        assert result["waiting"] is False

    def test_populated_kata_dir_has_tasks(self, tmp_path):
        import kata_web

        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()

        state = {
            "tasks": {"T1": "in-progress", "T2": "assigned"},
            "gate": None,
            "driftLedger": {},
        }
        (kata_dir / "board.md").write_text("", encoding="utf-8")
        (kata_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        result = kata_web.build_web_view(str(kata_dir))
        assert len(result["tasks"]) == 2

    def test_absent_kata_dir_returns_waiting_true(self, tmp_path):
        import kata_web

        missing = tmp_path / "nonexistent_kata"
        result = kata_web.build_web_view(str(missing))
        assert result["waiting"] is True

    def test_empty_kata_dir_returns_waiting_true(self, tmp_path):
        import kata_web

        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()
        # No board.md or state.json
        result = kata_web.build_web_view(str(kata_dir))
        assert result["waiting"] is True

    def test_bad_json_state_returns_waiting_true(self, tmp_path):
        import kata_web

        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()
        (kata_dir / "board.md").write_text("", encoding="utf-8")
        (kata_dir / "state.json").write_text("NOT VALID JSON {{{{", encoding="utf-8")

        result = kata_web.build_web_view(str(kata_dir))
        # bad JSON → state=None; no board events → waiting=True
        assert result["waiting"] is True

    def test_board_only_no_state_returns_not_waiting(self, tmp_path):
        """Board events without state → not waiting (events present)."""
        import kata_web

        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()
        board_text = "2026-06-21T10:00:00Z | agent | CLAIM | T1 | msg\n"
        (kata_dir / "board.md").write_text(board_text, encoding="utf-8")

        result = kata_web.build_web_view(str(kata_dir))
        # Has board events, no state → waiting=False (events exist)
        assert result["waiting"] is False

    def test_drift_escalations_serialised_as_list(self, tmp_path):
        import kata_web

        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()
        state = {
            "tasks": {"T1": "in-progress"},
            "gate": None,
            "driftLedger": {"unauthorizedDeviations": 3, "escalations": 2},
        }
        (kata_dir / "board.md").write_text("", encoding="utf-8")
        (kata_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        result = kata_web.build_web_view(str(kata_dir))
        de = result["driftEscalations"]
        assert isinstance(de, list)
        assert de == [3, 2]


# ---------------------------------------------------------------------------
# _safe_path / path traversal rejection
# ---------------------------------------------------------------------------


class TestSafePath:
    def test_dotdot_segment_raises(self):
        """build_web_view must reject kata_dir containing '..'."""
        import kata_web

        with pytest.raises(SystemExit):
            kata_web.build_web_view("../some/escape")

    def test_dotdot_in_middle_raises(self):
        import kata_web

        with pytest.raises(SystemExit):
            kata_web.build_web_view("valid/../../escape")

    def test_plain_path_does_not_raise(self, tmp_path):
        import kata_web

        # Should not raise SystemExit (returns waiting=True since dir is absent)
        kata_dir = tmp_path / "safe_dir"
        result = kata_web.build_web_view(str(kata_dir))
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Handler — optional server round-trip (port 0, hermetic)
# ---------------------------------------------------------------------------


class TestHandlerRoundTrip:
    """Optional: bind to port 0 and do a single /api/view request.

    Skipped if the import of http.client fails for any reason, or if
    there is a platform issue binding.  Hermetic: no real .kata dir.
    """

    def _make_server(self, tmp_path):
        import kata_web
        from http.server import ThreadingHTTPServer

        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()
        # No board or state → waiting=True; keeps test fast

        server = ThreadingHTTPServer(("127.0.0.1", 0), kata_web.Handler)
        server.kata_dir = str(kata_dir)
        return server

    def test_root_returns_html(self, tmp_path):
        import http.client
        import threading
        import kata_web

        server = self._make_server(tmp_path)
        port = server.server_address[1]
        t = threading.Thread(target=server.handle_request, daemon=True)
        t.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("GET", "/")
            resp = conn.getresponse()
            assert resp.status == 200
            ct = resp.getheader("Content-Type", "")
            assert "text/html" in ct
            body = resp.read().decode("utf-8")
            assert "改善型" in body
        finally:
            conn.close()
            t.join(timeout=2)
            server.server_close()

    def test_api_view_returns_json(self, tmp_path):
        import http.client
        import threading
        import kata_web

        server = self._make_server(tmp_path)
        port = server.server_address[1]
        t = threading.Thread(target=server.handle_request, daemon=True)
        t.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("GET", "/api/view")
            resp = conn.getresponse()
            assert resp.status == 200
            ct = resp.getheader("Content-Type", "")
            assert "application/json" in ct
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            assert data["waiting"] is True
        finally:
            conn.close()
            t.join(timeout=2)
            server.server_close()

    def test_unknown_path_returns_404(self, tmp_path):
        import http.client
        import threading
        import kata_web

        server = self._make_server(tmp_path)
        port = server.server_address[1]
        t = threading.Thread(target=server.handle_request, daemon=True)
        t.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("GET", "/unknown/path")
            resp = conn.getresponse()
            assert resp.status == 404
        finally:
            conn.close()
            t.join(timeout=2)
            server.server_close()
