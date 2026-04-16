"""Tests for merged_lane_proposal_workers merge logic (no network)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import merged_lane_proposal_workers as mlw  # noqa: E402


class MergeLaneRowsTests(unittest.TestCase):
    def test_merge_keeps_first_work_id(self) -> None:
        rows = [
            {"work_id": "W1", "topic_codes": ["T01"]},
            {"work_id": "W1", "topic_codes": ["T02"]},
            {"work_id": "W2"},
        ]
        got = mlw.merge_lane_rows(rows)
        self.assertEqual(len(got), 2)
        self.assertEqual(got[0]["topic_codes"], ["T01"])


if __name__ == "__main__":
    unittest.main()
