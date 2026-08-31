# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for losalamos Project creation and loading utilities.

Features
--------
 - Test project creation via ``new_project`` (dict and file-based config)
 - Test loading existing projects via ``load_project``
 - Validate main note creation and metadata defaults
 - Validate sources config file installation
 - Validate Project internal data initialization and filesystem side effects

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
from losalamos.notes import NoteProject, NoteOrganization, NoteSapiens, NoteBasic

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
            new_project(config={"name": "TestProject"})

        with self.assertRaises(ValueError):
            new_project(config={"folder_base": str(self.base_dir)})

    def test_new_project_success(self):
        """
        new_project should create a project and initialize folders.
        """
        config = {
            "folder_base": str(self.base_dir),
            "name": "MyProject",
            "alias": "MP",
            "source": "unit-test",
            "description": "test project",
        }

        p = new_project(config)

        # type & attributes
        self.assertIsInstance(p, Project)
        self.assertEqual(p.name, "MyProject")
        self.assertEqual(p.alias, "MP")
        self.assertEqual(p.source, "unit-test")
        self.assertEqual(p.description, "test project")

        # filesystem
        project_root = self.base_dir / "MyProject"
        self.assertTrue(project_root.is_dir())

    def test_new_project_creates_main_note(self):
        """
        new_project should create the main Markdown note file.
        """
        config = {
            "folder_base": str(self.base_dir),
            "name": "NoteProject",
        }
        p = new_project(config)

        note_path = Path(p.folder_root) / "NoteProject.md"
        self.assertTrue(note_path.is_file())
        self.assertIsNotNone(p.main_note)

    def test_new_project_note_metadata_defaults(self):
        """
        new_project should set default status and aliases in the main note.
        """
        config = {
            "folder_base": str(self.base_dir),
            "name": "DefaultsProject",
        }
        p = new_project(config)

        status = p.get_attribute(entry_key="status", clean_cref=False)
        self.assertEqual(status, "on going")

        aliases = p.main_note.metadata.get("aliases")
        self.assertIsInstance(aliases, list)
        self.assertTrue(any("DefaultsProject" in str(a) for a in aliases))

    def test_new_project_note_metadata_from_config(self):
        """
        new_project should write note metadata fields supplied in config.
        """
        config = {
            "folder_base": str(self.base_dir),
            "name": "MetaProject",
            "title": "My Survey",
            "status": "planning",
        }
        p = new_project(config)

        title = p.get_attribute(entry_key="title", clean_cref=False)
        self.assertIn("My Survey", title)

        status = p.get_attribute(entry_key="status", clean_cref=False)
        self.assertEqual(status, "planning")

    def test_new_project_with_sources_file(self):
        """
        new_project should copy a sources file into admin/config/ when
        the 'sources' key is provided.
        """
        # write a minimal sources.yaml to a temp location
        import yaml

        sources_content = {"organizations": [], "sapiens": [], "services": []}
        src_file = Path(self._tmp_root) / "sources_fixture.yaml"
        src_file.write_text(yaml.dump(sources_content), encoding="utf-8")

        config = {
            "folder_base": str(self.base_dir),
            "name": "SourcesProject",
            "sources": str(src_file),
        }
        p = new_project(config)

        dst = Path(p.folder_root) / "admin/config" / f"sources{src_file.suffix}"
        self.assertTrue(dst.is_file())

    def test_new_project_from_yaml_file(self):
        """
        new_project should accept a YAML file path as config.
        """
        import yaml

        cfg = {
            "folder_base": str(self.base_dir),
            "name": "YamlProject",
            "title": "From YAML",
        }
        cfg_file = Path(self._tmp_root) / "project_config.yaml"
        cfg_file.write_text(yaml.dump(cfg), encoding="utf-8")

        p = new_project(config=str(cfg_file))

        self.assertIsInstance(p, Project)
        self.assertEqual(p.name, "YamlProject")
        title = p.get_attribute(entry_key="title", clean_cref=False)
        self.assertIn("From YAML", title)

    def test_new_project_existing_folder_raises(self):
        """
        new_project should raise if project folder already exists.
        """
        project_root = self.base_dir / "ExistingProject"
        project_root.mkdir(parents=True)

        with self.assertRaises(ValueError):
            new_project(
                config={
                    "folder_base": str(self.base_dir),
                    "name": "ExistingProject",
                }
            )

    # -------------------------------------------------------------------
    # load_project
    # -------------------------------------------------------------------

    def test_load_project_success(self):
        """
        load_project should load an existing project folder.
        """
        new_project(
            config={
                "folder_base": str(self.base_dir),
                "name": "LoadableProject",
            }
        )

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


class TestProjectContractor(unittest.TestCase):
    """
    Tests for Project.get_attribute (quote stripping), _collect_md_files,
    load_contractor, and load_contractor_sapiens.
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="losalamos_test_contractor_"))

        cls.org_dir = cls._tmp / "organizations"
        cls.sapiens_dir = cls._tmp / "individuals"
        cls.org_dir.mkdir()
        cls.sapiens_dir.mkdir()

        # organization note fixture
        (cls.org_dir / "AMA Consultoria.md").write_text(
            "---\nnote_type: organization\nname: AMA Consultoria\n---\n# AMA Consultoria\n",
            encoding="utf-8",
        )

        # sapiens note fixture
        (cls.sapiens_dir / "John Doe.md").write_text(
            "---\nnote_type: sapiens\nname: John Doe\n---\n# John Doe\n",
            encoding="utf-8",
        )

        # project note: plain contractor value
        cls._note_plain = cls._tmp / "project_plain.md"
        cls._note_plain.write_text(
            "---\nnote_type: project\nname: TestProject\ncontractor: AMA Consultoria\n---\n# TestProject\n",
            encoding="utf-8",
        )

        # project note: contractor wrapped in double quotes (YAML artifact)
        cls._note_quoted = cls._tmp / "project_quoted.md"
        cls._note_quoted.write_text(
            '---\nnote_type: project\nname: TestProject\ncontractor: "AMA Consultoria"\n---\n# TestProject\n',
            encoding="utf-8",
        )

        # project note: contractor is a sapiens (not an org)
        cls._note_sapiens_contractor = cls._tmp / "project_sapiens_ctr.md"
        cls._note_sapiens_contractor.write_text(
            "---\nnote_type: project\nname: TestProject\ncontractor: John Doe\n---\n# TestProject\n",
            encoding="utf-8",
        )

        # project note: both contractor (org) and contractor_sapiens fields
        cls._note_with_sapiens = cls._tmp / "project_with_sapiens.md"
        cls._note_with_sapiens.write_text(
            "---\nnote_type: project\nname: TestProject\ncontractor: AMA Consultoria\ncontractor_sapiens: John Doe\n---\n# TestProject\n",
            encoding="utf-8",
        )

        # project note: contractor not present in any source
        cls._note_unknown = cls._tmp / "project_unknown.md"
        cls._note_unknown.write_text(
            "---\nnote_type: project\nname: TestProject\ncontractor: Unknown Corp\n---\n# TestProject\n",
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _make_project(self, note_path, org_sources=None, sapiens_sources=None):
        """Instantiate a Project with a preloaded main note and configured sources."""
        p = Project(name="TestProject", alias="TP")
        p.main_note = NoteProject(name="TestProject", alias="TP")
        p.main_note.load(file_note=note_path)
        if org_sources is not None:
            p.sources["organizations"] = org_sources
        if sapiens_sources is not None:
            p.sources["sapiens"] = sapiens_sources
        return p

    # -------------------------------------------------------------------
    # _collect_md_files
    # -------------------------------------------------------------------

    def test_collect_md_files_returns_stem_map(self):
        """
        _collect_md_files should return a dict mapping file stems to paths.
        """
        p = Project()
        result = p._collect_md_files(sources=[self.org_dir])
        self.assertIn("AMA Consultoria", result)
        self.assertIsInstance(result["AMA Consultoria"], Path)

    def test_collect_md_files_none_returns_empty(self):
        """
        _collect_md_files should return an empty dict when sources is None.
        """
        p = Project()
        result = p._collect_md_files(sources=None)
        self.assertEqual(result, {})

    # -------------------------------------------------------------------
    # get_attribute — quote stripping
    # -------------------------------------------------------------------

    def test_get_attribute_strips_surrounding_quotes(self):
        """
        get_attribute should strip YAML-artifact double quotes from values.
        """
        p = self._make_project(self._note_quoted)
        value = p.get_attribute(entry_key="contractor", clean_cref=False)
        self.assertEqual(value, "AMA Consultoria")

    def test_get_attribute_plain_value_unchanged(self):
        """
        get_attribute should leave values that have no surrounding quotes intact.
        """
        p = self._make_project(self._note_plain)
        value = p.get_attribute(entry_key="contractor", clean_cref=False)
        self.assertEqual(value, "AMA Consultoria")

    # -------------------------------------------------------------------
    # load_contractor
    # -------------------------------------------------------------------

    def test_load_contractor_from_organizations(self):
        """
        load_contractor should set self.contractor to a NoteOrganization when
        the contractor name matches a file in sources["organizations"].
        """
        p = self._make_project(self._note_plain, org_sources=[self.org_dir])
        p.load_contractor()
        self.assertIsInstance(p.contractor, NoteOrganization)
        self.assertIsNotNone(p.contractor_path)

    def test_load_contractor_quoted_name_resolves(self):
        """
        A contractor name wrapped in YAML quotes must still match the note file.
        """
        p = self._make_project(self._note_quoted, org_sources=[self.org_dir])
        p.load_contractor()
        self.assertIsInstance(p.contractor, NoteOrganization)

    def test_load_contractor_falls_back_to_sapiens(self):
        """
        load_contractor should set self.contractor to a NoteSapiens when the
        contractor name is not found in org sources but is found in sapiens sources.
        """
        p = self._make_project(
            self._note_sapiens_contractor,
            sapiens_sources=[self.sapiens_dir],
        )
        p.load_contractor()
        self.assertIsInstance(p.contractor, NoteSapiens)

    def test_load_contractor_not_found_raises(self):
        """
        load_contractor should raise FileNotFoundError when the contractor
        name is not present in any source.
        """
        p = self._make_project(
            self._note_unknown,
            org_sources=[self.org_dir],
            sapiens_sources=[self.sapiens_dir],
        )
        with self.assertRaises(FileNotFoundError):
            p.load_contractor()

    def test_load_contractor_empty_sources_raises(self):
        """
        load_contractor should raise FileNotFoundError when self.sources is empty.
        """
        p = self._make_project(self._note_plain)
        with self.assertRaises(FileNotFoundError):
            p.load_contractor()

    # -------------------------------------------------------------------
    # load_contractor_sapiens
    # -------------------------------------------------------------------

    def test_load_contractor_sapiens_sets_attributes(self):
        """
        load_contractor_sapiens should set self.contractor_sapiens to a
        NoteSapiens and populate self.contractor_sapiens_path.
        """
        p = self._make_project(
            self._note_with_sapiens,
            org_sources=[self.org_dir],
            sapiens_sources=[self.sapiens_dir],
        )
        p.load_contractor_sapiens()
        self.assertIsInstance(p.contractor_sapiens, NoteSapiens)
        self.assertIsNotNone(p.contractor_sapiens_path)

    def test_load_contractor_sapiens_triggers_load_contractor(self):
        """
        load_contractor_sapiens should automatically load the contractor
        when self.contractor has not been set yet.
        """
        p = self._make_project(
            self._note_with_sapiens,
            org_sources=[self.org_dir],
            sapiens_sources=[self.sapiens_dir],
        )
        self.assertIsNone(p.contractor)
        p.load_contractor_sapiens()
        self.assertIsNotNone(p.contractor)

    def test_load_contractor_sapiens_not_found_raises(self):
        """
        load_contractor_sapiens should raise FileNotFoundError when the
        contractor_sapiens name is not found in sapiens sources.
        """
        p = self._make_project(
            self._note_with_sapiens,
            org_sources=[self.org_dir],
        )
        with self.assertRaises(FileNotFoundError):
            p.load_contractor_sapiens()


# ***********************************************************************
# SCRIPT
# ***********************************************************************

if __name__ == "__main__":
    unittest.main()
