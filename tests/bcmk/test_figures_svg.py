# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short script description (1-3 sentences)}
todo docstring

"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import os
import shutil
import unittest
import tempfile
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
from PIL import Image

# ... {develop}

# Project-level imports
# =======================================================================
from tests.conftest import *
from losalamos.utils import *
from losalamos.figures import FigureSVG

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# FUNCTIONS
# ***********************************************************************

# CLASSES
# ***********************************************************************


@unittest.skipUnless(RUN_BENCHMARKS, reason="skipping benchmarks")
class BCMKTestFigureSVG(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare large datasets and output folders
        """
        cls.output_dir = OUTPUT_DIR
        cls.src_data_file = DATA_DIR / "drawing_01.svg"

        # make a temporary copy
        cls.data_file = make_local_tempfile(cls.src_data_file)

        print(testmsg(f"figures :: folder = {cls.output_dir}"))
        print(testmsg(f"figures :: svg = {cls.data_file}"))

    def setUp(self):
        """
        Runs before each test method
        """
        self.svg = FigureSVG()
        self.svg.load_data(file_data=self.data_file)

        # make sure all layers are shown
        ls = self.svg.get_layers()
        self.svg.show_layers(labels=ls, inclusive=True)

        return None

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.data_file)

    def test_init(self):
        self.assertIsInstance(self.svg, FigureSVG)
        print(testmsg("init check passed"))

    def test_to_file(self):
        file_output = OUTPUT_DIR / "test_to_file.png"
        self.svg.to_image(file_output=file_output)

        # Integrity: Does the file exist?
        assert file_output.exists(), f"Output file {file_output} was not created."
        print(testmsg("tofile output check passed"))

    def test_to_file_hide(self):

        file_output = OUTPUT_DIR / "test_to_file_hide.png"
        self.svg.to_image(file_output=file_output, hide_layers=["decorations", "frame"])

        # Integrity: Does the file exist?
        assert file_output.exists(), f"Output file {file_output} was not created."
        print(testmsg("hide output check passed"))

    def test_to_file_crop(self):

        file_output = OUTPUT_DIR / "test_to_file_crop.png"
        self.svg.to_image(
            file_output=file_output,
            hide_layers=["decorations"],
            show_layers=["main", "annotations"],
            crop_id="mainframe",
        )

        # Integrity: Does the file exist?
        assert file_output.exists(), f"Output file {file_output} was not created."
        print(testmsg("crop output check passed"))

    def test_change_color(self):

        file_name = "test_change_color"
        file_output_svg = OUTPUT_DIR / f"{file_name}.svg"
        file_output = OUTPUT_DIR / "test_change_color.png"

        dc = self.svg.get_layer_elements(label="main")
        self.svg.set_element_color(
            element=dc["rect234"]["element"],
            fill="#2BBFD6",
        )

        self.svg.export(
            folder=OUTPUT_DIR,
            filename=file_name,
        )

        # include image
        shutil.copy(DATA_DIR / "budyko.jpeg", OUTPUT_DIR / "budyko.jpeg")

        new_svg = FigureSVG()
        new_svg.load_data(file_output_svg)
        new_svg.to_image(file_output=file_output, crop_id="mainframe")

        # Integrity: Does the file exist?
        assert file_output.exists(), f"Output file {file_output} was not created."
        print(testmsg("color output check passed"))


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    unittest.main()

    # ... {develop}
