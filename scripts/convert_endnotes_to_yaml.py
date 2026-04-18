"""Convert book endnote paper-like citations to landscape YAML files."""

import glob
import json
import re
import textwrap
from pathlib import Path

PAPERS_DIR = Path("/home/user/lecommons/landscape/resources/papers")
ENDNOTES_FILE = Path(
    "/home/user/lecommons/archive/corpus/book_endnotes_unique.jsonl"
)

CONCEPT_TOPIC_MAP = [
    (r"tutor|intelligent tutoring|cognitive tutor|adaptive learn|formative|hint|scaffold",
     "T06"),
    (r"analytic|prediction|dashboard|mooc|massive open", "T09"),
    (r"cognitive load|working memory|schema|multimedia learn", "T04"),
    (r"retrieval|testing effect|spacing|self.determin|metacogni|self.regulat",
     "T01"),
    (r"collaborat|cscl|peer learn|knowledge build|discourse", "T07"),
    (r"simulat|virtual reality|augmented reality|embodied|game.based|immersive",
     "T08"),
    (r"systems engineer|instructional system|addie|human systems|sociotechnical|"
     r"human factor|human.centered|hsi",
     "T02"),
    (r"instructional design|curriculum|scaffold|backward design|4c.id|"
     r"worked example",
     "T03"),
    (r"transfer of train|workforce|kirkpatrick|training program|team train|"
     r"professional develop",
     "T10"),
    (r"design principle|learning principle|first principle|mayer|multimedia",
     "T12"),
    (r"randomized control|rct|design.based research|quasi.experiment|causal",
     "T17"),
    (r"meta.analy|systematic review|evidence.based|what works|research synthesis",
     "T15"),
    (r"knowledge trac|bayesian knowledge|item response|psychometric", "T11"),
    (r"online learn|distance learn|e.learn|blended|flipped|lms", "T14"),
    (r"platform|technology.enhanc|educational technolog|edtech", "T16"),
    (r"learn|cogniti|educat|teach|instruct|student|knowledge", "T01"),
]


def text_to_topics(text: str) -> tuple[str, list[str]]:
    """Map free text to (primary_topic, secondary_topics)."""
    assigned: list[str] = []
    for pattern, topic in CONCEPT_TOPIC_MAP:
        if re.search(pattern, text, re.IGNORECASE):
            if topic not in assigned:
                assigned.append(topic)
        if len(assigned) >= 3:
            break
    if not assigned:
        assigned = ["T01"]
    return assigned[0], assigned[1:3]


def cite_tier(count: int) -> str:
    """Classify citation tier from count."""
    if count >= 5000:
        return "foundational"
    if count >= 800:
        return "highly_cited"
    return "contemporary"


def slugify(title: str) -> str:
    """Make a short filename-safe slug."""
    words = re.sub(r"[^a-z0-9\s]", "", title.lower()).split()
    stop = {"a", "an", "the", "of", "in", "on", "at", "to", "for", "and",
            "or", "with", "by", "from", "as", "is", "are", "that", "this"}
    significant = [w for w in words if w not in stop and len(w) > 2][:2]
    return "-".join(significant) if significant else "paper"


def parse_authors(citation_text: str) -> list[str]:
    """Extract author names from a formatted citation string.

    Handles Chicago-style citations like:
    'Smith, John, and Jane Doe. "Title..." Venue...'
    """
    # Find the title marker (quoted title starts with opening quote)
    # Authors come before the first quoted title
    match = re.match(r'^(.*?)["""]', citation_text, re.DOTALL)
    if not match:
        return []

    author_str = match.group(1).strip().rstrip(",. ")
    if not author_str:
        return []

    # Split on ", and " or " and " between author segments
    # Chicago style: "Last, First, and First Last."
    author_str = re.sub(r"\s+and\s+", " | ", author_str)
    parts = [p.strip() for p in author_str.split(",") if p.strip()]

    authors = []
    i = 0
    while i < len(parts):
        part = parts[i]
        if "|" in part:
            # "First Last" format (after the "and")
            for subpart in part.split("|"):
                subpart = subpart.strip()
                if subpart:
                    authors.append(subpart)
            i += 1
        elif i + 1 < len(parts) and not re.search(r"\d", parts[i + 1]):
            # "Last, First" pair
            last = parts[i].strip()
            first = parts[i + 1].strip()
            if first and len(first.split()) <= 3 and re.match(r"^[A-Z]", first):
                authors.append(f"{first} {last}")
                i += 2
            else:
                if last:
                    authors.append(last)
                i += 1
        else:
            if part:
                authors.append(part)
            i += 1

    return [a for a in authors if len(a) > 2][:6]


def extract_title(citation_text: str) -> str:
    """Extract quoted title from citation text."""
    match = re.search(r'["""](.+?)["""]', citation_text)
    if match:
        return match.group(1).strip()
    # Fallback: everything between first period and next period/venue
    parts = citation_text.split(".")
    if len(parts) > 1:
        return parts[1].strip()
    return ""


def extract_venue(citation_text: str, year: int) -> str:
    """Heuristically extract venue name from citation text."""
    # After the title and year
    year_str = str(year) if year else ""
    match = re.search(
        r'["""].+?["""]\s*\.\s*(?:In\s+)?(.+?)(?:,\s*(?:vol\.|no\.|' + year_str + r'|\d{4}))',
        citation_text, re.IGNORECASE
    )
    if match:
        venue = match.group(1).strip()
        return venue[:80]

    # Try "In Proceedings of..."
    proc_match = re.search(r"In\s+(Proceedings[^,]+)", citation_text)
    if proc_match:
        return proc_match.group(1).strip()[:80]

    return "Unknown Venue"


def load_existing_dois() -> set[str]:
    """Load DOIs from existing YAML files."""
    dois = set()
    for yf in PAPERS_DIR.glob("*.yaml"):
        for line in yf.read_text().splitlines():
            if line.startswith("doi:"):
                doi = line.split("doi:", 1)[1].strip().strip('"').lower()
                if doi:
                    dois.add(doi)
    return dois


def next_ap_id() -> int:
    """Find next available AP number."""
    import re as _re
    max_n = 149
    for yf in PAPERS_DIR.glob("le-ap-*.yaml"):
        m = _re.match(r"le-ap-(\d+)-", yf.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def yaml_block(data: dict) -> str:
    """Render paper YAML."""
    lines = [
        f'resource_id: {data["resource_id"]}',
        "content_type: AP",
        "status: seed",
        f'title: "{data["title"].replace(chr(34), chr(39))}"',
    ]
    if data["authors"]:
        lines.append("authors:")
        for a in data["authors"]:
            lines.append(f'  - {a}')
    else:
        lines.append("authors: []")

    lines.append(f'year: {data["year"]}')
    lines.append(f'venue: {data["venue"]}')
    if data.get("doi"):
        lines.append(f'doi: "{data["doi"]}"')
    lines.append(f'tier: {data["tier"]}')
    lines.append(f'citation_count_approx: 0')
    lines.append(f'openalex_id: ""')
    lines.append("significance: >")
    for wrapped in textwrap.wrap(data["significance"], width=78):
        lines.append(f"  {wrapped}")
    lines.append(f'primary_topic: {data["primary_topic"]}')
    if data["secondary_topics"]:
        lines.append("secondary_topics:")
        for t in data["secondary_topics"]:
            lines.append(f"  - {t}")
    return "\n".join(lines) + "\n"


def main() -> None:
    """Convert paper-like book endnotes to YAML, skipping DOI duplicates."""
    existing_dois = load_existing_dois()
    new_id = next_ap_id()
    written = 0
    skipped = 0

    with open(ENDNOTES_FILE) as f:
        entries = [json.loads(l) for l in f if l.strip()]

    for entry in entries:
        cat = entry.get("reference_category", "")
        if cat not in ("paper_like", "conference_like"):
            continue

        doi = (entry.get("doi") or "").lower().strip()
        if doi and doi in existing_dois:
            skipped += 1
            continue
        if doi:
            existing_dois.add(doi)

        citation_text = entry.get("citation_text", "")
        year = entry.get("year") or 0

        title = extract_title(citation_text)
        if not title:
            skipped += 1
            continue

        authors = parse_authors(citation_text)
        venue = extract_venue(citation_text, year)
        primary_topic, secondary_topics = text_to_topics(citation_text)

        significance = (
            f"Cited in Goodell & Kolodner, Learning Engineering Toolkit. "
            f"Addresses {primary_topic} topics in learning engineering. "
            f"Full bibliographic details in citation: {citation_text[:120]}..."
        )

        ap_id = f"LE-AP-{new_id:03d}"
        slug = slugify(title)
        year_str = str(year) if year else "0000"
        filename = f"le-ap-{new_id:03d}-{slug}-{year_str}.yaml"

        data = {
            "resource_id": ap_id,
            "title": title,
            "authors": authors,
            "year": year,
            "venue": venue,
            "doi": doi,
            "tier": "contemporary",
            "significance": significance,
            "primary_topic": primary_topic,
            "secondary_topics": secondary_topics,
        }

        (PAPERS_DIR / filename).write_text(yaml_block(data))
        new_id += 1
        written += 1

    print(
        f"Written: {written}  |  Skipped: {skipped}  |  "
        f"IDs: LE-AP-{next_ap_id() - written:03d}–LE-AP-{new_id - 1:03d}"
    )


if __name__ == "__main__":
    main()
