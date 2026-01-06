# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short module description (1-3 sentences)}
todo docstring

Features
--------
todo docstring

 - {feature 1}
 - {feature 2}
 - {feature 3}
 - {etc}

Overview
--------
todo docstring
{Overview description}

Examples
--------
todo docstring
{Examples in rST}

Print a message

.. code-block:: python

    # print message
    print("Hello world!")
    # [Output] >> 'Hello world!'


"""

# ***********************************************************************
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import unittest
from time import sleep

# ... {develop}

# External imports
# =======================================================================
import numpy as np
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from tests import conftest
from tests.conftest import RUN_BENCHMARKS, RUN_BENCHMARKS_XXL, testprint

# ... {develop}


# ***********************************************************************
# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# Subsubsection example
# -----------------------------------------------------------------------
HELLO = "Hello World!"  # example
# ... {develop}


# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


# ***********************************************************************
# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================
# ... {develop}


# FUNCTIONS -- Module-level
# =======================================================================
def emulate_simulation(data_path, output_path):
    # todo docstring
    data_file_path = f"{data_path}/numbers.csv"
    df = pd.read_csv(data_file_path, sep=";")
    sim_v = np.zeros(shape=len(df))
    sim_r = np.random.normal(loc=100, scale=2, size=len(df))
    testprint("running simulation")
    for i in range(5000):
        sim_v[i] = df["v3"].values[i] * sim_r[i]
        sleep(0.0002)
        print(f"step >> {i}")
    df_o = pd.DataFrame({"v3": df["v3"].values, "sim": sim_v})
    df_o.to_csv(output_path / "simulation.csv", sep=";", index=False)
    return 0


# ... {develop}


# ***********************************************************************
# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================
# ... {develop}

# CLASSES -- Module-level
# =======================================================================


@unittest.skipUnless(RUN_BENCHMARKS, reason="skipping benchmarks")
class BenchmarkTemplateTests(unittest.TestCase):

    # Setup methods
    # -------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        """
        Prepare large datasets and output folders
        """
        # download data if needed
        tpl = conftest.retrieve_dataset(name="numbers")
        cls.data_path = tpl[0]
        cls.output_path = tpl[1]

    def setUp(self):
        """
        Runs before each test method
        """
        # ... {develop}
        return None

    # Testing methods
    # -------------------------------------------------------------------

    def test_without_error(self):
        """
        Ensure the simulation runs without crashing.

        Other info
        """
        try:
            results = emulate_simulation(
                data_path=self.data_path, output_path=self.output_path
            )
        except Exception as e:
            self.fail(f"simulation crashed with error: {e}")

    def test_model_performance(self):
        """
        Measure execution time or performance.
        """
        import time

        start = time.time()
        # run
        emulate_simulation(data_path=self.data_path, output_path=self.output_path)

        elapsed = time.time() - start

        # Simple performance check (optional)
        testprint(f"model ran in {elapsed:.2f} seconds")
        # e.g., test fails if > 10 minutes
        self.assertLess(elapsed, 600)

    @unittest.skipUnless(RUN_BENCHMARKS_XXL, "skipping long benchmarks")
    def test_full_model_run(self):
        """
        Run the full simulation and check outputs
        """
        # Run simulation
        results = emulate_simulation(
            data_path=self.data_path, output_path=self.output_path
        )

        # Example assertions: basic validation of output
        self.assertIsNotNone(results)
        self.assertTrue((self.output_path / "summary.csv").exists())

    # Tear down methods
    # -------------------------------------------------------------------
    def tearDown(self):
        """
        Runs after each test method
        """
        # ... {develop}
        return None

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests
        """
        # ... {develop}
        return None


# ... {develop}


# ***********************************************************************
# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    from tests.conftest import RUN_BENCHMARKS

    RUN_BENCHMARKS = True

    # Script section
    # ===================================================================
    unittest.main()
    # ... {develop}

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
