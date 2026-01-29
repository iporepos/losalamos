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
import glob
import shutil
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
# import {module}
# ... {develop}

# Project-level imports
# =======================================================================
from losalamos.paths import FOLDER_TEMPLATES_NOTES

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# FUNCTIONS
# ***********************************************************************


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--notes", help="folder for notes templates.")
    # keep addig if more templates arise
    args = parser.parse_args()

    return args


def main():

    print("\nLos Alamos Templates Installer")
    print(80 * "=")
    print("\n")

    args = get_arguments()

    # NOTES
    # -------------------------------------------------------------------
    print("[Notes]")
    print(80 * "-")

    dst_notes = Path(args.notes)
    print(f"  Source folder: {FOLDER_TEMPLATES_NOTES}")
    print(f"  Target folder: {dst_notes}")

    st_pattern = f"{FOLDER_TEMPLATES_NOTES}\_*.md"
    ls_notes = glob.glob(st_pattern)

    if not ls_notes:
        print("  No note templates found.")
    else:
        print(f"  Found {len(ls_notes)} template(s):")

        for f in ls_notes:
            file_current = Path(f)
            name = file_current.name
            file_new = dst_notes / name

            shutil.copy(src=file_current, dst=file_new)
            print(f"    - {name}")

    print()  # spacing between template groups

    # FIGURES (future)
    # -------------------------------------------------------------------
    # print("[Figures]")
    # ...

    # DOCUMENTS (future)
    # -------------------------------------------------------------------
    # print("[Documents]")
    # ...

    print("Templates update completed.\n")


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    main()
    # ... {develop}
