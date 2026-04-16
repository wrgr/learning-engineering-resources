"""Query the people registry by name, organization, topic, location, or triage status."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data"
PEOPLE_FILE = DATA_DIR / "people.json"


def load_people() -> list[dict]:
    """Load the people registry from disk."""
    if PEOPLE_FILE.exists():
        return json.loads(PEOPLE_FILE.read_text())
    return []


def _matches(record: dict[str, Any], filters: dict[str, str]) -> bool:
    """Return True if all filters match the record (case-insensitive substring).

    Args:
        record: A people record dict.
        filters: Mapping of field name to search string.
    """
    for field, term in filters.items():
        value = record.get(field, "")
        if isinstance(value, list):
            value = " ".join(value)
        if term.lower() not in str(value).lower():
            return False
    return True


def search(
    *,
    name: str = "",
    organization: str = "",
    job_title: str = "",
    location: str = "",
    primary_topic: str = "",
    triage: str = "",
    status: str = "",
) -> list[dict]:
    """Return records matching all supplied filters (empty string = wildcard).

    Args:
        name: Substring match against display_name.
        organization: Substring match against organization.
        job_title: Substring match against job_title.
        location: Substring match against location.
        primary_topic: Exact or substring match against primary_topic.
        triage: Exact match against triage field (e.g. 'APPROVED').
        status: Exact match against status field (e.g. 'CANDIDATE').

    Returns:
        List of matching people records, sorted by last_name then first_name.
    """
    filters: dict[str, str] = {}
    if name:
        filters["display_name"] = name
    if organization:
        filters["organization"] = organization
    if job_title:
        filters["job_title"] = job_title
    if location:
        filters["location"] = location
    if primary_topic:
        filters["primary_topic"] = primary_topic
    if triage:
        filters["triage"] = triage
    if status:
        filters["status"] = status

    people = load_people()
    results = [r for r in people if _matches(r, filters)]
    return sorted(results, key=lambda r: (r.get("last_name", ""), r.get("first_name", "")))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Search the people registry.")
    parser.add_argument("--name", default="")
    parser.add_argument("--organization", default="")
    parser.add_argument("--job-title", default="")
    parser.add_argument("--location", default="")
    parser.add_argument("--topic", default="")
    parser.add_argument("--triage", default="")
    parser.add_argument("--status", default="")
    args = parser.parse_args()

    results = search(
        name=args.name,
        organization=args.organization,
        job_title=args.job_title,
        location=args.location,
        primary_topic=args.topic,
        triage=args.triage,
        status=args.status,
    )
    print(json.dumps(results, indent=2))
    print(f"\n{len(results)} result(s)")
