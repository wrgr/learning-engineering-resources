#!/usr/bin/env python3
"""Build a normalized corpus package from the LE workbook + methodology markdown."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
import xml.etree.ElementTree as ET

NS_MAIN = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"pr": "http://schemas.openxmlformats.org/package/2006/relationships"}

DEFAULT_BOOK_PDFS = [
    "/Users/wgray13/Desktop/Learning Engineering Toolkit_26_04_07_15_45_22A.pdf",
    "/Users/wgray13/Downloads/Learning Engineering Toolkit_26_04_07_15_45_22.pdf",
]

TABLE_CONFIG = {
    "Topic Map": {
        "header_row": 3,
        "required_field": "topic_code",
        "required_pattern": r"^T\d{2}$",
        "slug": "topic_map",
    },
    "Content Type Taxonomy": {
        "header_row": 2,
        "required_field": "content_type",
        "slug": "content_type_taxonomy",
    },
    "Programs & People Registry": {
        "header_row": 3,
        "required_field": "resource_id",
        "slug": "programs_people_registry",
    },
    "Corpus Registry": {
        "header_row": 3,
        "required_field": "corpus_id",
        "slug": "corpus_registry",
    },
    "Knowledge Graph Seeds": {
        "header_row": 3,
        "required_field": "node_type",
        "slug": "knowledge_graph_seeds",
    },
    "Learning Journeys": {
        "header_row": 3,
        "required_field": "journey_id",
        "slug": "learning_journeys",
    },
    "Selection Pipeline": {
        "header_row": 2,
        "required_field": "step",
        "slug": "selection_pipeline",
    },
    "Gap Tracker": {"header_row": 3, "required_field": "gap_id", "slug": "gap_tracker"},
    "Expansion Sources": {
        "header_row": 3,
        "required_field": "source_id",
        "slug": "expansion_sources",
    },
    "Metadata Schema": {
        "header_row": 2,
        "required_field": "field_name",
        "slug": "metadata_schema",
    },
    "Update Log": {"header_row": 2, "required_field": "date", "slug": "update_log"},
}


def normalize_header(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return slug.strip("_")


def split_topics(value: str) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_number(value: str):
    value = value.strip()
    if not value:
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


@dataclass
class Workbook:
    shared_strings: List[str]
    sheet_targets: Dict[str, str]
    archive: zipfile.ZipFile

    @classmethod
    def load(cls, path: Path) -> "Workbook":
        archive = zipfile.ZipFile(path)
        workbook_xml = ET.fromstring(archive.read("xl/workbook.xml"))
        rels_xml = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        shared_xml = ET.fromstring(archive.read("xl/sharedStrings.xml"))

        shared_strings = [
            "".join(node.text or "" for node in item.findall(".//m:t", NS_MAIN))
            for item in shared_xml.findall("m:si", NS_MAIN)
        ]
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels_xml.findall("pr:Relationship", NS_REL)
        }
        sheet_targets: Dict[str, str] = {}
        for sheet in workbook_xml.findall("m:sheets/m:sheet", NS_MAIN):
            name = sheet.attrib["name"]
            rid = sheet.attrib[
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            ]
            sheet_targets[name] = rel_map[rid]
        return cls(shared_strings=shared_strings, sheet_targets=sheet_targets, archive=archive)

    def read_sheet_rows(self, sheet_name: str) -> List[List[str]]:
        target = self.sheet_targets[sheet_name]
        root = ET.fromstring(self.archive.read(f"xl/{target}"))
        rows: List[List[str]] = []
        for row in root.findall("m:sheetData/m:row", NS_MAIN):
            cells: Dict[int, str] = {}
            for cell in row.findall("m:c", NS_MAIN):
                ref = cell.attrib.get("r", "")
                match = re.match(r"([A-Z]+)\d+", ref)
                if not match:
                    continue
                idx = col_to_index(match.group(1))
                cells[idx] = parse_cell_value(cell, self.shared_strings)
            if cells:
                width = max(cells.keys()) + 1
                ordered = [""] * width
                for i, value in cells.items():
                    ordered[i] = value
                rows.append(ordered)
            else:
                rows.append([])
        return rows


def col_to_index(col: str) -> int:
    value = 0
    for ch in col:
        value = value * 26 + ord(ch) - 64
    return value - 1


def parse_cell_value(cell: ET.Element, shared_strings: List[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        node = cell.find("m:is/m:t", NS_MAIN)
        return (node.text or "") if node is not None else ""
    node = cell.find("m:v", NS_MAIN)
    if node is None or node.text is None:
        return ""
    if cell_type == "s":
        return shared_strings[int(node.text)]
    return node.text


def to_records(
    rows: List[List[str]],
    header_row: int,
    required_field: str,
    required_pattern: str | None = None,
) -> List[Dict[str, str]]:
    header_idx = header_row - 1
    if header_idx >= len(rows):
        return []
    raw_header = rows[header_idx]
    header = [normalize_header(col) for col in raw_header]
    required_key = normalize_header(required_field)

    records: List[Dict[str, str]] = []
    for row in rows[header_idx + 1 :]:
        if not row or not any(cell.strip() for cell in row):
            continue
        record: Dict[str, str] = {}
        for idx, key in enumerate(header):
            if not key:
                continue
            record[key] = row[idx].strip() if idx < len(row) else ""
        required_value = record.get(required_key, "")
        if not required_value:
            continue
        if required_pattern and not re.fullmatch(required_pattern, required_value):
            continue
        records.append(record)
    return records


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: List[Dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=True) + "\n")


def build_unified_records(
    corpus_registry: List[Dict[str, str]], programs_people_registry: List[Dict[str, str]]
) -> Dict[str, List[Dict]]:
    academic_records = []
    for row in corpus_registry:
        record = {
            "resource_id": row.get("corpus_id", ""),
            "record_type": "academic_paper",
            "status": row.get("status", ""),
            "selection_tier": row.get("selection_tier", ""),
            "title": row.get("title", ""),
            "authors": row.get("authors", ""),
            "year": parse_number(row.get("year", "")) if row.get("year") else None,
            "venue": row.get("venue", ""),
            "doi": row.get("doi", ""),
            "primary_topic": row.get("primary_topic", ""),
            "secondary_topics": split_topics(row.get("secondary_topics", "")),
            "topic_justification": row.get("topic_justification", ""),
            "content_type": row.get("content_type", ""),
            "evidence_type": row.get("evidence_type", ""),
            "recency_flag": row.get("recency_flag", ""),
            "cross_seed_score": parse_number(row.get("cross_seed_score", "")),
            "subdomain_score": parse_number(row.get("subdomain_score", "")),
            "citation_count": parse_number(row.get("citation_count", "")),
            "citation_velocity_2yr": parse_number(row.get("citation_velocity_2yr", "")),
            "openalex_id": row.get("openalex_id", ""),
            "selection_source": row.get("selection_source", ""),
            "reviewed_by": row.get("reviewed_by", ""),
            "date_reviewed": row.get("date_reviewed", ""),
            "notes": row.get("notes", ""),
            "ieee_icicle_listed": row.get("ieee_icicle_listed", ""),
        }
        academic_records.append(record)

    non_paper_records = []
    for row in programs_people_registry:
        record = {
            "resource_id": row.get("resource_id", ""),
            "record_type": "non_paper_resource",
            "status": row.get("status", ""),
            "content_type": row.get("content_type", ""),
            "name": row.get("name", ""),
            "affiliation_or_venue": row.get("affiliation_or_venue", ""),
            "url": row.get("url", ""),
            "primary_topic": row.get("primary_topic", ""),
            "secondary_topics": split_topics(row.get("secondary_topics", "")),
            "description": row.get("description", ""),
            "notes": row.get("notes", ""),
            "selection_tier": row.get("selection_tier", ""),
            "selection_source": row.get("selection_source", ""),
            "ieee_icicle_listed": row.get("ieee_icicle_listed", ""),
            "reviewed_by": row.get("reviewed_by", ""),
            "date_reviewed": row.get("date_reviewed", ""),
        }
        non_paper_records.append(record)

    unified = sorted(
        [*academic_records, *non_paper_records], key=lambda rec: rec.get("resource_id", "")
    )
    return {
        "academic_records": academic_records,
        "non_paper_records": non_paper_records,
        "unified_records": unified,
    }


def status_breakdown(records: List[Dict], key: str = "status") -> Dict[str, int]:
    counter = Counter(rec.get(key, "") for rec in records)
    return dict(sorted(counter.items(), key=lambda kv: kv[0]))


def clean_citation_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    value = value.replace(" .", ".").replace(" ,", ",").replace(" ;", ";")
    return value


def extract_urls(value: str) -> List[str]:
    normalized = re.sub(r"www\.\s+", "www.", value, flags=re.IGNORECASE)
    normalized = re.sub(r"https?://\s+", lambda m: m.group(0).replace(" ", ""), normalized)
    urls = re.findall(r"(https?://\S+|www\.\S+)", normalized, flags=re.IGNORECASE)
    cleaned = []
    for url in urls:
        cleaned.append(url.rstrip(".,);"))
    return sorted(set(cleaned))


def extract_doi(value: str) -> str:
    match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", value)
    return match.group(0) if match else ""


def extract_year(value: str):
    match = re.search(r"\b(19|20)\d{2}\b", value)
    if not match:
        return None
    return int(match.group(0))


def is_likely_reference(value: str) -> bool:
    has_url = bool(re.search(r"(https?://|www\.)", value, flags=re.IGNORECASE))
    has_year = bool(re.search(r"\b(19|20)\d{2}\b", value))
    has_source_term = bool(
        re.search(
            r"\b(journal|press|proceedings|conference|review|doi|university|report|blog|standard|guideline|handbook|encyclopedia|book|lecture notes)\b",
            value,
            flags=re.IGNORECASE,
        )
    )
    has_author_like_prefix = bool(re.match(r"^[A-Z][A-Za-z'\-]+,", value))
    return has_url or (has_year and (has_source_term or has_author_like_prefix))


def infer_reference_category(value: str) -> str:
    if re.search(
        r"\b(conference|proceedings|symposium|workshop|hcii|aied|edm|learning@scale|lak)\b",
        value,
        flags=re.IGNORECASE,
    ):
        return "conference_like"
    if extract_doi(value):
        return "paper_like"
    if re.search(
        r"\b(journal|proceedings|conference|arxiv|review|vol\.|no\.)\b",
        value,
        flags=re.IGNORECASE,
    ):
        return "paper_like"
    if re.search(
        r"\b(press|routledge|wiley|springer|pearson|harper|cambridge|oxford|book|edition|ed\.)\b",
        value,
        flags=re.IGNORECASE,
    ):
        return "book_like"
    if re.search(
        r"\b(standard|guideline|government|report|association|institute|initiative|unesco|ieee)\b",
        value,
        flags=re.IGNORECASE,
    ):
        return "report_or_standard_like"
    if re.search(
        r"\b(blog|wikipedia|government|association|institute|guidance|code of ethics|standard|report|white paper|toolkit)\b",
        value,
        flags=re.IGNORECASE,
    ):
        return "grey_like"
    if re.search(r"(https?://|www\.)", value, flags=re.IGNORECASE):
        return "grey_like"
    return "unknown"


def normalize_for_dedupe(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def evaluate_expansion_eligibility(text: str):
    normalized = text.strip()
    lowered = normalized.lower()

    if re.match(r"^\(\d{4}\)", normalized):
        return False, "malformed_fragment"

    if "informed by:" in lowered:
        return False, "aggregated_note"

    if re.search(r"\b(comments made during meeting|personal communication|conversation with)\b", lowered):
        return False, "non_document_source"

    has_url_or_doi = bool(extract_doi(normalized) or extract_urls(normalized))
    if has_url_or_doi:
        return True, "has_url_or_doi"

    if not re.search(r"\b(19|20)\d{2}\b", normalized):
        return False, "missing_year"

    has_doc_markers = bool(
        re.search(
            r"\b(journal|proceedings|conference|press|report|guideline|standard|book|vol\.|no\.|edition|ed\.|university|publisher|routledge|wiley|springer|pearson|harper|cambridge|oxford)\b",
            normalized,
            flags=re.IGNORECASE,
        )
    )
    if has_doc_markers:
        return True, "bibliographic_markers"

    has_author_pattern = bool(re.match(r"^[A-Z][A-Za-z'`\-]+,", normalized))
    if has_author_pattern and len(normalized) >= 50:
        return True, "author_year_pattern"

    return False, "insufficient_bibliographic_signal"


def is_page_header_or_noise(line: str) -> bool:
    if not line:
        return True
    if "Learning Engineering Toolkit" in line:
        return True
    if re.search(r"\|\s*\d+$", line):
        return True
    if line in {"KEY POINTS"}:
        return True
    return False


def should_stop_endnotes_section(line: str, has_collected_any: bool) -> bool:
    if not has_collected_any:
        return False
    if re.match(r"^(CHAPTER|Chapter)\s+\d+\b", line):
        return True
    if line.lower().startswith("about the authors"):
        return True
    if line in {
        "FOUNDATIONS",
        "PRACTICE",
        "CONTEXT",
        "APPENDIX",
        "ACKNOWLEDGMENTS",
        "INDEX",
        "TABLE OF CONTENTS",
    }:
        return True
    return False


def _finalize_endnote_reference(
    source_pdf: Path, section_index: int, note_number: int, lines: List[str]
):
    text = clean_citation_text(" ".join(lines))
    if len(text) < 20:
        return None
    if not is_likely_reference(text):
        return None
    return {
        "source_pdf": str(source_pdf),
        "section_index": section_index,
        "note_number": note_number,
        "citation_text": text,
        "doi": extract_doi(text),
        "urls": extract_urls(text),
        "year": extract_year(text),
        "reference_category": infer_reference_category(text),
    }


def extract_endnote_references_from_pdf(source_pdf: Path) -> List[Dict]:
    text = subprocess.check_output(["pdftotext", str(source_pdf), "-"]).decode(
        "utf-8", errors="ignore"
    )
    lines = [line.replace("\x0c", "").strip() for line in text.splitlines()]
    endnote_indices = [idx for idx, line in enumerate(lines) if line.lower() == "endnotes"]
    if not endnote_indices:
        return []

    records: List[Dict] = []
    for section_idx, start_idx in enumerate(endnote_indices, start=1):
        next_idx = endnote_indices[section_idx] if section_idx < len(endnote_indices) else len(lines)
        block = lines[start_idx + 1 : next_idx]

        pending_number = None
        current_number = None
        current_lines: List[str] = []
        nonref_streak = 0
        collected_in_section = 0

        for line in block:
            if should_stop_endnotes_section(line, has_collected_any=collected_in_section > 0):
                break

            if is_page_header_or_noise(line):
                if current_number is None:
                    nonref_streak += 1
                    if collected_in_section > 0 and nonref_streak > 80:
                        break
                continue

            full_start = re.match(r"^(\d{1,3})\s+(.+)$", line)
            number_only = re.match(r"^(\d{1,3})$", line)

            if full_start:
                if current_number is not None:
                    finalized = _finalize_endnote_reference(
                        source_pdf, section_idx, current_number, current_lines
                    )
                    if finalized:
                        records.append(finalized)
                        collected_in_section += 1
                current_number = int(full_start.group(1))
                current_lines = [full_start.group(2)]
                pending_number = None
                nonref_streak = 0
                continue

            if number_only:
                if current_number is not None:
                    finalized = _finalize_endnote_reference(
                        source_pdf, section_idx, current_number, current_lines
                    )
                    if finalized:
                        records.append(finalized)
                        collected_in_section += 1
                current_number = None
                current_lines = []
                pending_number = int(number_only.group(1))
                nonref_streak = 0
                continue

            if pending_number is not None:
                current_number = pending_number
                current_lines = [line]
                pending_number = None
                nonref_streak = 0
                continue

            if current_number is not None:
                current_lines.append(line)
                nonref_streak = 0
                continue

            nonref_streak += 1
            if collected_in_section > 0 and nonref_streak > 40:
                break

        if current_number is not None:
            finalized = _finalize_endnote_reference(
                source_pdf, section_idx, current_number, current_lines
            )
            if finalized:
                records.append(finalized)

    return records


def dedupe_endnote_references(raw_records: List[Dict]) -> List[Dict]:
    by_key: Dict[str, Dict] = {}
    for record in raw_records:
        key = normalize_for_dedupe(record["citation_text"])
        if not key:
            continue
        occurrence = {
            "source_pdf": record["source_pdf"],
            "section_index": record["section_index"],
            "note_number": record["note_number"],
        }
        if key not in by_key:
            by_key[key] = {
                "citation_text": record["citation_text"],
                "doi": record["doi"],
                "urls": list(record["urls"]),
                "year": record["year"],
                "reference_category": record["reference_category"],
                "source_occurrences": [occurrence],
            }
            continue

        existing = by_key[key]
        existing["source_occurrences"].append(occurrence)
        existing["urls"] = sorted(set(existing["urls"] + record["urls"]))
        if not existing["doi"] and record["doi"]:
            existing["doi"] = record["doi"]
        if existing["reference_category"] == "unknown" and record["reference_category"] != "unknown":
            existing["reference_category"] = record["reference_category"]
        if existing["year"] is None and record["year"] is not None:
            existing["year"] = record["year"]

    deduped = sorted(by_key.values(), key=lambda rec: rec["citation_text"].lower())
    for idx, record in enumerate(deduped, start=1):
        record["reference_id"] = f"LE-ENDNOTE-{idx:04d}"
        record["source_pdf_count"] = len({occ["source_pdf"] for occ in record["source_occurrences"]})
        eligible, reason = evaluate_expansion_eligibility(record["citation_text"])
        record["expansion_eligible"] = eligible
        record["expansion_eligibility_reason"] = reason
    return deduped


def build_expansion_seed_queries(
    workbook_expansion_sources: List[Dict[str, str]],
    corpus_registry: List[Dict[str, str]],
    endnote_references: List[Dict],
) -> List[Dict]:
    seeds: List[Dict] = []
    corpus_by_id = {row.get("corpus_id", ""): row for row in corpus_registry}

    for row in workbook_expansion_sources:
        source_id = row.get("source_id", "")
        if not source_id:
            continue

        title = row.get("title", "")
        authors = row.get("authors", "")
        year = row.get("year", "")
        doi = row.get("doi", "")
        if title == "(see Corpus Registry)" or not title:
            corpus_row = corpus_by_id.get(source_id, {})
            title = corpus_row.get("title", title)
            authors = corpus_row.get("authors", authors)
            year = corpus_row.get("year", year)
            doi = corpus_row.get("doi", doi)

        query_parts = [title, authors, year, doi]
        query_text = " ".join(part.strip() for part in query_parts if part and part.strip())
        if not query_text:
            continue
        seeds.append(
            {
                "seed_id": f"WORKBOOK-{source_id}",
                "seed_kind": "workbook_expansion_source",
                "reference_category": "workbook_anchor",
                "query_text": query_text,
                "title": title,
                "authors": authors,
                "year": parse_number(year) if year else None,
                "doi": doi,
                "source_sheet": "Expansion Sources",
            }
        )

    for row in endnote_references:
        if not row.get("expansion_eligible", False):
            continue
        seeds.append(
            {
                "seed_id": row["reference_id"],
                "seed_kind": "book_endnote_reference",
                "reference_category": row["reference_category"],
                "query_text": row["citation_text"],
                "title": "",
                "authors": "",
                "year": row["year"],
                "doi": row["doi"],
                "expansion_eligibility_reason": row.get("expansion_eligibility_reason", ""),
                "source_sheet": "Learning Engineering Toolkit Endnotes",
            }
        )

    return seeds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workbook",
        default="le_corpus_specification_v1.xlsx",
        help="Path to corpus specification workbook",
    )
    parser.add_argument(
        "--methodology",
        default="corpus_construction_methodology_generic.md",
        help="Path to methodology markdown",
    )
    parser.add_argument(
        "--book-pdf",
        action="append",
        default=[],
        help="Path to a Learning Engineering Toolkit PDF (repeat for multiple files)",
    )
    parser.add_argument("--output-dir", default="corpus", help="Output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workbook_path = Path(args.workbook)
    methodology_path = Path(args.methodology)
    requested_book_pdfs = [Path(item).expanduser() for item in args.book_pdf]
    if not requested_book_pdfs:
        requested_book_pdfs = [
            Path(candidate).expanduser()
            for candidate in DEFAULT_BOOK_PDFS
            if Path(candidate).expanduser().exists()
        ]
    output_dir = Path(args.output_dir)
    tables_dir = output_dir / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    wb = Workbook.load(workbook_path)
    extracted_tables: Dict[str, List[Dict[str, str]]] = {}
    for sheet_name, config in TABLE_CONFIG.items():
        rows = wb.read_sheet_rows(sheet_name)
        records = to_records(
            rows=rows,
            header_row=config["header_row"],
            required_field=config["required_field"],
            required_pattern=config.get("required_pattern"),
        )
        extracted_tables[sheet_name] = records
        write_json(tables_dir / f"{config['slug']}.json", records)

    unified_payload = build_unified_records(
        corpus_registry=extracted_tables["Corpus Registry"],
        programs_people_registry=extracted_tables["Programs & People Registry"],
    )
    write_jsonl(output_dir / "academic_papers.jsonl", unified_payload["academic_records"])
    write_jsonl(output_dir / "non_paper_resources.jsonl", unified_payload["non_paper_records"])
    write_jsonl(output_dir / "records.jsonl", unified_payload["unified_records"])

    methodology_text = methodology_path.read_text(encoding="utf-8")
    (output_dir / "methodology.md").write_text(methodology_text, encoding="utf-8")

    missing_book_pdfs = [str(path) for path in requested_book_pdfs if not path.exists()]
    usable_book_pdfs = [path for path in requested_book_pdfs if path.exists()]
    endnote_raw_records: List[Dict] = []
    for pdf_path in usable_book_pdfs:
        endnote_raw_records.extend(extract_endnote_references_from_pdf(pdf_path))
    endnote_unique_records = dedupe_endnote_references(endnote_raw_records)
    endnote_eligible_records = [rec for rec in endnote_unique_records if rec.get("expansion_eligible")]
    endnote_excluded_records = [rec for rec in endnote_unique_records if not rec.get("expansion_eligible")]

    if endnote_raw_records:
        write_jsonl(output_dir / "book_endnotes_raw.jsonl", endnote_raw_records)
    if endnote_unique_records:
        write_jsonl(output_dir / "book_endnotes_unique.jsonl", endnote_unique_records)
    if endnote_eligible_records:
        write_jsonl(output_dir / "book_endnotes_expansion_eligible.jsonl", endnote_eligible_records)
    if endnote_excluded_records:
        write_jsonl(output_dir / "book_endnotes_expansion_excluded.jsonl", endnote_excluded_records)

    expansion_seed_queries = build_expansion_seed_queries(
        workbook_expansion_sources=extracted_tables["Expansion Sources"],
        corpus_registry=extracted_tables["Corpus Registry"],
        endnote_references=endnote_unique_records,
    )
    write_jsonl(output_dir / "expansion_seed_queries.jsonl", expansion_seed_queries)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_files": {
            "workbook": str(workbook_path),
            "methodology": str(methodology_path),
            "book_pdfs_used": [str(path) for path in usable_book_pdfs],
            "book_pdfs_missing": missing_book_pdfs,
        },
        "counts": {
            "total_records": len(unified_payload["unified_records"]),
            "academic_records": len(unified_payload["academic_records"]),
            "non_paper_records": len(unified_payload["non_paper_records"]),
            "topics": len(extracted_tables["Topic Map"]),
            "expansion_sources": len(extracted_tables["Expansion Sources"]),
            "book_endnote_references_raw": len(endnote_raw_records),
            "book_endnote_references_unique": len(endnote_unique_records),
            "book_endnote_references_expansion_eligible": len(endnote_eligible_records),
            "book_endnote_references_expansion_excluded": len(endnote_excluded_records),
            "book_endnote_references_paper_like": sum(
                1 for rec in endnote_unique_records if rec["reference_category"] == "paper_like"
            ),
            "book_endnote_references_conference_like": sum(
                1 for rec in endnote_unique_records if rec["reference_category"] == "conference_like"
            ),
            "book_endnote_references_book_like": sum(
                1 for rec in endnote_unique_records if rec["reference_category"] == "book_like"
            ),
            "book_endnote_references_grey_like": sum(
                1 for rec in endnote_unique_records if rec["reference_category"] == "grey_like"
            ),
            "expansion_seed_queries_total": len(expansion_seed_queries),
            "gaps": len(extracted_tables["Gap Tracker"]),
            "learning_journeys": len(extracted_tables["Learning Journeys"]),
        },
        "status_breakdown": {
            "academic": status_breakdown(unified_payload["academic_records"]),
            "non_paper": status_breakdown(unified_payload["non_paper_records"]),
            "overall": status_breakdown(unified_payload["unified_records"]),
        },
        "topic_breakdown": {
            "academic_primary_topic": dict(
                sorted(
                    Counter(
                        rec.get("primary_topic", "")
                        for rec in unified_payload["academic_records"]
                        if rec.get("primary_topic")
                    ).items(),
                    key=lambda kv: kv[0],
                )
            ),
            "non_paper_primary_topic": dict(
                sorted(
                    Counter(
                        rec.get("primary_topic", "")
                        for rec in unified_payload["non_paper_records"]
                        if rec.get("primary_topic")
                    ).items(),
                    key=lambda kv: kv[0],
                )
            ),
        },
        "outputs": {
            "records": "records.jsonl",
            "academic": "academic_papers.jsonl",
            "non_paper": "non_paper_resources.jsonl",
            "expansion_seed_queries": "expansion_seed_queries.jsonl",
            "book_endnotes_raw": "book_endnotes_raw.jsonl",
            "book_endnotes_unique": "book_endnotes_unique.jsonl",
            "book_endnotes_expansion_eligible": "book_endnotes_expansion_eligible.jsonl",
            "book_endnotes_expansion_excluded": "book_endnotes_expansion_excluded.jsonl",
            "tables_dir": "tables",
            "methodology_copy": "methodology.md",
        },
    }
    write_json(output_dir / "manifest.json", manifest)
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
