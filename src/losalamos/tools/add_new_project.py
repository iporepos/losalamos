# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Create a new numbered project inside a vault.

Reads a tool config file (YAML, TOML, or JSON) that sets the vault root and
folder system. The first interactive screen lists existing branches so the
user can pick one or create a new one. Metadata fields are then filled in
interactively, and :func:`losalamos.new_project` is called.

**Shell usage**

.. code-block:: bash

    python -m losalamos.tools.add_new_project --config path/to/config.toml

**Tool config keys**

- ``vault`` (*str*, required) — root directory where branch folders live.
- ``folder_system`` (*str*, optional) — ``"default"`` (branch folder is
  ``<branch>/``, project names are ``<branch><separator><NNN>``) or
  ``"alphanumerical"`` (branch folder is ``<branch>000/``, project names
  are ``<branch><NNN>``). Defaults to ``"default"``.
- ``separator`` (*str*, optional) — string inserted between the branch name
  and the number in the default folder system, e.g. ``"_"`` → ``Research_001``.
  Absent or ``""`` means no separator, e.g. ``Research001``. Ignored for
  ``alphanumerical``.
- ``sources`` (*str*, optional) — path to a shared sources config file
  (copied into each new project's ``admin/config/``).

**Interaction keys**

- ``0`` at the letter filter or at the numbered list — skip the current field.
- ``ENTER`` at the letter filter — show all entries.
- ``+`` at the branch picker — create a new branch.
- ``s`` at the project confirmation — skip all optional fields and create immediately.
- ``b`` after a filtered list — go back to the letter filter.
- ``q`` at any prompt — abort and exit.

.. dropdown:: Example — tool config file (default system)
    :icon: code-square
    :open:

    Save an ``add_project.toml`` and pass it with ``--config``:

    .. code-block:: toml

        vault = "C:/My Drive/projects"
        folder_system = "default"
        separator = "_"
        sources = "C:/vault/sources.toml"
        language = "pt-br"

.. dropdown:: Example — tool config file (alphanumerical system)
    :icon: code-square

    .. code-block:: toml

        vault = "C:/My Drive/projects"
        folder_system = "alphanumerical"
        sources = "C:/vault/sources.toml"

"""

# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import re
import argparse
from pathlib import Path

# Project-level imports
# =======================================================================
import losalamos
from losalamos.notes import NoteBasic
from losalamos.project import _load_config
from losalamos.tools.core import *


# CONSTANTS
# ***********************************************************************

_COLUMNS = 3
_COL_WIDTH = 28


# EXCEPTIONS
# ***********************************************************************


class _Quit(Exception):
    """Raised when the user types ``q`` to abort the session."""

    pass


# FUNCTIONS
# ***********************************************************************


def get_arguments():
    """
    Parse command-line arguments.

    :returns: Parsed argument namespace with a ``config`` attribute.
    """
    parser = argparse.ArgumentParser(
        description="Create a new numbered project inside a project folder group.",
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        help="Path to the tool config file (.yaml, .toml, or .json).",
    )
    return parser.parse_args()


def _next_increment(
    branch_path: Path, branch: str, separator: str = "", width: int = 3
) -> str:
    """
    Scan *branch_path* and return the next available project name.

    Strips the branch name prefix then any leading non-digit characters
    (the separator) from each folder name before extracting the number,
    so it works for both ``Research_001`` and ``A001`` layouts.

    :param branch_path: Directory containing sibling project folders.
    :param branch: Branch name prefix, e.g. ``"Research"`` or ``"A"``.
    :param separator: Optional string between branch name and number, e.g. ``"_"``.
    :param width: Zero-pad width for the numeric suffix.
    :returns: Next project name, e.g. ``"Research_003"`` or ``"A003"``.
    :rtype: str
    """
    numbers = []
    if branch_path.exists():
        for item in branch_path.iterdir():
            if not item.is_dir():
                continue
            if not item.name.lower().startswith(branch.lower()):
                continue
            tail = item.name[len(branch) :]
            # strip optional separator then leading non-digits
            digits = re.sub(r"^\D*", "", tail)
            if digits:
                numbers.append(int(digits))
    next_num = max(numbers) + 1 if numbers else 1
    return f"{branch}{separator}{str(next_num).zfill(width)}"


def _collect_names(directories) -> list[str]:
    """
    Scan directories for ``.md`` files and return a sorted list of stems.

    :param directories: List of directory paths to scan.
    :returns: Alphabetically sorted list of note names (file stems).
    :rtype: list[str]
    """
    names = []
    if not directories:
        return names
    for d in directories:
        p = Path(d)
        if p.is_dir():
            for f in p.glob("*.md"):
                names.append(f.stem)
    return sorted(set(names))


def _collect_services(directories) -> tuple[list[str], list[str]]:
    """
    Scan directories for service notes and return parallel ID and label lists.

    The label combines the file stem (service ID) with the ``abstract`` field
    from the note's front matter, e.g. ``SRV001  —  Environmental Consulting``.

    :param directories: List of directory paths to scan.
    :returns: Tuple of ``(ids, labels)`` sorted by ID.
    :rtype: tuple[list[str], list[str]]
    """
    pairs = []
    if not directories:
        return [], []
    for d in directories:
        p = Path(d)
        if p.is_dir():
            for f in p.glob("*.md"):
                meta = NoteBasic.parse_metadata(note_file=f) or {}
                abstract = (meta.get("abstract") or "").strip()
                label = f"{f.stem}  —  {abstract}" if abstract else f.stem
                pairs.append((f.stem, label))
    pairs.sort(key=lambda x: x[0])
    if not pairs:
        return [], []
    ids, labels = zip(*pairs)
    return list(ids), list(labels)


def _print_columns(
    items: list[str],
    columns: int | None = None,
    col_width: int | None = None,
) -> None:
    """
    Print *items* as a numbered list, auto-selecting column count by size.

    Column count auto-detection (when *columns* is ``None``):
    fewer than 20 items → 1 column; fewer than 40 → 2 columns; 40+ → 3 columns.
    """
    n = len(items)
    if columns is None:
        if n < 20:
            columns, col_width = 1, None
        elif n < 40:
            columns = 2
            col_width = col_width or 40
        else:
            columns = _COLUMNS
            col_width = col_width or _COL_WIDTH
    elif col_width is None:
        col_width = _COL_WIDTH

    for i, name in enumerate(items):
        label = f"[{i + 1:2d}] {name}"
        if columns == 1:
            print(f"  {label}")
        else:
            print(f"  {label:<{col_width}}", end="")
            if (i + 1) % columns == 0:
                print()
    if columns > 1 and n % columns != 0:
        print()
    print()


def _field_header(label: str) -> None:
    """Print a lightweight field section separator."""
    width = BAR_SIZE - 4
    print(f"\n  {label}")
    print("  " + "-" * width)


def _ask_text(label: str) -> str | None:
    """
    Prompt for a free-text value.

    :param label: Field name shown in the prompt.
    :returns: Entered string, or ``None`` when the user skips.
    :raises _Quit: When the user enters ``q``.
    """
    raw = input(f"  {label}  [ENTER=skip  q=quit]: ").strip()
    if raw.lower() == "q":
        raise _Quit()
    return raw or None


def _pick_item(
    names: list[str],
    label: str,
    display: list[str] | None = None,
    columns: int | None = None,
    col_width: int | None = None,
) -> str | None:
    """
    Interactive picker with alphabetical navigation and numbered selection.

    :param names: Sorted list of candidate names (used for filtering and return value).
    :param label: Field name used in display and prompts.
    :param display: Optional display labels parallel to *names*. When provided,
        these strings appear in the numbered list while *names* values are
        returned on selection.
    :param columns: Number of columns. ``None`` auto-detects from list length.
    :param col_width: Column width for alignment. ``None`` auto-detects.
    :returns: Selected name from *names*, or ``None`` when the user skips.
    :raises _Quit: When the user enters ``q``.
    """
    _field_header(label)

    if not names:
        print(get_message(f"No {label} entries available — skipping."))
        return None

    _display = display if display is not None else names

    while True:
        letter = input("  Jump to letter  [A-Z / ENTER=show all / 0=skip]: ").strip()

        if letter == "0":
            return None

        if letter == "":
            filtered_names = names
            filtered_display = _display
        else:
            pairs = [
                (n, d)
                for n, d in zip(names, _display)
                if n.upper().startswith(letter.upper())
            ]
            if not pairs:
                print(f"  No entries starting with '{letter.upper()}'. Try again.\n")
                continue
            filtered_names, filtered_display = map(list, zip(*pairs))

        _print_columns(items=filtered_display, columns=columns, col_width=col_width)

        choice = input(
            f"  Select  [1-{len(filtered_names)} / 0=skip / b=back / q=quit]: "
        ).strip()

        if choice.lower() == "q":
            raise _Quit()
        if choice == "0":
            return None
        if choice.lower() == "b":
            continue  # restart loop — back to letter prompt

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(filtered_names):
                selected = filtered_names[idx]
                print(get_message(f"Selected: {selected}"))
                return selected
            print(f"  Out of range (1–{len(filtered_names)}). Try again.\n")
        except ValueError:
            print("  Enter a number.\n")


def _pick_party(
    org_names: list[str],
    sapiens_names: list[str],
    label: str,
) -> tuple[str | None, str | None]:
    """
    Interactive picker for a project party (contractor or client).

    Asks whether the party is an organization or a human (sapiens), then
    picks from the appropriate list. For humans, also asks whether the
    sapiens contact is the same person or someone else.

    :param org_names: Sorted list of organization names.
    :param sapiens_names: Sorted list of sapiens (person) names.
    :param label: Field label shown in headers and prompts.
    :returns: Tuple of ``(party_value, sapiens_contact_value)``.
    :raises _Quit: When the user enters ``q``.
    """
    _field_header(label)
    print("  [O] Organization   [H] Human (sapiens)   [0] Skip")
    print()

    while True:
        kind = input("  Type  [O/H / 0=skip / q=quit]: ").strip().lower()
        if kind == "q":
            raise _Quit()
        if kind == "0":
            return None, None
        if kind == "o":
            party = _pick_item(names=org_names, label=f"{label} (organization)")
            if party is None:
                return None, None
            sapiens = _pick_item(names=sapiens_names, label=f"{label} contact")
            return party, sapiens
        if kind == "h":
            party = _pick_item(names=sapiens_names, label=f"{label} (human)")
            if party is None:
                return None, None
            print()
            print(f"  Contact for {label}: same person ({party})?")
            print()
            while True:
                ans = (
                    input("  [y=same / n=pick another / 0=skip / q=quit]: ")
                    .strip()
                    .lower()
                )
                if ans == "q":
                    raise _Quit()
                if ans == "0":
                    return party, None
                if ans in ("y", ""):
                    return party, party
                if ans == "n":
                    sapiens = _pick_item(names=sapiens_names, label=f"{label} contact")
                    return party, sapiens
                print("  Enter y, n, or 0.\n")
        print("  Enter O, H, or 0.\n")


def _list_branches(vault: Path, folder_system: str) -> list[dict]:
    """
    Scan *vault* and return branch info dicts sorted by name.

    For ``alphanumerical``, branches are directories whose name ends in ``000``.
    For ``default``, all top-level directories in the vault are treated as branches.

    :param vault: Root vault directory.
    :param folder_system: ``"alphanumerical"`` or ``"default"``.
    :returns: List of dicts with keys ``name``, ``path``, ``branch``,
        ``project_count``.
    :rtype: list[dict]
    """
    branches = []
    if not vault.exists():
        return branches
    for item in sorted(vault.iterdir()):
        if not item.is_dir():
            continue
        if folder_system == "alphanumerical":
            if not item.name.endswith("000"):
                continue
            branch_prefix = item.name[:-3]
        else:
            branch_prefix = item.name
        count = sum(
            1
            for sub in item.iterdir()
            if sub.is_dir() and re.sub(r"^\D*", "", sub.name[len(branch_prefix) :])
        )
        branches.append(
            {
                "name": item.name,
                "path": item,
                "branch": branch_prefix,
                "project_count": count,
            }
        )
    return branches


def _pick_branch(
    vault: Path,
    folder_system: str,
) -> tuple[str, str, Path]:
    """
    Interactive branch picker.

    Lists existing branches in *vault*. The user selects one or creates a
    new one with ``+``.

    :param vault: Root vault directory.
    :param folder_system: ``"alphanumerical"`` or ``"default"``.
    :returns: Tuple of ``(branch, branch_folder, branch_path)``.
    :raises _Quit: When the user enters ``q``.
    """
    while True:
        branches = _list_branches(vault=vault, folder_system=folder_system)

        heading_subsection("Select branch")
        if branches:
            for i, b in enumerate(branches):
                n = b["project_count"]
                label = f"({n} project{'s' if n != 1 else ''})"
                print(f"  [{i + 1:2d}]  {b['name']:<24}  {label}")
        else:
            print(get_message("No branches found — use [+] to create one."))
        print(f"  [+]   Create new branch")
        print()

        n_branches = len(branches)
        range_hint = f"1-{n_branches} / " if n_branches else ""
        choice = input(f"  Select  [{range_hint}+ / q=quit]: ").strip()

        if choice.lower() == "q":
            raise _Quit()

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
            if folder_system == "alphanumerical":
                branch_folder = f"{raw}000"
                branch = raw
            else:
                branch_folder = raw
                branch = raw
            branch_path = vault / branch_folder
            branch_path.mkdir(parents=True, exist_ok=True)
            print(get_message(f"Created : {branch_path}"))
            return branch, branch_folder, branch_path

        try:
            idx = int(choice) - 1
            if 0 <= idx < n_branches:
                b = branches[idx]
                return b["branch"], b["name"], b["path"]
            print(f"  Out of range (1–{n_branches}). Try again.\n")
        except ValueError:
            print("  Enter a number, +, or q.\n")


def main() -> None:
    heading_section("ADD NEW PROJECT")

    args = get_arguments()
    tool_cfg = _load_config(source=args.config)

    if "vault" not in tool_cfg:
        raise ValueError(
            f"Tool config missing required key: 'vault'. "
            f"Keys found: {list(tool_cfg.keys())}. "
            "If using TOML, ensure these keys are not nested under a [section] header."
        )

    vault = Path(tool_cfg["vault"])
    folder_system = tool_cfg.get("folder_system", "default")
    separator = tool_cfg.get("separator", "") or ""
    sources_file = tool_cfg.get("sources", None)

    # Load available names from sources for interactive pickers
    # ----------------------------------------------------------------
    org_names: list[str] = []
    sapiens_names: list[str] = []
    service_ids: list[str] = []
    service_labels: list[str] = []

    if sources_file:
        try:
            src_cfg = _load_config(source=sources_file)
            search = src_cfg.get("folders", {}).get("search", {})
            org_names = _collect_names(directories=search.get("organizations", []))
            sapiens_names = _collect_names(directories=search.get("sapiens", []))
            service_ids, service_labels = _collect_services(
                directories=search.get("services", [])
            )
        except Exception as exc:
            print(
                get_warning(f"Could not load sources ({exc}) — pickers will be empty.")
            )

    try:
        # Pick branch
        # ----------------------------------------------------------------
        branch, branch_folder, branch_path = _pick_branch(
            vault=vault,
            folder_system=folder_system,
        )

        # Compute next project name for chosen branch
        # ----------------------------------------------------------------
        eff_separator = "" if folder_system == "alphanumerical" else separator
        project_name = _next_increment(
            branch_path=branch_path,
            branch=branch,
            separator=eff_separator,
        )

        # Show next project info
        # ----------------------------------------------------------------
        heading_subsection("Next project")
        print(get_message(f"Branch   : {branch_folder}"))
        print(get_message(f"Name     : {project_name}"))
        print(get_message(f"Location : {branch_path / project_name}"))
        print()

        confirm = (
            input("  Proceed?  [ENTER=yes / s=skip details / q=quit]: ").strip().lower()
        )

        if confirm == "q":
            print("\n  Aborted.\n")
            return

        skip_details = confirm == "s"

        # Interactive metadata fields
        # ----------------------------------------------------------------
        title = None
        alias = None
        contractor = None
        contractor_sapiens = None
        client = None
        client_sapiens = None
        service_id = None

        if not skip_details:
            _field_header("Title")
            title = _ask_text(label="Title")

            _field_header("Alias")
            alias = _ask_text(label="Alias")

            contractor, contractor_sapiens = _pick_party(
                org_names=org_names,
                sapiens_names=sapiens_names,
                label="Contractor",
            )
            client, client_sapiens = _pick_party(
                org_names=org_names,
                sapiens_names=sapiens_names,
                label="Client",
            )
            service_id = _pick_item(
                names=service_ids,
                label="Service",
                display=service_labels,
            )

        # Build project config dict
        # ----------------------------------------------------------------
        project_config: dict = {
            "folder_base": str(vault),
            "branch": branch_folder,
            "name": project_name,
        }
        if alias:
            project_config["alias"] = alias
        if sources_file:
            project_config["sources"] = sources_file
        if title:
            project_config["title"] = title
        if contractor:
            project_config["contractor"] = contractor
        if contractor_sapiens:
            project_config["contractor_sapiens"] = contractor_sapiens
        if client:
            project_config["client"] = client
        if client_sapiens:
            project_config["client_sapiens"] = client_sapiens
        if service_id:
            project_config["service_id"] = service_id
        if "language" in tool_cfg:
            project_config["language"] = tool_cfg["language"]

        # Create
        # ----------------------------------------------------------------
        heading_subsection("Creating project")
        losalamos.new_project(config=project_config)

        heading_subsection("Done")
        print(get_message(f"Project  : {project_name}"))
        print(get_message(f"Location : {branch_path / project_name}"))
        if title:
            print(get_message(f"Title    : {title}"))
        print()

    except _Quit:
        print("\n  Aborted.\n")


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":
    main()
