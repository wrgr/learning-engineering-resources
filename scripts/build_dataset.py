#!/usr/bin/env python3
"""Build website data artifacts from the current Learning Engineering corpus."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "corpus"
DATA_DIR = ROOT / "data"
OPENALEX_BASE = "https://api.openalex.org"
OPENALEX_TIMEOUT_SEC = 30.0
OPENALEX_SLEEP_SEC = 0.15
OPENALEX_BATCH_SIZE = 20
OPENALEX_MAX_RETRIES = 6
OPENALEX_SELECT_FIELDS = (
    "id,doi,display_name,abstract_inverted_index,authorships,"
    "publication_year,type,cited_by_count,primary_location,host_venue,referenced_works"
)
OPENALEX_CACHE_PATH = CORPUS_DIR / "cache" / "openalex_works_cache.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_doi(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    text = text.replace("https://doi.org/", "").replace("http://doi.org/", "")
    text = text.replace("doi.org/", "").replace("DOI:", "").strip()
    return text


def to_work_id(openalex_id: str) -> str:
    text = (openalex_id or "").strip()
    if not text:
        return ""
    if text.startswith("W") and "/" not in text:
        return text
    return text.rstrip("/").split("/")[-1]


def chunked(items: List[str], size: int) -> Iterable[List[str]]:
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def load_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def listify(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def parse_authors(value: str) -> List[str]:
    text = (value or "").strip()
    if not text:
        return []
    # Preserve compact citation strings like "Smith J et al."
    if " and " in text and "," not in text:
        return [part.strip() for part in text.split(" and ") if part.strip()]
    return [text]


def normalize_url(value: str) -> str:
    text = (value or "").strip()
    if not text or text.lower() in {"[internal]", "internal", "n/a"}:
        return ""
    if text.startswith("www."):
        return f"https://{text}"
    return text


def doi_to_url(doi: str) -> str:
    doi = normalize_doi(doi)
    if not doi:
        return ""
    if doi.startswith("http://") or doi.startswith("https://"):
        return doi
    return f"https://doi.org/{doi}"


def citation_plain(title: str, authors: str, year, venue: str, doi: str) -> str:
    parts = []
    if authors:
        parts.append(authors)
    if year:
        parts.append(f"({year})")
    if title:
        parts.append(f"{title}.")
    if venue:
        parts.append(venue)
    if doi:
        parts.append(f"DOI: {doi}")
    return " ".join(parts).strip()


def citation_bibtex(key: str, title: str, authors: str, year, venue: str, doi: str) -> str:
    safe_key = (key or "resource").replace(" ", "_")
    lines = [f"@misc{{{safe_key},", f"  title = {{{title}}},"]
    if authors:
        lines.append(f"  author = {{{authors}}},")
    if year:
        lines.append(f"  year = {{{year}}},")
    if venue:
        lines.append(f"  howpublished = {{{venue}}},")
    if doi:
        lines.append(f"  doi = {{{doi}}},")
    lines.append("}")
    return "\n".join(lines)


def api_get_json(path: str, params: Dict[str, str]) -> Dict:
    q = dict(params)
    mailto = (os.getenv("OPENALEX_MAILTO") or "").strip()
    if mailto and "mailto" not in q:
        q["mailto"] = mailto

    url = f"{OPENALEX_BASE}{path}?{urllib.parse.urlencode(q)}"
    req = urllib.request.Request(url, headers={"User-Agent": "learning-engineering-resources/1.0"})

    last_error = None
    for attempt in range(OPENALEX_MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=OPENALEX_TIMEOUT_SEC) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if OPENALEX_SLEEP_SEC > 0:
                time.sleep(OPENALEX_SLEEP_SEC)
            return data
        except urllib.error.HTTPError as exc:
            last_error = exc
            retriable = exc.code in {429, 500, 502, 503, 504}
            if not retriable or attempt >= OPENALEX_MAX_RETRIES:
                raise
            retry_after = 0.0
            if exc.headers:
                raw = exc.headers.get("Retry-After", "").strip()
                if raw:
                    try:
                        retry_after = float(raw)
                    except ValueError:
                        retry_after = 0.0
            wait_sec = retry_after if retry_after > 0 else min(2**attempt, 60)
            time.sleep(wait_sec)
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt >= OPENALEX_MAX_RETRIES:
                raise
            time.sleep(min(2**attempt, 30))

    raise RuntimeError(f"OpenAlex request failed after retries: {last_error}")


def decode_abstract(index: Dict) -> str:
    if not isinstance(index, dict) or not index:
        return ""

    max_pos = -1
    for positions in index.values():
        if not isinstance(positions, list):
            continue
        for pos in positions:
            if isinstance(pos, int) and pos > max_pos:
                max_pos = pos

    if max_pos < 0 or max_pos > 50000:
        return ""

    tokens = [""] * (max_pos + 1)
    for token, positions in index.items():
        if not isinstance(positions, list):
            continue
        for pos in positions:
            if isinstance(pos, int) and 0 <= pos <= max_pos and not tokens[pos]:
                tokens[pos] = str(token)

    text = " ".join(token for token in tokens if token).strip()
    if not text:
        return ""
    for punct in [",", ".", ";", ":", "?", "!", ")", "]", "}"]:
        text = text.replace(f" {punct}", punct)
    for punct in ["(", "[", "{"]:
        text = text.replace(f"{punct} ", punct)
    return text.strip()


def work_to_metadata(work: Dict) -> Dict:
    work_id = to_work_id(work.get("id", ""))
    doi = normalize_doi(work.get("doi", ""))

    authors: List[str] = []
    seen = set()
    for row in work.get("authorships", []) or []:
        name = ((row.get("author") or {}).get("display_name") or "").strip()
        if name and name not in seen:
            seen.add(name)
            authors.append(name)

    venue = ((work.get("primary_location") or {}).get("source") or {}).get("display_name", "")
    if not venue:
        venue = ((work.get("host_venue") or {}).get("display_name") or "").strip()

    return {
        "work_id": work_id,
        "openalex_id": (work.get("id") or "").strip(),
        "doi": doi,
        "title": (work.get("display_name") or "").strip(),
        "abstract": decode_abstract(work.get("abstract_inverted_index")),
        "authors": authors,
        "year": work.get("publication_year"),
        "type": (work.get("type") or "").strip(),
        "cited_by_count": int(work.get("cited_by_count") or 0),
        "venue": (venue or "").strip(),
        "referenced_works": [to_work_id(ref) for ref in (work.get("referenced_works") or []) if to_work_id(ref)],
    }


def load_openalex_cache(path: Path) -> Dict[str, Dict]:
    if not path.exists():
        return {}
    try:
        payload = load_json(path)
    except Exception:
        return {}
    if isinstance(payload, dict) and isinstance(payload.get("works"), dict):
        return payload["works"]
    if isinstance(payload, dict):
        return payload
    return {}


def save_openalex_cache(path: Path, rows: Dict[str, Dict]) -> None:
    payload = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "works": rows,
        "count": len(rows),
    }
    write_json(path, payload)


def fetch_openalex_metadata(seed_papers: List[Dict], hop_papers: List[Dict]) -> Dict[str, Dict]:
    papers = seed_papers + hop_papers
    cache = load_openalex_cache(OPENALEX_CACHE_PATH)

    work_ids_needed: Set[str] = set()
    dois_needed: Set[str] = set()

    for paper in papers:
        work_id = to_work_id(paper.get("openalex_id", "")) or (
            paper.get("id", "") if str(paper.get("id", "")).startswith("W") else ""
        )
        doi = normalize_doi(paper.get("doi", ""))
        if work_id and work_id not in cache:
            work_ids_needed.add(work_id)
        if doi:
            dois_needed.add(doi)

    fetched = 0

    for batch in chunked(sorted(work_ids_needed), OPENALEX_BATCH_SIZE):
        try:
            data = api_get_json(
                "/works",
                {
                    "filter": "openalex:" + "|".join(batch),
                    "per-page": str(len(batch)),
                    "select": OPENALEX_SELECT_FIELDS,
                },
            )
        except Exception as exc:
            print(f"[warn] OpenAlex batch fetch failed for {len(batch)} IDs: {exc}")
            continue
        for work in data.get("results", []):
            meta = work_to_metadata(work)
            if meta["work_id"]:
                cache[meta["work_id"]] = meta
                fetched += 1

    doi_to_work_id = {meta.get("doi"): wid for wid, meta in cache.items() if meta.get("doi")}
    for doi in sorted(dois_needed):
        if doi in doi_to_work_id:
            continue
        try:
            data = api_get_json(
                "/works",
                {"filter": f"doi:{doi}", "per-page": "1", "select": OPENALEX_SELECT_FIELDS},
            )
        except Exception as exc:
            print(f"[warn] OpenAlex DOI fetch failed for {doi}: {exc}")
            continue
        results = data.get("results", [])
        if not results:
            continue
        meta = work_to_metadata(results[0])
        if meta["work_id"]:
            cache[meta["work_id"]] = meta
            doi_to_work_id[doi] = meta["work_id"]
            fetched += 1

    if fetched:
        save_openalex_cache(OPENALEX_CACHE_PATH, cache)

    return cache


def enrich_papers_with_openalex(seed_papers: List[Dict], hop_papers: List[Dict]) -> Dict:
    metadata_by_work_id = fetch_openalex_metadata(seed_papers, hop_papers)
    metadata_by_doi = {
        meta["doi"]: meta for meta in metadata_by_work_id.values() if isinstance(meta, dict) and meta.get("doi")
    }

    total = 0
    enriched = 0
    abstracts_filled = 0

    for paper in seed_papers + hop_papers:
        total += 1
        paper_doi = normalize_doi(paper.get("doi", ""))
        work_id = to_work_id(paper.get("openalex_id", "")) or (
            paper.get("id", "") if str(paper.get("id", "")).startswith("W") else ""
        )

        meta = metadata_by_work_id.get(work_id) or metadata_by_doi.get(paper_doi)
        if not meta:
            continue
        enriched += 1

        if not paper.get("openalex_id") and meta.get("openalex_id"):
            paper["openalex_id"] = meta["openalex_id"]
        if (not paper.get("title") or paper.get("title", "").strip().lower() == "untitled") and meta.get("title"):
            paper["title"] = meta["title"]
        if not paper.get("abstract") and meta.get("abstract"):
            paper["abstract"] = meta["abstract"]
            abstracts_filled += 1
        if not paper.get("authors") and meta.get("authors"):
            paper["authors"] = meta["authors"]
        if not paper.get("year") and meta.get("year"):
            paper["year"] = meta["year"]
        if not paper.get("doi") and meta.get("doi"):
            paper["doi"] = meta["doi"]
        if not paper.get("type") and meta.get("type"):
            paper["type"] = meta["type"]
        if (not paper.get("cited_by_count")) and meta.get("cited_by_count"):
            paper["cited_by_count"] = meta["cited_by_count"]
        if not paper.get("referenced_works") and meta.get("referenced_works"):
            paper["referenced_works"] = meta["referenced_works"]
        if not paper.get("venue") and meta.get("venue"):
            paper["venue"] = meta["venue"]

        authors_text = ", ".join(paper.get("authors", []))
        venue_text = (paper.get("venue") or "").strip()
        doi_text = normalize_doi(paper.get("doi", ""))
        paper["citation_plain"] = citation_plain(
            paper.get("title", ""),
            authors_text,
            paper.get("year"),
            venue_text,
            doi_text,
        )
        paper["citation_bibtex"] = citation_bibtex(
            paper.get("id", "resource"),
            paper.get("title", ""),
            authors_text,
            paper.get("year"),
            venue_text,
            doi_text,
        )
        paper["source_url"] = doi_to_url(doi_text) or paper.get("openalex_id", "")

    missing_abstracts = sum(1 for paper in (seed_papers + hop_papers) if not (paper.get("abstract") or "").strip())
    return {
        "papers_total": total,
        "papers_with_openalex_match": enriched,
        "abstracts_filled": abstracts_filled,
        "papers_missing_abstract": missing_abstracts,
    }


@dataclass
class Topic:
    code: str
    layer: str
    name: str
    why: str


def load_topics() -> Tuple[List[Topic], Dict[str, Topic]]:
    rows = load_json(CORPUS_DIR / "tables" / "topic_map.json")
    topics: List[Topic] = []
    for row in rows:
        code = row.get("topic_code", "").strip()
        if not code:
            continue
        topics.append(
            Topic(
                code=code,
                layer=(row.get("layer") or "").strip(),
                name=(row.get("topic_name") or "").strip(),
                why=(row.get("why_it_matters") or "").strip(),
            )
        )
    topic_by_code = {topic.code: topic for topic in topics}
    return topics, topic_by_code


def build_seed_topic_lookup(topic_by_code: Dict[str, Topic]) -> Dict[str, Set[str]]:
    lookup: Dict[str, Set[str]] = defaultdict(set)

    corpus_rows = load_json(CORPUS_DIR / "tables" / "corpus_registry.json")
    for row in corpus_rows:
        corpus_id = (row.get("corpus_id") or "").strip()
        if not corpus_id:
            continue
        topics = [row.get("primary_topic", "")] + listify(row.get("secondary_topics", []))
        topics = [t for t in topics if t in topic_by_code]
        if not topics:
            continue
        lookup[f"WORKBOOK-{corpus_id}"].update(topics)

    expansion_rows = load_json(CORPUS_DIR / "tables" / "expansion_sources.json")
    for row in expansion_rows:
        source_id = (row.get("source_id") or "").strip()
        if not source_id:
            continue
        topics = [row.get("primary_topic", "")] + listify(row.get("topics_covered", []))
        topics = [t for t in topics if t in topic_by_code]
        if topics:
            lookup[f"WORKBOOK-{source_id}"].update(topics)

    return lookup


def build_seed_papers(topic_by_code: Dict[str, Topic]) -> List[Dict]:
    rows = load_jsonl(CORPUS_DIR / "academic_papers.jsonl")
    papers: List[Dict] = []
    for row in rows:
        topic_codes = [row.get("primary_topic", "")] + listify(row.get("secondary_topics", []))
        topic_codes = [code for code in topic_codes if code in topic_by_code]

        title = (row.get("title") or "").strip()
        authors_text = (row.get("authors") or "").strip()
        year = row.get("year")
        venue = (row.get("venue") or "").strip()
        doi = normalize_doi(row.get("doi") or "")

        paper = {
            "id": (row.get("resource_id") or "").strip(),
            "openalex_id": (row.get("openalex_id") or "").strip(),
            "title": title,
            "abstract": "",
            "year": year,
            "doi": doi,
            "venue": venue,
            "type": "seed_record",
            "cited_by_count": int(row.get("citation_count") or 0) if str(row.get("citation_count") or "").isdigit() else 0,
            "authors": parse_authors(authors_text),
            "referenced_works": [],
            "citation_plain": citation_plain(title, authors_text, year, venue, doi),
            "citation_bibtex": citation_bibtex((row.get("resource_id") or "seed"), title, authors_text, year, venue, doi),
            "source_url": doi_to_url(doi),
            "scope": "seed",
            "status": (row.get("status") or "").strip(),
            "selection_tier": (row.get("selection_tier") or "").strip(),
            "topic_codes": topic_codes,
            "artifact_type": (row.get("content_type") or "AP").strip() or "AP",
            "topic_names": [topic_by_code[code].name for code in topic_codes if code in topic_by_code],
        }
        if paper["id"]:
            papers.append(paper)

    # De-duplicate by id while preserving first occurrence.
    by_id = {}
    for paper in papers:
        by_id.setdefault(paper["id"], paper)
    return list(by_id.values())


def build_hop_papers(topic_by_code: Dict[str, Topic], seed_topic_lookup: Dict[str, Set[str]]) -> List[Dict]:
    rows = load_jsonl(CORPUS_DIR / "expansion" / "candidates_cross_seed_ge2_kcore2_indegree2.jsonl")
    papers: List[Dict] = []
    for row in rows:
        topic_codes: Set[str] = set()
        for seed_id in row.get("origin_seed_ids", []) or []:
            topic_codes.update(seed_topic_lookup.get(seed_id, set()))

        mapped_topics = sorted(code for code in topic_codes if code in topic_by_code)
        if not mapped_topics:
            continue

        work_id = (row.get("work_id") or "").strip()
        if not work_id:
            continue

        doi = normalize_doi(row.get("doi") or "")
        title = (row.get("title") or "Untitled").strip()
        year = row.get("publication_year")
        venue = (row.get("host_venue") or "").strip()

        papers.append(
            {
                "id": work_id,
                "openalex_id": (row.get("openalex_id") or "").strip(),
                "title": title,
                "abstract": "",
                "year": year,
                "doi": doi,
                "venue": venue,
                "type": (row.get("type") or "article").strip() or "article",
                "cited_by_count": int(row.get("cited_by_count") or 0),
                "authors": [],
                "referenced_works": [],
                "citation_plain": citation_plain(title, "", year, venue, doi),
                "citation_bibtex": citation_bibtex(work_id, title, "", year, venue, doi),
                "source_url": doi_to_url(doi) or (row.get("openalex_id") or ""),
                "scope": "hop",
                "topic_codes": mapped_topics,
                "topic_names": [topic_by_code[code].name for code in mapped_topics],
                "artifact_type": "derived_one_hop",
                "cross_seed_score": int(row.get("cross_seed_score") or 0),
                "origin_seed_ids": row.get("origin_seed_ids", []),
                "edge_types": row.get("edge_types", []),
            }
        )

    by_id = {}
    for paper in papers:
        by_id.setdefault(paper["id"], paper)
    return list(by_id.values())


def build_resources(topic_by_code: Dict[str, Topic]) -> Tuple[Dict, List[Dict]]:
    rows = load_jsonl(CORPUS_DIR / "non_paper_resources.jsonl")

    items_by_topic: Dict[str, List[Dict]] = defaultdict(list)
    flat_rows: List[Dict] = []

    for row in rows:
        primary = (row.get("primary_topic") or "").strip()
        if primary not in topic_by_code:
            continue

        secondary = [code for code in listify(row.get("secondary_topics", [])) if code in topic_by_code]
        topic_codes = [primary, *[code for code in secondary if code != primary]]

        title = (row.get("name") or "Untitled").strip()
        item = {
            "resource_id": (row.get("resource_id") or "").strip(),
            "title": title,
            "url": normalize_url(row.get("url") or ""),
            "context": (row.get("description") or "").strip(),
            "topic_codes": topic_codes,
            "content_type": (row.get("content_type") or "").strip(),
            "status": (row.get("status") or "").strip(),
            "section": f"{primary} {topic_by_code[primary].name}",
        }
        items_by_topic[primary].append(item)
        flat_rows.append(item)

    sections = []
    for code, topic in topic_by_code.items():
        entries = items_by_topic.get(code, [])
        if not entries:
            continue
        sections.append({"section": f"{code} {topic.name}", "items": entries})

    payload = {
        "source_url": "corpus/non_paper_resources.jsonl",
        "section_count": len(sections),
        "item_count": len(flat_rows),
        "sections": sections,
    }
    return payload, flat_rows


def build_programs(non_paper_rows: List[Dict]) -> Dict:
    category_map = {
        "PC": "academic",
        "PP": "people",
        "CE": "events",
        "TP": "tools",
        "CO": "organizations",
        "GL": "grey_literature",
    }
    programs = []
    for row in non_paper_rows:
        if row.get("content_type") not in {"PC", "CO", "TP", "CE", "PP", "GL"}:
            continue
        programs.append(
            {
                "name": row.get("title", ""),
                "category": category_map.get(row.get("content_type"), "other"),
                "summary": row.get("context", ""),
                "links": [row.get("url")] if row.get("url") else [],
            }
        )

    return {"programs": programs, "adjacent_program_mentions": []}


def build_endnotes() -> Tuple[Dict, Dict]:
    notes = load_jsonl(CORPUS_DIR / "book_endnotes_unique.jsonl")

    raw_notes = []
    enriched_rows = []
    for row in notes:
        artifact_type = (row.get("reference_category") or "grey_like").strip() or "grey_like"
        raw_notes.append(
            {
                "id": row.get("reference_id"),
                "artifact_type": artifact_type,
                "raw_text": row.get("citation_text", ""),
                "doi": row.get("doi", ""),
                "urls": row.get("urls", []),
                "expansion_eligible": bool(row.get("expansion_eligible")),
            }
        )

        enriched_rows.append(
            {
                "id": row.get("reference_id"),
                "chapter": None,
                "matched": bool(row.get("expansion_eligible")),
                "work_id": "",
                "artifact_type": artifact_type,
            }
        )

    raw_payload = {"notes": raw_notes, "count": len(raw_notes)}
    enriched_payload = {"rows": enriched_rows, "count": len(enriched_rows)}
    return raw_payload, enriched_payload


def build_gaps() -> Dict:
    rows = load_json(CORPUS_DIR / "tables" / "gap_tracker.json")
    gaps = []
    for row in rows:
        gap_id = (row.get("gap_id") or "").strip()
        if not gap_id:
            continue
        gaps.append(
            {
                "id": gap_id.lower().replace("-", "_"),
                "label": f"{row.get('topic', '').strip()} {row.get('gap_description', '').strip()}".strip(),
                "detail": (row.get("recommended_action") or "").strip(),
                "evidence_links": [],
                "evidence": {
                    "topic": row.get("topic"),
                    "severity": row.get("severity"),
                    "status": row.get("status"),
                },
            }
        )
    return {"gaps": gaps}


def build_topic_payload(topics: List[Topic]) -> Dict:
    return {
        "count": len(topics),
        "topics": [
            {
                "topic_code": topic.code,
                "layer": topic.layer,
                "topic_name": topic.name,
                "why_it_matters": topic.why,
            }
            for topic in topics
        ],
    }


def build_graph(
    topics: List[Topic],
    seed_papers: List[Dict],
    hop_papers: List[Dict],
    resources_flat: List[Dict],
) -> Dict:
    nodes: List[Dict] = []
    edges: List[Dict] = []

    topic_codes = {topic.code for topic in topics}
    topic_index = {topic.code: topic for topic in topics}

    for topic in topics:
        nodes.append(
            {
                "id": topic.code,
                "label": f"{topic.code} {topic.name}",
                "type": "topic",
                "hop": 0,
                "topic_code": topic.code,
                "provenance": {
                    "layer": topic.layer,
                    "why_it_matters": topic.why,
                },
            }
        )

    for paper in seed_papers:
        nodes.append(
            {
                "id": paper["id"],
                "label": paper["title"],
                "type": "paper",
                "hop": 0,
                "topic_codes": paper.get("topic_codes", []),
                "provenance": {
                    "scope": "seed",
                    "selection_tier": paper.get("selection_tier"),
                    "artifact_type": paper.get("artifact_type"),
                },
            }
        )

    hop_by_id = {paper["id"]: paper for paper in hop_papers}
    for paper in hop_papers:
        nodes.append(
            {
                "id": paper["id"],
                "label": paper["title"],
                "type": "paper",
                "hop": 1,
                "topic_codes": paper.get("topic_codes", []),
                "provenance": {
                    "scope": "hop",
                    "cross_seed_score": paper.get("cross_seed_score"),
                    "artifact_type": paper.get("artifact_type"),
                },
            }
        )

    for resource in resources_flat:
        rid = resource.get("resource_id")
        if not rid:
            continue
        nodes.append(
            {
                "id": rid,
                "label": resource.get("title", "Resource"),
                "type": "resource",
                "hop": 0,
                "topic_codes": resource.get("topic_codes", []),
                "provenance": {
                    "content_type": resource.get("content_type"),
                    "status": resource.get("status"),
                },
            }
        )

    edge_seen: Set[Tuple[str, str, str]] = set()

    def add_edge(source: str, target: str, edge_type: str, provenance: Dict | None = None) -> None:
        if not source or not target or source == target:
            return
        key = (source, target, edge_type)
        if key in edge_seen:
            return
        edge_seen.add(key)
        edge = {"source": source, "target": target, "type": edge_type}
        if provenance:
            edge["provenance"] = provenance
        edges.append(edge)

    # Topic-to-topic relations from knowledge graph seeds.
    kg_rows = load_json(CORPUS_DIR / "tables" / "knowledge_graph_seeds.json")
    for row in kg_rows:
        if (row.get("node_type") or "") != "TOPIC":
            continue
        src = (row.get("node_id") or "").strip()
        dst = (row.get("edge_target") or "").strip()
        if src in topic_codes and dst in topic_codes:
            add_edge(src, dst, "prereq", {"edge_label": row.get("edge_label", "")})

    # Topic to papers.
    for paper in seed_papers + hop_papers:
        for code in paper.get("topic_codes", []):
            if code in topic_codes:
                add_edge(code, paper["id"], "contains")

    # Topic to resources.
    for resource in resources_flat:
        rid = resource.get("resource_id")
        for code in resource.get("topic_codes", []):
            if rid and code in topic_codes:
                add_edge(code, rid, "resource")

    # Seed to hop expansion edges (mapped through origin seed ids).
    for paper in hop_papers:
        for seed_id in paper.get("origin_seed_ids", []) or []:
            if not seed_id.startswith("WORKBOOK-LE-T1-"):
                continue
            seed_paper_id = seed_id.replace("WORKBOOK-", "", 1)
            add_edge(seed_paper_id, paper["id"], "expands_to")

    return {"nodes": nodes, "edges": edges}


def build_summary(
    seed_papers: List[Dict],
    hop_papers: List[Dict],
    resources_flat: List[Dict],
    graph: Dict,
    endnotes_raw: Dict,
    openalex_enrichment: Dict,
) -> Dict:
    seed_resolution = load_jsonl(CORPUS_DIR / "expansion" / "seed_resolutions.jsonl")
    matched_endnotes = sum(
        1
        for row in seed_resolution
        if row.get("seed_kind") == "book_endnote_reference" and bool(row.get("matched"))
    )

    return {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "parsed_endnotes": endnotes_raw.get("count", 0),
        "matched_endnotes": matched_endnotes,
        "seed_papers": len(seed_papers),
        "one_hop_papers": len(hop_papers),
        "icicle_resource_items": len(resources_flat),
        "graph_nodes": len(graph.get("nodes", [])),
        "graph_edges": len(graph.get("edges", [])),
        "openalex_papers_total": openalex_enrichment.get("papers_total", 0),
        "openalex_matches": openalex_enrichment.get("papers_with_openalex_match", 0),
        "openalex_abstracts_filled": openalex_enrichment.get("abstracts_filled", 0),
        "papers_missing_abstract": openalex_enrichment.get("papers_missing_abstract", 0),
    }


def build_extra_docs() -> Dict:
    return {
        "count": 2,
        "documents": [
            {
                "source_type": "methodology",
                "title": "Corpus Construction Methodology (April 2026)",
                "url": "",
                "file_path": str(CORPUS_DIR / "methodology.md"),
                "summary": "Methodological framework for seed expansion, cross-seed filtering, subdomain scoring, and manual quality controls.",
            },
            {
                "source_type": "specification",
                "title": "Learning Engineering Corpus Specification Workbook v1",
                "url": "",
                "file_path": str(ROOT / "le_corpus_specification_v1.xlsx"),
                "summary": "Canonical topic map, registries, metadata schema, gaps, and selection pipeline for this corpus.",
            },
        ],
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    topics, topic_by_code = load_topics()
    seed_topic_lookup = build_seed_topic_lookup(topic_by_code)

    seed_papers = build_seed_papers(topic_by_code)
    hop_papers = build_hop_papers(topic_by_code, seed_topic_lookup)
    openalex_enrichment = enrich_papers_with_openalex(seed_papers, hop_papers)

    resources_payload, resources_flat = build_resources(topic_by_code)
    programs_payload = build_programs(resources_flat)
    endnotes_raw, endnotes_enriched = build_endnotes()
    gaps_payload = build_gaps()
    topic_payload = build_topic_payload(topics)

    graph_payload = build_graph(topics, seed_papers, hop_papers, resources_flat)
    summary_payload = build_summary(
        seed_papers,
        hop_papers,
        resources_flat,
        graph_payload,
        endnotes_raw,
        openalex_enrichment,
    )
    extra_docs_payload = build_extra_docs()

    write_json(DATA_DIR / "build_summary.json", summary_payload)
    write_json(DATA_DIR / "graph.json", graph_payload)
    write_json(DATA_DIR / "icicle_resources.json", resources_payload)
    write_json(DATA_DIR / "papers_seed.json", {"papers": seed_papers})
    write_json(DATA_DIR / "papers_one_hop.json", {"papers": hop_papers})
    write_json(DATA_DIR / "endnotes_raw.json", endnotes_raw)
    write_json(DATA_DIR / "endnotes_enriched.json", endnotes_enriched)
    write_json(DATA_DIR / "programs_summary.json", programs_payload)
    write_json(DATA_DIR / "gaps.json", gaps_payload)
    write_json(DATA_DIR / "extra_docs.json", extra_docs_payload)
    write_json(DATA_DIR / "topic_map.json", topic_payload)

    print(json.dumps(summary_payload, indent=2))


if __name__ == "__main__":
    main()
