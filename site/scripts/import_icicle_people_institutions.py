"""Seed the community collection with ICICLE people and institutions.

Source: archive/corpus/tables/programs_people_registry.json
  - all CO (organizations) and PC (programs) records
  - PP (person) records only when 'ICICLE' appears in their affiliation,
    description, or notes (i.e. explicitly on the ICICLE site's roster)

The titlesearch practitioner registry is intentionally not consulted here —
titlesearch results are kept self-contained outside this site for now.

Idempotent: skips MDX files that already exist on disk. Run from the repo root:

    source venv/bin/activate
    python3 site/scripts/import_icicle_people_institutions.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "archive" / "corpus" / "tables" / "programs_people_registry.json"
COMMUNITY = ROOT / "site" / "src" / "content" / "community"


def slugify(text: str) -> str:
    """Convert a title to a filesystem-safe slug, clipped to 70 chars."""
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:70] or "untitled"


def yaml_escape(s: str) -> str:
    """Quote a string value for YAML frontmatter output."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def is_icicle_person(r: dict) -> bool:
    """Return True if this person's record explicitly mentions ICICLE."""
    if r.get("content_type") != "PP":
        return False
    blob = " ".join(
        str(r.get(k, "") or "")
        for k in ("affiliation_or_venue", "description", "notes")
    ).lower()
    return "icicle" in blob


def infer_cluster(rec: dict) -> str:
    """Pull a SIG / MIG tag from the affiliation field when present."""
    aff = rec.get("affiliation_or_venue", "") or ""
    m = re.search(r"IEEE ICICLE\s*[—–-]\s*([^;]+)", aff)
    if m:
        return f"ICICLE {m.group(1).strip()}"
    if "IEEE ICICLE" in aff:
        return "IEEE ICICLE"
    head = aff.split("—")[0].split("/")[0].strip()
    return head[:60]


def write_mdx(slug: str, frontmatter: dict, body: str) -> bool:
    """Write a single community MDX file unless it already exists."""
    COMMUNITY.mkdir(parents=True, exist_ok=True)
    path = COMMUNITY / f"{slug}.mdx"
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
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {yaml_escape(str(item))}")
            return
        lines.append(f"{key}: {yaml_escape(str(value))}")

    put("title", frontmatter["title"])
    put("format", frontmatter["format"])
    put("venue", frontmatter.get("venue"))
    put("url", frontmatter.get("url"))
    put("cluster", frontmatter.get("cluster"))
    put("topics", frontmatter.get("topics", []))
    put("tags", frontmatter.get("tags", []))

    prov = frontmatter["provenance"]
    lines.append("provenance:")
    lines.append(f"  dataset: {yaml_escape(prov['dataset'])}")
    if prov.get("ref"):
        lines.append(f"  ref: {yaml_escape(prov['ref'])}")

    lines.append("---")
    lines.append("")
    lines.append(body.strip() or "_No description yet._")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return True


def ingest_people(registry: list[dict], stats: dict) -> None:
    """Emit person MDX for every ICICLE-tagged PP record."""
    for r in registry:
        if not is_icicle_person(r):
            continue
        name = r["name"]
        aff = r.get("affiliation_or_venue", "") or ""
        desc = (r.get("description", "") or "").strip()

        frontmatter = {
            "title": name,
            "format": "person",
            "venue": aff,
            "url": r.get("url") if (r.get("url") or "").startswith("http") else None,
            "cluster": infer_cluster(r),
            "topics": ["T16"],
            "tags": ["icicle"],
            "provenance": {
                "dataset": "IEEE ICICLE programs & people registry",
                "ref": r["resource_id"],
            },
        }
        if write_mdx(f"person-{slugify(name)}", frontmatter, desc):
            stats["people"] = stats.get("people", 0) + 1


def ingest_orgs_and_programs(registry: list[dict], stats: dict) -> None:
    """Emit MDX for every CO (org) and PC (program) record."""
    for r in registry:
        ct = r.get("content_type")
        if ct not in {"CO", "PC"}:
            continue
        name = r["name"]
        fmt = "org" if ct == "CO" else "program"
        aff = r.get("affiliation_or_venue", "") or ""
        url = r.get("url")
        url = url if url and url.startswith("http") else None

        frontmatter = {
            "title": name,
            "format": fmt,
            "venue": aff,
            "url": url,
            "cluster": infer_cluster(r),
            "topics": ["T16"],
            "tags": ["icicle"] if ("ieee icicle" in aff.lower() or "icicle" in name.lower()) else [],
            "provenance": {
                "dataset": "IEEE ICICLE programs & people registry",
                "ref": r["resource_id"],
            },
        }
        body = (r.get("description", "") or "").strip() or "_No description yet._"
        slug_prefix = "org-" if ct == "CO" else "program-"
        if write_mdx(f"{slug_prefix}{slugify(name)}", frontmatter, body):
            key = "orgs" if ct == "CO" else "programs"
            stats[key] = stats.get(key, 0) + 1


def main() -> None:
    """Ingest ICICLE people + all institutions/programs into the community collection."""
    if not REGISTRY.exists():
        raise SystemExit(f"Registry not found: {REGISTRY}")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    stats: dict[str, int] = {}
    ingest_people(registry, stats)
    ingest_orgs_and_programs(registry, stats)

    print("Wrote community MDX:")
    print(f"  people:   +{stats.get('people', 0)}")
    print(f"  orgs:     +{stats.get('orgs', 0)}")
    print(f"  programs: +{stats.get('programs', 0)}")
    print(f"  total:    {sum(stats.values())}")


if __name__ == "__main__":
    main()
