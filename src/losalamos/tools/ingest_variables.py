# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Batch-creation tool for variable registry notes.

Reads a JSON seed file and writes one Obsidian ``.md`` note per entry into
a target vault folder using :class:`losalamos.notes.NoteVariable`.

Codes are user-assigned and must appear in each entry. Shared fields
(``subject``, ``tags``, ``category``, etc.) can be declared once in
``defaults`` and are merged into every entry automatically.

Usage
-----

.. code-block:: shell

    python -m losalamos.tools.ingest_variables --variables <seed.json> [--overwrite]

Seed JSON format
----------------

The seed file is a **list of batches**. Each batch targets one vault folder
and carries its own ``defaults`` and ``entries``.

.. code-block:: json

    [
        {
            "vault": "/path/to/vault/hydrology",
            "defaults": {
                "subject": "[[Surface Hydrology]]",
                "tags": ["hydrology"],
                "category": "physical"
            },
            "entries": [
                {
                    "code": "F101V001",
                    "name": "Streamflow",
                    "alias": "streamflow",
                    "units": "m^3/s",
                    "range": "[0U)",
                    "symbol": "Q",
                    "dimension": "L^{3}/T"
                }
            ]
        },
        {
            "vault": "/path/to/vault/climate",
            "defaults": {
                "subject": "[[Climatology]]",
                "tags": ["climate"]
            },
            "entries": []
        }
    ]

Batch keys
----------
``vault``
    Required per batch. Path to the destination vault folder.

``defaults``
    Fields applied to every entry in the batch. Entry-level values override
    on conflict, except for ``tags`` which are merged additively.

``tags``
    Additive. ``defaults`` tags apply to every entry; entry-level tags
    extend them. The base tag ``variable-note`` is always prepended.

``subject``
    Entry-level value overrides the default for that entry. Write as
    Obsidian wiki-link notation: ``[[Note Name]]``.

``code``
    User-assigned. Not validated — omitting it leaves the field blank.
"""

# IMPORTS
# =======================================================================

import argparse
import json
import sys
from pathlib import Path

from losalamos.notes import NoteVariable


# HELPERS
# =======================================================================


def _as_list(value) -> list:
    """Coerce a tags value to a list, handling str, list, and None.

    :param value: Raw value — str, list, or None.
    :return: List of strings, empty list for missing/null input.
    """
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def _merge(defaults: dict, entry: dict) -> dict:
    """Merge defaults with entry overrides. Entry values take precedence.

    :param defaults: Shared field values from the ``defaults`` block.
    :param entry: Individual entry dict.
    :return: Merged dict.
    """
    merged = dict(defaults)
    merged.update(entry)
    return merged


def _validate(entry: dict, required_fields: set) -> None:
    """Raise ``ValueError`` if any required field is missing or empty.

    :param entry: Merged entry dict.
    :param required_fields: Set of field names that must be non-empty.
    """
    for field in required_fields:
        if not entry.get(field):
            raise ValueError(
                f"Entry missing required field '{field}': "
                f"{entry.get('name', '<unnamed>')}"
            )


def _write_entry(
    note_cls: NoteVariable,
    entry: dict,
    vault_folder: Path,
    overwrite: bool,
) -> bool:
    """Write a single variable note to disk.

    :param note_cls: Shared ``NoteVariable`` instance (reused across entries).
    :param entry: Fully resolved entry dict with ``_tags`` and ``_subject`` set.
    :param vault_folder: Destination folder for the note file.
    :param overwrite: When ``False``, skip files that already exist.
    :return: ``True`` if the note was written, ``False`` if skipped.
    """
    filename = f"{entry['name']}.md"
    file_path = vault_folder / filename

    if file_path.exists() and not overwrite:
        print(f"  [skip]      {filename}")
        return False

    action = "overwrite" if file_path.exists() else "write"
    note_cls.load_new(file_note=file_path, entry=entry)
    note_cls.save()
    print(f"  [{action}]     {filename}")
    return True


# ENTRY POINT
# =======================================================================


def _run_batch(batch: dict, note_cls: NoteVariable, overwrite: bool) -> tuple[int, int]:
    """Process one batch (vault + defaults + entries).

    :param batch: Single batch dict with ``vault``, ``defaults``, and ``entries``.
    :param note_cls: Shared ``NoteVariable`` instance reused across batches.
    :param overwrite: When ``False``, skip files that already exist.
    :return: Tuple ``(written, skipped)`` counts for this batch.
    """
    vault_raw = batch.get("vault")
    if not vault_raw:
        raise ValueError("A batch is missing the required 'vault' key.")
    vault_folder = Path(vault_raw)
    vault_folder.mkdir(parents=True, exist_ok=True)

    defaults = batch.get("defaults", {})
    entries = batch.get("entries", [])

    print(f"Vault : {vault_folder}  ({len(entries)} entries)")

    if not entries:
        print("  No entries — skipping.")
        return 0, 0

    default_tags = _as_list(defaults.get("tags"))
    default_subject = defaults.get("subject") or ""

    written = 0
    skipped = 0

    for entry in entries:
        merged = _merge(defaults, entry)
        _validate(merged, note_cls.REQUIRED_FIELDS)

        merged["_tags"] = NoteVariable._resolve_tags(
            default_tags=default_tags,
            entry_tags=_as_list(entry.get("tags")),
        )
        merged["_subject"] = NoteVariable._resolve_subject(
            default_subject=default_subject,
            entry_subject=entry.get("subject") or "",
        )

        ok = _write_entry(
            note_cls=note_cls,
            entry=merged,
            vault_folder=vault_folder,
            overwrite=overwrite,
        )
        written += ok
        skipped += not ok

    print(f"  {written} written, {skipped} skipped.")
    return written, skipped


def ingest_variables(
    seed_path: Path,
    overwrite: bool = False,
) -> None:
    """Read a JSON seed file and process all batches.

    The seed must be a list of batch dicts, each with a ``vault``, optional
    ``defaults``, and an ``entries`` list. A single batch dict is also accepted.

    :param seed_path: Path to the JSON seed file.
    :type seed_path: :class:`pathlib.Path`
    :param overwrite: If ``False`` (default), existing files are skipped.
    :type overwrite: bool
    """
    with open(seed_path, "r", encoding="utf-8") as f:
        seed = json.load(f)

    batches = seed if isinstance(seed, list) else [seed]

    print(f"Seed  : {seed_path.name}  ({len(batches)} batch(es))")
    print()

    note_cls = NoteVariable()
    total_written = 0
    total_skipped = 0

    for i, batch in enumerate(batches, start=1):
        if len(batches) > 1:
            print(f"[{i}/{len(batches)}]")
        written, skipped = _run_batch(
            batch=batch, note_cls=note_cls, overwrite=overwrite
        )
        total_written += written
        total_skipped += skipped
        print()

    print(f"Total — {total_written} written, {total_skipped} skipped.")


# CLI
# =======================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch-create variable registry notes from a seed JSON file."
    )
    parser.add_argument(
        "--variables",
        required=True,
        metavar="SEED_JSON",
        help="Path to the seed JSON file.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing note files.",
    )
    args = parser.parse_args()

    _seed_path = Path(args.variables)
    if not _seed_path.exists():
        print(f"Seed file not found: {_seed_path}")
        sys.exit(1)

    ingest_variables(seed_path=_seed_path, overwrite=args.overwrite)
