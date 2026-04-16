"""Tests for title-based off-topic pruning of merged-lane papers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import prune_merged_lane_offtopic as prune  # noqa: E402


class OfftopicTitleTests(unittest.TestCase):
    def test_flags_obvious_non_education(self) -> None:
        self.assertTrue(prune.title_is_offtopic("Review of Particle Physics"))
        self.assertTrue(prune.title_is_offtopic("Peanut shell derived hard carbon as ultralong cycling anodes for lithium batteries"))

    def test_keeps_education_titles(self) -> None:
        self.assertFalse(prune.title_is_offtopic("Learning Engineering Toolkit"))
        self.assertFalse(prune.title_is_offtopic("Active learning narrows achievement gaps for underrepresented students"))


if __name__ == "__main__":
    unittest.main()
