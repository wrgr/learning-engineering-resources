"""Registry smoke tests for learning-engineering institutions and faculty rows."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class LearningEngineeringInstitutionsRegistryTests(unittest.TestCase):
    def test_key_program_and_people_ids_present(self) -> None:
        path = REPO / "corpus" / "tables" / "programs_people_registry.json"
        rows = json.loads(path.read_text(encoding="utf-8"))
        by_id = {r["resource_id"]: r for r in rows}
        for rid in (
            "LE-PP-003",
            "LE-PP-074",
            "LE-PP-075",
            "LE-PP-076",
            "LE-PP-077",
            "LE-PP-078",
            "LE-PP-079",
            "LE-PP-080",
            "LE-PP-081",
            "LE-PP-082",
            "LE-PP-083",
            "LE-PP-084",
            "LE-PP-085",
            "LE-PP-086",
            "LE-PP-087",
            "LE-PP-088",
            "LE-PP-089",
        ):
            self.assertIn(rid, by_id, f"missing {rid}")
        self.assertIn("learning-engineering-virtual-institute.org", by_id["LE-PP-003"]["url"])
        self.assertIn("learninganalytics.upenn.edu", by_id["LE-PP-084"]["url"])
        self.assertIn("gse-ldt.stanford.edu", by_id["LE-PP-085"]["url"])
        self.assertIn("aialoe.org", by_id["LE-PP-087"]["url"])
        self.assertIn("engineering.purdue.edu/ENE", by_id["LE-PP-089"]["url"])


if __name__ == "__main__":
    unittest.main()
