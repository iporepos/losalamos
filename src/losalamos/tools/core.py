# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Core constants and functions for the ``losalamos.tools`` package.

"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
# import {module}
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

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# Subsubsection example
# -----------------------------------------------------------------------
# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}
BAR_SIZE = 80

# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================
# ... {develop}

# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


def heading(msg, symbol, prefix, upper=False, tail_n=1):
    print("\n")

    print(BAR_SIZE * symbol)

    if upper:
        msg = msg.upper()

    if prefix is not None:
        print(f"{prefix} -- {msg}")
    else:
        print(f"{msg}")

    print(tail_n * "\n")


def heading_section(msg):
    heading(msg, symbol="=", prefix="LOSALAMOS", upper=True, tail_n=2)


def heading_subsection(msg):
    heading(msg, symbol="-", prefix=None, upper=False)


def get_message(msg, prefix=None):
    if prefix is not None:
        return f" >>> {prefix} --- {msg}"
    else:
        return f" >>> {msg}"


def get_warning(msg):
    return get_message(msg, "! WARNING !")


def heading_done():
    heading_subsection(msg="DONE")


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================
# ... {develop}

# CLASSES -- Module-level
# =======================================================================
# ... {develop}


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    print("Hello world!")
    # ... {develop}

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
