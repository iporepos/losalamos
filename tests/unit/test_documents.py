# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for Document creation and loading utilities.

Features
--------
 - Test document folder creation via ``Document.new``
 - Validate simple mode (BASE_TEMPLATE only)
 - Validate overlay mode (BASE_TEMPLATE merged with template_overlay)
 - Validate filesystem side effects and return value
 - Validate error handling for invalid inputs

Overview
--------
This test suite validates the behavioral contract of the ``Document.new``
method, ensuring correct error handling, filesystem setup, overlay merge
semantics, and the integrity of the returned path.

Examples
--------
From the terminal, run:

.. code-block:: bash

    python ./tests/unit/test_documents.py

"""

# ***********************************************************************
# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import shutil
import tempfile
import unittest
from pathlib import Path

# Project-level imports
# =======================================================================
from losalamos.documents import Document

# ***********************************************************************
# CLASSES
# ***********************************************************************


class TestDocumentNew(unittest.TestCase):
    """
    Tests for ``Document.new`` — folder creation, template copying,
    overlay merge semantics, error handling, and return value.
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests.

        Creates a temporary root directory and two minimal template trees:

        - ``cls._base_template``: stands in for ``BASE_TEMPLATE`` and
          contains a small representative file tree.
        - ``cls._overlay_template``: used in overlay-mode tests; shares
          one file with the base (collision) and adds one exclusive file.
        """
        cls._tmp_root = tempfile.mkdtemp(prefix="document_test_")

        # Build a minimal BASE_TEMPLATE tree
        # --------------------------------------------------------------
        cls._base_template = Path(cls._tmp_root) / "_base_template"
        cls._base_template.mkdir()
        (cls._base_template / "main.txt").write_text("base main")
        (cls._base_template / "config.cfg").write_text("base config")
        assets = cls._base_template / "assets"
        assets.mkdir()
        (assets / "logo.png").write_bytes(b"\x89PNG")

        # Build a minimal overlay template tree
        # --------------------------------------------------------------
        cls._overlay_template = Path(cls._tmp_root) / "_overlay_template"
        cls._overlay_template.mkdir()
        (cls._overlay_template / "main.txt").write_text("overlay main")  # collision
        (cls._overlay_template / "extra.txt").write_text("overlay extra")  # overlay-only

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests. Removes the entire temporary tree.
        """
        shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def setUp(self):
        """
        Runs before each test.

        Creates a fresh ``Document`` instance with ``BASE_TEMPLATE``
        pointing to the temporary base template built in ``setUpClass``.
        Each test receives a unique ``work_dir`` to avoid cross-test
        filesystem interference.
        """
        self.doc = Document(name="TestDoc", alias="TD")
        self.doc.BASE_TEMPLATE = self._base_template

        self.work_dir = Path(self._tmp_root) / f"work_{self._testMethodName}"
        self.work_dir.mkdir()

    # -------------------------------------------------------------------
    # Return value
    # -------------------------------------------------------------------

    def test_new_returns_path(self):
        """
        ``new`` should return a ``pathlib.Path`` instance on success.
        """
        result = self.doc.new("doc_return", self.work_dir)
        self.assertIsInstance(result, Path)

    def test_new_returns_absolute_path(self):
        """
        The returned path should be absolute.
        """
        result = self.doc.new("doc_absolute", self.work_dir)
        self.assertTrue(result.is_absolute())

    def test_new_returns_correct_path(self):
        """
        The returned path should equal ``folder/name``.
        """
        result = self.doc.new("doc_correct", self.work_dir)
        self.assertEqual(result, self.work_dir / "doc_correct")

    # -------------------------------------------------------------------
    # Simple mode — filesystem
    # -------------------------------------------------------------------

    def test_new_simple_creates_target_folder(self):
        """
        ``new`` should create the target folder on the filesystem.
        """
        target = self.doc.new("doc_simple", self.work_dir)
        self.assertTrue(target.is_dir())

    def test_new_simple_copies_all_base_files(self):
        """
        Simple mode should copy every file from ``BASE_TEMPLATE``.
        """
        target = self.doc.new("doc_simple_files", self.work_dir)

        self.assertTrue((target / "main.txt").exists())
        self.assertTrue((target / "config.cfg").exists())
        self.assertTrue((target / "assets" / "logo.png").exists())

    def test_new_simple_preserves_file_content(self):
        """
        Simple mode should preserve file contents from ``BASE_TEMPLATE``.
        """
        target = self.doc.new("doc_simple_content", self.work_dir)

        self.assertEqual((target / "main.txt").read_text(), "base main")
        self.assertEqual((target / "config.cfg").read_text(), "base config")

    def test_new_simple_preserves_subfolder_structure(self):
        """
        Simple mode should preserve the subdirectory structure of ``BASE_TEMPLATE``.
        """
        target = self.doc.new("doc_simple_tree", self.work_dir)
        self.assertTrue((target / "assets").is_dir())

    # -------------------------------------------------------------------
    # Overlay mode — merge semantics
    # -------------------------------------------------------------------

    def test_new_overlay_collision_resolved_to_overlay(self):
        """
        Overlay mode: files present in both templates should come from
        ``template_overlay``, not ``BASE_TEMPLATE``.
        """
        target = self.doc.new(
            "doc_overlay_collision",
            self.work_dir,
            template_overlay=self._overlay_template,
        )
        self.assertEqual((target / "main.txt").read_text(), "overlay main")

    def test_new_overlay_base_only_files_are_copied(self):
        """
        Overlay mode: files present only in ``BASE_TEMPLATE`` should still
        be copied to the target.
        """
        target = self.doc.new(
            "doc_overlay_base_only",
            self.work_dir,
            template_overlay=self._overlay_template,
        )
        self.assertTrue((target / "config.cfg").exists())
        self.assertEqual((target / "config.cfg").read_text(), "base config")

    def test_new_overlay_only_files_are_copied(self):
        """
        Overlay mode: files present only in ``template_overlay`` should
        be copied to the target.
        """
        target = self.doc.new(
            "doc_overlay_only",
            self.work_dir,
            template_overlay=self._overlay_template,
        )
        self.assertTrue((target / "extra.txt").exists())
        self.assertEqual((target / "extra.txt").read_text(), "overlay extra")

    def test_new_overlay_base_subfolder_files_are_copied(self):
        """
        Overlay mode: subdirectory files from ``BASE_TEMPLATE`` with no
        counterpart in the overlay should still be copied.
        """
        target = self.doc.new(
            "doc_overlay_subfolders",
            self.work_dir,
            template_overlay=self._overlay_template,
        )
        self.assertTrue((target / "assets" / "logo.png").exists())

    def test_new_overlay_result_is_union_of_both_trees(self):
        """
        Overlay mode: the target should contain the union of all files
        from both templates.
        """
        target = self.doc.new(
            "doc_overlay_union",
            self.work_dir,
            template_overlay=self._overlay_template,
        )
        expected = {"main.txt", "config.cfg", "extra.txt"}
        found = {f.name for f in target.rglob("*") if f.is_file()}
        self.assertTrue(expected.issubset(found))

    # -------------------------------------------------------------------
    # Error handling
    # -------------------------------------------------------------------

    def test_new_raises_if_target_exists(self):
        """
        ``new`` should raise ``FileExistsError`` if the target folder
        already exists, without modifying any files.
        """
        existing = self.work_dir / "doc_exists"
        existing.mkdir()

        with self.assertRaises(FileExistsError):
            self.doc.new("doc_exists", self.work_dir)

    def test_new_raises_if_overlay_is_not_a_directory(self):
        """
        ``new`` should raise ``NotADirectoryError`` if ``template_overlay``
        points to a path that is not a valid directory.
        """
        with self.assertRaises(NotADirectoryError):
            self.doc.new(
                "doc_bad_overlay",
                self.work_dir,
                template_overlay="/nonexistent/path/to/nowhere",
            )

    def test_new_no_files_written_on_existing_target(self):
        """
        When ``FileExistsError`` is raised, no new files should be
        created inside the already-existing target folder.
        """
        existing = self.work_dir / "doc_no_write"
        existing.mkdir()
        (existing / "sentinel.txt").write_text("untouched")

        try:
            self.doc.new("doc_no_write", self.work_dir)
        except FileExistsError:
            pass

        # Only the sentinel we placed should be there
        files = list(existing.iterdir())
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "sentinel.txt")

    def test_new_no_files_written_on_bad_overlay(self):
        """
        When ``NotADirectoryError`` is raised due to an invalid overlay,
        the target folder should not have been created at all.
        """
        target = self.work_dir / "doc_no_write_overlay"

        try:
            self.doc.new(
                "doc_no_write_overlay",
                self.work_dir,
                template_overlay="/nonexistent/path",
            )
        except NotADirectoryError:
            pass

        self.assertFalse(target.exists())


# ***********************************************************************
# SCRIPT
# ***********************************************************************

if __name__ == "__main__":
    unittest.main()