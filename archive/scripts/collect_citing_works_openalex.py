"""Collect OpenAlex works that cite given seed work IDs (one or two forward hops in the citation graph)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from openalex_client import api_get_json
from utils import ROOT, load_dotenv_optional, load_json, to_work_id, write_json

DEFAULT_SEEDS = ROOT / "data" / "merged" / "papers_merged_lane.json"
DEFAULT_OUT = ROOT / "corpus" / "merged_lane" / "citing_one_hop_candidates.json"
DEFAULT_IEEE_SEEDS = ROOT / "corpus" / "merged_lane" / "ieee_conference_seed_work_ids.json"


def _work_ids_from_merged_papers(path: Path) -> List[str]:
    """Return OpenAlex W… ids from merged lane papers JSON."""
    payload = load_json(path)
    out: List[str] = []
    for paper in payload.get("papers") or []:
        wid = to_work_id((paper.get("openalex_id") or paper.get("id") or "").strip())
        if wid.startswith("W"):
            out.append(wid)
    return out


def work_ids_from_seed_list_json(path: Path) -> List[str]:
    """Return W… ids from `ieee_conference_seed_work_ids.json` or any JSON with a `work_ids` array."""
    if not path.is_file():
        return []
    raw = load_json(path)
    if not isinstance(raw, dict):
        return []
    ids = raw.get("work_ids")
    if not isinstance(ids, list):
        return []
    out: List[str] = []
    for item in ids:
        if isinstance(item, str):
            w = to_work_id(item.strip())
            if w.startswith("W"):
                out.append(w)
    return out


def collect_citing_rows_for_seeds(
    seeds: List[str],
    *,
    max_per_seed: int,
    max_pages: int,
    hop_round: int,
) -> Tuple[List[Dict[str, Any]], Set[str]]:
    """Collect citing works for each seed; dedupe across seeds; tag rows with hop_round."""
    seen: Set[str] = set()
    rows: List[Dict[str, Any]] = []
    for seed in seeds:
        works = fetch_citing_works_for_seed(
            seed,
            max_per_seed=max_per_seed,
            max_pages=max_pages,
        )
        for w in works:
            wid = to_work_id((w.get("id") or "").strip())
            if not wid.startswith("W") or wid in seen:
                continue
            seen.add(wid)
            rows.append(
                {
                    "work_id": wid,
                    "cites_seed": seed,
                    "hop_round": hop_round,
                    "title": (w.get("display_name") or "").strip(),
                    "publication_year": w.get("publication_year"),
                    "cited_by_count": int(w.get("cited_by_count") or 0),
                    "type": (w.get("type") or "").strip(),
                }
            )
    return rows, seen


def fetch_citing_works_for_seed(
    seed_wid: str,
    *,
    max_per_seed: int,
    max_pages: int,
) -> List[Dict[str, Any]]:
    """Return work dicts that cite `seed_wid`, sorted by cited_by_count via repeated /works pages."""
    collected: List[Dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        if len(collected) >= max_per_seed:
            break
        data = api_get_json(
            "/works",
            {
                "filter": f"cites:{seed_wid},is_paratext:false",
                "sort": "cited_by_count:desc",
                "per-page": "50",
                "page": str(page),
                "select": "id,display_name,publication_year,cited_by_count,type,doi",
            },
        )
        batch = data.get("results") or []
        if not batch:
            break
        for w in batch:
            if len(collected) >= max_per_seed:
                break
            collected.append(w)
    return collected


def _dedupe_candidates_by_hop(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prefer the smallest hop_round when the same work_id appears twice."""
    best: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        wid = row.get("work_id") or ""
        if not wid:
            continue
        prev = best.get(wid)
        if prev is None or int(row.get("hop_round") or 99) < int(prev.get("hop_round") or 99):
            best[wid] = row
    return list(best.values())


def _round2_seed_ids(
    round1_rows: List[Dict[str, Any]],
    *,
    exclude: Set[str],
    max_seeds: int,
) -> List[str]:
    """Pick high cited_by_count round-1 candidates as seeds for a second hop."""
    ranked = sorted(round1_rows, key=lambda r: int(r.get("cited_by_count") or 0), reverse=True)
    out: List[str] = []
    for r in ranked:
        wid = (r.get("work_id") or "").strip()
        if not wid.startswith("W") or wid in exclude:
            continue
        out.append(wid)
        if len(out) >= max_seeds:
            break
    return out


def main() -> None:
    """CLI: write citing-hop candidates for manual review (not auto-appended to lane_work_specs)."""
    load_dotenv_optional()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--merged-papers",
        type=Path,
        default=DEFAULT_SEEDS,
        help="JSON with papers list (default: data/merged/papers_merged_lane.json).",
    )
    parser.add_argument(
        "--no-merged",
        action="store_true",
        help="Do not load seeds from --merged-papers (use --seed-list-json and/or --work-id only).",
    )
    parser.add_argument(
        "--seed-list-json",
        type=Path,
        default=DEFAULT_IEEE_SEEDS,
        help="JSON with work_ids array (default: corpus/merged_lane/ieee_conference_seed_work_ids.json). Pass a non-existent path to skip.",
    )
    parser.add_argument(
        "--work-id",
        action="append",
        default=[],
        help="Additional W… id (repeatable); unioned with merged and seed-list seeds.",
    )
    parser.add_argument("--max-per-seed", type=int, default=40, help="Cap citing works collected per seed.")
    parser.add_argument("--max-pages", type=int, default=5, help="OpenAlex pages per seed (50 works/page).")
    parser.add_argument(
        "--rounds",
        type=int,
        choices=(1, 2),
        default=1,
        help="2 = second hop using top cited round-1 candidates as seeds (see --max-round2-seeds).",
    )
    parser.add_argument(
        "--max-round2-seeds",
        type=int,
        default=80,
        help="Max distinct round-1 candidate works to use as seeds for hop 2 (sorted by cited_by_count).",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    seeds: List[str] = []
    if not args.no_merged and args.merged_papers.is_file():
        seeds.extend(_work_ids_from_merged_papers(args.merged_papers))
    if args.seed_list_json.is_file():
        seeds.extend(work_ids_from_seed_list_json(args.seed_list_json))
    seeds.extend(to_work_id(w.strip()) for w in args.work_id if w.strip())
    seeds = [w for w in seeds if w.startswith("W")]
    seeds = list(dict.fromkeys(seeds))
    if not seeds:
        raise SystemExit(
            "No seed work ids: build data/merged/papers_merged_lane.json, add ids to ieee_conference_seed_work_ids.json, "
            "or pass --work-id W… (use --no-merged with explicit seeds only)."
        )

    seeds_r0 = set(seeds)
    rows_r1, _ = collect_citing_rows_for_seeds(
        seeds,
        max_per_seed=args.max_per_seed,
        max_pages=args.max_pages,
        hop_round=1,
    )
    all_rows = list(rows_r1)
    seeds_r2: List[str] = []

    if args.rounds == 2:
        seeds_r2 = _round2_seed_ids(rows_r1, exclude=seeds_r0, max_seeds=args.max_round2_seeds)
        rows_r2, _ = collect_citing_rows_for_seeds(
            seeds_r2,
            max_per_seed=args.max_per_seed,
            max_pages=args.max_pages,
            hop_round=2,
        )
        all_rows.extend(rows_r2)

    rows = _dedupe_candidates_by_hop(all_rows)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed_count": len(seeds),
        "candidate_count": len(rows),
        "seeds": seeds,
        "candidates": rows,
        "rounds_requested": args.rounds,
        "round2_seed_count": len(seeds_r2),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, payload)
    print(f"Wrote {len(rows)} unique citing works from {len(seeds)} base seeds -> {args.output}")


if __name__ == "__main__":
    main()
