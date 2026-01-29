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
from importlib.resources import files

# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# DATA
# -----------------------------------------------------------------------
FOLDER_DATA = files("losalamos") / "data"


# TEMPLATES
# -----------------------------------------------------------------------
FOLDER_TEMPLATES = FOLDER_DATA / "templates"
FOLDER_TEMPLATES_NOTES = FOLDER_TEMPLATES / "notes"


if __name__ == "__main__":

    print("Hello World!")
