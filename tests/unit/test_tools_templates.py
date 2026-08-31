# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for ``losalamos.tools.templates``

todo docstring

Features
--------
 - describre

Overview
--------


Examples
--------
From the terminal, run:

.. code-block:: bash

    python ./tests/unit/test_tools_templates.py


"""
import glob
import os

# ***********************************************************************
# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import shutil, sys
import tempfile
import unittest
from pathlib import Path
import subprocess

# External imports
# =======================================================================
import pandas as pd

# Project-level imports
# =======================================================================
from tests.conftest import OUTPUT_DIR

# ***********************************************************************
# CLASSES
# ***********************************************************************


class TestToolsTemplates(unittest.TestCase):
    # -------------------------------------------------------------------
    # Setup / teardown
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests.
        """
        cls._tmp_root = tempfile.mkdtemp(prefix="losalamos_test_tools_templates_")

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
        self.notes_dir = self.base_dir / "notes"
        os.makedirs(self.notes_dir, exist_ok=True)

    # -------------------------------------------------------------------
    # run tool
    # -------------------------------------------------------------------
    def test_tool(self):

        # set command
        # ---------------------------------------------------------------
        cmd = [
            sys.executable,
            "-m",
            "losalamos.tools.update_templates",
            # arguments
            "--notes",
            self.notes_dir,
        ]

        # run command
        # ---------------------------------------------------------------
        subprocess.run(cmd)

        # develop assertions
        # ---------------------------------------------------------------

        ls_notes = os.listdir(self.notes_dir)
        # self.assertTrue(len(ls_notes) > 0)


# ***********************************************************************
# SCRIPT
# ***********************************************************************

if __name__ == "__main__":
    unittest.main()
