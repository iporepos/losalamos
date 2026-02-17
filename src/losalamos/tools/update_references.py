# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short module description (1-3 sentences)}
todo docstring

"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import argparse
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
from tqdm import tqdm

# ... {develop}

# Project-level imports
# =======================================================================
from losalamos.notes import NoteReference
from losalamos.tools.core import *

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# FUNCTIONS
# ***********************************************************************


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--folder", help="folder reference update.")
    # keep adding if more templates arise
    args = parser.parse_args()

    return args


def _collect_reference_notes(folder: Path) -> list[Path]:
    """
    Scan a folder for markdown notes and return only those
    whose metadata declares note_type == 'reference'.
    """
    ls_notes = list(folder.glob("*.md"))

    if not ls_notes:
        return []

    ls_references: list[Path] = []

    for file_note in tqdm(ls_notes, desc=" >>> ", unit="note"):
        dc = NoteReference.parse_metadata(file_note)
        if dc.get("note_type") == "reference":
            ls_references.append(file_note)

    return ls_references


def _update_references(ls_references: list[Path]) -> None:
    """
    Update all reference notes.
    """
    nr = NoteReference()  # reuse single instance if stateless

    for file_note in tqdm(ls_references, desc=" >>> ", unit="note"):
        nr.update_note(file_note=file_note)


def main() -> None:
    heading_section("UPDATE REFERENCES")

    args = get_arguments()
    dst_references = Path(args.folder)

    heading_subsection("Folder")
    print(get_message(f"Target folder: {dst_references}"))

    if not dst_references.exists():
        print(get_warning("Target folder does not exist."))
        return

    heading_subsection("Collecting references")
    ls_references = _collect_reference_notes(dst_references)

    if not ls_references:
        print(get_warning("No reference notes found."))
        return

    print(get_message(f"Found {len(ls_references)} reference notes."))

    heading_subsection("Updating references")
    _update_references(ls_references)
    print(get_message(f"Updated {len(ls_references)} reference notes."))

    heading_done()


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    main()
    # ... {develop}
