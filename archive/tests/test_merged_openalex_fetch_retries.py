"""Tests for merged-lane OpenAlex work fetch retry wrapper."""

from __future__ import annotations

import sys
import unittest
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from build_merged_site_dataset import _fetch_openalex_work_for_lane


class MergedOpenAlexFetchRetriesTests(unittest.TestCase):
    @patch("build_merged_site_dataset.api_get_json")
    def test_succeeds_after_transient_failures(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = [
            ConnectionError("reset"),
            {"id": "https://openalex.org/W1", "display_name": "X"},
        ]
        out = _fetch_openalex_work_for_lane("W1")
        self.assertEqual(out["display_name"], "X")
        self.assertEqual(mock_get.call_count, 2)

    @patch("build_merged_site_dataset.api_get_json")
    def test_404_not_retried(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = urllib.error.HTTPError(
            "https://api.openalex.org/works/W999", 404, "Not Found", {}, BytesIO(b"{}")
        )
        with self.assertRaises(RuntimeError):
            _fetch_openalex_work_for_lane("W999")
        self.assertEqual(mock_get.call_count, 1)


if __name__ == "__main__":
    unittest.main()
