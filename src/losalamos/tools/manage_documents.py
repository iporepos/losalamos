# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Terminal document manager for a project folder group.

Reads a tool config file (YAML, TOML, or JSON) that sets the base folder
and folder prefix. Presents an interactive project picker, then a
per-project home page to add, edit, or build asset documents (invoices,
receipts, proposals).

**Shell usage**

.. code-block:: bash

    python -m losalamos.tools.manage_documents --config path/to/config.yaml

**Tool config keys**

- ``basefolder`` (*str*, required) — root directory where project group folders live.
- ``prefix`` (*str*, required) — string prefix for project folders, e.g. ``C`` or ``Projects-Consulting-``.

**Navigation**

- Project list: enter a number to open, ``q`` to quit.
- Home page: ``A`` add / ``E`` edit / ``B`` build / ``P`` back to projects / ``Q`` quit.
- Confirmation: ``ENTER`` or ``y`` to confirm, ``c`` to cancel, ``q`` to quit the tool.

.. dropdown:: Example — tool config file
    :icon: code-square
    :open:

    TOML and JSON are also accepted.

    .. code-block:: yaml

        # Root directory that holds all project group folders.
        basefolder: "C:/My Drive/projects"

        # Prefix that identifies the project folder group.
        # Can be a single letter (e.g. C) or any string (e.g. Projects-Consulting-).
        prefix: C

"""

# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import os
import shutil
import argparse
import platform
import subprocess
import webbrowser
from pathlib import Path

# Project-level imports
# =======================================================================
import losalamos
from losalamos.notes import NoteBasic
from losalamos.project import _load_config
from losalamos.tools.core import *


# CONSTANTS
# ***********************************************************************

# Document asset types handled by this tool (uppercase)
_ASSET_TYPES = ["INVOICE", "RECEIPT", "PROPOSAL"]

# Project-relative subfolder for each asset type
_SUBFOLDER = {
    "INVOICE": "budget/documents",
    "RECEIPT": "budget/documents",
    "PROPOSAL": "admin/proposals",
}

# Add-method names on Project, keyed by asset type
_ADD_METHOD = {
    "INVOICE": "add_invoice",
    "RECEIPT": "add_receipt",
    "PROPOSAL": "add_proposal",
}

# Build-method names on Project, keyed by asset type
_BUILD_METHOD = {
    "INVOICE": "build_invoice",
    "RECEIPT": "build_receipt",
    "PROPOSAL": "build_proposal",
}


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
        description="Terminal document manager for a project folder group.",
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        help="Path to the tool config file (.yaml, .toml, or .json).",
    )
    return parser.parse_args()


def _load_projects(collection_path: Path, prefix: str) -> list[dict]:
    """
    Scan *collection_path* and return project info dicts sorted by name.

    :param collection_path: Directory containing sibling project folders.
    :param prefix: Folder name prefix, e.g. ``"C"`` or ``"Projects-Consulting-"``.
    :returns: List of dicts with keys ``name``, ``path``, ``title``.
    :rtype: list[dict]
    """
    projects = []
    if not collection_path.exists():
        return projects
    for item in sorted(collection_path.iterdir()):
        if not item.is_dir():
            continue
        tail = item.name[len(prefix) :]
        if item.name.upper().startswith(prefix.upper()) and tail.isdigit():
            title = _read_project_title(project_path=item, name=item.name)
            projects.append({"name": item.name, "path": item, "title": title})
    return projects


def _read_project_title(project_path: Path, name: str) -> str:
    """Read the title from a project's main note without loading the full project."""
    note_file = project_path / f"{name}.md"
    if not note_file.is_file():
        return "—"
    meta = NoteBasic.parse_metadata(note_file=note_file)
    title = str(meta.get("title") or "").strip("\"'").strip()
    return title if title else "—"


def _print_projects(projects: list[dict]) -> None:
    """Print a numbered project list."""
    print()
    for i, p in enumerate(projects):
        idx = f"[{i + 1:2d}]"
        title = p["title"]
        if len(title) > 45:
            title = title[:42] + "..."
        print(f"  {idx}  {p['name']:<10}  {title}")
    print()


def _print_documents(doc_df) -> None:
    """Print a numbered document list with name and relative folder path."""
    if doc_df.empty:
        print(get_message("No documents found."))
        print()
        return
    for i, row in doc_df.iterrows():
        idx = f"[{i + 1:2d}]"
        asset_type = str(row["asset_type"]).upper()
        subfolder = _SUBFOLDER.get(asset_type, "?")
        rel_path = f"{subfolder}/{row['name']}"
        print(f"  {idx}  {row['asset_id']:<6}  {row['name']:<32}  {rel_path}")
    print()


def _active_documents(doc_df, folder_root: Path):
    """
    Filter *doc_df* to rows whose document folder still exists on disk.

    Tombstone asset notes (folder deleted, note kept for numbering) are
    excluded so they never appear in the UI.

    :param doc_df: DataFrame from :meth:`~losalamos.Project.get_assets`.
    :param folder_root: Project root path.
    :returns: Filtered and re-indexed DataFrame.
    """

    def _exists(row):
        subfolder = _SUBFOLDER.get(str(row["asset_type"]).upper(), "")
        return (Path(folder_root) / subfolder / str(row["name"])).is_dir()

    return doc_df[doc_df.apply(_exists, axis=1)].reset_index(drop=True)


def _pick_document(doc_df, label: str = "Select document") -> dict | None:
    """
    Prompt the user to select a document from *doc_df*.

    :param doc_df: DataFrame returned by :meth:`~losalamos.Project.get_assets`.
    :param label: Prompt label.
    :returns: Row dict of the selected document, or ``None`` to cancel.
    :raises _Quit: When the user enters ``q``.
    """
    if doc_df.empty:
        print(get_message("No documents available."))
        return None

    while True:
        choice = input(
            f"  {label}  [1-{len(doc_df)} / ENTER=cancel / q=quit]: "
        ).strip()
        if choice.lower() == "q":
            raise _Quit()
        if choice == "":
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(doc_df):
                return doc_df.iloc[idx].to_dict()
            print(f"  Out of range (1–{len(doc_df)}). Try again.\n")
        except ValueError:
            print("  Enter a number.\n")


def _confirm(prompt: str = "Confirm?") -> bool:
    """
    Ask for a yes/cancel/quit confirmation.

    :returns: ``True`` when confirmed, ``False`` when cancelled.
    :raises _Quit: When the user enters ``q``.
    """
    answer = input(f"  {prompt}  [ENTER=confirm / c=cancel / q=quit]: ").strip().lower()
    if answer == "q":
        raise _Quit()
    return answer in ("", "y")


def _open_in_explorer(path: Path) -> None:
    """Open *path* in the OS file explorer."""
    system = platform.system()
    if system == "Windows":
        os.startfile(str(path))
    elif system == "Darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def _action_add(pj) -> None:
    """Interactive add-document flow."""
    heading_subsection("Add document")
    print("  [I] Invoice   [R] Receipt   [P] Proposal")
    print()
    choice = input("  Select type  [I/R/P / ENTER=cancel / q=quit]: ").strip().lower()

    if choice == "q":
        raise _Quit()
    if choice == "":
        return

    type_map = {"i": "INVOICE", "r": "RECEIPT", "p": "PROPOSAL"}
    if choice not in type_map:
        print(get_warning("Invalid choice."))
        return

    asset_type = type_map[choice]
    kwargs = {}

    # For receipts, offer an optional invoice link
    if asset_type == "RECEIPT":
        all_df = pj.get_assets()
        inv_df = all_df[all_df["asset_type"].str.upper() == "INVOICE"].reset_index(
            drop=True
        )

        if not inv_df.empty:
            print()
            print("  Link to an existing invoice? (optional)")
            _print_documents(inv_df)
            sel = _pick_document(doc_df=inv_df, label="Select invoice")
            if sel is not None:
                kwargs["invoice_id"] = sel["asset_id"]

    print()
    print(get_message(f"Action  : add {asset_type}"))
    if kwargs.get("invoice_id"):
        print(get_message(f"Linked  : {kwargs['invoice_id']}"))
    print()

    if not _confirm():
        print(get_message("Cancelled."))
        return

    method = getattr(pj, _ADD_METHOD[asset_type])
    method(**kwargs)
    print(get_message(f"{asset_type} created."))


def _action_edit(pj, doc_df) -> None:
    """Interactive edit-document flow: open the TeX folder in the file explorer."""
    heading_subsection("Edit document")
    _print_documents(doc_df)
    row = _pick_document(doc_df=doc_df)
    if row is None:
        return

    asset_type = str(row["asset_type"]).upper()
    name = row["name"]
    subfolder = _SUBFOLDER.get(asset_type, "inputs/documents")
    doc_folder = Path(pj.folder_root) / subfolder / name

    if not doc_folder.is_dir():
        print(get_warning(f"Folder not found: '{doc_folder}'"))
        return

    print()
    print(get_message(f"Opening : {doc_folder}"))
    _open_in_explorer(path=doc_folder)
    input("\n  Press ENTER when done editing... ")


def _action_view(pj, doc_df) -> None:
    """Interactive view-PDF flow: open the latest compiled PDF in the default viewer."""
    heading_subsection("View PDF")
    _print_documents(doc_df)
    row = _pick_document(doc_df=doc_df)
    if row is None:
        return

    asset_type = str(row["asset_type"]).upper()
    name = row["name"]
    subfolder = _SUBFOLDER.get(asset_type, "inputs/documents")
    doc_dir = Path(pj.folder_root) / subfolder

    candidates = sorted(
        doc_dir.glob(f"{name}_V*.pdf"),
        key=lambda p: p.stat().st_mtime,
    )

    if not candidates:
        print()
        print(get_warning(f"No PDF found for '{name}'. Build it first."))
        print()
        return

    pdf = candidates[-1]
    print()
    print(get_message(f"Opening : {pdf.name}"))
    webbrowser.open(pdf.as_uri())


def _action_build(pj, doc_df) -> None:
    """Interactive build-document flow: compile to PDF."""
    heading_subsection("Build document")
    _print_documents(doc_df)
    row = _pick_document(doc_df=doc_df)
    if row is None:
        return

    asset_type = str(row["asset_type"]).upper()
    file_id = row["asset_id"]

    print()
    print(get_message(f"Action  : build {asset_type}  {file_id}"))
    print()

    if not _confirm():
        print(get_message("Cancelled."))
        return

    method = getattr(pj, _BUILD_METHOD[asset_type])
    pdf = method(file_id=file_id)
    print(get_message(f"PDF     : {pdf}"))


def _action_delete(pj, doc_df) -> None:
    """
    Interactive delete-document flow.

    Removes the document TeX folder and any compiled PDFs. The sidecar
    asset note is kept as a tombstone so the asset ID is never reused.
    """
    heading_subsection("Delete document")
    _print_documents(doc_df)
    row = _pick_document(doc_df=doc_df)
    if row is None:
        return

    asset_type = str(row["asset_type"]).upper()
    name = row["name"]
    subfolder = _SUBFOLDER.get(asset_type, "inputs/documents")
    doc_dir = Path(pj.folder_root) / subfolder
    doc_folder = doc_dir / name
    pdfs = sorted(doc_dir.glob(f"{name}_V*.pdf"))

    print()
    print(get_message(f"Delete  : {doc_folder}"))
    for pdf in pdfs:
        print(get_message(f"Delete  : {pdf.name}"))
    print(get_message("Keep    : sidecar note (legacy for ID numbering)"))
    print()

    if not _confirm(prompt="Confirm delete? This cannot be undone."):
        print(get_message("Cancelled."))
        return

    shutil.rmtree(str(doc_folder))
    for pdf in pdfs:
        pdf.unlink()

    print(get_message(f"Deleted : {name}"))


def _home(pj, project_info: dict) -> str:
    """
    Home page loop for a selected project.

    Reloads the project on each iteration so the document list is always
    current after an add or build action.

    :returns: ``"quit"`` to exit the tool or ``"projects"`` to return to the list.
    """
    while True:
        pj.update()
        all_df = pj.get_assets()
        doc_df = _active_documents(
            doc_df=all_df[
                all_df["asset_type"].str.upper().isin(_ASSET_TYPES)
            ].reset_index(drop=True),
            folder_root=pj.folder_root,
        )

        heading_subsection(f"{project_info['name']}  —  {project_info['title']}")
        _print_documents(doc_df)

        print(
            "  [A] Add document    [E] Edit document    [B] Build document    [V] View PDF"
        )
        print(
            "  [D] Delete document [P] Back to projects                      [Q] Quit"
        )
        print()

        choice = input("  Select: ").strip().lower()
        print()

        if choice == "q":
            return "quit"
        if choice == "p":
            return "projects"
        if choice == "a":
            _action_add(pj=pj)
        elif choice == "e":
            _action_edit(pj=pj, doc_df=doc_df)
        elif choice == "b":
            _action_build(pj=pj, doc_df=doc_df)
        elif choice == "v":
            _action_view(pj=pj, doc_df=doc_df)
        elif choice == "d":
            _action_delete(pj=pj, doc_df=doc_df)


def main() -> None:
    heading_section("DOCUMENT MANAGER")

    args = get_arguments()
    tool_cfg = _load_config(source=args.config)

    for key in ("basefolder", "prefix"):
        if key not in tool_cfg:
            raise ValueError(f"Tool config missing required key: '{key}'")

    basefolder = Path(tool_cfg["basefolder"])
    prefix = tool_cfg["prefix"]
    collection_path = basefolder / f"{prefix}000"

    try:
        while True:
            projects = _load_projects(
                collection_path=collection_path,
                prefix=prefix,
            )

            if not projects:
                print(get_warning(f"No projects found in '{collection_path}'."))
                break

            heading_subsection("Projects")
            _print_projects(projects=projects)

            choice = input(f"  Select project  [1-{len(projects)} / q=quit]: ").strip()

            if choice.lower() == "q":
                break

            try:
                idx = int(choice) - 1
                if not (0 <= idx < len(projects)):
                    print(f"  Out of range (1–{len(projects)}).\n")
                    continue
            except ValueError:
                print("  Enter a number.\n")
                continue

            selected = projects[idx]
            pj = losalamos.load_project(project_folder=str(selected["path"]))

            result = _home(pj=pj, project_info=selected)
            if result == "quit":
                break
            # "projects" → loop back to project list

    except _Quit:
        pass

    print("\n  Goodbye.\n")


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":
    main()
