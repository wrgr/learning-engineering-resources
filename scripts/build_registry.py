"""Build site/src/data/programs_people_registry.json from landscape/resources/ YAML files.

Reads all YAML files in landscape/resources/<type>/ subdirectories and writes a flat
JSON array suitable for graph.astro consumption.  This script is the canonical way to
regenerate the registry; do not hand-edit the output JSON.
"""

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    # Minimal YAML parser for our flat record schema (no nested sequences beyond arrays)
    yaml = None  # type: ignore

REPO_ROOT = Path(__file__).parent.parent
RESOURCES_DIR = REPO_ROOT / "landscape" / "resources"
OUTPUT_FILE = REPO_ROOT / "site" / "src" / "data" / "programs_people_registry.json"

# Subdirectories in landscape/resources/ to include in the registry
# (papers are excluded — too large; queried separately via papers_seed.json)
INCLUDE_TYPES = {"people", "organizations", "grey_literature", "programs",
                 "conferences", "tools", "journals", "standards", "history_timeline"}


def parse_yaml_simple(text: str) -> dict:
    """Parse a simple flat YAML record without a full YAML library.

    Handles: scalar strings, quoted strings, block scalars (>), and lists.
    Stops at the first blank line after a block scalar.
    """
    result: dict = {}
    lines = text.splitlines()
    i = 0

    def read_block_scalar(indent_ref: int) -> str:
        """Collect folded block scalar lines until dedent."""
        nonlocal i
        parts = []
        while i < len(lines):
            line = lines[i]
            if line.strip() == "":
                i += 1
                continue
            spaces = len(line) - len(line.lstrip())
            if spaces <= indent_ref and line.strip():
                break
            parts.append(line.strip())
            i += 1
        return " ".join(parts)

    def read_list(indent_ref: int) -> list:
        """Collect list items (lines starting with '  - ')."""
        nonlocal i
        items = []
        while i < len(lines):
            line = lines[i]
            if line.strip() == "":
                i += 1
                continue
            spaces = len(line) - len(line.lstrip())
            if spaces < indent_ref:
                break
            m = re.match(r"^\s+- (.+)$", line)
            if m:
                items.append(m.group(1).strip().strip("\"'"))
                i += 1
            else:
                break
        return items

    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue

        m = re.match(r"^(\w[\w_]*):\s*(.*)", line)
        if not m:
            i += 1
            continue

        key = m.group(1)
        raw_val = m.group(2).strip()
        i += 1

        if raw_val == "|" or raw_val == ">":
            # block scalar: next indented lines
            result[key] = read_block_scalar(0)
        elif raw_val == "":
            # might be a list next
            if i < len(lines) and re.match(r"^\s+- ", lines[i]):
                result[key] = read_list(1)
            else:
                result[key] = None
        else:
            # inline value — strip quotes
            val = raw_val.strip('"\'')
            result[key] = val

    return result


def load_yaml_record(path: Path) -> dict:
    """Load a YAML file to a dict, using PyYAML if available."""
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        try:
            return yaml.safe_load(text) or {}
        except Exception:
            pass
    return parse_yaml_simple(text)


def normalise_secondary_topics(raw) -> list[str]:
    """Normalise secondary_topics to a list of strings."""
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(t).strip() for t in raw if t]
    if isinstance(raw, str):
        return [t.strip() for t in raw.replace(",", " ").split() if t.strip()]
    return []


def record_to_registry_entry(record: dict, subdir: str) -> dict | None:
    """Convert a landscape YAML record to a flat registry entry."""
    rid = record.get("resource_id") or record.get("id")
    if not rid:
        return None

    content_type = record.get("content_type", subdir.upper()[:2])
    name = (
        record.get("name")
        or record.get("title")
        or record.get("event")
        or rid
    )
    url = record.get("url") or record.get("doi") or ""
    if url and record.get("doi") and not url.startswith("http"):
        url = f"https://doi.org/{url}"

    description = record.get("description") or record.get("significance") or ""
    primary_topic = record.get("primary_topic") or "T00"
    secondary_topics = normalise_secondary_topics(record.get("secondary_topics"))

    entry: dict = {
        "resource_id": rid,
        "content_type": content_type,
        "status": record.get("status") or "APPROVED",
        "name": name,
        "url": url,
        "primary_topic": primary_topic,
        "secondary_topics": secondary_topics,
        "description": description,
    }

    # Include extra fields for people
    if content_type == "PP":
        for field in ("affiliation", "era", "role", "years"):
            if record.get(field):
                entry[field] = record[field]

    return entry


def main() -> None:
    """Consolidate all landscape YAML files into a flat registry JSON."""
    entries: list[dict] = []
    seen_ids: set[str] = set()
    errors: list[str] = []

    for subdir in sorted(INCLUDE_TYPES):
        subdir_path = RESOURCES_DIR / subdir
        if not subdir_path.is_dir():
            continue
        yaml_files = sorted(subdir_path.glob("*.yaml"))
        for yf in yaml_files:
            try:
                record = load_yaml_record(yf)
                entry = record_to_registry_entry(record, subdir)
                if entry is None:
                    errors.append(f"No resource_id in {yf.name}")
                    continue
                rid = entry["resource_id"]
                if rid in seen_ids:
                    errors.append(f"Duplicate resource_id {rid} in {yf.name}")
                    continue
                seen_ids.add(rid)
                entries.append(entry)
            except Exception as exc:
                errors.append(f"Error reading {yf}: {exc}")

    OUTPUT_FILE.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Registry built: {len(entries)} entries → {OUTPUT_FILE}")
    if errors:
        print(f"\nWarnings ({len(errors)}):")
        for e in errors[:20]:
            print(f"  {e}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")


if __name__ == "__main__":
    main()
