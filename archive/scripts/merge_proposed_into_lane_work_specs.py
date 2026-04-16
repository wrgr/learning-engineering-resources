"""Merge `proposed_lane_additions.json` lane rows into `lane_work_specs.json` (dedupe by work_id, strip audit fields)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Set

from utils import ROOT, load_json, write_json

DEFAULT_PROPOSED = ROOT / "corpus" / "merged_lane" / "proposed_lane_additions.json"
DEFAULT_LANE = ROOT / "corpus" / "merged_lane" / "lane_work_specs.json"


def clean_lane_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Drop proposal-only keys; keep lane_work_specs-compatible fields."""
    return {k: v for k, v in row.items() if k and not str(k).startswith("_")}


def merge_proposed_into_specs(
    specs: List[Dict[str, Any]], proposed_rows: List[Dict[str, Any]]
) -> tuple[List[Dict[str, Any]], int, int]:
    """Return new specs list, count appended, count skipped (duplicate work_id)."""
    seen: Set[str] = {(r.get("work_id") or "").strip() for r in specs if (r.get("work_id") or "").strip()}
    out = list(specs)
    appended = 0
    skipped = 0
    for row in proposed_rows:
        wid = (row.get("work_id") or "").strip()
        if not wid:
            skipped += 1
            continue
        if wid in seen:
            skipped += 1
            continue
        seen.add(wid)
        out.append(clean_lane_row(row))
        appended += 1
    return out, appended, skipped


def main() -> None:
    """CLI: append cleaned proposed rows to lane_work_specs.json."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposed", type=Path, default=DEFAULT_PROPOSED)
    parser.add_argument("--lane", type=Path, default=DEFAULT_LANE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    proposed_payload = load_json(args.proposed)
    rows = proposed_payload.get("lane_rows") or []
    if not isinstance(rows, list):
        raise SystemExit("proposed file must contain a lane_rows array")

    specs = load_json(args.lane)
    if not isinstance(specs, list):
        raise SystemExit("lane_work_specs must be a JSON array")

    merged, appended, skipped = merge_proposed_into_specs(specs, rows)
    print(f"lane rows before: {len(specs)}; proposed: {len(rows)}; appended: {appended}; skipped (dup/empty): {skipped}")

    if args.dry_run:
        return

    write_json(args.lane, merged)
    print(f"Wrote {len(merged)} rows -> {args.lane}")


if __name__ == "__main__":
    main()
