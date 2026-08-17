"""T10 mirror — "Runs survive interruption / lost runs are recoverable": FACADE.

Live shape: ``kata_restore.detect_lost_run:76`` / ``restore`` / ``kata_restore.fold_board:153``
have zero callers; no run-id anywhere; ``state.json`` is never written in a live run.
"""


def detect_lost_run(repo_root):
    return {"lost": False, "root": repo_root}


def restore_run(run_id):
    return {"restored": run_id}


def fold_board(board_content):
    return {"lines": len(board_content.splitlines())}
