"""Tests for optional `.env` loading in scripts/utils.py (no real secrets)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class LoadDotenvOptionalTests(unittest.TestCase):
    def test_loads_unset_keys_only(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from utils import load_dotenv_optional  # noqa: E402

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / ".env"
            p.write_text(
                'FOO_FROM_ENV=hello\n'
                'BAR=quoted "world"\n'
                'export BAZ=1\n'
                '# comment\n'
                'EMPTY=\n',
                encoding="utf-8",
            )
            prior = os.environ.get("ALREADY_SET")
            os.environ["ALREADY_SET"] = "yes"
            p.write_text(
                p.read_text(encoding="utf-8") + "ALREADY_SET=override\n",
                encoding="utf-8",
            )
            try:
                load_dotenv_optional(p)
                self.assertEqual(os.environ.get("FOO_FROM_ENV"), "hello")
                self.assertEqual(os.environ.get("BAR"), 'quoted "world"')
                self.assertEqual(os.environ.get("BAZ"), "1")
                self.assertEqual(os.environ.get("EMPTY"), "")
                self.assertEqual(os.environ.get("ALREADY_SET"), "yes")
            finally:
                for k in ("FOO_FROM_ENV", "BAR", "BAZ", "EMPTY"):
                    os.environ.pop(k, None)
                if prior is None:
                    os.environ.pop("ALREADY_SET", None)
                else:
                    os.environ["ALREADY_SET"] = prior


if __name__ == "__main__":
    unittest.main()
