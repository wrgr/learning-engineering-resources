"""Build `data/merged/` site bundle: classic graph + distilled broad-lane papers from OpenAlex."""

from __future__ import annotations

import hashlib
import subprocess
import time
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from openalex_client import api_get_json, work_to_metadata
from utils import ROOT, citation_bibtex, citation_plain, doi_to_url, load_dotenv_optional, load_json, write_json

DATA_DIR = ROOT / "data"
CORPUS_MERGED = ROOT / "corpus" / "merged_lane"
OUT_DIR = DATA_DIR / "merged"

# Outer retries on top of `openalex_client.api_get_json` (handles rate limits inside).
_MERGED_LANE_FETCH_ATTEMPTS = 8


def _sha256_file(path: Path) -> str:
    """Return lowercase hex SHA-256 of file contents for reproducibility audits."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head_optional() -> str:
    """Return current repo HEAD sha, or empty string if unavailable (not a git checkout or git missing)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=8,
        )
        if proc.returncode != 0:
            return ""
        return (proc.stdout or "").strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _merged_lane_input_provenance() -> Dict[str, Any]:
    """Fingerprint merged-lane corpus inputs so runs are auditable and reruns are comparable."""
    inputs: Dict[str, Path] = {
        "lane_work_specs.json": CORPUS_MERGED / "lane_work_specs.json",
        "openalex_thematic_queries.json": CORPUS_MERGED / "openalex_thematic_queries.json",
        "coverage_manifest.json": CORPUS_MERGED / "coverage_manifest.json",
        "programs_people_registry.json": ROOT / "corpus" / "tables" / "programs_people_registry.json",
    }
    sha_map: Dict[str, str] = {}
    rel_paths: Dict[str, str] = {}
    for label, p in inputs.items():
        rel_paths[label] = str(p.relative_to(ROOT))
        sha_map[label] = _sha256_file(p) if p.is_file() else ""
    return {
        "input_sha256": sha_map,
        "input_paths_relative_to_repo": rel_paths,
        "git_head": _git_head_optional(),
    }


def _fetch_openalex_work_for_lane(wid: str) -> Dict[str, Any]:
    """GET `/works/{wid}` with exponential backoff; do not retry permanent 404."""
    last_exc: BaseException | None = None
    for attempt in range(_MERGED_LANE_FETCH_ATTEMPTS):
        try:
            work = api_get_json(f"/works/{wid}", {})
            if not isinstance(work, dict) or not (work.get("id") or "").strip():
                raise ValueError(f"invalid or empty OpenAlex work payload for {wid}")
            return work
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code == 404:
                raise RuntimeError(f"OpenAlex work not found (404): {wid}") from exc
        except Exception as exc:
            last_exc = exc
        if attempt < _MERGED_LANE_FETCH_ATTEMPTS - 1:
            delay = min(2.0 * (2**attempt), 120.0)
            time.sleep(delay)
    raise RuntimeError(
        f"OpenAlex /works/{wid} failed after {_MERGED_LANE_FETCH_ATTEMPTS} attempts: {last_exc}"
    ) from last_exc


def _openalex_work_ids_from_papers_file(path: Path) -> Set[str]:
    """Return OpenAlex work IDs (W…) referenced by `papers_seed.json` / `papers_one_hop.json`."""
    payload = load_json(path)
    papers = payload.get("papers") or []
    out: Set[str] = set()
    for paper in papers:
        oid = (paper.get("openalex_id") or "").strip()
        if oid:
            out.add(oid.rstrip("/").split("/")[-1])
    return out


def _dedupe_lane_specs(
    specs: List[Dict[str, Any]], classic_work_ids: Set[str]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Drop lane rows whose work already exists in seed/hop; drop duplicate work_id (first row wins)."""
    seen_wid: Set[str] = set()
    kept: List[Dict[str, Any]] = []
    skipped: List[str] = []
    for spec in specs:
        wid = (spec.get("work_id") or "").strip()
        if not wid:
            skipped.append("empty work_id")
            continue
        if wid in seen_wid:
            skipped.append(f"duplicate work_id in lane_work_specs: {wid}")
            continue
        if wid in classic_work_ids:
            skipped.append(f"already in seed/hop papers (openalex_id): {wid}")
            continue
        seen_wid.add(wid)
        kept.append(spec)
    return kept, skipped


def _topic_names(topic_codes: List[str], topic_map: Dict[str, Any]) -> List[str]:
    by_code = {t["topic_code"]: t["topic_name"] for t in topic_map.get("topics", [])}
    return [by_code.get(c, "") for c in topic_codes]


def build_merged_bundle() -> None:
    load_dotenv_optional()
    raw_specs: List[Dict[str, Any]] = load_json(CORPUS_MERGED / "lane_work_specs.json")
    classic_ids = _openalex_work_ids_from_papers_file(DATA_DIR / "papers_seed.json") | _openalex_work_ids_from_papers_file(
        DATA_DIR / "papers_one_hop.json"
    )
    specs, skip_reasons = _dedupe_lane_specs(raw_specs, classic_ids)
    base_graph = load_json(DATA_DIR / "graph.json")
    base_summary = load_json(DATA_DIR / "build_summary.json")
    topic_map = load_json(DATA_DIR / "topic_map.json")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    papers: List[Dict[str, Any]] = []
    nodes = list(base_graph.get("nodes", []))
    edges = list(base_graph.get("edges", []))
    fetch_log: List[Dict[str, Any]] = []

    for spec in specs:
        wid = spec["work_id"]
        t0 = time.perf_counter()
        work = _fetch_openalex_work_for_lane(wid)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        fetch_log.append({"work_id": wid, "ok": True, "elapsed_ms": elapsed_ms})
        meta = work_to_metadata(work)
        tier = spec.get("corpus_tier", "core")
        if tier not in ("core", "expanded"):
            tier = "core"

        authors_join = ", ".join(meta["authors"][:48])
        venue = meta.get("venue") or ""
        doi = meta.get("doi") or ""
        plain = citation_plain(meta["title"], authors_join, meta["year"], venue, doi)
        bib = citation_bibtex(wid, meta["title"], authors_join, meta["year"], venue, doi)
        topic_codes = [str(c) for c in spec.get("topic_codes", [])]

        paper: Dict[str, Any] = {
            "id": meta["work_id"],
            "openalex_id": meta["openalex_id"],
            "title": meta["title"],
            "abstract": meta.get("abstract") or "",
            "abstract_source": "openalex",
            "abstract_is_proxy": False,
            "year": meta["year"],
            "doi": doi,
            "venue": venue,
            "type": meta.get("type") or "article",
            "cited_by_count": meta.get("cited_by_count") or 0,
            "authors": meta["authors"],
            "referenced_works": meta.get("referenced_works") or [],
            "citation_plain": plain,
            "citation_bibtex": bib,
            "source_url": doi_to_url(doi) if doi else "",
            "topic_codes": topic_codes,
            "topic_names": _topic_names(topic_codes, topic_map),
            "artifact_type": "derived_merged_lane",
            "corpus_tier": tier,
            "source_lane": spec.get("source_lane", "merged_lane"),
            "cross_seed_score": 0,
            "edge_types": ["merged_lane"],
        }
        if spec.get("source_expansion"):
            paper["source_expansion"] = spec["source_expansion"]
        if spec.get("registry_program_id"):
            paper["registry_program_id"] = spec["registry_program_id"]
        if spec.get("registry_person_id"):
            paper["registry_person_id"] = spec["registry_person_id"]
        if spec.get("thematic_query_id"):
            paper["thematic_query_id"] = spec["thematic_query_id"]
        papers.append(paper)

        label = meta["title"]
        if len(label) > 118:
            label = label[:115] + "..."

        nodes.append(
            {
                "id": meta["work_id"],
                "label": label,
                "type": "paper",
                "hop": 2,
                "topic_codes": topic_codes,
                "corpus_tier": tier,
                "provenance": {
                    "scope": "merged_lane",
                    "source_lane": spec.get("source_lane", ""),
                    **(
                        {"registry_program_id": spec["registry_program_id"]}
                        if spec.get("registry_program_id")
                        else {}
                    ),
                    **(
                        {"registry_person_id": spec["registry_person_id"]}
                        if spec.get("registry_person_id")
                        else {}
                    ),
                    **({"source_expansion": spec["source_expansion"]} if spec.get("source_expansion") else {}),
                    **(
                        {"thematic_query_id": spec["thematic_query_id"]}
                        if spec.get("thematic_query_id")
                        else {}
                    ),
                },
            }
        )
        for code in topic_codes:
            edges.append({"source": code, "target": meta["work_id"], "type": "contains"})

    summary = dict(base_summary)
    summary["merged_lane_papers"] = len(papers)
    summary["merged_lane_core"] = sum(1 for p in papers if p.get("corpus_tier") == "core")
    summary["merged_lane_expanded"] = sum(1 for p in papers if p.get("corpus_tier") == "expanded")
    summary["merged_lane_specs_input"] = len(raw_specs)
    summary["merged_lane_specs_skipped"] = skip_reasons
    summary["merged_lane_openalex_fetch_log"] = fetch_log
    summary["merged_lane_input_provenance"] = _merged_lane_input_provenance()
    summary["graph_nodes"] = len(nodes)
    summary["graph_edges"] = len(edges)
    summary["built_merged_at_utc"] = datetime.now(timezone.utc).isoformat()

    write_json(OUT_DIR / "papers_merged_lane.json", {"papers": papers})
    write_json(OUT_DIR / "graph.json", {"nodes": nodes, "edges": edges})
    write_json(OUT_DIR / "build_summary.json", summary)


if __name__ == "__main__":
    build_merged_bundle()
    print(f"Wrote merged bundle under {OUT_DIR}")
    summary = load_json(OUT_DIR / "build_summary.json")
    skipped = summary.get("merged_lane_specs_skipped") or []
    if skipped:
        print(f"Skipped {len(skipped)} lane spec row(s) (dedupe): {skipped}")
