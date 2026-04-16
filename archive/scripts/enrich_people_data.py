#!/usr/bin/env python3
"""Enrich titlesearch/data/people.json with LE title assessment and fill attribute gaps.

Adds le_title_assessment ('yes'/'maybe'/'no') and le_assessment_reason to each record.
Fills empty city/state_region/country from the location string where parseable.
Fills career_stage where currently 'unknown' and inferable from job_title/bio.
Never overwrites existing non-empty field values.
"""

import json
import re
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "titlesearch" / "data" / "people.json"

US_STATES: dict[str, str] = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
}

COUNTRY_MAP: dict[str, str] = {
    "United States": "US", "United Kingdom": "GB", "England": "GB",
    "Scotland": "GB", "Wales": "GB", "Germany": "DE", "France": "FR",
    "India": "IN", "Jordan": "JO", "Morocco": "MA", "Egypt": "EG",
    "Spain": "ES", "Turkey": "TR", "Türkiye": "TR", "Indonesia": "ID",
    "Philippines": "PH", "Malaysia": "MY", "Australia": "AU", "Canada": "CA",
    "Pakistan": "PK", "China": "CN", "Belgium": "BE", "Rwanda": "RW",
    "Kenya": "KE", "Tanzania": "TZ", "South Africa": "ZA", "Vietnam": "VN",
    "Serbia": "RS", "Argentina": "AR", "Colombia": "CO", "Kuwait": "KW",
    "Armenia": "AM", "Greece": "GR", "United Arab Emirates": "AE",
    "Netherlands": "NL", "Poland": "PL", "Switzerland": "CH", "Portugal": "PT",
    "Italy": "IT", "Sweden": "SE", "Denmark": "DK", "Norway": "NO",
    "Finland": "FI", "Brazil": "BR", "Mexico": "MX", "Israel": "IL",
    "Japan": "JP", "South Korea": "KR", "Singapore": "SG", "Nigeria": "NG",
    "Ghana": "GH", "Ethiopia": "ET", "Estonia": "EE",
}

# Unambiguously US metro areas (excludes Brisbane, Lille, Hyderabad, Rosario, etc.)
US_METRO_LOWER: set[str] = {
    "greater boston", "greater philadelphia", "greater chicago",
    "new york city metropolitan", "washington dc", "san francisco bay",
    "greater tampa bay", "greater pittsburgh", "greater st. louis",
    "salt lake city", "louisville metropolitan", "raleigh-durham",
    "crestview-fort walton", "spokane-coeur", "greater indianapolis",
    "greater denver", "greater atlanta", "greater houston", "greater dallas",
    "greater miami", "greater minneapolis", "greater detroit",
    "greater portland", "greater austin", "greater new york",
    "greater seattle", "greater los angeles", "greater nashville",
    "greater orlando", "greater richmond",
    "los angeles metropolitan",
}

# Metro areas whose location-string alone is enough to pin country (non-US cases)
METRO_COUNTRY_MAP: dict[str, str] = {
    "greater hyderabad": "IN",
    "greater rosario": "AR",
    "frankfurt rhine-main": "DE",
    "athens metropolitan": "GR",
    "bogotá": "CO",
    "bogota": "CO",
    "greater lille": "FR",
    "tallinn": "EE",
    "greater brisbane": "AU",
    "greater paris": "FR",
    "paris metropolitan": "FR",
}

# Machine-learning / robotics patterns that are NOT education-LE titles
ML_RE = re.compile(
    r"(?i)\b(machine\s+learning\s+engineer|ml\s+engineer|deep\s+learning\s+engineer|"
    r"machin\s+learning|mechine\s+learning|meaching\s+learning|machile\s+learning|"
    r"robotics?\s+learning\s+engineer|robot\s+learning\s+engineer)"
)

# Metaphorical "learning" used as adjective modifying engineer persona
METAPHOR_RE = re.compile(
    r"(?i)\b(quick[\s\-]?learning\s+engineer|ever[\s\-]?learning\s+engineer|"
    r"fast[\s\-]?learning\s+engineer|continuous(?:ly)?\s+learning\s+engineer|"
    r"keep\s+learning\s+engineer|always[\s\-]?learning\s+engineer)"
)


def parse_location(location: str) -> tuple[str, str, str]:
    """Return (city, state_region, country) inferred from location string.

    Returns empty strings for parts that cannot be determined reliably.
    """
    if not location:
        return "", "", ""
    loc = location.strip()

    # Exact country-name match
    for name, code in COUNTRY_MAP.items():
        if loc.lower() == name.lower():
            return "", "", code

    parts = [p.strip() for p in loc.split(",")]

    if len(parts) >= 3:
        city_raw, state_raw, country_raw = parts[0], parts[1], parts[-1]
        country = COUNTRY_MAP.get(country_raw, "")
        if not country and "United States" in country_raw:
            country = "US"
        state = US_STATES.get(state_raw, state_raw) if country == "US" else state_raw
        city = "" if city_raw.lower().startswith("greater") else city_raw
        return city, state, country

    if len(parts) == 2:
        city_raw, second = parts[0], parts[1]
        if second in US_STATES:
            return city_raw, US_STATES[second], "US"
        if second in US_STATES.values():
            return city_raw, second, "US"
        country = COUNTRY_MAP.get(second, "")
        if country:
            city = "" if city_raw.lower().startswith("greater") else city_raw
            return city, "", country
        return city_raw, second, ""

    # Single token — check known US metro keywords
    loc_lower = loc.lower()
    if any(kw in loc_lower for kw in US_METRO_LOWER):
        return "", "", "US"

    # Check non-US known metros
    for kw, code in METRO_COUNTRY_MAP.items():
        if kw in loc_lower:
            return "", "", code

    return "", "", ""


def infer_career_stage(job_title: str, org: str, bio: str) -> str:
    """Infer career stage from text fields; return '' when uncertain."""
    t = (job_title or "").lower()
    b = (bio or "").lower()
    o = (org or "").lower()

    academic_orgs = (
        "university", "college", "institute", "school ", "academy",
        "cmu", "mit", "asu", "johns hopkins", "dartmouth", "northwestern",
    )

    if any(x in t for x in ("professor", "associate professor", "assistant professor", "dean ", "faculty ")):
        return "faculty"
    if any(x in t or x in b for x in (
        "phd student", "doctoral candidate", "doctoral student",
        "graduate student", "graduate assistant", "phd candidate",
    )):
        return "student"
    if any(x in t for x in ("research scientist", "research assistant", "research associate", "postdoc")):
        return "researcher"
    if "retired" in t:
        return "practitioner"
    if any(x in t for x in ("ceo", "chief executive", "founder", "co-founder", "president")):
        return "industry"
    if any(x in t for x in ("teacher", "instructor", "lecturer", "educator")):
        return "practitioner"
    if any(x in t for x in ("learning engineer", "instructional designer", "instructional systems")):
        return "practitioner"
    if any(x in t for x in ("engineer", "developer", "analyst", "designer", "coordinator", "specialist")):
        return "practitioner" if any(x in o for x in academic_orgs) else "industry"

    return ""


def assess_le_title(person: dict) -> tuple[str, str]:
    """Return (assessment, reason) for LE title classification.

    assessment values: 'yes' (confirmed LE), 'maybe' (uncertain), 'no' (not LE).
    """
    status = person.get("status", "")
    triage = person.get("triage", "")
    job_title = (person.get("job_title") or "").strip()
    bio = (person.get("bio") or "").strip()
    dept = (person.get("department") or "").strip()
    combined = f"{job_title} {bio}"

    if status == "ARCHIVED":
        return "no", "Status ARCHIVED — rejected by triage"

    m = ML_RE.search(combined)
    if m:
        return "no", f'ML/robotics context: "{m.group()}"'

    m = METAPHOR_RE.search(combined)
    if m:
        return "no", f'Metaphorical usage: "{m.group()}"'

    title_l = job_title.lower()
    bio_l = bio.lower()

    le_in_title = bool(re.search(r"learning engineer", title_l))
    le_in_bio = (not le_in_title) and bool(re.search(r"learning engineer", bio_l))
    le_in_dept = (not le_in_title) and (not le_in_bio) and bool(
        re.search(r"learning engineer", dept.lower())
    )

    if le_in_title:
        if status == "APPROVED" or triage == "APPROVED":
            return "yes", "Explicit LE title; triage/status APPROVED"
        return "maybe", f"LE in job_title but triage={triage}, status={status} — verify"

    if le_in_bio:
        return "maybe", "LE in bio only; primary job_title is a different role"

    if le_in_dept:
        return "maybe", f'LE in department only: "{dept}"'

    return "maybe", "No LE term found in title, bio, or dept — insufficient data"


def main() -> None:
    """Read, enrich, and overwrite people.json."""
    data: list[dict] = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    counts: dict[str, int] = {"yes": 0, "maybe": 0, "no": 0}
    loc_filled = stage_filled = 0
    needs_manual: list[str] = []

    for person in data:
        loc = person.get("location", "")

        # Fill location subfields only when currently empty
        if loc and not person.get("country"):
            city, state, country = parse_location(loc)
            if city and not person.get("city"):
                person["city"] = city
                loc_filled += 1
            if state and not person.get("state_region"):
                person["state_region"] = state
            if country and not person.get("country"):
                person["country"] = country

        # Infer career_stage only when currently 'unknown'
        if person.get("career_stage") == "unknown":
            inferred = infer_career_stage(
                person.get("job_title", ""),
                person.get("organization", ""),
                person.get("bio", ""),
            )
            if inferred:
                person["career_stage"] = inferred
                stage_filled += 1

        # Add LE title assessment (always set, even if already present)
        assessment, reason = assess_le_title(person)
        person["le_title_assessment"] = assessment
        person["le_assessment_reason"] = reason
        counts[assessment] += 1

        if assessment == "maybe" and person.get("triage") == "NEEDS_REVIEW":
            needs_manual.append(person["person_id"])

    DATA_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    total = len(data)
    yes, maybe, no = counts["yes"], counts["maybe"], counts["no"]
    print(f"Processed {total} records.")
    print(f"\nLE title assessment:")
    print(f"  yes   (confirmed LE): {yes:3d}  ({yes/total:.0%})")
    print(f"  maybe (uncertain):    {maybe:3d}  ({maybe/total:.0%})")
    print(f"  no    (not LE):       {no:3d}  ({no/total:.0%})")
    print(f"\nAttribute gaps filled:")
    print(f"  Location subfields: {loc_filled}")
    print(f"  Career stage:       {stage_filled}")
    print(f"\nRecords needing manual review (NEEDS_REVIEW + maybe): {', '.join(needs_manual) or 'none'}")


if __name__ == "__main__":
    main()
