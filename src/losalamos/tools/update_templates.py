# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Synchronise note templates to a target project folder.

Copies all ``_*.md`` template files from the project-level templates
source into the specified destination directory.

**Shell usage**

.. code-block:: bash

    python -m losalamos.tools.update_templates --notes /path/to/notes

    # Using short flag
    python -m losalamos.tools.update_templates -n /path/to/notes

"""
# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import argparse
import glob
import os
import shutil
from pathlib import Path

# Project-level imports
# =======================================================================
from losalamos.paths import FOLDER_TEMPLATES_NOTES
from losalamos.tools.core import *


# FUNCTIONS
# ***********************************************************************


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--notes", help="Destination folder for note templates.")
    args = parser.parse_args()
    return args


def main():
    """
    Copy note templates from the project source into the target folder.

    Templates are identified by the ``_*.md`` glob pattern. Missing
    templates produce a warning; no error is raised.
    """
    heading_section("UPDATE TEMPLATES")

    args = get_arguments()

    # NOTES
    # -------------------------------------------------------------------
    heading_subsection("[Notes]")

    dst_notes = Path(args.notes)
    print(get_message(f"Source folder: {FOLDER_TEMPLATES_NOTES}"))
    print(get_message(f"Target folder: {dst_notes}"))

    st_pattern = f"{FOLDER_TEMPLATES_NOTES}\\_*.md"
    ls_notes = glob.glob(st_pattern)

    if not ls_notes:
        print(get_warning("No note templates found."))
    else:
        print(get_message(f"Found {len(ls_notes)} template(s):\n"))

        for f in ls_notes:
            file_current = Path(f)
            name = file_current.name
            file_new = dst_notes / name

            shutil.copy(src=file_current, dst=file_new)
            print(f"    - {name}")

    # FIGURES (future)
    # -------------------------------------------------------------------
    # heading_subsection("[Figures]")
    # ...

    # DOCUMENTS (future)
    # -------------------------------------------------------------------
    # heading_subsection("[Documents]")
    # ...

    heading_done()


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":
    main()
