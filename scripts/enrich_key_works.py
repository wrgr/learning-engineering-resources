"""Top up key_works on landscape people via OpenAlex, biased toward LE work.

For every file under landscape/resources/people/ whose `key_works` list has
fewer than three entries, fetches the person's top works from OpenAlex and
appends up to five entries per person.

Picking strategy:
  1. Use `openalex_id` on the record if already set.
  2. Else search by name, prefer candidates whose institution matches the
     record's `affiliation` and whose topics are education-related.
  3. Pull the author's top 50 works by cited_by_count, then re-rank by
     (LE-keyword hit) * 10 + log10(cites + 1). This biases selection toward
     LE-relevant work even when the person's single most-cited paper is
     from a different field.
  4. Reject any work whose venue string contains clearly non-LE markers
     (entomology, neurology, sports, etc.). These are almost always a
     same-name, different-person mismatch.

Existing key_works are preserved; duplicates are removed by comparing the
title portion only (venue-abbreviation variants are treated as matches).

Requires PyYAML (see scripts/requirements.txt) and network access to OpenAlex.
`OPENALEX_MAILTO` must be set in the environment or .env.

Usage:
    python3 scripts/enrich_key_works.py            # dry run
    python3 scripts/enrich_key_works.py --write    # apply
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


def _load_env_file(path: Path) -> None:
    """Populate os.environ from a KEY=VALUE .env file; shell env wins."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


_load_env_file(REPO_ROOT / ".env")
MAIL = os.environ.get("OPENALEX_MAILTO", "")
KEY = os.environ.get("OPENALEX_API_KEY", "")

EDUCATION_KEYWORDS = (
    "education", "learning", "cognitive", "psycholog", "instruction",
    "tutoring", "pedagog", "training", "e-learning", "edtech",
    "analytics", "tutor", "mooc", "classroom", "student", "teacher",
    "curriculum", "assessment",
)

LE_KEYWORDS = (
    "learning engineer", "learning scienc", "learning analytics", "educational data",
    "instructional design", "intelligent tutor", "cognitive tutor", "adaptive learning",
    "personalized learning", "educational technology", "cognitive load",
    "scaffolding", "problem-based learning", "case-based", "knowledge tracing",
    "learner model", "open learn", "mooc", "online learn", "classroom",
    "competency", "bloom", "metacognit", "self-regulated",
)

# Venues that flag a same-name mismatch when they appear on a candidate work.
NON_LE_VENUE_MARKERS = (
    "entomology", "neurology", "oncology", "cardiolog", "biochem",
    "pharmacol", "surgery", "rugby", "oxygen uptake", "biosciences",
    "planar energy", "alzheimer", "parkinson", "brain injury",
    "sports medicine", "sports science", "treadmill",
)


def oa_get(path: str) -> dict:
    """GET OpenAlex with mailto + api_key; return parsed JSON."""
    if not MAIL:
        raise RuntimeError("OPENALEX_MAILTO is not set. Export it or put it in .env.")
    sep = "&" if "?" in path else "?"
    url = f"https://api.openalex.org{path}{sep}mailto={MAIL}"
    if KEY:
        url += f"&api_key={KEY}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def _topic_text(a: dict) -> str:
    """Concatenate all topic/concept display names for an author into lowercase text."""
    parts: list[str] = []
    for t in (a.get("topics") or [])[:10]:
        parts.append(t.get("display_name", ""))
    for c in (a.get("x_concepts") or [])[:10]:
        parts.append(c.get("display_name", ""))
    return " ".join(parts).lower()


def pick_author(results: list[dict], affiliation: str) -> dict | None:
    """Rank OpenAlex author candidates by (affiliation-match + edu-profile + cites)."""
    if not results:
        return None
    aff_l = (affiliation or "").lower()

    def score(a: dict) -> tuple[int, int]:
        inst = " ".join(
            i.get("display_name", "") for i in (a.get("last_known_institutions") or [])
        ).lower()
        topics = _topic_text(a)
        aff_hit = 1 if (aff_l and aff_l in inst) else 0
        edu_hit = 1 if any(k in topics for k in EDUCATION_KEYWORDS) else 0
        return (aff_hit + edu_hit, a.get("cited_by_count", 0))

    return sorted(results, key=score, reverse=True)[0]


def resolve_author(name: str, affiliation: str, openalex_id: str) -> dict | None:
    """Return an OpenAlex author record for a person, or None if nothing found."""
    if openalex_id:
        aid = openalex_id.rsplit("/", 1)[-1]
        try:
            return oa_get(f"/authors/{aid}")
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            pass
    q = urllib.parse.quote(name)
    data = oa_get(f"/authors?search={q}&per_page=15")
    return pick_author(data.get("results", []), affiliation)


def le_relevant_works(author_id: str, n: int = 5, pool_size: int = 50) -> list[dict]:
    """Return up to n works biased toward LE relevance.

    Scores each candidate work by (LE-keyword hits * 10) + log10(cites + 1),
    so a moderately cited LE paper beats a heavily cited off-topic paper.
    Entries with non-LE venue markers are rejected outright.
    """
    aid = author_id.rsplit("/", 1)[-1]
    data = oa_get(
        f"/works?filter=author.id:{aid}&sort=cited_by_count:desc&per_page={pool_size}"
    )
    pool = data.get("results", []) or []

    def venue_of(w: dict) -> str:
        return ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "") or ""

    def is_non_le_venue(w: dict) -> bool:
        v = venue_of(w).lower()
        return any(m in v for m in NON_LE_VENUE_MARKERS)

    # Drop works whose venue is obviously non-LE — almost always a wrong-person match.
    pool = [w for w in pool if not is_non_le_venue(w)]

    def le_score(w: dict) -> float:
        title = (w.get("title") or "").lower()
        haystack = f"{title} {venue_of(w).lower()}"
        hits = sum(1 for k in LE_KEYWORDS if k in haystack)
        cites = w.get("cited_by_count", 0) or 0
        return hits * 10 + math.log10(cites + 1)

    ranked = sorted(pool, key=le_score, reverse=True)
    le_ranked = [w for w in ranked if any(
        k in (w.get("title") or "").lower() for k in LE_KEYWORDS
    )]
    return (le_ranked or ranked)[:n]


def format_citation(w: dict) -> str:
    """Render 'Title (Venue, Year)' from an OpenAlex work."""
    title = (w.get("title") or "Untitled").strip().rstrip(".")
    year = w.get("publication_year") or "n.d."
    venue = (w.get("primary_location") or {}).get("source") or {}
    name = venue.get("display_name") or ""
    return f"{title} ({name}, {year})" if name else f"{title} ({year})"


def norm_title_only(citation: str) -> str:
    """Strip any trailing ' (Venue, Year)' suffix from a citation, return a normalised title.

    Used for dedup so that 'Design Experiments... (JLS, 1992)' and
    'Design Experiments... (Journal of the Learning Sciences, 1992)' compare equal.
    """
    bare = re.sub(r"\s*\([^()]+\)\s*$", "", citation).strip()
    return re.sub(r"[^a-z0-9]+", " ", bare.lower()).strip()


def main(write: bool) -> int:
    """Enrich every person yaml whose key_works has fewer than three entries."""
    enriched: list[tuple[str, str, int]] = []
    skipped: list[tuple[str, str, str]] = []

    for yf in sorted(PEOPLE_DIR.glob("*.yaml")):
        rec = yaml.safe_load(yf.read_text(encoding="utf-8")) or {}
        existing = rec.get("key_works") or []
        if not isinstance(existing, list):
            existing = []
        if len(existing) >= 3:
            continue
        name = rec.get("name") or ""
        if not name:
            continue
        rid = rec.get("resource_id", yf.stem)
        try:
            author = resolve_author(
                name,
                rec.get("affiliation", "") or "",
                rec.get("openalex_id", "") or "",
            )
            if not author:
                skipped.append((rid, name, "no OpenAlex match"))
                continue
            works = le_relevant_works(author["id"], n=8, pool_size=50)
            if not works:
                skipped.append((rid, name, "OpenAlex returned 0 eligible works"))
                continue
            blob = " ".join((w.get("title") or "") for w in works).lower()
            if not any(k in blob for k in EDUCATION_KEYWORDS + LE_KEYWORDS):
                skipped.append((rid, name, "no LE-relevant works in top 50"))
                continue
            existing_titles = {norm_title_only(x) for x in existing}
            additions: list[str] = []
            for w in works:
                cite = format_citation(w)
                if norm_title_only(cite) in existing_titles:
                    continue
                additions.append(cite)
                existing_titles.add(norm_title_only(cite))
                if len(existing) + len(additions) >= 5:
                    break
            if not additions:
                continue
            rec["key_works"] = list(existing) + additions
            if not rec.get("openalex_id"):
                rec["openalex_id"] = author.get("id", "")
            enriched.append((rid, name, len(rec["key_works"])))
            if write:
                with yf.open("w", encoding="utf-8") as fp:
                    yaml.safe_dump(
                        rec, fp,
                        sort_keys=False, allow_unicode=True, width=110, default_flow_style=False,
                    )
            time.sleep(0.25)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            skipped.append((rid, name, f"error: {e}"))

    print(f"Enriched: {len(enriched)}")
    for rid, name, n in enriched:
        print(f"  {rid}  {name:<28}  now has {n} key_works")
    if skipped:
        print(f"\nSkipped ({len(skipped)}):")
        for rid, name, reason in skipped:
            print(f"  {rid}  {name:<28}  {reason}")
    if not write:
        print("\n(dry run — use --write to apply)")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="Write changes to disk.")
    args = parser.parse_args()
    sys.exit(main(write=args.write))
