# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Top-level vault manager with three-level navigation.

Reads a tool config file (YAML, TOML, or JSON) listing one or more vaults.
Navigation flows from vault → branch → project → document management.
Adding a project writes a temporary config file and delegates to
:func:`losalamos.tools.add_new_project.run`.

**Shell usage**

.. code-block:: bash

    python -m losalamos.tools.manage_vault --config path/to/config.toml

**Tool config keys**

Each entry in the ``vaults`` array supports:

- ``name`` (*str*, required) — display name shown in the vault list.
- ``path`` (*str*, required) — root directory where branch folders live.
- ``folder_system`` (*str*, optional) — ``"default"`` or ``"alphanumerical"``.
  Defaults to ``"default"``.
- ``separator`` (*str*, optional) — string between branch name and number in
  the default system. Defaults to ``""``.
- ``sources`` (*str*, optional) — path to a shared sources config file.
- ``language`` (*str*, optional) — language tag (e.g. ``"pt-br"``).

.. dropdown:: Example — tool config file
    :icon: code-square
    :open:

    .. code-block:: toml

        [[vaults]]
        name = "Client Projects"
        path = "C:/My Drive/projects"
        folder_system = "default"
        separator = "_"
        sources = "C:/vault/sources.toml"
        language = "pt-br"

        [[vaults]]
        name = "Research"
        path = "C:/research"
        folder_system = "alphanumerical"

"""

# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import json
import re
import argparse
import tempfile
from pathlib import Path

# Project-level imports
# =======================================================================
import losalamos
from losalamos.project import _load_config
from losalamos.tools.core import *
from losalamos.tools.add_new_project import (
    _list_branches,
    _next_increment,
    run as _add_project_run,
)
from losalamos.tools.manage_documents import (
    _load_projects,
    _read_project_title,
    _print_projects,
    _home,
    _Quit as _DocQuit,
)


# EXCEPTIONS
# ***********************************************************************


class _Quit(Exception):
    """Raised when the user chooses to exit the tool."""

    pass


# FUNCTIONS
# ***********************************************************************


def get_arguments():
    """
    Parse command-line arguments.

    :returns: Parsed argument namespace with a ``config`` attribute.
    """
    parser = argparse.ArgumentParser(
        description="Top-level vault manager with vault/branch/project navigation.",
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        help="Path to the tool config file (.yaml, .toml, or .json).",
    )
    return parser.parse_args()


def _pick_vault(vaults: list[dict]) -> dict:
    """
    Interactive vault picker.

    :param vaults: List of vault dicts from the tool config.
    :returns: Selected vault dict.
    :raises _Quit: When the user enters ``q``.
    """
    while True:
        heading_subsection("Vaults")
        for i, v in enumerate(vaults):
            print(f"  [{i + 1:2d}]  {v['name']}")
        print()

        choice = input(f"  Select vault  [1-{len(vaults)} / q=quit]: ").strip()

        if choice.lower() == "q":
            raise _Quit()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(vaults):
                return vaults[idx]
            print(f"  Out of range (1–{len(vaults)}). Try again.\n")
        except ValueError:
            print("  Enter a number.\n")


def _pick_branch(vault: dict) -> Path | None:
    """
    Interactive branch picker for a vault.

    Lists existing branches; the user selects one or creates a new one
    with ``+``.

    :param vault: Vault dict from the tool config.
    :returns: Path to the selected or newly created branch folder,
        or ``None`` to go back.
    :raises _Quit: When the user enters ``q``.
    """
    vault_path = Path(vault["path"])
    folder_system = vault.get("folder_system", "default")

    while True:
        branches = _list_branches(vault=vault_path, folder_system=folder_system)

        heading_subsection(f"Branches — {vault['name']}")
        if branches:
            for i, b in enumerate(branches):
                n = b["project_count"]
                label = f"({n} project{'s' if n != 1 else ''})"
                print(f"  [{i + 1:2d}]  {b['name']:<24}  {label}")
        else:
            print(get_message("No branches found — use [+] to create one."))
        print(f"  [+]   Add new branch")
        print()

        n_branches = len(branches)
        range_hint = f"1-{n_branches} / " if n_branches else ""
        choice = input(f"  Select  [{range_hint}+ / p=back / q=quit]: ").strip()

        if choice.lower() == "q":
            raise _Quit()
        if choice.lower() == "p":
            return None

        if choice == "+":
            if folder_system == "alphanumerical":
                raw = input(
                    "  Branch prefix (e.g. C for C000)  [ENTER=cancel / q=quit]: "
                ).strip()
            else:
                raw = input(
                    "  Branch name (e.g. Research)  [ENTER=cancel / q=quit]: "
                ).strip()
            if raw.lower() == "q":
                raise _Quit()
            if not raw:
                continue
            branch_folder = f"{raw}000" if folder_system == "alphanumerical" else raw
            branch_path = vault_path / branch_folder
            branch_path.mkdir(parents=True, exist_ok=True)
            print(get_message(f"Created : {branch_path}"))
            return branch_path

        try:
            idx = int(choice) - 1
            if 0 <= idx < n_branches:
                return branches[idx]["path"]
            print(f"  Out of range (1–{n_branches}). Try again.\n")
        except ValueError:
            print("  Enter a number, +, p, or q.\n")


def _pick_project(vault: dict, branch_path: Path) -> dict | None:
    """
    Interactive project picker for a branch.

    Lists existing projects; the user selects one or adds a new one with ``+``.

    :param vault: Vault dict from the tool config (provides context for add).
    :param branch_path: Path to the branch folder.
    :returns: Project info dict (keys: ``name``, ``path``, ``title``),
        or ``None`` to go back.
    :raises _Quit: When the user enters ``q``.
    """
    vault_path = Path(vault["path"])
    folder_system = vault.get("folder_system", "default")
    branch_folder = branch_path.name
    branch = branch_folder[:-3] if folder_system == "alphanumerical" else branch_folder

    while True:
        projects = _load_projects(branch_path=branch_path, branch=branch)

        heading_subsection(f"Projects — {branch_folder}")
        if projects:
            _print_projects(projects=projects)
        else:
            print(get_message("No projects found — use [+] to add one."))
            print()
        print(f"  [+]   Add new project")
        print()

        n = len(projects)
        range_hint = f"1-{n} / " if n else ""
        choice = input(f"  Select  [{range_hint}+ / p=back / q=quit]: ").strip()

        if choice.lower() == "q":
            raise _Quit()
        if choice.lower() == "p":
            return None

        if choice == "+":
            _add_project(vault=vault, branch_path=branch_path)
            continue  # refresh project list after add

        try:
            idx = int(choice) - 1
            if 0 <= idx < n:
                return projects[idx]
            print(f"  Out of range (1–{n}). Try again.\n")
        except ValueError:
            print("  Enter a number, +, p, or q.\n")


def _add_project(vault: dict, branch_path: Path) -> None:
    """
    Add a new project by writing a temporary config and calling
    :func:`losalamos.tools.add_new_project.run`.

    :param vault: Vault dict providing folder_system, separator, sources, language.
    :param branch_path: Path to the branch folder where the project will be created.
    """
    cfg: dict = {"folder": str(branch_path)}
    for key in ("folder_system", "separator", "sources", "language"):
        if key in vault:
            cfg[key] = vault[key]

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(cfg, f)
        tmp_path = f.name

    try:
        _add_project_run(source=tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _manage_project(vault: dict, project: dict) -> str:
    """
    Open the document management home page for a selected project.

    :param vault: Vault dict (used for vault path context).
    :param project: Project info dict with ``path`` and ``name``.
    :returns: ``"quit"`` or ``"projects"`` (back to project list).
    """
    pj = losalamos.load_project(
        project_folder=str(project["path"]),
        vault=vault["path"],
    )
    try:
        return _home(pj=pj, project_info=project)
    except _DocQuit:
        return "quit"


def run(config_path: str) -> None:
    """
    Start the vault manager.

    :param config_path: Path to the tool config file.
    :type config_path: str
    """
    heading_section("VAULT MANAGER")

    tool_cfg = _load_config(source=config_path)
    vaults = tool_cfg.get("vaults", [])

    if not vaults:
        raise ValueError(
            "Tool config missing 'vaults' list. "
            "Define at least one [[vaults]] entry."
        )

    try:
        while True:
            vault = _pick_vault(vaults=vaults)

            while True:
                branch_path = _pick_branch(vault=vault)
                if branch_path is None:
                    break  # back to vault picker

                while True:
                    project = _pick_project(vault=vault, branch_path=branch_path)
                    if project is None:
                        break  # back to branch picker

                    result = _manage_project(vault=vault, project=project)
                    if result == "quit":
                        raise _Quit()
                    # "projects" → back to project picker

    except _Quit:
        pass

    print("\n  Goodbye.\n")


def main() -> None:
    args = get_arguments()
    run(config_path=args.config)


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":
    main()
