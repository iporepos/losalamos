# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Miscellaneous utilities module

"""
import shutil

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
from pathlib import Path
from datetime import datetime
from time import sleep

# ... {develop}

# External imports
# =======================================================================
# import {module}
# ... {develop}

# Project-level imports
# =======================================================================
# import {module}
# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# FUNCTIONS
# ***********************************************************************
def get_timestamp(milliseconds=False):
    """
    Generates a formatted timestamp string based on the current system time.

    :param milliseconds: Whether to include a millisecond suffix preceded by ``P``. Default value = ``False``
    :type milliseconds: bool
    :return: The formatted date-time string.
    :rtype: str
    """
    # Capture current time
    now = datetime.now()

    sts = "%Y%m%dT%H%M%S"

    if milliseconds:
        # %f provides microseconds, so we take the first 3 digits for milliseconds
        milliseconds = now.strftime("%f")[:3]
        # Format the main string and inject the 'P' and milliseconds
        sts = f"{sts}P{milliseconds}"

    return now.strftime(sts)


def make_local_tempfile(src_file):
    """
    Creates a temporary copy of a source file in the same directory with a unique timestamped name.

    .. note::

        The function uses a loop with a 1-millisecond sleep to ensure a unique filename is generated
        if a collision occurs at the same timestamp.

    :param src_file: The path to the source file to be copied.
    :type src_file: str | :class:`pathlib.Path`
    :return: The path to the newly created temporary file, or ``None`` if creation fails.
    :rtype: :class:`pathlib.Path` | None
    """
    src_file = Path(src_file)

    folder = src_file.parent
    name = src_file.stem
    extension = src_file.suffix

    while True:
        time_stamp = get_timestamp(milliseconds=True)
        dst_file = folder / f"__tempfile__{name}_{time_stamp}{extension}"
        if not dst_file.is_file():
            shutil.copy(src_file, dst_file)
            return dst_file

        sleep(0.001)

    return None


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    from tests.conftest import DATA_DIR, OUTPUT_DIR

    # Script section
    # ===================================================================
    print("Hello World!")

    src_file = DATA_DIR / "budyko.jpeg"
    dst_file = OUTPUT_DIR / "budyko.jpeg"
    shutil.copy(src_file, dst_file)

    src_file = dst_file
    for i in range(3):
        make_local_tempfile(src_file)

    print(get_timestamp(milliseconds=False))
    print(get_timestamp(milliseconds=True))

    # ... {develop}
