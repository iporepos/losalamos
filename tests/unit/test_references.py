# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for ``losalamos.references`` BibTeX parsing and serialization.

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
from losalamos.references import Reference
from tests.conftest import OUTPUT_DIR, RUN_BENCHMARKS

# ***********************************************************************
# CLASSES
# ***********************************************************************


class TestReferencePercent(unittest.TestCase):
    """
    Tests for ``%`` LaTeX escaping in ``losalamos.references.Reference``.
    ``self.data`` must hold raw text; only ``.bib`` output is escaped.
    """

    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        if RUN_BENCHMARKS:
            cls._tmp_root = OUTPUT_DIR / "references"
            cls._tmp_root.mkdir(parents=True, exist_ok=True)
        else:
            cls._tmp_root = Path(tempfile.mkdtemp(prefix="losalamos_test_refs_"))

        # source abstract mixes raw and already-escaped percents
        cls.file_bib = cls._tmp_root / "percent.bib"
        cls.file_bib.write_text(
            "@article{percent2020,\n"
            "  title = {Percent Test},\n"
            "  abstract = {Rose 43% and 12\\% fell},\n"
            "}\n",
            encoding="utf-8",
        )
        cls.expected = "Rose 43% and 12% fell"

    @classmethod
    def tearDownClass(cls):
        if not RUN_BENCHMARKS:
            shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def setUp(self):
        self.ref = Reference.get_by_entry(entry_type="article")
        self.ref.load_data(file_data=self.file_bib)

    # -------------------------------------------------------------------
    # tests
    # -------------------------------------------------------------------

    def test_parse_bib_unescapes_abstract(self):
        """parse_bib() returns the abstract without ``\\%`` escapes."""
        ls = Reference.parse_bib(file_parse=self.file_bib)
        self.assertEqual(ls[0]["abstract"], self.expected)

    def test_data_is_raw(self):
        """Loaded ``self.data`` keeps the abstract free of LaTeX escapes."""
        self.assertEqual(self.ref.data["abstract"], self.expected)

    def test_to_bib_escapes(self):
        """to_bib() writes every ``%`` in the abstract as ``\\%``."""
        file_out = self.ref.to_bib(output=self._tmp_root / "escaped.bib")
        text = file_out.read_text(encoding="utf-8")
        self.assertIn(r"Rose 43\% and 12\% fell", text)

    def test_roundtrip(self):
        """Writing and reloading a bib keeps ``self.data`` unchanged."""
        file_out = self.ref.to_bib(output=self._tmp_root / "roundtrip.bib")
        ref_new = Reference.get_by_entry(entry_type="article")
        ref_new.load_data(file_data=file_out)
        self.assertEqual(ref_new.data["abstract"], self.expected)


# SCRIPT
# ***********************************************************************

if __name__ == "__main__":
    unittest.main()
