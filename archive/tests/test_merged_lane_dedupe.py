"""Tests for merged-lane spec deduplication against seed/hop OpenAlex work IDs."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from build_merged_site_dataset import _dedupe_lane_specs


class MergedLaneDedupeTests(unittest.TestCase):
    def test_skips_work_id_in_classic_pool(self) -> None:
        specs = [
            {"work_id": "W1", "topic_codes": ["T00"]},
            {"work_id": "W2", "topic_codes": ["T01"]},
        ]
        kept, skipped = _dedupe_lane_specs(specs, {"W1"})
        self.assertEqual([s["work_id"] for s in kept], ["W2"])
        self.assertTrue(any("W1" in s for s in skipped))

    def test_duplicate_work_id_in_file_dropped(self) -> None:
        specs = [
            {"work_id": "W9", "topic_codes": ["T00"]},
            {"work_id": "W9", "topic_codes": ["T01"]},
        ]
        kept, skipped = _dedupe_lane_specs(specs, set())
        self.assertEqual(len(kept), 1)
        self.assertTrue(any("duplicate work_id" in s for s in skipped))


if __name__ == "__main__":
    unittest.main()
