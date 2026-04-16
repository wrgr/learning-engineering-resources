"""Registry smoke tests: ICICLE SIGs/MIGs rows from programs_people_registry.json."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class IcicleSigsRegistryTests(unittest.TestCase):
    def test_registry_has_sigs_page_and_chairs(self) -> None:
        path = REPO / "corpus" / "tables" / "programs_people_registry.json"
        rows = json.loads(path.read_text(encoding="utf-8"))
        by_id = {r["resource_id"]: r for r in rows}
        page = by_id.get("LE-PP-055")
        self.assertIsNotNone(page)
        assert page is not None
        self.assertEqual(page.get("content_type"), "CO")
        self.assertIn("sagroups.ieee.org/icicle/sigs/", page.get("url", ""))
        self.assertEqual(by_id.get("LE-PP-056", {}).get("name"), "Jodi Lis")
        self.assertEqual(by_id.get("LE-PP-073", {}).get("name"), "DJ Jaeger")
        expected = [
            "Jodi Lis",
            "Bedriye Akson",
            "Aaron Kessler",
            "Amy Parent",
            "Adesola Ogundimu",
            "Mei-Mei Li",
            "Abby Bregman",
            "Li (Lee) Liang",
            "Erin Czerwinski",
            "Baptiste Moreau-Pernet",
            "Emily Marasco",
            "Rob Nyland",
            "Eric Ultes",
            "Jason Virtue",
            "Zarka Ali",
            "John Ellis",
            "John Costa",
            "DJ Jaeger",
        ]
        for i, name in enumerate(expected, start=56):
            rid = f"LE-PP-{i:03d}"
            self.assertEqual(by_id.get(rid, {}).get("name"), name, f"mismatch at {rid}")


if __name__ == "__main__":
    unittest.main()
