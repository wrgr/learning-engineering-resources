"""Tests for merged lane proposal inclusion defaults."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import merged_lane_proposal as mlp  # noqa: E402


class InclusionConfigTests(unittest.TestCase):
    def test_defaults_are_permissive(self) -> None:
        d = mlp.load_inclusion_defaults(REPO / "corpus/merged_lane/nonexistent.json")
        self.assertEqual(d["min_citations"], 5)
        self.assertEqual(d["per_person"], 25)
        self.assertGreaterEqual(d["max_pages"], 4)

    def test_strict_defaults_match_legacy(self) -> None:
        d = mlp.strict_inclusion_defaults()
        self.assertEqual(d["min_citations"], 25)
        self.assertEqual(d["per_person"], 12)
        self.assertEqual(d["max_pages"], 4)

    def test_json_overrides_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "inc.json"
            p.write_text(json.dumps({"min_citations": 3, "max_pages": 10, "bogus": 1}), encoding="utf-8")
            d = mlp.load_inclusion_defaults(p)
            self.assertEqual(d["min_citations"], 3)
            self.assertEqual(d["max_pages"], 10)


if __name__ == "__main__":
    unittest.main()
