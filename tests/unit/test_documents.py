"""
Unit tests for the Document base class: __str__, load_data, and new().
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from losalamos.documents import Document


class TestDocumentStr(unittest.TestCase):
    """Tests for Document.__str__ -- must not crash on list-based data."""

    def setUp(self):
        self.doc = Document(name="StrDoc", alias="SD")

    def test_str_with_none_data(self):
        """Fresh, unloaded instance: data is None, must not raise."""
        result = str(self.doc)
        self.assertIn("Data:", result)
        self.assertIn("None", result)

    def test_str_with_short_data_no_truncation(self):
        """<=10 lines: full body shown, no ' ... ' truncation marker."""
        self.doc.data = ["line1\n", "line2\n", "line3\n"]
        result = str(self.doc)
        self.assertIn("line1", result)
        self.assertIn("line3", result)
        self.assertNotIn(" ... ", result)

    def test_str_with_long_data_truncates_head_tail(self):
        """>10 lines: head and tail shown, middle collapsed with ' ... '."""
        self.doc.data = [f"line{i}\n" for i in range(20)]
        result = str(self.doc)
        self.assertIn("line0", result)  # head
        self.assertIn("line19", result)  # tail
        self.assertIn(" ... ", result)
        self.assertNotIn("line10", result)  # middle, should be collapsed out


class TestDocumentLoadData(unittest.TestCase):
    """Tests for Document.load_data."""

    def setUp(self):
        self.tmp_root = Path(tempfile.mkdtemp(prefix="loaddata_test_"))
        self.doc = Document(name="LoadDoc", alias="LD")

    def tearDown(self):
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_load_data_sets_absolute_file_data(self):
        f = self.tmp_root / "sample.txt"
        f.write_text("hello\nworld\n")
        self.doc.load_data(f)
        self.assertTrue(self.doc.file_data.is_absolute())
        self.assertEqual(self.doc.file_data, f.absolute())

    def test_load_data_sets_data_as_line_list(self):
        f = self.tmp_root / "sample.txt"
        f.write_text("hello\nworld\n")
        self.doc.load_data(f)
        self.assertEqual(self.doc.data, ["hello\n", "world\n"])


class TestDocumentNew(unittest.TestCase):
    """
    Tests for Document.new -- folder creation, template copying, overlay
    merge semantics, error handling, and the in-place load performed on
    success.

    NOTE ON SIGNATURE: new(self, folder, name=None, template_overlay=None).
    folder is positional-first; name is optional and defaults to self.name
    when omitted. Every call below follows that order deliberately -- this
    suite previously used a (name, folder) calling convention that didn't
    match the real signature, which silently mis-targeted every test.
    """

    @classmethod
    def setUpClass(cls):
        cls._tmp_root = Path(tempfile.mkdtemp(prefix="document_test_"))

        # Minimal BASE_TEMPLATE tree
        cls._base_template = cls._tmp_root / "_base_template"
        cls._base_template.mkdir()
        (cls._base_template / "main.txt").write_text("base main")
        (cls._base_template / "config.cfg").write_text("base config")
        assets = cls._base_template / "assets"
        assets.mkdir()
        (assets / "logo.png").write_bytes(b"\x89PNG")

        # Minimal overlay template tree
        cls._overlay_template = cls._tmp_root / "_overlay_template"
        cls._overlay_template.mkdir()
        (cls._overlay_template / "main.txt").write_text("overlay main")
        (cls._overlay_template / "extra.txt").write_text("overlay extra")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def setUp(self):
        self.doc = Document(name="TestDoc", alias="TD")
        self.doc.BASE_TEMPLATE = self._base_template
        self.work_dir = self._tmp_root / f"work_{self._testMethodName}"
        self.work_dir.mkdir()

    # -- in-place contract --------------------------------------------

    def test_new_returns_none(self):
        result = self.doc.new(self.work_dir, "doc_return")
        self.assertIsNone(result)

    def test_new_defaults_name_to_self_name_when_omitted(self):
        """name=None (the default) should fall back to self.name."""
        self.doc.new(self.work_dir)
        target = self.work_dir / "TestDoc"  # self.doc.name
        self.assertTrue(target.is_dir())
        self.assertEqual(self.doc.file_data, target / "main.txt")

    def test_new_explicit_name_overrides_self_name(self):
        self.doc.new(self.work_dir, "explicit_name")
        target = self.work_dir / "explicit_name"
        self.assertTrue(target.is_dir())
        self.assertFalse((self.work_dir / "TestDoc").exists())

    def test_new_loads_file_data_in_place(self):
        self.doc.new(self.work_dir, "doc_file_data")
        expected = self.work_dir / "doc_file_data" / "main.txt"
        self.assertEqual(self.doc.file_data, expected)
        self.assertTrue(self.doc.file_data.is_absolute())

    def test_new_loads_data_in_place(self):
        self.doc.new(self.work_dir, "doc_data_lines")
        self.assertEqual(self.doc.data, ["base main"])

    # -- simple mode: filesystem ----------------------------------------

    def test_new_simple_creates_target_folder(self):
        self.doc.new(self.work_dir, "doc_simple")
        self.assertTrue((self.work_dir / "doc_simple").is_dir())

    def test_new_simple_copies_all_base_files(self):
        self.doc.new(self.work_dir, "doc_simple_files")
        target = self.work_dir / "doc_simple_files"
        self.assertTrue((target / "main.txt").exists())
        self.assertTrue((target / "config.cfg").exists())
        self.assertTrue((target / "assets" / "logo.png").exists())

    def test_new_simple_preserves_file_content(self):
        self.doc.new(self.work_dir, "doc_simple_content")
        target = self.work_dir / "doc_simple_content"
        self.assertEqual((target / "main.txt").read_text(), "base main")
        self.assertEqual((target / "config.cfg").read_text(), "base config")

    def test_new_simple_preserves_subfolder_structure(self):
        self.doc.new(self.work_dir, "doc_simple_tree")
        self.assertTrue((self.work_dir / "doc_simple_tree" / "assets").is_dir())

    # -- overlay mode: merge semantics -----------------------------------

    def test_new_overlay_collision_resolved_to_overlay(self):
        self.doc.new(
            self.work_dir,
            "doc_overlay_collision",
            template_overlay=self._overlay_template,
        )
        target = self.work_dir / "doc_overlay_collision"
        self.assertEqual((target / "main.txt").read_text(), "overlay main")

    def test_new_overlay_base_only_files_are_copied(self):
        self.doc.new(
            self.work_dir,
            "doc_overlay_base_only",
            template_overlay=self._overlay_template,
        )
        target = self.work_dir / "doc_overlay_base_only"
        self.assertEqual((target / "config.cfg").read_text(), "base config")

    def test_new_overlay_only_files_are_copied(self):
        self.doc.new(
            self.work_dir,
            "doc_overlay_only",
            template_overlay=self._overlay_template,
        )
        target = self.work_dir / "doc_overlay_only"
        self.assertEqual((target / "extra.txt").read_text(), "overlay extra")

    def test_new_overlay_base_subfolder_files_are_copied(self):
        self.doc.new(
            self.work_dir,
            "doc_overlay_subfolders",
            template_overlay=self._overlay_template,
        )
        target = self.work_dir / "doc_overlay_subfolders"
        self.assertTrue((target / "assets" / "logo.png").exists())

    def test_new_overlay_result_is_union_of_both_trees(self):
        self.doc.new(
            self.work_dir,
            "doc_overlay_union",
            template_overlay=self._overlay_template,
        )
        target = self.work_dir / "doc_overlay_union"
        expected = {"main.txt", "config.cfg", "extra.txt"}
        found = {f.name for f in target.rglob("*") if f.is_file()}
        self.assertTrue(expected.issubset(found))

    # -- error handling --------------------------------------------------

    def test_new_raises_if_target_exists(self):
        existing = self.work_dir / "doc_exists"
        existing.mkdir()
        with self.assertRaises(FileExistsError):
            self.doc.new(self.work_dir, "doc_exists")

    def test_new_raises_if_overlay_is_not_a_directory(self):
        with self.assertRaises(NotADirectoryError):
            self.doc.new(
                self.work_dir,
                "doc_bad_overlay",
                template_overlay="/nonexistent/path/to/nowhere",
            )

    def test_new_no_files_written_on_existing_target(self):
        existing = self.work_dir / "doc_no_write"
        existing.mkdir()
        (existing / "sentinel.txt").write_text("untouched")
        try:
            self.doc.new(self.work_dir, "doc_no_write")
        except FileExistsError:
            pass
        files = list(existing.iterdir())
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "sentinel.txt")

    def test_new_no_files_written_on_bad_overlay(self):
        target = self.work_dir / "doc_no_write_overlay"
        try:
            self.doc.new(
                self.work_dir,
                "doc_no_write_overlay",
                template_overlay="/nonexistent/path",
            )
        except NotADirectoryError:
            pass
        self.assertFalse(target.exists())

    def test_new_raises_filenotfound_when_no_main_file(self):
        """BASE_TEMPLATE with zero top-level main.* files."""
        no_main_template = self._tmp_root / "_no_main_template"
        no_main_template.mkdir()
        (no_main_template / "config.cfg").write_text("no main here")
        self.doc.BASE_TEMPLATE = no_main_template
        with self.assertRaises(FileNotFoundError):
            self.doc.new(self.work_dir, "doc_no_main")

    def test_new_raises_filenotfound_when_multiple_main_files(self):
        """BASE_TEMPLATE with two top-level main.* files -- ambiguous."""
        ambiguous_template = self._tmp_root / "_ambiguous_template"
        ambiguous_template.mkdir()
        (ambiguous_template / "main.txt").write_text("main one")
        (ambiguous_template / "main.tex").write_text("main two")
        self.doc.BASE_TEMPLATE = ambiguous_template
        with self.assertRaises(FileNotFoundError):
            self.doc.new(self.work_dir, "doc_ambiguous_main")


class _VariantLevelA(Document):
    """Throwaway subclass for the MRO variant-template test below."""

    VARIANT_TEMPLATE = None  # set per-test on the class itself


class _VariantLevelB(_VariantLevelA):
    """Second-level subclass -- must layer on top of level A, not shadow it."""

    VARIANT_TEMPLATE = None  # set per-test on the class itself


class TestDocumentNewVariantTemplateMRO(unittest.TestCase):
    """
    Regression test: new() must merge every ancestor's VARIANT_TEMPLATE
    (via a base-to-derived MRO walk), not just the most-derived class's
    own value. Before this fix, _VariantLevelB(_VariantLevelA) would
    silently shadow level A's VARIANT_TEMPLATE via ordinary Python
    attribute resolution instead of layering on top of it.
    """

    @classmethod
    def setUpClass(cls):
        cls._tmp_root = Path(tempfile.mkdtemp(prefix="mro_test_"))

        cls._base_template = cls._tmp_root / "_base"
        cls._base_template.mkdir()
        (cls._base_template / "main.txt").write_text("base main")

        cls._variant_a = cls._tmp_root / "_variant_a"
        cls._variant_a.mkdir()
        (cls._variant_a / "from_a.txt").write_text("from level A")

        cls._variant_b = cls._tmp_root / "_variant_b"
        cls._variant_b.mkdir()
        (cls._variant_b / "from_b.txt").write_text("from level B")

        _VariantLevelA.VARIANT_TEMPLATE = cls._variant_a
        _VariantLevelB.VARIANT_TEMPLATE = cls._variant_b

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def setUp(self):
        self.doc = _VariantLevelB(name="MRODoc", alias="MD")
        self.doc.BASE_TEMPLATE = self._base_template
        self.work_dir = self._tmp_root / f"work_{self._testMethodName}"
        self.work_dir.mkdir()

    def test_new_merges_every_ancestor_variant_template(self):
        self.doc.new(self.work_dir, "doc_mro")
        target = self.work_dir / "doc_mro"
        self.assertTrue(
            (target / "from_a.txt").exists(),
            "Level A's VARIANT_TEMPLATE file is missing -- an ancestor's "
            "variant was shadowed instead of merged.",
        )
        self.assertTrue(
            (target / "from_b.txt").exists(),
            "Level B's own VARIANT_TEMPLATE file is missing.",
        )


if __name__ == "__main__":
    unittest.main()
