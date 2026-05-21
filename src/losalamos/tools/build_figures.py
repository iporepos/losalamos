# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.

"""
Build image outputs from a folder of SVG files using a JSON parameter file.

This tool iterates over all ``.svg`` files in a source folder and exports
each one to the specified format (png, jpeg, pdf, svg) using Inkscape as
the rendering backend.

**Shell usage**

.. code-block:: bash

    # Export all SVGs in a folder to JPEG
    python -m losalamos.tools.build_figures \\
        --src /path/to/svgs \\
        --dst /path/to/output \\
        --par /path/to/params.json

    # Using short flags
    python -m losalamos.tools.build_figures -s ./svgs -d ./out -p ./params.json

**Parameter file format**

.. code-block:: json

    {
        "figure_format": "jpeg",
        "crop_id":       "frame",
        "show_layers":   ["main", "leader_lines", "labels_en"],
        "hide_layers":   ["frames", "labels_pt"],
        "suffix":        "en"
    }

.. note::

    ``figure_format`` accepts ``"png"``, ``"jpeg"``, ``"pdf"``, or ``"svg"``.
    ``crop_id`` may be ``null`` to export the full page.
    ``suffix`` is optional — when provided it is appended to the output filename stem.

"""

# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import argparse
import json
import pprint
from pathlib import Path

# External imports
# =======================================================================
from tqdm import tqdm

# Project-level imports
# =======================================================================
from losalamos.figures import FigureSVG
from losalamos.tools.core import *


# FUNCTIONS
# ***********************************************************************


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--src", help="Source folder of SVG files.")
    parser.add_argument("-d", "--dst", help="Destination folder for outputs.")
    parser.add_argument("-p", "--par", help="JSON parameter file.")
    args = parser.parse_args()
    return args


def main() -> None:
    heading_section("BUILD IMAGES")

    args = get_arguments()
    src_folder = Path(args.src)
    dst_folder = Path(args.dst)
    par_file = Path(args.par)

    heading_subsection("Folders")
    print(get_message(f"Source folder: {src_folder}"))
    print(get_message(f"Target folder: {dst_folder}"))

    heading_subsection("Parameters")
    print(get_message(f"JSON file: {par_file}"))
    with open(par_file, "r") as f:
        parameters = json.load(f)

    figure_format = parameters["figure_format"]
    crop_id = parameters["crop_id"]
    show_layers = parameters["show_layers"]
    hide_layers = parameters["hide_layers"]
    suffix = parameters.get("suffix", None)
    dpi = parameters.get("dpi", 300)

    # resolve output extension
    # -----------------------------------------------------------------------
    ext_map = {
        "png": ".png",
        "jpeg": ".png",  # conversion to jpeg is downstream
        "pdf": ".pdf",
        "svg": ".svg",
    }
    ext = ext_map.get(figure_format, ".png")

    ls_svgs = list(src_folder.glob("*.svg"))

    ls_outputs = []
    print("\n\n")
    for f in tqdm(ls_svgs, desc=figure_format, unit="file"):

        # build output path
        # -------------------------------------------------------------------
        stem = f"{f.stem}_{suffix}" if suffix else f.stem
        fo = dst_folder / f"{stem}{ext}"

        svg = FigureSVG()
        svg.load_data(file_data=f)

        # dispatch to the right export method
        # -------------------------------------------------------------------
        common = dict(
            file_output=fo,
            crop_id=crop_id,
            show_layers=show_layers,
            hide_layers=hide_layers,
            show_inclusive=True,
        )

        if figure_format == "jpeg":
            svg.to_image(**common, to_jpeg=True, remove_png=True, dpi=dpi)

        elif figure_format == "png":
            svg.to_image(**common, to_jpeg=False, remove_png=False, dpi=dpi)

        elif figure_format == "pdf":
            svg.to_pdf(**common)

        elif figure_format == "svg":
            svg.to_svg(**common)

        else:
            raise ValueError(f"Unsupported figure_format: '{figure_format}'")

        ls_outputs.append(fo.name)

    heading_subsection("Outputs")
    pprint.pp(ls_outputs)
    heading_done()


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":
    main()
