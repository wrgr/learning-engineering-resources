"""Unit tests for fast-path paper enrichment stub in `scripts/build_dataset.py`."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from build_dataset import _paper_enrichment_stub


class PaperEnrichmentStubTests(unittest.TestCase):
    def test_stub_counts_papers(self) -> None:
        seed = [{"id": "a", "abstract": "x", "abstract_source": "openalex", "abstract_is_proxy": False}]
        hop = [{"id": "W1", "abstract": "", "abstract_source": "", "abstract_is_proxy": False}]
        out = _paper_enrichment_stub(seed, hop)
        self.assertEqual(out["papers_total"], 2)
        self.assertGreaterEqual(out["papers_missing_abstract"], 1)


if __name__ == "__main__":
    unittest.main()
