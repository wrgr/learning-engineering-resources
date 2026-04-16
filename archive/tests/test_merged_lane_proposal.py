"""Unit tests for merged-lane proposal helpers (no OpenAlex network calls)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import merged_lane_proposal as mlp  # noqa: E402


class MergedLaneProposalHelpersTests(unittest.TestCase):
    def test_topic_codes_from_registry_row_orders_and_dedupes(self) -> None:
        row = {"primary_topic": "T00", "secondary_topics": "T06, T07, T06"}
        self.assertEqual(mlp.topic_codes_from_registry_row(row), ["T00", "T06", "T07"])

    def test_topic_codes_default_when_empty(self) -> None:
        row: dict = {}
        self.assertEqual(mlp.topic_codes_from_registry_row(row), ["T00"])


if __name__ == "__main__":
    unittest.main()
