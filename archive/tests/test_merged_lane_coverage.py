"""Tests that lane_work_specs meets corpus/merged_lane/coverage_manifest.json commitments."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class MergedLaneCoverageTests(unittest.TestCase):
    def test_lane_specs_cover_manifest_registry_ids(self) -> None:
        manifest = json.loads(
            (REPO / "corpus" / "merged_lane" / "coverage_manifest.json").read_text(encoding="utf-8")
        )
        specs = json.loads(
            (REPO / "corpus" / "merged_lane" / "lane_work_specs.json").read_text(encoding="utf-8")
        )
        prog_ids = {r.get("registry_program_id") for r in specs if r.get("registry_program_id")}
        person_ids = {r.get("registry_person_id") for r in specs if r.get("registry_person_id")}
        for rid in manifest.get("required_registry_program_ids") or []:
            self.assertIn(
                rid,
                prog_ids,
                f"Add a lane_work_specs row with registry_program_id {rid} or update the manifest.",
            )
        for rid in manifest.get("required_registry_person_ids") or []:
            self.assertIn(
                rid,
                person_ids,
                f"Add a lane_work_specs row with registry_person_id {rid} or update the manifest.",
            )
        min_themed = int(manifest.get("minimum_thematic_rows") or 0)
        thematic_n = sum(1 for r in specs if r.get("source_expansion") == "thematic")
        self.assertGreaterEqual(
            thematic_n,
            min_themed,
            f"Expected at least {min_themed} thematic rows (source_expansion: thematic).",
        )


if __name__ == "__main__":
    unittest.main()
