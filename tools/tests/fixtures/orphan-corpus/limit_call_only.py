"""Limit fixture — verbatim: "call-only edges".

``used_as_value`` is imported and referenced as a VALUE by ``limit_call_only_consumer.py``.
graph_gen's ``_extract_refs`` only walks ``call`` expressions, so no ref edge exists and S1
reports a genuinely-referenced symbol as unwired. A false positive, demonstrated not prosed.
"""


def used_as_value(x):
    return x
