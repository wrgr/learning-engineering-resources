"""Convert archive JSONL candidates to landscape YAML paper files."""

import json
import os
import re
import sys
from pathlib import Path

PAPERS_DIR = Path("/home/user/lecommons/landscape/resources/papers")
CANDIDATES_FILE = Path(
    "/home/user/lecommons/archive/corpus/expansion/"
    "candidates_cross_seed_ge2_kcore2_indegree2.jsonl"
)

# Map OpenAlex concept display_name keywords → topic codes
# Ordered: first match wins for primary_topic
CONCEPT_TOPIC_MAP = [
    # T06: ITS / tutoring / adaptive learning
    (r"tutor|intelligent tutoring|cognitive tutor|adaptive learn|formative|hint|scaffold",
     "T06"),
    # T09: Learning analytics / data / prediction / MOOC analytics
    (r"learning analytic|educational data|prediction|at.risk|dashboard|clickstream|"
     r"engagement|mooc|massive open",
     "T09"),
    # T04: Cognitive load / working memory / multimedia / schema
    (r"cognitive load|working memory|schema|multimedia learn|split.attention|"
     r"redundancy|germane|intrinsic|extraneous",
     "T04"),
    # T01: Learning science / memory / retrieval / spacing / motivation
    (r"retrieval practice|testing effect|spacing effect|spaced repetition|"
     r"desirable difficult|interleav|self.determin|intrinsic motiv|metacogni|"
     r"self.regulat|self.efficac|growth mindset",
     "T01"),
    # T07: Collaborative / CSCL / discourse / peer
    (r"collaborat|cscl|peer learn|knowledge build|discourse|discussion|"
     r"computer.supported cooperative",
     "T07"),
    # T08: Simulation / embodied / VR / AR / game
    (r"simulat|virtual reality|augmented reality|embodied|game.based|"
     r"serious game|mixed reality|immersive",
     "T08"),
    # T02: Systems engineering / ADDIE / HSI / design process
    (r"systems engineer|instructional system|addie|human systems|"
     r"sociotechnical|system develop|human factor",
     "T02"),
    # T03: Instructional design / curriculum / scaffolding / UbD
    (r"instructional design|curriculum|scaffold|lesson plan|learning objective|"
     r"backward design|4c.id|worked example",
     "T03"),
    # T10: Training / transfer / workforce / evaluation / Kirkpatrick
    (r"transfer of train|workforce train|kirkpatrick|training program|"
     r"team train|corporate learn|professional develop",
     "T10"),
    # T12: Design principles / multimedia / learning theory applied
    (r"design principle|learning principle|first principle|mayer|"
     r"coherence principle|segmenting",
     "T12"),
    # T17: Research methods / RCT / DBR / experimental
    (r"randomized control|rct|design.based research|quasi.experiment|"
     r"causal inference|effect size",
     "T17"),
    # T15: Evidence-based / systematic review / meta-analysis
    (r"meta.analy|systematic review|evidence.based|what works|effect size|"
     r"research synthesis",
     "T15"),
    # T11: Educational data mining / knowledge tracing
    (r"knowledge trac|bayesian knowledge|item response|psychometric|"
     r"educational data min",
     "T11"),
    # T14: Online learning / distance / e-learning platforms
    (r"online learn|distance learn|e.learn|blended|flipped classroom|"
     r"lms|learning management",
     "T14"),
    # T16: EdTech platforms / tools / technology
    (r"platform|technology.enhanc|educational technolog|edtech|learning platform",
     "T16"),
    # Fallback: general learning / cognition / education
    (r"learn|cogniti|educat|teach|instruct|student|knowledge", "T01"),
]


def concepts_to_topics(concepts: list[dict]) -> tuple[str, list[str]]:
    """Map concepts_top list to (primary_topic, secondary_topics)."""
    assigned: list[str] = []
    concept_text = " ".join(c.get("display_name", "") for c in concepts).lower()

    for pattern, topic in CONCEPT_TOPIC_MAP:
        if re.search(pattern, concept_text, re.IGNORECASE):
            if topic not in assigned:
                assigned.append(topic)
        if len(assigned) >= 3:
            break

    if not assigned:
        assigned = ["T01"]

    return assigned[0], assigned[1:3]


def cite_tier(count: int) -> str:
    """Classify citation tier."""
    if count >= 5000:
        return "foundational"
    if count >= 800:
        return "highly_cited"
    return "contemporary"


def slugify(title: str) -> str:
    """Make a short filename-safe slug from a title."""
    # Take first three significant words
    words = re.sub(r"[^a-z0-9\s]", "", title.lower()).split()
    stop = {"a", "an", "the", "of", "in", "on", "at", "to", "for", "and",
            "or", "with", "by", "from", "as", "is", "are", "that", "this",
            "it", "its", "be", "was", "were", "how", "what", "which"}
    significant = [w for w in words if w not in stop and len(w) > 2][:2]
    return "-".join(significant) if significant else "paper"


def load_existing_dois() -> set[str]:
    """Load DOIs from existing YAML files for deduplication."""
    dois = set()
    for yf in PAPERS_DIR.glob("*.yaml"):
        text = yf.read_text()
        for line in text.splitlines():
            if line.startswith("doi:"):
                doi = line.split("doi:", 1)[1].strip().strip('"').lower()
                if doi:
                    dois.add(doi)
    return dois


def next_ap_id() -> int:
    """Find the next available AP number."""
    max_n = 149
    for yf in PAPERS_DIR.glob("le-ap-*.yaml"):
        m = re.match(r"le-ap-(\d+)-", yf.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def significance_from_concepts(title: str, venue: str, concepts: list[dict]) -> str:
    """Generate minimal significance text from available metadata."""
    top_concepts = [c["display_name"] for c in concepts[:3]]
    concept_str = ", ".join(top_concepts) if top_concepts else "learning and instruction"
    venue_str = venue or "academic journal"
    return (
        f"Published in {venue_str}; addresses {concept_str.lower()}. "
        f"Quality-filtered from OpenAlex cross-seed expansion of the Goodell & Kolodner "
        f"Learning Engineering Toolkit corpus. Authors pending OpenAlex enrichment."
    )


def yaml_block(data: dict) -> str:
    """Render YAML manually to control formatting."""
    lines = []
    lines.append(f'resource_id: {data["resource_id"]}')
    lines.append(f'content_type: AP')
    lines.append(f'status: seed')
    lines.append(f'title: "{data["title"].replace(chr(34), chr(39))}"')
    lines.append("authors: []")
    lines.append(f'year: {data["year"]}')
    lines.append(f'venue: {data["venue"]}')
    if data.get("doi"):
        lines.append(f'doi: "{data["doi"]}"')
    lines.append(f'tier: {data["tier"]}')
    lines.append(f'citation_count_approx: {data["citations"]}')
    lines.append(f'cross_seed_score: {data["cross_seed_score"]}')
    lines.append(f'openalex_id: "{data["openalex_id"]}"')
    lines.append("significance: >")
    # Wrap significance at ~80 chars
    sig = data["significance"]
    import textwrap
    for wrapped_line in textwrap.wrap(sig, width=78):
        lines.append(f"  {wrapped_line}")
    lines.append(f'primary_topic: {data["primary_topic"]}')
    if data["secondary_topics"]:
        lines.append("secondary_topics:")
        for t in data["secondary_topics"]:
            lines.append(f"  - {t}")
    return "\n".join(lines) + "\n"


def main() -> None:
    """Convert archive JSONL to YAML files, skipping DOI duplicates."""
    existing_dois = load_existing_dois()
    start_id = next_ap_id()

    candidates = []
    with open(CANDIDATES_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                candidates.append(json.loads(line))

    # Deduplicate by DOI within candidates too
    seen_dois: set[str] = set(existing_dois)
    new_id = start_id
    written = 0
    skipped_dup = 0
    skipped_no_title = 0

    for entry in candidates:
        title = entry.get("title", "").strip()
        if not title:
            skipped_no_title += 1
            continue

        doi = (entry.get("doi") or "").lower().strip()
        if doi and doi in seen_dois:
            skipped_dup += 1
            continue
        if doi:
            seen_dois.add(doi)

        year = entry.get("publication_year") or 0
        venue = entry.get("host_venue") or "Unknown Venue"
        citations = entry.get("cited_by_count") or 0
        concepts = entry.get("concepts_top") or []
        cross_seed = entry.get("cross_seed_score") or 0
        openalex_id = entry.get("work_id") or entry.get("openalex_id") or ""

        primary_topic, secondary_topics = concepts_to_topics(concepts)
        tier = cite_tier(citations)
        significance = significance_from_concepts(title, venue, concepts)

        ap_id = f"LE-AP-{new_id:03d}"
        slug = slugify(title)
        year_str = str(year) if year else "0000"
        filename = f"le-ap-{new_id:03d}-{slug}-{year_str}.yaml"

        data = {
            "resource_id": ap_id,
            "title": title,
            "year": year,
            "venue": venue,
            "doi": doi,
            "tier": tier,
            "citations": citations,
            "cross_seed_score": cross_seed,
            "openalex_id": openalex_id,
            "significance": significance,
            "primary_topic": primary_topic,
            "secondary_topics": secondary_topics,
        }

        out_path = PAPERS_DIR / filename
        out_path.write_text(yaml_block(data))
        new_id += 1
        written += 1

    print(
        f"Written: {written} files  |  "
        f"Skipped (dup DOI): {skipped_dup}  |  "
        f"Skipped (no title): {skipped_no_title}  |  "
        f"IDs: LE-AP-{start_id:03d} – LE-AP-{new_id - 1:03d}"
    )


if __name__ == "__main__":
    main()
