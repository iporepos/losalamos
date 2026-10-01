# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Terminal budget manager for a single project.

Accepts a project folder path and presents the transfer home page for that
project directly. Project and branch navigation is handled by the
higher-level :mod:`losalamos.tools.manage_vault` tool.

Transfers are the single entry point for billing: adding an inflow transfer
here always creates its invoice and receipt pair as a side effect (via
:meth:`losalamos.project.Project.add_inflow_transfer`). Those two documents
then show up in the document manager (:mod:`losalamos.tools.manage_documents`)
for editing, building, and viewing, but cannot be created from there directly.

**Shell usage**

.. code-block:: bash

    python -m losalamos.tools.manage_budget path/to/project/folder

**Navigation**

- Home page: ``I`` add inflow / ``O`` add outflow / ``P`` back / ``Q`` quit.
- Confirmation: ``ENTER`` or ``y`` to confirm, ``c`` to cancel, ``q`` to quit.

"""

# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import argparse
import calendar
import datetime
from pathlib import Path

# Project-level imports
# =======================================================================
import losalamos
from losalamos.notes import NoteBasic
from losalamos.tools.core import *
from losalamos.tools.new_project import (
    _collect_names,
    _pick_item,
    _Quit as _PartyQuit,
)
from losalamos.tools.manage_documents import _read_project_title


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
        description="Terminal budget manager for a single project.",
    )
    parser.add_argument(
        "source",
        help="Path to the project folder.",
    )
    return parser.parse_args()


def _print_transfers(transfer_df) -> None:
    """Print a numbered transfer list with direction, status, and value."""
    if transfer_df.empty:
        print(get_message("No transfers found."))
        print()
        return
    for i, row in transfer_df.iterrows():
        idx = f"[{i + 1:2d}]"
        direction = str(row["direction"] or "").upper()
        status = str(row["status"] or "")
        value = row["value"]
        date = row["date"] or ""
        print(
            f"  {idx}  {row['name']:<28}  {direction:<8}  {status:<10}  "
            f"{value!s:<10}  {date}"
        )
    print()


def _clean_link(value) -> str | None:
    """
    Strip YAML quotes and Obsidian ``[[...]]`` brackets from a stored link value.

    Fields read back from disk (e.g. via :meth:`~losalamos.project.Project.get_latest_transfer`)
    carry the raw wiki-link form (e.g. ``'[[Acme Corp]]'``). This recovers the
    plain name for display and for reuse as a fresh *payer*/*receiver* input.

    :param value: Raw stored field value, or ``None``/empty.
    :returns: Plain name, or ``None`` when *value* is falsy.
    """
    if not value:
        return None
    v = str(value).strip().strip("\"'")
    v = NoteBasic.clean_cref(entry_key=v)
    return v or None


def _ask_value(previous: float | None = None) -> float:
    """
    Prompt for the mandatory transfer value.

    :param previous: Value from the previous transfer of the same direction,
        offered as a one-key copy shortcut. ``None`` when there is none.
    :type previous: float or None
    :returns: Entered value as a float.
    :raises _Quit: When the user enters ``q``.
    """
    print()
    if previous is not None:
        print(f"  [P] Copy from previous ({previous})")
    options = "number" + (" / p=copy previous" if previous is not None else "")
    while True:
        raw = input(f"  Value (mandatory)  [{options} / q=quit]: ").strip()
        if raw.lower() == "q":
            raise _Quit()
        if previous is not None and raw.lower() == "p":
            return float(previous)
        try:
            return float(raw)
        except ValueError:
            print("  Enter a numeric value.\n")


def _ask_transfer_date(previous: str | None = None) -> str | None:
    """
    Prompt for the transfer date, with ``today``/``next month`` shortcuts.

    :param previous: Date from the previous transfer of the same direction,
        offered as a one-key copy shortcut (copied verbatim, not advanced to
        a next occurrence). ``None`` when there is none.
    :type previous: str or None
    :returns: Date string in ``YYYY-MM-DD`` format, or ``None`` to skip.
    :raises _Quit: When the user enters ``q``.
    """
    today = datetime.date.today()
    print()
    shortcuts = "  [T] Today   [N] Next month"
    if previous:
        shortcuts += f"   [P] Copy from previous ({previous})"
    print(shortcuts + "   or type a date as YYYY-MM-DD")
    options = "T/N" + ("/P" if previous else "") + "/YYYY-MM-DD"
    while True:
        raw = input(f"  Date  [{options} / ENTER=skip / q=quit]: ").strip()
        if raw.lower() == "q":
            raise _Quit()
        if raw == "":
            return None
        if raw.lower() == "t":
            return today.isoformat()
        if raw.lower() == "n":
            year, month = today.year, today.month + 1
            if month > 12:
                year, month = year + 1, 1
            day = min(today.day, calendar.monthrange(year, month)[1])
            return datetime.date(year, month, day).isoformat()
        if previous and raw.lower() == "p":
            return previous
        try:
            datetime.datetime.strptime(raw, "%Y-%m-%d")
            return raw
        except ValueError:
            extra = ", P" if previous else ""
            print(f"  Enter T, N{extra}, a date as YYYY-MM-DD, or ENTER to skip.\n")


def _load_party_names(pj) -> tuple[list[str], list[str]]:
    """Collect organization and person names from the project's configured sources."""
    search = pj.sources.get("folders", {}).get("search", {})
    org_names = _collect_names(directories=search.get("organizations", []))
    person_names = _collect_names(
        directories=(search.get("persons") or []) + (search.get("sapiens") or [])
    )
    return org_names, person_names


def _pick_party(
    org_names: list[str],
    person_names: list[str],
    label: str,
    previous: str | None = None,
) -> str | None:
    """
    Interactive picker for a transfer party (payer or receiver).

    Asks whether the party is an organization or a person, then picks from
    the matching list — the same lookup used for contractor/client in
    :func:`losalamos.tools.new_project._pick_party`, without its
    contact-person sub-flow (not applicable to transfer parties).

    :param org_names: Sorted list of organization names.
    :param person_names: Sorted list of person names.
    :param label: Field label shown in prompts.
    :param previous: Plain name from the previous transfer of the same
        direction, offered as a one-key copy shortcut. ``None`` when there
        is none.
    :type previous: str or None
    :returns: Selected name, or ``None`` to skip.
    :raises _Quit: When the user enters ``q``.
    """
    print()
    print(f"  {label}")
    options = "  [O] Organization   [H] Person   [0] Skip"
    if previous:
        options += f"   [P] Copy from previous ({previous})"
    print(options)
    print()
    while True:
        extra = "/P" if previous else ""
        kind = input(f"  Type  [O/H{extra} / 0=skip / q=quit]: ").strip().lower()
        if kind == "q":
            raise _Quit()
        if kind == "0":
            return None
        if previous and kind == "p":
            return previous
        if kind == "o":
            return _pick_item(names=org_names, label=f"{label} (organization)")
        if kind == "h":
            return _pick_item(names=person_names, label=f"{label} (person)")
        extra_msg = ", P" if previous else ""
        print(f"  Enter O, H{extra_msg}, or 0.\n")


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


def _gather_transfer_inputs(pj, label: str, direction: str) -> dict | None:
    """
    Run the shared value/date/payer/receiver prompt sequence.

    When a previous transfer of the same *direction* already exists in the
    project, each field prompt offers a ``[P] Copy from previous`` shortcut
    sourced from it — common for transfers that are installments of the same
    recurring service.

    :param pj: Loaded :class:`~losalamos.project.Project`.
    :param label: Heading label for this flow, e.g. ``"Add inflow transfer"``.
    :param direction: ``"inflow"`` or ``"outflow"`` — scopes the "previous
        transfer" lookup, since payer/receiver roles flip between directions.
    :type direction: str
    :returns: Dict with keys ``value``, ``date``, ``payer``, ``receiver``,
        or ``None`` when the user cancels at the final confirmation.
    :raises _Quit: When the user enters ``q``.
    """
    heading_subsection(label)

    previous = pj.get_latest_transfer(direction=direction)
    prev_value_raw = previous.get("value")
    prev_value = float(prev_value_raw) if prev_value_raw not in (None, "") else None

    value = _ask_value(previous=prev_value)
    date = _ask_transfer_date(previous=previous.get("date") or None)

    org_names, person_names = _load_party_names(pj)
    payer = _pick_party(
        org_names=org_names,
        person_names=person_names,
        label="Payer",
        previous=_clean_link(previous.get("payer")),
    )
    receiver = _pick_party(
        org_names=org_names,
        person_names=person_names,
        label="Receiver",
        previous=_clean_link(previous.get("receiver")),
    )

    print()
    print(get_message(f"Value    : {value}"))
    print(get_message(f"Date     : {date or '—'}"))
    print(get_message(f"Payer    : {payer or '—'}"))
    print(get_message(f"Receiver : {receiver or '—'}"))
    print(get_message("Status   : expected"))
    print()

    if not _confirm():
        print(get_message("Cancelled."))
        return None

    return {"value": value, "date": date, "payer": payer, "receiver": receiver}


def _ask_copy_invoice_from(pj) -> str | None:
    """
    Offer to seed the new invoice (and, transitively, its receipt) from the
    latest invoice in the project.

    Only one combined question is asked -- the receipt is always derived
    from this transfer's own new invoice via *invoice_id*, so it inherits
    any copied content automatically; there is no separate receipt prompt.

    :param pj: Loaded :class:`~losalamos.project.Project`.
    :returns: Asset file ID of the latest invoice to copy from, or ``None``
        when there is no previous invoice or the user declines.
    :raises _Quit: When the user enters ``q``.
    """
    assets = pj.get_assets()
    invoices = assets[assets["asset_type"] == "invoice"]
    if invoices.empty:
        return None

    latest = invoices.iloc[-1]
    print()
    print(get_message(f"Previous invoice found: {latest['name']}"))
    if _confirm(
        prompt="Copy its content (services, party info) into the new invoice/receipt?"
    ):
        return latest["asset_id"]
    return None


def _action_add_inflow(pj) -> None:
    """Interactive add-inflow-transfer flow. Creates the transfer, invoice, and receipt."""
    inputs = _gather_transfer_inputs(
        pj=pj, label="Add inflow transfer", direction="inflow"
    )
    if inputs is None:
        return

    copy_invoice_from = _ask_copy_invoice_from(pj=pj)

    transfer, invoice, receipt = pj.add_inflow_transfer(
        copy_invoice_from=copy_invoice_from, **inputs
    )
    print(get_message(f"Transfer : {transfer.metadata['name']}"))
    print(get_message(f"Invoice  : {invoice.name}"))
    print(get_message(f"Receipt  : {receipt.name}"))


def _action_add_outflow(pj) -> None:
    """Interactive add-outflow-transfer flow."""
    inputs = _gather_transfer_inputs(
        pj=pj, label="Add outflow transfer", direction="outflow"
    )
    if inputs is None:
        return

    transfer = pj.add_transfer(
        direction="outflow", status="expected", account=None, **inputs
    )
    print(get_message(f"Transfer : {transfer.metadata['name']}"))


def _home(pj, project_info: dict) -> str:
    """
    Home page loop for a selected project's budget.

    Reloads the project on each iteration so the transfer list is always
    current after an add action.

    :returns: ``"quit"`` to exit the tool or ``"projects"`` to return to the
        caller (the vault manager's manager picker, or the project list).
    """
    while True:
        pj.update()
        transfer_df = pj.get_transfers()

        heading_subsection(f"{project_info['name']}  —  {project_info['title']}")
        _print_transfers(transfer_df)

        print("  [I] Add inflow    [O] Add outflow    [P] Back    [Q] Quit")
        print()

        choice = input("  Select: ").strip().lower()
        print()

        if choice == "q":
            return "quit"
        if choice == "p":
            return "projects"
        if choice == "i":
            _action_add_inflow(pj=pj)
        elif choice == "o":
            _action_add_outflow(pj=pj)


def run(project_folder: str, vault: str = None) -> None:
    """
    Open the budget manager home page for a single project.

    Can be called directly (e.g. from :mod:`losalamos.tools.manage_vault`)
    or via :func:`main` when invoked from the command line.

    :param project_folder: Path to the project root folder.
    :type project_folder: str
    :param vault: Optional path to the vault root, passed to
        :func:`losalamos.load_project` for branch detection.
    :type vault: str or None
    """
    heading_section("BUDGET MANAGER")

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
    except (_Quit, _PartyQuit):
        pass

    print("\n  Goodbye.\n")


def main() -> None:
    args = get_arguments()
    run(project_folder=args.source)


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":
    main()
