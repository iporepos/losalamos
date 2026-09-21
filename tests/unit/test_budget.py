# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""Unit tests for ``losalamos.budget.Budget``."""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from losalamos.budget import Budget


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _simple_budget(name="TestBudget"):
    b = Budget(name=name)
    b.year = 2027
    b.duration = 1
    return b


def _minimal_batches():
    return [
        {
            "defaults": {
                "direction": "outflow",
                "account": "ACC-01",
                "currency": "BRL",
                "payer": "Alice",
            },
            "transfers": [
                {"value": 100.0, "receiver": "Bob", "recurrence": "1 month"},
            ],
        }
    ]


# ***********************************************************************
# CLASSES
# ***********************************************************************


class TestResolveDates(unittest.TestCase):
    """Recurrence engine — ``Budget._resolve_dates``."""

    def test_monthly_generates_12_dates(self):
        dates = Budget._resolve_dates(recurrence="1 month", year=2027, duration=1)
        self.assertEqual(len(dates), 12)
        self.assertEqual(dates[0], "2027-01-01")
        self.assertEqual(dates[-1], "2027-12-01")

    def test_monthly_plural_accepted(self):
        dates = Budget._resolve_dates(recurrence="1 months", year=2027, duration=1)
        self.assertEqual(len(dates), 12)

    def test_bimestral_generates_6_dates(self):
        dates = Budget._resolve_dates(recurrence="2 months", year=2027, duration=1)
        self.assertEqual(len(dates), 6)

    def test_weekly_generates_52_or_53_dates(self):
        # A year starting on certain weekdays fits 53 weekly intervals; both are correct.
        dates = Budget._resolve_dates(recurrence="1 week", year=2027, duration=1)
        self.assertIn(len(dates), (52, 53))

    def test_yearly_generates_1_date(self):
        dates = Budget._resolve_dates(recurrence="1 year", year=2027, duration=1)
        self.assertEqual(len(dates), 1)
        self.assertEqual(dates[0], "2027-01-01")

    def test_yearly_month_day_anchor(self):
        dates = Budget._resolve_dates(
            recurrence="1 year", year=2027, duration=1, month=3, day=15
        )
        self.assertEqual(dates[0], "2027-03-15")

    def test_multiyear_recurrence_single_duration(self):
        # "3 years" within a 1-year budget: exactly 1 occurrence in year 0
        dates = Budget._resolve_dates(recurrence="3 years", year=2027, duration=1)
        self.assertEqual(len(dates), 1)

    def test_day_anchor_applied(self):
        dates = Budget._resolve_dates(recurrence="1 month", year=2027, duration=1, day=10)
        self.assertTrue(all(d.endswith("-10") for d in dates))

    def test_unknown_recurrence_returns_empty(self):
        dates = Budget._resolve_dates(recurrence="non-recurrent", year=2027, duration=1)
        self.assertEqual(dates, [])

    def test_two_year_duration_doubles_monthly(self):
        dates = Budget._resolve_dates(recurrence="1 month", year=2027, duration=2)
        self.assertEqual(len(dates), 24)


class TestAddMonths(unittest.TestCase):
    """Month arithmetic — ``Budget._add_months``."""

    def test_simple_addition(self):
        result = Budget._add_months(date(2027, 1, 15), 3)
        self.assertEqual(result, date(2027, 4, 15))

    def test_year_rollover(self):
        result = Budget._add_months(date(2027, 11, 1), 3)
        self.assertEqual(result, date(2028, 2, 1))

    def test_day_clamped_to_month_end(self):
        # Jan 31 + 1 month → Feb 28
        result = Budget._add_months(date(2027, 1, 31), 1)
        self.assertEqual(result, date(2027, 2, 28))


class TestWiki(unittest.TestCase):
    """Wiki-link helper — ``Budget._wiki``."""

    def test_plain_text_wrapped(self):
        self.assertEqual(Budget._wiki("Landlord Co"), '"[[Landlord Co]]"')

    def test_already_bracketed_normalized(self):
        self.assertEqual(Budget._wiki("[[Landlord Co]]"), '"[[Landlord Co]]"')

    def test_already_quoted_and_bracketed_unchanged(self):
        self.assertEqual(Budget._wiki('"[[Landlord Co]]"'), '"[[Landlord Co]]"')

    def test_empty_returns_empty(self):
        self.assertEqual(Budget._wiki(""), "")
        self.assertEqual(Budget._wiki(None), "")


class TestBudgetBuild(unittest.TestCase):
    """``Budget.build`` — collection size, naming, direction normalisation."""

    def test_monthly_transfer_generates_12_notes(self):
        b = _simple_budget()
        b.build(batches=_minimal_batches())
        self.assertEqual(len(b.collection), 12)

    def test_note_name_format(self):
        b = _simple_budget(name="MyBudget")
        b.build(batches=_minimal_batches())
        names = list(b.collection.keys())
        # expect TRANSFER_MyBudget_YYYY-MM_NNNN
        for name in names:
            parts = name.split("_")
            self.assertEqual(parts[0], "TRANSFER")
            self.assertEqual(parts[1], "MyBudget")
            self.assertRegex(parts[2], r"^\d{4}-\d{2}$")
            self.assertRegex(parts[3], r"^\d{4}$")

    def test_custom_note_prefix(self):
        b = _simple_budget()
        b.NOTE_PREFIX = "payment"
        b.build(batches=_minimal_batches())
        name = list(b.collection.keys())[0]
        self.assertTrue(name.startswith("PAYMENT_"))

    def test_direction_plural_normalised(self):
        b = _simple_budget()
        b.build(batches=[{
            "defaults": {"account": "A", "recurrence": "1 year"},
            "transfers": [{"value": 50, "direction": "outflows"}],
        }])
        note = list(b.collection.values())[0]
        self.assertEqual(note.metadata["direction"], "outflow")

    def test_build_resets_previous_collection(self):
        b = _simple_budget()
        b.build(batches=_minimal_batches())
        first_count = len(b.collection)
        b.build(batches=_minimal_batches())
        self.assertEqual(len(b.collection), first_count)

    def test_catalog_rows_match_collection(self):
        b = _simple_budget()
        b.build(batches=_minimal_batches())
        self.assertEqual(len(b.catalog), len(b.collection))


class TestBudgetEquivalent(unittest.TestCase):
    """``monthly_equivalent`` and ``annual_equivalent`` — pivot, net, account filter."""

    @classmethod
    def setUpClass(cls):
        cls.budget = Budget(name="EquivTest")
        cls.budget.year = 2027
        cls.budget.duration = 1
        cls.budget.build(batches=[
            {
                "defaults": {
                    "direction": "outflow",
                    "account": "ACC-01",
                    "recurrence": "1 month",
                    "currency": "BRL",
                },
                "transfers": [{"value": 1200.0, "receiver": "Landlord"}],
            },
            {
                "defaults": {
                    "direction": "inflow",
                    "account": "ACC-01",
                    "recurrence": "1 month",
                    "currency": "BRL",
                },
                "transfers": [{"value": 3000.0, "payer": "Employer"}],
            },
            {
                "defaults": {
                    "direction": "outflow",
                    "account": "ACC-02",
                    "recurrence": "1 month",
                    "currency": "BRL",
                },
                "transfers": [{"value": 500.0, "receiver": "Gym"}],
            },
        ])

    def test_monthly_columns(self):
        df = self.budget.monthly_equivalent()
        self.assertIn("equivalence", df.columns)
        self.assertIn("account", df.columns)
        self.assertIn("inflow", df.columns)
        self.assertIn("outflow", df.columns)
        self.assertIn("net", df.columns)

    def test_equivalence_label(self):
        df = self.budget.monthly_equivalent()
        self.assertTrue((df["equivalence"] == "monthly").all())

    def test_annual_label(self):
        df = self.budget.annual_equivalent()
        self.assertTrue((df["equivalence"] == "annual").all())

    def test_net_equals_inflow_minus_outflow(self):
        df = self.budget.monthly_equivalent()
        for _, row in df.iterrows():
            self.assertAlmostEqual(row["net"], row["inflow"] - row["outflow"])

    def test_monthly_value_acc01(self):
        # ACC-01: outflow 1200/mo, inflow 3000/mo → both exact
        df = self.budget.monthly_equivalent()
        row = df[df["account"] == "ACC-01"].iloc[0]
        self.assertAlmostEqual(row["outflow"], 1200.0)
        self.assertAlmostEqual(row["inflow"], 3000.0)

    def test_account_filter_single(self):
        df = self.budget.monthly_equivalent(account="ACC-01")
        self.assertEqual(list(df["account"].unique()), ["ACC-01"])

    def test_account_filter_list(self):
        df = self.budget.monthly_equivalent(account=["ACC-01", "ACC-02"])
        self.assertEqual(len(df), 2)

    def test_stored_attribute_updated(self):
        self.budget.monthly_equivalent()
        self.assertIsNotNone(self.budget.catalog_monthly)
        self.budget.annual_equivalent()
        self.assertIsNotNone(self.budget.catalog_annual)


class TestBudgetSave(unittest.TestCase):
    """``Budget.save`` — raises without folder; writes flat files."""

    def test_save_raises_without_output_folder(self):
        b = _simple_budget()
        b.build(batches=_minimal_batches())
        with self.assertRaises(ValueError):
            b.save()

    def test_save_writes_flat_files(self):
        b = _simple_budget()
        b.build(batches=_minimal_batches())
        with tempfile.TemporaryDirectory() as tmp:
            b.output_folder = Path(tmp)
            b.save()
            written = list(Path(tmp).glob("*.md"))
            self.assertEqual(len(written), 12)

    def test_save_split_creates_subfolders(self):
        b = _simple_budget()
        b.build(batches=_minimal_batches())
        b.split = True
        with tempfile.TemporaryDirectory() as tmp:
            b.output_folder = Path(tmp)
            b.save()
            self.assertTrue((Path(tmp) / "outflows").is_dir())
            written = list((Path(tmp) / "outflows").glob("*.md"))
            self.assertEqual(len(written), 12)


if __name__ == "__main__":
    unittest.main()
