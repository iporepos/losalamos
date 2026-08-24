"""
populate_attributes.py
---------------------
Batch-creation script for Flare canonical attribute registry notes.

Reads a JSON seed file and writes one Obsidian ``.md`` note per entry into
a target vault folder, using :class:`losalamos.notes.NoteAttribute`.

Depends on ``losalamos`` being installed with ``NoteAttribute`` present in
``losalamos.notes``. Run from any location.

Usage
-----

.. code-block:: shell

    python populate_attributes.py <seed.json> <vault_folder> [--overwrite]

Seed JSON format
----------------

.. code-block:: json

    {
        "defaults": {
            "theme": "101",
            "type": "R",
            "category": "variable",
            "tags": ["hydrology"],
            "subject": "[[Surface Hydrology]]"
        },
        "entries": [
            {
                "name": "Streamflow",
                "title": "Volumetric flow rate of water in a channel cross-section",
                "units_ref": "m^3/s",
                "domain": "[0U)",
                "symbol": "Q",
                "alias": "streamflow",
                "dimension": "L^{3}/T",
                "source": "Chow et al. (1988) Applied Hydrology",
                "synonyms": "discharge, river flow",
                "abstract": "...",
                "tags": ["surface-water"],
                "twin_notes": ["Discharge", "River Flow"]
            }
        ]
    }

Defaults and entries
--------------------
``theme``
    Required in ``defaults``. Determines the ``TTT`` segment of all codes
    in this batch. One seed file = one theme.

``tags``
    Additive. ``defaults`` tags apply to every entry; entry-level tags
    extend them. The base tag ``attribute-note`` is always present.

``subject``
    Override. Entry-level subject replaces the default for that entry.
    Write as Obsidian wiki-link notation: ``[[Note Name]]``.
    Missing or null at either level is ignored.

``twin_notes``
    Population directive (not written to frontmatter). List of synonym
    names that receive their own note with a serial code and ``twin_code``
    pointing to the canonical. Twins inherit the canonical's resolved tags
    and subject.

``code``
    Never written in the seed — always auto-assigned by scanning existing
    notes in the vault folder and incrementing from the highest serial.

Field conventions
-----------------
``symbol``
    LaTeX raw, no ``$`` delimiters. Stripped automatically if present.

``dimension``
    Plain exponent notation, no ``[]`` brackets. Stripped automatically.

``units_ref``
    Plain readable text, no LaTeX. Rendered downstream.

``domain``
    Interval notation using ``U`` in place of ``:`` to avoid YAML conflicts.
    Examples: ``[0U)``, ``(U)``, ``(0U)``, ``[0U1]``, ``(-273.15U)``.
"""

# IMPORTS
# =======================================================================

import json
import re
import sys
from pathlib import Path

from losalamos.notes import Note, NoteAttribute


# CONSTANTS
# =======================================================================

# Regex to match a Flare attribute code — F101A007 etc.
CODE_PATTERN = re.compile(r"^F(\d{3})A(\d{3})$")


# HELPERS
# =======================================================================

def _as_list(value) -> list:
    """
    Coerce a seed tags value to a list, handling str, list, and None.

    :param value: Raw tags value — str, list, or None.
    :return: List of tag strings, empty list for missing/null.
    """
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def _scan_next_serial(vault_folder: Path, theme: str) -> int:
    """
    Scan existing ``.md`` notes in ``vault_folder`` by reading each file's
    ``code`` frontmatter field, and return the next available serial for
    the given theme.

    Note files are named by attribute name (not code), so frontmatter
    scanning is required rather than filename globbing.

    :param vault_folder: Path to the vault folder to scan.
    :param theme: Three-digit theme string, e.g. ``"101"``.
    :return: Next available serial as an integer (1-indexed).
    """
    max_serial = 0

    for md_file in vault_folder.glob("*.md"):
        try:
            metadata = Note.parse_metadata(md_file)
        except Exception:
            continue
        if not metadata:
            continue
        code = str(metadata.get("code", "")).strip()
        match = CODE_PATTERN.match(code)
        if match and match.group(1) == theme:
            serial = int(match.group(2))
            if serial > max_serial:
                max_serial = serial

    return max_serial + 1


def _merge(defaults: dict, entry: dict) -> dict:
    """Merge defaults with entry overrides. Entry values take precedence."""
    merged = {k: v for k, v in defaults.items()}
    merged.update(entry)
    return merged


def _validate(entry: dict, required_fields: set) -> None:
    """
    Raise ValueError if any required field is missing from the entry.

    :param entry: Merged entry dict.
    :param required_fields: Set of field names that must be present.
    """
    for field in required_fields:
        if not entry.get(field):
            raise ValueError(
                f"Entry missing required field '{field}': "
                f"{entry.get('name', '<unnamed>')}"
            )


def _assign_code(theme: str, serial: int) -> str:
    """Build a Flare attribute code, e.g. ``F101A007``."""
    return f"F{theme}A{serial:03d}"


def _note_filename(name: str) -> str:
    """Build the ``.md`` filename from the attribute name, preserving spaces."""
    return f"{name}.md"


def _read_existing_code(file_path: Path) -> str | None:
    """
    Read the ``code`` field from the frontmatter of an existing note.

    Returns ``None`` if the file does not exist, has no frontmatter, or
    the ``code`` field is absent or empty.

    :param file_path: Path to the ``.md`` file.
    :return: Existing code string, e.g. ``"F101A003"``, or ``None``.
    """
    if not file_path.exists():
        return None
    try:
        metadata = Note.parse_metadata(file_path)
    except Exception:
        return None
    if not metadata:
        return None
    code = str(metadata.get("code", "")).strip()
    return code if code else None


def _write_entry(
    note_cls: NoteAttribute,
    entry: dict,
    vault_folder: Path,
    overwrite: bool,
    label: str = "write",
) -> tuple[bool, bool]:
    """
    Write a single note to disk.

    On refresh (``overwrite=True``, file already exists), the existing
    ``code`` is read from frontmatter and reused — the serial counter is
    not consumed. All other content is updated from the entry dict.

    On create (file does not exist), the code must already be assigned in
    ``entry`` by the caller.

    :param note_cls: Shared ``NoteAttribute`` instance.
    :param entry: Fully resolved entry dict — code and ``_tags`` /
        ``_subject`` already assigned for new entries; for existing entries
        the code will be overwritten by the value read from disk.
    :param vault_folder: Destination folder.
    :param overwrite: If ``False``, skip existing files. If ``True``,
        refresh them keeping their existing code.
    :param label: Display label for console output.
    :return: Tuple ``(written, serial_consumed)`` — both booleans.
        ``serial_consumed`` is ``False`` when an existing code was reused.
    """
    filename = _note_filename(entry["name"])
    file_path = vault_folder / filename
    existing_code = _read_existing_code(file_path)

    if existing_code and not overwrite:
        print(f"  [skip]   {filename} — already exists")
        return False, False

    if existing_code:
        # Refresh: reuse existing code, do not consume a serial
        entry = {**entry, "code": existing_code}
        action = f"refresh"
    else:
        action = label

    note_cls.load_new(file_note=file_path, entry=entry)
    note_cls.save()
    print(f"  [{action}] {filename}  →  {entry['code']}")
    serial_consumed = existing_code is None
    return True, serial_consumed


def _build_twin_entry(
    name: str,
    code: str,
    twin_code: str,
    tags: list,
    subject: str,
) -> dict:
    """
    Build a minimal entry dict for a twin note.

    Twin notes carry only ``name``, ``code``, ``twin_code``, and the
    resolved ``_tags`` and ``_subject`` inherited from their canonical.
    All other fields are left empty.

    :param name: Display name of the twin, e.g. ``"Rainfall"``.
    :param code: Auto-assigned Flare code for the twin.
    :param twin_code: Flare code of the canonical entry this twin points to.
    :param tags: Resolved tag list inherited from the canonical entry.
    :param subject: Resolved subject string inherited from the canonical.
    :return: Minimal entry dict.
    """
    return {
        "name": name,
        "code": code,
        "twin_code": twin_code,
        "_tags": tags,
        "_subject": subject,
    }


# ENTRY POINT
# =======================================================================

def populate_canonical(
    seed_path: Path,
    vault_folder: Path,
    overwrite: bool = False,
) -> None:
    """
    Read a JSON seed file and write one Obsidian attribute note per entry,
    followed immediately by any twin notes declared under ``twin_notes``.

    Codes are auto-assigned sequentially within the theme for both canonical
    entries and twins, in the order they appear in the seed file.

    :param seed_path: Path to the JSON seed file.
    :param vault_folder: Destination folder for note files.
    :param overwrite: If ``False`` (default), skip existing files.
        If ``True``, overwrite them.
    """
    vault_folder.mkdir(parents=True, exist_ok=True)

    with open(seed_path, "r", encoding="utf-8") as f:
        seed = json.load(f)

    defaults = seed.get("defaults", {})
    entries = seed.get("entries", [])

    if not entries:
        print("No entries found in seed file.")
        return

    theme = defaults.get("theme")
    if not theme:
        raise ValueError("'theme' must be defined in 'defaults'.")
    theme = str(theme).zfill(3)

    print(f"Seed  : {seed_path.name} — {len(entries)} entries")
    print(f"Theme : {theme}")
    print(f"Vault : {vault_folder}")
    print()

    next_serial = _scan_next_serial(vault_folder, theme)
    print(f"Next serial : {next_serial:03d}")
    print()

    note_cls = NoteAttribute()
    written = 0
    skipped = 0

    # Extract default-level tags and subject once
    default_tags = _as_list(defaults.get("tags"))
    default_subject = defaults.get("subject") or ""

    for entry in entries:
        merged = _merge(defaults, entry)
        _validate(merged, note_cls.REQUIRED_FIELDS)

        # Population directives — strip before passing to note
        twin_names = merged.pop("twin_notes", None) or []
        merged.pop("code", None)

        # Resolve tags (additive) and subject (local override)
        merged["_tags"] = NoteAttribute._resolve_tags(
            default_tags=default_tags,
            entry_tags=_as_list(entry.get("tags")),
        )
        merged["_subject"] = NoteAttribute._resolve_subject(
            default_subject=default_subject,
            entry_subject=entry.get("subject") or "",
        )

        # Assign a tentative code — reused or consumed depending on whether
        # the file already exists (resolved inside _write_entry)
        tentative_code = _assign_code(theme, next_serial)
        merged["code"] = tentative_code

        ok, serial_consumed = _write_entry(note_cls, merged, vault_folder, overwrite, label="write")
        written += ok
        skipped += not ok
        if serial_consumed:
            next_serial += 1

        # Canonical code for twins is the one actually written (may differ
        # from tentative_code if the note was refreshed)
        canonical_code = merged["code"] if not ok else (
            tentative_code if serial_consumed
            else _read_existing_code(vault_folder / _note_filename(merged["name"])) or tentative_code
        )

        # Write twin notes immediately after, inheriting canonical's
        # resolved tags and subject
        for twin_name in twin_names:
            twin_code = _assign_code(theme, next_serial)
            twin_entry = _build_twin_entry(
                name=twin_name,
                code=twin_code,
                twin_code=canonical_code,
                tags=merged["_tags"],
                subject=merged["_subject"],
            )
            ok, serial_consumed = _write_entry(note_cls, twin_entry, vault_folder, overwrite, label="twin ")
            written += ok
            skipped += not ok
            if serial_consumed:
                next_serial += 1

    print()
    print(f"Done — {written} written, {skipped} skipped.")


# CLI
# =======================================================================

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python populate_canonical.py <seed.json> <vault_folder> [--overwrite]")
        sys.exit(1)

    seed_path = Path(sys.argv[1])
    vault_folder = Path(sys.argv[2])
    overwrite = "--overwrite" in sys.argv

    if not seed_path.exists():
        print(f"Seed file not found: {seed_path}")
        sys.exit(1)

    populate_canonical(seed_path, vault_folder, overwrite=overwrite)