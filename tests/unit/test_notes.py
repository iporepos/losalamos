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
from losalamos.notes import NoteCollection, NoteOrganization, NoteSapiens
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


class TestNoteOrganization(unittest.TestCase):
    """
    Tests for ``losalamos.notes.NoteOrganization``.
    """

    EXPECTED_FIELDS = {
        "note_type",
        "timestamp",
        "name",
        "acronym",
        "org_domain",
        "org_type",
        "email",
        "phone",
        "affiliation",
        "place",
        "address",
        "cnpj",
        "website",
        "abstract",
    }

    @classmethod
    def setUpClass(cls):
        if RUN_BENCHMARKS:
            cls._tmp_root = OUTPUT_DIR / "notes_organization"
            cls._tmp_root.mkdir(parents=True, exist_ok=True)
        else:
            cls._tmp_root = Path(tempfile.mkdtemp(prefix="losalamos_test_org_"))

    @classmethod
    def tearDownClass(cls):
        if not RUN_BENCHMARKS:
            shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def setUp(self):
        self.note = NoteOrganization()
        self.file = self._tmp_root / "TestOrg.md"

    def test_load_new(self):
        """load_new creates the file and populates metadata."""
        self.note.load_new(file_note=self.file)
        self.assertIsNotNone(self.note.metadata)
        self.assertIsNotNone(self.note.data)

    def test_note_type(self):
        """note_type field must be 'organization'."""
        self.note.load_new(file_note=self.file)
        self.assertEqual(self.note.metadata.get("note_type"), "organization")

    def test_metadata_fields(self):
        """All template fields must be present after load_new."""
        self.note.load_new(file_note=self.file)
        missing = self.EXPECTED_FIELDS - set(self.note.metadata.keys())
        self.assertSetEqual(missing, set(), msg=f"Missing fields: {missing}")

    def test_save_roundtrip(self):
        """Save then reload preserves note_type and name."""
        self.note.load_new(file_note=self.file)
        self.note.save()

        reloaded = NoteOrganization()
        reloaded.load(file_note=self.file)
        self.assertEqual(reloaded.metadata.get("note_type"), "organization")
        self.assertIn(self.file.stem, reloaded.metadata.get("name", ""))

    def test_abstract_pattern(self):
        """update() correctly writes abstract into the [!Info] block."""
        self.note.load_new(file_note=self.file)
        self.note.metadata["abstract"] = '"A test organization."'
        self.note.update()
        head_text = "\n".join(self.note.data[self.note.STR_HEAD])
        self.assertIn("A test organization.", head_text)


class TestNoteSapiens(unittest.TestCase):
    """
    Tests for ``losalamos.notes.NoteSapiens``.
    """

    EXPECTED_FIELDS = {
        "note_type",
        "timestamp",
        "name",
        "email",
        "email_pro",
        "phone",
        "place",
        "abstract",
        "edu_background",
        "degree",
        "profession",
        "affiliation_edu",
        "affiliation_pro",
        "address",
        "lattes",
        "orcid",
        "website",
        "cpf",
        "rg",
        "github",
        "linkedin",
    }

    @classmethod
    def setUpClass(cls):
        if RUN_BENCHMARKS:
            cls._tmp_root = OUTPUT_DIR / "notes_sapiens"
            cls._tmp_root.mkdir(parents=True, exist_ok=True)
        else:
            cls._tmp_root = Path(tempfile.mkdtemp(prefix="losalamos_test_sap_"))

    @classmethod
    def tearDownClass(cls):
        if not RUN_BENCHMARKS:
            shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def setUp(self):
        self.note = NoteSapiens()
        self.file = self._tmp_root / "TestPerson.md"

    def test_load_new(self):
        """load_new creates the file and populates metadata."""
        self.note.load_new(file_note=self.file)
        self.assertIsNotNone(self.note.metadata)
        self.assertIsNotNone(self.note.data)

    def test_note_type(self):
        """note_type field must be 'sapiens'."""
        self.note.load_new(file_note=self.file)
        self.assertEqual(self.note.metadata.get("note_type"), "sapiens")

    def test_metadata_fields(self):
        """All template fields must be present after load_new."""
        self.note.load_new(file_note=self.file)
        missing = self.EXPECTED_FIELDS - set(self.note.metadata.keys())
        self.assertSetEqual(missing, set(), msg=f"Missing fields: {missing}")

    def test_save_roundtrip(self):
        """Save then reload preserves note_type and name."""
        self.note.load_new(file_note=self.file)
        self.note.save()

        reloaded = NoteSapiens()
        reloaded.load(file_note=self.file)
        self.assertEqual(reloaded.metadata.get("note_type"), "sapiens")
        self.assertIn(self.file.stem, reloaded.metadata.get("name", ""))

    def test_abstract_pattern(self):
        """update() correctly writes abstract into the [!Info] block."""
        self.note.load_new(file_note=self.file)
        self.note.metadata["abstract"] = '"A test person."'
        self.note.update()
        head_text = "\n".join(self.note.data[self.note.STR_HEAD])
        self.assertIn("A test person.", head_text)


# ***********************************************************************
# SCRIPT
# ***********************************************************************

if __name__ == "__main__":
    unittest.main()
