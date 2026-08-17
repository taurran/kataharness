"""Limit fixture — verbatim: "fabricated `src` attribution".

``zzz_actual_caller`` is the real caller of ``imported_target``. graph_gen's ``_extract_refs``
attributes every ref edge to ``next(iter(sorted(file_symbol_ids)))`` — the file's
alphabetically-first symbol — so the recorded provenance names ``aaa_innocent``, which calls
nothing. Wiring provenance from this graph is therefore file-accurate and symbol-fabricated.
"""

from limit_fabricated_target import imported_target


def aaa_innocent():
    return 1


def zzz_actual_caller():
    return imported_target()
