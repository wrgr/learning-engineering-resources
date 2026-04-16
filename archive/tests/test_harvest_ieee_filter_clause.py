"""Tests for harvest_ieee_icicle_conference_works filter helpers (no network)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import harvest_ieee_icicle_conference_works as h  # noqa: E402


class FilterClauseTests(unittest.TestCase):
    def test_empty_is_paratext_only(self) -> None:
        self.assertEqual(h._filter_clause(None), "is_paratext:false")
        self.assertEqual(h._filter_clause(""), "is_paratext:false")

    def test_year_range(self) -> None:
        self.assertEqual(h._filter_clause("2020-2026"), "is_paratext:false,publication_year:2020-2026")


if __name__ == "__main__":
    unittest.main()
