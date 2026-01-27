# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short module description (1-3 sentences)}
todo docstring

Features
--------
todo docstring

* {feature 1}
* {feature 2}
* {feature 3}
* {etc}

Overview
--------
todo docstring
{Overview description}

Examples
--------
todo docstring
{Examples in rST}

Print a message

.. code-block:: python

    # print message
    print("Hello world!")
    # [Output] >> 'Hello world!'


"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import os
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from losalamos.root import FileSys

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# Subsubsection example
# -----------------------------------------------------------------------

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}
SUBFOLDERS = {
    "folder": [
        "admin/contracts",
        "admin/contracts/main",
        "admin/proposals",
        "admin/docs",
        "admin/paperwork",
        "admin/meetings",
        "admin/received",
        "admin/comms",
        "budget/inflows",
        "budget/outflows",
        "inputs/data",
        "inputs/scripts",
        "inputs/docs",
        "inputs/received",
        "inputs/visuals",
        "inputs/visuals/raw",
        "outputs/public",
        "outputs/history",
        "outputs/latest",
    ],
}

# FUNCTIONS
# ***********************************************************************


# FUNCTIONS -- Project-level
# =======================================================================
def new_project(specs):
    """
    Create a new Project from a specification dictionary.

    .. danger::

        This method overwrites all existing default files.

    :param specs: Dictionary containing project specifications.

        **Required keys**:

        - ``folder_base`` (*str*): Path where the project folder will be created.
        - ``name`` (*str*): Name of the project.

        **Optional keys**:

        - ``alias`` (*str*): Alternative identifier. Defaults to ``None``.
        - ``source`` (*str*): Source reference. Defaults to empty string.
        - ``description`` (*str*): Project description. Defaults to empty string.

    :type specs: dict
    :raises ValueError: If any required key is missing.
    :returns: A new `:class:`losalamos.Project` instance initialized with the given specifications.
    :rtype: :class:`losalamos.Project`


    .. dropdown:: Script example
        :icon: code-square
        :open:

        Import ``losalamos``

        .. code-block:: python

           import losalamos

        Create a new ``losalamos.Project``. First setup details.

        .. code-block:: python

            # [CHANGE THIS] setup specs dictionary
            project_specs = {
                "folder_base": "C:/to/losalamos", # change this path
                "name": "newProject",
                "alias": "NPrj",
                "source": "Me",
                "description": "Just a test"
            }

        Then call ``new_project()``

        .. code-block:: python

            losalamos.new_project(specs=project_specs)

        Create and get the project instance:

        .. code-block:: python

            prj = losalamos.new_project(specs=project_specs)



    """
    # --- Required keys ---
    required = ["folder_base", "name"]
    for key in required:
        if key not in specs:
            raise ValueError(f"Missing required key: '{key}'")

    # --- Optional keys with defaults ---
    defaults = {"alias": None, "source": "", "description": ""}
    merged = {**defaults, **specs}

    # --- Use merged dict safely ---
    # create base folder if not exists
    os.makedirs(merged["folder_base"], exist_ok=True)

    folder_root = Path(merged["folder_base"]) / merged["name"]
    if os.path.isdir(folder_root):
        raise ValueError(f"Project folder already exists '{folder_root}'")

    # instantiate project
    p = Project(name=merged["name"], alias=merged["alias"])
    p.source = merged["source"]
    p.description = merged["description"]
    p.folder_base = merged["folder_base"]
    p.update()
    p.setup()

    return p


def load_project(project_folder):
    """
    Loads a Project from folder

    :param project_folder: path to project root folder
    :type project_folder: str or Path
    :returns: A new `:class:`losalamos.Project` instance.
    :rtype: :class:`losalamos.Project`

    .. dropdown:: Script example
        :icon: code-square
        :open:

        Load an existing ``losalamos.Project``

        .. code-block:: python

            # import the package
            import losalamos

            # get project instance
            pj = losalamos.load_project(project_folder="path/to/project/folder")


    """
    if os.path.isdir(project_folder):
        name = os.path.basename(project_folder)
        folder_base = os.path.abspath(Path(project_folder).parent)
        p = Project(name=name, alias=None)
        p.name = name
        p.folder_base = folder_base

        # update project
        p.update()

        # setup
        p.setup()

        return p
    else:
        raise ValueError(f"Project folder not found: {project_folder}'")


# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


# CLASSES
# ***********************************************************************


# CLASSES -- Project-level
# =======================================================================
# ... {develop}
class Project(FileSys):
    # todo docstring

    def __init__(self, name="LosAlamosProject", alias="LAProj"):
        super().__init__(name=name, alias=alias)
        self.load_data()

    def load_data(self):
        # todo docstring
        df = pd.DataFrame(SUBFOLDERS)
        df["file"] = ""
        df["file_template"] = ""
        self.data = df.copy()
        return None


# CLASSES -- Module-level
# =======================================================================
# ... {develop}


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    print("Hello world!")
    # ... {develop}

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
