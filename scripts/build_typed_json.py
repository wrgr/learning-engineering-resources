"""Build landscape/data/ typed JSON files from landscape/resources/ YAML files.

Outputs one JSON file per content type in landscape/data/:
  papers.json, people.json, grey_literature.json, organizations.json,
  history_timeline.json, programs.json, conferences.json, tools.json,
  journals.json, standards.json

These files are consumed by lebokai/scripts/enrich.ts and other downstream
tools. Regenerate after any change to landscape/resources/.

Run from the repo root:
    python3 scripts/build_typed_json.py

Requires PyYAML (see scripts/requirements.txt).
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
RESOURCES_DIR = REPO_ROOT / "landscape" / "resources"
OUTPUT_DIR = REPO_ROOT / "landscape" / "data"

# Map resource subdir → output filename
SUBDIR_TO_FILE: dict[str, str] = {
    "papers": "papers.json",
    "people": "people.json",
    "grey_literature": "grey_literature.json",
    "organizations": "organizations.json",
    "history_timeline": "history_timeline.json",
    "programs": "programs.json",
    "conferences": "conferences.json",
    "tools": "tools.json",
    "journals": "journals.json",
    "standards": "standards.json",
}


def load_yaml(path: Path) -> dict:
    """Load a YAML record file to a dict."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def normalise_record(record: dict) -> dict:
    """Normalise secondary_topics to a list and cast numeric fields."""
    raw_st = record.get("secondary_topics")
    if isinstance(raw_st, str):
        record["secondary_topics"] = [
            t.strip() for t in raw_st.replace(",", " ").split() if t.strip()
        ]
    elif raw_st is None:
        record["secondary_topics"] = []

    # Cast year and citation_count_approx to int where possible
    for field in ("year", "citation_count_approx", "volume", "cross_seed_score"):
        val = record.get(field)
        if val is not None:
            try:
                record[field] = int(val)
            except (ValueError, TypeError):
                pass

    return record


def build_typed_json() -> None:
    """Read all YAML files and write typed JSON files to landscape/data/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total_written = 0
    errors: list[str] = []

    for subdir, out_filename in SUBDIR_TO_FILE.items():
        subdir_path = RESOURCES_DIR / subdir
        if not subdir_path.is_dir():
            continue

        yaml_files = sorted(subdir_path.glob("*.yaml"))
        records: list[dict] = []
        for yf in yaml_files:
            try:
                record = load_yaml(yf)
                record = normalise_record(record)
                records.append(record)
            except Exception as exc:
                errors.append(f"{yf.name}: {exc}")

        out_path = OUTPUT_DIR / out_filename
        out_path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"  {out_filename}: {len(records)} entries")
        total_written += len(records)

    print(f"\nTotal: {total_written} records written to {OUTPUT_DIR}")
    if errors:
        print(f"\nWarnings ({len(errors)}):")
        for e in errors[:20]:
            print(f"  {e}")


if __name__ == "__main__":
    build_typed_json()
