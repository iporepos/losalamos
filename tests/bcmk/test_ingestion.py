# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short script description (1-3 sentences)}
todo docstring

"""
import glob
import pprint

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import unittest
from pathlib import Path
import tempfile

# ... {develop}

# External imports
# =======================================================================

# ... {develop}

# Project-level imports
# =======================================================================
from tests.conftest import *
from losalamos.utils import *
from losalamos.ingestion import Ingester

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# FUNCTIONS
# ***********************************************************************

# CLASSES
# ***********************************************************************


@unittest.skipUnless(RUN_BENCHMARKS, reason="skipping benchmarks")
class BCMKTestIngesterArticle(unittest.TestCase):

    OBJECT = Ingester
    LABEL = "ingester"

    @classmethod
    def setUpClass(cls):
        """
        Prepare large datasets and output folders
        """
        cls.output_dir = OUTPUT_DIR / "library/papers"
        cls.output_dir.mkdir(exist_ok=True)

        cls.data_folder = DATA_DIR / "incoming/article"

        folder = cls.data_folder / "climatology"
        ls = list(folder.glob("*.pdf"))
        cls.pdf_file_old = ls[0]

        folder = cls.data_folder / "hydrology"
        ls = list(folder.glob("*.pdf"))
        cls.pdf_file_new = ls[0]

    def setUp(self):
        """
        Runs before each test method
        """
        self.ingester = self.OBJECT(src=self.data_folder, dst=self.output_dir)
        return None

    def test_parse_bib(self):
        folder = self.data_folder / "climatology"
        ls = list(folder.glob("*.bib"))
        file_bib = ls[0]
        print(testmsg(f"parsing bib: {file_bib.name}"))
        self.assertTrue(file_bib.is_file())

        if file_bib.is_file():
            dc = self.ingester.parse_bib(file_parse=file_bib)
            print(testmsg("parsed:\n"))
            pprint.pp(dc)
            self.assertIsInstance(dc, dict)

    def _parse_pdf_metadata(self, file_pdf):

        print(testmsg(f"getting pdf metadata from: {file_pdf.name}"))
        self.assertTrue(file_pdf.is_file())

        if file_pdf.is_file():
            dc = self.ingester.parse_pdf_metadata(file_pdf)
            print(testmsg("parsed:\n"))
            pprint.pp(dc)
            self.assertIsInstance(dc, dict)

    def _parse_pdf_pages(self, file_pdf):

        print(testmsg(f"getting pdf pages from: {file_pdf.name}"))
        self.assertTrue(file_pdf.is_file())

        if file_pdf.is_file():
            s = self.ingester.parse_pdf_pages(file_parse=file_pdf, n_pages=1)
            print(testmsg("parsed:\n"))
            # pprint.pp(s)
            print(s)
            self.assertIsInstance(s, str)

    def test_pdfs(self):

        # metadata
        self._parse_pdf_metadata(file_pdf=self.pdf_file_old)
        self._parse_pdf_metadata(file_pdf=self.pdf_file_new)

        # pages
        self._parse_pdf_pages(file_pdf=self.pdf_file_old)
        self._parse_pdf_pages(file_pdf=self.pdf_file_new)

    def test_get_incoming_files(self):
        df = self.ingester.get_incoming_files()
        print("\n")
        print("Incoming files:\n")
        print(df.to_string())
        print("\n")

    def test_run(self):
        self.ingester.run()


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    unittest.main()

    # ... {develop}
