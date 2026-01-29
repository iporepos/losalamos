# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for losalamos Project creation and loading utilities.

Features
--------
 - Test project creation via `new_project`
 - Test loading existing projects via `load_project`
 - Validate Project internal data initialization
 - Validate filesystem side effects

Overview
--------
This test suite validates the behavioral contract of the Project API,
ensuring correct error handling, filesystem setup, and internal data
structures.

Examples
--------
From the terminal, run:

.. code-block:: bash

    python ./tests/unit/test_project.py


"""

# ***********************************************************************
# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import os
import shutil
import tempfile
import unittest
from pathlib import Path

# External imports
# =======================================================================
import pandas as pd

# Project-level imports
# =======================================================================
from losalamos.project import (
    new_project,
    load_project,
    Project,
    SUBFOLDERS,
)

# ***********************************************************************
# CLASSES
# ***********************************************************************

class TestProject(unittest.TestCase):
    """
    Tests for Project creation, loading, and initialization.
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests.
        """
        cls._tmp_root = tempfile.mkdtemp(prefix="losalamos_test_")

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests.
        """
        shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def setUp(self):
        """
        Runs before each test.
        """
        self.base_dir = Path(self._tmp_root)

    # -------------------------------------------------------------------
    # new_project
    # -------------------------------------------------------------------

    def test_new_project_missing_required_key(self):
        """
        new_project should fail if required keys are missing.
        """
        with self.assertRaises(ValueError):
            new_project(specs={"name": "TestProject"})

        with self.assertRaises(ValueError):
            new_project(specs={"folder_base": str(self.base_dir)})

    def test_new_project_success(self):
        """
        new_project should create a project and initialize folders.
        """
        specs = {
            "folder_base": str(self.base_dir),
            "name": "MyProject",
            "alias": "MP",
            "source": "unit-test",
            "description": "test project",
        }

        p = new_project(specs)

        # type & attributes
        self.assertIsInstance(p, Project)
        self.assertEqual(p.name, "MyProject")
        self.assertEqual(p.alias, "MP")
        self.assertEqual(p.source, "unit-test")
        self.assertEqual(p.description, "test project")

        # filesystem
        project_root = self.base_dir / "MyProject"
        self.assertTrue(project_root.is_dir())

    def test_new_project_existing_folder_raises(self):
        """
        new_project should raise if project folder already exists.
        """
        project_root = self.base_dir / "ExistingProject"
        project_root.mkdir(parents=True)

        specs = {
            "folder_base": str(self.base_dir),
            "name": "ExistingProject",
        }

        with self.assertRaises(ValueError):
            new_project(specs)

    # -------------------------------------------------------------------
    # load_project
    # -------------------------------------------------------------------

    def test_load_project_success(self):
        """
        load_project should load an existing project folder.
        """
        # create project first
        specs = {
            "folder_base": str(self.base_dir),
            "name": "LoadableProject",
        }
        new_project(specs)

        project_root = self.base_dir / "LoadableProject"

        p = load_project(project_root)

        self.assertIsInstance(p, Project)
        self.assertEqual(p.name, "LoadableProject")
        self.assertEqual(Path(p.folder_base), self.base_dir)

    def test_load_project_missing_folder(self):
        """
        load_project should fail if folder does not exist.
        """
        missing = self.base_dir / "DoesNotExist"

        with self.assertRaises(ValueError):
            load_project(missing)

    # -------------------------------------------------------------------
    # Project internals
    # -------------------------------------------------------------------

    def test_project_load_data_structure(self):
        """
        Project.load_data should initialize a proper dataframe.
        """
        p = Project(name="X", alias="Y")

        self.assertTrue(hasattr(p, "data"))
        self.assertIsInstance(p.data, pd.DataFrame)

        # expected columns
        self.assertIn("folder", p.data.columns)
        self.assertIn("file", p.data.columns)
        self.assertIn("file_template", p.data.columns)

        # consistency with SUBFOLDERS
        self.assertEqual(
            len(p.data),
            len(SUBFOLDERS["folder"]),
        )

        self.assertListEqual(
            list(p.data["folder"]),
            SUBFOLDERS["folder"],
        )


# ***********************************************************************
# SCRIPT
# ***********************************************************************

if __name__ == "__main__":
    unittest.main()