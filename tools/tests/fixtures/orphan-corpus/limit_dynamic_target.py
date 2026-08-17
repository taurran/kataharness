"""Limit fixture — verbatim: "dynamic imports invisible".

``dynamic_only`` is reached at runtime through ``importlib.import_module`` + ``getattr``, which
produces neither an import edge (the module name is a string) nor a ref edge (the call node's
function is ``getattr``). S1 reports a live symbol as unwired: a false positive.
"""


def dynamic_only():
    return "dynamic"
