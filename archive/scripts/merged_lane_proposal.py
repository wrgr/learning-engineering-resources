"""Propose merged-lane OpenAlex work rows from `programs_people_registry` people (PP) via citation-sorted works."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from openalex_client import api_get_json
from utils import ROOT, load_dotenv_optional, load_json, to_work_id, write_json

CORPUS_MERGED = ROOT / "corpus" / "merged_lane"
INCLUSION_PATH = CORPUS_MERGED / "proposal_inclusion.json"
REGISTRY_PATH = ROOT / "corpus" / "tables" / "programs_people_registry.json"
DEFAULT_OUT = CORPUS_MERGED / "proposed_lane_additions.json"
OVERRIDES_PATH = CORPUS_MERGED / "openalex_author_overrides.json"

_TOPIC_RE = re.compile(r"T\d{2}")


def load_inclusion_defaults(path: Path = INCLUSION_PATH) -> Dict[str, int]:
    """Load permissive defaults from `proposal_inclusion.json`; fall back if missing or partial."""
    base = {"min_citations": 5, "per_person": 25, "year_min": 1990, "year_max": 2026, "max_pages": 8}
    if not path.is_file():
        return base
    raw = load_json(path)
    if not isinstance(raw, dict):
        return base
    for key in base:
        val = raw.get(key)
        if isinstance(val, int) and val >= 0:
            base[key] = val
    return base


def strict_inclusion_defaults() -> Dict[str, int]:
    """Tighter thresholds (legacy behavior) when `--strict` is set."""
    return {"min_citations": 25, "per_person": 12, "year_min": 2005, "year_max": 2026, "max_pages": 4}


def topic_codes_from_registry_row(row: Dict[str, Any]) -> List[str]:
    """Return ordered unique topic codes from a registry row's primary and secondary topic fields."""
    raw = f"{row.get('primary_topic', '')} {row.get('secondary_topics', '')}"
    seen: Set[str] = set()
    out: List[str] = []
    for m in _TOPIC_RE.finditer(raw):
        code = m.group(0)
        if code not in seen:
            seen.add(code)
            out.append(code)
    if not out:
        out.append("T00")
    return out


def collect_excluded_work_ids(repo_root: Path) -> Set[str]:
    """Work IDs already covered by seed, hop, merged lane, or existing lane specs (dedupe targets)."""
    data = repo_root / "data"
    merged = data / "merged" / "papers_merged_lane.json"
    ex: Set[str] = set()
    for rel in ("papers_seed.json", "papers_one_hop.json"):
        p = data / rel
        if not p.is_file():
            continue
        payload = load_json(p)
        for paper in payload.get("papers") or []:
            oid = (paper.get("openalex_id") or "").strip()
            if oid:
                ex.add(to_work_id(oid))
    if merged.is_file():
        payload = load_json(merged)
        for paper in payload.get("papers") or []:
            oid = (paper.get("openalex_id") or paper.get("id") or "").strip()
            if oid:
                ex.add(to_work_id(oid))
    lane_specs = repo_root / "corpus" / "merged_lane" / "lane_work_specs.json"
    if lane_specs.is_file():
        for row in load_json(lane_specs):
            wid = (row.get("work_id") or "").strip()
            if wid:
                ex.add(wid)
    return ex


def _name_similarity(a: str, b: str) -> float:
    """Return 0–1 fuzzy match score for two display names."""
    x = (a or "").strip().lower()
    y = (b or "").strip().lower()
    if not x or not y:
        return 0.0
    return SequenceMatcher(None, x, y).ratio()


def resolve_openalex_author_id(
    registry_name: str, affiliation_hint: str, overrides: Dict[str, str], resource_id: str
) -> Tuple[Optional[str], float, List[Dict[str, Any]]]:
    """Pick an OpenAlex author id for this registry person; return (author_id, score, raw_candidates)."""
    if resource_id in overrides:
        aid = overrides[resource_id].strip()
        if aid.startswith("http"):
            aid = aid.rstrip("/").split("/")[-1]
        return (aid if aid.startswith("A") else None, 1.0, [])

    data = api_get_json(
        "/authors",
        {
            "search": registry_name.strip(),
            "per-page": "15",
            "select": "id,display_name,works_count,last_known_institutions",
        },
    )
    results = data.get("results") or []
    if not results:
        return (None, 0.0, [])

    best: Optional[Dict[str, Any]] = None
    best_score = 0.0
    for cand in results:
        dn = (cand.get("display_name") or "").strip()
        score = _name_similarity(registry_name, dn)
        inst_blob = ""
        for inst in cand.get("last_known_institutions") or []:
            inst_blob += " " + (inst.get("display_name") or "")
        if affiliation_hint and len(affiliation_hint) > 4:
            aff = affiliation_hint.lower()
            inst_lower = inst_blob.lower()
            if aff[:18] in inst_lower or aff.split(",")[0].strip()[:14] in inst_lower:
                score += 0.08
        wc = int(cand.get("works_count") or 0)
        if wc > 200:
            score += 0.02
        if score > best_score:
            best_score = score
            best = cand

    if best is None:
        return (None, 0.0, results)
    raw_id = (best.get("id") or "").strip()
    author_id = to_work_id(raw_id) if raw_id else ""
    if not author_id.startswith("A"):
        return (None, best_score, results)
    return (author_id, min(best_score, 1.0), results)


def fetch_top_works_for_author(
    author_id: str, per_page: int, max_pages: int, min_citations: int, year_min: int, year_max: int
) -> List[Dict[str, Any]]:
    """Return OpenAlex work objects for an author, sorted by citations (API-side sort)."""
    # Omit `type` in the filter string (OpenAlex OR-syntax varies); filter document types in Python below.
    flt = f"authorships.author.id:{author_id},is_paratext:false,publication_year:{year_min}-{year_max}"
    out: List[Dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        data = api_get_json(
            "/works",
            {
                "filter": flt,
                "sort": "cited_by_count:desc",
                "per-page": str(min(per_page, 200)),
                "page": str(page),
                "select": "id,display_name,publication_year,cited_by_count,type",
            },
        )
        batch = data.get("results") or []
        if not batch:
            break
        for w in batch:
            wtype = (w.get("type") or "").strip().lower()
            if wtype not in {"article", "review", "book", "book chapter"}:
                continue
            cites = int(w.get("cited_by_count") or 0)
            if cites >= min_citations:
                out.append(w)
    return out


def build_lane_row_for_work(
    work: Dict[str, Any],
    resource_id: str,
    topic_codes: List[str],
    corpus_tier: str,
    source_lane_prefix: str,
) -> Dict[str, Any]:
    """Shape one proposed lane row plus audit fields under `_proposal_audit`."""
    wid = to_work_id((work.get("id") or "").strip())
    row: Dict[str, Any] = {
        "work_id": wid,
        "topic_codes": list(topic_codes),
        "corpus_tier": corpus_tier if corpus_tier in ("core", "expanded") else "expanded",
        "source_lane": f"{source_lane_prefix}:{resource_id}",
        "source_expansion": "person",
        "registry_person_id": resource_id,
        "_proposal_audit": {
            "title": (work.get("display_name") or "").strip(),
            "publication_year": work.get("publication_year"),
            "cited_by_count": int(work.get("cited_by_count") or 0),
            "type": (work.get("type") or "").strip(),
        },
    }
    return row


def _append_rows_for_person(
    person: Dict[str, Any],
    *,
    excluded: Set[str],
    overrides: Dict[str, str],
    per_person: int,
    min_citations: int,
    year_min: int,
    year_max: int,
    max_pages: int,
    corpus_tier: str,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Resolve one registry person to OpenAlex works and return new lane rows plus log lines."""
    notes: List[str] = []
    rid = (person.get("resource_id") or "").strip()
    name = (person.get("name") or "").strip()
    aff = (person.get("affiliation_or_venue") or "").strip()
    if not rid or not name:
        return [], [f"skip row with missing resource_id or name: {person}"]

    author_id, match_score, _cands = resolve_openalex_author_id(name, aff, overrides, rid)
    if not author_id:
        return [], [f"no author match for {rid} {name}"]
    if match_score < 0.82 and rid not in overrides:
        notes.append(
            f"weak author match ({match_score:.2f}) for {rid} {name} — add to {OVERRIDES_PATH.name} if wrong"
        )

    works = fetch_top_works_for_author(
        author_id,
        per_page=50,
        max_pages=max_pages,
        min_citations=min_citations,
        year_min=year_min,
        year_max=year_max,
    )
    topics = topic_codes_from_registry_row(person)
    lane_rows: List[Dict[str, Any]] = []
    taken = 0
    for w in works:
        wid = to_work_id((w.get("id") or "").strip())
        if not wid.startswith("W") or wid in excluded:
            continue
        lane_rows.append(build_lane_row_for_work(w, rid, topics, corpus_tier, "person_expansion_auto"))
        excluded.add(wid)
        taken += 1
        if taken >= per_person:
            break
    if taken == 0:
        notes.append(f"no new works above citation threshold for {rid} {name}")
    return lane_rows, notes


def run_proposal(
    *,
    registry_path: Path,
    excluded: Set[str],
    overrides: Dict[str, str],
    per_person: int,
    min_citations: int,
    year_min: int,
    year_max: int,
    max_pages: int,
    only_resource_id: Optional[str],
    corpus_tier: str,
) -> Dict[str, Any]:
    """Fetch OpenAlex data and return a JSON-serializable report with `lane_rows` and metadata."""
    registry = load_json(registry_path)
    people = [
        r
        for r in registry
        if (r.get("content_type") or "").strip() == "PP"
        and (r.get("status") or "").strip() in {"APPROVED", "SEED"}
    ]
    if only_resource_id:
        people = [r for r in people if (r.get("resource_id") or "").strip() == only_resource_id]
    lane_rows: List[Dict[str, Any]] = []
    notes: List[str] = []

    for person in people:
        rows, batch_notes = _append_rows_for_person(
            person,
            excluded=excluded,
            overrides=overrides,
            per_person=per_person,
            min_citations=min_citations,
            year_min=year_min,
            year_max=year_max,
            max_pages=max_pages,
            corpus_tier=corpus_tier,
        )
        lane_rows.extend(rows)
        notes.extend(batch_notes)

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "parameters": {
            "per_person": per_person,
            "min_citations": min_citations,
            "year_min": year_min,
            "year_max": year_max,
            "max_pages": max_pages,
            "corpus_tier": corpus_tier,
            "only_resource_id": only_resource_id,
        },
        "lane_rows": lane_rows,
        "notes": notes,
    }


def _resolved_inclusion_params(args: argparse.Namespace, inc: Dict[str, int]) -> Tuple[int, int, int, int, int]:
    """Apply CLI overrides on top of inclusion dict."""
    per_person = args.per_person if args.per_person is not None else inc["per_person"]
    min_citations = args.min_citations if args.min_citations is not None else inc["min_citations"]
    year_min = args.year_min if args.year_min is not None else inc["year_min"]
    year_max = args.year_max if args.year_max is not None else inc["year_max"]
    max_pages = args.max_pages if args.max_pages is not None else inc["max_pages"]
    return per_person, min_citations, year_min, year_max, max_pages


def _load_overrides(path: Path) -> Dict[str, str]:
    """Load optional `resource_id` → OpenAlex author id URL or bare A-id mapping."""
    if not path.is_file():
        return {}
    raw = load_json(path)
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, str] = {}
    for k, v in raw.items():
        if isinstance(k, str) and isinstance(v, str):
            out[k.strip()] = v.strip()
    return out


def main() -> None:
    """CLI entry: propose merged-lane rows from registry people via OpenAlex."""
    load_dotenv_optional()
    parser = argparse.ArgumentParser(
        description="Propose merged-lane work_id rows from PP registry entries (OpenAlex; requires network)."
    )
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--overrides", type=Path, default=OVERRIDES_PATH)
    parser.add_argument(
        "--inclusion-config",
        type=Path,
        default=INCLUSION_PATH,
        help="JSON with min_citations, per_person, year_min, year_max, max_pages (ignored if --strict).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Use legacy tighter thresholds (min_citations 25, per_person 12, max_pages 4).",
    )
    parser.add_argument(
        "--per-person",
        type=int,
        default=None,
        help="Max new works per person after dedupe (default: from inclusion config).",
    )
    parser.add_argument(
        "--min-citations",
        type=int,
        default=None,
        help="Minimum cited_by_count to include (default: from inclusion config).",
    )
    parser.add_argument("--year-min", type=int, default=None)
    parser.add_argument("--year-max", type=int, default=None)
    parser.add_argument("--max-pages", type=int, default=None, help="OpenAlex list pages to scan per author (50 works/page cap).")
    parser.add_argument("--corpus-tier", choices=("core", "expanded"), default="expanded")
    parser.add_argument("--only-resource-id", default="", help="Restrict to one LE-PP-xxx id.")
    args = parser.parse_args()

    inc = strict_inclusion_defaults() if args.strict else load_inclusion_defaults(args.inclusion_config)
    per_person, min_citations, year_min, year_max, max_pages = _resolved_inclusion_params(args, inc)

    overrides = _load_overrides(args.overrides)
    excluded = collect_excluded_work_ids(ROOT)
    report = run_proposal(
        registry_path=args.registry,
        excluded=excluded,
        overrides=overrides,
        per_person=per_person,
        min_citations=min_citations,
        year_min=year_min,
        year_max=year_max,
        max_pages=max_pages,
        only_resource_id=args.only_resource_id.strip() or None,
        corpus_tier=args.corpus_tier,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, report)
    print(f"Wrote {len(report.get('lane_rows') or [])} proposed rows to {args.output}")
    notes = report.get("notes") or []
    if notes:
        print("Notes:")
        for n in notes[:40]:
            print(f"  - {n}")
        if len(notes) > 40:
            print(f"  ... and {len(notes) - 40} more")


if __name__ == "__main__":
    main()
