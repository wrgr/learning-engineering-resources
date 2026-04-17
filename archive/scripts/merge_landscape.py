"""Merge landscape/ data into the main archive corpus tables.

Performs four merges:
  1. landscape/data/people.json     → programs_people_registry.json  (PP entries)
  2. landscape/data/papers.json     → academic_papers.jsonl          (AP entries)
  3. landscape/data/grey_literature.json → programs_people_registry.json (GL entries)
  4. landscape/data/organizations.json  → split by content_type:
       - CO/CE → programs_people_registry.json
       - SG    → icicle_resources_registry.json

Deduplicates on name (people/orgs) and title (papers/grey lit).
Reassigns resource IDs from LE-LS-* namespace into LE-PP-* or LE-IC-* as appropriate.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LANDSCAPE = ROOT / "landscape" / "data"
TABLES = ROOT / "archive" / "corpus" / "tables"
CORPUS = ROOT / "archive" / "corpus"

PP_REGISTRY = TABLES / "programs_people_registry.json"
IC_REGISTRY = TABLES / "icicle_resources_registry.json"
PAPERS_JSONL = CORPUS / "academic_papers.jsonl"
SEEDS_JSONL = CORPUS / "expansion_seed_queries.jsonl"


def load_json(path: Path) -> list:
    """Load a JSON array from a file."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: list) -> None:
    """Write a JSON array to a file."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file."""
    rows = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    """Write a JSONL file."""
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def next_pp_id(registry: list) -> int:
    """Find the next available LE-PP-NNN number."""
    max_n = 0
    for r in registry:
        rid = r.get("resource_id", "")
        if rid.startswith("LE-PP-"):
            try:
                n = int(rid.split("-")[-1])
                max_n = max(max_n, n)
            except ValueError:
                pass
    return max_n + 1


def next_ic_id(registry: list) -> int:
    """Find the next available LE-IC-NNN number."""
    max_n = 0
    for r in registry:
        rid = r.get("resource_id", "")
        if rid.startswith("LE-IC-"):
            try:
                n = int(rid.split("-")[-1])
                max_n = max(max_n, n)
            except ValueError:
                pass
    return max_n + 1


def normalize_name(name: str) -> str:
    """Normalize a name for dedup comparison."""
    return " ".join(name.lower().strip().split())


def normalize_title(title: str) -> str:
    """Normalize a title for dedup comparison."""
    return " ".join(title.lower().strip().split())


def person_to_pp_row(person: dict, new_id: str) -> dict:
    """Convert a landscape person record to a PP registry row."""
    secondary = person.get("secondary_topics", [])
    if isinstance(secondary, list):
        secondary = ", ".join(secondary)
    return {
        "resource_id": new_id,
        "status": "APPROVED",
        "content_type": "PP",
        "name": person["name"],
        "affiliation_or_venue": person.get("affiliation", ""),
        "url": person.get("url", ""),
        "primary_topic": person.get("primary_topic", "T00"),
        "secondary_topics": secondary,
        "description": person.get("role", ""),
        "notes": f"Landscape merge. Era: {person.get('era', 'unknown')}. Original ID: {person.get('resource_id', '')}.",
    }


def grey_lit_to_pp_row(item: dict, new_id: str) -> dict:
    """Convert a landscape grey literature record to a GL registry row."""
    secondary = item.get("secondary_topics", [])
    if isinstance(secondary, list):
        secondary = ", ".join(secondary)
    authors = item.get("authors", [])
    if isinstance(authors, list):
        authors = "; ".join(authors)
    return {
        "resource_id": new_id,
        "status": "APPROVED",
        "content_type": "GL",
        "name": item["title"],
        "affiliation_or_venue": item.get("publisher", ""),
        "url": item.get("url", ""),
        "primary_topic": item.get("primary_topic", "T00"),
        "secondary_topics": secondary,
        "description": item.get("significance", ""),
        "notes": f"Landscape merge. Authors: {authors}. Year: {item.get('year', '')}. Original ID: {item.get('resource_id', '')}.",
    }


def org_to_pp_row(org: dict, new_id: str) -> dict:
    """Convert a landscape org/conference record to a registry row."""
    ct = org.get("content_type", "CO")
    secondary = org.get("secondary_topics", [])
    if isinstance(secondary, list):
        secondary = ", ".join(secondary)
    return {
        "resource_id": new_id,
        "status": "APPROVED",
        "content_type": ct,
        "name": org.get("name", ""),
        "affiliation_or_venue": org.get("acronym", ""),
        "url": org.get("url", ""),
        "primary_topic": org.get("primary_topic", "T00"),
        "secondary_topics": secondary,
        "description": org.get("focus", ""),
        "notes": f"Landscape merge. Type: {org.get('type', '')}. Original ID: {org.get('resource_id', '')}. {org.get('notes', '')}",
    }


def org_to_ic_row(org: dict, new_id: str) -> dict:
    """Convert a landscape standards record to an ICICLE registry row."""
    secondary = org.get("secondary_topics", [])
    if isinstance(secondary, list):
        secondary = ", ".join(secondary)
    return {
        "resource_id": new_id,
        "status": "APPROVED",
        "content_type": "SG",
        "name": org.get("name", ""),
        "affiliation_or_venue": org.get("acronym", ""),
        "url": org.get("url", ""),
        "primary_topic": org.get("primary_topic", "T00"),
        "secondary_topics": secondary,
        "description": org.get("focus", ""),
        "notes": f"Landscape merge. Original ID: {org.get('resource_id', '')}. {org.get('notes', '')}",
    }


def paper_to_jsonl_row(paper: dict) -> dict:
    """Convert a landscape paper to an academic_papers.jsonl row."""
    secondary = paper.get("secondary_topics", [])
    if isinstance(secondary, list):
        secondary = ", ".join(secondary)
    authors = paper.get("authors", [])
    if isinstance(authors, list):
        authors = "; ".join(authors)
    return {
        "title": paper["title"],
        "authors": authors,
        "year": paper.get("year"),
        "venue": paper.get("venue", ""),
        "doi": paper.get("doi", ""),
        "url": paper.get("url", ""),
        "primary_topic": paper.get("primary_topic", "T00"),
        "secondary_topics": secondary,
        "tier": paper.get("tier", ""),
        "citation_count_approx": paper.get("citation_count_approx"),
        "significance": paper.get("significance", ""),
        "source": f"landscape_merge:{paper.get('resource_id', '')}",
    }


def paper_to_seed_query(paper: dict) -> dict | None:
    """Convert a landscape paper to a seed query for OpenAlex expansion."""
    doi = (paper.get("doi") or "").strip()
    title = (paper.get("title") or "").strip()
    if not doi and not title:
        return None
    return {
        "seed_id": paper.get("resource_id", ""),
        "seed_kind": "landscape_paper",
        "query_text": title,
        "doi": doi,
        "year": paper.get("year"),
    }


def main() -> None:
    """Run the landscape merge."""
    pp_registry = load_json(PP_REGISTRY)
    ic_registry = load_json(IC_REGISTRY)
    papers = load_jsonl(PAPERS_JSONL)
    seeds = load_jsonl(SEEDS_JSONL)

    pp_next = next_pp_id(pp_registry)
    ic_next = next_ic_id(ic_registry)

    existing_pp_names = {normalize_name(r.get("name", "")) for r in pp_registry}
    existing_ic_names = {normalize_name(r.get("name", "")) for r in ic_registry}
    existing_paper_titles = {normalize_title(p.get("title", "")) for p in papers}
    existing_seed_ids = {s.get("seed_id", "") for s in seeds}

    counts: Counter[str] = Counter()

    # 1. People
    landscape_people = load_json(LANDSCAPE / "people.json")
    for person in landscape_people:
        norm = normalize_name(person["name"])
        if norm in existing_pp_names:
            counts["people_skipped_dup"] += 1
            continue
        new_id = f"LE-PP-{pp_next:03d}"
        pp_registry.append(person_to_pp_row(person, new_id))
        existing_pp_names.add(norm)
        pp_next += 1
        counts["people_added"] += 1

    # 2. Grey literature
    landscape_gl = load_json(LANDSCAPE / "grey_literature.json")
    for item in landscape_gl:
        norm = normalize_title(item["title"])
        if norm in existing_pp_names or norm in existing_ic_names:
            counts["grey_lit_skipped_dup"] += 1
            continue
        # Check if already in registry by name
        existing_names_check = {normalize_name(r.get("name", "")) for r in pp_registry}
        norm_name = normalize_name(item["title"])
        if norm_name in existing_names_check:
            counts["grey_lit_skipped_dup"] += 1
            continue
        new_id = f"LE-PP-{pp_next:03d}"
        pp_registry.append(grey_lit_to_pp_row(item, new_id))
        pp_next += 1
        counts["grey_lit_added"] += 1

    # 3. Organizations — split CO/CE → PP registry, SG → IC registry
    landscape_orgs = load_json(LANDSCAPE / "organizations.json")
    for org in landscape_orgs:
        ct = org.get("content_type", "CO")
        norm = normalize_name(org.get("name", ""))
        if ct == "SG":
            if norm in existing_ic_names:
                counts["orgs_skipped_dup"] += 1
                continue
            new_id = f"LE-IC-{ic_next:03d}"
            ic_registry.append(org_to_ic_row(org, new_id))
            existing_ic_names.add(norm)
            ic_next += 1
            counts["standards_added"] += 1
        else:
            if norm in existing_pp_names:
                counts["orgs_skipped_dup"] += 1
                continue
            new_id = f"LE-PP-{pp_next:03d}"
            pp_registry.append(org_to_pp_row(org, new_id))
            existing_pp_names.add(norm)
            pp_next += 1
            counts["orgs_added"] += 1

    # 4. Papers → academic_papers.jsonl + seed queries
    landscape_papers = load_json(LANDSCAPE / "papers.json")
    for paper in landscape_papers:
        norm = normalize_title(paper["title"])
        if norm in existing_paper_titles:
            counts["papers_skipped_dup"] += 1
            continue
        papers.append(paper_to_jsonl_row(paper))
        existing_paper_titles.add(norm)
        counts["papers_added"] += 1

        seed = paper_to_seed_query(paper)
        if seed and seed["seed_id"] not in existing_seed_ids:
            seeds.append(seed)
            existing_seed_ids.add(seed["seed_id"])
            counts["seeds_added"] += 1

    # Write outputs
    write_json(PP_REGISTRY, pp_registry)
    write_json(IC_REGISTRY, ic_registry)
    write_jsonl(PAPERS_JSONL, papers)
    write_jsonl(SEEDS_JSONL, seeds)

    print("Landscape merge complete:")
    for key, val in sorted(counts.items()):
        print(f"  {key}: {val}")
    print(f"\nFinal counts:")
    print(f"  programs_people_registry: {len(pp_registry)}")
    print(f"  icicle_resources_registry: {len(ic_registry)}")
    print(f"  academic_papers: {len(papers)}")
    print(f"  expansion_seed_queries: {len(seeds)}")


if __name__ == "__main__":
    main()
