"""Tests for collect_citing_works_openalex helpers (no network)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import collect_citing_works_openalex as cc  # noqa: E402


class CitingWorksHelpersTests(unittest.TestCase):
    def test_work_ids_from_merged_papers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "papers.json"
            p.write_text(
                json.dumps(
                    {
                        "papers": [
                            {"openalex_id": "https://openalex.org/W111", "id": "W111"},
                            {"id": "W222"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            got = cc._work_ids_from_merged_papers(p)
            self.assertEqual(got, ["W111", "W222"])

    def test_work_ids_from_seed_list_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ieee.json"
            p.write_text(
                json.dumps({"work_ids": ["https://openalex.org/W999", "W888", "bad"]}),
                encoding="utf-8",
            )
            got = cc.work_ids_from_seed_list_json(p)
            self.assertEqual(got, ["W999", "W888"])

    def test_dedupe_candidates_prefers_lower_hop(self) -> None:
        rows = [
            {"work_id": "W1", "hop_round": 2},
            {"work_id": "W1", "hop_round": 1},
        ]
        got = cc._dedupe_candidates_by_hop(rows)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["hop_round"], 1)

    def test_round2_seed_ids_respects_cap_and_exclude(self) -> None:
        round1 = [
            {"work_id": "W10", "cited_by_count": 100},
            {"work_id": "W20", "cited_by_count": 50},
            {"work_id": "W30", "cited_by_count": 10},
        ]
        got = cc._round2_seed_ids(round1, exclude={"W20"}, max_seeds=2)
        self.assertEqual(got, ["W10", "W30"])


if __name__ == "__main__":
    unittest.main()
