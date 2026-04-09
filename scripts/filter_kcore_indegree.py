#!/usr/bin/env python3
"""Filter expansion candidates by cross-seed and in-degree k-core."""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

OPENALEX_BASE = "https://api.openalex.org"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="corpus/expansion/candidates_cross_seed_ge2.jsonl",
        help="Input candidate JSONL file (already filtered by cross_seed_score >= 2)",
    )
    parser.add_argument(
        "--output-dir",
        default="corpus/expansion",
        help="Output directory",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=2,
        help="k threshold for in-degree and k-core pruning",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=40,
        help="OpenAlex batch size for work fetches",
    )
    parser.add_argument(
        "--sleep-sec",
        type=float,
        default=0.12,
        help="Pause between API calls",
    )
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=30.0,
        help="HTTP timeout in seconds",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=True) + "\n")


def to_work_id(openalex_id: str) -> str:
    if not openalex_id:
        return ""
    return openalex_id.rstrip("/").split("/")[-1]


def chunked(items: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def api_get_json(path: str, params: Dict[str, str], timeout_sec: float, sleep_sec: float) -> Dict:
    url = f"{OPENALEX_BASE}{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=timeout_sec) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if sleep_sec > 0:
        time.sleep(sleep_sec)
    return data


def fetch_referenced_works_map(
    work_ids: List[str], batch_size: int, timeout_sec: float, sleep_sec: float
) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for batch in chunked(work_ids, batch_size):
        filt = "openalex:" + "|".join(batch)
        data = api_get_json(
            "/works",
            {
                "filter": filt,
                "per-page": str(len(batch)),
                "select": "id,referenced_works",
            },
            timeout_sec=timeout_sec,
            sleep_sec=sleep_sec,
        )
        for work in data.get("results", []):
            wid = to_work_id(work.get("id", ""))
            refs = [to_work_id(ref) for ref in (work.get("referenced_works") or [])]
            out[wid] = [r for r in refs if r]
    return out


def build_induced_edges(work_ids: Set[str], refs_map: Dict[str, List[str]]) -> List[Tuple[str, str]]:
    edges: List[Tuple[str, str]] = []
    for src, refs in refs_map.items():
        if src not in work_ids:
            continue
        for dst in refs:
            if dst in work_ids and dst != src:
                edges.append((src, dst))
    return edges


def indegree_counts(nodes: Set[str], edges: List[Tuple[str, str]]) -> Dict[str, int]:
    counts = {n: 0 for n in nodes}
    for src, dst in edges:
        if src in nodes and dst in nodes:
            counts[dst] += 1
    return counts


def k_in_core(nodes: Set[str], edges: List[Tuple[str, str]], k: int) -> Set[str]:
    active = set(nodes)
    while True:
        indeg = indegree_counts(active, edges)
        remove = {n for n in active if indeg.get(n, 0) < k}
        if not remove:
            return active
        active -= remove
        if not active:
            return active


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    candidates = load_jsonl(input_path)
    work_ids = sorted(
        {
            (row.get("work_id") or "")
            for row in candidates
            if isinstance(row.get("work_id"), str) and row.get("work_id")
        }
    )
    work_id_set = set(work_ids)

    refs_map = fetch_referenced_works_map(
        work_ids=work_ids,
        batch_size=args.batch_size,
        timeout_sec=args.timeout_sec,
        sleep_sec=args.sleep_sec,
    )
    edges = build_induced_edges(work_id_set, refs_map)
    indeg = indegree_counts(work_id_set, edges)

    k = args.k
    indeg_ge_k = {wid for wid, val in indeg.items() if val >= k}
    kcore_nodes = k_in_core(work_id_set, edges, k=k)
    final_nodes = kcore_nodes & indeg_ge_k

    by_work_id = {row.get("work_id"): row for row in candidates if row.get("work_id")}
    final_rows = [by_work_id[wid] for wid in sorted(final_nodes) if wid in by_work_id]
    final_rows_sorted = sorted(
        final_rows,
        key=lambda r: (-(r.get("cross_seed_score") or 0), -(indeg.get(r.get("work_id"), 0)), r.get("work_id", "")),
    )

    out_file = output_dir / f"candidates_cross_seed_ge2_kincore_indeg_ge{k}.jsonl"
    write_jsonl(out_file, final_rows_sorted)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": str(input_path),
        "k": k,
        "counts": {
            "input_candidates": len(candidates),
            "input_work_ids": len(work_id_set),
            "induced_edges": len(edges),
            "indegree_ge_k": len(indeg_ge_k),
            "k_in_core_nodes": len(kcore_nodes),
            "final_nodes": len(final_nodes),
        },
        "output_file": str(out_file),
    }
    write_json(output_dir / f"kcore_indegree_summary_k{k}.json", summary)
    print(json.dumps(summary["counts"], indent=2))


if __name__ == "__main__":
    main()
