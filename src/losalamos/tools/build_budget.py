# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Build transfer notes from a budget seed configuration.

Reads a config file and one or more budget (batch) files, builds the
in-memory :class:`~losalamos.budget.Budget` collection, optionally prints
the equivalent analysis, and optionally writes the notes to disk.

Usage
-----

.. code-block:: shell

    python -m losalamos.tools.build_budget --config <config_file>

Config file
-----------

The config file can be TOML, YAML, or JSON.

**Required keys**

- ``name`` — budget name, used as the note filename prefix.
- ``year`` — budget year (integer).
- ``budgets`` — list of paths to batch files.

**Optional keys**

- ``duration`` — number of years to cover (default ``1``).
- ``folder`` — output folder path. When absent or ``null``, notes are built
  in memory only and not written.
- ``split`` — write inflows and outflows into separate subfolders
  (default ``false``).
- ``equivalent`` — print the equivalent analysis after building (default
  ``false``).

.. tab-set::

    .. tab-item:: TOML

        .. code-block:: toml

            name     = "HouseBudget"
            year     = 2027
            duration = 1
            folder   = "/vault/budget/house"
            split    = false
            equivalent = true

            budgets = [
                "/seeds/house_contracts.toml",
                "/seeds/house_income.toml",
            ]

    .. tab-item:: YAML

        .. code-block:: yaml

            name:     HouseBudget
            year:     2027
            duration: 1
            folder:   /vault/budget/house
            split:    false
            equivalent: true

            budgets:
              - /seeds/house_contracts.yaml
              - /seeds/house_income.yaml

    .. tab-item:: JSON

        .. code-block:: json

            {
              "name": "HouseBudget",
              "year": 2027,
              "duration": 1,
              "folder": "/vault/budget/house",
              "split": false,
              "equivalent": true,
              "budgets": [
                "/seeds/house_contracts.json",
                "/seeds/house_income.json"
              ]
            }

Budget file
-----------

A budget file holds one or more batches. Each batch has a ``defaults`` block
and a ``transfers`` list. Entry-level keys override ``defaults``.

.. tab-set::

    .. tab-item:: TOML

        .. code-block:: toml

            [[batch]]
            [batch.defaults]
            commitment = "contracts"
            recurrence = "1 month"
            currency   = "BRL"
            account    = "BB-001"
            payer      = "Person Name"
            direction  = "outflow"

            [[batch.transfers]]
            value    = 1000.00
            receiver = "Landlord Co"
            day      = 5

            [[batch.transfers]]
            value    = 500.00
            receiver = "Internet Provider"
            day      = 15


            [[batch]]
            [batch.defaults]
            commitment = "income"
            recurrence = "1 month"
            currency   = "BRL"
            account    = "BB-001"
            receiver   = "Person Name"
            direction  = "inflow"

            [[batch.transfers]]
            value = 5000.00
            payer = "Employer Co"
            day   = 5

    .. tab-item:: YAML

        .. code-block:: yaml

            batch:
              - defaults:
                  commitment: contracts
                  recurrence: 1 month
                  currency:   BRL
                  account:    BB-001
                  payer:      Person Name
                  direction:  outflow
                transfers:
                  - value:    1000.00
                    receiver: Landlord Co
                    day:      5
                  - value:    500.00
                    receiver: Internet Provider
                    day:      15

              - defaults:
                  commitment: income
                  recurrence: 1 month
                  currency:   BRL
                  account:    BB-001
                  receiver:   Person Name
                  direction:  inflow
                transfers:
                  - value: 5000.00
                    payer: Employer Co
                    day:   5

    .. tab-item:: JSON

        .. code-block:: json

            [
              {
                "defaults": {
                  "commitment": "contracts",
                  "recurrence": "1 month",
                  "currency": "BRL",
                  "account": "BB-001",
                  "payer": "Person Name",
                  "direction": "outflow"
                },
                "transfers": [
                  {"value": 1000.00, "receiver": "Landlord Co",      "day": 5},
                  {"value":  500.00, "receiver": "Internet Provider", "day": 15}
                ]
              },
              {
                "defaults": {
                  "commitment": "income",
                  "recurrence": "1 month",
                  "currency": "BRL",
                  "account": "BB-001",
                  "receiver": "Person Name",
                  "direction": "inflow"
                },
                "transfers": [
                  {"value": 5000.00, "payer": "Employer Co", "day": 5}
                ]
              }
            ]

"""

# IMPORTS
# =======================================================================

import argparse
import sys
from pathlib import Path

from losalamos.budget import Budget
from losalamos.root import MbaE


# HELPERS
# =======================================================================


def _load_batches(path: Path) -> list:
    """
    Load a budget file and return its list of batches.

    Accepts TOML, YAML, or JSON. TOML and YAML files may wrap batches under
    a top-level ``batch`` key; JSON files may be a bare list. Both forms are
    normalised to a plain list.

    :param path: Path to the budget file.
    :type path: :class:`pathlib.Path`
    :raises FileNotFoundError: If the file does not exist.
    :raises ValueError: If no ``batch``/batches can be found in the file.
    :return: List of batch dicts.
    :rtype: list
    """
    raw = MbaE.load_config_file(path=path)

    if isinstance(raw, list):
        return raw

    if isinstance(raw, dict):
        if "batch" in raw:
            return raw["batch"]
        # single batch dict without a wrapper key
        if "transfers" in raw or "defaults" in raw:
            return [raw]

    raise ValueError(
        f"Cannot parse batch structure from '{path.name}'. "
        "Expected a list of batches or a dict with a 'batch' key."
    )


# ENTRY POINT
# =======================================================================


def build_budget(config_path: Path) -> Budget:
    """
    Build a :class:`~losalamos.budget.Budget` from a config file.

    Loads the config, resolves and merges all batch files listed under
    ``budgets``, builds the in-memory collection, optionally prints the
    equivalent analysis, and optionally saves notes to disk.

    :param config_path: Path to the config file (TOML, YAML, or JSON).
    :type config_path: :class:`pathlib.Path`
    :raises ValueError: If required config keys are missing or a batch file
        cannot be parsed.
    :return: The populated :class:`~losalamos.budget.Budget` instance.
    :rtype: :class:`~losalamos.budget.Budget`
    """
    config = MbaE.load_config_file(path=config_path)

    # --- validate required keys ---
    for key in ("name", "year", "budgets"):
        if not config.get(key):
            print(f"[error] Config is missing required key: '{key}'")
            sys.exit(1)

    name = config["name"]
    year = int(config["year"])
    duration = int(config.get("duration") or 1)
    folder = config.get("folder") or None
    split = bool(config.get("split", False))
    equivalent = bool(config.get("equivalent", False))

    # --- load and merge all batch files ---
    all_batches = []
    budget_paths = config["budgets"]
    print(f"\nConfig : {config_path.name}")
    print(f"Budget : {name}  |  year={year}  duration={duration}\n")

    for bp in budget_paths:
        bp = Path(bp)
        batches = _load_batches(bp)
        print(f"  [loaded]  {bp.name}  ({len(batches)} batch(es))")
        all_batches.extend(batches)

    print(
        f"\n  {len(all_batches)} total batch(es) across {len(budget_paths)} file(s)\n"
    )

    # --- build ---
    budget = Budget(name=name)
    budget.year = year
    budget.duration = duration
    budget.split = split

    if folder is not None:
        budget.output_folder = Path(folder)

    budget.build(batches=all_batches)
    print(f"Built  : {len(budget.collection)} transfer note(s) in memory\n")

    # --- equivalent analysis ---
    if equivalent:
        sep = "─" * 60
        print(sep)
        print(f" Monthly equivalent  (by account)")
        print(sep)
        print(budget.monthly_equivalent().to_string(index=False))
        print()
        print(sep)
        print(f" Annual equivalent  (by account)")
        print(sep)
        print(budget.annual_equivalent().to_string(index=False))
        print()

    # --- save ---
    if folder is not None:
        budget.save()
        print(f"Saved  : {len(budget.collection)} note(s) → {budget.output_folder}\n")
    else:
        print("No folder set — notes kept in memory, nothing written.\n")

    return budget


# CLI
# =======================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build transfer notes from a budget config file."
    )
    parser.add_argument(
        "--config",
        required=True,
        metavar="CONFIG_FILE",
        help="Path to the config file (TOML, YAML, or JSON).",
    )
    args = parser.parse_args()
    build_budget(config_path=Path(args.config))
