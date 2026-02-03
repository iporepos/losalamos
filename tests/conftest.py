# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Setup constants and other utilities for testing

"""

# ***********************************************************************
# IMPORTS
# ***********************************************************************
# import modules from other libs


# Native imports
# =======================================================================
import os
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import requests
import zipfile
import numpy as np
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
# import {module}
# ... {develop}


# ***********************************************************************
# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# Project-level
# =======================================================================

# Paths
# -----------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
# ... {develop}

# Files
# -----------------------------------------------------------------------
DATA_FILE = DATA_DIR / "test_data.csv"
DATASETS_FILE = DATA_DIR / "datasets.csv"

# Other
# -----------------------------------------------------------------------
DATASETS_DF = pd.read_csv(DATASETS_FILE, sep=";")


# ... {develop}

# Names
# -----------------------------------------------------------------------
REPO_NAME = os.path.basename(Path(BASE_DIR).parent)
# ... {develop}

# Benchmark tests
# -----------------------------------------------------------------------

# benchmark tests disabled -- default to "0" (false)
RUN_BENCHMARKS = os.getenv("RUN_BENCHMARKS", "0") == "1"

# large benchmark tests disabled -- default to "0" (false)
RUN_BENCHMARKS_XXL = os.getenv("RUN_BENCHMARKS_XXL", "0") == "1"
# ... {develop}

# Module-level
# =======================================================================
# {develop}


# ***********************************************************************
# FUNCTIONS
# ***********************************************************************


# Project-level
# =======================================================================


def testmsg(s):
    """
    Formats a string into a standardized lowercase test message prefixing the repository name.

    :param s: The message content to be formatted.
    :type s: str
    :return: The formatted string in lowercase.
    :rtype: str
    """
    s2 = f"{REPO_NAME} -- tests >>> {s}".lower()
    return s2


def testprint(s):
    """
    Formats a message and prints it to the console with an immediate flush.

    :param s: The message content to be printed.
    :type s: str
    :return: The formatted string that was printed.
    :rtype: str
    """
    s2 = testmsg(s)
    print(s2, flush=True)
    return s2


def make_output():
    """
    Ensures the existence of the global output directory.

    :return: None.
    :rtype: None
    """
    testprint("making output dir")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return None


def make_data(size=100):
    """
    Generates a synthetic CSV dataset if the data file does not already exist.

    .. note::

        The function creates a :class:`pandas.DataFrame` with three columns:
        ``v1`` and ``v2`` containing random integers, and ``v3`` representing
        the ratio of the two.

    :param size: The number of rows to generate for the dataset. Default value = 100
    :type size: int
    :return: None.
    :rtype: None
    """
    testprint("making data")
    if not os.path.isfile(DATA_FILE):
        v = np.random.randint(low=10, high=100, size=size)
        v2 = np.random.randint(low=10, high=100, size=size)
        v3 = v2 / v
        df = pd.DataFrame({"v1": v, "v2": v2, "v3": v3})
        df.to_csv(DATA_FILE, sep=";", index=False)
        testprint("data created")
    else:
        testprint("data already available")
    return None


def load_data():
    testprint("loading numbers data")
    df = pd.read_csv(DATA_FILE, sep=";")
    return df


# ... {develop}

# Module-level
# =======================================================================


def retrieve_dataset(name):
    """
    Validates and prepares the directory paths for a specific dataset.

    .. note::

        This function checks for dataset existence in the local configuration,
        triggers an installation if the data is missing, and ensures a
        corresponding output directory is created.

    :param name: The unique identifier of the dataset to retrieve.
    :type name: str
    :return: A tuple containing the dataset source directory and the output directory, or ``False`` if not found.
    :rtype: tuple or bool
    """
    ls_datasets = DATASETS_DF["name"].unique()
    if name not in set(ls_datasets):
        testprint(f"dataset {name} not found")
        return False
    else:
        # install dataset
        dataset_dir = DATA_DIR / name
        if not os.path.exists(dataset_dir):
            dataset_dir = install_dataset(name)

        # get output
        output_path = OUTPUT_DIR / name
        os.makedirs(output_path, exist_ok=True)

        return (dataset_dir, output_path)


def install_dataset(name):
    """
    Downloads and extracts a dataset into the local data directory.

    :param name: The name of the dataset to be installed.
    :type name: str
    :return: The path to the directory where the dataset was installed.
    :rtype: :class:`pathlib.Path` or str
    """
    dataset_dir = DATA_DIR / name
    os.makedirs(dataset_dir, exist_ok=True)
    dataset_url = DATASETS_DF.loc[DATASETS_DF["name"] == name, "url"].values[0]
    zip_path = os.path.join(dataset_dir, f"{name}.zip")

    testprint(f"donwloading dataset: {name} ...")
    download_file(dataset_url, dst=zip_path)

    testprint(f"extracting dataset '{name}'...")
    extract_zip(zip_path, dataset_dir)
    os.remove(zip_path)
    return dataset_dir


def download_file(url, dst):
    """
    Streams and saves a file from a specified URL to a local destination.

    :param url: The remote URL of the file to download.
    :type url: str
    :param dst: The local file path where the content should be saved.
    :type dst: str
    :return: None.
    :rtype: None
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dst, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return None


def extract_zip(file_path, extract_to):
    """
    Extracts all contents of a ZIP archive to a specified directory.

    :param file_path: The local path to the ZIP archive file.
    :type file_path: str
    :param extract_to: The directory path where files should be extracted.
    :type extract_to: str
    :return: None.
    :rtype: None
    """
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)


# ... {develop}

# ***********************************************************************
# CLASSES
# ***********************************************************************

# Project-level
# =======================================================================
# {develop}

# Module-level
# =======================================================================


class DatasetDownloadError(Exception):
    """
    Custom exception for dataset download issues.
    """

    pass


# ... {develop}

# ***********************************************************************
# SCRIPT
# ***********************************************************************
# standalone behaviour as a script

if __name__ == "__main__":

    # Script section
    # ===================================================================
    testprint("conftest.py")

    # Make data
    # -------------------------------------------------------------------
    make_data(size=50)

    # ... {develop}

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
