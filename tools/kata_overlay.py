"""kata_overlay.py — overlay store + base+overlay→SKILL.md composer for KataHarness.

Provides the overlay layer defined in the install-update-polish DESIGN §2/§3/§6.
This module is PURE and STDLIB-ONLY: NO git, NO network, NO yaml, NO third-party
imports.  The materialize path runs via ``uv run python tools/kata_install.py`` from
the HOME ROOT (and a plain ``python3``/``python`` fallback) where pyyaml is NOT
guaranteed to be installed — the same zero-dependency invariant that lets
``install.sh`` run anywhere.  Importing yaml here (directly or transitively via
``validate_skills``) would make ``kata_install``'s import-guarded ``_materialize_pass``
silently no-op in a real install, so overlays would never materialize.  Therefore
this module splits frontmatter and edits it with a byte-preserving LINE-BASED
editor, never a YAML parse + re-dump.

The overlay store lives at <home>/.kata-overlay/overlay.json (git-ignored, user-owned).
The materialization record lives at <home>/.kata-overlay/materialized.json.

Public API
----------
overlay_dir(home) -> Path
read_overlay(home) -> dict
validate_overlay(data) -> list[str]
has_overlay(home, name) -> bool
apply_overlay(base_text, entry) -> str
write_overlay_entry(home, name, entry) -> Path
drop_overlay_entry(home, name) -> bool
adaptation_context(home) -> "install"|"dev-repo"
read_materialized(home) -> dict
write_materialized(home, obj) -> Path
record_slot(home, name, info) -> Path
drop_slot(home, name) -> bool

Overlay schema (overlay.json):

    {
      "schema": 1,
      "skills": {
        "<skill-name>": {
          "frontmatterOverrides": { "<field>": <value> },
          "prepend": [ { "anchor": "<heading or null>", "markdown": "<block>" } ],
          "append":  [ { "anchor": "<heading or null>", "markdown": "<block>" } ],
          "pin": "<semver>|null",
          "baseSha": "<sha256 of base SKILL.md at authoring time>|null",
          "baseSuiteSemver": "<suite semver at authoring>|null"
        }
      }
    }

Materialized schema (materialized.json):

    {
      "schema": 1,
      "slots": {
        "<skill-name>": {
          "hostPath": "<abs path to host slot>",
          "baseMode": "symlink|copy",
          "source": "overlay|fork",
          "appliedSha": "<sha256 of the composed SKILL.md>"
        }
      }
    }

Compose semantics — M4 (DESIGN §2, frozen):
- frontmatterOverrides = shallow per-key REPLACE.  List-valued keys (tags,
  allowed-tools, aliases, supersedes) are replaced WHOLESALE, never element-merged.
  Each overridden key's value-block is rebuilt; EVERY non-overridden frontmatter
  line is left BYTE-IDENTICAL (no reformatting).
- prepend/append blocks: spliced at a named heading-anchor.
    prepend: inserted as FIRST content immediately AFTER the anchor heading line.
    append:  inserted as LAST content just BEFORE the next equal-or-higher heading
             (or end of section if none).
    anchor=None: start-of-body (prepend) / end-of-body (append).
- Multiple blocks for the same anchor apply in array order.
- Fail-CLOSED: an anchor that does not resolve in a present base → ValueError.
- Missing-base (M3): handled by the CALLER (B2 materialize pass), NOT here.
  apply_overlay assumes base_text is present.

Security: all operator-supplied paths are ``..``-guarded (CWE-23).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_OVERLAY_DIR_NAME = ".kata-overlay"
_OVERLAY_FILENAME = "overlay.json"
_MATERIALIZED_FILENAME = "materialized.json"
_SCHEMA = 1


# ---------------------------------------------------------------------------
# Path safety — mirror kata_version._safe_abs convention exactly
# ---------------------------------------------------------------------------


def _safe_abs(raw: str | Path) -> Path:
    """Reject ``..`` traversal (CWE-23) then resolve to an absolute path."""
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"kata_overlay: refusing path with '..' traversal: {raw!r}")
    return p.resolve()


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def overlay_dir(home: str | Path) -> Path:
    """Absolute path to the overlay store directory: ``<home>/.kata-overlay``."""
    return _safe_abs(home) / _OVERLAY_DIR_NAME


def _overlay_path(home: str | Path) -> Path:
    return overlay_dir(home) / _OVERLAY_FILENAME


def _materialized_path(home: str | Path) -> Path:
    return overlay_dir(home) / _MATERIALIZED_FILENAME


# ---------------------------------------------------------------------------
# overlay.json read / write
# ---------------------------------------------------------------------------


def read_overlay(home: str | Path) -> dict:
    """Parse overlay.json; degrade to ``{"schema":1,"skills":{}}`` on absent/corrupt.

    Mirrors the fail-closed-but-lenient read pattern from ``kata_settings.read_settings``
    and ``kata_version.read_stamp``.
    """
    p = _overlay_path(home)
    if not p.exists():
        return {"schema": _SCHEMA, "skills": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"schema": _SCHEMA, "skills": {}}
        if "skills" not in data or not isinstance(data["skills"], dict):
            return {"schema": _SCHEMA, "skills": {}}
        return data
    except (json.JSONDecodeError, OSError):
        return {"schema": _SCHEMA, "skills": {}}


def validate_overlay(data: dict) -> list[str]:
    """Pure validator for the overlay store structure.

    Returns a list of ERROR strings (empty list = valid).  Fail-closed: unknown
    or mis-typed fields are errors.  Anchor resolvability is checked at
    apply_overlay time (requires the actual base text), not here.
    """
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["overlay store must be a dict"]
    if not isinstance(data.get("schema"), int):
        errors.append(f"'schema' must be an int; got: {data.get('schema')!r}")
    skills = data.get("skills")
    if not isinstance(skills, dict):
        errors.append("'skills' must be a dict")
        return errors
    for name, entry in skills.items():
        if not isinstance(entry, dict):
            errors.append(f"skill '{name}': entry must be a dict")
            continue
        fmo = entry.get("frontmatterOverrides", {})
        if not isinstance(fmo, dict):
            errors.append(f"skill '{name}': frontmatterOverrides must be a dict")
        for key in ("prepend", "append"):
            val = entry.get(key, [])
            if not isinstance(val, list):
                errors.append(f"skill '{name}': '{key}' must be a list")
            else:
                for i, block in enumerate(val):
                    if not isinstance(block, dict):
                        errors.append(f"skill '{name}': {key}[{i}] must be a dict")
                    elif "markdown" not in block:
                        errors.append(
                            f"skill '{name}': {key}[{i}] missing required 'markdown' key"
                        )
        pin = entry.get("pin")
        if pin is not None and not isinstance(pin, str):
            errors.append(f"skill '{name}': 'pin' must be a semver string or null; got {pin!r}")
    return errors


def has_overlay(home: str | Path, name: str) -> bool:
    """True iff a non-empty entry exists for ``name`` in the overlay store."""
    overlay = read_overlay(home)
    return name in overlay.get("skills", {})


def write_overlay_entry(home: str | Path, name: str, entry: dict) -> Path:
    """Read-merge-write a single skill's overlay entry.

    NEVER wholesale-overwrites the store — implements the D127 / item-3 lesson
    from kata_settings: read existing → update only the named skill → write.
    All other skills' entries are preserved verbatim.

    Returns the path to overlay.json.
    """
    od = overlay_dir(home)
    od.mkdir(parents=True, exist_ok=True)
    data = read_overlay(home)
    data.setdefault("schema", _SCHEMA)
    data.setdefault("skills", {})
    data["skills"][name] = entry
    p = _overlay_path(home)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return p


def drop_overlay_entry(home: str | Path, name: str) -> bool:
    """Remove one skill's overlay entry (factory-reset of a single skill).

    Returns True if the entry was present and removed; False if it was not found.
    All other skills' entries are preserved.
    """
    data = read_overlay(home)
    skills = data.get("skills", {})
    if name not in skills:
        return False
    del skills[name]
    data["skills"] = skills
    od = overlay_dir(home)
    od.mkdir(parents=True, exist_ok=True)
    p = _overlay_path(home)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# Frontmatter split — stdlib-only (NO yaml).  Mirrors the SKILL.md shape
# "---\n<frontmatter>\n---\n<body>" using the same split as
# validate_skills.parse_frontmatter, but returns the RAW frontmatter TEXT
# (not a parsed dict) so editing stays byte-preserving.
# ---------------------------------------------------------------------------


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    """Split a SKILL.md string into (raw_frontmatter_text, body).

    Returns ``(None, text)`` when there is no leading frontmatter block.
    Otherwise returns the raw text BETWEEN the opening and closing ``---``
    delimiters (including its own leading/trailing newlines) and the body
    (everything after the closing ``---``, starting with its newline).

    Reconstruction is exact: ``"---" + fm + "---" + body == original``.
    """
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    return parts[1], parts[2]


# Top-level frontmatter key line: starts with a non-space char, has a colon,
# no leading whitespace (so indented continuation / list items are NOT keys).
_TOP_KEY_RE = re.compile(r"^(\S[^:]*):")

# Characters that force double-quoting of a scalar to keep it a valid, safe
# YAML/SKILL.md value.  Over-quoting is harmless (it round-trips identically);
# under-quoting is not — so we quote liberally on any of these.
_QUOTE_TRIGGER = set(":#[]{}&*!|>%@`\"',")


def _emit_str(s: str) -> str:
    """Emit a string scalar — bare when safe, double-quoted otherwise."""
    if s == "":
        return '""'
    needs = (
        s != s.strip()  # leading/trailing whitespace
        or s[0] in "-?"  # ambiguous YAML indicators at start
        or any(ch in _QUOTE_TRIGGER for ch in s)
    )
    if not needs:
        return s
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _emit_scalar(val) -> str:
    """Emit a single override value as an inline (flow) YAML scalar/collection.

    Handles the value types that appear in real frontmatter overrides:
    None, bool, int/float, str, list, dict.  Lists/dicts use flow style
    (``[a, b]`` / ``{k: v}``) — the same convention real skills already use
    for ``allowed-tools``/``tags`` (e.g. ``allowed-tools: [Read, Bash]``).
    """
    if val is None:
        return "null"
    if isinstance(val, bool):  # before int (bool is an int subclass)
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        return _emit_str(val)
    if isinstance(val, list):
        return "[" + ", ".join(_emit_scalar(v) for v in val) + "]"
    if isinstance(val, dict):
        return "{" + ", ".join(f"{k}: {_emit_scalar(v)}" for k, v in val.items()) + "}"
    return _emit_str(str(val))


def _emit_key_line(key: str, val) -> str:
    """Emit one ``key: value`` frontmatter line for an override."""
    return f"{key}: {_emit_scalar(val)}"


def _edit_frontmatter(fm_text: str, overrides: dict) -> str:
    """Apply frontmatterOverrides to RAW frontmatter text, byte-preserving.

    M4 semantics: each overridden top-level key's value-BLOCK is rebuilt
    wholesale (the whole block — multi-line list values included — is replaced
    by a single flow-style line); a key absent from the base is appended.  Every
    NON-overridden line is left byte-identical (no reformatting of untouched keys).

    A top-level key line matches ``^(\\S[^:]*):``.  Its value-block extends from
    that line through all following lines that are blank, indented (leading
    whitespace), or list items (``-`` …), up to (not including) the next
    top-level key.  Trailing blank lines within a rebuilt block are re-emitted so
    the frontmatter keeps its closing ``---`` on its own line.
    """
    if not overrides:
        return fm_text

    lines = fm_text.split("\n")
    key_positions: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        m = _TOP_KEY_RE.match(line)
        if m:
            key_positions.append((idx, m.group(1).strip()))

    remaining = dict(overrides)
    first_key_idx = key_positions[0][0] if key_positions else len(lines)

    out: list[str] = list(lines[:first_key_idx])  # preamble (e.g. leading "")
    for pos, (idx, key) in enumerate(key_positions):
        end = key_positions[pos + 1][0] if pos + 1 < len(key_positions) else len(lines)
        block = lines[idx:end]
        if key in remaining:
            # Count trailing blank lines in the original block — preserve them so
            # the last-key case keeps the frontmatter's trailing newline.
            trailing_blanks = 0
            for bl in reversed(block):
                if bl.strip() == "":
                    trailing_blanks += 1
                else:
                    break
            out.append(_emit_key_line(key, remaining.pop(key)))
            out.extend([""] * trailing_blanks)
        else:
            out.extend(block)

    # Any overrides for keys absent from the base: insert before trailing blanks
    # so the closing delimiter stays on its own line.
    if remaining:
        insert_pos = len(out)
        while insert_pos > 0 and out[insert_pos - 1].strip() == "":
            insert_pos -= 1
        new_lines = [_emit_key_line(k, v) for k, v in remaining.items()]
        out[insert_pos:insert_pos] = new_lines

    return "\n".join(out)


# ---------------------------------------------------------------------------
# apply_overlay — the M4 compose semantics (DESIGN §2, frozen)
# ---------------------------------------------------------------------------


def apply_overlay(base_text: str, entry: dict) -> str:
    """Apply an overlay entry to a base SKILL.md string → composed SKILL.md string.

    M4 compose semantics (DESIGN §2):

    ``frontmatterOverrides``
        Shallow per-key REPLACE over the base frontmatter, applied with a
        byte-preserving LINE-BASED editor (no YAML parse/re-dump).  List-valued
        keys (tags, allowed-tools, aliases, supersedes) are replaced WHOLESALE —
        to extend a list the overlay must restate the full intended list.  Keys
        absent from the override are left byte-identical to the base.

    ``prepend``/``append`` blocks
        Each block targets a named heading anchor (e.g. ``"## Output"``).
        - prepend: inserted as the FIRST content immediately after the heading line.
        - append: inserted as the LAST content just before the next heading of
          equal-or-higher level, or end of section if none follows.
        anchor=None → start-of-body (prepend) / end-of-body (append).
        Multiple blocks for the same anchor apply in array order.

    Fail-CLOSED
        An anchor that does not resolve in a *present* base → ``ValueError``.
        This is distinct from the missing-base case (M3): when the upstream skill
        no longer exists, the B2 materialize pass emits a NOTE and skips the entry
        *without calling apply_overlay*.  This function assumes ``base_text`` is
        present.  Never call apply_overlay with an absent base — that is M3 territory.

    Stdlib-only: no yaml, no third-party imports (the install/materialize path is
    not guaranteed to have pyyaml).
    """
    fm_text, body = _split_frontmatter(base_text)

    # 1. Apply frontmatterOverrides byte-preserving (only when frontmatter present).
    overrides: dict = entry.get("frontmatterOverrides", {})
    if fm_text is not None and overrides:
        fm_text = _edit_frontmatter(fm_text, overrides)

    # 2. Apply prepend blocks.
    prepend_blocks: list[dict] = entry.get("prepend", [])
    if prepend_blocks:
        body = _apply_blocks(body, prepend_blocks, "prepend")

    # 3. Apply append blocks.
    append_blocks: list[dict] = entry.get("append", [])
    if append_blocks:
        body = _apply_blocks(body, append_blocks, "append")

    # 4. Reconstruct.  When there is no frontmatter block, return body + splices.
    if fm_text is None:
        return body
    return "---" + fm_text + "---" + body


def _find_heading_index(lines: list[str], anchor: str) -> int | None:
    """Return the index of the first line matching *anchor* (trailing-whitespace-tolerant).

    Returns None when not found.  When the same heading appears multiple times,
    the first occurrence is used (unambiguous for the common single-occurrence case).
    """
    anchor_stripped = anchor.rstrip()
    for i, line in enumerate(lines):
        if line.rstrip() == anchor_stripped:
            return i
    return None


def _heading_level(line: str) -> int:
    """Return the ATX heading level (count of leading ``#``); 0 if not a heading."""
    # Strip up to 3 leading spaces (CommonMark ATX spec), then count '#'.
    stripped = line.lstrip(" ")
    if not stripped.startswith("#"):
        return 0
    level = 0
    for ch in stripped:
        if ch == "#":
            level += 1
        else:
            break
    # A valid ATX heading must have a space (or be just #s); guard against #word.
    if level < len(stripped) and stripped[level] not in (" ", "\t", "\n", ""):
        return 0
    return level


def _apply_blocks(body: str, blocks: list[dict], mode: str) -> str:
    """Apply all prepend (or append) blocks to the body string.

    For ``prepend``: blocks are processed in REVERSE order so that the array
    order is preserved in the final output (each block inserts at the same
    anchor position, so reverse processing yields the correct sequence).

    For ``append``: blocks are processed in FORWARD order — each successive
    block finds the same anchor and inserts after the previous insertion,
    naturally preserving array order.

    Raises ``ValueError`` on an unresolvable anchor (fail-closed).
    """
    lines: list[str] = body.split("\n")

    if mode == "prepend":
        for block in reversed(blocks):
            lines = _insert_prepend(lines, block)
    else:
        for block in blocks:
            lines = _insert_append(lines, block)

    return "\n".join(lines)


def _insert_prepend(lines: list[str], block: dict) -> list[str]:
    """Insert one prepend block.  Returns the updated lines list."""
    anchor = block.get("anchor")
    markdown: str = block.get("markdown", "")
    markdown_lines: list[str] = markdown.split("\n")

    if anchor is None:
        # null anchor: start-of-body.  Body starts with "\n" so lines[0] == "".
        # Insert after the leading empty string so reconstruction keeps "---"
        # delimiters on their own line.
        if lines and lines[0] == "":
            return lines[:1] + markdown_lines + lines[1:]
        # Unusual: body doesn't start with \n — prepend before everything.
        return markdown_lines + lines

    idx = _find_heading_index(lines, anchor)
    if idx is None:
        raise ValueError(
            f"kata_overlay: prepend anchor {anchor!r} not found in base body (fail-closed)"
        )
    # Insert immediately after the heading line.
    return lines[: idx + 1] + markdown_lines + lines[idx + 1 :]


def _insert_append(lines: list[str], block: dict) -> list[str]:
    """Insert one append block.  Returns the updated lines list."""
    anchor = block.get("anchor")
    markdown: str = block.get("markdown", "")
    markdown_lines: list[str] = markdown.split("\n")

    if anchor is None:
        # null anchor: end-of-body — append after all existing lines.
        return lines + markdown_lines

    idx = _find_heading_index(lines, anchor)
    if idx is None:
        raise ValueError(
            f"kata_overlay: append anchor {anchor!r} not found in base body (fail-closed)"
        )

    # Determine anchor heading level.
    anchor_level = _heading_level(lines[idx])
    if anchor_level == 0:
        # Matched line is not actually a heading (edge case); treat as level 1.
        anchor_level = 1

    # Find the next line that is a heading of equal-or-higher level (fewer/equal #s).
    insert_at = len(lines)  # default: end of document
    for j in range(idx + 1, len(lines)):
        level = _heading_level(lines[j])
        if level > 0 and level <= anchor_level:
            insert_at = j
            break

    return lines[:insert_at] + markdown_lines + lines[insert_at:]


# ---------------------------------------------------------------------------
# adaptation_context — context discriminator for kata-improve (DESIGN §6)
# ---------------------------------------------------------------------------


def adaptation_context(home: str | Path) -> str:
    """Context discriminator for ``kata-improve`` (DESIGN §6.2).

    Returns ``"install"`` iff ``<home>/.kata-version`` exists (written by any
    successful install — plain or via ``--update``, per M1 DESIGN §5).  Returns
    ``"dev-repo"`` otherwise (a canonical maintainer checkout that has never
    been installed into a host has no stamp, so the safety rail defaults off).

    PURE: no git, no network.  Delegates path resolution to kata_version.stamp_path
    (same ``..``-guard convention, avoids duplicating the stamp filename constant).
    kata_version is itself stdlib-only, so this import adds no yaml dependency.
    """
    import kata_version  # clean same-package import; kata_version is stdlib-only

    return "install" if kata_version.stamp_path(home).exists() else "dev-repo"


# ---------------------------------------------------------------------------
# materialized.json read / write
# ---------------------------------------------------------------------------


def read_materialized(home: str | Path) -> dict:
    """Parse materialized.json; degrade to ``{"schema":1,"slots":{}}`` on absent/corrupt."""
    p = _materialized_path(home)
    if not p.exists():
        return {"schema": _SCHEMA, "slots": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"schema": _SCHEMA, "slots": {}}
        if "slots" not in data or not isinstance(data["slots"], dict):
            return {"schema": _SCHEMA, "slots": {}}
        return data
    except (json.JSONDecodeError, OSError):
        return {"schema": _SCHEMA, "slots": {}}


def write_materialized(home: str | Path, obj: dict) -> Path:
    """Write the materialization record and return its path."""
    od = overlay_dir(home)
    od.mkdir(parents=True, exist_ok=True)
    p = _materialized_path(home)
    p.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    return p


def record_slot(home: str | Path, name: str, info: dict) -> Path:
    """Read-merge-write a single slot entry in materialized.json.

    Preserves all other slots (same D127 / read-merge-write discipline as
    ``write_overlay_entry``).  Returns the path to materialized.json.
    """
    od = overlay_dir(home)
    od.mkdir(parents=True, exist_ok=True)
    data = read_materialized(home)
    data.setdefault("schema", _SCHEMA)
    data.setdefault("slots", {})
    data["slots"][name] = info
    p = _materialized_path(home)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return p


def drop_slot(home: str | Path, name: str) -> bool:
    """Remove one slot from materialized.json.

    Returns True if the slot was present and removed; False if not found.
    All other slots are preserved.
    """
    data = read_materialized(home)
    slots = data.get("slots", {})
    if name not in slots:
        return False
    del slots[name]
    data["slots"] = slots
    od = overlay_dir(home)
    od.mkdir(parents=True, exist_ok=True)
    p = _materialized_path(home)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True
