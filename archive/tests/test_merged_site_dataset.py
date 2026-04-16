"""Smoke tests for merged site data bundle and lane specs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class MergedSiteDatasetTests(unittest.TestCase):
    def test_merged_lane_specs_valid(self) -> None:
        path = REPO / "corpus" / "merged_lane" / "lane_work_specs.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(raw, list)
        for row in raw:
            self.assertIn("work_id", row)
            self.assertIn("topic_codes", row)
            self.assertIn(row.get("corpus_tier", "core"), ("core", "expanded"))
            if "source_expansion" in row:
                self.assertIn(row["source_expansion"], ("thematic", "program", "person"))

    def test_merged_artifacts_exist(self) -> None:
        merged = REPO / "data" / "merged"
        for name in ("build_summary.json", "graph.json", "papers_merged_lane.json"):
            self.assertTrue((merged / name).is_file(), f"missing {name}")

    def test_merged_graph_has_merged_lane_nodes(self) -> None:
        graph = json.loads((REPO / "data" / "merged" / "graph.json").read_text(encoding="utf-8"))
        nodes = graph.get("nodes") or []
        hop2 = [n for n in nodes if n.get("type") == "paper" and n.get("hop") == 2]
        self.assertGreaterEqual(len(hop2), 3)
        tiers = {n.get("corpus_tier") for n in hop2}
        self.assertTrue(tiers.issubset({"core", "expanded", None}))

    def test_openalex_thematic_queries_include_llms(self) -> None:
        path = REPO / "corpus" / "merged_lane" / "openalex_thematic_queries.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        ids = {q["id"] for q in raw.get("queries", [])}
        self.assertTrue({"ai_education", "ai_learning_engineering", "llms_in_education"}.issubset(ids))


if __name__ == "__main__":
    unittest.main()
