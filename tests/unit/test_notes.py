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
from tests.conftest import OUTPUT_DIR, RUN_BENCHMARKS

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
        if RUN_BENCHMARKS:
            cls._tmp_root = OUTPUT_DIR / "notes"
            cls._tmp_root.mkdir(parents=True, exist_ok=True)
        else:
            cls._tmp_root = Path(tempfile.mkdtemp(prefix="losalamos_test_notes_"))
        cls.ls_fields = ["note_name", "note_type", "timestamp", "note_file"]

    @classmethod
    def tearDownClass(cls):
        if not RUN_BENCHMARKS:
            shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def setUp(self):
        self.base_dir = Path(self._tmp_root)
        self.nc = NoteCollection(name="Testing", alias="tst")

    # -------------------------------------------------------------------
    # helpers
    # -------------------------------------------------------------------

    def _assert_collection_loaded(self):
        """Shared assertions for a loaded NoteCollection"""

        pprint.pp(self.nc.collection)

        # check collection
        self.assertGreater(len(self.nc.collection), 0)

        for obj in self.nc.collection.values():
            self.assertIsInstance(obj, self.nc.baseobject)

        # check catalog
        self.assertIsInstance(self.nc.catalog, pd.DataFrame)

        self.assertTrue(set(self.ls_fields).issubset(self.nc.catalog.columns))

        print(self.nc.catalog[self.ls_fields].to_string())

    # -------------------------------------------------------------------
    # loads
    # -------------------------------------------------------------------

    def test_init(self):
        """Ensure NoteCollection initializes with correct metadata."""
        print(self.nc)
        assert self.nc.name == "Testing"
        assert self.nc.alias == "tst"

    def test_collection(self):
        """Validate collection and catalog after loading a folder."""
        self.nc.load_folder(folder=DATA_DIR)
        self._assert_collection_loaded()

    def test_load_list(self):
        """Load notes from an explicit file list."""
        ls = glob.glob(str(DATA_DIR / "*.md"))
        self.assertGreater(len(ls), 0)

        self.nc.load_list(files=ls)
        self._assert_collection_loaded()

    def test_load_folder(self):
        """Load notes from a directory."""
        self.nc.load_folder(folder=DATA_DIR)
        self._assert_collection_loaded()


# ***********************************************************************
# SCRIPT
# ***********************************************************************

if __name__ == "__main__":
    unittest.main()
