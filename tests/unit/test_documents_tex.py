# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for ``DocumentTeX`` methods.

Features
--------
- Test main-file detection via ``load_data``
- Validate ``make_flat`` resolves ``\\input`` / ``\\include`` recursively
- Validate ``make_flat`` embeds a pre-built ``.bbl`` file
- Validate ``to_flat`` with ``compile_first=False`` (no latexmk required)
- Validate ``split_preamble`` structure, custom names, custom output folder
- Validate ``split_preamble`` safety guard (stem collision)
- Validate ``split_preamble`` error handling for malformed input
- Validate ``lint_paragraphs``, ``lint_decorations_remove``,
  ``lint_decorations_add``, ``lint_blank_lines``

Overview
--------
``to_pdf`` is intentionally excluded: it requires ``latexmk`` and is an
integration concern unsuitable for CI. ``to_flat`` is tested with
``compile_first=False`` so it never shells out to ``latexmk``.

All tests that write files operate under a root directory resolved at
class setup time. When ``RUN_BENCHMARKS`` is off (the default), a
``tempfile.mkdtemp`` tree is used and torn down after the class finishes.
When ``RUN_BENCHMARKS`` is on, files are written to
``OUTPUT_DIR / "tex" / <class_prefix>`` and kept for manual inspection.

Running
-------
Standard run (no output files retained)::

    python -m tests.unit.test_documents_tex

With benchmark output enabled (output files written to ``tests/outputs/tex/``):

.. code-block:: bash

    # Linux / macOS
    RUN_BENCHMARKS=1 python -m tests.unit.test_documents_tex

    # Windows (Command Prompt)
    set RUN_BENCHMARKS=1 && python -m tests.unit.test_documents_tex

    # Windows (PowerShell)
    $env:RUN_BENCHMARKS="1"; python -m tests.unit.test_documents_tex
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
from losalamos.documents import DocumentTeX
from tests.conftest import DATA_DIR, OUTPUT_DIR, RUN_BENCHMARKS

# ***********************************************************************
# CONSTANTS
# ***********************************************************************

TEX_DIR = DATA_DIR


# ***********************************************************************
# CLASSES
# ***********************************************************************


class TestDocumentTeXLoadData(unittest.TestCase):
    """
    Tests for ``DocumentTeX.load_data`` — file reading and ``is_main``
    detection.
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    def setUp(self):
        self.doc = DocumentTeX()

    # -------------------------------------------------------------------
    # is_main detection
    # -------------------------------------------------------------------

    def test_load_main_sets_is_main_true(self):
        """A file containing \\documentclass must have is_main=True."""
        self.doc.load_data(TEX_DIR / "tex_main.tex")
        self.assertTrue(self.doc.is_main)

    def test_load_fragment_sets_is_main_false(self):
        """A file without \\documentclass must have is_main=False."""
        self.doc.load_data(TEX_DIR / "tex_fragment.tex")
        self.assertFalse(self.doc.is_main)

    def test_load_data_populates_data_list(self):
        """load_data must populate self.data as a non-empty list."""
        self.doc.load_data(TEX_DIR / "tex_main.tex")
        self.assertIsInstance(self.doc.data, list)
        self.assertGreater(len(self.doc.data), 0)

    def test_load_data_sets_file_data_as_absolute_path(self):
        """file_data must be resolved to an absolute Path."""
        self.doc.load_data(TEX_DIR / "tex_main.tex")
        self.assertIsInstance(self.doc.file_data, Path)
        self.assertTrue(self.doc.file_data.is_absolute())


class TestMakeFlat(unittest.TestCase):
    """
    Tests for ``DocumentTeX.make_flat`` — recursive ``\\input`` resolution
    and ``.bbl`` embedding.
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        if RUN_BENCHMARKS:
            cls._tmp_root = OUTPUT_DIR / "tex" / "makeflat"
            cls._tmp_root.mkdir(parents=True, exist_ok=True)
        else:
            cls._tmp_root = Path(tempfile.mkdtemp(prefix="losalamos_test_makeflat_"))

    @classmethod
    def tearDownClass(cls):
        if not RUN_BENCHMARKS:
            shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def _work_dir(self):
        """Return a fresh per-test subdirectory."""
        d = Path(self._tmp_root) / self._testMethodName
        d.mkdir(exist_ok=True)
        return d

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _copy_fixtures(self, work_dir, include_bbl=False):
        """
        Copy the standard fixture tree into work_dir so make_flat can
        resolve \\input{tex_section} relative to the copied tex_main.tex.
        """
        shutil.copy(TEX_DIR / "tex_main.tex", work_dir / "tex_main.tex")
        shutil.copy(TEX_DIR / "tex_section.tex", work_dir / "tex_section.tex")
        if include_bbl:
            shutil.copy(TEX_DIR / "tex_main.bbl", work_dir / "tex_main.bbl")
        return work_dir / "tex_main.tex"

    # -------------------------------------------------------------------
    # Return value
    # -------------------------------------------------------------------

    def test_returns_string(self):
        """make_flat must return a str."""
        work_dir = self._work_dir()
        main = self._copy_fixtures(work_dir)
        result = DocumentTeX.make_flat(main, output_tex=work_dir / "flat.tex")
        self.assertIsInstance(result, str)

    # -------------------------------------------------------------------
    # \\input resolution
    # -------------------------------------------------------------------

    def test_input_directive_is_resolved(self):
        """\\input{tex_section} must be replaced by the contents of tex_section.tex."""
        work_dir = self._work_dir()
        main = self._copy_fixtures(work_dir)
        result = DocumentTeX.make_flat(main, output_tex=work_dir / "flat.tex")
        self.assertNotIn(r"\input{tex_section}", result)
        self.assertIn(r"\section{Methods}", result)

    def test_documentclass_retained_after_flatten(self):
        """\\documentclass must survive flattening."""
        work_dir = self._work_dir()
        main = self._copy_fixtures(work_dir)
        result = DocumentTeX.make_flat(main, output_tex=work_dir / "flat.tex")
        self.assertIn(r"\documentclass", result)

    def test_begin_document_retained_after_flatten(self):
        """\\begin{document} must survive flattening."""
        work_dir = self._work_dir()
        main = self._copy_fixtures(work_dir)
        result = DocumentTeX.make_flat(main, output_tex=work_dir / "flat.tex")
        self.assertIn(r"\begin{document}", result)

    # -------------------------------------------------------------------
    # .bbl embedding
    # -------------------------------------------------------------------

    def test_bibliography_replaced_by_bbl_content(self):
        """\\bibliography{refs} must be replaced by the .bbl file content."""
        work_dir = self._work_dir()
        main = self._copy_fixtures(work_dir, include_bbl=True)
        result = DocumentTeX.make_flat(main, output_tex=work_dir / "flat.tex")
        self.assertNotIn(r"\bibliography{refs}", result)
        self.assertIn(r"\begin{thebibliography}", result)

    def test_bibliography_kept_when_no_bbl(self):
        """\\bibliography{} must be left intact when no .bbl file exists."""
        work_dir = self._work_dir()
        main = self._copy_fixtures(work_dir, include_bbl=False)
        result = DocumentTeX.make_flat(main, output_tex=work_dir / "flat.tex")
        self.assertIn(r"\bibliography{refs}", result)

    # -------------------------------------------------------------------
    # Output file
    # -------------------------------------------------------------------

    def test_output_file_is_written(self):
        """The output path must exist on disk after make_flat."""
        work_dir = self._work_dir()
        main = self._copy_fixtures(work_dir)
        out = work_dir / "flat.tex"
        DocumentTeX.make_flat(main, output_tex=out)
        self.assertTrue(out.exists())

    def test_inplace_write_when_output_tex_is_none(self):
        """When output_tex is None, the source file must be overwritten."""
        work_dir = self._work_dir()
        main = self._copy_fixtures(work_dir)
        original_content = main.read_text(encoding="utf-8")
        DocumentTeX.make_flat(main, output_tex=None)
        new_content = main.read_text(encoding="utf-8")
        self.assertNotEqual(original_content, new_content)
        self.assertNotIn(r"\input{tex_section}", new_content)

    def test_output_file_content_matches_return_value(self):
        """Returned string and written file content must be identical."""
        work_dir = self._work_dir()
        main = self._copy_fixtures(work_dir)
        out = work_dir / "flat.tex"
        result = DocumentTeX.make_flat(main, output_tex=out)
        self.assertEqual(result, out.read_text(encoding="utf-8"))


class TestToFlat(unittest.TestCase):
    """
    Tests for ``DocumentTeX.to_flat`` with ``compile_first=False``.
    ``to_pdf`` / ``latexmk`` is never invoked.
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        if RUN_BENCHMARKS:
            cls._tmp_root = OUTPUT_DIR / "tex" / "toflat"
            cls._tmp_root.mkdir(parents=True, exist_ok=True)
        else:
            cls._tmp_root = Path(tempfile.mkdtemp(prefix="losalamos_test_toflat_"))

    @classmethod
    def tearDownClass(cls):
        if not RUN_BENCHMARKS:
            shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def _work_dir(self):
        d = Path(self._tmp_root) / self._testMethodName
        d.mkdir(exist_ok=True)
        return d

    def _make_doc(self, work_dir):
        """Return a loaded DocumentTeX instance pointing at the copied tex_main.tex."""
        shutil.copy(TEX_DIR / "tex_main.tex", work_dir / "tex_main.tex")
        shutil.copy(TEX_DIR / "tex_section.tex", work_dir / "tex_section.tex")
        doc = DocumentTeX()
        doc.load_data(work_dir / "tex_main.tex")
        return doc

    # -------------------------------------------------------------------
    # Fragment guard
    # -------------------------------------------------------------------

    def test_to_flat_returns_none_for_fragment(self):
        """to_flat must return None silently for non-main files."""
        doc = DocumentTeX()
        doc.load_data(TEX_DIR / "tex_fragment.tex")
        result = doc.to_flat(compile_first=False)
        self.assertIsNone(result)

    # -------------------------------------------------------------------
    # Happy path
    # -------------------------------------------------------------------

    def test_to_flat_returns_string_for_main(self):
        """to_flat must return a str for a main file."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        result = doc.to_flat(compile_first=False)
        self.assertIsInstance(result, str)

    def test_to_flat_resolves_input(self):
        """to_flat must inline \\input{tex_section} content."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        result = doc.to_flat(compile_first=False)
        self.assertNotIn(r"\input{tex_section}", result)
        self.assertIn(r"\section{Methods}", result)

    def test_to_flat_writes_to_file_output(self):
        """When file_output is given, the file must exist on disk."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        out = work_dir / "output_flat.tex"
        doc.to_flat(file_output=out, compile_first=False)
        self.assertTrue(out.exists())

    def test_to_flat_inplace_when_no_file_output(self):
        """When file_output is None, the source file must be overwritten."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        original = (work_dir / "tex_main.tex").read_text(encoding="utf-8")
        doc.to_flat(file_output=None, compile_first=False)
        new_content = (work_dir / "tex_main.tex").read_text(encoding="utf-8")
        self.assertNotEqual(original, new_content)


class TestSplitPreamble(unittest.TestCase):
    """
    Tests for ``DocumentTeX.split_preamble`` — structural splitting,
    custom names, output folder, and error handling.
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        if RUN_BENCHMARKS:
            cls._tmp_root = OUTPUT_DIR / "tex" / "split"
            cls._tmp_root.mkdir(parents=True, exist_ok=True)
        else:
            cls._tmp_root = Path(tempfile.mkdtemp(prefix="losalamos_test_split_"))

    @classmethod
    def tearDownClass(cls):
        if not RUN_BENCHMARKS:
            shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def _work_dir(self):
        d = Path(self._tmp_root) / self._testMethodName
        d.mkdir(exist_ok=True)
        return d

    def _copy_main(self, work_dir, name="tex_main.tex"):
        """Copy tex_main.tex into work_dir under the given filename."""
        src = work_dir / name
        shutil.copy(TEX_DIR / "tex_main.tex", src)
        return src

    # -------------------------------------------------------------------
    # Return value
    # -------------------------------------------------------------------

    def test_returns_tuple_of_two_paths(self):
        """split_preamble must return a 2-tuple of Path objects."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        result = DocumentTeX.split_preamble(src, output_folder=out_dir)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], Path)
        self.assertIsInstance(result[1], Path)

    def test_returned_paths_exist(self):
        """Both returned paths must exist on the filesystem."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        preamble_path, main_path = DocumentTeX.split_preamble(
            src, output_folder=out_dir
        )
        self.assertTrue(preamble_path.exists())
        self.assertTrue(main_path.exists())

    # -------------------------------------------------------------------
    # Default names
    # -------------------------------------------------------------------

    def test_default_output_names(self):
        """Default output stems must be 'preamble' and 'main'."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        preamble_path, main_path = DocumentTeX.split_preamble(
            src, output_folder=out_dir
        )
        self.assertEqual(preamble_path.stem, "preamble")
        self.assertEqual(main_path.stem, "main")

    # -------------------------------------------------------------------
    # Custom names
    # -------------------------------------------------------------------

    def test_custom_preamble_name(self):
        """Custom preamble_name must be reflected in the output filename."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        preamble_path, _ = DocumentTeX.split_preamble(
            src, preamble_name="header", output_folder=out_dir
        )
        self.assertEqual(preamble_path.stem, "header")

    def test_custom_main_name(self):
        """Custom main_name must be reflected in the output filename."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        _, main_path = DocumentTeX.split_preamble(
            src, main_name="document", output_folder=out_dir
        )
        self.assertEqual(main_path.stem, "document")

    # -------------------------------------------------------------------
    # Preamble content
    # -------------------------------------------------------------------

    def test_preamble_contains_usepackage(self):
        """preamble.tex must contain the \\usepackage lines from the source."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        preamble_path, _ = DocumentTeX.split_preamble(src, output_folder=out_dir)
        content = preamble_path.read_text(encoding="utf-8")
        self.assertIn(r"\usepackage", content)

    def test_preamble_does_not_contain_documentclass(self):
        """preamble.tex must not contain \\documentclass."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        preamble_path, _ = DocumentTeX.split_preamble(src, output_folder=out_dir)
        content = preamble_path.read_text(encoding="utf-8")
        self.assertNotIn(r"\documentclass", content)

    def test_preamble_does_not_contain_begin_document(self):
        """preamble.tex must not contain \\begin{document}."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        preamble_path, _ = DocumentTeX.split_preamble(src, output_folder=out_dir)
        content = preamble_path.read_text(encoding="utf-8")
        self.assertNotIn(r"\begin{document}", content)

    # -------------------------------------------------------------------
    # Main stub content
    # -------------------------------------------------------------------

    def test_main_retains_documentclass(self):
        """main.tex must retain the \\documentclass line."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        _, main_path = DocumentTeX.split_preamble(src, output_folder=out_dir)
        content = main_path.read_text(encoding="utf-8")
        self.assertIn(r"\documentclass", content)

    def test_main_contains_input_preamble(self):
        """main.tex must contain \\input{preamble} in place of the preamble block."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        _, main_path = DocumentTeX.split_preamble(src, output_folder=out_dir)
        content = main_path.read_text(encoding="utf-8")
        self.assertIn(r"\input{preamble}", content)

    def test_main_input_uses_custom_preamble_name(self):
        """\\input{} in main must use the custom preamble_name argument."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        _, main_path = DocumentTeX.split_preamble(
            src, preamble_name="header", output_folder=out_dir
        )
        content = main_path.read_text(encoding="utf-8")
        self.assertIn(r"\input{header}", content)

    def test_main_retains_begin_document(self):
        """main.tex must retain \\begin{document}."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        _, main_path = DocumentTeX.split_preamble(src, output_folder=out_dir)
        content = main_path.read_text(encoding="utf-8")
        self.assertIn(r"\begin{document}", content)

    def test_main_retains_end_document(self):
        """main.tex must retain \\end{document}."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        _, main_path = DocumentTeX.split_preamble(src, output_folder=out_dir)
        content = main_path.read_text(encoding="utf-8")
        self.assertIn(r"\end{document}", content)

    def test_main_does_not_contain_usepackage(self):
        """main.tex must not contain \\usepackage (moved to preamble)."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        _, main_path = DocumentTeX.split_preamble(src, output_folder=out_dir)
        content = main_path.read_text(encoding="utf-8")
        self.assertNotIn(r"\usepackage", content)

    def test_input_preamble_surrounded_by_blank_lines(self):
        """\\input{preamble} must be surrounded by blank lines in main.tex."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "split"
        _, main_path = DocumentTeX.split_preamble(src, output_folder=out_dir)
        content = main_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        idx = next(i for i, ln in enumerate(lines) if r"\input{preamble}" in ln)
        self.assertEqual(lines[idx - 1].strip(), "")
        self.assertEqual(lines[idx + 1].strip(), "")

    # -------------------------------------------------------------------
    # Custom output folder
    # -------------------------------------------------------------------

    def test_custom_output_folder_is_created(self):
        """split_preamble must create the output_folder if it does not exist."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir)
        out_dir = work_dir / "nested" / "split"
        self.assertFalse(out_dir.exists())
        DocumentTeX.split_preamble(src, output_folder=out_dir)
        self.assertTrue(out_dir.exists())

    def test_output_folder_default_is_input_parent(self):
        """When output_folder is None the files land next to the source."""
        work_dir = self._work_dir()
        # Use a name that won't collide with default output stems
        src = self._copy_main(work_dir, name="document.tex")
        preamble_path, main_path = DocumentTeX.split_preamble(src)
        self.assertEqual(preamble_path.parent, src.parent)
        self.assertEqual(main_path.parent, src.parent)

    # -------------------------------------------------------------------
    # Safety guard -- stem collision
    # -------------------------------------------------------------------

    def test_raises_on_stem_collision_with_preamble_name(self):
        """ValueError when input stem matches preamble_name in the same folder."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir, name="preamble.tex")
        with self.assertRaises(ValueError):
            DocumentTeX.split_preamble(src)  # default preamble_name="preamble"

    def test_raises_on_stem_collision_with_main_name(self):
        """ValueError when input stem matches main_name in the same folder."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir, name="main.tex")
        with self.assertRaises(ValueError):
            DocumentTeX.split_preamble(src)  # default main_name="main"

    def test_no_collision_when_different_output_folder(self):
        """No ValueError when stems match but output_folder differs from input parent."""
        work_dir = self._work_dir()
        src = self._copy_main(work_dir, name="preamble.tex")
        out_dir = work_dir / "split"
        preamble_path, main_path = DocumentTeX.split_preamble(
            src, output_folder=out_dir
        )
        self.assertTrue(preamble_path.exists())
        self.assertTrue(main_path.exists())

    # -------------------------------------------------------------------
    # Error handling -- malformed input
    # -------------------------------------------------------------------

    def test_raises_when_no_documentclass(self):
        """ValueError when the input file has no \\documentclass."""
        work_dir = self._work_dir()
        src = work_dir / "tex_fragment.tex"
        shutil.copy(TEX_DIR / "tex_fragment.tex", src)
        out_dir = work_dir / "split"
        with self.assertRaises(ValueError):
            DocumentTeX.split_preamble(src, output_folder=out_dir)

    def test_raises_when_no_begin_document(self):
        """ValueError when the input file has no \\begin{document}."""
        work_dir = self._work_dir()
        src = work_dir / "incomplete.tex"
        src.write_text(
            r"\documentclass{article}" + "\n" + r"\usepackage{amsmath}" + "\n",
            encoding="utf-8",
        )
        out_dir = work_dir / "split"
        with self.assertRaises(ValueError):
            DocumentTeX.split_preamble(src, output_folder=out_dir)

    def test_comment_documentclass_not_detected(self):
        """A commented-out \\documentclass must not be detected as a main file."""
        work_dir = self._work_dir()
        src = work_dir / "commented.tex"
        src.write_text(
            "% \\documentclass{article}\n" "\\usepackage{amsmath}\n",
            encoding="utf-8",
        )
        out_dir = work_dir / "split"
        with self.assertRaises(ValueError):
            DocumentTeX.split_preamble(src, output_folder=out_dir)


class TestLintParagraphs(unittest.TestCase):
    """
    Tests for ``DocumentTeX.lint_paragraphs`` — wrapped prose joining.
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        if RUN_BENCHMARKS:
            cls._tmp_root = OUTPUT_DIR / "tex" / "lintpar"
            cls._tmp_root.mkdir(parents=True, exist_ok=True)
        else:
            cls._tmp_root = Path(tempfile.mkdtemp(prefix="losalamos_test_lintpar_"))

    @classmethod
    def tearDownClass(cls):
        if not RUN_BENCHMARKS:
            shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def _work_dir(self):
        d = Path(self._tmp_root) / self._testMethodName
        d.mkdir(exist_ok=True)
        return d

    def _run(self, body_lines, work_dir=None):
        """
        Wrap body_lines in a minimal document, run lint_paragraphs inplace,
        return the body of the result (lines between \\begin/\\end{document}).
        """
        if work_dir is None:
            work_dir = self._work_dir()
        content = (
            "\\documentclass{article}\n"
            "\\begin{document}\n" + "\n".join(body_lines) + "\n\\end{document}\n"
        )
        src = work_dir / "doc.tex"
        src.write_text(content, encoding="utf-8")
        DocumentTeX.lint_paragraphs(src)
        result = src.read_text(encoding="utf-8")
        start = result.index("\\begin{document}\n") + len("\\begin{document}\n")
        end = result.index("\\end{document}")
        return result[start:end]

    # -------------------------------------------------------------------
    # Paragraph joining
    # -------------------------------------------------------------------

    def test_wrapped_lines_joined_into_one(self):
        """Consecutive non-blank prose lines must be joined into a single line."""
        body = self._run(
            [
                "This is the first line",
                "of a wrapped paragraph.",
            ]
        )
        self.assertIn("This is the first line of a wrapped paragraph.", body)

    def test_blank_line_separates_paragraphs(self):
        """A blank line must produce two separate output paragraphs."""
        body = self._run(
            [
                "First paragraph.",
                "",
                "Second paragraph.",
            ]
        )
        lines = [ln for ln in body.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 2)

    def test_preamble_passed_through_unchanged(self):
        """Lines before \\begin{document} must not be modified."""
        work_dir = self._work_dir()
        content = (
            "\\documentclass{article}\n"
            "\\newcommand{\\R}{\\mathbb{R}}\n"
            "\\begin{document}\n"
            "Body.\n"
            "\\end{document}\n"
        )
        src = work_dir / "doc.tex"
        src.write_text(content, encoding="utf-8")
        DocumentTeX.lint_paragraphs(src)
        result = src.read_text(encoding="utf-8")
        self.assertIn("\\newcommand{\\R}{\\mathbb{R}}", result)

    def test_equation_environment_not_reflowed(self):
        """Lines inside an equation environment must not be joined."""
        body = self._run(
            [
                "\\begin{equation}",
                "  E = mc^2",
                "\\end{equation}",
            ]
        )
        self.assertIn("  E = mc^2", body)

    def test_returns_output_path(self):
        """lint_paragraphs must return a Path."""
        work_dir = self._work_dir()
        src = work_dir / "doc.tex"
        src.write_text(
            "\\documentclass{article}\n\\begin{document}\nHello.\n\\end{document}\n",
            encoding="utf-8",
        )
        result = DocumentTeX.lint_paragraphs(src)
        self.assertIsInstance(result, Path)


class TestLintDecorationsRemove(unittest.TestCase):
    """
    Tests for ``DocumentTeX.lint_decorations_remove`` — decoration comment
    stripping.
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        if RUN_BENCHMARKS:
            cls._tmp_root = OUTPUT_DIR / "tex" / "lintdecr"
            cls._tmp_root.mkdir(parents=True, exist_ok=True)
        else:
            cls._tmp_root = Path(tempfile.mkdtemp(prefix="losalamos_test_lintdecr_"))

    @classmethod
    def tearDownClass(cls):
        if not RUN_BENCHMARKS:
            shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def _work_dir(self):
        d = Path(self._tmp_root) / self._testMethodName
        d.mkdir(exist_ok=True)
        return d

    def _make_tex(self, lines, work_dir):
        src = work_dir / "doc.tex"
        src.write_text("\n".join(lines), encoding="utf-8")
        return src

    # -------------------------------------------------------------------
    # Decoration removal
    # -------------------------------------------------------------------

    def test_ruler_comment_is_removed(self):
        """A comment-only line of dashes must be stripped."""
        work_dir = self._work_dir()
        src = self._make_tex(["% -------------------", "Some prose."], work_dir)
        DocumentTeX.lint_decorations_remove(src)
        result = src.read_text(encoding="utf-8")
        self.assertNotIn("% -------------------", result)
        self.assertIn("Some prose.", result)

    def test_real_comment_is_kept(self):
        """A comment containing letters must be preserved."""
        work_dir = self._work_dir()
        src = self._make_tex(["% This is a real comment.", "Prose."], work_dir)
        DocumentTeX.lint_decorations_remove(src)
        result = src.read_text(encoding="utf-8")
        self.assertIn("% This is a real comment.", result)

    def test_trailing_decoration_stripped_from_prose(self):
        """A trailing decoration comment on a prose line must be removed."""
        work_dir = self._work_dir()
        src = self._make_tex([r"\newcommand{\foo}{bar} % ==="], work_dir)
        DocumentTeX.lint_decorations_remove(src)
        result = src.read_text(encoding="utf-8")
        self.assertNotIn("% ===", result)
        self.assertIn(r"\newcommand{\foo}{bar}", result)

    def test_except_chars_preserves_matching_ruler(self):
        """A ruler whose character is in except_chars must be kept."""
        work_dir = self._work_dir()
        src = self._make_tex(["% ################", "Prose."], work_dir)
        DocumentTeX.lint_decorations_remove(src, except_chars=["#"])
        result = src.read_text(encoding="utf-8")
        self.assertIn("% ################", result)

    def test_returns_path(self):
        """lint_decorations_remove must return a Path."""
        work_dir = self._work_dir()
        src = self._make_tex(["Prose."], work_dir)
        result = DocumentTeX.lint_decorations_remove(src)
        self.assertIsInstance(result, Path)


class TestLintDecorationsAdd(unittest.TestCase):
    """
    Tests for ``DocumentTeX.lint_decorations_add`` — ruler injection above
    section headings.
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        if RUN_BENCHMARKS:
            cls._tmp_root = OUTPUT_DIR / "tex" / "lintdeca"
            cls._tmp_root.mkdir(parents=True, exist_ok=True)
        else:
            cls._tmp_root = Path(tempfile.mkdtemp(prefix="losalamos_test_lintdeca_"))

    @classmethod
    def tearDownClass(cls):
        if not RUN_BENCHMARKS:
            shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def _work_dir(self):
        d = Path(self._tmp_root) / self._testMethodName
        d.mkdir(exist_ok=True)
        return d

    def _run(self, body_lines, **kwargs):
        work_dir = self._work_dir()
        content = (
            "\\documentclass{article}\n"
            "\\begin{document}\n" + "\n".join(body_lines) + "\n\\end{document}\n"
        )
        src = work_dir / "doc.tex"
        src.write_text(content, encoding="utf-8")
        DocumentTeX.lint_decorations_add(src, **kwargs)
        return src.read_text(encoding="utf-8")

    # -------------------------------------------------------------------
    # Ruler injection
    # -------------------------------------------------------------------

    def test_ruler_injected_before_section(self):
        """A ruler must appear on the line immediately before \\section."""
        result = self._run(["\\section{Introduction}", "Body."])
        lines = result.splitlines()
        idx = next(i for i, ln in enumerate(lines) if "\\section{Introduction}" in ln)
        self.assertIn("*", lines[idx - 1])  # default section char is '*'

    def test_ruler_not_duplicated_on_rerun(self):
        """Running lint_decorations_add twice must not duplicate the ruler."""
        work_dir = self._work_dir()
        content = (
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "\\section{Intro}\n"
            "Body.\n"
            "\\end{document}\n"
        )
        src = work_dir / "doc.tex"
        src.write_text(content, encoding="utf-8")
        DocumentTeX.lint_decorations_add(src)
        DocumentTeX.lint_decorations_add(src)
        result = src.read_text(encoding="utf-8")
        lines = result.splitlines()
        ruler_count = sum(
            1
            for ln in lines
            if ln.strip().startswith("% ")
            and "\\section" not in ln
            and set(ln.strip()[2:]) <= {"*"}
        )
        self.assertEqual(ruler_count, 1)

    def test_custom_ruler_char(self):
        """A custom ruler char must appear in the injected ruler."""
        result = self._run(
            ["\\section{Methods}", "Body."],
            ruler_chars=["#", "~"],
        )
        lines = result.splitlines()
        idx = next(i for i, ln in enumerate(lines) if "\\section{Methods}" in ln)
        self.assertIn("~", lines[idx - 1])

    def test_raises_on_zero_ruler_len(self):
        """ruler_len < 1 must raise ValueError."""
        work_dir = self._work_dir()
        src = work_dir / "doc.tex"
        src.write_text(
            "\\documentclass{article}\n\\begin{document}\n\\end{document}\n",
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            DocumentTeX.lint_decorations_add(src, ruler_len=0)

    def test_returns_path(self):
        """lint_decorations_add must return a Path."""
        work_dir = self._work_dir()
        src = work_dir / "doc.tex"
        src.write_text(
            "\\documentclass{article}\n\\begin{document}\nBody.\n\\end{document}\n",
            encoding="utf-8",
        )
        result = DocumentTeX.lint_decorations_add(src)
        self.assertIsInstance(result, Path)


class TestLintBlankLines(unittest.TestCase):
    """
    Tests for ``DocumentTeX.lint_blank_lines`` — blank-line normalisation.
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        if RUN_BENCHMARKS:
            cls._tmp_root = OUTPUT_DIR / "tex" / "lintbl"
            cls._tmp_root.mkdir(parents=True, exist_ok=True)
        else:
            cls._tmp_root = Path(tempfile.mkdtemp(prefix="losalamos_test_lintbl_"))

    @classmethod
    def tearDownClass(cls):
        if not RUN_BENCHMARKS:
            shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def _work_dir(self):
        d = Path(self._tmp_root) / self._testMethodName
        d.mkdir(exist_ok=True)
        return d

    def _run(self, body_lines):
        work_dir = self._work_dir()
        content = (
            "\\documentclass{article}\n"
            "\\begin{document}\n" + "\n".join(body_lines) + "\n\\end{document}\n"
        )
        src = work_dir / "doc.tex"
        src.write_text(content, encoding="utf-8")
        path, stats = DocumentTeX.lint_blank_lines(src)
        result = src.read_text(encoding="utf-8")
        start = result.index("\\begin{document}\n") + len("\\begin{document}\n")
        end = result.index("\\end{document}")
        return result[start:end], stats

    # -------------------------------------------------------------------
    # Blank-line collapsing
    # -------------------------------------------------------------------

    def test_multiple_blanks_collapsed_to_one(self):
        """Three consecutive blank lines in prose must collapse to one."""
        body, stats = self._run(
            [
                "Paragraph one.",
                "",
                "",
                "",
                "Paragraph two.",
            ]
        )
        lines = body.splitlines()
        consecutive_blanks = max(
            sum(1 for _ in g)
            for k, g in __import__("itertools").groupby(
                lines, key=lambda l: l.strip() == ""
            )
            if k
        )
        self.assertLessEqual(consecutive_blanks, 1)
        self.assertGreater(stats["collapsed"], 0)

    def test_single_blank_line_kept(self):
        """A single blank line must not be removed."""
        body, _ = self._run(
            [
                "Paragraph one.",
                "",
                "Paragraph two.",
            ]
        )
        self.assertIn("", body.splitlines())

    # -------------------------------------------------------------------
    # Return value
    # -------------------------------------------------------------------

    def test_returns_tuple(self):
        """lint_blank_lines must return a (Path, dict) tuple."""
        work_dir = self._work_dir()
        src = work_dir / "doc.tex"
        src.write_text(
            "\\documentclass{article}\n\\begin{document}\nBody.\n\\end{document}\n",
            encoding="utf-8",
        )
        result = DocumentTeX.lint_blank_lines(src)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], Path)
        self.assertIsInstance(result[1], dict)

    def test_stats_keys_present(self):
        """The stats dict must contain 'collapsed' and 'padded' keys."""
        work_dir = self._work_dir()
        src = work_dir / "doc.tex"
        src.write_text(
            "\\documentclass{article}\n\\begin{document}\nBody.\n\\end{document}\n",
            encoding="utf-8",
        )
        _, stats = DocumentTeX.lint_blank_lines(src)
        self.assertIn("collapsed", stats)
        self.assertIn("padded", stats)


class TestExport(unittest.TestCase):
    """
    Tests for ``DocumentTeX.export`` — plain copy, flatten, and split modes.
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        if RUN_BENCHMARKS:
            cls._tmp_root = OUTPUT_DIR / "tex" / "export"
            cls._tmp_root.mkdir(parents=True, exist_ok=True)
        else:
            cls._tmp_root = Path(tempfile.mkdtemp(prefix="losalamos_test_export_"))

    @classmethod
    def tearDownClass(cls):
        if not RUN_BENCHMARKS:
            shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def _work_dir(self):
        d = Path(self._tmp_root) / self._testMethodName
        d.mkdir(exist_ok=True)
        return d

    def _make_doc(self, work_dir):
        """Return a loaded DocumentTeX instance pointing at the copied tex_main.tex."""
        shutil.copy(TEX_DIR / "tex_main.tex", work_dir / "tex_main.tex")
        shutil.copy(TEX_DIR / "tex_section.tex", work_dir / "tex_section.tex")
        doc = DocumentTeX()
        doc.load_data(work_dir / "tex_main.tex")
        return doc

    # -------------------------------------------------------------------
    # Return value
    # -------------------------------------------------------------------

    def test_returns_path(self):
        """export must return a Path."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        result = doc.export(work_dir, "out_plain")
        self.assertIsInstance(result, Path)

    def test_returns_absolute_path(self):
        """The returned path must be absolute."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        result = doc.export(work_dir, "out_abs")
        self.assertTrue(result.is_absolute())

    def test_returns_correct_path(self):
        """The returned path must equal folder_root/name."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        result = doc.export(work_dir, "out_correct")
        self.assertEqual(result, work_dir / "out_correct")

    # -------------------------------------------------------------------
    # Plain mode (flatten=False, split=False)
    # -------------------------------------------------------------------

    def test_plain_creates_export_folder(self):
        """Plain export must create the folder_root/name directory."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        export_dir = doc.export(work_dir, "out_plain_dir")
        self.assertTrue(export_dir.is_dir())

    def test_plain_copies_source_file(self):
        """Plain export must copy the source file retaining its original name."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        export_dir = doc.export(work_dir, "out_plain_copy")
        self.assertTrue((export_dir / "tex_main.tex").exists())

    def test_plain_source_file_content_unchanged(self):
        """Plain export must copy the file content verbatim."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        original = (work_dir / "tex_main.tex").read_text(encoding="utf-8")
        export_dir = doc.export(work_dir, "out_plain_content")
        exported = (export_dir / "tex_main.tex").read_text(encoding="utf-8")
        self.assertEqual(original, exported)

    def test_plain_retains_input_directives(self):
        """Plain export must not resolve \\input directives."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        export_dir = doc.export(work_dir, "out_plain_input")
        content = (export_dir / "tex_main.tex").read_text(encoding="utf-8")
        self.assertIn(r"\input{tex_section}", content)

    # -------------------------------------------------------------------
    # Flatten mode (flatten=True, split=False)
    # -------------------------------------------------------------------

    def test_flatten_creates_export_folder(self):
        """Flatten export must create the folder_root/name directory."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        export_dir = doc.export(work_dir, "out_flat_dir", flatten=True)
        self.assertTrue(export_dir.is_dir())

    def test_flatten_output_named_after_export_folder(self):
        """Flatten export must produce <name>.tex inside the export folder."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        export_dir = doc.export(work_dir, "out_flat_name", flatten=True)
        self.assertTrue((export_dir / "out_flat_name.tex").exists())

    def test_flatten_resolves_input_directives(self):
        """Flatten export must inline \\input{tex_section} content."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        export_dir = doc.export(work_dir, "out_flat_resolve", flatten=True)
        content = (export_dir / "out_flat_resolve.tex").read_text(encoding="utf-8")
        self.assertNotIn(r"\input{tex_section}", content)
        self.assertIn(r"\section{Methods}", content)

    def test_flatten_only_one_tex_file_produced(self):
        """Flatten export must produce exactly one .tex file."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        export_dir = doc.export(work_dir, "out_flat_single", flatten=True)
        tex_files = list(export_dir.glob("*.tex"))
        self.assertEqual(len(tex_files), 1)

    # -------------------------------------------------------------------
    # Split mode (split=True)
    # -------------------------------------------------------------------

    def test_split_creates_export_folder(self):
        """Split export must create the folder_root/name directory."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        export_dir = doc.export(work_dir, "out_split_dir", split=True)
        self.assertTrue(export_dir.is_dir())

    def test_split_produces_preamble_and_main(self):
        """Split export must produce preamble.tex and main.tex."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        export_dir = doc.export(work_dir, "out_split_files", split=True)
        self.assertTrue((export_dir / "preamble.tex").exists())
        self.assertTrue((export_dir / "main.tex").exists())

    def test_split_no_temp_flat_file_left(self):
        """Split export must not leave the intermediate flat file behind."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        export_dir = doc.export(work_dir, "out_split_cleanup", split=True)
        leftover = list(export_dir.glob("_*_flat.tex"))
        self.assertEqual(len(leftover), 0)

    def test_split_only_two_tex_files_produced(self):
        """Split export must produce exactly two .tex files."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        export_dir = doc.export(work_dir, "out_split_count", split=True)
        tex_files = list(export_dir.glob("*.tex"))
        self.assertEqual(len(tex_files), 2)

    def test_split_main_contains_input_preamble(self):
        """main.tex produced by split export must contain \\input{preamble}."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        export_dir = doc.export(work_dir, "out_split_main", split=True)
        content = (export_dir / "main.tex").read_text(encoding="utf-8")
        self.assertIn(r"\input{preamble}", content)

    def test_split_preamble_contains_usepackage(self):
        """preamble.tex produced by split export must contain \\usepackage."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        export_dir = doc.export(work_dir, "out_split_preamble", split=True)
        content = (export_dir / "preamble.tex").read_text(encoding="utf-8")
        self.assertIn(r"\usepackage", content)

    # -------------------------------------------------------------------
    # Error handling
    # -------------------------------------------------------------------

    def test_raises_runtime_error_for_fragment(self):
        """export must raise RuntimeError when is_main is False."""
        doc = DocumentTeX()
        doc.load_data(TEX_DIR / "tex_fragment.tex")
        work_dir = self._work_dir()
        with self.assertRaises(RuntimeError):
            doc.export(work_dir, "out_fragment")

    def test_raises_file_exists_error_if_folder_exists(self):
        """export must raise FileExistsError if the export folder already exists."""
        work_dir = self._work_dir()
        doc = self._make_doc(work_dir)
        existing = work_dir / "out_exists"
        existing.mkdir()
        with self.assertRaises(FileExistsError):
            doc.export(work_dir, "out_exists")


# ***********************************************************************
# SCRIPT
# ***********************************************************************

if __name__ == "__main__":
    unittest.main()
