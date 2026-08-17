"""Consumes ``used_as_value`` without ever calling it — the call-only-edges blind spot."""

from limit_call_only import used_as_value


def register_handlers():
    return {"handler": used_as_value}
