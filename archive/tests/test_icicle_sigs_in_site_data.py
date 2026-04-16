"""After `build_dataset.py`, ICICLE SIGs registry rows must appear in `data/icicle_resources.json`."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class IcicleSigsSiteDataTests(unittest.TestCase):
    def test_merged_resources_json_includes_sigs_page_id(self) -> None:
        path = REPO / "data" / "icicle_resources.json"
        self.assertTrue(path.is_file(), "run: python3 scripts/build_dataset.py --skip-paper-enrichment")
        text = path.read_text(encoding="utf-8")
        self.assertIn("LE-PP-055", text)
        self.assertIn("IEEE ICICLE SIGs", text)


if __name__ == "__main__":
    unittest.main()
