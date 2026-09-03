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

    def test_new_project_alias_written_to_note(self):
        """alias supplied in config must appear as a field in the project note."""
        p = new_project(
            config={
                "folder_base": str(self.base_dir),
                "name": "AliasProject",
                "alias": "APJ",
            }
        )
        alias_val = p.main_note.metadata.get("alias", "")
        self.assertIn("APJ", str(alias_val))

    def test_new_project_contractor_wiki_link(self):
        """contractor and client fields must be stored as Obsidian wiki-links."""
        p = new_project(
            config={
                "folder_base": str(self.base_dir),
                "name": "LinkProject",
                "contractor": "Acme Corp",
                "client": "Beta Ltd",
                "contractor_sapiens": "John Doe",
                "client_sapiens": "Jane Doe",
            }
        )
        for field, expected in [
            ("contractor", '"[[Acme Corp]]"'),
            ("client", '"[[Beta Ltd]]"'),
            ("contractor_sapiens", '"[[John Doe]]"'),
            ("client_sapiens", '"[[Jane Doe]]"'),
        ]:
            val = str(p.main_note.metadata.get(field, ""))
            self.assertIn(expected, val, f"{field} missing wiki-link")

    def test_new_project_no_budget_documents_folder(self):
        """budget/documents must not be auto-created by new_project."""
        p = new_project(
            config={
                "folder_base": str(self.base_dir),
                "name": "NoBudgetDocs",
            }
        )
        self.assertFalse((Path(p.folder_root) / "budget" / "documents").exists())

    def test_new_project_no_admin_documents_folder(self):
        """admin/documents must not be auto-created by new_project."""
        p = new_project(
            config={
                "folder_base": str(self.base_dir),
                "name": "NoAdminDocs",
            }
        )
        self.assertFalse((Path(p.folder_root) / "admin" / "documents").exists())

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
        search = p.sources.setdefault("folders", {}).setdefault("search", {})
        if org_sources is not None:
            search["organizations"] = org_sources
        if sapiens_sources is not None:
            search["sapiens"] = sapiens_sources
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


class TestRemoteFolders(unittest.TestCase):
    """Tests for Phase 3: remote folder resolution and creation."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="losalamos_remote_"))
        cls._remote_docs = cls._tmp / "remote_docs"
        cls._remote_data = cls._tmp / "remote_data"
        cls._remote_docs.mkdir()
        cls._remote_data.mkdir()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _make_project(self, name, branch=None):
        p = Project(name=name, alias=name)
        p.folder_base = str(self._tmp)
        p.branch = branch
        p.update()
        return p

    # --- _resolve_remote_folders ---

    def test_no_remote_falls_back_to_folder_root(self):
        """When sources has no documents/data keys, remote folders equal folder_root."""
        p = self._make_project("FlatProj")
        self.assertEqual(p.folder_remote_documents, p.folder_root)
        self.assertEqual(p.folder_remote_data, p.folder_root)

    def test_documents_remote_mirrors_flat_layout(self):
        """documents key in sources sets folder_remote_documents to remote/name."""
        p = self._make_project("FlatProj2")
        p.sources.setdefault("folders", {}).setdefault("remote", {})["documents"] = str(
            self._remote_docs
        )
        p._resolve_remote_folders()
        expected = self._remote_docs / "FlatProj2"
        self.assertEqual(p.folder_remote_documents, expected)

    def test_documents_remote_mirrors_branch_layout(self):
        """With a branch, remote mirrors vault/branch/name structure."""
        p = self._make_project("C001", branch="Consulting")
        p.sources.setdefault("folders", {}).setdefault("remote", {})["documents"] = str(
            self._remote_docs
        )
        p._resolve_remote_folders()
        expected = self._remote_docs / "Consulting" / "C001"
        self.assertEqual(p.folder_remote_documents, expected)

    def test_data_remote_resolved_independently(self):
        """data key resolves folder_remote_data separately from documents."""
        p = self._make_project("DataProj")
        p.sources.setdefault("folders", {}).setdefault("remote", {})["data"] = str(
            self._remote_data
        )
        p._resolve_remote_folders()
        expected = self._remote_data / "DataProj"
        self.assertEqual(p.folder_remote_data, expected)

    # --- _setup_remote_folders ---

    def test_setup_remote_creates_inputs_documents(self):
        """_setup_remote_folders creates inputs/documents under the remote docs root."""
        p = self._make_project("SetupProj")
        p.sources.setdefault("folders", {}).setdefault("remote", {})["documents"] = str(
            self._remote_docs
        )
        p._resolve_remote_folders()
        p._setup_remote_folders()
        self.assertTrue((p.folder_remote_documents / "inputs" / "documents").is_dir())

    def test_setup_remote_creates_inputs_data(self):
        """_setup_remote_folders creates inputs/data under the remote data root."""
        p = self._make_project("SetupProj2")
        p.sources.setdefault("folders", {}).setdefault("remote", {})["data"] = str(
            self._remote_data
        )
        p._resolve_remote_folders()
        p._setup_remote_folders()
        self.assertTrue((p.folder_remote_data / "inputs" / "data").is_dir())

    def test_setup_remote_no_op_when_no_remote(self):
        """_setup_remote_folders is a no-op when remote equals folder_root."""
        p = self._make_project("NoRemoteProj")
        # should not raise
        try:
            p._setup_remote_folders()
        except Exception as exc:
            self.fail(f"_setup_remote_folders raised unexpectedly: {exc}")

    # --- _locate_document_source remote fallback ---

    def test_locate_finds_source_in_remote_when_local_missing(self):
        """_locate_document_source falls back to remote when local is absent."""
        p = self._make_project("LocProj")
        p.folder_root = Path(self._tmp) / "LocProj"
        p.sources.setdefault("folders", {}).setdefault("remote", {})["documents"] = str(
            self._remote_docs
        )
        p._resolve_remote_folders()

        # plant the source in the remote location
        remote_src = (
            p.folder_remote_documents / "inputs" / "documents" / "INVOICE_LocProj_F001"
        )
        remote_src.mkdir(parents=True)

        result = p._locate_document_source(name="INVOICE_LocProj_F001")
        self.assertEqual(result, remote_src)

    def test_locate_raises_with_both_paths_when_neither_exists(self):
        """FileNotFoundError message includes both local and remote paths."""
        p = self._make_project("LocProj2")
        p.folder_root = Path(self._tmp) / "LocProj2"
        p.sources.setdefault("folders", {}).setdefault("remote", {})["documents"] = str(
            self._remote_docs
        )
        p._resolve_remote_folders()

        with self.assertRaises(FileNotFoundError) as ctx:
            p._locate_document_source(name="RECEIPT_LocProj2_F999")
        msg = str(ctx.exception)
        self.assertIn("RECEIPT_LocProj2_F999", msg)
        self.assertIn("inputs/documents", msg.replace("\\", "/"))


class TestProjectBranch(unittest.TestCase):
    """Tests for the branch tier in folder_root."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="losalamos_branch_"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_new_project_with_branch_creates_nested_folder(self):
        """new_project with branch should create folder_base/branch/name."""
        p = new_project(
            config={
                "folder_base": str(self._tmp),
                "name": "C001",
                "branch": "Consulting",
            }
        )
        expected = self._tmp / "Consulting" / "C001"
        self.assertTrue(expected.is_dir())
        self.assertEqual(Path(p.folder_root), expected)

    def test_new_project_without_branch_flat_layout_unchanged(self):
        """new_project without branch keeps the flat folder_base/name layout."""
        p = new_project(
            config={
                "folder_base": str(self._tmp),
                "name": "FlatProject",
            }
        )
        expected = self._tmp / "FlatProject"
        self.assertTrue(expected.is_dir())
        self.assertEqual(Path(p.folder_root), expected)

    def test_branch_attribute_set_on_project(self):
        """Project.branch should reflect the value passed in config."""
        p = new_project(
            config={
                "folder_base": str(self._tmp),
                "name": "C002",
                "branch": "Research",
            }
        )
        self.assertEqual(p.branch, "Research")

    def test_branch_none_by_default(self):
        """Project.branch should be None when not supplied."""
        p = Project(name="X", alias="x")
        self.assertIsNone(p.branch)

    def test_main_note_inside_folder_root(self):
        """main_note_path must sit directly inside folder_root regardless of branch."""
        p = new_project(
            config={
                "folder_base": str(self._tmp),
                "name": "C003",
                "branch": "Admin",
            }
        )
        self.assertEqual(p.main_note_path, p.folder_root / "C003.md")

    def test_load_project_branch_folder_works(self):
        """load_project should load a project that lives inside a branch sub-folder."""
        new_project(
            config={
                "folder_base": str(self._tmp),
                "name": "C004",
                "branch": "Consulting",
            }
        )
        project_root = self._tmp / "Consulting" / "C004"
        p = load_project(project_folder=project_root)
        self.assertIsInstance(p, Project)
        self.assertEqual(p.name, "C004")

    def test_load_project_with_vault_sets_branch(self):
        """load_project with vault should set branch so folder_root is vault/branch/name."""
        new_project(
            config={
                "folder_base": str(self._tmp),
                "name": "C007",
                "branch": "Consulting",
            }
        )
        project_root = self._tmp / "Consulting" / "C007"
        p = load_project(project_folder=project_root, vault=str(self._tmp))
        self.assertEqual(p.branch, "Consulting")
        self.assertEqual(Path(p.folder_base), self._tmp)
        self.assertEqual(Path(p.folder_root), project_root)

    def test_branch_not_written_to_note(self):
        """branch must not appear as a metadata field in the project note."""
        p = new_project(
            config={
                "folder_base": str(self._tmp),
                "name": "C005",
                "branch": "Consulting",
            }
        )
        self.assertNotIn("branch", p.main_note.metadata)

    def test_existing_branch_folder_raises(self):
        """new_project should raise if the project folder already exists inside the branch."""
        new_project(
            config={
                "folder_base": str(self._tmp),
                "name": "C006",
                "branch": "Consulting",
            }
        )
        with self.assertRaises(ValueError):
            new_project(
                config={
                    "folder_base": str(self._tmp),
                    "name": "C006",
                    "branch": "Consulting",
                }
            )


class TestAssetDocumentPaths(unittest.TestCase):
    """
    Tests for Phase 1 path layout: source at inputs/documents/{name}/,
    note at inputs/documents/{name}.md, old type-specific folder untouched.
    """

    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="losalamos_assetpaths_"))
        cls._project = new_project(
            config={
                "folder_base": str(cls._tmp),
                "name": "PathProject",
                "alias": "PP",
            }
        )
        cls._invoice = cls._project.add_invoice()
        cls._invoice_name = cls._invoice.name
        cls._receipt = cls._project.add_receipt()
        cls._receipt_name = cls._receipt.name

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_add_invoice_source_in_inputs_documents(self):
        """add_invoice should create the working tree under inputs/documents/."""
        source = (
            Path(self._project.folder_root)
            / "inputs"
            / "documents"
            / self._invoice_name
        )
        self.assertTrue(source.is_dir(), f"Source folder missing: {source}")

    def test_add_invoice_note_in_inputs_documents(self):
        """add_invoice should place the sidecar note at inputs/documents/{name}.md."""
        note = (
            Path(self._project.folder_root)
            / "inputs"
            / "documents"
            / f"{self._invoice_name}.md"
        )
        self.assertTrue(note.is_file(), f"Invoice note missing: {note}")

    def test_budget_documents_folder_not_created(self):
        """budget/documents/ must not be auto-created by new_project or add_invoice."""
        self.assertFalse(
            (Path(self._project.folder_root) / "budget" / "documents").exists()
        )

    def test_add_receipt_note_in_inputs_documents(self):
        """add_receipt() should place its note at inputs/documents/{name}.md."""
        note = (
            Path(self._project.folder_root)
            / "inputs"
            / "documents"
            / f"{self._receipt_name}.md"
        )
        self.assertTrue(note.is_file(), f"Receipt note missing: {note}")

    def test_add_receipt_with_missing_invoice_raises(self):
        """add_receipt(invoice_id=...) should raise FileNotFoundError when the invoice source is absent."""
        with self.assertRaises(FileNotFoundError):
            self._project.add_receipt(invoice_id="F999")


class TestLocateDocumentSource(unittest.TestCase):
    """Tests for Project._locate_document_source."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="losalamos_locdoc_"))
        cls._inputs_docs = cls._tmp / "MyProject" / "inputs" / "documents"
        cls._inputs_docs.mkdir(parents=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _make_project(self):
        p = Project(name="MyProject", alias="MP")
        p.folder_root = str(self._tmp / "MyProject")
        return p

    def test_finds_existing_source_folder(self):
        """_locate_document_source should return the path when the folder exists."""
        (self._inputs_docs / "INVOICE_MyProject_F001").mkdir(exist_ok=True)
        p = self._make_project()
        result = p._locate_document_source(name="INVOICE_MyProject_F001")
        self.assertTrue(result.is_dir())
        self.assertEqual(result.name, "INVOICE_MyProject_F001")

    def test_missing_folder_raises_file_not_found(self):
        """_locate_document_source should raise FileNotFoundError when absent."""
        p = self._make_project()
        with self.assertRaises(FileNotFoundError):
            p._locate_document_source(name="INVOICE_MyProject_F999")

    def test_error_message_contains_name(self):
        """FileNotFoundError message should include the document name."""
        p = self._make_project()
        with self.assertRaises(FileNotFoundError) as ctx:
            p._locate_document_source(name="RECEIPT_MyProject_F042")
        self.assertIn("RECEIPT_MyProject_F042", str(ctx.exception))

    def test_returns_path_object(self):
        """_locate_document_source should return a pathlib.Path."""
        (self._inputs_docs / "PROPOSAL_MyProject_F002").mkdir(exist_ok=True)
        p = self._make_project()
        result = p._locate_document_source(name="PROPOSAL_MyProject_F002")
        self.assertIsInstance(result, Path)


# ***********************************************************************
# SCRIPT
# ***********************************************************************


def _make_bare_project(tmp_root, name="testproj"):
    """Create a minimal project folder with the required subfolder tree."""
    folder_base = tmp_root / "base"
    folder_base.mkdir(parents=True, exist_ok=True)
    pj = Project(name=name, alias="TP")
    pj.folder_base = str(folder_base)
    pj.update()
    pj.setup()
    return pj


class TestAddTransfer(unittest.TestCase):
    """Project.add_transfer() creates a NoteTransfer in the right subfolder."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="transfer_add_"))
        cls._pj = _make_bare_project(cls._tmp)
        cls._note = cls._pj.add_transfer(
            transfer_type="inflow",
            date="2026-09-02",
            account="main-account",
            value=1500.0,
            status="Executed",
            protocol="Transfer",
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_note_file_exists_in_inflows(self):
        inflows = Path(self._pj.folder_root) / "budget" / "inflows"
        md_files = list(inflows.glob("*.md"))
        self.assertEqual(len(md_files), 1)

    def test_note_type_is_transfer(self):
        self.assertEqual(self._note.metadata.get("note_type"), "transfer")

    def test_transfer_type_stored(self):
        self.assertEqual(self._note.metadata.get("transfer_type"), "inflow")

    def test_account_stored(self):
        self.assertEqual(self._note.metadata.get("account"), "main-account")

    def test_value_stored(self):
        self.assertEqual(self._note.metadata.get("value"), 1500.0)

    def test_method_defaults_to_manual(self):
        self.assertEqual(self._note.metadata.get("method"), "Manual")

    def test_outflow_goes_to_outflows_folder(self):
        pj = _make_bare_project(self._tmp, name="outproj")
        pj.add_transfer(
            transfer_type="outflow",
            date="2026-09-02",
            account="expenses",
            value=200.0,
        )
        outflows = Path(pj.folder_root) / "budget" / "outflows"
        self.assertTrue(any(outflows.glob("*.md")))

    def test_invalid_transfer_type_raises(self):
        with self.assertRaises(ValueError):
            self._pj.add_transfer(
                transfer_type="sideways",
                date="2026-09-02",
                account="x",
                value=0,
            )

    def test_transfer_id_increments(self):
        pj = _make_bare_project(self._tmp, name="incproj")
        n1 = pj.add_transfer(
            transfer_type="inflow", date="2026-09-02", account="a", value=10
        )
        n2 = pj.add_transfer(
            transfer_type="inflow", date="2026-09-02", account="b", value=20
        )
        id1 = n1.metadata.get("name", "").split("_")[-1]
        id2 = n2.metadata.get("name", "").split("_")[-1]
        self.assertNotEqual(id1, id2)


class TestGetTransfers(unittest.TestCase):
    """Project.get_transfers() returns a DataFrame of all transfer notes."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="transfer_get_"))
        cls._pj = _make_bare_project(cls._tmp)
        cls._pj.add_transfer(
            transfer_type="inflow", date="2026-09-01", account="a", value=100
        )
        cls._pj.add_transfer(
            transfer_type="outflow", date="2026-09-02", account="b", value=50
        )
        cls._df = cls._pj.get_transfers()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_returns_dataframe(self):
        self.assertIsInstance(self._df, pd.DataFrame)

    def test_row_count_matches(self):
        self.assertEqual(len(self._df), 2)

    def test_expected_columns_present(self):
        expected = {
            "name",
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
        self.assertTrue(expected.issubset(set(self._df.columns)))

    def test_both_transfer_types_present(self):
        types = set(self._df["transfer_type"].tolist())
        self.assertIn("inflow", types)
        self.assertIn("outflow", types)

    def test_empty_when_no_transfers(self):
        pj = _make_bare_project(self._tmp, name="emptyproj")
        df = pj.get_transfers()
        self.assertEqual(len(df), 0)


if __name__ == "__main__":
    unittest.main()
