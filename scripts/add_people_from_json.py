"""Create landscape person YAMLs from a JSON list of contributor specs.

Takes a JSON file whose top-level is an array of objects like:

    [
      {
        "name": "Janet Kolodner",
        "affiliation_hint": "Boston College",
        "topic_hints": ["learning", "cognitive"],
        "role": "Co-editor, Learning Engineering Toolkit; case-based reasoning pioneer.",
        "source": "Goodell & Kolodner (2022) — editor."
      },
      ...
    ]

For each entry, resolves the person on OpenAlex (preferring authors whose
institution matches `affiliation_hint` and whose topics match `topic_hints`),
writes a YAML file to landscape/resources/people/, and assigns the next free
LE-PP-NNN id. Existing people (by name match) are skipped.

`key_works` is populated in the same pass when the picked author has
education-related top works; otherwise the field is left empty with a
`notes:` line so the curator can fill it in (or run enrich_key_works.py).

Example inputs live under scripts/data/:
    scripts/data/goodell_book_contributors.json

Requires PyYAML (see scripts/requirements.txt) and network access to OpenAlex.
`OPENALEX_MAILTO` must be set in the environment or .env.

Usage:
    python3 scripts/add_people_from_json.py scripts/data/goodell_book_contributors.json
    python3 scripts/add_people_from_json.py ... --write
"""

from __future__ import annotations

import argparse
import json
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
)


def oa_get(path: str) -> dict:
    """GET OpenAlex with mailto + api_key; return parsed JSON."""
    if not MAIL:
        raise RuntimeError("OPENALEX_MAILTO is not set.")
    sep = "&" if "?" in path else "?"
    url = f"https://api.openalex.org{path}{sep}mailto={MAIL}"
    if KEY:
        url += f"&api_key={KEY}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def _topic_text(a: dict) -> str:
    """Concatenate an author's topic/concept names into lowercase text."""
    parts: list[str] = []
    for t in (a.get("topics") or [])[:10]:
        parts.append(t.get("display_name", ""))
    for c in (a.get("x_concepts") or [])[:10]:
        parts.append(c.get("display_name", ""))
    return " ".join(parts).lower()


def is_in_education(author: dict) -> bool:
    """True if any topic/concept name is education-related."""
    txt = _topic_text(author)
    return any(k in txt for k in EDUCATION_KEYWORDS)


def pick_author(results: list[dict], affiliation_hint: str, topic_hints: list[str]) -> dict | None:
    """Rank candidates by (aff_hit + topic_hit + edu_hit), tie-break by cites."""
    if not results:
        return None

    def score(a: dict) -> tuple[int, int]:
        inst = " ".join(
            i.get("display_name", "") for i in (a.get("last_known_institutions") or [])
        ).lower()
        topics = _topic_text(a)
        aff_hit = 1 if (affiliation_hint and affiliation_hint.lower() in inst) else 0
        topic_hit = 1 if any(h.lower() in topics for h in topic_hints) else 0
        edu_hit = 1 if is_in_education(a) else 0
        return (aff_hit + topic_hit + edu_hit, a.get("cited_by_count", 0))

    return sorted(results, key=score, reverse=True)[0]


def top_works(author_id: str, n: int = 5) -> list[dict]:
    """Return up to n most-cited works for the author."""
    aid = author_id.rsplit("/", 1)[-1]
    data = oa_get(
        f"/works?filter=author.id:{aid}&sort=cited_by_count:desc&per_page={n}"
    )
    return data.get("results", []) or []


def format_citation(w: dict) -> str:
    """Render a single OpenAlex work as 'Title (Venue, Year)'."""
    title = (w.get("title") or "Untitled").strip().rstrip(".")
    year = w.get("publication_year") or "n.d."
    venue = (w.get("primary_location") or {}).get("source") or {}
    name = venue.get("display_name") or ""
    return f"{title} ({name}, {year})" if name else f"{title} ({year})"


def slugify_lastname(name: str) -> str:
    """Filesystem slug from the surname — matches existing le-pp-NNN-LAST.yaml convention."""
    last = name.rsplit(" ", 1)[-1]
    return re.sub(r"[^a-z0-9]+", "-", last.lower()).strip("-") or "person"


def load_existing() -> tuple[set[str], set[str]]:
    """Return (names lowercased, existing LE-PP-* ids) already on disk."""
    names: set[str] = set()
    ids: set[str] = set()
    for f in PEOPLE_DIR.glob("*.yaml"):
        rec = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if rec.get("name"):
            names.add(rec["name"].lower())
        if rec.get("resource_id"):
            ids.add(rec["resource_id"])
    return names, ids


def next_person_id(existing_ids: set[str], start: int = 210) -> int:
    """Pick next free LE-PP-NNN, starting from `start` to avoid low-number collisions."""
    n = start
    while f"LE-PP-{n:03d}" in existing_ids:
        n += 1
    return n


def build_record(spec: dict, author: dict | None, rid: str) -> dict:
    """Assemble a person YAML record from a spec + optional OpenAlex author."""
    name = spec["name"]
    role = spec.get("role") or ""
    source = spec.get("source") or ""
    topic_hints = spec.get("topic_hints") or []
    aff_hint = spec.get("affiliation_hint") or ""

    picked_inst = ""
    if author:
        picked_inst = " ".join(
            i.get("display_name", "") for i in (author.get("last_known_institutions") or [])
        ).lower()
    aff_ok = bool(aff_hint) and aff_hint.lower() in picked_inst
    topics_blob = _topic_text(author) if author else ""
    topic_ok = any(h.lower() in topics_blob for h in topic_hints)
    confident = bool(author and (aff_ok or topic_ok or is_in_education(author)))

    key_works: list[str] = []
    inst = aff_hint
    oa_id = ""
    note = source.strip()
    if confident:
        works = top_works(author["id"], n=5)
        blob = " ".join((w.get("title") or "") for w in works).lower()
        if works and any(k in blob for k in EDUCATION_KEYWORDS):
            key_works = [format_citation(w) for w in works]
            inst = (author.get("last_known_institutions") or [{}])[0].get("display_name", "") or aff_hint
            oa_id = author.get("id", "")
            note = (note + f" Affiliation and top works auto-populated from OpenAlex author {oa_id}; verify on review.").strip()
        else:
            note = (note + " OpenAlex pick had no education-related top works — populate key_works manually.").strip()
    elif author:
        note = (note + " OpenAlex disambiguation was inconclusive — populate key_works manually.").strip()
    else:
        note = (note + " No OpenAlex match found.").strip()

    return {
        "resource_id": rid,
        "content_type": "PP",
        "source": "json_batch_add",
        "status": "APPROVED",
        "name": name,
        "affiliation": inst,
        "era": "contemporary",
        "role": role,
        "description": f"{role}".strip() or name,
        "key_works": key_works,
        "primary_topic": "T00",
        "secondary_topics": [],
        "url": oa_id,
        "openalex_id": oa_id,
        "notes": note,
    }


def main(input_path: Path, write: bool, start_id: int) -> int:
    """Create YAML records for each contributor spec in the JSON input."""
    specs = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(specs, list):
        print("Input JSON must be an array of contributor specs.", file=sys.stderr)
        return 2

    existing_names, existing_ids = load_existing()
    next_n = next_person_id(existing_ids, start=start_id)
    created = 0
    skipped = 0

    for spec in specs:
        name = spec.get("name", "").strip()
        if not name:
            continue
        if name.lower() in existing_names:
            print(f"  SKIP  {name}  (already present)")
            skipped += 1
            continue
        try:
            data = oa_get(f"/authors?search={urllib.parse.quote(name)}&per_page=15")
            author = pick_author(
                data.get("results", []),
                spec.get("affiliation_hint") or "",
                spec.get("topic_hints") or [],
            )
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            print(f"  ERROR {name}: {e}")
            continue

        rid = f"LE-PP-{next_n:03d}"
        next_n += 1
        rec = build_record(spec, author, rid)
        out = PEOPLE_DIR / f"le-pp-{int(rid.split('-')[-1]):03d}-{slugify_lastname(name)}.yaml"
        status = "OK" if rec["key_works"] else "NEEDS REVIEW"
        print(f"  +     {rid}  {name:<28}  [{status}]  ({len(rec['key_works'])} works)")
        if write:
            with out.open("w", encoding="utf-8") as fp:
                yaml.safe_dump(
                    rec, fp,
                    sort_keys=False, allow_unicode=True, width=110, default_flow_style=False,
                )
        created += 1
        time.sleep(0.25)

    print(f"\nCreated: {created}  Skipped: {skipped}")
    if not write:
        print("(dry run — use --write to apply)")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", type=Path, help="Path to JSON file with contributor specs.")
    parser.add_argument("--write", action="store_true", help="Write YAML files to disk.")
    parser.add_argument("--start-id", type=int, default=210,
                        help="Starting LE-PP-NNN suffix when assigning new ids.")
    args = parser.parse_args()
    sys.exit(main(args.input, args.write, args.start_id))
