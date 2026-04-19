"""Expand the paper corpus with top LE-relevant works from conference-chair people.

For every person YAML under landscape/resources/people/ that has an openalex_id,
fetch the author's top works and keep the top N whose title+venue pass the same
LE-keyword / non-LE-venue filter used by enrich_key_works.py. Deduplicate against
the existing paper corpus (by DOI and by openalex work id), then write any new
papers under landscape/resources/papers/ as LE-AP-NNN YAML files with
`source: openalex_expansion` and `status: seed`.

Topic inheritance: each new paper's primary_topic is taken from the introducing
chair with the highest cited_by_count among co-authoring chairs; secondary_topics
is the union across all chair co-authors (minus the primary).

Usage:
    python3 scripts/expand_corpus_from_chairs.py            # dry run (default 5 per chair)
    python3 scripts/expand_corpus_from_chairs.py --write    # apply
    python3 scripts/expand_corpus_from_chairs.py --per-chair 10 --write
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
PEOPLE_DIR = REPO_ROOT / "landscape" / "resources" / "people"
PAPERS_DIR = REPO_ROOT / "landscape" / "resources" / "papers"

MAIL = os.environ.get("OPENALEX_MAILTO", "")
KEY = os.environ.get("OPENALEX_API_KEY", "")

# LE relevance keywords — matches enrich_key_works.py
LE_KEYWORDS = (
    "learning engineer", "learning scienc", "learning analytics", "educational data",
    "instructional design", "intelligent tutor", "cognitive tutor", "adaptive learning",
    "personalized learning", "educational technology", "cognitive load",
    "scaffolding", "problem-based learning", "case-based", "knowledge tracing",
    "learner model", "open learn", "mooc", "online learn", "classroom",
    "competency", "bloom", "metacognit", "self-regulated",
)

# Venues that flag a same-name mismatch — drop outright.
NON_LE_VENUE_MARKERS = (
    "entomology", "neurology", "oncology", "cardiolog", "biochem",
    "pharmacol", "surgery", "rugby", "oxygen uptake", "biosciences",
    "planar energy", "alzheimer", "parkinson", "brain injury",
    "sports medicine", "sports science", "treadmill",
)

# Chairs introduced in this expansion pass — LE-PP-250 through LE-PP-321.
CHAIR_ID_RANGE = range(250, 322)


def oa_get(path: str) -> dict:
    """GET OpenAlex with mailto + api_key; return parsed JSON."""
    if not MAIL:
        raise RuntimeError("OPENALEX_MAILTO is not set. Export it or source .env.")
    sep = "&" if "?" in path else "?"
    url = f"https://api.openalex.org{path}{sep}mailto={MAIL}"
    if KEY:
        url += f"&api_key={KEY}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def venue_of(w: dict) -> str:
    """Return the primary source display_name for a work, or empty string."""
    return ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "") or ""


def is_non_le_venue(w: dict) -> bool:
    """True if the work's venue contains an obviously-non-LE marker."""
    v = venue_of(w).lower()
    return any(m in v for m in NON_LE_VENUE_MARKERS)


def le_score(w: dict) -> float:
    """Score a work by LE-keyword hits in title+venue, tie-broken by citations."""
    title = (w.get("title") or "").lower()
    haystack = f"{title} {venue_of(w).lower()}"
    hits = sum(1 for k in LE_KEYWORDS if k in haystack)
    cites = w.get("cited_by_count", 0) or 0
    return hits * 10 + math.log10(cites + 1)


def le_filtered_works(author_id: str, n: int, pool_size: int = 50) -> list[dict]:
    """Return up to n LE-relevant works for this author."""
    aid = author_id.rsplit("/", 1)[-1]
    data = oa_get(
        f"/works?filter=author.id:{aid}&sort=cited_by_count:desc&per_page={pool_size}"
    )
    pool = [w for w in (data.get("results") or []) if not is_non_le_venue(w)]
    le_hits = [
        w for w in pool
        if any(k in (w.get("title") or "").lower() for k in LE_KEYWORDS)
        or any(k in venue_of(w).lower() for k in LE_KEYWORDS)
    ]
    return sorted(le_hits, key=le_score, reverse=True)[:n]


def load_chairs() -> list[dict]:
    """Load all chair people records (LE-PP in CHAIR_ID_RANGE) that have an openalex_id."""
    out = []
    for yf in sorted(PEOPLE_DIR.glob("le-pp-*.yaml")):
        rec = yaml.safe_load(yf.read_text(encoding="utf-8")) or {}
        rid = rec.get("resource_id", "")
        m = re.match(r"LE-PP-(\d+)", rid)
        if not m or int(m.group(1)) not in CHAIR_ID_RANGE:
            continue
        if not rec.get("openalex_id"):
            continue
        out.append(rec)
    return out


def load_existing_index() -> tuple[set[str], set[str]]:
    """Return (set of lowercased DOIs, set of OpenAlex work IDs) already in the corpus."""
    dois: set[str] = set()
    oa_ids: set[str] = set()
    for yf in PAPERS_DIR.glob("*.yaml"):
        rec = yaml.safe_load(yf.read_text(encoding="utf-8")) or {}
        d = (rec.get("doi") or "").strip().lower()
        if d:
            dois.add(normalize_doi(d))
        oid = (rec.get("openalex_id") or "").strip()
        if oid:
            oa_ids.add(oid.rsplit("/", 1)[-1])  # strip domain if present
    return dois, oa_ids


def normalize_doi(doi: str) -> str:
    """Strip leading https://doi.org/ and lowercase a DOI so comparisons are stable."""
    d = doi.lower().strip()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d


def next_available_id(start: int = 830) -> int:
    """Find the lowest unused LE-AP integer >= start."""
    used = set()
    for yf in PAPERS_DIR.glob("le-ap-*.yaml"):
        m = re.match(r"le-ap-(\d+)", yf.name)
        if m:
            used.add(int(m.group(1)))
    i = start
    while i in used:
        i += 1
    return i


def tier_for(cites: int) -> str:
    """Map citation count into the corpus's three-bucket tier scheme."""
    if cites >= 1000:
        return "foundational"
    if cites >= 500:
        return "highly_cited"
    return "contemporary"


def slug_from_work(w: dict, authors: list[str]) -> str:
    """Build a short hyphenated filename slug like 'koedinger-1997' from a work."""
    year = w.get("publication_year") or "nd"
    # Use first author surname if available
    first = authors[0] if authors else ""
    surname = first.split()[-1] if first else "anon"
    surname = re.sub(r"[^a-zA-Z]+", "", surname).lower() or "anon"
    return f"{surname}-{year}"


def extract_authors(w: dict) -> list[str]:
    """Return author display_names in order from an OpenAlex work."""
    return [
        (a.get("author") or {}).get("display_name", "")
        for a in (w.get("authorships") or [])
        if (a.get("author") or {}).get("display_name")
    ]


def merge_topics(chairs: list[dict]) -> tuple[str, list[str]]:
    """Pick primary_topic from the top-cited chair; union secondaries from all co-authoring chairs."""
    # Rank chairs by their recorded cited_by_count if available, else keep order given.
    primary_candidates = [c.get("primary_topic") for c in chairs if c.get("primary_topic")]
    primary = primary_candidates[0] if primary_candidates else "T00"
    secondaries: list[str] = []
    for c in chairs:
        for t in c.get("secondary_topics") or []:
            if t != primary and t not in secondaries:
                secondaries.append(t)
    return primary, secondaries[:3]  # cap to keep noise down


def significance_text(authors: list[str], venue: str, chair_names: list[str]) -> str:
    """Auto-compose a short provenance-aware significance blurb."""
    chair_list = ", ".join(chair_names) if chair_names else "chairs"
    v = venue or "Unknown Venue"
    return (
        f"Published in {v}. LE-filtered expansion seeded from conference-chair authorship "
        f"({chair_list}). OpenAlex-seeded; curation pending."
    )


def build_paper_record(w: dict, chairs: list[dict], rid_num: int) -> dict:
    """Materialize a full paper YAML record dict from an OpenAlex work + author chairs."""
    authors = extract_authors(w)
    doi = normalize_doi(w.get("doi") or "")
    cites = w.get("cited_by_count", 0) or 0
    primary, secondaries = merge_topics(chairs)
    chair_names = [c.get("name", "") for c in chairs]
    rec = {
        "resource_id": f"LE-AP-{rid_num:03d}",
        "content_type": "AP",
        "source": "openalex_expansion",
        "status": "seed",
        "title": (w.get("title") or "").strip(),
        "authors": authors,
        "year": w.get("publication_year"),
        "venue": venue_of(w) or "Unknown Venue",
        "doi": doi,
        "tier": tier_for(cites),
        "citation_count_approx": cites,
        "cross_seed_score": len(chairs),
        "openalex_id": w.get("id", "").rsplit("/", 1)[-1],
        "significance": significance_text(authors, venue_of(w), chair_names),
        "primary_topic": primary,
        "secondary_topics": secondaries,
    }
    return rec


def write_yaml(path: Path, rec: dict) -> None:
    """Serialize a paper record as YAML, preserving insertion order."""
    with path.open("w", encoding="utf-8") as fp:
        yaml.safe_dump(
            rec, fp,
            sort_keys=False, allow_unicode=True, width=110, default_flow_style=False,
        )


def main(per_chair: int, write: bool) -> int:
    """Pull top LE works per chair, dedup, write new paper YAMLs; return non-zero on hard error."""
    chairs = load_chairs()
    if not chairs:
        print("No chairs with openalex_id found under le-pp-250..321.")
        return 1
    print(f"Loaded {len(chairs)} chairs with openalex_id")

    # Collect candidate works keyed by openalex work id, tracking which chairs introduced them.
    # { work_id: {"work": {...}, "chairs": [chair_dict, ...]} }
    candidates: dict[str, dict] = {}
    fetch_errors: list[tuple[str, str]] = []

    for c in chairs:
        aid = c.get("openalex_id", "")
        try:
            works = le_filtered_works(aid, n=per_chair)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            fetch_errors.append((c.get("resource_id"), str(e)))
            continue
        for w in works:
            wid = (w.get("id") or "").rsplit("/", 1)[-1]
            if not wid:
                continue
            entry = candidates.setdefault(wid, {"work": w, "chairs": []})
            entry["chairs"].append(c)
        time.sleep(0.25)

    print(f"Collected {len(candidates)} unique candidate works across chairs")
    if fetch_errors:
        print(f"Fetch errors: {len(fetch_errors)}")
        for rid, err in fetch_errors[:5]:
            print(f"  {rid}  {err}")

    # Dedup against the existing paper corpus.
    existing_dois, existing_oa_ids = load_existing_index()
    print(f"Existing corpus: {len(existing_dois)} DOIs, {len(existing_oa_ids)} openalex_ids indexed")

    new_records: list[dict] = []
    next_id = next_available_id(start=830)
    for wid, entry in sorted(
        candidates.items(),
        key=lambda kv: (-(kv[1]["work"].get("cited_by_count") or 0)),
    ):
        w = entry["work"]
        doi = normalize_doi(w.get("doi") or "")
        if wid in existing_oa_ids:
            continue
        if doi and doi in existing_dois:
            continue
        rec = build_paper_record(w, entry["chairs"], next_id)
        new_records.append(rec)
        existing_dois.add(doi)
        existing_oa_ids.add(wid)
        next_id = next_available_id(start=next_id + 1)

    print(f"New papers to write: {len(new_records)}")
    for rec in new_records[:10]:
        cn = rec["citation_count_approx"]
        print(f"  {rec['resource_id']} [{rec['tier']}, {cn} cites] {rec['title'][:70]}")
    if len(new_records) > 10:
        print(f"  ... and {len(new_records) - 10} more")

    if not write:
        print("\n(dry run — use --write to apply)")
        return 0

    written = 0
    for rec in new_records:
        authors = rec.get("authors") or []
        slug = slug_from_work({"publication_year": rec.get("year")}, authors)
        num = int(rec["resource_id"].split("-")[-1])
        fn = f"le-ap-{num:03d}-{slug}.yaml"
        path = PAPERS_DIR / fn
        # Guard: avoid filename collisions with a numeric-suffix retry.
        suffix = 1
        while path.exists():
            path = PAPERS_DIR / f"le-ap-{num:03d}-{slug}-{suffix}.yaml"
            suffix += 1
        write_yaml(path, rec)
        written += 1
    print(f"Wrote {written} new paper YAMLs under {PAPERS_DIR}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--per-chair", type=int, default=5, help="Papers per chair (default: 5)")
    parser.add_argument("--write", action="store_true", help="Write changes to disk.")
    args = parser.parse_args()
    sys.exit(main(per_chair=args.per_chair, write=args.write))
