"""Append OpenAlex work ids from ieee_conference_seed_work_ids.json into lane_work_specs.json for merged graph builds."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Set

from utils import ROOT, load_json, to_work_id, write_json

DEFAULT_IEEE = ROOT / "corpus" / "merged_lane" / "ieee_conference_seed_work_ids.json"
DEFAULT_LANE = ROOT / "corpus" / "merged_lane" / "lane_work_specs.json"


def classic_openalex_work_ids(data_dir: Path) -> Set[str]:
    """Return W… ids already in curated seed / one-hop papers (build skips these)."""
    out: Set[str] = set()
    for rel in ("papers_seed.json", "papers_one_hop.json"):
        p = data_dir / rel
        if not p.is_file():
            continue
        payload = load_json(p)
        for paper in payload.get("papers") or []:
            oid = (paper.get("openalex_id") or paper.get("id") or "").strip()
            if oid:
                out.add(to_work_id(oid))
    return out


def lane_work_id_set(specs: List[Dict[str, Any]]) -> Set[str]:
    """Existing lane work_ids."""
    return {(r.get("work_id") or "").strip() for r in specs if (r.get("work_id") or "").strip()}


def build_rows_for_ieee_seeds(
    work_ids: List[str],
    *,
    existing_lane: Set[str],
    classic: Set[str],
) -> tuple[List[Dict[str, Any]], int, int, int]:
    """Return new spec rows and counts: appended, skipped_lane, skipped_classic."""
    rows: List[Dict[str, Any]] = []
    skip_lane = 0
    skip_classic = 0
    for raw in work_ids:
        wid = to_work_id(str(raw).strip())
        if not wid.startswith("W"):
            continue
        if wid in existing_lane:
            skip_lane += 1
            continue
        if wid in classic:
            skip_classic += 1
            continue
        existing_lane.add(wid)
        rows.append(
            {
                "work_id": wid,
                "topic_codes": ["T00", "T16"],
                "corpus_tier": "expanded",
                "source_lane": "harvest:ieee_icicle_conference_seeds",
                "source_expansion": "thematic",
            }
        )
    return rows, len(rows), skip_lane, skip_classic


def main() -> None:
    """CLI: append IEEE harvest seeds into lane_work_specs.json."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ieee-json", type=Path, default=DEFAULT_IEEE)
    parser.add_argument("--lane", type=Path, default=DEFAULT_LANE)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ieee_payload = load_json(args.ieee_json)
    raw_ids = ieee_payload.get("work_ids") or []
    if not isinstance(raw_ids, list):
        raise SystemExit("ieee json must contain work_ids array")

    specs = load_json(args.lane)
    if not isinstance(specs, list):
        raise SystemExit("lane_work_specs must be a JSON array")

    lane_set = lane_work_id_set(specs)
    classic = classic_openalex_work_ids(args.data_dir)
    new_rows, n_new, skip_lane, skip_classic = build_rows_for_ieee_seeds(
        [str(x) for x in raw_ids],
        existing_lane=set(lane_set),
        classic=classic,
    )

    print(
        f"ieee work_ids: {len(raw_ids)}; new lane rows to add: {n_new}; "
        f"skip (already in lane): {skip_lane}; skip (in seed/hop): {skip_classic}"
    )

    if args.dry_run:
        return

    merged = specs + new_rows
    write_json(args.lane, merged)
    print(f"Wrote {len(merged)} total rows -> {args.lane}")


if __name__ == "__main__":
    main()
