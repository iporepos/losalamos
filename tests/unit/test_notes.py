# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for ``losalamos`` notes creation and loading utilities.

# todo docstring

"""

# ***********************************************************************
# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import glob, pprint
import shutil
import tempfile
import unittest
from pathlib import Path

# External imports
# =======================================================================
import pandas as pd

# Project-level imports
# =======================================================================
from losalamos.notes import NoteCollection
from tests.conftest import DATA_DIR

# ***********************************************************************
# CLASSES
# ***********************************************************************


class TestNoteCollection(unittest.TestCase):
    """
    Tests for handling ``losalamos.notes.NoteCollection``
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests.
        """
        cls._tmp_root = tempfile.mkdtemp(prefix="losalamos_test_notes_")

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

    def test_init(self):

        nc = NoteCollection(name="Testing", alias="tst")

        print(nc)

        assert nc.name == "Testing"
        assert nc.alias == "tst"

    def test_load_list(self):

        ls = glob.glob(str(DATA_DIR / "*.md"))
        print("loading files:")
        pprint.pp(ls)

        nc = NoteCollection(name="Testing", alias="tst")

        nc.load_list(files_list=ls)

        # check collection
        assert len(nc.collection.keys()) > 0
        for k in nc.collection:
            self.assertIsInstance(nc.collection[k], nc.baseobject)
        pprint.pp(nc.collection)

        # check catalog
        self.assertIsInstance(nc.catalog, pd.DataFrame)
        print("\n")
        ls_fields = ["note_name", "note_type", "timestamp", "note_file"]
        print(nc.catalog[ls_fields].to_string())


# ***********************************************************************
# SCRIPT
# ***********************************************************************

if __name__ == "__main__":
    unittest.main()
