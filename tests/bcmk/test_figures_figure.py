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
from losalamos.figures import Figure

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# FUNCTIONS
# ***********************************************************************

# CLASSES
# ***********************************************************************


class BCMKTestFigure(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare large datasets and output folders
        """
        if os.getenv("RUN_BENCHMARKS") == "1":
            cls.output_dir = OUTPUT_DIR
        else:
            cls.output_dir = Path(tempfile.mkdtemp(prefix="losalamos_test_figures_"))

        print(testmsg(f"figures :: folder = {cls.output_dir}"))

    def setUp(self):
        """
        Runs before each test method
        """
        self.fig = Figure()

        return None

    def test_init(self):
        self.assertIsInstance(self.fig, Figure)

    def test_scale_image(self):
        """
        Verifies that the image scaling process produces the expected output file
        and maintains valid image properties.
        """
        file_input = DATA_DIR / "budyko.jpeg"
        file_output = self.output_dir / "budyko scaled.jpeg"
        self.fig.scale_image(
            file_input=file_input, file_output=file_output, scale_factor=0.5, dpi=300
        )

        # Integrity: Does the file exist?
        assert file_output.exists(), f"Output file {file_output} was not created."
        print(testmsg("scaling output check passed"))

        # Logic: Load image to verify dimensions and format
        with Image.open(file_output) as img:
            # Verify Format
            assert img.format == "JPEG", f"Expected JPEG, got {img.format}"
            print(testmsg("scaling format check passed"))

            # Verify Scaling (Assuming original was e.g. 1000x1000)
            # We compare against the original's dimensions * scale_factor
            with Image.open(file_input) as original:
                expected_width = int(original.width * 0.5)
                expected_height = int(original.height * 0.5)

                assert (
                    img.width == expected_width
                ), f"Width mismatch: {img.width} != {expected_width}"
                assert (
                    img.height == expected_height
                ), f"Height mismatch: {img.height} != {expected_height}"
                print(testmsg("scaling size check passed"))

        # Verify DPI metadata
        with Image.open(file_output) as img:
            # img.info['dpi'] usually returns a tuple like (300, 300)
            output_dpi = img.info.get("dpi")

            self.assertIsNotNone(
                output_dpi, "DPI information is missing from the output image."
            )
            self.assertEqual(
                output_dpi[0], 300, f"Expected 300 DPI, but got {output_dpi[0]}"
            )
        print(testmsg("scaling dpi check passed"))

        print(testmsg("scaling passed"))
        return None

    def test_make_thumbnail_short(self):
        file_input = DATA_DIR / "horton.png"

        # fit mode
        file_output = self.output_dir / "horton thumbnail fit.jpeg"
        self.fig.make_thumbnail(
            file_input=file_input, file_output=file_output, mode="fit"
        )

        # Integrity: Does the file exist?
        assert file_output.exists(), f"Output file {file_output} was not created."
        print(testmsg("thumbnail output check passed"))

        # crop mode
        file_output = self.output_dir / "horton thumbnail crop.jpeg"
        self.fig.make_thumbnail(
            file_input=file_input, file_output=file_output, mode="crop"
        )

        # Integrity: Does the file exist?
        assert file_output.exists(), f"Output file {file_output} was not created."
        print(testmsg("thumbnail output check passed"))

        # crop mode 3:4
        file_output = self.output_dir / "horton thumbnail crop 3x4.jpeg"
        self.fig.make_thumbnail(
            file_input=file_input,
            file_output=file_output,
            mode="crop",
            figure_ratio=(3, 4),
        )

        # Integrity: Does the file exist?
        assert file_output.exists(), f"Output file {file_output} was not created."
        print(testmsg("thumbnail output check passed"))

    def test_image_to_jpg(self):
        file_input = DATA_DIR / "horton.png"
        file_output = self.output_dir / "horton converted.jpeg"

        Figure.image_to_jpeg(file_input=file_input, file_output=file_output)

        # Integrity: Does the file exist?
        assert file_output.exists(), f"Output file {file_output} was not created."
        print(testmsg("to jpg output check passed"))

        # Logic: Load image to verify format
        with Image.open(file_output) as img:
            # Verify Format
            assert img.format == "JPEG", f"Expected JPEG, got {img.format}"
            print(testmsg("to jpg format check passed"))


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    unittest.main()

    # ... {develop}
