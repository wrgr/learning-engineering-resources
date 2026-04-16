"""Tests for merge_proposed_into_lane_work_specs (no I/O)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import merge_proposed_into_lane_work_specs as m  # noqa: E402


class MergeProposedLaneTests(unittest.TestCase):
    def test_clean_strips_audit(self) -> None:
        row = {"work_id": "W1", "topic_codes": ["T00"], "_proposal_audit": {"x": 1}}
        got = m.clean_lane_row(row)
        self.assertNotIn("_proposal_audit", got)
        self.assertEqual(got["work_id"], "W1")

    def test_merge_skips_duplicate_work_id(self) -> None:
        specs = [{"work_id": "W1", "topic_codes": ["T01"]}]
        proposed = [{"work_id": "W1", "topic_codes": ["T02"]}, {"work_id": "W2", "topic_codes": ["T03"]}]
        merged, app, skip = m.merge_proposed_into_specs(specs, proposed)
        self.assertEqual(len(merged), 2)
        self.assertEqual(app, 1)
        self.assertEqual(skip, 1)
        self.assertEqual(merged[0]["topic_codes"], ["T01"])


if __name__ == "__main__":
    unittest.main()
