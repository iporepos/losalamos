# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Create a new numbered project inside a project folder group.

Reads a tool config file (YAML, TOML, or JSON) that sets the base folder,
folder prefix, and optional path to a shared sources config. Presents an
interactive terminal session to fill in project metadata fields, then calls
:func:`losalamos.new_project`.

**Shell usage**

.. code-block:: bash

    python -m losalamos.tools.add_new_project --config path/to/config.yaml

**Tool config keys**

- ``basefolder`` (*str*, required) — root directory where project group folders live.
- ``prefix`` (*str*, required) — string prefix for project folders, e.g. ``C`` or ``Projects-Consulting-``.
- ``sources`` (*str*, optional) — path to a shared sources config file
  (copied into each new project's ``admin/config/``).

**Interaction keys**

- ``ENTER`` on an empty prompt — skip the current field.
- ``s`` at the project confirmation — skip all optional fields and create immediately.
- ``b`` after a filtered list — go back to the letter filter.
- ``q`` at any prompt — abort and exit.

.. dropdown:: Example — tool config file
    :icon: code-square
    :open:

    TOML and JSON are also accepted. Save a ``add_project.yaml`` and pass it with ``--config``:

    .. code-block:: yaml

        # Root directory that holds all project group folders.
        # The tool resolves the group folder as <basefolder>/<prefix>000.
        # Quote paths that contain spaces or a literal '#'.
        basefolder: "C:/My Drive/projects"

        # Prefix that identifies the project folder group.
        # Can be a single letter (e.g. C) or any string (e.g. Projects-Consulting-).
        prefix: C

        # Path to the shared sources config file.
        # The file is copied into admin/config/ of every new project so that
        # Project.update() can resolve contractor, client, and service notes.
        sources: "C:/vault/sources.yaml"

        # BCP-47 language tag written into each new project note.
        # Controls document type labels (e.g. "invoice" → "Cobrança" for pt-br).
        # Defaults to "en" when omitted.
        language: pt-br

"""

# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
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


def _next_increment(collection_path: Path, prefix: str, width: int = 3) -> str:
    """
    Scan *collection_path* and return the next available project name.

    :param collection_path: Directory containing sibling project folders.
    :param prefix: Folder name prefix, e.g. ``"C"`` or ``"Projects-Consulting-"``.
    :param width: Zero-pad width for the numeric suffix.
    :returns: Next project name, e.g. ``"C003"``.
    :rtype: str
    """
    numbers = []
    if collection_path.exists():
        for item in collection_path.iterdir():
            if item.is_dir() and item.name.lower().startswith(prefix.lower()):
                suffix = item.name[len(prefix) :]
                if suffix.isdigit():
                    numbers.append(int(suffix))
    next_num = max(numbers) + 1 if numbers else 1
    return f"{prefix}{str(next_num).zfill(width)}"


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
                meta = NoteBasic.parse_metadata(note_file=f)
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
    columns: int = _COLUMNS,
    col_width: int = _COL_WIDTH,
) -> None:
    """Print *items* as a numbered multi-column list."""
    for i, name in enumerate(items):
        label = f"[{i + 1:2d}] {name}"
        print(f"  {label:<{col_width}}", end="")
        if (i + 1) % columns == 0:
            print()
    if len(items) % columns != 0:
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
    columns: int = _COLUMNS,
    col_width: int = _COL_WIDTH,
) -> str | None:
    """
    Interactive picker with alphabetical navigation and numbered selection.

    :param names: Sorted list of candidate names (used for filtering and return value).
    :param label: Field name used in display and prompts.
    :param display: Optional display labels parallel to *names*. When provided,
        these strings appear in the numbered list while *names* values are
        returned on selection.
    :param columns: Number of columns in the list display.
    :param col_width: Column width for alignment.
    :returns: Selected name from *names*, or ``None`` when the user skips.
    :raises _Quit: When the user enters ``q``.
    """
    _field_header(label)

    if not names:
        print(get_message(f"No {label} entries available — skipping."))
        return None

    _display = display if display is not None else names

    while True:
        letter = input("  Jump to letter  [A-Z / ENTER=show all / q=skip]: ").strip()

        if letter.lower() == "q":
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
            f"  Select  [1-{len(filtered_names)} / ENTER=skip / b=back / q=quit]: "
        ).strip()

        if choice.lower() == "q":
            raise _Quit()
        if choice == "":
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


def main() -> None:
    heading_section("ADD NEW PROJECT")

    args = get_arguments()
    tool_cfg = _load_config(source=args.config)

    for key in ("basefolder", "prefix"):
        if key not in tool_cfg:
            raise ValueError(f"Tool config missing required key: '{key}'")

    basefolder = Path(tool_cfg["basefolder"])
    prefix = tool_cfg["prefix"]
    sources_file = tool_cfg.get("sources", None)

    # Resolve group folder and next project name
    # ----------------------------------------------------------------
    collection_path = basefolder / f"{prefix}000"
    project_name = _next_increment(
        collection_path=collection_path,
        prefix=prefix,
    )

    # Load available names from sources for interactive pickers
    # ----------------------------------------------------------------
    org_names: list[str] = []
    sapiens_names: list[str] = []
    service_ids: list[str] = []
    service_labels: list[str] = []

    if sources_file:
        try:
            src_cfg = _load_config(source=sources_file)
            org_names = _collect_names(directories=src_cfg.get("organizations", []))
            sapiens_names = _collect_names(directories=src_cfg.get("sapiens", []))
            service_ids, service_labels = _collect_services(
                directories=src_cfg.get("services", [])
            )
        except Exception as exc:
            print(
                get_warning(f"Could not load sources ({exc}) — pickers will be empty.")
            )

    # Show next project info
    # ----------------------------------------------------------------
    heading_subsection("Next project")
    print(get_message(f"Prefix   : {prefix}"))
    print(get_message(f"Name     : {project_name}"))
    print(get_message(f"Location : {collection_path / project_name}"))
    print()

    try:
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

            contractor = _pick_item(names=org_names, label="Contractor")
            contractor_sapiens = _pick_item(
                names=sapiens_names,
                label="Contractor contact",
            )
            client = _pick_item(names=org_names, label="Client")
            client_sapiens = _pick_item(
                names=sapiens_names,
                label="Client contact",
            )
            service_id = _pick_item(
                names=service_ids,
                label="Service",
                display=service_labels,
                columns=2,
                col_width=42,
            )

        # Build project config dict
        # ----------------------------------------------------------------
        project_config: dict = {
            "folder_base": str(collection_path),
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
        print(get_message(f"Location : {collection_path / project_name}"))
        if title:
            print(get_message(f"Title    : {title}"))
        print()

    except _Quit:
        print("\n  Aborted.\n")


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":
    main()
