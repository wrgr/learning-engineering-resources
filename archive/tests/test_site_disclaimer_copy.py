"""Ensures shared disclaimer and edition labels exist in app/siteCopy.js for hero + footer."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SITE_COPY = REPO / "app" / "siteCopy.js"


class SiteDisclaimerCopyTests(unittest.TestCase):
    def test_site_copy_has_disclaimer_export(self) -> None:
        text = SITE_COPY.read_text(encoding="utf-8")
        self.assertIn("export const SITE_DISCLAIMER", text)
        self.assertRegex(
            text,
            re.compile(r"errors and omissions", re.I),
            "expected disclaimer phrase in siteCopy.js",
        )

    def test_site_copy_has_edition_labels_for_two_html_entry_points(self) -> None:
        text = SITE_COPY.read_text(encoding="utf-8")
        self.assertIn("export const EDITION_LABEL_CLASSIC", text)
        self.assertIn("export const EDITION_LABEL_MERGED", text)
        self.assertIn("index.html", text)
        self.assertIn("merged.html", text)


if __name__ == "__main__":
    unittest.main()
