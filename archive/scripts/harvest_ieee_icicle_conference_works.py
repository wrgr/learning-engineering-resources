"""Harvest OpenAlex work ids for IEEE ICICLE / adjacent conference proceedings into ieee_conference_seed_work_ids.json."""

from __future__ import annotations

import argparse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from openalex_client import api_get_json
from utils import ROOT, load_dotenv_optional, load_json, to_work_id, write_json

DEFAULT_OUT = ROOT / "corpus" / "merged_lane" / "ieee_conference_seed_work_ids.json"
DEFAULT_QUERY_PLAN = ROOT / "corpus" / "merged_lane" / "icicle_adjacent_conference_queries.json"

# Legacy keyword searches when no JSON plan exists.
LEGACY_QUERIES = [
    "IEEE ICICLE",
    "ICICLE learning engineering",
    "International Community for Learning Engineering",
]


def _venue_blob(work: Dict[str, Any]) -> str:
    """Concatenate venue-ish strings for heuristic matching."""
    loc = work.get("primary_location") or {}
    src = (loc.get("source") or {}).get("display_name") or ""
    host = ((work.get("host_venue") or {}).get("display_name") or "").strip()
    title = (work.get("display_name") or "").strip()
    return f"{title} {src} {host}".lower()


def _keep_for_ieee_le_conference(work: Dict[str, Any]) -> bool:
    """True when title or venue plausibly ties to ICICLE or IEEE LE conference context."""
    blob = _venue_blob(work)
    title = (work.get("display_name") or "").lower()
    if "icicle" in blob:
        return True
    if "learning engineering" in title:
        return True
    if "learning engineering" in blob and "ieee" in blob:
        return True
    if "ieee" in blob and "learning" in title and "engineering" in title:
        return True
    return False


def _filter_clause(year_range: str | None) -> str:
    """Build OpenAlex `filter` string (minimal filters reduce 400s from the API)."""
    if year_range is None or not str(year_range).strip():
        return "is_paratext:false"
    yr = str(year_range).strip()
    if yr.isdigit():
        return f"is_paratext:false,publication_year:{yr}"
    if "-" in yr and all(p.strip().isdigit() for p in yr.split("-", 1)):
        a, b = yr.split("-", 1)
        return f"is_paratext:false,publication_year:{a.strip()}-{b.strip()}"
    return "is_paratext:false"


def _load_query_plan(path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Return query entries and defaults from icicle_adjacent_conference_queries.json."""
    if not path.is_file():
        return [], {}
    raw = load_json(path)
    if not isinstance(raw, dict):
        return [], {}
    queries = raw.get("queries")
    if not isinstance(queries, list):
        return [], {}
    defaults = raw.get("defaults") if isinstance(raw.get("defaults"), dict) else {}
    return queries, defaults


def _fetch_page(
    search: str,
    *,
    filter_str: str,
    page: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """One OpenAlex /works page; raises HTTPError on fatal API errors."""
    data = api_get_json(
        "/works",
        {
            "search": search,
            "filter": filter_str,
            "sort": "relevance_score:desc",
            "per-page": "50",
            "page": str(page),
            # Keep `select` minimal — some paths (e.g. host_venue) have triggered 400s from OpenAlex.
            "select": "id,display_name,publication_year,cited_by_count,type,primary_location",
        },
    )
    return data.get("results") or [], data.get("meta") or {}


def harvest_from_plan(
    entries: List[Dict[str, Any]],
    defaults: Dict[str, Any],
    *,
    global_max_total: int,
    default_max_pages: int,
    default_max_per_query: int,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Harvest unique W ids using curated query entries."""
    seen: Set[str] = set()
    ordered: List[str] = []
    audit: List[Dict[str, Any]] = []

    d_pages = int(defaults.get("max_pages") or default_max_pages)
    d_cap = int(defaults.get("max_works_per_query") or default_max_per_query)
    raw_y = defaults.get("publication_year_filter")
    if raw_y is None or (isinstance(raw_y, str) and not raw_y.strip()):
        d_year: str | None = None
    else:
        d_year = str(raw_y).strip()

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        qid = str(entry.get("id") or entry.get("label") or "query")
        search = (entry.get("openalex_search") or "").strip()
        if not search:
            continue
        trust = bool(entry.get("trust_query", False))
        if "publication_year_filter" in entry:
            ey = entry.get("publication_year_filter")
            if ey is None or (isinstance(ey, str) and not ey.strip()):
                year = None
            else:
                year = str(ey).strip()
        else:
            year = d_year
        max_pages = int(entry.get("max_pages") or d_pages)
        cap = int(entry.get("max_works_per_query") or d_cap)
        filt = _filter_clause(year)
        collected = 0
        for page in range(1, max_pages + 1):
            if len(ordered) >= global_max_total or collected >= cap:
                break
            try:
                batch, meta = _fetch_page(search, filter_str=filt, page=page)
            except urllib.error.HTTPError as exc:
                detail = ""
                try:
                    raw = exc.read()
                    if isinstance(raw, bytes):
                        detail = raw[:800].decode("utf-8", errors="replace")
                except Exception:
                    detail = ""
                audit.append(
                    {
                        "query_id": qid,
                        "search": search[:200],
                        "page": page,
                        "http_error": exc.code,
                        "detail": detail,
                    }
                )
                break
            audit.append(
                {
                    "query_id": qid,
                    "page": page,
                    "meta_count": meta.get("count"),
                    "results_len": len(batch),
                }
            )
            if not batch:
                break
            for w in batch:
                if len(ordered) >= global_max_total or collected >= cap:
                    break
                if not trust and not _keep_for_ieee_le_conference(w):
                    continue
                wid = to_work_id((w.get("id") or "").strip())
                if not wid.startswith("W") or wid in seen:
                    continue
                seen.add(wid)
                ordered.append(wid)
                collected += 1
    return ordered, audit


def harvest_legacy(
    queries: List[str],
    *,
    max_pages_per_query: int,
    max_total: int,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Original narrow keyword harvest (heuristic filter on every hit)."""
    seen: Set[str] = set()
    ordered: List[str] = []
    audit: List[Dict[str, Any]] = []
    filt = _filter_clause(None)
    for q in queries:
        for page in range(1, max_pages_per_query + 1):
            if len(ordered) >= max_total:
                return ordered, audit
            try:
                batch, meta = _fetch_page(q, filter_str=filt, page=page)
            except urllib.error.HTTPError as exc:
                audit.append({"query": q, "page": page, "http_error": exc.code})
                break
            audit.append({"query": q, "page": page, "meta_count": meta.get("count"), "results_len": len(batch)})
            if not batch:
                break
            for w in batch:
                if len(ordered) >= max_total:
                    return ordered, audit
                if not _keep_for_ieee_le_conference(w):
                    continue
                wid = to_work_id((w.get("id") or "").strip())
                if not wid.startswith("W") or wid in seen:
                    continue
                seen.add(wid)
                ordered.append(wid)
    return ordered, audit


def main() -> None:
    """CLI: write ieee_conference_seed_work_ids.json with harvested W ids."""
    load_dotenv_optional()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--queries-json",
        type=Path,
        default=DEFAULT_QUERY_PLAN,
        help="Curated conference search plan (icicle_adjacent_conference_queries.json).",
    )
    parser.add_argument("--max-pages", type=int, default=12, help="Default max OpenAlex pages per query (50 works/page).")
    parser.add_argument("--max-per-query", type=int, default=150, help="Default cap of new works kept per query.")
    parser.add_argument("--max-total", type=int, default=10000, help="Global cap on unique work ids.")
    parser.add_argument(
        "--merge-existing",
        action="store_true",
        help="Union with existing work_ids in --output before writing (deduped).",
    )
    parser.add_argument(
        "--legacy-only",
        action="store_true",
        help="Ignore --queries-json; run narrow ICICLE keyword harvest only.",
    )
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        help="Extra legacy search string when using --legacy-only (repeatable).",
    )
    args = parser.parse_args()

    entries, defaults = _load_query_plan(args.queries_json)
    prior_ids: List[str] = []
    prior_desc = ""
    if args.output.is_file():
        raw = load_json(args.output)
        if isinstance(raw, dict):
            if isinstance(raw.get("description"), str):
                prior_desc = raw["description"]
            w = raw.get("work_ids")
            if isinstance(w, list):
                prior_ids = [str(x).strip() for x in w if str(x).strip().startswith("W")]

    if args.legacy_only or not entries:
        qlist = list(dict.fromkeys(LEGACY_QUERIES + [q.strip() for q in args.query if q.strip()]))
        work_ids, audit = harvest_legacy(
            qlist,
            max_pages_per_query=args.max_pages,
            max_total=args.max_total,
        )
        meta_queries = qlist
    else:
        work_ids, audit = harvest_from_plan(
            entries,
            defaults,
            global_max_total=args.max_total,
            default_max_pages=args.max_pages,
            default_max_per_query=args.max_per_query,
        )
        meta_queries = [e.get("id") for e in entries if isinstance(e, dict)]

    if args.merge_existing and prior_ids:
        seen: Set[str] = set()
        merged: List[str] = []
        for wid in prior_ids + work_ids:
            if wid in seen:
                continue
            seen.add(wid)
            merged.append(wid)
        work_ids = merged[: args.max_total]

    payload: Dict[str, Any] = {
        "description": prior_desc
        or "OpenAlex-harvested W ids for IEEE ICICLE / Learning Engineering–adjacent conferences (see harvest_meta).",
        "work_ids": work_ids,
        "harvest_meta": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "query_plan": str(args.queries_json.relative_to(ROOT)) if args.queries_json.is_file() else "",
            "legacy_only": args.legacy_only,
            "queries": meta_queries,
            "max_pages_default": args.max_pages,
            "max_per_query_default": args.max_per_query,
            "max_total": args.max_total,
            "merge_existing": args.merge_existing,
            "audit": audit,
            "count": len(work_ids),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, payload)
    print(f"Wrote {len(work_ids)} work ids -> {args.output}")


if __name__ == "__main__":
    main()
