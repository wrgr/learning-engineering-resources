"""Tests for OpenAlex query auth helpers used by `run_openalex_expansion.py`."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from run_openalex_expansion import openalex_env_auth_params


def _env_without_openalex_keys() -> dict:
    return {
        k: v
        for k, v in os.environ.items()
        if k not in ("OPENALEX_MAILTO", "OPENALEX_API_KEY", "OPENALEX_KEY")
    }


class OpenAlexExpansionAuthTests(unittest.TestCase):
    def test_openalex_env_auth_params_empty_without_env(self) -> None:
        with patch.dict(os.environ, _env_without_openalex_keys(), clear=True):
            self.assertEqual(openalex_env_auth_params(), {})

    def test_openalex_env_auth_params_reads_mailto_and_key(self) -> None:
        base = _env_without_openalex_keys()
        base["OPENALEX_MAILTO"] = "a@example.com"
        base["OPENALEX_API_KEY"] = "secret"
        with patch.dict(os.environ, base, clear=True):
            p = openalex_env_auth_params()
        self.assertEqual(p["mailto"], "a@example.com")
        self.assertEqual(p["api_key"], "secret")


if __name__ == "__main__":
    unittest.main()
