"""
Unit tests for DocumentTeX: load_data/is_main, make_flat, _copy_assets,
export, and split_preamble.

These use small synthetic .tex fixtures built per-test rather than the
real shipped base template, so the suite stays fast and isolated from
future template content changes -- it tests the logic in documents.py,
not the current content of any particular .tex file.
"""

import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from losalamos.documents import DocumentTeX


class TestDocumentTeXLoadData(unittest.TestCase):
    """is_main detection based on the presence of \\documentclass."""

    def setUp(self):
        self.tmp_root = Path(tempfile.mkdtemp(prefix="loaddata_tex_"))
        self.doc = DocumentTeX(name="TeXDoc", alias="TD")

    def tearDown(self):
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_is_main_true_when_documentclass_present(self):
        f = self.tmp_root / "main.tex"
        f.write_text(
            "\\documentclass{article}\n\\begin{document}\nhi\n\\end{document}\n"
        )
        self.doc.load_data(f)
        self.assertTrue(self.doc.is_main)

    def test_is_main_false_when_documentclass_absent(self):
        f = self.tmp_root / "chapter1.tex"
        f.write_text("This is just a partial file, no documentclass here.\n")
        self.doc.load_data(f)
        self.assertFalse(self.doc.is_main)


class TestDocumentTeXMakeFlat(unittest.TestCase):
    """make_flat: recursive \\input resolution, bibliography embedding,
    and asset collection (\\includegraphics / \\addbibresource)."""

    def setUp(self):
        self.tmp_root = Path(tempfile.mkdtemp(prefix="makeflat_test_"))

    def tearDown(self):
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_resolves_nested_input_root_relative(self):
        """
        Regression test: a nested file's own \\input reference must resolve
        relative to the project ROOT (input_tex.parent), not to that
        nested file's own directory -- the root-relative convention LaTeX
        itself uses for \\input/\\include regardless of nesting depth.
        """
        (self.tmp_root / "config").mkdir()
        main = self.tmp_root / "main.tex"
        main.write_text("\\documentclass{article}\n\\input{config/outer}\n")
        (self.tmp_root / "config" / "outer.tex").write_text(
            "outer content\n\\input{config/inner}\n"
        )
        (self.tmp_root / "config" / "inner.tex").write_text("inner content\n")

        flat = DocumentTeX.make_flat(main)
        self.assertIn("outer content", flat)
        self.assertIn("inner content", flat)
        self.assertNotIn("\\input{config/inner}", flat)

    def test_embeds_bibliography_when_bbl_exists(self):
        main = self.tmp_root / "main.tex"
        main.write_text("\\documentclass{article}\n\\bibliography{refs}\n")
        (self.tmp_root / "main.bbl").write_text(
            "\\begin{thebibliography}\nX\n\\end{thebibliography}\n"
        )

        flat = DocumentTeX.make_flat(main)
        self.assertIn("thebibliography", flat)
        self.assertNotIn("\\bibliography{refs}", flat)

    def test_leaves_bibliography_untouched_when_no_bbl(self):
        main = self.tmp_root / "main.tex"
        main.write_text("\\documentclass{article}\n\\bibliography{refs}\n")

        flat = DocumentTeX.make_flat(main)
        self.assertIn("\\bibliography{refs}", flat)

    def test_collects_addbibresource_asset(self):
        main = self.tmp_root / "main.tex"
        main.write_text("\\documentclass{article}\n\\addbibresource{references.bib}\n")
        bib = self.tmp_root / "references.bib"
        bib.write_text("@article{x,}\n")

        assets = set()
        flat = DocumentTeX.make_flat(main, assets=assets)
        self.assertIn(bib, assets)
        # addbibresource itself must stay in the flattened text (biber still
        # needs to read the raw .bib file after flattening)
        self.assertIn("\\addbibresource{references.bib}", flat)

    def test_addbibresource_missing_file_not_collected(self):
        main = self.tmp_root / "main.tex"
        main.write_text("\\documentclass{article}\n\\addbibresource{ghost.bib}\n")

        assets = set()
        DocumentTeX.make_flat(main, assets=assets)
        self.assertEqual(len(assets), 0)

    def test_collects_includegraphics_with_explicit_extension(self):
        main = self.tmp_root / "main.tex"
        main.write_text(
            "\\documentclass{article}\n"
            "\\includegraphics[width=1cm]{images/logo.png}\n"
        )
        (self.tmp_root / "images").mkdir()
        img = self.tmp_root / "images" / "logo.png"
        img.write_bytes(b"\x89PNG")

        assets = set()
        DocumentTeX.make_flat(main, assets=assets)
        self.assertIn(img, assets)

    def test_collects_includegraphics_with_omitted_extension(self):
        """LaTeX allows the extension to be omitted; make_flat should try
        common extensions and collect whichever file actually exists."""
        main = self.tmp_root / "main.tex"
        main.write_text("\\documentclass{article}\n\\includegraphics{images/logo}\n")
        (self.tmp_root / "images").mkdir()
        img = self.tmp_root / "images" / "logo.pdf"
        img.write_bytes(b"%PDF-1.4")

        assets = set()
        DocumentTeX.make_flat(main, assets=assets)
        self.assertIn(img, assets)

    def test_includegraphics_missing_file_not_collected(self):
        main = self.tmp_root / "main.tex"
        main.write_text("\\documentclass{article}\n\\includegraphics{no-such-image}\n")
        assets = set()
        DocumentTeX.make_flat(main, assets=assets)
        self.assertEqual(len(assets), 0)

    def test_no_asset_collection_when_assets_is_none(self):
        """Default behaviour (assets=None) must not error and must not
        attempt collection -- existing callers like to_flat() rely on this."""
        main = self.tmp_root / "main.tex"
        main.write_text("\\documentclass{article}\n\\includegraphics{images/logo}\n")
        flat = DocumentTeX.make_flat(main)  # assets omitted entirely
        self.assertIsInstance(flat, str)


class TestDocumentTeXCopyAssets(unittest.TestCase):
    """_copy_assets: relative-path preservation and the outside-root fallback."""

    def setUp(self):
        self.tmp_root = Path(tempfile.mkdtemp(prefix="copyassets_test_"))
        self.source_root = self.tmp_root / "project"
        self.source_root.mkdir()
        self.export_dir = self.tmp_root / "export"
        self.export_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_preserves_relative_path_under_source_root(self):
        (self.source_root / "images").mkdir()
        asset = self.source_root / "images" / "logo.png"
        asset.write_bytes(b"\x89PNG")

        DocumentTeX._copy_assets({asset}, self.source_root, self.export_dir)

        copied = self.export_dir / "images" / "logo.png"
        self.assertTrue(copied.exists())
        self.assertEqual(copied.read_bytes(), b"\x89PNG")

    def test_falls_back_to_filename_when_outside_source_root(self):
        outside_dir = self.tmp_root / "elsewhere"
        outside_dir.mkdir()
        asset = outside_dir / "stray.png"
        asset.write_bytes(b"\x89PNG")

        DocumentTeX._copy_assets({asset}, self.source_root, self.export_dir)

        copied = self.export_dir / "stray.png"
        self.assertTrue(copied.exists())


class TestDocumentTeXExport(unittest.TestCase):
    """export(): plain/flatten/split modes, asset copying, zip_export,
    and error handling."""

    def setUp(self):
        self.tmp_root = Path(tempfile.mkdtemp(prefix="export_test_"))
        self.project_dir = self.tmp_root / "project"
        self.project_dir.mkdir()

        main = self.project_dir / "main.tex"
        main.write_text(
            "\\documentclass{article}\n"
            "\\addbibresource{refs.bib}\n"
            "\\begin{document}\n"
            "\\input{content}\n"
            "\\end{document}\n"
        )
        (self.project_dir / "content.tex").write_text(
            "\\includegraphics{images/logo}\nSome body text.\n"
        )
        (self.project_dir / "images").mkdir()
        (self.project_dir / "images" / "logo.png").write_bytes(b"\x89PNG")
        (self.project_dir / "refs.bib").write_text("@article{x,}\n")

        self.doc = DocumentTeX(name="ExportDoc", alias="ED")
        self.doc.load_data(main)

        self.out_root = self.tmp_root / "out"
        self.out_root.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_plain_mode_copies_single_file_only(self):
        result = self.doc.export(self.out_root, "plain_export")
        self.assertEqual(result, self.out_root / "plain_export")
        self.assertTrue((result / "main.tex").exists())
        # plain mode never resolves \input or copies assets
        self.assertFalse((result / "content.tex").exists())
        self.assertFalse((result / "refs.bib").exists())

    def test_flatten_mode_merges_and_copies_assets(self):
        result = self.doc.export(self.out_root, "flat_export", flatten=True)
        merged = (result / "flat_export.tex").read_text()
        self.assertIn("Some body text.", merged)
        self.assertTrue((result / "refs.bib").exists())
        self.assertTrue((result / "images" / "logo.png").exists())

    def test_split_mode_produces_exactly_preamble_and_main(self):
        result = self.doc.export(self.out_root, "split_export", split=True)
        tex_files = sorted(p.name for p in result.glob("*.tex"))
        self.assertEqual(tex_files, ["main.tex", "preamble.tex"])
        # no leftover intermediate flat file
        self.assertEqual(len(list(result.glob("_*_flat.tex"))), 0)
        self.assertTrue((result / "refs.bib").exists())
        self.assertTrue((result / "images" / "logo.png").exists())

    def test_zip_export_places_files_at_archive_root(self):
        self.doc.export(self.out_root, "zip_export", split=True, zip_export=True)
        zip_path = self.out_root / "zip_export.zip"
        self.assertTrue(zip_path.exists())

        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
        # files sit at the archive root -- no "zip_export/" wrapping prefix
        self.assertIn("main.tex", names)
        self.assertIn("preamble.tex", names)
        self.assertIn("refs.bib", names)
        self.assertFalse(any(n.startswith("zip_export/") for n in names))

        # uncompressed folder still left in place alongside the zip
        self.assertTrue((self.out_root / "zip_export").is_dir())

    def test_raises_runtime_error_when_not_main(self):
        partial = self.project_dir / "partial.tex"
        partial.write_text("No documentclass in this one.\n")
        self.doc.load_data(partial)
        with self.assertRaises(RuntimeError):
            self.doc.export(self.out_root, "should_fail")

    def test_raises_file_exists_error_when_target_exists(self):
        (self.out_root / "already_there").mkdir()
        with self.assertRaises(FileExistsError):
            self.doc.export(self.out_root, "already_there")


class TestDocumentTeXSplitPreamble(unittest.TestCase):
    """split_preamble: structural slicing and its error conditions."""

    def setUp(self):
        self.tmp_root = Path(tempfile.mkdtemp(prefix="splitpreamble_test_"))

    def tearDown(self):
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_splits_preamble_and_body_correctly(self):
        main = self.tmp_root / "source.tex"
        main.write_text(
            "\\documentclass{article}\n"
            "\\usepackage{amsmath}\n"
            "\\newcommand{\\foo}{bar}\n"
            "\\begin{document}\n"
            "Hello world.\n"
            "\\end{document}\n"
        )
        preamble_path, main_path = DocumentTeX.split_preamble(main)

        preamble_content = preamble_path.read_text()
        main_content = main_path.read_text()

        self.assertIn("\\usepackage{amsmath}", preamble_content)
        self.assertIn("\\newcommand{\\foo}{bar}", preamble_content)
        self.assertNotIn("\\documentclass", preamble_content)

        self.assertIn("\\documentclass{article}", main_content)
        self.assertIn("\\input{preamble}", main_content)
        self.assertIn("Hello world.", main_content)
        self.assertNotIn("\\usepackage{amsmath}", main_content)

    def test_raises_valueerror_when_no_documentclass(self):
        partial = self.tmp_root / "partial.tex"
        partial.write_text("\\begin{document}\nNo class here.\n\\end{document}\n")
        with self.assertRaises(ValueError):
            DocumentTeX.split_preamble(partial)

    def test_raises_valueerror_when_no_begin_document(self):
        broken = self.tmp_root / "broken.tex"
        broken.write_text("\\documentclass{article}\nNo begin document here.\n")
        with self.assertRaises(ValueError):
            DocumentTeX.split_preamble(broken)

    def test_raises_valueerror_on_same_folder_stem_collision(self):
        main = self.tmp_root / "main.tex"
        main.write_text(
            "\\documentclass{article}\n\\begin{document}\nx\n\\end{document}\n"
        )
        with self.assertRaises(ValueError):
            # input stem "main" collides with the default main_name "main"
            # in the same directory
            DocumentTeX.split_preamble(main, output_folder=self.tmp_root)


if __name__ == "__main__":
    unittest.main()
