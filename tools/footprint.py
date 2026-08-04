"""Footprint manifest and diff-stat helpers for KataHarness runs.

Pure core functions (partition, is_within_footprint, manifest) do NOT call git.
Thin git wrappers (changed_since, diff_stat, changed_in_task) are provided
separately; changed_in_task and file_content_hashes are exercised by real-git /
tmp-dir tests, while changed_since/diff_stat remain thin pass-throughs.

A second, bytes-returning wrapper set (ref_exists, origin_head_ref,
renames_in_task, blob_at_ref, all through the pinned `_pinned_git`) supplies the
baseline reads the bump-on-modify check in validate_skills.py needs — kept here
so the repo's git call sites stay concentrated in one pinned module rather than
sprouting a fresh `subprocess` call in the validator.
"""

from __future__ import annotations

import hashlib
import os
import subprocess


def _normalize(path: str) -> str:
    """Normalize path separators to forward slashes."""
    return path.replace("\\", "/")


def _in_footprint(file: str, footprint: list[str]) -> bool:
    """Return True if *file* equals or is under any entry in *footprint*."""
    f = _normalize(file)
    for entry in footprint:
        e = _normalize(entry)
        if f == e:
            return True
        # treat entry as a directory prefix (ensure it ends with '/')
        prefix = e if e.endswith("/") else e + "/"
        if f.startswith(prefix):
            return True
    return False


def partition(changed_files: list[str], footprint: list[str]) -> dict:
    """Split *changed_files* into in-footprint and out-of-footprint buckets.

    Args:
        changed_files: Paths that changed in the current run (any separator).
        footprint: Declared allowed paths / directory prefixes.

    Returns:
        ``{"in_footprint": [...], "out_of_footprint": [...]}`` — both lists are
        normalized to forward slashes and sorted deterministically.
    """
    inside: list[str] = []
    outside: list[str] = []

    for raw in changed_files:
        normalized = _normalize(raw)
        if _in_footprint(raw, footprint):
            inside.append(normalized)
        else:
            outside.append(normalized)

    return {
        "in_footprint": sorted(inside),
        "out_of_footprint": sorted(outside),
    }


def is_within_footprint(changed_files: list[str], footprint: list[str]) -> bool:
    """Return True iff every changed file is within the declared footprint.

    Args:
        changed_files: Paths that changed in the current run.
        footprint: Declared allowed paths / directory prefixes.

    Returns:
        ``True`` when ``out_of_footprint`` is empty.
    """
    return len(partition(changed_files, footprint)["out_of_footprint"]) == 0


# Code-file extensions that indicate executable logic (conservative set).
_CODE_EXTENSIONS: frozenset[str] = frozenset(
    {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"}
)


def code_bearing(changed_files: list[str]) -> bool:
    """Return True iff any changed path has a code-file extension.

    "Code-bearing" means the change introduces or modifies executable logic.
    A run with only documentation, configuration, or data files (e.g. ``.md``,
    ``.json``, ``.txt``, ``.yml``) returns ``False``.  An empty list returns
    ``False``.

    Extension matching is case-insensitive; path separators are normalized via
    :func:`_normalize` before the suffix is extracted.

    Args:
        changed_files: Paths that changed in the current run (any separator).

    Returns:
        ``True`` if any file's extension (lowercased) is in
        ``_CODE_EXTENSIONS``; ``False`` otherwise.
    """
    for raw in changed_files:
        normalized = _normalize(raw)
        # Use posixpath-style suffix extraction: everything after the last dot.
        dot_idx = normalized.rfind(".")
        if dot_idx != -1:
            ext = normalized[dot_idx:].lower()
            if ext in _CODE_EXTENSIONS:
                return True
    return False


def manifest(
    changed_files: list[str],
    footprint: list[str],
    diffstat: str = "",
) -> dict:
    """Build a full footprint manifest for a KataHarness run.

    Args:
        changed_files: Paths that changed in the current run.
        footprint: Declared allowed paths / directory prefixes.
        diffstat: Optional ``git diff --stat`` output string.

    Returns:
        Dictionary with keys ``footprint``, ``changed``, ``inFootprint``,
        ``outOfFootprint``, ``withinFootprint``, ``diffstat``, and
        ``codeBearing``.
    """
    parts = partition(changed_files, footprint)
    return {
        "footprint": footprint,
        "changed": changed_files,
        "inFootprint": parts["in_footprint"],
        "outOfFootprint": parts["out_of_footprint"],
        "withinFootprint": is_within_footprint(changed_files, footprint),
        "diffstat": diffstat,
        "codeBearing": code_bearing(changed_files),
    }


# ---------------------------------------------------------------------------
# Thin git wrappers — NOT required by tests; pure core above must not call git
# ---------------------------------------------------------------------------


def changed_since(ref: str) -> list[str]:
    """Return a list of files changed since *ref* using ``git diff --name-only``.

    Pinned for determinism (DET-05, DETERMINISM-DOCTRINE law 1/5): the consumer
    (``footprint.json``'s ``withinFootprint``) is a compared verdict input, so the
    changed set must be byte-stable across operator git configs. ``--no-renames``
    keeps a rename visible as delete+add regardless of ``diff.renames`` (the same
    load-bearing pin ``changed_in_task`` documents for this consumer class);
    ``core.quotepath=off`` emits non-ASCII paths verbatim instead of octal-quoted
    (an octal-quoted path never matches a footprint prefix).

    Args:
        ref: Git ref (commit hash, branch, tag, etc.) to diff against HEAD.

    Returns:
        Sorted list of changed file paths (forward-slash normalized).
    """
    result = subprocess.run(
        ["git", "-c", "core.quotepath=off", "diff", "--name-only", "--no-renames", ref],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [_normalize(line) for line in result.stdout.splitlines() if line.strip()]
    return sorted(lines)


def changed_in_task(base_ref: str, task_ref: str = "HEAD") -> list[str]:
    """Return files a task changed **relative to its own fork point** (F5).

    The per-task lane check must NOT use a branch-range diff like
    ``git diff integration..task`` — if the task forked from an EARLIER
    integration head, that two-dot diff lists every file integration changed
    afterward as a foreign file, falsely tripping the drift check.

    This uses the **three-dot** form ``git diff base...task``, which diffs from
    ``merge-base(base, task)`` to ``task`` — i.e. only what the task's own
    commits changed since it diverged. Foreign integration-side changes are
    excluded by construction.

    ``--no-renames`` is load-bearing (adval F5-1): with rename detection on (the
    git default), a ``git mv foreign.txt owned/`` reports only the DESTINATION —
    the deletion of the foreign source is invisible to the lane check, and the
    result silently depends on the operator's ``diff.renames`` config. A lane
    check wants the add AND the delete, deterministically.

    ``core.quotepath=off`` is equally load-bearing (DET-04): with quotepath ON
    (the git default) a non-ASCII path is emitted octal-quoted
    (``"caf\\303\\251.py"``) and never matches its footprint prefix — a FALSE
    lane-drift trip. The pin emits the path verbatim so the partition compares
    real paths.

    Fail-closed (adval F5-2, D136): MULTIPLE merge-bases (criss-cross topology)
    make the three-dot base timestamp-dependent — the wrong pick both leaks
    foreign files AND drops task-own files. Ambiguous evidence cannot drive a
    drift verdict, so >1 merge-base RAISES; no common ancestor raises via git
    itself (rc 128). Scope note: only COMMITTED work is visible — dirty/staged
    worktree changes escape any git diff; the gate runs after the task commits.
    Runs in the process CWD (like ``changed_since``) — the orchestrator invokes
    it from the integration root.

    Args:
        base_ref: The integration branch/ref the task will merge into.
        task_ref: The task branch/commit tip (default ``HEAD``).

    Returns:
        Sorted, forward-slash-normalized list of the task's own changed files.
    """
    bases = subprocess.run(
        ["git", "merge-base", "--all", base_ref, task_ref],
        capture_output=True,
        text=True,
        check=True,  # no common ancestor ⇒ rc 1 ⇒ raises (fail-closed)
    )
    base_shas = [b for b in bases.stdout.split() if b]
    if len(base_shas) > 1:
        raise ValueError(
            f"changed_in_task: {len(base_shas)} merge-bases between {base_ref!r} "
            f"and {task_ref!r} (criss-cross topology) — the task diff is ambiguous "
            f"and cannot drive the lane check (D136 fail-closed). Escalate."
        )
    result = subprocess.run(
        [
            "git", "-c", "core.quotepath=off",
            "diff", "--name-only", "--no-renames", f"{base_ref}...{task_ref}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [_normalize(line) for line in result.stdout.splitlines() if line.strip()]
    return sorted(lines)


def file_content_hashes(paths: list[str], repo_root: str = ".") -> dict[str, str | None]:
    """Return ``{path: sha256-hex}`` for each path under *repo_root* (F5 / M4).

    The **evidence-validity substrate** for the Freeze/Float M4 inline
    evaluator: an inline verdict is stamped with the content hashes of the
    files its verify exercised; at the final gate the evidence is valid iff
    those exact files are byte-unchanged. A missing path maps to ``None`` so a
    deletion is detectable (never silently treated as unchanged).

    M4-consumer CONTRACT (adval F5-4): a ``None`` at STAMP time must itself
    invalidate the evidence — naive dict equality would match a gate-time
    ``None`` (``None == None``) and validate evidence for a file that was never
    read. ``None`` also conflates missing / directory / transiently-unreadable
    (all ``OSError``); at gate time that conflation is fail-closed (evidence
    invalid), which is the safe direction. Paths are joined onto *repo_root*
    without containment checks — callers pass repo-relative paths (the
    ``changed_in_task`` output), never untrusted absolute paths.

    Args:
        paths: Repo-relative paths (any separator) to hash.
        repo_root: Directory the paths are relative to (default cwd).

    Returns:
        Mapping of normalized path → sha256 hex digest, or ``None`` if absent.
    """
    result: dict[str, str | None] = {}
    for raw in paths:
        norm = _normalize(raw)
        full = os.path.join(repo_root, norm)
        try:
            with open(full, "rb") as fh:
                result[norm] = hashlib.sha256(fh.read()).hexdigest()
        except OSError:
            result[norm] = None
    return result


# ---------------------------------------------------------------------------
# Baseline reads — the git substrate for the bump-on-modify check (BOM-7/8/9)
#
# These return RAW BYTES on purpose.  ``subprocess.run(..., text=True)`` decodes
# git stdout with the PROCESS LOCALE (cp1252 on a default Windows box — the
# primary dev platform AND ``windows-latest`` in the CI matrix), so every
# non-ASCII byte comes back mojibaked.  Every shipped ``SKILL.md`` contains
# non-ASCII (``≤``, ``—``, ``⇒``, ``…``), so a locale-decoded baseline could
# never equal the UTF-8 file on disk and the consumer would read as "everything
# changed".  The caller decodes UTF-8 explicitly.
# ---------------------------------------------------------------------------


def _pinned_git(args: list[str]) -> subprocess.CompletedProcess[bytes]:
    """Run one read-only git command with this module's pinned config (Doctrine law 1).

    The pin set lives here once and is never re-derived per call site.
    ``core.quotepath=off`` emits a non-ASCII path verbatim instead of
    octal-quoted (DET-04), so a path git prints is directly comparable to a path
    built from a filesystem walk.

    ``check=False``: each caller decides its own policy for a non-zero exit
    (a ref that does not exist, a path absent at that ref).  Nothing here falls
    through to a permissive default — the policy lives at the call site.

    Runs in the process CWD, like :func:`changed_since` / :func:`changed_in_task`.

    Args:
        args: git arguments after the pinned ``-c`` flags — never ``argv[0]``.

    Returns:
        The completed process, with ``stdout``/``stderr`` as raw ``bytes``.
    """
    return subprocess.run(
        ["git", "-c", "core.quotepath=off", *args],
        capture_output=True,
        check=False,
    )


def ref_exists(ref: str) -> bool:
    """Return True iff *ref* resolves to a commit in the repository at the CWD.

    Args:
        ref: Any git ref-ish (``origin/master``, ``refs/remotes/origin/HEAD``, a SHA).

    Returns:
        ``True`` when ``git rev-parse --verify`` resolves ``<ref>^{commit}``.
    """
    return _pinned_git(["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"]).returncode == 0


def origin_head_ref() -> str | None:
    """Return the remote default-branch ref, or ``None`` when it is not set.

    Reads ``refs/remotes/origin/HEAD`` — the symbolic ref ``git clone`` writes to
    record the remote's default branch.  Used as the last base-ref candidate for
    repositories whose trunk is not called ``master`` (BOM-7).

    Returns:
        e.g. ``"refs/remotes/origin/main"``, or ``None`` if unset/not a repo.
    """
    proc = _pinned_git(["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"])
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace").strip() or None


def renames_in_task(base_ref: str, task_ref: str = "HEAD") -> dict[str, str]:
    """Return ``{new path: old path}`` for files RENAMED between the two refs.

    :func:`changed_in_task` pins ``--no-renames`` deliberately (adval F5-1) so a
    ``git mv`` stays visible as delete+add.  That is right for a lane check and
    wrong for a "what did this file look like before?" lookup: a path-keyed
    baseline read would find nothing at the new path and conclude the file is
    NEW — letting a moved-and-rewritten file launder itself past a
    changed-since-baseline rule (BOM-9).  This map closes that path.

    ``-M`` is passed EXPLICITLY rather than inherited from the operator's
    ``diff.renames`` config, so the map is config-independent (law 1).  The
    three-dot form matches :func:`changed_in_task`, so both describe the same
    fork-point comparison.

    Fail-closed: a git error RAISES rather than returning an empty map — an
    empty map is indistinguishable from "no renames" and would silently restore
    the very bypass this function exists to close (D136).

    Args:
        base_ref: The ref the work will merge into.
        task_ref: The branch/commit tip (default ``HEAD``).

    Returns:
        Mapping of forward-slash-normalized new path → old path.  Empty when the
        diff genuinely contains no renames.

    Raises:
        subprocess.CalledProcessError: git exited non-zero.
    """
    proc = _pinned_git(["diff", "-M", "--name-status", f"{base_ref}...{task_ref}"])
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(
            proc.returncode,
            ["git", "diff", "-M", "--name-status", f"{base_ref}...{task_ref}"],
            proc.stdout,
            proc.stderr,
        )
    mapping: dict[str, str] = {}
    for line in proc.stdout.decode("utf-8", "replace").splitlines():
        fields = line.split("\t")
        # Rename rows are `R<similarity>\t<old>\t<new>`; every other status is 2 fields.
        if len(fields) == 3 and fields[0].startswith("R"):
            mapping[_normalize(fields[2])] = _normalize(fields[1])
    return mapping


def blob_at_ref(ref: str, path: str) -> bytes | None:
    """Return the raw bytes of *path* as of *ref*, or ``None`` if absent there.

    *path* is repo-root-relative POSIX — the form :func:`changed_in_task` emits.
    ``<rev>:<path>`` resolves from the top of the tree (only a leading ``./``
    makes it CWD-relative), so the read does not depend on the process CWD.

    ``None`` means **absent at that ref**, which for the bump check is the one
    exempt case: a genuinely new file with nothing to bump from (BOM-4).  It must
    never be read as "unchanged".

    Args:
        ref: The baseline ref to read from.
        path: Repo-root-relative POSIX path.

    Returns:
        The blob's bytes, or ``None`` when the path does not exist at *ref*.
    """
    proc = _pinned_git(["show", f"{ref}:{path}"])
    if proc.returncode != 0:
        return None
    return proc.stdout


def diff_stat(ref: str) -> str:
    """Return the ``git diff --stat`` output since *ref*.

    Args:
        ref: Git ref (commit hash, branch, tag, etc.) to diff against HEAD.

    Pinned for determinism (DET-06, DETERMINISM-DOCTRINE law 6): a bare
    ``git diff --stat`` auto-sizes its output to the ``COLUMNS`` env var (falling
    back to the terminal width), so the same diff yields byte-different diffstat
    strings per terminal width. The string is stored verbatim in the durable
    ``footprint.json`` (via :func:`manifest` → ``gate_emit``), so a width-varying
    stat is a non-reproducible durable artifact. ``--stat=200`` and
    ``--stat-graph-width=200`` pin the total and graph column widths independent
    of ``COLUMNS`` / TTY, so the stat is byte-stable across operator terminals.

    Returns:
        Raw stat string from git.
    """
    result = subprocess.run(
        ["git", "diff", "--stat=200", "--stat-graph-width=200", ref],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()
