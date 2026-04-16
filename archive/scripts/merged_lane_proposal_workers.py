"""Run merged_lane_proposal.py in parallel shards (one registry person per job) and merge lane_rows."""

from __future__ import annotations

import argparse
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Set

from utils import ROOT, load_json, write_json

SCRIPTS = ROOT / "scripts"
REGISTRY_DEFAULT = ROOT / "corpus" / "tables" / "programs_people_registry.json"
INCLUSION_DEFAULT = ROOT / "corpus" / "merged_lane" / "proposal_inclusion.json"
PROPOSAL_SCRIPT = SCRIPTS / "merged_lane_proposal.py"


def _pp_resource_ids(registry_path: Path) -> List[str]:
    """Return LE-PP-xxx ids for approved/seed people rows."""
    rows = load_json(registry_path)
    out: List[str] = []
    for r in rows:
        if (r.get("content_type") or "").strip() != "PP":
            continue
        if (r.get("status") or "").strip() not in {"APPROVED", "SEED"}:
            continue
        rid = (r.get("resource_id") or "").strip()
        if rid:
            out.append(rid)
    return sorted(set(out))


def merge_lane_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep first row per work_id; rows must contain string work_id."""
    seen: Set[str] = set()
    merged: List[Dict[str, Any]] = []
    for row in rows:
        wid = (row.get("work_id") or "").strip()
        if not wid or wid in seen:
            continue
        seen.add(wid)
        merged.append(row)
    return merged


def _run_one_shard(args: tuple[Path, Path, Path, Path, str, bool]) -> tuple[str, int, str]:
    """Subprocess one merged_lane_proposal invocation; returns (resource_id, exit_code, stderr tail)."""
    proposal_script, inclusion, registry, out_path, rid, strict = args
    cmd = [
        sys.executable,
        str(proposal_script),
        "--registry",
        str(registry),
        "--inclusion-config",
        str(inclusion),
        "--only-resource-id",
        rid,
        "--output",
        str(out_path),
    ]
    if strict:
        cmd.append("--strict")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT), check=False)
    err = (proc.stderr or "")[-4000:]
    return (rid, proc.returncode, err)


def main() -> None:
    """CLI: shard merged_lane_proposal across PP rows and merge outputs."""
    parser = argparse.ArgumentParser(
        description="Parallel merged_lane_proposal runs (one --only-resource-id per worker) using proposal_inclusion.json."
    )
    parser.add_argument("--registry", type=Path, default=REGISTRY_DEFAULT)
    parser.add_argument("--inclusion-config", type=Path, default=INCLUSION_DEFAULT)
    parser.add_argument("--shard-dir", type=Path, default=ROOT / "corpus" / "merged_lane" / "proposal_shards")
    parser.add_argument("--merged-output", type=Path, default=ROOT / "corpus" / "merged_lane" / "proposed_lane_additions.json")
    parser.add_argument("--jobs", type=int, default=2, help="Concurrent proposal processes (stay low for OpenAlex).")
    parser.add_argument("--strict", action="store_true", help="Forward --strict to each merged_lane_proposal worker.")
    parser.add_argument(
        "--merge-only",
        action="store_true",
        help="Only merge existing JSON files in --shard-dir (skip running proposals).",
    )
    args = parser.parse_args()

    args.shard_dir.mkdir(parents=True, exist_ok=True)

    if not args.merge_only:
        rids = _pp_resource_ids(args.registry)
        if not rids:
            raise SystemExit("No PP APPROVED/SEED rows in registry.")
        tasks: List[tuple[Path, Path, Path, Path, str, bool]] = []
        for rid in rids:
            out_p = args.shard_dir / f"{rid}.json"
            tasks.append((PROPOSAL_SCRIPT, args.inclusion_config, args.registry, out_p, rid, args.strict))

        failures: List[str] = []
        with ProcessPoolExecutor(max_workers=max(1, args.jobs)) as ex:
            futures = {ex.submit(_run_one_shard, t): t[4] for t in tasks}
            for fut in as_completed(futures):
                rid, code, err = fut.result()
                if code != 0:
                    failures.append(f"{rid} exit {code}: {err[:500]}")

        if failures:
            print("Shard failures:")
            for line in failures[:20]:
                print(line)
            if len(failures) > 20:
                print(f"... and {len(failures) - 20} more")
            raise SystemExit(1)

    shard_files = sorted(args.shard_dir.glob("LE-PP-*.json"))
    if not shard_files:
        raise SystemExit(f"No shard files under {args.shard_dir}")

    all_rows: List[Dict[str, Any]] = []
    notes_acc: List[str] = []
    meta_params: Dict[str, Any] = {}
    for path in shard_files:
        payload = load_json(path)
        all_rows.extend(payload.get("lane_rows") or [])
        for n in payload.get("notes") or []:
            notes_acc.append(f"{path.name}: {n}")
        if not meta_params and isinstance(payload.get("parameters"), dict):
            meta_params = dict(payload["parameters"])

    merged_rows = merge_lane_rows(all_rows)
    report: Dict[str, Any] = {
        "generated_from_shards": [str(p.relative_to(ROOT)) for p in shard_files],
        "parameters": meta_params,
        "lane_rows": merged_rows,
        "notes": notes_acc[:5000],
        "shard_count": len(shard_files),
        "lane_rows_before_dedupe": len(all_rows),
        "lane_rows_after_dedupe": len(merged_rows),
    }
    args.merged_output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.merged_output, report)
    print(
        f"Merged {len(merged_rows)} unique lane rows from {len(shard_files)} shards -> {args.merged_output}"
    )


if __name__ == "__main__":
    main()
