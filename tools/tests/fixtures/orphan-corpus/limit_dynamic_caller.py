"""Reaches ``limit_dynamic_target.dynamic_only`` entirely dynamically."""

import importlib


def call_dynamically():
    mod = importlib.import_module("limit_dynamic_target")
    return getattr(mod, "dynamic_only")()
