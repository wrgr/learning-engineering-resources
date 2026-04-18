"""Generate resource_keywords.json and topic_clusters.json for the Explore view.

Reads all MDX frontmatter (no LLM required by default). Pass --llm to call the
Claude API for richer per-resource keyword suggestions. Outputs two files to
site/src/data/ that are committed and consumed at Astro build time.
"""

import argparse
import json
import re
import sys
import yaml
from pathlib import Path
from collections import Counter

CONTENT = Path(__file__).resolve().parent.parent / "src" / "content"
DATA_OUT = Path(__file__).resolve().parent.parent / "src" / "data"

COLLECTIONS = ["practice", "tools", "reading-list", "events", "community"]

# -- Topic → cluster assignment (manually curated from topic_map.json) -------

CLUSTERS = [
    {
        "id": 0,
        "name": "Foundations of Learning",
        "topics": ["T00", "T01"],
        "description": "What is learning engineering? Origins, definitions, and the learning science evidence base.",
    },
    {
        "id": 1,
        "name": "HSI & Human Performance",
        "topics": ["T02", "T09", "T13"],
        "description": "Human systems integration, expert knowledge elicitation, and high-consequence domain applications.",
    },
    {
        "id": 2,
        "name": "AI & Adaptive Learning",
        "topics": ["T06", "T07", "T08"],
        "description": "Intelligent tutoring systems, foundation models in learning, simulation, and experiential design.",
    },
    {
        "id": 3,
        "name": "Assessment & Evidence",
        "topics": ["T04", "T15", "T17"],
        "description": "Measurement, analytics, evidence standards, and research methods.",
    },
    {
        "id": 4,
        "name": "Workforce & Training Systems",
        "topics": ["T10", "T11", "T12"],
        "description": "Workforce development, learning infrastructure, and instructional design.",
    },
    {
        "id": 5,
        "name": "Ethics, Equity & Community",
        "topics": ["T14", "T16"],
        "description": "Algorithmic fairness, equity in access, standards, and professional credentialing.",
    },
    {
        "id": 6,
        "name": "LE Process & Knowledge",
        "topics": ["T03", "T05"],
        "description": "The learning engineering process, knowledge representation, and ontologies.",
    },
]

# Build reverse index: topic_code → cluster_id
TOPIC_TO_CLUSTER: dict[str, int] = {}
for c in CLUSTERS:
    for t in c["topics"]:
        TOPIC_TO_CLUSTER[t] = c["id"]

# -- Topic → representative keywords ----------------------------------------

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "T00": ["field overview", "learning engineering", "ICICLE", "instructional design", "LE definition"],
    "T01": ["learning science", "cognitive load theory", "spaced practice", "retrieval practice", "worked examples", "transfer of learning"],
    "T02": ["human systems integration", "HSI", "systems engineering", "human factors", "sociotechnical systems", "MBSE", "human performance"],
    "T03": ["LE process", "iterative design", "rapid prototyping", "formative evaluation", "evidence-based design", "A/B testing"],
    "T04": ["measurement", "learning analytics", "educational data mining", "psychometrics", "assessment", "competency measurement"],
    "T05": ["knowledge representation", "ontology", "knowledge graph", "concept maps", "skill taxonomy", "competency framework"],
    "T06": ["intelligent tutoring", "adaptive systems", "knowledge tracing", "Bayesian student model", "cognitive tutor", "ITS"],
    "T07": ["AI in learning", "foundation models", "LLM", "generative AI", "automated feedback", "AI tutors"],
    "T08": ["simulation", "serious games", "VR", "AR", "experiential learning", "scenario-based training"],
    "T09": ["expert knowledge elicitation", "cognitive task analysis", "SME elicitation", "tacit knowledge", "knowledge engineering"],
    "T10": ["workforce development", "training systems", "military training", "healthcare training", "upskilling", "on-the-job learning"],
    "T11": ["learning infrastructure", "LMS", "xAPI", "learning record stores", "interoperability", "platform architecture"],
    "T12": ["instructional design", "ADDIE", "backward design", "competency-based design", "curriculum mapping", "Bloom taxonomy"],
    "T13": ["high-consequence domains", "defense", "healthcare", "aviation", "human error", "safety-critical systems"],
    "T14": ["ethics", "equity", "algorithmic fairness", "data privacy", "responsible AI", "access and inclusion"],
    "T15": ["evidence standards", "Kirkpatrick", "evaluation", "decision-grade evidence", "reproducibility", "effectiveness research"],
    "T16": ["standards", "credentialing", "professional community", "IEEE ICICLE", "LE credential", "field maturation"],
    "T17": ["research methods", "randomized trials", "quasi-experimental design", "design-based research", "open science", "replication"],
}

# HSI-related keyword signals in title/summary for flagging hsi_relevant
HSI_SIGNALS = [
    "human systems integration", "hsi", "human factors", "crew resource management",
    "human error", "systems engineering", "sociotechnical", "human performance",
    "human-centered", "human as", "ergonomics",
]


def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter from an MDX file."""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}


def slug_from_path(path: Path, collection: str) -> str:
    """Convert a file path to the collection-prefixed slug used as a resource ID."""
    rel = path.stem
    return f"{collection}/{rel}"


def assign_cluster(topics: list[str]) -> int:
    """Return the cluster_id that best represents this resource's topics.

    Uses the cluster that appears most often across the topic list. Falls back
    to cluster 0 if no topics match.
    """
    counts: Counter[int] = Counter()
    for t in topics:
        cid = TOPIC_TO_CLUSTER.get(t)
        if cid is not None:
            counts[cid] += 1
    if not counts:
        return 0
    return counts.most_common(1)[0][0]


def is_hsi_relevant(topics: list[str], title: str, summary: str) -> bool:
    """Return True if this resource is Human Systems Integration relevant."""
    if "T02" in topics:
        return True
    text = (title + " " + (summary or "")).lower()
    return any(sig in text for sig in HSI_SIGNALS)


def derive_keywords(topics: list[str], tags: list[str]) -> list[str]:
    """Build a deduplicated keyword list from topic codes and existing tags."""
    kws: list[str] = []
    for t in topics:
        kws.extend(TOPIC_KEYWORDS.get(t, [])[:3])  # top 3 per topic
    for tag in tags:
        if tag and not re.match(r"^T\d+$", tag) and not tag.startswith("http"):
            kws.append(tag.replace("-", " "))
    seen: set[str] = set()
    result: list[str] = []
    for kw in kws:
        key = kw.lower()
        if key not in seen:
            seen.add(key)
            result.append(kw)
    return result[:12]


def enrich_with_llm(resources: list[dict]) -> dict[str, list[str]]:
    """Call Claude API to generate richer keywords. Returns id → keywords map."""
    try:
        import anthropic
    except ImportError:
        print("ERROR: anthropic package not installed. Run: pip install anthropic", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic()
    results: dict[str, list[str]] = {}

    for i, res in enumerate(resources):
        rid = res["id"]
        prompt = (
            f"Resource: {res['title']}\n"
            f"Format: {res['format']}\n"
            f"Topics: {', '.join(res['topics'])}\n"
            f"Summary: {res.get('summary', '')[:400]}\n\n"
            "List 6-8 concise keyword phrases (2-4 words each) that describe this resource's "
            "main themes. Focus on technical concepts, methods, and domain areas. "
            "Return only a JSON array of strings, no explanation."
        )
        try:
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()
            kws = json.loads(raw)
            if isinstance(kws, list):
                results[rid] = [str(k) for k in kws[:10]]
            else:
                results[rid] = []
        except Exception as e:
            print(f"  LLM error for {rid}: {e}", file=sys.stderr)
            results[rid] = []

        if (i + 1) % 10 == 0:
            print(f"  LLM enriched {i + 1}/{len(resources)}")

    return results


def main() -> None:
    """Entry point: parse args, scan content, write JSON outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llm", action="store_true", help="Call Claude API for keyword enrichment")
    args = parser.parse_args()

    resources: list[dict] = []
    for collection in COLLECTIONS:
        col_dir = CONTENT / collection
        if not col_dir.exists():
            continue
        for mdx in sorted(col_dir.glob("**/*.mdx")):
            fm = parse_frontmatter(mdx.read_text(encoding="utf-8"))
            if not fm:
                continue
            rid = slug_from_path(mdx, collection)
            topics = fm.get("topics") or []
            tags = [t for t in (fm.get("tags") or []) if t]
            resources.append({
                "id": rid,
                "title": fm.get("title", ""),
                "format": fm.get("format", ""),
                "topics": topics,
                "tags": tags,
                "summary": fm.get("summary", ""),
            })

    print(f"Loaded {len(resources)} resources across {len(COLLECTIONS)} collections.")

    llm_keywords: dict[str, list[str]] = {}
    if args.llm:
        print("Calling Claude API for keyword enrichment …")
        llm_keywords = enrich_with_llm(resources)

    resource_keywords: dict[str, dict] = {}
    for res in resources:
        rid = res["id"]
        base_kws = derive_keywords(res["topics"], res["tags"])
        llm_kws = llm_keywords.get(rid, [])
        # Merge: LLM keywords first (richer), then base keywords to fill gaps
        merged = llm_kws if llm_kws else base_kws
        resource_keywords[rid] = {
            "keywords": merged,
            "hsi_relevant": is_hsi_relevant(res["topics"], res["title"], res["summary"]),
            "cluster_id": assign_cluster(res["topics"]),
        }

    keywords_path = DATA_OUT / "resource_keywords.json"
    keywords_path.write_text(json.dumps(resource_keywords, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {keywords_path}")

    clusters_path = DATA_OUT / "topic_clusters.json"
    clusters_path.write_text(json.dumps(CLUSTERS, indent=2), encoding="utf-8")
    print(f"Wrote {clusters_path}")

    hsi_count = sum(1 for v in resource_keywords.values() if v["hsi_relevant"])
    print(f"Done. {hsi_count} HSI-relevant resources. Clusters: {len(CLUSTERS)}.")


if __name__ == "__main__":
    main()
