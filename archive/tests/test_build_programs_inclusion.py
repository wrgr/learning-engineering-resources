"""Programs summary must list every non-paper resource row, including unknown content_type codes."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from build_dataset import build_programs  # noqa: E402


class BuildProgramsInclusionTests(unittest.TestCase):
    def test_unknown_content_type_maps_to_other(self) -> None:
        rows = [
            {
                "title": "Mystery item",
                "context": "c",
                "url": "https://example.edu/x",
                "content_type": "ZZ",
                "resource_id": "LE-X-1",
            }
        ]
        out = build_programs(rows)
        self.assertEqual(len(out["programs"]), 1)
        self.assertEqual(out["programs"][0]["category"], "other")
        self.assertEqual(out["programs"][0]["content_type"], "ZZ")


if __name__ == "__main__":
    unittest.main()
