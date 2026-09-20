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
from losalamos.notes import (
    NoteBasic,
    NoteCollection,
    NoteOrganization,
    NoteSapiens,
    NoteTransfer,
)
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
class TestNoteTransfer(unittest.TestCase):
    """
    Tests for ``losalamos.notes.NoteTransfer``.
    """

    EXPECTED_FIELDS = {
        "note_type",
        "timestamp",
        "name",
        "abstract",
        "date",
        "transfer_type",
        "status",
        "account",
        "value",
        "commitment",
        "recurrence",
        "method",
        "protocol",
        "related_asset",
    }

    @classmethod
    def setUpClass(cls):
        if RUN_BENCHMARKS:
            cls._tmp_root = OUTPUT_DIR / "notes_transfer"
            cls._tmp_root.mkdir(parents=True, exist_ok=True)
        else:
            cls._tmp_root = Path(tempfile.mkdtemp(prefix="losalamos_test_transfer_"))

    @classmethod
    def tearDownClass(cls):
        if not RUN_BENCHMARKS:
            shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def setUp(self):
        self.note = NoteTransfer()
        self.file = self._tmp_root / "TestTransfer.md"

    def test_load_new(self):
        """load_new creates the file and populates metadata."""
        self.note.load_new(file_note=self.file)
        self.assertIsNotNone(self.note.metadata)
        self.assertIsNotNone(self.note.data)

    def test_note_type(self):
        """note_type field must be 'transfer'."""
        self.note.load_new(file_note=self.file)
        self.assertEqual(self.note.metadata.get("note_type"), "transfer")

    def test_metadata_fields(self):
        """All template fields must be present after load_new."""
        self.note.load_new(file_note=self.file)
        missing = self.EXPECTED_FIELDS - set(self.note.metadata.keys())
        self.assertSetEqual(missing, set(), msg=f"Missing fields: {missing}")

    def test_save_roundtrip(self):
        """Save then reload preserves note_type and name."""
        self.note.load_new(file_note=self.file)
        self.note.save()

        reloaded = NoteTransfer()
        reloaded.load(file_note=self.file)
        self.assertEqual(reloaded.metadata.get("note_type"), "transfer")
        self.assertIn(self.file.stem, reloaded.metadata.get("name", ""))


class TestNoteBasicExtraFields(unittest.TestCase):
    """
    Tests that NoteBasic preserves non-standard YAML fields across load and save.

    Obsidian plugins can inject arbitrary frontmatter keys that are not part of
    any template. These must survive a load/save roundtrip without being dropped.
    """

    _NOTE_CONTENT = (
        "---\n"
        "note_type: basic\n"
        "name: ExtraFieldNote\n"
        "abstract: \n"
        "obsidian_plugin_x: some value\n"
        "zebra_field: last alphabetically\n"
        "alpha_extra: first alphabetically\n"
        "---\n"
        "# ExtraFieldNote\n"
    )

    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="losalamos_test_extrafields_"))
        cls._file = cls._tmp / "ExtraFieldNote.md"
        cls._file.write_text(cls._NOTE_CONTENT, encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _load(self, path=None):
        note = NoteBasic()
        note.load(file_note=path or self._file)
        return note

    def test_extra_fields_preserved_after_load(self):
        """Non-standard fields must all be present in metadata after load."""
        note = self._load()
        for field in ("obsidian_plugin_x", "zebra_field", "alpha_extra"):
            self.assertIn(field, note.metadata, msg=f"'{field}' was dropped")

    def test_standard_fields_precede_extra_fields(self):
        """Every standard template field must appear before any extra field."""
        note = self._load()
        keys = list(note.metadata.keys())
        extra = {"obsidian_plugin_x", "zebra_field", "alpha_extra"}
        last_std = max(
            (keys.index(k) for k in note.metadata_standard if k in keys),
            default=-1,
        )
        first_extra = min(keys.index(k) for k in extra)
        self.assertLess(last_std, first_extra)

    def test_extra_fields_sorted_alphabetically(self):
        """Extra fields must appear in alphabetical order after the standard block."""
        note = self._load()
        keys = list(note.metadata.keys())
        extras = [k for k in keys if k not in note.metadata_standard]
        self.assertEqual(extras, sorted(extras))

    def test_extra_fields_survive_save_roundtrip(self):
        """Extra fields must still be present after save() and a fresh load()."""
        copy_path = self._tmp / "RoundtripNote.md"
        copy_path.write_text(self._NOTE_CONTENT, encoding="utf-8")

        note = NoteBasic()
        note.load(file_note=copy_path)
        note.save()

        reloaded = self._load(path=copy_path)
        for field in ("obsidian_plugin_x", "zebra_field", "alpha_extra"):
            self.assertIn(
                field, reloaded.metadata, msg=f"'{field}' lost after roundtrip"
            )


# SCRIPT
# ***********************************************************************

if __name__ == "__main__":
    unittest.main()
