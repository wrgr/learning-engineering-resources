"""Ensures sticky nav targets and section anchor ids stay aligned."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SITE_NAV = REPO / "app" / "components" / "SiteNav.js"
SECTION_FILES = [
    REPO / "app" / "components" / "sections" / "HeroSection.js",
    REPO / "app" / "components" / "sections" / "GraphWorkspaceSection.js",
    REPO / "app" / "components" / "sections" / "ResourceNavigatorSection.js",
    REPO / "app" / "components" / "sections" / "PapersSection.js",
    REPO / "app" / "components" / "sections" / "FieldSignalsSection.js",
    REPO / "app" / "components" / "sections" / "ExtraDocsSection.js",
    REPO / "app" / "components" / "sections" / "UpdateWorkflowSection.js",
]


class SiteNavAnchorTests(unittest.TestCase):
    def test_nav_ids_match_section_markup(self) -> None:
        nav_text = SITE_NAV.read_text(encoding="utf-8")
        id_matches = re.findall(r'id:\s*"([^"]+)"', nav_text)
        self.assertGreater(len(id_matches), 3, "expected NAV_LINKS ids in SiteNav.js")
        nav_ids = set(id_matches)

        found = set()
        for path in SECTION_FILES:
            text = path.read_text(encoding="utf-8")
            for m in re.finditer(r'\bid="([^"]+)"', text):
                found.add(m.group(1))

        missing = nav_ids - found
        self.assertFalse(
            missing,
            f"nav links reference ids missing from sections: {sorted(missing)}",
        )

    def test_site_nav_scroll_spy_markup(self) -> None:
        text = SITE_NAV.read_text(encoding="utf-8")
        self.assertIn("computeActiveSectionId", text)
        self.assertIn("aria-current", text)


if __name__ == "__main__":
    unittest.main()
