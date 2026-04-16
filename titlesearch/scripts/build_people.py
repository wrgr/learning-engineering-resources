"""Ingest raw source records (GitHub, RG, GS, LinkedIn, manual) and normalize them into people.json."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data"
PEOPLE_FILE = DATA_DIR / "people.json"

# Canonical source codes → provenance.source strings
SOURCE_MAP: dict[str, str] = {
    "GH": "github_search",
    "RG": "researchgate",
    "GS": "google_scholar",
    "LI": "linkedin",
    "WS": "web_search",
    "TW": "twitter",
}

# ── ID generation ─────────────────────────────────────────────────────────────

def _next_person_id(existing: list[dict]) -> str:
    """Return the next sequential person ID (LE-P-NNN)."""
    nums = [
        int(r["person_id"].split("-")[-1])
        for r in existing
        if r.get("person_id", "").startswith("LE-P-")
    ]
    n = max(nums, default=0) + 1
    return f"LE-P-{n:03d}"


# ── Name splitting ─────────────────────────────────────────────────────────────

def _split_name(display_name: str) -> tuple[str, str]:
    """Best-effort split of a display name into (first, last).

    Returns ('', '') for single-token or empty names rather than guessing.
    """
    parts = display_name.strip().split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    return ("", display_name.strip()) if parts else ("", "")


# ── Auto-triage (placeholder — replace with real logic) ───────────────────────

def auto_triage_gh(bio: str, login: str) -> tuple[str, str]:
    """Classify a GitHub profile as APPROVED / CANDIDATE / NEEDS_REVIEW.

    Args:
        bio: Profile bio text.
        login: GitHub username.

    Returns:
        Tuple of (triage_label, reason_string).
    """
    keywords = [
        "learning engineering", "learning science", "education", "edtech",
        "instructional design", "cognitive", "curriculum", "assessment",
    ]
    bio_lower = bio.lower()
    matched = [kw for kw in keywords if kw in bio_lower]
    if matched:
        return "CANDIDATE", f"bio contains: {', '.join(matched)}"
    return "NEEDS_REVIEW", "no domain keywords found in bio"


# ── GitHub record normalizer ───────────────────────────────────────────────────

def normalize_github_record(
    rec: dict[str, Any],
    *,
    query: str = "",
    retrieved_date: str | None = None,
) -> dict[str, Any]:
    """Convert a raw GitHub API user record to the people schema.

    Args:
        rec: Raw record dict from GitHub search or user API.
        query: The search query that surfaced this record (for provenance).
        retrieved_date: ISO date of retrieval; defaults to today.

    Returns:
        Normalized people record (not yet assigned a person_id).
    """
    retrieved_date = retrieved_date or date.today().isoformat()

    login: str = rec.get("login", "")
    display_name: str = (rec.get("name") or login).strip()
    bio: str = (rec.get("bio") or "").strip()
    org: str = re.sub(r"^@", "", (rec.get("company") or "").strip())
    location: str = (rec.get("location") or "").strip()
    profile_url: str = rec.get("profile_url", rec.get("html_url", ""))
    email: str = (rec.get("email") or "").strip()

    triage, triage_reason = auto_triage_gh(bio, login)
    first_name, last_name = _split_name(display_name)

    return {
        "person_id": "",  # assigned by upsert_record
        "first_name": first_name,
        "last_name": last_name,
        "display_name": display_name,
        "github_login": login,
        "bio": bio,
        "job_title": "",
        "organization": org,
        "department": "",
        "career_stage": "unknown",
        "email": email,
        "github_url": profile_url,
        "linkedin_url": "",
        "website_url": (rec.get("blog") or "").strip(),
        "orcid": "",
        "location": location,
        "city": "",
        "state_region": "",
        "country": "",
        "primary_topic": "",
        "secondary_topics": [],
        "keywords": [],
        "triage": triage,
        "triage_reason": triage_reason,
        "status": "CANDIDATE",
        "provenance": {
            "source": "github_search",
            "query": query,
            "source_url": profile_url,
            "retrieved_date": retrieved_date,
            "notes": "",
        },
        "last_updated": retrieved_date,
    }


# ── JSONL record normalizer (RG, GS, LinkedIn, manual) ───────────────────────

_TRIAGE_MAP = {"yes": "APPROVED", "probable": "CANDIDATE", "no": "REJECTED"}
_STATUS_MAP = {"yes": "APPROVED", "probable": "CANDIDATE", "no": "ARCHIVED"}


def normalize_jsonl_record(
    rec: dict[str, Any],
    *,
    retrieved_date: str | None = None,
) -> dict[str, Any]:
    """Convert a raw JSONL search record (RG, GS, LI, manual) to the people schema.

    Expects a record with at minimum ``query_id``, ``source``, and ``raw``.
    The ``raw`` sub-dict should contain ``name`` and any source-specific fields.

    Args:
        rec: Raw record as read from a QXXX_*.jsonl file.
        retrieved_date: ISO date of retrieval; defaults to today.

    Returns:
        Normalized people record (not yet assigned a person_id).
    """
    retrieved_date = retrieved_date or date.today().isoformat()
    raw: dict[str, Any] = rec.get("raw", {})

    display_name: str = (raw.get("name") or "").strip()
    first_name, last_name = _split_name(display_name)

    # Title precedence: explicit title field > snippet fallback
    job_title: str = (
        raw.get("rg_title") or raw.get("gs_title") or raw.get("li_title") or ""
    ).strip()

    source_code: str = rec.get("source", "")
    source: str = SOURCE_MAP.get(source_code, source_code.lower())

    # Best-effort profile URL across sources
    profile_url: str = (
        raw.get("rg_url")
        or raw.get("gs_url")
        or raw.get("li_url")
        or raw.get("profile_url")
        or ""
    )

    csv_triage: str = rec.get("triage", "")
    triage = _TRIAGE_MAP.get(csv_triage, "NEEDS_REVIEW")
    status = _STATUS_MAP.get(csv_triage, "CANDIDATE")

    notes_parts = [n for n in [raw.get("note", ""), rec.get("notes", "")] if n]
    notes = "; ".join(notes_parts)

    return {
        "person_id": "",
        "first_name": first_name,
        "last_name": last_name,
        "display_name": display_name,
        "github_login": "",
        "bio": (raw.get("bio") or raw.get("snippet") or "").strip(),
        "job_title": job_title,
        "organization": (raw.get("affiliation") or raw.get("organization") or "").strip(),
        "department": "",
        "career_stage": "unknown",
        "email": (raw.get("email") or "").strip(),
        "github_url": "",
        "linkedin_url": profile_url if source_code == "LI" else "",
        "website_url": "",
        "orcid": "",
        "location": (raw.get("location") or "").strip(),
        "city": "",
        "state_region": "",
        "country": "",
        "primary_topic": "",
        "secondary_topics": [],
        "keywords": [],
        "triage": triage,
        "triage_reason": rec.get("triage_reason", ""),
        "status": status,
        "provenance": {
            "source": source,
            "query": rec.get("query_id", ""),
            "source_url": profile_url if source_code != "LI" else "",
            "retrieved_date": retrieved_date,
            "notes": notes,
        },
        "last_updated": retrieved_date,
    }


# ── LinkedIn PhantomBuster record normalizer ──────────────────────────────────

# Patterns that indicate "learning engineer" is used in a non-educational sense.
# Covers ML/DL/RL subdisciplines and "continuously/fast/quick-learning" adjective phrases.
_FALSE_POSITIVE_PATTERNS = re.compile(
    r"\b("
    # ML/AI subdisciplines
    r"machine[- ]learning"
    r"|machile[- ]learning"          # common typo
    r"|deep[- ]learning"
    r"|reinforcement[- ]learning"
    r"|transfer[- ]learning"
    r"|federated[- ]learning"
    r"|representation[- ]learning"
    r"|contrastive[- ]learning"
    r"|self[- ]supervised[- ]learning"
    r"|unsupervised[- ]learning"
    r"|supervised[- ]learning"
    r"|\bML\b\s+engineer"
    r"|NLP\s+engineer"
    r"|computer\s+vision\s+engineer"
    r"|MLOps"
    # Robotics / embedded
    r"|robotics\s+learning"
    r"|aspiring\s+\w*\s*machine"
    # Continuous-learner adjective phrases
    r"|fast[- ]learning"
    r"|quick[- ]learning"
    r"|ever[- ]learning"
    r"|keep[- ]learning"
    r"|continuously[- ]learning"
    r"|continuous[- ]learning\s+engineer"
    r")\b",
    re.IGNORECASE,
)


def normalize_linkedin_pb_record(
    *,
    display_name: str,
    headline: str,
    location: str,
    company: str,
    job_title: str,
    industry: str,
    lists: list[str],
    triage_override: str | None = None,
    retrieved_date: str | None = None,
) -> dict[str, Any]:
    """Convert a PhantomBuster LinkedIn row to the people schema.

    Args:
        display_name: Full name as shown on LinkedIn.
        headline: LinkedIn profile headline (used as bio).
        location: Freetext location string.
        company: Company/organization name.
        job_title: Most recent job title from LinkedIn.
        industry: Company industry from LinkedIn.
        lists: PhantomBuster list names the record appeared in.
        triage_override: Force a specific triage value; None = auto-detect.
        retrieved_date: ISO date; defaults to today.

    Returns:
        Normalized people record (person_id assigned later by upsert_record).
    """
    retrieved_date = retrieved_date or date.today().isoformat()
    first_name, last_name = _split_name(display_name)
    org = re.sub(r"^@", "", (company or "").strip())

    if triage_override:
        triage = triage_override
        triage_reason = "manual override"
    elif _FALSE_POSITIVE_PATTERNS.search(headline):
        triage = "NEEDS_REVIEW"
        triage_reason = "headline pattern suggests non-educational use of 'engineer'"
    else:
        triage = "CANDIDATE"
        triage_reason = "headline contains learning engineer variant"

    return {
        "person_id": "",
        "first_name": first_name,
        "last_name": last_name,
        "display_name": display_name,
        "github_login": "",
        "bio": headline.strip(),
        "job_title": job_title.strip(),
        "organization": org,
        "department": "",
        "career_stage": "unknown",
        "email": "",
        "github_url": "",
        "linkedin_url": "",
        "website_url": "",
        "orcid": "",
        "location": location.strip(),
        "city": "",
        "state_region": "",
        "country": "",
        "primary_topic": "",
        "secondary_topics": [],
        "keywords": [industry] if industry and industry != "-" else [],
        "triage": triage,
        "triage_reason": triage_reason,
        "status": "CANDIDATE",
        "provenance": {
            "source": "linkedin_phantombuster",
            "query": "learning engineer (title/keyword search)",
            "source_url": "",
            "retrieved_date": retrieved_date,
            "notes": f"lists: {', '.join(lists)}",
        },
        "last_updated": retrieved_date,
    }


# ── Registry upsert ────────────────────────────────────────────────────────────

def upsert_record(record: dict[str, Any], existing: list[dict]) -> list[dict]:
    """Insert or update a record in the registry.

    Dedup key priority:
    1. github_login (when present) — unique across GH records
    2. display_name (case-insensitive) — fallback for RG/GS/LI records

    When an existing record is matched, person_id and status are preserved.

    Args:
        record: Normalized people record (person_id may be empty string).
        existing: Current list of records from people.json.

    Returns:
        Updated list with the record inserted or merged.
    """
    login = record.get("github_login", "")
    display = record.get("display_name", "").lower()

    for i, r in enumerate(existing):
        matched = (login and r.get("github_login") == login) or (
            not login
            and display
            and r.get("display_name", "").lower() == display
        )
        if matched:
            record["person_id"] = r["person_id"]
            record["status"] = r.get("status", record["status"])
            existing[i] = record
            return existing

    record["person_id"] = _next_person_id(existing)
    existing.append(record)
    return existing


def load_people() -> list[dict]:
    """Load the people registry from disk."""
    if PEOPLE_FILE.exists():
        return json.loads(PEOPLE_FILE.read_text())
    return []


def save_people(records: list[dict]) -> None:
    """Write the people registry to disk, sorted by person_id."""
    records_sorted = sorted(records, key=lambda r: r.get("person_id", ""))
    PEOPLE_FILE.write_text(json.dumps(records_sorted, indent=2))


# ── CLI entry point ────────────────────────────────────────────────────────────

def ingest_github_file(path: str, query: str = "") -> None:
    """Ingest a JSON file of raw GitHub user records into people.json.

    Args:
        path: Path to a JSON file containing a list of GitHub user records.
        query: The search query used to obtain the records.
    """
    raw: list[dict] = json.loads(Path(path).read_text())
    people = load_people()
    for rec in raw:
        normalized = normalize_github_record(rec, query=query)
        people = upsert_record(normalized, people)
    save_people(people)
    print(f"Ingested {len(raw)} records. Registry now has {len(people)} people.")


def ingest_jsonl_file(path: str) -> None:
    """Ingest a JSONL file of raw RG/GS/LI/manual records into people.json.

    Each line must be a JSON object with at minimum ``query_id``, ``source``,
    and ``raw``. Records with ``triage: SKIP`` are skipped silently.

    Args:
        path: Path to a QXXX_*.jsonl file in titlesearch/data/raw/.
    """
    lines = Path(path).read_text().splitlines()
    people = load_people()
    ingested = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("triage") == "SKIP" or not rec.get("raw", {}).get("name"):
            continue
        normalized = normalize_jsonl_record(rec)
        people = upsert_record(normalized, people)
        ingested += 1
    save_people(people)
    print(f"Ingested {ingested} records. Registry now has {len(people)} people.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python build_people.py github <raw_records.json> [query]")
        print("       python build_people.py jsonl  <QXXX_*.jsonl>")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "github":
        ingest_github_file(sys.argv[2], query=sys.argv[3] if len(sys.argv) > 3 else "")
    elif mode == "jsonl":
        ingest_jsonl_file(sys.argv[2])
    else:
        print(f"Unknown mode '{mode}'. Use 'github' or 'jsonl'.")
        sys.exit(1)
