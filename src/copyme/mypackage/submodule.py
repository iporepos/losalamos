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

* {feature 1}
* {feature 2}
* {feature 3}
* {etc}

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
from copyme.module import HELLO  # import from internal modules

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# Subsubsection example
# -----------------------------------------------------------------------
HELLO2 = "Hello Mars!"  # example
# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================


# Demo example
# -----------------------------------------------------------------------
def myfunc2(parameter1):
    # todo docstring
    print(f" >>>> {parameter1}")
    return None


# ... {develop}

# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================


# Demo example
# -----------------------------------------------------------------------
class MySubClass:
    # todo docstring

    def __init__(self):
        # todo docstring
        print("start class")
        self.value = 10

    # Internal methods
    # -------------------------------------------------------------------
    def _reset_value(self):
        # todo docstring
        self.value = 10
        return None

    # Public methods
    # -------------------------------------------------------------------
    def print_value(self):
        # todo docstring
        print(self.value)
        return None

    # Static methods
    # -------------------------------------------------------------------
    @staticmethod
    def print_message(s="Hello world!"):
        # todo docstring
        print(s)
        return None


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
    myfunc2(HELLO2)
    # ... {develop}
