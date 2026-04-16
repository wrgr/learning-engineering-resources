"""Tests for append_ieee_seeds_to_lane_work_specs row building (no I/O)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import append_ieee_seeds_to_lane_work_specs as app  # noqa: E402


class IeeeSeedRowsTests(unittest.TestCase):
    def test_build_skips_lane_and_classic(self) -> None:
        rows, n_new, skip_lane, skip_classic = app.build_rows_for_ieee_seeds(
            ["W1", "W2", "W3"],
            existing_lane={"W1"},
            classic={"W3"},
        )
        self.assertEqual(n_new, 1)
        self.assertEqual(skip_lane, 1)
        self.assertEqual(skip_classic, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["work_id"], "W2")
        self.assertEqual(rows[0]["source_expansion"], "thematic")
        self.assertIn("T00", rows[0]["topic_codes"])


if __name__ == "__main__":
    unittest.main()
