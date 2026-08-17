"""Calls ``limit_bare_name_b.shared_name`` — unambiguously, via an explicit import."""

from limit_bare_name_b import shared_name


def call_b():
    return shared_name()
