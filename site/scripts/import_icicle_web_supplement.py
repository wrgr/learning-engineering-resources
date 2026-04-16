"""Supplement the site with the priority items from sagroups.ieee.org/icicle/resources/.

This is a hand-curated add-on to the Excel and archive-registry seeders. It pulls
in items we identified as high-value but missing after a full read of the ICICLE
resources page:

  - Canonical book: Goodell & Kolodner, *Learning Engineering Toolkit* (+ 3 OA chapters)
  - Four widely-cited reports from the ICICLE Background/Reports section
  - GIFT + Yet Analytics (tooling platforms)
  - MITili, Playful Journey Lab, IEEE LTSC (community institutions)
  - Four ICICLE conference-year instances as events
  - "Examples of Roles on a LE Team" practice document

All items carry provenance ref = "IEEE ICICLE resources page (web harvest)".
Idempotent: skips MDX files whose slug already exists on disk.

    source venv/bin/activate
    python3 site/scripts/import_icicle_web_supplement.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "site" / "src" / "content"

DATASET = "IEEE ICICLE resources page (web harvest)"
SHEET = "sagroups.ieee.org/icicle/resources"

# Each tuple: (collection, {frontmatter+body})
ITEMS: list[tuple[str, dict]] = [
    # ─── Reading List: the canonical book + open-access chapters ───────────
    ("reading-list", {
        "title": "Learning Engineering Toolkit: Evidence-Based Practices from the Learning Sciences",
        "format": "book",
        "venue": "Routledge",
        "authors": "Jim Goodell and Janet Kolodner (eds.)",
        "year": 2022,
        "url": "https://www.routledge.com/Learning-Engineering-Toolkit-Evidence-Based-Practices-from-the-Learning/Goodell-Kolodner/p/book/9781032232829",
        "cluster": "ICICLE resources",
        "topics": ["T00", "T03"],
        "featured": True,
        "body": (
            "The canonical book-length treatment of learning engineering — edited by "
            "Goodell and Kolodner with contributions from many ICICLE practitioners. "
            "Defines the field, walks through the process, and gives concrete "
            "applied examples. Several chapters are free via Taylor & Francis Open Access."
        ),
    }),
    ("reading-list", {
        "title": "LE Toolkit — Introduction (open access chapter)",
        "format": "book",
        "venue": "Taylor & Francis Open Access",
        "authors": "Jim Goodell",
        "year": 2022,
        "url": "https://www.taylorfrancis.com/chapters/oa-edit/10.4324/9781003276579-3/introduction-jim-goodell",
        "cluster": "ICICLE resources",
        "topics": ["T00"],
        "body": "Open-access introductory chapter of the Learning Engineering Toolkit.",
    }),
    ("reading-list", {
        "title": "LE Toolkit — Learning Engineering is a Process (open access chapter)",
        "format": "book",
        "venue": "Taylor & Francis Open Access",
        "authors": "Aaron Kessler, Scotty Craig, Jim Goodell, Dina Kurzweil, Scott Greenwald",
        "year": 2022,
        "url": "https://www.taylorfrancis.com/chapters/oa-edit/10.4324/9781003276579-5/learning-engineering-process-aaron-kessler-scotty-craig-jim-goodell-dina-kurzweil-scott-greenwald",
        "cluster": "ICICLE resources",
        "topics": ["T03"],
        "body": "Open-access chapter defining learning engineering as an iterative process.",
    }),
    ("reading-list", {
        "title": "LE Toolkit — Learning Engineering Applies the Learning Sciences (open access chapter)",
        "format": "book",
        "venue": "Taylor & Francis Open Access",
        "authors": "Jim Goodell, Janet Kolodner, Aaron Kessler",
        "year": 2022,
        "url": "https://www.taylorfrancis.com/chapters/oa-edit/10.4324/9781003276579-6/learning-engineering-applies-learning-sciences-jim-goodell-janet-kolodner-aaron-kessler",
        "cluster": "ICICLE resources",
        "topics": ["T01", "T03"],
        "body": "Open-access chapter on the learning-sciences foundations of LE practice.",
    }),

    # ─── Reading List: four widely-cited reports ───────────────────────────
    ("reading-list", {
        "title": "The Science of Remote Learning",
        "format": "report",
        "venue": "MIT Open Learning",
        "authors": "Jim Goodell and Aaron Kessler (eds.)",
        "year": 2020,
        "url": "https://openlearning.mit.edu/sites/default/files/inline-files/TheScienceofRemoteLearning.pdf",
        "cluster": "ICICLE resources",
        "topics": ["T01", "T11"],
        "featured": True,
        "body": "Pandemic-era compilation from MIT Open Learning on what the learning sciences say about effective remote instruction.",
    }),
    ("reading-list", {
        "title": "2020 EDUCAUSE Horizon Report — Teaching and Learning Edition",
        "format": "report",
        "venue": "EDUCAUSE",
        "year": 2020,
        "url": "https://library.educause.edu/resources/2020/3/2020-educause-horizon-report-teaching-and-learning-edition",
        "cluster": "ICICLE resources",
        "topics": ["T00", "T15"],
        "body": "Includes a section on \"Elevation of Instructional Design, Learning Engineering, and UX Design in Pedagogy in Practice\" — widely cited in making the case for LE as an emerging role.",
    }),
    ("reading-list", {
        "title": "Bridging learning research and teaching practice for the public good: The learning engineer",
        "format": "report",
        "venue": "TIAA Institute",
        "authors": "Candace Thille",
        "year": 2016,
        "url": "https://www.tiaa.org/content/dam/tiaa/institute/pdf/full-report/2017-02/bridging-learning-research-and-teaching-practice.pdf",
        "cluster": "ICICLE resources",
        "topics": ["T00"],
        "featured": True,
        "body": "One of the earliest articulations of the learning-engineer role, by Candace Thille. Still cited as a founding document.",
    }),
    ("reading-list", {
        "title": "Online Education: A Catalyst for Higher Education Reforms",
        "format": "report",
        "venue": "MIT Online Education Policy Initiative",
        "year": 2016,
        "url": "https://oepi.mit.edu/files/2016/09/MIT-Online-Education-Policy-Initiative-April-2016.pdf",
        "cluster": "ICICLE resources",
        "topics": ["T11", "T16"],
        "body": "MIT policy report calling for learning engineering as a discipline — early institutional signal toward the field.",
    }),

    # ─── Practice: the \"roles and expertise\" doc that was missing ────────
    ("practice", {
        "title": "Examples of Roles and Areas of Expertise on a LE Team",
        "format": "framework",
        "venue": "IEEE ICICLE",
        "url": "https://docs.google.com/document/d/1TR0OdxNbcAdMpZB_jyOHFYvRoTB7Jh55q5q8A8HGiFY/edit",
        "cluster": "ICICLE resources",
        "topics": ["T00", "T16"],
        "body": "ICICLE-curated reference listing the roles and expertise that typically compose a learning engineering team — useful for staffing plans and hiring rubrics.",
    }),

    # ─── Tools ─────────────────────────────────────────────────────────────
    ("tools", {
        "title": "GIFT — Generalized Intelligent Framework for Tutoring",
        "format": "platform",
        "venue": "US Army Research Laboratory",
        "url": "https://gifttutoring.org/",
        "cluster": "ICICLE resources",
        "topics": ["T06", "T11"],
        "featured": True,
        "body": "Open-source framework for authoring, delivering, and assessing intelligent tutoring systems. Army-funded; widely used in defense and adjacent workforce training contexts.",
    }),
    ("tools", {
        "title": "Yet Analytics — Learning Engineering Tools",
        "format": "platform",
        "venue": "Yet Analytics",
        "url": "https://www.yetanalytics.com/learningengineering",
        "cluster": "ICICLE resources",
        "topics": ["T04", "T11"],
        "body": "Commercial learning-engineering toolkit spanning data design, instrumentation, and evaluation. Highlighted on the ICICLE resources page as a tools reference.",
    }),

    # ─── Community (institutions / orgs) ──────────────────────────────────
    ("community", {
        "title": "MIT Integrated Learning Initiative (MITili)",
        "format": "org",
        "venue": "MIT",
        "url": "https://mitili.mit.edu/",
        "cluster": "MIT",
        "topics": ["T01", "T11"],
        "body": "MIT-wide initiative supporting research on learning and its translation into practice. Adjacent to and overlapping with the LEAP group; regularly surfaces in ICICLE materials.",
    }),
    ("community", {
        "title": "Playful Journey Lab",
        "format": "org",
        "venue": "MIT",
        "url": "https://playful.mit.edu/",
        "cluster": "MIT",
        "topics": ["T08", "T01"],
        "body": "MIT lab building playful assessment tools and running the \"Schools of Tomorrow\" Learning Engineering Project Blueprint. Listed alongside MITili in ICICLE's community section.",
    }),
    ("community", {
        "title": "IEEE Learning Technology Standards Committee (LTSC)",
        "format": "org",
        "venue": "IEEE",
        "url": "https://sagroups.ieee.org/ltsc/",
        "cluster": "IEEE ICICLE",
        "topics": ["T16"],
        "body": "IEEE standards body responsible for learning-technology interoperability standards — the institutional home of xAPI-adjacent work and a natural partner to ICICLE's working groups.",
    }),

    # ─── Events: four ICICLE conference instances ──────────────────────────
    ("events", {
        "title": "ICICLE Conference on Learning Engineering 2024",
        "format": "conference",
        "venue": "IEEE ICICLE",
        "year": 2024,
        "url": "https://sagroups.ieee.org/icicle/2024-icicle-conference-on-learning-engineering/",
        "cluster": "ICICLE Annual Meeting",
        "topics": ["T00"],
        "featured": True,
        "body": "Annual ICICLE convening — 2024 program, proceedings, and recorded sessions.",
    }),
    ("events", {
        "title": "ICICLE Conference on Learning Engineering 2023",
        "format": "conference",
        "venue": "IEEE ICICLE",
        "year": 2023,
        "url": "https://sagroups.ieee.org/icicle/2023-icicle-conference-on-learning-engineering/",
        "cluster": "ICICLE Annual Meeting",
        "topics": ["T00"],
        "body": "Annual ICICLE convening — 2023 program, proceedings, and recorded sessions.",
    }),
    ("events", {
        "title": "ICICLE Conference on Learning Engineering 2022",
        "format": "conference",
        "venue": "IEEE ICICLE",
        "year": 2022,
        "url": "https://sagroups.ieee.org/icicle/2022-icicle-conference-on-learning-engineering/",
        "cluster": "ICICLE Annual Meeting",
        "topics": ["T00"],
        "body": "Annual ICICLE convening — 2022 program, proceedings, and recorded sessions.",
    }),
    ("events", {
        "title": "ICICLE Conference on Learning Engineering 2019",
        "format": "conference",
        "venue": "IEEE ICICLE",
        "year": 2019,
        "url": "https://sagroups.ieee.org/icicle/proceedings/",
        "cluster": "ICICLE Annual Meeting",
        "topics": ["T00"],
        "body": "First ICICLE conference proceedings — the opening public record of the field's annual meeting.",
    }),
]


def slugify(text: str) -> str:
    """Convert a title to a filesystem-safe slug, clipped to 70 chars."""
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:70] or "untitled"


def yaml_escape(s: str) -> str:
    """Quote a string value for YAML frontmatter output."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_mdx(collection: str, data: dict) -> bool:
    """Write a single MDX file unless a file with the same slug already exists."""
    out_dir = CONTENT / collection
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(data["title"])
    path = out_dir / f"{slug}.mdx"
    if path.exists():
        return False

    lines: list[str] = ["---"]

    def put(key: str, value):
        if value is None or value == "" or value == []:
            return
        if isinstance(value, bool):
            if value:
                lines.append(f"{key}: true")
            return
        if isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
            return
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {yaml_escape(str(item))}")
            return
        lines.append(f"{key}: {yaml_escape(str(value))}")

    put("title", data["title"])
    put("format", data["format"])
    put("venue", data.get("venue"))
    put("authors", data.get("authors"))
    if data.get("year"):
        put("year", int(data["year"]))
    put("url", data.get("url"))
    put("cluster", data.get("cluster"))
    put("topics", data.get("topics", []))
    put("tags", data.get("tags", []) + ["icicle"])
    put("featured", data.get("featured", False))

    lines.append("provenance:")
    lines.append(f"  dataset: {yaml_escape(DATASET)}")
    lines.append(f"  sheet: {yaml_escape(SHEET)}")

    lines.append("---")
    lines.append("")
    lines.append(data.get("body", "_Blurb pending._").strip())
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return True


def main() -> None:
    """Emit every item in ITEMS into its collection, skipping duplicates."""
    counts: dict[str, int] = {}
    for collection, data in ITEMS:
        if write_mdx(collection, data):
            counts[collection] = counts.get(collection, 0) + 1

    print("Wrote MDX from ICICLE web supplement:")
    for k in ("practice", "tools", "reading-list", "events", "community"):
        print(f"  {k:13s} +{counts.get(k, 0)}")
    print(f"  total         {sum(counts.values())}")


if __name__ == "__main__":
    main()
