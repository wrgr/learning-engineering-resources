"""Guardrail: graph-derived navigator rows module stays present for community toggle."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class GraphNavigatorRowsStubTests(unittest.TestCase):
    def test_module_exports_builder(self) -> None:
        path = REPO / "app" / "graphNavigatorRows.js"
        text = path.read_text(encoding="utf-8")
        self.assertIn("export function graphNodesToNavigatorRows", text)
        self.assertIn("browseGroupKey", text)
        self.assertIn("from_graph", text)


if __name__ == "__main__":
    unittest.main()
