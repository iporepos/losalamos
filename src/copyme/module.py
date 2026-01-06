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
# ... {develop}


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


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================


# Demo example
# -----------------------------------------------------------------------
def myfunc(parameter1):
    # todo docstring
    print(parameter1)
    ls_variable = [1, 2, 3, "ok", [2, 3, 4, 5, 6]]
    return None


def add(num1, num2):
    """
    Add two numbers

    :param num1: number 1
    :type num1: int or float
    :param num2: number 2
    :type num2: int or float
    :return: sum of numbers
    :rtype: int or float

    **Examples**

    >>> add(2, 3)
    5

    >>> add(20, 2.3)
    22.3

    """
    return num1 + num2


def multiply(num1, num2):
    """
    Multiply two numbers

    :param num1: number 1
    :type num1: int or float
    :param num2: number 2
    :type num2: int or float
    :return: product of numbers
    :rtype: int or float

    **Examples**

    >>> multiply(2, 3)
    6

    >>> multiply(20, 2)
    40

    """
    return num1 * num2


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
class MyClass:
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
    # Test doctests
    # ===================================================================
    import doctest

    doctest.testmod()

    # Script section
    # ===================================================================
    print("Hello world!")
    # ... {develop}

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
