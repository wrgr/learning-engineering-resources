"""Unit tests for OpenAlex quota/rate-limit detection used by api_get_json retries."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from openalex_client import _openalex_budget_or_rate_limit, _retry_after_seconds_from_openalex_body


class OpenAlexBudgetDetectionTests(unittest.TestCase):
    def test_detects_insufficient_budget_message(self) -> None:
        body = '{"error":"Rate limit exceeded","message":"Insufficient budget. Need more?"}'
        self.assertTrue(_openalex_budget_or_rate_limit(body))

    def test_non_json_not_budget(self) -> None:
        self.assertFalse(_openalex_budget_or_rate_limit("not json"))

    def test_retry_after_capped(self) -> None:
        body = '{"retryAfter": 68105}'
        self.assertLessEqual(_retry_after_seconds_from_openalex_body(body, 0), 120.0)


if __name__ == "__main__":
    unittest.main()
