# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Terminal document manager for a single project.

Accepts a project folder path and presents the document home page for that
project directly. Project and branch navigation is handled by the higher-level
:mod:`losalamos.tools.manage_vault` tool.

**Shell usage**

.. code-block:: bash

    python -m losalamos.tools.manage_documents path/to/project/folder

**Navigation**

- Home page: ``A`` add / ``E`` edit / ``B`` build / ``V`` view PDF /
  ``D`` delete / ``P`` back / ``Q`` quit.
- Confirmation: ``ENTER`` or ``y`` to confirm, ``c`` to cancel, ``q`` to quit.

"""

# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import re
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
from losalamos.documents import LatexCompileError, DOCUMENT_TYPES
from losalamos.tools.core import *


# CONSTANTS
# ***********************************************************************

# Document asset types handled by this tool (uppercase)
_ASSET_TYPES = ["INVOICE", "RECEIPT", "PROPOSAL", "REPORT"]

# Project-relative subfolder for each asset type (TeX source)
_SUBFOLDER = {
    "INVOICE": "inputs/documents",
    "RECEIPT": "inputs/documents",
    "PROPOSAL": "inputs/documents",
    "REPORT": "inputs/documents",
}

# Project-relative subfolder where each asset type's PDF and sidecar note live
_PDF_SUBFOLDER = {
    "INVOICE": "budget/inflows",
    "RECEIPT": "budget/inflows",
    "PROPOSAL": "admin/proposals",
    "REPORT": "outputs",
}

# Add-method names on Project, keyed by asset type
_ADD_METHOD = {
    "INVOICE": "add_invoice",
    "RECEIPT": "add_receipt",
    "PROPOSAL": "add_proposal",
    "REPORT": "add_report",
}

# Build-method names on Project, keyed by asset type
_BUILD_METHOD = {
    "INVOICE": "build_invoice",
    "RECEIPT": "build_receipt",
    "PROPOSAL": "build_proposal",
    "REPORT": "build_report",
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

    :returns: Parsed argument namespace with a ``source`` attribute.
    """
    parser = argparse.ArgumentParser(
        description="Terminal document manager for a single project.",
    )
    parser.add_argument(
        "source",
        help="Path to the project folder.",
    )
    return parser.parse_args()


def _load_projects(branch_path: Path, branch: str) -> list[dict]:
    """
    Scan *branch_path* and return project info dicts sorted by name.

    :param branch_path: Directory containing sibling project folders.
    :param branch: Branch name prefix, e.g. ``"Research"`` or ``"C"``.
    :returns: List of dicts with keys ``name``, ``path``, ``title``.
    :rtype: list[dict]
    """
    projects = []
    if not branch_path.exists():
        return projects
    for item in sorted(branch_path.iterdir()):
        if not item.is_dir():
            continue
        if not item.name.lower().startswith(branch.lower()):
            continue
        tail = item.name[len(branch) :]
        digits = re.sub(r"^\D*", "", tail)
        if digits:
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


def _active_documents(doc_df, folder_root: Path, folder_remote_documents=None):
    """
    Filter *doc_df* to rows whose document folder still exists on disk.

    Tombstone asset notes (folder deleted, note kept for numbering) are
    excluded so they never appear in the UI. Checks both the local project
    root and, when provided, the remote documents folder.

    :param doc_df: DataFrame from :meth:`~losalamos.Project.get_assets`.
    :param folder_root: Project root path.
    :param folder_remote_documents: Optional remote documents root path.
    :returns: Filtered and re-indexed DataFrame.
    """

    def _exists(row):
        subfolder = _SUBFOLDER.get(str(row["asset_type"]).upper(), "")
        name = str(row["name"])
        if (Path(folder_root) / subfolder / name).is_dir():
            return True
        if folder_remote_documents is not None:
            if (Path(folder_remote_documents) / subfolder / name).is_dir():
                return True
        return False

    return doc_df[doc_df.apply(_exists, axis=1)].reset_index(drop=True)


def _print_project_info(pj) -> None:
    """Print a compact metadata summary for the project."""

    def _get(key):
        val = pj.get_attribute(entry_key=key, clean_cref=True)
        return "" if val == f"[{key.upper()}]" else val

    fields = [
        ("Status", _get("status")),
        ("Alias", _get("alias")),
        ("Contractor", _get("contractor")),
        ("Client", _get("client")),
        ("Service", _get("service_id")),
        ("Revenue", _get("revenue_expected")),
        ("Start", _get("date_start")),
        ("End", _get("date_end")),
    ]
    for label, value in fields:
        if value:
            print(f"  {label:<12}: {value}")
    print()


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
    print("  [I] Invoice   [R] Receipt   [P] Proposal   [T] Report")
    print()
    choice = input("  Select type  [I/R/P/T / ENTER=cancel / q=quit]: ").strip().lower()

    if choice == "q":
        raise _Quit()
    if choice == "":
        return

    type_map = {"i": "INVOICE", "r": "RECEIPT", "p": "PROPOSAL", "t": "REPORT"}
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

    name = row["name"]
    try:
        doc_folder = pj._locate_document_source(name=name)
    except FileNotFoundError:
        print(get_warning(f"Folder not found for '{name}'"))
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
    pdf_subfolder = _PDF_SUBFOLDER.get(asset_type, "inputs/documents")
    doc_dir = Path(pj.folder_root) / pdf_subfolder

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
    try:
        pdf, zip_path = method(file_id=file_id)
    except LatexCompileError as exc:
        print()
        print(get_warning(f"Compile failed (exit {exc.returncode}): {exc}"))
        if exc.log_path and exc.log_path.exists():
            print(get_message(f"Log     : {exc.log_path}"))
        print()
        return
    print(get_message(f"PDF     : {pdf}"))
    print(get_message(f"Source  : {zip_path}"))


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

    name = row["name"]
    try:
        doc_folder = pj._locate_document_source(name=name)
    except FileNotFoundError:
        print(get_warning(f"Folder not found for '{name}'"))
        return

    asset_type = str(row["asset_type"]).upper()
    pdf_subfolder = _PDF_SUBFOLDER.get(asset_type, "inputs/documents")
    local_pdf_dir = Path(pj.folder_root) / pdf_subfolder
    pdfs = sorted(local_pdf_dir.glob(f"{name}_V*.pdf"))

    print()
    print(get_message(f"Delete  : {doc_folder}"))
    for pdf in pdfs:
        print(get_message(f"Delete  : {pdf.name}"))
    print(get_message("Keep    : sidecar note (legacy for ID numbering)"))
    print()

    if not _confirm(prompt="Confirm delete? This cannot be undone."):
        print(get_message("Cancelled."))
        return

    try:
        shutil.rmtree(str(doc_folder))
    except OSError as exc:
        print()
        print(get_warning(f"Could not delete folder: {exc.strerror}"))
        print(
            get_warning(
                "Close any file explorer windows or PDF viewers inside that folder and try again."
            )
        )
        return
    for pdf in pdfs:
        pdf.unlink()

    print(get_message(f"Deleted : {name}"))


def _action_reset(pj, doc_df) -> None:
    """
    Interactive reset-document flow: erase the TeX folder and recreate from template.

    Applies the same standard overlays used at creation time. All manual
    edits inside the document folder are permanently lost.
    """
    heading_subsection("Reset document")
    _print_documents(doc_df)
    row = _pick_document(doc_df=doc_df)
    if row is None:
        return

    name = row["name"]
    asset_type = str(row["asset_type"]).upper()

    try:
        doc_folder = pj._locate_document_source(name=name)
    except FileNotFoundError:
        print(get_warning(f"Folder not found for '{name}'"))
        return

    print()
    print(
        get_warning(
            f"ALL EDITS in '{name}' will be permanently erased and recreated from template."
        )
    )
    print()

    if not _confirm(prompt="First confirmation — reset document?"):
        print(get_message("Cancelled."))
        return

    if not _confirm(prompt="Second confirmation — all edits will be lost. Proceed?"):
        print(get_message("Cancelled."))
        return

    subfolder = doc_folder.parent
    template_overlay = (
        pj.sources.get("templates", {})
        .get("documents", {})
        .get(asset_type.lower(), None)
    )

    try:
        shutil.rmtree(str(doc_folder))
    except OSError as exc:
        print()
        print(get_warning(f"Could not delete folder: {exc.strerror}"))
        print(
            get_warning(
                "Close any file explorer windows or PDF viewers inside that folder and try again."
            )
        )
        return

    pj.add_document(
        document_type=asset_type.lower(),
        name=name,
        template_overlay=template_overlay,
        files_overlay=pj._standard_files_overlay(),
        subfolder=str(subfolder),
        condensed=False,
        compile_pdf=False,
    )
    pj._patch_project_tex(
        doc_folder=doc_folder,
        file_id=row["asset_id"],
        asset_type=asset_type,
    )
    if asset_type in ("INVOICE", "RECEIPT", "PROPOSAL"):
        pj._patch_metadata_tex(doc_folder=doc_folder)
    print(get_message(f"Reset   : {name}"))


def _action_clean(pj, doc_df) -> None:
    """Interactive clean-document flow: remove latexmk auxiliary files."""
    heading_subsection("Clean document")
    _print_documents(doc_df)
    row = _pick_document(doc_df=doc_df)
    if row is None:
        return

    name = row["name"]
    asset_type = str(row["asset_type"]).upper()

    try:
        doc_folder = pj._locate_document_source(name=name)
    except FileNotFoundError:
        print(get_warning(f"Folder not found for '{name}'"))
        return

    main_tex = doc_folder / "main.tex"
    if not main_tex.is_file():
        print(get_warning(f"main.tex not found in '{doc_folder}'"))
        return

    print()
    print(get_message(f"Action  : clean {asset_type}  {name}"))
    print()

    if not _confirm():
        print(get_message("Cancelled."))
        return

    klass = DOCUMENT_TYPES.get(asset_type.lower())
    if klass is None:
        print(get_warning(f"Unknown document type: '{asset_type}'"))
        return

    doc = klass(name=name)
    doc.load_data(file_data=main_tex)
    doc.clean()
    pdf = main_tex.with_suffix(".pdf")
    if pdf.exists():
        pdf.unlink()
    print(get_message("Auxiliary files removed."))


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
            folder_remote_documents=pj.folder_remote_documents,
        )

        heading_subsection(f"{project_info['name']}  —  {project_info['title']}")
        _print_project_info(pj=pj)
        _print_documents(doc_df)

        print(
            "  [A] Add document    [E] Edit document    [B] Build document    [V] View PDF"
        )
        print(
            "  [D] Delete document [C] Clean document   [R] Reset document    [P] Back"
        )
        print("  [Q] Quit")
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
        elif choice == "c":
            _action_clean(pj=pj, doc_df=doc_df)
        elif choice == "r":
            _action_reset(pj=pj, doc_df=doc_df)
        elif choice == "d":
            _action_delete(pj=pj, doc_df=doc_df)


def run(project_folder: str, vault: str = None) -> None:
    """
    Open the document manager home page for a single project.

    Can be called directly (e.g. from :mod:`losalamos.tools.manage_vault`)
    or via :func:`main` when invoked from the command line.

    :param project_folder: Path to the project root folder.
    :type project_folder: str
    :param vault: Optional path to the vault root, passed to
        :func:`losalamos.load_project` for branch detection.
    :type vault: str or None
    """
    heading_section("DOCUMENT MANAGER")

    project_path = Path(project_folder)
    pj = losalamos.load_project(
        project_folder=str(project_path),
        vault=vault,
    )
    project_info = {
        "name": project_path.name,
        "title": _read_project_title(project_path=project_path, name=project_path.name),
    }

    try:
        _home(pj=pj, project_info=project_info)
    except _Quit:
        pass

    print("\n  Goodbye.\n")


def main() -> None:
    args = get_arguments()
    run(project_folder=args.source)


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":
    main()
