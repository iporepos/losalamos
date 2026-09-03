# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Benchmark tests for DocumentTeX that require real external tools.

These tests invoke latexmk and pdflatex directly and are therefore
excluded from the standard unit-test suite. Enable by setting the
environment variable RUN_BENCHMARKS=1.
"""

# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import shutil
import tempfile
import unittest
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================

# ... {develop}

# Project-level imports
# =======================================================================
from tests.conftest import *
from losalamos.documents import DocumentTeX, LatexCompileError

# ... {develop}


# CONSTANTS
# ***********************************************************************


# FUNCTIONS
# ***********************************************************************

# CLASSES
# ***********************************************************************


@unittest.skipUnless(RUN_BENCHMARKS, reason="skipping benchmarks")
class BCMKTestDocumentTeXLatex(unittest.TestCase):
    """
    to_pdf() raises LatexCompileError when latexmk actually fails.

    Uses a .tex file that references a nonexistent document class, which
    causes pdflatex to abort immediately. A minimal latexmkrc forces
    ``-interaction=nonstopmode`` so the compile exits without blocking.
    """

    def setUp(self):
        self.tmp_root = Path(tempfile.mkdtemp(prefix="latex_err_real_"))
        main = self.tmp_root / "main.tex"
        main.write_text(
            "\\documentclass{nonexistentclassfortesting}\n"
            "\\begin{document}\\end{document}\n"
        )
        (self.tmp_root / "latexmkrc").write_text(
            "$pdflatex = 'pdflatex -interaction=nonstopmode %O %S';\n"
        )
        self.doc = DocumentTeX(name="RealErrDoc", alias="RED")
        self.doc.load_data(file_data=main)

    def tearDown(self):
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_compile_failure_raises_latex_compile_error(self):
        with self.assertRaises(LatexCompileError):
            self.doc.to_pdf()

    def test_compile_failure_returncode_nonzero(self):
        try:
            self.doc.to_pdf()
        except LatexCompileError as exc:
            self.assertNotEqual(exc.returncode, 0)

    def test_compile_failure_source_is_tex_file(self):
        try:
            self.doc.to_pdf()
        except LatexCompileError as exc:
            self.assertEqual(exc.source, self.doc.file_data.absolute())

    def test_compile_failure_log_path_set(self):
        try:
            self.doc.to_pdf()
        except LatexCompileError as exc:
            self.assertIsNotNone(exc.log_path)
            self.assertEqual(exc.log_path.suffix, ".log")


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":
    unittest.main()
