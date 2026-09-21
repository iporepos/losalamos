# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Budget generation and analysis utilities.

Provides :class:`Budget` for building collections of transfer notes from a
structured batch seed, with a recurrence engine that expands periodic
transfers into individual dated instances.

The typical workflow is:

1. Instantiate and configure the budget::

    from losalamos.budget import Budget
    from pathlib import Path

    budget = Budget()
    budget.year = 2027
    budget.duration = 1
    budget.output_folder = Path("vault/budget")

2. Build the in-memory collection from a batch seed::

    budget.build(batches=[
        {
            "defaults": {
                "currency": "BRL",
                "direction": "outflow",
                "payer": "My Company",
            },
            "transfers": [
                {"value": 1000.00, "receiver": "Rent Corp", "recurrence": "1 month"},
                {"value": 5000.00, "receiver": "Insurance Co", "recurrence": "1 year"},
            ],
        }
    ])

3. Inspect before writing::

    print(budget.catalog)
    print(budget.monthly_equivalent(group_by="commitment"))

4. Materialise notes to disk::

    budget.save()

"""
# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import calendar
import re
from datetime import date, timedelta
from pathlib import Path

# External imports
# =======================================================================
import pandas as pd

# Project-level imports
# =======================================================================
from losalamos.notes import NoteCollTransfer, NoteTransfer

# ... {develop}


# CONSTANTS
# ***********************************************************************
# ... {develop}


# CLASSES
# ***********************************************************************


class Budget(NoteCollTransfer):
    """
    A collection of transfer notes built from a batch seed.

    Extends :class:`~losalamos.notes.NoteCollTransfer` with a recurrence
    engine and budget-level statistics. Notes are held in memory until
    :meth:`save` materializes them as Markdown files.

    The collection can also be populated from existing files via the
    inherited :meth:`~losalamos.notes.NoteCollection.load_folder` and
    related methods.

    :param name: Budget name, used as the prefix for every generated note
        filename (e.g. ``"HouseBudget"`` → ``HouseBudget_2027_001.md``).
        Required — no default.
    :type name: str
    :param alias: Object alias. Default value = ``"Bgt"``
    :type alias: str

    **Attributes**

    - ``NOTE_PREFIX`` (*str*): Prefix for generated note filenames, uppercased
      at use. Default value = ``"transfer"``
    - ``year`` (*int*): Budget start year. Defaults to the current year.
    - ``duration`` (*int*): Number of years covered. Default value = ``1``
    - ``output_folder`` (*Path or None*): Destination for :meth:`save`.
    - ``split`` (*bool*): When ``True``, :meth:`save` writes inflows to
      ``output_folder/inflows/`` and outflows to ``output_folder/outflows/``.
      Default value = ``False``
    """

    NOTE_PREFIX = "transfer"

    def __init__(self, name, alias="Bgt"):
        super().__init__(name=name, alias=alias)
        self.year = date.today().year
        self.duration = 1
        self.output_folder = None
        self.split = False
        self.catalog_monthly = None
        self.catalog_annual = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def build(self, batches):
        """
        Populate the in-memory collection from a list of transfer batches.

        Each batch is a dict with a ``defaults`` block and a ``transfers``
        list. Every entry in ``transfers`` is merged with ``defaults``
        (entry-level keys win), then expanded by the recurrence engine into
        one :class:`~losalamos.notes.NoteTransfer` per occurrence.

        Two optional per-transfer anchor keys are consumed before the note
        is created and do not appear in the note metadata:

        - ``day`` (*int*): Day-of-month anchor. Default value = ``1``
        - ``month`` (*int*): Month anchor, only used for year-level
          recurrence. Default value = ``1``

        Calling :meth:`build` replaces any previously built content.
        No files are written to disk.

        :param batches: List of batch dicts, each with:

            - ``defaults`` (*dict*) — fields applied to every transfer in the batch.
            - ``transfers`` (*list[dict]*) — per-transfer overrides.

        :type batches: list[dict]
        :return: No value is returned.
        :rtype: None
        """
        # reset collection
        self.collection = dict()
        self.catalog = pd.DataFrame()
        self.size = 0

        counter = 1
        for batch in batches:
            defaults = batch.get("defaults", {})
            for entry in batch.get("transfers", []):
                merged = {**defaults, **entry}

                day = int(merged.pop("day", 1))
                month = int(merged.pop("month", 1))
                recurrence = str(merged.get("recurrence", "non-recurrent"))

                dates = Budget._resolve_dates(
                    recurrence=recurrence,
                    year=self.year,
                    duration=self.duration,
                    day=day,
                    month=month,
                )

                direction = str(merged.get("direction", "outflow")).lower().rstrip("s")

                for dt in dates:
                    name = f"{self.NOTE_PREFIX.upper()}_{self.name}_{dt[:7]}_{counter:04d}"

                    note = NoteTransfer(name=name, alias=name)
                    # load_new reads the template without writing any file
                    note.load_new(file_note=Path("_") / f"{name}.md")

                    note.metadata["name"] = name
                    note.metadata["date"] = dt
                    note.metadata["direction"] = direction
                    note.metadata["value"] = merged.get("value")
                    note.metadata["currency"] = merged.get("currency")
                    note.metadata["payer"] = Budget._wiki(merged.get("payer"))
                    note.metadata["receiver"] = Budget._wiki(merged.get("receiver"))
                    note.metadata["commitment"] = merged.get("commitment")
                    note.metadata["project"] = Budget._wiki(merged.get("project"))
                    note.metadata["recurrence"] = recurrence
                    note.metadata["account"] = merged.get("account")
                    note.metadata["status"] = merged.get("status", "expected")
                    note.metadata["method"] = merged.get("method", "manual")
                    note.metadata["protocol"] = merged.get("protocol")
                    note.metadata["domain"] = merged.get("domain")
                    note.metadata["category"] = merged.get("category")
                    note.metadata["subcategory"] = merged.get("subcategory")
                    note.metadata["related_asset"] = merged.get("related_asset")

                    self.append(note)
                    counter += 1

        return None

    def save(self):
        """
        Write all in-memory transfer notes to :attr:`output_folder`.

        When :attr:`split` is ``False`` (default), all notes are written flat
        into ``output_folder``. When ``True``, inflow notes go to
        ``output_folder/inflows/`` and outflow notes to
        ``output_folder/outflows/``. All required folders are created if absent.

        :raises ValueError: If :attr:`output_folder` is ``None``.
        :return: No value is returned.
        :rtype: None
        """
        if self.output_folder is None:
            raise ValueError("output_folder is not set")

        base = Path(self.output_folder)

        for name, note in self.collection.items():
            if self.split:
                direction = str(note.metadata.get("direction", "outflow")).lower()
                folder = base / f"{direction}s"
            else:
                folder = base
            folder.mkdir(parents=True, exist_ok=True)
            note.file_note = folder / f"{name}.md"
            note.save()

        return None

    def monthly_equivalent(self, group_by=None, account=None):
        """
        Return the monthly equivalent value across all transfers.

        Sums every note's value and divides by the total budget duration
        in months, normalising transfers with different recurrences to a
        common monthly baseline.

        The result is a wide table where ``direction`` becomes columns so
        inflows and outflows can be compared side by side:

        .. code-block:: text

            equivalence | account  | inflow  | outflow  | net
            monthly     | BB-001   | 10500   | 4780     | 5720
            monthly     | NB-002   | 1200    | 1455     | -255

        Pass *group_by* to add row-level breakdown after ``account``.

        :param group_by: Extra column name or list of column names used as
            additional row keys after ``account``, e.g. ``"commitment"`` or
            ``["commitment", "category"]``. When ``None``, rows are by
            ``account`` only.
        :type group_by: str, list, or None
        :param account: Account code or list of account codes to include.
            When ``None``, all accounts are included.
        :type account: str, list, or None
        :return: DataFrame with columns ``equivalence``, ``account``,
            optional extras, ``inflow``, ``outflow``, ``net``. Also stored
            as :attr:`catalog_monthly`.
        :rtype: :class:`pandas.DataFrame`
        """
        self.catalog_monthly = self._equivalent(
            divisor=self.duration * 12,
            scale_label="monthly",
            group_by=group_by,
            account=account,
        )
        return self.catalog_monthly

    def annual_equivalent(self, group_by=None, account=None):
        """
        Return the annual equivalent value across all transfers.

        Same wide layout as :meth:`monthly_equivalent` with
        ``equivalence = "annual"``.

        :param group_by: Extra column name or list of column names used as
            additional row keys after ``account``. When ``None``, rows are
            by ``account`` only.
        :type group_by: str, list, or None
        :param account: Account code or list of account codes to include.
            When ``None``, all accounts are included.
        :type account: str, list, or None
        :return: DataFrame with columns ``equivalence``, ``account``,
            optional extras, ``inflow``, ``outflow``, ``net``. Also stored
            as :attr:`catalog_annual`.
        :rtype: :class:`pandas.DataFrame`
        """
        self.catalog_annual = self._equivalent(
            divisor=self.duration,
            scale_label="annual",
            group_by=group_by,
            account=account,
        )
        return self.catalog_annual

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _equivalent(self, divisor, scale_label, group_by, account=None):
        """
        Pivot transfer values into a wide inflow/outflow table.

        Computes ``value / divisor`` for every note, optionally filters by
        *account*, groups by ``account`` plus any *group_by* extras, then
        pivots ``direction`` so that ``inflow`` and ``outflow`` become
        side-by-side columns. A leading ``equivalence`` column carries
        *scale_label* for reference.

        :param divisor: Total periods (months or years) to divide by.
        :param scale_label: Label written into the ``equivalence`` column.
        :param group_by: Extra row-key column(s) after ``account``, or ``None``.
        :param account: Account code or list of codes to filter on, or ``None``
            for all accounts.
        """
        df = self.catalog.copy()
        df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)

        if account is not None:
            codes = [account] if isinstance(account, str) else list(account)
            df = df[df["account"].isin(codes)]
        df["_equiv"] = df["value"] / divisor

        row_keys = ["account"]
        if group_by is not None:
            extras = [group_by] if isinstance(group_by, str) else list(group_by)
            row_keys = row_keys + extras

        grouped = df.groupby(row_keys + ["direction"])["_equiv"].sum().reset_index()
        pivoted = grouped.pivot_table(
            index=row_keys,
            columns="direction",
            values="_equiv",
            fill_value=0.0,
        ).reset_index()
        pivoted.columns.name = None

        for d in ("inflow", "outflow"):
            if d not in pivoted.columns:
                pivoted[d] = 0.0

        pivoted["net"] = pivoted["inflow"] - pivoted["outflow"]
        pivoted.insert(0, "equivalence", scale_label)

        return pivoted[["equivalence"] + row_keys + ["inflow", "outflow", "net"]]

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _wiki(value):
        """
        Wrap a plain-text name in quoted Obsidian wiki-link notation.

        The result always has the form ``"[[Name]]"`` — double quotes included
        as part of the string — so that ``metadata_to_list`` writes the field
        correctly in YAML frontmatter.  Existing outer quotes and ``[[``
        brackets are stripped before re-wrapping, so the input can be in any
        partial form.

        :param value: Raw name string, e.g. ``"Anthropic Inc"`` or ``"[[Anthropic Inc]]"``.
        :return: Quoted wiki-link string, e.g. ``'"[[Anthropic Inc]]"'``, or empty string.
        :rtype: str
        """
        if not value:
            return ""
        v = str(value).strip()
        # strip outer double quotes if already present
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        # strip wiki brackets if already present
        if v.startswith("[[") and v.endswith("]]"):
            v = v[2:-2]
        return f'"[[{v}]]"'

    @staticmethod
    def _resolve_dates(recurrence, year, duration, day=1, month=1):
        """
        Compute all occurrence dates for a recurrence rule within the budget window.

        Accepted syntax: ``"N day[s]"``, ``"N week[s]"``, ``"N month[s]"``,
        ``"N year[s]"``. Any other string yields an empty list.

        The anchor for the first occurrence is:

        - Day/week recurrences: ``year-01-{day}``
        - Month recurrences: ``year-01-{day}``
        - Year recurrences: ``year-{month}-{day}``

        For multi-year recurrences (e.g. ``"3 years"``), the first occurrence
        always falls in the starting year.

        :param recurrence: Recurrence string, e.g. ``"1 month"``, ``"2 weeks"``.
        :type recurrence: str
        :param year: Budget start year.
        :type year: int
        :param duration: Number of years in the budget window.
        :type duration: int
        :param day: Anchor day-of-month. Default value = ``1``
        :type day: int
        :param month: Anchor month (year recurrences only). Default value = ``1``
        :type month: int
        :return: Sorted list of ISO date strings within ``[year, year + duration)``.
        :rtype: list[str]
        """
        recurrence = str(recurrence).strip().lower()
        m = re.match(r"^(\d+)\s+(day|days|week|weeks|month|months|year|years)$", recurrence)
        if not m:
            return []

        n = int(m.group(1))
        unit = m.group(2).rstrip("s")  # normalise plural: "months" → "month"

        window_start = date(year, 1, 1)
        window_end = date(year + duration, 1, 1)
        dates = []

        if unit == "day":
            current = date(year, 1, day)
            delta = timedelta(days=n)
            while current < window_end:
                if current >= window_start:
                    dates.append(current.isoformat())
                current += delta

        elif unit == "week":
            current = date(year, 1, day)
            delta = timedelta(weeks=n)
            while current < window_end:
                if current >= window_start:
                    dates.append(current.isoformat())
                current += delta

        elif unit == "month":
            current = date(year, 1, day)
            while current < window_end:
                if current >= window_start:
                    dates.append(current.isoformat())
                current = Budget._add_months(current, n)

        elif unit == "year":
            # Multi-year: the first occurrence always falls within the start year.
            current = date(year, month, day)
            while current < window_end:
                if current >= window_start:
                    dates.append(current.isoformat())
                current = Budget._add_months(current, n * 12)

        return dates

    @staticmethod
    def _add_months(dt, n):
        """
        Add *n* months to a date, clamping to the last valid day when needed.

        :param dt: Source date.
        :type dt: :class:`datetime.date`
        :param n: Number of months to add.
        :type n: int
        :return: New date shifted forward by *n* months.
        :rtype: :class:`datetime.date`
        """
        total_months = dt.month - 1 + n
        new_year = dt.year + total_months // 12
        new_month = total_months % 12 + 1
        new_day = min(dt.day, calendar.monthrange(new_year, new_month)[1])
        return dt.replace(year=new_year, month=new_month, day=new_day)


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":
    print("Hello world!")
    # ... {develop}
