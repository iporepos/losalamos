# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Ingest reference files from a source directory into a target dataset structure.

This CLI wraps the project Ingester, providing a minimal interface for
batch ingestion with basic validation and progress feedback.

Usage
-----

Module execution (recommended):

Shell (bash/zsh):
```sh
python -m losalamos.tools.ingest_references \
    --src /path/to/source \
    --dst /path/to/destination
```

PowerShell (ps1):
```powershell
$SRC="C:\path\to\source"
$DST="C:\path\to\destination"

python -m losalamos.tools.ingest_references --src $SRC --dst $DST
```
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
from losalamos.ingestion import Ingester
from losalamos.tools.core import *

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# FUNCTIONS
# ***********************************************************************


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--src", help="source of incoming folder.")
    parser.add_argument("-d", "--dst", help="destination folder.")
    # keep adding if more templates arise
    args = parser.parse_args()

    return args


def main() -> None:
    heading_section("INGEST REFERENCES")

    args = get_arguments()
    src_folder = Path(args.src)
    dst_folder = Path(args.dst)

    heading_subsection("Folders")
    print(get_message(f"Source folder: {src_folder}"))
    print(get_message(f"Target folder: {dst_folder}"))

    if not dst_folder.exists():
        print(get_warning("Target folder does not exist."))
        return

    heading_subsection("Ingesting references")

    ingester = Ingester(src=src_folder, dst=dst_folder)
    ingester.run(cleanup=True)

    heading_done()


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    main()
    # ... {develop}
