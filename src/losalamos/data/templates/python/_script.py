# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short script description (1-3 sentences)}
todo docstring

Examples
--------
todo docstring

Print a message

.. code-block:: python

    # print message
    print("Hello world!")
    # [Output] >> 'Hello world!'


"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import argparse

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


def get_arguments():

    # 1. Initialize the Parser
    parser = argparse.ArgumentParser(
        description="A prototype script to argparse.",
        epilog="Usage example: python script.py data.csv --limit 10 -v",
    )

    # 2. Add Arguments
    """
    # Positional argument (Required)
    parser.add_argument(
        "filename",
        help="The path to the input file you want to process."
    )

    # Optional argument (Integer)
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=5,
        help="Maximum number of items to process (default: 5)"
    )    
    """

    # Flag/Boolean argument (True if present, False otherwise)
    parser.add_argument(
        "-w",
        "--write",
        action="store_true",
        help="Set as writing mode",
    )

    # 3. Parse the Arguments
    args = parser.parse_args()

    return args


def gate_keeper():

    print("\n\n !! WARNING !!\n\n")
    print(">>>> this script may overwrite data in this system\n")

    ans = input("confirm execution? [y/N] ")

    return ans in ("y", "yes")


def main():

    args = get_arguments()

    # Handle write mode
    # ===================================================================
    if args.write:
        ans = gate_keeper()
        if ans:
            print("Execution confirmed. Running in write mode.")
        else:
            print("Execution negated. Running in safe mode.")
            return None

    # Main function
    # ===================================================================
    # develop

    # [CONTINUE HERE]
    print("Hello World!")

    return None


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    main()

    # ... {develop}
