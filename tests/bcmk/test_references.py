# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short script description (1-3 sentences)}
todo docstring

"""
import pprint
import shutil

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
from losalamos.references import Reference, RefArticle

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# FUNCTIONS
# ***********************************************************************

# CLASSES
# ***********************************************************************


class BCMKTestReference(unittest.TestCase):

    OBJECT = Reference
    LABEL = "ref"

    @classmethod
    def setUpClass(cls):
        """
        Prepare large datasets and output folders
        """
        if os.getenv("RUN_BENCHMARKS") == "1":
            cls.output_dir = OUTPUT_DIR / "references"
            cls.output_dir.mkdir(exist_ok=True)
        else:
            cls.output_dir = Path(tempfile.mkdtemp(prefix="losalamos_test_references_"))

        cls.data_file = DATA_DIR / "ref_article.bib"

        print(testmsg(f"references :: folder = {cls.output_dir}"))
        print(testmsg(f"references :: bib = {cls.data_file}"))

    @classmethod
    def tearDownClass(cls):
        # cleanup local temp dirs
        if os.getenv("RUN_BENCHMARKS") == "0":
            shutil.rmtree(cls.output_dir)

    def setUp(self):
        """
        Runs before each test method
        """
        self.ref = self.OBJECT()
        self.ref.load_data(file_data=self.data_file)

        return None

    def test_data(self):
        pprint.pp(self.ref.data)
        self.assertIsInstance(self.ref.data, dict)

    def test_save(self):
        dst_file = self.output_dir / "save.bib"
        shutil.copy(src=self.ref.file_data, dst=dst_file)

        new_ref = self.OBJECT()
        new_ref.load_data(file_data=dst_file)
        new_ref.data["year"] = "1968"
        new_ref.save()

        ls = Reference.parse_bib(dst_file)
        dc = ls[0]
        yr = dc["year"]
        pprint.pp(dc)
        self.assertEqual(int(yr), 1968)

    def test_keys(self):

        ls = list(self.ref.CORE_FIELDS.keys())
        if self.ref.SPECIFIC_FIELDS is not None:
            ls = ls[:] + list(self.ref.SPECIFIC_FIELDS.keys())

        ls2 = list(self.ref.data.keys())

        ls.sort()
        ls2.sort()

        self.assertListEqual(list1=ls, list2=ls2)

    def test_parse_bib(self):
        ls = self.ref.parse_bib(self.ref.file_data)
        self.assertIsInstance(ls[0], dict)

    def test_to_bib(self):
        ts = get_timestamp(milliseconds=True)
        output = self.output_dir / f"{self.LABEL}_{ts}.bib"
        self.ref.to_bib(output=output)

        self.assertTrue(output.is_file())

    def test_harmonize_abs(self):
        print(self.ref.data["abstract"])
        self.assertTrue(True)

    def test_standardize(self):
        ls = self.ref.parse_bib(self.ref.file_data)
        dc = ls[0]

        print("\n\n")
        pprint.pp(dc)
        print("\n\n")
        pprint.pp(self.ref.data)
        self.assertTrue(True)

    def test_get_str_bib(self):
        s = self.ref.get_str_bib()
        print("\n\n")
        print(s)
        print("\n\n")
        self.assertTrue(True)

    def test_std_author(self):
        s = self.ref.standardize_author(bib_dict=self.ref.data)
        print("\n\n")
        print(f"Source:\n\t{self.ref.data['author']}")
        print(f"Standard:\n\t{s}")
        print("\n\n")
        self.assertTrue(True)

    def test_cite_line(self):
        ls = ["plain", "html", "md", "tex"]
        print("\n\n")
        for mode in ls:
            s1 = self.ref.cite_line(
                bib_dict=self.ref.data, text_format=mode, embed_link=True
            )
            print(s1)
        print("\n\n")
        self.assertTrue(True)

    def test_cite_full(self):
        pprint.pp(self.ref.data)
        ls = ["plain", "html", "md", "tex"]
        ls2 = ["apa", "mla", "chicago", "harvard", "vancouver", "abnt"]
        print("\n\n")
        for mode in ls:
            for style in ls2:
                s1 = self.ref.cite_full(
                    bib_dict=self.ref.data,
                    style=style,
                    text_format=mode,
                )
                print(f"\n{mode} {style}: \n\t")
                print(s1)
            print("")
        print("\n\n")
        self.assertTrue(True)


class BCMKTestArticle(BCMKTestReference):

    OBJECT = RefArticle
    LABEL = "article"


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    unittest.main()

    # ... {develop}
