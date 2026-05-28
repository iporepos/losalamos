# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Create a new SVG figure from a named drawing template.

Copies a template file from the project drawings library into a target
folder under the specified filename.

**Shell usage**

.. code-block:: bash

    python -m losalamos.tools.new_figure \\
        --tem story \\
        --nam my_figure \\
        --dst /path/to/output

.. code-block:: powershell

    python -m losalamos.tools.new_figure `
        --tem story `
        --nam my_figure `
        --dst "C:\\path\\to\\output"

.. note::

    The template is resolved as ``_{template_name}.svg`` inside the
    project drawings library (``FOLDER_TEMPLATES_DRAWINGS``).
    The destination folder is created if it does not exist.

"""

# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import argparse
import shutil
from pathlib import Path

# External imports
# =======================================================================

# Project-level imports
# =======================================================================
from losalamos.paths import FOLDER_TEMPLATES_DRAWINGS
from losalamos.tools.core import *


# FUNCTIONS
# ***********************************************************************


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tem", help="Template name")
    parser.add_argument("-n", "--nam", help="File name.")
    parser.add_argument("-d", "--dst", help="Destination folder for outputs.")
    args = parser.parse_args()
    return args


def main() -> None:
    heading_section("NEW FIGURE")

    args = get_arguments()
    template_name = args.tem
    file_name = args.nam
    dst_folder = Path(args.dst)

    # make folder
    dst_folder.mkdir(exist_ok=True, parents=True)

    template_file = FOLDER_TEMPLATES_DRAWINGS / f"_{template_name}.svg"

    heading_subsection("Template")
    print(get_message(f"File: {template_file}"))

    heading_subsection("Folder")
    print(get_message(f"Target folder: {dst_folder}"))

    fo = dst_folder / f"{file_name}.svg"

    shutil.copy(template_file, fo)

    heading_subsection("Outputs")
    print(fo.name)
    heading_done()


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":
    main()
